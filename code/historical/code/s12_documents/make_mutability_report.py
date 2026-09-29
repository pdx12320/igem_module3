# -*- coding: utf-8 -*-
"""
生成 Word 版「可突变性与突变方向分析」实验报告
用法：uv run --with python-docx python make_mutability_report.py
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

CN = "微软雅黑"


def set_cn(r, size=10.5, bold=False, color=None):
    r.font.name = CN
    r._element.rPr.rFonts.set(qn("w:eastAsia"), CN)
    r.font.size = Pt(size)
    r.font.bold = bold
    if color:
        r.font.color.rgb = RGBColor(*color)


def para(doc, text, size=10.5, bold=False, color=None, after=6, indent=False):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Pt(21)
    r = p.add_run(text)
    set_cn(r, size, bold, color)
    p.paragraph_format.space_after = Pt(after)
    return p


def heading(doc, text, level=1):
    h = doc.add_heading("", level=level)
    r = h.add_run(text)
    set_cn(r, 16 if level == 1 else 12.5 if level == 2 else 11,
           bold=True, color=(0x1F, 0x3B, 0x66) if level == 1 else (0x2E, 0x54, 0x8B))
    return h


def table(doc, headers, rows, font=9.5):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        set_cn(r, font, True, (0xFF, 0xFF, 0xFF))
    for row in rows:
        cs = t.add_row().cells
        for i, v in enumerate(row):
            cs[i].text = ""
            r = cs[i].paragraphs[0].add_run(str(v))
            set_cn(r, font)
    return t


doc = Document()
for s in doc.sections:
    s.top_margin = Inches(0.8); s.bottom_margin = Inches(0.8)
    s.left_margin = Inches(0.9); s.right_margin = Inches(0.9)

# 标题
tp = doc.add_paragraph(); tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = tp.add_run("可突变残基的「突变方向」分析\n实验报告")
set_cn(r, 17, True, (0x1F, 0x3B, 0x66))
sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sp.add_run("APOBEC（Pro.hA1）+1 位「保G排A」优化 · 接触类型 × 保守性/共进化 × PSSM × 湿实验验证")
set_cn(r, 10.5, color=(0x60, 0x60, 0x60))

# 摘要
heading(doc, "摘要", 1)
para(doc, "本报告回答一个核心问题：在确定某残基「同源上可突变」之后，如何判断它朝哪些氨基酸方向突变是允许的、哪些方向会导致失活。"
          "工作分四步：① 用原始结构文件区分接触的侧链/主链、碱基/糖磷酸；② 用 AlphaFold3 返回的 MSA（约 3500 条同源序列）计算每个位点的保守性与共进化程度；"
          "③ 用 MSA 的位点氨基酸分布（PSSM）给出「允许/禁止」的突变方向；④ 用 102 个湿实验突变逐条验证 PSSM 预测的可信度。"
          "结果：PSSM 对物化约束强的核心/口袋/出口位点精确率 71%，但对溶剂暴露的 loop1 位点（25/26/27/28）精确率仅 9%，整体准确率 52%，"
          "说明「进化频率」只能部分代理「失活」的真实机制——失活主要由突变引入的电荷/大芳香/无侧链等物化性质与局部环境的失配决定。", after=8)

# 一、研究目的
heading(doc, "一、研究目的（做了什么）", 1)
para(doc, "前期工作已经通过接触分析 + 保守性分析，判断了「哪些位点能否突变」。但遗留了一个更细致的问题：", indent=True)
para(doc, "1）接触到底发生在侧链还是主链、对象是碱基还是糖/磷酸骨架——这决定了接触是否「可设计」；", indent=True)
para(doc, "2）「同源可突变」只说明位点身份可变，却没有回答「朝哪些氨基酸方向可变」——例如 T31 突变为 D 大幅失活、突变为 A/C 不失活；", indent=True)
para(doc, "3）同源分析显示 M132 高度可变，但实验上 132 全系列结果都不理想，这需要进一步解释。", indent=True)
para(doc, "因此本研究尝试：在「可突变」的前提下，用 MSA 位点氨基酸分布回答「哪些方向可变、哪些方向不可变」，并用湿实验逐条检验该方法的可信度。", indent=True)

# 二、方法
heading(doc, "二、方法（怎么做的）", 1)

heading(doc, "2.1 接触类型分解（侧链/主链 × 碱基/糖磷酸）", 2)
para(doc, "直接用 300 个 AlphaFold3 原始结构文件（ModelCIF）解析原子：将蛋白原子分为侧链（非 N/CA/C/O）与主链（N/CA/C/O），"
          "将 RNA 的 +1 核苷酸原子分为碱基（嘌呤环 N/C/O）、糖（C1'–O5'）、磷酸（P/OP1/OP2）。"
          "对每个残基统计它与 +1 碱基/糖/磷酸的接触频率（≤5 Å），据此区分「侧链-碱基特异接触（可设计）」与「主链接触（结构性，改不动）」。" )

heading(doc, "2.2 可突变性分析（保守性 + 共进化）", 2)
para(doc, "用 AlphaFold3 返回的同源多序列比对（MSA，约 3500 条 APOBEC 家族序列，a3m 格式）计算每个位点的："
          "① 保守性——野生型残基频率与归一化香农熵（低熵 = 保守）；② 共进化——与催化核心（N57/H70/E72/C102/C105）的互信息（MI，高 = 功能耦合）。")

heading(doc, "2.3 突变方向分析（PSSM 序列谱）", 2)
para(doc, "对每个位点，统计 MSA 中 20 种氨基酸各自的出现频率，构成位置特异性评分矩阵（PSSM）。"
          "将频率 ≥1% 的氨基酸方向判为「允许方向」（进化已验证可行），频率 <1% 判为「禁止方向」（进化已排除，通常导致失活）。")

heading(doc, "2.4 湿实验验证", 2)
para(doc, "将 PSSM 预测与 102 个单点饱和湿实验突变逐条比对。实验以 GCG_388 编辑保留率 ≥50% 判「活性」、<50% 判「失活」，"
          "PSSM 以家族频率 ≥1% 判「允许」。构建混淆矩阵，计算整体准确率、以及「禁止方向→失活」的精确率与召回率，并按位点类型分层统计。")

# 三、结果
heading(doc, "三、结果（结果如何）", 1)

heading(doc, "3.1 接触类型：H29 靠主链读碱基，催化核心靠侧链", 2)
para(doc, "接触类型分解结果（A-swap 结构，频率 0–1）：")
table(doc,
      ["残基", "侧链-碱基", "主链-碱基", "侧链-糖磷", "主链-糖磷", "接触性质"],
      [["H29", "0.05", "0.94", "0.81", "1.00", "主链读碱基（结构性）"],
       ["K30", "0.64", "1.00", "0.68", "0.76", "侧链+主链混合"],
       ["T31", "1.00", "1.00", "0.03", "0.20", "侧链-碱基特异"],
       ["N57", "1.00", "0.26", "0.99", "0.77", "纯侧链-碱基特异（催化）"],
       ["H70", "1.00", "0.88", "0.12", "0", "纯侧链-碱基特异（催化）"],
       ["E72", "0.92", "0", "0", "0", "纯侧链-碱基特异（催化）"],
       ["W99", "0.90", "0.04", "0", "0", "纯侧链-碱基特异（保守 Trp）"]])
para(doc, "结论：H29 读 +1 碱基主要靠主链（94%）、侧链仅占 5%，因此其侧链身份不重要；N57/H70/E72/W99 是纯侧链-碱基特异接触，是催化核心。", after=8)

heading(doc, "3.2 可突变性：T31 高保守、N57 与活性中心共进化", 2)
table(doc,
      ["分级", "残基（WT 频率）"],
      [["不可动（>90% 保守）", "H70(97%)、E72(95%)、C102(100%)、C105(100%)、S98(91%)"],
       ["慎动（70–90%）", "G27(82%)、R28(84%)、T31(82%)、W99(74%)"],
       ["可突变（<70%）", "H29(22%)、K30(36%)、Y32(56%)、N57(67%)、A59(16%)、M132(5%)、W130(3%)"]])
para(doc, "这解释了 31 与 57 为何不可动：T31 保守性高达 82%（功能必需）；N57 保守性略低（67%），但与催化核心的共进化互信息最高（MI = 0.30），"
          "说明其与活性中心功能耦合，不可随意突变。", after=8)

heading(doc, "3.3 突变方向：T31 的 PSSM 完美预测失活方向", 2)
para(doc, "T31 的家族氨基酸分布为 T82% S6% V6% C3% A2%，其余（D/E/K/R/Y/W/F/G）均 <1%。与湿实验逐条对照：")
table(doc,
      ["突变", "家族频率", "实验 GCG", "判定"],
      [["T31A（Ala）", "2%", "0.50", "活性 ✓"],
       ["T31C（Cys）", "3%", "0.51", "活性 ✓"],
       ["T31V（Val）", "6%", "—（未测）", "预测活性"],
       ["T31D（Asp）", "0%", "0.00", "失活 ✓"],
       ["T31G（Gly）", "<1%", "0.07", "大部分失活 ✓"],
       ["T31Y（Tyr）", "0%", "0.00", "失活 ✓"]])
para(doc, "PSSM 的「允许/禁止」方向与实验失活模式完全吻合：T31 只能朝小侧链（A/C/V/I/S）方向突变，"
          "朝带电（D/E）、大芳香（Y/W/F）、无侧链（G）方向突变即失活。", after=8)
para(doc, "各候选位点的允许/禁止方向（PSSM 前 5）：")
table(doc,
      ["位点", "允许方向", "禁止方向"],
      [["T31", "T/S/V/C/A（小）", "D/E/K/R/Y/W/F（带电/大）"],
       ["N57", "N/D/S/G/K", "M/R/W/Y/F（大/带电）"],
       ["K30", "E/K/T/Q/R", "D/Y/W/F（大芳香/负电）"],
       ["Q58", "K/Q/E/R/N", "疏水大"],
       ["M132", "E/W/Q/M/D", "A/F/G/R（小/芳香混合）"]])

heading(doc, "3.4 PSSM 可信度：核心位点有效、loop 暴露位点失效", 2)
para(doc, "用 102 个湿实验突变逐条验证 PSSM，整体结果：")
table(doc,
      ["指标", "数值"],
      [["总突变数", "102"],
       ["准确率", "52%（≈随机）"],
       ["精确率（禁止方向→失活）", "38%"],
       ["召回率（真失活中被命中）", "68%"]])
para(doc, "按位点类型分层后差异显著：")
table(doc,
      ["位点类型", "突变数", "准确率", "精确率(禁止→失活)", "召回率"],
      [["核心/口袋/出口（30/31/57/58/60/98/130/131/132）", "54", "65%", "71%", "65%"],
       ["loop1 暴露（25/26/27/28）", "48", "38%", "9%", "100%"]])
para(doc, "即：PSSM 对物化约束强的核心位点中等有效（精确率 71%），但对溶剂暴露的 loop1 位点几乎失效（精确率 9%）。"
          "例如 G27 在家族中 82% 为 Gly（PSSM 判多数方向「禁止」），但实验上 G27→I/T/Q/P/V/M/K/H/F/E 全部保持活性（保留 64–100%）。", after=8)

# 四、解决了哪些问题
heading(doc, "四、解决了哪些问题", 1)
for t in [
    "1. 区分了「接触类型」：通过侧链/主链 × 碱基/糖磷酸的分解，明确了哪些接触是可设计的（侧链-碱基特异）、哪些是结构性的（主链接触，如 H29 靠主链读碱基）。",
    "2. 解释了「哪些位点不可动」：T31 因高保守性（82%）不可动；N57 因与活性中心共进化程度高（MI 0.30）不可动；H70/E72/C102/C105/S98 因 >90% 保守而不可动。",
    "3. 建立了「突变方向」的理论框架：用 MSA 的位点氨基酸分布（PSSM）给出「允许/禁止」方向，并能解释 T31→D/Y/G 失活、→A/C 活性这类具体现象。",
    "4. 量化了 PSSM 方法的可信度：明确了它在核心位点（精确率 71%）与溶剂暴露位点（精确率 9%）上的适用边界。",
]:
    para(doc, t, indent=True)

# 五、尚未解决的问题
heading(doc, "五、还有哪些问题无法解决", 1)
for t in [
    "1. 溶剂暴露位点的失活方向无法用 PSSM 预测：loop1 位点（25/26/27/28）精确率仅 9%。这些位点分子暴露度高、受实验环境影响大，"
    "进化上的保守性（如 G27 82% Gly）反映的是进化共识而非功能约束，因此「进化频率」与「失活」脱钩。",
    "2. M132 的悖论未解决：同源分析显示其高度可变（5% Met，允许 E/W/Q/M/D 等），但实验上 132 全系列都不理想（132D +1 比仅 1.42、132E 1.18、其余失活）。"
    "原因是 M132 位于出口通道（距 +1 碱基 15–20 Å），改变它只影响整体活性/产物释放，无法实现 +1 特异性——「可突变」与「可做 +1 特异性」是两件正交的事，本框架尚不能预测特异性。",
    "3. PSSM 作为「失活方向」预测器整体不可靠（准确率 52% ≈ 随机），因为失活主要由「突变引入的电荷/大芳香/无侧链与局部环境（磷酸骨架/紧凑口袋）的失配」决定，"
    "而非进化频率本身。要真正预测失活方向，需要建立「物化性质匹配 + 结构 clash/静电分析」的打分器，这部分尚未实现。",
    "4. 本研究只验证了「活性/失活」这一维度的方向，尚未把「+1 特异性（保G排A）」纳入同一框架；活性与特异性是两个正交问题，仍需分别处理。",
]:
    para(doc, t, indent=True)

# 六、结论
heading(doc, "六、结论", 1)
para(doc, "本研究建立了一套「可突变性 → 突变方向」的量化分析流程：接触类型分解（结构）→ 保守性/共进化（进化）→ PSSM 突变方向（序列谱）→ 湿实验验证。"
          "结果显示：PSSM 对物化约束强的核心位点有效（精确率 71%），对溶剂暴露位点失效（9%），整体准确率仅 52%。"
          "这说明「进化频率」只能部分代理「失活」机制——失活的真正原因是突变引入的电荷/大芳香/无侧链与局部环境的物化失配。"
          "未来应以「物化性质匹配 + 结构 clash 分析」取代 PSSM 频率来预测突变方向。", indent=True)

doc.save("可突变性与突变方向分析_实验报告.docx")
print("已生成：可突变性与突变方向分析_实验报告.docx")
