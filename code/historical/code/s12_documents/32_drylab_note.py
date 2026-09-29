# -*- coding: utf-8 -*-
"""
生成《干实验记录（Dry-lab Note）》
时间轴依据：工作目录内脚本与产出文件的真实修改时间戳（客观证据）
用法：uv run --with python-docx python 32_drylab_note.py
产出：干实验记录_APOBEC保G排A优化.docx
"""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = "干实验记录_APOBEC保G排A优化.docx"
CN = "微软雅黑"

def set_cn(r, size=10.5, bold=False, color=None):
    r.font.name = CN
    r._element.rPr.rFonts.set(qn("w:eastAsia"), CN)
    r.font.size = Pt(size); r.font.bold = bold
    if color: r.font.color.rgb = RGBColor(*color)

def para(doc, text, size=10.5, bold=False, color=None, after=4, indent=False):
    p = doc.add_paragraph()
    if indent: p.paragraph_format.first_line_indent = Pt(21)
    r = p.add_run(text); set_cn(r, size, bold, color)
    p.paragraph_format.space_after = Pt(after)
    return p

def bullet(doc, text, size=10, bold=False):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text); set_cn(r, size, bold)
    p.paragraph_format.space_after = Pt(2)

def heading(doc, text, level=1):
    h = doc.add_heading("", level=level)
    r = h.add_run(text)
    set_cn(r, 15 if level == 1 else 12.5 if level == 2 else 11, bold=True,
           color=(0x1F,0x3B,0x66) if level == 1 else (0x2E,0x54,0x8B))
    return h

def table(doc, headers, rows, font=9):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Light Grid Accent 1"
    for i,h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ""
        r = c.paragraphs[0].add_run(h); set_cn(r, font, True, (0xFF,0xFF,0xFF))
    for row in rows:
        cs = t.add_row().cells
        for i,v in enumerate(row):
            cs[i].text = ""
            r = cs[i].paragraphs[0].add_run(str(v)); set_cn(r, font)
    return t

doc = Document()
for s in doc.sections:
    s.top_margin = Inches(0.7); s.bottom_margin = Inches(0.7)
    s.left_margin = Inches(0.8); s.right_margin = Inches(0.8)

t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("干实验记录（Dry-lab Note）"); set_cn(r, 19, True, (0x1F,0x3B,0x66))
s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = s.add_run("REWIRE 系统 APOBEC「保 G 排 A」优化 · Pro.hA1 (199 aa)")
set_cn(r, 11, color=(0x60,0x60,0x60))
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("记录周期：2026-08-18 — 2026-09-12　｜　记录依据：工作目录内脚本与产出文件的真实修改时间戳")
set_cn(r, 9, color=(0x80,0x80,0x80))

heading(doc, "〇、说明", 1)
para(doc, "1. 本记录按真实时间轴（文件系统时间戳，精确到分钟）整理，覆盖从环境搭建到最新一轮湿实验突变清单的全部干实验工作。", 10)
para(doc, "2. 每条记录三要素：做了什么（脚本/分析）、得到什么结果、产出文件。", 10)
para(doc, "3. 项目目标：改造 APOBEC 使其在 +1 位偏好读 G（保 APOE c.388，GCG）而排斥 A（抑 c.871，GCA）。", 10)
para(doc, "4. 数据规模：AF3 复合物 300 个（3 组 RNA × 20 seed × 5 model）+ 突变体 22 个 × 2 底物 × 5 model；单点饱和 102 个；组合突变 71 组（a/b 重复）；同源 MSA 3504 条。", 10)

heading(doc, "一、总览时间轴", 1)
table(doc,
    ["日期", "主要工作", "关键产出", "核心结果"],
    [["08-18 ~ 08-26", "（湿实验与前期设计文档，非本次干实验）", "实验报告/实验计划/组合突变表/前期设计",
      "为后续干实验提供底盘与实验背景"],
     ["09-01", "环境搭建 + 结构质控 + 接触分析 + 互作分析 + 组合生成 + ML 工具重排",
      "af_utils.py、00–08 脚本、5 份 md 报告", "H29/K30 读 +1=G；催化核心在 +1=A 时贴近；**新发现 T31 为 A 特异氢键残基**；M132D/E 两工具一致"],
     ["09-02", "干预测与湿实验交叉验证 + 接触分解 + 保守性/共进化 + PSSM 突变方向",
      "09–14 脚本、3 份报告、可突变性与突变方向分析.docx", "**T31A 与 M132E 被实验证伪**；PSSM 核心位点 71% / 溶剂暴露位点 9%（整体 52%）；确立「接触≠功能」「ML 只做粗筛」"],
     ["09-04 ~ 09-05", "组会 PPT 制作 + RNA-seq 找最强脱靶 + 引入 CP/ΔCP 新方法",
      "两份 PPT、02_find_CU_offtarget.py、15_cp_dcp_analysis.py", "确定脱靶位点检索流程；建立 ContactSeek 式 CP+ΔCP 分析"],
     ["09-08", "11nt 模型复现 + 纯 +1 交换验证 + 生成 AF3 提交文件 + 突变体 CP 分析",
      "16–19 脚本、af3_submit/（44 个 JSON）", "新 11nt 模型与旧 7nt 结论一致；突变体 CP 可重复"],
     ["09-09", "突变位点空间聚类 + 靶点 C 到催化中心距离 + 最佳位点对筛选 + 导师汇报",
      "20–22 脚本、导师汇报.docx、组合结果整理表", "**所有功能 loop 缠绕成单一活性口袋**；WT 靶点 C→E72 = 2.88 Å vs GCA 6.33 Å；输出 Tier 分级位点对"],
     ["09-10", "全量证据整合 + 第一期组会 PPT + Δd_E72 回归 + 锌配位完整性",
      "23_integrate_all.py、四张主表、第一期 PPT、dE72_regression.csv", "**单点天花板 1.71**；**27T-30H-58M = 2.16 / 保留 77%（唯一双达标）**；Δd_E72 回归 r=−0.073"],
     ["09-11 ~ 09-12", "第二期 PPT + 综合稿合并 + 总体脱靶筛查 + GCG 靶点重定义 + 湿实验清单",
      "24–31 脚本、脱靶矩阵/热图、GCG 排序图、湿实验突变清单.xlsx",
      "**亲本有 63 个脱靶位点**；390 与 871 并列为主要脱靶；P 系列引入 28 个全新脱靶；新候选 R28A、26N+K30H、27D-30H-58M"]],
    font=8.5)

heading(doc, "二、逐日详情", 1)

heading(doc, "2026-09-01（16:26 – 19:54）环境搭建与首轮结构分析", 2)
bullet(doc, "16:26–16:50　建立共享分析模块 af_utils.py（cif 解析、原子筛选、最小距离）；完成 300 个 AF3 结构的清单与质控（00_manifest.py、01_qc.py）。")
bullet(doc, "结果：300 个 model 全部可用；AUGCAGC（完整脱靶）84/100 的 +1 位 pLDDT<60（中位 53.8），提示脱靶态建模置信度偏低——此点在 09-10 的回归分析中成为关键制约。")
bullet(doc, "17:03–17:15　+1 位接触分析（02_contacts.py、03_summary.py）与距离分布图；单点+组合方案生成（05_combinations.py：24 单点 → 1902 组 → 筛后前 1000）。")
bullet(doc, "结果：+1=G 由 H29/K30 读取；+1=A 时碱基摆向 H70/E72/W99 催化核心。")
bullet(doc, "17:07　互作分析（04_interactions.py：氢键 + Shrake-Rupley 埋藏面积）。")
bullet(doc, "结果：**新发现 T31 是 A 特异氢键残基**（GCA 中频率 1.00、GCG 中 0.00）。该假说在 09-02 被实验证伪。")
bullet(doc, "17:40–19:54　cif→pdb 转换（供在线工具）、mCSM-NA 与 PremPRI 提交与重排序。")
bullet(doc, "结果：M132D/E 在两工具中一致「保G排A」；输出《最终突变汇选报告》。")

heading(doc, "2026-09-02（11:27 – 18:12）干湿交叉验证与方法学框架建立", 2)
bullet(doc, "11:27–11:43　生成《完整工作报告》docx；用 102 个单点饱和湿实验数据反查干预测（09_experimental_validation.py）。")
bullet(doc, "结果：**K30H 1.71/84%（最佳单点）被证实**；G27D 1.53、G27T 1.45、M132D 1.42 证实；**T31A 1.32（无改善）与 M132E 1.18（差于 D）被证伪**，直接推翻 09-01 的 T31 假说与 PremPRI 对 D/E 的偏好。")
bullet(doc, "14:25–14:28　接触类型分解（10_contact_decomposition.py：侧链/主链 × 碱基/糖磷酸）。")
bullet(doc, "结果：H29 读碱基靠主链（94%，侧链仅 5%）；N57/H70/E72/W99 为纯侧链-碱基特异接触。")
bullet(doc, "14:26　保守性与共进化（11_conservation_coevolution.py，3504 条同源）。")
bullet(doc, "结果：H70/E72/C102/C105/S98 >90% 保守（不可动）；T31 82%、G27 82%、R28 84%（慎动）；K30 36%、H29 22%、M132 5%（可突变）；N57 与催化核心共进化 MI 最高（0.30）。")
bullet(doc, "15:06–15:14　突变方向 PSSM 分析并做湿实验验证（12、13 脚本）。")
bullet(doc, "结果：PSSM 对物化约束强的核心位点准确率 71%，对溶剂暴露的 loop 位点仅 9%，整体 52%；T31→D/E/Y（家族频率 0%）实验确实失活，机制为「电荷/大侧链与口袋失配」。")
bullet(doc, "18:12　共进化组合位点筛选（14_coevolution_combo.py），产出 351 对 MI 表。")
bullet(doc, "结果：25–30 MI 1.07（最高）、30–58 0.77、30–31 0.87 → 为后续组合设计提供进化依据。")

heading(doc, "2026-09-04 ~ 09-05（20:13 / 01:29 / 10:43 / 16:39 / 20:19）汇报产出与 CP/ΔCP 方法引入", 2)
bullet(doc, "09-04 20:13 与 09-05 01:29、10:43　组会 PPT 制作（含文献借鉴版）。")
bullet(doc, "09-05 16:39　从 RNA-seq 数据检索编辑最强的脱靶位点（02_find_CU_offtarget.py）。")
bullet(doc, "09-05 20:19　引入 ContactSeek 式 CP+ΔCP 分析（15_cp_dcp_analysis.py），以 AF3 contact_probs 替代距离接触。")
bullet(doc, "结果：确立 ΔCP = CP(GCA) − CP(GCG)；负值 = 读 +1G（保G），正值 = 贴 +1A（排A），为后续突变体机制判别提供统一指标。")

heading(doc, "2026-09-08（14:26 – 23:40）模型复现、AF3 提交与突变体 CP 分析", 2)
bullet(doc, "14:26–16:15　11nt 新模型（test / test2）的接触与 CP 复现 + 纯 +1 交换 ΔCP 验证（16、17 脚本）。")
bullet(doc, "结果：新 11nt 模型与旧 7nt 模型的 +1G 接触/CP 轮廓一致，方法可迁移。")
bullet(doc, "17:01　生成用于 AF3 server 的突变体提交文件（18_make_af3_submit.py），共 44 个 JSON（15 单点 + 6 组合 + WT，各 × GCG/GCA）。")
bullet(doc, "23:40　突变体模型的 CP/ΔCP 分析脚本（19_mut_cp.py）。")

heading(doc, "2026-09-09（15:08 – 20:52）空间几何分析与最佳位点对", 2)
bullet(doc, "15:08　突变位点空间距离聚类（20_site_spatial.py，20 个 WT rank0 模型均值）。")
bullet(doc, "结果：所有被关注的 loop 并非彼此独立，而是**缠绕成以催化核心为中心的单一活性位点口袋**。关键空间桥梁：28→99 = 2.9 Å、31→57 = 2.9 Å、30→99 = 3.3 Å、129→102（锌配位）= 3.7 Å。")
bullet(doc, "15:09　靶点 C(0 位) 到催化 E72 的距离（21_targetC_catalytic_dist.py）。")
bullet(doc, "结果：WT 在 GCG 下靶点 C 的脱氨原子 C4/N4 距 E72 = 2.88 Å（精确停靠），而在 GCA 下为 6.33 Å（远离）——构成天然偏好 GCG 的几何基础。")
bullet(doc, "15:12　生成《导师汇报_研究总结》docx（研究思路 + 全部结果）。")
bullet(doc, "20:31　最佳组合位点对综合筛选（22_best_combo_pairs.py，MI × 空间 × 实验三表整合）。")
bullet(doc, "结果：**Y32F+M132E（比 2.22 / 活性 0.35）与 G27D+Y32F（2.02 / 0.36）为「高比+高活性」双达标位点对**；输出 Tier 分级清单。")
bullet(doc, "20:44–20:52　组合突变结果整理表与导师汇报定稿。")

heading(doc, "2026-09-10（15:29 – 16:12）全量整合、第一期汇报与 Δd_E72 回归", 2)
bullet(doc, "15:29　全量证据整合（23_integrate_all.py），产出四张主表：位点主表、组合主表、位点对评分矩阵、最终推荐表。")
bullet(doc, "结果：**单点天花板确认 = 1.71（102 个单点无一突破 2.0）**；**27T-30H-58M 达 +1比 2.16、保留 77%，为 71 组中唯一双达标者**。")
bullet(doc, "16:04　生成第一期组会汇报 PPT（30 页）。")
bullet(doc, "16:12　Δd_E72 回归与三点复合物结构解析（23_dE72_regression.py）。")
bullet(doc, "结果（重要负结果）：全部 22 个突变体的 Δd_E72 与实测 +1比 回归得 **r = −0.073，95% CI [−0.600, +0.498]（横跨 0）→ 该几何指标不能作为主筛指标**。但分层后出现关键机制差异：**单点 r = +0.670（选择性几何位移），组合 r = −0.724（整体催化几何下调）**。三点复合物 27T-30H-58M 的 GCG 侧 C4N4–E72 退化为 6.51 Å，而**锌配位完整（三对配位距离与 WT 偏差 ≤0.22 Å）→ 酶未坏，是底物摆不到位**。")

heading(doc, "2026-09-11 ~ 09-12（19:28 / 23:19 / 00:28 / 09:57）第二期与综合稿汇报", 2)
bullet(doc, "09-11 19:28　生成第二期组会汇报 PPT（P1-1 / P1-2 执行结果汇报，27 页）。")
bullet(doc, "09-11 23:19 – 09-12 00:28　按「上期为《可突变性与突变方向分析》」的实际衔接关系，将第一期与第二期合并为综合稿 PPT（36 页）。")
bullet(doc, "结果：形成「上期（可突变性/突变方向）→ 第一期（三维证据整合）→ 本期（P1-1/P1-2 执行）」三阶段递进；修正了跨批次数据混用问题（将 Y32F 移出单点批次表）。")

heading(doc, "2026-09-12（11:16 – 14:06）总体脱靶筛查、GCG 靶点重定义与湿实验清单", 2)
bullet(doc, "11:16–11:17　组合突变体总体脱靶筛查（24_offtarget_scan.py、25_offtarget_screen.py），基于 Seq/ 扩增子深度测序变异表（951 bp，291 个 C 位点，117 样本）。")
bullet(doc, "结果：**亲本 PUF12-9 在扩增子内有 63 个脱靶位点、脱靶负荷 Σoff = 10.87，全尺度特异性仅 0.058**；最佳组合 27T-30H-58M 降至 10 个位点、Σoff = 1.07（降 10 倍）。识别出**低活性假象**：32 个样本 on-target <0.30，其「零脱靶」是检出下限截断所致。")
bullet(doc, "11:25–11:27　构建「突变 × 脱靶位点」矩阵与热图（26、27 脚本，含去 P 版）。")
bullet(doc, "结果：**pos 390（GCG，紧邻靶点 388 仅 2 nt）与 871 并列为主要脱靶**，按总编辑量 390 甚至居首（918% vs 882%）；**P 系列（P4/P5/P6/P7/P8）引入 28 个理性点突变从未产生的新脱靶位点**，而全部编号组合新增脱靶数均为 0。")
bullet(doc, "11:31–11:39　按「全部 GCG 位点均为靶点」重新分析（28、29 脚本）。")
bullet(doc, "结果：**亲本单位点偏好 GCG（每点 11.8% vs 2.45%，偏好比 4.83），但总量上脱靶多于靶点（Σ 556 vs 598，靶向比 0.93）**；组合突变普遍提高偏好比但降低绝对编辑量；**30H-58M（靶向比 1.87、活性 78%）与 25E-32F（1.72、70%）为「高活性+高靶向」双优**——此结论与单位点偏好比分析互相印证。")
bullet(doc, "13:57–13:58　P 部分仅保留 WT 重新排序绘图（30 脚本）。")
bullet(doc, "结果：WT 在全部 45 个突变体中靶向比排第 41 位；在活性 ≥70% 前提下仅 7 个突变体优于 WT，头部仍为 30H-58M、25E-32F。")
bullet(doc, "14:06　生成湿实验引物设计用突变清单（31_wetlab_mutation_list.py）。")
bullet(doc, "结果：4 个工作表——单点总表（102 已测 + 2 新候选）、组合总表（50 编号组合 + 7 P 变体 + 7 新推荐）、位点分类与依据（7 大类）、新候选推荐（12 项）。**共需新构建 9 个（2 新单点 + 7 新组合）**。")


heading(doc, "三、失败与返工记录", 1)
para(doc, "本节按类别记录全过程中的假说证伪、方法失效、判断错误与数据陷阱。失败记录一并保留，用于避免重复路径与界定各方法的适用边界。", 10)

heading(doc, "3.1 假说被自身湿实验证伪", 2)
table(doc,
    ["日期", "假说 / 预期", "证伪证据", "处置与后续"],
    [["09-01 提出 → 09-02 证伪",
      "T31（Thr）为 A 特异氢键残基（GCA 中接触频率 1.00、GCG 中 0.00），切除其 –OH 即可「排 A」；曾列为新排 A 靶点",
      "T31A：+1比 1.32、保留 97%（无改善）；T31C：1.25。与该假说预期不符",
      "**假说正式撤回**。确立原则「结构接触 ≠ 功能」；T31 改列为「条件性判别子」待验（拟做 T31A+K30H 上位性实验）"],
     ["09-01 提出 → 09-02 证伪",
      "M132E 为「保 G」最优解（PremPRI dG=0.54 最优；mCSM-NA 亦给 M132D/E 最高分 +9.46）",
      "实验：M132D = 1.42 >> M132E = 1.18。**PremPRI 把 D/E 优劣判反**",
      "M132E 由首选降级为 M132D 的备选；确立「ML 工具只能用于排除必失活方向，绝不能用于特异性排序」"],
     ["09-01 提出 → 09-02 证伪",
      "M132 可作为 +1 特异性改造靶点（两 ML 工具一致给出最高分）",
      "132D 1.42 仅比 WT 1.37 高 0.05；132E 更差。结构核查显示 M132 距 +1 碱基 15–20 Å、接触频率为 0",
      "**方向失败**。M132 重新定位为「出口通道残基」，只影响整体活性/产物释放，不参与 G/A 判别"]],
    font=8.5)

heading(doc, "3.2 方法与模型失效", 2)
table(doc,
    ["日期", "方法 / 模型", "失效表现", "原因诊断", "处置"],
    [["09-02", "PSSM 突变方向预测（预期可预测任意位点的允许/禁止方向）",
      "溶剂暴露的 loop 位点准确率仅 **9%**；整体准确率 52%",
      "loop1（25–28）分子暴露度高、受实验环境与表达影响大，进化频率 ≠ 功能约束",
      "将 PSSM 适用范围收窄为「物化约束强的核心位点」（71%）；对 loop 位点改用物化性质 + 结构 clash 分析"],
     ["09-09 / 09-10", "加性先验评分模型：0.30×MI + 0.25×空间 + 0.25×单点可行 + 0.20×可突变性",
      "与实测 +1比 的 Pearson r = **+0.138**、Spearman ρ = +0.286（n=8）→ 无预测能力",
      "组合效应存在显著上位性，线性加性假设不成立（如 30+58 理论第 1 但实测仅 1.69；25+30 比达标但活性崩至 23%）",
      "**正式放弃该模型**作为位点对筛选依据；改为「逐层取一位点」的设计规则"],
     ["09-10", "Δd_E72 作为计算主筛指标（第一期 P1-1 计划：若 r > 0.7 则采用）",
      "全部 22 个突变体回归得 **r = −0.073，95% CI [−0.600, +0.498]**（横跨 0）→ 阴性",
      "GCA 侧 AF3 构象高度离散（model 间 SD 2.3–3.9 Å，个例跨度 3.86–12.36 Å），噪声方差 1.58 > 观测方差 0.97 → 信度 ≈ 0",
      "不采用为全局主筛指标；但分层后发现其可区分机制（单点 r=+0.670 / 组合 r=−0.724）；提出 GCA 侧需 5→5–10 seed 重采样"]],
    font=8.5)

heading(doc, "3.3 判断错误与返工", 2)
table(doc,
    ["日期", "原判断", "核查发现", "返工处置"],
    [["09-09", "空间聚类：以最小重原子距离 ≤8 Å 做传递闭包，识别「空间上靠近的突变位点簇」",
      "结果 19 个位点全部连成 **1 个簇**——因主链相邻残基肽键 C′–N 距离仅 1.33 Å，把整条肽链串成一簇，掩盖真实空间聚集",
      "重写为「按功能区划分 + 只统计序列间隔 |i−j| > 2 的跨区段接触」，产出跨区段空间桥梁表（28→99 = 2.9 Å 等）"],
     ["09-09", "最佳位点对评估：以「含该位点的组合最高 ratio」归因位点对",
      "多位点组合被重复归因到其中每一对，产生 max-of-containing-pair 偏差（如 3 点组合的 ratio 被记到其 3 个位点对上）",
      "改为**只统计恰好 2 个位点**的纯组合，2 点实测 ratio 作为金标准"],
     ["09-11", "第一期计划书判断「现有 AF3 突变体只到双点，需补建 27T-30H-58M 与 27D-30H-58M 三点复合物」",
      "核查目录发现 `g27tk30hq58m` / `g27dk30hq58m` **本身就是三点**（序列逐位验证 res27=T/D、res30=H、res58=M），×GCG/GCA 各 5 model 已存在",
      "不重复提交 AF3，直接解析既有模型；并在第二期汇报中单列「前置澄清」说明此点"],
     ["09-12", "综合稿 PPT 中，将 Y32F（来自组合实验批次）列入「单点批次天花板」表",
      "Y32F 并非单点饱和批次样本，混入会触犯「两套实验基数不同」的既有隐患（单点亲本 C388=0.5145 vs 组合亲本 0.673）",
      "替换为纯单点批次数据（30H/25E/27D/58M/27T/26N/132D/59S/28W/31A/129W）"],
     ["09-02", "跨批次直接比较单点与组合的 +1比（如「单点相乘模型预测组合上限 ~2.0」）",
      "两套实验亲本背景不同：单点亲本 C388=0.5145/＋1比 1.371；组合亲本 C388=0.673/＋1比 1.191。组合亲本 on-target 高 31%、脱靶高 50%，净比值反而低 13%",
      "全部跨实验比较统一改用 **ROF =（自身+1比）÷（同实验亲本+1比）**"]],
    font=8.5)

heading(doc, "3.4 数据解读陷阱", 2)
table(doc,
    ["日期", "表面现象", "陷阱", "处置"],
    [["09-12", "多个组合在总体脱靶筛查中显示「脱靶位点数 = 0、全尺度特异性 S = 1.0」，看似完美特异",
      "**低活性假象**：32 个样本 on-target < 0.30（其中 5 个为 0.000），其脱靶全部低于变异检出下限（5%）而被截断，并非真正不编辑",
      "引入活性下限（on ≥ 0.30）与 GCG 均值 ≥2% 作联合判据；报告中明确标注被剔除样本"],
     ["09-09 / 09-12", "单点 M132D 保留率 89%，判定为「安全位点」",
      "**组合中的系统性压制**：加入 132D 的组合 C388 中位仅 0.191（132E 组合 0.346、不含 132 者 0.295）；含 132D 组合无一超过 0.30，最高失活率 12%",
      "确立判据「单点保留率高 ≠ 组合安全」，组合中一律改用 132E；并外推至 30H / 27D 同类矛盾位点"],
     ["09-12", "P 系列（P4/P5/P6/P7/P8）域重设计变体活性极高（90–114% of WT）",
      "其靶向比仅 1.0–1.2（≈WT 0.93），且**引入 28 个理性点突变从未产生的新脱靶位点**（占全部脱靶位点的 38%）",
      "**方向性放弃**；仅保留 WT（PUF12-9）作基线"],
     ["—", "命名备注：内部汇总表曾使用「排A指数」指代催化核心的 +1=A 接触偏好",
      "该指标越正表示越贴 +1A（即天然偏好 GCA），命名与「排除 A」的语义相反，易致误读",
      "更正表述为「A 偏好指数」，并在报告中加注说明"]],
    font=8.5)

heading(doc, "3.5 工程与环境问题（已解决）", 2)
table(doc,
    ["问题", "现象", "解决方案"],
    [["Python 环境", "`python` 为 Windows Store 存根，退出码 49 且无输出",
      "统一改用 `uv run python`（uv 环境）"],
     ["埋藏面积计算", "Shrake-Rupley 实现报 IndexError（布尔索引维度不匹配，rj 为 (1,N) 而掩码为 (N,)）",
      "重写为 r = 半径 + 探针半径，邻接表用 np.where 构建并修正广播"],
     ["组合脚本", "05_combinations.py 出现 combo_key KeyError: 0",
      "改为字典访问 s[\"resi\"] / s[\"wt\"] / s[\"sub\"]"],
     ["文件占用", "PPT 保存报 PermissionError（旧文件在 PowerPoint 中打开）",
      "改存新文件名"],
     ["中文字体", "matplotlib 中文显示为方块（tofu）",
      "设置 rcParams[\"font.sans-serif\"] = [\"Microsoft YaHei\", \"SimHei\", \"DejaVu Sans\"]"],
     ["边界越界", "28_GCG_target_analysis.py 对参考序列末位 C 取 +1 位时 IndexError",
      "motif() 增加边界判断，越界返回 \"?\""],
     ["依赖缺失", "openpyxl / matplotlib / python-docx / python-pptx 未预装",
      "统一用 `uv run --with <pkg>` 临时注入，不污染全局环境"]],
    font=8.5)

para(doc, "小结：以上 5 类共 19 项失败/返工中，3 项来自「干预测被湿实验直接证伪」（T31、M132E、M132 判别子），3 项为「方法/模型本身失效」（PSSM-loop、加性先验、Δd_E72），5 项为「判断错误需返工」，4 项为「数据解读陷阱」，7 项为工程问题。这些记录共同界定了现有计算手段的适用边界，也是本项目方法学结论（如「ML 只做粗筛」「单点保留≠组合安全」）的直接来源。", 10, True)

heading(doc, "四、贯穿性结论（按证据强度）", 1)
bullet(doc, "已可靠确立：单点 +1比 存在约 1.7 的天花板；组合 27T-30H-58M = 2.16 / 保留 77% 为唯一双达标；三点组合锌配位完好、活性下降源于底物定位而非催化中心崩坏。", 10, True)
bullet(doc, "方法学教训：结构接触只定位「谁参与」，不等于功能（T31）；ML 的 ΔΔG 只反映结合强度、不反映特异性且 D/E 判反（M132）；线性加性模型无法外推组合（r 分别为 −0.073 / +0.14）。", 10, True)
bullet(doc, "新增判据：① 跨实验比较须用同批次亲本归一（ROF）；② 候选进组合前须看侧链物化类型（带电/刚性替换高风险，如 132D）；③ 低活性样本的「零脱靶/高偏好」为假象，必须设活性下限。", 10, True)
bullet(doc, "口径依赖性：同一批数据在「位点特异性（仅 388）」与「基序特异性（全部 GCG）」两种定义下，最优候选不同（27T-30H-58M vs 30H-58M / 25E-32F）——报告结论时须明确所用定义。", 10, True)

heading(doc, "五、主要产出文件索引", 1)
table(doc,
    ["类别", "文件", "说明"],
    [["报告", "APOBEC_保G排A优化_完整工作报告.docx；可突变性与突变方向分析.docx；导师汇报_研究总结.docx；干实验记录（本文件）", "各类阶段性报告"],
     ["汇报", "可突变性与突变方向分析_组会汇报.pptx；APOBEC保G排A优化_组会汇报.pptx（第一期）；_第二期.pptx；_综合稿.pptx", "组会汇报 PPT"],
     ["结构分析", "results/contacts_frequency.csv、hbonds_per_residue.csv、cp_dcp.csv、mutation_site_spatial_distances.csv、targetC_catalytic_dist_summary.csv", "接触/CP/空间/催化几何"],
     ["突变分析", "results/dE72_regression.csv、zinc_coordination.csv、mut_cp_summary_保G排A_合并.csv、best_combo_pairs.csv", "突变体几何与组合筛选"],
     ["脱靶分析", "results/offtarget_screen_final.csv、offtarget_matrix.csv、GCG_target_summary.csv、GCG_vs_off_ranking_WT.csv", "本轮新增（09-12）"],
     ["湿实验交付", "results/湿实验突变清单_引物设计用.xlsx", "引物设计用突变清单"],
     ["脚本", "00–31 共 30+ 个 .py（af_utils.py 为共享模块）", "全流程可复现"]],
    font=8.5)

doc.save(OUT)
print("已生成", OUT)
