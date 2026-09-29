# -*- coding: utf-8 -*-
"""
生成 Word 版完整工作流与结果报告。
用法：uv run --with python-docx python make_word_report.py
产出：APOBEC_保G排A优化_完整工作报告.docx
"""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = "APOBEC_保G排A优化_完整工作报告.docx"
CN_FONT = "微软雅黑"


def set_cn(run, size=None, bold=None, color=None):
    run.font.name = CN_FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor(*color)


def para(doc, text, size=10.5, bold=False, color=None, space_after=6):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_cn(r, size=size, bold=bold, color=color)
    p.paragraph_format.space_after = Pt(space_after)
    return p


def heading(doc, text, level=1):
    h = doc.add_heading("", level=level)
    r = h.add_run(text)
    set_cn(r, size=16 if level == 1 else 13 if level == 2 else 11.5, bold=True,
           color=(0x1F, 0x3B, 0x66) if level == 1 else (0x2E, 0x54, 0x8B))
    return h


def add_table(doc, headers, rows, col_widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    for i, htxt in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(htxt)
        set_cn(r, size=9.5, bold=True, color=(0xFF, 0xFF, 0xFF))
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(val))
            set_cn(r, size=9.5)
    return t


doc = Document()
# 页边距
for s in doc.sections:
    s.top_margin = Inches(0.8); s.bottom_margin = Inches(0.8)
    s.left_margin = Inches(0.9); s.right_margin = Inches(0.9)

# ===== 标题 =====
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title.add_run("APOBEC 蛋白 +1 位「保G排A」突变优化\n完整工作流与结果报告")
set_cn(r, size=18, bold=True, color=(0x1F, 0x3B, 0x66))

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run("REWIRE 系统 · Pro.hA1 · 特异性编辑 GCG（c.388）而非 GCA（c.871）")
set_cn(r, size=11, color=(0x60, 0x60, 0x60))

para(doc, "报告日期：2026-09-02    方法平台：AlphaFold3 结构预测 · 纯 Python 结构分析 · mCSM-NA · PremPRI",
     size=9, color=(0x80, 0x80, 0x80))

# ===== 一、项目背景 =====
heading(doc, "一、项目背景与目标", 1)
para(doc, "本项目优化 REWIRE 系统中的 APOBEC 脱氨酶，使其特异性编辑 GCG 序列（APOE4 c.388 靶位），"
          "而非 GCA 序列（最严重脱靶位点 c.871），以降低 RNA 碱基编辑的脱靶率。"
          "编辑 C 为 0 位，靶位 GUGCGCG 与脱靶位 AUGCAGC 共享 -1=G，核心差异在 +1 位（G vs A）。")
para(doc, "底盘蛋白：Pro.hA1（199 aa）。三组 RNA 底物（蛋白序列完全相同，仅 RNA 不同）：")
add_table(doc,
          ["RNA 序列", "+1 位", "角色", "样本"],
          [["GUGCGCG", "G", "on-target（388 靶）", "20 seed × 5 model"],
           ["GUGCACG", "A", "纯 +1 交换对照", "20 seed × 5 model"],
           ["AUGCAGC", "A", "871 脱靶（完整上下文）", "20 seed × 5 model"]])

# ===== 二、工作流总览 =====
heading(doc, "二、工作流总览", 1)
add_table(doc,
          ["阶段", "工具/脚本", "产出", "关键结论"],
          [["1 数据盘点+质控", "00_manifest.py / 01_qc.py", "manifest.csv、qc_report.csv",
            "300 model 可用；AUGCAGC 84/100 的 +1 位 pLDDT<60"],
           ["2 +1 接触分析", "02_contacts.py / 03_summary.py", "contacts_long/frequency.csv",
            "+1=G 由 H29/K30 读；+1=A 摆向 H70/E72/W99"],
           ["3 距离分布图", "plot_distances.py", "小提琴图/频率图", "直观复现 G/A 机制差异"],
           ["4 互作分析", "04_interactions.py", "氢键/埋藏面积/filtered", "新发现 T31 为 A 特异氢键残基"],
           ["5 单点+组合生成", "05_combinations.py", "combinations_top1000.csv", "24 单点→1902 组合→筛后前 1000"],
           ["6 cif→pdb", "06_cif2pdb.py", "3 代表结构 PDB", "供在线工具提交"],
           ["7 mCSM-NA 验证", "07_mcsm_rerank.py", "mcsm_*_rerank.csv", "M132D/E 两口径一致保G排A"],
           ["8 PremPRI 验证", "08_prempri_rerank.py", "prempri_*_rerank.csv", "M132E 保G最优；T31 获排A支持"]])

# ===== 三、数据与方法 =====
heading(doc, "三、数据与方法", 1)
para(doc, "结构数据：AlphaFold3 服务器版输出（ModelCIF），三组 RNA × 20 seed × 5 model = 300 个结构。"
          "蛋白为 chain A（199 残基，编号与 FASTA 1:1 对应），RNA 为 chain B（7 核苷酸，+1 位 = chain B resi 5）。")
para(doc, "分析方法：纯 Python 标准库解析 cif（接触距离、几何氢键、Shrake-Rupley 界面埋藏面积），"
          "辅以 PyMOL 可视化脚本（.pml）；在线工具 mCSM-NA（蛋白-核酸结合 ΔΔG）与 PremPRI（蛋白-RNA 突变效应）交叉验证。")
para(doc, "符号约定提示：mCSM-NA 正 ΔΔG=增强结合（保）；PremPRI 正 ΔΔG=减弱结合（排）——二者方向相反，交叉比较时注意翻号。")

# ===== 四、阶段结果 =====
heading(doc, "四、各阶段结果", 1)

heading(doc, "4.1 质控", 2)
para(doc, "300 个 model 全部无硬剔除（链完整、+1 碱基原子齐全）。置信度方面，GUGCGCG 与 GUGCACG 各 100/100 通过；"
          "AUGCAGC 有 84/100 出现 +1 碱基 pLDDT<60（中位 53.8）、5 条 iptm<0.5，提示脱靶态 +1 位建模置信度偏低。")

heading(doc, "4.2 接触分析（距离）", 2)
para(doc, "关键残基到 +1 碱基的中位距离（Å）：")
add_table(doc,
          ["残基", "H29", "K30", "N57", "H70", "E72", "W99", "R69"],
          [["+1=G (GCG)", "3.56", "3.60", "6.55", "11.53", "14.48", "9.83", "11.2"],
           ["+1=A (swap)", "3.86", "3.29", "3.00", "2.73", "4.14", "4.08", "4.97"]])
para(doc, "结论：H29/K30 在 G/A 中都近距离读碱基（共同阅读器）；催化核心 H70/E72/W99 在 G 中远离（10–14 Å）、A 中靠近（2.7–4.1 Å），"
          "即 +1=A 时碱基摆向催化核心。")

heading(doc, "4.3 距离分布图", 2)
for img, cap in [("results/plots/distance_violin_key_residues.png", "图1 关键残基距离分布小提琴图（红虚线=5Å 接触阈值）"),
                 ("results/plots/frequency_bar.png", "图2 全残基 +1 碱基接触频率 G vs A 柱状对比")]:
    if os.path.exists(img):
        doc.add_picture(img, width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap_p = doc.add_paragraph(); cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap_p.add_run(cap); set_cn(r, size=9, color=(0x60, 0x60, 0x60))

heading(doc, "4.4 互作分析（氢键 + 界面埋藏面积）", 2)
para(doc, "氢键计数（供体-受体重原子 ≤3.5 Å）与界面埋藏面积（Shrake-Rupley）叠加，发现关键残基 T31：")
add_table(doc,
          ["指标", "GUGCGCG (G)", "GUGCACG (A-swap)", "AUGCAGC (A-off)"],
          [["T31 氢键频率", "0%", "100%（平均 2.68 条）", "55%（平均 1.3 条）"],
           ["T31 中位距离", "7.96 Å", "1.87 Å", "3.08 Å"],
           ["T31 埋藏面积", "23.3 Å²", "24.9 Å²", "26.9 Å²"]])
para(doc, "核心发现：T31（Thr）是 A 特异氢键残基——其 OH 与腺嘌呤 N6（供体）形成氢键（A 中 100%、G 中 0%），"
          "而鸟嘌呤在同位置是 O6（受体），故 T31 天然「保A」。切除 T31-OH 即为「排A」新靶点。")

heading(doc, "4.5 单点与组合生成", 2)
para(doc, "依据结构/互作证据 + 学姐饱和数据，构建 24 个有生化依据的单突变（12 位点），"
          "生成所有 2/3 位点组合共 1902 组，经「去稳定 + 无排A」筛选后按相乘模型排序，输出前 1000 组。")

heading(doc, "4.6 mCSM-NA 验证", 2)
para(doc, "20 个可评分突变（G27 为 Gly 无法评分、T31/S98A 因 RSA=0 外推不可靠）。关键结果：M132D/E 两口径一致保G排A；"
          "阅读器 H29/K30 在纯 +1 swap 上判别强，但在低置信度 AUGCAGC 结构上出现伪差。")

heading(doc, "4.7 PremPRI 验证", 2)
para(doc, "24 个突变全部有评分（含 G27）。关键结果：M132E 保G最优（dG=0.54）且仍判别；M132D 无判别（0.67–0.69），E 优于 D；"
          "T31V/I/L 获排A支持（score +0.16~+0.29）但 dG 1.78–2.13 同时伤 G。")

# ===== 五、关键发现 =====
heading(doc, "五、关键发现汇总", 1)
for t in [
    "1. T31 是 A 特异氢键残基（结构新发现，交接文档候选未含），可作为「排A」新靶点。",
    "2. M132E 是唯一 mCSM-NA 与 PremPRI 两工具都强且保G最优的突变；M132D 在 PremPRI 下无判别，E 优于 D。",
    "3. K30H（实验 +1 比 1.71）被两个 ML 工具系统性低估——它们主要预测破坏幅度，抓不住 G/A 特异性。",
    "4. 两 ML 工具均为单结构预测、判别分数偏小，只宜作「保G（破坏幅度）」粗筛，最终以实验+结构接触证据为准。",
]:
    para(doc, t, size=10.5)

# ===== 六、最终突变候选表 =====
heading(doc, "六、最终突变候选表", 1)
heading(doc, "6.1 单点候选", 2)
add_table(doc,
          ["优先级", "突变", "作用机制", "mCSM-NA", "PremPRI", "关键依据"],
          [["P0", "M132E", "出口排A", "+9.46", "+0.36", "两工具一致保G排A（保G最优 dG=0.54）"],
           ["P0", "M132D", "出口排A", "+9.46", "−0.02", "mCSM 强但 PremPRI 无判别（E 的备选）"],
           ["P0", "K30H", "+1 保G排A", "swap +2.89", "+0.03", "实验 +1 比 1.71（ML 均低估）"],
           ["P0", "G27D", "−1 特化压 ACA", "swap +1.50", "−0.15", "实验压 ACA 最强"],
           ["P0", "G27T", "−1 特化压 ACA", "swap +1.46", "+0.13", "实验压 ACA"],
           ["P1", "T31V/I/L", "切除 A 特异氢键（新）", "不可靠", "+0.16~0.29", "A 中 100% 成氢键 / G 中 0%"],
           ["P1", "K60R", "沟槽壁微调", "+1.15", "+0.46", "PremPRI 顶判别"],
           ["P1", "A59P", "沟槽壁微调", "+0.51", "+0.29", "保G优"],
           ["P1", "R28A/R28S", "近 H29 微调", "−2.5", "+0.16~0.23", "PremPRI 保G优（新）"],
           ["P1", "Y32F", "排 +2 G", "−8.03", "+0.23", "需 +2 口径验证"]])

heading(doc, "6.2 组合候选（推荐优先合成）", 2)
add_table(doc,
          ["优先级", "组合", "骨架", "说明"],
          [["P0", "A59P + K60R + M132E", "M132E 锚", "PremPRI 最佳（score 1.10）"],
           ["P0", "K60R + M132E + R28A", "M132E 锚", "PremPRI 次佳（score 1.04）"],
           ["P0", "G27D + K30H + M132E", "实验锚+出口", "前期相乘模型 top + 两工具正向"],
           ["P0", "G27T + K30H + M132E", "实验锚+出口", "同上（T 替换 D）"],
           ["P1", "K30H + T31V + M132E", "含 T31 探针", "结构+PremPRI 双支持"],
           ["P1", "M132E + T31V + R28A", "含 T31 探针", "PremPRI score 0.88"]])

# ===== 七、绝对禁区 =====
heading(doc, "七、绝对禁区（全程不触碰）", 1)
para(doc, "N57、H70、E72、W99（催化/锌相关残基）；C102、C105（锌配位）；G68（骨架保守）。")

# ===== 八、验证路径 =====
heading(doc, "八、推荐验证路径", 1)
for t in [
    "1. 首选合成：M132E 单点 + 4 条 P0 组合（A59P+K60R+M132E、K60R+M132E+R28A、G27D+K30H+M132E、G27T+K30H+M132E）。",
    "2. 排A探针：T31V 单点 + K30H+T31V+M132E，验证「切除 A 特异氢键」假说。",
    "3. 判定标准：on-target GCG 保留 ≥70% 且 +1 比 ≥2.0；剂量梯度区分「真特异性」vs「整体降活」。",
    "4. 工具定位：mCSM-NA/PremPRI 仅作「保G」粗筛，最终以实验 + 结构接触证据为准。",
]:
    para(doc, t, size=10.5)

# ===== 九、结论 =====
heading(doc, "九、结论", 1)
para(doc, "通过 AF3 深采样（300 结构）+ 多维接触/氢键/埋藏面积分析 + 双在线工具交叉验证，"
          "系统性地筛选出以 M132E 为锚点的「保G排A」突变组合，并新发现 T31 作为 A 特异氢键靶点。"
          "推荐以 M132E 为核心、搭配 K30H/G27D/T（实验锚）与 A59P/K60R/R28A（组合骨架）推进湿实验验证。")

doc.save(OUT)
print("已生成：", os.path.abspath(OUT))
