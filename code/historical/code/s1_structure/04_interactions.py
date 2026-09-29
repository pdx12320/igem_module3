# -*- coding: utf-8 -*-
"""
阶段 4 —— +1 位蛋白-RNA 相互作用分析（PISA 等价：氢键计数 + 界面埋藏面积）

对每个模型的蛋白残基量化其与 +1 位核苷酸的相互作用：
  1) 氢键计数（几何判定：供体-受体重原子距离 <=3.5 Å，无 H 原子近似）
  2) 界面埋藏面积（Shrake-Rupley SASA：残基在「蛋白+RNA」与「仅蛋白」两种
     语境下的 SASA 差 = 被 RNA 埋藏的面积；仅对每 seed 的 rank0 代表结构计算，
     以控制耗时）

产出：
  results/hbonds_per_residue.csv        —— 每 RNA × 残基 的氢键均值/频率（全部 300 模型）
  results/buried_area_per_residue.csv   —— 每 RNA × 残基 的埋藏面积均值（rank0 代表结构）
  results/filtered_residues.csv         —— 再次筛选后的可设计残基清单
"""
import os
import csv
from collections import defaultdict

import af_utils as U

OUT_DIR = "results"

# ---- 氢键供体/受体原子名 ----
PROT_DONOR = {"N", "NE", "NH1", "NH2", "NZ", "ND1", "NE2", "ND2", "NE1",
              "OG", "OG1", "OH"}
PROT_ACC = {"O", "OD1", "OD2", "OE1", "OE2", "OG", "OG1", "OH", "ND1", "NE2"}
RNA_DONOR = {"G": {"N1", "N2"}, "A": {"N6"}}
RNA_ACC = {"G": {"N3", "N7", "O6"}, "A": {"N1", "N3", "N7"}}

HB_DIST = 3.5

# 绝对禁区（不可突变）
FORBIDDEN = {57, 70, 72, 99, 102, 105, 68}   # N57/H70/E72/W99/C102/C105/G68
CORE_READERS = {29, 30}                       # H29/K30：碱基阅读器


def count_hbonds(prot_atoms, rna_atoms, rna_donor, rna_acc):
    """返回 (氢键原子对集合, 供体侧计数)。prot_atoms/rna_atoms 为原子 dict 列表。"""
    pairs = set()
    for pa in prot_atoms:
        pname = pa["atom_site.label_atom_id"]
        # 排除 Pro 骨架 N（无 H）
        if pname == "N" and pa["atom_site.label_comp_id"] == "PRO":
            continue
        pa_coord = U.coord(pa)
        for ra in rna_atoms:
            rname = ra["atom_site.label_atom_id"]
            ra_coord = U.coord(ra)
            dx, dy, dz = pa_coord[0] - ra_coord[0], pa_coord[1] - ra_coord[1], pa_coord[2] - ra_coord[2]
            d = (dx * dx + dy * dy + dz * dz) ** 0.5
            if d > HB_DIST:
                continue
            if pname in PROT_DONOR and rname in rna_acc:
                pairs.add((pa["atom_site.id"], ra["atom_site.id"]))
            if pname in PROT_ACC and rname in rna_donor:
                pairs.add((pa["atom_site.id"], ra["atom_site.id"]))
    return len(pairs)


def shrake_rupley(coords, radii, probe=1.4, n_sphere=100):
    """计算每个原子的溶剂可及表面积（Å²）。coords: (N,3) float; radii: (N,) float。"""
    import numpy as np
    n = len(coords)
    if n == 0:
        return np.zeros(0)

    # 斐波那契球面点（单位球）
    idx = np.arange(n_sphere)
    z = 1 - 2 * (idx + 0.5) / n_sphere
    phi = np.pi * (1 + 5 ** 0.5) * idx
    xy = np.sqrt(1 - z * z)
    unit = np.stack([xy * np.cos(phi), xy * np.sin(phi), z], axis=1)  # (n_sphere,3)

    r = radii + probe                      # (N,)
    # 成对距离矩阵
    diff = coords[:, None, :] - coords[None, :, :]
    dm = np.sqrt((diff ** 2).sum(-1))      # (N,N)

    asa = np.zeros(n)
    for i in range(n):
        # 邻居 j（与 i 的扩展球可能重叠，且非自身）
        nb = np.where((dm[i] <= r[i] + r) & (np.arange(n) != i))[0]
        if nb.size == 0:
            asa[i] = 4 * np.pi * r[i] ** 2
            continue
        pts = unit * r[i] + coords[i]                       # (S,3)
        d = np.sqrt(((pts[:, None, :] - coords[nb][None, :, :]) ** 2).sum(-1))  # (S,M)
        occluded = (d < r[nb][None, :]).any(axis=1)         # (S,)
        asa[i] = 4 * np.pi * r[i] ** 2 * (n_sphere - occluded.sum()) / n_sphere
    return asa


def radii_of(atoms):
    R = {"C": 1.7, "N": 1.55, "O": 1.52, "S": 1.8, "P": 1.8}
    return [R.get(a["atom_site.type_symbol"], 1.7) for a in atoms]


# ============ 读取 manifest 与 qc ============
manifest = []
with open(os.path.join(OUT_DIR, "manifest.csv"), encoding="utf-8-sig") as f:
    manifest = list(csv.DictReader(f))

skip = set()
with open(os.path.join(OUT_DIR, "qc_report.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        if row["qc_pass"] == "False":
            skip.add((row["rna"], row["seed"], int(row["rank"])))

# ============ 1) 氢键计数（全部模型） ============
hb_agg = defaultdict(lambda: defaultdict(list))   # rna -> resi -> [per-model hb_base]
hb_full_agg = defaultdict(lambda: defaultdict(list))
resn_map = {}

for row in manifest:
    rna, seed = row["rna"], row["seed"]
    rank = int(row["rank"])
    if (rna, seed, rank) in skip:
        continue
    cols, atoms = U.parse_atom_site(row["path"])
    plus1_all = U.atoms_of(atoms, U.RNA_CHAIN, U.PLUS1_RESI)
    plus1_base = [a for a in plus1_all if a["atom_site.label_atom_id"] in U.BASE_ATOMS]
    plus1_resn = plus1_all[0]["atom_site.label_comp_id"]
    rna_don = RNA_DONOR.get(plus1_resn, set())
    rna_acc = RNA_ACC.get(plus1_resn, set())

    rA = U.residues_by_chain(atoms, U.PROT_CHAIN)
    for resi, patoms in rA.items():
        resn_map[resi] = patoms[0]["atom_site.label_comp_id"]
        hb_agg[rna][resi].append(count_hbonds(patoms, plus1_base, rna_don, rna_acc))
        hb_full_agg[rna][resi].append(count_hbonds(patoms, plus1_all, rna_don, rna_acc))

hb_rows = []
for rna in U.RNA_SEQS:
    for resi in sorted(hb_agg[rna]):
        xs = hb_agg[rna][resi]
        xf = hb_full_agg[rna][resi]
        hb_rows.append({
            "rna": rna, "resi": resi, "resn": resn_map[resi],
            "n_model": len(xs),
            "mean_hb_base": round(sum(xs) / len(xs), 3),
            "freq_hb_base": round(sum(1 for x in xs if x > 0) / len(xs), 3),
            "mean_hb_full": round(sum(xf) / len(xf), 3),
            "freq_hb_full": round(sum(1 for x in xf if x > 0) / len(xf), 3),
        })

hb_fields = ["rna", "resi", "resn", "n_model", "mean_hb_base", "freq_hb_base",
             "mean_hb_full", "freq_hb_full"]
with open(os.path.join(OUT_DIR, "hbonds_per_residue.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=hb_fields)
    w.writeheader()
    w.writerows(hb_rows)

# ============ 2) 埋藏面积（每 seed rank0 代表结构） ============
import numpy as np  # noqa: E402

area_agg = defaultdict(lambda: defaultdict(list))

for row in manifest:
    if row["rank"] != "0":
        continue
    rna, seed = row["rna"], row["seed"]
    rank = int(row["rank"])
    if (rna, seed, rank) in skip:
        continue
    cols, atoms = U.parse_atom_site(row["path"])

    prot = [a for a in atoms if a["atom_site.label_asym_id"] == U.PROT_CHAIN]
    rna_atoms = [a for a in atoms if a["atom_site.label_asym_id"] == U.RNA_CHAIN]

    all_atoms = prot + rna_atoms
    all_coords = np.array([U.coord(a) for a in all_atoms], dtype=float)
    all_radii = np.array(radii_of(all_atoms), dtype=float)
    prot_coords = np.array([U.coord(a) for a in prot], dtype=float)
    prot_radii = np.array(radii_of(prot), dtype=float)

    asa_complex = shrake_rupley(all_coords, all_radii)
    asa_prot_only = shrake_rupley(prot_coords, prot_radii)

    # 蛋白原子在两种语境下的 ASA，按残基求和求差
    prot_map = defaultdict(lambda: [0.0, 0.0])   # resi -> [asa_complex, asa_free]
    for a, ac, af in zip(prot, asa_complex[:len(prot)], asa_prot_only):
        resi = int(a["atom_site.label_seq_id"])
        prot_map[resi][0] += ac
        prot_map[resi][1] += af
    for resi, (ac, af) in prot_map.items():
        area_agg[rna][resi].append(af - ac)     # 正值 = 被 RNA 埋藏的面积

area_rows = []
for rna in U.RNA_SEQS:
    for resi in sorted(area_agg[rna]):
        xs = area_agg[rna][resi]
        area_rows.append({
            "rna": rna, "resi": resi, "resn": resn_map[resi],
            "n_model": len(xs),
            "mean_buried_area": round(sum(xs) / len(xs), 2),
        })

area_fields = ["rna", "resi", "resn", "n_model", "mean_buried_area"]
with open(os.path.join(OUT_DIR, "buried_area_per_residue.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=area_fields)
    w.writeheader()
    w.writerows(area_rows)

print("氢键表写入 results/hbonds_per_residue.csv")
print("埋藏面积表写入 results/buried_area_per_residue.csv")

# ============ 3) 再次筛选 ============
# 标准：任一组 RNA 中 freq_hb_base>0 或 平均氢键>=0.05，且非禁区
filtered = []
for hb in hb_rows:
    resi = hb["resi"]
    if resi in FORBIDDEN:
        continue
    if (hb["freq_hb_base"] > 0 or hb["mean_hb_base"] >= 0.05) and resi in resn_map:
        filtered.append(hb)

# 合并三组信息
by_resi = defaultdict(dict)
for hb in filtered:
    by_resi[hb["resi"]]["resn"] = hb["resn"]
    by_resi[hb["resi"]][hb["rna"]] = hb["freq_hb_base"]

filter_rows = []
for resi in sorted(by_resi):
    d = by_resi[resi]
    filter_rows.append({
        "resi": resi, "resn": d["resn"],
        "freq_hb_G": d.get("GUGCGCG", 0.0),
        "freq_hb_Aswap": d.get("GUGCACG", 0.0),
        "freq_hb_Aoff": d.get("AUGCAGC", 0.0),
        "role": "reader" if resi in CORE_READERS else "",
    })
filter_fields = ["resi", "resn", "freq_hb_G", "freq_hb_Aswap", "freq_hb_Aoff", "role"]
with open(os.path.join(OUT_DIR, "filtered_residues.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=filter_fields)
    w.writeheader()
    w.writerows(filter_rows)

print("\n== 再次筛选后的可设计残基（含 +1 氢键频率 G / Aswap / Aoff）==")
for r in filter_rows:
    print(f"  {r['resi']:>3} {r['resn']:>4}  G={r['freq_hb_G']:>5}  "
          f"Aswap={r['freq_hb_Aswap']:>5}  Aoff={r['freq_hb_Aoff']:>5}  {r['role']}")
print("写入 results/filtered_residues.csv")
