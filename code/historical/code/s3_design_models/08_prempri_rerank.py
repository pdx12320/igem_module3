# -*- coding: utf-8 -*-
"""
阶段 8 —— PremPRI 结果解读与重新排序（单体 + 组合）

PremPRI 主列（ΔΔG，kcal/mol）：正 = 减弱结合（排），负 = 增强（保）[官方 Help]。
「保G排A」要求：对 GUGCGCG 的 ΔΔG 小（保G，尽量不破坏 on-target），
                对 GUGCACG/AUGCAGC 的 ΔΔG 大（排A，破坏 off-target）。

判别分数（越高越「保G排A」）：
  score_swap = dA_swap - dG
  score_off  = dA_off  - dG
  score      = (dA_swap + dA_off)/2 - dG   （平均排A − 排G，主排序）

组合：加和近似，附加「保G」筛选：组合总 dG（on-target 破坏）≤ 阈值。

产出：results/prempri_single_rerank.csv, results/prempri_combos_rerank.csv
"""
import os
import csv
from itertools import combinations

RAW = "results"
OUT = "results"

# 保G 筛选阈值（组合总 on-target ΔΔG 上限）
DG_COMBO_MAX = 3.0


def read_prempri(path):
    muts = {}
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            parts = line.split()
            if i == 0 or not parts:
                continue
            if parts[1] == "Mutation":   # 表头（Mutated Chain / Mutation / ...）
                continue
            # [0]=chain, [1]=mutation, [2]=PremPRI(ΔΔG), [3]=Interface?
            muts[parts[1]] = float(parts[2])
    return muts


G = read_prempri(os.path.join(RAW, "GUGCGCG.txt"))
SWAP = read_prempri(os.path.join(RAW, "GUGCACG.txt"))
OFF = read_prempri(os.path.join(RAW, "AUGCAGC.txt"))

all_keys = sorted(set(G) | set(SWAP) | set(OFF))
single = []
for k in all_keys:
    dG = G.get(k)
    dAsw = SWAP.get(k)
    dAoff = OFF.get(k)
    if dG is None or dAsw is None or dAoff is None:
        continue
    score = (dAsw + dAoff) / 2 - dG
    single.append({
        "mut": k, "dG": round(dG, 2), "dA_swap": round(dAsw, 2), "dA_off": round(dAoff, 2),
        "score_swap": round(dAsw - dG, 2), "score_off": round(dAoff - dG, 2),
        "score": round(score, 3),
        "保G": "优(ΔΔG≤1.0)" if dG <= 1.0 else ("中(≤1.5)" if dG <= 1.5 else "差(>1.5)"),
    })

single.sort(key=lambda r: -r["score"])

fields = ["mut", "dG", "dA_swap", "dA_off", "score_swap", "score_off", "score", "保G"]
with open(os.path.join(OUT, "prempri_single_rerank.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in single:
        w.writerow(r)

print("== 单体重新排序（score = 平均排A − 排G，正值=保G排A）==")
print(f"{'突变':<7} {'dG':>6} {'dA_swap':>8} {'dA_off':>8} {'score_swap':>10} {'score_off':>9} {'score':>7}  保G")
for r in single:
    print(f"{r['mut']:<7} {r['dG']:>6} {r['dA_swap']:>8} {r['dA_off']:>8} "
          f"{r['score_swap']:>10} {r['score_off']:>9} {r['score']:>7}  {r['保G']}")

# ---- 组合重新排序 ----
def pos(mut):
    return int("".join(ch for ch in mut[1:-1] if ch.isdigit()))

pool = single
combos = []
for k in (2, 3):
    for c in combinations(pool, k):
        if len(set(pos(r["mut"]) for r in c)) != k:
            continue
        label = "+".join(sorted(r["mut"] for r in c))
        dG_sum = sum(r["dG"] for r in c)
        s_swap = sum(r["score_swap"] for r in c)
        s_off = sum(r["score_off"] for r in c)
        score = sum(r["score"] for r in c)
        combos.append({
            "mutations": label, "n": k, "dG_sum": round(dG_sum, 2),
            "score": round(score, 2), "score_swap": round(s_swap, 2), "score_off": round(s_off, 2),
            "保G_pass": dG_sum <= DG_COMBO_MAX,
        })

combos.sort(key=lambda r: (-r["保G_pass"], -r["score"]))

cf = ["mutations", "n", "dG_sum", "score", "score_swap", "score_off", "保G_pass"]
with open(os.path.join(OUT, "prempri_combos_rerank.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cf)
    w.writeheader()
    for r in combos:
        w.writerow(r)

n_pass = sum(1 for r in combos if r["保G_pass"])
print(f"\n== 组合重新排序：{len(pool)} 单点 -> {len(combos)} 组；保G通过(dG_sum≤{DG_COMBO_MAX}) {n_pass} 组 ==")
print("前 20 组（保G通过优先，再按 score）：")
for r in combos[:20]:
    print(f"  {r['mutations']:<30} dG_sum={r['dG_sum']:>5} score={r['score']:>6} "
          f"sw={r['score_swap']:>6} off={r['score_off']:>6}  {'✓' if r['保G_pass'] else '✗'}")

print(f"\n写入 results/prempri_single_rerank.csv, results/prempri_combos_rerank.csv")
