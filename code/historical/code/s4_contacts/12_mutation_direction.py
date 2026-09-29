# -*- coding: utf-8 -*-
"""
阶段 12 —— 可突变残基的「突变方向」分析（PSSM 序列谱）

思想：某位点「同源可突变」只是说它身份可变；但 MSA 中该位点的氨基酸分布(PSSM)
给出了「允许/不允许」的具体方向：
  - 家族中出现频率较高的 AA = 可突变方向（进化上被允许）
  - 频率≈0 的 AA = 不可突变方向（进化上被排除，往往导致失活）

产出：results/pssm_direction.csv（候选位点 × 全部 AA 频率）
"""
import os
import csv
from collections import Counter

AA = "ACDEFGHIKLMNPQRSTVWY"

A3M = "GUGCGCG_20/001/msas/fold_001_paired_msa_chains_a.a3m"

# 候选位点（接触 +1/-1 碱基 或 实验做过饱和的）
CAND = [27, 28, 29, 30, 31, 32, 57, 58, 59, 60, 98, 132]


def read_a3m(path):
    seqs, cur = [], None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if cur is not None:
                    seqs.append(cur)
                cur = []
            elif cur is not None:
                cur.append(line)
    if cur is not None:
        seqs.append(cur)
    query = "".join(seqs[0]).upper()
    aligned = []
    for s in seqs:
        clean = "".join(ch for ch in "".join(s) if not ch.islower()).replace(".", "-")
        aligned.append(clean)
    return query, [s for s in aligned if len(s) == len(query)]


query, aligned = read_a3m(A3M)
L = len(query)
N = len(aligned)

# 每个位点的 AA 分布（去 gap）
pssm = {}
for j in range(L):
    cnt = Counter(aligned[i][j] for i in range(N) if aligned[i][j] != "-")
    tot = sum(cnt.values())
    pssm[j + 1] = {aa: cnt.get(aa, 0) / tot for aa in AA}

rows = []
for resi in CAND:
    dist = pssm[resi]
    ordered = sorted(dist.items(), key=lambda kv: -kv[1])
    row = dict(resi=resi, wt=query[resi - 1])
    for aa, f in ordered:
        row[aa] = round(f, 4)
    rows.append(row)

with open("results/pssm_direction.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["resi", "wt"] + list(AA))
    w.writeheader()
    for r in rows:
        w.writerow(r)

# 打印：每个候选位点 前5 AA + 是否含 D/E/K/R/Y（带电/大芳香）
PROP = {
    "D": "带电(-)", "E": "带电(-)", "K": "带电(+)", "R": "带电(+)",
    "Y": "大芳香", "W": "大芳香", "F": "大芳香",
}
print(f"MSA: {N} 条同源。候选位点氨基酸分布（前5）+ 关键'危险方向'在家族中的频率")
print(f"{'resi':>4} {'wt':>3} | 前5分布                                    | 带电/大方向在家族频率")
for r in rows:
    resi, wt = r["resi"], r["wt"]
    top = sorted(((aa, r[aa]) for aa in AA), key=lambda kv: -kv[1])[:5]
    tops = " ".join(f"{aa}{r[aa]*100:.0f}%" for aa, _ in top)
    dangers = []
    for aa in "DEKRYWF":
        if r[aa] > 0:
            dangers.append(f"{aa}{r[aa]*100:.0f}%")
        else:
            dangers.append(f"{aa}0%")
    print(f"{resi:>4} {wt:>3} | {tops:<42} | {' '.join(dangers)}")
