# -*- coding: utf-8 -*-
"""
阶段 29 —— 靶点(GCG)编辑总和 vs 脱靶(其他位点)编辑总和 的排序与绘图
（并加入原有分析的「活性」= C388 / 亲本C388）

口径：
  靶点 = 全部 GCG 位点（47 个 C）        → Σ_gcg  = 靶点编辑频率总和
  脱靶 = 其余全部 C 位点（244 个）        → Σ_off  = 脱靶编辑频率总和
  靶向比 = Σ_gcg / Σ_off                 → 排序依据（越高 = 编辑越集中于 GCG 靶点）
  活性   = C388 / 0.67677（亲本 PUF12-9 的 C388）→ 相对亲本的 on-target 保留率

样本范围：主排序排除全部 P 相关突变（延续前一步）；
          亲本 PUF12-9 与 P 系列数值在 CSV/图中单列对比。

产出：results/GCG_vs_off_ranking.csv
      results/GCG_vs_off_ranking.png
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

# 亲本参照
PAR_C388 = statistics.mean([st.get(388, 0) for st in by_mut["PUF12-9"]])
print(f"亲本 PUF12-9 的 C388 = {PAR_C388:.4f}  （活性 = C388 / {PAR_C388:.5f}）")

rows = []
for mut, ss in by_mut.items():
    sg = statistics.mean([sum(st.get(p, 0.0) for p in GCG) for st in ss])
    so = statistics.mean([sum(st.get(p, 0.0) for p in NON) for st in ss])
    n_g = statistics.mean([sum(1 for p in GCG if p in st) for st in ss])
    n_o = statistics.mean([sum(1 for p in NON if p in st) for st in ss])
    c388 = statistics.mean([st.get(388, 0) for st in ss])
    rows.append(dict(mut=mut, sum_gcg=sg, sum_off=so,
                     ratio=(sg / so) if so > 0 else float("inf"),
                     n_gcg=n_g, n_off=n_o, c388=c388, act=c388 / PAR_C388,
                     is_P=mut.startswith("P")))

main = sorted([r for r in rows if not r["is_P"]], key=lambda r: -r["ratio"])
prows = sorted([r for r in rows if r["is_P"]], key=lambda r: -r["ratio"])
par = next(r for r in rows if r["mut"] == "PUF12-9")

print()
print("=" * 118)
print("表  靶点(GCG)编辑总和 / 脱靶编辑总和 排序（非 P；按靶向比降序）")
print("=" * 118)
print(f"{'排名':>4}{'突变':<20}{'Σ_GCG(靶点)':>12}{'Σ_off(脱靶)':>12}{'靶向比':>9}"
      f"{'活性(保留)':>11}{'C388':>8}{'GCG位点数':>10}")
for i, r in enumerate([x for x in main if x["sum_gcg"] > 0.01], 1):
    print(f"{i:>4}{r['mut']:<20}{r['sum_gcg']*100:>12.0f}{r['sum_off']*100:>12.0f}"
          f"{r['ratio']:>9.2f}{r['act']*100:>10.0f}%{r['c388']*100:>8.0f}{r['n_gcg']:>10.1f}")
print("\n--- 参照 ---")
for r in [par] + prows:
    print(f"{'—':>4}{r['mut']:<20}{r['sum_gcg']*100:>12.0f}{r['sum_off']*100:>12.0f}"
          f"{r['ratio']:>9.2f}{r['act']*100:>10.0f}%{r['c388']*100:>8.0f}{r['n_gcg']:>10.1f}   (P系列/亲本，不参与主排序)")

with open("results/GCG_vs_off_ranking.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["rank", "mutation", "is_P", "sum_GCG_pct", "sum_nonGCG_pct", "targeting_ratio",
                "activity_retention", "C388_pct", "n_GCG_sites_detected", "n_nonGCG_detected"])
    rk = 0
    for r in sorted(rows, key=lambda x: (x["is_P"], -x["ratio"])):
        if not r["is_P"] and r["sum_gcg"] > 0.01:
            rk += 1
        w.writerow(["" if r["is_P"] else rk, r["mut"], r["is_P"], f"{r['sum_gcg']*100:.1f}",
                    f"{r['sum_off']*100:.1f}", f"{r['ratio']:.3f}", f"{r['act']:.3f}",
                    f"{r['c388']*100:.2f}", f"{r['n_gcg']:.1f}", f"{r['n_off']:.1f}"])
print("\n写入 results/GCG_vs_off_ranking.csv")

# ---------------- 绘图 ----------------
try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    plot_rows = [r for r in main if r["sum_gcg"] > 0.01][::-1]   # 反转：最优在上
    names = [r["mut"] for r in plot_rows]
    sg = np.array([r["sum_gcg"] * 100 for r in plot_rows])
    so = np.array([r["sum_off"] * 100 for r in plot_rows])
    act = np.array([r["act"] for r in plot_rows])

    fig = plt.figure(figsize=(19, 13), dpi=150)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], wspace=0.30)

    # 面板A：横向成对柱（Σ_gcg vs Σ_off），排序=靶向比
    ax = fig.add_subplot(gs[0, 0])
    y = np.arange(len(names)); h = 0.38
    ax.barh(y + h/2, sg, height=h, color="#2E548B", label="靶点 GCG 编辑总和 Σ_gcg")
    ax.barh(y - h/2, so, height=h, color="#C0392B", label="脱靶(其他 C)编辑总和 Σ_off")
    for i, r in enumerate(plot_rows):
        ax.text(max(sg[i], so[i]) + 12, i, f"比 {r['ratio']:.1f}  活性 {r['act']*100:.0f}%",
                va="center", fontsize=7.5, color="#333333")
    # 亲本参照线
    ax.axvline(par["sum_gcg"] * 100, ls="--", c="#1B6B5A", lw=1.2, alpha=.8)
    ax.axvline(par["sum_off"] * 100, ls="--", c="#8E44AD", lw=1.2, alpha=.8)
    ax.text(par["sum_gcg"]*100, len(names)-0.2, f" 亲本Σ_gcg={par['sum_gcg']*100:.0f}",
            color="#1B6B5A", fontsize=8, rotation=90, va="top")
    ax.text(par["sum_off"]*100, len(names)-0.2, f" 亲本Σ_off={par['sum_off']*100:.0f}",
            color="#8E44AD", fontsize=8, rotation=90, va="top")
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("编辑频率总和 %（47 个 GCG 靶点 / 244 个非 GCG 位点）", fontsize=11)
    ax.set_title("各突变体的靶点编辑总和 vs 脱靶编辑总和\n（自下而上 = 靶向比 Σ_gcg/Σ_off 由低到高；已排除 P 系列）", fontsize=12)
    ax.legend(loc="lower right", fontsize=9); ax.grid(alpha=.25, axis="x")

    # 面板B：散点 Σ_off vs Σ_gcg，颜色=活性
    ax2 = fig.add_subplot(gs[0, 1])
    sc = ax2.scatter(so, sg, c=act*100, cmap="RdYlGn", s=70, vmin=0, vmax=90,
                     edgecolors="#333333", linewidths=.6, zorder=3)
    lim = max(so.max(), sg.max()) * 1.12
    ax2.plot([0, lim], [0, lim], "--", c="#7F8C8D", lw=1.2)
    ax2.text(lim*0.62, lim*0.68, "Σ_gcg = Σ_off", fontsize=8, color="#7F8C8D", rotation=32)
    for r in plot_rows:
        if r["ratio"] > 3 or r["act"] > 0.7 or r["sum_off"] > 300:
            ax2.annotate(r["mut"], (r["sum_off"]*100, r["sum_gcg"]*100),
                         textcoords="offset points", xytext=(5, 3), fontsize=7.5)
    # 亲本
    ax2.scatter([par["sum_off"]*100], [par["sum_gcg"]*100], marker="*", s=280,
                c="#8E44AD", edgecolors="white", linewidths=1, zorder=4, label="亲本 PUF12-9")
    ax2.annotate("PUF12-9(亲本)", (par["sum_off"]*100, par["sum_gcg"]*100),
                 textcoords="offset points", xytext=(8, -12), fontsize=8.5, color="#8E44AD")
    cb = fig.colorbar(sc, ax=ax2, fraction=0.04, pad=0.02)
    cb.set_label("活性（相对亲本的 C388 保留 %）", fontsize=10)
    ax2.set_xlabel("脱靶编辑总和 Σ_off %", fontsize=11)
    ax2.set_ylabel("靶点 GCG 编辑总和 Σ_gcg %", fontsize=11)
    ax2.set_title("靶点 vs 脱靶 编辑总和\n（左上角 = 高靶向编辑 + 低脱靶；颜色 = 活性）", fontsize=12)
    ax2.legend(loc="lower right", fontsize=9); ax2.grid(alpha=.25)

    fig.suptitle("以「全部 GCG 为靶点」：靶点/脱靶编辑总和排序（含活性）", fontsize=15, y=0.975)
    fig.savefig("results/GCG_vs_off_ranking.png", bbox_inches="tight")
    print("写入 results/GCG_vs_off_ranking.png")
except Exception as e:
    print("绘图跳过:", e)
