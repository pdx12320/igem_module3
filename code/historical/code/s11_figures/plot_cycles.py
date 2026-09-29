# -*- coding: utf-8 -*-
"""
ORCA Wiki 科研绘图 —— APOBEC 编辑模块 DBTL 五个循环的数据图

遵循 create-wiki-figure skill，并按要求采用发表论文格式：
  · 全图 Arial；图内标注一律英文
  · 面板字母 A / B（粗体，左上角）；无图内标题（标题与说明放 caption.md）
  · 白底、无装饰边框；参考线含义集中在图外图例，避免文字压线或压点
  · 组别颜色全项目锁定于 orca-figure-style.json，不随每张图重新分配
  · 导出 PNG@2x / SVG / PDF，附 caption、alt-text、provenance（含源文件 SHA-256）

用法：uv run --with matplotlib --with numpy --with scipy python plot_cycles.py
"""
import csv, hashlib, math, shutil, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
from orca_plot import Theme, scatter, export   # noqa: E402

STYLE = HERE / "orca-figure-style.json"
RESULTS = ROOT / "results"

GROUP_ORDER = ["Active", "Below floor", "Partially inactive", "Inactive",
               "Not tested", "WT (GCA substrate)"]

theme = Theme(STYLE)
theme.order(GROUP_ORDER)
print(f"字体：{theme.font}（拉丁）／{theme.cjk}（CJK）")
for n in theme.notes:
    print("  ·", n)
INK, MUTED = theme.c["ink"], theme.c["muted"]


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rd(name):
    with open(RESULTS / name, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def fresh(d):
    p = HERE / d
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True)
    return p


def panel(ax, letter):
    """发表格式面板字母（粗体，左上角外侧）。"""
    ax.text(-0.145, 1.06, letter, transform=ax.transAxes, fontsize=13,
            fontweight="bold", color=INK, va="top", ha="left")


def outside_legend(ax, handles, y=0.5):
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, y),
              fontsize=9.5, frameon=False, handletextpad=0.6, labelspacing=0.75)


# ===========================================================================
# Cycle 1
# ===========================================================================
def fig_cycle1():
    rows = [r for r in rd("experimental_ranking.csv") if "PUF" not in r["mut"]]
    pts = [(num(r["ratio"]), num(r["retain"])) for r in rows
           if num(r["ratio"]) is not None and num(r["retain"]) is not None]
    act = [p for p in pts if p[1] >= 0.70]
    ina = [p for p in pts if p[1] < 0.70]

    fig, ax = theme.figure()
    with theme.context():
        for grp, dd in (("Below floor", ina), ("Active", act)):
            scatter(ax, [p[0] for p in dd], [p[1] for p in dd], theme, group=grp,
                    xlabel="+1 ratio (GCG / GCA)",
                    ylabel="Activity retention (C388 / parent)")
        ax.axhline(0.70, color=theme.c["teal600"], ls="--", lw=1.5, zorder=1)
        ax.axvline(2.00, color=theme.c["orange500"], ls="--", lw=1.5, zorder=1)
        ax.axvline(1.371, color=theme.c["line"], ls=":", lw=1.5, zorder=1)
        ax.annotate("K30H", xy=(1.71, 0.85), xytext=(2.30, 0.99), fontsize=10,
                    color=theme.c["orange500"], fontweight="bold", ha="left", va="center",
                    zorder=9, arrowprops=dict(arrowstyle="-|>", color=theme.c["orange500"],
                                              lw=1.3, shrinkA=3, shrinkB=5))
        ax.set_xlim(0.55, 3.45); ax.set_ylim(-0.07, 1.18)
        outside_legend(ax, [
            Line2D([], [], marker="o", ls="", ms=7,
                   markerfacecolor=theme.style("Active")["color"], markeredgecolor=INK,
                   label="Active (retention ≥ 0.70)"),
            Line2D([], [], marker="s", ls="", ms=7,
                   markerfacecolor=theme.style("Below floor")["color"], markeredgecolor=INK,
                   label="Below retention floor"),
            Line2D([], [], color=theme.c["line"], ls=":", lw=1.5,
                   label="Parent +1 ratio (1.371)"),
            Line2D([], [], color=theme.c["orange500"], ls="--", lw=1.5,
                   label="+1 ratio target (2.0)"),
            Line2D([], [], color=theme.c["teal600"], ls="--", lw=1.5,
                   label="Retention floor (0.70)")], y=0.5)
    return export(fig, fresh("cycle1-single-site"), theme, stem="cycle1",
                  caption=(
                      "Figure 1 | Single-site saturation: the +1 layer has one reader, and a hard ceiling.\n"
                      f"n = {len(pts)} single mutants of the APOBEC editing module (mean of two independent "
                      "transfections), read by amplicon deep sequencing of a 951 bp APOE amplicon. Dashed lines "
                      "mark the preset retention floor (0.70, teal) and the +1 ratio target (2.0, orange); the "
                      "dotted line marks the same-batch parent PUF12-9 (+1 ratio 1.371). K30H is the highest "
                      "+1 ratio in the batch (1.71 at 0.84 retention) and the only effective engineering of the "
                      "+1 layer — K30 is the single residue in the protein that reads this base through its "
                      "sidechain, and it reads G better than A (sidechain-base contact frequency 0.81 vs 0.64). "
                      "T31A removes the strongest A-specific sidechain-base hydrogen bond in the protein "
                      "(contact frequency 1.00 in the A-type complex, 0.00 in the G-type) yet reads GCG 0.501 / "
                      "GCA 0.379 / ACA 0.239, indistinguishable from the parent (0.514 / 0.375 / 0.294): "
                      "structural contact is not the same thing as functional driving force. "
                      "Source: results/experimental_ranking.csv."),
                  alt_text=("Scatter plot of 102 APOBEC single mutants, +1 ratio on the x axis against activity "
                            "retention on the y axis. Most points cluster at +1 ratio 1.0-1.5 and retention "
                            "0.2-1.0. The highest point, K30H, reaches +1 ratio 1.71 at 0.84 retention, still "
                            "below the +1 ratio target line at 2.0, with no single mutant reaching the target. "
                            "The point for T31A sits essentially on the parent, at +1 ratio 1.32."),
                  provenance={"source_file": "results/experimental_ranking.csv",
                              "sha256": sha256(RESULTS / "experimental_ranking.csv"),
                              "read_scope": f"all {len(pts)} single mutants (parent row excluded)",
                              "columns": {"mut": "mutant label", "ratio": "+1 ratio GCG/GCA",
                                          "retain": "C388 relative to same-batch parent PUF12-9"},
                              "units": "dimensionless ratios",
                              "transform": "none; no observation removed",
                              "note": "retention conflates expression, stability and catalysis"})


# ===========================================================================
# Cycle 2
# ===========================================================================
def fig_cycle2():
    rows = [r for r in rd("23_combo_master_table.csv") if num(r["ratio_p1"]) is not None]
    xs = np.array([num(r["ratio_p1"]) for r in rows])
    ys = np.array([num(r["retain_vs_parent"]) for r in rows])
    nm = [r["muts"] for r in rows]

    fig, ax = theme.figure()
    with theme.context():
        scatter(ax, xs, ys, theme, group="Active",
                xlabel="+1 ratio (GCG / GCA)",
                ylabel="Activity retention (vs. batch parent)")
        front, best = [], -1.0
        for x_, y_ in sorted(zip(xs, ys), reverse=True):
            if y_ > best:
                front.append((x_, y_)); best = y_
        fx, fy = zip(*front)
        ax.plot(fx, fy, color=theme.c["orange500"], lw=1.6, ls="--", zorder=2)
        ax.axhline(0.70, color=theme.c["teal600"], ls="--", lw=1.5, zorder=1)
        ax.axvline(2.00, color=theme.c["orange500"], ls="--", lw=1.5, zorder=1)
        i = nm.index("27T-30H-58M")
        ax.scatter([xs[i]], [ys[i]], s=180, marker="*", c=theme.c["orange500"],
                   edgecolors=INK, linewidths=0.8, zorder=9)
        ax.annotate("27T-30H-58M", xy=(xs[i], ys[i] + 0.03), xytext=(2.42, 0.93),
                    fontsize=10, color=theme.c["orange500"], fontweight="bold",
                    ha="left", va="center", zorder=10,
                    arrowprops=dict(arrowstyle="-|>", color=theme.c["orange500"], lw=1.3,
                                    shrinkA=3, shrinkB=6))
        ax.set_xlim(0.80, 4.15); ax.set_ylim(-0.08, 1.08)
        outside_legend(ax, [
            Line2D([], [], marker="o", ls="", ms=7,
                   markerfacecolor=theme.style("Active")["color"], markeredgecolor=INK,
                   label="Combinatorial variants (n = %d)" % len(rows)),
            Line2D([], [], marker="*", ls="", ms=11, markerfacecolor=theme.c["orange500"],
                   markeredgecolor=INK, label="27T-30H-58M (2.16 / 0.77)"),
            Line2D([], [], color=theme.c["orange500"], ls="--", lw=1.6, label="Pareto front"),
            Line2D([], [], color=theme.c["orange500"], ls="--", lw=1.5, label="+1 ratio target (2.0)"),
            Line2D([], [], color=theme.c["teal600"], ls="--", lw=1.5, label="Retention floor (0.70)")],
            y=0.5)
    return export(fig, fresh("cycle2-combinatorial"), theme, stem="cycle2",
                  caption=(
                      "Figure 2 | Combinatorial mutagenesis: crossing 2.0 requires acting on two recognition "
                      "layers at once.\n"
                      f"n = {len(rows)} plotted points with a +1 ratio reading, drawn from the 49 constructs in "
                      "the analysis master table (the wet-lab record lists 50; 27D-32F was dropped for having "
                      "no usable data). Of the 49, 44 were transfected in duplicate, 4 in singlicate and 2 in "
                      "quadruplicate. Each point is the mean of its replicates. The orange dashed line is the "
                      "Pareto front (highest retention achievable at a given +1 ratio) and slopes down to the "
                      "right, showing that higher ratios cost activity. The star marks 27T-30H-58M, the only "
                      "variant above +1 ratio 2.0 that retains near-floor activity; its three components act on "
                      "different layers — 27T on the −1 anchor (a 36-fold suppression of ACA-class substrate at "
                      "88% retention on its own), 30H on the +1 reader, and 58M on activity maintenance. The "
                      "front is conserved rather than removed by combining: every variant above ratio 2.5 "
                      "retains less than 40%. Source: results/23_combo_master_table.csv."),
                  alt_text=(f"Scatter plot of {len(rows)} APOBEC combinatorial constructs with a +1 ratio "
                            "reading, +1 ratio on the x axis (0.8-4.1) against activity retention on the y axis "
                            "(0-1). An orange dashed Pareto front slopes down to the right, showing that "
                            "higher ratios cost activity. A starred point, 27T-30H-58M, sits at +1 ratio 2.16 "
                            "and retention 0.77; no other variant above +1 ratio 2.0 stays near the 0.70 "
                            "retention line."),
                  provenance={"source_file": "results/23_combo_master_table.csv",
                              "sha256": sha256(RESULTS / "23_combo_master_table.csv"),
                              "read_scope": f"all {len(rows)} combinations with a +1 ratio reading",
                              "columns": {"muts": "combination", "ratio_p1": "+1 ratio GCG/GCA",
                                          "retain_vs_parent": "C388 relative to combinatorial-batch parent"},
                              "units": "dimensionless ratios",
                              "transform": "none; no observation removed",
                              "note": "the combinatorial batch uses a different parental baseline; "
                                      "cross-batch comparison requires ROF normalisation"})


# ===========================================================================
# Cycle 3
# ===========================================================================
def fig_cycle3():
    from scipy import stats as st
    rows = [r for r in rd("GCG_vs_off_ranking_WT.csv") if r["is_WT"] != "True"]
    fin = [r for r in rows if num(r["targeting_ratio"]) is not None]
    n_inf = len(rows) - len(fin)
    c388 = np.array([num(r["C388_pct"]) for r in fin])
    tr = np.array([num(r["targeting_ratio"]) for r in fin])
    off = np.array([num(r["sum_nonGCG_pct"]) for r in fin])
    r_p = float(np.corrcoef(off, tr)[0, 1])
    r_s = float(st.spearmanr(off, tr)[0])

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5), layout="constrained")
    with theme.context():
        ax = axes[0]
        for lo, hi, key in [(10, 20, "orange500"), (35, 60, "teal600")]:
            m = (c388 >= lo) & (c388 <= hi)
            ax.axvspan(lo, hi, color=theme.c[key], alpha=0.10, zorder=0)
            ax.plot([lo, hi], [np.median(tr[m])] * 2, color=theme.c[key], lw=2.6,
                    solid_capstyle="butt", zorder=4)
        scatter(ax, c388, tr, theme, group="Active",
                xlabel="On-target editing, C388 (%)", ylabel="Targeting ratio")
        ax.axhline(1.0, color=theme.c["line"], ls=":", lw=1.4, zorder=1)
        ax.set_ylim(-0.4, 9.6); ax.set_xlim(-2, 62)
        ax.text(0.5, 0.965, f"n = {int(((c388>=10)&(c388<=20)).sum())}  median 2.53",
                transform=ax.transAxes, ha="center", va="top", fontsize=9.5,
                color=theme.c["orange500"], zorder=9)
        ax.text(0.79, 0.335, f"n = {int(((c388>=35)&(c388<=60)).sum())}  median 1.20",
                transform=ax.transAxes, ha="center", va="top", fontsize=9.5,
                color=theme.c["teal600"], zorder=9)
        ax.text(0.03, 0.97, f"{n_inf} constructs: ratio = ∞\n(denominator collapse), not plotted",
                transform=ax.transAxes, ha="left", va="top", fontsize=9,
                color=theme.c["coral400"], linespacing=1.5, zorder=9)
        panel(ax, "A")

        ax = axes[1]
        scatter(ax, off, tr, theme, group="Active",
                xlabel="Σ non-GCG editing (%)", ylabel="Targeting ratio")
        z = np.polyfit(off, tr, 1)
        xs_ = np.linspace(off.min(), off.max(), 60)
        ax.plot(xs_, np.polyval(z, xs_), color=theme.c["orange500"], lw=1.6, ls="--", zorder=2)
        ax.set_xlim(-8, 265); ax.set_ylim(-0.4, 9.6)
        ax.text(0.03, 0.97,
                f"vs. Σ non-GCG:  Pearson r = {r_p:+.3f},  Spearman ρ = {r_s:+.3f}\n"
                "C388% vs. Σ non-GCG%:  Pearson r = +0.760",
                transform=ax.transAxes, fontsize=9, color=theme.c["ink"],
                va="top", ha="left", linespacing=1.7, zorder=9,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=theme.c["line"], lw=0.9))
        panel(ax, "B")
    return export(fig, fresh("cycle3-targeting-ratio"), theme, stem="cycle3",
                  caption=(
                      "Figure 3 | On-target and off-target editing are coupled, and the targeting ratio hides it.\n"
                      f"n = {len(fin)} combinatorial variants with a finite targeting ratio; a further {n_inf} "
                      "variants had every off-target site below the 5% detection floor, leaving the denominator "
                      "at zero (ratio = ∞, not plotted). (A) Shaded bands mark the predefined low-activity "
                      "(C388 10-20%) and high-activity (35-60%) strata; thick lines are stratum medians "
                      "(2.53 and 1.20). (B) Targeting ratio against total off-target editing, with a linear fit "
                      "and both correlation coefficients. The underlying biology is that total off-target "
                      "editing tracks on-target efficiency (Pearson r = +0.760 across the unfiltered set): "
                      "within this mutational spectrum the two share a common determinant, so off-targets are "
                      "not a detachable module and a reducing ratio cannot be read as improved discrimination. "
                      "Source: results/GCG_vs_off_ranking_WT.csv."),
                  alt_text=("Two-panel figure. Panel A plots targeting ratio against on-target editing C388 (%), "
                            "with a shaded low-activity band (10-20%, n=13, median 2.53) and high-activity band "
                            "(35-60%, n=14, median 1.20). Panel B plots targeting ratio against total off-target "
                            "editing with a downward-sloping fit, Pearson r = -0.390 and Spearman rho = -0.557. "
                            "The ratio rises as on-target activity falls, because low-activity samples lose their "
                            "off-target signal to the detection floor."),
                  provenance={"source_file": "results/GCG_vs_off_ranking_WT.csv",
                              "sha256": sha256(RESULTS / "GCG_vs_off_ranking_WT.csv"),
                              "read_scope": f"50 variants, {len(fin)} finite and {n_inf} infinite ratio",
                              "columns": {"C388_pct": "APOE c.388 editing (%)",
                                          "targeting_ratio": "Σ(47 GCG sites) / Σ(244 non-GCG sites)",
                                          "sum_nonGCG_pct": "summed non-GCG editing (%)"},
                              "units": "percentages for editing; targeting ratio dimensionless",
                              "transform": "infinite ratios flagged but excluded from correlation and plotting",
                              "note": "the two correlation coefficients use different measures and must not "
                                      "both be reported as r"})


# ===========================================================================
# Cycle 4
# ===========================================================================
def fig_cycle4():
    rows = rd("阴性对照_DM.csv")
    rows.sort(key=lambda r: num(r["D_M"]))
    CLS = {"完全失活": "Inactive", "有活性": "Active", "部分失活": "Partially inactive",
           "未测": "Not tested", "WT（GCA 底物）": "WT (GCA substrate)"}
    names = [r["construct"] for r in rows]
    vals = [num(r["D_M"]) for r in rows]
    grp = [CLS.get(r["functional_class"], "Not tested") for r in rows]
    XMAX = 11.6

    fig, ax = theme.figure(height=6.6)
    with theme.context():
        for i, (v, g) in enumerate(zip(vals, grp)):
            ax.barh(i, v, height=theme.g["bar_width"], facecolor=theme.style(g)["color"],
                    alpha=0.85, edgecolor=INK, linewidth=0.7, zorder=2)
        ax.axvline(1.57, color=INK, ls="--", lw=1.3, zorder=3)
        for i, v in enumerate(vals):
            ax.text(XMAX - 0.15, i, f"{v:.2f}", va="center", ha="right",
                    fontsize=8.5, color=MUTED)
        ax.set_yticks(np.arange(len(names)))
        ax.set_yticklabels(names, fontsize=9)
        for t, g in zip(ax.get_yticklabels(), grp):
            if g in ("Inactive", "WT (GCA substrate)"):
                t.set_color(theme.style(g)["color"])
        ax.set_xlabel("D_M (whitened Mahalanobis distance to wild type)")
        ax.set_xlim(0, XMAX); ax.set_ylim(-1.4, len(names) + 0.4)
        ax.set_xticks([0, 2, 4, 6, 8, 10])
        ax.text(1.72, len(names) + 0.05, "WT null 95th pct = 1.57",
                color=INK, fontsize=9, va="center", ha="left")
        seen = [g for g in GROUP_ORDER if g in set(grp)]
        outside_legend(ax, [Patch(facecolor=theme.style(g)["color"], edgecolor=INK,
                                  linewidth=0.7, alpha=0.85, label=g) for g in seen], y=0.5)
    return export(fig, fresh("cycle4-negative-controls"), theme, stem="cycle4",
                  caption=(
                      "Figure 4 | Our substitutions did not remodel the interface: deviation follows the "
                      "substrate, not the mutation.\n"
                      f"n = {len(rows)} constructs. D_M is the Mahalanobis distance to wild type computed on a "
                      "whitening basis defined solely by the 20 wild-type seeds (construct centroid over all "
                      "models); the dashed line at 1.57 is the 95th percentile of the leave-one-out wild-type "
                      "null. Bar colour encodes the functional class. E72A, an obligatory-dead catalytic "
                      "knockout, has the lowest D_M of the set (0.90) — removing the catalytic centre leaves the "
                      "interface essentially untouched, so binding and catalysis are decoupled in this enzyme. "
                      "WT-GCA — the wild-type protein with only the substrate swapped — reaches 5.61, above the "
                      "completely inactive T31D (5.50): the contact pattern is set by which RNA is bound, not by "
                      "what the protein was changed to. Protein signal is still present when the perturbation is "
                      "severe (N57W, D_M = 8.89, the highest in the set) but is otherwise drowned out. "
                      "Source: results/阴性对照_DM.csv."),
                  alt_text=("Horizontal bar chart ranking 28 constructs by D_M from high to low. The highest is "
                            "N57W at 8.89 and the lowest is Y32F at 0.49. The catalytic knockout E72A, which "
                            "must be completely inactive, has D_M = 0.90, near the bottom. WT-GCA, in which only "
                            "the RNA substrate was changed, reaches 5.61, above the completely inactive T31D "
                            "at 5.50. Structural deviation therefore does not track loss of function."),
                  provenance={"source_file": "results/阴性对照_DM.csv",
                              "sha256": sha256(RESULTS / "阴性对照_DM.csv"),
                              "read_scope": f"all {len(rows)} constructs",
                              "columns": {"construct": "construct label", "D_M": "whitened Mahalanobis distance",
                                          "functional_class": "class from wet-lab activity retention"},
                              "units": "D_M dimensionless (RMS of z-scores over WT principal directions)",
                              "transform": "D_M uses a WT-only whitening basis to avoid basis contamination",
                              "note": "E72A and N57A were modelled in silico only and not assayed"})


# ===========================================================================
# Cycle 5
# ===========================================================================
def fig_cycle5():
    FA = ROOT / "Apobec前期设计附件/Apobec前期设计附件/全长反设计.fa"
    WTS = ("MEASPASGPRHLMDPAIFTSNFNNGIGRHKTYLCYEVERLDNGTSVKMDQHRGFLHNQAKNLLCGFYGRHVEVNFIKKFTSERDF"
           "HPSMSCSITWFLSWSPCWECSQAIREFLSRHPGVTLVIYVARLFWHMDQQNRQGLRDLVNSGVTIQIMTYDEFKHCWDTFVDHQG"
           "APFQPWDGLDEHSQALSGRLRAILQNQGN")
    recs, buf = [], []
    for line in FA.read_text(encoding="utf-8").splitlines():
        if line.startswith(">"):
            if buf: recs.append("".join(buf))
            buf = []
        else:
            buf.append(line.strip())
    if buf: recs.append("".join(buf))
    samp = [s for s in recs if len(s) == 199 and s != WTS]
    AA = "ACDEFGHIKLMNPQRSTVWY"
    fr = np.zeros((199, 20))
    for s in samp:
        for i, a in enumerate(s):
            if a in AA:
                fr[i, AA.index(a)] += 1
    fr /= len(samp)
    top = fr.max(1)

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5), layout="constrained")
    with theme.context():
        ax = axes[0]
        th = np.arange(0.0, 0.95, 0.05)
        cnt = [int((top >= t).sum()) for t in th]
        ax.plot(th, cnt, color=theme.c["indigo700"], lw=1.6, marker="o", markersize=4, zorder=3)
        ax.axvline(0.5, color=theme.c["teal600"], ls="--", lw=1.4, zorder=2)
        ax.axvline(0.8, color=theme.c["orange500"], ls="--", lw=1.4, zorder=2)
        ax.set_xlabel("AiCE frequency threshold")
        ax.set_ylabel("Positions passing filter")
        ax.set_xlim(-0.03, 1.02); ax.set_ylim(-6, max(cnt) * 1.22)
        ax.text(0.53, 0.97, "γ = 0.5\ncoil", transform=ax.transAxes, fontsize=9,
                color=theme.c["teal600"], va="top", ha="left", linespacing=1.5)
        ax.text(0.78, 0.78, "β = 0.8\nstructured", transform=ax.transAxes, fontsize=9,
                color=theme.c["orange500"], va="top", ha="right", linespacing=1.5)
        panel(ax, "A")

        ax = axes[1]
        lab = ["H29P", "K30T", "N57D", "A59P"]
        vv = [fr[28, AA.index("P")], fr[29, AA.index("T")],
              fr[56, AA.index("D")], fr[58, AA.index("P")]]
        ax.bar(range(4), vv, width=theme.g["bar_width"], facecolor=theme.c["coral400"],
               alpha=0.85, edgecolor=INK, linewidth=0.8, zorder=2)
        ax.axhline(0.5, color=theme.c["teal600"], ls="--", lw=1.4, zorder=3)
        for i, v in enumerate(vv):
            ax.text(i, v + 0.028, f"{v:.3f}", ha="center", va="bottom", fontsize=9,
                    color=INK, zorder=9)
        ax.set_xticks(range(4), lab, fontsize=9)
        ax.set_ylim(0, 1.30); ax.set_xlim(-0.7, 4.35)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_ylabel("MPNN sampling frequency")
        ax.set_xlabel("Substitution nominated by ProteinMPNN")
        ax.text(0.995, 0.515, "γ = 0.5", transform=ax.transAxes, fontsize=9,
                color=theme.c["teal600"], ha="right", va="center")
        panel(ax, "B")
    return export(fig, fresh("cycle5-aice-filter"), theme, stem="cycle5",
                  caption=(
                      "Figure 5 | The natural sequence distribution is not organised around +1 discrimination.\n"
                      f"Inverse-folding sampling: n = {len(samp)} sequences (ProteinMPNN, T = 0.3, full-length "
                      "design). (A) Number of positions passing the frequency threshold as the threshold "
                      "increases; γ = 0.5 (teal) and β = 0.8 (orange) mark the thresholds recommended by AiCE "
                      "for coil and structured regions respectively. (B) Sampling frequency of the four "
                      "substitutions previously nominated as strongly preferred. All four exceed γ = 0.5, so "
                      "none would be removed by the β/γ filter. The structural-constraint layer cannot rescue "
                      "the inverse-folding route here for a definitional reason: the APOBEC substrate-binding "
                      "interface is itself a loop, and 16 of the 18 candidate positions are coil by secondary "
                      "structure, so all fall under the permissive γ = 0.5. Independent of this figure, the "
                      "sampling frequency correlates negatively with the measured +1 ratio (Spearman ρ = −0.499) "
                      "and is 0.000 for K30H — the best measured variant is not in the distribution the model "
                      "proposes. Source: Apobec前期设计附件/全长反设计.fa."),
                  alt_text=("Two-panel figure. Panel A plots the number of positions passing the AiCE frequency "
                            "filter against the threshold, declining from about 120 positions at threshold 0 to "
                            "about 10 at threshold 0.9, with vertical lines at γ = 0.5 and β = 0.8. Panel B shows "
                            "bar heights of 0.771, 0.562, 0.875 and 0.896 for the substitutions H29P, K30T, "
                            "N57D and A59P, all above the γ = 0.5 line, so none is removed by the filter."),
                  provenance={"source_file": "Apobec前期设计附件/Apobec前期设计附件/全长反设计.fa",
                              "sha256": sha256(FA),
                              "read_scope": f"{len(samp)} sampled sequences at T = 0.3 "
                                             "(reference sequence with identical WT sequence excluded)",
                              "columns": {"position": "APOBEC 199 aa numbering (1-based)",
                                          "frequency": "occurrence of an amino acid among the sampled sequences"},
                              "units": "frequency as a proportion between 0 and 1",
                              "transform": "none; thresholds β = 0.8 / γ = 0.5 taken from the published AiCE code",
                              "note": "no DSSP binary available locally, so secondary structure was not "
                                      "recomputed for this figure; the recommended thresholds were reused as-is"})


# ===========================================================================
# Cycle 3b —— 偏倚的回补检验与重新排序
# ===========================================================================
def fig_cycle3b():
    from scipy import stats as st
    rows = [r for r in rd("GCG_vs_off_ranking_WT.csv") if r["is_WT"] != "True"]
    fin = [r for r in rows if num(r["targeting_ratio"]) is not None]
    keep = [r for r in fin if num(r["C388_pct"]) is not None and num(r["C388_pct"]) >= 30.0]

    def stats_of(sub):
        off = np.array([num(r["sum_nonGCG_pct"]) for r in sub])
        tr = np.array([num(r["targeting_ratio"]) for r in sub])
        c3 = np.array([num(r["C388_pct"]) for r in sub])
        return (float(st.spearmanr(off, tr)[0]), float(np.corrcoef(off, tr)[0, 1]),
                float(np.corrcoef(c3, off)[0, 1]))

    raw = sorted(fin, key=lambda r: -num(r["targeting_ratio"]))[:10]
    flt = sorted(keep, key=lambda r: -num(r["targeting_ratio"]))[:10]
    raw_set = {r["mutation"] for r in raw}
    flt_set = {r["mutation"] for r in flt}

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), layout="constrained")
    with theme.context():
        ax = axes[0]
        other = [r for r in fin if r["mutation"] not in raw_set and r["mutation"] not in flt_set]
        scatter(ax, [num(r["C388_pct"]) for r in other],
                [num(r["targeting_ratio"]) for r in other], theme, group="Not tested",
                xlabel="On-target editing, C388 (%)", ylabel="Targeting ratio")
        scatter(ax, [num(r["C388_pct"]) for r in raw if r["mutation"] not in flt_set],
                [num(r["targeting_ratio"]) for r in raw if r["mutation"] not in flt_set],
                theme, group="Inactive", xlabel="On-target editing, C388 (%)",
                ylabel="Targeting ratio")
        scatter(ax, [num(r["C388_pct"]) for r in flt],
                [num(r["targeting_ratio"]) for r in flt], theme, group="Active",
                xlabel="On-target editing, C388 (%)", ylabel="Targeting ratio")
        ax.axvline(30, color=INK, ls="--", lw=1.4, zorder=3)
        ax.set_xlim(-2, 58); ax.set_ylim(-0.4, 7.2)
        ax.text(28.3, 6.9, "activity floor 30%", rotation=90, fontsize=9,
                color=INK, va="top", ha="right")
        boxed = None
        ax.text(0.97, 0.62,
                "raw top-10\nbelow the floor\n10 / 10",
                transform=ax.transAxes, fontsize=9, color=theme.c["coral400"],
                ha="right", va="top", linespacing=1.55, zorder=9,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=theme.c["coral400"], lw=0.9))
        outside_legend(ax, [
            Line2D([], [], marker="o", ls="", ms=7,
                   markerfacecolor=theme.style("Active")["color"], markeredgecolor=INK,
                   label="Top-10 after floor (n=10)"),
            Line2D([], [], marker="s", ls="", ms=7,
                   markerfacecolor=theme.style("Inactive")["color"], markeredgecolor=INK,
                   label="Top-10 before floor (n=10)"),
            Line2D([], [], marker="D", ls="", ms=6,
                   markerfacecolor=theme.style("Not tested")["color"], markeredgecolor=INK,
                   label="Other variants (n=%d)" % len(other)),
            Line2D([], [], color=INK, ls="--", lw=1.4, label="Activity floor (30%)")], y=0.62)
        panel(ax, "A")

        ax = axes[1]
        s_all, p_all, c_all = stats_of(fin)
        s_flt, p_flt, c_flt = stats_of(keep)
        TRIPLE = [("Spearman ρ  (ratio vs off)", s_all, s_flt, theme.c["indigo700"]),
                  ("Pearson r  (ratio vs off)", p_all, p_flt, theme.c["orange500"]),
                  ("Pearson r  (C388 vs off)", c_all, c_flt, theme.c["teal600"])]
        xx = np.arange(2); w = 0.24
        for k, (lab, va, vb, col) in enumerate(TRIPLE):
            off_ = (k - 1) * (w + 0.02)
            ax.bar(xx + off_, [va, vb], width=w, facecolor=col, alpha=0.85,
                   edgecolor=INK, linewidth=0.8, zorder=2)
            for i, v in enumerate((va, vb)):
                ax.text(i + off_, v + (0.04 if v > 0 else -0.04), f"{v:+.2f}",
                        ha="center", va="bottom" if v > 0 else "top",
                        fontsize=8.5, color=INK, zorder=9)
        ax.axhline(0, color=INK, lw=0.9, zorder=3)
        ax.set_xticks(xx, ["No\nfloor", "Floor\n≥30%"], fontsize=8.5)
        ax.set_xlim(-0.55, 1.55); ax.set_ylim(-0.95, 1.05)
        ax.set_ylabel("Correlation coefficient")
        outside_legend(ax, [Patch(facecolor=c, edgecolor=INK, linewidth=0.8, alpha=0.85, label=l)
                            for l, _, _, c in TRIPLE], y=0.5)
        panel(ax, "B")
    return export(fig, fresh("cycle3b-rerank"), theme, stem="cycle3b",
                  caption=(
                      "Figure 3b | Back-testing the activity floor: the coupling is a property of the enzyme, "
                      "not of the plotting.\n"
                      f"n = {len(fin)} variants with a finite targeting ratio, of which {len(keep)} pass an "
                      "on-target activity floor of 30%. (A) Targeting ratio against on-target editing. All ten "
                      "variants at the top of the unfiltered ranking (squares) lie below the floor; after "
                      "applying it, the top ten (circles) is an entirely different set — overlap 0/10. "
                      "(B) Correlation coefficients under the two regimes. The floor eliminates the undefined "
                      "ratios (9 → 0) and weakens the C388%/off-target confound (+0.76 → +0.60), but does not "
                      "remove it, and the ratio–off-target association becomes stronger (−0.56 → −0.65). "
                      "The floor is therefore necessary but not sufficient: it removes the artefact of the "
                      "detection limit, while the underlying activity–off-target coupling that generates the "
                      "trend remains, and can only be addressed by genuine substrate discrimination. "
                      "Source: results/GCG_vs_off_ranking_WT.csv; analysis in 58_targeting_ratio_rerank.py."),
                  alt_text=("Two-panel figure. Panel A scatters targeting ratio against on-target editing "
                            "C388 (%). A vertical dashed line marks the 30% activity floor; all ten squares "
                            "(top-10 before the floor) sit left of it, while the ten circles (top-10 after the "
                            "floor) sit right of it, with no overlap between the two sets. Panel B compares "
                            "correlation coefficients with and without the floor: the ratio-versus-off-target "
                            "Spearman goes from -0.56 to -0.65, the Pearson from -0.39 to -0.46, and the "
                            "C388-versus-off-target Pearson falls from +0.76 to +0.60 — weakened but not removed."),
                  provenance={"source_file": "results/GCG_vs_off_ranking_WT.csv",
                              "sha256": sha256(RESULTS / "GCG_vs_off_ranking_WT.csv"),
                              "read_scope": f"50 combinatorial variants; {len(fin)} finite ratio; "
                                            f"{len(keep)} additionally pass C388 ≥ 30%",
                              "columns": {"C388_pct": "APOE c.388 editing (%)",
                                          "targeting_ratio": "Σ(47 GCG sites) / Σ(244 non-GCG sites)",
                                          "sum_nonGCG_pct": "summed non-GCG editing (%)"},
                              "units": "percentages for editing; targeting ratio dimensionless",
                              "transform": "thirty-two samples with C388 < 30% excluded in the filtered regime; "
                                           "infinite ratios excluded from correlations in both regimes",
                              "note": "the top-10 lists before and after the floor share no members"})


for fn in (fig_cycle1, fig_cycle2, fig_cycle3, fig_cycle3b, fig_cycle4, fig_cycle5):
    out = fn()
    print(f"  ✓ {Path(out['png']).parent.name}")
print("\n完成。输出目录：", HERE)
