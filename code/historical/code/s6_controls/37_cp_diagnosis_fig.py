# -*- coding: utf-8 -*-
"""
阶段 37 —— 「CP 偏离能否解释活性」诊断图
四联图：
 (a) 三个 CP 偏离指标的 z 值（GCG），灰带 = 噪声地板 ±3 SD
 (b) 靶C–E72 距离（GCG），虚线 = WT 参考
 (c) 蛋白–靶C CP 偏离 vs 实测活性保留率（显示无相关）
 (d) 突变位点保守性 vs 蛋白–靶C CP 偏离（显示 r=+0.85 混杂）

产出：results/figs/fig7_CP偏离诊断.png
"""
import csv, sys, math
sys.stdout.reconfigure(encoding="utf-8")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

CONS = {25:0.02, 26:0.04, 27:0.82, 28:0.84, 29:0.22, 30:0.36, 31:0.82, 32:0.56,
        57:0.67, 58:0.29, 59:0.16, 60:0.30, 98:0.91, 129:0.29, 130:0.03, 131:0.21,
        132:0.05, 133:0.43}
POS = {"M132D":[132], "M132E":[132], "K30H":[30], "G27T-K30H-Q58M":[27,30,58],
       "G27T":[27], "G27D":[27], "G27D-K30H":[27,30], "K30H-Q58M":[30,58],
       "G25E":[25], "G25E-K30H":[25,30], "A59P":[59], "K60R":[60]}

rows = [r for r in csv.DictReader(open("results/CP偏离_汇总.csv", encoding="utf-8-sig"))
        if r["substrate"] == "GCG"]
ORDER = ["M132D", "M132E", "K30H", "K30H-Q58M", "G25E", "A59P", "G27D", "G27T",
         "G27D-K30H", "G27T-K30H-Q58M"]
D = {r["variant"]: r for r in rows}
D = {k: D[k] for k in ORDER if k in D}
names = list(D)
f = lambda v, k: float(D[v][k])

# 显示用短名（去掉 WT 字母前缀，与湿实验叫法一致）
SHORT = {"M132D": "132D", "M132E": "132E", "K30H": "30H", "K30H-Q58M": "30H-58M",
         "G25E": "25E", "A59P": "59P", "G27D": "27D", "G27T": "27T",
         "G27D-K30H": "27D-30H", "G27T-K30H-Q58M": "27T-30H-58M"}
tick = [SHORT.get(v, v) for v in names]

fig, axes = plt.subplots(2, 2, figsize=(17, 12))
fig.suptitle("图7　AF3 接触概率（CP）偏离能否解释「组合后活性下降」？—— 诊断结论：不能",
             fontsize=15, fontweight="bold", y=0.985)

# ---- (a) 三指标 z 值 ----
ax = axes[0][0]
x = np.arange(len(names)); w = 0.27
for i, (k, lab, c) in enumerate([("z_intra", "蛋白内部 CP（长程）", "#8FB8DE"),
                                 ("z_pocket", "活性口袋内部 CP", "#F2A65A"),
                                 ("z_protC", "蛋白–靶C CP", "#C0504D")]):
    ax.bar(x + (i - 1) * w, [f(v, k) for v in names], w, label=lab, color=c,
           edgecolor="white", linewidth=0.6)
ax.axhspan(-3, 3, color="0.85", zorder=0)
ax.axhline(3, color="0.45", ls="--", lw=1)
ax.text(0.02, 0.93, "灰带 = 噪声地板 ±3 SD", transform=ax.transAxes, fontsize=9, color="0.35")
ax.set_xticks(x); ax.set_xticklabels(tick, rotation=42, ha="right", fontsize=9.5)
ax.set_ylabel("偏离 WT 的 z 值（SD 数）", fontsize=11)
ax.set_ylim(-4, 46)
ax.set_title("(a) 三个 CP 指标的偏离：只有口袋内部与蛋白–靶C 超出噪声，\n且幅度由「突变了哪个位点」决定",
             fontsize=11.5, fontweight="bold")
ax.legend(fontsize=9, loc="upper left"); ax.grid(axis="y", alpha=0.25)

# ---- (b) d_E72 ----
ax = axes[0][1]
vals = [f(v, "d_E72") for v in names]
cols = ["#C0504D" if v >= 4 else "#8FB8DE" for v in vals]
ax.bar(x, vals, color=cols, edgecolor="white")
ax.axhline(2.88, color="#1F3B66", ls="--", lw=1.4, label="WT (C4/N4–E72) = 2.88 Å")
for i, v in enumerate(vals):
    ax.text(i, v + 0.18, f"{v:.2f}", ha="center", fontsize=8.5)
ax.set_xticks(x); ax.set_xticklabels(tick, rotation=42, ha="right", fontsize=9.5)
ax.set_ylabel("靶C C4/N4 – E72 羧基 最小距离 (Å)", fontsize=11)
ax.set_ylim(0, 8.2)
ax.set_title("(b) 催化几何：仅三点突变 27T-30H-58M 出现明显崩坏\n（中位 6.95 Å，5 模型中 3 个 >5 Å）",
             fontsize=11.5, fontweight="bold")
ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.25)

# ---- (c) 偏离 vs 活性 ----
ax = axes[1][0]
pts = [(f(v, "protC_rmsd"), float(D[v]["activity_retention"]), v)
       for v in names if D[v]["activity_retention"]]
ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=90, color="#C0504D", zorder=3)
OFF_C = {"M132D": (-42, 8), "M132E": (-42, -14), "K30H": (8, 4), "K30H-Q58M": (8, -14),
         "G25E": (8, 6), "G27T": (-10, 10), "G27D": (8, 6), "G27D-K30H": (8, 6),
         "G27T-K30H-Q58M": (-30, 10)}
for xx, yy, v in pts:
    ax.annotate(SHORT.get(v, v), (xx, yy), textcoords="offset points",
                xytext=OFF_C.get(v, (7, 5)), fontsize=9)
ax.set_xlim(-0.004, 0.076); ax.set_ylim(0.15, 1.05)
ax.axvspan(0.0014, 0.00911, color="#8FB8DE", alpha=0.22, zorder=0)
ax.text(0.0095, 0.05, "WT 噪声地板\n(seed 间最大差异)", fontsize=8.5, color="0.35")
ax.set_xlabel("蛋白–靶C CP 偏离（RMSD vs WT）", fontsize=11)
ax.set_ylabel("实测活性保留率", fontsize=11)
ax.set_title("(c) 偏离越大 ≠ 活性越低：r = −0.15\nG27T 偏离第二大，活性却最高（98%）",
             fontsize=11.5, fontweight="bold")
ax.grid(alpha=0.25)

# ---- (d) 保守性混杂 ----
ax = axes[1][1]
pts = [(max(CONS[p] for p in POS[v]), f(v, "protC_rmsd"), v)
       for v in names if v in POS]
ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=90, color="#5B8C5A", zorder=3)
OFF_D = {"G27T": (-8, -16), "G27D": (8, -4), "G27D-K30H": (-52, 6),
         "G27T-K30H-Q58M": (-96, -4), "K30H": (8, 4), "K30H-Q58M": (8, -12),
         "M132D": (8, 4), "G25E": (-34, 6), "A59P": (6, 6)}
for xx, yy, v in pts:
    ax.annotate(SHORT.get(v, v), (xx, yy), textcoords="offset points",
                xytext=OFF_D.get(v, (7, 5)), fontsize=9)
ax.set_xlim(-0.05, 0.95); ax.set_ylim(-0.004, 0.074)
xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
r = sxy / math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
zz = np.polyfit(xs, ys, 1)
xr = np.linspace(min(xs), max(xs), 50)
ax.plot(xr, zz[0] * xr + zz[1], color="#5B8C5A", ls="--", lw=1.4, alpha=0.7)
ax.set_xlabel("被突变位点的保守性（WT 频率）", fontsize=11)
ax.set_ylabel("蛋白–靶C CP 偏离（RMSD vs WT）", fontsize=11)
ax.set_title(f"(d) 混杂暴露：偏离 ≈ 位点保守性的代理变量（r = {r:+.2f}）\n"
             "同为位点27，G27T 与 G27D 化学迥异却给出几乎相同的偏离",
             fontsize=11.5, fontweight="bold")
ax.grid(alpha=0.25)

plt.tight_layout(rect=[0, 0, 1, 0.955])
plt.savefig("results/figs/fig7_CP偏离诊断.png", dpi=175, bbox_inches="tight")
print("写入 results/figs/fig7_CP偏离诊断.png")
