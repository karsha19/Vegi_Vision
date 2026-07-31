import os
import io
import json
import re
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from google import genai
from google.genai import errors as genai_errors
from PIL import Image

GEMINI_MODEL_DEFAULT = "gemini-flash-lite-latest"

# The identify call is small/fast by nature (one short label back), so a
# generous-but-bounded timeout keeps the UI from ever hanging indefinitely
# on a slow/stalled network call while still giving normal requests room.
IDENTIFY_TIMEOUT_SECONDS = 20
IDENTIFY_MAX_DIMENSION = 768  # downscaling this small cuts upload + inference time significantly

# Recipe generation returns a larger JSON payload and does more "thinking",
# so it gets more headroom than identify — but still a hard ceiling so a
# stalled request can never hang the app indefinitely.
GENERATE_RECIPE_TIMEOUT_SECONDS = 45

# One shared worker pool for the (rare, short-lived) blocking Gemini calls,
# so each request gets a real timeout instead of blocking Streamlit's
# script thread with no way out if the network stalls.
_gemini_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="veg-gemini")

# Simple bounded in-memory cache: same photo -> same answer, instantly,
# with no repeat API call. Keyed by a content hash of the (downscaled)
# image, so re-clicking "Identify" on the same photo, or re-uploading it
# later in the same server process, is free.
_identify_cache: dict[str, str] = {}
_identify_cache_lock = threading.Lock()
_IDENTIFY_CACHE_MAX_ENTRIES = 100

# The genai.Client wraps its own HTTP connection pool; building a new one
# per request (per rerun, since Streamlit reruns the whole script on every
# interaction) throws away connection keep-alive/TLS session reuse for no
# reason. One client is created per (process, api key) and reused for the
# life of the process.
_client_cache: dict[str, "genai.Client"] = {}
_client_cache_lock = threading.Lock()


def _resize_for_api(image: Image.Image, max_dimension: int = IDENTIFY_MAX_DIMENSION) -> Image.Image:
    """Downscale large photos before sending them to the API. Identifying
    a vegetable needs no more than a few hundred pixels of detail, and a
    smaller payload uploads and gets processed noticeably faster."""
    width, height = image.size
    largest_side = max(width, height)
    if largest_side <= max_dimension:
        return image
    scale = max_dimension / float(largest_side)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(new_size, Image.LANCZOS)


def _image_cache_key(image: Image.Image) -> str:
    """Cheap, stable fingerprint of an image's visual content, independent
    of the original file's size/format/EXIF noise."""
    thumb = _resize_for_api(image, max_dimension=128).convert("RGB")
    buf = io.BytesIO()
    thumb.save(buf, format="JPEG", quality=60)
    return hashlib.sha256(buf.getvalue()).hexdigest()


def _cache_get(key: str):
    with _identify_cache_lock:
        return _identify_cache.get(key)


def _cache_set(key: str, value: str):
    with _identify_cache_lock:
        if key not in _identify_cache and len(_identify_cache) >= _IDENTIFY_CACHE_MAX_ENTRIES:
            _identify_cache.pop(next(iter(_identify_cache)))
        _identify_cache[key] = value


def _get_model_name() -> str:
    return os.environ.get("GEMINI_MODEL", GEMINI_MODEL_DEFAULT)


def _get_api_key():
    return os.environ.get("GEMINI_API_KEY", "")


def is_configured() -> bool:
    return bool(_get_api_key())


def _get_client() -> genai.Client:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your environment or a .env file before generating recipes."
        )
    cached = _client_cache.get(api_key)
    if cached is not None:
        return cached
    with _client_cache_lock:
        cached = _client_cache.get(api_key)
        if cached is None:
            cached = genai.Client(api_key=api_key)
            _client_cache[api_key] = cached
        return cached


def _friendly_api_error(e: genai_errors.APIError) -> RuntimeError:
    """Translate the SDK's raw (often huge, JSON-dump) API errors into a
    short, actionable message instead of surfacing the whole payload."""
    code = getattr(e, "code", None)
    if code == 429:
        return RuntimeError(
            "Gemini API quota exceeded for the current model. This usually means "
            "either the free-tier quota for this model is temporarily at 0, or your "
            "Google Cloud project needs a billing account linked (it stays free unless "
            "you exceed the free allowance). Try again in a bit, switch GEMINI_MODEL to "
            "another current model (e.g. gemini-2.5-flash-lite), or check "
            "https://ai.google.dev/gemini-api/docs/rate-limits for current limits."
        )
    if code in (401, 403):
        return RuntimeError(
            "Gemini API key was rejected. Double-check GEMINI_API_KEY is correct and "
            "active in Google AI Studio."
        )
    if code == 404:
        return RuntimeError(
            f'Model "{_get_model_name()}" was not found. It may have been retired — '
            f"set GEMINI_MODEL to a current model name and try again."
        )
    if code and code >= 500:
        return RuntimeError("Gemini's servers are having trouble right now. Please try again shortly.")
    return RuntimeError(f"Gemini API error ({code or 'unknown'}): {getattr(e, 'message', str(e))}")


def identify_vegetable_from_image(image: Image.Image, timeout: float = IDENTIFY_TIMEOUT_SECONDS) -> str:
    """Send an uploaded image to Gemini and return a short vegetable name.

    Fast-path: if this exact photo (by content, not filename) was already
    identified in this server process, the cached answer is returned
    immediately with no network call at all.

    Otherwise the image is downscaled to a small, fast-to-upload size and
    the API call is run in a worker thread with a hard timeout, so a
    stalled connection can never hang the app indefinitely — it surfaces
    as a clear, catchable error instead.
    """
    cache_key = _image_cache_key(image)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    client = _get_client()
    prompt = (
        "Look at this image and identify the single main vegetable shown. "
        "Reply with ONLY the vegetable's common name in English, lowercase, "
        "no punctuation, no extra words. If more than one vegetable is visible, "
        "reply with a comma-separated list of their names."
    )
    api_image = _resize_for_api(image)

    def _call():
        return client.models.generate_content(
            model=_get_model_name(),
            contents=[prompt, api_image],
        )

    future = _gemini_executor.submit(_call)
    try:
        response = future.result(timeout=timeout)
    except FutureTimeoutError:
        future.cancel()
        raise RuntimeError(
            "Vegetable identification timed out. This is usually a slow network "
            "connection rather than the app itself — please try again, or use a "
            "smaller/clearer photo."
        )
    except genai_errors.APIError as e:
        raise _friendly_api_error(e)

    text = (response.text or "").strip().lower()
    text = re.sub(r"[^a-z,\s-]", "", text)
    result = text.strip()
    _cache_set(cache_key, result)
    return result


def _extract_json(text: str) -> dict:
    """Gemini sometimes wraps JSON in markdown fences; strip and parse safely."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())
    cleaned = cleaned.strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


RECIPE_SCHEMA_PROMPT = """
You are a professional chef and nutritionist. Create ONE detailed, delicious recipe
using primarily these vegetables: {vegetables}.
Preferred cuisine style: {cuisine}.
{extra_context_block}
Write ALL text values in the JSON (title, ingredients, instructions, tips,
substitutions, storage, nutrition labels, everything) in {language}. Use
natural, fluent, native-level {language} phrasing — do not leave any value
in English unless {language} is English. Keep the JSON keys themselves
exactly as shown below (do not translate the keys, only the values).

Respond with ONLY valid JSON (no markdown fences, no commentary) matching exactly
this schema:

{{
  "title": "string - appetizing recipe name",
  "cuisine": "string - cuisine type e.g. Italian, Indian, Thai, Mexican, Mediterranean",
  "vegetables": ["list", "of", "main", "vegetables", "used"],
  "servings": "string e.g. 4",
  "prep_time": "string e.g. 15 minutes",
  "cook_time": "string e.g. 25 minutes",
  "difficulty": "string - Easy, Medium, or Hard",
  "calories": "string e.g. 320 kcal per serving",
  "ingredients": ["list of ingredient strings with quantities"],
  "instructions": ["list of numbered step strings, clear and detailed"],
  "nutrition": {{
    "protein": "string e.g. 8g",
    "carbs": "string e.g. 40g",
    "fat": "string e.g. 12g",
    "fiber": "string e.g. 6g"
  }},
  "tips": ["list of chef tips strings"],
  "substitutions": ["list of ingredient substitution suggestion strings"],
  "storage": "string - how to store leftovers and for how long"
}}

Make the recipe realistic, well-balanced, and genuinely cookable at home.
"""


def generate_recipe(
    vegetables: list,
    cuisine: str = "Any",
    language: str = "English",
    extra_context: str = None,
    timeout: float = GENERATE_RECIPE_TIMEOUT_SECONDS,
) -> dict:
    client = _get_client()
    extra_block = ""
    if extra_context and extra_context.strip():
        extra_block = (
            f'Additional request from the user, spoken aloud (respect any '
            f'dietary preference, mood, or style mentioned, e.g. "healthy", '
            f'"quick", "spicy", "for kids"): "{extra_context.strip()}"\n'
        )
    prompt = RECIPE_SCHEMA_PROMPT.format(
        vegetables=", ".join(vegetables) if vegetables else "seasonal vegetables",
        cuisine=cuisine,
        language=language,
        extra_context_block=extra_block,
    )

    def _call():
        return client.models.generate_content(
            model=_get_model_name(),
            contents=prompt,
        )

    future = _gemini_executor.submit(_call)
    try:
        response = future.result(timeout=timeout)
    except FutureTimeoutError:
        future.cancel()
        raise RuntimeError(
            "Recipe generation timed out. This is usually a slow network connection "
            "or a busy model — please try again in a moment."
        )
    except genai_errors.APIError as e:
        raise _friendly_api_error(e)

    text = response.text or "{}"
    try:
        recipe = _extract_json(text)
    except (json.JSONDecodeError, AttributeError) as e:
        raise RuntimeError(f"Could not parse recipe from Gemini response: {e}")
    return recipe
