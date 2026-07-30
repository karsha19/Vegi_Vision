"""
styles.py
---------
Centralized theme system for Verdant.

Every color in the app is driven by CSS custom properties defined here in
ONE place. Components never hardcode hex values, `white`, `#fff`, `#000`,
etc. — they reference a semantic variable (--text-primary, --card,
--border, ...) and get the correct value automatically for whichever mode
(light/dark) is active. Toggling dark mode simply swaps the variable
values in :root; nothing else in the app needs to change.

Semantic variable contract (used everywhere, in this file and in app.py):

    --background        page background
    --surface            secondary background (sidebar, alt sections)
    --card                card / panel background
    --card-hover          card background on hover
    --primary             brand green (buttons, active states, accents)
    --primary-hover        brand green, hover/pressed state
    --primary-soft         low-opacity tint of primary (badges, highlights)
    --secondary-accent      warm brown accent (eyebrows, secondary pills)
    --text-primary          headings / high-emphasis text
    --text-secondary        body copy
    --text-muted             captions, helper text, timestamps
    --text-on-primary        text placed on top of a --primary background
    --border                 default border color
    --border-strong          higher-contrast border (inputs, dropzone)
    --input-bg                background for inputs/selects/textareas
    --placeholder              input placeholder text
    --shadow                   card / elevation shadow
    --shadow-strong             stronger shadow (modals, popovers)
    --success / --error / --warning / --info    status colors (toasts/alerts)
    --success-bg / --error-bg / --warning-bg / --info-bg   status backgrounds
    --focus-ring                 focus outline color for accessibility
"""

FONT_IMPORT = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;1,9..144,500&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
"""


def get_theme_css(dark_mode: bool, sidebar_collapsed: bool = False) -> str:
    """Return the full <style> block for the requested mode.

    All actual color values live in exactly two palettes below. Nothing
    downstream (this file's component rules, or app.py) ever repeats a
    hex code — everything consumes the semantic variables.
    """

    if dark_mode:
        palette = f"""
        /* ---------------- DARK MODE PALETTE ---------------- */
        --background: #12170f;
        --surface: #1a201a;
        --card: #202822;
        --card-hover: #262f27;
        --primary: #7fae6c;
        --primary-hover: #96c283;
        --primary-soft: rgba(127,174,108,0.16);
        --secondary-accent: #d7ab6f;
        --text-primary: #f5f7f0;
        --text-secondary: #cdd4c6;
        --text-muted: #98a293;
        --text-on-primary: #10190f;
        --border: rgba(245,247,240,0.10);
        --border-strong: rgba(245,247,240,0.22);
        --input-bg: #1c2420;
        --placeholder: #7d8779;
        --shadow: 0 10px 30px rgba(0,0,0,0.45);
        --shadow-strong: 0 18px 46px rgba(0,0,0,0.55);
        --success: #8fcf82; --success-bg: rgba(143,207,130,0.14);
        --error: #f0a396; --error-bg: rgba(240,163,150,0.14);
        --warning: #f0cf8f; --warning-bg: rgba(240,207,143,0.14);
        --info: #90bce0; --info-bg: rgba(144,188,224,0.14);
        --focus-ring: #96c283;
        """
    else:
        palette = f"""
        /* ---------------- LIGHT MODE PALETTE ---------------- */
        --background: #f7f2e7;
        --surface: #f0e9da;
        --card: #ffffff;
        --card-hover: #fbf8f0;
        --primary: #4d6b3d;
        --primary-hover: #3a5230;
        --primary-soft: rgba(77,107,61,0.10);
        --secondary-accent: #a2703b;
        --text-primary: #232821;
        --text-secondary: #374151;
        --text-muted: #6b6a5e;
        --text-on-primary: #ffffff;
        --border: #e3dac4;
        --border-strong: #cdc2a3;
        --input-bg: #ffffff;
        --placeholder: #7c7a6c;
        --shadow: 0 10px 26px rgba(90,73,42,0.10);
        --shadow-strong: 0 20px 44px rgba(90,73,42,0.16);
        --success: #2f7a4d; --success-bg: #e7f4ea;
        --error: #b3402f; --error-bg: #fbe9e6;
        --warning: #9a6d1f; --warning-bg: #faf0dc;
        --info: #2f5f8a; --info-bg: #e7f0f8;
        --focus-ring: #4d6b3d;
        """

    # Collapsed-state overrides: a narrow icon-only rail. Scoped to
    # tablet/desktop widths (min-width: 769px) so Streamlit's own native
    # mobile behavior — where the sidebar is already an off-canvas overlay
    # that slides in/out — is left completely untouched on phones.
    sidebar_collapsed_css = """
    @media (min-width: 769px) {
        section[data-testid="stSidebar"] {
            width: 84px !important;
            min-width: 84px !important;
            max-width: 84px !important;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-left: 0.4rem;
            padding-right: 0.4rem;
        }
        section[data-testid="stSidebar"] .stButton > button {
            justify-content: center;
            text-align: center;
            padding: 0.62rem 0.4rem;
            font-size: 1.1rem;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            transform: none;
            background: var(--card-hover);
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] {
            font-size: 0.75rem;
        }
    }
    """ if sidebar_collapsed else ""

    return f"""
    <style>
    :root {{
        {palette}
    }}

    html, body, [class*="css"] {{
        font-family: 'Manrope', sans-serif;
    }}

    #MainMenu, footer, header {{visibility: hidden;}}

    div.block-container {{
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 1300px;
    }}

    .stApp {{
        background: var(--background);
        color: var(--text-secondary);
    }}

    /* ---------- Typography ---------- */
    h1, h2, h3, h4, h5, h6, .headline {{
        font-family: 'Fraunces', serif;
        color: var(--text-primary);
        letter-spacing: -0.01em;
    }}
    p, span, div, label, li {{
        color: var(--text-secondary);
    }}
    a {{
        color: var(--primary);
        text-decoration: none;
        transition: color 0.15s ease;
    }}
    a:hover {{
        color: var(--primary-hover);
        text-decoration: underline;
    }}

    /* ================= SIDEBAR ================= */
    section[data-testid="stSidebar"] {{
        background: var(--surface);
        border-right: 1px solid var(--border);
        box-shadow: 4px 0 24px rgba(0,0,0,0.06);
        transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1),
                    min-width 0.28s cubic-bezier(0.4, 0, 0.2, 1);
        overflow-x: hidden;
    }}

    /* Keep the expanded sidebar wide enough that nav labels never wrap */
    @media (min-width: 769px) {{
        section[data-testid="stSidebar"] {{
            width: 288px !important;
            min-width: 288px !important;
            max-width: 288px !important;
        }}
    }}

    section[data-testid="stSidebar"] .block-container {{
        padding-top: 1.6rem;
        padding-left: 1.1rem;
        padding-right: 1.1rem;
        transition: padding 0.28s ease;
    }}

    /* Base text/icon color inside sidebar — high-contrast in both themes */
    section[data-testid="stSidebar"] * {{
        color: var(--text-secondary);
    }}

    /* ---- Hamburger / close toggle ---- */
    section[data-testid="stSidebar"] div[data-testid="stButton"]:first-of-type > button {{
        width: 40px;
        height: 40px;
        min-width: 40px;
        padding: 0 !important;
        border-radius: 50% !important;
        background: var(--primary) !important;
        color: var(--text-on-primary) !important;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 1.1rem;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-strong);
        transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
    }}
    section[data-testid="stSidebar"] div[data-testid="stButton"]:first-of-type > button p {{
        color: var(--text-on-primary) !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stButton"]:first-of-type > button:hover {{
        background: var(--primary-hover) !important;
        transform: scale(1.08) !important;
        box-shadow: var(--shadow-strong);
    }}
    section[data-testid="stSidebar"] div[data-testid="stButton"]:first-of-type > button:active {{
        transform: scale(0.96) !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stButton"]:first-of-type > button:focus-visible {{
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
    }}

    /* ---- Logo / brand area ---- */
    .brand-mark-collapsed {{
        text-align: center;
        font-size: 1.6rem;
        margin-bottom: 1rem;
    }}

    {sidebar_collapsed_css}

    .brand-mark {{
        font-family: 'Fraunces', serif;
        font-size: 1.62rem;
        font-weight: 700;
        color: var(--text-primary) !important;
        line-height: 1.15;
        margin-bottom: 0.15rem;
        letter-spacing: -0.01em;
    }}
    .brand-sub {{
        font-family: 'Manrope', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--secondary-accent) !important;
        margin-bottom: 1.9rem;
        opacity: 0.9;
    }}

    /* ---- Nav buttons (Generate Recipe / Recipe History / Favorites / Profile) ---- */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] div[data-testid="stButton"] {{
        margin-bottom: 0.4rem;
    }}
    div[data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        text-align: left;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        background: transparent;
        border: 1px solid transparent;
        color: var(--text-secondary) !important;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.01em;
        line-height: 1.2;
        padding: 0.78rem 1rem;
        min-height: 46px;
        border-radius: 14px;
        box-shadow: none;
        transition: background 0.18s ease, border-color 0.18s ease,
                    color 0.18s ease, transform 0.18s ease;
    }}
    div[data-testid="stSidebar"] .stButton > button p {{
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: inherit !important;
        margin: 0;
    }}

    /* Hover state — subtle bg + gentle shift, no layout jump */
    div[data-testid="stSidebar"] .stButton > button:hover {{
        background: var(--card-hover);
        border-color: var(--border);
        color: var(--text-primary) !important;
        transform: translateX(3px) scale(1.01);
    }}
    div[data-testid="stSidebar"] .stButton > button:active {{
        transform: translateX(1px) scale(0.99);
    }}
    div[data-testid="stSidebar"] .stButton > button:focus-visible {{
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
    }}

    /* ---- Active nav item ----
       A hidden marker div rendered right before the active nav button
       (see sidebar() in app.py) lets pure CSS pick out that one button
       via an adjacent-sibling selector, with no hardcoded per-page CSS. */
    div[data-testid="stSidebar"] .nav-active-marker
        + div[data-testid="stButton"] > button {{
        background: var(--primary-soft) !important;
        border-color: var(--primary) !important;
        color: var(--primary) !important;
        font-weight: 800 !important;
    }}
    div[data-testid="stSidebar"] .nav-active-marker
        + div[data-testid="stButton"] > button:hover {{
        background: var(--primary-soft) !important;
        transform: translateX(3px);
    }}
    .nav-active-marker {{ display: none; }}

    /* ---- Divider between nav / theme toggle / language ---- */
    section[data-testid="stSidebar"] hr.divider-thin {{
        border-top: 1px solid var(--border);
        margin: 1.1rem 0;
    }}

    /* ---- Language select inside sidebar ---- */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background: var(--input-bg) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }}

    /* ---------- Generic card ----------
       Cards are real st.container(border=True) blocks (see card() in
       app.py), so content actually nests inside them. We restyle
       Streamlit's own wrapper element rather than hand-rolling a <div>
       across two separate st.markdown() calls, which cannot nest
       Streamlit widgets between them and rendered as empty floating
       pills. A tiny invisible .card-tag marker lets CSS :has() find the
       right wrapper and style variants (accent / tight). */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-tag) {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 22px !important;
        box-shadow: var(--shadow) !important;
        transition: transform 0.22s ease, box-shadow 0.22s ease, background 0.2s ease;
        margin-bottom: 1.1rem;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-tag) > div {{
        gap: 0.5rem;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-tag-tight) {{
        padding: 0.2rem 0 !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-tag-accent) {{
        background: var(--primary-soft) !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-tag):hover {{
        transform: translateY(-3px);
    }}
    .card-tag, .card-tag-tight, .card-tag-accent {{ display: none; }}

    .eyebrow {{
        font-size: 0.68rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--secondary-accent) !important;
        font-weight: 700;
        margin-bottom: 0.35rem;
        display: block;
    }}

    .stat-num {{
        font-family: 'Fraunces', serif;
        font-size: 2.1rem;
        font-weight: 700;
        color: var(--text-primary) !important;
        line-height: 1;
    }}
    .stat-label {{
        color: var(--text-muted) !important;
        font-size: 0.8rem;
        margin-top: 0.3rem;
    }}

    /* ---------- Pills / badges ---------- */
    .pill {{
        display: inline-block;
        background: var(--surface);
        border: 1px solid var(--border);
        color: var(--text-secondary) !important;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.28rem 0.75rem;
        border-radius: 999px;
        margin: 0 0.3rem 0.3rem 0;
    }}
    .pill.green {{ background: var(--primary); color: var(--text-on-primary) !important; border: none; }}
    .pill.brown {{ background: var(--secondary-accent); color: var(--text-on-primary) !important; border: none; }}

    .recipe-title {{
        font-family: 'Fraunces', serif;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0.2rem 0 0.4rem 0;
        color: var(--text-primary) !important;
    }}

    .divider-thin {{
        border: none;
        border-top: 1px solid var(--border);
        margin: 0.9rem 0;
    }}

    /* ---------- Recipe steps ---------- */
    .step-row {{
        display: flex;
        gap: 0.8rem;
        margin-bottom: 0.85rem;
        align-items: flex-start;
    }}
    .step-num {{
        flex-shrink: 0;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: var(--primary);
        color: var(--text-on-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
        font-family: 'Fraunces', serif;
    }}
    .step-text {{
        color: var(--text-secondary) !important;
        line-height: 1.55;
        padding-top: 0.15rem;
    }}

    .ingredient-row {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.45rem 0;
        border-bottom: 1px dashed var(--border);
        color: var(--text-secondary) !important;
        font-size: 0.92rem;
    }}
    .ingredient-row:last-child {{ border-bottom: none; }}

    /* ---------- Buttons (main content) ---------- */
    .stButton > button {{
        background: var(--primary);
        color: var(--text-on-primary) !important;
        border: none;
        border-radius: 14px;
        padding: 0.6rem 1.4rem;
        font-weight: 700;
        font-size: 0.92rem;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
    }}
    .stButton > button p {{
        color: var(--text-on-primary) !important;
    }}
    .stButton > button:hover {{
        background: var(--primary-hover);
        transform: translateY(-2px);
        box-shadow: var(--shadow-strong);
    }}
    .stButton > button:focus-visible {{
        outline: 3px solid var(--focus-ring);
        outline-offset: 2px;
    }}
    .stButton > button:active {{
        transform: translateY(0);
    }}
    .stFormSubmitButton > button {{
        background: var(--primary);
        color: var(--text-on-primary) !important;
    }}
    .stFormSubmitButton > button:hover {{
        background: var(--primary-hover);
    }}

    /* ---------- Text inputs / selects / textareas ---------- */
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"],
    textarea,
    .stTextInput input,
    .stTextArea textarea {{
        border-radius: 12px !important;
        background: var(--input-bg) !important;
        border: 1px solid var(--border-strong) !important;
        color: var(--text-primary) !important;
    }}
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {{
        color: var(--placeholder) !important;
        opacity: 1;
    }}
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    .stTextArea textarea:focus {{
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px var(--primary-soft) !important;
    }}
    .stTextInput > label,
    .stSelectbox > label,
    .stTextArea > label,
    .stMultiSelect > label,
    .stFileUploader > label {{
        color: var(--text-secondary) !important;
        font-weight: 600;
        font-size: 0.85rem;
    }}

    /* Selected chips inside multiselect */
    span[data-baseweb="tag"] {{
        background: var(--primary) !important;
        color: var(--text-on-primary) !important;
    }}

    /* Dropdown menu / popover (rendered in a portal) */
    ul[data-testid="stSelectboxVirtualDropdown"],
    div[data-baseweb="popover"] ul {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        box-shadow: var(--shadow-strong) !important;
    }}
    ul[data-testid="stSelectboxVirtualDropdown"] li,
    div[data-baseweb="popover"] ul li {{
        color: var(--text-secondary) !important;
    }}
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover,
    div[data-baseweb="popover"] ul li:hover {{
        background: var(--primary-soft) !important;
    }}

    /* ---------- Tabs ---------- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.4rem;
        border-bottom: 1px solid var(--border);
    }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        color: var(--text-muted) !important;
        font-weight: 600;
        border-radius: 10px 10px 0 0;
        padding: 0.5rem 1rem;
    }}
    .stTabs [data-baseweb="tab"] p {{
        color: inherit !important;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: var(--text-primary) !important;
        background: var(--surface);
    }}
    .stTabs [aria-selected="true"] {{
        color: var(--primary) !important;
        border-bottom: 2px solid var(--primary);
    }}
    .stTabs [aria-selected="true"] p {{
        color: var(--primary) !important;
    }}

    /* ---------- File uploader / upload box ---------- */
    section[data-testid="stFileUploaderDropzone"] {{
        background: var(--surface) !important;
        border: 1.5px dashed var(--secondary-accent) !important;
        border-radius: 18px !important;
    }}
    section[data-testid="stFileUploaderDropzone"] * {{
        color: var(--text-secondary) !important;
    }}
    section[data-testid="stFileUploaderDropzone"] small {{
        color: var(--text-muted) !important;
    }}
    section[data-testid="stFileUploaderDropzone"] button {{
        background: var(--card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-strong) !important;
    }}

    /* ---------- Alerts / toasts (st.success, st.error, st.warning, st.info) ---------- */
    div[data-testid="stAlert"] {{
        border-radius: 14px;
        border: 1px solid var(--border);
    }}
    div[data-testid="stAlertContentSuccess"], div[data-testid="stAlert"]:has(svg[title="Success"]) {{
        background: var(--success-bg) !important;
        color: var(--success) !important;
    }}
    div[data-testid="stAlert"] p {{
        color: inherit;
    }}
    .stAlert [data-baseweb="notification"] {{
        color: var(--text-primary) !important;
    }}

    /* ---------- Modals / dialogs ---------- */
    div[data-testid="stDialog"] > div {{
        background: var(--card) !important;
        border: 1px solid var(--border);
        border-radius: 20px;
        box-shadow: var(--shadow-strong);
    }}
    div[data-testid="stDialog"] * {{
        color: var(--text-secondary) !important;
    }}
    div[data-testid="stDialog"] h1,
    div[data-testid="stDialog"] h2,
    div[data-testid="stDialog"] h3 {{
        color: var(--text-primary) !important;
    }}

    /* ---------- Empty state ---------- */
    .empty-state {{
        text-align: center;
        padding: 3rem 1.5rem;
        background: var(--surface);
        border: 1px dashed var(--border);
        border-radius: 22px;
        color: var(--text-muted) !important;
    }}
    .empty-state .icon {{ font-size: 2.4rem; margin-bottom: 0.6rem; }}
    .empty-state .title {{
        font-family: 'Fraunces', serif;
        font-size: 1.2rem;
        color: var(--text-primary) !important;
        margin-bottom: 0.3rem;
    }}

    /* ---------- Page header ---------- */
    .top-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        margin-bottom: 1.4rem;
    }}
    .top-header .kicker {{
        color: var(--secondary-accent) !important;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        font-size: 0.72rem;
        font-weight: 700;
    }}
    .top-header h1 {{
        margin: 0.15rem 0 0 0;
        font-size: 2.1rem;
        color: var(--text-primary) !important;
    }}

    /* ---------- Recipe / history / favorites mini cards ----------
       Same real-container approach as the main card system above. */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-tag-mini) {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 18px !important;
        margin-bottom: 0.9rem;
        transition: transform 0.18s ease, background 0.18s ease;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-tag-mini) > div {{
        padding: 1rem 1.1rem;
        gap: 0.4rem;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-tag-mini):hover {{
        transform: translateY(-2px);
        background: var(--card-hover);
    }}
    .recipe-card-mini {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: var(--text-secondary);
    }}
    .recipe-card-mini .recipe-title {{
        color: var(--text-primary) !important;
    }}

    /* ---------- Profile avatar ---------- */
    .avatar-badge {{
        width: 54px;
        height: 54px;
        border-radius: 16px;
        background: var(--primary-soft);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-family: 'Fraunces', serif;
        font-weight: 700;
        color: var(--primary) !important;
        border: 1px solid var(--border);
    }}

    /* ---------- Footer (reserved for future use) ---------- */
    .app-footer {{
        color: var(--text-muted) !important;
        font-size: 0.78rem;
        text-align: center;
        padding: 1.2rem 0;
        border-top: 1px solid var(--border);
        margin-top: 2rem;
    }}
    .app-footer a {{
        color: var(--secondary-accent) !important;
    }}

    /* ---------- Icons inherit currentColor ---------- */
    svg {{
        color: inherit;
    }}

    /* ---------- Voice Recipe Assistant ---------- */
    .voice-status {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        padding: 0.35rem 0.85rem;
        border-radius: 999px;
        background: var(--surface);
        border: 1px solid var(--border);
        color: var(--text-secondary) !important;
        margin: 0.6rem 0;
    }}
    .status-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--text-muted);
        flex-shrink: 0;
    }}
    .voice-status-idle .status-dot {{
        background: var(--text-muted);
    }}
    .voice-status-processing {{
        background: var(--info-bg);
        border-color: transparent;
        color: var(--info) !important;
    }}
    .voice-status-processing .status-dot {{
        background: var(--info);
        animation: voice-pulse 1s ease-in-out infinite;
    }}
    .voice-status-done {{
        background: var(--success-bg);
        border-color: transparent;
        color: var(--success) !important;
    }}
    .voice-status-done .status-dot {{
        background: var(--success);
    }}
    .voice-status-error {{
        background: var(--error-bg);
        border-color: transparent;
        color: var(--error) !important;
    }}
    .voice-status-error .status-dot {{
        background: var(--error);
    }}
    @keyframes voice-pulse {{
        0%   {{ transform: scale(1);   opacity: 1;   }}
        50%  {{ transform: scale(1.6); opacity: 0.55; }}
        100% {{ transform: scale(1);   opacity: 1;   }}
    }}
    /* The mic recorder is a sandboxed browser component (its own iframe),
       so page CSS can't reach inside it — this just keeps its surrounding
       spacing consistent with the rest of the bento layout. */
    iframe[title="streamlit_mic_recorder.mic_recorder"] {{
        border-radius: 14px;
    }}

    /* ---------- Focus visibility everywhere ---------- */
    a:focus-visible,
    button:focus-visible,
    input:focus-visible,
    select:focus-visible,
    textarea:focus-visible {{
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
    }}

    ::-webkit-scrollbar {{ width: 8px; }}
    ::-webkit-scrollbar-thumb {{ background: var(--text-muted); border-radius: 8px; }}
    </style>
    """
