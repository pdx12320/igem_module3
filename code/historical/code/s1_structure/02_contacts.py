# -*- coding: utf-8 -*-
"""
阶段 2 —— +1 位接触分析（双口径）

对每个通过质控的模型：
  - 提取 +1 位（chain B resi 5）的「碱基重原子」与「整核苷酸重原子」两套原子；
  - 计算每个蛋白残基（chain A）到这两套原子的最小重原子距离；
  - 按 3.5 / 4.0 / 5.0 Å 三档判定是否接触。

产出：
  results/contacts_long.csv   —— 每模型 × 199 蛋白残基 的完整距离表
  results/key_distances.csv   —— 关键残基子集（便于 G/A 对比）

依赖 results/manifest.csv 与 results/qc_report.csv（先跑 00、01）。
"""
import os
import csv

import af_utils as U

OUT_DIR = "results"
os.makedirs(OUT_DIR, exist_ok=True)


def coord_list(atoms):
    return [U.coord(a) for a in atoms]


def min_dist_to_coords(atom_coords, ligand_coords):
    """原子坐标列表 -> 配体坐标列表 的最小距离。"""
    if not atom_coords or not ligand_coords:
        return None
    best = None
    for (xa, ya, za) in atom_coords:
        for (xb, yb, zb) in ligand_coords:
            dx, dy, dz = xa - xb, ya - yb, za - zb
            d = dx * dx + dy * dy + dz * dz
            if best is None or d < best:
                best = d
    return best ** 0.5


# 读取 manifest 与 qc（跳过硬剔除模型）
manifest = []
with open(os.path.join(OUT_DIR, "manifest.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        manifest.append(row)

skip = set()
with open(os.path.join(OUT_DIR, "qc_report.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        if row["qc_pass"] == "False":
            skip.add((row["rna"], row["seed"], int(row["rank"])))

long_rows = []
key_rows = []

for row in manifest:
    rna, seed = row["rna"], row["seed"]
    rank = int(row["rank"])
    path = row["path"]
    if (rna, seed, rank) in skip:
        continue

    cols, atoms = U.parse_atom_site(path)
    plus1_all = U.atoms_of(atoms, U.RNA_CHAIN, U.PLUS1_RESI)
    plus1_base = [a for a in plus1_all if a["atom_site.label_atom_id"] in U.BASE_ATOMS]

    base_coords = coord_list(plus1_base)
    full_coords = coord_list(plus1_all)

    rA = U.residues_by_chain(atoms, U.PROT_CHAIN)
    for resi in sorted(rA):
        res_atoms = rA[resi]
        resn = res_atoms[0]["atom_site.label_comp_id"]
        rc = coord_list(res_atoms)

        d_base = min_dist_to_coords(rc, base_coords)
        d_full = min_dist_to_coords(rc, full_coords)

        rec = {
            "rna": rna, "seed": seed, "rank": rank,
            "resi": resi, "resn": resn,
            "min_dist_base": ("" if d_base is None else round(d_base, 3)),
            "min_dist_full": ("" if d_full is None else round(d_full, 3)),
        }
        for c in U.CUTOFFS:
            rec[f"contact_base_{c}"] = (d_base is not None and d_base <= c)
            rec[f"contact_full_{c}"] = (d_full is not None and d_full <= c)
        long_rows.append(rec)

        if resi in U.KEY_RESIDUES:
            key_rows.append(rec)

# 写 contacts_long.csv
long_fields = ["rna", "seed", "rank", "resi", "resn",
               "min_dist_base", "min_dist_full",
               "contact_base_3.5", "contact_base_4.0", "contact_base_5.0",
               "contact_full_3.5", "contact_full_4.0", "contact_full_5.0"]
with open(os.path.join(OUT_DIR, "contacts_long.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=long_fields)
    w.writeheader()
    w.writerows(long_rows)

# 写 key_distances.csv（沿用相同列）
with open(os.path.join(OUT_DIR, "key_distances.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=long_fields)
    w.writeheader()
    w.writerows(key_rows)

print(f"== 接触分析完成 ==")
print(f"  处理 model 数: {len(manifest) - len(skip)}（跳过硬剔除 {len(skip)}）")
print(f"  contacts_long.csv: {len(long_rows)} 行")
print(f"  key_distances.csv: {len(key_rows)} 行")
