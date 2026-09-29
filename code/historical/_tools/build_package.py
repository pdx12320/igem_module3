# -*- coding: utf-8 -*-
"""
把本项目的全部工作代码整理成一个可提交的工作流包。

产出：APOBEC_代码工作流包/
      ├── README.md / WORKFLOW.md / MANIFEST.md / DATA.md / requirements.txt
      ├── code/<阶段>/<原文件名>.py      （保留原文件名，便于与报告交叉引用）
      ├── code/_cancelled/               （已废止但保留记录的脚本）
      └── shell/                          （两个 shell 脚本）

用法：uv run python _build_pkg.py
"""
import ast, io, os, re, shutil, sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "APOBEC_代码工作流包")
CODE = os.path.join(OUT, "code")

# ---------------------------------------------------------------- 阶段定义
STAGES = [
    ("s0_env", "S0 环境、清单与共享工具",
     "把原始 AF3 输出归一化成统一清单，并定义全部下游脚本共用的工具函数。"),
    ("s1_structure", "S1 结构解析与界面刻画",
     "对 AF3 cif 做质控、接触统计、界面相互作用与突变库生成；cif→pdb 为服务器准备的格式转换。"),
    ("s2_af3_submit", "S2 AF3 任务生成",
     "按不同模型（复合物 / 阴性对照 / 纯蛋白 / 多 seed 拆分）生成 AlphaFold3 提交 JSON。"),
    ("s3_design_models", "S3 设计模型复核（mCSM-NA / PremPRI）",
     "生成服务器输入清单，回收结果并重新排序。"),
    ("s4_contacts", "S4 接触分解、保守性与共进化",
     "回答「哪些残基在读取碱基」「某位点能不能动」「能朝哪个方向变」。"),
    ("s5_cp", "S5 接触概率（CP/ΔCP）与结构几何",
     "以 AF3 接触概率为核心的结构描述量：ΔCP、空间聚类、催化几何、基线矩阵。"),
    ("s6_controls", "S6 阴性对照与纯蛋白对照",
     "引入答案已知的对照，检验 CP/偏离度究竟在衡量什么。"),
    ("s7_wetlab", "S7 湿实验数据整合与干湿互证",
     "把测序结果并入分析，做预测与实测的对照、监督学习与指标重评价。"),
    ("s8_offtarget", "S8 脱靶扫描与指标偏倚",
     "从 BAM 找 C→U 事件、构建脱靶矩阵、检验靶向比的系统性偏倚。"),
    ("s9_candidates", "S9 候选设计与回溯检验",
     "产出下一轮候选表，并对已发表方法做回溯检验。"),
    ("s10_batches", "S10 批次实测数据分析",
     "三批补充突变（37 组 / 64 样本）的逐组分析与绘图用表导出。"),
    ("s11_figures", "S11 绘图",
     "共享绘图样式 + 各类图的生成脚本。"),
    ("s12_documents", "S12 文档与交付物生成",
     "Markdown → Word/PPT 的生成器，以及论文页、DBTL 稿、绘图数据包导出。"),
]

# 文件 → 阶段
ASSIGN = {
    "s0_env": ["af_utils.py", "00_manifest.py"],
    "s1_structure": ["01_qc.py", "02_contacts.py", "03_summary.py", "04_interactions.py",
                     "05_combinations.py", "06_cif2pdb.py", "make_pml.py"],
    "s2_af3_submit": ["18_make_af3_submit.py", "42_make_negctrl_submit.py",
                      "44_split_seeds.py", "45_make_pure_protein_submit.py"],
    "s3_design_models": ["make_mcsmna_lists.py", "07_mcsm_rerank.py", "08_prempri_rerank.py"],
    "s4_contacts": ["10_contact_decomposition.py", "11_conservation_coevolution.py",
                    "12_mutation_direction.py", "13_pssm_validation.py",
                    "14_coevolution_combo.py"],
    "s5_cp": ["15_cp_dcp_analysis.py", "16_test_contact_cp.py", "17_test2_dcp.py",
              "19_mut_cp.py", "20_site_spatial.py", "21_targetC_catalytic_dist.py",
              "22_best_combo_pairs.py", "23_dE72_regression.py", "52_mutant_baseline_dcp.py"],
    "s6_controls": ["36_intra_cp_compare.py", "37_cp_diagnosis_fig.py", "38_cp_pca.py",
                    "41_negative_controls.py", "43_negctrl_analysis.py",
                    "46_pure_protein_analysis.py", "47_pc_interpretation.py",
                    "48_lr_and_pos31.py", "49_verify_intra_cp.py"],
    "s7_wetlab": ["09_experimental_validation.py", "23_integrate_all.py",
                  "28_GCG_target_analysis.py", "29_GCG_sum_ranking.py",
                  "30_GCG_vs_off_WT.py", "31_wetlab_mutation_list.py",
                  "35_dry_vs_wet_ranking.py", "50_ml_fitness_prediction.py",
                  "51_metric_reevaluation.py"],
    "s8_offtarget": ["02_find_CU_offtarget.py", "24_offtarget_scan.py",
                     "25_offtarget_screen.py", "26_offtarget_matrix.py",
                     "27_offtarget_matrix_noP.py", "58_targeting_ratio_rerank.py"],
    "s9_candidates": ["33_next_round_candidates.py", "analyze_pos29_screen.py",
                      "55_aice_beta_gamma_retro.py"],
    "s10_batches": ["analyze_new_batch.py", "analyze_batch3.py"],
    "s11_figures": ["34_report_figures.py", "57_make_wiki_figures.py",
                    "plot_distances.py"],
    "s12_documents": ["32_drylab_note.py", "53_make_full_chain_report.py",
                      "54_make_full_chain_ppt.py", "56_make_dbtl.py",
                      "gen_report_docx.py", "gen_report_pptx.py",
                      "make_mutability_report.py", "make_tutor_report.py",
                      "make_word_report.py", "make_presentation.py",
                      "make_presentation_v2.py", "make_presentation_combined.py",
                      "docx_build.py", "pptx_build.py", "pptx_slides.py",
                      "export_drylab_plotdata.py"],
}

# 来自「文案数据图表整理/」子目录、需一并收录的文件
EXTRA = [
    ("s11_figures", "文案数据图表整理/scientific-figures/orca_plot.py", "orca_plot.py"),
    ("s11_figures", "文案数据图表整理/scientific-figures/plot_cycles.py", "plot_cycles.py"),
    ("s11_figures", "文案数据图表整理/APOBEC_DryLab_Complete/orca_drylab_style.py",
     "orca_drylab_style.py"),
    ("s11_figures", "文案数据图表整理/APOBEC_DryLab_Complete/plot_drylab_figures.py",
     "plot_drylab_figures.py"),
    ("s11_figures", "文案数据图表整理/APOBEC_DryLab_Complete/collect_redrawn.py",
     "collect_redrawn.py"),
    ("s12_documents", "文案数据图表整理/APOBEC_DryLab_Complete/make_drylab_docx.py",
     "make_drylab_docx.py"),
    ("s12_documents", "文案数据图表整理/APOBEC_DryLab_Complete/make_bilingual_docx.py",
     "make_bilingual_docx.py"),
    ("s12_documents", "文案数据图表整理/make_wiki_docx.py", "make_wiki_docx.py"),
]

CANCELLED = [
    ("_已取消_纯蛋白分析/39_make_protein_only_submit.py", "39_make_protein_only_submit.py"),
    ("_已取消_纯蛋白分析/40_protein_only_pca.py", "40_protein_only_pca.py"),
]

SHELL = ["00_setup_reference.sh", "01_download_align.sh"]

# ---------------------------------------------------------------- 元信息提取
PATH_RE = re.compile(r"""["']([^"'\n]{3,90}?\.(?:csv|xlsx|xls|json|docx|pptx|png|pdf|fa|fasta|txt|pml|tsv|cif|pdb))["']""")
WRITE_HINT = ("savefig", "to_csv", "to_excel", ".save(", "writerow", "write_text",
              "shutil.copy", "make_archive", "open(")


def analyse(path):
    src = io.open(path, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
        doc = (ast.get_docstring(tree) or "").strip().split("\n")[0].strip()
    except Exception:
        doc = ""
    imports = set()
    try:
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    imports.add(a.name.split(".")[0])
            elif isinstance(n, ast.ImportFrom) and n.module:
                imports.add(n.module.split(".")[0])
    except Exception:
        pass
    STD = {"os", "sys", "re", "io", "csv", "json", "math", "ast", "time", "shutil",
           "hashlib", "collections", "itertools", "random", "subprocess", "glob",
           "argparse", "pathlib", "datetime", "statistics", "typing", "warnings",
           "textwrap", "unicodedata", "difflib", "tempfile", "zipfile", "xml",
           "importlib", "functools", "operator", "string", "copy", "pickle", "html"}
    third = sorted(i for i in imports if i not in STD and not i.startswith("_")
                   and i not in {"af_utils", "docx_build", "pptx_build", "pptx_slides",
                                 "orca_plot", "orca_drylab_style", "plot_drylab_figures"})
    local = sorted(i for i in imports if i in {"af_utils", "docx_build", "pptx_build",
                                               "pptx_slides", "orca_plot",
                                               "orca_drylab_style"})
    # 读写文件
    reads, writes = set(), set()
    for line in src.split("\n"):
        for m in PATH_RE.finditer(line):
            p = m.group(1)
            if any(k in line for k in ("savefig", "to_csv", "to_excel", ".save(",
                                       '"w"', "'w'", "writerow", "write_text", "make_archive")):
                writes.add(p)
            else:
                reads.add(p)
    writes -= reads
    return dict(doc=doc, third=third, local=local,
                reads=sorted(reads)[:6], writes=sorted(writes)[:6],
                lines=src.count("\n") + 1)


# ---------------------------------------------------------------- 建包
if os.path.exists(OUT):
    shutil.rmtree(OUT, ignore_errors=True)   # 目录可能被资源管理器占用，忽略失败
os.makedirs(CODE, exist_ok=True)
for d, _, _ in STAGES:
    os.makedirs(os.path.join(CODE, d))
os.makedirs(os.path.join(CODE, "_cancelled"))
os.makedirs(os.path.join(OUT, "shell"))

recs = []
missing = []
for stage, files in ASSIGN.items():
    for f in files:
        src = os.path.join(HERE, f)
        if not os.path.exists(src):
            missing.append(f); continue
        shutil.copy2(src, os.path.join(CODE, stage, f))
        recs.append((stage, f, analyse(src), ""))

for stage, src, name in EXTRA:
    p = os.path.join(HERE, src)
    if not os.path.exists(p):
        missing.append(name); continue
    shutil.copy2(p, os.path.join(CODE, stage, name))
    recs.append((stage, name, analyse(p), "（原位于 文案数据图表整理/）"))

for src, name in CANCELLED:
    p = os.path.join(HERE, src)
    if not os.path.exists(p):
        missing.append(name); continue
    shutil.copy2(p, os.path.join(CODE, "_cancelled", name))
    recs.append(("_cancelled", name, analyse(p), "**已废止，仅存档**"))

for f in SHELL:
    p = os.path.join(HERE, f)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(OUT, "shell", f))

print("已复制", len(recs), "个脚本；缺失：", missing or "无")

# ---------------------------------------------------------------- MANIFEST
lines = ["# 脚本清单｜APOBEC 编辑模块 · 计算工作流", "",
         f"共收录 **{len(recs)} 个 Python 脚本** + 2 个 shell 脚本。"
         "文件名保留原始编号，便于与报告正文中的引用对应。", "",
         "> 「读取 / 写出」两列由脚本源码中的路径字面量自动提取，仅供参考；"
         "完整的数据依赖见 `DATA.md`。", ""]
for stage, title, desc in STAGES:
    sub = [r for r in recs if r[0] == stage]
    if not sub:
        continue
    lines += [f"## {title}", "", desc, ""]
    for st, f, m, note in sorted(sub, key=lambda x: x[1]):
        lines += [f"### `{f}`", "",
                  f"- **用途**：{m['doc'] or '（源码无模块 docstring）'}",
                  f"- **规模**：{m['lines']} 行"
                  + (f"｜第三方依赖：{', '.join(m['third'])}" if m['third'] else "｜仅标准库"),
                  f"- **读取**：{'、'.join('`'+x+'`' for x in m['reads']) or '—'}",
                  f"- **写出**：{'、'.join('`'+x+'`' for x in m['writes']) or '—'}"]
        if m['local']:
            lines.append(f"- **依赖本项目模块**：{', '.join(m['local'])}")
        if note:
            lines.append(f"- **备注**：{note}")
        lines.append("")
lines += ["## `_cancelled/` 已废止脚本", ""]
for st, f, m, note in recs:
    if st != "_cancelled":
        continue
    lines += [f"### `{f}`（已废止）", "",
              f"- **原用途**：{m['doc']}",
              f"- **废止原因**：由 `45_make_pure_protein_submit.py` / `46_pure_protein_analysis.py` 取代。",
              ""]
io.open(os.path.join(OUT, "MANIFEST.md"), "w", encoding="utf-8").write("\n".join(lines))

# ---------------------------------------------------------------- requirements
third_all = set()
for _, _, m, _ in recs:
    third_all |= set(m["third"])
PKG = {"numpy": "numpy", "scipy": "scipy", "matplotlib": "matplotlib",
       "openpyxl": "openpyxl", "docx": "python-docx", "pptx": "python-pptx",
       "sklearn": "scikit-learn", "gemmi": "gemmi", "pysam": "pysam",
       "pydssp": "pydssp", "fontTools": "fonttools", "PIL": "pillow",
       "pandas": "pandas", "Bio": "biopython"}
req = ["# APOBEC 编辑模块 · 计算工作流 依赖清单",
       "# 安装：uv pip install -r requirements.txt  或  pip install -r requirements.txt",
       "# 说明：多数分析脚本只用标准库，下列依赖按阶段可选。",
       "#",
       "# —— 核心（多数分析/绘图脚本需要）——"]
core = ["numpy", "scipy", "matplotlib", "openpyxl"]
for n in core:
    req.append(PKG[n])
req += ["#", "# —— 文档与演示生成 ——", PKG["docx"], PKG["pptx"],
        "#", "# —— 按需（仅个别脚本使用）——"]
for name in sorted(third_all):
    if PKG.get(name) and PKG[name] not in core and PKG[name] not in (
            PKG["docx"], PKG["pptx"]):
        req.append(PKG[name])
req += ["fonttools  # plot_drylab_figures.py：可变字体实例化",
        "#", "# 注意：pptx_build.py 使用 PowerPoint COM（仅 Windows，需已安装 Office）。"]
io.open(os.path.join(OUT, "requirements.txt"), "w", encoding="utf-8").write("\n".join(req) + "\n")
print("MANIFEST.md / requirements.txt 已生成")
