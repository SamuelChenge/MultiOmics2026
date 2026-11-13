# Builds a conference presentation from group_project/slide_figures/.
#
#   python3 group_project/build_conference_pptx.py
#
# Output: group_project/study-b-conference-slides.pptx (16:9)
#
# Everything is a NATIVE PowerPoint object — real text boxes, real tables,
# real pictures — so every slide can be edited in PowerPoint / Google Slides.
# The design system is at the top: change a colour here and the whole
# deck restyles when you rerun the script.

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# --------------------------------------------------------------------------
# Design system: colours, fonts, geometry
# --------------------------------------------------------------------------
FIGDIR = Path(__file__).parent / "slide_figures"
OUT = Path(__file__).parent / "study-b-conference-slides.pptx"

NAVY = RGBColor(0x1F, 0x2A, 0x44)   # headings, title-slide background
INK = RGBColor(0x37, 0x41, 0x51)    # body text
MUTE = RGBColor(0x6B, 0x72, 0x80)   # captions, footers
LINE = RGBColor(0xD5, 0xDB, 0xE5)   # hairlines, table borders
PAPER = RGBColor(0xF5, 0xF7, 0xFA)  # light card fill

TEAL = RGBColor(0x0E, 0x7C, 0x7B)   # Q1 — microbiome composition
CORAL = RGBColor(0xE4, 0x57, 0x2E)  # Q2 — ring vs systemic genes
PURPLE = RGBColor(0x6D, 0x28, 0xD9)  # Q3 — community vs method
GOLD = RGBColor(0xB4, 0x59, 0x00)   # setup / caveats

FONT = "Calibri"
TITLE_FONT = "Calibri"

SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.55)


def tint(c, f=0.88):
    """A lighter version of colour c: f = how much white to mix in
    (0 = the colour itself, 1 = white)."""
    return RGBColor(int(c[0] * (1 - f) + 255 * f),
                    int(c[1] * (1 - f) + 255 * f),
                    int(c[2] * (1 - f) + 255 * f))


prs = Presentation()
prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H
BLANK = prs.slide_layouts[6]  # empty layout; we place everything ourselves


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def new_slide(accent):
    s = prs.slides.add_slide(BLANK)
    # Bottom accent bar: the question colour carried through the deck.
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, SLIDE_H - Inches(0.12),
                             SLIDE_W, Inches(0.12))
    style_shape(bar, accent)
    bar.height = Inches(0.12)
    return s


def style_shape(shape, fill, line=None):
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(0.75)
    shape.shadow.inherit = False
    return shape


def box(slide, x, y, w, h):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    return tf


def set_runs(p, text, size, color, bold=False, font=FONT):
    """Add runs to paragraph p, honouring **bold** markers in text.
    A literal \n becomes a real PowerPoint line break (<a:br/>)."""
    for i, chunk in enumerate(text.split("**")):
        if not chunk:
            continue
        for k, part in enumerate(chunk.split("\n")):
            if k:  # real line break between parts
                p._p.append(p._p.makeelement(qn("a:br"), {}))
            if not part:
                continue
            r = p.add_run()
            r.text = part
            f = r.font
            f.name = font
            f.size = Pt(size)
            f.color.rgb = color
            f.bold = bold or (i % 2 == 1)  # text inside **...** becomes bold


def kicker_title(slide, kicker, title, accent, title_size=30):
    # kicker: small all-caps label above the title
    tf = box(slide, MARGIN, Inches(0.30), SLIDE_W - 2 * MARGIN, Inches(0.34))
    p = tf.paragraphs[0]
    set_runs(p, kicker, 12.5, accent, bold=True)
    # thin rule under the kicker
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MARGIN, Inches(0.66),
                                  Inches(0.55), Pt(2.6))
    style_shape(rule, accent)
    # title
    tf = box(slide, MARGIN, Inches(0.78), SLIDE_W - 2 * MARGIN, Inches(0.80))
    p = tf.paragraphs[0]
    set_runs(p, title, title_size, NAVY, bold=True, font=TITLE_FONT)
    p.line_spacing = 1.0
    return slide


def bullets(slide, x, y, w, h, items, size=15, color=INK, space=7):
    """items: list of strings; '**' marks bold; strings starting with '~'
    are sub-bullets."""
    tf = box(slide, x, y, w, h)
    first = True
    for item in items:
        level = 1
        text = item
        if item.startswith("~"):
            level, text = 2, item[1:]
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(space)
        if level == 1:
            set_runs(p, "▪ " + text, size, color)
            p.space_after = Pt(space)
            p.line_spacing = 1.05
        else:
            p.level = 1
            set_runs(p, "– " + text, size - 1.5, MUTE)
            p.line_spacing = 1.05
    return tf


def stat_card(slide, x, y, w, h, big, label, color, big_size=26):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    style_shape(card, tint(color, 0.88), line=color)
    card.adjustments[0] = 0.14
    tf = card.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.14)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    set_runs(p, big, big_size, color, bold=True)
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(2)
    p2.line_spacing = 0.95
    set_runs(p2, label, 10.5, NAVY)
    return card


def picture(slide, name, x, y, w=None, h=None):
    """Insert a figure scaled to fit inside the box; returns the shape."""
    path = FIGDIR / name
    kw = {}
    if w is not None:
        kw["width"] = w
    if h is not None:
        kw["height"] = h
    pic = slide.shapes.add_picture(str(path), x, y, **kw)
    return pic


def caption(slide, text, x, y, w, size=10.5):
    tf = box(slide, x, y, w, Inches(0.30))
    p = tf.paragraphs[0]
    set_runs(p, text, size, MUTE)
    p.alignment = PP_ALIGN.CENTER
    return tf


def table(slide, x, y, w, headers, rows, col_w, accent, size=13,
          header_size=12.5):
    n_r, n_c = len(rows) + 1, len(headers)
    shp = slide.shapes.add_table(n_r, n_c, x, y, w,
                                 Inches(0.36) * n_r)
    tbl = shp.table
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = cw
    # header row
    for j, htxt in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = accent
        tf = cell.text_frame
        tf.margin_left = tf.margin_right = Inches(0.08)
        p = tf.paragraphs[0]
        set_runs(p, htxt, header_size, RGBColor(0xFF, 0xFF, 0xFF), bold=True)
    # body rows
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = (
                RGBColor(0xFF, 0xFF, 0xFF) if i % 2 else PAPER)
            tf = cell.text_frame
            tf.margin_left = tf.margin_right = Inches(0.08)
            p = tf.paragraphs[0]
            set_runs(p, str(val), size, INK, bold=(j == 0 and False))
    return tbl


def footer(slide, n, accent, text="Study B · Group B1–B5 · Data Science for Biology"):
    tf = box(slide, MARGIN, SLIDE_H - Inches(0.42), Inches(8), Inches(0.30))
    set_runs(tf.paragraphs[0], text, 10, MUTE)
    tf = box(slide, SLIDE_W - Inches(1.4), SLIDE_H - Inches(0.42),
             Inches(0.85), Inches(0.30))
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    set_runs(p, str(n), 10, accent, bold=True)


# ==========================================================================
# Slide 1 — Title
# ==========================================================================
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
style_shape(bg, NAVY)
# decorative accent blocks, top-right
for i, c in enumerate([TEAL, CORAL, PURPLE]):
    chip = s.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                              SLIDE_W - Inches(3.3) + i * Inches(1.1),
                              0, Inches(1.1), Inches(0.28))
    style_shape(chip, c)

tf = box(s, Inches(0.9), Inches(1.75), Inches(11.5), Inches(0.4))
set_runs(tf.paragraphs[0], "STUDY B · CONFERENCE PRESENTATION", 14,
         RGBColor(0x9F, 0xC5, 0xB8), bold=True)

tf = box(s, Inches(0.9), Inches(2.2), Inches(11.8), Inches(1.9))
p = tf.paragraphs[0]
set_runs(p, "Do hormonal contraceptives differ\nin their effect?", 44,
         RGBColor(0xFF, 0xFF, 0xFF), bold=True, font=TITLE_FONT)
p.line_spacing = 1.05

tf = box(s, Inches(0.9), Inches(4.1), Inches(11.5), Inches(0.8))
set_runs(tf.paragraphs[0],
         "Three methods, **93 people**, microbiome and host genes",
         20, RGBColor(0xC9, 0xD4, 0xE3))

tf = box(s, Inches(0.9), Inches(4.9), Inches(11.5), Inches(0.4))
set_runs(tf.paragraphs[0], "Group B1–B5  ·  Data Science for Biology workshop",
         14, RGBColor(0x8B, 0x99, 0xB0))

# three question chips across the bottom
chips = [
    (TEAL, "Q1", "Do the methods differ in\ncommunity composition?"),
    (CORAL, "Q2", "Does the ring differ from the\nsystemic methods in genes?"),
    (PURPLE, "Q3", "Does community type explain\nthe genes better than method?"),
]
for i, (c, tag, txt) in enumerate(chips):
    x = Inches(0.9) + i * Inches(4.0)
    card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(5.6),
                              Inches(3.75), Inches(1.25))
    style_shape(card, RGBColor(0x2A, 0x38, 0x58), line=c)
    card.adjustments[0] = 0.12
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.18)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    set_runs(p, f"{tag}  ", 15, c, bold=True)
    set_runs(p, txt.replace("\n", " "), 13, RGBColor(0xE8, 0xED, 0xF5))
    p.line_spacing = 1.0

# ==========================================================================
# Slide 2 — The three questions (roadmap)
# ==========================================================================
s = new_slide(NAVY)
kicker_title(s, "THE WEEK IN ONE SLIDE", "One dataset, three questions", NAVY)

cards = [
    (TEAL, "Q1 — Community composition",
     ["Do pill, injectable and ring carve the vaginal microbiome into three?",
      "**Species table:** 220 × 93",
      "**Test:** PERMANOVA on CLR + Euclidean distances"]),
    (CORAL, "Q2 — Ring vs systemic genes",
     ["The ring acts locally, the others systemically — do host genes differ?",
      "**Gene table:** 14,226 × 93",
      "**Test:** PERMANOVA + DESeq2 on raw counts"]),
    (PURPLE, "Q3 — Community vs method",
     ["Group by microbiome type, not method — which explains genes better?",
      "**Community:** Lactobacillus ≥ 50 % of species reads",
      "**Rule:** defined on species, tested on genes"]),
]
for i, (c, head, items) in enumerate(cards):
    x = MARGIN + i * Inches(4.15)
    card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.95),
                              Inches(3.9), Inches(3.6))
    style_shape(card, RGBColor(0xFF, 0xFF, 0xFF), line=c)
    card.adjustments[0] = 0.06
    card.shadow.inherit = False
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    set_runs(p, head, 16, c, bold=True)
    p.space_after = Pt(8)
    for it in items:
        p = tf.add_paragraph()
        p.space_after = Pt(6)
        set_runs(p, it, 12.5, INK)
        p.line_spacing = 1.05

tf = box(s, MARGIN, Inches(5.85), SLIDE_W - 2 * MARGIN, Inches(0.6))
p = tf.paragraphs[0]
set_runs(p, "Full workings: ", 13, MUTE)
set_runs(p, "**01-qc.html** (QC), **02** + **03** (Question 2), "
            "**05** (Question 1), **06** (Question 3) — every headline number "
            "in this deck can be traced to one of them.", 13, MUTE)
footer(s, 2, NAVY)

# ==========================================================================
# Slide 3 — Who, what, how many
# ==========================================================================
s = new_slide(GOLD)
kicker_title(s, "SETUP", "Who, what, how many", GOLD)

bullets(s, MARGIN, Inches(1.85), Inches(6.6), Inches(4.6), [
    "**93 participants**, one vaginal swab each, **one visit** — no time course",
    "Each person used one of three hormonal contraceptives **they chose "
    "themselves** — this is not a randomised trial",
    "Two sequencing tables for the same 93 samples, features in rows:",
    "~**species** — 220 species × 93 samples",
    "~**host genes** — 14,226 genes × 93 samples",
    "Plus **15 cytokines** measured in the same samples",
], size=16)

stat_card(s, Inches(7.6), Inches(1.95), Inches(2.3), Inches(1.15),
          "28", "pill", TEAL)
stat_card(s, Inches(10.0), Inches(1.95), Inches(2.3), Inches(1.15),
          "39", "injectable", CORAL)
stat_card(s, Inches(7.6), Inches(3.25), Inches(2.3), Inches(1.15),
          "26", "vaginal ring", PURPLE)
stat_card(s, Inches(10.0), Inches(3.25), Inches(2.3), Inches(1.15),
          "48 / 45", "lactobacillus / anaerobe\ncommunity type", NAVY, 22)

tf = box(s, Inches(7.6), Inches(4.7), Inches(4.9), Inches(1.3))
p = tf.paragraphs[0]
set_runs(p, "The question: do the methods differ in their effect? "
            "We answer it three ways — microbiome, genes, and community "
            "type vs method.", 13, MUTE)
p.line_spacing = 1.1
footer(s, 3, GOLD)

# ==========================================================================
# Slide 4 — Not a randomised trial (confounder)
# ==========================================================================
s = new_slide(GOLD)
kicker_title(s, "SETUP · CAVEATS FIRST", "No randomisation — people chose their method",
             GOLD, title_size=28)

pic = picture(s, "confounder_ph_by_arm.png", MARGIN, Inches(2.15),
              w=Inches(7.6))
caption(s, "Vaginal pH by method — the one baseline imbalance\n"
           "(Kruskal–Wallis p = 0.02)", MARGIN, pic.top + pic.height + Emu(40000),
        Inches(7.6))

bullets(s, Inches(8.55), Inches(2.0), Inches(4.25), Inches(4.8), [
    "Any arm difference could be the method **or something that tracks the "
    "choice**",
    "Checked every baseline variable:",
    "~Bacterial vaginosis — no (Fisher p = 0.63)",
    "~Nugent score — no (p = 0.65)",
    "~Sequencing batch — every arm in both batches",
    "**Vaginal pH — yes, p = 0.02:** median 4.55 in pill vs 5.0 in ring and "
    "injectable",
    "pH may be a **confounder** or **on the causal path** — we show the "
    "unadjusted answer and say where pH changes it",
], size=13.5)
footer(s, 4, GOLD)

# ==========================================================================
# Slide 5 — Power: who is compared with whom
# ==========================================================================
s = new_slide(GOLD)
kicker_title(s, "SETUP · POWER", "Who is compared with whom", GOLD)

table(s, MARGIN, Inches(1.95), Inches(7.9),
      ["Comparison", "n", "Note"],
      [
          ["All three arms", "93", "28 pill / 39 injectable / 26 ring"],
          ["ring vs pooled systemic", "26 vs 67", "pooled control is **58 % injectable**"],
          ["ring vs pill", "26 vs 28", "most even ring comparison"],
          ["ring vs injectable", "26 vs 39", "most powerful ring comparison"],
          ["pill vs injectable", "28 vs 39", "the pooling check"],
          ["community type", "93", "48 lactobacillus / 45 anaerobe"],
      ],
      [Inches(2.9), Inches(1.5), Inches(3.5)], GOLD, size=13)

bullets(s, Inches(8.75), Inches(2.0), Inches(4.0), Inches(4.6), [
    "The ring arm is the smallest — **ring comparisons have the least power**",
    "A bigger arm finds more \u201csignificant\u201d genes for the same true "
    "effect",
    "With 26–39 per group, only **large gene-expression differences** reach "
    "FDR < 0.05",
    "Small shifts land in the \u201csuggestive\u201d pile — remember this "
    "when reading Q2",
], size=14)
footer(s, 5, GOLD)

# ==========================================================================
# Slide 6 — QC: the two checks that mattered
# ==========================================================================
s = new_slide(GOLD)
kicker_title(s, "SETUP · QUALITY CONTROL", "QC — the two things that mattered",
             GOLD, title_size=28)

pic1 = picture(s, "qc_library_sizes.png", MARGIN, Inches(1.9), w=Inches(5.95))
caption(s, "Reads per sample, species vs RNA-seq — nine low-depth\n"
           "microbiome samples flagged, none dropped",
        MARGIN, pic1.top + pic1.height + Emu(40000), Inches(5.95))
pic2 = picture(s, "qc_hbb_blood_signal.png", Inches(6.8), Inches(1.9),
               w=Inches(5.95))
caption(s, "Blood (HBB/HBA) reads per sample — B093 carries about\n"
           "one third blood reads; the 92 %-survival check covers it",
        Inches(6.8), pic2.top + pic2.height + Emu(40000), Inches(5.95))

tf = box(s, MARGIN, Inches(6.35), SLIDE_W - 2 * MARGIN, Inches(0.5))
p = tf.paragraphs[0]
set_runs(p, "Neither check changed the plan: ", 13.5, INK)
set_runs(p, "**nine low-depth samples kept** (visible, not influential) and "
            "**B093 not dropped** — instead every hit list is retested "
            "without it.", 13.5, INK)
footer(s, 6, GOLD)

# ==========================================================================
# Slide 7 — QC: batch and feature prevalence
# ==========================================================================
s = new_slide(GOLD)
kicker_title(s, "SETUP · QUALITY CONTROL", "QC — batch and feature prevalence",
             GOLD, title_size=28)

pic1 = picture(s, "qc_batch_library_size.png", MARGIN, Inches(1.9),
               w=Inches(5.95))
caption(s, "Gene library size by sequencing batch and arm —\n"
           "no batch-depth problem",
        MARGIN, pic1.top + pic1.height + Emu(40000), Inches(5.95))
pic2 = picture(s, "qc_feature_prevalence.png", Inches(6.8), Inches(1.9),
               w=Inches(5.95))
caption(s, "Genes are dense, species are sparse — different filtering\n"
           "rules for the two tables",
        Inches(6.8), pic2.top + pic2.height + Emu(40000), Inches(5.95))

tf = box(s, MARGIN, Inches(6.35), SLIDE_W - 2 * MARGIN, Inches(0.5))
p = tf.paragraphs[0]
set_runs(p, "Consequence: ", 13.5, INK)
set_runs(p, "**raw counts into DESeq2** (never CPM, never logged), genes "
            "filtered at \u2265 10 reads in \u2265 10 samples, species "
            "ordination on the unfiltered table.", 13.5, INK)
footer(s, 7, GOLD)

# ==========================================================================
# Slide 8 — Q1 headline result
# ==========================================================================
s = new_slide(TEAL)
kicker_title(s, "QUESTION 1 · COMMUNITY COMPOSITION",
             "The three methods do not carve the microbiome into three",
             TEAL, title_size=28)

pic = picture(s, "q1_species_pcoa_by_arm.png", MARGIN, Inches(1.95),
              w=Inches(7.6))
caption(s, "Species PCoA (CLR + Euclidean), coloured by method — the arms "
           "overlap heavily", MARGIN, pic.top + pic.height + Emu(40000),
        Inches(7.6))

stat_card(s, Inches(8.55), Inches(2.0), Inches(4.2), Inches(1.05),
          "2.8 % · p = 0.172", "PERMANOVA, all three arms (n = 93),\n"
          "adjusted for batch, 9,999 permutations", TEAL, 22)
bullets(s, Inches(8.55), Inches(3.3), Inches(4.25), Inches(3.3), [
    "**No clear three-way difference** — not significant",
    "**No pairwise comparison survives adjustment** either (ring vs pill, "
    "ring vs injectable, pill vs injectable)",
    "No individual species stands out: DESeq2 hit counts at chance level in "
    "every comparison",
    "What **does** structure this map: community type (axis 1 holds 36 %) — "
    "that is Q3",
], size=13.5)
footer(s, 8, TEAL)

# ==========================================================================
# Slide 9 — Q1 robustness
# ==========================================================================
s = new_slide(TEAL)
kicker_title(s, "QUESTION 1 · ROBUSTNESS",
             "The community split is real; the method split is not",
             TEAL, title_size=28)

pic = picture(s, "qc_species_ordination_three_ways.png", MARGIN,
              Inches(1.9), w=Inches(9.4))
caption(s, "Species ordination under three distances (Bray–Curtis, Jaccard, "
           "CLR + Euclidean) with scree plots — same conclusion each time",
        MARGIN, pic.top + pic.height + Emu(50000), Inches(9.4))

bullets(s, Inches(10.3), Inches(2.0), Inches(2.5), Inches(4.6), [
    "Same answer under **all three distances**",
    "The **community-type** separation appears every time",
    "The **method** separation never does",
], size=13.5)
footer(s, 9, TEAL)

# ==========================================================================
# Slide 10 — Q2 map
# ==========================================================================
s = new_slide(CORAL)
kicker_title(s, "QUESTION 2 · RING vs SYSTEMIC GENES",
             "The gene maps overlap; the formal tests sit on the 0.05 line",
             CORAL, title_size=28)

pic = picture(s, "q2_gene_pcoa_by_arm.png", MARGIN, Inches(1.95),
              w=Inches(7.6))
caption(s, "Gene PCoA (CLR + Euclidean), coloured by method — heavy overlap",
        MARGIN, pic.top + pic.height + Emu(40000), Inches(7.6))

stat_card(s, Inches(8.55), Inches(2.0), Inches(4.2), Inches(1.05),
          "1.7 % · p = 0.041", "ring vs pooled systemic (n = 26 vs 67),\n"
          "borderline — reruns gave 0.03–0.055", CORAL, 22)
bullets(s, Inches(8.55), Inches(3.3), Inches(4.25), Inches(3.3), [
    "Three-arm test (adjusted for batch): **2.7 %, p = 0.101** — not "
    "significant",
    "**Spread check (betadisper):** one arm is not simply more scattered, "
    "which would fake a difference",
    "**Verdict:** suggestive at best — call it a lead, not a finding",
], size=13.5)
footer(s, 10, CORAL)

# ==========================================================================
# Slide 11 — Q2 volcano
# ==========================================================================
s = new_slide(CORAL)
kicker_title(s, "QUESTION 2 · RING vs SYSTEMIC GENES",
             "DESeq2: 165 genes at FDR < 0.05 — mostly small shifts",
             CORAL, title_size=28)

pic = picture(s, "q2_volcano_ring_vs_systemic.png", MARGIN, Inches(1.95),
              w=Inches(7.6))
caption(s, "Ring vs pooled systemic. Red: FDR < 0.05; labels: the ten "
           "smallest FDR values", MARGIN, pic.top + pic.height + Emu(40000),
        Inches(7.6))

stat_card(s, Inches(8.55), Inches(2.0), Inches(4.2), Inches(1.05),
          "165 / 14,226", "genes at FDR < 0.05 (88 up in the ring),\n"
          "n = 26 vs 67", CORAL, 22)
bullets(s, Inches(8.55), Inches(3.3), Inches(4.25), Inches(3.3), [
    "Dropping the blood-contaminated sample **B093 leaves 152 of 165 hits "
    "standing (92 %)** — the list does not hinge on one sample",
    "Caveat: raw-p hit lists are about **twice what chance gives**, and top "
    "hits are keratins and mucus genes — may partly be **cell mix**, not the "
    "ring",
    "If real, the effect is **modest** — no dramatic reprogramming of "
    "vaginal tissue",
], size=13.5)
footer(s, 11, CORAL)

# ==========================================================================
# Slide 12 — Is pooling fair?
# ==========================================================================
s = new_slide(CORAL)
kicker_title(s, "QUESTION 2 · A CHECK ON THE DESIGN",
             "Is pooling pill + injectable into \u201csystemic\u201d fair?",
             CORAL, title_size=28)

table(s, MARGIN, Inches(2.0), Inches(7.7),
      ["Evidence (pill vs injectable)", "Result"],
      [
          ["DESeq2 genes at FDR < 0.05", "**11** (chance would give ~5–7)"],
          ["Raw p < 0.05", "**738** vs ~711 expected by chance"],
          ["PERMANOVA (genes)", "**1.4 %, p = 0.54**"],
          ["Ring LFC vs pill vs injectable (all genes)",
           "**r = 0.71** — same direction"],
      ],
      [Inches(4.7), Inches(3.0)], CORAL, size=13)

bullets(s, Inches(8.6), Inches(1.95), Inches(4.15), Inches(4.6), [
    "**Why it is fair:** the two systemic arms are near-indistinguishable "
    "in the genes, and the ring's log2 fold changes point the same way "
    "against both (r = 0.71)",
    "**Caveat 1:** the pooled control is 58 % injectable, so \u201csystemic\u201d "
    "leans that way",
    "**Caveat 2:** adjusting for the pH imbalance changes the ring-vs-pill "
    "list from 97 to 191 genes — the pooled contrast is not the only "
    "defensible reading",
    "Alternative not chosen: keep the three arms separate (document 03 "
    "does exactly that as a check)",
], size=13)
footer(s, 12, CORAL)

# ==========================================================================
# Slide 13 — Q3 head-to-head
# ==========================================================================
s = new_slide(PURPLE)
kicker_title(s, "QUESTION 3 · COMMUNITY vs METHOD",
             "Group by community type, then test the genes", PURPLE)

pic = picture(s, "q3_gene_pcoa_by_community.png", MARGIN, Inches(1.95),
              w=Inches(7.6))
caption(s, "Same gene PCoA as Q2, coloured by community type — the split is "
           "clearer", MARGIN, pic.top + pic.height + Emu(40000), Inches(7.6))

table(s, Inches(8.55), Inches(2.05), Inches(4.2),
      ["Grouping", "share %", "p", "genes at\nFDR<0.05"],
      [
          ["community type\n(48 vs 45)", "1.4 %", "0.117", "**312**"],
          ["ring vs systemic\n(26 vs 67)", "1.6 %", "0.053", "**165**"],
      ],
      [Inches(1.5), Inches(0.7), Inches(0.8), Inches(1.2)], PURPLE, size=12)

bullets(s, Inches(8.55), Inches(3.95), Inches(4.25), Inches(2.7), [
    "**Tie on the map, community ahead gene by gene:** "
    "312 vs 165 genes at FDR < 0.05",
    "Groupings are **independent** — community is balanced across arms "
    "(\u03c7\u00b2 p = 0.50); gene lists barely overlap (27 shared)",
    "**pH tracks community type far more strongly than method** (p \u2248 "
    "1e-07 vs 0.02) — one more reason to adjust",
    "**Upshot: adjust for community type** before reading method effects",
], size=12.5)
footer(s, 13, PURPLE)

# ==========================================================================
# Slide 14 — Three answers in three lines
# ==========================================================================
s = new_slide(NAVY)
kicker_title(s, "WRAPPING UP", "The three answers in three lines", NAVY)

rows = [
    (TEAL, "Q1 — Community composition",
     "**The methods do not differ detectably** — PERMANOVA 2.8 %, p = 0.172 "
     "(n = 93). The strong structure is community type, not method."),
    (CORAL, "Q2 — Ring vs systemic genes",
     "**Small and suggestive** — 1.7 % of variation (p = 0.041) and 165 genes "
     "at FDR < 0.05, with cell-mix and pH caveats. Pooling pill + injectable "
     "is supported (11 hits, p = 0.54, r = 0.71)."),
    (PURPLE, "Q3 — Community type vs method",
     "**About a tie on the map (1.4 % vs 1.6 %), community ahead gene by gene "
     "(312 vs 165).** The groupings are independent — report both, and adjust "
     "for community when reading method effects."),
]
y = Inches(1.95)
for c, head, txt in rows:
    card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, MARGIN, y,
                              SLIDE_W - 2 * MARGIN, Inches(1.35))
    style_shape(card, tint(c, 0.93), line=c)
    card.adjustments[0] = 0.10
    tf = card.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.25)
    tf.margin_right = Inches(0.25)
    p = tf.paragraphs[0]
    set_runs(p, head, 15, c, bold=True)
    p.space_after = Pt(3)
    p2 = tf.add_paragraph()
    set_runs(p2, txt, 13, INK)
    p2.line_spacing = 1.05
    y += Inches(1.55)

tf = box(s, MARGIN, y + Emu(60000), SLIDE_W - 2 * MARGIN, Inches(0.7))
p = tf.paragraphs[0]
set_runs(p, "Standing caveat for all three: ", 13.5, GOLD, bold=True)
set_runs(p, "people chose their method, the arms differ in vaginal pH, and "
            "the ring arm is the smallest (n = 26) — treat every p-value here "
            "as a lead, not a verdict.", 13.5, GOLD)
footer(s, 14, NAVY)

# ==========================================================================
# Slide 15 — Choices made
# ==========================================================================
s = new_slide(NAVY)
kicker_title(s, "WRAPPING UP", "Choices made (and the alternatives we did not choose)",
             NAVY, title_size=28)

bullets(s, MARGIN, Inches(1.95), Inches(6.1), Inches(4.7), [
    "**Community type from the species table, tested on the gene table** "
    "(Lactobacillus \u2265 50 % of species reads) — a stricter 60 % cutoff "
    "is the alternative",
    "**Species ordination on the unfiltered table**, CLR + Euclidean with "
    "half-min replacement — filtering rare species first is the alternative",
    "**Genes \u2265 10 reads in \u2265 10 samples** — a stricter filter "
    "loses power, a laxer one wastes tests",
    "**Raw counts into DESeq2** (it normalises itself) — CPM or logged "
    "values would be wrong",
], size=13.5)

bullets(s, Inches(6.95), Inches(1.95), Inches(5.85), Inches(4.7), [
    "**Both PERMANOVA groupings reported** (three-arm and pooled) — showing "
    "only the pooled one would overstate the evidence, as it sits on the "
    "p = 0.05 line",
    "**9,999 permutations, by = \"margin\"** for every PERMANOVA — the "
    "sequential test is the (overstated) alternative",
    "**Main results unadjusted for pH** (it may be on the causal path); "
    "where pH matters we say so — full adjustment is the alternative",
    "**Quoted sensitivity numbers** from the review document rather than "
    "recomputing every fit on a slide",
], size=13.5)
footer(s, 15, NAVY)

# ==========================================================================
# Slide 16 — Closing / where the numbers live
# ==========================================================================
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
style_shape(bg, NAVY)
for i, c in enumerate([TEAL, CORAL, PURPLE]):
    chip = s.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                              SLIDE_W - Inches(3.3) + i * Inches(1.1),
                              SLIDE_H - Inches(0.28), Inches(1.1),
                              Inches(0.28))
    style_shape(chip, c)

tf = box(s, Inches(0.9), Inches(2.0), Inches(11), Inches(1.2))
p = tf.paragraphs[0]
set_runs(p, "Three questions, three answers,\nno verdicts — just leads.", 34,
         RGBColor(0xFF, 0xFF, 0xFF), bold=True, font=TITLE_FONT)
p.line_spacing = 1.1

tf = box(s, Inches(0.9), Inches(4.35), Inches(11.5), Inches(2.2))
p = tf.paragraphs[0]
set_runs(p, "Where every number lives:", 14, RGBColor(0x9F, 0xC5, 0xB8),
         bold=True)
p.space_after = Pt(8)
for line in [
    "**01-qc.html** — quality control  ·  **02-ring-vs-systemic.html** and "
    "**03-three-arms-review.html** — Question 2",
    "**05-q1-three-arms-composition.html** — Question 1  ·  "
    "**06-q3-community-vs-method.html** — Question 3",
    "**make_slide_figures.R** regenerates every figure in this deck from "
    "the data — the deck is fully reproducible",
]:
    p = tf.add_paragraph()
    p.space_after = Pt(6)
    set_runs(p, line, 13.5, RGBColor(0xC9, 0xD4, 0xE3))
    p.line_spacing = 1.1

tf = box(s, Inches(0.9), Inches(6.6), Inches(11), Inches(0.5))
set_runs(tf.paragraphs[0], "Thank you — questions?   ·   Group B1–B5", 15,
         RGBColor(0x8B, 0x99, 0xB0), bold=True)

# --------------------------------------------------------------------------
prs.core_properties.title = "Study B — Do hormonal contraceptives differ in their effect?"
prs.core_properties.author = "Group B1–B5"
prs.save(OUT)
print(f"wrote {OUT} with {len(prs.slides._sldIdLst)} slides")
