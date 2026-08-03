"""
styles.py
---------
Centralized theme system for VegiVision.

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
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;1,9..144,500&family=Manrope:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
"""


def build_hidden_style_html(css_rules: str) -> str:
    """Return HTML that injects a stylesheet while keeping it completely hidden from the UI."""
    return (
        "<div aria-hidden='true' style=\"position:absolute; left:-9999px; top:-9999px; "
        "width:1px; height:1px; overflow:hidden; opacity:0; pointer-events:none;\">"
        f"<style>{css_rules}</style></div>"
    )


def get_theme_css(dark_mode: bool, sidebar_collapsed: bool = False) -> str:
    """Return the CSS rules for the requested theme mode.

    All actual color values live in exactly two palettes below. Nothing
    downstream (this file's component rules, or app.py) ever repeats a
    hex code — everything consumes the semantic variables.
    """

    if dark_mode:
        palette = f"""
        /* ---------------- DARK MODE PALETTE (per design spec) ---------------- */
        --background: #121212;
        --surface: #191919;
        --sidebar: #191919;
        --card: #1C1C1C;
        --card-hover: #232323;
        --primary: #6F9A5F;
        --primary-hover: #84B880;
        --primary-soft: rgba(111,154,95,0.16);
        --secondary-accent: #d3a876;
        --text-primary: #F5F5F5;
        --text-secondary: #CFCFCF;
        --text-muted: #A1A1AA;
        --text-on-primary: #FFFFFF;
        --border: #323232;
        --border-strong: #454545;
        --input-bg: #1E1E1E;
        --placeholder: #8A8A8A;
        --shadow: 0 10px 28px rgba(0,0,0,0.45);
        --shadow-strong: 0 24px 56px rgba(0,0,0,0.55);
        --success: #66BB6A; --success-bg: rgba(102,187,106,0.14);
        --error: #EF5350; --error-bg: rgba(239,83,80,0.14);
        --warning: #FFCA28; --warning-bg: rgba(255,202,40,0.14);
        --info: #64B5F6; --info-bg: rgba(100,181,246,0.14);
        --focus-ring: rgba(111,154,95,0.4);
        --dropdown-hover: #262626;
        """
    else:
        palette = f"""
        /* ---------------- LIGHT MODE PALETTE (per design spec) ---------------- */
        --background: #F8F6F0;
        --surface: #F2F4ED;
        --sidebar: #F2F4ED;
        --card: #FFFFFF;
        --card-hover: #F5F3EC;
        --primary: #5A7D4D;
        --primary-hover: #496640;
        --primary-soft: rgba(90,125,77,0.10);
        --secondary-accent: #b08650;
        --text-primary: #222222;
        --text-secondary: #555555;
        --text-muted: #6E6E6E;
        --text-on-primary: #FFFFFF;
        --border: #E7E2D8;
        --border-strong: #D3C8AC;
        --input-bg: #FFFFFF;
        --placeholder: #9B9A90;
        --shadow: 0 8px 24px rgba(38,38,32,0.08);
        --shadow-strong: 0 20px 48px rgba(38,38,32,0.14);
        --success: #4CAF50; --success-bg: #E9F6EA;
        --error: #E5484D; --error-bg: #FBEAEA;
        --warning: #FFB020; --warning-bg: #FFF4E0;
        --info: #4A90E2; --info-bg: #E8F1FC;
        --focus-ring: rgba(90,125,77,0.35);
        --dropdown-hover: #ECE5D5;
        """

    
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
            background: var(--primary-hover);
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] {
            font-size: 0.75rem;
        }
    }
    """ if sidebar_collapsed else ""


    return f"""
    :root {{
        {palette}
        --radius-pill: 999px;
        --radius-card: 20px;
        --radius-input: 12px;
        --radius-icon: 16px;
    }}

    html, body {{
        color-scheme: {"dark" if dark_mode else "light"};
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

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"] {{
        background: var(--background) !important;
        color: var(--text-secondary) !important;
        transition: background-color 0.35s ease, color 0.35s ease;
    }}
    section[data-testid="stSidebar"] {{
        background: var(--sidebar) !important;
    }}
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    /* ---------- Typography ----------
       Streamlit ships its own bundled stylesheet with class-attribute
       and data-testid selectors that carry higher CSS specificity than
       a bare element selector like `div` or `p`. Without !important
       here, Streamlit's own static text color wins the cascade and the
       app's text silently stops following --text-primary/--text-
       secondary when dark mode is toggled, even though the variables
       themselves ARE updating correctly. Every rule in this block is
       !important specifically to guarantee our theme variables always
       win over Streamlit's built-in styling. */
    h1, h2, h3, h4, h5, h6, .headline {{
        font-family: 'Fraunces', serif;
        color: var(--text-primary) !important;
        letter-spacing: -0.01em;
    }}
    p, span, div, label, li,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] ol,
    [data-testid="stMarkdownContainer"] ul,
    [data-testid="stText"],
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span,
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"],
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] p,
    [data-testid="stTooltipIcon"],
    [data-testid="stTooltipHoverTarget"],
    [data-testid="stElementContainer"] p,
    [data-testid="stElementContainer"] span,
    .stCheckbox label span p,
    .stRadio label span p,
    .stSelectbox label span p,
    .stAlert p, .stAlert span {{
        color: var(--text-secondary) !important;
    }}
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] h5,
    [data-testid="stMarkdownContainer"] h6,
    [data-testid="stMarkdownContainer"] strong,
    [data-testid="stMarkdownContainer"] b {{
        color: var(--text-primary) !important;
    }}
    a {{
        color: var(--primary) !important;
        text-decoration: none;
        transition: color 0.15s ease;
    }}
    a:hover {{
        color: var(--primary-hover) !important;
        text-decoration: underline;
    }}

    /* ================= AUTH / LOGIN PAGE ================= */
    /* A hidden marker rendered at the top of auth_screen() lets this
       target the app background ONLY while the person is signed out,
       using the same :has() pattern already used for cards elsewhere
       in this file — no separate page/route system needed. */
    .stApp:has(.auth-page-marker) {{
        background:
            radial-gradient(circle at 12% 8%, var(--primary-soft), transparent 42%),
            radial-gradient(circle at 88% 92%, var(--primary-soft), transparent 40%),
            radial-gradient(circle at 90% 6%, var(--secondary-accent) 0%, transparent 2.4%),
            radial-gradient(circle at 6% 90%, var(--secondary-accent) 0%, transparent 2.2%),
            var(--background);
        background-attachment: fixed;
        transition: background-color 0.35s ease;
    }}
    .stApp:has(.auth-page-marker) .block-container {{
        max-width: 1300px;
    }}

    /* Soft, very-low-opacity leaf motif behind the auth card — decorative
       only, so it's an ::before layer rather than real content, and it
       inherits var(--primary) so it's always on-brand in both themes. */
    .auth-page-marker {{
        display: block;
        height: 0;
    }}
    .auth-page-marker::before {{
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        opacity: 0.05;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120'%3E%3Cpath d='M60 10c22 8 40 26 40 50 0 22-18 40-40 40S20 82 20 60c0-24 18-42 40-50z' fill='none' stroke='%234d6b3d' stroke-width='2'/%3E%3Cpath d='M60 10v90' stroke='%234d6b3d' stroke-width='2'/%3E%3C/svg%3E");
        background-size: 220px 220px;
        background-repeat: repeat;
    }}

    /* ---- Logo + tagline ---- */
    .auth-brand-wrap {{
        text-align: center;
        margin: 2.4rem 0 2.2rem 0;
        position: relative;
        z-index: 1;
    }}
    .auth-brand-icon-chip {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 54px;
        height: 54px;
        border-radius: var(--radius-card);
        background: var(--primary-soft);
        font-size: 1.6rem;
        margin-bottom: 1rem;
        border: 1px solid var(--border);
    }}
    .auth-brand-name {{
        font-family: 'Fraunces', serif;
        font-size: 2.7rem;
        font-weight: 700;
        letter-spacing: -0.015em;
        color: var(--text-primary);
        line-height: 1.1;
        margin-bottom: 0.5rem;
    }}
    .auth-brand-divider {{
        width: 46px;
        height: 3px;
        border-radius: var(--radius-pill);
        background: linear-gradient(90deg, var(--primary), var(--secondary-accent));
        margin: 0 auto 0.7rem auto;
    }}
    .auth-brand-tagline {{
        font-family: 'IBM Plex Mono', monospace;
        color: var(--text-muted);
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-size: 0.68rem;
        font-weight: 500;
    }}

    /* ---- Theme toggle button on the sign-in screen — a small round
       chip that mirrors the language selector's pill chrome so the two
       controls read as one consistent top-bar unit. ---- */
    .st-key-auth_theme_toggle button {{
        width: 40px !important;
        height: 40px !important;
        min-width: 40px !important;
        padding: 0 !important;
        border-radius: var(--radius-pill) !important;
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        box-shadow: none !important;
        font-size: 1rem;
        transition: background 0.15s ease, transform 0.15s ease, border-color 0.15s ease;
    }}
    .st-key-auth_theme_toggle button:hover {{
        background: var(--card-hover) !important;
        border-color: var(--border-strong) !important;
        transform: rotate(-8deg);
    }}

    /* ---- Language selector, blended into the top bar ---- */
    .auth-lang-select div[data-baseweb="select"] > div {{
        background: transparent !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-pill) !important;
        font-size: 0.8rem;
    }}
    .auth-lang-select div[data-baseweb="select"] > div:hover {{
        border-color: var(--primary) !important;
    }}

    /* ---- The auth card itself ----
       A premium, slightly glassy card: bigger radius, brand-gradient
       top edge, generous internal breathing room. Targeted via the
       same hidden-marker + :has() technique as card()/mini_card(). */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-tag) {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-card) !important;
        box-shadow: var(--shadow-strong) !important;
        padding: 0.4rem !important;
        max-width: 480px;
        margin-left: auto !important;
        margin-right: auto !important;
        position: relative;
        overflow: hidden;
        z-index: 1;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-tag)::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary), var(--secondary-accent), var(--primary));
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-tag) > div {{
        gap: 0.65rem;
        padding: 2.75rem 2.5rem;
    }}
    @media (max-width: 600px) {{
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-tag) > div {{
            padding: 1.75rem 1.25rem;
        }}
    }}
    .auth-card-tag {{ display: none; }}

    /* ---- Signature: a single hand-drawn vine that grows up the card's
       left edge on load — the one bold gesture on this page. Rendered as
       an inline SVG so the stroke can be animated with dashoffset; three
       gold "buds" fade in after the line finishes drawing. Everything
       else on the page stays deliberately quiet. ---- */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-tag) {{
        margin-left: 14px !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-tag)::after {{
        content: "";
        position: absolute;
        top: 26px;
        left: -14px;
        width: 28px;
        height: 230px;
        pointer-events: none;
        background-repeat: no-repeat;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='230' viewBox='0 0 28 230'%3E%3Cpath d='M14 4 C 6 30, 22 55, 12 82 S 4 130, 16 158 S 8 200, 14 226' fill='none' stroke='%235A7D4D' stroke-width='1.6' stroke-linecap='round'/%3E%3Ccircle cx='18' cy='46' r='3.2' fill='%23b08650'/%3E%3Ccircle cx='9' cy='104' r='3.2' fill='%23b08650'/%3E%3Ccircle cx='19' cy='172' r='3.2' fill='%23b08650'/%3E%3C/svg%3E");
        opacity: 0;
        animation: vine-fade-in 0.6s ease-out 0.3s forwards;
    }}
    @keyframes vine-fade-in {{
        to {{ opacity: 1; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-tag)::after {{
            animation: none;
            opacity: 1;
        }}
    }}

    /* ---- Segmented pill tabs (Sign In / Create Account, and reused
       app-wide for a consistent tab language on e.g. the Generate page) ---- */
    .stTabs [role="tablist"] {{
        gap: 0.25rem;
        border-bottom: none;
        background: var(--surface);
        padding: 0.3rem;
        border-radius: var(--radius-pill) !important;
        border: 1px solid var(--border);
        overflow: hidden;
    }}
    .stTabs [data-testid="stTab"] {{
        background: transparent;
        color: var(--text-muted) !important;
        font-weight: 700;
        font-size: 0.86rem;
        border-radius: var(--radius-pill) !important;
        padding: 0.55rem 1.2rem;
        overflow: hidden;
        transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
    }}
    .stTabs [data-testid="stTab"] * {{
        border-radius: inherit;
    }}
    .stTabs [data-testid="stTab"] p {{
        color: inherit !important;
    }}
    .stTabs [data-testid="stTab"]:hover {{
        color: var(--text-primary) !important;
        background: var(--card-hover);
    }}
    .stTabs [data-testid="stTab"][data-selected],
    .stTabs [data-testid="stTab"][aria-selected="true"] {{
        color: var(--text-on-primary) !important;
        background: var(--primary) !important;
        border-radius: var(--radius-pill) !important;
        box-shadow: var(--shadow);
    }}
    .stTabs [data-testid="stTab"][data-selected] p,
    .stTabs [data-testid="stTab"][aria-selected="true"] p {{
        color: var(--text-on-primary) !important;
    }}
    .stTabs [data-testid="stTab"] .react-aria-SelectionIndicator {{
        display: none !important;
    }}
    .stTabs [data-testid="stTabPanel"] {{
        padding-top: 1.2rem;
    }}

    /* ---- Password show/hide toggle, styled to match the input chrome ---- */
    button[aria-label="Show password"],
    button[aria-label="Hide password"] {{
        color: var(--text-muted) !important;
        transition: color 0.15s ease;
    }}
    button[aria-label="Show password"]:hover,
    button[aria-label="Hide password"]:hover {{
        color: var(--primary) !important;
    }}

    /* ================= SIDEBAR ================= */
    section[data-testid="stSidebar"] {{
        background: var(--sidebar);
        border-right: 1px solid var(--border);
        box-shadow: var(--shadow);
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

    /* ---- Remove Streamlit's native "<<" collapse arrow ----
       The app has its own custom ☰ / ✕ toggle button (see sidebar() in
       app.py), so Streamlit's built-in collapse control is redundant
       clutter — hide it completely, in both expanded and collapsed
       states, without touching anything else in the sidebar. */
    button[data-testid="stSidebarCollapseButton"],
    div[data-testid="stSidebarCollapseButton"],
    button[data-testid="stExpandSidebarButton"],
    div[data-testid="stExpandSidebarButton"] {{
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }}

    /* ---- Hamburger / close toggle ----
       Scoped by Streamlit's key-based class (added automatically for
       every widget with a `key=`) rather than :first-of-type — each
       sidebar button lives in its own wrapper container, so
       ":first-of-type" was trivially true for ALL of them, not just
       the toggle, which squashed every nav label into a 40px circle. */
    section[data-testid="stSidebar"] .st-key-sidebar_toggle > div > button,
    section[data-testid="stSidebar"] .st-key-sidebar_toggle button {{
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
    section[data-testid="stSidebar"] .st-key-sidebar_toggle button p {{
        color: var(--text-on-primary) !important;
    }}
    section[data-testid="stSidebar"] .st-key-sidebar_toggle button:hover {{
        background: var(--primary-hover) !important;
        transform: scale(1.08) !important;
        box-shadow: var(--shadow-strong);
    }}
    section[data-testid="stSidebar"] .st-key-sidebar_toggle button:active {{
        transform: scale(0.96) !important;
    }}
    section[data-testid="stSidebar"] .st-key-sidebar_toggle button:focus-visible {{
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
    section[data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        text-align: left;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        background: var(--primary);
        border: 1px solid transparent;
        color: var(--text-on-primary) !important;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.01em;
        line-height: 1.2;
        padding: 0.78rem 1rem;
        min-height: 46px;
        border-radius: var(--radius-pill) !important;
        overflow: hidden;
        box-shadow: var(--shadow);
        transition: background 0.18s ease, border-color 0.18s ease,
                    color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
    }}
    section[data-testid="stSidebar"] .stButton > button p {{
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: inherit !important;
        margin: 0;
    }}

    /* Hover state — deeper green + gentle shift, no layout jump */
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: var(--primary-hover);
        border-color: var(--primary-hover);
        color: var(--text-on-primary) !important;
        transform: translateX(3px) scale(1.01);
        box-shadow: var(--shadow-strong);
    }}
    section[data-testid="stSidebar"] .stButton > button:active {{
        transform: translateX(1px) scale(0.99);
    }}
    section[data-testid="stSidebar"] .stButton > button:focus-visible {{
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
    }}

    /* ---- Active nav item ---- */
    section[data-testid="stSidebar"] .nav-active-marker
        + div[data-testid="stButton"] > button {{
        background: var(--primary-hover) !important;
        border-color: var(--text-on-primary) !important;
        color: var(--text-on-primary) !important;
        font-weight: 800 !important;
        box-shadow: var(--shadow-strong) !important;
    }}
    section[data-testid="stSidebar"] .nav-active-marker
        + div[data-testid="stButton"] > button:hover {{
        background: var(--primary-hover) !important;
        transform: translateX(3px);
    }}
    .nav-active-marker {{ display: none; }}

    /* ---- Divider between nav / theme toggle / language ---- */
    section[data-testid="stSidebar"] hr.divider-thin {{
        border-top: 1px solid var(--border);
        margin: 1.1rem 0;
    }}

    /* ---- Language select inside sidebar ---- */
    .sidebar-lang-block {{
        margin-top: 0.15rem;
        padding: 0.1rem 0.05rem 0;
    }}
    .sidebar-lang-label {{
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-secondary) !important;
        margin-bottom: 0.45rem;
        letter-spacing: 0.01em;
    }}
    section[data-testid="stSidebar"] .st-key-sidebar_lang_select div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] .st-key-sidebar_lang_select div[data-baseweb="select"] > div > div,
    section[data-testid="stSidebar"] .sidebar-lang-block .stSelectbox > div > div,
    section[data-testid="stSidebar"] .sidebar-lang-block div[data-baseweb="select"] > div {{
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-pill) !important;
        color: var(--text-primary) !important;
        min-height: 42px;
        box-shadow: none !important;
    }}
    section[data-testid="stSidebar"] .st-key-sidebar_lang_select div[data-baseweb="select"] * {{
        color: var(--text-primary) !important;
    }}
    section[data-testid="stSidebar"] .st-key-sidebar_lang_select div[data-baseweb="select"] > div:hover,
    section[data-testid="stSidebar"] .st-key-sidebar_lang_select div[data-baseweb="select"] > div:focus-within,
    section[data-testid="stSidebar"] .sidebar-lang-block .stSelectbox > div > div:hover,
    section[data-testid="stSidebar"] .sidebar-lang-block div[data-baseweb="select"] > div:hover,
    section[data-testid="stSidebar"] .sidebar-lang-block .stSelectbox > div > div:focus-within,
    section[data-testid="stSidebar"] .sidebar-lang-block div[data-baseweb="select"] > div:focus-within {{
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px var(--primary-soft) !important;
    }}
    section[data-testid="stSidebar"] .sidebar-lang-block .stSelectbox > label {{
        display: none !important;
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
        border-radius: var(--radius-card) !important;
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
        border-radius: var(--radius-pill);
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
        background: linear-gradient(135deg, var(--primary), var(--primary-hover));
        color: var(--text-on-primary) !important;
        border: none;
        border-radius: var(--radius-pill) !important;
        padding: 0.7rem 1.5rem;
        font-weight: 700;
        font-size: 0.92rem;
        box-shadow: var(--shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
    }}
    .stButton > button p {{
        color: var(--text-on-primary) !important;
    }}
    .stButton > button:hover {{
        filter: brightness(1.05);
        transform: translateY(-2px);
        box-shadow: var(--shadow-strong);
    }}
    .stButton > button:focus-visible {{
        outline: 3px solid var(--focus-ring);
        outline-offset: 2px;
    }}
    .stButton > button:active {{
        transform: translateY(0);
        filter: brightness(0.97);
    }}
    .stButton > button:disabled,
    .stButton > button[disabled] {{
        background: var(--border) !important;
        color: var(--text-muted) !important;
        box-shadow: none !important;
        cursor: not-allowed;
        transform: none !important;
        filter: none !important;
        opacity: 0.75;
    }}
    .stButton > button:disabled p {{
        color: var(--text-muted) !important;
    }}
    /* Streamlit's built-in "running" state (shown while a callback with
       a spinner is executing) — keep the button visibly active rather
       than looking identical to a plain disabled button. */
    .stButton > button.st-emotion-cache-running,
    .stButton[data-testid~="stButtonRunning"] > button {{
        background: linear-gradient(135deg, var(--primary), var(--primary-hover)) !important;
        color: var(--text-on-primary) !important;
        opacity: 0.85;
        cursor: progress;
    }}
    .stFormSubmitButton > button {{
        background: linear-gradient(135deg, var(--primary), var(--primary-hover));
        color: var(--text-on-primary) !important;
        width: 100%;
        min-height: 50px;
        border-radius: var(--radius-pill) !important;
        padding: 0.7rem 1.5rem;
        font-weight: 700;
        font-size: 0.98rem;
        letter-spacing: 0.01em;
        box-shadow: var(--shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
    }}
    .stFormSubmitButton > button p {{
        color: var(--text-on-primary) !important;
        font-weight: 700 !important;
    }}
    .stFormSubmitButton > button:hover {{
        filter: brightness(1.05);
        transform: translateY(-2px);
        box-shadow: var(--shadow-strong);
    }}
    .stFormSubmitButton > button:active {{
        transform: translateY(0);
        filter: brightness(0.97);
    }}
    .stFormSubmitButton > button:focus-visible {{
        outline: 3px solid var(--focus-ring);
        outline-offset: 2px;
    }}
    .stFormSubmitButton > button:disabled,
    .stFormSubmitButton > button[disabled] {{
        background: var(--border) !important;
        color: var(--text-muted) !important;
        box-shadow: none !important;
        cursor: not-allowed;
        transform: none !important;
        filter: none !important;
        opacity: 0.75;
    }}

    /* ---------- Radio buttons ---------- */
    .stRadio > label {{
        color: var(--text-secondary) !important;
        font-weight: 600;
        font-size: 0.85rem;
    }}
    .stRadio [role="radiogroup"] {{
        gap: 0.6rem;
    }}
    .stRadio [data-baseweb="radio"] {{
        background: transparent !important;
    }}
    .stRadio [data-baseweb="radio"] > div:first-child {{
        border-color: var(--border-strong) !important;
        background: var(--input-bg) !important;
    }}
    .stRadio [data-baseweb="radio"] input:checked + div {{
        border-color: var(--primary) !important;
    }}
    .stRadio [data-baseweb="radio"] input:checked + div > div {{
        background: var(--primary) !important;
    }}
    .stRadio label span[data-testid="stMarkdownContainer"] p,
    .stRadio label div {{
        color: var(--text-primary) !important;
        font-weight: 500;
    }}

    /* ---------- Text inputs / selects / textareas ---------- */
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] > div > div,
    div[data-baseweb="base-input"],
    textarea,
    .stTextInput input,
    .stTextArea textarea {{
        border-radius: var(--radius-input) !important;
        background: var(--input-bg) !important;
        border: 1.5px solid var(--border) !important;
        color: var(--text-primary) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
    }}
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div {{
        min-height: 48px;
    }}
    div[data-baseweb="input"]:hover,
    div[data-baseweb="select"] > div:hover {{
        border-color: var(--border-strong) !important;
    }}
    .stTextInput input, .stTextArea textarea {{
        padding: 0.85rem 1rem !important;
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
        box-shadow: 0 0 0 4px var(--primary-soft) !important;
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

    /* ---------- Dropdown menu / popover (rendered in a portal) ----------
       Covers every st.selectbox in the app — sidebar, Profile, Sign In,
       Sign Up, and any future ones — since Streamlit renders the open
       options list into one shared portal, not inside each widget. */
    ul[data-testid="stSelectboxVirtualDropdown"],
    div[data-baseweb="popover"] ul {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-input) !important;
        box-shadow: var(--shadow-strong) !important;
        padding: 4px !important;
    }}

    /* Base option text — same comfortable, high-contrast color as the
       rest of the app's primary text (soft off-white on dark, dark gray
       on light), so every option reads as clearly as the selected one. */
    ul[data-testid="stSelectboxVirtualDropdown"] li,
    div[data-baseweb="popover"] ul li,
    ul[data-testid="stSelectboxVirtualDropdown"] li *,
    div[data-baseweb="popover"] ul li * {{
        color: var(--text-primary) !important;
        background: transparent !important;
        font-weight: 500;
        border-radius: 8px !important;
        transition: background 0.15s ease, color 0.15s ease;
    }}

    /* Hover / keyboard-highlighted option */
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover,
    div[data-baseweb="popover"] ul li:hover,
    ul[data-testid="stSelectboxVirtualDropdown"] li[data-highlighted="true"],
    div[data-baseweb="popover"] ul li[data-highlighted="true"] {{
        background: var(--dropdown-hover) !important;
    }}
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover *,
    div[data-baseweb="popover"] ul li:hover *,
    ul[data-testid="stSelectboxVirtualDropdown"] li[data-highlighted="true"] *,
    div[data-baseweb="popover"] ul li[data-highlighted="true"] * {{
        background: transparent !important;
        color: var(--text-primary) !important;
    }}

    /* Selected option — accent color + soft highlighted background,
       clearly distinct from both the default and hover states. */
    ul[data-testid="stSelectboxVirtualDropdown"] li[aria-selected="true"],
    div[data-baseweb="popover"] ul li[aria-selected="true"] {{
        background: var(--primary-soft) !important;
    }}
    ul[data-testid="stSelectboxVirtualDropdown"] li[aria-selected="true"] *,
    div[data-baseweb="popover"] ul li[aria-selected="true"] * {{
        background: transparent !important;
        color: var(--primary) !important;
        font-weight: 700 !important;
    }}

    /* Keyboard focus ring for accessibility */
    ul[data-testid="stSelectboxVirtualDropdown"] li:focus-visible,
    div[data-baseweb="popover"] ul li:focus-visible {{
        outline: 2px solid var(--focus-ring) !important;
        outline-offset: -2px;
    }}

    /* ---------- File uploader / upload box ---------- */
    section[data-testid="stFileUploaderDropzone"] {{
        background: var(--surface) !important;
        border: 1.5px dashed var(--secondary-accent) !important;
        border-radius: var(--radius-card) !important;
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
        border-radius: var(--radius-input);
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
        border-radius: var(--radius-card);
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
        border-radius: var(--radius-card);
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
        border-radius: var(--radius-card) !important;
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
        border-radius: var(--radius-card);
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

    /* ---------- Profile page: large avatar, bio, danger zone ---------- */
    .profile-avatar-large {{
        width: 108px;
        height: 108px;
        border-radius: 50%;
        background: var(--primary-soft);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.4rem;
        font-family: 'Fraunces', serif;
        font-weight: 700;
        color: var(--primary) !important;
        border: 3px solid var(--card);
        box-shadow: var(--shadow);
        margin: 0 auto 0.9rem auto;
        overflow: hidden;
    }}
    .profile-avatar-large img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 50%;
    }}
    .profile-name {{
        font-family: 'Fraunces', serif;
        font-size: 1.25rem;
        font-weight: 700;
        text-align: center;
        color: var(--text-primary) !important;
        margin-bottom: 0.1rem;
    }}
    .profile-meta-row {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0;
        border-bottom: 1px dashed var(--border);
        color: var(--text-secondary) !important;
        font-size: 0.88rem;
    }}
    .profile-meta-row:last-child {{ border-bottom: none; }}
    .profile-meta-row .meta-icon {{
        flex-shrink: 0;
        width: 20px;
        text-align: center;
        color: var(--primary) !important;
    }}
    .profile-meta-row .meta-empty {{
        color: var(--text-muted) !important;
        font-style: italic;
    }}
    .bio-text {{
        color: var(--text-secondary) !important;
        line-height: 1.6;
        font-size: 0.92rem;
    }}
    .danger-zone-box {{
        border: 1px solid var(--error) !important;
        background: var(--error-bg) !important;
        border-radius: var(--radius-card);
        padding: 1rem 1.1rem;
        margin-top: 0.6rem;
    }}
    .danger-zone-box .danger-title {{
        color: var(--error) !important;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 0.3rem;
    }}
    .danger-zone-box .danger-desc {{
        color: var(--text-secondary) !important;
        font-size: 0.82rem;
        margin-bottom: 0.7rem;
    }}
    div[data-testid="stVerticalBlock"] > div.element-container:has(.danger-btn-marker)
        + div[data-testid="stButton"] > button {{
        background: var(--error) !important;
        color: var(--text-on-primary) !important;
    }}
    div[data-testid="stVerticalBlock"] > div.element-container:has(.danger-btn-marker)
        + div[data-testid="stButton"] > button:hover {{
        filter: brightness(0.92);
    }}
    .danger-btn-marker {{ display: none; }}

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
        border-radius: var(--radius-pill);
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
        border-radius: var(--radius-input);
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

    /* ================= AI CHAT ASSISTANT (floating widget) ================= */
    /* Floating circular toggle button, fixed bottom-right on every page. */
    .chat-fab-anchor {{
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999;
    }}
    .chat-fab-anchor .stButton > button {{
        width: 58px;
        height: 58px;
        border-radius: 50% !important;
        background: linear-gradient(135deg, var(--primary), var(--primary-hover)) !important;
        color: var(--text-on-primary) !important;
        font-size: 1.5rem;
        box-shadow: var(--shadow-strong) !important;
        border: none !important;
        padding: 0 !important;
        min-height: 0 !important;
        transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease;
    }}
    .chat-fab-anchor .stButton > button:hover {{
        transform: scale(1.08) translateY(-2px) !important;
    }}
    .chat-fab-anchor .stButton > button:active {{
        transform: scale(0.96) !important;
    }}

    /* Chat panel — fixed above the FAB, animates in on open. */
    .chat-panel-anchor {{
        position: fixed;
        bottom: 96px;
        right: 24px;
        width: 380px;
        max-width: calc(100vw - 32px);
        max-height: 70vh;
        z-index: 9998;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius-card);
        box-shadow: var(--shadow-strong);
        padding: 14px 16px 10px;
        display: flex;
        flex-direction: column;
        animation: chat-panel-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
        overflow: hidden;
    }}
    @keyframes chat-panel-in {{
        from {{ opacity: 0; transform: translateY(16px) scale(0.97); }}
        to   {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}
    @media (max-width: 480px) {{
        .chat-panel-anchor {{
            right: 16px;
            left: 16px;
            width: auto;
            bottom: 88px;
        }}
    }}

    .chat-panel-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 1.02rem;
        color: var(--text-primary);
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border);
        margin-bottom: 6px;
    }}
    .chat-online-dot {{
        font-size: 0.72rem;
        color: var(--success);
        font-weight: 600;
    }}

    .chat-messages {{
        overflow-y: auto;
        max-height: 42vh;
        padding: 4px 2px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        scroll-behavior: smooth;
    }}
    .chat-empty {{
        text-align: center;
        padding: 24px 8px;
        color: var(--text-muted);
    }}
    .chat-empty-title {{
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 4px;
    }}
    .chat-empty-sub {{
        font-size: 0.85rem;
        line-height: 1.4;
    }}
    .chat-row {{
        display: flex;
        animation: chat-msg-in 0.2s ease;
    }}
    @keyframes chat-msg-in {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .chat-bubble-user {{ justify-content: flex-end; }}
    .chat-bubble-ai {{ justify-content: flex-start; }}
    .chat-bubble {{
        max-width: 82%;
        padding: 9px 13px;
        border-radius: var(--radius-input);
        font-size: 0.88rem;
        line-height: 1.45;
        word-wrap: break-word;
    }}
    .chat-bubble-user .chat-bubble {{
        background: linear-gradient(135deg, var(--primary), var(--primary-hover));
        color: var(--text-on-primary);
        border-bottom-right-radius: 4px;
    }}
    .chat-bubble-ai .chat-bubble {{
        background: var(--surface);
        color: var(--text-primary);
        border: 1px solid var(--border);
        border-bottom-left-radius: 4px;
    }}

    /* Quick-suggestion chips + input row: keep them visually compact so
       the panel doesn't grow taller than the message list itself. */
    .chat-panel-anchor .stButton > button {{
        font-size: 0.76rem;
        padding: 0.3rem 0.5rem;
        border-radius: var(--radius-pill);
        min-height: 0;
    }}
    .chat-panel-anchor .stTextInput input {{
        min-height: 38px !important;
        padding: 0.5rem 0.8rem !important;
    }}
    .chat-panel-anchor .stFormSubmitButton > button {{
        min-height: 38px;
        border-radius: var(--radius-pill);
        padding: 0.4rem 0.6rem;
    }}

    /* ================================================================
       PREMIUM POLISH LAYER
       ================================================================ */
    .stButton > button,
    .stDownloadButton > button,
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"],
    .stTextInput input,
    .stTextArea textarea,
    section[data-testid="stSidebar"] .stButton > button,
    [data-testid="stFileUploaderDropzone"],
    .stRadio [data-baseweb="radio"] > div:first-child {{
        transition: transform 0.18s cubic-bezier(0.34, 1.56, 0.64, 1),
                    box-shadow 0.22s ease,
                    border-color 0.2s ease,
                    background-color 0.2s ease,
                    color 0.2s ease !important;
    }}
    .stButton > button:not(:disabled):hover,
    .stDownloadButton > button:not(:disabled):hover {{
        transform: translateY(-1px);
        box-shadow: var(--shadow-strong) !important;
    }}
    .stButton > button:not(:disabled):active,
    .stDownloadButton > button:not(:disabled):active {{
        transform: translateY(0px) scale(0.98);
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        transition: transform 0.22s ease, box-shadow 0.22s ease;
        box-shadow: var(--shadow) !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
        box-shadow: var(--shadow-strong) !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:not(:disabled):hover {{
        background: var(--primary-hover) !important;
        transform: translateX(2px);
    }}
    .stTextInput input:focus-visible,
    .stTextArea textarea:focus-visible,
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="input"]:focus-within {{
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px var(--primary-soft) !important;
    }}
    [class*="eyebrow"], .section-eyebrow {{
        letter-spacing: 0.08em;
        font-weight: 700;
        opacity: 0.85;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        border-radius: var(--radius-card) !important;
        border: 1.5px dashed var(--border-strong) !important;
        background: var(--surface) !important;
    }}
    [data-testid="stFileUploaderDropzone"]:hover {{
        border-color: var(--primary) !important;
        background: var(--primary-soft) !important;
    }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{
        background: var(--border-strong);
        border-radius: 8px;
        border: 2px solid transparent;
        background-clip: content-box;
    }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}
    @media (prefers-reduced-motion: reduce) {{
        * {{ transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; }}
    }}

    /* ---- Primary/secondary button hierarchy ---- */
    .stButton > button[kind="secondary"],
    .stFormSubmitButton > button[kind="secondary"] {{
        background: transparent !important;
        color: var(--text-secondary) !important;
        border: 1.5px solid var(--border-strong) !important;
        border-radius: var(--radius-pill) !important;
        font-weight: 600 !important;
        box-shadow: none !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        background: var(--surface) !important;
        border-color: var(--primary) !important;
        color: var(--primary) !important;
        transform: translateY(-1px);
    }}
    .stButton > button[kind="secondary"]:active {{
        transform: translateY(0) scale(0.98);
    }}
    div[class*="st-key-delete_"] .stButton > button[kind="secondary"]:hover {{
        border-color: var(--error) !important;
        color: var(--error) !important;
        background: var(--error-bg) !important;
    }}
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button {{
        font-weight: 700 !important;
        letter-spacing: 0.01em;
    }}
    section[data-testid="stSidebar"] .nav-active-marker {{
        border-radius: 0 6px 6px 0;
    }}
    section[data-testid="stSidebar"] .stButton > button {{
        font-weight: 600 !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(.stButton) {{
        margin-bottom: 0.15rem;
    }}

    /* Main CTA gets clear top-of-hierarchy prominence */
    div[class*="st-key-generate_btn"] .stButton > button {{
        font-size: 1.05rem !important;
        padding: 0.85rem 1.5rem !important;
        letter-spacing: 0.02em;
        box-shadow: var(--shadow-strong) !important;
    }}
    div[class*="st-key-generate_btn"] .stButton > button:hover {{
        transform: translateY(-2px) !important;
    }}
    </style>
    """