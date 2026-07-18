"""
app.py
------
Vegetable Recipe Maker — an editorial / bento-grid Streamlit app powered
by Gemini + SQLite. Run with: streamlit run app.py
"""

import os
import base64
import io
import time
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

import db
import gemini_helper as gm
from styles import get_theme_css, FONT_IMPORT

load_dotenv()

st.set_page_config(
    page_title="Verdant — Vegetable Recipe Maker",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

CUISINES = ["Any", "Italian", "Indian", "Thai", "Mexican", "Mediterranean", "Chinese", "American", "French", "Middle Eastern"]


# ------------------------------------------------------------- session ----

def init_session():
    defaults = {
        "user": None,
        "page": "generate",
        "dark_mode": False,
        "auth_mode": "login",
        "current_recipe": None,
        "selected_recipe_id": None,
        "veg_image": None,
        "detected_veg": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


def inject_css():
    st.markdown(FONT_IMPORT, unsafe_allow_html=True)
    st.markdown(get_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)


inject_css()


# ------------------------------------------------------------ helpers -----

def image_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def b64_to_image_html(b64: str, height="180px") -> str:
    if not b64:
        return ""
    return f'<img src="data:image/png;base64,{b64}" style="width:100%;height:{height};object-fit:cover;border-radius:16px;margin-bottom:0.7rem;" />'


def empty_state(icon: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="icon">{icon}</div>
            <div class="title">{title}</div>
            <div>{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


from contextlib import contextmanager


@contextmanager
def card(accent=False):
    """A real bento-style card.

    Uses st.container(border=True) so everything written inside the
    `with` block is *actually* nested inside the card in the DOM (unlike
    hand-rolling a <div> across two separate st.markdown() calls, which
    Streamlit does not nest and which renders as an empty floating pill).
    A tiny hidden marker lets styles.py find and restyle this exact
    container via a CSS :has() selector.
    """
    with st.container(border=True):
        tag_class = "card-tag-accent" if accent else "card-tag"
        st.markdown(f'<div class="{tag_class}"></div>', unsafe_allow_html=True)
        yield


@contextmanager
def mini_card():
    """A smaller card used for recipe grid tiles in History / Favorites."""
    with st.container(border=True):
        st.markdown('<div class="card-tag-mini"></div>', unsafe_allow_html=True)
        yield


# --------------------------------------------------------------- auth -----

def auth_screen():
    st.markdown(
        """
        <div style="text-align:center; margin-top:2.5rem; margin-bottom:1rem;">
            <div style="font-family:'Fraunces',serif; font-size:2.4rem; font-weight:700;">🌿 Verdant</div>
            <div style="color:var(--text-muted); letter-spacing:0.12em; text-transform:uppercase; font-size:0.78rem;">
                A quiet little kitchen journal, powered by AI
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_center, col_b = st.columns([1, 1.2, 1])
    with col_center:
        with card(accent=True):
            tabs = st.tabs(["Sign In", "Create Account"])

            with tabs[0]:
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button("Sign In →")
                    if submitted:
                        if not username or not password:
                            st.error("Please fill in both fields.")
                        else:
                            with st.spinner("Checking your credentials..."):
                                time.sleep(0.4)
                                user = db.verify_user(username, password)
                            if user:
                                st.session_state.user = user
                                st.success(f"Welcome back, {user['username']}!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Invalid username or password.")

            with tabs[1]:
                with st.form("register_form"):
                    new_username = st.text_input("Choose a username")
                    new_email = st.text_input("Email")
                    new_password = st.text_input("Choose a password", type="password")
                    confirm_password = st.text_input("Confirm password", type="password")
                    submitted = st.form_submit_button("Create Account →")
                    if submitted:
                        if not all([new_username, new_email, new_password]):
                            st.error("Please fill in all fields.")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match.")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters.")
                        else:
                            with st.spinner("Setting up your account..."):
                                time.sleep(0.4)
                                ok, msg = db.create_user(new_username, new_email, new_password)
                            if ok:
                                st.success(msg + " Please sign in.")
                            else:
                                st.error(msg)


# ------------------------------------------------------------ sidebar -----

def sidebar():
    with st.sidebar:
        st.markdown('<div class="brand-mark">🌿 Verdant</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-sub">Vegetable Recipe Journal</div>', unsafe_allow_html=True)

        nav_items = [
            ("generate", "✨  Generate Recipe"),
            ("history", "📖  Recipe History"),
            ("favorites", "❤️  Favorites"),
            ("profile", "🪴  Profile"),
        ]
        for key, label in nav_items:
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)

        mode_label = "☀️  Light Mode" if st.session_state.dark_mode else "🌙  Dark Mode"
        if st.button(mode_label, key="toggle_theme", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="font-size:0.85rem; color:var(--text-secondary);">
                Signed in as<br><b>{st.session_state.user['username']}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("↩  Log Out", key="logout_btn", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "generate"
            st.rerun()

        if not gm.is_configured():
            st.markdown(
                '<div style="margin-top:1rem; font-size:0.75rem; color:#b3552e;">'
                '⚠ GEMINI_API_KEY not set — recipe generation is disabled until it is configured.'
                '</div>',
                unsafe_allow_html=True,
            )


# --------------------------------------------------------- recipe card ----

def render_recipe(recipe: dict, recipe_id=None, user_id=None, show_favorite=True):
    is_fav = db.is_favorite(user_id, recipe_id) if (recipe_id and user_id) else False

    with card():
        header_col, fav_col = st.columns([5, 1])
        with header_col:
            st.markdown(f'<span class="eyebrow">{recipe.get("cuisine","")} · {recipe.get("difficulty","")}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="recipe-title">{recipe.get("title","Untitled Recipe")}</div>', unsafe_allow_html=True)
        with fav_col:
            if show_favorite and recipe_id and user_id:
                fav_icon = "💚" if is_fav else "🤍"
                if st.button(fav_icon, key=f"fav_{recipe_id}"):
                    db.toggle_favorite(user_id, recipe_id)
                    st.rerun()

        pills = []
        for label, key in [("⏱ Prep", "prep_time"), ("🔥 Cook", "cook_time"), ("🍽 Serves", "servings"), ("⚡ Calories", "calories")]:
            val = recipe.get(key)
            if val:
                pills.append(f'<span class="pill">{label}: {val}</span>')
        st.markdown("".join(pills), unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.3])

    with col1:
        with card():
            st.markdown('<span class="eyebrow">🥕 Ingredients</span>', unsafe_allow_html=True)
            ingredients = recipe.get("ingredients", [])
            if ingredients:
                rows = "".join(f'<div class="ingredient-row">• {i}</div>' for i in ingredients)
                st.markdown(rows, unsafe_allow_html=True)
            else:
                st.caption("No ingredients listed.")

        nutrition = recipe.get("nutrition", {})
        if nutrition:
            with card():
                st.markdown('<span class="eyebrow">📊 Nutrition (per serving)</span>', unsafe_allow_html=True)
                pills = "".join(f'<span class="pill brown">{k.title()}: {v}</span>' for k, v in nutrition.items())
                st.markdown(pills, unsafe_allow_html=True)

        storage = recipe.get("storage", "")
        if storage:
            with card():
                st.markdown('<span class="eyebrow">🧊 Storage</span>', unsafe_allow_html=True)
                st.markdown(f'<div style="color:var(--text-secondary); font-size:0.9rem;">{storage}</div>', unsafe_allow_html=True)

    with col2:
        with card():
            st.markdown('<span class="eyebrow">👩‍🍳 Instructions</span>', unsafe_allow_html=True)
            steps = recipe.get("instructions", [])
            for idx, step in enumerate(steps, start=1):
                st.markdown(
                    f"""
                    <div class="step-row">
                        <div class="step-num">{idx}</div>
                        <div class="step-text">{step}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        tips = recipe.get("tips", [])
        subs = recipe.get("substitutions", [])
        if tips or subs:
            with card():
                if tips:
                    st.markdown('<span class="eyebrow">💡 Chef Tips</span>', unsafe_allow_html=True)
                    for t in tips:
                        st.markdown(f'<div class="step-text">• {t}</div>', unsafe_allow_html=True)
                if subs:
                    st.markdown('<span class="eyebrow" style="margin-top:0.8rem;">🔄 Substitutions</span>', unsafe_allow_html=True)
                    for s in subs:
                        st.markdown(f'<div class="step-text">• {s}</div>', unsafe_allow_html=True)


# --------------------------------------------------------- generate page --

def page_generate():
    st.markdown(
        """
        <div class="top-header">
            <div>
                <div class="kicker">Today's Craving</div>
                <h1>Generate a Recipe</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_input, col_preview = st.columns([1.3, 1])

    with col_input:
        with card():
            st.markdown('<span class="eyebrow">🥦 Choose Your Vegetables</span>', unsafe_allow_html=True)

            tab_upload, tab_manual = st.tabs(["📷 Upload Image", "⌨️ Type / Select"])

            with tab_upload:
                uploaded = st.file_uploader("Upload a photo of a vegetable", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
                if uploaded:
                    img = Image.open(uploaded).convert("RGB")
                    st.session_state.veg_image = img
                    st.image(img, caption="Uploaded image", use_container_width=True)
                    if st.button("🔍 Identify Vegetable", key="identify_btn"):
                        if not gm.is_configured():
                            st.error("Gemini API key not configured.")
                        else:
                            with st.spinner("Looking closely at your vegetable..."):
                                try:
                                    detected = gm.identify_vegetable_from_image(img)
                                    st.session_state.detected_veg = detected
                                    st.success(f"Detected: **{detected}**")
                                except Exception as e:
                                    st.error(f"Couldn't identify the image: {e}")

            with tab_manual:
                manual_input = st.text_input(
                    "Vegetable names (comma separated)",
                    value=st.session_state.detected_veg,
                    placeholder="e.g. spinach, tomato, bell pepper",
                )
                common_veggies = st.multiselect(
                    "...or pick from common vegetables",
                    ["Potato", "Spinach", "Tomato", "Carrot", "Broccoli", "Cauliflower", "Bell Pepper",
                     "Zucchini", "Eggplant", "Onion", "Mushroom", "Peas", "Pumpkin", "Okra", "Cabbage"],
                )
                if manual_input:
                    st.session_state.detected_veg = manual_input

            st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
            cuisine_choice = st.selectbox("Preferred cuisine style", CUISINES)

            final_veggies = []
            if st.session_state.detected_veg:
                final_veggies.extend([v.strip() for v in st.session_state.detected_veg.split(",") if v.strip()])
            if "common_veggies" in dir() and common_veggies:
                final_veggies.extend(common_veggies)
            final_veggies = list(dict.fromkeys(final_veggies))  # dedupe, preserve order

            if final_veggies:
                st.markdown("".join(f'<span class="pill green">{v}</span>' for v in final_veggies), unsafe_allow_html=True)

            generate_clicked = st.button("✨ Generate Recipe", key="generate_btn", use_container_width=True)

    with col_preview:
        with card(accent=True):
            st.markdown('<span class="eyebrow">🍽 What You\'ll Get</span>', unsafe_allow_html=True)
            st.markdown(
                """
                <div style="color:var(--text-secondary); font-size:0.9rem; line-height:1.7;">
                A complete, chef-crafted recipe card including ingredients, step-by-step
                instructions, prep &amp; cook time, calories, difficulty, nutrition facts,
                chef tips, ingredient substitutions, and storage guidance — saved straight
                to your personal recipe journal.
                </div>
                """,
                unsafe_allow_html=True,
            )

    if generate_clicked:
        if not final_veggies:
            st.error("Please upload an image or enter/select at least one vegetable.")
        elif not gm.is_configured():
            st.error("GEMINI_API_KEY is not configured. Set it in your environment to generate recipes.")
        else:
            with st.spinner("Simmering up your recipe..."):
                try:
                    recipe = gm.generate_recipe(final_veggies, cuisine_choice)
                    st.session_state.current_recipe = recipe
                    st.success("Your recipe is ready!")
                except Exception as e:
                    st.error(f"Recipe generation failed: {e}")

    if st.session_state.current_recipe:
        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
        render_recipe(st.session_state.current_recipe, show_favorite=False)

        save_col, discard_col = st.columns([1, 1])
        with save_col:
            if st.button("💾 Save to Journal", key="save_recipe_btn", use_container_width=True):
                recipe_to_save = dict(st.session_state.current_recipe)
                if st.session_state.veg_image is not None:
                    recipe_to_save["image_data"] = image_to_b64(st.session_state.veg_image)
                rid = db.save_recipe(st.session_state.user["id"], recipe_to_save)
                st.success("Saved to your recipe history! 🎉")
                st.session_state.current_recipe = None
                st.session_state.veg_image = None
                st.session_state.detected_veg = ""
                time.sleep(0.6)
                st.rerun()
        with discard_col:
            if st.button("✕ Discard", key="discard_recipe_btn", use_container_width=True):
                st.session_state.current_recipe = None
                st.rerun()
    else:
        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
        empty_state("🍲", "No recipe yet", "Upload a vegetable photo or type a few names, then hit Generate.")


# ----------------------------------------------------------- history page -

def page_history():
    st.markdown(
        """
        <div class="top-header">
            <div><div class="kicker">Your Journal</div><h1>Recipe History</h1></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.session_state.user["id"]
    cuisines = ["All"] + db.get_distinct_cuisines(user_id)

    fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
    with fcol1:
        search = st.text_input("🔍 Search by title or vegetable", key="history_search")
    with fcol2:
        cuisine_filter = st.selectbox("Cuisine", cuisines, key="history_cuisine")
    with fcol3:
        difficulty_filter = st.selectbox("Difficulty", ["All", "Easy", "Medium", "Hard"], key="history_difficulty")

    recipes = db.get_user_recipes(user_id, search, cuisine_filter, difficulty_filter)

    if not recipes:
        empty_state("📭", "No recipes found", "Try a different search or generate your first recipe.")
        return

    if st.session_state.selected_recipe_id:
        selected = next((r for r in recipes if r["id"] == st.session_state.selected_recipe_id), None) or db.get_recipe(st.session_state.selected_recipe_id)
        if selected:
            if st.button("← Back to all recipes", key="back_btn"):
                st.session_state.selected_recipe_id = None
                st.rerun()
            render_recipe(selected, recipe_id=selected["id"], user_id=user_id)
            if st.button("🗑 Delete Recipe", key="delete_btn"):
                db.delete_recipe(selected["id"], user_id)
                st.session_state.selected_recipe_id = None
                st.success("Recipe deleted.")
                time.sleep(0.4)
                st.rerun()
        return

    # bento grid of recipe cards, 3 per row
    cols = st.columns(3)
    for idx, r in enumerate(recipes):
        with cols[idx % 3]:
            with mini_card():
                if r.get("image_data"):
                    st.markdown(b64_to_image_html(r["image_data"]), unsafe_allow_html=True)
                st.markdown(f'<span class="eyebrow">{r.get("cuisine","")}</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="recipe-title" style="font-size:1.1rem;">{r["title"]}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<span class="pill">{r.get("difficulty","")}</span>'
                    f'<span class="pill">⏱ {r.get("prep_time","")}</span>',
                    unsafe_allow_html=True,
                )
                if st.button("View Recipe →", key=f"view_{r['id']}", use_container_width=True):
                    st.session_state.selected_recipe_id = r["id"]
                    st.rerun()


# ---------------------------------------------------------- favorites page

def page_favorites():
    st.markdown(
        """
        <div class="top-header">
            <div><div class="kicker">Loved & Saved</div><h1>Favorite Recipes</h1></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    user_id = st.session_state.user["id"]
    favs = db.get_favorite_recipes(user_id)

    if not favs:
        empty_state("💚", "No favorites yet", "Tap the heart on any recipe in your history to save it here.")
        return

    cols = st.columns(3)
    for idx, r in enumerate(favs):
        with cols[idx % 3]:
            with mini_card():
                if r.get("image_data"):
                    st.markdown(b64_to_image_html(r["image_data"]), unsafe_allow_html=True)
                st.markdown(f'<span class="eyebrow">{r.get("cuisine","")}</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="recipe-title" style="font-size:1.1rem;">{r["title"]}</div>', unsafe_allow_html=True)
                if st.button("View Recipe →", key=f"favview_{r['id']}", use_container_width=True):
                    st.session_state.page = "history"
                    st.session_state.selected_recipe_id = r["id"]
                    st.rerun()


# ------------------------------------------------------------ profile page

def page_profile():
    user = st.session_state.user
    stats = db.get_user_stats(user["id"])

    st.markdown(
        """
        <div class="top-header">
            <div><div class="kicker">Your Kitchen</div><h1>Profile</h1></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_col1, top_col2 = st.columns([1, 3])
    with top_col1:
        with card():
            initials = user["username"][:2].upper()
            st.markdown(f'<div class="avatar-badge">{initials}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="margin-top:0.8rem; font-weight:700; font-size:1.1rem; color:var(--text-primary);">{user["username"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color:var(--text-muted); font-size:0.85rem;">{user["email"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color:var(--text-muted); font-size:0.78rem; margin-top:0.4rem;">Member since {user["created_at"][:10]}</div>', unsafe_allow_html=True)

    with top_col2:
        s1, s2, s3 = st.columns(3)
        stat_data = [
            (s1, stats["total_recipes"], "Recipes Generated"),
            (s2, stats["total_favorites"], "Favorites Saved"),
            (s3, stats["unique_cuisines"], "Cuisines Explored"),
        ]
        for col, num, label in stat_data:
            with col:
                with card(accent=True):
                    st.markdown(f'<div class="stat-num">{num}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="stat-label">{label}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
    st.markdown('<span class="eyebrow">🕰 Recently Generated</span>', unsafe_allow_html=True)
    recent = db.get_user_recipes(user["id"])[:5]
    if not recent:
        empty_state("🌱", "Nothing here yet", "Your generated recipes will show up in this timeline.")
    else:
        for r in recent:
            st.markdown(
                f"""
                <div class="recipe-card-mini" style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-weight:700;">{r['title']}</div>
                        <div style="color:var(--text-muted); font-size:0.8rem;">{r.get('cuisine','')} · {r['created_at'][:10]}</div>
                    </div>
                    <div class="pill">{r.get('difficulty','')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ------------------------------------------------------------------ main --

def main():
    if st.session_state.user is None:
        auth_screen()
        return

    sidebar()

    page = st.session_state.page
    if page == "generate":
        page_generate()
    elif page == "history":
        page_history()
    elif page == "favorites":
        page_favorites()
    elif page == "profile":
        page_profile()


if __name__ == "__main__":
    main()
