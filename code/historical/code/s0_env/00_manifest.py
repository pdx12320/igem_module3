# -*- coding: utf-8 -*-
"""
阶段 0 —— 清单归一化
扫描 3 个 RNA 文件夹，生成 manifest.csv，统一 seed 与 rank，并做完整性断言。

产出：results/manifest.csv
列：rna, seed, rank, path
"""
import os
import csv
import glob
import re

import af_utils as U

OUT_DIR = "results"
os.makedirs(OUT_DIR, exist_ok=True)

rows = []
problems = []

for rd in U.RNA_DIRS:
    # 只把包含 *_job_request.json 的子目录当作 seed 目录
    seed_dirs = [d for d in glob.glob(os.path.join(rd, "*/"))
                 if glob.glob(os.path.join(d, "*_job_request.json"))]

    for sd in sorted(seed_dirs):
        job = glob.glob(os.path.join(sd, "*_job_request.json"))[0]
        seed, rna, protein = U.read_job(job)

        models = sorted(glob.glob(os.path.join(sd, "*_model_[0-4].cif")))
        ranks = []
        for m in models:
            m2 = re.search(r"_model_(\d)\.cif$", m)
            rank = int(m2.group(1))
            ranks.append(rank)
            rows.append([rna, seed, rank, os.path.abspath(m)])

        if len(models) != 5 or sorted(ranks) != [0, 1, 2, 3, 4]:
            problems.append((rd, seed, len(models)))

# 写出 manifest
with open(os.path.join(OUT_DIR, "manifest.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["rna", "seed", "rank", "path"])
    w.writerows(rows)

# 断言与汇总
print("== manifest 汇总 ==")
from collections import Counter, defaultdict
by_rna = defaultdict(set)
for rna, seed, rank, path in rows:
    by_rna[rna].add(seed)

all_ok = True
for rna in U.RNA_SEQS:
    n_seed = len(by_rna[rna])
    n_model = sum(1 for r in rows if r[0] == rna)
    flag = "OK" if n_seed == 20 and n_model == 100 else "*** 异常 ***"
    if flag != "OK":
        all_ok = False
    print(f"  {rna}: {n_seed} seeds, {n_model} models  [{flag}]")

print(f"  总计: {len(rows)} 个 model cif")
if problems:
    print("*** 以下 seed 的 model 数量异常：", problems)
    all_ok = False
if all_ok:
    print("  断言通过：每条 RNA 20 个独立 seed × 5 个 model = 100 结构。")
else:
    print("  存在异常，请先检查数据完整性。")
print("写入 results/manifest.csv")
