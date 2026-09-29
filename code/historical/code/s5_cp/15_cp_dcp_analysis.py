# -*- coding: utf-8 -*-
"""
阶段 15 —— ContactSeek 式 CP + ΔCP 分析（替代距离接触分析）

方法（借鉴 ContactSeek, Nature 2026）：
  - 从 AF3 输出的 full_data JSON 里取「contact_probs」矩阵（两残基在 8 Å 内的概率），
    比「用坐标算距离」更敏感，能捕捉距离没变但接触概率变化的微弱差异。
  - 对每个模型提取「蛋白残基 ↔ +1 核苷酸(chain B resi 5)」的 CP。
  - 按 RNA 分组取平均 CP；算 ΔCP = CP(off) − CP(on)：
        ΔCP_swap = CP(GUGCACG) − CP(GUGCGCG)   （纯 +1 G→A 交换）
        ΔCP_off  = CP(AUGCAGC) − CP(GUGCGCG)   （完整脱靶）
  - ΔCP > 0 = 该残基在 +1=A 时接触增强（脱靶稳定）→ 排A 候选。

产出：results/cp_dcp.csv、results/cp_dcp_ranking.csv
"""
import csv
import json
import os
import re
from collections import defaultdict

import af_utils as U

OUT = "results"

manifest = list(csv.DictReader(open(os.path.join(OUT, "manifest.csv"), encoding="utf-8-sig")))


def full_data_path(model_cif_path, rank):
    """由 model_0.cif 路径推导 full_data_0.json 路径。"""
    return re.sub(rf"_model_{rank}\.cif$", f"_full_data_{rank}.json", model_cif_path)


def load_cp(model_path, rank):
    """加载 token_chain_ids / token_res_ids / contact_probs。"""
    p = full_data_path(model_path, rank)
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    return d["token_chain_ids"], d["token_res_ids"], d["contact_probs"]


def extract_cp(chain_ids, res_ids, cp, target_chain, target_res):
    """返回 {蛋白残基: CP(该残基 → 目标核苷酸)}。"""
    # 找目标核苷酸的 token 索引
    tgt_idx = None
    for i in range(len(chain_ids)):
        if chain_ids[i] == target_chain and res_ids[i] == target_res:
            tgt_idx = i
            break
    if tgt_idx is None:
        return {}
    out = {}
    for i in range(len(chain_ids)):
        if chain_ids[i] == U.PROT_CHAIN:
            # CP 取两方向的最大值（更稳健）
            c = max(cp[i][tgt_idx], cp[tgt_idx][i])
            out[res_ids[i]] = c
    return out


# 聚合：rna -> resi -> [CP 列表]
agg = defaultdict(lambda: defaultdict(list))
nmodel = defaultdict(int)

for m in manifest:
    rna = m["rna"]
    rank = int(m["rank"])
    try:
        chain_ids, res_ids, cp = load_cp(m["path"], rank)
    except FileNotFoundError:
        continue
    nmodel[rna] += 1
    per_res = extract_cp(chain_ids, res_ids, cp, U.RNA_CHAIN, U.PLUS1_RESI)
    for resi, c in per_res.items():
        agg[rna][resi].append(c)

# 平均 CP
mean_cp = defaultdict(dict)   # rna -> resi -> mean CP
for rna in U.RNA_SEQS:
    for resi, cs in agg[rna].items():
        mean_cp[rna][resi] = sum(cs) / len(cs)

# 计算 ΔCP
all_resi = set()
for rna in U.RNA_SEQS:
    all_resi |= set(mean_cp[rna].keys())

rows = []
for resi in sorted(all_resi):
    cg = mean_cp["GUGCGCG"].get(resi, 0.0)
    ca_swap = mean_cp["GUGCACG"].get(resi, 0.0)
    ca_off = mean_cp["AUGCAGC"].get(resi, 0.0)
    rows.append(dict(
        resi=resi,
        cp_G=round(cg, 4),
        cp_A_swap=round(ca_swap, 4),
        cp_A_off=round(ca_off, 4),
        dcp_swap=round(ca_swap - cg, 4),
        dcp_off=round(ca_off - cg, 4),
    ))

with open(f"{OUT}/cp_dcp.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["resi", "cp_G", "cp_A_swap", "cp_A_off", "dcp_swap", "dcp_off"])
    w.writeheader()
    w.writerows(rows)

# 排名：按 ΔCP（swap，纯 +1 判别）降序
ranked = sorted(rows, key=lambda r: -r["dcp_swap"])
with open(f"{OUT}/cp_dcp_ranking.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["rank", "resi", "cp_G", "cp_A_swap", "cp_A_off", "dcp_swap", "dcp_off"])
    w.writeheader()
    for i, r in enumerate(ranked, 1):
        w.writerow(dict(rank=i, **r))

# 打印关键残基 + 前 20
KEYS = [27, 28, 29, 30, 31, 32, 57, 58, 59, 60, 70, 72, 98, 99, 102, 105, 130, 132]
print(f"== 关键残基的 CP / ΔCP（+1 核苷酸）==")
print(f"{'resi':>4} {'CP(G)':>7} {'CP(A_swap)':>10} {'CP(A_off)':>9} {'ΔCP_swap':>9} {'ΔCP_off':>8}")
for resi in KEYS:
    r = next((x for x in rows if x["resi"] == resi), None)
    if r:
        print(f"{resi:>4} {r['cp_G']:>7} {r['cp_A_swap']:>10} {r['cp_A_off']:>9} "
              f"{r['dcp_swap']:>+9} {r['dcp_off']:>+8}")

print(f"\n== ΔCP_swap 前 20（+1=G→A 时接触增强最多的残基 = 排A候选）==")
print(f"{'resi':>4} {'CP(G)':>7} {'CP(A)':>7} {'ΔCP':>8}")
for r in ranked[:20]:
    print(f"{r['resi']:>4} {r['cp_G']:>7} {r['cp_A_swap']:>7} {r['dcp_swap']:>+8}")

print(f"\n写入 {OUT}/cp_dcp.csv, {OUT}/cp_dcp_ranking.csv")
