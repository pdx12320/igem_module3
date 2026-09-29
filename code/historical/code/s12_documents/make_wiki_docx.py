# -*- coding: utf-8 -*-
"""
把 wiki 文案（Markdown）转成 Word，便于与队友的 docx 流程对接。

用法：uv run --with python-docx python make_wiki_docx.py [中英双语|SONAR体]
      不带参数时两份都生成。
产出：APOBEC_Wiki_文案_中英双语.docx、APOBEC_Wiki_文案_SONAR体.docx
"""
import os, re, sys, time
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
VARIANTS = ["中英双语", "SONAR体"]
_argv = [a for a in sys.argv[1:] if not a.startswith("-")]
TARGETS = _argv if _argv else VARIANTS
for _v in TARGETS:
    if _v not in VARIANTS:
        sys.exit(f"未知变体 {_v}；可选：{'、'.join(VARIANTS)}")

CN = "微软雅黑"
INK, NAVY, MUTED, ACC = (0x17, 0x15, 0x36), (0x2E, 0x26, 0x7C), (0x6B, 0x68, 0x80), (0xB4, 0x4A, 0x3C)


def _cn(run, size=None, bold=None, color=None, italic=None):
    run.font.name = CN
    run._element.rPr.rFonts.set(qn("w:eastAsia"), CN)
    if size is not None: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if italic is not None: run.font.italic = italic
    if color is not None: run.font.color.rgb = RGBColor(*color)


def build(variant):
    src = os.path.join(HERE, f"APOBEC_Wiki_文案_{variant}.md")
    out = os.path.join(HERE, f"APOBEC_Wiki_文案_{variant}.docx")
    try:
        with open(out, "r+b"):
            pass
    except (PermissionError, FileNotFoundError):
        if os.path.exists(out):
            out = out.replace(".docx", f"_{time.strftime('%m%d_%H%M')}.docx")

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.4)
    sec.top_margin = sec.bottom_margin = Cm(2.2)
    st = doc.styles["Normal"]
    st.font.name = CN
    st.font.size = Pt(11)
    st._element.rPr.rFonts.set(qn("w:eastAsia"), CN)

    def para(text, size=11, bold=False, color=(0x26, 0x26, 0x26), after=8):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = 1.5
        # 行内 **粗体**
        for seg in re.split(r"(\*\*[^*]+\*\*)", text):
            if not seg:
                continue
            if seg.startswith("**") and seg.endswith("**"):
                r = p.add_run(seg[2:-2]); _cn(r, size, True, color)
            else:
                r = p.add_run(seg); _cn(r, size, bold, color)
        return p

    lines = open(src, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        s = ln.strip()
        if not s:
            i += 1; continue
        if s == "---":
            doc.add_paragraph(); i += 1; continue
        if s.startswith("### "):
            doc.add_heading(s[4:], 3); i += 1; continue
        if s.startswith("## "):
            doc.add_heading(s[3:], 2); i += 1; continue
        if s.startswith("# "):
            doc.add_heading(s[2:], 1); i += 1; continue
        if s.startswith(">"):
            para(s.lstrip("> ").strip(), 9.5, False, MUTED); i += 1; continue
        if s.startswith("*") and s.endswith("*") and not s.startswith("**"):
            para(s.strip("*"), 11, False, MUTED); i += 1; continue
        if s.startswith("图 "):
            para(s, 9.5, False, MUTED, after=14); i += 1; continue
        para(s)
        i += 1

    doc.save(out)
    print("写入", out)


for _v in TARGETS:
    build(_v)
