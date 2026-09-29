# -*- coding: utf-8 -*-
"""
生成 mCSM-NA 单突变验证表（三组 RNA 各一份，内容相同，格式为 mCSM 输入格式）：
    每行： <链名> <野生残基><位置><突变残基>   例： A G27D
三组 RNA 各自对应一个结构文件提交，故分别输出三个 .txt 文件。
"""
import os

CHAIN = "A"   # 蛋白链名（AF3 cif 中蛋白为 chain A）

# (野生残基, 位置, 突变残基) —— 与 05_combinations.py 的单突变库一致
MUTS = [
    ("G", 25, "E"),
    ("I", 26, "D"),
    ("G", 27, "D"), ("G", 27, "T"), ("G", 27, "V"), ("G", 27, "I"),
    ("R", 28, "A"), ("R", 28, "S"),
    ("H", 29, "N"), ("H", 29, "F"),
    ("K", 30, "H"), ("K", 30, "N"),
    ("T", 31, "A"), ("T", 31, "V"), ("T", 31, "I"), ("T", 31, "L"),
    ("Y", 32, "F"),
    ("A", 59, "P"), ("A", 59, "S"),
    ("K", 60, "H"), ("K", 60, "R"),
    ("S", 98, "A"),
    ("M", 132, "D"), ("M", 132, "E"),
]

RNAS = ["GUGCGCG", "GUGCACG", "AUGCAGC"]

OUT_DIR = "results"
os.makedirs(OUT_DIR, exist_ok=True)

for rna in RNAS:
    path = os.path.join(OUT_DIR, f"mcsmna_mutations_{rna}.txt")
    with open(path, "w", encoding="utf-8") as f:
        for wt, resi, sub in MUTS:
            f.write(f"{CHAIN} {wt}{resi}{sub}\n")
    print(f"写入 {path}（{len(MUTS)} 条）")
