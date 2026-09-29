# -*- coding: utf-8 -*-
"""
阶段 1 —— 质控（标准档）
对 manifest 中每一个 model cif 逐条做结构完整性与置信度检查。

硬性剔除（HARD_FAIL，接触分析会跳过）：
  - 缺 chain B（RNA 链）
  - chain A 残基数 != 199（蛋白链不完整）
  - +1 位（chain B resi 5）碱基重原子不齐全（无法做碱基接触）

软警告（WARN，仅标记，不剔除）：
  - +1 碱基平均 pLDDT < 60
  - iptm < 0.5
  - has_clash = True

产出：results/qc_report.csv 、results/qc_summary.md
"""
import os
import csv
import glob
import json
import re

import af_utils as U

OUT_DIR = "results"
os.makedirs(OUT_DIR, exist_ok=True)

# 阈值（标准档）
PLDDT_WARN = 60.0
IPTM_WARN = 0.5


def read_summary_confidences(seed_dir, rank):
    """读取对应 rank 的 summary_confidences JSON，返回 dict。"""
    pat = os.path.join(seed_dir, f"*_summary_confidences_{rank}.json")
    hits = glob.glob(pat)
    if not hits:
        return {}
    with open(hits[0], "r", encoding="utf-8") as f:
        return json.load(f)


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def min_of(xs):
    xs = [x for x in xs if x is not None]
    return min(xs) if xs else None


report = []
count = {"total": 0, "hard_fail": 0, "warn": 0, "pass": 0}

with open(os.path.join(OUT_DIR, "manifest.csv"), encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rna, seed, rank, path = row["rna"], row["seed"], int(row["rank"]), row["path"]
        count["total"] += 1

        flags = []
        # 解析结构
        cols, atoms = U.parse_atom_site(path)
        rA = U.residues_by_chain(atoms, U.PROT_CHAIN)
        rB = U.residues_by_chain(atoms, U.RNA_CHAIN)

        # +1 碱基
        plus1_all = U.atoms_of(atoms, U.RNA_CHAIN, U.PLUS1_RESI)
        plus1_resn = plus1_all[0]["atom_site.label_comp_id"] if plus1_all else "?"
        plus1_base = U.atoms_of(atoms, U.RNA_CHAIN, U.PLUS1_RESI, names=U.BASE_ATOMS)
        base_names = set(a["atom_site.label_atom_id"] for a in plus1_base)
        expected = U.PURINE_BASE.get(plus1_resn, set())
        base_complete = base_names >= expected

        # 结构完整性
        chainA_n = len(rA)
        chainB_n = len(rB)
        if chainB_n == 0:
            flags.append("HARD:no_RNA_chainB")
        if chainA_n != 199:
            flags.append("HARD:chainA_res!=199")
        if not base_complete:
            flags.append("HARD:plus1_base_incomplete")

        # 置信度
        conf = read_summary_confidences(os.path.dirname(path), rank)
        iptm = conf.get("iptm")
        ptm = conf.get("ptm")
        ranking = conf.get("ranking_score")
        has_clash = conf.get("has_clash")
        frac_dis = conf.get("fraction_disordered")

        plus1_plddt = [U.atom_plddt(a) for a in plus1_base]
        plus1_plddt_mean = mean(plus1_plddt)
        plus1_plddt_min = min_of(plus1_plddt)

        # 关键残基 CA pLDDT
        key_ca_plddt = []
        for resi, exp in U.KEY_RESIDUES.items():
            ca = U.atoms_of(atoms, U.PROT_CHAIN, resi, names={"CA"})
            if ca:
                key_ca_plddt.append(U.atom_plddt(ca[0]))
        key_ca_mean = mean(key_ca_plddt)

        if plus1_plddt_mean is not None and plus1_plddt_mean < PLDDT_WARN:
            flags.append("WARN:plus1_plddt<%.0f" % PLDDT_WARN)
        if iptm is not None and iptm < IPTM_WARN:
            flags.append("WARN:iptm<%.1f" % IPTM_WARN)
        if has_clash:
            flags.append("WARN:has_clash")

        hard_fail = any(f.startswith("HARD:") for f in flags)
        warn = any(f.startswith("WARN:") for f in flags)
        if hard_fail:
            count["hard_fail"] += 1
        elif warn:
            count["warn"] += 1
        else:
            count["pass"] += 1

        report.append({
            "rna": rna, "seed": seed, "rank": rank,
            "chainA_res": chainA_n, "chainB_res": chainB_n,
            "plus1_resn": plus1_resn, "plus1_base_complete": base_complete,
            "plus1_base_plddt_mean": round(plus1_plddt_mean, 2) if plus1_plddt_mean is not None else "",
            "plus1_base_plddt_min": round(plus1_plddt_min, 2) if plus1_plddt_min is not None else "",
            "key_ca_plddt_mean": round(key_ca_mean, 2) if key_ca_mean is not None else "",
            "iptm": iptm, "ptm": ptm, "ranking_score": ranking,
            "has_clash": has_clash, "fraction_disordered": frac_dis,
            "qc_pass": not hard_fail,
            "qc_flags": ";".join(flags),
        })

# 写出 csv
fieldnames = list(report[0].keys())
with open(os.path.join(OUT_DIR, "qc_report.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(report)

# 按 rna 汇总
from collections import defaultdict
summ = defaultdict(lambda: {"n": 0, "fail": 0, "warn": 0, "pass": 0})
for r in report:
    s = summ[r["rna"]]
    s["n"] += 1
    if not r["qc_pass"]:
        s["fail"] += 1
    elif r["qc_flags"]:
        s["warn"] += 1
    else:
        s["pass"] += 1

lines = ["# QC 汇总（标准档）", ""]
lines.append(f"- 总计 {count['total']} 个 model；硬剔除 {count['hard_fail']}，警告 {count['warn']}，通过 {count['pass']}。")
lines.append("")
lines.append("| RNA | 总数 | 通过 | 警告 | 硬剔除 |")
lines.append("|---|---|---|---|---|")
for rna in U.RNA_SEQS:
    s = summ[rna]
    lines.append(f"| {rna} | {s['n']} | {s['pass']} | {s['warn']} | {s['fail']} |")

# 列出被硬剔除的模型
failed = [r for r in report if not r["qc_pass"]]
if failed:
    lines.append("")
    lines.append("## 硬剔除模型清单")
    lines.append("")
    for r in failed:
        lines.append(f"- {r['rna']} seed={r['seed']} rank={r['rank']}  [{r['qc_flags']}]")

with open(os.path.join(OUT_DIR, "qc_summary.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("== QC 汇总 ==")
print("\n".join(lines))
print("\n写入 results/qc_report.csv, results/qc_summary.md")
