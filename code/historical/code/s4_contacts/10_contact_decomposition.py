# -*- coding: utf-8 -*-
"""
阶段 10 —— 差异接触的「接触类型」分解

对每个与 +1 核苷酸接触的蛋白残基，把接触拆成：
  蛋白侧  ×  RNA 侧
  侧链(sidechain) / 主链(backbone)  ×  碱基(base) / 糖(sugar) / 磷酸(phosphate)

目的：区分「可设计」的碱基特异侧链接触 vs 「结构性」的主链/糖磷酸接触。
  - 侧链-碱基接触 = 可设计（可通过突变侧链调谐碱基特异性）
  - 主链接触     = 结构性（突变侧链改不动骨架，基本不可设计）

产出：results/contact_decomposition.csv
"""
import os
import csv
from collections import defaultdict

import af_utils as U

OUT = "results"

# 蛋白原子分类
BB = {"N", "CA", "C", "O", "OXT"}
# RNA 原子分类
BASE = {"N1", "C2", "N3", "C4", "C5", "C6", "N7", "C8", "N9", "O6", "N2", "N6"}
SUGAR = {"C1'", "C2'", "O2'", "C3'", "O3'", "C4'", "O4'", "C5'", "O5'"}
PHOS = {"P", "OP1", "OP2"}

CUTOFF = 5.0


def classify_prot(name):
    return "bb" if name in BB else "sc"


def classify_rna(name):
    if name in BASE:
        return "base"
    if name in SUGAR:
        return "sugar"
    if name in PHOS:
        return "phos"
    return "other"


def contact_type(prot_atoms, rna_atoms):
    """返回 (has_sc_base, has_bb_base, has_sc_sugphos, has_bb_sugphos)。"""
    sc_base = bb_base = sc_sp = bb_sp = False
    for pa in prot_atoms:
        pcls = classify_prot(pa["atom_site.label_atom_id"])
        pc = U.coord(pa)
        for ra in rna_atoms:
            rcls = classify_rna(ra["atom_site.label_atom_id"])
            rc = U.coord(ra)
            dx, dy, dz = pc[0]-rc[0], pc[1]-rc[1], pc[2]-rc[2]
            if (dx*dx + dy*dy + dz*dz) ** 0.5 > CUTOFF:
                continue
            if pcls == "sc" and rcls == "base":
                sc_base = True
            elif pcls == "bb" and rcls == "base":
                bb_base = True
            elif pcls == "sc" and rcls in ("sugar", "phos"):
                sc_sp = True
            elif pcls == "bb" and rcls in ("sugar", "phos"):
                bb_sp = True
    return sc_base, bb_base, sc_sp, bb_sp


# 读 manifest（跳过不必要，全部处理）
manifest = list(csv.DictReader(open(os.path.join(OUT, "manifest.csv"), encoding="utf-8-sig")))

# 聚合：rna -> resi -> 各类型计数
agg = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0]))   # [sc_base, bb_base, sc_sp, bb_sp]
nmodel = defaultdict(int)
resn_map = {}

for m in manifest:
    rna = m["rna"]
    nmodel[rna] += 1
    cols, atoms = U.parse_atom_site(m["path"])
    plus1 = U.atoms_of(atoms, U.RNA_CHAIN, U.PLUS1_RESI)
    rA = U.residues_by_chain(atoms, U.PROT_CHAIN)
    for resi, patoms in rA.items():
        resn_map[resi] = patoms[0]["atom_site.label_comp_id"]
        sc_base, bb_base, sc_sp, bb_sp = contact_type(patoms, plus1)
        a = agg[rna][resi]
        a[0] += sc_base; a[1] += bb_base; a[2] += sc_sp; a[3] += bb_sp

# 写 CSV：每 RNA × 残基 的频率
rows = []
for rna in U.RNA_SEQS:
    for resi in sorted(agg[rna]):
        a = agg[rna][resi]; n = nmodel[rna]
        sc_base = round(a[0]/n, 2); bb_base = round(a[1]/n, 2)
        sc_sp = round(a[2]/n, 2); bb_sp = round(a[3]/n, 2)
        # 设计性：侧链-碱基接触高 = 可设计特异性；主链为主 = 结构性
        if sc_base >= 0.5 and bb_base < sc_base:
            tag = "可设计(侧链-碱基特异)"
        elif bb_base >= 0.5 or bb_sp >= 0.5:
            tag = "结构性(主链/糖磷酸为主)"
        elif sc_sp >= 0.5:
            tag = "可设计(侧链-糖磷酸)"
        else:
            tag = ""
        rows.append(dict(rna=rna, resi=resi, resn=resn_map[resi],
                         sc_base=sc_base, bb_base=bb_base, sc_sugphos=sc_sp, bb_sugphos=bb_sp,
                         designability=tag))

with open(f"{OUT}/contact_decomposition.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["rna", "resi", "resn", "sc_base", "bb_base",
                                      "sc_sugphos", "bb_sugphos", "designability"])
    w.writeheader()
    w.writerows(rows)

# 聚焦关键/候选残基
KEYS = [27, 28, 29, 30, 31, 32, 57, 58, 59, 60, 67, 68, 69, 70, 72, 98, 99, 102, 105, 129, 130, 131, 132, 133]
print("== 关键残基 接触类型分解（A-swap GUGCACG，频率 0-1）==")
print(f"{'resi':>4} {'resn':>4} {'侧链-碱基':>8} {'主链-碱基':>8} {'侧链-糖磷':>8} {'主链-糖磷':>8}  设计性")
for r in rows:
    if r["rna"] == "GUGCACG" and r["resi"] in KEYS and (r["sc_base"] > 0 or r["bb_base"] > 0 or r["sc_sugphos"] > 0 or r["bb_sugphos"] > 0):
        print(f"{r['resi']:>4} {r['resn']:>4} {r['sc_base']:>8.2f} {r['bb_base']:>8.2f} "
              f"{r['sc_sugphos']:>8.2f} {r['bb_sugphos']:>8.2f}  {r['designability']}")

print(f"\n写入 {OUT}/contact_decomposition.csv")
