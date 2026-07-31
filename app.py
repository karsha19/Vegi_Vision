import os
import base64
import io
import time
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

import db
import gemini_helper as gm
import voice_assistant as va
from styles import get_theme_css, FONT_IMPORT
from translations import t, LANGUAGES, DEFAULT_LANGUAGE, current_language_meta

load_dotenv()

st.set_page_config(
    page_title="VegiVision — Vegetable Recipe Maker",
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
        "last_generated_recipe_id": None,
        "selected_recipe_id": None,
        "veg_image": None,
        "detected_veg": "",
        "language": DEFAULT_LANGUAGE,
        "sidebar_collapsed": False,
        "profile_edit_mode": False,
        "profile_confirm_delete": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


def inject_css():
    st.markdown(FONT_IMPORT, unsafe_allow_html=True)
    # Defensive: if styles.py on disk is an older copy that doesn't accept
    # sidebar_collapsed yet, fall back to the 1-argument call instead of
    # crashing with a TypeError. This can happen if the project's files
    # get out of sync (e.g. only app.py was updated, not styles.py).
    try:
        css = get_theme_css(st.session_state.dark_mode, st.session_state.sidebar_collapsed)
    except TypeError:
        css = get_theme_css(st.session_state.dark_mode)
        st.warning(
            "Your styles.py file looks outdated (it doesn't support the collapsible "
            "sidebar yet) — the app will still run, but please replace styles.py with "
            "the latest version so the sidebar collapse/expand feature works.",
            icon="⚠️",
        )
    st.markdown(css, unsafe_allow_html=True)
    if current_language_meta().get("rtl"):
        st.markdown(
            """<style>
            .stApp, .stApp * { direction: rtl; }
            div[data-testid="stSidebar"] .stButton > button:hover { transform: translateX(-3px); }
            </style>""",
            unsafe_allow_html=True,
        )


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


def profile_avatar_html(user: dict) -> str:
    """Large circular avatar for the Profile page: the user's uploaded
    picture if present, otherwise their initials on a soft brand-green
    background — same fallback style as the small avatar-badge used
    elsewhere."""
    pic = user.get("profile_picture") or ""
    if pic:
        inner = f'<img src="data:image/png;base64,{pic}" />'
    else:
        name_source = (user.get("display_name") or user.get("username") or "?").strip()
        initials = name_source[:2].upper() if name_source else "?"
        inner = initials
    return f'<div class="profile-avatar-large">{inner}</div>'


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
    # Hidden marker: everything else in this function renders as normal
    # Streamlit content, but this single tag lets styles.py detect "we're
    # on the signed-out screen" via a CSS :has() selector and apply the
    # decorative background + leaf motif only here — nowhere else in the
    # app is affected.
    st.markdown('<div class="auth-page-marker"></div>', unsafe_allow_html=True)

    top_l, top_r = st.columns([4, 1])
    with top_r:
        toggle_col, lang_col = st.columns([1, 2.4])
        with toggle_col:
            theme_icon = "☀️" if st.session_state.dark_mode else "🌙"
            if st.button(theme_icon, key="auth_theme_toggle", help=t("theme_light") if st.session_state.dark_mode else t("theme_dark")):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
        with lang_col:
            st.markdown('<div class="auth-lang-select">', unsafe_allow_html=True)
            lang_codes = list(LANGUAGES.keys())
            lang_labels = [f"{LANGUAGES[c]['flag']} {LANGUAGES[c]['name']}" for c in lang_codes]
            current_idx = lang_codes.index(st.session_state.language)
            chosen = st.selectbox(
                t("language_label"), lang_labels, index=current_idx, key="auth_lang_select", label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            chosen_code = lang_codes[lang_labels.index(chosen)]
            if chosen_code != st.session_state.language:
                st.session_state.language = chosen_code
                st.rerun()

    st.markdown(
        f"""
        <div class="auth-brand-wrap">
            <div class="auth-brand-icon-chip">🌿</div>
            <div class="auth-brand-name">{t('app_brand')}</div>
            <div class="auth-brand-divider"></div>
            <div class="auth-brand-tagline">{t('auth_subtitle')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_center, col_b = st.columns([1, 1.2, 1])
    with col_center:
        with st.container(border=True):
            st.markdown('<div class="auth-card-tag"></div>', unsafe_allow_html=True)
            tabs = st.tabs([t("tab_signin"), t("tab_register")])

            with tabs[0]:
                with st.form("login_form"):
                    username = st.text_input(t("label_username"))
                    password = st.text_input(t("label_password"), type="password")
                    submitted = st.form_submit_button(t("btn_signin"))
                    if submitted:
                        if not username or not password:
                            st.error(t("err_fill_both"))
                        else:
                            with st.spinner(t("msg_checking")):
                                time.sleep(0.4)
                                user = db.verify_user(username, password)
                            if user:
                                st.session_state.user = user
                                st.success(t("msg_welcome_back", name=user["username"]))
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(t("err_invalid_creds"))

            with tabs[1]:
                with st.form("register_form"):
                    new_username = st.text_input(t("label_choose_username"))
                    new_email = st.text_input(t("label_email"))
                    new_password = st.text_input(t("label_choose_password"), type="password")
                    confirm_password = st.text_input(t("label_confirm_password"), type="password")
                    submitted = st.form_submit_button(t("btn_register"))
                    if submitted:
                        if not all([new_username, new_email, new_password]):
                            st.error(t("err_fill_all"))
                        elif new_password != confirm_password:
                            st.error(t("err_pw_mismatch"))
                        elif len(new_password) < 6:
                            st.error(t("err_pw_short"))
                        else:
                            with st.spinner(t("msg_setting_up")):
                                time.sleep(0.4)
                                ok, msg = db.create_user(new_username, new_email, new_password)
                            if ok:
                                st.success(t("msg_account_created"))
                            else:
                                st.error(t("err_username_exists"))


# ------------------------------------------------------------ sidebar -----

def _toggle_sidebar():
    st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed


def sidebar():
    collapsed = st.session_state.sidebar_collapsed

    with st.sidebar:
        toggle_icon = "☰" if collapsed else "✕"
        toggle_help = t("sidebar_maximize") if collapsed else t("sidebar_minimize")
        st.button(toggle_icon, key="sidebar_toggle", help=toggle_help, on_click=_toggle_sidebar)

        if collapsed:
            st.markdown('<div class="brand-mark brand-mark-collapsed">🌿</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="brand-mark">🌿 {t("app_brand")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="brand-sub">{t("app_tagline")}</div>', unsafe_allow_html=True)

        nav_items = [
            ("generate", "✨", "nav_generate"),
            ("history", "📖", "nav_history"),
            ("favorites", "❤️", "nav_favorites"),
            ("profile", "🪴", "nav_profile"),
        ]
        for key, icon, label_key in nav_items:
            if not collapsed and st.session_state.page == key:
                st.markdown('<div class="nav-active-marker"></div>', unsafe_allow_html=True)
            label = icon if collapsed else f"{icon}  {t(label_key)}"
            if st.button(label, key=f"nav_{key}", use_container_width=True, help=t(label_key) if collapsed else None):
                st.session_state.page = key
                st.rerun()

        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)

        theme_icon = "☀️" if st.session_state.dark_mode else "🌙"
        theme_text = t("theme_light") if st.session_state.dark_mode else t("theme_dark")
        theme_label = theme_icon if collapsed else f"{theme_icon}  {theme_text}"
        if st.button(theme_label, key="toggle_theme", use_container_width=True, help=theme_text if collapsed else None):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)

        lang_codes = list(LANGUAGES.keys())
        current_idx = lang_codes.index(st.session_state.language)
        if collapsed:
            lang_labels = [LANGUAGES[c]["flag"] for c in lang_codes]
        else:
            st.markdown(f'<div style="font-size:0.8rem; font-weight:600; color:var(--text-secondary); margin-bottom:0.3rem;">🌐 {t("language_label")}</div>', unsafe_allow_html=True)
            lang_labels = [f"{LANGUAGES[c]['flag']} {LANGUAGES[c]['name']}" for c in lang_codes]
        chosen = st.selectbox(
            t("language_label"), lang_labels, index=current_idx, key="sidebar_lang_select", label_visibility="collapsed"
        )
        chosen_code = lang_codes[lang_labels.index(chosen)]
        if chosen_code != st.session_state.language:
            st.session_state.language = chosen_code
            st.rerun()

        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)

        if not collapsed:
            st.markdown(
                f"""
                <div style="font-size:0.85rem; color:var(--text-secondary);">
                    {t('signed_in_as')}<br><b>{st.session_state.user['username']}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

        logout_label = "↩" if collapsed else f"↩  {t('logout')}"
        if st.button(logout_label, key="logout_btn", use_container_width=True, help=t("logout") if collapsed else None):
            st.session_state.user = None
            st.session_state.page = "generate"
            st.rerun()

        if not gm.is_configured() and not collapsed:
            st.markdown(
                f'<div style="margin-top:1rem; font-size:0.75rem; color:var(--error);">'
                f'⚠ {t("api_key_warning")}'
                f'</div>',
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
        for label_key, key in [("label_prep", "prep_time"), ("label_cook", "cook_time"), ("label_serves", "servings"), ("label_calories", "calories")]:
            val = recipe.get(key)
            if val:
                pills.append(f'<span class="pill">{t(label_key)}: {val}</span>')
        st.markdown("".join(pills), unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.3])

    with col1:
        with card():
            st.markdown(f'<span class="eyebrow">🥕 {t("eyebrow_ingredients")}</span>', unsafe_allow_html=True)
            ingredients = recipe.get("ingredients", [])
            if ingredients:
                rows = "".join(f'<div class="ingredient-row">• {i}</div>' for i in ingredients)
                st.markdown(rows, unsafe_allow_html=True)
            else:
                st.caption(t("no_ingredients"))

        nutrition = recipe.get("nutrition", {})
        if nutrition:
            with card():
                st.markdown(f'<span class="eyebrow">📊 {t("eyebrow_nutrition")}</span>', unsafe_allow_html=True)
                pills = "".join(f'<span class="pill brown">{k.title()}: {v}</span>' for k, v in nutrition.items())
                st.markdown(pills, unsafe_allow_html=True)

        storage = recipe.get("storage", "")
        if storage:
            with card():
                st.markdown(f'<span class="eyebrow">🧊 {t("eyebrow_storage")}</span>', unsafe_allow_html=True)
                st.markdown(f'<div style="color:var(--text-secondary); font-size:0.9rem;">{storage}</div>', unsafe_allow_html=True)

    with col2:
        with card():
            st.markdown(f'<span class="eyebrow">👩‍🍳 {t("eyebrow_instructions")}</span>', unsafe_allow_html=True)
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
                    st.markdown(f'<span class="eyebrow">💡 {t("eyebrow_tips")}</span>', unsafe_allow_html=True)
                    for tip in tips:
                        st.markdown(f'<div class="step-text">• {tip}</div>', unsafe_allow_html=True)
                if subs:
                    st.markdown(f'<span class="eyebrow" style="margin-top:0.8rem;">🔄 {t("eyebrow_substitutions")}</span>', unsafe_allow_html=True)
                    for s in subs:
                        st.markdown(f'<div class="step-text">• {s}</div>', unsafe_allow_html=True)


# --------------------------------------------------------- generate page --

def page_generate():
    st.markdown(
        f"""
        <div class="top-header">
            <div>
                <div class="kicker">{t('kicker_today')}</div>
                <h1>{t('title_generate')}</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_input, col_preview = st.columns([1.3, 1])

    with col_input:
        with card():
            st.markdown(f'<span class="eyebrow">🥦 {t("eyebrow_choose_veg")}</span>', unsafe_allow_html=True)

            tab_upload, tab_manual, tab_voice = st.tabs([
                f"📷 {t('tab_upload_image')}",
                f"⌨️ {t('tab_type_select')}",
                f"🎙️ {t('tab_voice_input')}",
            ])

            with tab_upload:
                upload_mode = st.radio(
                    t("upload_mode_label"),
                    options=["file", "camera"],
                    format_func=lambda m: t("upload_mode_file") if m == "file" else t("upload_mode_camera"),
                    horizontal=True,
                    label_visibility="collapsed",
                    key="upload_mode",
                )

                img_source = None
                if upload_mode == "file":
                    img_source = st.file_uploader(t("upload_label"), type=["jpg", "jpeg", "png"], label_visibility="collapsed")
                else:
                    img_source = st.camera_input(t("camera_label"), label_visibility="collapsed")

                if img_source:
                    img = Image.open(img_source).convert("RGB")
                    st.session_state.veg_image = img
                    st.image(img, caption=t("caption_uploaded"), use_container_width=True)
                    if st.button(f"🔍 {t('btn_identify')}", key="identify_btn"):
                        if not gm.is_configured():
                            st.error(t("err_gemini_not_configured"))
                        else:
                            with st.spinner(t("msg_looking")):
                                try:
                                    detected = gm.identify_vegetable_from_image(img)
                                    st.session_state.detected_veg = detected
                                    st.success(t("msg_detected", name=detected))
                                except Exception as e:
                                    st.error(t("err_identify_failed", error=e))

            with tab_manual:
                manual_input = st.text_input(
                    t("label_manual_veg"),
                    value=st.session_state.detected_veg,
                    placeholder=t("placeholder_manual_veg"),
                )
                common_veggies = st.multiselect(
                    t("label_pick_common"),
                    ["Potato", "Spinach", "Tomato", "Carrot", "Broccoli", "Cauliflower", "Bell Pepper",
                     "Zucchini", "Eggplant", "Onion", "Mushroom", "Peas", "Pumpkin", "Okra", "Cabbage"],
                )
                if manual_input:
                    st.session_state.detected_veg = manual_input

            with tab_voice:
                va.render_voice_input()

            st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
            cuisine_choice = st.selectbox(t("label_cuisine_style"), CUISINES)

            final_veggies = []
            if st.session_state.detected_veg:
                final_veggies.extend([v.strip() for v in st.session_state.detected_veg.split(",") if v.strip()])
            if "common_veggies" in dir() and common_veggies:
                final_veggies.extend(common_veggies)
            final_veggies = list(dict.fromkeys(final_veggies))  # dedupe, preserve order

            if final_veggies:
                st.markdown("".join(f'<span class="pill green">{v}</span>' for v in final_veggies), unsafe_allow_html=True)

            generate_clicked = st.button(f"✨ {t('btn_generate')}", key="generate_btn", use_container_width=True)

    with col_preview:
        with card(accent=True):
            st.markdown(f'<span class="eyebrow">🍽 {t("eyebrow_what_get")}</span>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div style="color:var(--text-secondary); font-size:0.9rem; line-height:1.7;">
                {t('desc_what_get')}
                </div>
                """,
                unsafe_allow_html=True,
            )

    if generate_clicked:
        if not final_veggies:
            st.error(t("err_no_veggies"))
        elif not gm.is_configured():
            st.error(t("err_gemini_not_configured2"))
        else:
            with st.spinner(t("msg_simmering")):
                try:
                    recipe_language = LANGUAGES[st.session_state.language]["gemini_name"]
                    voice_context = st.session_state.get("voice_raw_text") or None
                    recipe = gm.generate_recipe(final_veggies, cuisine_choice, recipe_language, extra_context=voice_context)
                    st.session_state.current_recipe = recipe

                    # Automatically persist every generated recipe to the user's
                    # History — no manual "save" action required. Works for
                    # recipes generated from an uploaded image, a live camera
                    # capture, typed/selected vegetables, or voice input, since
                    # veg_image is populated identically in all of those paths.
                    recipe_to_save = dict(recipe)
                    if st.session_state.veg_image is not None:
                        recipe_to_save["image_data"] = image_to_b64(st.session_state.veg_image)
                    new_recipe_id = db.save_recipe(st.session_state.user["id"], recipe_to_save)
                    st.session_state.last_generated_recipe_id = new_recipe_id

                    st.success(t("msg_saved"))
                except Exception as e:
                    st.error(t("err_recipe_failed", error=e))

    if st.session_state.current_recipe:
        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
        render_recipe(st.session_state.current_recipe, show_favorite=False)

        fav_col, discard_col = st.columns([1, 1])
        with fav_col:
            gen_recipe_id = st.session_state.last_generated_recipe_id
            user_id = st.session_state.user["id"]
            already_fav = db.is_favorite(user_id, gen_recipe_id) if gen_recipe_id else False

            if already_fav:
                st.button(
                    "💚 Added to Favorites",
                    key="fav_generated_btn",
                    use_container_width=True,
                    disabled=True,
                )
                st.caption("This recipe is already in your Favorites.")
            else:
                if st.button(
                    "❤️ Add to Favorites",
                    key="fav_generated_btn",
                    use_container_width=True,
                    disabled=gen_recipe_id is None,
                ):
                    # Recipe is already in History (auto-saved on generation);
                    # this only marks it as a favorite, it never inserts a
                    # second history/recipe row.
                    db.toggle_favorite(user_id, gen_recipe_id)
                    st.success("Recipe added to Favorites successfully!")
                    st.rerun()
        with discard_col:
            if st.button(f"✕ {t('btn_discard')}", key="discard_recipe_btn", use_container_width=True):
                st.session_state.current_recipe = None
                st.session_state.last_generated_recipe_id = None
                va.reset_voice_state()
                st.rerun()
    else:
        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
        empty_state("🍲", t("empty_no_recipe_title"), t("empty_no_recipe_sub"))


# ----------------------------------------------------------- history page -

def page_history():
    st.markdown(
        f"""
        <div class="top-header">
            <div><div class="kicker">{t('kicker_journal')}</div><h1>{t('title_history')}</h1></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.session_state.user["id"]
    cuisines = [t("option_all")] + db.get_distinct_cuisines(user_id)

    fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
    with fcol1:
        search = st.text_input(f"🔍 {t('search_placeholder')}", key="history_search")
    with fcol2:
        cuisine_filter = st.selectbox(t("label_cuisine_filter"), cuisines, key="history_cuisine")
    with fcol3:
        difficulty_filter = st.selectbox(t("label_difficulty_filter"), [t("option_all"), "Easy", "Medium", "Hard"], key="history_difficulty")

    db_cuisine_filter = "All" if cuisine_filter == t("option_all") else cuisine_filter
    db_difficulty_filter = "All" if difficulty_filter == t("option_all") else difficulty_filter
    recipes = db.get_user_recipes(user_id, search, db_cuisine_filter, db_difficulty_filter)

    if not recipes:
        empty_state("📭", t("empty_no_recipes_title"), t("empty_no_recipes_sub"))
        return

    if st.session_state.selected_recipe_id:
        selected = next((r for r in recipes if r["id"] == st.session_state.selected_recipe_id), None) or db.get_recipe(st.session_state.selected_recipe_id)
        if selected:
            if st.button(f"← {t('btn_back')}", key="back_btn"):
                st.session_state.selected_recipe_id = None
                st.rerun()
            render_recipe(selected, recipe_id=selected["id"], user_id=user_id)
            if st.button(f"🗑 {t('btn_delete')}", key="delete_btn"):
                db.delete_recipe(selected["id"], user_id)
                st.session_state.selected_recipe_id = None
                st.success(t("msg_recipe_deleted"))
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
                if st.button(t("btn_view_recipe"), key=f"view_{r['id']}", use_container_width=True):
                    st.session_state.selected_recipe_id = r["id"]
                    st.rerun()


# ---------------------------------------------------------- favorites page

def page_favorites():
    st.markdown(
        f"""
        <div class="top-header">
            <div><div class="kicker">{t('kicker_loved')}</div><h1>{t('title_favorites')}</h1></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    user_id = st.session_state.user["id"]
    favs = db.get_favorite_recipes(user_id)

    if not favs:
        empty_state("💚", t("empty_no_favorites_title"), t("empty_no_favorites_sub"))
        return

    cols = st.columns(3)
    for idx, r in enumerate(favs):
        with cols[idx % 3]:
            with mini_card():
                if r.get("image_data"):
                    st.markdown(b64_to_image_html(r["image_data"]), unsafe_allow_html=True)
                st.markdown(f'<span class="eyebrow">{r.get("cuisine","")}</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="recipe-title" style="font-size:1.1rem;">{r["title"]}</div>', unsafe_allow_html=True)
                if st.button(t("btn_view_recipe"), key=f"favview_{r['id']}", use_container_width=True):
                    st.session_state.page = "history"
                    st.session_state.selected_recipe_id = r["id"]
                    st.rerun()


# ------------------------------------------------------------ profile page

def _crop_to_square(img: Image.Image, size: int = 320) -> Image.Image:
    """Center-crop to a square and resize, so uploaded photos always
    render cleanly inside the circular avatar regardless of aspect ratio."""
    img = img.convert("RGB")
    w, h = img.size
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    return img.crop((left, top, left + side, top + side)).resize((size, size))


def _render_profile_header(user: dict):
    st.markdown(
        f"""
        <div class="top-header">
            <div><div class="kicker">{t('kicker_kitchen')}</div><h1>{t('title_profile')}</h1></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_profile_view(user: dict, stats: dict):
    top_col1, top_col2 = st.columns([1, 2])

    with top_col1:
        with card():
            st.markdown(profile_avatar_html(user), unsafe_allow_html=True)
            display = user.get("display_name") or user["username"]
            st.markdown(f'<div class="profile-name">{display}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div style="text-align:center;color:var(--text-muted);font-size:0.82rem;margin-bottom:0.6rem;">@{user["username"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="text-align:center;color:var(--text-muted);font-size:0.75rem;margin-bottom:1rem;">🕰 {t("member_since", date=user["created_at"][:10])}</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"✏️  {t('btn_edit_profile')}", key="btn_open_edit_profile", use_container_width=True):
                st.session_state.profile_edit_mode = True
                st.rerun()

    with top_col2:
        s1, s2, s3 = st.columns(3)
        stat_data = [
            (s1, stats["total_recipes"], t("stat_recipes")),
            (s2, stats["total_favorites"], t("stat_favorites")),
            (s3, stats["unique_cuisines"], t("stat_cuisines")),
        ]
        for col, num, label in stat_data:
            with col:
                with card(accent=True):
                    st.markdown(f'<div class="stat-num">{num}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="stat-label">{label}</div>', unsafe_allow_html=True)

        with card():
            st.markdown(f'<span class="eyebrow">📇 {t("label_bio")}</span>', unsafe_allow_html=True)
            email_val = user.get("email") or ""
            phone_val = user.get("phone") or ""
            location_val = user.get("location") or ""
            bio_val = user.get("bio") or ""

            def meta_row(icon, value, empty_key):
                shown = value if value else f'<span class="meta-empty">{t(empty_key)}</span>'
                return f'<div class="profile-meta-row"><span class="meta-icon">{icon}</span><span>{shown}</span></div>'

            st.markdown(meta_row("📧", email_val, "not_added"), unsafe_allow_html=True)
            st.markdown(meta_row("📞", phone_val, "no_phone"), unsafe_allow_html=True)
            st.markdown(meta_row("📍", location_val, "no_location"), unsafe_allow_html=True)
            st.markdown('<div style="margin-top:0.7rem;">', unsafe_allow_html=True)
            if bio_val:
                st.markdown(f'<div class="bio-text">{bio_val}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bio-text" style="font-style:italic; color:var(--text-muted);">{t("no_bio")}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


def _render_profile_edit_form(user: dict):
    with card(accent=True):
        st.markdown(f'<span class="eyebrow">✏️ {t("edit_profile")}</span>', unsafe_allow_html=True)

        with st.form("edit_profile_form"):
            col_pic, col_fields = st.columns([1, 2])

            with col_pic:
                st.markdown(profile_avatar_html(user), unsafe_allow_html=True)
                uploaded_pic = st.file_uploader(
                    t("upload_profile_picture"), type=["png", "jpg", "jpeg"], key="profile_pic_uploader"
                )
                remove_pic = st.checkbox(
                    t("remove_profile_picture"), key="profile_pic_remove_cb",
                    disabled=not bool(user.get("profile_picture")),
                )

            with col_fields:
                new_username = st.text_input(t("label_username"), value=user["username"], key="edit_username")
                new_display_name = st.text_input(
                    t("label_display_name"), value=user.get("display_name") or "", key="edit_display_name"
                )
                new_email = st.text_input(t("label_email"), value=user.get("email") or "", key="edit_email")
                fcol1, fcol2 = st.columns(2)
                with fcol1:
                    new_phone = st.text_input(
                        t("label_phone"), value=user.get("phone") or "",
                        placeholder=t("placeholder_phone"), key="edit_phone",
                    )
                with fcol2:
                    new_location = st.text_input(
                        t("label_location"), value=user.get("location") or "",
                        placeholder=t("placeholder_location"), key="edit_location",
                    )

            new_bio = st.text_area(
                t("label_bio"), value=user.get("bio") or "",
                placeholder=t("placeholder_bio"), height=100, key="edit_bio",
            )

            save_col, cancel_col = st.columns(2)
            with save_col:
                submitted = st.form_submit_button(t("btn_save_changes"), use_container_width=True)
            with cancel_col:
                cancelled = st.form_submit_button(t("btn_cancel"), use_container_width=True)

        if cancelled:
            st.session_state.profile_edit_mode = False
            st.rerun()

        if submitted:
            if not new_username.strip() or not new_email.strip():
                st.error(t("err_fill_all"))
            else:
                pic_data = None
                if remove_pic:
                    pic_data = ""
                elif uploaded_pic is not None:
                    try:
                        img = _crop_to_square(Image.open(uploaded_pic))
                        pic_data = image_to_b64(img)
                    except Exception as e:
                        st.error(t("err_profile_update_failed", error=str(e)))
                        pic_data = None

                ok, msg = db.update_user_profile(
                    user["id"],
                    new_username.strip(),
                    new_display_name.strip(),
                    new_email.strip(),
                    new_phone.strip(),
                    new_location.strip(),
                    new_bio.strip(),
                    profile_picture=pic_data,
                )
                if ok:
                    st.session_state.user = db.get_user_by_id(user["id"])
                    st.session_state.profile_edit_mode = False
                    st.success(t("msg_profile_updated"))
                    time.sleep(0.4)
                    st.rerun()
                else:
                    st.error(msg)


def _render_recent_activity(user_id: int):
    st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
    st.markdown(f'<span class="eyebrow">🕰 {t("eyebrow_recent")}</span>', unsafe_allow_html=True)
    recent = db.get_user_recipes(user_id)[:5]
    if not recent:
        empty_state("🌱", t("empty_no_recent_title"), t("empty_no_recent_sub"))
    else:
        for r in recent:
            st.markdown(
                f"""
                <div class="recipe-card-mini" style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-weight:700;">🍲 {r['title']}</div>
                        <div style="color:var(--text-muted); font-size:0.8rem;">{r.get('cuisine','')} · {r['created_at'][:10]}</div>
                    </div>
                    <div class="pill">{r.get('difficulty','')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_preferences():
    st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
    st.markdown(f'<span class="eyebrow">🎛 {t("eyebrow_preferences")}</span>', unsafe_allow_html=True)
    with card():
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            st.markdown(f'<div style="font-weight:700; margin-bottom:0.3rem;">{t("pref_theme")}</div>', unsafe_allow_html=True)
            status = t("pref_dark_mode_on") if st.session_state.dark_mode else t("pref_dark_mode_off")
            st.markdown(f'<div style="color:var(--text-muted); font-size:0.85rem; margin-bottom:0.6rem;">{status}</div>', unsafe_allow_html=True)
            icon = "☀️" if st.session_state.dark_mode else "🌙"
            appearance_label = t("theme_light") if st.session_state.dark_mode else t("theme_dark")
            if st.button(f"{icon}  {appearance_label}", key="profile_toggle_theme"):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
        with pcol2:
            st.markdown(f'<div style="font-weight:700; margin-bottom:0.3rem;">{t("pref_language")}</div>', unsafe_allow_html=True)
            st.markdown('<div class="profile-lang-select">', unsafe_allow_html=True)
            lang_codes = list(LANGUAGES.keys())
            current_idx = lang_codes.index(st.session_state.language)
            lang_labels = [f"{LANGUAGES[c]['flag']} {LANGUAGES[c]['name']}" for c in lang_codes]
            chosen = st.selectbox(
                t("language_label"), lang_labels, index=current_idx,
                key="profile_lang_select", label_visibility="collapsed",
            )
            st.markdown('</div>', unsafe_allow_html=True)
            chosen_code = lang_codes[lang_labels.index(chosen)]
            if chosen_code != st.session_state.language:
                st.session_state.language = chosen_code
                st.rerun()


def _render_account_settings(user: dict):
    st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)
    st.markdown(f'<span class="eyebrow">🔐 {t("eyebrow_account_settings")}</span>', unsafe_allow_html=True)

    with card():
        with st.expander(f"🔑 {t('change_password')}"):
            with st.form("change_password_form"):
                current_pw = st.text_input(t("label_current_password"), type="password", key="cp_current")
                new_pw = st.text_input(t("label_new_password"), type="password", key="cp_new")
                confirm_pw = st.text_input(t("label_confirm_password"), type="password", key="cp_confirm")
                submitted_pw = st.form_submit_button(t("btn_update_password"))
            if submitted_pw:
                if not current_pw or not new_pw or not confirm_pw:
                    st.error(t("err_fill_all"))
                elif new_pw != confirm_pw:
                    st.error(t("err_pw_mismatch"))
                elif len(new_pw) < 6:
                    st.error(t("err_pw_short"))
                else:
                    ok, msg = db.update_user_password(user["id"], current_pw, new_pw)
                    if ok:
                        st.success(t("msg_password_updated"))
                    else:
                        st.error(msg)

        st.markdown('<hr class="divider-thin">', unsafe_allow_html=True)

        if st.button(f"↩  {t('btn_logout')}", key="profile_logout_btn", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "generate"
            st.session_state.profile_edit_mode = False
            st.rerun()

        st.markdown(
            f"""
            <div class="danger-zone-box">
                <div class="danger-title">⚠️ {t('danger_zone')}</div>
                <div class="danger-desc">{t('confirm_delete_account')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        confirm = st.checkbox(t("confirm_delete_checkbox"), key="profile_confirm_delete_cb")
        st.markdown('<div class="danger-btn-marker"></div>', unsafe_allow_html=True)
        if st.button(f"🗑  {t('btn_delete_account')}", key="profile_delete_account_btn", disabled=not confirm, use_container_width=True):
            if db.delete_user(user["id"]):
                st.session_state.user = None
                st.session_state.page = "generate"
                st.session_state.profile_edit_mode = False
                st.success(t("account_deleted"))
                time.sleep(0.6)
                st.rerun()
            else:
                st.error(t("error_deleting_account"))


def page_profile():
    user = st.session_state.user
    stats = db.get_user_stats(user["id"])

    _render_profile_header(user)

    if st.session_state.profile_edit_mode:
        _render_profile_edit_form(user)
    else:
        _render_profile_view(user, stats)

    _render_recent_activity(user["id"])
    _render_preferences()
    _render_account_settings(user)


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