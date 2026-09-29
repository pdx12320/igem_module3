# -*- coding: utf-8 -*-
"""
docx_build.py —— 用「已知可用 DOCX 作为模板 + 注入 document.xml」的方式生成 DOCX
（本机 Word COM 不可用，PPTX 用 COM 模板法，DOCX 用现成 docx 作模板）
"""
import os, re, sys, zipfile, shutil
from xml.sax.saxutils import escape as _e
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "导师汇报_APOBEC_保G排A优化_研究总结.docx")

# 颜色
NAVY, NAVY2, BLUE, GOLD = "1F3864", "1F4E79", "2E74B5", "F2A900"
GREEN, RED, GRAY, LGRAY = "548235", "C00000", "404040", "595959"
TXT, WHITE = "262626", "FFFFFF"
BG, WARNBG, KEYBG = "F2F7FB", "FFF4E5", "EAF3FB"


def _rpr(sz=21, b=False, i=False, color=TXT, font="等线", u=False):
    # sz 单位为半磅：21 => 10.5pt
    x = (f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:eastAsia="{font}" w:cs="{font}"/>'
         f'<w:b w:val="{1 if b else 0}"/><w:i w:val="{1 if i else 0}"/>'
         f'<w:color w:val="{color}"/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>')
    if u:
        x += '<w:u w:val="single"/>'
    return x


def _runs(text, sz=21, b=False, i=False, color=TXT, font="等线"):
    """支持 **粗体** 与 [[红色]] 标记"""
    out = []
    for seg in re.split(r'(\*\*[^*]+\*\*|\[\[[^\]]+\]\])', str(text)):
        if not seg:
            continue
        bb, cc = b, color
        if seg.startswith("**") and seg.endswith("**"):
            seg, bb = seg[2:-2], True
        elif seg.startswith("[[") and seg.endswith("]]"):
            seg, cc = seg[2:-2], RED
        out.append(f'<w:r><w:rPr>{_rpr(sz, bb, i, cc, font)}</w:rPr>'
                   f'<w:t xml:space="preserve">{_e(seg)}</w:t></w:r>')
    return "".join(out) or f'<w:r><w:rPr>{_rpr(sz,b,i,color,font)}</w:rPr><w:t></w:t></w:r>'


class Docx:
    def __init__(self, template=TEMPLATE):
        self.tpl = template
        self.body = []
        with zipfile.ZipFile(template) as z:
            doc = z.read("word/document.xml").decode("utf-8")
        m = re.search(r'(<w:body[^>]*>)', doc)
        self.head = doc[:m.end()]
        s = re.search(r'(<w:sectPr\b.*?</w:sectPr>)\s*</w:body>', doc, re.S)
        self.sect = s.group(1) if s else (
            '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
            'w:header="851" w:footer="992" w:gutter="0"/>'
            '<w:cols w:space="720"/><w:docGrid w:linePitch="360"/></w:sectPr>')

    # ---------- 基本块 ----------
    def _p(self, inner, jc=None, after=90, before=0, line=300, ind=None, bdr=None, shd=None):
        pr = ['<w:pPr>']
        if bdr:
            pr.append(bdr)
        if shd:
            pr.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{shd}"/>')
        pr.append(f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>')
        if ind:
            pr.append(f'<w:ind {ind}/>')
        if jc:
            pr.append(f'<w:jc w:val="{jc}"/>')
        pr.append('</w:pPr>')
        self.body.append(f'<w:p>{"".join(pr)}{inner}</w:p>')
        return self

    def p(self, text, sz=21, b=False, color=TXT, jc=None, after=90, before=0,
          ind=None, i=False, font="等线", line=300):
        return self._p(_runs(text, sz, b, i, color, font), jc, after, before, line, ind)

    def h1(self, t):
        bdr = ('<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="2" w:color="2E74B5"/></w:pBdr>')
        self._p(_runs(t, 32, True, False, NAVY2), after=110, before=260, bdr=bdr)
        return self

    def h2(self, t):
        bdr = ('<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="2" w:color="BFBFBF"/></w:pBdr>')
        self._p(_runs(t, 26, True, False, BLUE), after=90, before=200, bdr=bdr)
        return self

    def h3(self, t):
        return self.p(t, sz=23, b=True, color=NAVY, after=70, before=140)

    def h4(self, t):
        return self.p(t, sz=21, b=True, color=GRAY, after=60, before=110)

    def bullet(self, text, level=0, sz=21):
        ind = f'w:left="{360 + level * 340}" w:hanging="260"'
        mark = "● " if level == 0 else ("○ " if level == 1 else "· ")
        return self._p(_runs(mark + text, sz, False, False, TXT), after=55, ind=ind, line=288)

    def note(self, text, kind="note"):
        fill = {"note": WARNBG, "key": KEYBG, "warn": "FDECEA"}[kind]
        col = {"note": GOLD, "key": NAVY, "warn": RED}[kind]
        bdr = (f'<w:pBdr><w:left w:val="single" w:sz="18" w:space="6" w:color="{col}"/></w:pBdr>')
        self._p(_runs(text, 20, False, False, "8A5A00" if kind == "note" else TXT),
                after=110, before=60, bdr=bdr, shd=fill, ind='w:left="120" w:right="120"')
        return self

    def key(self, text):
        return self.note(text, "key")

    def warn(self, text):
        return self.note(text, "warn")

    def small(self, text):
        return self.p(text, sz=17, color=LGRAY, after=100)

    def pagebreak(self):
        self.body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        return self

    def spacer(self, n=1):
        for _ in range(n):
            self.p("", sz=10, after=0)
        return self

    def table(self, header, rows, widths=None, sz=17, aligns=None, hdr_fill=NAVY2,
              zebra=True, first_col_left=True):
        n = len(header)
        widths = widths or [1] * n
        tot = sum(widths)
        AVAIL = 9360
        cols = [int(AVAIL * w / tot) for w in widths]
        grid = "".join(f'<w:gridCol w:w="{c}"/>' for c in cols)

        def cell(txt, w, is_hdr, fill=None, al="center"):
            shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ""
            inner = _runs(txt, sz, is_hdr, False, WHITE if is_hdr else TXT)
            return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}'
                    f'<w:vAlign w:val="center"/></w:tcPr>'
                    f'<w:p><w:pPr><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/>'
                    f'<w:jc w:val="{al}"/></w:pPr>{inner}</w:p></w:tc>')

        x = ['<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/>'
             '<w:tblBorders>'
             '<w:top w:val="single" w:sz="8" w:color="7F7F7F"/>'
             '<w:left w:val="single" w:sz="8" w:color="7F7F7F"/>'
             '<w:bottom w:val="single" w:sz="8" w:color="7F7F7F"/>'
             '<w:right w:val="single" w:sz="8" w:color="7F7F7F"/>'
             '<w:insideH w:val="single" w:sz="4" w:color="BFBFBF"/>'
             '<w:insideV w:val="single" w:sz="4" w:color="BFBFBF"/>'
             '</w:tblBorders>'
             '<w:tblLayout w:type="fixed"/><w:tblLook w:val="04A0"/></w:tblPr>'
             f'<w:tblGrid>{grid}</w:tblGrid>']
        x.append('<w:tr><w:trPr><w:tblHeader/></w:trPr>' +
                 "".join(cell(t, cols[i], True, hdr_fill, "center") for i, t in enumerate(header)) +
                 '</w:tr>')
        for ri, r in enumerate(rows):
            fill = BG if (zebra and ri % 2 == 1) else None
            x.append('<w:tr>')
            for ci, t in enumerate(r):
                al = "center"
                if aligns and ci < len(aligns):
                    al = {"l": "left", "c": "center", "r": "right"}[aligns[ci]]
                elif first_col_left and ci == 0:
                    al = "left"
                x.append(cell(t, cols[ci], False, fill, al))
            x.append('</w:tr>')
        x.append('</w:tbl>')
        self.body.append("".join(x))
        self.p("", sz=10, after=60)
        return self

    def save(self, out, landscape=False):
        doc = self.head + "".join(self.body) + self.sect + "</w:body></w:document>"
        if landscape:
            doc = re.sub(r'<w:pgSz w:w="(\d+)" w:h="(\d+)"',
                         lambda m: f'<w:pgSz w:w="{m.group(2)}" w:h="{m.group(1)}" w:orient="landscape"', doc)
        out = os.path.abspath(out)
        wd = os.path.join(HERE, "_work", "docx")
        if os.path.isdir(wd):
            shutil.rmtree(wd)
        os.makedirs(wd, exist_ok=True)
        with zipfile.ZipFile(self.tpl) as z:
            z.extractall(wd)
        with open(os.path.join(wd, "word", "document.xml"), "w", encoding="utf-8") as f:
            f.write(doc)
        # 去掉缩略图（尺寸不符会导致 Word 警告）并同步清理 [Content_Types] 与 _rels/.rels
        th = os.path.join(wd, "docProps", "thumbnail.wmf")
        if os.path.exists(th):
            os.remove(th)
        ct = os.path.join(wd, "[Content_Types].xml")
        s = open(ct, encoding="utf-8").read()
        s = re.sub(r'<Override PartName="/docProps/thumbnail\.wmf"[^/]*/>', '', s)
        s = re.sub(r'<Default Extension="wmf"[^/]*/>', '', s)
        open(ct, "w", encoding="utf-8").write(s)
        for relp in (os.path.join(wd, "_rels", ".rels"),
                     os.path.join(wd, "docProps", "_rels", "core.xml.rels")):
            if os.path.exists(relp):
                r = open(relp, encoding="utf-8").read()
                r2 = re.sub(r'<Relationship[^>]*Target="[^"]*thumbnail\.wmf"[^>]*/>', '', r)
                r2 = re.sub(r'<Relationship[^>]*thumbnail[^>]*/>', '', r2)
                if r2 != r:
                    open(relp, "w", encoding="utf-8").write(r2)
        names = []
        for root, dirs, files in os.walk(wd):
            for fn in files:
                names.append(os.path.relpath(os.path.join(root, fn), wd).replace("\\", "/"))
        ctn = "[Content_Types].xml"
        names.sort(key=lambda x: (x != ctn, x))
        if os.path.exists(out):
            os.remove(out)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for nm in names:
                z.write(os.path.join(wd, nm.replace("/", os.sep)), nm)
        return out


def verify(path):
    """结构自检：zip 完整性 + XML 合法性"""
    import xml.etree.ElementTree as ET
    ok, msgs = True, []
    try:
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                ok = False; msgs.append("zip CRC error")
            for n in z.namelist():
                if n.endswith(".xml") or n.endswith(".rels"):
                    try:
                        ET.fromstring(z.read(n))
                    except Exception as ex:
                        ok = False; msgs.append(f"XML FAIL {n}: {ex}")
            msgs.append(f"parts={len(z.namelist())}")
    except Exception as ex:
        ok = False; msgs.append(str(ex))
    return ok, " | ".join(msgs)
