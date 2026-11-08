"""
lessonkit.py  -  Lesson Pack Design System v1.0
Reusable tokens, styles and components for AI-generated language-lesson PDFs.

Colour = function (never decoration):
  BLUE   -> reading / explanations / calm focus
  YELLOW -> vocabulary, idioms, false cognates
  GREEN  -> patterns, formulas, pronunciation guides
  RED    -> exceptions, common errors, alerts (use sparingly)
Neutral ink/paper carry structure (fronts, teacher notes, tables).
"""
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, Flowable, PageBreak,
                                KeepTogether, NextPageTemplate)
from reportlab.pdfgen import canvas as rl_canvas

# ------------------------------------------------------------------ fonts
import os, urllib.request

FONT_DIRS = [os.environ.get("LESSONKIT_FONTS", ""), "/content/fonts",
             "/content/drive/MyDrive/AI_English_Teacher_Agent/System/fonts", "/usr/share/fonts"]
FONT_URLS = {
    "Carlito-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/carlito/Carlito-Regular.ttf",
    "Carlito-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/carlito/Carlito-Bold.ttf",
    "Carlito-Italic.ttf": "https://github.com/google/fonts/raw/main/ofl/carlito/Carlito-Italic.ttf",
    "Carlito-BoldItalic.ttf": "https://github.com/google/fonts/raw/main/ofl/carlito/Carlito-BoldItalic.ttf",
    "Poppins-Medium.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Medium.ttf",
    "Poppins-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "Poppins-MediumItalic.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-MediumItalic.ttf",
    "Poppins-BoldItalic.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-BoldItalic.ttf",
    "DejaVuSans.ttf": "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf",
    "DejaVuSans-Bold.ttf": "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf",
}

def ensure_fonts(dest="/content/fonts"):
    """Download the fonts that are not found anywhere (Colab). Safe to call repeatedly."""
    os.makedirs(dest, exist_ok=True)
    for name, url in FONT_URLS.items():
        if _find(name) is None:
            try: urllib.request.urlretrieve(url, os.path.join(dest, name))
            except Exception as e: print(f"  aviso: nao foi possivel baixar {name}: {e}")

def _find(fname):
    for root in FONT_DIRS:
        if root and os.path.isdir(root):
            for dp, _, fs in os.walk(root):
                if fname in fs: return os.path.join(dp, fname)
    return None

def register_fonts():
    # alias -> candidate files in order of preference (falls back to DejaVu if a family is missing)
    spec = {
        "Body":    ["Carlito-Regular.ttf", "DejaVuSans.ttf"],
        "Body-B":  ["Carlito-Bold.ttf", "DejaVuSans-Bold.ttf"],
        "Body-I":  ["Carlito-Italic.ttf", "DejaVuSans-Oblique.ttf", "DejaVuSans.ttf"],
        "Body-BI": ["Carlito-BoldItalic.ttf", "DejaVuSans-BoldOblique.ttf", "DejaVuSans-Bold.ttf"],
        "Head":    ["Poppins-Medium.ttf", "DejaVuSans.ttf"],
        "Head-B":  ["Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"],
        "Head-I":  ["Poppins-MediumItalic.ttf", "DejaVuSans-Oblique.ttf", "DejaVuSans.ttf"],
        "Head-BI": ["Poppins-BoldItalic.ttf", "DejaVuSans-BoldOblique.ttf", "DejaVuSans-Bold.ttf"],
        "Sym":     ["DejaVuSans.ttf"], "Sym-B": ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"],
    }
    for alias, cands in spec.items():
        path = next((p for p in (_find(c) for c in cands) if p), None)
        if path is None:
            raise FileNotFoundError(f"Fonte nao encontrada para {alias}: {cands}. Rode ensure_fonts() primeiro.")
        pdfmetrics.registerFont(TTFont(alias, path))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-B", italic="Body-I", boldItalic="Body-BI")
    pdfmetrics.registerFontFamily("Head", normal="Head", bold="Head-B", italic="Head-I", boldItalic="Head-BI")
    pdfmetrics.registerFontFamily("Sym", normal="Sym", bold="Sym-B", italic="Sym", boldItalic="Sym-B")

if any(_find(n) is None for n in FONT_URLS):   # e.g. fresh Colab runtime
    ensure_fonts()
register_fonts()

# ------------------------------------------------------------------ tokens
PALETTE = {
    "ink": "#1E2A38", "muted": "#5B6776", "line": "#D9DEE5", "paper": "#F3F5F8", "white": "#FFFFFF",
    "blue":   dict(main="#2B6CB0", dark="#1E4E8C", tint="#E8F1FB", soft="#CBE0F7"),
    "yellow": dict(main="#F2B600", dark="#6B4E00", tint="#FFF6D6", soft="#FFE89A"),
    "green":  dict(main="#2F9E6B", dark="#1B6446", tint="#E4F5EC", soft="#BFE8D2"),
    "red":    dict(main="#D64545", dark="#9B2525", tint="#FDEAEA", soft="#F8C9C9"),
}
ROLE_LABEL = {"blue": "Read", "yellow": "Vocabulary", "green": "Pattern", "red": "Watch out"}
SPACE = dict(xs=4, sm=8, md=12, lg=16, xl=24, xxl=32)           # 4-pt scale
PAGE_W, PAGE_H = A4
MX, MTOP, MBOT = 18 * mm, 24 * mm, 20 * mm
CW = PAGE_W - 2 * MX                                              # content width
COVER_H = 140

def C(h): return colors.HexColor(h)
INK, MUTED, LINE, PAPER = C(PALETTE["ink"]), C(PALETTE["muted"]), C(PALETTE["line"]), C(PALETTE["paper"])

def tokens_json(path):
    with open(path, "w") as f:
        json.dump(dict(palette=PALETTE, space=SPACE, role_labels=ROLE_LABEL,
                       page=dict(size="A4", margin_x_mm=18, margin_top_mm=24, margin_bottom_mm=20)), f, indent=2)

# ------------------------------------------------------------------ styles
def _ps(name, **kw):
    base = dict(fontName="Body", fontSize=11, leading=16, textColor=INK)
    base.update(kw); return ParagraphStyle(name, **base)

ST = {
    "h1":      _ps("h1", fontName="Head-B", fontSize=24, leading=30),
    "h2":      _ps("h2", fontName="Head-B", fontSize=17, leading=22),
    "h3":      _ps("h3", fontName="Head-B", fontSize=11, leading=15),
    "label":   _ps("label", fontName="Head", fontSize=7.5, leading=10, textColor=MUTED, charSpace=0.8),
    "body":    _ps("body"),
    "text":    _ps("text", fontSize=12, leading=18.5),               # student reading text
    "small":   _ps("small", fontSize=10, leading=14),
    "cap":     _ps("cap", fontSize=9, leading=12, textColor=MUTED),
    "teacher": _ps("teacher", fontSize=10, leading=14.5, textColor=C("#3B4756")),
    "cell":    _ps("cell", fontSize=10.5, leading=14),
    "cellb":   _ps("cellb", fontName="Body-B", fontSize=10.5, leading=14),
    "th":      _ps("th", fontName="Head", fontSize=7.5, leading=10, textColor=colors.white, charSpace=0.7),
    "instr":   _ps("instr", fontName="Body-B", fontSize=11.5, leading=16),
    "center":  _ps("center", alignment=TA_CENTER),
}
def P(t, s="body", **kw):
    st = ST[s] if not kw else ParagraphStyle("x", parent=ST[s], **kw)
    return Paragraph(t, st)

# ------------------------------------------------------------------ inline markup
def hl(text, kind):
    """Inline highlighter: kind = vocab | verb | subj | err  (semantic colours)."""
    k = {"vocab": "yellow", "verb": "green", "subj": "blue", "err": "red"}[kind]
    p = PALETTE[k]
    return f'<font backColor="{p["soft"]}" color="{p["dark"]}">{text}</font>'
def ok(t):  return f'<font name="Sym" color="{PALETTE["green"]["main"]}">\u2713</font> {t}'
def bad(t): return f'<font name="Sym" color="{PALETTE["red"]["main"]}">\u2717</font> {t}'
def muted(t): return f'<font color="{PALETTE["muted"]}">{t}</font>'

# ------------------------------------------------------------------ flowables
class ModeMarker(Flowable):
    """Zero-height flowable: tags the page as student / teacher / system (shown in running header)."""
    PAGE_MODE = {}
    def __init__(self, mode): super().__init__(); self.mode = mode; self.width = 0; self.height = 0
    def wrap(self, aw, ah): return (0, 0)
    def draw(self): ModeMarker.PAGE_MODE[self.canv.getPageNumber()] = self.mode

class NumBadge(Flowable):
    def __init__(self, num, size=46):
        super().__init__(); self.num, self.size = num, size; self.width = self.height = size
    def draw(self):
        c, s = self.canv, self.size
        c.setFillColor(INK); c.roundRect(0, 0, s, s, 6, stroke=0, fill=1)
        c.setFillColor(colors.white); c.setFont("Head-B", 21); c.drawCentredString(s / 2, s / 2 - 4, self.num)
        seg = (s - 16) / 4
        for i, k in enumerate(["blue", "yellow", "green", "red"]):          # brand motif
            c.setFillColor(C(PALETTE[k]["main"])); c.rect(8 + i * seg, 7, seg, 3, stroke=0, fill=1)

class Timeline(Flowable):
    """Proportional lesson timeline. segments = [(label, minutes, dark: bool)]"""
    def __init__(self, segs, width=CW, height=44):
        super().__init__(); self.segs, self.width, self.height = segs, width, height
    def draw(self):
        c = self.canv; total = sum(m for _, m, _ in self.segs); gap = 2; x = 0
        usable = self.width - gap * (len(self.segs) - 1)
        for label, m, dark in self.segs:
            w = usable * m / total
            c.setFillColor(INK if dark else C("#CBD2DB")); c.roundRect(x, 14, w, 28, 4, stroke=0, fill=1)
            c.setFillColor(colors.white if dark else INK)
            c.setFont("Head-B", 8); c.drawCentredString(x + w / 2, 31, f"{m}'")
            c.setFont("Head", 6.2); c.drawCentredString(x + w / 2, 21, label)
            x += w + gap
        c.setFillColor(MUTED); c.setFont("Head", 7); c.drawString(0, 2, "0 min"); c.drawRightString(self.width, 2, f"{total} min")

class FamilyTree(Flowable):
    """Blank 3-generation family tree to be completed by students."""
    def __init__(self, width=CW, height=170):
        super().__init__(); self.width, self.height = width, height
    def _box(self, x, y, w, h, label, strong=False):
        c = self.canv
        c.setStrokeColor(INK if strong else C("#9AA5B1")); c.setLineWidth(1.6 if strong else 0.8)
        c.setFillColor(C(PALETTE["blue"]["tint"]) if strong else colors.white)
        c.roundRect(x, y, w, h, 5, stroke=1, fill=1)
        c.setFillColor(MUTED); c.setFont("Head", 6.5); c.drawCentredString(x + w / 2, y + 4.5, label.upper())
    def draw(self):
        c, W, H = self.canv, self.width, self.height
        bw, bh = 94, 34
        y1, y2, y3 = H - bh, H / 2 - bh / 2, 0
        cA, cB = W * 0.25, W * 0.75
        c.setStrokeColor(C("#9AA5B1")); c.setLineWidth(0.8)
        for cx in (cA, cB):                                            # grandparent couples
            xs = [cx - bw - 6, cx + 6]
            c.line(xs[0] + bw, y1 + bh / 2, xs[1], y1 + bh / 2)
            c.line(cx, y1 + bh / 2, cx, y2 + bh)
            self._box(xs[0], y1, bw, bh, "grandmother"); self._box(xs[1], y1, bw, bh, "grandfather")
        self._box(cA - bw / 2, y2, bw, bh, "mother"); self._box(cB - bw / 2, y2, bw, bh, "father")
        c.setStrokeColor(C("#9AA5B1")); c.line(cA + bw / 2, y2 + bh / 2, cB - bw / 2, y2 + bh / 2)
        mid, bus, off = W / 2, y3 + bh + 14, bw + 30
        c.line(mid, y2 + bh / 2, mid, bus); c.line(mid - off, bus, mid + off, bus)
        for dx, lab, strong in [(-off, "sister / brother", False), (0, "my partner", True), (off, "sister / brother", False)]:
            c.setStrokeColor(C("#9AA5B1")); c.setLineWidth(0.8); c.line(mid + dx, bus, mid + dx, y3 + bh)
            self._box(mid + dx - bw / 2, y3, bw, bh, lab, strong)

class WriteLines(Flowable):
    def __init__(self, n=3, width=CW, gap=24):
        super().__init__(); self.n, self.width, self.gap = n, width, gap; self.height = n * gap
    def draw(self):
        self.canv.setStrokeColor(C("#B8C1CC")); self.canv.setLineWidth(0.6)
        for i in range(self.n):
            y = self.height - (i + 1) * self.gap + 6; self.canv.line(0, y, self.width, y)

# ------------------------------------------------------------------ components
FORCE_SPLIT = False   # set to True by the renderer's retry when a block is taller than a page
def spacer(k="md"): return Spacer(1, SPACE[k])

def callout(kind, body, label=None, width=CW, bg=None, height=None, split=False):
    """Semantic callout card. kind: blue|yellow|green|red. body: str or list of flowables."""
    p = PALETTE[kind]
    lab = label or ROLE_LABEL[kind]
    chip = Paragraph(f'<font name="Sym" color="{p["main"]}">\u25A0</font>&nbsp; {lab.upper()}',
                     ParagraphStyle("chip", fontName="Head-B", fontSize=7.5, leading=10, textColor=C(p["dark"]), charSpace=0.8))
    inner = [chip, Spacer(1, 5)] + ([Paragraph(body, ST["body"])] if isinstance(body, str) else list(body))
    t = Table([[inner]], colWidths=[width], rowHeights=[height] if height else None, splitInRow=1 if (split or FORCE_SPLIT) else 0)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C(bg or p["tint"])), ("LINEBEFORE", (0, 0), (0, -1), 4, C(p["main"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 12), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t

def teacher_rail(text_pt, width=CW, label="Professor"):
    t = Table([[P(label.upper(), "label"), P(text_pt, "teacher")]], colWidths=[84, width - 84])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PAPER), ("LEFTPADDING", (0, 0), (-1, -1), 12),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 9),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 10), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LINEBEFORE", (0, 0), (0, -1), 1.2, C("#9AA5B1"))]))
    return t

def front_header(num, tag, title, subtitle):
    right = [P(f"FRONT {num} \u00B7 {tag}".upper(), "label"), Spacer(1, 2), P(title, "h2"), P(subtitle, "body", textColor=MUTED, fontSize=10.5, leading=14)]
    t = Table([[NumBadge(num), right]], colWidths=[60, CW - 60])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0)]))
    return t

def section_title(text, sub=None):
    out = [P(text.upper(), "label", textColor=INK, fontName="Head-B", fontSize=8.5)]
    if sub: out.append(P(sub, "cap"))
    return out

def checklist(items, width=CW):
    if not items: return Spacer(1, 1)
    rows = [[P('<font name="Sym">\u25A1</font>', "body", fontSize=13, textColor=INK), P(t, "body")] for t in items]
    t = Table(rows, colWidths=[24, width - 24])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    return t

def meta_strip(items, width=CW):
    cells = [[[P(k.upper(), "label"), Spacer(1, 2), P(v, "cellb")] for k, v in items]]
    n = len(items); t = Table(cells, colWidths=[width / n] * n)
    st = [("LINEABOVE", (0, 0), (-1, 0), 1.5, INK), ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
          ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 9), ("LEFTPADDING", (0, 0), (-1, -1), 0),
          ("VALIGN", (0, 0), (-1, -1), "TOP")]
    for i in range(1, n): st.append(("LINEBEFORE", (i, 0), (i, 0), 0.5, LINE)); st.append(("LEFTPADDING", (i, 0), (i, 0), 12))
    t.setStyle(TableStyle(st)); return t

def data_table(header, rows, widths, zebra=False, head_bg=None, valign="TOP", pad=7):
    data = [[P(h.upper(), "th") for h in header]] + [[c if not isinstance(c, str) else P(c, "cell") for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), head_bg or INK), ("VALIGN", (0, 0), (-1, -1), valign),
          ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
          ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
          ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE)]
    t.setStyle(TableStyle(st)); return t

def two_col(left, right, gap=14, widths=None):
    w = widths or [(CW - gap) / 2, (CW - gap) / 2]
    t = Table([[left, "", right]], colWidths=[w[0], gap, w[1]])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return t

def color_key(width=CW):
    cells = []
    for k, txt in [("blue", "Read &amp; understand"), ("yellow", "Remember"), ("green", "Notice the pattern"), ("red", "Watch out!")]:
        p = PALETTE[k]
        cells.append(Paragraph(f'<font name="Sym" color="{p["main"]}" size="11">\u25A0</font>&nbsp; <font name="Head-B" size="7.5" color="{p["dark"]}">{ROLE_LABEL[k].upper()}</font><br/>'
                               f'<font size="9.5" color="{PALETTE["muted"]}">{txt}</font>', ParagraphStyle("k", fontName="Body", fontSize=9.5, leading=13)))
    t = Table([cells], colWidths=[width / 4] * 4)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), C("#FAFBFC")), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 12)]))
    return t

# ------------------------------------------------------------------ document
class _Canvas(rl_canvas.Canvas):
    """Two-pass canvas: running header + footer with 'n / N'."""
    meta = dict(running_left="", running_right="", footer="")
    def __init__(self, *a, **k): super().__init__(*a, **k); self._saved = []
    def showPage(self): self._saved.append(dict(self.__dict__)); self._startPage()
    def save(self):
        n = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st); self._decorate(n); super().showPage()
        super().save()
    def _decorate(self, total):
        pg = self._pageNumber; m = self.meta
        if pg > 1:
            self.setFont("Head", 7); self.setFillColor(MUTED)
            self.drawString(MX, PAGE_H - 13 * mm, m["running_left"].upper())
            mode = ModeMarker.PAGE_MODE.get(pg)
            if mode:
                label = {"student": "STUDENT PAGE", "teacher": "TEACHER PAGE", "system": "DESIGN SYSTEM"}[mode]
                w = self.stringWidth(label, "Head-B", 6.8) + 14
                x = PAGE_W - MX - w
                if mode == "teacher": self.setFillColor(C("#CBD2DB")); self.roundRect(x, PAGE_H - 14.2 * mm, w, 13, 6.5, stroke=0, fill=1)
                else: self.setStrokeColor(INK); self.setLineWidth(0.8); self.roundRect(x, PAGE_H - 14.2 * mm, w, 13, 6.5, stroke=1, fill=0)
                self.setFillColor(INK); self.setFont("Head-B", 6.8); self.drawCentredString(x + w / 2, PAGE_H - 12.1 * mm, label)
            self.setStrokeColor(LINE); self.setLineWidth(0.5); self.line(MX, PAGE_H - 16.5 * mm, PAGE_W - MX, PAGE_H - 16.5 * mm)
        # footer
        y = 11 * mm
        for i, k in enumerate(["blue", "yellow", "green", "red"]):
            self.setFillColor(C(PALETTE[k]["main"])); self.rect(MX + i * 7, y - 1, 5, 5, stroke=0, fill=1)
        self.setFillColor(MUTED); self.setFont("Head", 7); self.drawString(MX + 34, y, m["footer"].upper())
        self.drawRightString(PAGE_W - MX, y, f"{pg} / {total}")

def build_pdf(path, story, cover, running_left, footer, title="Lesson Pack", author="Lesson Pack"):
    """cover = dict(kicker, title, subtitle, chips=[...])"""
    _Canvas.meta = dict(running_left=running_left, running_right="", footer=footer)
    def draw_cover(c, doc):
        c.saveState()
        c.setFillColor(INK); c.rect(0, PAGE_H - COVER_H, PAGE_W, COVER_H, stroke=0, fill=1)
        seg = PAGE_W / 4
        for i, k in enumerate(["blue", "yellow", "green", "red"]):
            c.setFillColor(C(PALETTE[k]["main"])); c.rect(i * seg, PAGE_H - COVER_H, seg, 6, stroke=0, fill=1)
        c.setFillColor(C("#9FB3C8")); c.setFont("Head", 8); c.drawString(MX, PAGE_H - 42, cover["kicker"].upper())
        fs = 30
        while fs > 17 and c.stringWidth(cover["title"], "Head-B", fs) > CW: fs -= 1
        c.setFillColor(colors.white); c.setFont("Head-B", fs); c.drawString(MX, PAGE_H - 78, cover["title"])
        c.setFillColor(C("#D5DEE8")); c.setFont("Body", 14.5); c.drawString(MX, PAGE_H - 100, cover["subtitle"])
        x = MX
        for chip in cover["chips"]:
            w = c.stringWidth(chip, "Head", 7.5) + 18
            c.setStrokeColor(C("#6F8399")); c.setLineWidth(0.8); c.roundRect(x, PAGE_H - 128, w, 17, 8.5, stroke=1, fill=0)
            c.setFillColor(colors.white); c.setFont("Head", 7.5); c.drawString(x + 9, PAGE_H - 122.5, chip); x += w + 8
        c.restoreState()
    doc = BaseDocTemplate(path, pagesize=A4, leftMargin=MX, rightMargin=MX, topMargin=MTOP, bottomMargin=MBOT,
                          title=title, author=author)
    f1 = Frame(MX, MBOT, CW, PAGE_H - COVER_H - 18 - MBOT, id="f1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    f2 = Frame(MX, MBOT, CW, PAGE_H - MTOP - MBOT, id="f2", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="first", frames=[f1], onPage=draw_cover, autoNextPageTemplate="rest"),
                          PageTemplate(id="rest", frames=[f2])])
    doc.build(story, canvasmaker=_Canvas)


def equal_heights(builders, widths):
    """builders: callables f(height|None) -> Table. Returns tables with the same (max) natural height."""
    H = max(b(None).wrap(w, 10000)[1] for b, w in zip(builders, widths))
    return [b(H) for b in builders]
