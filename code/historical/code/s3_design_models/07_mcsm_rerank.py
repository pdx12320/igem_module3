# -*- coding: utf-8 -*-
"""
阶段 7 —— mCSM-NA 结果解读与重新排序（单体 + 组合）

mCSM-NA 符号约定（官方 Help）：正 ΔΔG = 增强结合（保），负 ΔΔG = 减弱结合（排）。
即「保G排A」要求：对 GUGCGCG 的 ΔΔG 偏正（保G），对 A 结构的 ΔΔG 偏负（排A）。

判别分数（越高越「保G排A」）：
  score_swap = dG - dA_swap   （纯 +1 判别，用高置信度 GUGCGCG/GUGCACG 对）
  score_off  = dG - dA_off    （临床脱靶判别，GUGCGCG vs AUGCAGC，结构置信度较低）

产出：
  results/mcsm_single_rerank.csv
  results/mcsm_combos_rerank.csv
"""
import os
import csv

RAW = "results/mcsmna_raw"
OUT = "results"

# 可靠性判定：RSA=0 且 |ΔΔG|>5 视为模型外推不可靠
UNRELIABLE_THRESHOLD = 5.0

# 读取三份 mCSM-NA 结果
def read_mcsm(path):
    muts = {}
    with open(path, encoding="utf-8") as f:
        header = None
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == "PDB_FILE":
                header = parts
                continue
            if len(parts) < 7:
                continue
            # PDB_FILE CHAIN WILD_RES RES_POS MUT_RES RSA PRED_DDG
            chain, wt, pos, mt, rsa, ddg = parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
            key = f"{wt}{pos}{mt}"
            muts[key] = {"rsa": float(rsa), "ddg": float(ddg)}
    return muts

G = read_mcsm(os.path.join(RAW, "GUGCGCG.txt"))
SWAP = read_mcsm(os.path.join(RAW, "GUGCACG.txt"))
OFF = read_mcsm(os.path.join(RAW, "AUGCAGC.txt"))

# 汇总单体
all_keys = sorted(set(G) | set(SWAP) | set(OFF))
single = []
for k in all_keys:
    dG = G.get(k, {}).get("ddg")
    dAsw = SWAP.get(k, {}).get("ddg")
    dAoff = OFF.get(k, {}).get("ddg")
    rsa = G.get(k, {}).get("rsa")
    if dG is None or dAsw is None or dAoff is None:
        continue
    score_swap = dG - dAsw
    score_off = dG - dAoff
    # 可靠性：任一结构 RSA=0 且 |ΔΔG| 过大
    unreliable = (rsa is not None and rsa == 0.0) and (
        max(abs(dG), abs(dAsw), abs(dAoff)) > UNRELIABLE_THRESHOLD)
    single.append({
        "mut": k, "dG": round(dG, 2), "dA_swap": round(dAsw, 2), "dA_off": round(dAoff, 2),
        "rsa": rsa, "score_swap": round(score_swap, 2), "score_off": round(score_off, 2),
        "combined": round(score_swap + score_off, 2),
        "unreliable": unreliable,
    })

single.sort(key=lambda r: -r["combined"])

fields = ["mut", "dG", "dA_swap", "dA_off", "rsa", "score_swap", "score_off",
          "combined", "unreliable"]
with open(os.path.join(OUT, "mcsm_single_rerank.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in single:
        w.writerow({k: (r[k] if r[k] != "" else "") for k in fields})

print("== 单体重新排序（按 score_swap = dG - dA_swap，正值=保G排A）==")
print(f"{'突变':<7} {'dG':>7} {'dA_swap':>8} {'dA_off':>8} {'score_swap':>10} {'score_off':>9}  备注")
for r in single:
    note = "不可靠(RSA=0外推)" if r["unreliable"] else ""
    print(f"{r['mut']:<7} {r['dG']:>7} {r['dA_swap']:>8} {r['dA_off']:>8} "
          f"{r['score_swap']:>10} {r['score_off']:>9}  {note}")

# ---- 组合重新排序（加和近似）----
# 可靠突变池：排除不可靠的 T31*/S98A（G27 因 mCSM-NA 无法对 Gly 评分，本就不在数据中）
pool = [r for r in single if not r["unreliable"]]

from itertools import combinations

combos = []
for k in (2, 3):
    for c in combinations(pool, k):
        # 位点号：突变串形如 "K30H" -> 中间数字
        def pos(mut):
            return int("".join(ch for ch in mut[1:-1] if ch.isdigit()))
        if len(set(pos(r["mut"]) for r in c)) != k:
            continue
        label = "+".join(sorted(r["mut"] for r in c))
        s_swap = sum(r["score_swap"] for r in c)
        s_off = sum(r["score_off"] for r in c)
        ddG_G = sum(r["dG"] for r in c)
        combos.append({
            "mutations": label, "n": k, "score_swap": round(s_swap, 2),
            "score_off": round(s_off, 2), "combined": round(s_swap + s_off, 2),
            "dG_sum": round(ddG_G, 2),
        })

combos.sort(key=lambda r: -r["combined"])

cf = ["mutations", "n", "score_swap", "score_off", "combined", "dG_sum"]
with open(os.path.join(OUT, "mcsm_combos_rerank.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cf)
    w.writeheader()
    for r in combos:
        w.writerow({k: r[k] for k in cf})

print(f"\n== 组合重新排序：可靠突变池 {len(pool)} 个 -> {len(combos)} 组（2/3 位点）==")
print("前 20 组：")
for r in combos[:20]:
    print(f"  {r['mutations']:<32} score_swap={r['score_swap']:>7}  score_off={r['score_off']:>7}")

print(f"\n写入 results/mcsm_single_rerank.csv, results/mcsm_combos_rerank.csv")
