# -*- coding: utf-8 -*-
"""
把 Dry Lab 页面的 Markdown 转成 Word（iGEM wiki 交付用）。

支持：# / ## / ### 标题、**粗体**、`等宽`、[文字](链接)、![图注](路径)、
      独立成段的 $$...$$ 公式块、**Figure N. ...** 图注段落。

用法：uv run --with python-docx python make_drylab_docx.py
产出：APOBEC_DryLab_Complete.docx
"""
import os, re, sys, time
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "APOBEC_DryLab_Complete.md")
OUT = os.path.join(HERE, "APOBEC_DryLab_Complete.docx")
try:
    with open(OUT, "r+b"):
        pass
except (PermissionError, FileNotFoundError):
    if os.path.exists(OUT):
        OUT = OUT.replace(".docx", f"_{time.strftime('%m%d_%H%M')}.docx")

EN = "Calibri"
CJK = "微软雅黑"
INK = (0x1A, 0x1A, 0x1A)
NAVY = (0x1F, 0x3B, 0x66)
MUTED = (0x59, 0x59, 0x59)
LINK = (0x1F, 0x4E, 0x79)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.4)
sec.top_margin = sec.bottom_margin = Cm(2.2)
st = doc.styles["Normal"]
st.font.name = EN
st.font.size = Pt(10.5)
st._element.rPr.rFonts.set(qn("w:eastAsia"), CJK)


def _fmt(run, size=None, bold=None, italic=None, color=None, mono=False):
    name = "Consolas" if mono else EN
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), CJK)
    if size is not None: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if italic is not None: run.font.italic = italic
    if color is not None: run.font.color.rgb = RGBColor(*color)


INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def rich(p, text, size=10.5, color=INK, bold=False, italic=False):
    """写入一行文本，处理 **粗体**、`等宽`、[文字](链接)。"""
    for seg in INLINE.split(text):
        if not seg:
            continue
        if seg.startswith("**") and seg.endswith("**"):
            _fmt(p.add_run(seg[2:-2]), size, True, italic, color)
        elif seg.startswith("`") and seg.endswith("`"):
            _fmt(p.add_run(seg[1:-1]), size - 0.5, bold, italic, (0x30, 0x30, 0x30), mono=True)
        elif seg.startswith("[") and "](" in seg:
            label, url = re.match(r"\[([^\]]+)\]\(([^)]+)\)", seg).groups()
            r = p.add_run(label)
            _fmt(r, size, bold, italic, LINK)
        else:
            _fmt(p.add_run(seg), size, bold, italic, color)


def para(text, size=10.5, color=INK, bold=False, italic=False, after=8, align=None, indent=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.45
    if align is not None:
        p.alignment = align
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
        p.paragraph_format.first_line_indent = Cm(-indent)
    rich(p, text, size, color, bold, italic)
    return p


lines = open(SRC, encoding="utf-8").read().splitlines()
i, first_h1 = 0, True
while i < len(lines):
    s = lines[i].strip()
    if not s:
        i += 1
        continue

    # 独立公式块 $$ ... $$
    if s == "$$":
        block, j = [], i + 1
        while j < len(lines) and lines[j].strip() != "$$":
            if lines[j].strip():
                block.append(lines[j].strip())
            j += 1
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(10)
        _fmt(p.add_run(" ".join(block)), 10.5, False, True, INK, mono=True)
        i = j + 1
        continue

    # 图片
    m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", s)
    if m:
        path = os.path.join(HERE, m.group(2).replace("/", os.sep))
        if os.path.exists(path):
            doc.add_picture(path, width=Cm(15.5))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.paragraphs[-1].paragraph_format.space_before = Pt(8)
        else:
            para(f"[缺图：{m.group(2)}]", 9, MUTED, after=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        i += 1
        continue

    # 标题
    if s.startswith("# "):
        if first_h1:
            para(s[2:], 20, NAVY, True, after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
            first_h1 = False
        else:
            para(s[2:], 15, NAVY, True, after=14, align=WD_ALIGN_PARAGRAPH.CENTER)
        i += 1
        continue
    if s.startswith("## "):
        p = doc.add_heading(s[3:], 2)
        for r in p.runs:
            _fmt(r, 13.5, True, False, NAVY)
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(8)
        i += 1
        continue
    if s.startswith("### "):
        p = doc.add_heading(s[4:], 3)
        for r in p.runs:
            _fmt(r, 11.5, True, False, NAVY)
        i += 1
        continue

    # Figure 图注：小字号灰色
    if re.match(r"\*\*Figure \d+\.", s):
        para(s, 9, MUTED, after=16)
        i += 1
        continue

    # 参考文献条目：悬挂缩进
    if re.match(r"^[A-Z][A-Za-z’\-]+,\s+[A-Z]\.", s) or s.startswith("Google DeepMind.") \
       or s.startswith("scikit-learn developers.") or s.startswith("SciPy community."):
        para(s, 9.5, INK, after=10, indent=0.75)
        i += 1
        continue

    para(s)
    i += 1

doc.save(OUT)
print("写入", OUT)
