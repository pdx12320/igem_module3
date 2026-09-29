# -*- coding: utf-8 -*-
"""
阶段 14 —— 共进化筛选组合突变位点（初步可行性评估）

思想：若两个位点在进化上共变（互信息 MI 高），说明它们功能耦合，突变时需协同考虑，
     可能是组合突变的候选位点对（尤其与 +1 识别环 K30/H29/T31/Q58 共变的位点）。
方法：从 AF3 MSA 计算候选位点间的成对互信息(MI)，找高耦合位点对。
"""
import csv
import math
from collections import Counter

import numpy as np

A3M = "GUGCGCG_20/001/msas/fold_001_paired_msa_chains_a.a3m"
AA = "ACDEFGHIKLMNPQRSTVWY-"
AA_IDX = {aa: i for i, aa in enumerate(AA)}

# 候选位点（+1/-1 识别环 + 催化核心 + 已饱和区）
CAND = [25, 26, 27, 28, 29, 30, 31, 32, 56, 57, 58, 59, 60,
        67, 68, 69, 70, 72, 98, 99, 102, 105, 129, 130, 131, 132, 133]
# 关键 +1 识别残基
READERS = {30: "K30", 29: "H29", 31: "T31", 58: "Q58"}


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
    aligned = [s for s in ["".join(ch for ch in "".join(s) if not ch.islower()).replace(".", "-") for s in seqs]
               if len(s) == len(query)]
    return query, aligned


query, aligned = read_a3m(A3M)
L = len(query)
M = np.array([[AA_IDX.get(ch, 20) for ch in s] for s in aligned], dtype=np.int32)
N = len(M)


def mi(a, b):
    idx = a * 21 + b
    joint = np.bincount(idx, minlength=441).astype(float)
    joint /= joint.sum()
    pa = np.bincount(a, minlength=21).astype(float); pa /= pa.sum()
    pb = np.bincount(b, minlength=21).astype(float); pb /= pb.sum()
    v = 0.0
    for i in range(21):
        for k in range(21):
            p = joint[i * 21 + k]
            if p > 0:
                v += p * math.log(p / (pa[i] * pb[k]))
    return v


# 成对 MI
pairs = []
pos_set = CAND
for i, pi in enumerate(pos_set):
    for pj in pos_set[i + 1:]:
        m = mi(M[:, pi - 1], M[:, pj - 1])
        pairs.append((pi, pj, m))

pairs.sort(key=lambda x: -x[2])

print(f"MSA: {N} 条序列。候选 {len(pos_set)} 位点成对互信息(MI) 前 20：")
print(f"{'位点对':>10} {'MI':>7}   (wt->wt)")
for pi, pj, m in pairs[:20]:
    print(f"{pi:>3}-{pj:<3} {m:>7.4f}   {query[pi-1]}->{query[pj-1]}")

print(f"\n== 与 +1 识别残基共变最强的位点（组合位点候选）==")
for rp, rn in READERS.items():
    coupled = [(pj, m) for (pi, pj, m) in pairs if pi == rp or pj == rp]
    coupled.sort(key=lambda x: -x[1])
    top = " ".join(f"{pj}({m:.3f})" for pj, m in coupled[:6])
    print(f"  {rn}({rp}): {top}")

# 保存
with open("results/coevolution_pairs.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["pos1", "pos2", "MI", "wt1", "wt2"])
    for pi, pj, m in pairs:
        w.writerow([pi, pj, round(m, 4), query[pi-1], query[pj-1]])
print("\n写入 results/coevolution_pairs.csv")
