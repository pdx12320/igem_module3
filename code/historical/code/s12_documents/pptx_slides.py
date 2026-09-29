# -*- coding: utf-8 -*-
"""pptx_slides.py —— 生成 slide XML（纯 OOXML），并配合 pptx_build 组装成可打开的 PPTX"""
import sys, re
from xml.sax.saxutils import escape as _e
sys.stdout.reconfigure(encoding="utf-8")

S = dict(
    NAVY="1F4E79", NAVY2="16365C", GOLD="F2A900", BLUE="2E74B5",
    GREEN="548235", RED="C00000", PURPLE="7030A0", GRAY="404040",
    LGRAY="7F7F7F", BG="F2F7FB", WARN="FFF4E5", TXT="262626", WHITE="FFFFFF",
    SUB="BDD7EE", SUB2="D6E4F0",
)


def _runs(paras):
    """paras: list of dict(t, sz, b, color, i) —— 返回 a:p 列表"""
    out = []
    for p in paras:
        rr = []
        segs = re.split(r'(\*\*[^*]+\*\*)', str(p.get("t", "")))
        for seg in segs:
            if not seg:
                continue
            b = p.get("b", False)
            if seg.startswith("**") and seg.endswith("**"):
                seg, b = seg[2:-2], True
            rr.append(
                f'<a:r><a:rPr lang="zh-CN" altLang="en-US" sz="{int(p.get("sz",18)*100)}" '
                f'b="{1 if b else 0}" i="{1 if p.get("i",False) else 0}" dirty="0">'
                f'<a:solidFill><a:srgbClr val="{p.get("color",S["TXT"])}"/></a:solidFill>'
                f'<a:latin typeface="Calibri"/><a:ea typeface="等线"/></a:rPr>'
                f'<a:t>{_e(seg)}</a:t></a:r>')
        algn = p.get("align", "l")
        bu = p.get("bullet", False)
        ppr = f'<a:pPr algn="{algn}"' + (' indent="-228600" marL="228600"' if bu else "") + '>'
        ppr += ('<a:buFont typeface="Arial"/><a:buChar char="●"/>' if bu else '<a:buNone/>')
        if p.get("space_before"):
            ppr += f'<a:spcBef><a:spcPts val="{int(p["space_before"]*100)}"/></a:spcBef>'
        if p.get("space_after"):
            ppr += f'<a:spcAft><a:spcPts val="{int(p["space_after"]*100)}"/></a:spcAft>'
        ppr += '</a:pPr>'
        out.append(f'<a:p>{ppr}{"".join(rr) if rr else "<a:endParaRPr lang=\"zh-CN\"/>"}</a:p>')
    return "".join(out)


class Deck:
    W, H = 12192000, 6858000

    def __init__(self):
        self.parts = []     # list[str] 每个是 spTree 内容
        self._id = 100

    def _nid(self, k=1):
        self._id += k
        return self._id

    # ---------- 原子 ----------
    def box(self, x, y, cx, cy, paras, anchor="t", wrap="square"):
        i = self._nid()
        return (f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="T{i}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
                f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(cx)}" cy="{int(cy)}"/></a:xfrm>'
                f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
                f'<p:txBody><a:bodyPr wrap="{wrap}" lIns="0" tIns="0" rIns="0" bIns="0" anchor="{anchor}">'
                f'<a:normAutofit/></a:bodyPr><a:lstStyle/>{_runs(paras)}</p:txBody></p:sp>')

    def rect(self, x, y, cx, cy, fill, line=None, lw=12700):
        i = self._nid()
        ln = (f'<a:ln w="{lw}"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
              if line else '<a:ln><a:noFill/></a:ln>')
        return (f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="R{i}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
                f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(cx)}" cy="{int(cy)}"/></a:xfrm>'
                f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
                f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>{ln}</p:spPr>'
                f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="zh-CN"/></a:p></p:txBody></p:sp>')

    def table(self, x, y, cx, header, rows, widths=None, sz=10.5,
              hdr_fill=S["NAVY"], zebra=True, align=None, row_h=238760):
        i = self._nid()
        nc = len(header)
        widths = widths or [1] * nc
        tot = sum(widths)
        colw = [int(cx * w / tot) for w in widths]

        def tc(txt, fill, b=False, color=S["TXT"], al="ctr", h=None):
            hh = f' h="{h}"' if h else ""
            return (f'<a:tc{hh}><a:txBody><a:bodyPr lIns="45720" rIns="45720" tIns="13716" bIns="13716" '
                    f'anchor="ctr"/><a:lstStyle/><a:p><a:pPr algn="{al}"><a:buNone/></a:pPr>'
                    f'<a:r><a:rPr lang="zh-CN" sz="{int(sz*100)}" b="{1 if b else 0}" dirty="0">'
                    f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
                    f'<a:latin typeface="Calibri"/><a:ea typeface="等线"/></a:rPr>'
                    f'<a:t>{_e(str(txt))}</a:t></a:r></a:p></a:txBody>'
                    f'<a:tcPr marL="45720" marR="45720" marT="13716" marB="13716">'
                    f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
                    f'<a:lnL w="6350"><a:solidFill><a:srgbClr val="D9D9D9"/></a:solidFill></a:lnL>'
                    f'<a:lnR w="6350"><a:solidFill><a:srgbClr val="D9D9D9"/></a:solidFill></a:lnR>'
                    f'<a:lnT w="6350"><a:solidFill><a:srgbClr val="D9D9D9"/></a:solidFill></a:lnT>'
                    f'<a:lnB w="6350"><a:solidFill><a:srgbClr val="D9D9D9"/></a:solidFill></a:lnB>'
                    f'</a:tcPr></a:tc>')

        out = [f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{i}" name="Tbl{i}"/>'
               f'<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/>'
               f'</p:nvGraphicFramePr><p:xfrm><a:off x="{int(x)}" y="{int(y)}"/>'
               f'<a:ext cx="{int(cx)}" cy="{int((len(rows)+1)*row_h)}"/></p:xfrm>'
               f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
               f'<a:tbl><a:tblPr firstRow="1" bandRow="1"/>'
               f'<a:tblGrid>{"".join(f"<a:gridCol w=\"{w}\"/>" for w in colw)}</a:tblGrid>']
        out.append('<a:tr h="%d">' % int(row_h * 1.25) + "".join(
            tc(t, hdr_fill, True, S["WHITE"], "ctr", int(row_h * 1.25)) for t in header) + '</a:tr>')
        for ri, r in enumerate(rows):
            fill = S["BG"] if (zebra and ri % 2 == 1) else "FFFFFF"
            cells = []
            for ci, t in enumerate(r):
                al = align[ci] if (align and ci < len(align)) else "ctr"
                cells.append(tc(t, fill, False, S["TXT"], al, row_h))
            out.append(f'<a:tr h="{row_h}">' + "".join(cells) + '</a:tr>')
        out.append('</a:tbl></a:graphicData></a:graphic></p:graphicFrame>')
        return "".join(out)

    # ---------- 页面 ----------
    def _page(self, *shapes):
        self.parts.append("".join(shapes))

    def _header(self, title, subtitle=None, band=S["NAVY"]):
        sh = [self.rect(0, 0, self.W, 914400, band),
              self.rect(0, 914400, self.W, 45720, S["GOLD"])]
        n = len(title)
        tsz = 28 if n <= 24 else (24 if n <= 34 else (20 if n <= 46 else 17))
        sh.append(self.box(500000, 152400, self.W - 1000000, 610000,
                           [dict(t=title, sz=tsz, b=True, color=S["WHITE"])], anchor="ctr"))
        if subtitle:
            sh.append(self.box(500000, 700000, self.W - 1000000, 200000,
                               [dict(t=subtitle, sz=11, color=S["SUB2"])], anchor="ctr"))
        return sh, 1080000

    def title(self, main, sub, metas):
        sh = [self.rect(0, 0, self.W, self.H, S["NAVY"]),
              self.rect(0, int(self.H * .64), self.W, int(self.H * .36), S["NAVY2"]),
              self.rect(0, int(self.H * .625), self.W, 63500, S["GOLD"]),
              self.box(700000, int(self.H * .20), self.W - 1400000, 1400000,
                       [dict(t=main, sz=38, b=True, color=S["WHITE"], align="ctr")], anchor="ctr"),
              self.box(700000, int(self.H * .44), self.W - 1400000, 800000,
                       [dict(t=sub, sz=17, color=S["SUB"], align="ctr")], anchor="ctr"),
              self.box(900000, int(self.H * .72), self.W - 1800000, 900000,
                       [dict(t=m, sz=12.5, color=S["SUB2"], align="ctr", space_after=5) for m in metas],
                       anchor="t")]
        self._page(*sh)

    def section(self, num, text, sub=""):
        sh = [self.rect(0, 0, self.W, self.H, S["NAVY"]),
              self.box(900000, int(self.H * .30), 2000000, 1300000,
                       [dict(t=f"{num:02d}", sz=64, b=True, color=S["GOLD"], align="ctr")], anchor="ctr"),
              self.rect(int(self.W * .255), int(self.H * .42), 63500, 1100000, S["GOLD"]),
              self.box(int(self.W * .305), int(self.H * .36), int(self.W * .62), 1200000,
                       [dict(t=text, sz=30, b=True, color=S["WHITE"], space_after=10),
                        dict(t=sub, sz=13.5, color=S["SUB"])], anchor="ctr")]
        self._page(*sh)

    def bullets(self, title, items, subtitle=None, note=None):
        sh, y = self._header(title, subtitle)
        paras = []
        for it in items:
            txt, lvl = it if isinstance(it, tuple) else (it, 0)
            paras.append(dict(t=txt, sz=(16 if lvl == 0 else 13),
                              color=(S["NAVY"] if lvl == 0 else S["GRAY"]),
                              bullet=(lvl == 0), align="l",
                              space_after=(8 if lvl == 0 else 3),
                              space_before=(7 if lvl == 0 else 0)))
        sh.append(self.box(500000, y, self.W - 1000000, self.H - y - (760000 if note else 320000),
                           paras, anchor="t"))
        if note:
            sh.append(self.rect(500000, self.H - 720000, self.W - 1000000, 500000, S["WARN"], S["GOLD"]))
            sh.append(self.box(600000, self.H - 690000, self.W - 1200000, 440000,
                               [dict(t=note, sz=11.5, color="8A5A00")], anchor="ctr"))
        self._page(*sh)

    def table_page(self, title, header, rows, widths=None, subtitle=None, note=None,
                   sz=10.5, align=None, hdr_fill=S["NAVY"], row_h=238760):
        sh, y = self._header(title, subtitle)
        nrow = len(rows) + 1
        total_h = nrow * row_h + (0.25 * row_h if nrow else 0)
        avail = self.H - y - (760000 if note else 280000)
        scale = 1.0
        if total_h > avail:
            scale = avail / total_h
            row_h = int(row_h * scale)
            sz = max(7.5, sz * scale)
        sh.append(self.table(280000, y, self.W - 560000, header, rows, widths,
                             sz=sz, align=align, hdr_fill=hdr_fill, row_h=row_h))
        if note:
            sh.append(self.rect(280000, self.H - 720000, self.W - 560000, 500000, S["WARN"], S["GOLD"]))
            sh.append(self.box(380000, self.H - 690000, self.W - 760000, 440000,
                               [dict(t=note, sz=11.5, color="8A5A00")], anchor="ctr"))
        self._page(*sh)

    def kpis(self, title, kpis, subtitle=None, note=None, cols=None):
        """kpis: list of (值, 标签, 颜色)"""
        sh, y = self._header(title, subtitle)
        n = len(kpis)
        cols = cols or n
        rowsn = (n + cols - 1) // cols
        gap = 228600
        w = (self.W - 680000 - gap * (cols - 1)) // cols
        hbox = 1500000 if rowsn == 1 else 1280000
        for i, (val, lab, col) in enumerate(kpis):
            r, c = divmod(i, cols)
            x = 340000 + c * (w + gap)
            yy = y + 100000 + r * (hbox + 200000)
            sh.append(self.rect(x, yy, w, hbox, "F4F8FC", col))
            sh.append(self.rect(x, yy, w, 63500, col))
            sh.append(self.box(x + 45720, yy + 90000, w - 91440, hbox - 140000,
                               [dict(t=val, sz=(28 if rowsn == 1 else 23), b=True, color=col,
                                     align="ctr", space_after=5),
                                dict(t=lab, sz=(11.5 if rowsn == 1 else 10.5),
                                     color=S["GRAY"], align="ctr")], anchor="ctr"))
        if note:
            sh.append(self.rect(340000, self.H - 820000, self.W - 680000, 560000, S["WARN"], S["GOLD"]))
            sh.append(self.box(440000, self.H - 790000, self.W - 880000, 500000,
                               [dict(t=note, sz=12, color="8A5A00")], anchor="ctr"))
        self._page(*sh)

    def two_col(self, title, left_title, left_items, right_title, right_items,
                subtitle=None, note=None, accent_l=S["NAVY"], accent_r=S["GREEN"]):
        sh, y = self._header(title, subtitle)
        w = (self.W - 680000 - 260000) // 2
        for k, (tt, items, ac, x) in enumerate([
                (left_title, left_items, accent_l, 340000),
                (right_title, right_items, accent_r, 340000 + w + 260000)]):
            sh.append(self.rect(x, y + 60000, w, 420000, ac))
            sh.append(self.box(x + 120000, y + 90000, w - 240000, 380000,
                               [dict(t=tt, sz=14, b=True, color=S["WHITE"])], anchor="ctr"))
            paras = []
            for it in items:
                txt, lvl = it if isinstance(it, tuple) else (it, 0)
                paras.append(dict(t=txt, sz=(12.5 if lvl == 0 else 11),
                                  color=(S["TXT"] if lvl == 0 else S["GRAY"]),
                                  bullet=(lvl == 0), space_after=(7 if lvl else 2),
                                  space_before=(5 if lvl else 0)))
            sh.append(self.box(x + 60000, y + 560000, w - 120000,
                               self.H - y - (900000 if note else 500000), paras, anchor="t"))
        if note:
            sh.append(self.rect(340000, self.H - 800000, self.W - 680000, 540000, S["WARN"], S["GOLD"]))
            sh.append(self.box(440000, self.H - 770000, self.W - 880000, 480000,
                               [dict(t=note, sz=12, color="8A5A00")], anchor="ctr"))
        self._page(*sh)

    def end(self, main, subs):
        sh = [self.rect(0, 0, self.W, self.H, S["NAVY"]),
              self.rect(0, int(self.H * .28), self.W, 63500, S["GOLD"]),
              self.box(800000, int(self.H * .34), self.W - 1600000, 1200000,
                       [dict(t=main, sz=36, b=True, color=S["WHITE"], align="ctr")], anchor="ctr"),
              self.box(1200000, int(self.H * .54), self.W - 2400000, 1400000,
                       [dict(t=s, sz=14.5, color=S["SUB"], align="ctr", space_after=9) for s in subs],
                       anchor="t")]
        self._page(*sh)

    # ---------- 生成完整 slide XML ----------
    def xmls(self):
        head = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
                'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
                '<p:cSld><p:spTree>'
                '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
                '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')
        tail = ('</p:spTree></p:cSld>'
                '<p:clrMapOvr><a:overrideClrMapping bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" '
                'accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" '
                'accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
                '</p:clrMapOvr></p:sld>')
        return [head + p + tail for p in self.parts]
