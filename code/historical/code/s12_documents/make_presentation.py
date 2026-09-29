# -*- coding: utf-8 -*-
"""
生成组会汇报 PPT（严谨科学风，含 +1 特异性结果与两篇文献借鉴）
用法：uv run --with python-pptx python make_presentation.py
产出：可突变性与突变方向分析_组会汇报.pptx
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn

NAVY = RGBColor(0x1F, 0x3B, 0x66)
BLUE = RGBColor(0x2E, 0x54, 0x8B)
ACCENT = RGBColor(0xB4, 0x4A, 0x3C)
TEAL = RGBColor(0x1B, 0x6B, 0x5A)
GRAY = RGBColor(0x40, 0x40, 0x40)
LIGHT = RGBColor(0xF2, 0xF4, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "微软雅黑"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def set_font(run, size=16, bold=False, color=GRAY, name=FONT):
    run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = color; run.font.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
    ea.set('typeface', name)


def add_slide():
    return prs.slides.add_slide(BLANK)


def add_title(slide, text, size=26):
    box = slide.shapes.add_textbox(Inches(0.55), Inches(0.3), Inches(12.2), Inches(0.8))
    tf = box.text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run(); r.text = text; set_font(r, size, True, NAVY)
    line = slide.shapes.add_shape(1, Inches(0.58), Inches(1.02), Inches(3.2), Pt(2.2))
    line.fill.solid(); line.fill.fore_color.rgb = BLUE; line.line.fill.background()


def add_bullets(slide, items, left=0.7, top=1.3, width=12.0, height=5.9, size=16):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame; tf.word_wrap = True
    for i, (txt, lvl, bold, color) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = lvl; p.space_after = Pt(8)
        r = p.add_run(); r.text = ("• " if lvl == 0 else "– ") + txt
        set_font(r, size if lvl == 0 else size - 2, bold, color)
    return box


def add_table(slide, headers, rows, left=0.7, top=1.4, width=12.0, col_w=None, size=12):
    n = len(headers)
    shp = slide.shapes.add_table(len(rows) + 1, n, Inches(left), Inches(top), Inches(width), Inches(0.5 + 0.42 * len(rows)))
    tbl = shp.table
    if col_w:
        for i, w in enumerate(col_w):
            tbl.columns[i].width = Inches(w)
    for j, h in enumerate(headers):
        c = tbl.cell(0, j); c.text = h; c.fill.solid(); c.fill.fore_color.rgb = NAVY
        for p in c.text_frame.paragraphs:
            for r in p.runs:
                set_font(r, size, True, WHITE)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = tbl.cell(i + 1, j); c.text = str(v); c.fill.solid(); c.fill.fore_color.rgb = LIGHT if i % 2 == 0 else WHITE
            for p in c.text_frame.paragraphs:
                for r in p.runs:
                    set_font(r, size, False, GRAY)
    return tbl


def page_num(slide, n):
    box = slide.shapes.add_textbox(Inches(12.6), Inches(7.05), Inches(0.6), Inches(0.35))
    p = box.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT
    r = p.add_run(); r.text = str(n); set_font(r, 10, False, GRAY)


# ===================== 1 标题 =====================
s = add_slide()
box = s.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.4), Inches(1.8))
tf = box.text_frame; tf.word_wrap = True
r = tf.paragraphs[0].add_run(); r.text = "可突变残基的「突变方向」分析及文献借鉴"
set_font(r, 32, True, NAVY)
p2 = tf.add_paragraph(); r = p2.add_run()
r.text = "APOBEC（Pro.hA1）+1 位「保G排A」优化 · 接触类型 × 保守性/共进化 × PSSM × 湿实验验证"
set_font(r, 15, False, BLUE)
b2 = s.shapes.add_textbox(Inches(1.0), Inches(4.7), Inches(8.0), Inches(0.8))
r = b2.text_frame.paragraphs[0].add_run(); r.text = "组会汇报"
set_font(r, 14, False, GRAY)

# ===================== 2 背景 =====================
s = add_slide(); add_title(s, "研究背景与目标")
add_bullets(s, [
    ("目标：优化 REWIRE 系统中 APOBEC，特异性编辑 GCG（c.388）而非 GCA（c.871），降低脱靶", 0, False, GRAY),
    ("编辑 C 为 0 位；靶位 GUGCGCG（+1=G）与脱靶 AUGCAGC（+1=A）核心差异在 +1 位", 0, False, GRAY),
    ("前期：300 个 AF3 结构接触分析 + 102 个单点饱和突变（湿实验）", 0, False, GRAY),
    ("关键瓶颈：单点 +1 比（GCG/GCA）天花板 = 1.71，未达 2.0 目标 → 需组合突变", 0, True, ACCENT),
])
page_num(s, 2)

# ===================== 3 先前 +1 特异性结果 =====================
s = add_slide(); add_title(s, "先前研究：+1 位特异性结果")
add_table(s, ["维度", "关键结果"],
          [["+1 识别机制", "K30 侧链读 +1 碱基（侧链-碱基 64%）；H29 主链读（主链 94%）"],
           ["+1=A 的脱靶态", "碱基摆向催化核心 H70/E72/W99，T31 形成 A 特异氢键"],
           ["实验单点 +1 比", "K30H 1.71（最佳）、25E 1.55、G27D 1.53、58M 1.46、G27T 1.45"],
           ["瓶颈", "单点天花板 1.71 < 2.0，需组合不同判别轴（+1/−1/+2）"]],
          col_w=[3.2, 8.8], size=13)
page_num(s, 3)

# ===================== 4 本阶段问题 =====================
s = add_slide(); add_title(s, "本阶段三个科学问题")
add_bullets(s, [
    ("① 接触的性质：侧链还是主链？碱基还是糖/磷酸？—— 决定接触是否「可设计」", 0, True, NAVY),
    ("② 可突变性：哪些位点能突变？—— 保守性 + 共进化（解释 31/57 不可动）", 0, True, NAVY),
    ("③ 突变方向：可突变前提下，朝哪些氨基酸方向可变、哪些会失活？—— PSSM", 0, True, NAVY),
])
page_num(s, 4)

# ===================== 5 方法 =====================
s = add_slide(); add_title(s, "方法与数据")
add_table(s, ["分析", "数据/工具", "回答的问题"],
          [["接触类型分解", "300 个 AF3 原始结构", "侧链/主链 × 碱基/糖磷酸"],
           ["可突变性", "AF3 返回 MSA（约 3500 同源）", "保守性 + 共进化（MI）"],
           ["突变方向", "同 MSA 位点氨基酸分布（PSSM）", "允许/禁止方向"],
           ["湿实验验证", "102 个单点饱和突变", "检验 PSSM 可信度"]],
          col_w=[3.0, 5.5, 3.5], size=13)
page_num(s, 5)

# ===================== 6 结果1 接触类型 =====================
s = add_slide(); add_title(s, "结果一：接触类型分解（A-swap）")
add_table(s, ["残基", "侧链-碱基", "主链-碱基", "接触性质"],
          [["H29", "0.05", "0.94", "主链读碱基（结构性）"],
           ["K30", "0.64", "1.00", "侧链+主链混合"],
           ["T31", "1.00", "1.00", "侧链-碱基特异"],
           ["N57/H70/E72/W99", "0.9–1.0", "低", "纯侧链特异（催化核心）"]],
          col_w=[3.5, 2.2, 2.2, 4.1], size=13)
box = s.shapes.add_textbox(Inches(0.7), Inches(4.7), Inches(12.0), Inches(1.0))
r = box.text_frame.paragraphs[0].add_run()
r.text = "结论：H29 读碱基靠主链（侧链仅 5%）；催化核心是纯侧链-碱基特异接触。"
set_font(r, 14, True, ACCENT)
page_num(s, 6)

# ===================== 7 结果2 可突变性 =====================
s = add_slide(); add_title(s, "结果二：可突变性（保守性 + 共进化）")
add_table(s, ["分级", "残基（野生型频率）"],
          [["不可动（>90%）", "H70(97%) E72(95%) C102/C105(100%) S98(91%)"],
           ["慎动（70–90%）", "G27(82%) R28(84%) T31(82%) W99(74%)"],
           ["可突变（<70%）", "H29(22%) K30(36%) Q58(29%) M132(5%)…"],
           ["仅特定替换", "N57（67%，共进化 MI=0.30 最高）"]],
          col_w=[3.0, 9.0], size=13)
box = s.shapes.add_textbox(Inches(0.7), Inches(5.0), Inches(12.0), Inches(1.0))
r = box.text_frame.paragraphs[0].add_run()
r.text = "结论：T31 高保守不可动；N57 与活性中心共进化程度最高，故不可动。"
set_font(r, 14, True, ACCENT)
page_num(s, 7)

# ===================== 8 结果3 PSSM =====================
s = add_slide(); add_title(s, "结果三：PSSM 突变方向（T31 案例）")
add_table(s, ["T31 家族分布", "T82%  S6%  V6%  C3%  A2%（其余 <1%）", ""],
          [["突变", "家族频率", "实验 GCG"],
           ["T31A（Ala）", "2%", "0.50（活性）"],
           ["T31C（Cys）", "3%", "0.51（活性）"],
           ["T31D（Asp）", "0%", "0.00（失活）"],
           ["T31G（Gly）", "<1%", "0.07（大部分失活）"],
           ["T31Y（Tyr）", "0%", "0.00（失活）"]],
          col_w=[5.0, 3.5, 3.5], size=12)
box = s.shapes.add_textbox(Inches(0.7), Inches(5.5), Inches(12.0), Inches(1.0))
r = box.text_frame.paragraphs[0].add_run()
r.text = "PSSM 的「允许/禁止」方向与实验失活模式完全吻合。"
set_font(r, 14, True, ACCENT)
page_num(s, 8)

# ===================== 9 结果4 验证 =====================
s = add_slide(); add_title(s, "结果四：PSSM 湿实验验证（102 突变）")
add_table(s, ["指标", "数值"], [["准确率", "52%"], ["精确率（禁止→失活）", "38%"], ["召回率", "68%"]],
          col_w=[4.0, 4.0], size=13, left=0.7, top=1.35)
add_table(s, ["位点类型", "准确率", "精确率(禁止→失活)", "召回率"],
          [["核心/口袋/出口", "65%", "71%", "65%"],
           ["loop1 暴露（25/26/27/28）", "38%", "9%", "100%"]],
          col_w=[6.2, 1.9, 2.1, 1.8], size=12, left=0.7, top=3.2)
box = s.shapes.add_textbox(Inches(0.7), Inches(5.9), Inches(12.0), Inches(1.0))
r = box.text_frame.paragraphs[0].add_run()
r.text = "PSSM 对核心位点有效（71%）、对溶剂暴露 loop 位点失效（9%）。"
set_font(r, 14, True, ACCENT)
page_num(s, 9)

# ===================== 10 讨论 解决 =====================
s = add_slide(); add_title(s, "讨论：解决了哪些问题")
add_bullets(s, [
    ("区分了接触可设计性：侧链-碱基特异 = 可设计；主链接触 = 结构性（如 H29）", 0, False, GRAY),
    ("解释「哪些位点不可动」：T31 高保守；N57 与活性中心共进化；H70/E72/C102/C105/S98 >90% 保守", 0, False, GRAY),
    ("建立「突变方向」框架：PSSM 给出允许/禁止方向，解释 T31→D/Y/G 失活、→A/C 活性", 0, False, GRAY),
    ("量化 PSSM 适用边界：核心位点 71%、loop 位点 9%", 0, False, GRAY),
])
page_num(s, 10)

# ===================== 11 讨论 未解决 =====================
s = add_slide(); add_title(s, "讨论：尚未解决的问题")
add_bullets(s, [
    ("溶剂暴露位点失效：loop1 精确率仅 9%，分子暴露度高、受实验环境影响大", 0, True, ACCENT),
    ("M132 悖论：同源高度可变（5%）但实验全系列不理想——位于出口通道（距 +1 碱基 15–20 Å），只影响整体活性、无法做 +1 特异性", 0, True, ACCENT),
    ("PSSM 整体不可靠（52%）：失活由「电荷/大芳香/无侧链 vs 环境」的物化失配决定，而非进化频率", 0, False, GRAY),
    ("本框架只验证「活性/失活」，尚未纳入「+1 特异性」这一正交维度", 0, False, GRAY),
])
page_num(s, 11)

# ===================== 12 文献1 Wang 2021 =====================
s = add_slide(); add_title(s, "文献借鉴一：Wang et al. 2021（Nat Commun）")
box = s.shapes.add_textbox(Inches(0.7), Inches(1.25), Inches(12.0), Inches(0.5))
r = box.text_frame.paragraphs[0].add_run()
r.text = "A general theoretical framework to design base editors with reduced bystander effects"
set_font(r, 13, False, BLUE)
add_bullets(s, [
    ("核心：选择性由突变引起的结合自由能变化 ΔΔE_m 决定，且对 ΔΔE_m 呈非单调依赖（最优 ~4–6 kBT）", 0, True, NAVY),
    ("ΔΔE_m 太小 → 不特异；太大 → 目标+脱靶双阻断（失活）", 1, False, GRAY),
    ("解释了为什么 N57/T31 多数突变失活：ΔΔE_m 过大进入「双阻」失活区", 0, True, ACCENT),
    ("对 REWIRE 的启示：保G排A = 适度削弱 +1=A 脱靶结合，而非把脱靶结合打到 0", 0, False, GRAY),
], top=1.8)
page_num(s, 12)

# ===================== 13 文献2 Song 2026 Cell =====================
s = add_slide(); add_title(s, "文献借鉴二：Song et al. 2026（Cell, LEAPER 3.0）")
box = s.shapes.add_textbox(Inches(0.7), Inches(1.25), Inches(12.0), Inches(0.5))
r = box.text_frame.paragraphs[0].add_run()
r.text = "RNA structure programs endogenous ADAR for precise and efficient editing（魏文胜组）"
set_font(r, 13, False, BLUE)
add_bullets(s, [
    ("方法与我们高度一致：AF3 结构预测 + 数千模型统计（作者因单次预测不稳定而采用统计）", 0, True, TEAL),
    ("核心发现：ADAR 结合界面分区（催化/DRBM/外围），A-U 与 A-C 对结构扰动的敏感性不同", 0, False, GRAY),
    ("策略：在 DRBM 区放置 bulge 选择性抑制 A-U 脱靶、保留 A-C on-target → 单核苷酸精度", 0, True, ACCENT),
    ("启示：通过「适度结构扰动」选择性削弱脱靶，与我们的「适度调制结合」异曲同工", 0, False, GRAY),
], top=1.8)
page_num(s, 13)

# ===================== 14 文献启示 =====================
s = add_slide(); add_title(s, "两篇文献对我们的借鉴")
add_table(s, ["文献", "核心思想", "对应到我们的工作"],
          [["Wang 2021", "ΔΔE_m 非单调；适度削弱脱靶结合", "K30H 等通过调制结合实现 +1 判别"],
           ["Song 2026", "结构扰动选择性削弱 A-U 脱靶", "我们的「接触分解」定位可扰动区域"],
           ["共同原则", "特异性靠「削弱脱靶」而非「增强 on-target」", "组合应聚焦中度削弱 +1=A 结合"]],
          col_w=[2.6, 5.2, 4.2], size=12.5)
box = s.shapes.add_textbox(Inches(0.7), Inches(4.6), Inches(12.0), Inches(1.2))
r = box.text_frame.paragraphs[0].add_run()
r.text = "方法学验证：Song 2026 与我们一样采用「AF3 + 多模型统计」，佐证了我们 300 结构统计分析的合理性。"
set_font(r, 14, True, TEAL)
page_num(s, 14)

# ===================== 15 下一步 =====================
s = add_slide(); add_title(s, "下一步方向")
add_bullets(s, [
    ("主线（最高优先级）：组合已验证单点，打不同判别轴", 0, True, NAVY),
    ("     K30H（+1） × G27D/G27T（−1） × Y32F（+2） × Q58M（+1 次级）", 1, False, GRAY),
    ("借鉴文献：组合设计应遵循「适度削弱脱靶」原则，避免过度削弱（ΔΔE_m 过大→失活）", 0, False, BLUE),
    ("辅助：DCA 共进化找与 K30 耦合、可突变的第二壳层位点", 0, False, BLUE),
    ("长期：定向进化 / 深度突变扫描，突破单点 1.71 与理性设计 ~2.0 天花板", 0, False, BLUE),
])
page_num(s, 15)

# ===================== 16 总结 =====================
s = add_slide(); add_title(s, "总结")
add_bullets(s, [
    ("建立「可突变性 → 突变方向」量化流程：接触分解 → 保守性/共进化 → PSSM → 湿实验验证", 0, False, GRAY),
    ("PSSM 对核心位点有效（71%）、对溶剂暴露位点失效（9%），整体准确率 52%", 0, False, GRAY),
    ("失活的真实原因是「物化性质 vs 环境失配」，应以物化+结构 clash 分析取代进化频率", 0, False, GRAY),
    ("文献共识：特异性靠「适度削弱脱靶」而非「增强 on-target」——组合设计遵循此原则", 0, True, NAVY),
], size=16)
box = s.shapes.add_textbox(Inches(0.7), Inches(6.0), Inches(12.0), Inches(0.8))
p = box.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = "谢谢！欢迎讨论"
set_font(r, 20, True, NAVY)
page_num(s, 16)

prs.save("可突变性与突变方向分析_组会汇报_含文献.pptx")
print("已生成：可突变性与突变方向分析_组会汇报_含文献.pptx  （16 页）")
