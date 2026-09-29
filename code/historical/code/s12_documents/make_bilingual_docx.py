# -*- coding: utf-8 -*-
"""
把中英对照版 Markdown 转成 Word。

排版规则：逐段判断是否含中日韩字符——
  含中文 → 中文段落样式（左侧缩进 + 深灰蓝），表示「这是译文」；
  纯英文 → 英文段落样式（正常色），表示「这是原文」。
标题、图注、公式、引文注释各有专门处理。

用法：uv run --with python-docx python make_bilingual_docx.py
产出：APOBEC_DryLab_Complete_中英对照.docx
"""
import os, re, sys, time
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "APOBEC_DryLab_Complete_中英对照.md")
OUT = os.path.join(HERE, "APOBEC_DryLab_Complete_中英对照.docx")
try:
    with open(OUT, "r+b"):
        pass
except (PermissionError, FileNotFoundError):
    if os.path.exists(OUT):
        OUT = OUT.replace(".docx", f"_{time.strftime('%m%d_%H%M')}.docx")

EN_FONT, CJK_FONT = "Calibri", "微软雅黑"
INK = (0x1A, 0x1A, 0x1A)          # 英文原文
ZH_INK = (0x1F, 0x3B, 0x66)       # 中文译文（深蓝，便于与原文区分）
NAVY = (0x1F, 0x3B, 0x66)
MUTED = (0x59, 0x59, 0x59)
LINK = (0x1F, 0x4E, 0x79)

CJK = re.compile(r"[　-〿぀-ヿ一-鿿＀-￯]")

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.3)
sec.top_margin = sec.bottom_margin = Cm(2.2)
st = doc.styles["Normal"]
st.font.name = EN_FONT
st.font.size = Pt(10.5)
st._element.rPr.rFonts.set(qn("w:eastAsia"), CJK_FONT)


def _fmt(run, size=None, bold=None, italic=None, color=None, mono=False):
    run.font.name = "Consolas" if mono else EN_FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), CJK_FONT)
    if size is not None: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if italic is not None: run.font.italic = italic
    if color is not None: run.font.color.rgb = RGBColor(*color)


INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\$[^$]+\$)")


def rich(p, text, size=10.5, color=INK, bold=False, italic=False):
    for seg in INLINE.split(text):
        if not seg:
            continue
        if seg.startswith("**") and seg.endswith("**"):
            _fmt(p.add_run(seg[2:-2]), size, True, italic, color)
        elif seg.startswith("`") and seg.endswith("`"):
            _fmt(p.add_run(seg[1:-1]), size - .5, bold, italic, (0x30, 0x30, 0x30), mono=True)
        elif seg.startswith("$") and seg.endswith("$") and len(seg) > 2:
            _fmt(p.add_run(seg[1:-1]), size, bold, True, color, mono=True)
        elif seg.startswith("[") and "](" in seg:
            label = re.match(r"\[([^\]]+)\]\(([^)]+)\)", seg).group(1)
            _fmt(p.add_run(label), size, bold, italic, LINK)
        else:
            _fmt(p.add_run(seg), size, bold, italic, color)


def para(text, size=10.5, color=INK, bold=False, italic=False, after=6,
         align=None, indent=None, mono=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.4
    if align is not None:
        p.alignment = align
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    if mono:
        _fmt(p.add_run(text), size, bold, italic, color, mono=True)
    else:
        rich(p, text, size, color, bold, italic)
    return p


lines = open(SRC, encoding="utf-8").read().splitlines()
i, first_h1 = 0, True
in_formula = False
while i < len(lines):
    s = lines[i].strip()
    if not s:
        i += 1
        continue

    if s == "$$":
        block, j = [], i + 1
        while j < len(lines) and lines[j].strip() != "$$":
            if lines[j].strip():
                block.append(lines[j].strip())
            j += 1
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(4)
        _fmt(p.add_run(" ".join(block)), 10.5, False, True, INK, mono=True)
        i = j + 1
        continue

    m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", s)
    if m:
        path = os.path.join(HERE, m.group(2).replace("/", os.sep))
        if os.path.exists(path):
            doc.add_picture(path, width=Cm(15.6))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.paragraphs[-1].paragraph_format.space_before = Pt(8)
        else:
            para(f"[缺图：{m.group(2)}]", 9, MUTED, after=6, align=WD_ALIGN_PARAGRAPH.CENTER)
        i += 1
        continue

    if s.startswith("# "):
        t = s[2:]
        if first_h1:
            para(t, 20, NAVY, True, after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
            first_h1 = False
        else:
            para(t, 15, NAVY, True, after=14, align=WD_ALIGN_PARAGRAPH.CENTER)
        i += 1
        continue
    if s.startswith("## "):
        p = doc.add_heading(s[3:], 2)
        for r in p.runs:
            _fmt(r, 13.5, True, False, NAVY)
        p.paragraph_format.space_before = Pt(15)
        p.paragraph_format.space_after = Pt(8)
        i += 1
        continue
    if s.startswith("### "):
        p = doc.add_heading(s[4:], 3)
        for r in p.runs:
            _fmt(r, 11.5, True, False, NAVY)
        i += 1
        continue

    if s.startswith(">"):
        para(s.lstrip("> ").strip(), 9, MUTED, after=4, indent=.4)
        i += 1
        continue

    if re.match(r"\*\*(Figure|图)\s*\d+[\.　]", s):
        para(s, 9, MUTED, after=4 if not CJK.search(s) else 14,
             indent=.4 if not CJK.search(s) else 0)
        i += 1
        continue

    if s.startswith("（按学术惯例"):
        para(s, 9.5, MUTED, after=10)
        i += 1
        continue

    if re.match(r"^[A-Z][A-Za-z’\-]+,\s+[A-Z]\.", s) or s.startswith("Google DeepMind.") \
       or s.startswith("scikit-learn developers.") or s.startswith("SciPy community."):
        para(s, 9.5, INK, after=10, indent=.75)
        i += 1
        continue

    # 正文：按是否含中文选择样式
    if CJK.search(s):
        para(s, 10.5, ZH_INK, after=12, indent=.55)
    else:
        para(s, 10.5, INK, after=4)
    i += 1

doc.save(OUT)
print("写入", OUT)
