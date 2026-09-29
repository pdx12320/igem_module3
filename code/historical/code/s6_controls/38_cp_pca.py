# -*- coding: utf-8 -*-
"""
阶段 38 —— 以 CP 为特征的 PCA 聚类分析
问题：蛋白内部 CP、蛋白–靶C CP、两者叠加，能否把 WT / 132D / 132E / 30H / 27T-30H-58M 分成不同 cluster？

特征集（4 套，均单独做 PCA）：
  F1 内部CP(全)      蛋白链内 199×199 上三角，i<j                 → 19 701 维
  F2 内部CP(长程)    仅 |i−j|≥5（剔除序列近邻的平凡接触）          → 18 811 维
  F3 靶C-CP          蛋白各残基 ↔ 靶 C(RNA resi 4) 的 CP          →    199 维
  F4 叠加            F1 + F3                                     → 19 900 维
  F5 叠加(分块标准化) F1/F3 各自归一化后拼接（避免高维块压过低维块）

样本：WT 100 个 model（20 seed × 5）+ 4 个突变体各 5 个 model = 120

「能否分开」的判定标准（关键）：
  变异体只有 1 个 seed，其 5 个 model 高度相关，直接看散点会高估分离度。
  故以 WT 的 20 个 seed 质心（每个 = 5 model 均值，与突变体同尺度）构造零假设：
      D = 马氏距离（由 WT seed 质心的协方差白化），做留一法
  突变体的 D 与这 20 个 seed 的 D 分布比较 → 经验 p 值。
  全局检验用 Fisher 合并 4 个 D 检验的 p 值。
  注意：朴素的「打乱标签 + pseudo-F」置换检验在此无效——突变体 5 个 model 来自同一 seed、
  彼此高度相关，任何 5 个相关样本的组合都会比随机标签更「聚」，故必然显著。

产出：
  results/CP_PCA_分离度.csv
  results/figs/fig8_CP_PCA散点.png
  results/figs/fig9_CP_PCA分离度.png
"""
import json, glob, os, sys, math, csv
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import af_utils as U

PROT, RNA, TARGET_C = U.PROT_CHAIN, U.RNA_CHAIN, 4
WT_DIR, MUT_ROOT = "GUGCGCG_20", "new/mut"
N_MODEL_PER_SEED = 5
VARIANTS = [("m132d", "132D"), ("m132e", "132E"),
            ("k30h", "30H"), ("g27tk30hq58m", "27T-30H-58M")]
GROUPS = ["WT", "WT-GCA", "132D", "132E", "30H", "27T-30H-58M"]
COLORS = {"WT": "0.72", "WT-GCA": "#9C27B0", "132D": "#C0504D", "132E": "#E8A33D",
          "30H": "#3B6EA5", "27T-30H-58M": "#7E57C2"}


# ---------------------------------------------------------------------------
# 读取
# ---------------------------------------------------------------------------
def load_dir(d):
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*full_data*.json"))):
        j = json.load(open(f, encoding="utf-8"))
        cids, rids = j["token_chain_ids"], j["token_res_ids"]
        cpm = np.asarray(j["contact_probs"], dtype=np.float64)
        idx = np.array([i for i in range(len(cids)) if cids[i] == PROT])
        t = next(i for i in range(len(cids)) if cids[i] == RNA and rids[i] == TARGET_C)
        sub = cpm[np.ix_(idx, idx)]
        M = np.maximum(sub, sub.T)
        v = np.maximum(cpm[idx, t], cpm[t, idx])
        out.append((M, v))
    return out


print("读取数据 …", flush=True)
wt_seeds = sorted(x for x in glob.glob(os.path.join(WT_DIR, "*")) if os.path.isdir(x))
wt_data = []
for s in wt_seeds:
    md = load_dir(s)
    if md:
        wt_data.append(md)
N_SEED = len(wt_data)
wt_models = [m for sd in wt_data for m in sd]

var_data = {}
for key, name in VARIANTS:
    d = os.path.join(MUT_ROOT, f"{key}_gcg")
    var_data[name] = load_dir(d)
    print(f"  {name}: {len(var_data[name])} model", flush=True)
print(f"  WT: {N_SEED} seed × {N_MODEL_PER_SEED} model = {len(wt_models)} model")

n_prot = wt_models[0][0].shape[0]
iu = np.triu_indices(n_prot, k=1)
lr = np.array([(i, j) for i in range(n_prot) for j in range(i + 5, n_prot)])

def feats(md):
    """把一组 (M, v) 转成 4 套特征向量。"""
    intra = np.array([m[iu] for m, _ in md])
    intralr = np.array([m[lr[:, 0], lr[:, 1]] for m, _ in md])
    protC = np.array([v for _, v in md])
    return {"F1_内部CP全": intra,
            "F2_内部CP长程": intralr,
            "F3_靶C_CP": protC,
            "F4_叠加": np.hstack([intra, protC])}

WT = feats(wt_models)
VAR = {name: feats(var_data[name]) for _, name in VARIANTS}
FSETS = ["F1_内部CP全", "F2_内部CP长程", "F3_靶C_CP", "F4_叠加", "F5_叠加(分块标准化)"]

# 第二组 WT：同一蛋白、换用 GCA 底物（20 seed × 5 model）。
# 作用 = 只换底物、不改蛋白时的 CP 自然偏移 → 判断突变体分离是否有意义的标尺。
wt2_models = []
for _s in sorted(x for x in glob.glob(os.path.join("GUGCACG_20", "*")) if os.path.isdir(x)):
    _md = load_dir(_s)
    if _md:
        wt2_models.extend(_md)
WTG = feats(wt2_models)


# ---------------------------------------------------------------------------
# PCA
# ---------------------------------------------------------------------------
def pca(X):
    Xc = X - X.mean(axis=0)
    U_, S_, _ = np.linalg.svd(Xc, full_matrices=False)
    scores = U_ * S_
    ve = S_ ** 2 / (S_ ** 2).sum()
    return scores, ve


def build_X(fs):
    """F5 为分块标准化叠加：两块的总体方差各归一，避免 19701 维压过 199 维。"""
    if fs == "F5_叠加(分块标准化)":
        A = np.vstack([WT["F1_内部CP全"], WTG["F1_内部CP全"]] +
                      [VAR[n]["F1_内部CP全"] for _, n in VARIANTS])
        B = np.vstack([WT["F3_靶C_CP"], WTG["F3_靶C_CP"]] +
                      [VAR[n]["F3_靶C_CP"] for _, n in VARIANTS])
        A = A / A.std(); B = B / B.std()
        return np.hstack([A, B])
    return np.vstack([WT[fs], WTG[fs]] + [VAR[n][fs] for _, n in VARIANTS])


def analyse(fs):
    X = build_X(fs)
    n_wt = len(WT["F1_内部CP全"])
    n_wtg = len(WTG["F1_内部CP全"])
    labels = np.array(["WT"] * n_wt + ["WT-GCA"] * n_wtg +
                      [n for _, n in VARIANTS for _ in range(len(VAR[n]["F1_内部CP全"]))])
    scores, ve = pca(X)          # 仅用于散点图

    # --- D_M：在「仅由 WT(GCG) seed 定义」的基底上做白化马氏距离 ---
    # 不能用含被检组的合并 PCA 基底：那样 D 会随纳入了哪些组而变。
    # 实测：加入 WT-GCA 后，27T-30H-58M 的合并-PCA D 从 9.38 掉到 2.82（基底污染）；
    # 而 WT-only 基底的 D_M 对所有既有构建体数值稳定。
    wt_mask = labels == "WT"
    W = X[wt_mask]
    n_seed_eff = len(W) // N_MODEL_PER_SEED
    Ws = W[: n_seed_eff * N_MODEL_PER_SEED].reshape(
        -1, N_MODEL_PER_SEED, X.shape[1]).mean(1)
    w_mean = Ws.mean(0)
    _, Sw, Vt = np.linalg.svd(Ws - w_mean, full_matrices=False)
    K = min(10, Ws.shape[0] - 2)
    Vk = Vt[:K].T
    sW = (Ws - w_mean) @ Vk
    cwt, sd_all = sW.mean(0), np.maximum(sW.std(0, ddof=1), 1e-12)
    Dm = lambda s: math.sqrt(float(np.mean(((s - cwt) / sd_all) ** 2)))

    null = []
    for i in range(Ws.shape[0]):
        oth = np.delete(sW, i, axis=0)
        c, s2 = oth.mean(0), np.maximum(oth.std(0, ddof=1), 1e-12)
        null.append(math.sqrt(float(np.mean(((sW[i] - c) / s2) ** 2))))
    null = np.array(null)

    rows = []
    for name in GROUPS[1:]:
        D = Dm((X[labels == name].mean(0) - w_mean) @ Vk)
        p = (1 + int((null >= D).sum())) / (1 + len(null))
        rows.append(dict(feature=fs, group=name, D=D, p=p,
                         null_med=float(np.median(null)),
                         null_p95=float(np.percentile(null, 95))))

    # --- 全局检验：Fisher 合并 4 个 D 检验 ---
    # 注：朴素的「打乱标签 + pseudo-F」置换检验在此无效——突变体 5 个 model 来自同一
    #     seed、彼此高度相关，任何 5 个相关样本的组合都会比随机标签更「聚」，故必然显著。
    ps = [max(r["p"], 1e-6) for r in rows]
    chi2 = -2 * sum(math.log(p) for p in ps)
    from math import exp
    def chi2_sf(x, k):   # 生存函数（k=8 偶自由度，级数展开）
        t = x / 2.0; s = 0.0; term = 1.0
        for i in range(0, k // 2):
            if i > 0:
                term *= t / i
            s += term
        return min(1.0, exp(-t) * s)
    pF = chi2_sf(chi2, 2 * len(ps))

    return dict(fs=fs, scores=scores, ve=ve, labels=labels, rows=rows,
                chi2=chi2, pF=pF, seed_sk=sW, K=K)


RES = {fs: analyse(fs) for fs in FSETS}

# ---------------------------------------------------------------------------
# 控制台
# ---------------------------------------------------------------------------
print("\n" + "=" * 104)
print("PCA 结果：5 套特征 × 5 组")
print("=" * 104)
for fs in FSETS:
    R = RES[fs]
    print(f"\n【{fs}】维度 {build_X(fs).shape[1]}　"
          f"PC1–PC4 方差解释 = {' '.join(f'{v:.1%}' for v in R['ve'][:4])}")
    print(f"  Fisher 合并检验 chi2 = {R['chi2']:.2f} (df=8)，p = {R['pF']:.4f} "
          f"({'整体可区分' if R['pF'] < 0.05 else '整体不可区分'}）")
    print(f"  {'组':<14}{'马氏距离D':>10}{'WT seed 零假设中位':>18}{'95分位':>9}{'经验p':>9}  判定")
    for r in R["rows"]:
        verdict = "✓ 超出噪声" if r["p"] <= 0.05 else "✗ 落在 WT 噪声内"
        print(f"  {r['group']:<14}{r['D']:>10.3f}{r['null_med']:>18.3f}"
              f"{r['null_p95']:>9.3f}{r['p']:>9.3f}  {verdict}")

print("\n" + "=" * 104)
print("诊断：各组「整体尺度」是否不同（PCA 的 PC1 可能只是整体接触强度）")
print("=" * 104)
def _feat(g, key):
    """按组名取特征（WT 与第二组 WT-GCA 不在 VAR 里）。"""
    if g == "WT":
        return WT[key]
    if g == "WT-GCA":
        return WTG[key]
    return VAR[g][key]


INTRA_SUM = np.concatenate([_feat(g, "F1_内部CP全").sum(1) for g in GROUPS])
GF = np.concatenate([np.array([g] * len(_feat(g, "F1_内部CP全"))) for g in GROUPS])
print(f"{'组':<14}{'内部CP均值':>12}{'内部CP总和':>12}{'靶C-CP总和':>12}")
for g in GROUPS:
    A = _feat(g, "F1_内部CP全")
    B = _feat(g, "F3_靶C_CP")
    print(f"{g:<14}{A.mean():>12.5f}{A.sum(1).mean():>12.2f}{B.sum(1).mean():>12.2f}")
print()
for fs in FSETS:
    R = RES[fs]
    r = float(np.corrcoef(R["scores"][:, 0], INTRA_SUM)[0, 1])
    print(f"  {fs:<24} PC1 与「内部CP总和」相关 r = {r:+.3f}")

with open("results/CP_PCA_分离度.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["feature_set", "group", "mahalanobis_D", "null_median", "null_p95",
                "empirical_p", "fisher_chi2", "fisher_p", "PC1_var", "PC2_var", "PC3_var"])
    for fs in FSETS:
        R = RES[fs]
        for r in R["rows"]:
            w.writerow([fs, r["group"], round(r["D"], 4), round(r["null_med"], 4),
                        round(r["null_p95"], 4), round(r["p"], 4), round(R["chi2"], 3),
                        round(R["pF"], 4)] + [round(v, 5) for v in R["ve"][:3]])

# ---------------------------------------------------------------------------
# 图 8：散点
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

PAIRS = [(0, 1), (1, 2), (2, 3)]
fig, axes = plt.subplots(len(FSETS), 3, figsize=(16.5, 4.0 * len(FSETS)))
fig.suptitle("图8　以 CP 为特征的 PCA：WT / 132D / 132E / 30H / 27T-30H-58M 能否分开？\n"
             "灰点 = WT（GCG 底物，100 model，零假设基准）；紫点 = 第二组 WT（GCA 底物，100 model，蛋白完全未变）；"
             "彩色点 = 各突变体的 5 个 model；虚线椭圆 = WT 的 1 SD",
             fontsize=13.5, fontweight="bold", y=0.995)

for r, fs in enumerate(FSETS):
    R = RES[fs]
    for c, (a, b) in enumerate(PAIRS):
        ax = axes[r][c]
        for g in GROUPS:
            s = R["scores"][R["labels"] == g]
            if g in ("WT", "WT-GCA"):
                ax.scatter(s[:, a], s[:, b], s=13, c=COLORS[g],
                           alpha=0.55 if g == "WT" else 0.45,
                           edgecolors="none", zorder=1,
                           label=None if g == "WT" else "WT（GCA 底物）")
                ax.scatter(*s[:, [a, b]].mean(0), marker="X", s=200,
                           c=COLORS[g], edgecolors="black", linewidths=1.1, zorder=4)
            else:
                ax.scatter(s[:, a], s[:, b], s=62, c=COLORS[g], edgecolors="black",
                           linewidths=0.6, zorder=3, label=g)
                mu = s[:, [a, b]].mean(0)
                ax.scatter(*mu, marker="X", s=170, c=COLORS[g],
                           edgecolors="black", linewidths=1.0, zorder=4)
        # WT 1SD 椭圆
        w = R["scores"][R["labels"] == "WT"][:, [a, b]]
        mu = w.mean(0); cov = np.cov(w.T)
        th = np.linspace(0, 2 * np.pi, 120)
        e = np.array([np.cos(th), np.sin(th)])
        L = np.linalg.cholesky(cov + 1e-12 * np.eye(2))
        ax.plot(*(mu[:, None] + L @ e), color="0.35", ls="--", lw=1.1, zorder=2)
        ax.set_xlabel(f"PC{a+1} ({R['ve'][a]:.1%})", fontsize=10)
        ax.set_ylabel(f"PC{b+1} ({R['ve'][b]:.1%})", fontsize=10)
        ax.grid(alpha=0.22)
        if r == 0 and c == 0:
            ax.legend(fontsize=8.5, loc="best", framealpha=0.9)
        if c == 0:
            ax.set_title(f"{fs}\nFisher 合并 p = {R['pF']:.4f}"
                         + ("　→ 整体可区分" if R["pF"] < 0.05 else "　→ 不可区分"),
                         fontsize=11, fontweight="bold")
plt.tight_layout(rect=[0, 0, 1, 0.945])
plt.savefig("results/figs/fig8_CP_PCA散点.png", dpi=155, bbox_inches="tight")
print("\n写入 results/figs/fig8_CP_PCA散点.png")

# ---------------------------------------------------------------------------
# 图 9：分离度量化
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, len(FSETS), figsize=(5.0 * len(FSETS), 5.2))
fig.suptitle("图9　分离度量化：突变体到 WT 质心的马氏距离 vs WT 自身 20 个 seed 的零假设分布",
             fontsize=13.5, fontweight="bold")
for i, fs in enumerate(FSETS):
    ax = axes[i]
    R = RES[fs]
    null = [r["null_med"] for r in R["rows"]]
    # 重算零假设分布用于绘制
    seed_sk = R["seed_sk"]
    tiny = 1e-12
    nd = []
    for k in range(N_SEED):
        oth = np.delete(seed_sk, k, axis=0)
        c, sd = oth.mean(0), oth.std(0, ddof=1)
        sd = np.maximum(sd, 0.01 * max(sd.max(), tiny))
        nd.append(math.sqrt(np.mean(((seed_sk[k] - c) / sd) ** 2)))
    ax.hist(nd, bins=12, color="0.8", edgecolor="0.5",
            label=f"WT seed 零假设 (n={N_SEED})")
    ax.axvline(np.percentile(nd, 95), color="0.35", ls="--", lw=1.2,
               label=f"95 分位 = {np.percentile(nd,95):.2f}")
    for j, rr in enumerate(R["rows"]):
        ax.bar(j, rr["D"], width=0.55, color=COLORS[rr["group"]],
               edgecolor="black", linewidth=0.5, zorder=3)
        ax.text(j, rr["D"] + 0.12, f"{rr['D']:.2f}\np={rr['p']:.3f}",
                ha="center", fontsize=8.5, zorder=4)
    ax.set_xticks(range(len(R["rows"])))
    ax.set_xticklabels([r["group"] for r in R["rows"]], rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("到 WT 质心的马氏距离 D", fontsize=10)
    ax.set_title(f"{fs}\nFisher 合并 p = {R['pF']:.4f}", fontsize=11, fontweight="bold")
    ax.legend(fontsize=8.5)
    ax.grid(axis="y", alpha=0.25)
plt.tight_layout(rect=[0, 0, 1, 0.90])
plt.savefig("results/figs/fig9_CP_PCA分离度.png", dpi=155, bbox_inches="tight")
print("写入 results/figs/fig9_CP_PCA分离度.png")
print("写入 results/CP_PCA_分离度.csv")
