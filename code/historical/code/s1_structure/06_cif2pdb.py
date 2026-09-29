# -*- coding: utf-8 -*-
"""
阶段 6 —— cif -> pdb 批量转换（为 mCSM-NA 等服务器准备结构文件）

用法：
  uv run --with gemmi python 06_cif2pdb.py [representative|rank0|all]

模式：
  representative（默认）—— 每条 RNA 只挑 1 个代表结构（rank0）：
        GUGCGCG / GUGCACG 取 seed 最小的 rank0；
        AUGCAGC 自动挑 +1 碱基 pLDDT 最高的 rank0（因其 +1 位整体置信度偏低）。
  rank0 —— 每条 RNA 全部 20 个 seed 的 rank0（共 60 个）。
  all   —— 全部 300 个 model。

产出：results/pdb/{rna}_seed{seed}_rank{rank}.pdb
并在转换后自动校验：蛋白链 A 是否 199 残基、RNA 链 B 是否 7 残基。
"""
import os
import sys
import csv

import gemmi

OUT = os.path.join("results", "pdb")
os.makedirs(OUT, exist_ok=True)

MODE = sys.argv[1] if len(sys.argv) > 1 else "representative"
assert MODE in ("representative", "rank0", "all"), f"未知模式 {MODE}"

# 读取清单与质控
manifest = list(csv.DictReader(open("results/manifest.csv", encoding="utf-8-sig")))
qc = {(r["rna"], r["seed"], int(r["rank"])): r
      for r in csv.DictReader(open("results/qc_report.csv", encoding="utf-8-sig"))}

RNA_SEQS = ["GUGCGCG", "GUGCACG", "AUGCAGC"]


def seed_int(seed):
    return int(seed) if seed.isdigit() else 10 ** 9


def plus1_plddt(m):
    q = qc.get((m["rna"], m["seed"], int(m["rank"])), {})
    v = q.get("plus1_base_plddt_mean", "")
    try:
        return float(v)
    except (TypeError, ValueError):
        return -1.0


def pick():
    if MODE == "all":
        return manifest
    if MODE == "rank0":
        return [m for m in manifest if m["rank"] == "0"]

    # representative
    chosen = []
    for rna in RNA_SEQS:
        r0 = [m for m in manifest if m["rna"] == rna and m["rank"] == "0"]
        if rna == "AUGCAGC":
            r0.sort(key=plus1_plddt, reverse=True)      # 挑 +1 pLDDT 最高
        else:
            r0.sort(key=lambda m: seed_int(m["seed"]))   # 挑 seed 最小
        chosen.append(r0[0])
    return chosen


def convert(m):
    cif = m["path"]
    st = gemmi.read_structure(cif)
    out = os.path.join(OUT, f"{m['rna']}_seed{m['seed']}_rank{m['rank']}.pdb")
    st.write_pdb(out)

    # 校验：链与残基数
    model = st[0]
    chains = {}
    for ch in model:
        chains[ch.name] = len([r for r in ch])
    nA = chains.get("A", 0)
    nB = chains.get("B", 0)
    flag = "OK" if nA == 199 and nB == 7 else "*** 异常 ***"
    pl = plus1_plddt(m)
    print(f"  {m['rna']} seed{m['seed']} rank{m['rank']} -> "
          f"{os.path.basename(out)}  链A={nA} 链B={nB} [{flag}] +1pLDDT={pl}")
    return out, flag


print(f"模式：{MODE}")
rows = pick()
print(f"待转换：{len(rows)} 个 model -> results/pdb/")

bad = 0
for m in rows:
    out, flag = convert(m)
    if flag != "OK":
        bad += 1

print(f"\n完成：转换 {len(rows)} 个；异常 {bad} 个。")
