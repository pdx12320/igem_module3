# -*- coding: utf-8 -*-
"""
阶段 9 —— 学姐第一批单位点饱和实验数据 重新分析 + 计算预测交叉验证

数据：ACA_295(脱靶) / GCG_388(on-target) / GCA_871(+1=A脱靶)，每个突变 2 重复。
指标：
  on-target 保留率 = GCG_mut / GCG_WT
  +1 比(保G排A) = GCG_388 / GCA_871   （WT=1.37，越高越特异）
产出：results/experimental_ranking.csv、results/cross_validation.csv
"""
import csv
import statistics
import openpyxl

SRC = r"data\external\01a06031-d7d4-72cf-a2a5-f46d90d768dd.xlsx"
OUT = "results"

wb = openpyxl.load_workbook(SRC, data_only=True)
ws = wb["Sheet1"]
dp = wb["测序深度"]

data, depth = {}, {}
for row in ws.iter_rows(values_only=True):
    if row[0] is None or row[1] is None:
        continue
    n = str(row[0]).strip()
    if n == "ACA_295":
        continue
    data.setdefault(n, []).append((row[1], row[2], row[3]))
for row in dp.iter_rows(values_only=True):
    if row[0] is None or row[1] is None:
        continue
    n = str(row[0]).strip()
    if n == "ACA_295_DP":
        continue
    depth.setdefault(n, []).append((row[1], row[2], row[3]))


def mean(xs):
    return statistics.mean(xs)


wt = next(mean([r[1] for r in reps]) for n, reps in data.items() if "WT" in n)
wt_gca = next(mean([r[2] for r in reps]) for n, reps in data.items() if "WT" in n)

rows = []
for n, reps in data.items():
    gcg = mean([r[1] for r in reps])
    gca = mean([r[2] for r in reps])
    aca = mean([r[0] for r in reps])
    ratio = gcg / gca if gca else 0
    retain = gcg / wt
    d = depth.get(n)
    mindp = min(min(x) for x in d) if d else None
    rows.append(dict(mut=n, GCG=round(gcg, 3), GCA=round(gca, 3), ACA=round(aca, 3),
                     ratio=round(ratio, 2), retain=round(retain, 2),
                     depth=mindp, active=retain >= 0.7))

rows.sort(key=lambda r: (-r["ratio"]))

# 全排名（保留活跃） + 探针（活性崩但高比）
with open(f"{OUT}/experimental_ranking.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["mut", "GCG", "GCA", "ACA", "ratio", "retain", "depth", "active"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

# 交叉验证
CAND = [("M132E", "132E"), ("M132D", "132D"), ("K30H", "30H"), ("K30N", "30N"),
        ("G27D", "27D"), ("G27T", "27T"), ("G27V", "27V"), ("G27I", "27I"),
        ("T31A", "31A"), ("T31C", "31C"), ("A59S", "59S"), ("K60H", "60H"),
        ("R28W", "28W"), ("25E", "25E"), ("58M", "58M")]
cv = []
for label, key in CAND:
    if key not in data:
        cv.append(dict(cand=label, exp="未测试", ratio="", retain="", verdict="未覆盖"))
        continue
    reps = data[key]
    gcg = mean([r[1] for r in reps]); gca = mean([r[2] for r in reps])
    ratio = gcg / gca if gca else 0; retain = gcg / wt
    verdict = "✓证实" if (ratio > wt / wt_gca and retain >= 0.7) else ("✗证伪/无改善" if ratio <= wt / wt_gca else "活性偏低(探针)")
    cv.append(dict(cand=label, exp=key, ratio=round(ratio, 2), retain=f"{retain:.0%}", verdict=verdict))

with open(f"{OUT}/cross_validation.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["cand", "exp", "ratio", "retain", "verdict"])
    w.writeheader()
    w.writerows(cv)

print(f"WT 基线: GCG={wt:.3f} GCA={wt_gca:.3f}  +1比={wt/wt_gca:.2f}")
print(f"\n=== 活跃(保留≥70%)突变按 +1比 排序 前 15 ===")
for r in [x for x in rows if x["active"]][:15]:
    print(f"  {r['mut']:<8} GCG={r['GCG']:.3f} GCA={r['GCA']:.3f} ACA={r['ACA']:.3f} "
          f"+1比={r['ratio']:.2f} 保留={r['retain']:.0%}")
print(f"\n=== 计算候选 交叉验证 ===")
for r in cv:
    print(f"  {r['cand']:<8} 实验{r['exp']:<5} +1比={r['ratio']:<5} 保留={r['retain']:<5} {r['verdict']}")
print(f"\n写入 {OUT}/experimental_ranking.csv, {OUT}/cross_validation.csv")
