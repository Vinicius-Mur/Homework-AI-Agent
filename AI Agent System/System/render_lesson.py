"""
render_lesson.py - renders the JSON produced under lesson_schema.LessonSchema with the Lesson Pack design system.
Public API:  build_advanced_pdf(json_data: dict, output_path: str) -> str
"""
import re
from xml.sax.saxutils import escape
import lessonkit as _lk
from lessonkit import *          # tokens, styles, components, build_pdf, ensure_fonts
from reportlab.platypus.doctemplate import LayoutError

KIND = {"vocab": "vocab", "verb": "verb", "exception": "err", "err": "err"}
STAGES = [("Lead-in", 3, False), ("01 Input", 10, True), ("02 Shadow", 8, True),
          ("03 Task cycle", 22, True), ("04 Reconfig.", 10, True), ("Check", 7, False)]


# ------------------------------------------------------------------ text helpers
def esc(t): return escape(str(t if t is not None else ""))

def mark_highlights(text, highlights):
    """Escapes the text and wraps each highlight (longest first, no overlaps) in the semantic colours."""
    s, spans = esc(text), []
    for h in sorted(highlights or [], key=lambda h: -len(str(h.get("text", "")))):
        t = esc(h.get("text", "")).strip()
        if not t: continue
        for m in re.finditer(re.escape(t), s):
            a, b = m.span()
            if not any(a < y and x < b for x, y, _ in spans):
                spans.append((a, b, KIND.get(h.get("kind", "vocab"), "vocab")))
    out, pos = [], 0
    for a, b, k in sorted(spans):
        out += [s[pos:a], hl(s[a:b], k)]; pos = b
    out.append(s[pos:])
    return "".join(out).replace("\n", "<br/>")

def stress_markup(line, words):
    s = esc(line)
    for w in sorted(words or [], key=len, reverse=True):
        w = esc(w).strip()
        if w:
            s = re.sub(rf"(?<![\w>])({re.escape(w)})(?![\w<])",
                       rf'<font name="Body-B" color="{PALETTE["green"]["dark"]}">\1</font>', s, count=1, flags=re.I)
    return s

def card(label, body, width=CW, height=None):
    inner = [P(esc(label).upper(), "label", textColor=INK, fontName="Head-B"), Spacer(1, 4)] + ([P(body)] if isinstance(body, str) else list(body))
    t = Table([[inner]], colWidths=[width], rowHeights=[height] if height else None, splitInRow=1 if _lk.FORCE_SPLIT else 0)
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, C("#9AA5B1")), ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
    return t

def small_label(text): return P(esc(text).upper(), "label", textColor=INK, fontName="Head-B", fontSize=8.5)
def sub_caption(text): return P(esc(text), "cap")
def has(x): return bool(x) and (not isinstance(x, str) or x.strip() != "")


# ------------------------------------------------------------------ pages
def page_overview(d, S):
    S += [ModeMarker("teacher"),
          meta_strip([("Level", d.get("cefr_level", "")), ("Time", "60 minutes"), ("Language focus", esc(d.get("focus_summary", ""))), ("Format", "TBLT \u00B7 4 fronts")]),
          spacer("md"), small_label("Learning objectives"), spacer("xs"),
          P(f"<b>Main aim.</b> {esc(d.get('main_aim', ''))}"), spacer("sm"),
          checklist([esc(o) for o in d.get("objectives", [])]), spacer("md"),
          small_label("Lesson flow"), spacer("sm"), Timeline(STAGES), spacer("sm")]
    rows = [("3", "Lead-in", "Whole class", "Activate the topic and the key words.", "\u2014"),
            ("10", "Comprehensible Input", "Individual \u2192 pairs", "Read and listen. Gist first, then true / false.", "01"),
            ("8", "Shadowing", "Whole class \u2192 pairs", "Listen, mark stress, echo, shadow the model dialogue.", "02"),
            ("22", "Task cycle (TBLT)", "Pairs \u2192 groups", "Pre-task \u2192 task \u2192 planning \u2192 report \u2192 language focus.", "03"),
            ("10", "Reconfiguration", "Individual \u2192 pairs", "Rebuild sentences from meaning blocks; transform sentences.", "04"),
            ("7", "Check & close", "Individual", "Exit ticket + can-do self-assessment.", "\u2713")]
    S += [data_table(["Min", "Stage", "Interaction", "What happens", "Front"],
                     [[P(r[0], "cellb"), P(f"<b>{r[1]}</b>", "cell"), P(r[2], "small", textColor=MUTED), P(r[3], "cell"), P(r[4], "cellb", alignment=TA_CENTER)] for r in rows],
                     [34, 106, 82, CW - 34 - 106 - 82 - 52, 52], pad=4), spacer("md"), color_key()]

def page_input(d, S):
    S += [PageBreak(), ModeMarker("student"),
          front_header("01", "Comprehensible Input", "Read and listen", "A short, understandable text (i+1) that carries the target language."), spacer("md"),
          teacher_rail(esc(d.get("teacher_lead_in", ""))), spacer("md")]
    text = mark_highlights(d.get("comprehensible_input_text", ""), d.get("highlights", []))
    wb = [P(f"<b>{esc(i.get('word'))}</b><br/><font size='9.5' color='#5B6776'>{esc(i.get('meaning'))}</font>", "cell") for i in d.get("word_bank", [])]
    wb_flow = []
    for w in wb: wb_flow += [w, Spacer(1, 10)]
    LW = 308; RW = CW - LW - 14
    left = lambda h, w=LW: callout("blue", [P(text, "text", fontSize=11.5, leading=17.5)], label="Read", width=w, height=h, split=True)
    right = lambda h, w=RW: callout("yellow", wb_flow, label="Word bank", width=w, height=h)
    if left(None).wrap(LW, 10000)[1] > 520:                       # very long text: stack instead of side by side
        S += [callout("blue", [P(text, "text", fontSize=11.5, leading=17.5)], label="Read", split=True), spacer("sm"), callout("yellow", wb_flow, label="Word bank")]
    else:
        l, r = equal_heights([left, right], [LW, RW]); S.append(two_col(l, r, gap=14, widths=[LW, RW]))
    S += [spacer("xs"), P(f"Highlights: {hl('yellow','vocab')} new words \u00B7 {hl('green','verb')} target verb forms \u00B7 {hl('red','err')} irregular", "cap"), spacer("md")]
    HW = (CW - 14) / 2
    def gist(h):
        body = []
        for i, q in enumerate(d.get("gist_questions", []), 1):
            opts = " &nbsp;&nbsp; ".join(f"{'abc'[j]}) {esc(o)}" for j, o in enumerate(q.get("options", [])[:3]))
            body += [P(f"{i}. {esc(q.get('question'))}", "cellb"), P(opts, "cell"), Spacer(1, 6)]
        return card("A \u00B7 Gist \u2014 circle", body, width=HW, height=h)
    def tf(h):
        body = []
        for i, t in enumerate(d.get("true_false", []), 1): body += [P(f"{i}. {esc(t.get('statement'))} &nbsp;<b>___</b>", "cell"), Spacer(1, 3)]
        return card("B \u00B7 Detail \u2014 true (T) or false (F)?", body, width=HW, height=h)
    g, t = equal_heights([gist, tf], [HW, HW]); S.append(two_col(g, t, gap=14))

def page_shadowing(d, S):
    S += [PageBreak(), ModeMarker("student"),
          front_header("02", "Shadowing", "Listen, then speak with the model", "Imitate rhythm, stress and intonation. This dialogue also models the task."), spacer("md"),
          teacher_rail(esc(d.get("teacher_shadowing_note", ""))), spacer("md")]
    steps = [("1", "Listen", "no reading"), ("2", "Mark", "stress words"), ("3", "Echo", "line by line"), ("4", "Shadow", "speak together")]
    cells = []
    for n, a, b in steps:
        cells += [Paragraph(f'<font name="Head-B" size="13" color="#FFFFFF">{n}</font>', ParagraphStyle("n", alignment=TA_CENTER, leading=16)),
                  P(f"<b>{a}</b><br/><font size='9' color='#5B6776'>{b}</font>", "cell", leading=12.5)]
    lad = Table([cells], colWidths=[26, CW / 4 - 26] * 4)
    sty = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("LEFTPADDING", (0, 0), (-1, -1), 4),
           ("BOX", (0, 0), (-1, -1), 0.5, LINE), ("BACKGROUND", (0, 0), (-1, -1), C("#FAFBFC"))]
    for i in range(4):
        sty += [("BACKGROUND", (2 * i, 0), (2 * i, 0), INK), ("LEFTPADDING", (2 * i, 0), (2 * i, 0), 0), ("RIGHTPADDING", (2 * i, 0), (2 * i, 0), 0), ("LEFTPADDING", (2 * i + 1, 0), (2 * i + 1, 0), 9)]
    lad.setStyle(TableStyle(sty)); S += [lad, spacer("md")]

    lines = d.get("shadowing_dialogue", [])
    if lines:
        first = lines[0].get("speaker", "")
        rows, dsty = [], [("BACKGROUND", (1, 0), (1, -1), C(PALETTE["green"]["tint"])), ("LINEBEFORE", (1, 0), (1, -1), 4, C(PALETTE["green"]["main"])),
                          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                          ("LEFTPADDING", (1, 0), (1, -1), 14), ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 0)]
        for i, ln in enumerate(lines):
            arrow = "\u2197" if str(ln.get("intonation", "")).lower().startswith("r") else "\u2198"
            rows.append([Paragraph(f'<font name="Head-B" size="7" color="#FFFFFF">{esc(ln.get("speaker", "")).upper()[:8]}</font>', ParagraphStyle("sp", alignment=TA_CENTER, leading=10)),
                         P(f'{stress_markup(ln.get("line", ""), ln.get("stress_words", []))} <font name="Sym" size="10">{arrow}</font>', "text", fontSize=12.5, leading=18)])
            dsty.append(("BACKGROUND", (0, i), (0, i), INK if ln.get("speaker") == first else C("#4A5A6C")))
            if i < len(lines) - 1: dsty.append(("LINEBELOW", (0, i), (-1, i), 2, colors.white))
        dt = Table(rows, colWidths=[48, CW - 48 - 28]); dt.setStyle(TableStyle(dsty))
        S += [KeepTogether([small_label("Model dialogue"), spacer("xs"), dt, spacer("xs"),
                            P(f"<font name='Body-B' color='{PALETTE['green']['dark']}'>Green bold</font> = stressed word \u00B7 <font name='Sym'>\u2197</font> voice goes up \u00B7 <font name='Sym'>\u2198</font> voice goes down", "cap")]), spacer("lg")]
    pf = d.get("pronunciation_focus") or {}
    if has(pf.get("title")):
        ex = " &nbsp;\u00B7&nbsp; ".join(f"<b>{esc(e)}</b>" for e in pf.get("examples", []))
        body = [P(f"<b>{esc(pf.get('title'))}.</b> {esc(pf.get('rule'))}", "cell"), Spacer(1, 6), P(ex, "cell", fontSize=11.5)]
        S.append(callout("green", body, label="Pattern \u00B7 pronunciation"))
        if has(pf.get("common_slip")): S += [spacer("sm"), callout("red", esc(pf.get("common_slip")), label="Watch out")]

def page_task(d, S):
    t = d.get("tblt_task", {})
    S += [PageBreak(), ModeMarker("student"),
          front_header("03", "Task-Based Learning", esc(t.get("title", "Task")), "Meaning first. Use the language you have; form comes after the task."), spacer("md"),
          teacher_rail(esc(d.get("teacher_tblt_note", ""))), spacer("md")]
    out = Table([[P("OUTCOME", "label", textColor=colors.white, fontName="Head-B"),
                  P(esc(t.get("outcome", "")), "body", textColor=colors.white, fontSize=12.5, leading=17)]], colWidths=[70, CW - 70])
    out.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 14),
                             ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
    S += [out, spacer("sm"), card("Your role and the problem", esc(t.get("role_problem", ""))), spacer("md")]
    stp = [("PRE-TASK", "2 min", t.get("pre_task")), ("TASK", "8 min", t.get("task")), ("PLAN", "3 min", t.get("planning")), ("REPORT", "5 min", t.get("report"))]
    st = Table([[P(a, "th", textColor=INK, fontName="Head-B"), P(b, "cellb", textColor=MUTED), P(esc(c), "cell")] for a, b, c in stp], colWidths=[64, 46, CW - 110])
    st.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE), ("LINEABOVE", (0, 0), (-1, 0), 0.5, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 4)]))
    S += [st, spacer("md"), small_label("Task prompts"), spacer("sm")]
    prompts = t.get("task_prompts", [])
    tb = [[P("#", "th"), P("PROMPT", "th"), P("YOUR NOTES", "th")]] + [[P(str(i), "cellb", textColor=MUTED), P(esc(p), "cell"), ""] for i, p in enumerate(prompts, 1)]
    pt = Table(tb, colWidths=[26, 250, CW - 276], repeatRows=1)
    pt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE),
                            ("LINEBEFORE", (2, 1), (2, -1), 0.5, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 1), (-1, -1), 5), ("BOTTOMPADDING", (0, 1), (-1, -1), 5)]))
    S += [pt, spacer("md")]
    ul = t.get("useful_language", [])
    if ul:
        lines = [[P(esc(x), "cell")] for x in ul]
        w = Table(lines, colWidths=[CW - 26 - 24]); w.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.white), ("LINEBELOW", (0, 0), (-1, -2), 0.5, LINE),
                                                                        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
        S.append(callout("green", [w], label="Useful language"))

def page_language_focus(d, S):
    lf = d.get("language_focus") or {}
    if not has(lf.get("title")): return
    S += [PageBreak(), ModeMarker("student"), P("FRONT 03 \u00B7 CONTINUED", "label"), spacer("xs"), P("Language focus after the task", "h2"), spacer("md")]
    S += [small_label("Your notes from the task"), sub_caption("Write 2 sentences you said or heard."), spacer("xs"), WriteLines(2, gap=26), spacer("md")]
    heads = (lf.get("column_headers") or ["", "", ""])[:3]
    rows = [[P(esc(h).upper(), "th") for h in heads]]
    sty = [("BACKGROUND", (0, 0), (-1, 0), C(PALETTE["green"]["dark"])), ("BACKGROUND", (0, 1), (-1, -1), colors.white), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
    for i, r in enumerate(lf.get("rows", []), 1):
        exc = r.get("is_exception")
        rows.append([P(f"<b>{esc(r.get('col1'))}</b>", "cell"), P(esc(r.get("col2")), "cell"), P(hl(esc(r.get("col3")), "err" if exc else "verb"), "cellb")])
        if exc: sty.append(("BACKGROUND", (0, i), (-1, i), C("#FFF7F7")))
    tab = Table(rows, colWidths=[CW * 0.3, CW * 0.33, CW - 26 - CW * 0.63]); tab.setStyle(TableStyle(sty))
    S += [callout("green", [P(f"<b>{esc(lf.get('title'))}.</b> {esc(lf.get('formula'))}", "body"), Spacer(1, 7), tab], label="Pattern"), spacer("md")]
    errs = lf.get("errors", [])
    if errs:
        er = [[P(bad(esc(e.get("wrong"))), "cell"), P(ok(esc(e.get("right"))), "cell")] for e in errs]
        et = Table(er, colWidths=[(CW - 26) / 2] * 2)
        et.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.white), ("LINEBELOW", (0, 0), (-1, -2), 0.5, LINE), ("TOPPADDING", (0, 0), (-1, -1), 5),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        S.append(callout("red", [et, Spacer(1, 4), P("<b>Your turn:</b> find one of these errors in your own notes and correct it.", "small")], label="Watch out \u00B7 common errors"))

def page_reconfig(d, S):
    rc = d.get("reconfiguration", {})
    S += [PageBreak(), ModeMarker("student"),
          front_header("04", "Reconfiguration", "Same meaning, new shape", "Rebuild and transform language. Notice what moves."), spacer("md"),
          teacher_rail(esc(d.get("teacher_reconfiguration_note", ""))), spacer("md"),
          small_label("Activity A \u00B7 Rebuild the sentence"), sub_caption(rc.get("shuffle_instruction", "")), spacer("sm")]
    for i, it in enumerate(rc.get("shuffle_items", []), 1):
        chips = " ".join(f'<font backColor="#E3E8EE">&nbsp;&nbsp;{esc(b)}&nbsp;&nbsp;</font>' for b in it.get("blocks", []))
        blk = Table([[P(f"<b>{i}.</b>", "cell", textColor=MUTED),
                      [P(f"<i>{esc(it.get('intent_hint'))}</i>", "small", textColor=MUTED), Spacer(1, 4), P(chips, "text", fontSize=12, leading=20), WriteLines(1, width=CW - 34, gap=24)]]],
                    colWidths=[24, CW - 24])
        blk.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        S.append(KeepTogether(blk))
    items = rc.get("transform_items", [])
    if items and has(rc.get("transform_instruction")):
        S += [spacer("lg"), small_label("Activity B \u00B7 Transform"), sub_caption(rc.get("transform_instruction")), spacer("sm")]
        rt = [[P("ORIGINAL", "th"), P("YOU WRITE\u2026", "th")]] + [[P(f"{i}. {esc(x.get('original'))}", "cell"), ""] for i, x in enumerate(items, 1)]
        rtab = Table(rt, colWidths=[CW / 2] * 2, rowHeights=[22] + [29] * len(items))
        rtab.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), C(PALETTE["blue"]["main"])), ("BACKGROUND", (1, 0), (1, 0), C(PALETTE["green"]["main"])),
                                  ("BACKGROUND", (0, 1), (0, -1), C(PALETTE["blue"]["tint"])), ("BACKGROUND", (1, 1), (1, -1), C(PALETTE["green"]["tint"])),
                                  ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 1), (-1, -1), 1.5, colors.white), ("LEFTPADDING", (0, 0), (-1, -1), 12)]))
        S.append(rtab)

def page_check(d, S):
    S += [PageBreak(), ModeMarker("student"), P("CHECK \u00B7 5 MINUTES", "label"), spacer("xs"), P("Quick check of understanding", "h2"),
          P("Work alone. Circle or write. Your teacher will check the answers with you.", "body", textColor=MUTED, fontSize=10.5), spacer("lg")]
    for i, it in enumerate(d.get("check_items", []), 1):
        num = Table([[Paragraph(f'<font name="Head-B" size="12" color="#FFFFFF">{i}</font>', ParagraphStyle("q", alignment=TA_CENTER, leading=14))]], colWidths=[26], rowHeights=[26])
        num.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        opts = it.get("options", [])
        extra = P(" &nbsp;&nbsp;&nbsp; ".join(f"{'abc'[j]}) {esc(o)}" for j, o in enumerate(opts[:3])), "text", fontSize=12) if opts else WriteLines(2, width=CW - 40, gap=26)
        t = Table([[num, [P(esc(it.get("prompt")), "instr", fontSize=11.5), Spacer(1, 6), extra]]], colWidths=[40, CW - 40])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 8),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 10), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE)]))
        S.append(KeepTogether(t))
    cando = d.get("can_do", [])
    if cando:
        S += [spacer("xl"), small_label("I can\u2026"), sub_caption("Fill the circles: 1 = not yet \u00B7 2 = almost \u00B7 3 = yes!"), spacer("sm")]
        cr = [[P(esc(c), "body"), P('<font name="Sym" size="15">\u25CB&nbsp;&nbsp;\u25CB&nbsp;&nbsp;\u25CB</font>', "body", alignment=TA_CENTER)] for c in cando]
        ct = Table(cr, colWidths=[CW - 110, 110])
        ct.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOX", (0, 0), (-1, -1), 0.8, C("#9AA5B1")), ("LINEBELOW", (0, 0), (-1, -2), 0.5, LINE),
                                ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9), ("LEFTPADDING", (0, 0), (-1, -1), 14)]))
        S.append(ct)

def page_teacher(d, S):
    S += [PageBreak(), ModeMarker("teacher"), P("TEACHER NOTES", "label"), spacer("xs"), P("Language analysis, problems and answer key", "h2"), spacer("md")]
    m = d.get("mfp", {})
    mfp = Table([[P("MEANING", "th"), P("FORM", "th"), P("PRONUNCIATION", "th")],
                 [P(esc(m.get("meaning")), "small"), P(esc(m.get("form")), "small"), P(esc(m.get("pronunciation")), "small")]], colWidths=[CW / 3] * 3)
    mfp.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                             ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9), ("BOX", (0, 1), (-1, -1), 0.5, LINE), ("LINEBEFORE", (1, 1), (2, -1), 0.5, LINE)]))
    S += [small_label("Language analysis (MFP)"), spacer("sm"), mfp, spacer("md")]
    probs = d.get("anticipated_problems", [])
    if probs:
        S += [small_label("Anticipated problems & solutions"), spacer("sm"),
              data_table(["Problem", "Solution"], [[P(esc(p.get("problem")), "cell"), P(esc(p.get("solution")), "cell")] for p in probs], [200, CW - 200], pad=3), spacer("sm")]
    key = []
    g = d.get("gist_questions", [])
    if g: key.append(("01 Input", "Gist: " + " \u00B7 ".join(f"{i} {esc(q.get('answer'))}" for i, q in enumerate(g, 1))
                      + " \u00B7 True/false: " + ", ".join(f"{i} {'T' if t.get('answer') else 'F'}" for i, t in enumerate(d.get("true_false", []), 1))))
    rc = d.get("reconfiguration", {})
    if rc.get("shuffle_items"): key.append(("04 Rebuild", " \u00B7 ".join(f"{i} {esc(x.get('answer'))}" for i, x in enumerate(rc["shuffle_items"], 1))))
    if rc.get("transform_items"): key.append(("04 Transform", " \u00B7 ".join(f"{i} {esc(x.get('answer'))}" for i, x in enumerate(rc["transform_items"], 1))))
    if d.get("check_items"): key.append(("05 Check", " \u00B7 ".join(f"{i} {esc(x.get('answer'))}" for i, x in enumerate(d["check_items"], 1))))
    if key:
        S += [small_label("Answer key"), spacer("sm"), data_table(["Stage", "Answers"], [[P(f"<b>{a}</b>", "cell"), P(b, "cell")] for a, b in key], [90, CW - 90], pad=3), spacer("sm")]
    if has(d.get("pedagogical_rationale")):
        S.append(callout("blue", esc(d.get("pedagogical_rationale")), label="Read \u00B7 rationale"))


# ------------------------------------------------------------------ public API
def build_advanced_pdf(json_data: dict, output_path: str) -> str:
    """Renders the lesson. If a block is taller than a page, retries once with splittable blocks."""
    for attempt in (0, 1):
        _lk.FORCE_SPLIT = bool(attempt)
        try:
            return _build(json_data, output_path)
        except LayoutError:
            if attempt: raise
        finally:
            _lk.FORCE_SPLIT = False

def _build(json_data, output_path):
    d, S = json_data or {}, []
    page_overview(d, S); page_input(d, S); page_shadowing(d, S); page_task(d, S)
    page_language_focus(d, S); page_reconfig(d, S); page_check(d, S); page_teacher(d, S)
    title = d.get("lesson_title", "English Lesson"); level = d.get("cefr_level", "")
    build_pdf(output_path, S,
              cover=dict(kicker=f"Lesson pack \u00B7 {level}", title=title, subtitle=d.get("focus_summary", ""),
                         chips=[f"{level} \u00B7 CEFR", "60 MIN", "4 FRONTS: INPUT \u00B7 SHADOWING \u00B7 TBLT \u00B7 RECONFIGURATION"]),
              running_left=title, footer=f"Lesson Pack \u00B7 {level} \u00B7 {title}"[:70], title=f"Lesson Pack - {title}", author="AI English Teacher Agent")
    print(f"\u2728 PDF guardado em: {output_path}")
    return output_path
