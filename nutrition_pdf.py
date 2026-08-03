"""
nutrition_pdf.py
-----------------
Renders a Smart Nutrition Assistant plan (profile + AI-generated
recommendation) into a simple, clean PDF for download. Kept as its own
module so the PDF-building logic doesn't clutter app.py and can be reused
or tested independently.
"""

import io
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem,
)

PRIMARY = colors.HexColor("#5A7D4D")
MUTED = colors.HexColor("#6E6E6E")
BORDER = colors.HexColor("#E7E2D8")


def _styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("title", parent=base["Title"], textColor=PRIMARY, fontSize=20),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], textColor=PRIMARY, spaceBefore=14, spaceAfter=6),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], textColor=colors.HexColor("#222222"), spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontSize=10, leading=14),
        "muted": ParagraphStyle("muted", parent=base["BodyText"], fontSize=9, textColor=MUTED),
    }
    return styles


def build_meal_plan_pdf(profile: dict, plan: dict, created_at: str = None) -> bytes:
    """Build a PDF (as bytes) summarizing the given nutrition profile and
    AI-generated plan. `profile` and `plan` use the same keys produced by
    gemini_helper.generate_nutrition_plan() / the Nutrition Assistant form.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    s = _styles()
    story = []

    story.append(Paragraph("VegiVision — Smart Nutrition Assistant", s["title"]))
    ts = created_at or datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    story.append(Paragraph(f"Generated: {ts}", s["muted"]))
    story.append(Spacer(1, 12))

    # Profile summary
    story.append(Paragraph("Your Profile", s["h2"]))
    profile_rows = [
        ["Age", str(profile.get("age", "—")), "Gender", str(profile.get("gender", "—"))],
        ["Height", f"{profile.get('height', '—')} cm", "Weight", f"{profile.get('weight', '—')} kg"],
        ["Activity Level", str(profile.get("activity_level", "—")), "Health Goal", str(profile.get("health_goal", "—"))],
        ["Dietary Preference", str(profile.get("dietary_preference", "—")), "Allergies", str(profile.get("allergies") or "None")],
    ]
    t = Table(profile_rows, colWidths=[3.2 * cm, 5.3 * cm, 3.2 * cm, 5.3 * cm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (2, 0), (2, -1), MUTED),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Nutrition summary
    story.append(Paragraph("Nutrition Summary", s["h2"]))
    macros = plan.get("macros", {}) or {}
    story.append(Paragraph(f"<b>Daily calorie target:</b> {plan.get('calorie_target', '—')}", s["body"]))
    story.append(Paragraph(
        f"<b>Macros:</b> Protein {macros.get('protein', '—')} · "
        f"Carbs {macros.get('carbs', '—')} · Fat {macros.get('fat', '—')}",
        s["body"],
    ))
    story.append(Paragraph(f"<b>Hydration goal:</b> {plan.get('hydration_goal', '—')}", s["body"]))
    story.append(Spacer(1, 8))

    # Meal plan
    story.append(Paragraph("Daily Meal Plan", s["h2"]))
    meal_plan = plan.get("meal_plan", {}) or {}
    for meal_key, meal_label in (
        ("breakfast", "Breakfast"), ("lunch", "Lunch"),
        ("snacks", "Snacks"), ("dinner", "Dinner"),
    ):
        items = meal_plan.get(meal_key) or []
        if not items:
            continue
        story.append(Paragraph(meal_label, s["h3"]))
        bullets = []
        for it in items:
            if isinstance(it, dict):
                text = f"<b>{it.get('item', '')}</b> — {it.get('reason', '')}"
            else:
                text = str(it)
            bullets.append(ListItem(Paragraph(text, s["body"])))
        story.append(ListFlowable(bullets, bulletType="bullet", start="•"))

    # Recommended vegetables
    veggies = plan.get("recommended_vegetables") or []
    if veggies:
        story.append(Paragraph("Recommended Vegetables", s["h2"]))
        bullets = []
        for v in veggies:
            if isinstance(v, dict):
                name = v.get("name", "")
                nutrient = v.get("nutrient", "")
                reason = v.get("reason", "")
                label = f"<b>{name}</b>"
                if nutrient:
                    label += f" (rich in {nutrient})"
                if reason:
                    label += f" — {reason}"
            else:
                label = str(v)
            bullets.append(ListItem(Paragraph(label, s["body"])))
        story.append(ListFlowable(bullets, bulletType="bullet", start="•"))

    # Substitutions
    subs = plan.get("substitutions") or []
    if subs:
        story.append(Paragraph("Healthier Substitutions", s["h2"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(str(x), s["body"])) for x in subs],
            bulletType="bullet", start="•",
        ))

    # Weekly tips
    tips = plan.get("weekly_tips") or []
    if tips:
        story.append(Paragraph("Weekly Healthy Eating Tips", s["h2"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(str(x), s["body"])) for x in tips],
            bulletType="bullet", start="•",
        ))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Generated by VegiVision's Smart Nutrition Assistant. This plan is AI-generated "
        "guidance, not medical advice — consult a healthcare professional for personalized "
        "medical or dietary requirements.",
        s["muted"],
    ))

    doc.build(story)
    return buf.getvalue()

