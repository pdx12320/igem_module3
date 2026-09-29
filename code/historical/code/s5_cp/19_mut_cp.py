# -*- coding: utf-8 -*-
"""
阶段 19 —— 突变体模型的 CP / ΔCP 分析，并与 WT 对比

对 new/mut/ 下每个突变（× GCG/GCA 两 motif，各 5 模型）：
  提取「蛋白残基 ↔ +1 核苷酸(RNA res 5)」的 CP；
  算 ΔCP = CP(GCA) - CP(GCG)；
  对比 WT 的 ΔCP，看突变是否改变 +1 G/A 判别。

产出：results/mut_cp_dcp.csv（每突变 × 残基的 CP_G/CP_A/ΔCP）
"""
import json
import csv
import os
import glob
from collections import defaultdict

import af_utils as U

OUT = "results"
PLUS1_RESI = 5

# 突变列表（new/mut 下的目录名）
MUTS = ["a59p", "g25e", "g25ek30h", "g27d", "g27dk30h", "g27dk30hq58m",
        "g27t", "g27tk30h", "g27tk30hq58m", "k30h", "k30hq58m", "k60r",
        "m132d", "m132e"]

def process(dirname):
    cp = defaultdict(list)
    for fjson in sorted(glob.glob(os.path.join(dirname, "*full_data*.json"))):
        d = json.load(open(fjson, encoding="utf-8"))
        cids = d["token_chain_ids"]; rids = d["token_res_ids"]; cpm = d["contact_probs"]
        tgt = next(i for i in range(len(cids)) if cids[i]==U.RNA_CHAIN and rids[i]==PLUS1_RESI)
        for i in range(len(cids)):
            if cids[i]==U.PROT_CHAIN:
                cp[rids[i]].append(max(cpm[i][tgt], cpm[tgt][i]))
    return {r: sum(v)/len(v) for r, v in cp.items()}

# 读 WT 参考（results/cp_dcp.csv）
wt = {}
for r in csv.DictReader(open(f"{OUT}/cp_dcp.csv", encoding="utf-8-sig")):
    wt[int(r["resi"])] = dict(cp_G=float(r["cp_G"]), cp_A=float(r["cp_A_swap"]), dcp=float(r["dcp_swap"]))

# 计算每个突变
result = {}
for m in MUTS:
    g = process(f"new/mut/{m}_gcg")
    a = process(f"new/mut/{m}_gca")
    resis = set(g) | set(a)
    result[m] = {r: dict(cpG=g.get(r,0), cpA=a.get(r,0), dcp=a.get(r,0)-g.get(r,0)) for r in resis}

# 输出 CSV
with open(f"{OUT}/mut_cp_dcp.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["mut", "resi", "cp_G", "cp_A", "dcp", "wt_cpG", "wt_cpA", "wt_dcp"])
    for m in MUTS:
        for r in sorted(result[m]):
            d = result[m][r]
            ww = wt.get(r, {})
            w.writerow([m, r, round(d["cpG"],4), round(d["cpA"],4), round(d["dcp"],4),
                        round(ww.get("cp_G",0),4), round(ww.get("cp_A",0),4), round(ww.get("dcp",0),4)])

# 打印关键残基的 ΔCP 对比
KEYS = [27,28,29,30,31,32,57,58,59,60,70,72,99,102,105,129,130,132]
print("== 各突变的 ΔCP（+1 位，正值=排A方向，负值=保G方向）关键残基 ==")
print(f"{'突变':<16}", end="")
for k in KEYS:
    print(f"{k:>5}", end="")
print(f"{'  (vs WT 变化)':>18}")
for m in MUTS:
    print(f"{m:<16}", end="")
    for k in KEYS:
        d = result[m].get(k, {})
        print(f"{d.get('dcp',0):>+5.2f}", end="")
    # 与 WT 的差异（关键残基 29/30 的 ΔCP 变化）
    d30 = result[m].get(30,{}).get('dcp',0) - wt.get(30,{}).get('dcp',0)
    d29 = result[m].get(29,{}).get('dcp',0) - wt.get(29,{}).get('dcp',0)
    print(f"  (ΔΔCP 29={d29:+.2f} 30={d30:+.2f})")
print(f"{'WT(参考)':<16}", end="")
for k in KEYS:
    print(f"{wt.get(k,{}).get('dcp',0):>+5.2f}", end="")
print()
print(f"\n写入 {OUT}/mut_cp_dcp.csv")
