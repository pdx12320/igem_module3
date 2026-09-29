# -*- coding: utf-8 -*-
"""
阶段 48 —— 两个问题的定量回答
  ① 「蛋白内部 CP 的长程」（F2，|i−j|≥5）到底是什么？为什么这么定义？
  ② 「27 位两个突变性质迥异」这个说法是否站得住？—— 附位点 31 的 5 个替换作对照

产出：results/长程CP_统计.csv、results/位点31替换系列.csv
"""
import json, glob, os, sys, math, csv
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import af_utils as U

PROT, RNA, TARGET_C = U.PROT_CHAIN, U.RNA_CHAIN, 4

# 残基体积（Å³，Zamyatnin 1972 常用值）与生理 pH 下的侧链电荷
VOL = {"G": 60.1, "A": 88.6, "S": 89.0, "C": 108.5, "D": 111.1, "T": 116.1,
       "N": 114.1, "P": 112.7, "E": 138.4, "V": 140.0, "Q": 143.8, "H": 153.2,
       "M": 162.9, "I": 166.7, "L": 166.7, "K": 168.6, "R": 173.4, "F": 189.9,
       "Y": 193.6, "W": 227.8}
CHG = {"D": -1, "E": -1, "K": 1, "R": 1, "H": 0.1}


def load_dir(d):
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*full_data*.json"))):
        j = json.load(open(f, encoding="utf-8"))
        cids = j["token_chain_ids"]
        cpm = np.asarray(j["contact_probs"], dtype=np.float64)
        idx = np.array([i for i in range(len(cids)) if cids[i] == PROT])
        sub = cpm[np.ix_(idx, idx)]
        out.append(np.maximum(sub, sub.T))
    return out


# ===========================================================================
# ① 长程内部 CP
# ===========================================================================
print("=" * 104)
print("① 「蛋白内部 CP 的长程」（F2）是什么")
print("=" * 104)

wt_dirs = sorted(x for x in glob.glob("GUGCGCG_20/*") if os.path.isdir(x))
WT = [M for d in wt_dirs for M in load_dir(d)]
A = np.array(WT)                       # (100, 199, 199)
n = A.shape[1]
iu = np.triu_indices(n, k=1)
sep = np.abs(iu[0] - iu[1])            # 序列间隔（0-based 索引之差）
mbar = A.mean(0)
sd = A.std(0, ddof=1)

print(f"\nWT-GCG：{A.shape[0]} 个 model，残基数 {n}，残基对总数 {len(iu[0])}")
print(f"\n{'序列间隔 |i−j|':<16}{'残基对数':>10}{'占比':>8}{'平均CP':>10}{'CP范围':>18}{'跨model SD':>12}")
for lo, hi, lab in [(1, 1, "1"), (2, 2, "2"), (3, 3, "3"), (4, 4, "4"),
                    (5, 9, "5–9"), (10, 19, "10–19"), (20, 49, "20–49"),
                    (50, 999, "≥50")]:
    m = (sep >= lo) & (sep <= hi)
    if not m.any(): continue
    vals = mbar[iu[0][m], iu[1][m]]
    print(f"{lab:<16}{int(m.sum()):>10}{m.mean():>8.1%}{vals.mean():>10.3f}"
          f"{f'{vals.min():.3f}–{vals.max():.3f}':>18}"
          f"{sd[iu[0][m], iu[1][m]].mean():>12.4f}")

near = sep < 5
far = ~near
print(f"\nF2 的定义：剔除 |i−j| < 5 的残基对")
print(f"  剔除 {int(near.sum())} 对（{near.mean():.1%}），保留 {int(far.sum())} 对（{far.mean():.1%}）")

# 这些"长程"对在三维空间里真的远吗？（用 CP 作代理：CP 高 = 空间上近）
cp_far = mbar[iu[0][far], iu[1][far]]
for thr in [0.5, 0.8, 0.9]:
    print(f"  保留对中 CP > {thr} 的占 {float((cp_far > thr).mean()):.1%}"
          f"　→ 这些在三维空间里其实是近的")

# 剔除前后，PCA/分离度结果差多少？直接用数据本身比较
var_near = np.var(A[:, iu[0][near], iu[1][near]], axis=0).sum()
var_far = np.var(A[:, iu[0][far], iu[1][far]], axis=0).sum()
print(f"\n  跨 model 方差总量：序列近邻对(被剔除) = {var_near:.3f}，"
      f"保留对 = {var_far:.3f}　→ 剔除部分仅占 {var_near/(var_near+var_far):.2%}")

with open("results/长程CP_统计.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["seq_separation", "n_pairs", "fraction_of_pairs", "mean_CP",
                "CP_min", "CP_max", "mean_SD_across_models"])
    for lo, hi, lab in [(1, 1, "1"), (2, 2, "2"), (3, 3, "3"), (4, 4, "4"),
                        (5, 9, "5-9"), (10, 19, "10-19"), (20, 49, "20-49"), (50, 999, ">=50")]:
        m = (sep >= lo) & (sep <= hi)
        if not m.any(): continue
        vals = mbar[iu[0][m], iu[1][m]]
        w.writerow([lab, int(m.sum()), round(float(m.mean()), 4), round(float(vals.mean()), 4),
                    round(float(vals.min()), 4), round(float(vals.max()), 4),
                    round(float(sd[iu[0][m], iu[1][m]].mean()), 5)])

# ===========================================================================
# ② 位点 27 与位点 31 的替换系列
# ===========================================================================
print("\n" + "=" * 104)
print("② 「27 位两个突变性质迥异」是否站得住")
print("=" * 104)

WT_SEQ = json.load(open("af3_submit/WT_GCG.json", encoding="utf-8"))[0]["sequences"][0]["proteinChain"]["sequence"]
print(f"\nWT 序列：27 位 = {WT_SEQ[26]}，31 位 = {WT_SEQ[30]}，"
      f"132 位 = {WT_SEQ[131]}，57 位 = {WT_SEQ[56]}，72 位 = {WT_SEQ[71]}")

# 有 AF3 模型、且为同一位点单点替换的系列
SERIES = {
    27: [("G27T", "G", "T", "new/mut/g27t_gcg"),
         ("G27D", "G", "D", "new/mut/g27d_gcg")],
    31: [("T31A", "T", "A", "new/negctrl/t31a_gcg_s01"),
         ("T31D", "T", "D", "new/negctrl/t31d_gcg_s01"),
         ("T31V", "T", "V", "new/mut/folds_2026_09_08_16_18/t31v_gcg"),
         ("T31I", "T", "I", "new/mut/folds_2026_09_08_16_18/t31i_gcg"),
         ("T31L", "T", "L", "new/mut/folds_2026_09_08_16_18/t31l_gcg")],
}

# 参考：WT 的内部 CP 与 靶C-CP
wt_mats = [M for d in wt_dirs for M in load_dir(d)]
wt_c = []
for d in wt_dirs:
    for f in sorted(glob.glob(os.path.join(d, "*full_data*.json"))):
        j = json.load(open(f, encoding="utf-8"))
        cids, rids = j["token_chain_ids"], j["token_res_ids"]
        cpm = np.asarray(j["contact_probs"], dtype=np.float64)
        idx = np.array([i for i in range(len(cids)) if cids[i] == PROT])
        t = next(i for i in range(len(cids)) if cids[i] == RNA and rids[i] == TARGET_C)
        wt_c.append(np.maximum(cpm[idx, t], cpm[t, idx]))
Mbar = np.mean(wt_mats, axis=0)
Cbar = np.mean(wt_c, axis=0)
lr = np.array([(i, j) for i in range(n) for j in range(i + 5, n)])
rmsd = lambda a, b: math.sqrt(float(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))

print(f"\n{'替换':<10}{'位点':>5}{'侧链体积':>10}{'电荷':>6}"
      f"{'内部CP偏离':>12}{'靶C-CP偏离':>12}   与同系列对照")
print("-" * 104)
recs = []
for pos, items in SERIES.items():
    base = WT_SEQ[pos - 1]
    print(f"  ── 位点 {pos}（WT = {base}）──")
    for name, wt_aa, mut_aa, d in items:
        if not os.path.isdir(d):
            print(f"  {name:<10}{pos:>5}   （缺少 AF3 模型：{d}）"); continue
        mats = load_dir(d)
        if not mats: continue
        Mb = np.mean(mats, axis=0)
        cs = []
        for f in sorted(glob.glob(os.path.join(d, "*full_data*.json"))):
            j = json.load(open(f, encoding="utf-8"))
            cids, rids = j["token_chain_ids"], j["token_res_ids"]
            cpm = np.asarray(j["contact_probs"], dtype=np.float64)
            idx = np.array([i for i in range(len(cids)) if cids[i] == PROT])
            t = next(i for i in range(len(cids)) if cids[i] == RNA and rids[i] == TARGET_C)
            cs.append(np.maximum(cpm[idx, t], cpm[t, idx]))
        Cb = np.mean(cs, axis=0)
        iz = rmsd([Mb[i, j] for i, j in lr], [Mbar[i, j] for i, j in lr])
        cz = rmsd(Cb, Cbar)
        dv = VOL[mut_aa] - VOL[wt_aa]
        dq = CHG.get(mut_aa, 0) - CHG.get(wt_aa, 0)
        recs.append(dict(pos=pos, name=name, wt=wt_aa, mut=mut_aa,
                         vol=VOL[mut_aa], vol_delta=dv, charge=CHG.get(mut_aa, 0),
                         intra_dev=iz, protC_dev=cz))
        print(f"  {name:<10}{pos:>5}{VOL[mut_aa]:>10.1f}{CHG.get(mut_aa,0):>6.1f}"
              f"{iz:>12.5f}{cz:>12.5f}   Δ体积 {dv:+.1f} Å³，Δ电荷 {dq:+.1f}")

print("\n" + "-" * 104)
print("同位点两两比较（判断「CP 响应」由什么决定）")
print("-" * 104)
for pos, items in SERIES.items():
    sub = [r for r in recs if r["pos"] == pos]
    for i in range(len(sub)):
        for j in range(i + 1, len(sub)):
            a, b = sub[i], sub[j]
            same_v = abs(a["vol"] - b["vol"]) < 10
            same_q = a["charge"] == b["charge"]
            print(f"  {a['name']:<8} vs {b['name']:<8} "
                  f"Δ体积 {abs(a['vol']-b['vol']):>5.1f} Å³（{'相近' if same_v else '不同'}），"
                  f"Δ电荷 {abs(a['charge']-b['charge']):>4.1f}（{'相同' if same_q else '不同'}）"
                  f" → 靶C-CP 偏离比值 {max(a['protC_dev'],b['protC_dev'])/min(a['protC_dev'],b['protC_dev']):>5.2f}×")

with open("results/位点31替换系列.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(recs[0]))
    w.writeheader(); w.writerows(recs)
print("\n写入 results/长程CP_统计.csv、results/位点31替换系列.csv")
