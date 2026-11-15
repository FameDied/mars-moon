import sys
import os
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_atlas_x_presentation(output_path="ATLAS-X_Planetary_Architecture_Presentation.pptx"):
    prs = Presentation()
    # 16:9 Widescreen standard
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Authentic ATLAS-X Theme Color Palette
    C_VOID = RGBColor(4, 7, 11)             # #04070B deep void
    C_CARD = RGBColor(11, 18, 30)            # #0B121E hud card surface
    C_CARD_ALT = RGBColor(15, 23, 42)        # #0F172A slate accent card
    C_CARD_HOVER = RGBColor(19, 31, 51)      # #131F33 elevated card
    C_BORDER = RGBColor(30, 43, 66)          # #1E2B42 hairline border
    C_BORDER_BRIGHT = RGBColor(56, 78, 115)  # #384E73 active hairline
    C_CYAN = RGBColor(56, 189, 248)          # #38BDF8 orbit sky blue
    C_EMERALD = RGBColor(16, 185, 129)       # #10B981 go green
    C_ROSE = RGBColor(239, 68, 68)           # #EF4444 nogo red
    C_AMBER = RGBColor(245, 158, 11)         # #F59E0B solar amber
    C_WHITE = RGBColor(255, 255, 255)        # #FFFFFF pure white
    C_LIGHT = RGBColor(226, 232, 240)        # #E2E8F0 text primary
    C_MUTED = RGBColor(148, 163, 184)        # #94A3B8 text secondary
    C_DIM = RGBColor(100, 116, 139)          # #64748B text dim
    C_PH_BG = RGBColor(7, 13, 23)            # #070D17 placeholder bg
    C_PH_BORDER = RGBColor(45, 80, 122)      # #2D507A placeholder border
    C_PH_DASH = RGBColor(56, 189, 248)       # #38BDF8 accent highlight

    FONT_TITLE = "Helvetica"
    FONT_BODY = "Arial"
    FONT_MONO = "Courier New"

    def add_bg_and_header(slide, slide_num, total_slides, eyebrow_text, title_text, category_badge="ATLAS-X ARCHITECTURE"):
        # Full void background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_VOID
        bg.line.fill.background()

        # Top subtle glow hairline
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.35), Inches(11.733), Inches(0.015))
        line.fill.solid()
        line.fill.fore_color.rgb = C_BORDER
        line.line.fill.background()

        # Eyebrow & Category Badges
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.44), Inches(9.8), Inches(0.28))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        
        # Pill Tag: ATLAS-X
        r_pill = p.add_run()
        r_pill.text = "ATLAS-X MISSION CONTROL  //  "
        r_pill.font.name = FONT_MONO
        r_pill.font.size = Pt(9.5)
        r_pill.font.bold = True
        r_pill.font.color.rgb = C_CYAN

        # Eyebrow track description
        r_cat = p.add_run()
        r_cat.text = eyebrow_text.upper()
        r_cat.font.name = FONT_MONO
        r_cat.font.size = Pt(9.5)
        r_cat.font.color.rgb = C_MUTED

        # Slide Number Indicator (Top Right)
        num_box = slide.shapes.add_textbox(Inches(10.6), Inches(0.44), Inches(1.933), Inches(0.28))
        tf_num = num_box.text_frame
        tf_num.word_wrap = False
        tf_num.margin_left = tf_num.margin_top = tf_num.margin_right = tf_num.margin_bottom = 0
        p_num = tf_num.paragraphs[0]
        p_num.alignment = PP_ALIGN.RIGHT
        r_num = p_num.add_run()
        r_num.text = f"SLIDE {slide_num:02d} / {total_slides:02d}"
        r_num.font.name = FONT_MONO
        r_num.font.size = Pt(10)
        r_num.font.bold = True
        r_num.font.color.rgb = C_EMERALD

        # Title / Headline
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.733), Inches(0.65))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_t = tf_title.paragraphs[0]
        r_t = p_t.add_run()
        r_t.text = title_text
        r_t.font.name = FONT_TITLE
        r_t.font.size = Pt(21)
        r_t.font.bold = True
        r_t.font.color.rgb = C_WHITE

        # Divider hairline under title
        div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.42), Inches(11.733), Inches(0.015))
        div.fill.solid()
        div.fill.fore_color.rgb = C_BORDER
        div.line.fill.background()

        # Bottom footer bar with mission telemetry
        ft_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.12), Inches(11.733), Inches(0.25))
        tf_ft = ft_box.text_frame
        tf_ft.word_wrap = True
        tf_ft.margin_left = tf_ft.margin_top = tf_ft.margin_right = tf_ft.margin_bottom = 0
        p_ft = tf_ft.paragraphs[0]
        r_ft = p_ft.add_run()
        r_ft.text = "ATLAS-X: Physics-First Planetary Base Architecture • Discrete Global H3 (Res 6/7) • 37 Tables • 524 Sites • Apache 2.0 Open Science"
        r_ft.font.name = FONT_MONO
        r_ft.font.size = Pt(8.5)
        r_ft.font.color.rgb = C_DIM

    def create_card(slide, left, top, width, height, border_color=C_BORDER, fill_color=C_CARD):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = fill_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.2)
        return card

    def create_placeholder(slide, left, top, width, height, title, subtitle, spec_hint, aspect_ratio="16:9 HD", is_split=False):
        # Placeholder Outer Container
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        box.fill.solid()
        box.fill.fore_color.rgb = C_PH_BG
        box.line.color.rgb = C_PH_BORDER
        box.line.width = Pt(1.5)

        # Top Cyan Accent Indicator Bar
        accent_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Inches(0.04))
        accent_bar.fill.solid()
        accent_bar.fill.fore_color.rgb = C_CYAN
        accent_bar.line.fill.background()

        # HUD Corner Crosshair Marks [+]
        tick_offset = Inches(0.12)
        tick_size = Inches(0.2)
        for tx, ty in [(left + tick_offset, top + tick_offset),
                       (left + width - tick_offset - tick_size, top + tick_offset),
                       (left + tick_offset, top + height - tick_offset - tick_size),
                       (left + width - tick_offset - tick_size, top + height - tick_offset - tick_size)]:
            tbox = slide.shapes.add_textbox(tx, ty, tick_size, tick_size)
            ttf = tbox.text_frame
            ttf.word_wrap = False
            ttf.margin_left = ttf.margin_top = ttf.margin_right = ttf.margin_bottom = 0
            tp = ttf.paragraphs[0]
            tr = tp.add_run()
            tr.text = "+"
            tr.font.name = FONT_MONO
            tr.font.size = Pt(10)
            tr.font.color.rgb = C_BORDER_BRIGHT

        # Inner Content Frame
        tf = box.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = Inches(0.3)
        tf.margin_right = Inches(0.3)
        tf.margin_top = Inches(0.2 if not is_split else 0.1)
        tf.margin_bottom = Inches(0.2 if not is_split else 0.1)

        # Line 1: Badge
        p1 = tf.paragraphs[0]
        p1.alignment = PP_ALIGN.CENTER
        r1 = p1.add_run()
        r1.text = "⬡ SCREENSHOT PLACEHOLDER ⬡\n"
        r1.font.name = FONT_MONO
        r1.font.size = Pt(9 if is_split else 10)
        r1.font.bold = True
        r1.font.color.rgb = C_CYAN

        # Line 2: Title
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = f"{title.upper()}\n"
        r2.font.name = FONT_TITLE
        r2.font.size = Pt(11.5 if is_split else 13.5)
        r2.font.bold = True
        r2.font.color.rgb = C_WHITE

        # Line 3: Detailed Description
        p3 = tf.add_paragraph()
        p3.alignment = PP_ALIGN.CENTER
        r3 = p3.add_run()
        r3.text = f"{subtitle}\n\n" if not is_split else f"{subtitle}\n"
        r3.font.name = FONT_BODY
        r3.font.size = Pt(8.5 if is_split else 9.5)
        r3.font.color.rgb = C_LIGHT

        # Line 4: Tech Specification & Insertion Tip
        p4 = tf.add_paragraph()
        p4.alignment = PP_ALIGN.CENTER
        r4 = p4.add_run()
        r4.text = f"⚙ {spec_hint}  •  Format: {aspect_ratio}\n"
        r4.font.name = FONT_MONO
        r4.font.size = Pt(7.5 if is_split else 8.5)
        r4.font.color.rgb = C_EMERALD

        if not is_split:
            r4_sub = p4.add_run()
            r4_sub.text = "[ In PowerPoint: Format Shape → Picture Fill, or Paste image over this box ]"
            r4_sub.font.name = FONT_MONO
            r4_sub.font.size = Pt(7.5)
            r4_sub.font.color.rgb = C_DIM

        return box

    print("Generating Slide 1: Title & Core Problem...")
    # ==========================================
    # SLIDE 1: Title & The Core Problem (Architecture Overview)
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    add_bg_and_header(s1, 1, 7, "Architecture Overview", "ATLAS-X: Physics-First Planetary Base Architecture & Split-Twin Analog Engine")

    col1_w = Inches(5.6)
    c1_left = Inches(0.8)

    # Card 1: Problem 1 - Fake 99% Matches
    c1_1 = create_card(s1, c1_left, Inches(1.65), col1_w, Inches(1.35), border_color=C_ROSE)
    s1_ind1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, c1_left, Inches(1.65), Inches(0.08), Inches(1.35))
    s1_ind1.fill.solid(); s1_ind1.fill.fore_color.rgb = C_ROSE; s1_ind1.line.fill.background()
    tf = c1_1.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.08)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "THE FATAL FLAW IN LEGACY ANALOG TOOLS\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_ROSE
    p_b = tf.add_paragraph()
    r = p_b.add_run(); r.text = "Legacy analog tools claim fake \"99% Earth matches\" by ignoring gravity (0.165g Moon / 0.38g Mars), vacuum, and cosmic radiation. Fake high scores create catastrophic engineering blindspots."; r.font.name = FONT_BODY; r.font.size = Pt(10); r.font.color.rgb = C_LIGHT

    # Card 2: Problem 2 - Surface Realities
    c1_2 = create_card(s1, c1_left, Inches(3.12), col1_w, Inches(1.35), border_color=C_AMBER)
    s1_ind2 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, c1_left, Inches(3.12), Inches(0.08), Inches(1.35))
    s1_ind2.fill.solid(); s1_ind2.fill.fore_color.rgb = C_AMBER; s1_ind2.line.fill.background()
    tf = c1_2.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.08)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "PERMANENT BASES DEMAND MULTI-DOMAIN SURVIVAL\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_AMBER
    p_b = tf.add_paragraph()
    r = p_b.add_run(); r.text = "Permanent bases require more than flat ground—they require supersonic plume-safe pads (>1.5 km separation), basalt lava tube radiation shielding, and multi-day eclipse power survival."; r.font.name = FONT_BODY; r.font.size = Pt(10); r.font.color.rgb = C_LIGHT

    # Card 3: Problem 3 - Deterministic Solution
    c1_3 = create_card(s1, c1_left, Inches(4.59), col1_w, Inches(1.35), border_color=C_EMERALD)
    s1_ind3 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, c1_left, Inches(4.59), Inches(0.08), Inches(1.35))
    s1_ind3.fill.solid(); s1_ind3.fill.fore_color.rgb = C_EMERALD; s1_ind3.line.fill.background()
    tf = c1_3.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.08)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "THE ATLAS-X ZERO-HALLUCINATION SOLUTION\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_EMERALD
    p_b = tf.add_paragraph()
    r = p_b.add_run(); r.text = "A deterministic, zero-hallucination decision engine harmonizing 37 NASA, USGS, and ESA datasets into Uber H3 grids with analytic Taylor uncertainty bounds."; r.font.name = FONT_BODY; r.font.size = Pt(10); r.font.color.rgb = C_LIGHT

    # Live Links Card (Bottom Left)
    link_c = create_card(s1, c1_left, Inches(6.06), col1_w, Inches(0.88), border_color=C_CYAN, fill_color=C_CARD_ALT)
    tf_l = link_c.text_frame; tf_l.word_wrap = True
    tf_l.margin_left = Inches(0.2); tf_l.margin_top = Inches(0.06); tf_l.margin_right = Inches(0.15); tf_l.margin_bottom = Inches(0.06)
    p1 = tf_l.paragraphs[0]
    r = p1.add_run(); r.text = "🌐 LIVE APP: "; r.font.name = FONT_MONO; r.font.size = Pt(8); r.font.bold = True; r.font.color.rgb = C_CYAN
    r_url = p1.add_run(); r_url.text = "famedied.github.io/mars-moon  "; r_url.font.name = FONT_MONO; r_url.font.size = Pt(8); r_url.font.bold = True; r_url.font.color.rgb = C_WHITE
    r_url.hyperlink.address = "https://famedied.github.io/mars-moon/"
    r = p1.add_run(); r.text = "🐙 REPO: "; r.font.name = FONT_MONO; r.font.size = Pt(8); r.font.bold = True; r.font.color.rgb = C_EMERALD
    r_gh = p1.add_run(); r_gh.text = "github.com/FameDied/mars-moon\n"; r_gh.font.name = FONT_MONO; r_gh.font.size = Pt(8); r_gh.font.bold = True; r_gh.font.color.rgb = C_WHITE
    r_gh.hyperlink.address = "https://github.com/FameDied/mars-moon"
    p2 = tf_l.add_paragraph()
    r = p2.add_run(); r.text = "📄 ARCHITECTURE PDF: "; r.font.name = FONT_MONO; r.font.size = Pt(8); r.font.bold = True; r.font.color.rgb = C_AMBER
    r_pdf = p2.add_run(); r_pdf.text = "famedied.github.io/mars-moon/atlas-x-architecture.pdf"; r_pdf.font.name = FONT_MONO; r_pdf.font.size = Pt(8); r_pdf.font.bold = True; r_pdf.font.color.rgb = C_WHITE
    r_pdf.hyperlink.address = "https://famedied.github.io/mars-moon/atlas-x-architecture.pdf"

    # Right Column: Screenshot Placeholder (Full-bleed Hero Earth Horizon)
    create_placeholder(s1, Inches(6.65), Inches(1.65), Inches(5.88), Inches(5.26),
                       title="Hero Earth Horizon & Live App View",
                       subtitle="Full-bleed screenshot of your Hero Earth horizon\n+ live URL (famedied.github.io/mars-moon) & GitHub repo\n(showing glowing atmosphere + orbit telemetry HUD)",
                       spec_hint="Live 3D Horizon View (famedied.github.io/mars-moon)",
                       aspect_ratio="16:9 HD")

    print("Generating Slide 2: System Architecture & Data Provenance...")
    # ==========================================
    # SLIDE 2: System Architecture & Data Provenance
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    add_bg_and_header(s2, 2, 7, "Data Provenance", "System Architecture & Multi-Agency Data Provenance")

    # Top: 4 Key Numbers Stat Banners
    stat_w = Inches(2.78)
    stat_h = Inches(1.22)
    stats = [
        ("37", "HARMONIZED TABLES", "NASA PDS, USGS, ESA, JAXA, JSC Astromaterials", C_CYAN),
        ("524", "CANDIDATE SITES", "Uber H3 Res 6 & 7 (Extraterrestrial Targets)", C_EMERALD),
        ("12", "UNDER-STUDIED ANALOGS", "Peer-Reviewed DOIs & Wolf Diplomatic Tags", C_AMBER),
        ("0ms", "SQLITE 3 + FTS5 + PARQUET", "Local zero-latency indexed analytical queries", C_WHITE)
    ]
    for i, (num, label, desc, color) in enumerate(stats):
        sx = Inches(0.8) + i * Inches(2.98)
        sc = create_card(s2, sx, Inches(1.65), stat_w, stat_h, border_color=C_BORDER)
        sacc = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, sx, Inches(1.65), stat_w, Inches(0.04))
        sacc.fill.solid(); sacc.fill.fore_color.rgb = color; sacc.line.fill.background()
        tf = sc.text_frame; tf.word_wrap = True
        tf.margin_left = Inches(0.15); tf.margin_top = Inches(0.10); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.08)
        p = tf.paragraphs[0]
        r = p.add_run(); r.text = num; r.font.name = FONT_TITLE; r.font.size = Pt(23); r.font.bold = True; r.font.color.rgb = color
        p2 = tf.add_paragraph()
        r = p2.add_run(); r.text = label; r.font.name = FONT_MONO; r.font.size = Pt(8.5); r.font.bold = True; r.font.color.rgb = C_WHITE
        p3 = tf.add_paragraph()
        r = p3.add_run(); r.text = desc; r.font.name = FONT_BODY; r.font.size = Pt(7.5); r.font.color.rgb = C_MUTED

    # Middle-Left: Clean 4-Step Pipeline Flow Diagram
    pipe_left = Inches(0.8)
    pipe_top = Inches(3.05)
    pipe_w = Inches(6.0)
    steps_s2 = [
        ("STEP 1: EXTRATERRESTRIAL NO-GO & MAUT",
         "Eliminates tip-over slope (>10°), boulders (>5%), polar shadows (<80% solar), thin atmosphere (z > -2,000m). Computes continuous utility S-curves.",
         C_ROSE),
        ("STEP 2: ANTI-CLICHÉ EARTH SCREENING",
         "Applies spatial novelty prior (P_novelty) suppressing over-studied sites (Antarctica/Atacama) by 85%. Enforces Wolf Amendment & diplomatic field-access tags.",
         C_AMBER),
        ("STEP 3: DIMENSIONLESS PHYSICS & AITCHISON SIMPLEX",
         "Transforms geochemical mineralogy into Aitchison simplex space (isometric log-ratios). Evaluates Ledoit-Wolf covariance shrinkage & delta vectors (g, P, rad).",
         C_CYAN),
        ("STEP 4: DECISION SCORECARDS & UNCERTAINTY",
         "Propagates sensor-resolution variances via first-order Taylor expansion (±1.96σ LCB). 1,000-trial Monte Carlo stability confirms >90% rank retention.",
         C_EMERALD)
    ]
    step_h = Inches(0.88)
    step_gap = Inches(0.12)
    for idx, (stitle, sdesc, scolor) in enumerate(steps_s2):
        sy = pipe_top + idx * (step_h + step_gap)
        scard = create_card(s2, pipe_left, sy, pipe_w, step_h, border_color=C_BORDER)
        sind = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, pipe_left, sy, Inches(0.06), step_h)
        sind.fill.solid(); sind.fill.fore_color.rgb = scolor; sind.line.fill.background()
        stf = scard.text_frame; stf.word_wrap = True
        stf.margin_left = Inches(0.2); stf.margin_top = Inches(0.08); stf.margin_right = Inches(0.15); stf.margin_bottom = Inches(0.06)
        p = stf.paragraphs[0]
        r = p.add_run(); r.text = stitle; r.font.name = FONT_MONO; r.font.size = Pt(9); r.font.bold = True; r.font.color.rgb = scolor
        p2 = stf.add_paragraph()
        r = p2.add_run(); r.text = sdesc; r.font.name = FONT_BODY; r.font.size = Pt(8.5); r.font.color.rgb = C_LIGHT

        # Connector indicator chevron between steps
        if idx < 3:
            arr_y = sy + step_h
            arr_box = s2.shapes.add_textbox(pipe_left + Inches(0.25), arr_y - Inches(0.06), Inches(0.5), Inches(0.2))
            atf = arr_y_box = arr_box.text_frame
            atf.margin_left = atf.margin_top = atf.margin_right = atf.margin_bottom = 0
            ap = atf.paragraphs[0]
            ar = ap.add_run(); ar.text = "▼"; ar.font.name = FONT_BODY; ar.font.size = Pt(7); ar.font.color.rgb = C_CYAN

    # Right: Pipeline Diagram / Data Architecture Placeholder
    create_placeholder(s2, Inches(7.05), Inches(3.05), Inches(5.48), Inches(3.88),
                       title="4-Step Pipeline & Architecture Diagram",
                       subtitle="Clean 4-step pipeline diagram:\nStep 1: Extraterrestrial No-Go & MAUT → Step 2: Anti-Cliché Earth Screening\n→ Step 3: Dimensionless Physics & Aitchison Simplex → Step 4: Decision Scorecards",
                       spec_hint="System Architecture Diagram & Parquet Data Flow",
                       aspect_ratio="4:3 / 16:9")

    print("Generating Slide 3: Live Mission Director & Engineering Cutoffs...")
    # ==========================================
    # SLIDE 3: Live Mission Director & Engineering Cutoffs
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    add_bg_and_header(s3, 3, 7, "Physical Constraints", "Live Mission Director & Engineering Cutoffs")

    col3_w = Inches(5.5)

    # Card 1: Tier 1 Hard Engineering Cutoffs
    c3_1 = create_card(s3, Inches(0.8), Inches(1.65), col3_w, Inches(2.45), border_color=C_ROSE)
    s3_ind1 = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.65), Inches(0.08), Inches(2.45))
    s3_ind1.fill.solid(); s3_ind1.fill.fore_color.rgb = C_ROSE; s3_ind1.line.fill.background()
    tf = c3_1.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "TIER 1 HARD CUTOFFS: ZERO FAILURE TOLERANCE\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_ROSE
    bullets_tier1 = [
        ("Slope Limit (μ_S ≤ 10.0°): ", "Strictly eliminates lander tip-over envelope at 5m baseline using LOLA & MOLA DTMs."),
        ("Rock Abundance (f_rock ≤ 5.0%): ", "Eliminates fatal boulder landing fields using LRO Diviner & Mars THEMIS thermal inertia."),
        ("Polar Illumination (≥ 80.0%) & Direct Earth LoS (≥ 50.0%): ", "Guarantees continuous solar array power and uninterrupted telecom line-of-sight without blackout traps.")
    ]
    for btitle, bbody in bullets_tier1:
        pb = tf.add_paragraph()
        r1 = pb.add_run(); r1.text = "• " + btitle; r1.font.name = FONT_BODY; r1.font.size = Pt(9); r1.font.bold = True; r1.font.color.rgb = C_WHITE
        r2 = pb.add_run(); r2.text = bbody; r2.font.name = FONT_BODY; r2.font.size = Pt(9); r2.font.color.rgb = C_LIGHT

    # Card 2: Site Optimization Highlights
    c3_2 = create_card(s3, Inches(0.8), Inches(4.25), col3_w, Inches(2.65), border_color=C_EMERALD)
    s3_ind2 = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(4.25), Inches(0.08), Inches(2.65))
    s3_ind2.fill.solid(); s3_ind2.fill.fore_color.rgb = C_EMERALD; s3_ind2.line.fill.background()
    tf = c3_2.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "OPTIMIZATION HIGHLIGHTS: MARS & MOON TARGETS\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_EMERALD
    bullets_opt = [
        ("Hellas Basin (-7,150 m Elevation): ", "Optimal candidate for heavy payload Entry, Descent & Landing (EDL). Maximized atmospheric column provides a +45% to +60% aerodynamic deceleration mass bonus."),
        ("Jezero Crater (Astrobiology): ", "Optimal candidate for delta clay & carbonate biosignature detection under strict COSPAR Category IVb/c Special Region planetary protection buffers."),
        ("Nobile South Plateau (Moon, +3,480 m): ", "Rank #1 Lunar Outpost: 94.9% peak solar illumination, 85.0% Direct-to-Earth LoS, and 1.90 km rover haul distance to cryogenic PSR water ice.")
    ]
    for btitle, bbody in bullets_opt:
        pb = tf.add_paragraph()
        r1 = pb.add_run(); r1.text = "• " + btitle; r1.font.name = FONT_BODY; r1.font.size = Pt(9); r1.font.bold = True; r1.font.color.rgb = C_WHITE
        r2 = pb.add_run(); r2.text = bbody; r2.font.name = FONT_BODY; r2.font.size = Pt(9); r2.font.color.rgb = C_LIGHT

    # Right Column: Screenshot Placeholder (3D Mission Director Globe & Sliders)
    create_placeholder(s3, Inches(6.55), Inches(1.65), Inches(5.98), Inches(5.25),
                       title="3D Globe & MCDA Sliders Interface",
                       subtitle="Screenshot of your 3D Mars/Moon globe showing\nEmerald (GO) vs. Red (NO-GO) H3 hexagons and the left MCDA sliders\n(demonstrating real-time interactive cutoff filtering)",
                       spec_hint="Live 3D App: famedied.github.io/mars-moon",
                       aspect_ratio="16:9 Widescreen")

    print("Generating Slide 4: Permanent Base Topology & Survival Engineering...")
    # ==========================================
    # SLIDE 4: Permanent Base Topology & Survival Engineering
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    add_bg_and_header(s4, 4, 7, "Base Triad Topology", "Permanent Base Topology & Survival Engineering")

    col4_w = Inches(5.5)

    # Card 1: 3-Hexagon Base Triad
    c4_1 = create_card(s4, Inches(0.8), Inches(1.65), col4_w, Inches(2.55), border_color=C_CYAN)
    s4_ind1 = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.65), Inches(0.08), Inches(2.55))
    s4_ind1.fill.solid(); s4_ind1.fill.fore_color.rgb = C_CYAN; s4_ind1.line.fill.background()
    tf = c4_1.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "3-HEXAGON BASE TRIAD (UBER H3 RESOLUTION 7)\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_CYAN
    triad_items = [
        ("H_pad (Lander Spaceport): ", "Separates landing pads by >1.5 km from living quarters, completely eliminating supersonic rocket plume ejecta scouring (Krueger & Cooper criteria)."),
        ("H_hab (Habitat & Operations): ", "Centered in topographically shielded depression with redundant pressurized ingress corridors."),
        ("H_isru (Cryo Volatiles & Fuel): ", "Optimized haul corridor keeping cryogenic water ice transport work at an ultra-low 0.17–0.26 kWh/ton (596.5 J/kg one-way haul).")
    ]
    for btitle, bbody in triad_items:
        pb = tf.add_paragraph()
        r1 = pb.add_run(); r1.text = "• " + btitle; r1.font.name = FONT_BODY; r1.font.size = Pt(9); r1.font.bold = True; r1.font.color.rgb = C_WHITE
        r2 = pb.add_run(); r2.text = bbody; r2.font.name = FONT_BODY; r2.font.size = Pt(9); r2.font.color.rgb = C_LIGHT

    # Card 2: Survival Physics & Extreme Power Architectures
    c4_2 = create_card(s4, Inches(0.8), Inches(4.35), col4_w, Inches(2.55), border_color=C_EMERALD)
    s4_ind2 = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(4.35), Inches(0.08), Inches(2.55))
    s4_ind2.fill.solid(); s4_ind2.fill.fore_color.rgb = C_EMERALD; s4_ind2.line.fill.background()
    tf = c4_2.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "SURVIVAL PHYSICS: RADIATION & POWER ARCHITECTURES\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_EMERALD
    survival_items = [
        ("Subsurface Lava Tubes (-90% Radiation): ", "Basalt roof overburden cuts ionizing GCR/SPE cosmic radiation by 90% (207.2 → 20.7 mSv/yr, 0.10x transmission factor)."),
        ("Regenerative Fuel Cells (RFC): ", "Saves 8.54 metric tons of dry payload mass over Li-ion batteries during the 102.5-hour lunar polar eclipse night."),
        ("Dual 10 kWe Kilopower Fission: ", "Delivers continuous base baseload, surviving extreme Mars global dust storms (optical depth τ = 3.0) where solar arrays black out.")
    ]
    for btitle, bbody in survival_items:
        pb = tf.add_paragraph()
        r1 = pb.add_run(); r1.text = "• " + btitle; r1.font.name = FONT_BODY; r1.font.size = Pt(9); r1.font.bold = True; r1.font.color.rgb = C_WHITE
        r2 = pb.add_run(); r2.text = bbody; r2.font.name = FONT_BODY; r2.font.size = Pt(9); r2.font.color.rgb = C_LIGHT

    # Right Column: Screenshot Placeholder (3-Hexagon Base Triad & Lava Tube Gauge)
    create_placeholder(s4, Inches(6.55), Inches(1.65), Inches(5.98), Inches(5.25),
                       title="3-Hexagon Base Triad & Radiation Gauge",
                       subtitle="Screenshot of your 3-Hexagon Base Triad (H_pad, H_hab, H_isru)\n+ Lava Tube Radiation Shield gauge dropping 90%\n(showing layout topology and radiation attenuation telemetry)",
                       spec_hint="Base Layout & Subsurface Attenuation Telemetry",
                       aspect_ratio="16:9 Widescreen")

    print("Generating Slide 5: The Split-Twin Discovery & Sample Verification...")
    # ==========================================
    # SLIDE 5: The "Split-Twin" Discovery & Sample Verification
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    add_bg_and_header(s5, 5, 7, "Split-Twin Analogs", "The \"Split-Twin\" Discovery & Sample Verification")

    col5_w = Inches(5.5)

    # Card 1: The Split-Twin Breakthrough
    c5_1 = create_card(s5, Inches(0.8), Inches(1.65), col5_w, Inches(2.55), border_color=C_CYAN)
    s5_ind1 = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.65), Inches(0.08), Inches(2.55))
    s5_ind1.fill.solid(); s5_ind1.fill.fore_color.rgb = C_CYAN; s5_ind1.line.fill.background()
    tf = c5_1.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "THE \"SPLIT-TWIN\" DISCOVERY: CLOSING PHYSICAL GAPS\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_CYAN
    split_items = [
        ("No Single Earth Site is Sufficient: ", "Earth cannot simultaneously match planetary geology, vacuum, and cryo-cold. Single-site tests leave fatal engineering blindspots."),
        ("Complementary Site Pairing: ", "Pairing two complementary Earth sites covers physical gaps no single site can match:"),
        ("  • Danakil + Samail Ophiolite: ", "77.5% combined envelope coverage (ultra-acidic brines + mantle serpentinization)."),
        ("  • Danakil + Svalbard Bockfjorden: ", "80.6% combined envelope coverage (cryogenic hydrothermal volcanism)."),
        ("Explicit Environmental Offloads: ", "Gravity crane offload (62.1% Mars / 83.5% Moon) + thermal vacuum cryo-chiller (35 K).")
    ]
    for btitle, bbody in split_items:
        pb = tf.add_paragraph()
        r1 = pb.add_run(); r1.text = btitle; r1.font.name = FONT_BODY; r1.font.size = Pt(8.5); r1.font.bold = True; r1.font.color.rgb = C_WHITE
        r2 = pb.add_run(); r2.text = bbody; r2.font.name = FONT_BODY; r2.font.size = Pt(8.5); r2.font.color.rgb = C_LIGHT

    # Card 2: Ground-Truth Sample Verification
    c5_2 = create_card(s5, Inches(0.8), Inches(4.35), col5_w, Inches(2.55), border_color=C_AMBER)
    s5_ind2 = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(4.35), Inches(0.08), Inches(2.55))
    s5_ind2.fill.solid(); s5_ind2.fill.fore_color.rgb = C_AMBER; s5_ind2.line.fill.background()
    tf = c5_2.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "GROUND-TRUTH VERIFICATION: AITCHISON COMPOSITIONAL SIMPLEX\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_AMBER
    sample_items = [
        ("Simplex Geometry (Zero Spurious Correlations): ", "Geochemical oxide percentages (SiO2, FeO, TiO2, Al2O3) evaluated via isometric log-ratio (ilr) transformations."),
        ("Apollo 14 Impact Breccia Benchmark: ", "Aitchison distance d_A = 0.593 against authentic Johnson Space Center (JSC) Lunar Sample Compendium."),
        ("Martian Shergottite NWA 2990 Benchmark: ", "Aitchison distance d_A = 0.542 confirming high-fidelity mineralogical alignment to pyroxene-olivine Martian meteorites.")
    ]
    for btitle, bbody in sample_items:
        pb = tf.add_paragraph()
        r1 = pb.add_run(); r1.text = "• " + btitle; r1.font.name = FONT_BODY; r1.font.size = Pt(9); r1.font.bold = True; r1.font.color.rgb = C_WHITE
        r2 = pb.add_run(); r2.text = bbody; r2.font.name = FONT_BODY; r2.font.size = Pt(9); r2.font.color.rgb = C_LIGHT

    # Right Column: Screenshot Placeholder (Radar Chart + Flight Arc)
    create_placeholder(s5, Inches(6.55), Inches(1.65), Inches(5.98), Inches(5.25),
                       title="4-Axis Radar Chart & Split-Twin Arc",
                       subtitle="Screenshot of your Overlapping 4-Axis Radar Chart\n(Geomorphology, Geochemistry, Thermophysics, Volatiles)\n+ the glowing Split-Twin flight arc connecting Earth analog twins",
                       spec_hint="Radar Telemetry & Earth Flight Arc Visual",
                       aspect_ratio="16:9 Widescreen")

    print("Generating Slide 6: Verification, Reproducibility & Open Science...")
    # ==========================================
    # SLIDE 6: Verification, Reproducibility & Open Science
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    add_bg_and_header(s6, 6, 7, "Verification & Open Science", "Verification, Reproducibility & Open Science")

    col6_w = Inches(5.5)

    # Card 1: 100% Deterministic Engine
    c6_1 = create_card(s6, Inches(0.8), Inches(1.65), col6_w, Inches(2.55), border_color=C_EMERALD)
    s6_ind1 = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.65), Inches(0.08), Inches(2.55))
    s6_ind1.fill.solid(); s6_ind1.fill.fore_color.rgb = C_EMERALD; s6_ind1.line.fill.background()
    tf = c6_1.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "100% DETERMINISTIC: ZERO LLM HALLUCINATIONS\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_EMERALD
    det_items = [
        ("Zero Black-Box Hallucinations: ", "Not an opaque generative model—every decision score is mathematically traceable to peer-reviewed NASA/ESA calibration data."),
        ("Analytic Taylor Error Propagation: ", "First-order Taylor expansion calculates measurement variance bounds (±1.96σ LCB), penalizing lower-resolution instruments."),
        ("1,000-Trial Monte Carlo Stability: ", "Synthetic noise perturbation tests across all 524 sites confirm >90% top-rank retention, proving exceptional algorithmic robustness.")
    ]
    for btitle, bbody in det_items:
        pb = tf.add_paragraph()
        r1 = pb.add_run(); r1.text = "• " + btitle; r1.font.name = FONT_BODY; r1.font.size = Pt(9); r1.font.bold = True; r1.font.color.rgb = C_WHITE
        r2 = pb.add_run(); r2.text = bbody; r2.font.name = FONT_BODY; r2.font.size = Pt(9); r2.font.color.rgb = C_LIGHT

    # Card 2: Open Source & Production Pipeline
    c6_2 = create_card(s6, Inches(0.8), Inches(4.35), col6_w, Inches(2.55), border_color=C_CYAN)
    s6_ind2 = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(4.35), Inches(0.08), Inches(2.55))
    s6_ind2.fill.solid(); s6_ind2.fill.fore_color.rgb = C_CYAN; s6_ind2.line.fill.background()
    tf = c6_2.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "OPEN SCIENCE & REPRODUCIBLE PIPELINE\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_CYAN
    open_items = [
        ("Automated Test Suite (pytest): ", "220 / 220 automated unit and property-based scientific tests passing in 6.22 seconds (100% pass rate)."),
        ("Permissive Open-Source Licensing: ", "Released under Apache License 2.0 (LICENSE) with machine-readable CITATION.cff for academic reproducibility."),
        ("Universal CLI Tooling: ", "Standalone executable CLI (`python cli.py match`) with formatted ANSI terminal scorecards and Snappy Parquet export.")
    ]
    for btitle, bbody in open_items:
        pb = tf.add_paragraph()
        r1 = pb.add_run(); r1.text = "• " + btitle; r1.font.name = FONT_BODY; r1.font.size = Pt(9); r1.font.bold = True; r1.font.color.rgb = C_WHITE
        r2 = pb.add_run(); r2.text = bbody; r2.font.name = FONT_BODY; r2.font.size = Pt(9); r2.font.color.rgb = C_LIGHT

    # Right Column: Terminal Verification Showcase Screenshot (Embedded if available)
    terminal_img_path = "atlas_x_verification_showcase.png"
    if os.path.exists(terminal_img_path):
        # Embed the generated high-resolution terminal showcase screenshot
        img_box = s6.shapes.add_picture(terminal_img_path, Inches(6.55), Inches(1.65), Inches(5.98), Inches(5.25))
        # Thin hairline border accent
        border_rect = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.55), Inches(1.65), Inches(5.98), Inches(5.25))
        border_rect.fill.background()
        border_rect.line.color.rgb = C_BORDER_BRIGHT
        border_rect.line.width = Pt(1.5)
    else:
        create_placeholder(s6, Inches(6.55), Inches(1.65), Inches(5.98), Inches(5.25),
                           title="pytest Terminal & CLI Match Scorecard",
                           subtitle="Screenshot of your pytest terminal (220 passed in 6.22s)\n+ the formatted cli.py match output scorecard table\n(proving 100% automated test coverage and execution speed)",
                           spec_hint="Terminal Execution: 220 passed in 6.22s",
                           aspect_ratio="16:9 Terminal View")

    print("Generating Slide 7: Try ATLAS-X Live (Live Access & Deployment)...")
    # ==========================================
    # SLIDE 7: Try ATLAS-X Live (Live Access & Deployment)
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    add_bg_and_header(s7, 7, 7, "Live Access & Deployment", "Try ATLAS-X Live — Explore 524 Sites & Split-Twins")

    col7_w = Inches(5.5)

    # Card 1: Direct Access Links
    c7_1 = create_card(s7, Inches(0.8), Inches(1.65), col7_w, Inches(2.55), border_color=C_CYAN, fill_color=C_CARD_ALT)
    s7_ind1 = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.65), Inches(0.08), Inches(2.55))
    s7_ind1.fill.solid(); s7_ind1.fill.fore_color.rgb = C_CYAN; s7_ind1.line.fill.background()
    tf = c7_1.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "DIRECT ACCESS & VERIFICATION LINKS (ONLINE 24/7/365)\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_CYAN

    p1 = tf.add_paragraph()
    r = p1.add_run(); r.text = "🌐 LIVE 3D MISSION CONTROL APP:\n"; r.font.name = FONT_MONO; r.font.size = Pt(9); r.font.bold = True; r.font.color.rgb = C_WHITE
    r_u1 = p1.add_run(); r_u1.text = "https://famedied.github.io/mars-moon/\n"; r_u1.font.name = FONT_MONO; r_u1.font.size = Pt(9.5); r_u1.font.bold = True; r_u1.font.color.rgb = C_CYAN
    r_u1.hyperlink.address = "https://famedied.github.io/mars-moon/"
    r_desc1 = p1.add_run(); r_desc1.text = "• Interactive 3D WebGL globes for Earth, Moon & Mars with H3 hex overlays\n"; r_desc1.font.name = FONT_BODY; r_desc1.font.size = Pt(8.5); r_desc1.font.color.rgb = C_LIGHT

    p2 = tf.add_paragraph()
    r = p2.add_run(); r.text = "🐙 OPEN-SOURCE REPOSITORY & CLI:\n"; r.font.name = FONT_MONO; r.font.size = Pt(8.5); r.font.bold = True; r.font.color.rgb = C_WHITE
    r_u2 = p2.add_run(); r_u2.text = "https://github.com/FameDied/mars-moon\n"; r_u2.font.name = FONT_MONO; r_u2.font.size = Pt(9); r_u2.font.bold = True; r_u2.font.color.rgb = C_EMERALD
    r_u2.hyperlink.address = "https://github.com/FameDied/mars-moon"
    r_desc2 = p2.add_run(); r_desc2.text = "• Complete database, 220 automated unit tests, and CLI decision tool\n"; r_desc2.font.name = FONT_BODY; r_desc2.font.size = Pt(8); r_desc2.font.color.rgb = C_LIGHT

    p3 = tf.add_paragraph()
    r = p3.add_run(); r.text = "📄 ARCHITECTURE & RESEARCH PAPER (PDF):\n"; r.font.name = FONT_MONO; r.font.size = Pt(8.5); r.font.bold = True; r.font.color.rgb = C_WHITE
    r_u3 = p3.add_run(); r_u3.text = "https://famedied.github.io/mars-moon/atlas-x-architecture.pdf\n"; r_u3.font.name = FONT_MONO; r_u3.font.size = Pt(9); r_u3.font.bold = True; r_u3.font.color.rgb = C_AMBER
    r_u3.hyperlink.address = "https://famedied.github.io/mars-moon/atlas-x-architecture.pdf"
    r_desc3 = p3.add_run(); r_desc3.text = "• Full paper, mathematical proofs, and verification audits"; r_desc3.font.name = FONT_BODY; r_desc3.font.size = Pt(8); r_desc3.font.color.rgb = C_LIGHT

    # Card 2: Summary of Architectural Pillars
    c7_2 = create_card(s7, Inches(0.8), Inches(4.35), col7_w, Inches(2.55), border_color=C_EMERALD)
    s7_ind2 = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(4.35), Inches(0.08), Inches(2.55))
    s7_ind2.fill.solid(); s7_ind2.fill.fore_color.rgb = C_EMERALD; s7_ind2.line.fill.background()
    tf = c7_2.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.15); tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "CORE ARCHITECTURAL PILLARS & VERIFIED CAPABILITIES\n"; r.font.name = FONT_MONO; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = C_EMERALD
    criteria = [
        ("Harmonized Data Architecture: ", "Harmonized 37 NASA/USGS/ESA datasets into unified Uber H3 schema; zero data silos."),
        ("Physics-First Fidelity: ", "Eliminated fake matches through authentic physical delta-vectors (gravity crane, cryo chamber, radiation)."),
        ("Operational Feasibility: ", "Pioneered the 3-Hexagon Base Triad (>1.5 km plume buffer) and Complementary Split-Twin pairing."),
        ("Rigorous Verification: ", "220 / 220 passing tests, Taylor variance propagation, and sub-millisecond local SQLite/Parquet.")
    ]
    for btitle, bbody in criteria:
        pb = tf.add_paragraph()
        r1 = pb.add_run(); r1.text = "• " + btitle; r1.font.name = FONT_BODY; r1.font.size = Pt(8.5); r1.font.bold = True; r1.font.color.rgb = C_WHITE
        r2 = pb.add_run(); r2.text = bbody; r2.font.name = FONT_BODY; r2.font.size = Pt(8.5); r2.font.color.rgb = C_LIGHT

    # Right Column: Split Screenshot Placeholders (Live Web App + GitHub Repo)
    right_x = Inches(6.55)
    right_w = Inches(5.98)
    split_h = Inches(2.55)

    # Top Half: Live Web App View
    create_placeholder(s7, right_x, Inches(1.65), right_w, split_h,
                       title="Live 3D Mission Control Application View",
                       subtitle="Screenshot of live web application interface\n(famedied.github.io/mars-moon)",
                       spec_hint="Live 3D App Interface",
                       aspect_ratio="16:9 Split View",
                       is_split=True)

    # Bottom Half: GitHub Repo View
    create_placeholder(s7, right_x, Inches(4.35), right_w, split_h,
                       title="GitHub Repository & CLI Match View",
                       subtitle="Screenshot of GitHub repo (FameDied/mars-moon)\nor terminal running python cli.py match",
                       spec_hint="Open Source Repository & Verification",
                       aspect_ratio="16:9 Split View",
                       is_split=True)

    prs.save(output_path)
    print(f"✅ Generated high-fidelity presentation: {output_path}")

if __name__ == "__main__":
    build_atlas_x_presentation()
