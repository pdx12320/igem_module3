# -*- coding: utf-8 -*-
"""
阶段 47 —— fig8 中每个主成分（PC1–PC4）到底在编码什么？

fig8 是 5 行（特征集 F1–F5）× 3 列（PC1–PC2 / PC2–PC3 / PC3–PC4），
即每套特征用 4 个主成分展示。本脚本量化每个 PC 的含义：

  ① 方差解释率
  ② Cohen's d（WT-GCG vs WT-GCA）= 该 PC 是否是「RNA 底物轴」
  ③ Cohen's d（WT-GCG vs 各突变体）= 该 PC 是否是「突变轴」
  ④ 与「整体接触强度」的相关（判断是否只是全局尺度）
  ⑤ 载荷最大的残基对 / 残基（给出结构解读）

产出：results/PC含义.csv
"""
import json, glob, os, sys, math, csv
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import af_utils as U

PROT, RNA, TARGET_C = U.PROT_CHAIN, U.RNA_CHAIN, 4
N_PER_SEED = 5
WT_DIR, WT2_DIR, MUT_ROOT = "GUGCGCG_20", "GUGCACG_20", "new/mut"
VARIANTS = [("m132d", "132D"), ("m132e", "132E"),
            ("k30h", "30H"), ("g27tk30hq58m", "27T-30H-58M")]
POCKET = list(range(25, 33)) + list(range(57, 61)) + list(range(70, 73)) + \
         list(range(99, 106)) + list(range(129, 134))


def load_dir(d):
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*full_data*.json"))):
        j = json.load(open(f, encoding="utf-8"))
        cids, rids = j["token_chain_ids"], j["token_res_ids"]
        cpm = np.asarray(j["contact_probs"], dtype=np.float64)
        idx = np.array([i for i in range(len(cids)) if cids[i] == PROT])
        t = next(i for i in range(len(cids)) if cids[i] == RNA and rids[i] == TARGET_C)
        sub = cpm[np.ix_(idx, idx)]
        out.append((np.maximum(sub, sub.T), np.maximum(cpm[idx, t], cpm[t, idx])))
    return out


print("读取数据 …", flush=True)
W1 = [m for s in sorted(x for x in glob.glob(WT_DIR + "/*") if os.path.isdir(x))
      for m in load_dir(s)]
W2 = [m for s in sorted(x for x in glob.glob(WT2_DIR + "/*") if os.path.isdir(x))
      for m in load_dir(s)]
VA = {n: [m for m in load_dir(os.path.join(MUT_ROOT, f"{k}_gcg"))] for k, n in VARIANTS}
print(f"  WT-GCG {len(W1)}，WT-GCA {len(W2)}，突变体 " +
      "，".join(f"{n} {len(v)}" for n, v in VA.items()))

n_prot = 199
iu = np.triu_indices(n_prot, k=1)
lr_mask = np.array([abs(i - j) >= 5 for i, j in zip(*iu)])
pk_mask = np.array([(i + 1) in POCKET and (j + 1) in POCKET for i, j in zip(*iu)])


def feats(md):
    intra = np.array([m[iu] for m, _ in md])
    protC = np.array([v for _, v in md])
    return {"F1_内部CP全": intra,
            "F2_内部CP长程": np.array([m[iu][lr_mask] for m, _ in md]),
            "F3_靶C_CP": protC,
            "F4_叠加": np.hstack([intra, protC])}


FSETS = ["F1_内部CP全", "F2_内部CP长程", "F3_靶C_CP", "F4_叠加"]
F1 = feats(W1); F2 = feats(W2); FV = {n: feats(v) for n, v in VA.items()}

# 每个特征集的「索引→含义」映射（用于读载荷）
IDXMAP = {
    "F1_内部CP全": [("pair", iu[0][k], iu[1][k]) for k in range(len(iu[0]))],
    "F2_内部CP长程": [("pair", iu[0][k], iu[1][k]) for k in range(len(iu[0])) if lr_mask[k]],
    "F3_靶C_CP": [("resi", r + 1, None) for r in range(n_prot)],
    "F4_叠加": ([("pair", iu[0][k], iu[1][k]) for k in range(len(iu[0]))] +
                [("resi", r + 1, None) for r in range(n_prot)]),
}


def cohen_d(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    na, nb = len(a), len(b)
    s = math.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return (a.mean() - b.mean()) / s if s > 0 else float("nan")


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    x, y = x - x.mean(), y - y.mean()
    d = math.sqrt((x ** 2).sum() * (y ** 2).sum())
    return float((x * y).sum() / d) if d > 0 else float("nan")


print("\n" + "=" * 112)
print("fig8 各主成分的含义")
print("=" * 112)
rows = []
for fs in FSETS:
    X = np.vstack([F1[fs], F2[fs]] + [FV[n][fs] for _, n in VARIANTS])
    labels = np.array(["WT-GCG"] * len(F1[fs]) + ["WT-GCA"] * len(F2[fs]) +
                      [n for _, n in VARIANTS for _ in range(len(FV[n][fs]))])
    Xc = X - X.mean(0)
    U_, S_, Vt = np.linalg.svd(Xc, full_matrices=False)
    SC = U_ * S_
    VE = S_ ** 2 / (S_ ** 2).sum()

    # 与「整体接触强度」的相关：一律用蛋白内部 CP 总和（对 F3 也有意义，衡量整体折叠状态）
    intr_sum = np.concatenate([F1["F1_内部CP全"].sum(1)] * 1) if False else None
    isum = np.concatenate([F1["F1_内部CP全"].sum(1), F2["F1_内部CP全"].sum(1)] +
                          [FV[n]["F1_内部CP全"].sum(1) for _, n in VARIANTS])

    print(f"\n【{fs}】方差解释 PC1–PC4 = " +
          " / ".join(f"{v:.1%}" for v in VE[:4]))
    # 尺度统一：以 WT-GCG 的 20 个 seed 质心在该 PC 上的 SD 为单位（z 值）。
    # 不能用 Cohen's d：突变体只有 1 个 seed，组内 SD≈0，d 会被严重夸大。
    n1, n2 = len(F1[fs]), len(F2[fs])
    wt_seed = SC[:n1].reshape(-1, N_PER_SEED, SC.shape[1]).mean(1)
    gca_seed = SC[n1:n1 + n2].reshape(-1, N_PER_SEED, SC.shape[1]).mean(1)
    sd_pc = np.maximum(wt_seed.std(0, ddof=1), 1e-12)
    cwt = wt_seed.mean(0)

    print(f"  {'PC':<5}{'方差':>7}{'z(GCG→GCA)':>13}{'z(最远突变体)':>15}"
          f"{'r(接触强度)':>13}   载荷最大者")
    for k in range(4):
        s = SC[:, k]
        z_rna = float((gca_seed[:, k].mean() - cwt[k]) / sd_pc[k])
        z_mut, z_who = 0.0, ""
        for _, n in VARIANTS:
            v = abs(float((SC[labels == n][:, k].mean() - cwt[k]) / sd_pc[k]))
            if v > z_mut: z_mut, z_who = v, n
        d_rna, d_mut = z_rna, z_mut
        r_int = pearson(s, isum)
        load = Vt[k]
        top = np.argsort(-np.abs(load))[:3]
        desc = []
        for t in top:
            kind, a, b = IDXMAP[fs][t]
            desc.append(f"{a}-{b}" if kind == "pair" else f"残基{a}")
        print(f"  PC{k+1:<3}{VE[k]:>7.1%}{d_rna:>13.2f}{d_mut:>15.2f}{r_int:>13.2f}"
              f"   {', '.join(desc)}  ({z_who})")
        rows.append(dict(feature_set=fs, PC=f"PC{k+1}", var_explained=round(float(VE[k]), 5),
                         z_WTGCG_to_WTGCA=round(d_rna, 3),
                         z_farthest_mutant=round(d_mut, 3),
                         farthest_mutant=z_who,
                         r_with_contact_strength=round(r_int, 3),
                         top_loadings=", ".join(desc)))

# ---- 补充：各组在 PC1/PC2 上的位置（均值 ± SD）----
print("\n" + "=" * 112)
print("各组在前 2 个主成分上的位置（均值 ± SD）—— 看 PC1/PC2 各自把谁分开")
print("=" * 112)
for fs in ["F1_内部CP全", "F3_靶C_CP"]:
    X = np.vstack([F1[fs], F2[fs]] + [FV[n][fs] for _, n in VARIANTS])
    labels = np.array(["WT-GCG"] * len(F1[fs]) + ["WT-GCA"] * len(F2[fs]) +
                      [n for _, n in VARIANTS for _ in range(len(FV[n][fs]))])
    Xc = X - X.mean(0)
    U_, S_, _ = np.linalg.svd(Xc, full_matrices=False)
    SC = U_ * S_
    VE = S_ ** 2 / (S_ ** 2).sum()
    print(f"\n【{fs}】PC1 = {VE[0]:.1%}，PC2 = {VE[1]:.1%}")
    print(f"  {'组':<14}{'PC1':>16}{'PC2':>16}")
    for g in ["WT-GCG", "WT-GCA"] + [n for _, n in VARIANTS]:
        s = SC[labels == g]
        print(f"  {g:<14}{s[:,0].mean():>10.2f} ± {s[:,0].std():<4.2f}"
              f"{s[:,1].mean():>10.2f} ± {s[:,1].std():<4.2f}")

with open("results/PC含义.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print("\n写入 results/PC含义.csv")
