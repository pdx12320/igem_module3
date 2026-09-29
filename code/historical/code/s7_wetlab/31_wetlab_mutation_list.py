# -*- coding: utf-8 -*-
"""
阶段 31 —— 湿实验引物设计用「突变位点清单」
（质粒序列已有，故只给位点/组合 + 分类 + 使用原因）

内容：
  Sheet1  单点突变总表（此前已测 102 个 + 新候选单点）
  Sheet2  组合突变总表（此前已测 57 种 + 新推荐组合）
  Sheet3  位点分类与依据（每个位点的角色、可动性、使用原因、禁区说明）
  Sheet4  新候选推荐（按优先级，附使用原因与预期）

产出：results/湿实验突变清单_引物设计用.xlsx
      results/湿实验突变清单_单点.csv / _组合.csv / _位点分类.csv
"""
import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

NAVY = "1F3B66"; LIGHT = "F2F4F8"; ACC = "B44A3C"; GREEN = "1E7A46"

# ============ 位点分类与使用原因（核心表） ============
SITE_CLASS = [
    # (位点, WT, 分类, 功能角色, 可动性, 保守性, 使用原因 / 依据)
    ("25", "G", "loop1-N（−1 上游锚定）", "N 端调节", "可动", "0.02（高度可变）",
     "单点 25E 实测 +1比 1.55/保留 89%（意外强）；与 K30 共进化 MI 1.07（全局最高）→ 组合优先搭档"),
    ("26", "I", "loop1-N（−1 上游锚定）", "−1 端调节", "可动", "0.04（高度可变）",
     "26N 实测 1.42/保留 98%（无活性代价）；与 K30 共变 MI 0.90 + 空间 8.0 Å → 未测组合首选"),
    ("27", "G", "loop1-N（−1 位主锚）", "−1 位特化，压制 ACA 类脱靶", "慎动", "0.82（较保守）",
     "27D 使 ACA/GCA 降至 0.008（36 倍压制）、+1比 1.53/保留 88%；27T 保留 98%。−1 轴核心锚点"),
    ("28", "R", "loop1-N（口袋壁）", "loop1 壁，紧贴保守 W99（2.9 Å）", "慎动", "0.84（较保守）",
     "★ 新候选：CP 分析显示 R28A 的保G指数 −0.400（全局最负）、排A指数 +0.305（全局最高）→ 唯一双向增强位点；尚未湿实验"),
    ("29", "H", "＋1 碱基阅读器", "保 G 阅读（主链为主，侧链仅 5%）", "可动", "0.22（可变）",
     "mCSM-NA 纯 +1 swap 判别最强（+5.36），但侧链贡献仅 5% → 仅作机制探针，不作主力候选"),
    ("30", "K", "＋1 碱基阅读器（主）", "保 G 阅读主（侧链读 Hoogsteen 边）", "可动", "0.36（可变）",
     "★ 唯一可动的 +1 侧链读取器：K30H 实测 1.71/保留 84%（最佳单点）；且为全部组合的核心锚点"),
    ("31", "T", "＋1 碱基阅读器（A 偏好侧）", "仅对 A 形成侧链氢键（非判别开关）", "慎动", "0.82（较保守）",
     "结构接触强但功能无效（T31A 1.32 无改善）→ 用于验证「条件性判别子」假说（T31A+K30H）"),
    ("32", "Y", "±2 位（下游）", "排 +2 G", "可动", "0.56（可变）",
     "Y32F 在组合中为最强比提升器（边际 Δ+1比 +0.21）；与 M132E 组合实测 2.22/活性 0.35（最佳位点对）"),
    ("57", "N", "loop3（催化必需）", "催化必需残基", "禁区", "0.67（与催化核心共进化 MI 最高 0.30）",
     "⚠ 不建议加入新组合：N57 突变（D/A/G/M/R/S/W）实验大多失活，仅特定替换（如 N57G）可考虑"),
    ("58", "Q", "loop3（排A 稳定）", "loop3 排 A / 产物稳定", "可动", "0.29（可变）",
     "★ 唯一强活性保护器：Q58M 使保留率 +14pp（1.46/79%）；与 30H 共变 MI 0.77 + 空间 7.7 Å"),
    ("59", "A", "loop3（沟槽壁）", "loop3 壁", "可动", "0.16（可变）",
     "59S 实测 1.33/保留 74%；与 30 共变 MI 0.88 + 空间 7.0 Å → 未测组合候选"),
    ("60", "K", "loop3（沟槽尾）", "loop3 尾 / 出口邻位", "可动", "0.30（可变）",
     "单点比值高但活性代价大（60Q 2.55/保留 17%、60H 1.55/57%）→ 仅作机制探针，不建议组合"),
    ("98", "S", "WS 环", "WS 环（91% 保守）", "慎动", "0.91（高保守）",
     "98 位多突变降活（98G 1.45/保留 47%）；与 29N 组合比值 1.86 但活性低 → 不推荐"),
    ("129", "F", "loop7 / 出口通道", "loop7 头", "可动", "0.29（可变）",
     "129W 实测 1.30/保留 87%（温和、保活性）；与 M132 空间 5.5 Å → 出口轴辅助位点"),
    ("130", "W", "loop7 / 出口通道", "loop7 探针（活性开关）", "可动", "0.03（高度可变）",
     "130G 比值极高（3.00）但保留仅 32% → 只作「脱靶清除」机制探针，不可作候选"),
    ("131", "H", "loop7 / 出口通道", "loop7", "可动", "0.21（可变）",
     "单点普遍偏弱（131R 1.72/保留 31%）；与 K30 共变 MI 0.87，可作共进化验证探针"),
    ("132", "M", "loop7 / 出口通道", "出口通道（距 +1 位 15–20 Å，不接触碱基）", "可动", "0.05（高度可变）",
     "★ 132D 实测 1.42/保留 89%，但组合中系统性压制活性（含 132D 组合 C388 中位 0.191）→ 组合中改用 132E"),
    ("133", "D", "loop7 / 出口通道", "loop7 尾", "可动", "0.43（可变）",
     "133Y 1.37/保留 51%，表现平庸 → 低优先级"),
    ("70/72/99/102/105", "H/E/W/C/C", "催化核心 / 锌配位", "Zn²⁺ 配位（H70/C102/C105）+ 质子供体（E72）+ 保守 Trp（W99）",
     "绝对禁区", "0.95–1.00（绝对保守）",
     "⚠ 任何突变都会失活：不纳入任何组合（P1-2 结构分析确认三点组合的锌配位仍完好，突变会破坏它）"),
]

# ============ 新候选（未测） ============
NEW_CAND = [
    ("N1", "R28A", "单点", "loop1-N", "P0",
     "CP 保G指数 −0.400（最负）+ 排A指数 +0.305（最高）＝唯一双向增强位点；PSSM 允许方向；贴保守 W99（2.9 Å）",
     "预期：提高 +1 比且不损活性；同时验证「口袋壁重塑」机制"),
    ("N2", "R28S", "单点", "loop1-N", "P1",
     "同 R28A 但侧链更短，扰动更温和（保G −0.345）", "预期：R28A 的温和备选"),
    ("N3", "T31V", "单点", "＋1 阅读器", "P1",
     "CP：T31V 下 GCG 侧催化几何保持（C4N4–E72 = 2.98 Å ≈ WT 2.88）；而 T31I/L 被推远至 5.07/5.70 Å",
     "预期：T31V 耐受、T31I/L 显著降活 → 验证「大侧链变构失活」模型"),
    ("N4", "T31A+K30H", "双点", "＋1 阅读器 × ＋1 阅读器", "P1",
     "收口 T31 悖论：检验 T31 是否只在 K30 存在时才起作用（条件性判别子）",
     "预期：若上位性显著 → 「结构接触≠独立功能」成立"),
    ("N5", "26N+K30H", "双点", "loop1-N × ＋1 阅读器", "P0",
     "共进化 MI 0.90（第二高）+ 空间 8.0 Å；两单点均高保留（26N 98%、K30H 84%）",
     "预期：两个「低活性代价」位点叠加，冲击比 ≥2.0 且保留 ≥80%"),
    ("N6", "30H+59S", "双点", "＋1 阅读器 × loop3", "P1",
     "共进化 MI 0.88 + 空间 7.0 Å；59S 保留 74%、30H 保留 84%",
     "预期：loop3 壁协同 +1 读取，比与活性兼顾"),
    ("N7", "27D-30H-58M", "三点", "−1 锚 × ＋1 阅读 × loop3", "P0",
     "27D 对 ACA 压制比 27T 强 5 倍（0.008 vs 0.042）、保留 88%；结构解析显示其 GCG 侧几何（5.05 Å）比 27T 版（6.51 Å）更温和",
     "预期：比 ≥2.0 且 on-target 保留优于 27T-30H-58M（77%）"),
    ("N8", "30H-58M+27T", "三点", "（= 已测 27T-30H-58M 对照）", "—",
     "已测：比 2.16 / 保留 77%，全部 71 组中唯一双达标", "作为 N7 的平行对照"),
    ("N9", "27D-30H-32F-58M", "四点", "−1 锚 × ＋1 阅读 × ±2 × loop3", "P1",
     "以 27D-30H-32F（实测 3.44/保留 38%）为骨架叠加唯一活性保护器 58M",
     "预期：冲击比 ≥3.0，但需重点监测活性"),
    ("N10", "25E+K30H+58M", "三点", "loop1-N × ＋1 阅读 × loop3", "P1",
     "25E 与 30H 共变 MI 1.07（最高）+ 58M 活性保护；25E 实测 1.55/保留 89%",
     "预期：MI 最高的位点对 + 唯一保护器"),
    ("N11", "A59P", "单点", "loop3", "P2",
     "PremPRI 保G优 + 判别（score +0.29）；沟槽壁微调，不碰 +1 接触",
     "预期：温和改善，作组合骨架备用"),
    ("N12", "K60R", "单点", "loop3", "P2",
     "PremPRI 判别最强（+0.46）、保G中上；埋藏面积中等、几乎无氢键",
     "预期：沟槽壁电荷微调，低风险探针"),
]

# ============ 已测单点（从 experimental_ranking.csv 汇总） ============
import re
from collections import defaultdict
singles = defaultdict(list)
for r in csv.DictReader(open("results/experimental_ranking.csv", encoding="utf-8-sig")):
    m = re.match(r'(\d+)([A-Z])$', r["mut"])
    if m:
        singles[int(m.group(1))].append(
            (r["mut"], float(r["ratio"]), float(r["retain"]), r["active"] == "True"))

WT_SEQ = ("MEASPASGPRHLMDPAIFTSNFNNGIGRHKTYLCYEVERLDNGTSVKMDQHRGFLHNQAKNLLCGFYGR"
          "HVEVNFIKKFTSERDFHPSMSCSITWFLSWSPCWECSQAIREFLSRHPGVTLVIYVARLFWHMDQQNR"
          "QGLRDLVNSGVTIQIMTYDEFKHCWDTFVDHQGAPFQPWDGLDEHSQALSGRLRAILQNQGN")
def wt_aa(pos): return WT_SEQ[int(pos)-1]

SITE_TAG = {25: "loop1-N", 26: "loop1-N", 27: "loop1-N（−1主锚）", 28: "loop1-N（壁）",
            30: "＋1阅读器（主）", 31: "＋1阅读器（A侧）", 57: "loop3（催化必需·禁区）",
            58: "loop3（排A）", 59: "loop3（壁）", 60: "loop3（尾）", 98: "WS环",
            129: "loop7（头）", 130: "loop7（探针）", 131: "loop7", 132: "loop7（出口）", 133: "loop7（尾）"}

# ============ 已测组合 ============
import glob, os
def mutname(n):
    m = re.match(r'G\d+-(b?)(\d+)-(.*)$', n)
    return m.group(3) if m else n
combos = set()
for f in sorted(glob.glob("Seq/Var/*.var.xls")):
    if ".filt." in f: continue
    combos.add(mutname(os.path.basename(f).replace(".var.xls", "")))
combos_numbered = sorted([c for c in combos if not c.startswith("P")])
combos_P = sorted([c for c in combos if c.startswith("P")])

# ============ 写 Excel ============
wb = Workbook()
thin = Side(style="thin", color="BBBBBB")
bd = Border(left=thin, right=thin, top=thin, bottom=thin)
def style_header(ws, ncol, row=1):
    for j in range(1, ncol + 1):
        c = ws.cell(row=row, column=j)
        c.font = Font(bold=True, color="FFFFFF", size=10)
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = bd
def fill_rows(ws, rows, start=2, size=9.5):
    for i, row in enumerate(rows, start=start):
        for j, v in enumerate(row, start=1):
            c = ws.cell(row=i, column=j, value=v)
            c.font = Font(size=size)
            c.alignment = Alignment(vertical="top", wrap_text=True)
            c.border = bd
            if i % 2 == 0:
                c.fill = PatternFill("solid", fgColor=LIGHT)

# --- Sheet1 单点 ---
ws = wb.active; ws.title = "1_单点突变总表"
ws.append(["编号", "位点", "位点分类", "WT", "突变", "状态", "实验+1比", "保留率", "判定", "使用原因/备注"])
hdr = ws[1]
rows = []
n = 0
for pos in sorted(singles):
    items = sorted(singles[pos], key=lambda x: -x[1])
    for k, (mut, ratio, retain, act) in enumerate(items):
        n += 1
        verdict = "✓ 可用（保留≥60%）" if act else ("活性偏低" if retain < 0.6 else "")
        reason = {
            30: "唯一可动的 +1 侧链读取器；组合核心锚",
            27: "−1 位主锚，压制 ACA 类脱靶最强",
            58: "唯一强活性保护器（+14pp）",
            25: "与 K30 共变 MI 最高（1.07）",
            26: "与 K30 共变 MI 0.90，保留近 100%",
            32: "排 +2 G，组合中最强比提升器",
            31: "验证「条件性判别子」（单点无效）",
            57: "⚠ 催化必需，突变多失活，不建议进新组合",
            60: "比值高但活性代价大，仅探针",
            130: "比值极高但活性崩，仅「清除」探针",
            28: "★ 新候选 R28A/S 的依据位点（CP 双向增强）",
            59: "59S 保留 74%；与 K30 共变 MI 0.88 + 空间 7.0 Å → 未测组合候选",
            98: "高度保守（91%），多突变降活 → 仅留档，不推荐进组合",
            129: "129W 保留 87%（温和保活性）；出口轴辅助位点",
            131: "单点普遍偏弱（保留 31–65%）→ 仅作共进化验证探针",
            132: "⚠ 132D 组合中系统性压制活性 → 组合中须改用 132E",
            133: "133Y 保留 51%，表现平庸 → 低优先级",
        }.get(pos, "已饱和位点，数据留档")
        rows.append([f"S{n}", pos, SITE_TAG.get(pos, ""), wt_aa(pos), mut, "已测",
                     f"{ratio:.2f}", f"{retain:.2f}", verdict, reason])
single_rows = list(rows)
fill_rows(ws, rows)
# 新候选单点
for cid, mut, typ, cls, pri, why, exp in NEW_CAND:
    if typ == "单点":
        n += 1
        pos = re.search(r'(\d+)', mut).group(1)
        rows2 = [[f"NEW-{cid}", pos, SITE_TAG.get(int(pos), cls), wt_aa(pos), mut, "★新候选",
                  "—", "—", f"优先级 {pri}", f"{why}｜{exp}"]]
        fill_rows(ws, rows2, start=len(rows) + 2)
style_header(ws, 10)
for col, w in zip("ABCDEFGHIJ", [8, 6, 20, 5, 10, 9, 9, 8, 16, 62]):
    ws.column_dimensions[col].width = w

# --- Sheet2 组合 ---
ws2 = wb.create_sheet("2_组合突变总表")
ws2.append(["编号", "组合", "位点数", "位点构成", "位点分类标签", "状态", "使用原因 / 预期"])
rows = []
combo_rows = rows
for i, c in enumerate(combos_numbered, 1):
    parts = re.findall(r'(\d+)([A-Z]+)', c)
    sites = [p[0] for p in parts]
    tags = " × ".join(SITE_TAG.get(int(s), "？") for s in sites)
    note = "空白/阴性对照样本（非突变组合）" if not sites else "既有组合实验，数据留档"
    rows.append([f"已测C{i}", c, len(sites), "+".join(sites) if sites else "—", tags if tags else "—", "已测", note])
for i, c in enumerate(combos_P, 1):
    rows.append([f"已测P{i}", c, 1, "—", "P 系列 loop 重设计变体", "已测",
                 "⚠ 已证实引入 28 个全新脱靶位点，不建议继续此方向"])
fill_rows(ws2, rows)
combo_rows = list(rows)
start = len(rows) + 2
new_combo = []
for cid, mut, typ, cls, pri, why, exp in NEW_CAND:
    if typ != "单点":
        parts = re.findall(r'(\d+)', mut)
        new_combo.append([f"NEW-{cid}", mut, len(parts), "+".join(parts), cls, "★新推荐",
                          f"[{pri}] {why}｜{exp}"])
fill_rows(ws2, new_combo, start=start)
style_header(ws2, 7)
for col, w in zip("ABCDEFG", [10, 22, 7, 18, 26, 10, 78]):
    ws2.column_dimensions[col].width = w

# --- Sheet3 位点分类与依据 ---
ws3 = wb.create_sheet("3_位点分类与依据")
ws3.append(["位点", "WT", "位点分类", "功能角色", "可动性", "保守性(WT频率)", "使用原因 / 依据"])
fill_rows(ws3, [list(r) for r in SITE_CLASS])
style_header(ws3, 7)
for col, w in zip("ABCDEFG", [16, 5, 26, 30, 10, 20, 88]):
    ws3.column_dimensions[col].width = w

# --- Sheet4 新候选推荐 ---
ws4 = wb.create_sheet("4_新候选推荐")
ws4.append(["编号", "突变/组合", "类型", "位点分类", "优先级", "使用原因（分析依据）", "预期目标"])
fill_rows(ws4, [list(r) for r in NEW_CAND])
style_header(ws4, 7)
for col, w in zip("ABCDEFG", [9, 20, 8, 24, 8, 70, 46]):
    ws4.column_dimensions[col].width = w

wb.save("results/湿实验突变清单_引物设计用.xlsx")
print("写入 results/湿实验突变清单_引物设计用.xlsx")

# CSV 版本
with open("results/湿实验突变清单_单点.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["编号","位点","位点分类","突变","状态","实验+1比","保留率","判定","使用原因"])
    w.writerows([[r[0],r[1],r[2],r[4],r[5],r[6],r[7],r[8],r[9]] for r in single_rows])
with open("results/湿实验突变清单_组合.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["编号","组合","位点数","位点构成","位点分类标签","状态","使用原因"])
    w.writerows([[r[0],r[1],r[2],r[3],r[4],r[5],r[6]] for r in combo_rows])
with open("results/湿实验突变清单_位点分类.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["位点","WT","位点分类","功能角色","可动性","保守性","使用原因"])
    w.writerows(SITE_CLASS)

print(f"单点条目 {len(singles)} 位点 / {sum(len(v) for v in singles.values())} 个突变")
print(f"组合条目 {len(combos_numbered)} 个编号组合 + {len(combos_P)} 个 P 变体")
print(f"新候选 {len(NEW_CAND)} 项")
