"""
ai_chat.py
-----------
Backend service for "VegiVision AI" -- a conversational assistant scoped to
food, nutrition, recipes, vegetables, and cooking. Kept as its own module
(separate from gemini_helper's recipe/nutrition generation) so the chat
persona, prompt shape, and history-formatting logic stay independent and
reusable, while still sharing the same underlying Gemini client, API-key
handling, and friendly-error translation as the rest of the app -- the key
itself is never read or referenced from app.py or any frontend code, only
from environment variables inside this backend module.
"""

from google.genai import errors as genai_errors

from gemini_helper import _get_client, _get_model_name, is_configured, _friendly_api_error

MAX_HISTORY_TURNS = 12  # how many prior turns to include as context

SYSTEM_PERSONA = """You are "VegiVision AI", a friendly, knowledgeable assistant built into the
VegiVision vegetable recipe app. You help users with:
- Recommending recipes based on vegetables they have
- Healthy meal ideas and nutritional benefits
- Ingredient substitutes and cooking tips
- Vegetable storage methods and seasonal availability
- Vitamins, minerals, and general nutrition questions
- Recipes for weight loss, muscle gain, diabetic-friendly, and children's meals
- Dietary preferences: vegan, vegetarian, gluten-free, etc.
- Helping users understand a vegetable VegiVision just detected for them
- Explaining how to cook unfamiliar vegetables

Stay strictly within food, nutrition, cooking, and vegetables. If asked about
something unrelated, briefly and kindly redirect back to what you can help
with. You are not a doctor -- for medical concerns (e.g. diabetes management),
give general, safe, widely-accepted dietary information and suggest
confirming specifics with a healthcare professional.

Keep answers conversational, warm, and concise (a few short paragraphs or a
short list, not an essay) unless the user asks for more detail. You may use
light markdown (bold, bullet lists) for readability. Reply in {language}.
"""


def _format_history(messages: list) -> str:
    """messages: list of {"role": "user"|"assistant", "content": str}."""
    trimmed = messages[-MAX_HISTORY_TURNS:]
    lines = []
    for m in trimmed:
        speaker = "User" if m["role"] == "user" else "VegiVision AI"
        lines.append(f"{speaker}: {m['content']}")
    return "\n".join(lines)


def chat_with_assistant(
    messages: list,
    new_message: str,
    language: str = "English",
    vegetable_context: str = None,
) -> str:
    """Send the conversation (prior `messages` + `new_message`) to Gemini
    and return the assistant's reply as plain text.

    `messages` is the existing history (list of {"role","content"} dicts,
    NOT including `new_message`). `vegetable_context` is the vegetable
    VegiVision most recently detected for this user, if any, so questions
    like "what can I cook?" resolve without asking which vegetable.
    """
    if not is_configured():
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your environment or a .env file to use VegiVision AI."
        )

    client = _get_client()

    context_note = ""
    if vegetable_context:
        context_note = (
            f"\nContext: the user most recently scanned/selected the vegetable "
            f"\"{vegetable_context}\" in the app. If their next question is vague "
            f"(e.g. \"what can I cook?\", \"is this healthy?\"), assume they mean "
            f"this vegetable unless they clearly ask about something else.\n"
        )

    history_block = _format_history(messages)
    prompt = (
        SYSTEM_PERSONA.format(language=language)
        + context_note
        + ("\nConversation so far:\n" + history_block + "\n" if history_block else "\n")
        + f"\nUser: {new_message}\nVegiVision AI:"
    )

    try:
        response = client.models.generate_content(
            model=_get_model_name(),
            contents=prompt,
        )
    except genai_errors.APIError as e:
        raise _friendly_api_error(e)
    except Exception as e:
        # Network hiccups / timeouts from the underlying HTTP client don't
        # always surface as genai_errors.APIError -- translate generically
        # rather than leaking a raw exception to the UI.
        raise RuntimeError(f"VegiVision AI couldn't respond right now ({e}). Please try again.")

    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("VegiVision AI didn't return a response. Please try again.")
    return text