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
- **Adding another language**: open `translations.py`, copy the `"en"` block
  inside `TRANSLATIONS`, translate every value (keep the keys and any
  `{placeholder}` tokens exactly as they are), and add an entry for it in
  `LANGUAGES` at the top of the file. Nothing else needs to change — the rest
  of the app only ever calls `t("some_key")`.
