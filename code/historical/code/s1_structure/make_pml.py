# -*- coding: utf-8 -*-
"""
生成 PyMOL 可视化抽查脚本（.pml）

为每条 RNA 取「seed 最小」的那个 seed 的 rank0 结构，生成一个 .pml：
  - 载入 cif
  - 高亮 +1 位碱基（黄色）与整核苷酸
  - 高亮 chain A 中与 +1 位 ≤5 Å 接触的蛋白残基（蓝色）
  - 输出 PNG

运行方式（需已安装 PyMOL）：pymol <文件>.pml
产出：results/pml/*.pml
"""
import os
import csv
import glob

import af_utils as U

OUT_DIR = os.path.join("results", "pml")
os.makedirs(OUT_DIR, exist_ok=True)

# 载入 manifest，选出每条 RNA 的最小 seed 的 rank0
manifest = []
with open(os.path.join("results", "manifest.csv"), encoding="utf-8-sig") as f:
    manifest = list(csv.DictReader(f))

best = {}
for row in manifest:
    if row["rank"] != "0":
        continue
    key = row["rna"]
    seed_int = int(row["seed"]) if row["seed"].isdigit() else 10**9
    if key not in best or seed_int < best[key][0]:
        best[key] = (seed_int, row)

BASE_SEL = "name N9+C8+N7+C5+C6+N6+O6+N1+C2+N2+N3+C4"

for rna in U.RNA_SEQS:
    seed_int, row = best[rna]
    path = row["path"].replace("\\", "/")          # PyMOL 接受正斜杠
    out_png = os.path.abspath(os.path.join(OUT_DIR, f"check_{rna}_seed{row['seed']}_rank0.png")).replace("\\", "/")
    pml_path = os.path.join(OUT_DIR, f"check_{rna}_seed{row['seed']}_rank0.pml")

    pml = f"""# PyMOL 抽查：{rna}  seed={row['seed']}  rank0
reinitialize
set bg_rgb, [1,1,1]
load {path}, m

hide everything
show cartoon, m and chain A

# +1 位碱基（黄）与整核苷酸
select plus1_base, m and chain B and resi 5 and ({BASE_SEL})
select plus1_all, m and chain B and resi 5

# 与 +1 整核苷酸 <=5A 接触的蛋白残基（蓝）
select contact5, (m and chain A) within 5.0 of plus1_all

show sticks, plus1_all
show sticks, contact5
color yellow, plus1_all
color tv_blue, contact5
set stick_radius, 0.2

zoom contact5, 8
ray 1600, 1200
png {out_png}, dpi=300
"""
    with open(pml_path, "w", encoding="utf-8") as f:
        f.write(pml)
    print("生成", pml_path)
