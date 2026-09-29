# -*- coding: utf-8 -*-
"""
依据队友的绘图规范（见 orca_drylab_style.py）重绘 Dry Lab 页面的 10 张图。

排版约定（针对图例重叠与拥挤的修正）：
  · 每张图最多 2 个面板，一律 1 行 × 2 列，横向铺满，不出现 2×2 小图。
  · 全部图例统一置于面板下方（图级图例），不进入任何坐标轴区域。
  · 图内文字一律英文；save_checked() 会在写盘前断言无中日韩字符。
  · 数据表里的中文枚举（feature_set / 分组 / 优先级 / functional_class）显式映射为英文。

用法：uv run --with matplotlib --with numpy --with openpyxl --with scipy python plot_drylab_figures.py
"""
import csv, os, re, sys, math
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from orca_drylab_style import (
    BLUE, ORANGE, GREEN, GREY, INK, PURPLE, FILL_BLUE, FILL_ORANGE,
    GRID, SPINE, FAINT, RULE, DARK, CLASS_COLORS, CLASS_STYLE, class_handles,
    canvas, titles, footnotes, style_axes, panel, legend_below, save_checked,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(HERE, "APOBEC_DryLab_assets")
R = lambda *p: os.path.join(ROOT, "results", *p)

# ---- 数据表中的中文枚举 → 英文（图内只允许英文） ----
FEATURE_SET = {"P1_内部CP全": "Internal CP (all)",
               "P2_内部CP长程": "Internal CP (long-range)",
               "P3_口袋内部CP": "Pocket CP"}
PRIORITY_BASE = {"必做": "Required"}
PRIORITY_QUAL = {"首推": "top pick", "控制": "control", "金标准": "gold standard",
                 "机制": "mechanism", "对照": "reference"}
CLS_CN = {"完全失活": "Inactive", "有活性": "Active", "部分失活": "Partially inactive",
          "未测": "Not tested", "WT（GCA 底物）": "WT (GCA substrate)",
          "新失活对照（未测）": "New inactive control (not measured)",
          "WT 参照": "Wild-type reference"}
# 构建体名里的中文（阴性对照表把两个野生型对照写成中文）
CONSTRUCT_CN = {"WT（GCG 亲本）": "WT (GCG parent)", "WT（GCA 底物）": "WT (GCA substrate)"}


def construct_en(v):
    if v in CONSTRUCT_CN:
        return CONSTRUCT_CN[v]
    m = re.match(r"^WT\s*[（(]\s*([A-Z]{3})\s*[^）)]*[）)]$", str(v))
    return f"WT ({m.group(1)} substrate)" if m else str(v)


def priority_en(v):
    """'P0（首推）' → 'P0 (top pick)'；'必做' → 'Required'。"""
    v = str(v).strip()
    m = re.match(r"^([^（(]+)\s*[（(]([^）)]*)[）)]?$", v)
    if m:
        base, qual = m.group(1).strip(), m.group(2).strip()
        return f"{base} ({PRIORITY_QUAL.get(qual, qual)})"
    return PRIORITY_BASE.get(v, v)

FOOT = dict(start=.105, step=.026)


def rd(name):
    with open(R(name), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(x, d=None):
    try:
        v = float(x)
        return d if (math.isnan(v) or math.isinf(v)) else v
    except (TypeError, ValueError):
        return d


def short(m):
    """G27T-K30H-Q58M → 27T-30H-58M"""
    out = []
    for part in str(m).replace("+", "-").split("-"):
        part = part.strip()
        out.append(part[1:] if len(part) > 1 and part[0].isalpha() and part[1:].isdigit() else part)
    return "-".join(out)


def two_panel(h=9.2, wspace=.22):
    return canvas(w=15.8, h=h, ncols=2, wspace=wspace, bottom=.30, top=.83)


def one_panel(h=8.8, left=.085, right=.965):
    return canvas(w=15.8, h=h, left=left, right=right, bottom=.28, top=.84)


TICK = dict(rotation=45, ha="right", rotation_mode="anchor", fontsize=8.6)


# ===========================================================================
# Figure 2 — what the deviation descriptor encodes (2 panels)
# ===========================================================================
def fig2():
    rows = [r for r in rd("CP偏离_汇总.csv") if r["substrate"] == "GCG"]
    ORDER = ["M132D", "M132E", "K30H", "K30H-Q58M", "G25E", "A59P", "G27D", "G27T",
             "G27D-K30H", "G27T-K30H-Q58M"]
    D = {r["variant"]: r for r in rows}
    order = [v for v in ORDER if v in D]
    tick = [short(v) for v in order]

    fig, (a, b) = two_panel()
    x = np.arange(len(order)); w = .26
    hs = []
    for i, (k, lab, col) in enumerate([("z_intra", "Internal CP (long-range)", BLUE),
                                       ("z_pocket", "Pocket CP", ORANGE),
                                       ("z_protC", "Protein–target-C CP", GREEN)]):
        hs.append(a.bar(x + (i - 1) * w, [num(D[v][k], 0) for v in order], w, label=lab,
                        color=col, edgecolor="white", linewidth=.6, zorder=3))
    a.axhspan(-3, 3, color="#EFEFEF", zorder=0)
    for v in (3, -3):
        a.axhline(v, color=RULE, ls="--", lw=1, zorder=2)
    a.set_xticks(x); a.set_xticklabels(tick, **TICK)
    a.set_ylabel("z-score vs wild type (SD)")
    a.set_title("Deviation descriptors", fontsize=11.5, color=INK, pad=8)
    style_axes(a, grid="y"); panel(a, "A")

    zs, act = [], []
    for v in order:
        aa = num(D[v]["activity_retention"])
        if aa is not None:
            zs.append(num(D[v]["z_protC"], 0)); act.append(aa)
    b.scatter(zs, act, s=110, color=BLUE, edgecolor="white", linewidth=1.2, zorder=4)
    if len(zs) > 2:
        r = float(np.corrcoef(zs, act)[0, 1])
        b.text(.04, .93, f"Pearson r = {r:+.3f}   (n = {len(zs)})", transform=b.transAxes,
               fontsize=10.5, color=INK)
    b.set_xlabel("protein–target-C CP deviation (z)")
    b.set_ylabel("activity retention")
    b.set_title("Deviation against measured activity", fontsize=11.5, color=INK, pad=8)
    style_axes(b, grid="both"); panel(b, "B")

    titles(fig, "Contact-probability deviation does not explain loss of activity",
           "Constructs are ordered along a fixed sequence. The grey band marks the ±3 SD noise floor "
           "of the descriptor itself, so values inside it are indistinguishable from noise.")
    legend_below(fig, [h for h in hs], [h.get_label() for h in hs], ncol=3, y=.175)
    footnotes(fig, [
        "A  three deviation descriptors per construct; the grey band is the ±3 SD noise floor of the descriptor.",
        "B  protein–target-C deviation against measured activity retention: the two are not ordered.",
        "†  An apparent trend in B is confounded by the conservation of the mutated position, which is itself correlated with the deviation; that comparison is reported in the text rather than shown here.",
    ], **FOOT)
    return save_checked(fig, os.path.join(ASSETS, "figure_2_cp_deviation.png"))


# ===========================================================================
# Figure 3 — per-residue ΔΔCP heat map (single panel)
# ===========================================================================
def fig3():
    import openpyxl
    wb = openpyxl.load_workbook(R("突变体基线ΔCP_全199残基.xlsx"), data_only=True)
    rows = list(wb["2_ΔΔCP矩阵"].iter_rows(values_only=True))
    head = rows[0]
    muts = [h for h in head[3:] if h]
    data = [r for r in rows[1:] if r and isinstance(r[0], int)]
    mat = np.array([[num(v, 0.0) for v in r[3:3 + len(muts)]] for r in data], dtype=float)
    idx = np.argsort(-np.nanmax(np.abs(mat), axis=1))[:22]
    idx = idx[np.argsort([data[i][0] for i in idx])]
    sub = mat[idx, :]
    labs = [f"{data[i][1]}{data[i][0]}" for i in idx]

    fig, ax = one_panel(h=9.0, left=.075, right=.895)
    vmax = float(np.nanmax(np.abs(sub)))
    im = ax.imshow(sub, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(muts)))
    ax.set_xticklabels([short(m) for m in muts], **TICK)
    ax.set_yticks(range(len(idx))); ax.set_yticklabels(labs, fontsize=9)
    ax.tick_params(axis="both", length=0, pad=6)
    for j in range(len(muts)):
        for i in range(len(idx)):
            v = sub[i, j]
            if abs(v) >= .05:
                ax.text(j, i, f"{v:+.2f}", ha="center", va="center", fontsize=6.4,
                        color="white" if abs(v) > vmax * .62 else DARK)
    cb = fig.colorbar(im, ax=ax, fraction=.020, pad=.012)
    cb.set_label("ΔΔCP vs wild type", fontsize=10)
    cb.outline.set_edgecolor(SPINE); cb.ax.tick_params(length=0, pad=4)
    ax.set_xlabel("construct")

    titles(fig, "Per-residue contact-probability change relative to wild type",
           "The 22 residues with the largest change, across all mutant constructs. Only |ΔΔCP| ≥ 0.05 "
           "is labelled; the independent wild-type rerun sets the interpretation threshold at 0.0265.")
    footnotes(fig, [
        "Residues are ordered by sequence position. Positive values indicate a larger G-minus-A contact difference than in wild type.",
        "The two reader positions H29 and K30 approach zero in the triple combination, i.e. they stop distinguishing the two substrates.",
        "†  Values are means over the available model records; a single value below 0.0265 is not interpreted on its own.",
    ], **FOOT)
    return save_checked(fig, os.path.join(ASSETS, "figure_3_ddcp_heatmap.png"))


# ===========================================================================
# Figure 4 — negative-control diagnosis (2 panels)
# ===========================================================================
def fig4():
    rows = rd("阴性对照_偏离与PCA.csv")
    gcg = [r for r in rows if r["substrate"] == "GCG"]
    rows = gcg or rows
    names = [construct_en(r["construct"]) for r in rows]
    cls = [CLS_CN.get(r["functional_class"], "Not tested") for r in rows]

    # 参考线取本表内野生型（GCG 亲本）的值，避免与其它表的 2.88 Å 混用
    wtrow = next((r for r in rows if "WT" in r["construct"] and "GCG" in r["construct"]), None)
    wt_ref = num(wtrow["d_E72"]) if wtrow else None

    fig, (a, b) = two_panel(h=10.0)
    x = np.arange(len(names))
    for xi, r, c in zip(x, rows, cls):
        v = num(r["d_E72"])
        if v is None or not np.isfinite(v):
            # 该构建体未做几何建模：不画柱、不补零，用一个明确标记
            a.plot([xi], [0], marker="x", ms=8, mew=1.8, color=GREY, zorder=5)
            a.text(xi, 0, "not modelled", ha="center", va="bottom", fontsize=7.5,
                   color=GREY, rotation=90, zorder=5)
            continue
        st = CLASS_STYLE.get(c, {"color": GREY})
        a.bar(xi, v, .6, color=st["color"], edgecolor=st.get("edge", "white"),
              linewidth=.7, hatch=st.get("hatch"), zorder=3)
    if wt_ref is not None:
        a.axhline(wt_ref, color=INK, ls="--", lw=1.6, zorder=4)
        a.text(len(names) - .5, wt_ref, f" wild-type reference {wt_ref:.3f} Å (this table)",
               va="bottom", ha="right", fontsize=9.5, color=INK)
    a.set_xticks(x); a.set_xticklabels(names, **TICK)
    a.set_ylabel("target C4N4 – E72 distance (Å)")
    a.set_title("Catalytic geometry", fontsize=11.5, color=INK, pad=8)
    style_axes(a, grid="y"); panel(a, "A")

    w = .26
    hs = []
    for i, (k, lab, col) in enumerate([("z_intra", "Internal CP (long-range)", BLUE),
                                       ("z_pocket", "Pocket CP", ORANGE),
                                       ("z_protC", "Protein–target-C CP", GREEN)]):
        hs.append(b.bar(x + (i - 1) * w, [num(r[k], 0) for r in rows], w, label=lab,
                        color=col, edgecolor="white", linewidth=.6, zorder=3))
    b.axhspan(-3, 3, color="#EFEFEF", zorder=0)
    for v in (3, -3):
        b.axhline(v, color=RULE, ls="--", lw=1, zorder=2)
    b.set_xticks(x); b.set_xticklabels(names, **TICK)
    b.set_ylabel("z-score vs wild type (SD)")
    b.set_title("Deviation descriptors", fontsize=11.5, color=INK, pad=8)
    style_axes(b, grid="y"); panel(b, "B")

    titles(fig, "Control constructs whose functional outcome was already known",
           "Panel A encodes functional class; panel B encodes the deviation descriptor. The two encodings "
           "are independent and each has its own legend.")
    seen = [k for k in CLASS_STYLE if k in set(cls)]
    legend_below(fig, [Patch(facecolor=CLASS_STYLE[k]["color"],
                             edgecolor=CLASS_STYLE[k].get("edge", "white"),
                             hatch=CLASS_STYLE[k].get("hatch"), label=k) for k in seen],
                 None, ncol=min(len(seen), 3), y=.185)
    legend_below(fig, [Patch(facecolor=col, edgecolor="white", label=lab)
                       for lab, col in (("Internal CP (long-range)", BLUE),
                                        ("Pocket CP", ORANGE),
                                        ("Protein–target-C CP", GREEN))],
                 None, ncol=3, y=.118)
    footnotes(fig, [
        "A  the catalytic distance, bars coloured by functional class (first legend).",
        "B  the three deviation descriptors, bars coloured by descriptor (second legend); the grey band is the ±3 SD noise floor.",
        "†  E72A was not modelled geometrically, so its distance is absent rather than zero, and is marked \"not modelled\". "
        "E72A and N57A are designed inactive controls that have not been assayed, and are not grouped with measured inactive constructs.",
    ], start=.082, step=.024)
    return save_checked(fig, os.path.join(ASSETS, "figure_4_negctrl_diagnosis.png"))


# ===========================================================================
# Figure 5 — control constructs in PC space and by D_M (2 panels)
# ===========================================================================
def fig5():
    pc = rd("阴性对照_PC坐标.csv")
    dm = rd("阴性对照_DM.csv")
    dmap = {r["construct"]: num(r["D_M"]) for r in dm}
    LABEL = {"E72A", "N57W", "N57A", "T31D", "T31A", "WT-GCA", "Y32F"}

    fig, (a, b) = two_panel(h=9.4, wspace=.26)
    cls_of = {r["construct"]: CLS_CN.get(r["functional_class"], "Not tested") for r in pc}
    seen = [k for k in CLASS_STYLE if k in set(cls_of.values())]
    for k in seen:
        pts = [(num(r["PC1"]), num(r["PC2"]), r["construct"]) for r in pc
               if cls_of[r["construct"]] == k]
        pts = [(p, q, n) for p, q, n in pts if p is not None and q is not None]
        if pts:
            st = CLASS_STYLE[k]
            a.scatter([p for p, _, _ in pts], [q for _, q, _ in pts], s=110,
                      facecolor=st["marker_face"], edgecolor=st["marker_edge"],
                      linewidth=1.5, zorder=4)
    for r in pc:
        if r["construct"] in LABEL:
            a.annotate(r["construct"], (num(r["PC1"], 0), num(r["PC2"], 0)),
                       textcoords="offset points", xytext=(8, -3), fontsize=9.5, color=DARK)
    a.axhline(0, color=FAINT, lw=.8); a.axvline(0, color=FAINT, lw=.8)
    a.set_xlabel("PC1"); a.set_ylabel("PC2")
    a.set_title("Principal-component space", fontsize=11.5, color=INK, pad=8)
    style_axes(a, grid="both"); panel(a, "A")

    order = sorted([k for k in dmap if dmap[k] is not None], key=lambda k: dmap[k])
    y = np.arange(len(order))
    cls_map = {r["construct"]: CLS_CN.get(r["functional_class"], "Not tested") for r in dm}
    for yi, k in zip(y, order):
        st = CLASS_STYLE.get(cls_map.get(k, "Not tested"), {"color": GREY})
        b.barh(yi, dmap[k], .72, color=st["color"], edgecolor=st.get("edge", "white"),
               linewidth=.6, hatch=st.get("hatch"), zorder=3)
    b.axvline(1.57, color=INK, ls="--", lw=1.6, zorder=4)
    b.text(1.57, len(order) - .5, " null 95th pct 1.57", va="top", ha="left",
           fontsize=9.5, color=INK)
    b.set_yticks(y); b.set_yticklabels(order, fontsize=8.6)
    b.set_xlabel("D$_M$ (Mahalanobis distance to wild type)")
    b.set_title("Deviation from wild type", fontsize=11.5, color=INK, pad=8)
    style_axes(b, grid="x"); panel(b, "B")

    titles(fig, "The control constructs in principal-component space and by deviation",
           "The whitening basis is defined by the wild-type seeds alone, so it does not shift with whichever "
           "constructs are included in the comparison.")
    handles, seen = class_handles(set(cls_of.values()))
    legend_below(fig, handles, None, ncol=min(len(seen), 3), y=.175)
    footnotes(fig, [
        "A  only the labelled constructs are annotated, to keep the panel legible; the leading components separate constructs by which substrate was modelled.",
        "B  D$_M$ for all constructs, with the leave-one-out wild-type 95th percentile as reference.",
        "†  E72A and N57A are designed inactive controls that have not been assayed. They are shown as a separate class "
        "(hollow with an orange outline) and are not grouped with the measured inactive constructs.",
    ], **FOOT)
    return save_checked(fig, os.path.join(ASSETS, "figure_5_negctrl_pca.png"))


# ===========================================================================
# Figure 6 — protein-only models across feature sets (2 panels)
# ===========================================================================
def fig6():
    sep = rd("纯蛋白_分离度.csv")
    cls = rd("纯蛋白_分类表现.csv")
    names = [r["construct"] for r in sep]
    SETS = [("D_M_P1_内部CP全", FEATURE_SET["P1_内部CP全"], BLUE),
            ("D_M_P2_内部CP长程", FEATURE_SET["P2_内部CP长程"], ORANGE),
            ("D_M_P3_口袋内部CP", FEATURE_SET["P3_口袋内部CP"], GREEN)]

    fig, (a, b) = two_panel(h=9.2)
    x = np.arange(len(names)); w = .26
    hs = []
    for i, (k, lab, col) in enumerate(SETS):
        hs.append(a.bar(x + (i - 1) * w, [num(r[k], 0) for r in sep], w, label=lab,
                        color=col, edgecolor="white", linewidth=.6, zorder=3))
    a.set_xticks(x); a.set_xticklabels(names, **TICK)
    a.set_ylabel("D$_M$ within the protein-only models")
    a.set_title("Deviation, by feature set", fontsize=11.5, color=INK, pad=8)
    style_axes(a, grid="y"); panel(a, "A")

    if cls:
        xs = np.arange(len(cls))
        acc = [num(r["construct_accuracy"], 0) for r in cls]
        b.bar(xs, acc, .5, color=[BLUE, ORANGE, GREEN][:len(cls)],
              edgecolor="white", linewidth=.6, zorder=3)
        for i, v in enumerate(acc):
            b.text(i, v + .025, f"{v:.2f}", ha="center", fontsize=10, color=INK)
        b.axhline(.5, color=RULE, ls="--", lw=1.3, zorder=4)
        b.text(len(cls) - .45, .5, " chance 0.50", va="bottom", ha="right",
               fontsize=9.5, color=GREY)
        b.set_xticks(xs)
        b.set_xticklabels([FEATURE_SET.get(str(r["feature_set"]), str(r["feature_set"]))
                           for r in cls], **TICK)
        b.set_ylim(0, 1.05)
        b.set_ylabel("dead / active classification accuracy")
        b.set_title("Classification from protein-only models", fontsize=11.5, color=INK, pad=8)
    style_axes(b, grid="y"); panel(b, "B")

    titles(fig, "With RNA removed, constructs separate by changes in the protein itself",
           "Sixty protein-only jobs were submitted: 20 seeds for wild type and four seeds for each of ten "
           "constructs. The feature sets differ in which internal contacts they use.")
    legend_below(fig, [h for h in hs], [h.get_label() for h in hs], ncol=3, y=.175)
    footnotes(fig, [
        "A  deviation from wild type within the protein-only models, computed separately for each feature set.",
        "B  accuracy of assigning a construct to the dead or active group from the protein-only models, against the chance level.",
        "†  The protein-only comparison isolates the contribution of the mutation; comparison with the complex-based analysis shows how much of the original grouping was attributable to the bound substrate.",
    ], **FOOT)
    return save_checked(fig, os.path.join(ASSETS, "figure_6_protein_only_pca.png"))


# ===========================================================================
# Figure 7 — complex vs protein-only deviation (single panel)
# ===========================================================================
def fig7():
    dm = {r["construct"]: num(r["D_M"]) for r in rd("阴性对照_DM.csv")}
    sep = {r["construct"]: num(r["D_M_P1_内部CP全"]) for r in rd("纯蛋白_分离度.csv")}
    keys = sorted([k for k in dm if k in sep and dm[k] is not None and sep[k] is not None],
                  key=lambda k: sep[k])

    fig, ax = one_panel(h=9.0)
    x = np.arange(len(keys)); w = .36
    h1 = ax.bar(x - w / 2, [dm[k] for k in keys], w, color=BLUE, edgecolor="white",
                linewidth=.6, label="Complex (with RNA)", zorder=3)
    h2 = ax.bar(x + w / 2, [sep[k] for k in keys], w, color=ORANGE, edgecolor="white",
                linewidth=.6, label="Protein-only (no RNA)", zorder=3)
    ax.axhline(1.57, color=INK, ls="--", lw=1.4, zorder=4)
    ax.text(len(keys) - .5, 1.57, " wild-type null 1.57", va="bottom", ha="right",
            fontsize=9.5, color=INK)
    for k in ("T31D", "E72A"):
        if k in keys:
            i = keys.index(k)
            ax.annotate(f"{sep[k]/dm[k]*100:.0f}% retained", (i, max(dm[k], sep[k])),
                        textcoords="offset points", xytext=(0, 10), ha="center",
                        fontsize=9.5, color=INK, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(keys, **TICK)
    ax.set_ylabel("D$_M$ (Mahalanobis distance to wild type)")

    titles(fig, "Removing the RNA separates the mutation effect from the substrate effect",
           "Each construct is shown under both modelling conditions. For T31D most of the deviation is "
           "substrate-driven; E72A is the only construct that deviates more without RNA.")
    legend_below(fig, [h1, h2], None, ncol=2, y=.135)
    footnotes(fig, [
        "Constructs are ordered by their protein-only deviation. Each bar is a deviation from the wild-type reference of the same condition.",
        "T31D loses 78% of its deviation when the RNA is removed; E72A rises from 0.903 to 1.656, i.e. RNA binding had been masking a protein defect.",
        "†  The protein-only representation uses internal contacts only, so the two conditions are not comparable in absolute scale; the comparison is of the direction and magnitude of change.",
    ], start=.085, step=.026)
    return save_checked(fig, os.path.join(ASSETS, "figure_7_protein_only_vs_complex.png"))


# ===========================================================================
# Figure 8 — single-site saturation (single panel)
# ===========================================================================
def fig8():
    allr = rd("experimental_ranking.csv")
    parent = next((r for r in allr if "WT" in r["mut"] or "PUF" in r["mut"]), None)
    cand = [r for r in allr if r is not parent and num(r["retain"]) is not None]
    # 分母（GCA）检出为 0 时，比值不可定义，表中记为 0 —— 这类行不参与作图
    usable = [r for r in cand if num(r["GCA"]) not in (None, 0.0) and num(r["ratio"]) is not None]
    dropped = [r for r in cand if r not in usable]
    xs = np.array([num(r["ratio"]) for r in usable])
    ys = np.array([num(r["retain"]) for r in usable])

    fig, ax = one_panel(h=9.0)
    act = ys >= .70
    h1 = ax.scatter(xs[~act], ys[~act], s=62, color=GREY, alpha=.75, edgecolor="white",
                    linewidth=.7, zorder=3, label="retention < 0.70")
    h2 = ax.scatter(xs[act], ys[act], s=70, color=BLUE, edgecolor="white", linewidth=.8,
                    zorder=4, label="retention ≥ 0.70")
    # 星标 = 达到活性下限的突变体中比值最高者（K30H），而不是全图比值最高者
    ok = [r for r in usable if num(r["retain"]) >= .70]
    star = max(ok, key=lambda r: num(r["ratio"]))
    ax.scatter([num(star["ratio"])], [num(star["retain"])], s=230, marker="*", color=ORANGE,
               edgecolor="white", linewidth=1.1, zorder=6)
    ax.annotate(f"{star['mut']}  ({num(star['ratio']):.2f}, {num(star['retain']):.2f})",
                (num(star["ratio"]), num(star["retain"])), textcoords="offset points",
                xytext=(-14, 14), fontsize=10.5, color=INK, fontweight="bold", ha="right")
    # 超过 2.0 但活性代价极大的点单独标注，避免读成「已达标」
    for r in sorted([r for r in usable if num(r["ratio"]) >= 2.0],
                    key=lambda r: -num(r["ratio"])):
        ax.annotate(f"{r['mut']}", (num(r["ratio"]), num(r["retain"])),
                    textcoords="offset points", xytext=(0, -16), ha="center",
                    fontsize=9, color=GREY)
    if parent:
        # 用未舍入的同批亲本比值，与正文的 1.371 对齐
        par_ratio = num(parent["GCG"]) / num(parent["GCA"])
        ax.axvline(par_ratio, color=RULE, ls=":", lw=1.5, zorder=2)
        ax.text(par_ratio, 1.02, f" parent {par_ratio:.3f}", va="bottom", ha="left",
                fontsize=9.5, color=GREY)
    ax.axvline(2.0, color=ORANGE, ls="--", lw=1.5, zorder=2)
    ax.text(2.0, 1.02, " target 2.0", va="bottom", ha="left", fontsize=9.5, color=ORANGE)
    ax.axhline(.70, color=GREEN, ls="--", lw=1.5, zorder=2)
    ax.text(0.02, .71, " retention floor 0.70", transform=ax.get_yaxis_transform(),
            va="bottom", ha="left", fontsize=9.5, color=GREEN)
    ax.set_xlabel("+1 ratio (GCG / GCA)")
    ax.set_ylabel("activity retention (vs same-batch parent)")

    n_hi = sum(1 for r in usable if num(r["ratio"]) >= 2.0)
    titles(fig, "Single-site saturation: the +1 layer has one reader and a hard ceiling",
           f"{len(usable)} single mutants plotted, each the mean of two independent transfections. "
           f"{n_hi} exceed the 2.0 target but only at a severe activity cost.")
    legend_below(fig, [h1, h2], None, ncol=2, y=.135)
    above = sorted([r for r in usable if num(r["ratio"]) >= 2.0], key=lambda r: -num(r["ratio"]))
    above_txt = ", ".join(f"{r['mut']} {num(r['ratio']):.2f}" for r in above)
    drop_txt = ", ".join(r["mut"] for r in dropped)
    footnotes(fig, [
        f"Starred: {star['mut']}, the highest +1 ratio among mutants retaining at least 70% activity. "
        "It is neither the highest point of the panel nor the highest ratio in it.",
        f"The {n_hi} mutants above the 2.0 line ({above_txt}) all retain well under 40% activity, "
        "so the target is not reached at acceptable activity.",
        ("†  " + f"{drop_txt} is not plotted: its GCA editing was not detected, so the ratio is undefined rather than zero. "
         if dropped else "")
        + "T31A, which removes the strongest A-specific sidechain–base contact in the domain, sits on the parent and does not improve specificity.",
        "†  Retention is expressed relative to the same-batch parent, which conflates expression, stability and catalysis; it is not a purified-activity measurement.",
    ], start=.085, step=.026)
    return save_checked(fig, os.path.join(ASSETS, "figure_8_single_site_validation.png"))


# ===========================================================================
# Figure 9 — targeting ratio across the amplicon (2 panels)
# ===========================================================================
def fig9():
    rows = [r for r in rd("GCG_vs_off_ranking_WT.csv") if r.get("is_WT") != "True"]
    fin = [r for r in rows if num(r["targeting_ratio"]) is not None]
    n_inf = len(rows) - len(fin)
    c388 = np.array([num(r["C388_pct"]) for r in fin])
    tr = np.array([num(r["targeting_ratio"]) for r in fin])
    off = np.array([num(r["sum_nonGCG_pct"]) for r in fin])

    fig, (a, b) = two_panel(h=9.0)
    low = (c388 >= 10) & (c388 < 20)
    high = (c388 >= 35) & (c388 <= 60)
    a.axvspan(10, 20, color=FILL_ORANGE, alpha=.55, zorder=0)
    a.axvspan(35, 60, color=FILL_BLUE, alpha=.55, zorder=0)
    a.scatter(c388, tr, s=58, color=BLUE, alpha=.8, edgecolor="white", linewidth=.6, zorder=3)
    if low.sum():
        a.hlines(float(np.median(tr[low])), 10, 20, color=ORANGE, lw=2.6, zorder=5)
        a.text(15, float(np.median(tr[low])), f"median {np.median(tr[low]):.2f}", va="bottom",
               ha="center", fontsize=9.5, color=ORANGE, zorder=6)
    if high.sum():
        a.hlines(float(np.median(tr[high])), 35, 60, color=BLUE, lw=2.6, zorder=5)
        a.text(47.5, float(np.median(tr[high])), f"median {np.median(tr[high]):.2f}", va="bottom",
               ha="center", fontsize=9.5, color=BLUE, zorder=6)
    a.set_xlabel("on-target editing, c.388 (%)")
    a.set_ylabel("targeting ratio  Σ(GCG) / Σ(non-GCG)")
    a.set_title("Ratio against on-target activity", fontsize=11.5, color=INK, pad=8)
    style_axes(a, grid="y"); panel(a, "A")

    b.scatter(off, tr, s=58, color=BLUE, alpha=.8, edgecolor="white", linewidth=.6, zorder=3)
    if len(off) > 2:
        k, c0 = np.polyfit(off, tr, 1)
        xx = np.linspace(off.min(), off.max(), 50)
        b.plot(xx, k * xx + c0, color=ORANGE, lw=2.0, zorder=4)
        from scipy import stats as st
        b.text(.04, .93, f"Pearson r = {float(np.corrcoef(off, tr)[0,1]):+.3f}\n"
                         f"Spearman ρ = {float(st.spearmanr(off, tr)[0]):+.3f}\n"
                         f"n = {len(fin)}", transform=b.transAxes, fontsize=10.5,
               color=INK, linespacing=1.6)
    b.set_xlabel("total off-target editing, Σ(non-GCG) (%)")
    b.set_ylabel("targeting ratio")
    b.set_title("Ratio against off-target load", fontsize=11.5, color=INK, pad=8)
    style_axes(b, grid="both"); panel(b, "B")

    titles(fig, "The targeting ratio rises as on-target activity falls",
           f"{len(fin)} constructs with a finite ratio; a further {n_inf} had every off-target site below "
           "the detection floor, leaving the denominator at zero.")
    footnotes(fig, [
        "A  shaded bands mark the predefined low-activity (10–20%) and high-activity (35–60%) strata; thick lines are stratum medians.",
        "B  the ratio against total off-target editing, with a linear fit and both coefficients.",
        "†  The trend is produced by the detection floor, not by improved discrimination: as activity falls, off-target sites are recorded as zero first. On-target and off-target editing are themselves strongly correlated (Pearson r = +0.760).",
    ], **FOOT)
    return save_checked(fig, os.path.join(ASSETS, "figure_9_targeting_ratio.png"))


# ===========================================================================
# Figure 10 — next-round candidates (2 panels)
# ===========================================================================
def fig10():
    import openpyxl
    wb = openpyxl.load_workbook(R("下一步实验突变候选表_61组.xlsx"), data_only=True)
    rows = list(wb["突变候选表_61组"].iter_rows(values_only=True))
    head = list(rows[0])
    ci, gi, pi = head.index("编号"), head.index("分组"), head.index("优先级")
    recs = [r for r in rows[1:] if r and r[ci]]
    groups = {}
    for r in recs:
        groups.setdefault(str(r[gi]).split()[0], []).append(priority_en(r[pi]))
    keys = sorted(groups)
    GROUP_LABEL = {"A": "A\nreplication", "B": "B\nnew single", "C": "C\nnew\ncombinations",
                   "D": "D\ncontrols", "E": "E\nrelaxed\npairing"}

    fig, (a, b) = two_panel(h=9.0)
    x = np.arange(len(keys))
    counts = [len(groups[k]) for k in keys]
    a.bar(x, counts, .5, color=[BLUE, ORANGE, GREEN, "#7E8D99", GREY][:len(keys)],
          edgecolor="white", linewidth=.6, zorder=3)
    for xi, v in zip(x, counts):
        a.text(xi, v + .3, str(v), ha="center", fontsize=10.5, color=INK)
    a.set_xticks(x); a.set_xticklabels([GROUP_LABEL.get(k, k) for k in keys], fontsize=9.5)
    a.set_ylabel("constructs in the group")
    a.set_ylim(0, max(counts) * 1.22)
    a.set_title("Group sizes", fontsize=11.5, color=INK, pad=8)
    style_axes(a, grid="y"); panel(a, "A")

    allv = {v for k in keys for v in groups[k]}
    order = [p for p in ("Required", "P0 (top pick)", "P0 (gold standard)", "P0 (control)",
                         "P0", "P1 (control)", "P1 (mechanism)", "P1",
                         "P2 (mechanism)", "P2 (reference)", "P2") if p in allv]
    order += sorted(allv - set(order))
    cols = [ORANGE, BLUE, GREEN, "#7E8D99", GREY]
    bottom = np.zeros(len(keys)); hs = []
    for i, p in enumerate(order):
        vals = np.array([sum(1 for v in groups[k] if v == p) for k in keys], dtype=float)
        hs.append(b.bar(x, vals, .5, bottom=bottom, color=cols[i % len(cols)],
                        edgecolor="white", linewidth=.6, label=p, zorder=3))
        bottom += vals
    b.set_xticks(x); b.set_xticklabels(keys)
    b.set_ylabel("constructs by priority")
    b.set_title("Priority composition", fontsize=11.5, color=INK, pad=8)
    style_axes(b, grid="y"); panel(b, "B")

    titles(fig, "Candidates assembled for the next engineering cycle",
           f"{len(recs)} candidates in {len(keys)} groups: replication of existing constructs, new single "
           "substitutions, new combinations, control variants and relaxed pairings.")
    legend_below(fig, [h[0] for h in hs], order, ncol=len(order), y=.175)
    footnotes(fig, [
        "A  group sizes. Group D converts two contested mechanisms into directly measurable comparisons rather than arguments from structure.",
        "B  priority composition within each group.",
        "†  The design also adds a dose gradient from 0.25× to 4×, since every specificity value so far was obtained at a single dose.",
    ], **FOOT)
    return save_checked(fig, os.path.join(ASSETS, "figure_10_candidate_overview.png"))


# ===========================================================================
# Figure 11 — retrospective test of the AiCE constraint filter (2 panels)
# ===========================================================================
def fig11():
    fa = os.path.join(ROOT, "Apobec前期设计附件", "Apobec前期设计附件", "全长反设计.fa")
    seqs, cur = [], None
    for line in open(fa, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith(">"):
            if cur:
                seqs.append("".join(cur))
            cur = []
        elif cur is not None:
            cur.append(line.strip())
    if cur:
        seqs.append("".join(cur))
    ref, samp = seqs[0], seqs[1:]
    L = min(len(s) for s in samp)
    ths = np.linspace(0.001, 0.95, 40)
    npass = []
    for t in ths:
        c = 0
        for i in range(L):
            col = [s[i] for s in samp]
            if col.count(max(set(col), key=col.count)) / len(col) >= t:
                c += 1
        npass.append(c)
    npass = np.array(npass)

    # 四个争议替换取自「位点级」表（回溯检验表存的是 102 个已测单点，不含它们）
    aice = rd("AiCE过滤器_位点级.csv")
    wanted = ["H29P", "K30T", "N57D", "A59P"]
    found = {}
    for r in aice:
        key = f"{r['WT']}{r['位点']}{r['MPNN最高频aa']}"
        if key in wanted:
            found[key] = num(r["最高频"], 0.0)
    four = {k: found[k] for k in wanted if k in found}
    if not four:
        raise ValueError("fig11 panel B: no contested substitution found in AiCE过滤器_位点级.csv")

    fig, (a, b) = two_panel(h=9.0)
    a.plot(ths, npass, color=BLUE, lw=2.4, zorder=4)
    a.axvline(.5, color=GREEN, ls="--", lw=1.6, zorder=3)
    a.axvline(.8, color=ORANGE, ls="--", lw=1.6, zorder=3)
    a.text(.5, a.get_ylim()[1] * .97, " γ = 0.5", va="top", ha="left", fontsize=9.5, color=GREEN)
    a.text(.8, a.get_ylim()[1] * .97, " β = 0.8", va="top", ha="left", fontsize=9.5, color=ORANGE)
    a.set_xlabel("sampling-frequency threshold")
    a.set_ylabel("positions passing the threshold")
    a.set_title("Positions surviving the filter", fontsize=11.5, color=INK, pad=8)
    style_axes(a, grid="y"); panel(a, "A")

    if four:
        keys = list(four)
        x = np.arange(len(keys))
        b.bar(x, [four[k] for k in keys], .45, color=ORANGE, edgecolor="white",
              linewidth=.6, zorder=3)
        b.axhline(.5, color=GREEN, ls="--", lw=1.8, zorder=4)
        b.text(len(keys) - .45, .5, " γ = 0.5", va="bottom", ha="right", fontsize=9.5, color=GREEN)
        for xi, k in zip(x, keys):
            b.text(xi, four[k] + .02, f"{four[k]:.3f}", ha="center", fontsize=10, color=INK)
        b.set_xticks(x); b.set_xticklabels(keys)
        b.set_ylim(0, 1.0)
        b.set_ylabel("ProteinMPNN sampling frequency")
        b.set_title("Contested substitutions", fontsize=11.5, color=INK, pad=8)
    style_axes(b, grid="y"); panel(b, "B")

    titles(fig, "A published structural-constraint filter does not remove the contested substitutions",
           f"Retrospective application to {len(samp)} sampled sequences. The filter is stricter in structured "
           "regions and permissive in coils, and this interface is a loop.")
    footnotes(fig, [
        "A  positions surviving the frequency threshold as the threshold is raised, with the thresholds recommended for coil and structured regions.",
        "B  sampling frequency of the substitutions previously nominated as strongly preferred. All exceed γ = 0.5 and would therefore be retained.",
        "†  16 of the 18 candidate positions are coil by secondary structure. The best measured variant, K30H, has a sampling frequency of 0.000 and would not be nominated; sampling frequency correlates negatively with measured specificity (Spearman ρ = −0.499).",
    ], **FOOT)
    return save_checked(fig, os.path.join(ASSETS, "figure_11_method_retrospective.png"))


# ===========================================================================
# Figure 15 — results of the designed batch (2 panels)
# ===========================================================================
def fig15():
    """本批 37 个突变组：ROF–保留率全景；D 组配对对照；以及 C13 孔的剔除。"""
    rows = [r for r in rd("下一批突变_绘图用表.csv")]
    GRP_LABEL = {"A": "A replication", "B": "B new single", "C": "C new combinations",
                 "D": "D controls", "E": "E relaxed / anomalous", "new": "not in candidate list"}
    GRP_COL = {"A": GREY, "B": PURPLE, "C": BLUE, "D": ORANGE, "E": GREEN, "new": "#7E8D99"}

    fig, (a, b) = two_panel(h=9.6, wspace=.24)
    excl = [r for r in rows if r.get("excluded_failed_well") == "TRUE"]
    undef = [r for r in rows if r["undef"] == "TRUE" and r.get("excluded_failed_well") != "TRUE"]
    pts = [r for r in rows if r["undef"] != "TRUE"]
    for g in GRP_LABEL:
        sub = [r for r in pts if r["grp"] == g]
        if sub:
            a.scatter([num(r["ret"]) for r in sub], [num(r["rof"]) for r in sub], s=105,
                      color=GRP_COL[g], edgecolor="white", linewidth=1.1,
                      label=GRP_LABEL[g], zorder=4)
    # 比值不可定义的组：贴在底部，单独标记；若连保留率都无可信读数，另置一处并注明
    if undef:
        ux = [num(r["ret"]) if num(r["ret"]) is not None else 0.03 for r in undef]
        a.scatter(ux, [0.30] * len(undef), s=115, marker="v",
                  color="white", edgecolor=ORANGE, linewidth=1.6, zorder=5)
        for r, xi in zip(undef, ux):
            lack = "" if num(r["ret"]) is not None else "\n(no reliable reading)"
            a.annotate(f"{r['mut']}\n(ratio undefined){lack}", (xi, 0.30),
                       textcoords="offset points", xytext=(0, -30), ha="center",
                       fontsize=8.5, color=ORANGE)
    # 判为孔失败的样本：叉号标记，明示「不作为结果」
    for r in excl:
        xi = num(r["ret"]) if num(r["ret"]) is not None else 0.03
        a.scatter([xi], [0.30], s=150, marker="X", color="#B00020",
                  edgecolor="white", linewidth=.9, zorder=6)
        a.annotate(f"{r['mut']}\n(failed well, excluded)", (xi, 0.30),
                   textcoords="offset points", xytext=(0, -30), ha="center",
                   fontsize=8.5, color="#B00020", weight="bold")
    a.axhline(1.0, color=RULE, ls=":", lw=1.6, zorder=2)
    a.text(a.get_xlim()[1], 1.0, " same-batch parent ", va="bottom", ha="right",
           fontsize=9.5, color=GREY)
    a.axvline(.70, color=GREEN, ls="--", lw=1.6, zorder=2)
    a.text(.70, a.get_ylim()[1], " retention floor 0.70", va="top", ha="left",
           fontsize=9.5, color=GREEN)
    for r in pts:
        if r["cid"] in ("D03", "D04", "D05", "E20") or (r["rof"] and num(r["rof"]) >= 1.9):
            a.annotate(r["mut"], (num(r["ret"]), num(r["rof"])), textcoords="offset points",
                       xytext=(7, -3), fontsize=8.8, color=DARK)
    a.set_xlabel("activity retention (c.388 vs the batch reference)")
    a.set_ylabel("ROF (this construct's ratio ÷ the same-batch parent's ratio)")
    a.set_title("37 groups from the designed batch", fontsize=11.5, color=INK, pad=8)
    style_axes(a, grid="both"); panel(a, "A")

    # 面板 B：同一骨架的两个版本（跨批复现），以及 D 组配对；C13 孔单列为剔除项
    bars = [("27T-30H-58M\n(earlier batch)", .772, ORANGE, ""),
            ("27T-30H-58M\n+132E  (D03)", .673, BLUE, ""),
            ("25E-30H-58M\n+132D  (D04)", .340, ORANGE, ""),
            ("25E-30H-58M\n+132E  (D05)", .752, BLUE, "")]
    x = np.arange(len(bars))
    b.bar(x, [v for _, v, _, _ in bars], .5, color=[c for _, _, c, _ in bars],
          edgecolor="white", linewidth=.7, zorder=3)
    for xi, (_, v, _, note) in zip(x, bars):
        b.text(xi, v + .02, f"{v:.2f}", ha="center", fontsize=10, color=INK)
        if note:
            b.text(xi, .03, note, ha="center", fontsize=8, color="white", rotation=90, zorder=5)
    # C13 孔：以幽灵柱呈现，明确标注为剔除
    xc = len(bars)
    b.bar([xc], [.079], .5, color="white", edgecolor="#B00020", linewidth=1.6,
          hatch="///", zorder=3)
    b.text(xc, .10, "0.08", ha="center", fontsize=10, color="#B00020")
    b.text(xc, .30, "failed well\nexcluded", ha="center", fontsize=8.5, color="#B00020",
           weight="bold", zorder=5)
    b.axhline(.70, color=GREEN, ls="--", lw=1.6, zorder=4)
    b.text(len(bars) - .5, .70, " retention floor ", va="bottom", ha="right",
           fontsize=9.5, color=GREEN)
    b.set_xticks(np.arange(len(bars) + 1))
    b.set_xticklabels([lab for lab, _, _, _ in bars] + ["27T-30H-58M\n(C13, this batch)"], fontsize=9)
    b.set_ylim(0, 1.0)
    b.set_ylabel("activity retention")
    b.set_title("The same scaffold across two batches, and the Group D pairing",
                fontsize=11.5, color=INK, pad=8)
    style_axes(b, grid="y"); panel(b, "B")

    titles(fig, "The designed batch: the pairing resolves position 132, and the previous best is reproduced",
           "ROF normalises each construct's ratio to the same-batch parent (PUF12, ratio 1.070); the parental "
           "ratio itself drifts between batches, from 1.371 to 1.191 to 1.070.")
    legend_below(fig, [Line2D([], [], marker="o", ls="", ms=10, color=GRP_COL[g],
                              label=GRP_LABEL[g]) for g in GRP_LABEL], None, ncol=3, y=.165)
    footnotes(fig, [
        "A  in the G25E background, changing position 132 from D to E alone moves retention from 0.34 to 0.75 at the same scaffold.",
        "B  the 27T-30H-58M scaffold was measured in two batches. Its 132E version gave c.388 0.533 and c.871 0.256 here, against 0.520 and 0.241 earlier.",
        "C13  the 27T-30H-58M well in this batch returned c.388 0.063 with c.871 undetected. Since the same three substitutions reproduce at 0.533 in D03, "
        "the well is treated as a failed measurement and excluded rather than read as a negative result.",
        "†  26N-31G has an undefined ratio because c.871 was not detected in either replicate; it is marked separately rather than plotted as zero.",
    ], **FOOT)
    return save_checked(fig, os.path.join(ASSETS, "figure_15_designed_batch.png"))


if __name__ == "__main__":
    jobs = [("figure_2_cp_deviation", fig2), ("figure_3_ddcp_heatmap", fig3),
            ("figure_4_negctrl_diagnosis", fig4), ("figure_5_negctrl_pca", fig5),
            ("figure_6_protein_only_pca", fig6), ("figure_7_protein_only_vs_complex", fig7),
            ("figure_8_single_site_validation", fig8), ("figure_9_targeting_ratio", fig9),
            ("figure_10_candidate_overview", fig10), ("figure_11_method_retrospective", fig11),
            ("figure_15_designed_batch", fig15),
            ("figure_16_replication_saturation", fig16)]
    ok, fail = 0, []
    for name, fn in jobs:
        try:
            p = fn()
            print(f"  ✓ {name}")
            ok += 1
        except Exception as e:
            print(f"  ✗ {name}  {type(e).__name__}: {e}")
            fail.append((name, f"{type(e).__name__}: {e}"))
    print(f"\n完成 {ok}/{len(jobs)}")
    for n, m in fail:
        print("   失败", n, m)


def fig16():
    """第三批：关键构建体的跨批复现，27 位饱和（+1 轴与 −1 轴）。"""
    rows = [r for r in rd("第三批_绘图用表.csv")]
    singles27 = [r for r in rows if r["mut"].startswith("27") and r["grp"] == "single"]
    parent = next(r for r in rows if r["mut"] == "PUF12")

    fig, (a, b, c) = canvas(w=15.8, h=10.4, ncols=3, wspace=.30,
                            bottom=.30, top=.80, width_ratios=[.92, 1.08, 1.0])

    # ---- 面板 A：批内秩与帕累托结构（背景不同，只能做批内比较）
    muts = [r for r in rows if r["is_ref"] == "FALSE"]
    front = [r for r in muts
             if not any((num(o["rof"]) >= num(r["rof"]) and num(o["ret"]) >= num(r["ret"])
                         and (num(o["rof"]) > num(r["rof"]) or num(o["ret"]) > num(r["ret"])))
                        for o in muts)]
    a.scatter([num(r["ret"]) for r in muts], [num(r["rof"]) for r in muts], s=95,
              color=GREY, edgecolor="white", linewidth=1.0, zorder=3,
              label="other constructs")
    fr = sorted(front, key=lambda r: num(r["rof"]))
    a.plot([num(r["ret"]) for r in fr], [num(r["rof"]) for r in fr], color=GREEN,
           lw=2.0, ls="--", zorder=4, label="Pareto front")
    for r in fr:
        if r["mut"] != "27T-30H-58M":
            a.scatter([num(r["ret"])], [num(r["rof"])], s=115, color=BLUE,
                      edgecolor="white", linewidth=1.0, zorder=5)
    trip = next(r for r in muts if r["mut"] == "27T-30H-58M")
    a.scatter([num(trip["ret"])], [num(trip["rof"])], s=230, marker="*", color=ORANGE,
              edgecolor="white", linewidth=1.1, zorder=6, label="27T-30H-58M (triple)")
    for m, dx, dy in [("27T-30H-58M", 13, -13), ("30H-58M", -16, 6), ("27D-30H", 10, -13),
                      ("25E-30H", 10, 3), ("27I", 10, -6), ("27V", 10, -4), ("27E", 10, -4)]:
        r = next((x for x in muts if x["mut"] == m), None)
        if r:
            a.annotate(m, (num(r["ret"]), num(r["rof"])), textcoords="offset points",
                       xytext=(dx, dy), fontsize=8.8, color=DARK)
    a.axhline(1.0, color=RULE, ls=":", lw=1.6, zorder=2)
    a.text(1.042, 1.005, " parent level ", va="bottom", ha="right", fontsize=8.8, color=GREY)
    a.axvline(.95, color=GREEN, ls=":", lw=1.5, zorder=2)
    a.text(.95, a.get_ylim()[0], " 0.95 retention", va="bottom", ha="left",
           fontsize=8.8, color=GREEN)
    a.set_xlabel("activity retention (c.388 vs the batch parent)")
    a.set_ylabel("ROF (ratio \u00f7 same-batch parent ratio)")
    a.set_title("Within-batch rank: the triple is the pivotal point", fontsize=11.5,
                color=INK, pad=8)
    style_axes(a, grid="both"); panel(a, "A", dx=-.11)
    a.legend(loc="lower right", fontsize=8.2, frameon=True, framealpha=.93)

    # ---- 面板 B：27 位饱和
    xr = [num(r["ret"]) for r in singles27]
    yr = [num(r["rof"]) for r in singles27]
    gain = [r for r in singles27 if num(r["rof"]) >= 1.13]
    flat = [r for r in singles27 if num(r["rof"]) < 1.13]
    b.scatter([num(r["ret"]) for r in flat], [num(r["rof"]) for r in flat], s=110,
              color=GREY, edgecolor="white", linewidth=1.1, zorder=4, label="no gain over parent")
    b.scatter([num(r["ret"]) for r in gain], [num(r["rof"]) for r in gain], s=140, marker="D",
              color=ORANGE, edgecolor="white", linewidth=1.1, zorder=5, label="gain, at an activity cost")
    for r in singles27:
        b.annotate(r["mut"], (num(r["ret"]), num(r["rof"])), textcoords="offset points",
                   xytext=(8, -3), fontsize=9, color=DARK)
    b.axhline(1.0, color=RULE, ls=":", lw=1.6, zorder=2)
    b.axvline(.90, color=GREEN, ls="--", lw=1.5, zorder=2)
    b.text(.90, b.get_ylim()[0], " 0.90 retention", va="bottom", ha="left", fontsize=8.8, color=GREEN)
    b.set_xlabel("activity retention (c.388 vs the batch parent)")
    b.set_ylabel("ROF")
    b.set_title("Position-27 saturation: 10 substitutions", fontsize=11.5, color=INK, pad=8)
    style_axes(b, grid="both"); panel(b, "B", dx=-.09)
    legend_below(fig, *b.get_legend_handles_labels(), ncol=3, y=0.185, fontsize=9)

    # ---- 面板 C：−1 轴（c.295）
    order = sorted(singles27, key=lambda r: -(num(r["c295"]) or 0))
    labels = [r["mut"] for r in order]
    vals = [num(r["c295"]) for r in order]
    xs2 = np.arange(len(order))
    cols = [ORANGE if r["c295_not_detected"] == "TRUE" else BLUE for r in order]
    c.bar(xs2, vals, .62, color=cols, edgecolor="white", linewidth=.7, zorder=3)
    pv = num(parent["c295"])
    c.axhline(pv, color=DARK, ls="--", lw=1.6, zorder=4)
    c.text(len(order) - .5, pv, f" parent {pv:.3f} ", va="bottom", ha="right",
           fontsize=9, color=DARK)
    for x_, r in zip(xs2, order):
        if r["c295_not_detected"] == "TRUE":
            c.text(x_, .012, "n.d.", ha="center", fontsize=8.4, color=ORANGE, weight="bold")
    c.set_xticks(xs2); c.set_xticklabels(labels, **TICK)
    c.set_ylim(0, max(pv, max(vals)) * 1.28)
    c.set_ylabel("c.295 editing (ACA-class, −1 layer)")
    c.set_title("7 of 10 fall below detection here", fontsize=11.5, color=INK, pad=8)
    style_axes(c, grid="y"); panel(c, "C", dx=-.10)
    legend_below(fig, [Line2D([], [], marker="s", ls="", ms=11, color=BLUE, label="detected"),
                       Line2D([], [], marker="s", ls="", ms=11, color=ORANGE,
                              label="not detected (below the 5% floor)")],
                 None, ncol=3, y=0.115, fontsize=9)

    titles(fig, "A different library background: the triple still leads its panel, and position 27 is saturated",
           "All three panels come from one batch of 64 samples (29 groups) built in a library background "
           "different from the earlier batches, so only within-batch comparisons are made here.")
    footnotes(fig, [
        "A  ratios are not comparable across batches built in different backgrounds, so the comparison is made within this panel; ROF divides each construct's ratio by this batch's parent ratio.",
        "B  the three substitutions that raise ROF above 1.13 — 27I, 27V and 27E — all retain only 0.74–0.80 activity.",
        "B  the triple is the only construct near the top on both axes: the highest ROF among constructs retaining at least 0.95 activity, and the highest retention among those reaching ROF 1.20.",
        "C  the parent edits c.295 at 0.309; seven of the ten position-27 substitutions suppress it below the detection floor.",
    ], **FOOT)
    return save_checked(fig, os.path.join(ASSETS, "figure_16_replication_saturation.png"))
