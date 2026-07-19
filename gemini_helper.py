"""
gemini_helper.py
----------------
Thin wrapper around the Gemini API for:
  1. Identifying a vegetable from an uploaded image.
  2. Generating a full structured recipe (JSON) from a list of vegetables.

The API key is read from the GEMINI_API_KEY environment variable —
never hard-coded, never displayed in the UI.
"""

import os
import json
import re
import google.genai as genai
from PIL import Image

GEMINI_MODEL_NAME = "gemini-flash-lite-latest"


def _get_api_key():
    return os.environ.get("GEMINI_API_KEY", "")


def is_configured() -> bool:
    return bool(_get_api_key())


def _configure():
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your environment or a .env file before generating recipes."
        )
    genai.configure(api_key=api_key)


def identify_vegetable_from_image(image: Image.Image) -> str:
    """Send an uploaded image to Gemini and return a short vegetable name."""
    _configure()
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    prompt = (
        "Look at this image and identify the single main vegetable shown. "
        "Reply with ONLY the vegetable's common name in English, lowercase, "
        "no punctuation, no extra words. If more than one vegetable is visible, "
        "reply with a comma-separated list of their names."
    )
    response = model.generate_content([prompt, image])
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


def generate_recipe(vegetables: list, cuisine: str = "Any", language: str = "English") -> dict:
    """Generate a structured recipe dict from Gemini, written in `language`."""
    _configure()
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    prompt = RECIPE_SCHEMA_PROMPT.format(
        vegetables=", ".join(vegetables) if vegetables else "seasonal vegetables",
        cuisine=cuisine,
        language=language,
    )
    response = model.generate_content(prompt)
    text = response.text or "{}"
    try:
        recipe = _extract_json(text)
    except (json.JSONDecodeError, AttributeError) as e:
        raise RuntimeError(f"Could not parse recipe from Gemini response: {e}")
    return recipe
