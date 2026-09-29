# -*- coding: utf-8 -*-
"""
阶段 21 —— 靶点 C（编辑 C，0位 = RNA res 4）到酶催化中心的距离分析

核心思路：
  APOBEC 催化脱氨发生在「靶点 C(0) 碱基」上，催化中心由
  N57/H70/E72/W99/C102/C105（含锌配位 H70/C102/C105、催化 E72）组成。
  对每个 WT/突变体 × GCG/GCA 结构：
    1) d(C→core)：靶 C 碱基任两原子到「任一催化中心残基侧链原子」的最小距离；
    2) d(C→E72OE)：靶 C 的 C4/N4（被脱氨原子）到催化 E72 侧链羧基的最小距离；
    3) 锌配位残基 (H70/C102/C105) 各自到靶 C 的最小距离。
  若突变使靶 C 远离催化核心（d 变大），提示可能降低总体活性/脱氨效率
  （对应实验 on-target 保留率下降）；距离保持则提示活性几何未受扰动。

比较对象（都有 5 model 可用）：
  - WT：new/mut/folds_2026_09_08_16_18/wt_{gcg|gca}
  - 突变：new/mut/*_{gcg|gca}（14 个，batch1）+ folds 目录中突变（batch2）

产出：results/targetC_catalytic_dist_summary.csv
      results/targetC_catalytic_dist_detail.csv
"""
import os, csv, glob
from collections import defaultdict

import af_utils as U

C0_RESI = 4          # 靶点 C（0位）在 RNA 链的 resi
CAT_RES = [57, 70, 72, 99, 102, 105]   # 催化核心残基
SIDECHAIN_EXCL = {"N", "CA", "C", "O"} # 排除主链原子
ZN = [70, 102, 105]   # 锌配位
E72 = 72

MAINCHAIN_RNA = {"P", "OP1", "OP2", "O5'", "C5'", "C4'", "O4'", "C3'", "O3'", "C2'", "O2'", "C1'"}

def sidechain(atoms):
    return [a for a in atoms if a.get("atom_site.label_atom_id") not in SIDECHAIN_EXCL]

def base_c_atoms(atoms):
    """RNA res4 的碱基原子（排除糖/磷酸）"""
    return [a for a in atoms if a.get("atom_site.label_atom_id") not in MAINCHAIN_RNA]

def sidechain_carboxyl(atoms):
    """E72 羧基 OE1/OE2（催化脱氨的质子供体端）"""
    return [a for a in atoms if a.get("atom_site.label_atom_id") in ("OE1", "OE2")]

def process(dirname, prefix=None):
    """返回 dict[resi] -> {resn, d_core, d_e72, zn70, zn102, zn105, d_zn_min}"""
    # 收集所有 model
    res_accum = defaultdict(list)
    fjson = sorted(glob.glob(os.path.join(dirname, "*full_data*.json")))
    if not fjson:
        return None
    for jf in fjson:
        cif = jf.replace("full_data", "model").replace(".json", ".cif")
        if not os.path.exists(cif):
            # model file naming: fold_{name}_model_{k}.cif vs full_data_{k}
            import re
            m = re.search(r"full_data_(\d+).json", jf)
            k = m.group(1)
            base = os.path.basename(jf)[:jf.find("full_data")]
            cand = os.path.join(dirname, f"{base}model_{k}.cif")
            cif = cand if os.path.exists(cand) else None
        if not cif:
            continue
        cols, atoms = U.parse_atom_site(cif)
        prot = U.residues_by_chain(atoms, U.PROT_CHAIN)
        c0 = base_c_atoms(U.atoms_of(atoms, U.RNA_CHAIN, C0_RESI))
        if not c0:
            continue
        rec = {}
        # 全催化核心侧链原子池
        cat_atoms = []
        for r in CAT_RES:
            cat_atoms += sidechain(prot.get(r, []))
        rec["d_core"] = U.min_dist(c0, cat_atoms)
        # E72 羧基
        e72c = sidechain_carboxyl(prot.get(E72, []))
        rec["d_e72"] = U.min_dist(c0, e72c)
        # 各锌配位残基侧链
        for r in ZN:
            rec[f"zn{r}"] = U.min_dist(c0, sidechain(prot.get(r, [])))
        # 靶 C 的 C4/N4 到 E72 OE
        c4n4 = [a for a in c0 if a["atom_site.label_atom_id"] in ("C4", "N4")]
        rec["d_C4N4_e72"] = U.min_dist(c4n4, e72c) if c4n4 else None
        for k, v in rec.items():
            if v is not None:
                res_accum[k].append(v)
    return {k: sum(v)/len(v) for k, v in res_accum.items()}

def mean_sd(xs):
    if not xs:
        return None, None
    m = sum(xs)/len(xs)
    v = sum((x-m)**2 for x in xs)/len(xs)
    return m, v**0.5

# ---- 定义比较组 ----
# WT: folds 目录 wt；batch2 突变；batch1 突变（new/mut 下无 wt，需对照）
BATCH2 = "new/mut/folds_2026_09_08_16_18"
groups = {}

# WT 对照：batch2 wt
for rna in ("gcg", "gca"):
    groups[f"wt_{rna}"] = ("WT(batch2)", f"{BATCH2}/wt_{rna}")

# batch1 mutants
for m in ["a59p", "g25e", "g25ek30h", "g27d", "g27dk30h", "g27dk30hq58m",
          "g27t", "g27tk30h", "g27tk30hq58m", "k30h", "k30hq58m", "k60r",
          "m132d", "m132e"]:
    for rna in ("gcg", "gca"):
        groups[f"{m}_{rna}"] = (f"mut:{m}", f"new/mut/{m}_{rna}")

# batch2 mutants
for m in ["q58m", "r28a", "r28s", "t31i", "t31l", "t31v", "y32f"]:
    for rna in ("gcg", "gca"):
        groups[f"{m}_{rna}"] = (f"mut:{m}", f"{BATCH2}/{m}_{rna}")

# ---- 计算 ----
results = {}
for key, (label, d) in groups.items():
    per = process(d)
    if per:
        results[key] = (label, per)

# ---- 保存 detail ----
with open("results/targetC_catalytic_dist_summary.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["group", "motif", "label", "d_C_to_core(A)", "d_C_to_E72_OE(A)",
                "d_C4N4_to_E72(A)", "zn70(A)", "zn102(A)", "zn105(A)"])
    rows = []
    for key in sorted(results):
        label, per = results[key]
        motif = "GCG" if key.endswith("gcg") else "GCA"
        mut = key.rsplit("_", 1)[0]
        rows.append([mut, motif, label,
                     f"{per.get('d_core'):.2f}" if per.get('d_core') else "",
                     f"{per.get('d_e72'):.2f}" if per.get('d_e72') else "",
                     f"{per.get('d_C4N4_e72'):.2f}" if per.get('d_C4N4_e72') else "",
                     f"{per.get('zn70'):.2f}" if per.get('zn70') else "",
                     f"{per.get('zn102'):.2f}" if per.get('zn102') else "",
                     f"{per.get('zn105'):.2f}" if per.get('zn105') else ""])
    for r in rows:
        w.writerow(r)

# ---- 打印 ----
print("=== 靶点C(RNA res4) → 催化中心 距离（5 model 平均，Å）===\n")
print(f"{'组':<22}{'motif':<6}{'C→core':>8}{'C→E72OE':>9}{'C4N4→E72':>10}{'zn70':>7}{'zn102':>7}{'zn105':>7}")
for key in sorted(results):
    label, per = results[key]
    motif = "GCG" if key.endswith("gcg") else "GCA"
    def f(v, prec=2):
        return f"{v:.{prec}f}" if v is not None else "-"
    print(f"{key:<22}{motif:<6}{f(per.get('d_core')):>8}{f(per.get('d_e72')):>9}"
          f"{f(per.get('d_C4N4_e72')):>10}{f(per.get('zn70')):>7}{f(per.get('zn102')):>7}{f(per.get('zn105')):>7}")

print("\n写入 results/targetC_catalytic_dist_summary.csv")
