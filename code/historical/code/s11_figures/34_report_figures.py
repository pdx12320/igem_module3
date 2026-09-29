# -*- coding: utf-8 -*-
"""
阶段 34 —— 汇报用图（6 张，供 PPT/报告直接插入）
图1 单点突变全景（+1比 vs 保留率）
图2 组合突变 Pareto 前沿（比 vs 保留）
图3 总体脱靶负荷对比（亲本 vs 各组合）
图4 GCG 靶向比 vs 活性（WT 基线）
图5 D 组控制变量实验布局示意（58 配对 / 132 三元组）
图6 下一轮 41 组候选总览
产出：results/figs/fig1..fig6*.png
"""
import csv, os, re, sys, statistics
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
os.makedirs("results/figs", exist_ok=True)

NAVY = "#1F3B66"; BLUE = "#2E548B"; ACC = "#B44A3C"; TEAL = "#1B6B5A"
GREEN = "#1E7A46"; GRAY = "#606060"; LIGHT = "#F2F4F8"; GOLD = "#C9A227"

# ============ 数据 ============
singles = []
for r in csv.DictReader(open("results/experimental_ranking.csv", encoding="utf-8-sig")):
    m = re.match(r'(\d+)([A-Z])$', r["mut"])
    if not m: continue
    singles.append(dict(mut=r["mut"], resi=int(m.group(1)), ratio=float(r["ratio"]),
                        retain=float(r["retain"]),
                        c388=float(r["GCG"]), c871=float(r["GCA"]),
                        active=r["active"] == "True"))

combo = []
for r in csv.DictReader(open("results/offtarget_screen_final.csv", encoding="utf-8-sig")):
    combo.append(dict(mut=r["mutant"], on=float(r["on_388"]), n_off=float(r["n_off"]),
                      load=float(r["off_load_sum"]), norm=float(r["norm_load"]),
                      S=float(r["S_global"])))

gcg = []
for r in csv.DictReader(open("results/GCG_vs_off_ranking_WT.csv", encoding="utf-8-sig")):
    try:
        gcg.append(dict(mut=r["mutation"], ratio=float(r["targeting_ratio"]),
                        act=float(r["activity_retention"]), is_wt=r["is_WT"] == "True",
                        sg=float(r["sum_GCG_pct"]), so=float(r["sum_nonGCG_pct"])))
    except ValueError:
        continue

# ============================================================
# 图1 单点突变全景
# ============================================================
fig, ax = plt.subplots(figsize=(11, 7), dpi=200)
act = [s for s in singles if s["active"]]
ina = [s for s in singles if not s["active"]]
ax.scatter([s["retain"]*100 for s in ina], [s["ratio"] for s in ina],
           s=42, c="#C8C8C8", edgecolors="#909090", linewidths=.5, label=f"保留<60%（{len(ina)} 个，不可用）", zorder=2)
ax.scatter([s["retain"]*100 for s in act], [s["ratio"] for s in act],
           s=70, c=BLUE, edgecolors="white", linewidths=.8, label=f"保留≥60%（{len(act)} 个，可用）", zorder=3)
ax.axhline(2.0, ls="--", c=ACC, lw=1.3)
ax.text(3, 2.03, "单点天花板未突破线（+1比 = 2.0）", color=ACC, fontsize=9)
ax.axvline(60, ls=":", c=GREEN, lw=1.2)
ax.text(61, 2.9, "保留率 60% 门槛", color=GREEN, fontsize=9, rotation=90, va="top")
for k, s in enumerate(sorted(act, key=lambda x: -x["ratio"])[:8]):
    dx, dy = [(6, 5), (6, -12), (6, 5), (6, -12), (-24, 5), (6, -12), (6, 5), (6, -12)][k % 8]
    ax.annotate(s["mut"], (s["retain"]*100, s["ratio"]), textcoords="offset points",
                xytext=(dx, dy), fontsize=8.5, color=NAVY, fontweight="bold")
ax.set_xlabel("on-target 保留率 %（相对 WT）", fontsize=12)
ax.set_ylabel("＋1 比（GCG/GCA）", fontsize=12)
ax.set_title(f"图1　单点饱和突变全景（{len(singles)} 个突变，16 个位点）\n"
             f"保留≥60% 的最优单点 = {max(act, key=lambda x: x['ratio'])['mut']}"
             f"（比 {max(act, key=lambda x: x['ratio'])['ratio']:.2f}）—— 无一突破 2.0",
             fontsize=12.5, pad=12)
ax.legend(loc="upper right", fontsize=9.5); ax.grid(alpha=.25)
ax.set_ylim(0.8, 3.2)
fig.tight_layout(); fig.savefig("results/figs/fig1_单点突变全景.png"); plt.close(fig)
print("图1 完成")

# ============================================================
# 图2 组合突变 Pareto 前沿
# ============================================================
fig, ax = plt.subplots(figsize=(11, 7), dpi=200)
big = [c for c in combo if c["on"] >= 0.30]
small = [c for c in combo if c["on"] < 0.30]
ax.scatter([c["on"]*100 for c in small], [c["norm"] for c in small],
           s=40, c="#D8D8D8", edgecolors="#A0A0A0", linewidths=.4,
           label=f"活性不足（on<30%，{len(small)} 组，脱靶被检出下限截断）", zorder=2)
ax.scatter([c["on"]*100 for c in big], [c["norm"] for c in big],
           s=75, c=BLUE, edgecolors="white", linewidths=.8, label=f"活性可用（on≥30%，{len(big)} 组）", zorder=3)
# 标注有效候选
lab = ["27T-30H-58M","27T-32F","30H-58M","32F-132E","25E-27D","32F-58M","PUF12-9","27T-58M","25E-58M","32F"]
for c in big:
    if c["mut"] in lab:
        col = ACC if c["mut"] == "27T-30H-58M" else (GRAY if c["mut"] == "PUF12-9" else NAVY)
        ax.annotate(c["mut"], (c["on"]*100, c["norm"]), textcoords="offset points",
                    xytext=(6, 4), fontsize=8.5, color=col,
                    fontweight="bold" if c["mut"] in ("27T-30H-58M","PUF12-9") else "normal")
ax.axhline(16.14, ls="--", c=GRAY, lw=1.2)
ax.text(52, 16.5, "亲本 PUF12-9 水平（归一化脱靶负荷 16.1）", color=GRAY, fontsize=9, ha="right")
ax.axvline(30, ls=":", c=ACC, lw=1.2)
ax.set_xlabel("on-target 编辑效率 C388 %", fontsize=12)
ax.set_ylabel("归一化脱靶负荷  Σoff / on（越低越特异）", fontsize=12)
ax.set_title("图2　组合突变体：活性 vs 全局脱靶负荷\n左下角 = 高活性 + 高特异性；最佳平衡点为 27T-30H-58M",
             fontsize=12.5, pad=12)
ax.legend(loc="upper left", fontsize=9.5); ax.grid(alpha=.25)
ax.set_ylim(-0.5, 19)
fig.tight_layout(); fig.savefig("results/figs/fig2_组合Pareto前沿.png"); plt.close(fig)
print("图2 完成")

# ============================================================
# 图3 总体脱靶负荷对比（脱靶位点数 + 负荷）
# ============================================================
show = ["PUF12-9","25E-58M","32F","32F-58M","27T-58M","58M-132E","30H-58M","27T-32F-132E","27T-30H-58M","32F-132E","25E-27D"]
d = {c["mut"]: c for c in combo}
show = [m for m in show if m in d]
show = sorted(show, key=lambda m: d[m]["load"])
fig, axes = plt.subplots(1, 2, figsize=(14, 6.6), dpi=200)
ax = axes[0]
cols = [ACC if m == "PUF12-9" else (GREEN if m == "27T-30H-58M" else BLUE) for m in show]
ax.barh(range(len(show)), [d[m]["load"] for m in show], color=cols)
ax.set_yticks(range(len(show))); ax.set_yticklabels(show, fontsize=9.5)
for i, m in enumerate(show):
    ax.text(d[m]["load"]+0.15, i, f'{d[m]["load"]:.2f}', va="center", fontsize=8.5)
ax.set_xlabel("脱靶负荷 Σoff（全部非靶点 C→T 频率之和，%）", fontsize=11)
ax.set_title("(a) 总体脱靶负荷", fontsize=12)
ax.grid(alpha=.25, axis="x")
ax = axes[1]
ax.barh(range(len(show)), [d[m]["n_off"] for m in show], color=cols)
ax.set_yticks(range(len(show))); ax.set_yticklabels([""]*len(show))
for i, m in enumerate(show):
    ax.text(d[m]["n_off"]+0.6, i, f'{d[m]["n_off"]:.0f}', va="center", fontsize=8.5)
ax.set_xlabel("检出脱靶位点数（C→T，freq ≥5%）", fontsize=11)
ax.set_title("(b) 脱靶位点数量", fontsize=12)
ax.grid(alpha=.25, axis="x")
fig.suptitle("图3　组合突变体的总体脱靶对比（红=亲本，绿=最佳候选 27T-30H-58M）", fontsize=13, y=0.98)
fig.tight_layout(); fig.savefig("results/figs/fig3_总体脱靶负荷.png"); plt.close(fig)
print("图3 完成")

# ============================================================
# 图4 GCG 靶向比 vs 活性
# ============================================================
fig, ax = plt.subplots(figsize=(11, 7), dpi=200)
wt = next((g for g in gcg if g["is_wt"]), None)
for g in gcg:
    if g["is_wt"]:
        ax.scatter(g["sg"], g["so"], marker="*", s=420, c=GREEN,
                   edgecolors="white", linewidths=1.2, zorder=5, label="WT (PUF12-9) 基线")
    else:
        c = ACC if g["mut"] == "27T-30H-58M" else BLUE
        s = 150 if g["mut"] == "27T-30H-58M" else 45
        ax.scatter(g["sg"], g["so"], s=s, c=c, edgecolors="white", linewidths=.7, zorder=3)
        if g["mut"] in ("27T-30H-58M","30H-58M","25E-32F","32F","25E-58M","32F-58M","27T-58M","PUF12-9"):
            ax.annotate(g["mut"], (g["sg"], g["so"]), textcoords="offset points",
                        xytext=(6, 4), fontsize=8.5,
                        color=ACC if g["mut"] == "27T-30H-58M" else NAVY,
                        fontweight="bold" if g["mut"] == "27T-30H-58M" else "normal")
if wt:
    lim = max(wt["sg"], wt["so"]) * 1.15
    ax.plot([0, lim], [0, lim], "--", c=GRAY, lw=1.2)
    ax.text(lim*0.60, lim*0.66, "Σ_GCG = Σ_非GCG（等比例线）", fontsize=9, color=GRAY, rotation=34)
    ax.scatter([], [], marker="s", s=0, label=f"WT 靶向比 {wt['ratio']:.2f}")
ax.set_xlabel("GCG 靶点编辑总和 Σ_gcg %", fontsize=12)
ax.set_ylabel("非 GCG（脱靶）编辑总和 Σ_off %", fontsize=12)
ax.set_title("图4　以「全部 GCG 为靶点」的靶向偏好\n"
             "对角线上方 = 编辑偏向 GCG 靶点；WT 位于对角线上（比 0.93）", fontsize=12.5, pad=12)
ax.legend(loc="lower right", fontsize=10); ax.grid(alpha=.25)
fig.tight_layout(); fig.savefig("results/figs/fig4_GCG靶向偏好.png"); plt.close(fig)
print("图4 完成")

# ============================================================
# 图5 D 组控制变量实验布局示意
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(15, 6.8), dpi=200)
# 左：58 配对
ax = axes[0]; ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
ax.set_title("(a) Q58M 保护效应：同背景 ±58M 配对（7 对）", fontsize=12.5, pad=8)
pairs = [("G27T+K30H", "D01", "C13"), ("G27D+K30H", "C14", "C27"), ("G25E+K30H", "C18", "C28"),
         ("G27D", "C04", "C17"), ("G27T", "C05", "C16"), ("K30H", "C02", "C15"), ("I26N", "C10", "C36")]
ax.text(2.2, 9.4, "无 58M", fontsize=11, fontweight="bold", color=BLUE, ha="center")
ax.text(7.6, 9.4, "+ Q58M", fontsize=11, fontweight="bold", color=GREEN, ha="center")
for i, (bg, a, b) in enumerate(pairs):
    y = 8.6 - i * 1.15
    hl = (bg == "G27T+K30H")
    ax.add_patch(FancyBboxPatch((0.2, y-0.35), 4.0, 0.7, boxstyle="round,pad=0.06",
                                fc="#FFF4CC" if hl else LIGHT, ec=GOLD if hl else "#CCCCCC", lw=1.6 if hl else 1))
    ax.text(2.2, y, f"{bg}   [{a}]", fontsize=9, ha="center", va="center",
            color=NAVY, fontweight="bold" if hl else "normal")
    ax.add_patch(FancyBboxPatch((5.6, y-0.35), 4.0, 0.7, boxstyle="round,pad=0.06",
                                fc="#FFF4CC" if hl else "#E6F4EA", ec=GOLD if hl else GREEN, lw=1.6 if hl else 1))
    ax.text(7.6, y, f"+Q58M   [{b}]", fontsize=9, ha="center", va="center",
            color=NAVY, fontweight="bold" if hl else "normal")
    ax.annotate("", xy=(5.5, y), xytext=(4.3, y),
                arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.1))
ax.text(5.0, 0.2, "唯一变量 = 58 位；配对差值 = Q58M 净效应（Δ保留率 / Δ比）",
        fontsize=9.5, ha="center", color=TEAL, style="italic")
# 右：132 三元组
ax = axes[1]; ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
ax.set_title("(b) M132D 破坏效应：同背景三元组（无 / D / E，2 组背景）", fontsize=12.5, pad=8)
tris = [("G27T+K30H+Q58M", "C13", "D02", "D03"), ("G25E+K30H+Q58M", "C28", "D04", "D05")]
xs = [1.7, 4.5, 7.6]; labs = ["无 132", "+M132D", "+M132E"]
for i, (bg, a, b, c) in enumerate(tris):
    y = 7.4 - i * 3.2
    ax.text(5.0, y + 0.95, bg, fontsize=10, ha="center", fontweight="bold", color=NAVY)
    for x, lb, cid, col in zip(xs, labs, [a, b, c], [BLUE, ACC, GREEN]):
        ax.add_patch(FancyBboxPatch((x-1.25, y-0.45), 2.5, 0.9, boxstyle="round,pad=0.07",
                                    fc=col, ec=col, lw=1))
        ax.text(x, y+0.12, lb, fontsize=9.5, ha="center", va="center", color="white", fontweight="bold")
        ax.text(x, y-0.62, f"[{cid}]", fontsize=8.5, ha="center", va="center", color=GRAY)
    ax.annotate("", xy=(6.3, y), xytext=(5.8, y), arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.1))
    ax.annotate("", xy=(3.2, y), xytext=(2.7, y), arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.1))
ax.text(5.0, 0.5, "唯一变量 = 132 位残基身份；若 D 臂活性显著最低 → 证实 D 特有破坏性\n"
                  "（若 D、E 均低 → 则是出口轴位置本身不耐受）",
        fontsize=9.5, ha="center", color=TEAL, style="italic")
fig.suptitle("图5　D 组控制变量实验布局（解决「132/58 效应无干净对照」）", fontsize=13.5, y=0.99)
fig.tight_layout(); fig.savefig("results/figs/fig5_D组控制变量布局.png"); plt.close(fig)
print("图5 完成")

# ============================================================
# 图6 下一轮 41 组候选总览
# ============================================================
GROUPS = {
 "A 复验（18）": [("C01","WT","必做"),("C02","K30H","P0"),("C03","G25E","P1"),("C04","G27D","P0"),
   ("C05","G27T","P1"),("C06","Q58M","P0"),("C07","M132D","P1"),("C08","M132E","P1"),
   ("C09","Y32F","P1"),("C10","I26N","P2"),("C11","A59S","P2"),("C12","W129Y","P2"),
   ("C13","27T-30H-58M","P0★"),("C14","27D-30H","P1"),("C15","30H-58M","P1"),
   ("C16","27T-58M","P2"),("C17","27D-58M","P2"),("C18","25E-30H","P1")],
 "B 新候选单点（6）": [("C19","R28A","P0★"),("C20","R28S","P1"),("C21","T31V","P1"),
   ("C22","A59P","P2"),("C23","K60R","P2"),("C24","H29N","P2")],
 "C 新候选组合（12）": [("C25","26N+K30H","P0★"),("C26","30H+59S","P1"),("C27","27D-30H-58M","P0★"),
   ("C28","25E-30H-58M","P1"),("C29","R28A+K30H","P1"),("C30","T31A+K30H","P1"),
   ("C31","27D-30H-32F-58M","P1"),("C32","26N+K30H+58M","P1"),("C33","R28A+58M","P2"),
   ("C34","R28A+K30H+58M","P1"),("C35","32F-132E-58M","P1"),("C36","26N+58M","P2")],
 "D 控制变量组（5）": [("D01","27T-30H（-58M）","P0"),("D02","27T-30H-58M+132D","P0"),
   ("D03","27T-30H-58M+132E","P0"),("D04","25E-30H-58M+132D","P1"),("D05","25E-30H-58M+132E","P1")],
}
fig, ax = plt.subplots(figsize=(15, 8.2), dpi=200)
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
COL = {"A 复验（18）": "#DCE7F5", "B 新候选单点（6）": "#FBE3D8",
       "C 新候选组合（12）": "#F7D9D3", "D 控制变量组（5）": "#D9EFDF"}
EC = {"A 复验（18）": BLUE, "B 新候选单点（6）": "#D97B4A",
      "C 新候选组合（12）": ACC, "D 控制变量组（5）": GREEN}
y0 = 9.2
COLS = {"A 复验（18）": 6, "B 新候选单点（6）": 6, "C 新候选组合（12）": 6, "D 控制变量组（5）": 3}
for gname, items in GROUPS.items():
    n = len(items); cols = COLS[gname]; rows = (n + cols - 1) // cols
    h = rows * 0.62 + 0.75
    step = 9.4 / cols
    ax.add_patch(FancyBboxPatch((0.12, y0 - h), 9.76, h, boxstyle="round,pad=0.08",
                                fc=COL[gname], ec=EC[gname], lw=1.6, alpha=.55))
    ax.text(0.45, y0 - 0.32, gname, fontsize=12, fontweight="bold", color=EC[gname], va="center")
    for k, (cid, mut, pri) in enumerate(items):
        r, c = divmod(k, cols)
        x = 0.42 + c * step; y = y0 - 0.95 - r * 0.62
        star = "★" if "★" in pri else ""
        ax.text(x, y, f"{cid}", fontsize=7.5, color=GRAY, va="center")
        ax.text(x + 0.40, y, mut, fontsize=8.5, color=NAVY, va="center",
                fontweight="bold" if star else "normal")
        pc = ACC if "P0" in pri else (GOLD if "P1" in pri else GRAY)
        # 动态偏移：按名称长度推进，避免与优先级标签相撞
        off = 0.40 + len(mut) * 0.062 + 0.10
        ax.text(x + off, y, pri.replace("★", "") + star, fontsize=7.5, color=pc, va="center")
    y0 -= (h + 0.22)
ax.text(5.0, 0.28, "共 41 组（新构建体 23 组）｜★ = P0 优先解读｜D 组为控制变量验证（132 破坏 / 58 保护）",
        fontsize=10.5, ha="center", color=TEAL, fontweight="bold")
ax.set_title("图6　下一轮实验 41 组候选总览", fontsize=14.5, pad=10)
fig.tight_layout(); fig.savefig("results/figs/fig6_候选总览.png"); plt.close(fig)
print("图6 完成")

print("\n全部图已写入 results/figs/")
for f in sorted(os.listdir("results/figs")):
    print("  ", f, f"{os.path.getsize('results/figs/'+f)//1024} KB")
