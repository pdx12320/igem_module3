# -*- coding: utf-8 -*-
"""
阶段 30 —— 靶点(GCG)编辑总和 vs 脱靶编辑总和 排序与绘图（P 部分仅保留 WT）

样本范围变更（相对阶段 29）：
  剔除：P4-SNE、P5-TWD、P6-WFD、P7-THE、P7-SNE、P8-GVD（P 系列 loop 重设计变体）
  保留：PUF12-9 —— 即 WT / 组合亲本，作为正常一行参与排序（图中以星标与绿色突出）

口径（与阶段 29 一致）：
  靶点 = 全部 47 个 GCG 位点  → Σ_gcg
  脱靶 = 其余 244 个 C 位点    → Σ_off
  靶向比 = Σ_gcg / Σ_off      → 排序依据
  活性   = C388 / C388(WT=PUF12-9)

产出：results/GCG_vs_off_ranking_WT.csv
      results/GCG_vs_off_ranking_WT.png
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
    return "?" if (i - 1 < 0 or i + 1 >= L) else REF[i-1] + "C" + REF[i+1]

GCG = [p for p in CS if motif(p) == "GCG"]
NON = [p for p in CS if motif(p) != "GCG"]
WT_NAME = "PUF12-9"
EXCLUDE_PS = {"P4-SNE", "P5-TWD", "P6-WFD", "P7-THE", "P7-SNE", "P8-GVD"}

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

by_mut = defaultdict(list)
for f in sorted(glob.glob("Seq/Var/*.var.xls")):
    if ".filt." in f: continue
    n = os.path.basename(f).replace(".var.xls", "")
    by_mut[mut_of(n)].append(parse(f))

PAR_C388 = statistics.mean([st.get(388, 0) for st in by_mut[WT_NAME]])
print(f"WT(PUF12-9) 的 C388 = {PAR_C388:.4f}  → 活性 = C388 / {PAR_C388:.5f}")
print(f"剔除的 P 系列: {', '.join(sorted(EXCLUDE_PS))}；保留 WT: {WT_NAME}\n")

rows = []
for mut, ss in by_mut.items():
    if mut in EXCLUDE_PS:
        continue
    sg = statistics.mean([sum(st.get(p, 0.0) for p in GCG) for st in ss])
    so = statistics.mean([sum(st.get(p, 0.0) for p in NON) for st in ss])
    n_g = statistics.mean([sum(1 for p in GCG if p in st) for st in ss])
    n_o = statistics.mean([sum(1 for p in NON if p in st) for st in ss])
    c388 = statistics.mean([st.get(388, 0) for st in ss])
    rows.append(dict(mut=mut, sum_gcg=sg, sum_off=so,
                     ratio=(sg / so) if so > 0 else float("inf"),
                     n_gcg=n_g, n_off=n_o, c388=c388, act=c388 / PAR_C388,
                     is_wt=(mut == WT_NAME)))

main = sorted(rows, key=lambda r: -r["ratio"])

print("=" * 122)
print("表  靶点(GCG)编辑总和 / 脱靶编辑总和 排序（P 部分仅保留 WT；按靶向比降序）")
print("=" * 122)
print(f"{'排名':>4}{'突变':<20}{'Σ_GCG(靶点)':>12}{'Σ_off(脱靶)':>12}{'靶向比':>9}"
      f"{'活性(保留)':>11}{'C388':>8}{'GCG位点数':>10}")
rk = 0
for r in main:
    if r["sum_gcg"] <= 0.01: continue
    rk += 1
    tag = "  ← WT 基线" if r["is_wt"] else ""
    print(f"{rk:>4}{r['mut']:<20}{r['sum_gcg']*100:>12.0f}{r['sum_off']*100:>12.0f}"
          f"{r['ratio']:>9.2f}{r['act']*100:>10.0f}%{r['c388']*100:>8.0f}{r['n_gcg']:>10.1f}{tag}")

print()
print("=== 联合判据：活性 ≥70% 的候选（按靶向比降序）===")
print(f"{'突变':<20}{'靶向比':>9}{'活性':>8}{'Σ_GCG':>9}{'Σ_off':>8}")
for r in sorted([x for x in main if x["act"] >= 0.70 and x["sum_gcg"] > 0.01], key=lambda x: -x["ratio"]):
    print(f"{r['mut']:<20}{r['ratio']:>9.2f}{r['act']*100:>7.0f}%{r['sum_gcg']*100:>9.0f}{r['sum_off']*100:>8.0f}")

with open("results/GCG_vs_off_ranking_WT.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["rank", "mutation", "is_WT", "sum_GCG_pct", "sum_nonGCG_pct", "targeting_ratio",
                "activity_retention", "C388_pct", "n_GCG_detected", "n_nonGCG_detected"])
    rk = 0
    for r in main:
        if r["sum_gcg"] > 0.01: rk += 1
        w.writerow([rk if r["sum_gcg"] > 0.01 else "", r["mut"], r["is_wt"],
                    f"{r['sum_gcg']*100:.1f}", f"{r['sum_off']*100:.1f}", f"{r['ratio']:.3f}",
                    f"{r['act']:.3f}", f"{r['c388']*100:.2f}", f"{r['n_gcg']:.1f}", f"{r['n_off']:.1f}"])
print("\n写入 results/GCG_vs_off_ranking_WT.csv")

# ---------------- 绘图 ----------------
try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    plot_rows = [r for r in main if r["sum_gcg"] > 0.01][::-1]
    names = [r["mut"] + ("  ★WT" if r["is_wt"] else "") for r in plot_rows]
    sg = np.array([r["sum_gcg"] * 100 for r in plot_rows])
    so = np.array([r["sum_off"] * 100 for r in plot_rows])
    act = np.array([r["act"] for r in plot_rows])
    is_wt = np.array([r["is_wt"] for r in plot_rows])

    fig = plt.figure(figsize=(19, 13.5), dpi=150)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], wspace=0.30)

    # 面板A：成对柱，WT 用绿色高亮
    ax = fig.add_subplot(gs[0, 0])
    y = np.arange(len(names)); h = 0.38
    cols_g = ["#1E7A46" if w else "#2E548B" for w in is_wt]
    cols_o = ["#7DCEA0" if w else "#C0392B" for w in is_wt]
    ax.barh(y + h/2, sg, height=h, color=cols_g, label="靶点 GCG 编辑总和 Σ_gcg")
    ax.barh(y - h/2, so, height=h, color=cols_o, label="脱靶(其他 C)编辑总和 Σ_off")
    for i, r in enumerate(plot_rows):
        lab = f"比 {r['ratio']:.1f}  活性 {r['act']*100:.0f}%" + ("  ★WT基线" if r["is_wt"] else "")
        ax.text(max(sg[i], so[i]) + 12, i, lab, va="center", fontsize=7.5,
                color="#1E7A46" if r["is_wt"] else "#333333",
                fontweight="bold" if r["is_wt"] else "normal")
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=8)
    for tick, w in zip(ax.get_yticklabels(), is_wt):
        if w: tick.set_color("#1E7A46"); tick.set_fontweight("bold")
    ax.set_xlabel("编辑频率总和 %（47 个 GCG 靶点 / 244 个非 GCG 位点）", fontsize=11)
    ax.set_title("各突变体的靶点编辑总和 vs 脱靶编辑总和\n"
                 "（自下而上 = 靶向比 Σ_gcg/Σ_off 由低到高；P 部分仅保留 WT）", fontsize=12)
    ax.legend(loc="lower right", fontsize=9); ax.grid(alpha=.25, axis="x")

    # 面板B：散点
    ax2 = fig.add_subplot(gs[0, 1])
    nw = ~is_wt
    sc = ax2.scatter(so[nw], sg[nw], c=act[nw]*100, cmap="RdYlGn", s=70, vmin=0, vmax=90,
                     edgecolors="#333333", linewidths=.6, zorder=3)
    ax2.scatter(so[is_wt], sg[is_wt], marker="*", s=420, c="#1E7A46",
                edgecolors="white", linewidths=1.2, zorder=5, label="WT (PUF12-9)")
    lim = max(so.max(), sg.max()) * 1.12
    ax2.plot([0, lim], [0, lim], "--", c="#7F8C8D", lw=1.2)
    ax2.text(lim*0.63, lim*0.70, "Σ_gcg = Σ_off", fontsize=8, color="#7F8C8D", rotation=32)
    for r in plot_rows:
        if r["ratio"] > 3 or r["act"] > 0.7 or r["sum_off"] > 300 or r["is_wt"]:
            ax2.annotate(r["mut"] + ("(WT)" if r["is_wt"] else ""),
                         (r["sum_off"]*100, r["sum_gcg"]*100),
                         textcoords="offset points", xytext=(6, 4), fontsize=7.5,
                         color="#1E7A46" if r["is_wt"] else "#333333",
                         fontweight="bold" if r["is_wt"] else "normal")
    cb = fig.colorbar(sc, ax=ax2, fraction=0.04, pad=0.02)
    cb.set_label("活性（相对 WT 的 C388 保留 %）", fontsize=10)
    ax2.set_xlabel("脱靶编辑总和 Σ_off %", fontsize=11)
    ax2.set_ylabel("靶点 GCG 编辑总和 Σ_gcg %", fontsize=11)
    ax2.set_title("靶点 vs 脱靶 编辑总和\n（左上角 = 高靶向编辑 + 低脱靶；颜色 = 活性）", fontsize=12)
    ax2.legend(loc="lower right", fontsize=9); ax2.grid(alpha=.25)

    fig.suptitle("以「全部 GCG 为靶点」：靶点/脱靶编辑总和排序（P 部分仅保留 WT）", fontsize=15, y=0.975)
    fig.savefig("results/GCG_vs_off_ranking_WT.png", bbox_inches="tight")
    print("写入 results/GCG_vs_off_ranking_WT.png")
except Exception as e:
    print("绘图跳过:", e)
