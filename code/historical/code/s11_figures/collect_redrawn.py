# -*- coding: utf-8 -*-
"""
把本轮重绘的 10 张图收集到一个独立交付文件夹，并生成清单。

用法：uv run python collect_redrawn.py
产出：../APOBEC_DryLab_重绘图/  （10 张 PNG + README.md + manifest.json）
"""
import hashlib, json, os, shutil, sys, datetime
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "APOBEC_DryLab_assets")
OUT = os.path.abspath(os.path.join(HERE, "..", "APOBEC_DryLab_重绘图"))

FIGS = [
    ("figure_2_cp_deviation.png", "Figure 2", "Contact-probability deviation diagnosis",
     ["A  three deviation descriptors vs the ±3 SD noise floor",
      "B  protein–target-C deviation against measured activity"],
     "results/CP偏离_汇总.csv"),
    ("figure_3_ddcp_heatmap.png", "Figure 3", "Per-residue ΔΔCP heat map",
     ["single panel  22 residues × all constructs"],
     "results/突变体基线ΔCP_全199残基.xlsx (sheet 2_ΔΔCP矩阵)"),
    ("figure_4_negctrl_diagnosis.png", "Figure 4", "Negative-control diagnosis",
     ["A  catalytic C4N4–E72 distance, coloured by functional class",
      "B  three deviation descriptors vs the ±3 SD noise floor"],
     "results/阴性对照_偏离与PCA.csv"),
    ("figure_5_negctrl_pca.png", "Figure 5", "Control constructs in PC space and by D_M",
     ["A  PC1–PC2 by functional class (key constructs labelled)",
      "B  D_M for all constructs vs the wild-type null"],
     "results/阴性对照_PC坐标.csv, results/阴性对照_DM.csv"),
    ("figure_6_protein_only_pca.png", "Figure 6", "Protein-only models across feature sets",
     ["A  D_M within the protein-only models, by feature set",
      "B  dead/active classification accuracy"],
     "results/纯蛋白_分离度.csv, results/纯蛋白_分类表现.csv"),
    ("figure_7_protein_only_vs_complex.png", "Figure 7", "Complex vs protein-only deviation",
     ["single panel  paired bars per construct, T31D and E72A annotated"],
     "results/阴性对照_DM.csv, results/纯蛋白_分离度.csv"),
    ("figure_8_single_site_validation.png", "Figure 8", "Single-site saturation",
     ["single panel  +1 ratio vs activity retention, 102 single mutants"],
     "results/experimental_ranking.csv"),
    ("figure_9_targeting_ratio.png", "Figure 9", "Behaviour of the targeting ratio",
     ["A  ratio vs on-target activity, with activity strata",
      "B  ratio vs total off-target editing, with both coefficients"],
     "results/GCG_vs_off_ranking_WT.csv"),
    ("figure_10_candidate_overview.png", "Figure 10", "Next-round candidate overview",
     ["A  group sizes",
      "B  priority composition within each group"],
     "results/下一步实验突变候选表_61组.xlsx (sheet 突变候选表_61组)"),
    ("figure_11_method_retrospective.png", "Figure 11", "Retrospective test of the AiCE filter",
     ["A  positions surviving the frequency threshold",
      "B  sampling frequency of the four contested substitutions"],
     "Apobec前期设计附件/全长反设计.fa, results/AiCE过滤器_位点级.csv"),
]

STYLE = {
    "font": "Noto Sans SC (static Regular/Bold instantiated from the system variable font)",
    "rcParams": {"font.size": 10, "axes.titlesize": 12, "axes.unicode_minus": False,
                 "pdf.fonttype": 42, "svg.fonttype": "path"},
    "palette": {"blue": "#246A9A", "orange": "#B46A19", "green": "#347565",
                "grey": "#64748B", "ink": "#18334B",
                "purple_extension": "#6D4C8E"},
    "layout": {"figure_width_in": 15.8, "dpi": 300, "bbox_inches": None,
               "max_panels_per_figure": 2, "legend": "below the panels (figure-level)"},
    "guards": ["no CJK characters anywhere in the figure text",
               "every axes must contain plotted data (no empty panels)"],
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for fn, num_, title, panels, src in FIGS:
        s = os.path.join(SRC, fn)
        if not os.path.exists(s):
            print(f"  缺失 {fn}")
            continue
        d = os.path.join(OUT, fn)
        shutil.copy2(s, d)
        rows.append({"file": fn, "figure": num_, "title": title, "panels": panels,
                     "source_data": src, "sha256": sha256(d),
                     "size_bytes": os.path.getsize(d)})
        print(f"  ✓ {fn}")

    manifest = {
        "round": "2026-09-23 redraw",
        "purpose": "All figures redrawn for the APOBEC Dry Lab page, in the plotting "
                   "conventions used for the clustering figures.",
        "count": len(rows),
        "style": STYLE,
        "figures": rows,
        "generator": "plot_drylab_figures.py (+ orca_drylab_style.py)",
        "note": "Figure 1 and Figures 12–14 on the page are the clustering figures produced "
                "outside this round and are not reproduced here.",
    }
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    lines = ["# APOBEC Dry Lab —— 本轮重绘图（2026-09-23）", "",
             f"共 **{len(rows)}** 张，均为 4740 px 宽（15.8 in × 300 dpi），白底，"
             "图内文字全英文，图例统一置于面板下方。", "",
             "样式依据队友聚类图的绘图规范（字体、调色板、版式），"
             "规格见 `manifest.json` 的 `style` 字段。", "",
             "| 图 | 标题 | 面板 | 数据来源 |", "|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['figure']} | {r['title']} | {'；'.join(r['panels'])} | `{r['source_data']}` |")
    lines += ["", "## 校验", "",
              "- 图内文字经 CJK 字符断言，构建时若有中文会直接报错、不出图。",
              "- 每个面板经空面板断言，若坐标轴内无任何数据图元会报错。",
              "- 每个文件的 SHA-256 记录在 `manifest.json`。", "",
              "## 重绘方式", "",
              "```bash",
              "uv run --with matplotlib --with numpy --with openpyxl --with scipy python plot_drylab_figures.py",
              "uv run python collect_redrawn.py",
              "```", "",
              "页面用图（供 docx 嵌入）另存于 `../APOBEC_DryLab_Complete/APOBEC_DryLab_assets/`，与本目录内容一致。"]
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n写入 {OUT}")
    print(f"  {len(rows)} 张 PNG + README.md + manifest.json")


if __name__ == "__main__":
    main()
