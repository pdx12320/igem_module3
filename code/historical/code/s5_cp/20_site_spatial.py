# -*- coding: utf-8 -*-
"""
阶段 20 —— 突变位点空间距离聚类分析（v2：区分序列邻居 vs 三维长程接近）

关键方法学问题：主链上相邻残基（|i-j|=1）的肽键必然 <2 Å，若用距离做传递闭包，
会把整条多肽链连成一个簇，掩盖真正的「三维空间聚集」。因此本版：
  1) 按生物学功能区（loop1/阅读器/loop3/催化核心/W-S环/loop7-出口）分区；
  2) 跨区段(或区内但非序列邻居)的空间接近才有意义，只统计 |i-j|>2 的近邻对；
  3) 给出「跨区段空间桥梁」表，识别哪些不同 loop 的突变位点在 3D 上互相贴近。

产出：results/mutation_site_spatial_distances.csv  （两两距离矩阵，含所有对）
      results/mutation_site_cross_region_bridges.csv（跨区段空间接近对）
"""
import os, csv
from collections import defaultdict

import af_utils as U

# 生物学功能区划分（按序列 + 文献 loop）
REGIONS = [
    ("loop1-N", [25, 26, 27, 28]),
    ("+1阅读器/loop", [29, 30, 31, 32]),
    ("loop3", [57, 58, 59, 60]),
    ("催化核心(参照)", [70, 72, 102, 105]),
    ("W-S环", [98, 99]),
    ("loop7-出口", [129, 130, 131, 132, 133]),
]
ALL_SITES = [r for _, rs in REGIONS for r in rs]
REGION_OF = {r: name for name, rs in REGIONS for r in rs}
CATALYTIC = set([70, 72, 102, 105])

MUT_HISTORY = {
    25: ["G25E"], 26: ["I26D"],
    27: ["G27D/T/V/I/Q/P"], 28: ["R28A/S/W"], 29: ["H29N/F/P"],
    30: ["K30H/T/N"], 31: ["T31A/V/I/L/S/C"], 32: ["Y32F"],
    57: ["N57D/A/G*"], 58: ["Q58M/V"], 59: ["A59P/S"], 60: ["K60R/H"],
    70: ["H70(锌)"], 72: ["E72(催化)"], 98: ["S98A"],
    99: ["W99(保守)"], 102: ["C102(锌)"], 105: ["C105(锌)"],
    129: ["W129"], 130: ["W130G"], 131: ["R131"],
    132: ["M132D/E/A/F/G"], 133: ["T133"],
}

def residue_ca(atoms_by_res, resi):
    for a in atoms_by_res.get(resi, []):
        if a["atom_site.label_atom_id"] == "CA":
            return U.coord(a)
    return None

seeds = sorted([d for d in os.listdir("GUGCGCG_20") if d.isdigit()])
ca_sum = defaultdict(float); ma_sum = defaultdict(float)
ca_n = defaultdict(int); ma_n = defaultdict(int)
for sd in seeds:
    cif = os.path.join("GUGCGCG_20", sd, f"fold_{sd}_model_0.cif")
    if not os.path.exists(cif):
        continue
    cols, atoms = U.parse_atom_site(cif)
    abr = U.residues_by_chain(atoms, U.PROT_CHAIN)
    site_atoms = {r: abr.get(r, []) for r in ALL_SITES}
    cas = {r: residue_ca(abr, r) for r in ALL_SITES}
    for a in range(len(ALL_SITES)):
        i = ALL_SITES[a]
        for j in ALL_SITES[a+1:]:
            ci, cj = cas.get(i), cas.get(j)
            if ci and cj:
                d2 = sum((ci[k]-cj[k])**2 for k in range(3))**0.5
                ca_sum[(i, j)] += d2; ca_n[(i, j)] += 1
            d = U.min_dist(site_atoms[i], site_atoms[j])
            if d is not None:
                ma_sum[(i, j)] += d; ma_n[(i, j)] += 1

ca_avg = {k: v/ca_n[k] for k, v in ca_sum.items()}
ma_avg = {k: v/ma_n[k] for k, v in ma_sum.items()}

# ---- 1) 完整两两距离矩阵 ----
with open("results/mutation_site_spatial_distances.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["resi1", "region1", "resi2", "region2", "seq_gap", "ca_dist_A", "minatom_dist_A", "note"])
    for (i, j) in sorted(ca_avg):
        ca = ca_avg[(i, j)]; ma = ma_avg.get((i, j))
        gap = abs(i - j)
        note = "序列邻居(必然近)" if gap == 1 else ""
        if gap > 2:
            if ma is not None and ma <= 5.0:
                note = "跨区段强接触(3D)" if REGION_OF[i] != REGION_OF[j] else "区内强接触"
            elif ma is not None and ma <= 8.0:
                note = "跨区段邻近(3D)" if REGION_OF[i] != REGION_OF[j] else "区内邻近"
            elif REGION_OF[i] != REGION_OF[j] and ma is not None and ma <= 12.0:
                note = "弱邻近"
        w.writerow([i, REGION_OF[i], j, REGION_OF[j], gap, round(ca, 2), round(ma, 2) if ma else "", note])

# ---- 2) 跨区段空间桥梁（排除序列邻居与催化参照的锌配位内部）----
bridges = []
for (i, j), ma in ma_avg.items():
    gap = abs(i - j)
    r1, r2 = REGION_OF[i], REGION_OF[j]
    if gap <= 2 or r1 == r2:
        continue
    if ma <= 8.0:
        bridges.append((i, j, r1, r2, round(ca_avg[(i, j)], 1), round(ma, 1)))

with open("results/mutation_site_cross_region_bridges.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["resi1", "region1", "resi2", "region2", "ca_dist_A", "minatom_dist_A"])
    for row in sorted(bridges, key=lambda x: x[5]):
        w.writerow(list(row))

print("=== 跨区段空间桥梁（不同功能区的位点，3D 距离 ≤ 8 Å）===")
print("排序：按最小重原子距离\n")
print(f"{'resi':<5}{'区1':<10}{'resi':<5}{'区2':<12}{'Cα':>6}{'minatom':>9}")
for (i, j, r1, r2, ca, ma) in sorted(bridges, key=lambda x: x[5]):
    print(f"{i:<5}{r1:<10}{j:<5}{r2:<12}{ca:>6.1f}{ma:>8.1f}")

print("\n=== 关键提示 ===")
print("· 跨区段强接触(<5Å)或邻近(5–8Å)的位点：三维上贴近，突变可能共享口袋/构象偶联")
print("· 但「空间近」不等于「功能耦合」——是否真正影响活性/选择性需以组合实验为准")
print("\n写入 results/mutation_site_spatial_distances.csv")
print("写入 results/mutation_site_cross_region_bridges.csv")
