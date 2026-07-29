# 🌿 Verdant — Vegetable Recipe Maker

A portfolio-quality Streamlit app that turns vegetables into fully structured,
chef-crafted recipes using the Gemini API — styled as an editorial + bento
grid cooking magazine rather than a default Streamlit dashboard.

## Features

- Secure username/email login & registration (SQLite, PBKDF2-hashed passwords)
- Upload a vegetable photo (Gemini identifies it) or type/select names manually
- Full recipe generation: title, cuisine, ingredients, step-by-step instructions,
  prep/cook time, calories, difficulty, servings, nutrition, chef tips,
  substitutions, and storage guidance
- **Multi-language UI + recipes** — 10 languages (English, Hindi, Chinese,
  Korean, Spanish, French, German, Japanese, Arabic, Portuguese). Switch
  language from the sidebar (or the login screen); every label, button, and
  message updates instantly, and Gemini writes the *recipe content itself*
  in the selected language. Arabic automatically switches the whole layout
  to right-to-left.
- **Voice Recipe Assistant** — a "🎙️ Voice Input" tab next to Upload Image
  and Type/Select, with two modes:
  - **Live Typing** (default): uses the browser's own speech recognition
    to type your words into the box *as you talk*, no stop-and-wait step.
    Requires Chrome or Edge (the browser API isn't available elsewhere);
    on unsupported browsers it shows a clear notice and still accepts
    manual typing in the same box.
  - **Record & Transcribe**: works in any browser — record a clip, then
    it's transcribed once you stop.
  Either way the recognized text lands in an editable field — same
  generation pipeline as typed input, so it saves to SQLite exactly like
  any other recipe. Handles no-speech, unclear-speech, and service-down
  cases with friendly messages.
- Save recipes to your personal journal (SQLite)
- Recipe History with search + cuisine/difficulty filters
- Favorites (heart toggle)
- Profile page with stats (recipes generated, favorites, cuisines explored)
- Dark / Light mode toggle, built on a centralized CSS variable theme system
- Custom CSS: earthy palette, rounded bento cards, soft shadows, Fraunces +
  Manrope typography, hover animations, custom empty states

## Project structure

```
veggie_recipe_maker/
├── app.py              # Streamlit UI, page routing, bento layout
├── db.py                # SQLite schema + all persistence functions
├── gemini_helper.py      # Gemini API calls (image ID + recipe generation)
├── voice_assistant.py     # Speech-to-text: mic capture, transcription, status UI
├── voice_component/       # Custom static Streamlit component: live browser speech-to-text
│   └── index.html
├── styles.py             # All custom CSS as one theme-aware string
├── translations.py       # i18n: all UI strings, one dict per language
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and add your Gemini API key:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env`:
   ```
   GEMINI_API_KEY=your_real_key_here
   ```
   Get a key at https://aistudio.google.com/apikey

3. Run the app:
   ```bash
   streamlit run app.py
   ```

The SQLite database (`veggie_recipes.db`) is created automatically on first run.

## Notes

- Passwords are never stored in plain text — each is hashed with PBKDF2-HMAC-SHA256
  and a unique per-user salt.
- The Gemini API key is read only from the environment; it is never hard-coded
  or displayed in the UI.
- If `GEMINI_API_KEY` isn't set, the app still loads (login/history/favorites/
  profile all work) but recipe generation is disabled with a clear warning.
- **"Quota exceeded" / 429 errors**: this comes from Google, not the app.
  It usually means either the configured model currently has 0 free-tier
  quota for your project, or your Google Cloud project needs a billing
  account linked (Gemini's free tier still requires this step even though
  it stays $0 unless you exceed the free allowance). Google's free-model
  lineup also shifts over time. Set `GEMINI_MODEL` in your `.env` to
  another current model (e.g. `gemini-2.5-flash-lite`) if the default
  stops working, and check
  https://ai.google.dev/gemini-api/docs/rate-limits for current numbers.
- **Adding another language**: open `translations.py`, copy the `"en"` block
  inside `TRANSLATIONS`, translate every value (keep the keys and any
  `{placeholder}` tokens exactly as they are), and add an entry for it in
  `LANGUAGES` at the top of the file. Nothing else needs to change — the rest
  of the app only ever calls `t("some_key")`.
- **Voice input, Live Typing mode** runs entirely in the browser via the
  native Web Speech API — no audio ever leaves the browser for this mode.
  It's implemented as a small dependency-free custom Streamlit component
  (`voice_component/index.html`) that speaks Streamlit's component
  protocol directly over `postMessage`, so it needs no npm/build step.
  Chrome and Edge support this natively; Firefox and Safari currently
  don't, so the component detects that and falls back to a plain,
  manually-typeable box with a notice instead of failing silently.
- **Voice input, Record & Transcribe mode** runs speech-to-text via `SpeechRecognition`'s free Google
  Web Speech API backend, which requires outbound internet access from
  wherever you run the app. The microphone itself is captured in the
  *browser* (via the `streamlit-mic-recorder` component), not on the
  server, so this also works correctly when the app is deployed remotely —
  it does not try to open a microphone device on the server machine. If
  `SpeechRecognition` or `streamlit-mic-recorder` aren't installed, this
  mode shows a friendly notice instead of crashing; typing and image
  upload keep working normally. To swap in Whisper (e.g. for offline
  use) later, only `transcribe_wav_bytes()` in `voice_assistant.py` needs
  to change.
