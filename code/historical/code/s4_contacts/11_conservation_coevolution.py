# -*- coding: utf-8 -*-
"""
阶段 11 —— 序列保守性 + 共进化分析（回答「某位点能否突变」）

数据源：AF3 输出的 APOBEC 家族 MSA（a3m，3504 条同源序列）。
  - 保守性：每个位点的 野生型残基频率 与 归一化香农熵（低=保守=大概率不能动）。
  - 共进化：每个位点与催化核心(N57/H70/E72/C102/C105)的互信息(MI)，
             MI 高 = 与核心共进化 = 功能耦合，不能独立突变。

产出：results/conservation.csv、results/coevolution_with_core.csv
"""
import os
import csv
import math
from collections import Counter

import numpy as np

OUT = "results"

A3M = "GUGCGCG_20/001/msas/fold_001_paired_msa_chains_a.a3m"

# 催化核心（共进化参照）
CORE = [57, 70, 72, 102, 105]   # 1-based

AA = "ACDEFGHIKLMNPQRSTVWY-"
AA_IDX = {aa: i for i, aa in enumerate(AA)}


def read_a3m(path):
    """解析 a3m，返回 (query_seq, [aligned_seqs])，去掉小写插入，按 query 对齐。"""
    seqs = []
    headers = []
    cur = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith(">"):
                headers.append(line)
                if cur is not None:
                    seqs.append(cur)
                cur = []
            else:
                if cur is None:
                    continue
                cur.append(line)
    if cur is not None:
        seqs.append(cur)
    # 拼合每段（可能多行），去掉小写插入
    aligned = []
    query = "".join(seqs[0]).upper()
    for s in seqs:
        raw = "".join(s)
        clean = "".join(ch for ch in raw if not ch.islower())
        aligned.append(clean.replace(".", "-"))
    return query, aligned


query, aligned = read_a3m(A3M)
L = len(query)
n = len(aligned)
print(f"query 长度={L}  序列数={n}")

# 验证对齐长度
lens = Counter(len(s) for s in aligned)
bad = {k: v for k, v in lens.items() if k != L}
if bad:
    print("⚠ 部分序列对齐长度异常(非199):", bad)
# 只保留长度==L 的序列
aligned = [s for s in aligned if len(s) == L]

# 编码为整数矩阵
M = np.array([[AA_IDX.get(ch, 20) for ch in s] for s in aligned], dtype=np.int32)
N, L = M.shape
print(f"用于分析：{N} 条 × {L} 列")

# ---- 保守性 ----
conservation = []
for j in range(L):
    col = M[:, j]
    wt = query[j]
    wt_i = AA_IDX[wt]
    n_nongap = int((col != 20).sum())
    gap_frac = float((col == 20).mean())
    wt_frac = float((col == wt_i).sum() / max(n_nongap, 1))
    # 归一化香农熵（0=完全保守, 1=完全可变）
    counts = np.bincount(col, minlength=21)
    p = counts / max(counts.sum(), 1)
    p = p[p > 0]
    H = -float((p * np.log(p)).sum())
    H_norm = H / math.log(21)
    conservation.append(dict(resi=j+1, wt=wt, gap_frac=round(gap_frac, 3),
                             wt_freq=round(wt_frac, 3), entropy=round(H_norm, 3)))

with open(f"{OUT}/conservation.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["resi", "wt", "gap_frac", "wt_freq", "entropy"])
    w.writeheader()
    w.writerows(conservation)

# ---- 共进化：每个位点 vs 催化核心 的 MI ----
def mi_cols(a, b):
    """两列之间的互信息。"""
    idx = a * 21 + b                      # 联合类别 0..440
    joint = np.bincount(idx, minlength=441).astype(float)
    joint /= joint.sum()
    pa = np.bincount(a, minlength=21).astype(float); pa /= pa.sum()
    pb = np.bincount(b, minlength=21).astype(float); pb /= pb.sum()
    mi = 0.0
    for i in range(21):
        for k in range(21):
            pjk = joint[i*21 + k]
            if pjk > 0:
                mi += pjk * math.log(pjk / (pa[i] * pb[k]))
    return mi

core_idx = [c - 1 for c in CORE]
coevo = []
for j in range(L):
    a = M[:, j]
    mis = [mi_cols(a, M[:, c]) for c in core_idx]
    coevo.append(dict(resi=j+1, wt=query[j],
                      mean_MI_core=round(float(np.mean(mis)), 4),
                      max_MI_core=round(float(max(mis)), 4)))

with open(f"{OUT}/coevolution_with_core.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["resi", "wt", "mean_MI_core", "max_MI_core"])
    w.writeheader()
    w.writerows(coevo)

# ---- 打印关键残基 ----
KEYS = [25, 26, 27, 28, 29, 30, 31, 32, 56, 57, 58, 59, 60, 67, 68, 69, 70, 72,
        98, 99, 102, 105, 129, 130, 131, 132, 133]
print(f"\n== 关键残基 保守性 + 共进化 ==")
print(f"{'resi':>4} {'wt':>3} {'gap%':>6} {'WT频率':>7} {'熵(低=保守)':>10} {'共进化MI':>8}  判定")
for j in KEYS:
    c = conservation[j-1]; ce = coevo[j-1]
    wt_f = c["wt_freq"]; ent = c["entropy"]; mi = ce["mean_MI_core"]
    if wt_f >= 0.9:
        verdict = "高度保守(不可动)"
    elif wt_f >= 0.7:
        verdict = "较保守(慎动)"
    else:
        verdict = "可变(可突变)"
    print(f"{c['resi']:>4} {c['wt']:>3} {c['gap_frac']*100:>6.0f} {wt_f:>7.2f} {ent:>10.3f} {mi:>8.4f}  {verdict}")

print(f"\n写入 {OUT}/conservation.csv, {OUT}/coevolution_with_core.csv")
