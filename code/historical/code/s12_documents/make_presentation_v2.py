# -*- coding: utf-8 -*-
"""
生成组会汇报 PPT（第二期）
—— 承接上期《APOBEC保G排A优化_组会汇报.pptx》：
    上期提出 P1-1（Δd_E72 回归）与 P1-2（三点复合物结构解析）→ 本期汇报执行结果
—— 以《导师汇报_APOBEC_保G排A优化_研究总结.docx》的研究思路为主线骨架
—— 突出「干实验预测 ⇄ 湿实验验证」的双向指导

用法：uv run --with python-pptx python make_presentation_v2.py
产出：APOBEC保G排A优化_组会汇报_第二期.pptx
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

NAVY = RGBColor(0x1F, 0x3B, 0x66)
BLUE = RGBColor(0x2E, 0x54, 0x8B)
ACCENT = RGBColor(0xB4, 0x4A, 0x3C)
TEAL = RGBColor(0x1B, 0x6B, 0x5A)
GRAY = RGBColor(0x40, 0x40, 0x40)
LIGHT = RGBColor(0xF2, 0xF4, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x1E, 0x7A, 0x46)
FONT = "微软雅黑"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def set_font(run, size=16, bold=False, color=GRAY, name=FONT):
    run.font.size = Pt(size); run.font.bold = bold
    run.font.color.rgb = color; run.font.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
    ea.set('typeface', name)


def add_slide():
    return prs.slides.add_slide(BLANK)


def add_title(slide, text, size=26):
    box = slide.shapes.add_textbox(Inches(0.55), Inches(0.28), Inches(12.2), Inches(0.8))
    tf = box.text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run(); r.text = text; set_font(r, size, True, NAVY)
    line = slide.shapes.add_shape(1, Inches(0.58), Inches(1.0), Inches(3.2), Pt(2.2))
    line.fill.solid(); line.fill.fore_color.rgb = BLUE; line.line.fill.background()


def add_sub(slide, text, top=1.06, size=12, color=BLUE):
    box = slide.shapes.add_textbox(Inches(0.6), Inches(top), Inches(12.2), Inches(0.4))
    tf = box.text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run(); r.text = text; set_font(r, size, False, color)


def add_bullets(slide, items, left=0.7, top=1.35, width=12.0, height=5.8, size=15):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame; tf.word_wrap = True
    for i, (txt, lvl, bold, color) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = lvl; p.space_after = Pt(7)
        r = p.add_run(); r.text = ("• " if lvl == 0 else "– ") + txt
        set_font(r, size if lvl == 0 else size - 2, bold, color)
    return box


def add_table(slide, headers, rows, left=0.7, top=1.5, width=12.0, col_w=None,
              size=11, hdr_size=None, row_h=0.32):
    n_r, n_c = len(rows) + 1, len(headers)
    shape = slide.shapes.add_table(n_r, n_c, Inches(left), Inches(top),
                                   Inches(width), Inches(row_h * n_r))
    tbl = shape.table
    if col_w:
        total = sum(col_w)
        for i, w in enumerate(col_w):
            tbl.columns[i].width = Inches(width * w / total)
    for j, h in enumerate(headers):
        c = tbl.cell(0, j); c.text = ""
        c.fill.solid(); c.fill.fore_color.rgb = NAVY
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = str(h)
        set_font(r, hdr_size or size, True, WHITE)
    for i, row in enumerate(rows, start=1):
        for j, v in enumerate(row):
            c = tbl.cell(i, j); c.text = ""
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            if i % 2 == 0:
                c.fill.solid(); c.fill.fore_color.rgb = LIGHT
            p = c.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
            r = p.add_run(); r.text = str(v)
            col = GRAY
            s = str(v)
            if any(k in s for k in ("✓", "安全", "完好", "阳性")):
                col = GREEN
            if any(k in s for k in ("✗", "⚠", "阴性", "失效", "崩", "失活")):
                col = ACCENT
            set_font(r, size, False, col)
    return tbl


def add_kpi(slide, items, top=1.6, height=1.5):
    """大数字卡片：[ (数字, 标签, 颜色), ... ]"""
    n = len(items); gap = 0.3
    w = (12.0 - gap * (n - 1)) / n
    for i, (num, lab, col) in enumerate(items):
        left = 0.7 + i * (w + gap)
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top),
                                     Inches(w), Inches(height))
        box.fill.solid(); box.fill.fore_color.rgb = WHITE
        box.line.color.rgb = col; box.line.width = Pt(1.5)
        tf = box.text_frame; tf.word_wrap = True
        tf.margin_top = Pt(8)
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = num; set_font(r, 30, True, col)
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = lab; set_font(r2, 12, False, GRAY)


def add_note(slide, text, top=6.85, color=ACCENT, size=11.5):
    box = slide.shapes.add_textbox(Inches(0.7), Inches(top), Inches(12.0), Inches(0.45))
    tf = box.text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run(); r.text = text
    set_font(r, size, True, color)


def add_section(num, title, subtitle):
    s = add_slide()
    band = s.shapes.add_shape(1, Inches(0), Inches(2.5), prs.slide_width, Inches(2.2))
    band.fill.solid(); band.fill.fore_color.rgb = NAVY; band.line.fill.background()
    box = s.shapes.add_textbox(Inches(1.0), Inches(2.7), Inches(11.0), Inches(1.8))
    tf = box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; r = p.add_run(); r.text = num
    set_font(r, 40, True, RGBColor(0x8F, 0xB4, 0xDE))
    p2 = tf.add_paragraph(); r2 = p2.add_run(); r2.text = title
    set_font(r2, 30, True, WHITE)
    p3 = tf.add_paragraph(); r3 = p3.add_run(); r3.text = subtitle
    set_font(r3, 14, False, RGBColor(0xC8, 0xD6, 0xE8))
    return s


# =====================================================================
# 封面
# =====================================================================
s = add_slide()
bar = s.shapes.add_shape(1, Inches(0), Inches(0), prs.slide_width, Inches(0.35))
bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
box = s.shapes.add_textbox(Inches(0.9), Inches(1.9), Inches(11.5), Inches(3.0))
tf = box.text_frame; tf.word_wrap = True
r = tf.paragraphs[0].add_run(); r.text = "APOBEC「保 G 排 A」优化 · 第二期"
set_font(r, 40, True, NAVY)
p = tf.add_paragraph(); r = p.add_run()
r.text = "从「提出计划」到「验证结论」：P1-1 Δd_E72 回归 + P1-2 三点复合物结构解析"
set_font(r, 19, False, ACCENT)
p = tf.add_paragraph(); r = p.add_run()
r.text = "干实验预测 ⇄ 湿实验验证 的双向迭代"
set_font(r, 16, False, TEAL)
box2 = s.shapes.add_textbox(Inches(0.9), Inches(5.3), Inches(11.5), Inches(1.6))
tf2 = box2.text_frame; tf2.word_wrap = True
for t, sz, c in [
    ("承接上期：共进化 MI × 空间耦合 × 实验保留率 三维证据整合（P1-1 / P1-2 计划）", 13, GRAY),
    ("本期新增：22 突变体 Δd_E72 全补齐与回归 · 27T-30H-58M / 27D-30H-58M 结构解析 · 132D 组合活性压制效应", 13, GRAY),
    ("数据：AF3 复合物 300 + 22 突变体 ×2 底物 ｜ 单点饱和 103 ｜ 组合 71 组 (n=2)", 12, BLUE),
    ("组会汇报 · 2026-09-11", 11, RGBColor(0x80, 0x80, 0x80)),
]:
    pp = tf2.add_paragraph() if tf2.paragraphs[0].runs else tf2.paragraphs[0]
    rr = pp.add_run(); rr.text = t; set_font(rr, sz, False, c)

# =====================================================================
# 衔接页
# =====================================================================
s = add_slide(); add_title(s, "上期回顾 → 本期定位")
add_table(s,
    ["上期（9/10）提出的问题", "本期（9/11）的执行与结论"],
    [["P1-1：Δd_E72 能否作为主筛指标？\n对全部 22 个突变体补齐 Δd_E72，与实测＋1比做回归。\n若 r>0.7 → 计算有效；若不成立 → 放弃计算筛选",
      "已完成：r = −0.073，95% CI [−0.600, +0.498]\n→ 阴性，不支持作为主筛指标\n但分层后发现关键机制差异（单点 +0.67 / 组合 −0.72）"],
     ["P1-2：给 27T-30H-58M 补结构解析\n测 Δd_E72、C4N4–E72、锌配位完整性",
      "已完成（模型原已存在）：\nC4N4–E72 呈单调退化梯度 2.88→4.5→6.5 Å\n锌配位完好（偏差<0.22 Å）→ 酶没坏，底物摆不到位"],
     ["上期遗留风险：组合特异性是否为活性衰减假象",
      "本期新增证据：132D 组合活性压制效应（单点保留89% vs 组合中位0.191）\n并外推至 30H / 27D 同类矛盾位点"]],
    top=1.5, col_w=[5, 7], size=12)

# =====================================================================
# 提纲
# =====================================================================
s = add_slide(); add_title(s, "本期汇报提纲")
add_bullets(s, [
    ("一、研究思路主线：三个正交问题 + 干湿双向闭环", 0, True, NAVY),
    ("二、干 → 湿：结构接触 / PSSM / CP 如何指导突变设计并被实验检验", 1, False, GRAY),
    ("三、湿 → 干：实验的三个「打脸」发现如何倒逼预测方法迭代", 1, False, GRAY),
    ("四、P1-1 执行：22 突变体 Δd_E72 回归（阴性结果 + 分层真相 + 噪声诊断）", 0, True, NAVY),
    ("五、P1-2 执行：三点复合物结构解析（催化几何梯度 + 锌配位完整性）", 0, True, NAVY),
    ("六、新增：132D 组合活性压制效应及其可推广性", 0, True, NAVY),
    ("七、综合结论与下一步（P0 剂量梯度仍为最高优先级）", 0, True, NAVY),
], top=1.45, size=15)

# =====================================================================
add_section("01", "研究思路主线", "三个正交问题 · 干湿双向闭环")

s = add_slide(); add_title(s, "研究思路：把一个大问题拆成三个可独立检验的正交问题")
add_table(s,
    ["正交问题", "回答手段", "核心结论"],
    [["Q1 谁接触 +1 碱基？\n（结构接触）",
      "AF3 复合物 → 距离/氢键/埋藏面积\n→ 升级为 ContactSeek 式 CP/ΔCP",
      "保G：H29/K30（读 +1=G）\n排A：催化核心 N57/H70/E72/W99/C102 + T31"],
     ["Q2 谁突变不失活？\n（进化/保守性）",
      "AF3 MSA(3504 同源) 保守性 + 共进化 MI\n+ PSSM 突变方向",
      "催化核心/锌配位绝对不可动\nK30/M132/H29/A59/Y32 可突变；T31 慎动"],
     ["Q3 谁真正做 G/A 判别？\n（只能靠湿实验）",
      "单点饱和 103 → 组合湿实验 71 组\n（EGFP + APOE 双报告，n=2）",
      "单点天花板 1.71；\n组合 27T-30H-58M 破 2.0（2.16）"]],
    top=1.5, col_w=[3.2, 4.4, 4.4], size=12)
add_note(s, "贯穿原则：结构只定位「谁参与」，保守性只回答「能不能动」，ML 只预测结合 ΔΔG —— 三者都不等于特异性，唯实验能定 Q3。", top=6.75, color=ACCENT)

s = add_slide(); add_title(s, "干湿双向闭环：预测与验证如何相互指导")
# 左框：干→湿
b1 = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(1.5), Inches(5.3), Inches(4.3))
b1.fill.solid(); b1.fill.fore_color.rgb = RGBColor(0xEC, 0xF2, 0xFA); b1.line.color.rgb = BLUE
tf = b1.text_frame; tf.word_wrap = True; tf.margin_left = Pt(14); tf.margin_top = Pt(10)
p = tf.paragraphs[0]; r = p.add_run(); r.text = "干 → 湿：预测指导实验"
set_font(r, 17, True, BLUE)
for t in ["结构接触 → 锁定 +1/−1 判别残基",
          "CP/ΔCP → 预测突变如何重塑判别网络",
          "保守性/共进化 → 排除必失活位点（T31 82%、N57 共进化最高）",
          "PSSM → 给出「允许/禁止」突变方向，避免无效实验",
          "组合位点对筛选 → 优先合成清单"]:
    pp = tf.add_paragraph(); pp.space_after = Pt(6)
    rr = pp.add_run(); rr.text = "• " + t; set_font(rr, 12.5, False, GRAY)
# 右框：湿→干
b2 = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.3), Inches(1.5), Inches(5.3), Inches(4.3))
b2.fill.solid(); b2.fill.fore_color.rgb = RGBColor(0xFB, 0xEF, 0xEC); b2.line.color.rgb = ACCENT
tf = b2.text_frame; tf.word_wrap = True; tf.margin_left = Pt(14); tf.margin_top = Pt(10)
p = tf.paragraphs[0]; r = p.add_run(); r.text = "湿 → 干：实验倒逼预测升级"
set_font(r, 17, True, ACCENT)
for t in ["单点天花板 1.71 → 迫使转向组合设计",
          "M132 悖论（同源5%可变却实验平庸）→ 揭穿「出口通道≠判别子」",
          "T31 结构接触强却实验无效 → 确立「接触≠功能」",
          "PremPRI 判反 M132E/D → 确立「ML 只做粗筛」",
          "132D 组合塌方 → 提出「单点保留≠组合安全」新判据"]:
    pp = tf.add_paragraph(); pp.space_after = Pt(6)
    rr = pp.add_run(); rr.text = "• " + t; set_font(rr, 12.5, False, GRAY)
# 中间双向箭头
ar = s.shapes.add_shape(MSO_SHAPE.LEFT_RIGHT_ARROW, Inches(6.05), Inches(3.0), Inches(1.2), Inches(0.9))
ar.fill.solid(); ar.fill.fore_color.rgb = TEAL; ar.line.fill.background()
add_note(s, "方法学主张：干实验的价值不在「算得准」，而在缩小搜索空间并给出可证伪的机制假设；湿实验的价值不只是筛选，更在于暴露预测体系的失效边界。", top=6.15, color=TEAL)

# =====================================================================
add_section("02", "干 → 湿", "预测如何被湿实验检验")

s = add_slide(); add_title(s, "干→湿 ①：结构/ML 预测的单点设计，被 103 个湿实验单点检验")
add_table(s,
    ["突变", "＋1比", "保留", "预测来源", "验证结果"],
    [["K30H", "1.71", "84%", "接触+1碱基 + 可突变", "✓ 证实（最佳单点）"],
     ["G25E", "1.55", "89%", "loop1 探针（此前低估）", "✓ 证实"],
     ["G27D", "1.53", "88%", "−1 位特化，压 ACA", "✓ 证实"],
     ["Q58M", "1.46", "79%", "loop3（此前被排除）", "✓ 证实（实为排A）"],
     ["G27T", "1.45", "98%", "−1 位特化，高保留", "✓ 证实"],
     ["M132D", "1.42", "89%", "出口排A（mCSM/PremPRI）", "✓ 证实（但增益有限）"],
     ["M132E", "1.18", "83%", "PremPRI 保G最优", "✗ 证伪（D≫E，判反）"],
     ["T31A", "1.32", "97%", "「T31 排A」氢键假说", "✗ 假说撤回（接触≠功能）"],
     ["A59S", "1.33", "74%", "PremPRI 高判别", "✗ 高估"]],
    top=1.55, col_w=[1.5, 1.2, 1.2, 4.2, 3.5], size=11.5)
add_note(s, "命中率观察：结构接触类预测（K30H/G27D/T）可靠；ML 的 ΔΔG 类预测在 D/E、判别强度上反复失真。", top=6.9)

s = add_slide(); add_title(s, "干→湿 ②：PSSM 突变方向预测 —— 核心位点有效，溶剂暴露位点失效")
add_table(s,
    ["T31 突变", "家族频率 (PSSM)", "实验 GCG", "判定"],
    [["T31A", "2%", "0.50", "✓ 活性"],
     ["T31C", "3%", "0.51", "✓ 活性"],
     ["T31V", "6%", "—（未测）", "预测活性"],
     ["T31S", "6%", "—（未测）", "预测活性"],
     ["T31D", "0%", "0.00", "✓ 预测失活（静电排斥磷酸骨架）"],
     ["T31G", "<1%", "0.07", "✓ 预测失活（失去侧链）"],
     ["T31Y", "0%", "0.00", "✓ 预测失活（空间位阻）"]],
    top=1.55, col_w=[2.0, 3.0, 3.0, 4.0], size=11.5)
add_kpi(s, [("71%", "核心位点 PSSM 准确率", GREEN),
            ("9%", "溶剂暴露 loop 位点", ACCENT),
            ("52%", "整体准确率", GRAY)], top=4.9, height=1.35)
add_note(s, "结论：失活的真实机制是「物化性质 vs 环境失配」（电荷/大芳香/无侧链），进化频率只是代理指标。", top=6.55)

s = add_slide(); add_title(s, "干→湿 ③：CP/ΔCP 突变体重测 —— 用结构验证「设计是否真的改变了判别网络」")
add_table(s,
    ["突变", "保G指数\n(H29+K30 ΔCP)", "排A指数\n(催化核心)", "结构判读", "实验对照"],
    [["WT", "−0.33", "+0.24", "基准", "1.37"],
     ["K30H", "−0.30", "+0.27", "H29 保G增强(−0.41→−0.51)；K30 自身弱化", "1.71 (84%)"],
     ["Q58M", "−0.37", "+0.28", "K30 保G独立增强(−0.24→−0.28)", "1.46 (79%)"],
     ["R28A（未测）", "−0.40", "+0.31", "双向增强：H29 与催化核心均更强", "待验证"],
     ["T31V→I→L", "−0.26→+0.06", "≈+0.26", "大侧链变构压塌 H29/K30（保G指数归零）", "预测 I/L 显著降活"],
     ["27T-30H-58M", "0.00", "+0.27", "保G崩塌但排A保持 → 高判别机制", "2.16"]],
    top=1.55, col_w=[2.3, 2.4, 2.0, 5.0, 1.9], size=11)
add_note(s, "批间一致性校验：同目录 wt 重跑与旧 100-model WT 高度一致（保G指数 −0.325 vs −0.328）→ 该指标可重复。", top=6.75)

# =====================================================================
add_section("03", "湿 → 干", "实验的三个「打脸」发现如何倒逼预测迭代")

s = add_slide(); add_title(s, "湿→干：三个关键「打脸」发现")
add_table(s,
    ["实验发现", "被否定的干预测", "倒逼出的新认知"],
    [["单点天花板 1.71\n（103 个单点无一破 2.0）",
      "「找到最强单点即可达标」",
      "单个位点只能强化三层机制中的一层 → 单点存在结构性上限，必须组合"],
     ["M132 悖论\n（同源 5% 可变、ML 高分，实验平庸 1.42/1.18）",
      "mCSM-NA/PremPRI 的 ΔΔG 高分 = 高价值候选",
      "M132 位于出口通道、距 +1 碱基 15–20 Å，只影响活性不影响特异性\n→ ML 预测的是结合强度，不是特异性"],
     ["T31 悖论\n（结构上唯一「仅对 A」的侧链氢键，实验 1.32 无改善）",
      "「结构接触 = 可设计靶点」",
      "接触≠功能：该氢键不驱动 A 编辑\n→ 结构证据必须叠加功能验证"],
     ["加性先验模型失效\n（30+58 理论 0.81 第1，实测 1.69/78%）",
      "「MI + 距离 + 单点效应」线性可加",
      "组合存在显著上位效应 → 线性模型不可外推（本期 P1-1 再次确认）"]],
    top=1.5, col_w=[3.6, 3.6, 4.8], size=11)

s = add_slide(); add_title(s, "★ 本期重点：132D 矛盾 —— 单点保留 89%，组合却系统性压制活性")
add_table(s,
    ["层级", "C388 中位", "C388>0.3 占比", "全失活比例"],
    [["单点 132D", "0.89（保留率）", "—", "—"],
     ["含 132D 的组合 (n=13)", "0.191", "0%", "12%"],
     ["含 132E 的组合 (n=9)", "0.346", "56%", "0%"],
     ["不含 132 的组合 (n≈30)", "0.295", "47%", "7%"]],
    top=1.55, col_w=[4.0, 2.6, 2.8, 2.6], size=12)
add_sub(s, "受控对比（固定其余位点，仅切换 132）—— 排除混淆因素后的关键证据", top=4.6)
add_table(s,
    ["背景", "不含 132", "+132D", "+132E"],
    [["27T + 32F", "0.403", "0.249", "0.485"],
     ["27D + 32F", "0.289", "0.172", "—"],
     ["30H + 32F", "0.153", "0.000", "0.153"]],
    top=5.05, col_w=[3.0, 3.0, 3.0, 3.0], size=11.5, row_h=0.3)
add_note(s, "机制：132D 把 Asp 负电荷引入出口通道，单点时构象余量足够可容忍；组合时其他突变已压缩余量，再叠加即越过活性阈值。132E 侧链更长更柔 → 组合安全。", top=6.85, size=10.5)

s = add_slide(); add_title(s, "矛盾可否推广？—— 可以，判据是「侧链物化类型」而非「单点保留率」")
add_table(s,
    ["位点", "单点保留", "含该位点组合 C388 中位", "组合 >0.3 占比", "判定"],
    [["132D", "0.89", "0.191", "0%", "⚠ 典型矛盾"],
     ["30H", "0.84", "0.153", "15%", "⚠ 更严重"],
     ["27D", "0.88", "0.263", "18%", "⚠ 中度矛盾"],
     ["27T", "0.98", "0.295", "46%", "组合安全"],
     ["25E", "0.89", "0.302", "50%", "组合安全"],
     ["58M", "0.79", "0.476", "80%", "组合安全"],
     ["132E", "0.83", "0.346", "56%", "组合安全"]],
    top=1.5, col_w=[2.0, 2.2, 3.6, 2.6, 2.6], size=11.5)
add_note(s, "规律：出问题的都是「带电/刚性侧链替换」(D/H)；安全的是「疏水/柔性/保守替换」(T/E/M)。→ 候选突变进组合前，先看物化类型，再信单点保留率。", top=6.75)

# =====================================================================
add_section("04", "P1-1 执行", "22 突变体 Δd_E72 回归：阴性结果与分层真相")

s = add_slide(); add_title(s, "P1-1 方法：Δd_E72 的定义与全部 22 个突变体（节选）")
add_sub(s, "Δd_E72 = d_E72(GCA) − d_E72(GCG)；d_E72 = 靶点 C(0位, RNA res4) 的脱氨原子 C4/N4 到催化 E72 羧基的最小距离", top=1.12)
add_table(s,
    ["突变", "d_GCG(Å)", "d_GCA(Å)", "Δd_E72(Å)", "实测＋1比"],
    [["WT", "2.88", "6.33", "3.45", "1.37"],
     ["K30H", "2.78", "7.13", "4.35", "1.71"],
     ["K30H+Q58M", "2.68", "7.64", "4.96", "1.69*"],
     ["M132E", "2.84", "4.76", "1.92", "1.18"],
     ["M132D", "3.01", "5.05", "2.04", "1.42"],
     ["27T", "3.10", "6.55", "3.45", "1.45"],
     ["27D", "3.18", "6.59", "3.41", "1.53"],
     ["G25E", "2.86", "5.20", "2.34", "1.55"],
     ["Q58M", "2.56", "5.53", "2.97", "1.46"],
     ["Y32F", "3.00", "5.86", "2.86", "1.47"],
     ["★27T-30H-58M", "6.51", "8.34", "1.83", "2.16"],
     ["★27D-30H-58M", "5.05", "6.56", "1.50", "—"]],
    top=1.75, col_w=[2.8, 2.0, 2.0, 2.2, 2.2], size=10.5, row_h=0.3)
add_note(s, "*K30H+Q58M 取 30H-58M 实测。22 个突变体已全部补齐并写入 results/dE72_regression.csv。", top=6.95, size=10.5)

s = add_slide(); add_title(s, "P1-1 结果：回归为阴性（r ≈ 0）")
add_kpi(s, [("r = −0.073", "Pearson 相关系数", ACCENT),
            ("[−0.600, +0.498]", "95% 置信区间（横跨 0）", ACCENT),
            ("ρ = −0.044", "Spearman 秩相关", GRAY),
            ("n = 13", "有实测值的突变体", BLUE)], top=1.5, height=1.5)
add_bullets(s, [
    ("拟合式：＋1比 = −0.0246 × Δd_E72 + 1.717", 0, True, NAVY),
    ("留一交叉验证 RMSE = 0.38，预测残差均值 −0.01 → 无系统偏差，但也无预测力", 1, False, GRAY),
    ("按上期设定的判据（r > 0.7 才采用）→ Δd_E72 不能作为组合筛选的主指标", 0, True, ACCENT),
], top=3.35, size=14)
add_note(s, "但「r≈0」不等于「几何无关」—— 必须做噪声诊断与分层，才能判断是真无关还是被测量误差淹没。", top=5.6, color=TEAL)

s = add_slide(); add_title(s, "P1-1 分层真相：单点与组合走的是两套完全不同的机制")
add_table(s,
    ["分层", "n", "r", "机制解读"],
    [["全部", "13", "−0.073", "混合两类机制 → 相互抵消，表面无相关"],
     ["仅单点突变", "9", "+0.670", "单点靠「选择性几何位移」：+1=A 时靶点C 被推离催化中心越远，特异性越高"],
     ["仅组合突变", "4", "−0.724", "组合靠「整体催化几何下调」：GCG 侧本身被推远，特异性来自活性衰减的不对称性"]],
    top=1.55, col_w=[2.4, 1.2, 1.8, 6.6], size=12)
add_sub(s, "关键反例：三点组合 Δd_E72 最小（1.83）却特异性最高（2.16）", top=4.35, size=13, color=ACCENT)
add_table(s,
    ["突变", "Δd_E72", "d_GCG（催化几何）", "实测＋1比", "本质"],
    [["K30H", "4.35", "2.78（良好）", "1.71", "真·选择性位移"],
     ["M132E", "1.92", "2.84（良好）", "1.18", "无位移 → 无特异性"],
     ["27T-30H-58M", "1.83", "6.51（退化）", "2.16", "几何整体下调 → 不对称衰减"]],
    top=4.85, col_w=[2.6, 1.8, 2.8, 2.0, 2.8], size=11, row_h=0.32)
add_note(s, "结论：不能用一个线性模型同时描述单点与组合 —— 这正是上期「加性先验失效」在几何层面的再次确认。", top=6.95)

s = add_slide(); add_title(s, "P1-1 噪声诊断：为什么几何指标会失效")
add_table(s,
    ["指标", "数值", "含义"],
    [["GCG 侧 model 间 SD", "≈ 0.25 Å", "稳定 —— GCG 复合物构象收敛"],
     ["GCA 侧 model 间 SD", "≈ 2.3 – 3.9 Å", "极不稳定 —— +1=A 复合物构象高度离散"],
     ["Δd_E72 观测方差", "0.97", "指标本身携带的真实差异"],
     ["噪声方差（5 model 均值）", "1.58", "噪声大于效应"],
     ["信度 rel = 1 − 噪声/观测", "≈ 0", "指标完全被噪声淹没"]],
    top=1.55, col_w=[4.0, 3.0, 5.0], size=12)
add_sub(s, "极端个例：WT_GCA 的 5 个 model 距离为 4.65 / 4.20 / 3.86 / 6.59 / 12.36 Å", top=4.75, size=13, color=ACCENT)
add_bullets(s, [
    ("根因：AF3 对「+1=A（脱靶态）」的预测置信度本就偏低（前期 QC：AUGCAGC 84/100 的 +1 位 pLDDT<60，中位 53.8）", 0, False, GRAY),
    ("方法学结论：该指标若要可用，必须先把 GCA 侧从 5 model 提升到 5–10 seed × 5 model，否则单条件均值不可靠", 0, True, NAVY),
], top=5.35, size=12.5)

# =====================================================================
add_section("05", "P1-2 执行", "三点复合物结构解析：催化几何梯度与锌配位完整性")

s = add_slide(); add_title(s, "P1-2 前置澄清：三点复合物「已存在」，无需重建")
add_bullets(s, [
    ("上期计划书写「现有 AF3 突变体只到双点」—— 实际核查发现命名即是三点：", 0, False, GRAY),
    ("g27tk30hq58m = G27T + K30H + Q58M = 27T-30H-58M", 1, True, NAVY),
    ("g27dk30hq58m = G27D + K30H + Q58M = 27D-30H-58M", 1, True, NAVY),
    ("两者 × {GCG, GCA} × 5 models 文件完整；序列已逐位验证（res27=T/D、res30=H、res58=M）", 0, False, GRAY),
    ("→ 因此直接解析这四个复合物，未重复提交 AF3（节省计算资源，且与既有 CP/ΔCP 分析同源可比）", 0, True, TEAL),
], top=1.5, size=14.5)
add_note(s, "这一步本身也说明：数据集在增长过程中需要定期重新盘点命名与实际内容，避免重复计算。", top=6.5, color=TEAL)

s = add_slide(); add_title(s, "P1-2 结果：催化几何呈单调退化梯度")
add_table(s,
    ["复合物", "C4N4–E72 均值 (Å)", "SD (Å)", "相对 WT 判读"],
    [["WT_GCG", "2.88", "0.32", "基准：催化几何良好且稳定"],
     ["27T-30H_GCG（双点）", "4.52", "2.15", "中度退化"],
     ["27D-30H_GCG（双点）", "4.77", "2.73", "中度退化"],
     ["27D-30H-58M_GCG（三点）", "5.05", "2.16", "显著退化"],
     ["★27T-30H-58M_GCG（三点）", "6.51", "2.71", "★ 最严重退化"],
     ["WT_GCA", "6.33", "3.16", "脱靶态本已远离"],
     ["27T-30H-58M_GCA", "8.34", "3.61", "进一步远离"]],
    top=1.5, col_w=[4.4, 2.8, 1.8, 3.0], size=11.5)
add_kpi(s, [("2.88 → 4.5 → 6.5 Å", "WT → 双点 → 三点：每叠加一个突变，靶点 C 被逐步推离催化中心", ACCENT)], top=5.4, height=1.2)
add_note(s, "这正是 27T-30H-58M「＋1比 2.16 但 on-target 保留仅 77%」的结构基础 —— 代价被精确量化。", top=6.75)

s = add_slide(); add_title(s, "P1-2 结果：锌配位完整性 —— 完全保持")
add_table(s,
    ["复合物", "H70–C102 (Å)", "H70–C105 (Å)", "C102–C105 (Å)", "判读"],
    [["WT_GCG", "3.49", "3.44", "3.79", "基准"],
     ["WT_GCA", "3.62", "3.45", "3.83", "正常"],
     ["27T-30H-58M_GCG", "3.63", "3.66", "3.78", "✓ 完好（偏差 ≤0.22）"],
     ["27T-30H-58M_GCA", "3.63", "3.57", "3.80", "✓ 完好"],
     ["27D-30H-58M_GCG", "3.57", "3.60", "3.79", "✓ 完好"],
     ["27D-30H-58M_GCA", "3.64", "3.51", "3.78", "✓ 完好"]],
    top=1.5, col_w=[3.6, 2.4, 2.4, 2.4, 3.0], size=11.5)
add_bullets(s, [
    ("全部复合物的三个锌配位距离均落在 3.4–3.8 Å 正常范围，与 WT 偏差 ≤ 0.22 Å", 0, False, GRAY),
    ("全 22 个突变体中锌配位偏离最大者为 T31L（0.47 Å），三点组合仅 0.17–0.22 Å", 0, False, GRAY),
], top=4.5, size=13)
add_note(s, "★ 核心结论：酶没有坏 —— 锌指与催化残基结构完好；活性下降来自「底物摆不到位」而非「催化中心崩坏」。这为后续设计指明方向：应修「底物定位」而非换催化残基。", top=5.6, color=TEAL)

# =====================================================================
add_section("06", "综合结论", "干湿互指的方法学沉淀 · 下一步")

s = add_slide(); add_title(s, "综合结论：干湿互指的三条方法学沉淀")
add_table(s,
    ["#", "结论", "证据"],
    [["1", "预测可靠性的分层：结构接触（谁参与）可靠；ML ΔΔG（结合强度）只可粗筛；\n几何判别指标（Δd_E72）在跨组合尺度上失效",
      "K30H/G27D/T 证实 vs M132E/T31A/A59S 证伪；P1-1 r=−0.073"],
     ["2", "单点与组合走两套机制：单点靠选择性几何位移（r=+0.67）；\n组合靠整体催化几何下调（r=−0.72）→ 线性加性模型必然失效",
      "P1-1 分层；27T-30H-58M Δd 最小却比最高"],
     ["3", "「单点保留率高」不能预测「组合安全」：真正判据是侧链物化类型\n（带电/刚性替换高风险；疏水/柔性/保守替换安全）",
      "132D/30H/27D 组合塌方；27T/25E/58M/132E 安全"]],
    top=1.5, col_w=[0.8, 6.4, 4.8], size=11)
add_note(s, "可迁移的设计规则：① 每层机制各取一个位点组成组合；② 避开带电/刚性替换进组合；③ 用「同批次亲本 ROF」而非绝对比值做跨实验比较。", top=5.4, color=TEAL)
add_kpi(s, [("2.16", "27T-30H-58M ＋1比（唯一双达标）", GREEN),
            ("77%", "on-target 保留", BLUE),
            ("6.51 Å", "其 GCG 侧催化几何代价（WT 2.88）", ACCENT)], top=3.5, height=1.5)

s = add_slide(); add_title(s, "下一步：优先级不变，P0 仍是决定项目成败的一步")
add_table(s,
    ["优先级", "任务", "为什么"],
    [["P0（最高）", "剂量梯度实验：验证 2.16 是「真特异性」还是「活性衰减假象」",
      "若为假象，此前全部组合结论需重估；且已有 132D 组合塌方的前车之鉴"],
     ["P0", "GCA 侧多 seed 重采样（5→5–10 seed × 5 model）",
      "P1-1 已证明 GCA 侧噪声（SD 2.3–3.9 Å）使几何指标信度归零"],
     ["P1", "优先合成 Y32F+M132E、G27D+Y32F（本期最佳位点对：ratio 2.2/2.0，活性 0.35/0.36）",
      "唯一比 ≥2.0 且 C388 ≥0.35 的「高比+高活性」双达标位点对"],
     ["P1", "R28A 单点验证（CP 预测双向增强，尚未湿实验）",
      "计算新发现的强候选，风险与潜力并存"],
     ["P2", "共进化+空间交集位点对的定向进化建库（27-30、30-58、30-99）",
      "MI 与空间均支持的耦合对，优于穷举"]],
    top=1.5, col_w=[1.6, 6.0, 4.4], size=11)
add_note(s, "一句话：27T-30H-58M 仍是最佳候选，但它是「保 G 排 A」还是「整体降活」，取决于 P0 剂量梯度实验 —— 这一步不可跳过。", top=6.85)

# 结束页
s = add_slide()
band = s.shapes.add_shape(1, Inches(0), Inches(2.6), prs.slide_width, Inches(2.0))
band.fill.solid(); band.fill.fore_color.rgb = NAVY; band.line.fill.background()
box = s.shapes.add_textbox(Inches(1.0), Inches(2.9), Inches(11.3), Inches(1.6))
tf = box.text_frame; tf.word_wrap = True
r = tf.paragraphs[0].add_run(); r.text = "谢谢 · 请批评指正"
set_font(r, 34, True, WHITE)
p = tf.add_paragraph(); r = p.add_run()
r.text = "核心问题：P0-1 剂量梯度是否仍应作为最高优先级？（本期新增证据支持：是）"
set_font(r, 15, False, RGBColor(0xC8, 0xD6, 0xE8))

prs.save("APOBEC保G排A优化_组会汇报_第二期.pptx")
print("已生成 APOBEC保G排A优化_组会汇报_第二期.pptx，共", len(prs.slides.__iter__.__self__._sldIdLst), "页")
