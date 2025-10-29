# brochure_builder.py (updated)
"""
brochure_builder.py — Agent 3: PDF Brochure Builder (continuous layout) with images

Usage:
    python brochure_builder.py
    python brochure_builder.py --job_id 20251022T115158Z-07805a17

Output:
    jobs/<job_id>/brochure_<job_id>.pdf
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
import math

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Frame,
    PageTemplate,
    Flowable,
    KeepTogether,
)
from reportlab.platypus.tables import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak

# Fonts
FONT_MAIN = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
try:
    if Path("Montserrat-Regular.ttf").exists() and Path("Montserrat-Bold.ttf").exists():
        pdfmetrics.registerFont(TTFont("Montserrat", "Montserrat-Regular.ttf"))
        pdfmetrics.registerFont(TTFont("Montserrat-Bold", "Montserrat-Bold.ttf"))
        FONT_MAIN = "Montserrat"
        FONT_BOLD = "Montserrat-Bold"
except Exception:
    pass

# Page settings
PAGE_SIZE = A4
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE
MARGINS = dict(left=48, right=48, top=60, bottom=72)

# Footer content and position
FOOTER_TEXT_LINE1 = "Contact: David P. Koch, Chief Commercial Officer  |  954-654-2997  |  dkoch@transradialtechnologies.com"
FOOTER_TEXT_LINE2 = "CAUTION - Investigational device. Limited by Federal (or United States) law to investigational use."

# Colors
PRIMARY = colors.HexColor("#1f497d")
ACCENT = colors.HexColor("#5b9bd5")
DIVIDER = colors.HexColor("#d9e6f6")
TEXT_COLOR = colors.HexColor("#222222")
CARD_BG = colors.HexColor("#f5f8fb")

# Horizontal divider
class HorizontalRule(Flowable):
    def __init__(self, width="100%", thickness=1, color=DIVIDER, space_before=6, space_after=6):
        super().__init__()
        self.width = width
        self.thickness = thickness
        self.color = color
        self.space_before = space_before
        self.space_after = space_after

    def wrap(self, availWidth, availHeight):
        return (availWidth, self.space_before + self.space_after + self.thickness)

    def draw(self):
        w = self.canv._pagesize[0] - (MARGINS["left"] + MARGINS["right"])
        x = MARGINS["left"]
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(x, 0 + self.space_after, x + w, 0 + self.space_after)



# === Custom Section Header with Colored Background ===
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable

class ColoredSectionHeader(Flowable):
    def __init__(self, text, width, height=18, bg_color=colors.HexColor("#c00000"), text_color=colors.white, font=FONT_BOLD, font_size=11, left_padding=6):
        super().__init__()
        self.text = text
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.text_color = text_color
        self.font = font
        self.font_size = font_size
        self.left_padding = left_padding

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height + 4)

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(self.bg_color)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.setFillColor(self.text_color)
        c.setFont(self.font, self.font_size)
        c.drawString(self.left_padding, 4, self.text)
        c.restoreState()

    

from reportlab.lib.utils import ImageReader

def draw_intro_background(canvas, doc):
    """
    Draws a background image behind the intro section on the first page.
    """
    try:
        bg_path = Path("image.webp")  # adjust path if needed
        if not bg_path.exists():
            return
        img = ImageReader(str(bg_path))
        # Adjusted height and position (roughly top 40% of page)
        img_height = PAGE_HEIGHT * 0.25
        img_y = PAGE_HEIGHT - img_height - 80  # slight upward shift

        canvas.saveState()
        canvas.drawImage(
            img,
            0,
            img_y,
            width=PAGE_WIDTH,
            height=img_height,
            mask='auto'
        )
        canvas.restoreState()
    except Exception as e:
        print("[warn] Failed to draw background image:", e)




# Paragraph styles (unique names)
def make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BrochureTitle", fontName=FONT_BOLD, fontSize=24, leading=28,
                              alignment=TA_CENTER, textColor=PRIMARY, spaceAfter=3))
    styles.add(ParagraphStyle(name="BrochureSubtitle", fontName=FONT_MAIN, fontSize=12, leading=16,
                              alignment=TA_CENTER, textColor=ACCENT, spaceAfter=10))
    styles.add(ParagraphStyle(name="Intro", fontName=FONT_MAIN, fontSize=10, leading=14,
                              alignment=TA_LEFT, textColor=colors.white, spaceAfter=10))
    styles.add(ParagraphStyle(name="SectionHeader", fontName=FONT_BOLD, fontSize=14, leading=16,
                              alignment=TA_LEFT, textColor=PRIMARY, spaceBefore=7, spaceAfter=4))
    styles.add(ParagraphStyle(name="BodyTextCustom", fontName=FONT_MAIN, fontSize=10, leading=13,
                              alignment=TA_LEFT, textColor=TEXT_COLOR, spaceAfter=4))
    styles.add(ParagraphStyle(name="BulletCustom", fontName=FONT_MAIN, fontSize=10, leading=13,
                              leftIndent=10, spaceAfter=4))
    styles.add(ParagraphStyle(name="FooterStyle", fontName=FONT_MAIN, fontSize=8, leading=8,
                              alignment=TA_CENTER, textColor=colors.HexColor("#666666")))
    styles.add(ParagraphStyle(name="CardTitle", fontName=FONT_BOLD, fontSize=10, leading=11,
                              alignment=TA_LEFT, textColor=PRIMARY))
    styles.add(ParagraphStyle(name="CardBody", fontName=FONT_MAIN, fontSize=10, leading=10,
                              alignment=TA_LEFT, textColor=TEXT_COLOR))
    return styles

# Footer drawing (used for every page)
def draw_footer(canvas, doc):
    canvas.saveState()

    footer_height = 40
    footer_y = 0  # absolute bottom of page

    orange = colors.HexColor("#f57c00")
    canvas.setFillColor(orange)
    canvas.rect(0, footer_y, PAGE_WIDTH, footer_height, fill=1, stroke=0)

    # Text (white on orange background)
    canvas.setFillColor(colors.white)
    canvas.setFont(FONT_MAIN, 8)
    canvas.drawCentredString(PAGE_WIDTH / 2, footer_y + 22, FOOTER_TEXT_LINE1)
    canvas.drawCentredString(PAGE_WIDTH / 2, footer_y + 10, FOOTER_TEXT_LINE2)

    canvas.restoreState()




# Safe paragraph
def p(text, style):
    if not text:
        text = ""
    return Paragraph(text, style)

# Image helpers
def text_with_image(text, image_path, styles, image_width=120, image_height=90):
    """
    70% text / 30% image using usable width (accounts for margins).
    Ensures vertical top alignment for the image and text.
    """
    from reportlab.platypus import Table, TableStyle
    usable = PAGE_WIDTH - (MARGINS["left"] + MARGINS["right"])
    col_text = usable * 0.7
    col_image = usable * 0.3
    text_paragraph = Paragraph(text, styles["Intro"])
    img = None
    if image_path and Path(image_path).exists():
        img = Image(str(image_path), width=col_image - 6, height=image_height)  # small padding
    if img:
        table = Table([[text_paragraph, img]], colWidths=[col_text, col_image])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        return table
    else:
        return Paragraph(text, styles["Intro"])

def horizontal_images(image_paths, max_width_percent=0.9, gap=12, max_height=140):
    """
    Place up to 3 images horizontally, sized to fit the usable width with gap spacing.
    Skips invalid/missing images safely.
    """
    from reportlab.platypus import Table, TableStyle, Spacer
    usable = PAGE_WIDTH - (MARGINS["left"] + MARGINS["right"])

    # keep only valid existing images
    imgs_paths = [Path(p) for p in image_paths[:3] if p and Path(p).exists()]
    if not imgs_paths:
        return Spacer(1, 1)

    n = len(imgs_paths)
    if n == 0:
        return Spacer(1, 1)

    total_gap = gap * (n - 1)
    max_total_width = usable * max_width_percent
    img_width = max((max_total_width - total_gap) / n, 10)  # ensure >0
    img_height = max_height

    # build image list safely
    imgs = []
    for p in imgs_paths:
        try:
            imgs.append(Image(str(p), width=img_width, height=img_height))
        except Exception:
            continue  # skip corrupted image files

    if not imgs:
        return Spacer(1, 1)

    # Create the table
    table = Table([imgs], colWidths=[img_width] * len(imgs), hAlign='CENTER')
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), gap / 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), gap / 2),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


# Build "cards" grid for competitive advantages
def advantages_grid(advantages, styles):
    """
    Render advantages as 3-column cards. Each card has a light background and contains a title + short body.
    This function returns a list of flowables (each flowable is a KeepTogether(row_table)),
    so caller should extend() the story with the returned list.
    """
    if not advantages:
        return None

    cards = advantages[:6]
    card_contents = []  # store content blocks (not tables yet)

    for adv in cards:
        title = adv.get("advantage", "")
        expl = adv.get("explanation", "")
        if expl:
            sentences = [s.strip() for s in expl.split(".") if s.strip()]
            if len(sentences) < 2:
                expl = expl.rstrip(".") + ". This contributes to improved outcomes and practical benefits."
        else:
            expl = "Details not fully described in provided documents."

        # card content: a simple vertical stack (Paragraphs) - do NOT KeepTogether here
        content_block = [
            Paragraph(f"<b>{title}</b>", styles["CardTitle"]),
            Spacer(1, 4),
            Paragraph(expl, styles["CardBody"])
        ]
        card_contents.append(content_block)

    # arrange into rows of 3
    rows = []
    row = []
    for i, c in enumerate(card_contents):
        row.append(c)
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        # pad empty cells with a minimal spacer column
        while len(row) < 3:
            row.append([Spacer(1, 1)])
        rows.append(row)

    usable = PAGE_WIDTH - (MARGINS["left"] + MARGINS["right"])
    col_w = usable / 3.0

    flowables = []
    for r in rows:
        # For each cell content, build a single-cell table with the known column width
        cell_tables = []
        for c in r:
            # c is a list of flowables (Paragraph, Spacer, Paragraph)
            # create a table cell with fixed width col_w
            tcell = Table([[c]], colWidths=[col_w])
            tcell.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, DIVIDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            cell_tables.append(tcell)

        # assemble the row table (1 x up to 3 cols)
        trow = Table([cell_tables], colWidths=[col_w] * len(cell_tables), hAlign="CENTER")
        trow.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        # keep each row together but allow rows to break across pages
        flowables.append(KeepTogether(trow))

    return flowables


# Red title block (background rectangle + title text)
class TitleBlock(Flowable):
    """
    Draws a red rectangle behind the title text, centered horizontally.
    """
    def __init__(self, title, subtitle="", width=PAGE_WIDTH - 100, height=60,
                 bg_color=colors.HexColor("#d32f2f"), text_color=colors.white):
        super().__init__()
        self.title = title
        self.subtitle = subtitle
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.text_color = text_color

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height + 10)

    def draw(self):
        c = self.canv
        x = (PAGE_WIDTH - self.width) / 2
        y = 0

        # draw background rectangle
        c.setFillColor(self.bg_color)
        c.rect(x, y, self.width, self.height, fill=1, stroke=0)

        # draw title text
        c.setFillColor(self.text_color)
        c.setFont(FONT_BOLD, 20)
        text_y = y + self.height / 2 + 4
        c.drawCentredString(PAGE_WIDTH / 2, text_y, self.title)

        # optional subtitle below title
        if self.subtitle:
            c.setFont(FONT_MAIN, 10)
            c.drawCentredString(PAGE_WIDTH / 2, text_y - 16, self.subtitle)



# Generate PDF
def build_pdf_from_brochure(brochure: dict, output_path: Path, company_name: str = "Transradial"):
    styles = make_styles()
    story = []

    # Images folder
    images_dir = Path("./data/images")
    img_list = sorted(images_dir.glob("*.*"))  # allow jpg/png etc.
    # convert to Path list and filter by extension
    img_list = [p for p in img_list if p.suffix.lower() in (".jpg", ".jpeg", ".png")]

    # Title block
    story.append(Spacer(1, 18))
    story.append(
        TitleBlock(
            title=brochure.get("title", company_name),
            subtitle=brochure.get("subtitle", ""),
            width=PAGE_WIDTH,  # adjust width if you want a narrower block
            height=60,
            bg_color=colors.HexColor("#c62828"),  # deep red
            text_color=colors.white
        )
    )   
    story.append(Spacer(1, 16))


    # Intro + first image (70/30)
    first_image = img_list[0] if len(img_list) >= 1 else None
    if brochure.get("intro_summary"):
        story.append(text_with_image(brochure.get("intro_summary"), first_image, styles, image_height=110))
        story.append(Spacer(1, 6))

    story.append(HorizontalRule(space_before=6, space_after=10))

    # Key features (ensure 2+ sentences where possible)
    key_features = brochure.get("key_features", []) or []
    if key_features:
        story.append(ColoredSectionHeader("✨ Key Features", PAGE_WIDTH - (MARGINS["left"] + MARGINS["right"]), height=18))
        story.append(Spacer(1, 6))

        for feat in key_features[:6]:
            title = feat.get("feature", "")
            desc = feat.get("description", "") or ""
            # if description has only one sentence, append a neutral safe expansion
            sentences = [s.strip() for s in desc.split(".") if s.strip()]
            if len(sentences) < 2:
                if desc:
                    desc = desc.rstrip(".") + ". This feature helps improve outcomes and deliver practical benefits."
                else:
                    desc = "Details not fully specified in the provided documents."
            story.append(Paragraph(f"<b>{title}</b>", styles["BulletCustom"]))
            story.append(Paragraph(desc, styles["BodyTextCustom"]))
        story.append(Spacer(1, 8))
        story.append(HorizontalRule(space_before=6, space_after=10))

    # === MOVED: place horizontal images BEFORE Competitive Advantages ===
    hor_images = [str(p) for p in img_list[1:4]] if len(img_list) >= 2 else []
    story.append(horizontal_images(hor_images, max_height=140))
    story.append(Spacer(1, 6))
    story.append(HorizontalRule(space_before=6, space_after=10))
    # === end moved block ===

    # Competitive advantages as cards
    advantages = brochure.get("competitive_advantages", []) or []
    if advantages:
        story.append(PageBreak())     # start new page before advantages

        story.append(ColoredSectionHeader("🏆 Competitive Advantages", PAGE_WIDTH - (MARGINS["left"] + MARGINS["right"]), height=18))
        story.append(Spacer(1, 6))
        grid = advantages_grid(advantages, styles)
        if grid:
            if isinstance(grid, list):
                story.extend(grid)  # grid is a list of KeepTogether row tables
            else:
                story.append(grid)

            story.append(Spacer(1, 8))
        story.append(HorizontalRule(space_before=6, space_after=10))

    # How it works
    how_it_works = brochure.get("how_it_works", [])
    if not how_it_works:
        # fallback when missing: safe neutral high-level steps
        how_it_works = [
            {"step": 1, "title": "Preparation", "description": "Prepare the clinical environment and confirm patient eligibility. Follow device handling and safety guidelines as described in the documentation."},
            {"step": 2, "title": "Procedure", "description": "Perform the procedure using standard technique and the recommended accessories. Ensure monitoring and sterile technique throughout."},
            {"step": 3, "title": "Post-procedure Care", "description": "Monitor patient recovery, follow recommended post-procedure protocols, and schedule follow-up as needed."}
        ]

    if how_it_works:
        # (removed the previous images placement here — images are now before advantages)
        story.append(Spacer(1, 6))
        story.append(ColoredSectionHeader("⚙️ How It Works", PAGE_WIDTH - (MARGINS["left"] + MARGINS["right"]), height=18))
        story.append(Spacer(1, 6))
        for step in how_it_works[:5]:
            step_num = step.get("step") if step.get("step") is not None else ""
            title_text = f"<b>Step {step_num}</b>"
            if step.get("title"):
                title_text += f": {step.get('title')}"
            desc = step.get("description", "")
            if not desc:
                desc = "Detailed procedure steps are not available in the provided documents."
            story.append(Paragraph(title_text, styles["BulletCustom"]))
            story.append(Paragraph(desc, styles["BodyTextCustom"]))
        story.append(Spacer(1, 8))
        story.append(HorizontalRule(space_before=6, space_after=10))

    # Additional insights (pad if short)
    additional = brochure.get("additional_insights", "") or ""
    if additional:
        # pad if too short
        if len(additional.strip()) < 120:
            additional = additional.rstrip(".") + ". For more detailed case studies and performance data, please refer to the full documentation or contact our commercial team."
        story.append(ColoredSectionHeader("💡 Additional Insights", PAGE_WIDTH - (MARGINS["left"] + MARGINS["right"]), height=18))
        story.append(Spacer(1, 6))
        story.append(Paragraph(additional, styles["BodyTextCustom"]))
        story.append(Spacer(1, 8))
        story.append(HorizontalRule(space_before=6, space_after=10))

    # Footer block (also included on every page via draw_footer)
    story.append(Spacer(1, 10))
    story.append(Paragraph(FOOTER_TEXT_LINE1, styles["BodyTextCustom"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(FOOTER_TEXT_LINE2, styles["BodyTextCustom"]))

    # Build PDF with footer on every page (onPage and onPageEnd)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=PAGE_SIZE,
        leftMargin=MARGINS["left"],
        rightMargin=MARGINS["right"],
        topMargin=MARGINS["top"],
        bottomMargin=MARGINS["bottom"],
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    
    def first_page(canvas, doc):
        draw_intro_background(canvas, doc)  # background behind intro
        draw_footer(canvas, doc)

    def later_pages(canvas, doc):
        draw_footer(canvas, doc)

    # Define two templates: one for the first page, one for subsequent pages
    template_first = PageTemplate(id="FirstPage", frames=[frame], onPage=first_page)
    template_later = PageTemplate(id="LaterPages", frames=[frame], onPage=later_pages)

    doc.addPageTemplates([template_first, template_later])

    doc.build(story)
    print(f"[brochure_builder] Brochure PDF written to: {output_path}")

# Latest job folder
def find_latest_job(jobs_root: Path) -> Path:
    if not jobs_root.exists():
        raise FileNotFoundError(f"Jobs root does not exist: {jobs_root}")
    subdirs = [d for d in jobs_root.iterdir() if d.is_dir()]
    if not subdirs:
        raise FileNotFoundError("No job folders found in jobs/")
    latest = max(subdirs, key=lambda d: d.stat().st_mtime)
    return latest

def main():
    parser = argparse.ArgumentParser(description="Brochure PDF Builder")
    parser.add_argument("--job_id", help="Job ID (folder name under jobs/). If omitted, uses latest job.")
    parser.add_argument("--jobs_root", default="./jobs", help="Jobs folder root")
    parser.add_argument("--out_name", default=None, help="Optional output PDF filename (overrides default)")
    args = parser.parse_args()

    jobs_root = Path(args.jobs_root)
    if args.job_id:
        job_dir = jobs_root / args.job_id
    else:
        job_dir = find_latest_job(jobs_root)

    if not job_dir.exists():
        raise FileNotFoundError(f"Job folder not found: {job_dir}")

    brochure_json = job_dir / "brochure.json"
    if not brochure_json.exists():
        raise FileNotFoundError(f"brochure.json not found in {job_dir}. Run summarizer first.")

    with open(brochure_json, "r", encoding="utf-8") as fh:
        brochure = json.load(fh)

    # Build PDF filename
    if args.out_name:
        out_path = job_dir / args.out_name
    else:
        safe_id = job_dir.name.replace(":", "_").replace("/", "_")
        out_path = job_dir / f"brochure_{safe_id}.pdf"

    build_pdf_from_brochure(brochure, out_path, company_name="Transradial")
    print("[brochure_builder] Done.")

if __name__ == "__main__":
    main()
