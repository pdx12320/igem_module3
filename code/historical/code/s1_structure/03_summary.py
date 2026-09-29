# -*- coding: utf-8 -*-
"""
阶段 3 —— 汇总统计与 G/A 对比

读取 results/contacts_long.csv，产出：
  results/contacts_frequency.csv —— 每 (RNA × 蛋白残基) 的接触频率 + 距离中位数
  results/g_a_comparison.csv    —— 同一残基在 G 组 vs A 组的接触频率对比

分组口径：
  GUGCGCG  = "+1=G"（on-target）
  GUGCACG  = "+1=A"（纯 +1 交换，主对照）
  AUGCAGC  = "+1=A"（871 脱靶，侧翼不同，作补充）
  A_pooled = GUGCACG + AUGCAGC
"""
import os
import csv
from collections import defaultdict

import af_utils as U

OUT_DIR = "results"

RNA_GROUPS = {
    "GUGCGCG": "+1=G (on)",
    "GUGCACG": "+1=A (swap)",
    "AUGCAGC": "+1=A (off)",
}
G_RNA = "GUGCGCG"
A_PURE = "GUGCACG"
A_OFF = "AUGCAGC"
A_POOL = [A_PURE, A_OFF]


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return None
    if n % 2:
        return xs[n // 2]
    return (xs[n // 2 - 1] + xs[n // 2]) / 2.0


# 读取
data = defaultdict(lambda: defaultdict(lambda: {"n": 0, "n_base5": 0, "n_full5": 0,
                                                "n_base4": 0, "n_base3p5": 0,
                                                "dists_base": [], "dists_full": []}))
resn_map = {}

with open(os.path.join(OUT_DIR, "contacts_long.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        rna = row["rna"]
        resi = int(row["resi"])
        resn_map[resi] = row["resn"]
        d = data[rna][resi]
        d["n"] += 1
        if row["contact_base_5.0"] == "True":
            d["n_base5"] += 1
        if row["contact_base_4.0"] == "True":
            d["n_base4"] += 1
        if row["contact_base_3.5"] == "True":
            d["n_base3p5"] += 1
        if row["contact_full_5.0"] == "True":
            d["n_full5"] += 1
        if row["min_dist_base"] != "":
            d["dists_base"].append(float(row["min_dist_base"]))
        if row["min_dist_full"] != "":
            d["dists_full"].append(float(row["min_dist_full"]))

# 1) 频率表
freq_rows = []
for rna in U.RNA_SEQS:
    for resi in sorted(data[rna]):
        d = data[rna][resi]
        n = d["n"]
        freq_rows.append({
            "rna": rna, "resi": resi, "resn": resn_map[resi],
            "n_model": n,
            "freq_base_3.5": round(d["n_base3p5"] / n, 3),
            "freq_base_4.0": round(d["n_base4"] / n, 3),
            "freq_base_5.0": round(d["n_base5"] / n, 3),
            "freq_full_5.0": round(d["n_full5"] / n, 3),
            "median_min_dist_base": ("" if not d["dists_base"] else round(median(d["dists_base"]), 3)),
            "median_min_dist_full": ("" if not d["dists_full"] else round(median(d["dists_full"]), 3)),
        })

freq_fields = ["rna", "resi", "resn", "n_model",
               "freq_base_3.5", "freq_base_4.0", "freq_base_5.0", "freq_full_5.0",
               "median_min_dist_base", "median_min_dist_full"]
with open(os.path.join(OUT_DIR, "contacts_frequency.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=freq_fields)
    w.writeheader()
    w.writerows(freq_rows)

# 2) G/A 对比表
def freq(rna, resi, key):
    d = data[rna].get(resi)
    if not d or d["n"] == 0:
        return 0.0
    return d[key] / d["n"]

all_resi = set()
for rna in U.RNA_SEQS:
    all_resi |= set(data[rna].keys())

comp_rows = []
for resi in sorted(all_resi):
    fG = freq(G_RNA, resi, "n_base5")
    fA_pure = freq(A_PURE, resi, "n_base5")
    fA_off = freq(A_OFF, resi, "n_base5")
    # pooled A：合并两个 A 组的计数
    nA = data[A_PURE].get(resi, {}).get("n_base5", 0) + data[A_OFF].get(resi, {}).get("n_base5", 0)
    nA_total = data[A_PURE].get(resi, {}).get("n", 0) + data[A_OFF].get(resi, {}).get("n", 0)
    fA_pool = (nA / nA_total) if nA_total else 0.0

    comp_rows.append({
        "resi": resi, "resn": resn_map[resi],
        "freq_G": round(fG, 3),
        "freq_A_swap": round(fA_pure, 3),
        "freq_A_off": round(fA_off, 3),
        "freq_A_pooled": round(fA_pool, 3),
        "delta_G_minus_Aswap": round(fG - fA_pure, 3),
        "delta_G_minus_Apooled": round(fG - fA_pool, 3),
    })

comp_fields = ["resi", "resn", "freq_G", "freq_A_swap", "freq_A_off",
               "freq_A_pooled", "delta_G_minus_Aswap", "delta_G_minus_Apooled"]
with open(os.path.join(OUT_DIR, "g_a_comparison.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=comp_fields)
    w.writeheader()
    w.writerows(comp_rows)

# 控制台：打印 +1 碱基接触频率前 20 的残基（按 G 组频率）
print("== +1 碱基(≤5Å)接触频率：按 G 组(GCG)排序的前 20 个蛋白残基 ==")
print(f"{'resi':>5} {'resn':>4} {'G(on)':>7} {'A(swap)':>8} {'A(off)':>8} {'ΔG-A':>7}")
top = sorted(comp_rows, key=lambda r: -r["freq_G"])[:20]
for r in top:
    print(f"{r['resi']:>5} {r['resn']:>4} {r['freq_G']:>7} {r['freq_A_swap']:>8} "
          f"{r['freq_A_off']:>8} {r['delta_G_minus_Aswap']:>7}")

print(f"\n== 关键残基 G/A 对比 ==")
print(f"{'resi':>5} {'resn':>4} {'G(on)':>7} {'A(swap)':>8} {'A(off)':>8} {'ΔG-A':>7}")
for r in comp_rows:
    if r["resi"] in U.KEY_RESIDUES:
        print(f"{r['resi']:>5} {r['resn']:>4} {r['freq_G']:>7} {r['freq_A_swap']:>8} "
              f"{r['freq_A_off']:>8} {r['delta_G_minus_Aswap']:>7}")

print("\n写入 results/contacts_frequency.csv, results/g_a_comparison.csv")
