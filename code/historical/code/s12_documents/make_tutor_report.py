# -*- coding: utf-8 -*-
"""
生成导师阶段汇报 Word：
  「REWIRE-APOBEC Pro.hA1 —— GCG 特异性编辑的理性优化」研究思路与全部结果

用法：uv run --with python-docx python make_tutor_report.py
产出：导师汇报_APOBEC_保G排A优化_研究总结.docx
"""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = "导师汇报_APOBEC_保G排A优化_研究总结.docx"
CN = "微软雅黑"


def set_cn(r, size=10.5, bold=False, color=None, italic=False):
    r.font.name = CN
    r._element.rPr.rFonts.set(qn("w:eastAsia"), CN)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    if color:
        r.font.color.rgb = RGBColor(*color)


def para(doc, text, size=10.5, bold=False, color=None, after=5, indent=False):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Pt(21)
    r = p.add_run(text)
    set_cn(r, size, bold, color)
    p.paragraph_format.space_after = Pt(after)
    return p


def bullet(doc, text, size=10, bold=False, color=None):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text)
    set_cn(r, size, bold, color)
    p.paragraph_format.space_after = Pt(2)
    return p


def heading(doc, text, level=1):
    h = doc.add_heading("", level=level)
    r = h.add_run(text)
    set_cn(r, 16 if level == 1 else 13 if level == 2 else 11.5, bold=True,
           color=(0x1F, 0x3B, 0x66) if level == 1 else (0x2E, 0x54, 0x8B))
    return h


def table(doc, headers, rows, font=9, width_note=None):
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
    s.top_margin = Inches(0.7); s.bottom_margin = Inches(0.7)
    s.left_margin = Inches(0.85); s.right_margin = Inches(0.85)

# ===== 封面 =====
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("REWIRE 系统 APOBEC 蛋白\n「保G排A」特异性优化 —— 研究总结")
set_cn(r, 20, True, (0x1F, 0x3B, 0x66))
s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = s.add_run("目标：特异性编辑 GCG（APOE c.388）而非 GCA（c.871 脱靶）· 底盘 Pro.hA1 (CU5.1)")
set_cn(r, 11, color=(0x60, 0x60, 0x60))
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("2026-09-09 · 导师阶段汇报 · 干湿结合迭代")
set_cn(r, 9, color=(0x80, 0x80, 0x80))

# ===== 一、研究思路主线 =====
heading(doc, "一、研究思路主线（先读这一页）", 1)
para(doc, "要设计一个「多编辑 GCG、少编辑 GCA」的脱氨酶，必须先拆清三个正交问题，避免把不同问题混在一起：", 10.5)
table(doc,
      ["正交问题", "回答手段", "结论要点"],
      [["Q1 谁接触 +1 碱基？\n（结构接触）", "AF3 复合物 + 距离/氢键/埋藏面积 → 升级为 ContactSeek 式 CP/ΔCP",
        "保G：H29/K30（读 +1=G）\n排A：催化核心 N57/H70/E72/W99/C102 + T31（贴 +1=A）"],
       ["Q2 谁突变不失活？\n（进化/保守性）", "AF3 MSA(3504 同源) 保守性 + 共进化 MI + PSSM 方向",
        "催化核心/锌配位绝对保守不可动；\nK30/M132/H29/A59/Y32 可突变；T31 慎动"],
       ["Q3 谁真正做 G/A 判别？\n（只能靠实验）", "单点饱和 → 组合湿实验（EGFP+APOE 双报告）",
        "单点最高 K30H=1.71；\n组合 G27T+K30H+Q58M 破 2.0（≈2.1）"]],
      font=8.5)
para(doc, "贯穿原则（多次被实验验证/证伪后确立）：", 10, bold=True)
for b in [
    "结构接触只能定位「参与判别的残基」，不能外推活性高低；",
    "保守性/共进化回答「能不能动」，PSSM 只回答「活不活」，都不回答「辨不辨 G/A」；",
    "ML 工具（mCSM-NA/PremPRI）预测的是结合 ΔΔG 而非特异性，且符号约定相反，只能作破坏幅度粗筛；",
    "唯「接触 +1 碱基」且「可突变」且「实验 +1 比改善」三者并集，才是可靠候选 —— K30H 是唯一三者全满足的单点。",
]:
    bullet(doc, b, 10)

# ===== 二、体系与方法 =====
heading(doc, "二、体系与方法", 1)
heading(doc, "2.1 底物与模型系统", 2)
table(doc,
      ["RNA", "+1", "角色", "旧模型(300) / 新模型", "编号(编辑C=0位)"],
      [["GUGCGCG", "G", "on-target（388）", "20 seed×5 / 突变体重测", "+1=res5"],
       ["GUGCACG", "A", "纯 +1 交换对照", "同上", "+1=res5"],
       ["AUGCAGC", "A", "871 完整脱靶", "同上（+1 位 pLDDT 偏低）", "+1=res5"]],
      font=9)
heading(doc, "2.2 方法学演进", 2)
for b in [
    "① 经典几何接触（距离≤5Å / 氢键 / Shrake-Rupley 埋藏面积）→ ② ContactSeek 式 CP+ΔCP（AF3 contact_probs 直接读概率，更灵敏）→ ③ 突变体重预测验证（AF3 server 提交，14+8 突变 × GCG/GCA）。",
    "本报告新增两块空间几何分析：突变位点空间聚类（20_site_spatial.py）、靶点 C→催化中心距离（21_targetC_catalytic_dist.py）。",
]:
    bullet(doc, b, 10)

# ===== 三、核心机制结论 =====
heading(doc, "三、+1 位「保G/排A」的分子机制（结构层共识）", 1)
table(doc,
      ["残基", "功能定位", "接触 +1", "保守性", "可突变性", "最终判定"],
      [["H29", "读 +1=G（主链 π-堆叠读 Hoogsteen）", "G/A 都接触", "22%", "可突变", "保G阅读器"],
       ["K30", "读 +1=G（侧链读 Hoogsteen）", "G/A 都接触", "36%", "可突变", "保G阅读器（K30H=实验最佳单点）"],
       ["T31", "+1=A 特异氢键（OH↔A-N6）", "A 特异", "82%", "慎动", "A 偏好侧（非判别开关）"],
       ["N57/H70/E72/W99", "催化核心", "+1=A 时贴近", "67–97%", "不可动/仅特定替换", "排A接触体（禁区）"],
       ["C102/C105", "锌配位", "—", "100%", "不可动", "绝对禁区"],
       ["M132", "出口通道（距 +1 15–20Å）", "不接触", "5%", "可突变", "出口排A（影响活性非特异性）"]],
      font=8)
para(doc, "ΔCP 机制（AF3 contact_probs，WT）：ΔCP=CP(GCA)−CP(GCG)。H29(−0.41)、K30(−0.24) 为负 → 读 +1G（保G）；"
          "N57(+0.26)、H70(+0.19)、W99(+0.24)、C102(+0.27)、T31(+0.26) 为正 → 贴 +1A。", 10)

# ===== 四、突变体 CP 重测（干实验对设计的闭环） =====
heading(doc, "四、突变体的 CP 重测：从「设计」到「结构验证」的闭环", 1)
para(doc, "把 14+8 个突变（含单点与组合）重新提交 AF3 预测（GUGCGCG/GUGCACG），提取每个残基 CP 并算 ΔCP 变化。"
          "关键：同一目录内 wt 重跑与旧 100-model WT 高度一致（保G指数 −0.325 vs −0.328），证明批间可重复。", 10)
table(doc,
      ["突变", "保G指数(H29+K30 ΔCP均值)", "排A指数(催化核心均值)", "ΔCP 变化 vs WT", "实验对照"],
      [["WT", "−0.33", "+0.24", "基准", "+1比1.00"],
       ["K30H", "−0.30", "+0.27", "H29 保G增强(−0.41→−0.51)；K30 自身弱化", "+1比1.71(84%)"],
       ["Q58M", "−0.37", "+0.28", "K30 保G增强(−0.24→−0.28)，独立增强阅读", "+1比1.46(79%)"],
       ["R28A(未测)", "−0.40", "+0.31", "双向增强：H29 与催化核心均更强", "待验证→推荐优先"],
       ["T31V→L", "−0.26→+0.06", "≈+0.26", "T31 大侧链变构压塌 H29/K30（保G指数归零）", "预测 I/L 显著降活"],
       ["G27T+K30H+Q58M", "0.00", "+0.27", "保G崩塌但排A保持 → 高判别机制", "+1比≈2.1"],
       ["M132D/E", "−0.27", "+0.16", "几乎不变（出口通道，不触 +1）", "132D 1.42 / 132E 1.18"]],
      font=8.5)
para(doc, "核心解释：单点 K30H 靠「把读 G 任务转移到 H29」实现；组合不靠更强读 G，而靠「−1/+1 联合重塑 + 催化核心保持排 A」"
          "的强烈上位效应，这正是它能把 +1 比推过 2.0 而单点做不到的原因。", 10)

# ===== 五、新分析① 突变位点空间聚类 =====
heading(doc, "五、新分析①：突变位点空间距离聚类", 1)
para(doc, "问：我们改的这么多位点，哪些在三维空间上彼此靠近（可能共享口袋/构象偶联）？"
          "方法：用 WT 结构（GUGCGCG_20，20 rank0 模型均值）计算两两 Cα 与最小重原子距离，按功能区划分后找跨区段空间桥梁（≤8 Å）。", 10)
table(doc,
      ["功能区（位点）", "含突变", "距 +1/催化 的空间关系"],
      [["loop1-N(25-28)", "25E、26D、27D/T/V/I、28A/S", "与 W-S 环 W99 强接触（27→99:3.6Å、28→99:2.9Å）"],
       ["+1 阅读器(29-32)", "29、30H、31V/I/L、32F", "直接贴 +1 碱基；31→N57:2.9Å、30→N57:3.4Å"],
       ["loop3(57-60)", "57(禁区)、58M、59P、60R", "贴催化 H70（57→70:4.1Å、58→70:5.0Å）"],
       ["W-S 环(98-99)", "98A、99(保守)", "居口袋中央，被 loop1/阅读器/loop7 三面包围"],
       ["loop7/出口(129-133)", "130G(探针)、132D/E", "129 紧贴催化核心 C102(3.7Å)/H70(5.1Å) → M132 虽远离 +1 但处于催化核旁支路"]],
      font=8.5)
para(doc, "结构结论：被关注的功能 loop（25-32、57-60、98-99、129-133）在三维上并非彼此独立，而是缠绕在同一个"
          "「活性位点口袋」周围、以催化核心（N57/H70/E72/C102/C105）为共同的物理中心。", 10, bold=True)
para(doc, "空间桥梁明细（跨区段 minatom ≤ 8Å，完整 60+ 对见 results/mutation_site_spatial_distances.csv）：", 10)
table(doc,
      ["位点对(跨区)", "Cα(Å)", "minatom(Å)", "生物学含义"],
      [["28(loop1)→99(W-S)", "8.9", "2.9", "R28 与保守 W99 芳香/范德华接触 → 28 突变可能扰动催化侧"],
       ["31(reader)→57(loop3)", "5.7", "2.9", "T31 与催化必需 N57 极近 → 31 大侧链突变可挤 N57"],
       ["30(reader)→57/99", "6.5/8.4", "3.4/3.3", "K30 同时邻接 N57 与 W99，读 G 与催化一线之隔"],
       ["129→99 / 102", "5.4/6.7", "3.6/3.7", "loop7 起点贴 W99 与锌配位 C102"],
       ["57(loop3)→70(催化)", "4.6", "4.1", "loop3 与锌配位 H70 直接邻接"]],
      font=8.5)
para(doc, "与实验的对照：", 10, bold=True)
for b in [
    "「空间靠近」的位点间确实表现出耦合：G27T(loop1) 组合 K30H(阅读器) 后 H29/K30 的 ΔCP 被彻底改写（保G崩塌）——这与两者都贴 W99 同一口袋的结构一致。",
    "但「空间近 ≠ 必然影响整体活性」：M132 距 +1 达 15–20Å，仅与催化核外围(129 桥)间接相连，故 132D 只温和改变 +1 比(1.42)而保留 89% 活性；反之同属近邻的 T31I/L 因直接挤 N57/W99 邻位，预测活性损失更大。",
    "因此：空间聚类只提示「哪些突变可预期发生构象偶联、宜成组做组合」，是否真正影响整体活性，仍只能靠对应组合的湿实验逐条确认（本阶段已逐条测，见 §六）。",
]:
    bullet(doc, b, 9.5)

# ===== 六、新分析② 靶点C到催化中心距离 =====
heading(doc, "六、新分析②：靶点 C(0) 到催化中心 E72 的距离", 1)
para(doc, "问：被编辑的 C(0)（脱氨原子 C4/N4）到催化谷氨酸 E72 羧基的距离，是否被突变改变？"
          "该距离是「能否被脱氨」的一级几何判据：C 必须贴近 E72 才可被催化。", 10)
para(doc, "WT 基线（5 model 均值）：GCG（on-target）= 2.88 Å —— 靶 C 精确停靠催化位；"
          "GCA（+1=A）= 6.33 Å —— 靶 C 明显更远离催化位。这一差异本身就构成「天然偏好 GCG」的几何基础。", 10, bold=True)
table(doc,
      ["突变", "GCG 下 C→E72 (Å)", "GCA 下 C→E72 (Å)", "vs WT 判读", "实验对照"],
      [["WT", "2.88", "6.33", "基准", "+1比 1.37(WT)"],
       ["K30H", "2.78", "7.13", "GCG 不动，GCA 更远 → 强化排A 不伤G", "+1比 1.71(84%)"],
       ["K30H+Q58M", "2.68", "7.64", "同上，排A 再增强", "组合优"],
       ["G27T+K30H+Q58M", "6.51", "8.34", "GCA 更远(排A↑)；但 GCG 也被推远 → 解释 on-target 略降", "+1比≈2.1(77%)"],
       ["G27T / G27D", "3.10/3.18", "6.55/6.59", "≈WT（-1 位效应不体现在 C-E72 几何）", "+1比 1.45/1.53"],
       ["M132D/E", "3.01/2.84", "5.05/4.76", "GCG≈WT；GCA 反而更近 → 出口残基不直接作用于 C-E72", "132D 1.42"],
       ["T31I / T31L", "5.07/5.70", "6.17/7.89", "GCG 下 C 被挤离催化 E72 → 预测 on-target 活性受损", "预测 I/L 降活"]],
      font=8.5)
para(doc, "解读（重要边界）：", 10, bold=True)
for b in [
    "此几何指标能解释「为何 K30H 保活性又排 A」（GCG 不动、GCA 推远），也能解释组合 on-target 保留率下降（GCG 被推远至 6.5Å）。",
    "但它不解释 M132D/E、Q58M 这类出口通道/间接残基的特异性 —— 它们不改变 C→E72 几何，特异性来自产物释放或口袋间接重塑。说明「C→催化距离」只刻画「停靠/催化」这一条轴，不是全部机制。",
    "数据基于每个条件 5 个 AF3 model，是预测结构的几何推论，非实验证据；±0.7Å 以内差异视为噪声。",
]:
    bullet(doc, b, 9.5)

# ===== 七、湿实验验证汇总 =====
heading(doc, "七、湿实验验证：干预测可靠性的诚实评估", 1)
heading(doc, "7.1 第一批单点饱和（round 1）", 2)
table(doc,
      ["突变", "+1比(GCG/GCA)", "on-target保留", "判定"],
      [["K30H", "1.71", "84%", "最优单点：接触+可突变+实验一致 ✓"],
       ["G25E", "1.55", "89%", "意外强（我此前低估）✓"],
       ["G27D", "1.53", "88%", "压 ACA 最强 ✓"],
       ["Q58M", "1.46", "79%", "意外强（原排除，实为排A）✓"],
       ["G27T", "1.45", "98%", "高保留 ✓"],
       ["M132D", "1.42", "89%", "出口排A ✓"],
       ["M132E", "1.18", "83%", "PremPRI 判反（实验 D>>E）✗"],
       ["T31A", "1.32", "97%", "「T31 排A」假说撤回（结构接触≠功能）✗"],
       ["A59S / R28W", "1.33/1.32", "74%/94%", "ML 高估 ✗"]],
      font=8.5)
heading(doc, "7.2 组合湿实验（round 2，含对照）", 2)
table(doc,
      ["组合", "C388(GCG)", "C871(GCA)", "GCG/GCA", "要点"],
      [["G27T+K30H+Q58M(45/b45)", "0.524/0.516", "0.247/0.235", "≈2.1–2.2", "组合最高，破 2.0"],
       ["G27T+K30H(早期模型预期高)", "—", "—", "—", "组合优于任一单点 → 上位效应证实"]],
      font=8.5)
para(doc, "注：组合 xlsx 无独立 WT 行，比值用同表 C388/C871；具体保留率以同批次内 WT 对照为准（既有报告口径 77%）。", 9, color=(0x80,0x80,0x80))

heading(doc, "7.3 方法可靠性总表（多次迭代后的结论）", 2)
table(doc,
      ["预测手段", "可靠回答", "不可靠之处", "定位"],
      [["结构接触（距离/氢键）", "谁接触 +1、G/A 差异方向", "不能外推活性/绝对特异性", "定位残基"],
       ["CP / ΔCP（ContactSeek）", "突变如何重塑判别网络（H29/K30 角色、M132 无影响）", "绝对值无物理活性含义、单点排序可能失真", "机制判别"],
       ["保守性(3504 MSA)", "能不能动（禁/慎/可变）", "不辨方向与特异性", "活性筛"],
       ["共进化 MI", "与催化核耦合强弱（N57 最高）", "固定位点 MI=0，整体信号弱", "辅助"],
       ["PSSM", "朝哪些方向突变会失活（T31→D 0%）", "预测活性≠特异性；无法穷举创造性突变(K30H)", "排除必失活"],
       ["mCSM-NA / PremPRI", "结合 ΔΔG（保G破坏幅度）", "预测结合强度≠特异性；两工具方向相反；D/E 判反；低估 K30H", "粗筛"],
       ["C→催化中心距离(本报告)", "底物 C 是否精确停靠催化位(GCG 2.9 vs GCA 6.3)", "不覆盖出口通道/间接残基机制", "几何停靠轴"]],
      font=8)

# ===== 八、候选与下一步 =====
heading(doc, "八、最终推荐与下一步方向", 1)
heading(doc, "8.1 推荐（以实验为准）", 2)
for b in [
    "单点锚点（均已实验证实）：K30H(+1比1.71)、G27D/T(压ACA)、M132D(出口)、G25E、Q58M。",
    "组合主推：G27T+K30H+Q58M —— 目前唯一破 2.0 的组合（≈2.1），机制为「-1/+1 联合重塑 + 催化核心保持排A」。",
    "新增强候选（CP+空间距离推荐，尚未湿实验）：R28A（保G与排A双向增强、且贴保守 W99，风险与潜力并存，建议单点优先补测）。",
    "T31 系列判定：T31V 可测（≈WT 几何），T31I/L 预测显著伤 on-target（GCG 下 C 被推离催化位至 5.1–5.7Å）——若验证即证实「空间位阻 → 变构失活」模型。",
]:
    bullet(doc, b, 10)
heading(doc, "8.2 方法学下一步建议", 2)
for b in [
    "多 seed 重测以压噪：目前每条件仅 5 model，关键突变建议 5–10 seed × 5 model 复测 CP 与 C-E72 距离。",
    "把「C→催化停靠距离」做成可计算打分并入组合筛选（与 CP 正交）。",
    "用共进化对（如 27-30、30-99、129-102）指导下一代组合，比穷举更高效。",
    "组合已实证可破 2.0，下一目标可聚焦定向进化 + 结构启发的 R28A/Q58M 双点叠加，向 ≥2.5 推进。",
]:
    bullet(doc, b, 10)

heading(doc, "附：新分析交付文件", 1)
table(doc,
      ["文件", "内容"],
      [["results/mutation_site_spatial_distances.csv", "突变位点两两 Cα/最小重原子距离（20 模型均值）"],
       ["results/mutation_site_cross_region_bridges.csv", "跨功能区空间桥梁（≤8Å）"],
       ["results/targetC_catalytic_dist_summary.csv", "各 WT/突变 × GCG/GCA 靶 C→催化中心距离"],
       ["results/mut_cp_summary_保G排A_合并.csv", "14+8 突变 CP/ΔCP 汇总（保G/排A指数）"]],
      font=9)

doc.save(OUT)
print(f"已生成 {OUT}")
