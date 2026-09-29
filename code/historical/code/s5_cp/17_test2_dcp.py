# -*- coding: utf-8 -*-
"""
阶段 17 —— test2(+1=A, 11nt) 的接触+CP分析，并算 ΔCP = CP(+1A) - CP(+1G)（用 test 对比）

test  (11nt): CGUUGCGGAGG  -> +1=G (res 7)
test2 (11nt): CGUUGCAGAGG  -> +1=A (res 7)   【纯 +1 交换】
蛋白序列相同(Pro.hA1 199aa)。

对比：
  1) 新 11nt 的 ΔCP 与旧 7nt 的 ΔCP(dcp_swap) 是否一致；
  2) 新 11nt 的 +1G 接触是否复现旧结论。
"""
import json
import csv
import os
from collections import defaultdict

import af_utils as U

OUT = "results"
PLUS1_RESI = 7

def process(dirname, prefix):
    dist = defaultdict(list)
    cp = defaultdict(list)
    for rank in range(5):
        cif = os.path.join(dirname, f"{prefix}_model_{rank}.cif")
        fjson = os.path.join(dirname, f"{prefix}_full_data_{rank}.json")
        cols, atoms = U.parse_atom_site(cif)
        plus1 = U.atoms_of(atoms, U.RNA_CHAIN, PLUS1_RESI)
        rA = U.residues_by_chain(atoms, U.PROT_CHAIN)
        for resi, patoms in rA.items():
            d = U.min_dist(patoms, plus1)
            if d is not None:
                dist[resi].append(d)
        d = json.load(open(fjson, encoding="utf-8"))
        cids = d["token_chain_ids"]; rids = d["token_res_ids"]; cpm = d["contact_probs"]
        tgt = next(i for i in range(len(cids)) if cids[i]==U.RNA_CHAIN and rids[i]==PLUS1_RESI)
        for i in range(len(cids)):
            if cids[i]==U.PROT_CHAIN:
                cp[rids[i]].append(max(cpm[i][tgt], cpm[tgt][i]))
    res = {}
    for resi in set(dist)|set(cp):
        ds = dist.get(resi, []); cs = cp.get(resi, [])
        res[resi] = dict(
            freq=sum(1 for x in ds if x<=5.0)/len(ds) if ds else 0,
            mean_cp=sum(cs)/len(cs) if cs else 0,
        )
    return res

G = process("new/test", "fold_test1")     # +1=G
A = process("new/test2", "fold_test2")    # +1=A

# 旧 7nt ΔCP
old_dcp = {}
for r in csv.DictReader(open(f"{OUT}/cp_dcp.csv", encoding="utf-8-sig")):
    old_dcp[int(r["resi"])] = float(r["dcp_swap"])

KEYS = [27,28,29,30,31,32,57,58,59,60,67,68,69,70,72,98,99,102,105,129,130,131,132]
print("== 新 11nt 模型 ΔCP = CP(+1A) - CP(+1G)，与旧 7nt ΔCP(dcp_swap) 对比 ==")
print(f"{'resi':>4} {'CP(G)':>6} {'CP(A)':>6} {'ΔCP(新11nt)':>10} {'ΔCP(旧7nt)':>10}  方向一致?")
rows = []
for resi in KEYS:
    cg = G.get(resi,{}).get("mean_cp",0)
    ca = A.get(resi,{}).get("mean_cp",0)
    dcp = ca - cg
    od = old_dcp.get(resi, 0)
    # 方向一致：ΔCP 同号 或 都接近0
    if abs(dcp) < 0.05 and abs(od) < 0.05:
        tag = "✓都≈0"
    elif (dcp > 0.02 and od > 0.02) or (dcp < -0.02 and od < -0.02):
        tag = "✓方向一致"
    else:
        tag = "✗不一致"
    rows.append((resi, cg, ca, dcp, od, tag))
    print(f"{resi:>4} {cg:>6.3f} {ca:>6.3f} {dcp:>+10.3f} {od:>+10.3f}  {tag}")

# 保存
with open(f"{OUT}/test2_dcp.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["resi","cp_G","cp_A","dcp_11nt","dcp_7nt"])
    for r in rows:
        w.writerow([r[0], round(r[1],4), round(r[2],4), round(r[3],4), round(r[4],4)])

print(f"\n写入 {OUT}/test2_dcp.csv")
