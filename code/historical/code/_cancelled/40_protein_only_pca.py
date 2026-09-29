# -*- coding: utf-8 -*-
"""
阶段 40 —— 「纯蛋白模型」CP 的 PCA 与分离度检验（对照 38 的复合物模型）

背景：
  38 的 F1/F2 只取「蛋白–蛋白」子矩阵，但来自 蛋白+RNA 复合物模型。
  本脚本用 39 生成的「只给蛋白链」的 AF3 作业，检验同一问题：
  突变造成的 CP 偏离，是蛋白自身折叠的变化，还是 RNA 诱导的？

数据放置：
  把 39 生成的 6 个作业提交 AF3 server，下载结果全部丢到 new/protein_only/ 下，
  目录名随意——脚本读每个作业的 *_job_request.json，按蛋白序列自动归类。

与 38 的口径差异（有意为之，且更严格）：
  突变体为 10 个 seed（38 中只有 1 个），故除「整体质心 D」外，
  另给出「每个 seed 各自的 D」分布 → 可直接看 10 个独立 seed 是否一致。

产出：
  results/纯蛋白模型_分离度.csv
  results/figs/fig10_纯蛋白模型PCA.png
  results/figs/fig11_复合物_vs_纯蛋白.png
"""
import json, glob, os, sys, math, csv
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import af_utils as U

PROT = U.PROT_CHAIN
SRC = "new/protein_only"
N_MODEL_PER_SEED = 5

# 与 39 一致的突变定义
MUTS = {"WT": {}, "M132D": {132: "D"}, "M132E": {132: "E"},
        "K30H": {30: "H"}, "G27T-K30H-Q58M": {27: "T", 30: "H", 58: "M"}}
GROUPS = list(MUTS)
COLORS = {"WT": "0.72", "M132D": "#C0504D", "M132E": "#E8A33D",
          "K30H": "#3B6EA5", "G27T-K30H-Q58M": "#7E57C2"}
SHORT = {"M132D": "132D", "M132E": "132E", "K30H": "30H", "G27T-K30H-Q58M": "27T-30H-58M"}


def apply_muts(seq, muts):
    s = list(seq)
    for pos, aa in muts.items():
        s[pos - 1] = aa
    return "".join(s)


# ---------------------------------------------------------------------------
# 自动发现并归类
# ---------------------------------------------------------------------------
def discover(root):
    """返回 {group: {seed: [目录, ...]}}，按 job_request 的蛋白序列归类。"""
    if not os.path.isdir(root):
        return None
    dirs = sorted({os.path.dirname(p) for p in
                   glob.glob(os.path.join(root, "**", "*full_data*.json"), recursive=True)})
    if not dirs:
        return None
    # 用 39 的 WT 序列做基准
    ref = sorted(glob.glob("af3_submit/WT_GCG.json"))
    wt_seq = json.load(open(ref[0], encoding="utf-8"))[0]["sequences"][0]["proteinChain"]["sequence"]
    lookup = {apply_muts(wt_seq, m): g for g, m in MUTS.items()}

    out = {}
    unknown = []
    for d in dirs:
        jr = glob.glob(os.path.join(d, "*job_request.json"))
        if not jr:
            unknown.append((d, "无 job_request")); continue
        j = json.load(open(jr[0], encoding="utf-8"))[0]
        chains = [list(s.keys())[0] for s in j["sequences"]]
        if chains != ["proteinChain"]:
            unknown.append((d, f"非纯蛋白链 {chains}")); continue
        seq = j["sequences"][0]["proteinChain"]["sequence"]
        g = lookup.get(seq)
        if g is None:
            unknown.append((d, "序列不匹配任何构建体")); continue
        seed = str(j["modelSeeds"][0])
        out.setdefault(g, {}).setdefault(seed, []).append(d)
    return out, unknown


print("=" * 106)
print("阶段 40 —— 纯蛋白模型 CP 的 PCA 与分离度检验")
print("=" * 106)

res = discover(SRC)
if res is None:
    print(f"\n未在 {SRC}/ 下找到纯蛋白 AF3 结果。")
    print("请先提交 af3_submit_protein_only/ 中的 6 个作业，并把下载结果放到该目录后重跑。")
    sys.exit(0)
found, unknown = res
if unknown:
    print(f"\n⚠ {len(unknown)} 个目录未能归类（已跳过）：")
    for d, why in unknown[:10]:
        print(f"   {d}  ← {why}")
print(f"\n归类结果：")
for g in GROUPS:
    n_seed = len(found.get(g, {}))
    n_dir = sum(len(v) for v in found.get(g, {}).values())
    print(f"  {g:<18} seed 数 = {n_seed:<3} 目录数 = {n_dir}")


# ---------------------------------------------------------------------------
# 读 CP
# ---------------------------------------------------------------------------
def seed_map(d):
    mats = []
    for f in sorted(glob.glob(os.path.join(d, "*full_data*.json"))):
        j = json.load(open(f, encoding="utf-8"))
        cids = j["token_chain_ids"]
        cpm = np.asarray(j["contact_probs"], dtype=np.float64)
        idx = np.array([i for i in range(len(cids)) if cids[i] == PROT])
        sub = cpm[np.ix_(idx, idx)]
        mats.append(np.maximum(sub, sub.T))
    if not mats:
        return None
    return np.mean(mats, axis=0)


def seed_centroid(dirs):
    ms = [seed_map(d) for d in dirs]
    ms = [m for m in ms if m is not None]
    return np.mean(ms, axis=0) if ms else None


SEED_MAPS = {}
for g in GROUPS:
    for s, dirs in found.get(g, {}).items():
        m = seed_centroid(dirs)
        if m is not None:
            SEED_MAPS.setdefault(g, {})[s] = m
if "WT" not in SEED_MAPS or len(SEED_MAPS["WT"]) < 3:
    print("\nWT 的 seed 数不足（<3），无法构造零假设。")
    sys.exit(0)

N_PROT = next(iter(SEED_MAPS["WT"].values())).shape[0]
iu = np.triu_indices(N_PROT, k=1)
lr = np.array([(i, j) for i in range(N_PROT) for j in range(i + 5, N_PROT)])
FSETS = {"G1_纯蛋白CP全": iu, "G2_纯蛋白CP长程": (lr[:, 0], lr[:, 1])}


def run_pca(fs):
    """用 seed 质心做 PCA（单位 = seed，与 38 的零假设同尺度）。"""
    rows, labels = [], []
    for g in GROUPS:
        for s in sorted(SEED_MAPS.get(g, {})):
            M = SEED_MAPS[g][s]
            rows.append(M[FSETS[fs]]); labels.append(g)
    X = np.array(rows); labels = np.array(labels)
    Xc = X - X.mean(0)
    U_, S_, _ = np.linalg.svd(Xc, full_matrices=False)
    scores = U_ * S_
    ve = S_ ** 2 / (S_ ** 2).sum()

    wt = scores[labels == "WT"]
    cwt, sd = wt.mean(0), wt.std(0, ddof=1)
    sd = np.maximum(sd, 0.01 * max(sd.max(), 1e-12))
    K = min(10, wt.shape[0] - 1, scores.shape[1])
    tiny = 1e-12
    null = []
    for i in range(len(wt)):
        oth = np.delete(wt[:, :K], i, axis=0)
        c, s2 = oth.mean(0), oth.std(0, ddof=1)
        s2 = np.maximum(s2, 0.01 * max(s2.max(), tiny))
        null.append(math.sqrt(np.mean(((wt[i, :K] - c) / s2) ** 2)))
    null = np.array(null)

    out = {}
    for g in GROUPS[1:]:
        vs = scores[labels == g][:, :K]
        c = vs.mean(0)
        D = math.sqrt(np.mean(((c - cwt[:K]) / sd[:K]) ** 2))
        p = (1 + int((null >= D).sum())) / (1 + len(null))
        # 逐 seed 的 D（独立重复性）
        per = [math.sqrt(np.mean(((v - cwt[:K]) / sd[:K]) ** 2)) for v in vs]
        out[g] = dict(D=D, p=p, per_seed=per)
    return dict(scores=scores, ve=ve, labels=labels, null=null, rows=out, K=K)


RES = {fs: run_pca(fs) for fs in FSETS}

print("\n" + "=" * 106)
for fs in FSETS:
    R = RES[fs]
    print(f"\n【{fs}】维度 {len(FSETS[fs][0])}　"
          f"PC1–PC4 方差解释 = {' '.join(f'{v:.1%}' for v in R['ve'][:4])}")
    print(f"  WT seed 零假设（n={len(R['null'])}）：中位 {np.median(R['null']):.3f}，"
          f"95 分位 {np.percentile(R['null'], 95):.3f}")
    print(f"  {'组':<16}{'整体质心D':>11}{'经验p':>9}{'逐 seed D（中位）':>18}{'逐 seed 范围':>20}")
    for g in GROUPS[1:]:
        r = R["rows"][g]
        lo, hi = min(r["per_seed"]), max(r["per_seed"])
        rng = f"{lo:.2f} – {hi:.2f}"
        print(f"  {g:<16}{r['D']:>11.3f}{r['p']:>9.3f}"
              f"{float(np.median(r['per_seed'])):>18.3f}{rng:>20}")

# ---------------------------------------------------------------------------
# 与 38（复合物模型）并排
# ---------------------------------------------------------------------------
comp = {}
p38 = "results/CP_PCA_分离度.csv"
if os.path.exists(p38):
    for r in csv.DictReader(open(p38, encoding="utf-8-sig")):
        if r["feature_set"] == "F1_内部CP全":
            comp[r["group"]] = dict(D=float(r["mahalanobis_D"]), p=float(r["empirical_p"]))

print("\n" + "=" * 106)
print("并排对比：复合物模型（38 的 F1）vs 纯蛋白模型（本脚本 G1）")
print("=" * 106)
print(f"{'组':<16}{'复合物 D':>11}{'p':>8}{'纯蛋白 D':>11}{'p':>8}   差异解读")
for g in GROUPS[1:]:
    c = comp.get(g); v = RES["G1_纯蛋白CP全"]["rows"][g]
    if c is None:
        print(f"{g:<16}{'—':>11}{'—':>8}{v['D']:>11.3f}{v['p']:>8.3f}")
        continue
    if c["p"] <= 0.05 and v["p"] > 0.05:
        note = "复合物中显著、纯蛋白中消失 → 偏离依赖 RNA"
    elif c["p"] > 0.05 and v["p"] <= 0.05:
        note = "纯蛋白中出现、复合物中不显著 → 蛋白自身折叠改变"
    elif c["p"] <= 0.05 and v["p"] <= 0.05:
        note = "两者皆显著 → 蛋白自身即被扰动"
    else:
        note = "两者皆不显著 → 无法与 WT 噪声区分"
    print(f"{g:<16}{c['D']:>11.3f}{c['p']:>8.3f}{v['D']:>11.3f}{v['p']:>8.3f}   {note}")

with open("results/纯蛋白模型_分离度.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["feature_set", "group", "D_centroid", "empirical_p",
                "per_seed_D_median", "per_seed_D_min", "per_seed_D_max", "n_seed",
                "complex_model_D", "complex_model_p",
                "PC1_var", "PC2_var", "PC3_var"])
    for fs in FSETS:
        R = RES[fs]
        for g in GROUPS[1:]:
            r = R["rows"][g]; c = comp.get(g, {})
            w.writerow([fs, g, round(r["D"], 4), round(r["p"], 4),
                        round(float(np.median(r["per_seed"])), 4),
                        round(min(r["per_seed"]), 4), round(max(r["per_seed"]), 4),
                        len(r["per_seed"]),
                        round(c.get("D", float("nan")), 4) if c else "",
                        round(c.get("p", float("nan")), 4) if c else ""] +
                       [round(v, 5) for v in R["ve"][:3]])
print("\n写入 results/纯蛋白模型_分离度.csv")

# ---------------------------------------------------------------------------
# 图
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(1, len(FSETS) + 1, figsize=(6.0 * (len(FSETS) + 1), 5.6))
fig.suptitle("图10　纯蛋白模型（AF3 输入不含 RNA）的 CP 特征 PCA 与分离度",
             fontsize=14, fontweight="bold")
for i, fs in enumerate(FSETS):
    R = RES[fs]; ax = axes[i]
    for g in GROUPS:
        s = R["scores"][R["labels"] == g]
        if g == "WT":
            ax.scatter(s[:, 0], s[:, 1], s=42, c=COLORS[g], alpha=0.8,
                       edgecolors="none", label="WT（各 seed）")
        else:
            ax.scatter(s[:, 0], s[:, 1], s=95, c=COLORS[g], edgecolors="black",
                       linewidths=0.7, label=SHORT.get(g, g), zorder=3)
            ax.scatter(*s[:, :2].mean(0), marker="X", s=180, c=COLORS[g],
                       edgecolors="black", linewidths=1.0, zorder=4)
    ax.set_xlabel(f"PC1 ({R['ve'][0]:.1%})", fontsize=10)
    ax.set_ylabel(f"PC2 ({R['ve'][1]:.1%})", fontsize=10)
    ax.set_title(fs, fontsize=11.5, fontweight="bold")
    ax.legend(fontsize=8.5); ax.grid(alpha=0.25)

ax = axes[-1]
xs = np.arange(len(GROUPS) - 1); w = 0.36
cv = [comp.get(g, {}).get("D", np.nan) for g in GROUPS[1:]]
pv = [RES["G1_纯蛋白CP全"]["rows"][g]["D"] for g in GROUPS[1:]]
ax.bar(xs - w / 2, cv, w, label="复合物模型（含 RNA）", color="#8FB8DE", edgecolor="white")
ax.bar(xs + w / 2, pv, w, label="纯蛋白模型（无 RNA）", color="#C0504D", edgecolor="white")
ax.axhline(np.percentile(RES["G1_纯蛋白CP全"]["null"], 95), color="0.35", ls="--", lw=1.2,
           label="纯蛋白 WT seed 95 分位")
ax.set_xticks(xs); ax.set_xticklabels([SHORT.get(g, g) for g in GROUPS[1:]],
                                      rotation=25, ha="right", fontsize=9.5)
ax.set_ylabel("到 WT 质心的马氏距离 D", fontsize=10)
ax.set_title("分离度并排对比", fontsize=11.5, fontweight="bold")
ax.legend(fontsize=8.5); ax.grid(axis="y", alpha=0.25)
plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.savefig("results/figs/fig10_纯蛋白模型PCA.png", dpi=155, bbox_inches="tight")
print("写入 results/figs/fig10_纯蛋白模型PCA.png")
