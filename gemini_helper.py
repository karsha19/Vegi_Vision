import os
import json
import re
from google import genai
from google.genai import errors as genai_errors
from PIL import Image

GEMINI_MODEL_DEFAULT = "gemini-flash-lite-latest"


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
    return genai.Client(api_key=api_key)


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


def identify_vegetable_from_image(image: Image.Image) -> str:
    """Send an uploaded image to Gemini and return a short vegetable name."""
    client = _get_client()
    prompt = (
        "Look at this image and identify the single main vegetable shown. "
        "Reply with ONLY the vegetable's common name in English, lowercase, "
        "no punctuation, no extra words. If more than one vegetable is visible, "
        "reply with a comma-separated list of their names."
    )
    try:
        response = client.models.generate_content(
            model=_get_model_name(),
            contents=[prompt, image],
        )
    except genai_errors.APIError as e:
        raise _friendly_api_error(e)
    text = (response.text or "").strip().lower()
    text = re.sub(r"[^a-z,\s-]", "", text)
    return text.strip()


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


def generate_recipe(vegetables: list, cuisine: str = "Any", language: str = "English", extra_context: str = None) -> dict:
  
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
    try:
        response = client.models.generate_content(
            model=_get_model_name(),
            contents=prompt,
        )
    except genai_errors.APIError as e:
        raise _friendly_api_error(e)
    text = response.text or "{}"
    try:
        recipe = _extract_json(text)
    except (json.JSONDecodeError, AttributeError) as e:
        raise RuntimeError(f"Could not parse recipe from Gemini response: {e}")
    return recipe


NUTRITION_SCHEMA_PROMPT = """
You are a certified nutritionist and dietitian. Build a personalized, safe,
realistic daily nutrition and meal plan for the following person:

- Age: {age}
- Gender: {gender}
- Height: {height} cm
- Weight: {weight} kg
- Activity level: {activity_level}
- Dietary preference: {dietary_preference}
- Allergies / foods to avoid: {allergies}
- Health goal: {health_goal}

Favor vegetable-forward meals where sensible, since this app is a vegetable
recipe journal, but keep the plan nutritionally balanced and realistic for
the stated goal — do not force vegetables where they don't fit.

Write ALL text values in the JSON in {language}. Use natural, fluent,
native-level {language} phrasing. Keep the JSON keys themselves exactly as
shown below (do not translate the keys, only the values).

Respond with ONLY valid JSON (no markdown fences, no commentary) matching
exactly this schema:

{{
  "calorie_target": "string e.g. 2100 kcal/day",
  "macros": {{
    "protein": "string e.g. 110g",
    "carbs": "string e.g. 230g",
    "fat": "string e.g. 65g"
  }},
  "hydration_goal": "string e.g. 2.5 liters/day",
  "meal_plan": {{
    "breakfast": [{{"item": "string - dish/food name", "reason": "string - why this fits their profile"}}],
    "lunch": [{{"item": "string", "reason": "string"}}],
    "snacks": [{{"item": "string", "reason": "string"}}],
    "dinner": [{{"item": "string", "reason": "string"}}]
  }},
  "recommended_vegetables": [
    {{"name": "string - single vegetable name, lowercase", "nutrient": "string e.g. iron, vitamin C, fiber", "reason": "string - why it benefits this person"}}
  ],
  "substitutions": ["list of healthier ingredient-substitution suggestion strings"],
  "weekly_tips": ["list of short, actionable weekly healthy-eating tip strings, at least 5"]
}}

Each meal_plan section should have 1-3 items. recommended_vegetables should
have 4-8 entries. Be specific and practical, not generic. If allergies are
listed, NEVER recommend anything containing them.
"""


def generate_nutrition_plan(profile: dict, language: str = "English") -> dict:
    """Analyze a user's profile with Gemini and return a structured
    nutrition + meal plan dict matching NUTRITION_SCHEMA_PROMPT's schema."""
    client = _get_client()
    prompt = NUTRITION_SCHEMA_PROMPT.format(
        age=profile.get("age", "unspecified"),
        gender=profile.get("gender", "unspecified"),
        height=profile.get("height", "unspecified"),
        weight=profile.get("weight", "unspecified"),
        activity_level=profile.get("activity_level", "unspecified"),
        dietary_preference=profile.get("dietary_preference", "no specific preference"),
        allergies=profile.get("allergies") or "none reported",
        health_goal=profile.get("health_goal", "healthy lifestyle"),
        language=language,
    )
    try:
        response = client.models.generate_content(
            model=_get_model_name(),
            contents=prompt,
        )
    except genai_errors.APIError as e:
        raise _friendly_api_error(e)
    text = response.text or "{}"
    try:
        plan = _extract_json(text)
    except (json.JSONDecodeError, AttributeError) as e:
        raise RuntimeError(f"Could not parse nutrition plan from Gemini response: {e}")
    return plan