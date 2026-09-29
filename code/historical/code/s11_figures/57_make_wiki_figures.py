# -*- coding: utf-8 -*-
"""
57_make_wiki_figures.py —— 生成 iGEM wiki 展示级图表

产出到 文案数据图表整理/图表/：
  wiki_fig1_DBTL总流程.png      五循环总览流程图（干/湿分色 + 迭代回路）
  wiki_fig2_Cycle1_单点天花板.png
  wiki_fig3_Cycle2_组合突破.png
  wiki_fig4_Cycle3_指标偏倚.png
  wiki_fig5_Cycle4_阴性对照.png
  wiki_fig6_Cycle5_方法回溯.png
  wiki_fig0_项目总览.png        一页纸关键数字

用法：uv run --with matplotlib --with numpy --with pydssp python 57_make_wiki_figures.py
"""
import os, sys, csv, math, re
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
from collections import OrderedDict, Counter

OUT = os.path.join("文案数据图表整理", "图表")
os.makedirs(OUT, exist_ok=True)
DPI = 300

# ===========================================================================
# 统一视觉规范
# ===========================================================================
NAVY = "#1F3B66"
BLUE = "#2E548B"
SKY = "#5B8FC9"
LBLUE = "#D6E4F7"
ACC = "#B44A3C"
LACC = "#F5D9D4"
GREEN = "#1E7A46"
LGREEN = "#D6EBDD"
TEAL = "#1B6B5A"
GOLD = "#C8912A"
LGOLD = "#F7EBD2"
GRAY = "#404040"
LGRAY = "#8C8C8C"
BG = "#F7F9FC"
WHITE = "#FFFFFF"

plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "figure.facecolor": WHITE,
    "axes.facecolor": WHITE,
    "axes.edgecolor": "#C9D3E0",
    "axes.linewidth": 0.9,
    "axes.labelcolor": GRAY,
    "axes.titlecolor": NAVY,
    "xtick.color": GRAY, "ytick.color": GRAY,
    "xtick.labelsize": 10, "ytick.labelsize": 10,
    "axes.labelsize": 11.5,
    "axes.titlesize": 13,
    "legend.fontsize": 10,
    "legend.frameon": False,
    "grid.color": "#E3E9F2", "grid.linewidth": 0.8,
    "savefig.dpi": DPI, "savefig.bbox": "tight", "savefig.pad_inches": 0.25,
})


def style_ax(ax, grid="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if grid:
        ax.set_axisbelow(True)
        ax.grid(axis=grid, alpha=1.0)


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p)
    plt.close(fig)
    print(f"  写入 {p}")


def rd(path, **kw):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, **kw))


def fnum(x, d=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ===========================================================================
# fig1 —— DBTL 总流程图
# ===========================================================================
CYCLES = [
    ("Cycle 1", "单点饱和\n可行性验证",
     "AF3 三底物解耦建模\n接触类型分解\n保守性 / PSSM",
     "102 个单点突变质粒\nPCR 线性化 + 同源重组",
     "扩增子深度测序\nc.388 / c.871 / c.295",
     "天花板 1.71，无一达 2.0\n+1 位无 GCG 特异侧链读取元件\n→ 单点路线关闭"),
    ("Cycle 2", "组合突变\n突破天花板",
     "以证实单点为骨架\n三条组合规则\nROF 归一化口径",
     "50 个组合构建体\n双点 / 三点",
     "同批转染与测序\n位点边际效应分析",
     "G27T-K30H-Q58M = 2.16 / 77%\n唯一双达标\n→ 但高比与高活性不可兼得"),
    ("Cycle 3", "全局脱靶评估\n重定义「好」",
     "全扩增子观察窗口\n定义 targeting_ratio\n951 bp / 291 个 C 位点",
     "57 个构建体深度测序\n117 个样本\nP 域变体 P4–P8",
     "脱靶位点 / 负荷统计\n新增脱靶位点\n转录组重分析",
     "7 组脱靶完全清除但活性 <22%\nP 域引入 19 个新脱靶\n→ 指标本身被检测下限混淆"),
    ("Cycle 4", "结构复核\n检验隐含假设",
     "阴性对照设计\nWT-only 白化基 D_M\n纯蛋白对照",
     "7 个对照构建体\n65 个 AF3 建模任务",
     "D_M 零假设 95 分位 = 1.57\n复合物 vs 纯蛋白",
     "E72A（必然失活）D_M 全场最低\nWT 只换底物 > T31D\n→ CP 编码的是「哪条 RNA」"),
    ("Cycle 5", "方法回溯检验\n（进行中）",
     "top-N 回收率重评价\n监督学习\nAiCE β/γ 回溯检验",
     "48 条 MPNN 采样重分析\npydssp 二级结构\n61 条候选设计",
     "三种过滤口径的\n精确率 / 召回率\n与湿实验对照",
     "β/γ 一个都没剔除\n且漏掉全部有效突变\n→ 高约束设计 + 小规模验证"),
]

fig = plt.figure(figsize=(19.5, 12.4))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

ax.add_patch(Rectangle((0, 93.5), 100, 6.5, color=NAVY, zorder=1))
ax.text(2.2, 96.7, "Orca 系统 · APOBEC 编辑模块 —— DBTL 工程循环", fontsize=21,
        color=WHITE, va="center", fontweight="bold")
ax.text(97.8, 96.7, "Design · Build · Test · Learn  ×5", fontsize=13,
        color="#AFC6E4", va="center", ha="right")

# 阶段表头
HDR = ["设计  Design", "构建  Build", "测试  Test", "学习  Learn"]
COLX = [21.5, 39.5, 57.5, 76.5]
CW = 16.4
for x, h in zip(COLX, HDR):
    ax.add_patch(FancyBboxPatch((x - CW / 2, 88.4), CW, 3.4,
                                boxstyle="round,pad=0.18,rounding_size=0.6",
                                fc=LBLUE if h.startswith("设计") or h.startswith("学习") else LGREEN,
                                ec="none", zorder=2))
    ax.text(x, 90.1, h, ha="center", va="center", fontsize=12.5, color=NAVY, fontweight="bold")

ROWY = [78.5, 62.5, 46.5, 30.5, 14.5]
RH = 12.2
DRY = {0, 3}          # 设计与学习 = 干（计算）
WET = {1, 2}          # 构建与测试 = 湿

for i, (num, sub, d, b, t, l) in enumerate(CYCLES):
    y = ROWY[i]
    # 行底
    ax.add_patch(FancyBboxPatch((1.0, y - RH / 2 + 0.4), 97.6, RH,
                                boxstyle="round,pad=0.2,rounding_size=0.9",
                                fc=BG, ec="#DCE4EF", lw=1.0, zorder=1))
    # 左侧 cycle 标
    ax.text(4.6, y + 2.5, num, fontsize=15, color=NAVY, fontweight="bold", va="center")
    ax.text(4.6, y - 1.8, sub, fontsize=10.5, color=LGRAY, va="center", linespacing=1.5)
    # 四个阶段框
    for j, txt in enumerate([d, b, t, l]):
        x = COLX[j]
        is_dry = j in DRY
        fc = WHITE
        ec = BLUE if is_dry else GREEN
        ax.add_patch(FancyBboxPatch((x - CW / 2, y - RH / 2 + 0.9), CW, RH - 1.0,
                                    boxstyle="round,pad=0.15,rounding_size=0.5",
                                    fc=fc, ec=ec, lw=1.6, zorder=3))
        ax.text(x, y, txt, ha="center", va="center", fontsize=9.4, color=GRAY,
                linespacing=1.75, zorder=4)
    # 阶段间箭头
    for j in range(3):
        x0 = COLX[j] + CW / 2 + 0.35
        x1 = COLX[j + 1] - CW / 2 - 0.35
        ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>",
                                     mutation_scale=13, color="#9DB3CC", lw=1.6, zorder=4))
    # 迭代回路：Learn → 下一行 Design（走两行之间的空隙，不压文字）
    if i < len(CYCLES) - 1:
        y0 = y - RH / 2 + 0.4                       # 本行底边
        y1 = ROWY[i + 1] + RH / 2 + 0.4             # 下一行顶边
        ym = (y0 + y1) / 2
        ax.plot([COLX[3], COLX[3], COLX[0]], [y0, ym, ym], color=ACC, lw=2.0,
                ls=(0, (5, 3)), zorder=5, solid_capstyle="round")
        ax.add_patch(FancyArrowPatch((COLX[0], ym), (COLX[0], y1), arrowstyle="-|>",
                                     mutation_scale=15, color=ACC, lw=2.0, zorder=5))
        ax.text((COLX[0] + COLX[3]) / 2, ym, "迭代  Iterate", ha="center", va="center",
                fontsize=9.8, color=ACC, fontweight="bold", zorder=6,
                bbox=dict(boxstyle="round,pad=0.28", fc=WHITE, ec=ACC, lw=0.9))

ax.legend(handles=[Line2D([], [], marker="s", ls="", ms=13, mfc=WHITE, mec=BLUE, mew=1.8,
                          label="干实验 / Dry (in silico)"),
                   Line2D([], [], marker="s", ls="", ms=13, mfc=WHITE, mec=GREEN, mew=1.8,
                          label="湿实验 / Wet (bench)"),
                   Line2D([], [], color=ACC, lw=2.1, ls=(0, (5, 3)),
                          label="迭代回路 / Iteration")],
          loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.002), fontsize=11.5)
save(fig, "wiki_fig1_DBTL总流程.png")

# ===========================================================================
# fig2 —— Cycle 1：单点天花板
# ===========================================================================
rows = [r for r in rd("results/experimental_ranking.csv") if "PUF" not in r["mut"]]
X = np.array([[fnum(r["ratio"]), fnum(r["retain"])] for r in rows if fnum(r["ratio"])])
fig, ax = plt.subplots(figsize=(10.6, 7.2))
act = X[:, 1] >= 0.70
ax.axhline(0.70, color=GREEN, ls="--", lw=1.6, zorder=1)
ax.axvline(2.00, color=ACC, ls="--", lw=1.6, zorder=1)
ax.axvline(1.371, color=LGRAY, ls=":", lw=1.5, zorder=1)
ax.scatter(X[~act, 0], X[~act, 1], s=48, c="#C9D3E0", ec="none", label="活性未达标 (保留<0.70)", zorder=2)
ax.scatter(X[act, 0], X[act, 1], s=62, c=SKY, ec="none", label="活性达标 (保留≥0.70)", zorder=3)
HL = {"30H": (6, 8), "25E": (-30, 8), "27D": (-34, -16), "58M": (6, -14),
      "27T": (-32, 6), "26N": (6, -14), "132D": (6, 6), "60Q": (6, 6), "130G": (6, 6)}
for r in rows:
    if r["mut"] in HL and fnum(r["ratio"]):
        dx, dy = HL[r["mut"]]
        ax.annotate(r["mut"], (fnum(r["ratio"]), fnum(r["retain"])), fontsize=10,
                    color=ACC if fnum(r["retain"]) < 0.70 else NAVY, fontweight="bold",
                    xytext=(dx, dy), textcoords="offset points", zorder=5)
ax.annotate("", xy=(1.71, 0.84), xytext=(1.30, 0.55),
            arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.8))
ax.text(1.245, 0.50, "单点天花板 1.71\n(K30H)", fontsize=11, color=ACC,
        fontweight="bold", ha="left", linespacing=1.5)
ax.text(2.02, 0.10, "目标线 +1比 = 2.0\n无人达到", fontsize=10.5, color=ACC,
        ha="left", linespacing=1.5)
ax.text(1.375, 0.06, "亲本 1.371", fontsize=10, color=LGRAY, rotation=90, va="bottom")
ax.set_xlabel("+1 比  (+1 ratio = GCG / GCA)"); ax.set_ylabel("活性保留  (activity retention)")
ax.set_title("Cycle 1 · 102 个单点突变：活性的代价与比值的上限", pad=14)
ax.set_xlim(0.6, 3.4); ax.set_ylim(-0.05, 1.12)
style_ax(ax); ax.legend(loc="upper right")
save(fig, "wiki_fig2_Cycle1_单点天花板.png")

# ===========================================================================
# fig3 —— Cycle 2：组合突破 + Pareto
# ===========================================================================
cb = [r for r in rd("results/23_combo_master_table.csv") if fnum(r["ratio_p1"])]
cx = np.array([[fnum(r["ratio_p1"]), fnum(r["retain_vs_parent"])] for r in cb])
fig, ax = plt.subplots(figsize=(11.2, 7.2))
front, best = [], -1
for x_, y_ in sorted(zip(cx[:, 0], cx[:, 1]), reverse=True):
    if y_ > best:
        front.append((x_, y_)); best = y_
if front:
    fx, fy = zip(*front)
    ax.plot(fx, fy, color=GOLD, lw=2.2, ls="--", zorder=2, label="Pareto 前沿")
ax.scatter(cx[:, 0], cx[:, 1], s=64, c=LBLUE, ec=BLUE, lw=1.1, zorder=3,
           label="组合构建体 (n=50)")
ax.axhline(0.70, color=GREEN, ls="--", lw=1.5, zorder=1)
ax.axvline(2.00, color=ACC, ls="--", lw=1.5, zorder=1)
BEST = "27T-30H-58M"
key = {BEST: (10, 6), "58M-130G": (8, 5), "27D-30H-32F": (-12, -18),
       "32F-132E": (8, 5), "27T-32F-132D": (8, -14)}
for r in cb:
    if r["muts"] in key:
        ax.annotate(r["muts"].replace("-", "·"), (fnum(r["ratio_p1"]), fnum(r["retain_vs_parent"])),
                    fontsize=9.8, color=ACC if r["muts"] == BEST else GRAY,
                    fontweight="bold" if r["muts"] == BEST else "normal",
                    xytext=key[r["muts"]], textcoords="offset points", zorder=6)
star = [r for r in cb if r["muts"] == BEST][0]
ax.scatter([fnum(star["ratio_p1"])], [fnum(star["retain_vs_parent"])], s=290,
           marker="*", c=GOLD, ec=ACC, lw=1.4, zorder=7)
ax.set_xlabel("+1 比  (+1 ratio)"); ax.set_ylabel("活性保留  (vs 组合批亲本)")
ax.set_title("Cycle 2 · 组合突变突破单点天花板（但高比与高活性不可兼得）", pad=14)
style_ax(ax); ax.set_xlim(0.8, 4.1); ax.set_ylim(-0.05, 1.0); ax.legend(loc="upper right")
save(fig, "wiki_fig3_Cycle2_组合突破.png")

# ===========================================================================
# fig4 —— Cycle 3：指标偏倚（两块）
# ===========================================================================
from scipy import stats as _st

g = [r for r in rd("results/GCG_vs_off_ranking_WT.csv") if r["is_WT"] != "True"]
fin = [r for r in g if fnum(r["targeting_ratio"]) is not None
       and math.isfinite(fnum(r["targeting_ratio"]))]
n_inf = len(g) - len(fin)
c388 = np.array([fnum(r["C388_pct"]) for r in fin])
targ = np.array([fnum(r["targeting_ratio"]) for r in fin])
off = np.array([fnum(r["sum_nonGCG_pct"]) for r in fin])
r_p = np.corrcoef(off, targ)[0, 1]; r_s = _st.spearmanr(off, targ)[0]
c_p = np.corrcoef(c388, off)[0, 1]; c_s = _st.spearmanr(c388, off)[0]
YMAX = 7.0

fig, axes = plt.subplots(1, 2, figsize=(15.0, 6.8))
ax = axes[0]
for lo_, hi_, col, lab in [(10, 20, ACC, "低活性层"), (35, 60, GREEN, "高活性层")]:
    m = (c388 >= lo_) & (c388 <= hi_)
    ax.axvspan(lo_, hi_, color=col, alpha=0.10, zorder=1)
    ax.plot([lo_, hi_], [np.median(targ[m])] * 2, color=col, lw=3.4,
            solid_capstyle="butt", zorder=4)
    ax.text((lo_ + hi_) / 2, np.median(targ[m]) + 0.28,
            f"{lab}（{lo_}–{hi_}%）\nn={m.sum()}，中位 {np.median(targ[m]):.2f}",
            ha="center", fontsize=10.2, color=col, fontweight="bold",
            linespacing=1.5, zorder=5)
ax.scatter(c388, targ, s=72, c=LBLUE, ec=BLUE, lw=1.0, zorder=3)
ax.axhline(1.0, color=LGRAY, ls=":", lw=1.4, zorder=2)
ax.text(0.985, 0.04, f"{n_inf} 组比值 = ∞（分母塌缩），未绘入",
        transform=ax.transAxes, ha="right", fontsize=10.2, color=ACC,
        fontweight="bold", zorder=6,
        bbox=dict(boxstyle="round,pad=0.4", fc=LACC, ec=ACC, lw=1.0))
ax.set_xlabel("on-target 编辑率  C388 (%)")
ax.set_ylabel("靶向比  targeting_ratio")
ax.set_title("① 靶向比随活性下降而虚高", pad=12)
ax.set_ylim(-0.35, YMAX); style_ax(ax, grid="both")

ax = axes[1]
ax.scatter(off, targ, s=72, c=LBLUE, ec=BLUE, lw=1.0, zorder=3)
z = np.polyfit(off, targ, 1); xs = np.linspace(off.min(), off.max(), 60)
ax.plot(xs, np.polyval(z, xs), color=ACC, lw=2.1, ls="--", zorder=2,
        label=f"线性拟合")
ax.text(0.035, 0.965, f"targeting_ratio vs Σ非GCG\nPearson r = {r_p:+.3f}\nSpearman ρ = {r_s:+.3f}",
        transform=ax.transAxes, fontsize=11.5, color=ACC, fontweight="bold",
        va="top", linespacing=1.65,
        bbox=dict(boxstyle="round,pad=0.55", fc=LACC, ec=ACC, lw=1.2))
ax.text(0.035, 0.60, f"C388% vs Σ非GCG%\nPearson r = {c_p:+.3f}\nSpearman ρ = {c_s:+.3f}",
        transform=ax.transAxes, fontsize=11.5, color=NAVY, fontweight="bold",
        va="top", linespacing=1.65,
        bbox=dict(boxstyle="round,pad=0.55", fc=LBLUE, ec=BLUE, lw=1.2))
ax.set_xlabel("Σ 非 GCG 编辑率 (%)")
ax.set_ylabel("靶向比  targeting_ratio")
ax.set_title("② 分母驱动：脱靶总量越小，比值越高", pad=12)
ax.set_ylim(-0.35, YMAX); style_ax(ax, grid="both")
fig.suptitle(f"Cycle 3 · 靶向比被 5% 检测下限混淆（n={len(fin)} 个有限比值样本）",
             fontsize=14.5, color=NAVY, y=1.005, fontweight="bold")
save(fig, "wiki_fig4_Cycle3_指标偏倚.png")

# ===========================================================================
# fig5 —— Cycle 4：阴性对照 D_M
# ===========================================================================
dm = rd("results/阴性对照_DM.csv")
dm = sorted(dm, key=lambda r: -fnum(r["D_M"]))
names = [r["construct"] for r in dm]; vals = [fnum(r["D_M"]) for r in dm]
cls = [r["functional_class"] for r in dm]
COL = {"完全失活": ACC, "有活性": GREEN, "部分失活": GOLD, "未测": "#B9C4D2",
       "WT（GCA 底物）": "#7B4FA8"}
cols = [COL.get(c, "#B9C4D2") for c in cls]
fig, ax = plt.subplots(figsize=(11.2, 9.2))
y = np.arange(len(names))[::-1]
ax.barh(y, vals, color=cols, height=0.72, zorder=3)
ax.axvline(1.57, color=NAVY, ls="--", lw=1.8, zorder=2)
ax.text(1.62, len(names) - 0.6, "WT seed 零假设 95 分位 = 1.57",
        fontsize=10.5, color=NAVY, fontweight="bold")
for yy, v, n in zip(y, vals, names):
    ax.text(v + 0.13, yy, f"{v:.2f}", va="center", fontsize=9.3, color=GRAY)
ax.set_yticks(y); ax.set_yticklabels(names, fontsize=10)
for t, c in zip(ax.get_yticklabels(), cls):
    if c == "完全失活": t.set_color(ACC); t.set_fontweight("bold")
    elif c == "WT（GCA 底物）": t.set_color("#7B4FA8"); t.set_fontweight("bold")
    elif c == "有活性": t.set_color(GREEN)
ax.set_xlabel("D_M  （相对野生型的白化马氏距离）")
ax.set_title("Cycle 4 · 阴性对照：偏离大 ≠ 失活", pad=14)
ax.annotate("E72A（催化谷氨酸敲除，必然失活）\nD_M = 0.903 —— 全场最低",
            xy=(0.903, y[names.index("E72A")]), xytext=(2.4, y[names.index("E72A")] - 1.2),
            fontsize=11, color=ACC, fontweight="bold", linespacing=1.6,
            arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.9))
ax.annotate("WT 只换底物（蛋白未改）\nD_M = 5.605 > T31D（完全失活）5.498",
            xy=(5.605, y[names.index("WT-GCA")] + 0.35),
            xytext=(6.5, y[names.index("WT-GCA")] + 1.9),
            fontsize=10.8, color="#7B4FA8", fontweight="bold", linespacing=1.6,
            va="center",
            arrowprops=dict(arrowstyle="-|>", color="#7B4FA8", lw=1.9,
                            connectionstyle="arc3,rad=-0.25"))
ax.legend(handles=[Line2D([], [], marker="s", ls="", ms=12, mfc=c, mec="none", label=k)
                   for k, c in COL.items() if k in set(cls)],
          loc="lower right", fontsize=10)
style_ax(ax, grid="x"); ax.set_xlim(0, 10.2)
save(fig, "wiki_fig5_Cycle4_阴性对照.png")

# ===========================================================================
# fig6 —— Cycle 5：AiCE β/γ 回溯检验
# ===========================================================================
FA = "Apobec前期设计附件/Apobec前期设计附件/全长反设计.fa"
recs, nm, buf = [], None, []
for line in open(FA, encoding="utf-8"):
    line = line.rstrip("\n")
    if line.startswith(">"):
        if nm is not None: recs.append("".join(buf))
        nm, buf = line, []
    else: buf.append(line.strip())
recs.append("".join(buf))
WTS = ("MEASPASGPRHLMDPAIFTSNFNNGIGRHKTYLCYEVERLDNGTSVKMDQHRGFLHNQAKNLLCGFYGRHVEVNFIKKFTSERDF"
       "HPSMSCSITWFLSWSPCWECSQAIREFLSRHPGVTLVIYVARLFWHMDQQNRQGLRDLVNSGVTIQIMTYDEFKHCWDTFVDHQG"
       "APFQPWDGLDEHSQALSGRLRAILQNQGN")
SAMP = [s for s in recs if len(s) == 199 and s != WTS]
AA = "ACDEFGHIKLMNPQRSTVWY"
freq = np.zeros((199, 20))
for s in SAMP:
    for i, a in enumerate(s):
        if a in AA: freq[i, AA.index(a)] += 1
freq /= len(SAMP)

fig, axes = plt.subplots(1, 2, figsize=(15.0, 6.8))
ax = axes[0]
GAMMA = 0.5
cnt = []
for thr in np.arange(0, 0.95, 0.05):
    k = freq.max(1) >= thr
    cnt.append(int(k.sum()))
ax.plot(np.arange(0, 0.95, 0.05), cnt, color=BLUE, lw=2.4, marker="o", ms=5, zorder=3)
ax.axvline(GAMMA, color=GREEN, ls="--", lw=1.9, zorder=2)
ax.axvline(0.8, color=ACC, ls="--", lw=1.9, zorder=2)
ax.text(GAMMA + 0.015, max(cnt) * 0.86, "γ = 0.5\n(卷曲区阈值)", fontsize=11, color=GREEN,
        fontweight="bold", linespacing=1.5)
ax.text(0.815, max(cnt) * 0.86, "β = 0.8\n(结构化区阈值)", fontsize=11, color=ACC,
        fontweight="bold", linespacing=1.5)
ax.set_xlabel("AiCE 频率阈值"); ax.set_ylabel("通过过滤的位点数")
ax.set_title("① 这条蛋白有 83% 候选位点落在卷曲区\n→ 适用宽松阈值 γ=0.5", pad=12, linespacing=1.5)
style_ax(ax)

ax = axes[1]
labels = ["H29P", "K30T", "N57D", "A59P"]
vals_ = [freq[28, AA.index("P")], freq[29, AA.index("T")],
         freq[56, AA.index("D")], freq[58, AA.index("P")]]
bars = ax.bar(labels, vals_, color=LACC, ec=ACC, lw=1.6, width=0.58, zorder=3)
ax.axhline(GAMMA, color=GREEN, ls="--", lw=2.0, zorder=2)
ax.text(3.42, GAMMA + 0.022, "γ = 0.5", fontsize=12, color=GREEN, fontweight="bold", ha="right")
for b, v in zip(bars, vals_):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.022, f"{v:.3f}", ha="center",
            fontsize=11.5, color=ACC, fontweight="bold")
ax.set_ylim(0, 1.06); ax.set_ylabel("MPNN 采样频率")
ax.set_title("② 被点名的「强偏好」替换：频率远超阈值\n→ β/γ 过滤一个都没剔除", pad=12, linespacing=1.5)
style_ax(ax)
fig.suptitle("Cycle 5 · 回溯检验：AiCE 的 β/γ 结构约束过滤器能否救回逆折叠路线？",
             fontsize=14.5, color=NAVY, y=1.01, fontweight="bold")
save(fig, "wiki_fig6_Cycle5_方法回溯.png")

# ===========================================================================
# fig0 —— 项目总览
# ===========================================================================
fig, ax = plt.subplots(figsize=(14.2, 7.8))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
ax.add_patch(Rectangle((0, 0), 100, 100, color=BG, zorder=0))
ax.text(50, 93, "Orca 系统 · APOBEC 编辑模块", fontsize=25, color=NAVY,
        ha="center", fontweight="bold")
ax.text(50, 87.5, "「保 G 排 A」——让 RNA 碱基编辑器优先编辑 GCG（c.388）而非 GCA（c.871）",
        fontsize=13.5, color=GRAY, ha="center")
KPI = [(0.5, "1.371", "亲本 +1 比", NAVY), (20.4, "1.71", "单点天花板\n(K30H)", BLUE),
       (40.3, "2.16", "组合最优\n(保留 77%)", GREEN), (60.2, "117", "脱靶筛查样本\n57 个构建体", TEAL),
       (80.1, "5", "完成的 DBTL\n循环（+1 进行中）", GOLD)]
for x, num, lab, c in KPI:
    ax.add_patch(FancyBboxPatch((x, 69.5), 19.4, 14.5,
                                boxstyle="round,pad=0.4,rounding_size=1.0",
                                fc=WHITE, ec=c, lw=2.2, zorder=2))
    ax.text(x + 9.7, 78.0, num, fontsize=30, color=c, ha="center", fontweight="bold", zorder=3)
    ax.text(x + 9.7, 72.4, lab, fontsize=10.8, color=GRAY, ha="center",
            linespacing=1.5, zorder=3)
ax.text(3, 62.5, "五个循环递进", fontsize=14, color=NAVY, fontweight="bold")
FLOW = [("Cycle 1", "单点饱和", "天花板 1.71\n单点路线关闭", ACC),
        ("Cycle 2", "组合突变", "突破 2.0\n最优 2.16/77%", GREEN),
        ("Cycle 3", "全局脱靶", "7 组清除脱靶\n指标本身有偏", TEAL),
        ("Cycle 4", "结构复核", "CP 只编码\n「哪条 RNA」", "#7B4FA8"),
        ("Cycle 5", "方法回溯", "8 条假说否证\n→ 高约束设计", GOLD)]
for i, (c, t, o, col) in enumerate(FLOW):
    x = 3 + i * 19.2
    ax.add_patch(FancyBboxPatch((x, 34), 17, 23,
                                boxstyle="round,pad=0.35,rounding_size=0.9",
                                fc=WHITE, ec=col, lw=2.0, zorder=2))
    ax.add_patch(FancyBboxPatch((x, 51.4), 17, 5.6,
                                boxstyle="round,pad=0.35,rounding_size=0.9",
                                fc=col, ec="none", zorder=3))
    ax.text(x + 8.5, 54.2, c, fontsize=12.5, color=WHITE, ha="center",
            fontweight="bold", zorder=4)
    ax.text(x + 8.5, 46.5, t, fontsize=13.5, color=NAVY, ha="center", fontweight="bold", zorder=4)
    ax.text(x + 8.5, 39.5, o, fontsize=10.2, color=GRAY, ha="center",
            linespacing=1.6, zorder=4)
    if i < 4:
        ax.add_patch(FancyArrowPatch((x + 17.3, 45.5), (x + 19.0, 45.5), arrowstyle="-|>",
                                     mutation_scale=20, color="#9DB3CC", lw=2.4, zorder=4))
ax.add_patch(FancyBboxPatch((3, 5), 94, 24,
                            boxstyle="round,pad=0.4,rounding_size=1.0",
                            fc=WHITE, ec=BLUE, lw=2.0, zorder=2))
ax.text(6, 24.5, "核心方法学结论", fontsize=14, color=NAVY, fontweight="bold", zorder=3)
for i, t in enumerate([
        "①  +1 位天然不存在 GCG 特异的侧链读取元件 —— 单点无法做出特异性",
        "②  在 +1 位这个界面上，结构接触、机器学习打分、接触概率三类计算证据都不足以预测功能",
        "③  湿实验是唯一判据；每一次意外都转化为一条方法学规则（ROF 归一化 / 活性下限 0.30 / 噪声阈值 0.0265）"]):
    ax.text(6, 19.5 - i * 5.0, t, fontsize=11.8, color=GRAY, zorder=3, va="center")
save(fig, "wiki_fig0_项目总览.png")

print("\n全部图表生成完毕 →", OUT)
