# -*- coding: utf-8 -*-
"""
共享绘图样式 —— 严格对齐队友聚类图的视觉规范。

来源（队友脚本 skill_clustering/code/plot_pipeline_comparison.py）：
  font.family   = Noto Sans CJK SC（本机以同族 Noto Sans SC 替代）
  font.size 10 / axes.titlesize 12；axes.unicode_minus False
  pdf.fonttype 42 / ps.fonttype 42 / svg.fonttype path
  figure/axes/savefig facecolor 均为 white
  PNG dpi 300，保存时 bbox_inches=None（版面由 gridspec 显式控制）
  调色板 BLUE #246A9A / ORANGE #B46A19 / GREEN #347565 / GREY #64748B / INK #18334B
  浅色填充 #E8EAEE #D6E6F2 #F4D5B6 #D0E6DE #DCCFEA
  网格 #DDE3E8 lw .7；轴线 #A6B2BD；tick length 0, pad 7
  版式：左上 fig.text 标题（20, INK）→ 副标题（11, GREY）→ 底部脚注若干行
"""
import os
import re
import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager as fm
from matplotlib.text import Text
import matplotlib.pyplot as plt

# ---- 调色板（与队友一致） ----
BLUE = "#246A9A"
ORANGE = "#B46A19"
GREEN = "#347565"
GREY = "#64748B"
INK = "#18334B"

FILL_BLUE = "#D6E6F2"
FILL_ORANGE = "#F4D5B6"
FILL_GREEN = "#D0E6DE"
FILL_GREY = "#E8EAEE"
FILL_PURPLE = "#DCCFEA"

GRID = "#DDE3E8"
SPINE = "#A6B2BD"
FAINT = "#C5CED6"
RULE = "#7E8D99"
DARK = "#273444"
# 队友调色板之外的唯一扩展：第 5 个功能类别（WT 换底物）需要一个可区分的饱和色，
# 取自其热图配色中的紫色族。
PURPLE = "#6D4C8E"

# ---- 功能类别配色 ----
# 说明：负数对照表里有 6 类。前 4 类用调色板主色；「设计但未实测的失活对照」
# 用白底＋橙描边＋斜线阴影，以在视觉上区别于「已实测失活」；野生型参照用紫色。
CLASS_COLORS = {
    "Active": GREEN,
    "Inactive": ORANGE,
    "Partially inactive": BLUE,
    "Not tested": GREY,
    "New inactive control (not measured)": "white",
    "Wild-type reference": PURPLE,
}

CLASS_STYLE = {
    "Active": {"color": GREEN, "marker_face": GREEN, "marker_edge": "white"},
    "Inactive": {"color": ORANGE, "marker_face": ORANGE, "marker_edge": "white"},
    "Partially inactive": {"color": BLUE, "marker_face": BLUE, "marker_edge": "white"},
    "Not tested": {"color": GREY, "marker_face": GREY, "marker_edge": "white"},
    # 白底＋橙描边＋斜线阴影：与「已实测失活」的实心橙明确区分
    "New inactive control (not measured)": {"color": "white", "edge": ORANGE, "hatch": "///",
                                            "marker_face": "white", "marker_edge": ORANGE},
    "Wild-type reference": {"color": PURPLE, "marker_face": PURPLE, "marker_edge": "white"},
}


def class_handles(classes, order=None):
    """为功能类别图例生成 Patch 句柄（白底类带描边与阴影）。"""
    from matplotlib.patches import Patch
    seen = [k for k in (order or CLASS_STYLE) if k in classes]
    return [Patch(facecolor=CLASS_STYLE[k]["color"],
                  edgecolor=CLASS_STYLE[k].get("edge", "white"),
                  hatch=CLASS_STYLE[k].get("hatch"), label=k) for k in seen], seen


def _pick_font():
    """队友用 Noto Sans CJK SC。本机只有可变字重的 Noto Sans SC（matplotlib 只能取到
    Thin），因此优先注册由该可变字体实例化出的 Regular/Bold 静态字重；缺失时回退。"""
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    for fn in ("NotoSansSC-Regular.ttf", "NotoSansSC-Bold.ttf"):
        p = os.path.join(here, "fonts", fn)
        if os.path.exists(p):
            fm.fontManager.addfont(p)
    avail = {f.name for f in fm.fontManager.ttflist}
    for name in ("Noto Sans CJK SC", "Noto Sans SC", "Source Han Sans SC",
                 "Microsoft YaHei", "SimHei", "DejaVu Sans"):
        if name in avail:
            return name
    return "DejaVu Sans"


FONT = _pick_font()


def apply_rc():
    plt.rcParams.update({
        "font.family": FONT,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10.5,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "axes.unicode_minus": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "path",
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def canvas(w=15.8, h=9.1, left=.075, right=.975, bottom=.155, top=.845,
           nrows=1, ncols=1, wspace=.22, hspace=.42, width_ratios=None, height_ratios=None):
    """建画布并留出左上标题区与底部脚注区。"""
    apply_rc()
    fig = plt.figure(figsize=(w, h))
    gs = fig.add_gridspec(nrows, ncols, left=left, right=right, bottom=bottom, top=top,
                          wspace=wspace, hspace=hspace,
                          width_ratios=width_ratios, height_ratios=height_ratios)
    axes = [[fig.add_subplot(gs[i, j]) for j in range(ncols)] for i in range(nrows)]
    if nrows == 1 and ncols == 1:
        return fig, axes[0][0]
    if nrows == 1:
        return fig, axes[0]            # 1×N → 扁平列表
    if ncols == 1:
        return fig, [r[0] for r in axes]   # N×1 → 扁平列表
    return fig, axes                   # M×N → 二维


def titles(fig, title, subtitle=None, x=.035):
    """左上标题块，字号与位置对齐队友版式。"""
    fig.text(x, .962, title, fontsize=20, color=INK)
    if subtitle:
        fig.text(x, .921, subtitle, fontsize=11, color=GREY)


def footnotes(fig, lines, x=.035, start=.088, step=.028):
    """底部脚注若干行（自上而下）。"""
    y = start
    for t in lines:
        fig.text(x, y, t, fontsize=10 if not t.startswith("†") else 10, color=GREY if t.startswith("†") else DARK)
        y -= step


def style_axes(ax, grid=None, box=False):
    """统一轴线与网格；tick length 0 / pad 7。"""
    for side in ("top", "right"):
        ax.spines[side].set_visible(box)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(SPINE)
        ax.spines[side].set_linewidth(1.0)
    ax.tick_params(axis="both", length=0, pad=7)
    ax.set_axisbelow(True)
    if grid == "y":
        ax.grid(axis="y", color=GRID, lw=.7)
    elif grid == "x":
        ax.grid(axis="x", color=GRID, lw=.7)
    elif grid == "both":
        ax.grid(axis="both", color=GRID, lw=.7)


def panel(ax, letter, dx=-.085, dy=.055):
    """面板字母，置于坐标轴左上外侧。"""
    ax.text(dx, 1 + dy, letter, transform=ax.transAxes, fontsize=13,
            fontweight="bold", color=INK, va="bottom", ha="left")


def save(fig, path):
    fig.savefig(path, dpi=300, facecolor="white", bbox_inches=None)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# 图例置于面板下方：避免与数据点/柱体重叠
# ---------------------------------------------------------------------------
def legend_below(fig, handles=None, labels=None, ncol=3, y=0.175, fontsize=10):
    """在整张图下方居中放置统一图例（不进入任何坐标轴区域）。"""
    if not handles:
        fig.legend(loc="upper center", bbox_to_anchor=(0.5, y),
                   ncol=ncol, frameon=False, fontsize=fontsize)
        return
    if labels is None:
        labels = [h.get_label() for h in handles]
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, y),
               ncol=ncol, frameon=False, fontsize=fontsize)


# ---------------------------------------------------------------------------
# 图内文字必须全英文：绘制完成后逐条检查，发现中日韩字符即报错
# ---------------------------------------------------------------------------
_CJK = re.compile(r"[⺀-⻿　-〿぀-ヿ㐀-䶿"
                  r"一-鿿豈-﫿︰-﹏＀-￯]")


def assert_english(fig, name="figure"):
    bad = []
    for t in fig.findobj(match=Text):
        s = t.get_text()
        if s and _CJK.search(s):
            bad.append(s)
    if bad:
        raise ValueError(f"{name}: non-English text inside the figure: {bad[:6]}")


def assert_drawn(fig, name="figure"):
    """每个坐标轴都必须至少有一个承载数据的图元，否则视为空面板。"""
    empty = []
    for i, ax in enumerate(fig.get_axes()):
        if not (ax.patches or ax.lines or ax.collections or ax.images):
            empty.append(i)
    if empty:
        raise ValueError(f"{name}: panel(s) {empty} contain no plotted data")


def save_checked(fig, path):
    name = os.path.basename(path)
    assert_english(fig, name)
    assert_drawn(fig, name)
    return save(fig, path)
