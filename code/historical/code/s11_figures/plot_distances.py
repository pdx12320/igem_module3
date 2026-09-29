# -*- coding: utf-8 -*-
"""
绘制 +1 位接触的距离分布图（读取 results/key_distances.csv 与 contacts_frequency.csv）。

产出 results/plots/ 下：
  distance_violin_key_residues.png —— 关键残基距离小提琴图（G / A-swap / A-off 三组）
  frequency_bar.png               —— 全残基 +1 碱基(≤5Å)接触频率 柱状对比（G vs A-swap）
"""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 中文标签字体（Windows 下优先微软雅黑/黑体，避免缺字）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = os.path.join("results", "plots")
os.makedirs(OUT_DIR, exist_ok=True)

ORDER = ["GUGCGCG", "GUGCACG", "AUGCAGC"]
COLORS = {"GUGCGCG": "#2b6cb0", "GUGCACG": "#c53030", "AUGCAGC": "#718096"}
XLABEL = ["+1=G\n(GCG)", "+1=A\n(swap)", "+1=A\n(off)"]

KEY = [(29, "HIS"), (30, "LYS"), (32, "TYR"), (57, "ASN"), (58, "GLN"),
       (59, "ALA"), (60, "LYS"), (67, "TYR"), (68, "GLY"), (69, "ARG"),
       (70, "HIS"), (72, "GLU"), (99, "TRP")]

# ---------------- 读取 ----------------
data = defaultdict(lambda: defaultdict(list))
for row in csv.DictReader(open("results/key_distances.csv", encoding="utf-8-sig")):
    if row["min_dist_base"] != "":
        data[row["rna"]][int(row["resi"])].append(float(row["min_dist_base"]))

# ---------------- Fig 1：关键残基小提琴图 ----------------
fig, axes = plt.subplots(3, 5, figsize=(16, 9))
axes = axes.ravel()
for i, (resi, resn) in enumerate(KEY):
    ax = axes[i]
    dists = [data[rna].get(resi, []) for rna in ORDER]
    vp = ax.violinplot(dists, positions=[0, 1, 2], showmedians=True, showextrema=True)
    for j, body in enumerate(vp["bodies"]):
        body.set_facecolor(COLORS[ORDER[j]])
        body.set_alpha(0.55)
    for part in ("cbars", "cmins", "cmaxes", "cmedians"):
        vp[part].set_color("black")
        vp[part].set_linewidth(0.8)
    ax.set_title(f"{resn}{resi}", fontsize=11, fontweight="bold")
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(XLABEL, fontsize=7)
    ax.axhline(5.0, ls="--", lw=0.9, color="red", alpha=0.8)
    ax.axhline(3.5, ls=":", lw=0.9, color="orange", alpha=0.8)
    ax.set_ylabel("距离 (Å)", fontsize=8)
    ax.tick_params(axis="y", labelsize=7)
for j in range(len(KEY), len(axes)):
    axes[j].axis("off")
fig.suptitle("+1 位碱基 → 关键残基 最小重原子距离分布（红虚线=5Å 接触阈值，橙点线=3.5Å）",
             fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(os.path.join(OUT_DIR, "distance_violin_key_residues.png"), dpi=200)
plt.close(fig)

# ---------------- Fig 2：全残基接触频率柱状图（G vs A-swap） ----------------
freq = defaultdict(dict)
for row in csv.DictReader(open("results/contacts_frequency.csv", encoding="utf-8-sig")):
    freq[row["rna"]][int(row["resi"])] = float(row["freq_base_5.0"])

all_resi = sorted(set(freq["GUGCGCG"]) | set(freq["GUGCACG"]))
# 只画任一组频率 > 0.05 的残基
sel = [r for r in all_resi if freq["GUGCGCG"].get(r, 0) > 0.05 or freq["GUGCACG"].get(r, 0) > 0.05]
sel.sort(key=lambda r: -freq["GUGCGCG"].get(r, 0))

x = range(len(sel))
g = [freq["GUGCGCG"].get(r, 0) for r in sel]
a = [freq["GUGCACG"].get(r, 0) for r in sel]
labels = [f"{r}" for r in sel]

fig, ax = plt.subplots(figsize=(max(6, len(sel) * 0.5), 5))
w = 0.38
ax.bar([i - w / 2 for i in x], g, w, label="+1=G (GCG)", color=COLORS["GUGCGCG"], alpha=0.85)
ax.bar([i + w / 2 for i in x], a, w, label="+1=A (swap)", color=COLORS["GUGCACG"], alpha=0.85)
ax.set_xticks(list(x))
ax.set_xticklabels(labels, rotation=90, fontsize=8)
ax.set_ylabel("+1 碱基接触频率 (≤5Å)")
ax.set_title("蛋白残基与 +1 碱基的接触频率：G 组 vs A 组")
ax.legend()
ax.set_ylim(0, 1.05)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "frequency_bar.png"), dpi=200)
plt.close(fig)

print("已生成：")
print("  results/plots/distance_violin_key_residues.png")
print("  results/plots/frequency_bar.png")
print(f"  （{len(sel)} 个残基进入频率柱状图）")
