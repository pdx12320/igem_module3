# -*- coding: utf-8 -*-
"""
阶段 35 —— 干实验预测 vs 湿实验验证 最佳候选排序对照表
用途：把「干预测排出来的名次」与「湿实验实测的名次」并置，量化各预测手段的可靠性。

三张表：
  Sheet1 单点/突变级对照（干预测排名 vs 湿实测排名 + 一致性）
  Sheet2 位点级对照（16 个已测位点的干预测依据 vs 湿最佳表现）
  Sheet3 预测方法可靠性汇总（每种手段与实测的一致率）

产出：results/干湿排序对照表.xlsx / .csv
"""
import csv, re, sys, statistics
sys.stdout.reconfigure(encoding="utf-8")
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

NAVY = "1F3B66"; LIGHT = "F2F4F8"; OK = "E6F4EA"; BAD = "FBE3E1"; MID = "FFF6E0"

# ---------- 载入 ----------
def load(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))

mcsm = {r["mut"]: float(r["combined"]) for r in load("results/mcsm_single_rerank.csv")}
prem = {r["mut"]: float(r["score"]) for r in load("results/prempri_single_rerank.csv")}
wet = {}
for r in load("results/experimental_ranking.csv"):
    m = re.match(r'(\d+)([A-Z])$', r["mut"])
    if m:
        wet[r["mut"]] = dict(resi=int(m.group(1)), ratio=float(r["ratio"]),
                             retain=float(r["retain"]), active=r["active"] == "True")
# 组合实测
combo = {}
for r in load("results/offtarget_screen_final.csv"):
    try:
        combo[r["mutant"]] = dict(on=float(r["on_388"]), load=float(r["off_load_sum"]),
                                  norm=float(r["norm_load"]), S=float(r["S_global"]))
    except ValueError:
        pass
# 组合干预测（相乘模型）
pred_combo = {}
for r in load("results/combinations_top1000.csv"):
    pred_combo[r["mutations"].replace("+", "-").replace("G", "G")] = float(r["est_ratio"])
# GCG 口径
gcg = {}
for r in load("results/GCG_vs_off_ranking_WT.csv"):
    try:
        gcg[r["mutation"]] = dict(ratio=float(r["targeting_ratio"]), act=float(r["activity_retention"]),
                                  is_wt=r["is_WT"] == "True")
    except ValueError:
        pass

# 1-letter 转换（干预测键名 T31V 等；湿实验键名 31A 等）
def to_wet_key(k):
    m = re.match(r'([A-Z])(\d+)([A-Z])$', k)
    return f"{m.group(2)}{m.group(3)}" if m else k

# ---------- Sheet1：突变级对照 ----------
rows1 = []
for mut_dry, v_mcsm in mcsm.items():
    wk = to_wet_key(mut_dry)
    if wk not in wet: continue
    rows1.append(dict(
        dry=mut_dry, wet_key=wk, resi=wet[wk]["resi"],
        mcsm=v_mcsm, prem=prem.get(mut_dry),
        ratio=wet[wk]["ratio"], retain=wet[wk]["retain"], active=wet[wk]["active"],
    ))
# 排名（干：mCSM 降序；湿：+1比 降序）
rows1.sort(key=lambda x: -x["mcsm"])
for i, r in enumerate(rows1, 1): r["mcsm_rank"] = i
tmp = sorted(rows1, key=lambda x: -x["ratio"])
for i, r in enumerate(tmp, 1): r["wet_rank"] = i
for r in rows1:
    r["rank_diff"] = r["wet_rank"] - r["mcsm_rank"]
    d = r["rank_diff"]
    if d >= 3:
        r["verdict"] = f"✗ 干高估（干第{r['mcsm_rank']}→湿第{r['wet_rank']}）"
    elif d <= -3:
        r["verdict"] = f"↑ 干低估（干第{r['mcsm_rank']}→湿第{r['wet_rank']}）"
    else:
        r["verdict"] = f"○ 大致一致（差 {abs(d)} 名）"

# ---------- Sheet2：位点级对照 ----------
# 干预测依据（来自各分析）
SITE = {
 25:("loop1-N","可动","0.02","MI 1.07（与K30，最高）","mCSM 中性","—"),
 26:("loop1-N","可动","0.04","MI 0.90（与K30）","mCSM 弱","—"),
 27:("loop1-N（−1锚）","慎动","0.82","—","mCSM 无法评分(Gly)","PremPRI 弱(+0.13)"),
 28:("loop1-N（壁）","慎动","0.84","—","mCSM 判别强(swap +1.52)","PremPRI 优保G(+0.23)"),
 29:("＋1 阅读器","可动","0.22","—","★ mCSM swap 最强(+5.36)","—"),
 30:("＋1 阅读器（主）","可动","0.36","MI 0.87（与T31）","★ mCSM swap +2.89","PremPRI 中性(+0.03)"),
 31:("＋1 阅读器（A侧）","慎动","0.82","MI 0.87（与K30）","mCSM 不可靠(RSA=0)","PremPRI 支持排A(+0.29)"),
 32:("±2 位","可动","0.56","—","mCSM +1口径不利","PremPRI 判别但伤G(+0.23)"),
 57:("loop3（催化必需）","禁区","0.67","共进化 MI 最高（0.30）","—","—"),
 58:("loop3（排A）","可动","0.29","MI 0.77（与30H）","—","—"),
 59:("loop3（壁）","可动","0.16","MI 0.88（与K30）","mCSM 保G但中性","PremPRI 优保G(+0.29)"),
 60:("loop3（尾）","可动","0.30","—","mCSM 温和排A(+1.15)","★ PremPRI 判别最强(+0.46)"),
 98:("WS环","慎动","0.91","—","mCSM 不可靠(RSA=0)","—"),
 129:("loop7（头）","可动","0.29","—","—","—"),
 130:("loop7（探针）","可动","0.03","—","—","—"),
 131:("loop7","可动","0.21","MI 0.87（与K30）","—","—"),
 132:("loop7（出口）","可动","0.05","—","★ mCSM 最高(+9.46)","★ PremPRI 最优(+0.36)"),
 133:("loop7（尾）","可动","0.43","—","—","—"),
}
# 湿最佳（取保留≥0.6 中 ratio 最高；否则取 ratio 最高并标注）
from collections import defaultdict
by_pos = defaultdict(list)
for k, v in wet.items():
    by_pos[v["resi"]].append((k, v["ratio"], v["retain"], v["active"]))
rows2 = []
for resi in sorted(by_pos):
    items = sorted(by_pos[resi], key=lambda x: -x[1])
    ok = [x for x in items if x[3]]
    best = (ok[0] if ok else items[0])
    s = SITE.get(resi, ("?","?","?","?","?","?"))
    note = "" if ok else "⚠ 该位点无保留≥60%的可用突变"
    rows2.append([resi, s[0], s[1], s[2], s[3], s[4], s[5],
                  best[0], f"{best[1]:.2f}", f"{best[2]:.2f}",
                  "可用" if best[3] else "不可用", note])
# 湿排名（按最佳可用 ratio）
rows2.sort(key=lambda r: -(float(r[8]) if r[10]=="可用" else 0))
rows2 = [[f"W{i}"] + r for i, r in enumerate(rows2, 1)]

# ---------- Sheet3：预测方法可靠性 ----------
summ = []
# mCSM-NA：与湿实测对照
n = len(rows1)
if n:
    hit5 = sum(1 for r in rows1 if r["mcsm_rank"] <= 5 and r["active"])
    hi5 = sum(1 for r in rows1 if r["mcsm_rank"] <= 5)
    summ.append(["mCSM-NA（combined 分）", f"{n} 个可比突变",
                 f"前 5 名中 {hit5}/{hi5} 个湿实验可用",
                 "✗ 不可靠：把 M132D/E 排为并列第 1，但 M132E 实测最弱（1.18）；且对 G27/S98/T31 无法评分"])
if prem:
    pk = [k for k in prem if to_wet_key(k) in wet]
    hi = sorted(pk, key=lambda k: -prem[k])[:5]
    ok = sum(1 for k in hi if wet[to_wet_key(k)]["active"])
    summ.append(["PremPRI（score）", f"{len(pk)} 个可比突变",
                 f"前 5 名中 {ok}/{len(hi)} 个湿实验可用",
                 "✗ 不可靠：把 M132E 排第 2（实测 1.18 最弱），并把 D/E 优劣判反"])
summ.append(["共进化 MI（位点对）", "351 对",
             "头部对（25–30 = 1.07、30–58 = 0.77）在组合中均被证实有协同",
             "✓ 部分可靠：用于「选哪些位点配」有参考价值，但不预测幅度"])
summ.append(["CP / ΔCP（突变体重测）", "22 个突变体",
             "正确区分 K30H（H29 保G增强）与 M132D/E（ΔCP 不变，出口通道）",
             "✓ 可靠：用于机制判别，不用于排序"])
summ.append(["Δd_E72 几何指标", "22 个突变体",
             "与实测 +1比 回归 r = −0.073（95%CI −0.600~+0.498）",
             "✗ 失败：GCA 侧 AF3 噪声（SD 2.3–3.9 Å）使信度≈0；仅分层后有效（单点 +0.67 / 组合 −0.72）"])
summ.append(["加性先验模型（MI+空间+单点+保守）", "8 组组合",
             "与实测 +1比 r = +0.138",
             "✗ 失败：组合存在显著上位性，线性加和不可外推"])
summ.append(["相乘模型（est_ratio，1000 组）", "1902→1000 组",
             "Top1 G27D+K30H+M132D 未实测；实测最优 27T-30H-58M 在预测中并非首位",
             "✗ 不可靠：仅排序参考，误差 ±30–50%"])
summ.append(["结构接触（距离/氢键/埋藏）", "300 结构",
             "锁定 H29/K30 为 +1 读取器（✓）；但预测 T31 为排A靶点（✗ 实测无效）",
             "◐ 半可靠：定位「谁参与」可靠，判断「改了有没有用」不可靠"])
summ.append(["全局脱靶 / GCG 靶向比（本轮新增）", "117 样本",
             "亲本靶向比 0.93，最佳组合 30H-58M 达 1.87 且保活性 78%（与单位点偏好比一致）",
             "✓ 可靠：两个独立指标（偏好比、靶向比）在头部候选上互相验证"])

# ---------- 输出 ----------
wb = Workbook()
thin = Side(style="thin", color="BBBBBB"); bd = Border(left=thin,right=thin,top=thin,bottom=thin)
def style(ws, widths):
    for j in range(1, ws.max_column+1):
        c = ws.cell(row=1, column=j)
        c.font = Font(bold=True, color="FFFFFF", size=10)
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = bd
    for i in range(2, ws.max_row+1):
        for j in range(1, ws.max_column+1):
            c = ws.cell(row=i, column=j)
            c.font = Font(size=9); c.alignment = Alignment(vertical="top", wrap_text=True); c.border = bd
            if i % 2 == 0: c.fill = PatternFill("solid", fgColor=LIGHT)
    for col, w in zip("ABCDEFGHIJKLM", widths): ws.column_dimensions[col].width = w

ws = wb.active; ws.title = "1_突变级对照"
ws.append(["干预测排名","突变(干)","突变(湿)","位点","mCSM combined","干序位",
           "PremPRI","湿 +1比","湿 保留率","湿序位","名次差(湿−干)","一致性判定"])
ws.append([])
for r in sorted(rows1, key=lambda x: x["mcsm_rank"]):
    ws.append([r["mcsm_rank"], r["dry"], r["wet_key"], r["resi"],
               round(r["mcsm"],2), r["mcsm_rank"],
               round(r["prem"],2) if r["prem"] is not None else "—",
               round(r["ratio"],2), round(r["retain"],2), r["wet_rank"],
               r["rank_diff"], r["verdict"]])
ws.delete_rows(2)
style(ws, [10,10,10,6,12,8,9,9,9,8,11,22])

ws2 = wb.create_sheet("2_位点级对照")
ws2.append(["湿排名","位点","位点分类","可动性","保守性(WT频率)","共进化 MI","mCSM-NA 预测",
            "PremPRI 预测","湿最佳突变","+1比","保留率","可用性","备注"])
for r in rows2: ws2.append(r)
style(ws2, [7,5,17,7,12,20,20,18,11,7,7,8,26])

ws3 = wb.create_sheet("3_预测方法可靠性")
ws3.append(["预测手段","数据量","与湿实验的一致性","结论（可靠/不可靠）"])
for r in summ: ws3.append(r)
style(ws3, [30,16,50,60])

wb.save("results/干湿排序对照表.xlsx")
print("写入 results/干湿排序对照表.xlsx")

# ---------- 控制台 ----------
print("\n" + "="*104)
print("表1  突变级：干预测（mCSM-NA）排名 vs 湿实测（+1比）排名")
print("="*104)
print(f"{'干排名':>5}{'突变':<7}{'mCSM':>7}{'湿+1比':>8}{'保留':>7}{'湿排名':>7}{'名次差':>7}  判定")
for r in sorted(rows1, key=lambda x: x["mcsm_rank"]):
    print(f"{r['mcsm_rank']:>5}{r['wet_key']:<7}{r['mcsm']:>7.2f}{r['ratio']:>8.2f}"
          f"{r['retain']:>7.2f}{r['wet_rank']:>7}{r['rank_diff']:>+7}  {r['verdict']}")
if rows1:
    diffs = [abs(r["rank_diff"]) for r in rows1]
    print(f"\n平均绝对名次差 = {statistics.mean(diffs):.1f}（随机预期 ≈ {len(rows1)/3:.1f}）")
    sp = sum(1 for r in rows1 if r["verdict"].startswith("✓")) / len(rows1)
    agree = sum(1 for r in rows1 if abs(r["rank_diff"]) <= 2) / len(rows1)
    print(f"名次差 ≤2（大致一致）比例 = {agree:.0%}")
    print("关键错配：")
    for r in sorted(rows1, key=lambda x: -abs(x["rank_diff"]))[:4]:
        print(f"  {r['wet_key']}：干第 {r['mcsm_rank']} → 湿第 {r['wet_rank']}"
              f"（+1比 {r['ratio']:.2f} / 保留 {r['retain']:.2f}）")

print("\n" + "="*104)
print("表2  湿实验验证的最佳位点排序（保留≥60% 优先）")
print("="*104)
print(f"{'排名':>4}{'位点':<5}{'位点分类':<18}{'可动性':<7}{'湿最佳':<7}{'+1比':>7}{'保留':>7}  可用性")
for r in rows2:
    print(f"{r[0]:>4}{r[1]:<5}{r[2]:<18}{r[3]:<7}{r[8]:<7}{r[9]:>7}{r[10]:>7}  {r[11]}")

print("\n" + "="*104)
print("表3  预测方法可靠性汇总")
print("="*104)
for r in summ:
    print(f"\n【{r[0]}】{r[1]}")
    print(f"   一致性：{r[2]}")
    print(f"   结论：{r[3]}")
