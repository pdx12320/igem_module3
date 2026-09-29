# -*- coding: utf-8 -*-
"""
阶段 28 —— 以「全部 GCG 位点为靶点」重新分析

定义变更（相对阶段 24-27）：
  旧口径：on-target = pos388 单点；其余 C→T = 脱靶
  新口径：on-target = 参考序列中全部 GCG（-1=G, +1=G）的 C 位点（47 个）
          off-target = 其余全部 C 位点（244 个，含 GCA/GCT/GCC/ACA/TCA…）

指标（每个突变体，a/b 重复取均值）：
  GCG 编辑均值/总和、非 GCG 编辑均值/总和
  GCG 偏好比 = GCG均值 / 非GCG均值（>1 = 偏好 GCG 靶点）
  靶向特异性 S = Σgcg / (Σgcg + Σoff)

样本范围：延续上一步，去除全部 P 相关突变（PUF12-9 与 P4/P5/P6/P7/P8），
          P 系列数值在汇总表中单列对比。

产出：results/GCG_target_summary.csv
      results/GCG_sites_matrix.csv
      results/GCG_target_analysis.png
"""
import glob, os, re, sys, csv, statistics
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

REF = "".join(l for l in open("Seq/Bam/G22609034389-1-32F.for.ref.fa", encoding="utf-8").read().splitlines()
              if not l.startswith(">"))
L = len(REF); FLOOR = 0.05
CS = [i + 1 for i, c in enumerate(REF) if c == "C"]

def motif(p):
    i = p - 1
    if i - 1 < 0 or i + 1 >= L:
        return "?"
    return REF[i-1] + "C" + REF[i+1]

GCG = [p for p in CS if motif(p) == "GCG"]          # 靶点
NON = [p for p in CS if motif(p) != "GCG"]          # 非靶点
GCG_SET, NON_SET = set(GCG), set(NON)

def parse(p):
    out = {}
    for i, l in enumerate(open(p, encoding="latin-1")):
        if i == 0: continue
        c = l.rstrip("\n").split("\t")
        if len(c) < 11 or c[2] != "C" or c[3] != "T": continue
        try: pos, freq = int(c[1]), float(c[7])
        except ValueError: continue
        if freq >= FLOOR: out[pos] = freq
    return out

def mut_of(n):
    m = re.match(r'G\d+-(b?)(\d+)-(.*)$', n)
    return m.group(3) if m else n

data = {}
for f in sorted(glob.glob("Seq/Var/*.var.xls")):
    if ".filt." in f: continue
    n = os.path.basename(f).replace(".var.xls", "")
    data[n] = dict(mut=mut_of(n), sites=parse(f))

by_mut = defaultdict(list)
for s in data.values():
    by_mut[s["mut"]].append(s["sites"])

print(f"靶点(GCG) 位点数: {len(GCG)}   非靶点 C 位点数: {len(NON)}   合计 {len(CS)}")

def stats_for(sites):
    """sites: {pos: freq}；未检出=0"""
    g = [sites.get(p, 0.0) for p in GCG]
    o = [sites.get(p, 0.0) for p in NON]
    return dict(
        gcg_mean=statistics.mean(g), gcg_sum=sum(g), n_gcg=sum(1 for x in g if x > 0),
        off_mean=statistics.mean(o), off_sum=sum(o), n_off=sum(1 for x in o if x > 0),
        gcg_max=max(g), off_max=max(o),
    )

rows = []
for mut, ss in by_mut.items():
    agg = {}
    for k in ("gcg_mean","gcg_sum","n_gcg","off_mean","off_sum","n_off","gcg_max","off_max"):
        agg[k] = statistics.mean([stats_for(st)[k] for st in ss])
    agg["mut"] = mut
    agg["n_rep"] = len(ss)
    agg["gcg_pref"] = (agg["gcg_mean"] / agg["off_mean"]) if agg["off_mean"] > 0 else float("inf")
    agg["S"] = agg["gcg_sum"] / (agg["gcg_sum"] + agg["off_sum"]) if (agg["gcg_sum"] + agg["off_sum"]) > 0 else 0
    agg["is_P"] = mut.startswith("P")
    rows.append(agg)

# 非 P（主分析）与 P（对比）
main = sorted([r for r in rows if not r["is_P"]], key=lambda r: -r["gcg_pref"])
prows = sorted([r for r in rows if r["is_P"]], key=lambda r: -r["gcg_pref"])

print()
print("=" * 122)
print("表A  以「全部 GCG 为靶点」的突变体排序（非 P；按 GCG 偏好比 = GCG均值/非GCG均值 降序）")
print("=" * 122)
print(f"{'突变':<20}{'GCG均值%':>9}{'GCG总和%':>9}{'GCG位点数':>9}{'非GCG均值%':>11}{'非GCG总和%':>11}"
      f"{'偏好比':>8}{'S靶向':>7}")
for r in main:
    if r["gcg_sum"] < 0.05: continue
    print(f"{r['mut']:<20}{r['gcg_mean']*100:>9.2f}{r['gcg_sum']*100:>9.0f}{r['n_gcg']:>9.1f}"
          f"{r['off_mean']*100:>11.2f}{r['off_sum']*100:>11.0f}{r['gcg_pref']:>8.2f}{r['S']:>7.3f}")

print()
print("=" * 122)
print("表B  P 系列（对比；已从主分析剔除）")
print("=" * 122)
for r in prows:
    print(f"{r['mut']:<20}{r['gcg_mean']*100:>9.2f}{r['gcg_sum']*100:>9.0f}{r['n_gcg']:>9.1f}"
          f"{r['off_mean']*100:>11.2f}{r['off_sum']*100:>11.0f}{r['gcg_pref']:>8.2f}{r['S']:>7.3f}")

# 关键：388 单点 vs 全 GCG 口径的对照
print()
print("=" * 122)
print("表C  口径变更的影响：旧口径(on=388) vs 新口径(全 GCG)")
print("=" * 122)
par = next((r for r in rows if r["mut"] == "PUF12-9"), None)
print(f"{'突变':<20}{'388%':>7}{'GCG均值%':>10}{'旧判读':>26}{'新判读':>30}")
for r in main[:14]:
    mut = r["mut"]; ss = by_mut[mut]
    f388 = statistics.mean([st.get(388, 0) for st in ss]) * 100
    old = "高388" if f388 > 35 else ("中" if f388 > 20 else "低")
    new = f"偏好GCG({r['gcg_pref']:.2f})" if r["gcg_pref"] > 1 else f"偏好非GCG({r['gcg_pref']:.2f})"
    print(f"{mut:<20}{f388:>7.0f}{r['gcg_mean']*100:>10.1f}{old:>26}{new:>30}")

print()
print("="*122)
print("表D  联合判据筛查（GCG 均值 ≥ 2%，即靶向活性足够；按 GCG 偏好比降序）")
print("="*122)
print(f"{'突变':<20}{'GCG均值%':>9}{'非GCG均值%':>11}{'偏好比':>8}{'GCG位点数':>9}")
for r in sorted([x for x in rows if not x["is_P"] and x["gcg_mean"] >= 0.02], key=lambda x: -x["gcg_pref"]):
    print(f"{r['mut']:<20}{r['gcg_mean']*100:>9.2f}{r['off_mean']*100:>11.2f}{r['gcg_pref']:>8.2f}{r['n_gcg']:>9.1f}")
print()
print("对照：亲本 PUF12-9  GCG均值=%.2f%%  非GCG均值=%.2f%%  偏好比=%.2f" % (par["gcg_mean"]*100, par["off_mean"]*100, par["gcg_pref"]))

# ---- CSV: 汇总 ----
with open("results/GCG_target_summary.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["mutation","is_P","n_rep","gcg_mean_pct","gcg_sum_pct","n_gcg_sites",
                "nonGCG_mean_pct","nonGCG_sum_pct","n_nonGCG_sites","gcg_preference","S_targeting","f_388_pct"])
    for r in sorted(rows, key=lambda x: (x["is_P"], -x["gcg_pref"])):
        ss = by_mut[r["mut"]]
        f388 = statistics.mean([st.get(388, 0) for st in ss]) * 100
        w.writerow([r["mut"], r["is_P"], r["n_rep"], f"{r['gcg_mean']*100:.3f}", f"{r['gcg_sum']*100:.1f}",
                    f"{r['n_gcg']:.1f}", f"{r['off_mean']*100:.3f}", f"{r['off_sum']*100:.1f}",
                    f"{r['n_off']:.1f}", f"{r['gcg_pref']:.3f}", f"{r['S']:.4f}", f"{f388:.2f}"])

# ---- CSV: 突变 × GCG 位点矩阵 ----
gcg_sorted = sorted(GCG, key=lambda p: -sum(st.get(p, 0) for ss in by_mut.values() for st in ss))
with open("results/GCG_sites_matrix.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["mutation"] + [str(p) for p in gcg_sorted])
    w.writerow(["motif"] + ["GCG"] * len(gcg_sorted))
    for r in sorted(rows, key=lambda x: (x["is_P"], -x["gcg_sum"])):
        ss = by_mut[r["mut"]]
        vals = []
        for p in gcg_sorted:
            fr = [st[p] for st in ss if p in st]
            vals.append(f"{statistics.mean(fr)*100:.1f}" if fr else "")
        w.writerow([r["mut"]] + vals)

print("\n写入 results/GCG_target_summary.csv")
print("写入 results/GCG_sites_matrix.csv")

# ---- 绘图 ----
try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig = plt.figure(figsize=(20, 10.5), dpi=150)
    gs = fig.add_gridspec(1, 2, width_ratios=[0.9, 1.6], wspace=0.62)

    # 面板A：散点 GCG vs 非GCG
    ax = fig.add_subplot(gs[0, 0])
    for r in rows:
        x = r["gcg_mean"] * 100; y = r["off_mean"] * 100
        isP = r["is_P"]; lead = r["mut"] == "27T-30H-58M"
        c = "#C0392B" if lead else ("#8E8E8E" if isP else "#2E548B")
        s = 150 if lead else (70 if isP else 55)
        ax.scatter(x, y, s=s, c=c, zorder=3, edgecolors="white", linewidths=.8)
        if lead or isP or x > 12 or y > 12:
            ax.annotate(r["mut"], (x, y), textcoords="offset points", xytext=(5, 3), fontsize=7)
    lim = max(ax.get_xlim()[1], ax.get_ylim()[1])
    ax.plot([0, lim], [0, lim], "--", c="#7F8C8D", lw=1.2)
    ax.text(lim*0.55, lim*0.60, "GCG = 非GCG", fontsize=8, color="#7F8C8D", rotation=38)
    ax.set_xlabel("GCG 位点平均编辑 %（靶点）")
    ax.set_ylabel("非 GCG 位点平均编辑 %（脱靶）")
    ax.set_title("GCG 靶向偏好\n(对角线下方 = 偏好 GCG 靶点)", fontsize=12)
    ax.grid(alpha=.25)

    # 面板B：GCG 位点热图
    ax2 = fig.add_subplot(gs[0, 1])
    rs = sorted([r for r in rows if not r["is_P"] and r["gcg_sum"] > 0.2], key=lambda r: -r["gcg_sum"])
    M = np.full((len(rs), len(gcg_sorted)), np.nan)
    for i, r in enumerate(rs):
        for j, p in enumerate(gcg_sorted):
            fr = [st[p] for st in by_mut[r["mut"]] if p in st]
            if fr: M[i, j] = statistics.mean(fr) * 100
    im = ax2.imshow(M, aspect="auto", cmap="YlOrRd", vmin=0, vmax=45)
    ax2.set_xticks(range(len(gcg_sorted)))
    ax2.set_xticklabels([f"{p}" for p in gcg_sorted], fontsize=6.5, rotation=90)
    ax2.set_yticks(range(len(rs)))
    ax2.set_yticklabels([f"{r['mut']}  ({r['gcg_pref']:.1f})" for r in rs], fontsize=8)
    for i in range(len(rs)):
        for j in range(len(gcg_sorted)):
            if not np.isnan(M[i, j]) and M[i, j] >= 20:
                ax2.text(j, i, f"{M[i,j]:.0f}", ha="center", va="center", fontsize=5, color="black")
    # 标出 388 与 390
    for tag, col in ((388, "#1B6B5A"), (390, "#8E44AD")):
        if tag in gcg_sorted:
            j = gcg_sorted.index(tag)
            ax2.axvline(j, color=col, lw=1.6, alpha=.85, ls=":")
            ax2.text(j, -0.8, str(tag), ha="center", va="bottom", fontsize=8, color=col, fontweight="bold")
    cb = fig.colorbar(im, ax=ax2, fraction=0.02, pad=0.01); cb.set_label("编辑频率 %", fontsize=9)
    ax2.set_xlabel("GCG 靶点（位置；按总编辑量降序）— 绿=388 原靶点，紫=390 旁位", fontsize=10)
    ax2.set_title(f"各突变体在全部 {len(GCG)} 个 GCG 靶点上的编辑谱（非 P）", fontsize=12)
    fig.suptitle("以「全部 GCG 位点为靶点」重新分析", fontsize=15, y=0.98)
    fig.savefig("results/GCG_target_analysis.png", bbox_inches="tight")
    print("写入 results/GCG_target_analysis.png")
except Exception as e:
    print("绘图跳过:", e)
