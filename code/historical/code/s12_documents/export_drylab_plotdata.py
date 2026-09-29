# -*- coding: utf-8 -*-
"""
导出 Dry Lab 页面全部绘图所需数据，打包给绘图同学。

原则：每张图的 CSV 自包含、列名自解释（含单位），
      队友不需要进入项目 results/ 目录即可作画。

用法：uv run --with openpyxl python export_drylab_plotdata.py
产出：文案数据图表整理/APOBEC_DryLab_绘图数据包/
"""
import csv, json, os, re, shutil, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")
import openpyxl

ROOT = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(ROOT, "results", *p)
SRCASSETS = os.path.join(ROOT, "文案数据图表整理", "APOBEC_DryLab_Complete", "APOBEC_DryLab_assets")
OUT = os.path.join(ROOT, "文案数据图表整理", "APOBEC_DryLab_绘图数据包")
DATA = os.path.join(OUT, "data")
REF = os.path.join(OUT, "reference")
os.makedirs(DATA, exist_ok=True)
os.makedirs(REF, exist_ok=True)

WRITTEN = []


def rd(name):
    with open(R(name), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        v = float(x)
        return v
    except (TypeError, ValueError):
        return None


def w(name, header, rows, note=None):
    p = os.path.join(DATA, name)
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(header)
        for r in rows:
            wr.writerow(r)
    WRITTEN.append({"file": f"data/{name}", "rows": len(rows), "columns": header, "note": note})
    print(f"  ✓ data/{name}  ({len(rows)} 行)")


def clean(x, nd=4):
    """空值、'nan'、'inf' 一律输出为空字符串——不补 0，也不写成字面量 nan/inf。"""
    v = num(x)
    if v is None or v != v or v in (float("inf"), float("-inf")):
        return ""
    return round(v, nd)


# ===========================================================================
# Figure 2 — CP deviation diagnosis
# ===========================================================================
rows = [r for r in rd("CP偏离_汇总.csv") if r["substrate"] == "GCG"]
w("figure_02_cp_deviation.csv",
  ["construct", "z_internal_cp_longrange", "z_pocket_cp", "z_protein_targetC_cp",
   "target_C4N4_to_E72_distance_A", "activity_retention_fraction"],
  [[r["variant"], clean(r["z_intra"]), clean(r["z_pocket"]), clean(r["z_protC"]),
    clean(r["d_E72"]), clean(r["activity_retention"])] for r in rows],
  "面板 A = 前三个 z 列分组柱状图（灰带 ±3）；面板 B = z_protein_targetC_cp 对 activity_retention_fraction 散点。仅 GCG 底物。")

# ===========================================================================
# Figure 3 — per-residue ΔΔCP matrix（22 个变化最大的残基）
# ===========================================================================
wb = openpyxl.load_workbook(R("突变体基线ΔCP_全199残基.xlsx"), data_only=True)
ws = wb["2_ΔΔCP矩阵"]
allrows = list(ws.iter_rows(values_only=True))
head = allrows[0]
muts = [h for h in head[3:] if h]
data = [r for r in allrows[1:] if r and isinstance(r[0], int)]
import statistics
mat = [[num(v) or 0.0 for v in r[3:3 + len(muts)]] for r in data]
idx = sorted(sorted(range(len(data)), key=lambda i: -max(abs(x) for x in mat[i]))[:22],
             key=lambda i: data[i][0])
w("figure_03_ddcp_matrix.csv",
  ["residue_position", "wt_aa"] + [str(m) for m in muts],
  [[data[i][0], data[i][1]] + [round(v, 4) for v in mat[i]] for i in idx],
  "ΔΔCP 宽表（行=残基，列=构建体）。已按 |ΔΔCP| 最大值选出变化最大的 22 个残基，与文章图一致。")
w("figure_03_all_residues_ddcp.csv",
  ["residue_position", "wt_aa"] + [str(m) for m in muts],
  [[data[i][0], data[i][1]] + [round(v, 4) for v in mat[i]] for i in range(len(data))],
  "完整 199 残基 × 全部构建体的 ΔΔCP，供需要自行挑选残基时使用。")

# ===========================================================================
# Figure 4 — negative-control deviation diagnosis
# ===========================================================================
rows = [r for r in rd("阴性对照_偏离与PCA.csv") if r.get("substrate") == "GCG"] \
    or rd("阴性对照_偏离与PCA.csv")
CLS = {"完全失活": "Inactive", "有活性": "Active", "部分失活": "Partially inactive",
       "未测": "Not tested", "WT（GCA 底物）": "WT (GCA substrate)",
       "新失活对照（未测）": "New inactive control (not measured)",
       "WT 参照": "Wild-type reference"}
CONS = {"WT（GCG 亲本）": "WT (GCG parent)", "WT（GCA 底物）": "WT (GCA substrate)"}
wt_ref = next((num(r["d_E72"]) for r in rows
               if "WT" in r["construct"] and "GCG" in r["construct"]), None)
w("figure_04_negctrl_diagnosis.csv",
  ["construct", "is_reference_wildtype", "functional_class",
   "target_C4N4_to_E72_distance_A",
   "z_internal_cp_longrange", "z_pocket_cp", "z_protein_targetC_cp",
   "activity_retention_fraction"],
  [[CONS.get(r["construct"], r["construct"]),
    "TRUE" if "WT" in r["construct"] else "FALSE",
    CLS.get(r["functional_class"], r["functional_class"]),
    clean(r["d_E72"]), clean(r["z_intra"]), clean(r["z_pocket"]), clean(r["z_protC"]),
    clean(r["activity_retention"])] for r in rows],
  "**两套编码，必须各配一套图例**：面板 A 的柱按 `functional_class` 着色（功能类别图例）；"
  "面板 B 的柱按描述量着色——Internal CP (long-range) 蓝、Pocket CP 橙、Protein–target-C CP 绿（描述量图例）。"
  "两条图例不可合并为一条。"
  "共 29 行 = 27 个突变体/组合对照 + 2 个野生型参照（is_reference_wildtype = TRUE）。"
  "类别取值共 6 种：Active / Inactive / Partially inactive / Not tested / "
  "New inactive control (not measured) / Wild-type reference；"
  "其中「New inactive control (not measured)」是设计但未实测的失活对照，**不得并入已实测的 Inactive 组**。"
  f"面板 A 的参考线请取**本表内**野生型（GCG 亲本）的值 = {wt_ref:.3f} Å；"
  "不要使用 2.88 Å —— 那个值来自另一套几何测量（results/dE72_regression.csv 的野生型 2.884 Å），与本表不同源。"
  "E72A 的该列**留空**（未做几何建模），请勿补 0，也请勿在图上画成 0 点。"
  "另：正文「28 constructs」指的是 阴性对照_DM.csv 那一套（含 WT 换底物），与本表行数不同，作图按本表 29 行。")

# ===========================================================================
# Figure 5 — control constructs: PC space and D_M
# ===========================================================================
pc = rd("阴性对照_PC坐标.csv")
w("figure_05_negctrl_pca.csv",
  ["construct", "PC1", "PC2", "PC3", "D_M_mahalanobis_to_WT",
   "activity_retention_fraction", "functional_class"],
  [[r["construct"], clean(r["PC1"]), clean(r["PC2"]), clean(r["PC3"]), clean(r["D_M"]),
    clean(r["activity_retention"]), CLS.get(r["functional_class"], r["functional_class"])]
   for r in pc],
  "面板 A = PC1–PC2 散点（仅标注 E72A / N57W / N57A / T31D / T31A / WT-GCA / Y32F）；面板 B = D_M 横向柱状（参考线 1.57）。")

# ===========================================================================
# Figure 6 — protein-only models
# ===========================================================================
sep = rd("纯蛋白_分离度.csv")
w("figure_06a_protein_only_deviation.csv",
  ["construct", "D_M_internal_cp_all", "D_M_internal_cp_longrange",
   "D_M_pocket_cp", "activity_retention_fraction", "functional_class"],
  [[r["construct"], clean(r["D_M_P1_内部CP全"]), clean(r["D_M_P2_内部CP长程"]),
    clean(r["D_M_P3_口袋内部CP"]), clean(r["activity_retention"]),
    CLS.get(r["functional_class"], r["functional_class"])] for r in sep],
  "面板 A：三个特征集的分组柱状图。")
cls = rd("纯蛋白_分类表现.csv")
FS = {"P1_内部CP全": "Internal CP (all)", "P2_内部CP长程": "Internal CP (long-range)",
      "P3_口袋内部CP": "Pocket CP"}
w("figure_06b_protein_only_classification.csv",
  ["feature_set", "classification_accuracy", "chance_level"],
  [[FS.get(r["feature_set"], r["feature_set"]), clean(r["construct_accuracy"]), 0.5] for r in cls],
  "面板 B：柱状图，参考线 = 随机水平 0.50。")

# ===========================================================================
# Figure 7 — complex vs protein-only deviation
# ===========================================================================
dm = {r["construct"]: num(r["D_M"]) for r in rd("阴性对照_DM.csv")}
sp = {r["construct"]: num(r["D_M_P1_内部CP全"]) for r in sep}
keys = sorted([k for k in dm if k in sp and dm[k] is not None and sp[k] is not None],
              key=lambda k: sp[k])
ACT = {r["construct"]: num(r["activity_retention"]) for r in rd("阴性对照_DM.csv")}
w("figure_07_protein_only_vs_complex.csv",
  ["construct", "D_M_complex_with_RNA", "D_M_protein_only_no_RNA",
   "fraction_retained_pct", "activity_retention_fraction"],
  [[k, round(dm[k], 4), round(sp[k], 4), round(sp[k] / dm[k] * 100, 1),
    clean(ACT.get(k)) if ACT.get(k) is not None else ""] for k in keys],
  "成对柱状图；参考线 1.57；仅在 T31D 与 E72A 上标注 fraction_retained_pct。")

# ===========================================================================
# Figure 8 — single-site saturation
# ===========================================================================
er = rd("experimental_ranking.csv")


def ratio_undef(r):
    """分母（GCA）检出为 0 时比值不可定义；原表把这种情形记为 0，属编码歧义。"""
    gca = num(r["GCA"])
    return gca is None or gca == 0.0


par = next((r for r in er if "WT" in r["mut"] or "PUF" in r["mut"]), None)
par_ratio = (num(par["GCG"]) / num(par["GCA"])) if par else None
w("figure_08_single_site.csv",
  ["mutant", "on_target_GCG_fraction", "off_target_GCA_fraction", "ACA_fraction",
   "plus1_ratio_GCG_over_GCA", "plus1_ratio_defined",
   "activity_retention_vs_same_batch_parent", "read_depth", "is_parent", "reported_active"],
  [[r["mut"], clean(r["GCG"]), clean(r["GCA"]), clean(r["ACA"]),
    # 亲本行用未舍入的 GCG÷GCA（= 1.371，与正文一致）；其余行用源表的比值
    (clean(num(r["GCG"]) / num(r["GCA"])) if ("WT" in r["mut"] or "PUF" in r["mut"])
     else ("" if ratio_undef(r) else clean(r["ratio"]))),
    "FALSE" if ratio_undef(r) else "TRUE",
    clean(r["retain"]), r["depth"],
    "TRUE" if ("WT" in r["mut"] or "PUF" in r["mut"]) else "FALSE", r["active"]] for r in er],
  "散点：横轴 plus1_ratio，纵轴 activity_retention。"
  f"参考线：亲本 {par_ratio:.3f}（点线，= 亲本 GCG ÷ GCA，未舍入）、目标 2.0（橙虚线）、保留下限 0.70（绿虚线）。"
  "**星标 = K30H**，定义是「保留率 ≥ 0.70 的突变体中 +1 比最高者」——它既不是全图纵坐标最高点，也不是全图比值最高点。"
  "比值最高的三个点为 130G (3.00)、60Q (2.55)、31G (2.22)，但保留率分别只有 0.32 / 0.17 / 0.13，"
  "请在图上以灰点呈现并考虑加浅色标注，避免被读成「已达标」。"
  "**plus1_ratio_defined = FALSE 的行（31Y）**：其 GCA 检出为 0，比值不可定义（原表记为 0 属编码歧义），"
  "该行 plus1_ratio 已留空，请勿当作 0 值点绘制。")

# ===========================================================================
# Figure 9 — targeting ratio over the amplicon
# ===========================================================================
tr = rd("GCG_vs_off_ranking_WT.csv")


def ratio_defined(r):
    v = r["targeting_ratio"]
    return bool(v) and "inf" not in str(v).lower()


w("figure_09_targeting_ratio.csv",
  ["construct", "is_wildtype_parent", "on_target_C388_pct",
   "sum_GCG_editing_pct", "sum_nonGCG_editing_pct", "targeting_ratio",
   "targeting_ratio_defined", "n_nonGCG_sites_detected", "activity_retention_fraction"],
  [[r.get("mutation", ""), r.get("is_WT", ""), clean(r["C388_pct"]),
    clean(r.get("sum_GCG_pct")), clean(r["sum_nonGCG_pct"]),
    clean(r["targeting_ratio"]) if ratio_defined(r) else "",
    "TRUE" if ratio_defined(r) else "FALSE",
    clean(r.get("n_nonGCG_detected"), 1),
    clean(r.get("activity_retention"))] for r in tr],
  "面板 A：targeting_ratio 对 on_target_C388_pct（灰带 10–20% 与 35–60%，并标层中位数 2.53 / 1.20）；面板 B：对 sum_nonGCG_editing_pct 散点并加线性拟合。"
  "作图时请排除 is_wildtype_parent = TRUE 的行。targeting_ratio_defined = FALSE 表示分母为零、比值无定义，"
  "该单元格已留空请勿当 0 处理，这 9 行只在文中以「∞」记述、不入图。")

# ===========================================================================
# Figure 10 — next-round candidates
# ===========================================================================
wb2 = openpyxl.load_workbook(R("下一步实验突变候选表_61组.xlsx"), data_only=True)
rowsx = list(wb2["突变候选表_61组"].iter_rows(values_only=True))
hx = list(rowsx[0])
ci, gi, pi = hx.index("编号"), hx.index("分组"), hx.index("优先级")
mi = hx.index("突变")
recs = [r for r in rowsx[1:] if r and r[ci]]
PRI = {"必做": "Required", "首推": "top pick", "控制": "control",
       "金标准": "gold standard", "机制": "mechanism", "对照": "reference"}


def pri_en(v):
    v = str(v).strip()
    m = re.match(r"^([^（(]+)\s*[（(]([^）)]*)[）)]?$", v)
    if m:
        return f"{m.group(1).strip()} ({PRI.get(m.group(2).strip(), m.group(2).strip())})"
    return PRI.get(v, v)


w("figure_10a_candidate_groups_raw.csv",
  ["candidate_id", "group", "group_label", "mutant", "priority_en"],
  [[r[ci], str(r[gi]).split()[0], str(r[gi]), r[mi], pri_en(r[pi])] for r in recs],
  "61 条候选的原始清单，供核对条目。group = A–E。")
grp = {}
for r in recs:
    grp.setdefault(str(r[gi]).split()[0], []).append(pri_en(r[pi]))
w("figure_10b_candidate_group_sizes.csv",
  ["group", "group_label_en", "n_candidates"],
  [[k, {"A": "A replication", "B": "B new single", "C": "C new combinations",
        "D": "D controls", "E": "E relaxed pairing"}.get(k, k), len(grp[k])]
   for k in sorted(grp)],
  "面板 A：各组规模柱状图。")
allp = sorted({v for k in grp for v in grp[k]})
w("figure_10c_candidate_priority_matrix.csv",
  ["group"] + allp,
  [[k] + [sum(1 for v in grp[k] if v == p) for p in allp] for k in sorted(grp)],
  "面板 B：组内优先级堆叠柱状图（列即优先级类别）。")

# ===========================================================================
# Figure 11 — retrospective test of the AiCE filter
# ===========================================================================
fa = os.path.join(ROOT, "Apobec前期设计附件", "Apobec前期设计附件", "全长反设计.fa")
seqs, cur = [], None
for line in open(fa, encoding="utf-8"):
    line = line.rstrip("\n")
    if line.startswith(">"):
        if cur: seqs.append("".join(cur))
        cur = []
    elif cur is not None:
        cur.append(line.strip())
if cur: seqs.append("".join(cur))
samp = seqs[1:]
L = min(len(s) for s in samp)
prof = []
for i in range(L):
    col = [s[i] for s in samp]
    aa = max(set(col), key=col.count)
    prof.append((i + 1, aa, col.count(aa) / len(col)))
w("figure_11a_sampling_frequency_by_position.csv",
  ["position", "most_frequent_aa", "frequency"],
  [[p, aa, round(f, 4)] for p, aa, f in prof],
  "ProteinMPNN 采样（%d 条序列）逐位点最高频率，供自行重算「通过阈值位点数」曲线。" % len(samp))
ths = [round(0.001 + k * (0.95 - 0.001) / 39, 4) for k in range(40)]
w("figure_11b_positions_passing_threshold.csv",
  ["sampling_frequency_threshold", "n_positions_passing"],
  [[t, sum(1 for _, _, f in prof if f >= t)] for t in ths],
  "面板 A 的曲线数据；参考线 γ = 0.5（卷曲区）与 β = 0.8（结构化区）。")
aic = rd("AiCE过滤器_位点级.csv")
want = ["H29P", "K30T", "N57D", "A59P"]
found = {}
for r in aic:
    k = f"{r['WT']}{r['位点']}{r['MPNN最高频aa']}"
    if k in want:
        found[k] = (r["最高频"], r["适用阈值"], r["二级结构"])
w("figure_11c_contested_substitutions.csv",
  ["substitution", "sampling_frequency", "applicable_threshold_gamma",
   "secondary_structure", "exceeds_threshold"],
  [[k, clean(found[k][0]), clean(found[k][1], 2), found[k][2],
    "TRUE" if num(found[k][0]) >= num(found[k][1]) else "FALSE"] for k in want if k in found],
  "面板 B：柱状图，参考线 γ = 0.5。")

# ===========================================================================
# Figure 15 — 设计批次的实测结果
# ===========================================================================
batch = rd("下一批突变_绘图用表.csv")
GRP_EN = {"A": "A replication", "B": "B new single substitutions",
          "C": "C new combinations", "D": "D control variants",
          "E": "E relaxed / anomalous", "new": "not in candidate list"}
w("figure_15a_batch_rof_vs_retention.csv",
  ["construct", "candidate_id", "design_group", "design_group_label_en",
   "on_target_GCG_over_offtarget_GCA_ratio", "ratio_defined",
   "ROF_ratio_over_same_batch_parent", "activity_retention_fraction",
   "is_reference_parent", "excluded_failed_well"],
  [[r["mut"], r["cid"], r["grp"], GRP_EN.get(r["grp"], r["grp"]),
    clean(r["ratio"]) if r["undef"] != "TRUE" else "",
    "FALSE" if r["undef"] == "TRUE" else "TRUE",
    clean(r["rof"]) if r["undef"] != "TRUE" else "",
    clean(r["ret"]),
    "TRUE" if r["mut"] == "PUF12" else "FALSE",
    r.get("excluded_failed_well", "FALSE")] for r in batch],
  "面板 A：散点图，横轴 = activity_retention_fraction，纵轴 = ROF_ratio_over_same_batch_parent，按 design_group 着色。"
  "ratio_defined = FALSE 的构建体（c.871 未检出）不得按 0 绘制，应单独标记。"
  "参考线：ROF = 1.00（同批亲本水平）、activity_retention_fraction = 0.30（on-target 解读下限）。"
  "本批同批亲本 PUF12 比值 = 1.070（ROF 的分母即为此值），三批亲本比 1.371 → 1.191 → 1.070。"
  "excluded_failed_well = TRUE 的行（27T-30H-58M）是判为测量失败的孔，其保留率不是有效读数，"
  "只用于标注「此孔失败」，不得作为数据点、也不得参与任何计算。")

w("figure_15b_group_d_pairing.csv",
  ["bar_order", "comparison", "construct", "candidate_id", "batch",
   "position_132_residue", "on_target_GCG_over_offtarget_GCA_ratio",
   "ROF_ratio_over_same_batch_parent", "activity_retention_fraction",
   "excluded_failed_well"],
  [[1, "same scaffold, two batches", "27T-30H-58M", "C13", "combinatorial batch",
    "absent", 2.156, 1.809, 0.772, "FALSE"],
   [2, "same scaffold, two batches", "27T-30H-58M-132E", "D03", "this batch",
    "E", 2.0825, 1.9463, 0.6727, "FALSE"],
   [3, "Group D pair, same scaffold", "25E-30H-58M-132D", "D04", "this batch",
    "D", 2.5791, 2.4104, 0.3398, "FALSE"],
   [4, "Group D pair, same scaffold", "25E-30H-58M-132E", "D05", "this batch",
    "E", 1.6603, 1.5517, 0.7517, "FALSE"],
   [5, "failed well, excluded (not a result)", "27T-30H-58M", "C13", "this batch",
    "absent", "", "", 0.0789, "TRUE"]],
  "面板 B：分组柱状图，主量为 activity_retention_fraction。第 1–2 根是同骨架跨两批的两次测量"
  "（0.772 / 0.673，相互复现），第 3–4 根是同背景 132D/132E 配对（0.340 / 0.752，2.2 倍）。"
  "第 5 根 excluded_failed_well = TRUE，是判为测量失败的孔，画成白底＋红描边＋斜线阴影的「幽灵柱」，"
  "仅用于说明该孔被判失败，不得当作有效低活性数据点。"
  "第 1 根的 ratio/ROF 取自组合批（亲本比 1.192），其 ROF 按一致口径重算为 1.809；"
  "该骨架的 ratio 与 activity_retention_fraction 可直接引用。")

# ===========================================================================
# Figure 16 — 复现检验与 27 位饱和（第三批，64 样本 / 29 组）
# ===========================================================================
b3 = rd("第三批_绘图用表.csv")

w("figure_16a_cross_batch_replication.csv",
  ["construct", "batch", "on_target_GCG_over_offtarget_GCA_ratio",
   "activity_retention_fraction", "same_batch_parent_ratio",
   "ROF_ratio_over_same_batch_parent", "note"],
  [["27T-30H-58M", "combinatorial batch", 2.156, 0.772, 1.191, 1.810, ""],
   ["27T-30H-58M-132E", "supplementary batch", 2.083, 0.673, 1.070, 1.946, "carries all three substitutions"],
   ["27T-30H-58M", "this batch", 1.278, 0.980, 1.049, 1.218, "direct replication"],
   ["K30H", "single-mutant batch", 1.710, 0.840, 1.371, 1.247, ""],
   ["K30H", "this batch", 1.101, 0.872, 1.049, 1.050, "direct replication"]],
  "面板 A：折线图，x = batch（三档顺序固定），y = ROF_ratio_over_same_batch_parent，两条线分别连 27T-30H-58M 与 K30H。"
  "参考线 y = 1.00（同批亲本水平）。**三个批次的亲本比值不同（1.191 / 1.070 / 1.049），因此必须用 ROF 而非原始比值作纵轴。**"
  "本图要传达的是：两条线在第三个批次都明显下移——即此前报告的 1.71 与 2.16/2.08 未复现。")

w("figure_16b_batch3_groups.csv",
  ["construct", "group_type", "on_target_GCG_over_offtarget_GCA_ratio", "ROF_ratio_over_same_batch_parent",
   "activity_retention_fraction", "on_target_C388_fraction", "off_target_C871_fraction",
   "ACA_class_C295_fraction", "C295_not_detected", "n_samples", "is_reference_group"],
  [[r["mut"], r["grp"], clean(r["ratio"]), clean(r["rof"]), clean(r["ret"]),
    clean(r["c388"]), clean(r["c871"]), clean(r["c295"]),
    r["c295_not_detected"], r["n"], r["is_ref"]] for r in b3],
  "面板 B / C：本批 29 个组的全部量。面板 B = ROF 对 activity_retention_fraction 散点，只取 group_type = single 且组名以 27 开头者"
  "（即 27 位饱和的 10 个替换）；面板 C = 同一 10 个替换的 ACA_class_C295_fraction 柱状图，参考线取 is_reference_group = TRUE 中 "
  "construct = PUF12 的 0.3091，C295_not_detected = TRUE 的柱标 n.d.（低于 5% 检测线），**不要画成 0**。"
  "本批同批亲本 PUF12 比值为 1.049（ROF 的分母）。")

# ===========================================================================
# 参考图（页面现有 16 张，按文章编号命名）
# ===========================================================================
FIGREF = [("figure_1_workflow.png", "figure_01_workflow.png"),
          ("figure_2_cp_deviation.png", "figure_02_cp_deviation.png"),
          ("figure_3_ddcp_heatmap.png", "figure_03_ddcp_heatmap.png"),
          ("figure_4_negctrl_diagnosis.png", "figure_04_negctrl_diagnosis.png"),
          ("figure_5_negctrl_pca.png", "figure_05_negctrl_pca.png"),
          ("figure_6_protein_only_pca.png", "figure_06_protein_only.png"),
          ("figure_7_protein_only_vs_complex.png", "figure_07_protein_only_vs_complex.png"),
          ("figure_8_single_site_validation.png", "figure_08_single_site.png"),
          ("figure_9_targeting_ratio.png", "figure_09_targeting_ratio.png"),
          ("figure_10_candidate_overview.png", "figure_10_candidates.png"),
          ("figure_11_method_retrospective.png", "figure_11_aice_filter.png"),
          ("figure_12_clustering_activity.png", "figure_12_clustering_activity.png"),
          ("figure_13_clustering_stability.png", "figure_13_clustering_stability.png"),
          ("figure_14_key_residues.png", "figure_14_key_residues.png"),
          ("figure_15_designed_batch.png", "figure_15_designed_batch.png"),
          ("figure_16_replication_saturation.png", "figure_16_replication_saturation.png")]
print("参考图：")
for s, d in FIGREF:
    sp = os.path.join(SRCASSETS, s)
    if os.path.exists(sp):
        shutil.copy2(sp, os.path.join(REF, d))
        print(f"  ✓ reference/{d}")
    else:
        print(f"  ✗ 缺失 {s}")

# ===========================================================================
# 清单
# ===========================================================================
manifest = {
    "package": "APOBEC Dry Lab — 绘图数据交付包",
    "created_for": "绘图同学，用于重绘 Dry Lab 页面全部图",
    "article": "APOBEC_DryLab_Complete（Dry Lab 页面，共 16 张图）",
    "figures_in_scope": {
        "figure_02 – figure_11": "本次交付数据，由本包 data/ 中对应 CSV 生成",
        "figure_15": "设计批次的实测结果，由 data/figure_15a、figure_15b 生成",
        "figure_16": "复现检验与 27 位饱和，由 data/figure_16a、figure_16b 生成",
        "figure_01, figure_12 – figure_14": "聚类分析图，数据在队友自己的 skill_clustering 交付包中；"
                                            "本包 reference/ 仅提供现图供版式参考",
    },
    "data_files": WRITTEN,
}
with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


COLDESC = {
    "construct": "构建体名（突变体/组合/对照）",
    "mutant": "单点突变体名（如 30H = K30H）",
    "residue_position": "残基序号（1-based，对应 199 aa 编号）",
    "wt_aa": "该位点的野生型氨基酸（单字母）",
    "functional_class": "功能类别：Active / Inactive / Partially inactive / Not tested / WT (GCA substrate)",
    "is_reference_wildtype": "TRUE = 该行是野生型参照，不是突变体对照",
    "is_wildtype_parent": "TRUE = 该行是同批亲本，作画时应排除",
    "is_parent": "TRUE = 该行是亲本（用于定位参考线）",
    "reported_active": "原表标注是否有活性（True/False）",
    "activity_retention_fraction": "活性保留率（相对同批亲本，0–1 小数；混合了表达、稳定性与催化，非纯化活性）",
    "activity_retention_vs_same_batch_parent": "同上，列为该批次口径",
    "z_internal_cp_longrange": "蛋白内部长程接触概率相对野生型的 z 值（SD 数）",
    "z_pocket_cp": "活性口袋内部接触概率相对野生型的 z 值",
    "z_protein_targetC_cp": "蛋白–靶位 C 接触概率相对野生型的 z 值",
    "target_C4N4_to_E72_distance_A": "靶碱基 C4N4 原子到催化谷氨酸 E72 的距离（埃）；野生型参考值 2.88",
    "on_target_GCG_fraction": "靶点 c.388（GCG）编辑率（0–1 小数）",
    "off_target_GCA_fraction": "脱靶 c.871（GCA）编辑率（0–1 小数）",
    "ACA_fraction": "c.295（ACA）编辑率（0–1 小数）",
    "plus1_ratio_GCG_over_GCA": "+1 比 = c.388 编辑率 ÷ c.871 编辑率",
    "read_depth": "该样本测序深度",
    "on_target_C388_pct": "靶点 c.388 编辑率（%）",
    "sum_GCG_editing_pct": "全部 GCG 位点编辑率之和（%）",
    "sum_nonGCG_editing_pct": "全部非 GCG 位点编辑率之和（%）",
    "targeting_ratio": "靶向比 = Σ(GCG) ÷ Σ(非 GCG)；分母为零时无定义（留空）",
    "targeting_ratio_defined": "FALSE = 分母为零，比值无定义，请勿当 0 处理",
    "n_nonGCG_sites_detected": "检出编辑的非 GCG 位点数",
    "PC1": "第一主成分坐标（白化基仅由野生型 seed 定义）",
    "PC2": "第二主成分坐标",
    "PC3": "第三主成分坐标",
    "D_M_mahalanobis_to_WT": "相对野生型的马氏距离 D_M；零假设 95 分位 = 1.57",
    "D_M_complex_with_RNA": "复合物（含 RNA）条件下的 D_M",
    "D_M_protein_only_no_RNA": "纯蛋白（无 RNA）条件下的 D_M",
    "fraction_retained_pct": "纯蛋白 D_M ÷ 复合物 D_M（%），即未被 RNA 解释的那部分偏离占比",
    "D_M_internal_cp_all": "纯蛋白条件下、以全部内部 CP 为特征集的 D_M",
    "D_M_internal_cp_longrange": "纯蛋白条件下、仅用长程内部 CP 的 D_M",
    "D_M_pocket_cp": "纯蛋白条件下、仅用口袋内部 CP 的 D_M",
    "feature_set": "特征集名称",
    "classification_accuracy": "把构建体判入失活组/活性组的准确率（0–1）",
    "chance_level": "随机水平参考线 = 0.50",
    "candidate_id": "候选编号 C01–C61",
    "group": "候选分组字母 A–E",
    "group_label": "候选分组全称（原表中文）",
    "group_label_en": "候选分组英文标签（作图用）",
    "priority_en": "优先级（已译为英文，如 P0 (top pick)）",
    "n_candidates": "该组候选数",
    "position": "残基序号（1-based）",
    "most_frequent_aa": "ProteinMPNN 采样中该位点出现最多的氨基酸",
    "frequency": "该氨基酸在采样序列中的频率（0–1）",
    "sampling_frequency_threshold": "采样频率阈值（横轴）",
    "n_positions_passing": "最高频率 ≥ 阈值的位点数量",
    "substitution": "替换名（如 H29P）",
    "sampling_frequency": "该替换在 ProteinMPNN 采样中的频率（0–1）",
    "applicable_threshold_gamma": "该位点适用的频率阈值（卷曲区 γ = 0.5）",
    "secondary_structure": "二级结构：C = 无规卷曲，E = 折叠",
    "exceeds_threshold": "TRUE = 频率超过适用阈值，因此不会被过滤器剔除",
    "design_group": "设计批次的分组：A 复验 / B 新单点 / C 新组合 / D 控制变量 / E 异常配对与放宽口径 / new 不在候选表",
    "design_group_label_en": "同上，英文标签（作图用）",
    "on_target_GCG_over_offtarget_GCA_ratio": "+1 比 = c.388（GCG）编辑率 ÷ c.871（GCA）编辑率；只可同批比较",
    "ratio_defined": "FALSE = 分母（c.871）未检出，比值无定义，请勿当 0 处理或参与计算",
    "ROF_ratio_over_same_batch_parent": "ROF = 本构建体 +1 比 ÷ 同批亲本 +1 比；跨批唯一可比量",
    "is_reference_parent": "TRUE = 该行是同批亲本参照（PUF12），作画时作参考线而非数据点",
    "comparison": "该行在面板 B 中的角色",
    "position_132_residue": "132 位上的氨基酸（D 或 E）",
    "bar_order": "面板 B 中从左到右的柱序（1–4 为实柱，5 为幽灵柱）",
    "batch": "该测量来自哪一批（combinatorial batch / this batch）",
    "excluded_failed_well": "TRUE = 该孔判为测量失败予以剔除，其全部数值都不是有效读数，"
                            "仅用于标注「此孔失败」，不得参与任何计算或叙事",
    "batch": "该测量来自哪一批（single-mutant / combinatorial / supplementary / this batch）",
    "same_batch_parent_ratio": "该批次同批亲本的 +1 比（ROF 的分母）",
    "group_type": "single = 单点替换，combo = 组合，ref = 靶向模块参照组",
    "ACA_class_C295_fraction": "c.295（ACA 类，−1 层）编辑率；C295_not_detected = TRUE 表示低于 5% 检测线",
    "C295_not_detected": "TRUE = 该组两个重复均低于检测线，属有效读数但不得画成 0",
    "on_target_C388_fraction": "靶点 c.388 编辑率（0–1 小数）",
    "off_target_C871_fraction": "脱靶 c.871 编辑率（0–1 小数）",
    "note": "该行的补充说明",
}

lines = ["# 数据字典｜Dry Lab 绘图数据包", "",
         "每张图的数据表见 `data/`，列名自解释并含单位。所有数值与文章正文一致，重绘时请勿改动数值本身。",
         "", "布尔列取值为字符串 `TRUE` / `FALSE`；空白单元格表示「无定义或不可靠」，请勿补 0。", ""]
for m in WRITTEN:
    lines += [f"## `{m['file']}`", "", f"{m['note']}", "",
              "| 列名 | 说明 |", "|---|---|"]
    def desc(c):
        if c in COLDESC:
            return COLDESC[c]
        # ΔΔCP 宽表以构建体名为列
        if re.match(r"^[A-Z]\d+[A-Z]?([-+][A-Z]?\d+[A-Z]?)*$", str(c)) or "-" in str(c):
            return "该构建体的 ΔΔCP（相对野生型基线）"
        # 优先级矩阵以优先级标签为列
        if str(c) == "Required" or re.match(r"^P[012]\b", str(c)):
            return "该优先级下的候选数"
        return "—"

    lines += [f"| `{c}` | {desc(c)} |" for c in m["columns"]]
    lines += ["", f"SHA-256：`{sha(os.path.join(OUT, m['file']))}`", ""]
with open(os.path.join(OUT, "data_dictionary.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"\n写入 {OUT}")
print(f"  数据表 {len(WRITTEN)} 份 | 参考图 {len(FIGREF)} 张 | manifest.json | data_dictionary.md")
