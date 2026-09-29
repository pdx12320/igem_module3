# -*- coding: utf-8 -*-
"""
阶段 16 —— 新 test 模型（11nt RNA CGUUGCGGAGG，+1=G）的接触分析与 CP 分析，并与旧模型对比

新模型：RNA=CGUUGCGGAGG，编辑 C 在 res 6，+1=G 在 res 7。
旧模型：GUGCGCG(7nt)，编辑 C 在 res 4，+1=G 在 res 5。

对比：新模型(5个) vs 旧模型(100个) 的 +1G 接触/CP 轮廓是否一致。
"""
import json
import csv
import os
from collections import defaultdict

import af_utils as U

OUT = "results"

# 新模型
NEW_DIR = "new/test"
NEW_PLUS1_RESI = 7     # 11nt RNA 中 +1=G 在 res 7
NEW_NMODEL = 5

# ---- 1) 新模型：距离接触 + CP ----
new_dist = defaultdict(list)   # resi -> [min_dist]
new_cp = defaultdict(list)     # resi -> [cp]

for rank in range(5):
    cif = os.path.join(NEW_DIR, f"fold_test1_model_{rank}.cif")
    fjson = os.path.join(NEW_DIR, f"fold_test1_full_data_{rank}.json")

    # 距离接触
    cols, atoms = U.parse_atom_site(cif)
    plus1 = U.atoms_of(atoms, U.RNA_CHAIN, NEW_PLUS1_RESI)
    rA = U.residues_by_chain(atoms, U.PROT_CHAIN)
    for resi, patoms in rA.items():
        d = U.min_dist(patoms, plus1)
        if d is not None:
            new_dist[resi].append(d)

    # CP
    d = json.load(open(fjson, encoding="utf-8"))
    chain_ids = d["token_chain_ids"]
    res_ids = d["token_res_ids"]
    cp = d["contact_probs"]
    tgt = None
    for i in range(len(chain_ids)):
        if chain_ids[i] == U.RNA_CHAIN and res_ids[i] == NEW_PLUS1_RESI:
            tgt = i
            break
    for i in range(len(chain_ids)):
        if chain_ids[i] == U.PROT_CHAIN:
            new_cp[res_ids[i]].append(max(cp[i][tgt], cp[tgt][i]))

def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0

new_res = {}
for resi in set(new_dist) | set(new_cp):
    ds = new_dist.get(resi, [])
    cs = new_cp.get(resi, [])
    new_res[resi] = dict(
        freq_5A=sum(1 for x in ds if x <= 5.0) / len(ds) if ds else 0.0,
        median_dist=sorted(ds)[len(ds)//2] if ds else None,
        mean_cp=mean(cs),
    )

# ---- 2) 旧模型结果 ----
old_freq = {}   # resi -> freq_base_5.0 (GUGCGCG)
for r in csv.DictReader(open(f"{OUT}/contacts_frequency.csv", encoding="utf-8-sig")):
    if r["rna"] == "GUGCGCG":
        old_freq[int(r["resi"])] = float(r["freq_base_5.0"])
old_cp = {}     # resi -> cp_G (GUGCGCG)
for r in csv.DictReader(open(f"{OUT}/cp_dcp.csv", encoding="utf-8-sig")):
    old_cp[int(r["resi"])] = float(r["cp_G"])

# ---- 3) 对比输出 ----
KEYS = [25, 26, 27, 28, 29, 30, 31, 32, 56, 57, 58, 59, 60, 67, 68, 69, 70, 72, 98, 99, 102, 105, 129, 130, 131, 132, 133]
print(f"== 新模型(11nt, n={NEW_NMODEL}) vs 旧模型(GUGCGCG 7nt, n=100) 的 +1G 接触/CP 对比 ==")
print(f"{'resi':>4} {'旧freq5A':>8} {'新freq5A':>8} {'旧CP':>7} {'新CP':>7}  一致性")
for resi in KEYS:
    of = old_freq.get(resi, 0)
    nf = new_res.get(resi, {}).get("freq_5A", 0)
    oc = old_cp.get(resi, 0)
    nc = new_res.get(resi, {}).get("mean_cp", 0)
    # 一致性：都是高接触(>0.5)或都是低接触(<0.2)
    if (of > 0.5 and nf > 0.5) or (of < 0.2 and nf < 0.2):
        tag = "✓一致"
    elif (oc > 0.5 and nc > 0.5) or (oc < 0.2 and nc < 0.2):
        tag = "≈一致"
    else:
        tag = "✗差异"
    print(f"{resi:>4} {of:>8.2f} {nf:>8.2f} {oc:>7.3f} {nc:>7.3f}  {tag}")

# 保存新模型结果
with open(f"{OUT}/test_cp_dcp.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["resi", "freq_5A", "median_dist", "mean_cp"])
    for resi in sorted(new_res):
        w.writerow([resi, round(new_res[resi]["freq_5A"], 4),
                    round(new_res[resi]["median_dist"], 3) if new_res[resi]["median_dist"] else "",
                    round(new_res[resi]["mean_cp"], 4)])

print(f"\n新模型结果写入 {OUT}/test_cp_dcp.csv")
