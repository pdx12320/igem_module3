# -*- coding: utf-8 -*-
"""
本周组会汇报稿 = 第一期（三维证据整合）+ 第二期（P1-1/P1-2 执行）合并
衔接基线：上期组会《可突变性与突变方向分析_组会汇报.pptx》(12页)
          — 接触类型分解 → 保守性/共进化 → PSSM 突变方向 → 湿实验验证
主线：三阶段递进 + 干实验预测 ⇄ 湿实验验证 双向指导

用法：uv run --with python-pptx python make_presentation_combined.py
产出：APOBEC保G排A优化_组会汇报_综合稿.pptx
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


def add_title(slide, text, size=25):
    box = slide.shapes.add_textbox(Inches(0.55), Inches(0.26), Inches(12.3), Inches(0.8))
    tf = box.text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run(); r.text = text; set_font(r, size, True, NAVY)
    line = slide.shapes.add_shape(1, Inches(0.58), Inches(0.96), Inches(3.2), Pt(2.2))
    line.fill.solid(); line.fill.fore_color.rgb = BLUE; line.line.fill.background()


def add_sub(slide, text, top=1.02, size=12, color=BLUE):
    box = slide.shapes.add_textbox(Inches(0.6), Inches(top), Inches(12.2), Inches(0.4))
    tf = box.text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run(); r.text = text; set_font(r, size, False, color)


def add_bullets(slide, items, left=0.7, top=1.3, width=12.0, height=5.9, size=15):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame; tf.word_wrap = True
    for i, (txt, lvl, bold, color) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = lvl; p.space_after = Pt(6)
        r = p.add_run(); r.text = ("• " if lvl == 0 else "– ") + txt
        set_font(r, size if lvl == 0 else size - 2, bold, color)
    return box


def add_table(slide, headers, rows, left=0.7, top=1.45, width=12.0, col_w=None,
              size=11, hdr_size=None, row_h=0.3):
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
        r = p.add_run(); r.text = str(h); set_font(r, hdr_size or size, True, WHITE)
    for i, row in enumerate(rows, start=1):
        for j, v in enumerate(row):
            c = tbl.cell(i, j); c.text = ""
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            if i % 2 == 0:
                c.fill.solid(); c.fill.fore_color.rgb = LIGHT
            p = c.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
            r = p.add_run(); r.text = str(v)
            col = GRAY; s = str(v)
            if any(k in s for k in ("✓", "安全", "完好", "证实", "双达标")):
                col = GREEN
            if any(k in s for k in ("✗", "⚠", "阴性", "失效", "崩", "失活", "撤回")):
                col = ACCENT
            set_font(r, size, False, col)
    return tbl


def add_kpi(slide, items, top=1.6, height=1.4):
    n = len(items); gap = 0.3
    w = (12.0 - gap * (n - 1)) / n
    for i, (num, lab, col) in enumerate(items):
        left = 0.7 + i * (w + gap)
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top),
                                     Inches(w), Inches(height))
        box.fill.solid(); box.fill.fore_color.rgb = WHITE
        box.line.color.rgb = col; box.line.width = Pt(1.5)
        tf = box.text_frame; tf.word_wrap = True; tf.margin_top = Pt(6)
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = num; set_font(r, 27, True, col)
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = lab; set_font(r2, 11.5, False, GRAY)


def add_note(slide, text, top=6.75, color=ACCENT, size=11.5):
    box = slide.shapes.add_textbox(Inches(0.7), Inches(top), Inches(12.0), Inches(0.5))
    tf = box.text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run(); r.text = text
    set_font(r, size, True, color)


def add_section(num, title, subtitle):
    s = add_slide()
    band = s.shapes.add_shape(1, Inches(0), Inches(2.5), prs.slide_width, Inches(2.2))
    band.fill.solid(); band.fill.fore_color.rgb = NAVY; band.line.fill.background()
    box = s.shapes.add_textbox(Inches(1.0), Inches(2.7), Inches(11.2), Inches(1.8))
    tf = box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; r = p.add_run(); r.text = num
    set_font(r, 40, True, RGBColor(0x8F, 0xB4, 0xDE))
    p2 = tf.add_paragraph(); r2 = p2.add_run(); r2.text = title
    set_font(r2, 29, True, WHITE)
    p3 = tf.add_paragraph(); r3 = p3.add_run(); r3.text = subtitle
    set_font(r3, 14, False, RGBColor(0xC8, 0xD6, 0xE8))
    return s


# =====================================================================
# 封面
# =====================================================================
s = add_slide()
bar = s.shapes.add_shape(1, Inches(0), Inches(0), prs.slide_width, Inches(0.35))
bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
box = s.shapes.add_textbox(Inches(0.9), Inches(1.5), Inches(11.6), Inches(3.2))
tf = box.text_frame; tf.word_wrap = True
r = tf.paragraphs[0].add_run(); r.text = "APOBEC「保 G 排 A」优化"
set_font(r, 40, True, NAVY)
p = tf.add_paragraph(); r = p.add_run()
r.text = "阶段综合汇报：从突变方向分析 → 三维证据整合 → P1-1 / P1-2 执行验证"
set_font(r, 18, False, ACCENT)
p = tf.add_paragraph(); r = p.add_run()
r.text = "干实验预测 ⇄ 湿实验验证 的双向迭代"
set_font(r, 16, False, TEAL)
box2 = s.shapes.add_textbox(Inches(0.9), Inches(4.9), Inches(11.6), Inches(1.9))
tf2 = box2.text_frame; tf2.word_wrap = True
for t, sz, c in [
    ("目标：改造 REWIRE 系统 APOBEC，使其特异编辑 GCG（APOE c.388）而非 GCA（c.871）", 13, GRAY),
    ("底盘 Pro.hA1 (199 aa) ｜ AF3 复合物 300 + 22 突变体×2 底物 ｜ 单点饱和 103 ｜ 组合 71 组 (n=2)", 12.5, BLUE),
    ("本期新增：Δd_E72 全补齐与回归 · 27T-30H-58M / 27D-30H-58M 结构解析 · 132D 组合活性压制效应", 12.5, GRAY),
    ("组会汇报 · 2026-09-11", 11, RGBColor(0x80, 0x80, 0x80)),
]:
    pp = tf2.paragraphs[0] if not tf2.paragraphs[0].runs else tf2.add_paragraph()
    rr = pp.add_run(); rr.text = t; set_font(rr, sz, False, c)

# =====================================================================
# 三阶段衔接
# =====================================================================
s = add_slide(); add_title(s, "三阶段衔接：上期 → 第一期 → 本期")
add_table(s,
    ["阶段", "核心问题", "主要产出", "状态"],
    [["上期组会\n《可突变性与突变方向分析》",
      "接触是否可设计？哪些位点能变？朝哪些方向变？",
      "接触类型分解 · 保守性/共进化 · PSSM 突变方向 · 102 单点湿实验验证",
      "已完成"],
     ["第一期\n《三维证据整合》",
      "MI × 空间 × 实验三表如何收敛到候选？",
      "单点天花板 1.71 · 组合 27T-30H-58M = 2.16/77% · 三层分工机制 · 加性先验失效",
      "已完成"],
     ["本期（第二期）\n《P1-1 / P1-2 执行》",
      "几何指标能否预测特异性？三点复合物结构如何？",
      "Δd_E72 回归（阴性+分层真相）· 三点催化几何梯度 · 锌配位完好 · 132D 矛盾",
      "★ 本次新增"]],
    top=1.5, col_w=[3.0, 3.4, 5.0, 1.6], size=11.5, row_h=0.9)
add_note(s, "衔接要点：上期回答「哪些位点可用」，第一期回答「哪些组合最好」，本期回答「为什么好、以及预测方法错在哪」。", top=6.6, color=TEAL)

# 提纲
s = add_slide(); add_title(s, "汇报提纲")
add_bullets(s, [
    ("一、问题定义与证据底座（第一期）", 0, True, NAVY),
    ("问题定义 · 三个正交问题 · 干湿双向闭环 · 位点主表", 1, False, GRAY),
    ("二、第一期核心发现 A/B/C", 0, True, NAVY),
    ("A 两套实验基数不同 · B 结构定位（接触分解/T31 悖论/M132 出口）· C 单点天花板与核心成果", 1, False, GRAY),
    ("三、本期执行：P1-1 / P1-2（本次新增）", 0, True, ACCENT),
    ("湿→干三个打脸发现 · 132D 矛盾 · Δd_E72 回归 · 三点复合物结构解析", 1, False, GRAY),
    ("四、综合结论、不足与下一步", 0, True, NAVY),
    ("三条方法学沉淀 · 项目不足清单 · P0/P1/P2 计划更新", 1, False, GRAY),
], top=1.45, size=15)

# =====================================================================
add_section("01", "问题定义与证据底座", "388 vs 871 的 +1 位核心差异 · 三个正交维度 · 干湿双向闭环")

s = add_slide(); add_title(s, "问题定义：唯一核心差异在 +1 位")
add_table(s,
    ["位置", "−3", "−2", "−1", "0（编辑位）", "+1", "+2", "+3"],
    [["388 靶位（G 型）", "G", "U", "G", "C", "G", "C", "G"],
     ["871 脱靶（A 型）", "A", "U", "G", "C", "A", "G", "C"],
     ["是否差异", "差异", "同", "同", "同", "★ 核心", "差异", "差异"]],
    top=1.6, col_w=[2.8, 1.3, 1.3, 1.3, 1.9, 1.7, 1.3, 1.3], size=12.5)
add_bullets(s, [
    ("目标：改造 APOBEC，使其在 +1 位偏好读 G（保 388）、排斥 A（抑 871）", 0, True, NAVY),
    ("指标：＋1 比 = C388 编辑效率 / C871 编辑效率；约束：on-target 保留率 ≥ 可接受水平", 0, False, GRAY),
    ("编辑 C 为 0 位；三组 AF3 底物：GUGCGCG（+1=G）、GUGCACG（纯 +1 交换）、AUGCAGC（完整脱靶）", 0, False, GRAY),
], top=3.6, size=13.5)
add_note(s, "解耦逻辑：GCG vs GCA-swap = 纯 +1 效应；swap vs 完整脱靶 = 纯侧翼效应。", top=6.4, color=TEAL)

s = add_slide(); add_title(s, "研究思路：把大问题拆成三个可独立检验的正交问题")
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
add_note(s, "贯穿原则（上期已建立）：结构只定位「谁参与」，保守性只回答「能不能动」，ML 只预测结合 ΔΔG —— 三者都不等于特异性。", top=6.75)

s = add_slide(); add_title(s, "干湿双向闭环：预测与验证如何相互指导")
b1 = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(1.5), Inches(5.3), Inches(4.35))
b1.fill.solid(); b1.fill.fore_color.rgb = RGBColor(0xEC, 0xF2, 0xFA); b1.line.color.rgb = BLUE
tf = b1.text_frame; tf.word_wrap = True; tf.margin_left = Pt(14); tf.margin_top = Pt(10)
p = tf.paragraphs[0]; r = p.add_run(); r.text = "干 → 湿：预测指导实验"
set_font(r, 17, True, BLUE)
for t in ["接触类型分解 → 判定接触是否「可设计」",
          "结构接触 → 锁定 +1 / −1 判别残基",
          "保守性 + 共进化 → 排除必失活位点（T31 82%、N57 共进化最高）",
          "PSSM → 给出「允许/禁止」突变方向，避免无效实验",
          "CP/ΔCP → 预测突变如何重塑判别网络",
          "组合位点对筛选 → 生成优先合成清单"]:
    pp = tf.add_paragraph(); pp.space_after = Pt(5)
    rr = pp.add_run(); rr.text = "• " + t; set_font(rr, 12, False, GRAY)
b2 = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.3), Inches(1.5), Inches(5.3), Inches(4.35))
b2.fill.solid(); b2.fill.fore_color.rgb = RGBColor(0xFB, 0xEF, 0xEC); b2.line.color.rgb = ACCENT
tf = b2.text_frame; tf.word_wrap = True; tf.margin_left = Pt(14); tf.margin_top = Pt(10)
p = tf.paragraphs[0]; r = p.add_run(); r.text = "湿 → 干：实验倒逼预测升级"
set_font(r, 17, True, ACCENT)
for t in ["PSSM 验证：核心位点 71% / 溶剂暴露 loop 仅 9%",
          "单点天花板 1.71 → 迫使转向组合设计",
          "M132 悖论（同源 5% 可变却实验平庸）→ 出口通道 ≠ 判别子",
          "T31 悖论（结构接触强却实验无效）→ 接触 ≠ 功能",
          "PremPRI 判反 M132E/D → ML 只能做粗筛",
          "132D 组合塌方 → 「单点保留 ≠ 组合安全」新判据"]:
    pp = tf.add_paragraph(); pp.space_after = Pt(5)
    rr = pp.add_run(); rr.text = "• " + t; set_font(rr, 12, False, GRAY)
ar = s.shapes.add_shape(MSO_SHAPE.LEFT_RIGHT_ARROW, Inches(6.05), Inches(3.05), Inches(1.2), Inches(0.9))
ar.fill.solid(); ar.fill.fore_color.rgb = TEAL; ar.line.fill.background()
add_note(s, "方法学主张：干实验的价值不在「算得准」，而在缩小搜索空间并给出可证伪的机制假设；湿实验的价值不只是筛选，更在于暴露预测体系的失效边界。", top=6.15, color=TEAL)

# 表一 位点主表
s = add_slide(); add_title(s, "表一 · 位点主表（MI × 接触 × 保守性 × 实验，节选关键位点）", size=23)
add_sub(s, "SC = 侧链–碱基接触频率（0–1）；MI核 = 与催化核心的平均互信息；单点亲本 WT：C388=0.5145 / C871=0.3754 → ＋1比 = 1.371", top=1.0)
add_table(s,
    ["位点", "WT", "区域", "功能角色", "可动性", "保守", "MI核", "SC-G", "SC-A", "最佳单点", "＋1比", "保留"],
    [["25", "G", "loop1-N", "N端调节", "可动", "0.02", "0.21", "0.00", "0.00", "25E", "1.55", "0.89"],
     ["26", "I", "loop1-N", "−1端调节", "可动", "0.04", "0.19", "0.00", "0.00", "26N", "1.42", "0.98"],
     ["27", "G", "loop1-N", "−1位主锚", "慎动", "0.82", "0.13", "0.00", "0.00", "27D", "1.53", "0.88"],
     ["28", "R", "loop1-N", "loop1壁", "慎动", "0.84", "0.12", "0.18", "0.00", "28W", "1.32", "0.94"],
     ["29", "H", "阅读器", "保G阅读(主链)", "可动", "0.22", "0.18", "0.96", "0.05", "未测", "—", "—"],
     ["30", "K", "阅读器", "保G阅读主(侧链)", "可动", "0.36", "0.23", "0.81", "0.64", "30H", "1.71", "0.84"],
     ["31", "T", "阅读器", "贴A氢键(非判别)", "慎动", "0.82", "0.15", "0.00", "1.00", "31A", "1.32", "0.97"],
     ["32", "Y", "阅读器", "排+2G", "可动", "0.56", "0.21", "0.00", "0.00", "未测", "—", "—"],
     ["56", "H", "loop3", "loop3前壁", "可动", "0.05", "0.26", "0.01", "0.00", "未测", "—", "—"],
     ["57", "N", "loop3", "催化必需", "禁区", "0.67", "0.30", "0.02", "1.00", "57S", "1.59", "0.37"],
     ["58", "Q", "loop3", "loop3排A", "可动", "0.29", "0.24", "0.00", "0.00", "58I", "1.84", "0.10"],
     ["59", "A", "loop3", "loop3壁", "可动", "0.16", "0.23", "0.22", "0.00", "59S", "1.33", "0.74"],
     ["60", "K", "loop3", "loop3尾", "可动", "0.30", "0.13", "0.03", "0.02", "60Q", "2.55", "0.17"],
     ["98", "S", "WS环", "WS环", "慎动", "0.91", "0.08", "0.00", "0.00", "98G", "1.45", "0.47"],
     ["99", "W", "WS环", "保守Trp", "禁区", "0.74", "0.19", "0.00", "0.90", "未测", "—", "—"],
     ["129", "F", "loop7-出口", "loop7头", "可动", "0.29", "0.14", "0.00", "0.24", "129W", "1.30", "0.87"],
     ["130", "W", "loop7-出口", "loop7探针", "可动", "0.03", "0.19", "0.00", "0.01", "130G", "3.00", "0.32"],
     ["131", "H", "loop7-出口", "loop7", "可动", "0.21", "0.22", "0.00", "0.00", "131R", "1.72", "0.31"],
     ["132", "M", "loop7-出口", "出口通道", "可动", "0.05", "0.14", "0.00", "0.00", "132D", "1.42", "0.89"],
     ["133", "D", "loop7-出口", "loop7尾", "可动", "0.43", "0.13", "0.00", "0.00", "133Y", "1.37", "0.51"]],
    top=1.42, col_w=[0.75, 0.6, 1.5, 2.0, 0.9, 0.8, 0.8, 0.8, 0.8, 1.1, 0.8, 0.75],
    size=9.5, hdr_size=9.5, row_h=0.245)

# =====================================================================
add_section("02", "第一期核心发现", "A 两套实验基数 · B 结构定位 · C 单点天花板与核心成果")

s = add_slide(); add_title(s, "⚠ 关键发现 A：两套湿实验用了不同的亲本背景")
add_table(s,
    ["实验批次", "亲本", "C388 (on)", "C871 (off)", "＋1 比", "C295 (ACA)"],
    [["单点饱和", "WT (PUF12-9)", "0.5145", "0.3754", "1.371", "0.294"],
     ["组合突变", "PUF12-9（对照孔）", "0.673", "0.565", "1.191", "0.335"],
     ["差异", "—", "+31%", "+50%", "−13%", "+14%"]],
    top=1.55, col_w=[2.4, 3.0, 2.0, 2.0, 1.8, 1.8], size=12)
add_bullets(s, [
    ("组合亲本 on-target 更高，但脱靶也更高 → 净效果 ＋1比 反而更差", 0, True, ACCENT),
    ("影响：此前「单点相乘模型预测组合上限 ~2.0」的做法基线取错", 0, False, GRAY),
    ("校正：全部跨实验比较统一用 ROF =（自身＋1比）÷（同实验亲本＋1比）", 0, True, NAVY),
], top=3.6, size=13.5)
add_kpi(s, [("< 10%", "两次重复最大相对偏差", GREEN),
            ("0 例", "「一次有活性/一次全 0」严重不一致", GREEN),
            ("7 组", "两次重复 C871 均为 0（可重复清除）", TEAL),
            ("12/100", "C295(ACA) 检出行数 → ACA 分析不可用", ACCENT)], top=5.1, height=1.35)
add_note(s, "方法学更正：C871=0 应作为「脱靶彻底清除」单独分层；此前脚本当缺失值丢弃，低估了这些组合。", top=6.65)

s = add_slide(); add_title(s, "关键发现 B-1：接触类型分解 —— 谁在「直接读碱基」")
add_table(s,
    ["残基", "侧链–碱基 (GCG)", "侧链–碱基 (GCA)", "主链–碱基 (GCG)", "接触性质判定"],
    [["H29", "0.96", "0.05", "0.94", "主链读碱基（侧链贡献有限）"],
     ["K30", "0.81", "0.64", "0.16", "★ 侧链–碱基特异（唯一可动的 +1 读取器）"],
     ["T31", "0.00", "1.00", "0.00", "侧链特异，但仅对 A 形成"],
     ["N57", "0.02", "1.00", "0.01", "催化必需（侧链特异但不可动）"],
     ["H70 / E72 / W99", "—", "1.00 / 0.92 / 0.90", "—", "纯侧链–碱基（催化核心，绝对禁区）"],
     ["Q58", "0.00", "0.00", "0.01", "不直接接触碱基（loop3，间接）"],
     ["M132", "0.00", "0.00", "0.00", "完全不接触（出口通道，距 +1 位 15–20 Å）"]],
    top=1.55, col_w=[2.2, 2.4, 2.6, 2.4, 5.0], size=11.5)
add_note(s, "结论：G 型复合物中与 +1 碱基形成侧链特异接触的只有 H29（主链为主）与 K30 → 单点路线先天受限。", top=6.6)

s = add_slide(); add_title(s, "关键发现 B-2：T31 悖论 —— 结构接触 ≠ 功能")
b1 = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(1.5), Inches(5.8), Inches(3.0))
b1.fill.solid(); b1.fill.fore_color.rgb = RGBColor(0xEC, 0xF2, 0xFA); b1.line.color.rgb = BLUE
tf = b1.text_frame; tf.word_wrap = True; tf.margin_left = Pt(12); tf.margin_top = Pt(8)
p = tf.paragraphs[0]; r = p.add_run(); r.text = "结构证据（支持 T31 是排 A 靶点）"
set_font(r, 15, True, BLUE)
for t in ["GCA 中侧链–碱基接触频率 = 1.00",
          "GCG 中侧链–碱基接触频率 = 0.00",
          "是 +1 位唯一「仅对 A 形成」的侧链氢键",
          "表面上是最理想的「排 A」改造靶点"]:
    pp = tf.add_paragraph(); pp.space_after = Pt(4)
    rr = pp.add_run(); rr.text = "• " + t; set_font(rr, 12, False, GRAY)
b2 = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.5), Inches(5.8), Inches(3.0))
b2.fill.solid(); b2.fill.fore_color.rgb = RGBColor(0xFB, 0xEF, 0xEC); b2.line.color.rgb = ACCENT
tf = b2.text_frame; tf.word_wrap = True; tf.margin_left = Pt(12); tf.margin_top = Pt(8)
p = tf.paragraphs[0]; r = p.add_run(); r.text = "实验证据（否定该假说）"
set_font(r, 15, True, ACCENT)
for t in ["T31A：＋1比 1.32，保留 97% → 无改善",
          "T31C：＋1比 1.25，保留 98% → 无改善",
          "T31V/I/L：PremPRI 支持排 A，但明显伤 G",
          "→ 切除该氢键无效，「T31 排 A」假说正式撤回"]:
    pp = tf.add_paragraph(); pp.space_after = Pt(4)
    rr = pp.add_run(); rr.text = "• " + t; set_font(rr, 12, False, GRAY)
add_note(s, "开放问题：T31 是否只在 K30 存在时才起作用（条件性判别子）？建议做 T31A + K30H 上位性实验（→ 下一步 P1-3）。", top=4.8, color=TEAL)

s = add_slide(); add_title(s, "关键发现 B-3：M132 是出口通道残基，不是 +1 判别子")
add_bullets(s, [
    ("位置：与 +1 碱基距离 15–20 Å，接触频率 = 0，完全不接触碱基", 0, False, GRAY),
    ("真实作用：调整目标 C 到 E72 催化中心的几何，影响催化与产物释放", 0, False, GRAY),
    ("实验印证：132D 保留 89% 但 ＋1比仅 1.42（几乎无提升）；132E 更差（1.18）", 0, False, GRAY),
    ("关键教训：ML 工具（mCSM-NA 给 M132D/E 最高分 +9.5；PremPRI 偏好 E）预测的是结合强度 ΔΔG，不是 G/A 特异性 —— 且 PremPRI 把 D/E 判反", 0, True, ACCENT),
    ("修正后的用法：ML 工具只能用于排除必失活方向，绝不能用于特异性排序", 0, True, NAVY),
], top=1.5, size=14)
add_note(s, "这条结论解释了为何「计算预测高分」的 132 系列实验表现平庸 —— 指标用错了维度。", top=6.2)

s = add_slide(); add_title(s, "关键发现 C-1：单点天花板 —— 103 个突变无一突破 2.0")
add_table(s,
    ["突变", "功能角色", "＋1 比", "保留率", "突变", "功能角色", "＋1 比", "保留率"],
    [["30H", "保G阅读主(侧链)", "1.71", "0.84", "132D", "出口通道", "1.42", "0.89"],
     ["25E", "N端调节", "1.55", "0.89", "59S", "loop3壁", "1.33", "0.74"],
     ["27D", "−1位主锚", "1.53", "0.88", "28W", "loop1壁", "1.32", "0.94"],
     ["58M", "loop3排A", "1.46", "0.79", "31A", "贴A氢键(非判别)", "1.32", "0.97"],
     ["27T", "−1位主锚", "1.45", "0.98", "129W", "loop7头", "1.30", "0.87"],
     ["26N", "−1端调节", "1.42", "0.98", "—", "—", "—", "—"]],
    top=1.55, col_w=[1.1, 2.6, 1.1, 1.2, 1.1, 2.6, 1.1, 1.2], size=11)
add_kpi(s, [("1.71", "保留率 ≥60% 的单点上限", ACCENT),
            ("0 个", "103 个单点中突破 2.0 的数量", ACCENT)], top=3.9, height=1.4)
add_bullets(s, [
    ("结论：任何单个位点只能强化三层机制中的一层（见下页）→ 单点存在结构性上限，突破必须靠组合", 0, True, NAVY),
    ("注：58I（1.84）、130G（3.00）、60Q（2.55）等比更高，但保留率仅 0.10–0.32，属「以活性换比」的不可用突变", 1, False, GRAY),
], top=5.55, size=13)

s = add_slide(); add_title(s, "关键发现 C-2：核心成果 —— 比–活性 Pareto 前沿")
add_table(s,
    ["组合", "位点数", "＋1 比", "保留率", "脱靶倍数", "定位"],
    [["58M-130G", "2", "3.71", "0.29", "0.09", "比最高，活性低"],
     ["27D-30H-32F", "3", "3.44", "0.38", "0.13", "高比，活性中低"],
     ["32F-132E", "2", "2.22", "0.52", "0.28", "比与活性折中"],
     ["27T-32F", "2", "2.01", "0.59", "0.35", "−1 锚 × 排 +2G"],
     ["27T-132E", "2", "2.08", "0.60", "0.35", "高比高活性"],
     ["★ 27T-30H-58M", "3", "2.16", "0.77", "0.43", "★ 唯一双达标"],
     ["32F-58M", "2", "1.74", "0.79", "0.54", "高活性"],
     ["PUF12-9（亲本）", "1", "1.19", "1.00", "1.00", "基线"]],
    top=1.5, col_w=[3.0, 1.3, 1.3, 1.3, 1.5, 3.6], size=11)
add_note(s, "比 ≥2.0 且保留 ≥45% 的 Pareto 前沿仅 4 个；只有 27T-30H-58M 达到保留 ≥70% 的项目目标门槛。", top=6.5)

s = add_slide(); add_title(s, "★ 核心推荐：27T + 30H + 58M（G27T / K30H / Q58M）")
add_kpi(s, [("2.16", "＋1 比（亲本 1.19，+0.97）", GREEN),
            ("77%", "on-target 保留（C388 0.673→0.520）", BLUE),
            ("0.43", "脱靶倍数（C871 0.565→0.241）", TEAL),
            ("未检出", "C295 (ACA) 脱靶降至 0", GREEN)], top=1.7, height=1.55)
add_bullets(s, [
    ("全部 71 组组合中唯一同时满足「＋1比 ≥2.0」与「保留率 ≥70%」的变体", 0, True, NAVY),
    ("三层机制各取一个位点：G27T（−1 锚定）× K30H（+1 读取）× Q58M（活性保护）", 0, False, GRAY),
    ("本期 P1-2 将为其补上结构机制证据（见第三章）", 0, False, TEAL),
], top=3.7, size=14)

s = add_slide(); add_title(s, "机制模型：三层功能分工假设")
add_table(s,
    ["层级", "功能", "承担位点", "实验证据"],
    [["第一层\n+1 位读取", "决定对 G/A 的内在分辨能力",
      "K30（可动）\nH29（主链为主）\nT31（仅读 A，非判别）",
      "K30H：＋1比 1.71（最高单点）"],
     ["第二层\n−1 位锚定", "决定上游碱基选择，压制 ACA 类脱靶",
      "G27、I26、R28（loop1-N）",
      "G27D：ACA/GCA 降至 0.008（36 倍压制）"],
     ["第三层\n出口与活性调节", "决定整体活性与产物释放，间接影响表观比",
      "M132（出口）\nQ58（loop3）\nG25（N 端）",
      "Q58M 是唯一显著提升保留的位点（+14pp）；M132D 保留 89% 但比仅 1.42"]],
    top=1.5, col_w=[2.0, 3.6, 3.0, 4.0], size=11, row_h=0.75)
add_note(s, "推论：任何单点只强化一层 → 单点有天花板；27T-30H-58M 同时强化三层 → 唯一双达标。设计规则：每层各取一个位点，而非选 MI 最高/距离最近的两点。", top=5.6, color=TEAL)

s = add_slide(); add_title(s, "位点边际效应：比提升器 + 活性保护器 = 可复制的范式")
add_table(s,
    ["位点", "样本数", "Δ ＋1 比", "Δ 保留率", "角色判定"],
    [["Y32F", "14", "+0.21", "−3 pp", "比提升器（排 +2G）"],
     ["K30H", "9", "+0.20", "−9 pp", "比提升器（唯一可动的 +1 读取器）"],
     ["G27D/T", "18", "+0.12", "−2 pp", "比提升器 + ACA 压制"],
     ["M132D/E", "15", "+0.08", "−7 pp", "弱比提升，活性代价明显"],
     ["G25E", "9", "−0.27", "+2 pp", "中性 / 活性向"],
     ["Q58M", "10", "−0.17", "+14 pp", "★ 唯一强活性保护器"]],
    top=1.6, col_w=[2.0, 1.6, 1.8, 1.8, 5.0], size=11.5)
add_note(s, "设计规则：比提升器（27T / 30H / 32F）+ 唯一活性保护器（58M）→ 27T-30H-58M 不是巧合，而是可复制的范式。", top=5.9, color=TEAL)

# =====================================================================
add_section("03", "本期执行：P1-1 / P1-2", "本次新增 · 承接第一期「下一步」中的两项关键验证")

s = add_slide(); add_title(s, "本期任务定位：完成第一期遗留的两个关键验证")
add_table(s,
    ["第一期提出的问题", "本期执行结果"],
    [["P1-1：Δd_E72 能否作为主筛指标？\n对全部 22 个突变体补齐 Δd_E72 与实测＋1比做回归。\n判据：r > 0.7 → 采用；否则放弃计算筛选",
      "已完成：r = −0.073，95% CI [−0.600, +0.498] → 阴性\n但分层后发现关键机制差异：单点 +0.67 / 组合 −0.72\n噪声诊断定位失效根因（GCA 侧置信度低）"],
     ["P1-2：给 27T-30H-58M 补结构解析\n测 Δd_E72、C4N4–E72、锌配位完整性",
      "已完成（模型原已存在，无需重建）：\nC4N4–E72 单调退化 2.88→4.5→6.5 Å\n锌配位完好（偏差 ≤0.22 Å）→ 酶没坏，底物摆不到位"],
     ["第一期遗留风险 A1：组合特异性是否为活性衰减假象",
      "本期新增证据：132D 组合活性压制效应\n（单点保留 89% vs 组合中位 0.191），并外推至 30H / 27D"]],
    top=1.5, col_w=[5.2, 6.8], size=11.5, row_h=0.85)

s = add_slide(); add_title(s, "湿→干：四个关键「打脸」发现")
add_table(s,
    ["实验发现", "被否定的干预测", "倒逼出的新认知"],
    [["单点天花板 1.71\n（103 个单点无一破 2.0）", "「找到最强单点即可达标」",
      "单个位点只能强化三层机制中的一层 → 必须组合"],
     ["M132 悖论\n（同源 5% 可变、ML 高分，实验 1.42/1.18）", "ML 的 ΔΔG 高分 = 高价值候选",
      "M132 位于出口通道（距 +1 位 15–20 Å）→ ML 预测结合强度，不是特异性"],
     ["T31 悖论\n（结构上唯一「仅对 A」氢键，实验 1.32 无改善）", "「结构接触 = 可设计靶点」",
      "接触 ≠ 功能 → 结构证据必须叠加功能验证"],
     ["加性先验模型失效\n（30+58 理论 0.81 第1，实测 1.69/78%）", "「MI + 距离 + 单点效应」线性可加",
      "组合存在显著上位效应 → 线性模型不可外推（本期 P1-1 再次确认）"]],
    top=1.5, col_w=[3.5, 3.5, 5.0], size=11)

s = add_slide(); add_title(s, "★ 本期重点：132D 矛盾 —— 单点保留 89%，组合却系统性压制活性")
add_table(s,
    ["层级", "C388 中位", "C388>0.3 占比", "全失活比例"],
    [["单点 132D", "0.89（保留率）", "—", "—"],
     ["含 132D 的组合 (n=13)", "0.191", "0%", "12%"],
     ["含 132E 的组合 (n=9)", "0.346", "56%", "0%"],
     ["不含 132 的组合 (n≈30)", "0.295", "47%", "7%"]],
    top=1.5, col_w=[4.0, 2.6, 2.8, 2.6], size=12)
add_sub(s, "受控对比（固定其余位点，仅切换 132）—— 排除混淆因素后的关键证据", top=4.35, size=12.5)
add_table(s,
    ["背景", "不含 132", "+132D", "+132E"],
    [["27T + 32F", "0.403", "0.249", "0.485"],
     ["27D + 32F", "0.289", "0.172", "—"],
     ["30H + 32F", "0.153", "0.000", "0.153"]],
    top=4.8, col_w=[3.0, 3.0, 3.0, 3.0], size=11.5, row_h=0.3)
add_note(s, "机制：132D 把 Asp 负电荷引入出口通道；单点时构象余量足够可容忍，组合时其他突变已压缩余量，再叠加即越过活性阈值。132E 侧链更长更柔 → 组合安全。", top=6.55, size=10.5)

s = add_slide(); add_title(s, "矛盾可否推广？—— 判据是「侧链物化类型」而非「单点保留率」")
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
add_note(s, "规律：出问题的都是「带电/刚性侧链替换」(D/H)；安全的是「疏水/柔性/保守替换」(T/E/M)。→ 候选突变进组合前，先看物化类型，再信单点保留率。", top=6.6)

s = add_slide(); add_title(s, "P1-1 方法：Δd_E72 定义与 22 个突变体（节选）")
add_sub(s, "Δd_E72 = d_E72(GCA) − d_E72(GCG)；d_E72 = 靶点 C(0位, RNA res4) 的脱氨原子 C4/N4 到催化 E72 羧基的最小重原子距离", top=1.02)
add_table(s,
    ["突变", "d_GCG(Å)", "d_GCA(Å)", "Δd_E72(Å)", "实测＋1比", "突变", "d_GCG(Å)", "d_GCA(Å)", "Δd_E72(Å)", "实测＋1比"],
    [["WT", "2.88", "6.33", "3.45", "1.37", "Q58M", "2.56", "5.53", "2.97", "1.46"],
     ["K30H", "2.78", "7.13", "4.35", "1.71", "Y32F", "3.00", "5.86", "2.86", "1.47"],
     ["K30H+Q58M", "2.68", "7.64", "4.96", "1.69*", "G27D", "3.18", "6.59", "3.41", "1.53"],
     ["M132E", "2.84", "4.76", "1.92", "1.18", "G27T", "3.10", "6.55", "3.45", "1.45"],
     ["M132D", "3.01", "5.05", "2.04", "1.42", "G25E", "2.86", "5.20", "2.34", "1.55"],
     ["★27T-30H-58M", "6.51", "8.34", "1.83", "2.16", "★27D-30H-58M", "5.05", "6.56", "1.50", "—"]],
    top=1.75, col_w=[2.4, 1.7, 1.7, 1.9, 1.9, 2.4, 1.7, 1.7, 1.9, 1.9], size=10, row_h=0.3)
add_note(s, "*K30H+Q58M 取 30H-58M 实测值。22 个突变体已全部补齐，结果写入 results/dE72_regression.csv。", top=6.6, size=10.5)

s = add_slide(); add_title(s, "P1-1 结果：回归为阴性（r ≈ 0）")
add_kpi(s, [("r = −0.073", "Pearson 相关系数", ACCENT),
            ("[−0.600, +0.498]", "95% 置信区间（横跨 0）", ACCENT),
            ("ρ = −0.044", "Spearman 秩相关", GRAY),
            ("n = 13", "有实测值的突变体", BLUE)], top=1.6, height=1.5)
add_bullets(s, [
    ("拟合式：＋1比 = −0.0246 × Δd_E72 + 1.717", 0, True, NAVY),
    ("留一交叉验证 RMSE = 0.38，预测残差均值 −0.01 → 无系统偏差，但也无预测力", 1, False, GRAY),
    ("按第一期设定的判据（r > 0.7 才采用）→ Δd_E72 不能作为组合筛选的主指标", 0, True, ACCENT),
], top=3.5, size=14)
add_note(s, "但「r ≈ 0」不等于「几何无关」—— 必须做分层与噪声诊断，才能判断是真无关还是被测量误差淹没。", top=5.75, color=TEAL)

s = add_slide(); add_title(s, "P1-1 分层真相：单点与组合走的是两套完全不同的机制")
add_table(s,
    ["分层", "n", "r", "机制解读"],
    [["全部", "13", "−0.073", "混合两类机制 → 相互抵消，表面无相关"],
     ["仅单点突变", "9", "+0.670", "单点靠「选择性几何位移」：+1=A 时靶点 C 被推离催化中心越远，特异性越高"],
     ["仅组合突变", "4", "−0.724", "组合靠「整体催化几何下调」：GCG 侧本身被推远，特异性来自活性衰减的不对称性"]],
    top=1.5, col_w=[2.4, 1.2, 1.8, 6.6], size=12)
add_sub(s, "关键反例：三点组合 Δd_E72 最小（1.83）却特异性最高（2.16）", top=4.3, size=13, color=ACCENT)
add_table(s,
    ["突变", "Δd_E72", "d_GCG（催化几何）", "实测＋1比", "本质"],
    [["K30H", "4.35", "2.78（良好）", "1.71", "真·选择性位移"],
     ["M132E", "1.92", "2.84（良好）", "1.18", "无位移 → 无特异性"],
     ["27T-30H-58M", "1.83", "6.51（退化）", "2.16", "几何整体下调 → 不对称衰减"]],
    top=4.8, col_w=[2.6, 1.8, 2.8, 2.0, 2.8], size=11, row_h=0.32)
add_note(s, "结论：不能用一个线性模型同时描述单点与组合 —— 这是第一期「加性先验失效」在几何层面的再次确认。", top=6.65)

s = add_slide(); add_title(s, "P1-1 噪声诊断：为什么几何指标会失效")
add_table(s,
    ["指标", "数值", "含义"],
    [["GCG 侧 model 间 SD", "≈ 0.25 Å", "稳定 —— GCG 复合物构象收敛"],
     ["GCA 侧 model 间 SD", "≈ 2.3 – 3.9 Å", "极不稳定 —— +1=A 复合物构象高度离散"],
     ["Δd_E72 观测方差", "0.97", "指标本身携带的真实差异"],
     ["噪声方差（5 model 均值）", "1.58", "噪声大于效应"],
     ["信度 rel = 1 − 噪声/观测", "≈ 0", "指标完全被噪声淹没"]],
    top=1.55, col_w=[4.0, 3.0, 5.0], size=12)
add_sub(s, "极端个例：WT_GCA 的 5 个 model 距离为 4.65 / 4.20 / 3.86 / 6.59 / 12.36 Å", top=4.5, size=13, color=ACCENT)
add_bullets(s, [
    ("根因：AF3 对「+1=A（脱靶态）」的预测置信度本就偏低（前期 QC：AUGCAGC 84/100 的 +1 位 pLDDT<60，中位 53.8）", 0, False, GRAY),
    ("方法学结论：该指标若要可用，必须先把 GCA 侧从 5 model 提升到 5–10 seed × 5 model，否则单条件均值不可靠", 0, True, NAVY),
], top=5.1, size=12.5)

s = add_slide(); add_title(s, "P1-2 前置澄清：三点复合物「已存在」，无需重建")
add_bullets(s, [
    ("第一期计划书写「现有 AF3 突变体只到双点」—— 实际核查发现命名即是三点：", 0, False, GRAY),
    ("g27tk30hq58m = G27T + K30H + Q58M = 27T-30H-58M", 1, True, NAVY),
    ("g27dk30hq58m = G27D + K30H + Q58M = 27D-30H-58M", 1, True, NAVY),
    ("两者 × {GCG, GCA} × 5 models 文件完整；序列已逐位验证（res27=T/D、res30=H、res58=M）", 0, False, GRAY),
    ("→ 因此直接解析这四个复合物，未重复提交 AF3（节省计算资源，且与既有 CP/ΔCP 分析同源可比）", 0, True, TEAL),
], top=1.5, size=14.5)
add_note(s, "这一步本身也说明：数据集在增长过程中需要定期重新盘点命名与实际内容，避免重复计算。", top=6.35, color=TEAL)

s = add_slide(); add_title(s, "P1-2 结果：催化几何呈单调退化梯度")
add_table(s,
    ["复合物", "C4N4–E72 均值 (Å)", "SD (Å)", "相对 WT 判读"],
    [["WT_GCG", "2.88", "0.32", "基准：催化几何良好且稳定"],
     ["27T-30H_GCG（双点）", "4.52", "2.15", "中度退化"],
     ["27D-30H_GCG（双点）", "4.77", "2.73", "中度退化"],
     ["27D-30H-58M_GCG（三点）", "5.05", "2.16", "显著退化"],
     ["★ 27T-30H-58M_GCG（三点）", "6.51", "2.71", "★ 最严重退化"],
     ["WT_GCA", "6.33", "3.16", "脱靶态本已远离"],
     ["27T-30H-58M_GCA", "8.34", "3.61", "进一步远离"]],
    top=1.5, col_w=[4.4, 2.8, 1.8, 3.0], size=11.5)
add_kpi(s, [("2.88 → 4.5 → 6.5 Å", "WT → 双点 → 三点：每叠加一个突变，靶点 C 被逐步推离催化中心", ACCENT)], top=5.35, height=1.2)
add_note(s, "这正是 27T-30H-58M「＋1比 2.16 但 on-target 保留仅 77%」的结构基础 —— 代价被精确量化。", top=6.65)

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
], top=4.4, size=13)
add_note(s, "★ 核心结论：酶没有坏 —— 锌指与催化残基结构完好；活性下降来自「底物摆不到位」而非「催化中心崩坏」。设计方向应是修「底物定位」而非换催化残基。", top=5.5, color=TEAL)

# =====================================================================
add_section("04", "综合结论与下一步", "方法学沉淀 · 不足清单 · P0/P1/P2 计划更新")

s = add_slide(); add_title(s, "综合结论：干湿互指的三条方法学沉淀")
add_table(s,
    ["#", "结论", "证据"],
    [["1", "预测可靠性分层：结构接触（谁参与）可靠；ML ΔΔG（结合强度）只可粗筛；\n几何判别指标（Δd_E72）在跨组合尺度上失效",
      "K30H/G27D/T 证实 vs M132E/T31A/A59S 证伪；P1-1 r = −0.073"],
     ["2", "单点与组合走两套机制：单点靠选择性几何位移（r=+0.67）；\n组合靠整体催化几何下调（r=−0.72）→ 线性加性模型必然失效",
      "P1-1 分层；27T-30H-58M Δd 最小却比最高"],
     ["3", "「单点保留率高」不能预测「组合安全」：真正判据是侧链物化类型\n（带电/刚性替换高风险；疏水/柔性/保守替换安全）",
      "132D/30H/27D 组合塌方；27T/25E/58M/132E 安全"]],
    top=1.5, col_w=[0.8, 6.4, 4.8], size=11)
add_kpi(s, [("2.16", "27T-30H-58M ＋1比（唯一双达标）", GREEN),
            ("77%", "on-target 保留", BLUE),
            ("6.51 Å", "其 GCG 侧催化几何代价（WT 2.88）", ACCENT)], top=4.4, height=1.4)
add_note(s, "可迁移设计规则：① 每层机制各取一个位点组成组合；② 避开带电/刚性替换进组合；③ 跨实验比较必须用同批次亲本 ROF 归一化。", top=6.2, color=TEAL)

s = add_slide(); add_title(s, "项目不足与结论级风险（按严重程度）")
add_table(s,
    ["#", "不足", "影响", "严重度"],
    [["A1", "全部组合为单剂量，无剂量梯度", "无法区分「真特异性」与「整体活性衰减」—— 可能推翻主线结论", "★★★★★"],
     ["A2", "两套实验基数不同却未记录", "此前所有跨实验比较基线取错", "★★★★★"],
     ["A3", "同批次无单点-组合头对头", "上位性无法定量计算", "★★★★"],
     ["A4", "C295(ACA) 仅 12/100 行检出", "ACA 脱靶分析基本不可用", "★★★★"],
     ["A5", "C871=0 无判读阈值", "7 组「清除」中 C388 仅 8–22%，可能是测序深度不足", "★★★"],
     ["A6", "Y32F 无单点饱和数据", "最强比提升器（Δ+0.21）仅靠组合间接推断", "★★★"],
     ["B1", "ML 工具符号相反且判反 D/E", "只能用于排除必失活方向", "★★★"],
     ["B2", "AF3 完整脱靶结构 +1 位 pLDDT 仅 66", "对阅读器残基预测不可靠（本期噪声诊断已量化）", "★★★"]],
    top=1.45, col_w=[0.8, 4.2, 6.4, 1.4], size=9.5, row_h=0.42)
add_note(s, "结论层风险：① 27T-30H-58M 的 2.16 可能是活性衰减假象（A1）；② Q58M 补偿机制不明，若为非特异性提效则全局脱靶同步升高。", top=6.05)

s = add_slide(); add_title(s, "下一步：计划更新（P1-1 / P1-2 已完成）")
add_table(s,
    ["优先级", "任务", "状态 / 为什么"],
    [["P0-1", "剂量梯度实验：27T-30H-58M 与亲本平行做 0.25×–4×，每点 n=3。\n判据：在【等 on-target 效率】下比较 ＋1比；若高剂量回落到 1.2 则特异性结论需重写",
      "⚠ 最高优先级，不可跳过；本期 132D 塌方已证明「活性代价」真实存在"],
     ["P0-2", "补做 27D-30H-58M（同构替换，27D 比 1.53 > 27T 1.45，ACA 压制强 5 倍）\n并冲击 4 点组 27D-30H-32F-58M",
      "本期已完成其结构解析：GCG 侧 5.05 Å，比 27T 版本更温和 → 预期活性更优"],
     ["P0-3", "重新定义目标阈值：短期 ≥2.5 且保留 ≥60%；治疗意义 ≥5 且全转录组脱靶不恶化",
      "避免团队把 2.16 当作终点"],
     ["P1-3", "T31A + K30H 上位性实验，收口 T31 悖论",
      "若 T31 只在 K30 存在时起作用 → 「接触≠独立功能」"],
     ["P1-1", "Δd_E72 回归", "✓ 本期已完成 → 阴性；GCA 侧需多 seed 重采样（5→5–10 seed）"],
     ["P1-2", "27T-30H-58M 结构解析", "✓ 本期已完成 → 几何梯度 + 锌配位完好"],
     ["P2", "全转录组脱靶谱 · 表达量/稳定性测定 · 独立重复 + 同批头对头",
      "发表前必须；loop1+loop3+loop7 多点突变可能引入全新脱靶位点"]],
    top=1.45, col_w=[1.1, 6.6, 4.3], size=10, row_h=0.62)

s = add_slide(); add_title(s, "总结")
add_bullets(s, [
    ("已可靠得到：", 0, True, NAVY),
    ("单点 ＋1比 存在约 1.7–1.8 的天花板（103 个突变无一突破 2.0）", 1, False, GRAY),
    ("27T-30H-58M 三点组合把 ＋1比 从 1.19 提到 2.16（ROF 1.57）同时保留 77% 活性，是全部 71 组中唯一双达标者", 1, False, GRAY),
    ("已确认无效的路线：", 0, True, NAVY),
    ("单点饱和 +1 阅读器（结构上无 GCG 特异读取器）· T31 排 A（切除氢键无效）", 1, False, GRAY),
    ("M132 作为 +1 判别子（它是出口通道）· ML 工具做特异性排序（判反 D/E）", 1, False, GRAY),
    ("本期新增结论：", 0, True, ACCENT),
    ("Δd_E72 不能作为主筛指标（r=−0.073）；但分层后揭示单点（+0.67）与组合（−0.72）两套机制", 1, False, GRAY),
    ("三点组合的催化几何代价被量化（2.88→6.51 Å），且锌配位完好 → 酶没坏，是底物摆不到位", 1, False, GRAY),
    ("「单点保留率高」不能预测组合安全 —— 判据是侧链物化类型（带电/刚性替换高风险）", 1, False, GRAY),
    ("尚未证明（决定项目成败）：", 0, True, NAVY),
    ("2.16 是否来自真正的碱基识别改变，而非整体活性衰减（→ P0-1 剂量梯度）", 1, False, GRAY),
    ("全局脱靶谱是否同步改善（→ P2 全转录组）；Q58M 的活性补偿机制", 1, False, GRAY),
], top=1.35, size=13)
add_note(s, "一句话：27T-30H-58M 仍是目前最佳候选；但「为什么好」本期已部分回答，「是否真好」仍取决于 P0-1 剂量梯度实验。", top=6.95, size=11)

# 结束页
s = add_slide()
band = s.shapes.add_shape(1, Inches(0), Inches(2.6), prs.slide_width, Inches(2.0))
band.fill.solid(); band.fill.fore_color.rgb = NAVY; band.line.fill.background()
box = s.shapes.add_textbox(Inches(1.0), Inches(2.85), Inches(11.3), Inches(1.7))
tf = box.text_frame; tf.word_wrap = True
r = tf.paragraphs[0].add_run(); r.text = "谢谢 · 请批评指正"
set_font(r, 34, True, WHITE)
p = tf.add_paragraph(); r = p.add_run()
r.text = "核心问题：P0-1 剂量梯度是否仍应作为最高优先级？（本期新增证据支持：是）"
set_font(r, 15, False, RGBColor(0xC8, 0xD6, 0xE8))
p = tf.add_paragraph(); r = p.add_run()
r.text = "决策分岔：若 2.16 主要为活性衰减产物，是否转向定向进化或更换底盘？"
set_font(r, 13, False, RGBColor(0xA8, 0xBC, 0xD8))

prs.save("APOBEC保G排A优化_组会汇报_综合稿.pptx")
print("已生成 APOBEC保G排A优化_组会汇报_综合稿.pptx，共", len(prs.slides._sldIdLst), "页")
