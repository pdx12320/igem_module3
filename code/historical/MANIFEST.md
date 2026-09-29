# 脚本清单｜APOBEC 编辑模块 · 计算工作流

共收录 **88 个 Python 脚本** + 2 个 shell 脚本。文件名保留原始编号，便于与报告正文中的引用对应。

> 「读取 / 写出」两列由脚本源码中的路径字面量自动提取，仅供参考；完整的数据依赖见 `DATA.md`。

## S0 环境、清单与共享工具

把原始 AF3 输出归一化成统一清单，并定义全部下游脚本共用的工具函数。

### `00_manifest.py`

- **用途**：阶段 0 —— 清单归一化
- **规模**：73 行｜仅标准库
- **读取**：`*_job_request.json`、`*_model_[0-4].cif`、`写入 results/manifest.csv`
- **写出**：`manifest.csv`
- **依赖本项目模块**：af_utils

### `af_utils.py`

- **用途**：AF3 cif 质控 + 接触分析 共享工具（纯标准库，无第三方依赖）。
- **规模**：153 行｜仅标准库
- **读取**：—
- **写出**：—

## S1 结构解析与界面刻画

对 AF3 cif 做质控、接触统计、界面相互作用与突变库生成；cif→pdb 为服务器准备的格式转换。

### `01_qc.py`

- **用途**：阶段 1 —— 质控（标准档）
- **规模**：180 行｜仅标准库
- **读取**：`*_summary_confidences_{rank}.json`、`manifest.csv`
- **写出**：`qc_report.csv`
- **依赖本项目模块**：af_utils

### `02_contacts.py`

- **用途**：阶段 2 —— +1 位接触分析（双口径）
- **规模**：115 行｜仅标准库
- **读取**：`manifest.csv`、`qc_report.csv`
- **写出**：`contacts_long.csv`、`key_distances.csv`
- **依赖本项目模块**：af_utils

### `03_summary.py`

- **用途**：阶段 3 —— 汇总统计与 G/A 对比
- **规模**：149 行｜仅标准库
- **读取**：`\n写入 results/contacts_frequency.csv, results/g_a_comparison.csv`、`contacts_long.csv`
- **写出**：`contacts_frequency.csv`、`g_a_comparison.csv`
- **依赖本项目模块**：af_utils

### `04_interactions.py`

- **用途**：阶段 4 —— +1 位蛋白-RNA 相互作用分析（PISA 等价：氢键计数 + 界面埋藏面积）
- **规模**：245 行｜第三方依赖：numpy
- **读取**：`manifest.csv`、`qc_report.csv`、`写入 results/filtered_residues.csv`、`埋藏面积表写入 results/buried_area_per_residue.csv`、`氢键表写入 results/hbonds_per_residue.csv`
- **写出**：`buried_area_per_residue.csv`、`filtered_residues.csv`、`hbonds_per_residue.csv`
- **依赖本项目模块**：af_utils

### `05_combinations.py`

- **用途**：阶段 5 —— 单突变库 + 组合突变生成与合理性筛选（目标 ~1000 组）
- **规模**：125 行｜仅标准库
- **读取**：`输出前 {len(top)} 组 -> results/combinations_top1000.csv`
- **写出**：`combinations_top1000.csv`

### `06_cif2pdb.py`

- **用途**：阶段 6 —— cif -> pdb 批量转换（为 mCSM-NA 等服务器准备结构文件）
- **规模**：100 行｜第三方依赖：gemmi
- **读取**：`results/manifest.csv`、`results/qc_report.csv`
- **写出**：—

### `make_pml.py`

- **用途**：生成 PyMOL 可视化抽查脚本（.pml）
- **规模**：73 行｜仅标准库
- **读取**：`]}_rank0.pml`、`]}_rank0.png`、`manifest.csv`
- **写出**：—
- **依赖本项目模块**：af_utils

## S2 AF3 任务生成

按不同模型（复合物 / 阴性对照 / 纯蛋白 / 多 seed 拆分）生成 AlphaFold3 提交 JSON。

### `18_make_af3_submit.py`

- **用途**：阶段 18 —— 生成 AF3 server 提交 JSON：突变 APOBEC × GUGCGCG / GUGCACG
- **规模**：82 行｜仅标准库
- **读取**：`K30H_GCG.json`、`{name}_{rna_key}.json`
- **写出**：`WT_{rna_key}.json`

### `42_make_negctrl_submit.py`

- **用途**：阶段 42 —— 生成「阴性对照」AF3 提交文件（用于加入 PCA 与偏离诊断）
- **规模**：97 行｜仅标准库
- **读取**：`\n面板清单另存 {OUT}/_panel.csv`、`af3_submit/WT_GCG.json`、`{FNAME.get(name, name)}_{rna_tag}.json`
- **写出**：`_panel.csv`

### `44_split_seeds.py`

- **用途**：阶段 44 —— 把多 seed 的 AF3 提交文件拆成「一个 JSON 一个 seed」
- **规模**：103 行｜仅标准库
- **读取**：`{base}_s{int(s):02d}.json`、`清单已写入 提交清单_AF3.csv`
- **写出**：`提交清单_AF3.csv`

### `45_make_pure_protein_submit.py`

- **用途**：阶段 45 —— 生成「纯蛋白模型」AF3 提交文件（只给蛋白链，不给 RNA），共 60 个单 seed JSON
- **规模**：119 行｜仅标准库
- **读取**：`\n清单：{OUT}/_提交清单.csv`、`af3_submit/WT_GCG.json`、`{base}_s{int(s):02d}.json`
- **写出**：`_提交清单.csv`

## S3 设计模型复核（mCSM-NA / PremPRI）

生成服务器输入清单，回收结果并重新排序。

### `07_mcsm_rerank.py`

- **用途**：阶段 7 —— mCSM-NA 结果解读与重新排序（单体 + 组合）
- **规模**：127 行｜仅标准库
- **读取**：`AUGCAGC.txt`、`GUGCACG.txt`、`GUGCGCG.txt`、`\n写入 results/mcsm_single_rerank.csv, results/mcsm_combos_rerank.csv`
- **写出**：`mcsm_combos_rerank.csv`、`mcsm_single_rerank.csv`

### `08_prempri_rerank.py`

- **用途**：阶段 8 —— PremPRI 结果解读与重新排序（单体 + 组合）
- **规模**：116 行｜仅标准库
- **读取**：`AUGCAGC.txt`、`GUGCACG.txt`、`GUGCGCG.txt`、`\n写入 results/prempri_single_rerank.csv, results/prempri_combos_rerank.csv`
- **写出**：`prempri_combos_rerank.csv`、`prempri_single_rerank.csv`

### `make_mcsmna_lists.py`

- **用途**：生成 mCSM-NA 单突变验证表（三组 RNA 各一份，内容相同，格式为 mCSM 输入格式）：
- **规模**：38 行｜仅标准库
- **读取**：`mcsmna_mutations_{rna}.txt`
- **写出**：—

## S4 接触分解、保守性与共进化

回答「哪些残基在读取碱基」「某位点能不能动」「能朝哪个方向变」。

### `10_contact_decomposition.py`

- **用途**：阶段 10 —— 差异接触的「接触类型」分解
- **规模**：126 行｜仅标准库
- **读取**：`\n写入 {OUT}/contact_decomposition.csv`、`manifest.csv`
- **写出**：`{OUT}/contact_decomposition.csv`
- **依赖本项目模块**：af_utils

### `11_conservation_coevolution.py`

- **用途**：阶段 11 —— 序列保守性 + 共进化分析（回答「某位点能否突变」）
- **规模**：147 行｜第三方依赖：numpy
- **读取**：`\n写入 {OUT}/conservation.csv, {OUT}/coevolution_with_core.csv`
- **写出**：`{OUT}/coevolution_with_core.csv`、`{OUT}/conservation.csv`

### `12_mutation_direction.py`

- **用途**：阶段 12 —— 可突变残基的「突变方向」分析（PSSM 序列谱）
- **规模**：89 行｜仅标准库
- **读取**：—
- **写出**：`results/pssm_direction.csv`

### `13_pssm_validation.py`

- **用途**：阶段 13 —— PSSM 可突变方向预测 与 湿实验 逐突变核对（可信度/有效性评估）
- **规模**：149 行｜第三方依赖：openpyxl
- **读取**：`\n写入 results/pssm_validation.csv, results/pssm_confusion.csv`
- **写出**：`results/pssm_confusion.csv`、`results/pssm_validation.csv`

### `14_coevolution_combo.py`

- **用途**：阶段 14 —— 共进化筛选组合突变位点（初步可行性评估）
- **规模**：95 行｜第三方依赖：numpy
- **读取**：`\n写入 results/coevolution_pairs.csv`
- **写出**：`results/coevolution_pairs.csv`

## S5 接触概率（CP/ΔCP）与结构几何

以 AF3 接触概率为核心的结构描述量：ΔCP、空间聚类、催化几何、基线矩阵。

### `15_cp_dcp_analysis.py`

- **用途**：阶段 15 —— ContactSeek 式 CP + ΔCP 分析（替代距离接触分析）
- **规模**：131 行｜仅标准库
- **读取**：`\n写入 {OUT}/cp_dcp.csv, {OUT}/cp_dcp_ranking.csv`、`_full_data_{rank}.json`、`manifest.csv`
- **写出**：`{OUT}/cp_dcp.csv`、`{OUT}/cp_dcp_ranking.csv`
- **依赖本项目模块**：af_utils

### `16_test_contact_cp.py`

- **用途**：阶段 16 —— 新 test 模型（11nt RNA CGUUGCGGAGG，+1=G）的接触分析与 CP 分析，并与旧模型对比
- **规模**：105 行｜仅标准库
- **读取**：`\n新模型结果写入 {OUT}/test_cp_dcp.csv`、`fold_test1_full_data_{rank}.json`、`fold_test1_model_{rank}.cif`、`{OUT}/contacts_frequency.csv`、`{OUT}/cp_dcp.csv`
- **写出**：`{OUT}/test_cp_dcp.csv`
- **依赖本项目模块**：af_utils

### `17_test2_dcp.py`

- **用途**：阶段 17 —— test2(+1=A, 11nt) 的接触+CP分析，并算 ΔCP = CP(+1A) - CP(+1G)（用 test 对比）
- **规模**：85 行｜仅标准库
- **读取**：`\n写入 {OUT}/test2_dcp.csv`、`{OUT}/cp_dcp.csv`、`{prefix}_full_data_{rank}.json`、`{prefix}_model_{rank}.cif`
- **写出**：`{OUT}/test2_dcp.csv`
- **依赖本项目模块**：af_utils

### `19_mut_cp.py`

- **用途**：阶段 19 —— 突变体模型的 CP / ΔCP 分析，并与 WT 对比
- **规模**：84 行｜仅标准库
- **读取**：`*full_data*.json`、`\n写入 {OUT}/mut_cp_dcp.csv`、`{OUT}/cp_dcp.csv`
- **写出**：`{OUT}/mut_cp_dcp.csv`
- **依赖本项目模块**：af_utils

### `20_site_spatial.py`

- **用途**：阶段 20 —— 突变位点空间距离聚类分析（v2：区分序列邻居 vs 三维长程接近）
- **规模**：118 行｜仅标准库
- **读取**：`\n写入 results/mutation_site_spatial_distances.csv`、`fold_{sd}_model_0.cif`、`写入 results/mutation_site_cross_region_bridges.csv`
- **写出**：`results/mutation_site_cross_region_bridges.csv`、`results/mutation_site_spatial_distances.csv`
- **依赖本项目模块**：af_utils

### `21_targetC_catalytic_dist.py`

- **用途**：阶段 21 —— 靶点 C（编辑 C，0位 = RNA res 4）到酶催化中心的距离分析
- **规模**：157 行｜仅标准库
- **读取**：`*full_data*.json`、`\n写入 results/targetC_catalytic_dist_summary.csv`、`full_data_(\d+).json`、`{base}model_{k}.cif`
- **写出**：`results/targetC_catalytic_dist_summary.csv`
- **依赖本项目模块**：af_utils

### `22_best_combo_pairs.py`

- **用途**：阶段 22 —— 最佳组合位点对综合筛选
- **规模**：140 行｜第三方依赖：openpyxl
- **读取**：`\n写入 results/best_combo_pairs.csv`、`results/coevolution_pairs.csv`、`results/experimental_ranking.csv`、`results/mutation_site_spatial_distances.csv`、`组合突变结果/merged_data_var8_C295_C388_C871_C_to_T_重新核实_按var1格式.xlsx`
- **写出**：`results/best_combo_pairs.csv`

### `23_dE72_regression.py`

- **用途**：阶段 23 —— Δd_E72 补齐 + 与实测 +1 比回归 + 三点复合物结构解析
- **规模**：232 行｜第三方依赖：matplotlib
- **读取**：`*full_data*.json`、`\n写入 results/dE72_regression.csv, results/zinc_coordination.csv`、`写入 results/dE72_scatter.png`
- **写出**：`results/dE72_regression.csv`、`results/dE72_scatter.png`、`results/zinc_coordination.csv`
- **依赖本项目模块**：af_utils

### `52_mutant_baseline_dcp.py`

- **用途**：阶段 52 —— 导出「突变体基线 ΔCP（全 199 残基）」完整数据
- **规模**：193 行｜第三方依赖：numpy, openpyxl
- **读取**：`results/mut_cp_dcp.csv`、`results/mut_cp_dcp_batch2.csv`、`写入 results/突变体基线ΔCP_全199残基.xlsx`
- **写出**：`results/突变体基线ΔCP_全199残基.xlsx`

## S6 阴性对照与纯蛋白对照

引入答案已知的对照，检验 CP/偏离度究竟在衡量什么。

### `36_intra_cp_compare.py`

- **用途**：阶段 36 —— 检验「师姐假说」：突变体的「蛋白内部 CP」与「蛋白–靶C CP」相对 WT 的偏离，
- **规模**：276 行｜仅标准库
- **读取**：`*full_data*.json`、`*model_*.cif`、`\n写入 results/CP偏离_汇总.csv / CP偏离_零假设.csv / protC_cp_profile.csv`、`results/GCG_vs_off_ranking_WT.csv`、`results/experimental_ranking.csv`
- **写出**：`results/CP偏离_汇总.csv`、`results/CP偏离_零假设.csv`、`results/protC_cp_profile.csv`
- **依赖本项目模块**：af_utils

### `37_cp_diagnosis_fig.py`

- **用途**：阶段 37 —— 「CP 偏离能否解释活性」诊断图
- **规模**：130 行｜第三方依赖：matplotlib, numpy
- **读取**：`results/CP偏离_汇总.csv`、`写入 results/figs/fig7_CP偏离诊断.png`
- **写出**：`results/figs/fig7_CP偏离诊断.png`

### `38_cp_pca.py`

- **用途**：阶段 38 —— 以 CP 为特征的 PCA 聚类分析
- **规模**：338 行｜第三方依赖：matplotlib, numpy
- **读取**：`*full_data*.json`、`\n写入 results/figs/fig8_CP_PCA散点.png`、`写入 results/CP_PCA_分离度.csv`、`写入 results/figs/fig9_CP_PCA分离度.png`
- **写出**：`results/CP_PCA_分离度.csv`、`results/figs/fig8_CP_PCA散点.png`、`results/figs/fig9_CP_PCA分离度.png`
- **依赖本项目模块**：af_utils

### `41_negative_controls.py`

- **用途**：阶段 41 —— 湿实验「完全失活」阴性对照候选表
- **规模**：205 行｜第三方依赖：openpyxl
- **读取**：`\n写入 results/阴性对照候选表.xlsx`、`results/GCG_vs_off_ranking_WT.csv`、`results/experimental_ranking.csv`、`results/offtarget_per_sample.csv`
- **写出**：`results/阴性对照候选表.xlsx`

### `43_negctrl_analysis.py`

- **用途**：阶段 43 —— 把「完全失活阴性对照」并入偏离诊断（36）与 PCA（38），重做一次
- **规模**：597 行｜第三方依赖：matplotlib, numpy
- **读取**：`*full_data*.json`、`*job_request.json`、`*model_*.cif`、`\n写入 results/阴性对照_偏离与PCA.csv`、`af3_submit/WT_GCG.json`、`results/GCG_vs_off_ranking_WT.csv`
- **写出**：`results/figs/fig12_阴性对照_偏离诊断.png`、`results/figs/fig13_阴性对照_PCA.png`、`results/阴性对照_DM.csv`、`results/阴性对照_PC坐标.csv`、`results/阴性对照_偏离与PCA.csv`
- **依赖本项目模块**：af_utils

### `46_pure_protein_analysis.py`

- **用途**：阶段 46 —— 纯蛋白模型（AF3 输入不含 RNA）的内部 CP 能否分开聚类？
- **规模**：394 行｜第三方依赖：matplotlib, numpy
- **读取**：`*full_data*.json`、`*job_request.json`、`\n写入 results/纯蛋白_分离度.csv`、`af3_submit/WT_GCG.json`、`results/阴性对照_DM.csv`、`写入 results/figs/fig14_纯蛋白_PCA.png`
- **写出**：`results/figs/fig14_纯蛋白_PCA.png`、`results/figs/fig15_纯蛋白_vs_复合物.png`、`results/纯蛋白_分离度.csv`、`results/纯蛋白_分类表现.csv`
- **依赖本项目模块**：af_utils

### `47_pc_interpretation.py`

- **用途**：阶段 47 —— fig8 中每个主成分（PC1–PC4）到底在编码什么？
- **规模**：172 行｜第三方依赖：numpy
- **读取**：`*full_data*.json`、`\n写入 results/PC含义.csv`
- **写出**：`results/PC含义.csv`
- **依赖本项目模块**：af_utils

### `48_lr_and_pos31.py`

- **用途**：阶段 48 —— 两个问题的定量回答
- **规模**：183 行｜第三方依赖：numpy
- **读取**：`*full_data*.json`、`\n写入 results/长程CP_统计.csv、results/位点31替换系列.csv`、`af3_submit/WT_GCG.json`
- **写出**：`results/位点31替换系列.csv`、`results/长程CP_统计.csv`
- **依赖本项目模块**：af_utils

### `49_verify_intra_cp.py`

- **用途**：阶段 49 —— 核验：蛋白内部 CP 到底是怎么算出来的 + 修正一处残基编号标注错误
- **规模**：141 行｜第三方依赖：numpy
- **读取**：`*full_data*.json`、`GUGCGCG_20/001/*full_data*.json`、`\n写入 results/PC载荷_修正.csv`
- **写出**：`results/PC载荷_修正.csv`
- **依赖本项目模块**：af_utils

## S7 湿实验数据整合与干湿互证

把测序结果并入分析，做预测与实测的对照、监督学习与指标重评价。

### `09_experimental_validation.py`

- **用途**：阶段 9 —— 学姐第一批单位点饱和实验数据 重新分析 + 计算预测交叉验证
- **规模**：98 行｜第三方依赖：openpyxl
- **读取**：`\n写入 {OUT}/experimental_ranking.csv, {OUT}/cross_validation.csv`
- **写出**：`{OUT}/cross_validation.csv`、`{OUT}/experimental_ranking.csv`

### `23_integrate_all.py`

- **用途**：阶段 23(终版) —— 全数据整合
- **规模**：407 行｜第三方依赖：openpyxl
- **读取**：`\n→ results/23_combo_master_table.csv`、`\n→ results/23_final_recommendation.csv`、`\n→ results/23_pair_score_matrix.csv`、`\n→ results/23_site_master_table.csv`、`results/coevolution_pairs.csv`、`results/coevolution_with_core.csv`
- **写出**：`results/23_combo_master_table.csv`、`results/23_final_recommendation.csv`、`results/23_pair_score_matrix.csv`、`results/23_report.txt`、`results/23_site_master_table.csv`

### `28_GCG_target_analysis.py`

- **用途**：阶段 28 —— 以「全部 GCG 位点为靶点」重新分析
- **规模**：225 行｜第三方依赖：matplotlib, numpy
- **读取**：`.var.xls`、`Seq/Bam/G22609034389-1-32F.for.ref.fa`、`Seq/Var/*.var.xls`、`\n写入 results/GCG_target_summary.csv`、`写入 results/GCG_sites_matrix.csv`、`写入 results/GCG_target_analysis.png`
- **写出**：`results/GCG_sites_matrix.csv`、`results/GCG_target_analysis.png`、`results/GCG_target_summary.csv`

### `29_GCG_sum_ranking.py`

- **用途**：阶段 29 —— 靶点(GCG)编辑总和 vs 脱靶(其他位点)编辑总和 的排序与绘图
- **规模**：167 行｜第三方依赖：matplotlib, numpy
- **读取**：`.var.xls`、`Seq/Bam/G22609034389-1-32F.for.ref.fa`、`Seq/Var/*.var.xls`、`\n写入 results/GCG_vs_off_ranking.csv`、`写入 results/GCG_vs_off_ranking.png`
- **写出**：`results/GCG_vs_off_ranking.csv`、`results/GCG_vs_off_ranking.png`

### `30_GCG_vs_off_WT.py`

- **用途**：阶段 30 —— 靶点(GCG)编辑总和 vs 脱靶编辑总和 排序与绘图（P 部分仅保留 WT）
- **规模**：175 行｜第三方依赖：matplotlib, numpy
- **读取**：`.var.xls`、`Seq/Bam/G22609034389-1-32F.for.ref.fa`、`Seq/Var/*.var.xls`、`\n写入 results/GCG_vs_off_ranking_WT.csv`、`写入 results/GCG_vs_off_ranking_WT.png`
- **写出**：`results/GCG_vs_off_ranking_WT.csv`、`results/GCG_vs_off_ranking_WT.png`

### `31_wetlab_mutation_list.py`

- **用途**：阶段 31 —— 湿实验引物设计用「突变位点清单」
- **规模**：264 行｜第三方依赖：openpyxl
- **读取**：`.var.xls`、`Seq/Var/*.var.xls`、`results/experimental_ranking.csv`、`写入 results/湿实验突变清单_引物设计用.xlsx`
- **写出**：`results/湿实验突变清单_位点分类.csv`、`results/湿实验突变清单_单点.csv`、`results/湿实验突变清单_引物设计用.xlsx`、`results/湿实验突变清单_组合.csv`

### `35_dry_vs_wet_ranking.py`

- **用途**：阶段 35 —— 干实验预测 vs 湿实验验证 最佳候选排序对照表
- **规模**：240 行｜第三方依赖：openpyxl
- **读取**：`results/GCG_vs_off_ranking_WT.csv`、`results/combinations_top1000.csv`、`results/experimental_ranking.csv`、`results/mcsm_single_rerank.csv`、`results/offtarget_screen_final.csv`、`results/prempri_single_rerank.csv`
- **写出**：`results/干湿排序对照表.xlsx`

### `50_ml_fitness_prediction.py`

- **用途**：阶段 50 —— 以 targeting_ratio 为适应度的监督学习预测（对标 Peng et al. 2026 Mol Cell 的 MLDE）
- **规模**：351 行｜第三方依赖：numpy, openpyxl, sklearn
- **读取**：`\n写入 results/ML适应度_交叉验证.csv、results/ML适应度_候选预测.csv`、`af3_submit/WT_GCG.json`、`results/GCG_vs_off_ranking_WT.csv`、`results/下一步实验突变候选表_61组.xlsx`
- **写出**：`results/ML适应度_交叉验证.csv`、`results/ML适应度_候选预测.csv`

### `51_metric_reevaluation.py`

- **用途**：阶段 51 —— 用 top-5 / top-10 回收率重新评价此前所有方法
- **规模**：285 行｜第三方依赖：numpy
- **读取**：`\n写入 results/方法重评价_topN.csv`、`results/23_pair_score_matrix.csv`、`results/GCG_vs_off_ranking_WT.csv`、`results/dE72_regression.csv`、`results/experimental_ranking.csv`、`results/mcsm_single_rerank.csv`
- **写出**：`results/方法重评价_topN.csv`

## S8 脱靶扫描与指标偏倚

从 BAM 找 C→U 事件、构建脱靶矩阵、检验靶向比的系统性偏倚。

### `02_find_CU_offtarget.py`

- **用途**：步骤2：从三个重复的 BAM 中找 C→U（C→T）编辑事件，排序找出「脱靶编辑最强」的位点及其 motif。
- **规模**：108 行｜第三方依赖：pysam
- **读取**：`CU_offtarget_all.txt`
- **写出**：—

### `24_offtarget_scan.py`

- **用途**：阶段 24 —— 组合突变体的「总体脱靶」筛查（不限于 388/871）
- **规模**：216 行｜仅标准库
- **读取**：`*.var.xls`、`.var.xls`、`Seq/Bam/G22609034389-1-32F.for.ref.fa`、`\n写入 results/offtarget_per_sample.csv / offtarget_by_mutant.csv / offtarget_hotspots.csv`
- **写出**：`results/offtarget_by_mutant.csv`、`results/offtarget_hotspots.csv`、`results/offtarget_per_sample.csv`

### `25_offtarget_screen.py`

- **用途**：阶段 25 —— 组合突变体「总体脱靶」最终筛查
- **规模**：131 行｜仅标准库
- **读取**：`*.var.xls`、`.var.xls`、`Seq/Bam/G22609034389-1-32F.for.ref.fa`、`\n写入 results/offtarget_screen_final.csv`
- **写出**：`results/offtarget_screen_final.csv`

### `26_offtarget_matrix.py`

- **用途**：阶段 26 —— 「突变 × 脱靶位点」矩阵
- **规模**：147 行｜第三方依赖：matplotlib, numpy
- **读取**：`.var.xls`、`Seq/Bam/G22609034389-1-32F.for.ref.fa`、`Seq/Var/*.var.xls`、`\n注：数值 = 平均编辑频率(%), · = 未检出(<5%)；完整 74 位点矩阵见 results/offtarget_matrix.csv`、`写入 results/offtarget_matrix_heatmap.png`
- **写出**：`results/offtarget_matrix.csv`、`results/offtarget_matrix_heatmap.png`

### `27_offtarget_matrix_noP.py`

- **用途**：阶段 27 —— 「突变 × 脱靶位点」矩阵（去除全部 P 相关突变后重绘）
- **规模**：152 行｜第三方依赖：matplotlib, numpy
- **读取**：`.var.xls`、`Seq/Bam/G22609034389-1-32F.for.ref.fa`、`Seq/Var/*.var.xls`、`\n写入 results/offtarget_matrix_noP.csv`、`写入 results/offtarget_matrix_heatmap_noP.png`
- **写出**：`results/offtarget_matrix_heatmap_noP.png`、`results/offtarget_matrix_noP.csv`

### `58_targeting_ratio_rerank.py`

- **用途**：阶段 58 —— 靶向比偏倚的「回补检验」与校正后重新排序
- **规模**：274 行｜第三方依赖：numpy, scipy
- **读取**：`results/23_combo_master_table.csv`、`results/GCG_vs_off_ranking_WT.csv`、`results/offtarget_by_mutant.csv`、`results/下一步实验突变候选表_61组.csv`、`results/靶向比_回补检验.csv`、`results/靶向比_重排序对比.csv`
- **写出**：—

## S9 候选设计与回溯检验

产出下一轮候选表，并对已发表方法做回溯检验。

### `33_next_round_candidates.py`

- **用途**：阶段 33/36 —— 下一步实验突变候选表（61 组 = 原 41 组 + 新增 20 组 E 组）
- **规模**：260 行｜第三方依赖：openpyxl
- **读取**：`写入 results/下一步实验突变候选表_61组.csv`、`写入 results/下一步实验突变候选表_61组.xlsx`
- **写出**：`results/下一步实验突变候选表_61组.csv`、`results/下一步实验突变候选表_61组.xlsx`

### `55_aice_beta_gamma_retro.py`

- **用途**：阶段 55 —— 回溯检验 AiCE 的 β/γ 结构约束过滤器
- **规模**：264 行｜第三方依赖：numpy, openpyxl, pydssp
- **读取**：`Apobec前期设计附件/Apobec前期设计附件/全长反设计.fa`、`\n写入 results/AiCE过滤器_回溯检验.xlsx`、`prohA1_monomer_63e3b_unrelaxed_rank_001_alphafold2_ptm_model_2_seed_000.pdb`、`results/experimental_ranking.csv`、`写入 results/AiCE过滤器_回溯检验.csv / _位点级.csv`
- **写出**：`results/AiCE过滤器_位点级.csv`、`results/AiCE过滤器_回溯检验.csv`、`results/AiCE过滤器_回溯检验.xlsx`

### `analyze_pos29_screen.py`

- **用途**：位点 29 近饱和扫描（及位点 30 等）的数据分析。
- **规模**：349 行｜第三方依赖：matplotlib, numpy, openpyxl
- **读取**：`pos29_screen_depth_filtered.png`、`位点29_30扫描_深度筛选后.csv`
- **写出**：—
- **依赖本项目模块**：orca_drylab_style

## S10 批次实测数据分析

三批补充突变（37 组 / 64 样本）的逐组分析与绘图用表导出。

### `analyze_batch3.py`

- **用途**：第三批补充数据（64 样本 / 29 同名组）分析。
- **规模**：108 行｜第三方依赖：openpyxl
- **读取**：`\01a0ebae-7d96-70fe-9b5b-e61e328d0def.xlsx`、`第三批_分组分析.csv`、`第三批_绘图用表.csv`
- **写出**：—

### `analyze_new_batch.py`

- **用途**：分析下一批补充突变（37 个突变组 + 2 个参照）的实验结果。
- **规模**：171 行｜第三方依赖：openpyxl
- **读取**：`下一批突变_分组分析.csv`
- **写出**：—

## S11 绘图

共享绘图样式 + 各类图的生成脚本。

### `34_report_figures.py`

- **用途**：阶段 34 —— 汇报用图（6 张，供 PPT/报告直接插入）
- **规模**：275 行｜第三方依赖：matplotlib, numpy
- **读取**：`results/GCG_vs_off_ranking_WT.csv`、`results/experimental_ranking.csv`、`results/offtarget_screen_final.csv`
- **写出**：`results/figs/fig1_单点突变全景.png`、`results/figs/fig2_组合Pareto前沿.png`、`results/figs/fig3_总体脱靶负荷.png`、`results/figs/fig4_GCG靶向偏好.png`、`results/figs/fig5_D组控制变量布局.png`、`results/figs/fig6_候选总览.png`

### `57_make_wiki_figures.py`

- **用途**：57_make_wiki_figures.py —— 生成 iGEM wiki 展示级图表
- **规模**：481 行｜第三方依赖：matplotlib, numpy, scipy
- **读取**：`Apobec前期设计附件/Apobec前期设计附件/全长反设计.fa`、`results/23_combo_master_table.csv`、`results/GCG_vs_off_ranking_WT.csv`、`results/experimental_ranking.csv`、`results/阴性对照_DM.csv`、`wiki_fig0_项目总览.png`
- **写出**：—

### `collect_redrawn.py`

- **用途**：把本轮重绘的 10 张图收集到一个独立交付文件夹，并生成清单。
- **规模**：133 行｜仅标准库
- **读取**：`  {len(rows)} 张 PNG + README.md + manifest.json`、`Apobec前期设计附件/全长反设计.fa, results/AiCE过滤器_位点级.csv`、`figure_10_candidate_overview.png`、`figure_11_method_retrospective.png`、`figure_2_cp_deviation.png`、`figure_3_ddcp_heatmap.png`
- **写出**：`manifest.json`
- **备注**：（原位于 文案数据图表整理/）

### `orca_drylab_style.py`

- **用途**：共享绘图样式 —— 严格对齐队友聚类图的视觉规范。
- **规模**：227 行｜第三方依赖：matplotlib
- **读取**：—
- **写出**：—
- **备注**：（原位于 文案数据图表整理/）

### `orca_plot.py`

- **用途**：ORCA plotting primitives. Inputs must already have explicit, audited semantics.
- **规模**：391 行｜第三方依赖：matplotlib, numpy, platform
- **读取**：`alt-text.txt`、`figure-manifest.json`、`orca-figure-style.json`、`orca-style.json`、`{stem}.pdf`、`{stem}@2x.png`
- **写出**：—
- **备注**：（原位于 文案数据图表整理/）

### `plot_cycles.py`

- **用途**：ORCA Wiki 科研绘图 —— APOBEC 编辑模块 DBTL 五个循环的数据图
- **规模**：577 行｜第三方依赖：matplotlib, numpy, scipy
- **读取**：`23_combo_master_table.csv`、`Apobec前期设计附件/Apobec前期设计附件/全长反设计.fa`、`GCG_vs_off_ranking_WT.csv`、`experimental_ranking.csv`、`orca-figure-style.json`、`results/23_combo_master_table.csv`
- **写出**：—
- **依赖本项目模块**：orca_plot
- **备注**：（原位于 文案数据图表整理/）

### `plot_distances.py`

- **用途**：绘制 +1 位接触的距离分布图（读取 results/key_distances.csv 与 contacts_frequency.csv）。
- **规模**：99 行｜第三方依赖：matplotlib
- **读取**：`  results/plots/distance_violin_key_residues.png`、`  results/plots/frequency_bar.png`、`results/contacts_frequency.csv`、`results/key_distances.csv`
- **写出**：`distance_violin_key_residues.png`、`frequency_bar.png`

### `plot_drylab_figures.py`

- **用途**：依据队友的绘图规范（见 orca_drylab_style.py）重绘 Dry Lab 页面的 10 张图。
- **规模**：902 行｜第三方依赖：matplotlib, numpy, openpyxl, scipy
- **读取**：`AiCE过滤器_位点级.csv`、`CP偏离_汇总.csv`、`GCG_vs_off_ranking_WT.csv`、`experimental_ranking.csv`、`fig11 panel B: no contested substitution found in AiCE过滤器_位点级.csv`、`figure_10_candidate_overview.png`
- **写出**：—
- **依赖本项目模块**：orca_drylab_style
- **备注**：（原位于 文案数据图表整理/）

## S12 文档与交付物生成

Markdown → Word/PPT 的生成器，以及论文页、DBTL 稿、绘图数据包导出。

### `32_drylab_note.py`

- **用途**：生成《干实验记录（Dry-lab Note）》
- **规模**：282 行｜第三方依赖：docx
- **读取**：`09–14 脚本、3 份报告、可突变性与突变方向分析.docx`、`23_integrate_all.py、四张主表、第一期 PPT、dE72_regression.csv`、`24–31 脚本、脱靶矩阵/热图、GCG 排序图、湿实验突变清单.xlsx`、`results/湿实验突变清单_引物设计用.xlsx`、`可突变性与突变方向分析_组会汇报.pptx；APOBEC保G排A优化_组会汇报.pptx（第一期）；_第二期.pptx；_综合稿.pptx`、`干实验记录_APOBEC保G排A优化.docx`
- **写出**：—

### `53_make_full_chain_report.py`

- **用途**：53_make_full_chain_report.py —— 生成《APOBEC 保G排A 优化 · 实验全程汇报》Word 文档
- **规模**：1423 行｜第三方依赖：docx
- **读取**：`APOBEC保G排A优化_实验全程汇报.docx`、`fig12_阴性对照_偏离诊断.png`、`fig13_阴性对照_PCA.png`、`fig16_突变体ΔΔCP热图.png`、`fig1_单点突变全景.png`、`fig2_组合Pareto前沿.png`
- **写出**：—

### `54_make_full_chain_ppt.py`

- **用途**：54_make_full_chain_ppt.py —— 生成《APOBEC 保G排A 优化 · 实验全程汇报》PPT
- **规模**：967 行｜第三方依赖：pptx
- **读取**：`APOBEC保G排A优化_组会汇报_实验全程.pptx`、`fig16_突变体ΔΔCP热图.png`、`results/突变体基线ΔCP_全199残基.xlsx`
- **写出**：—

### `56_make_dbtl.py`

- **用途**：56_make_dbtl.py —— 把 APOBEC 编辑模块的全部实验整理为 iGEM 的 DBTL 循环
- **规模**：1272 行｜第三方依赖：docx, openpyxl
- **读取**：`APOBEC_DBTL_数据支撑表.xlsx`、`APOBEC_DBTL_迭代整理.docx`、`cycle3b-rerank/cycle3b@2x.png`、`fig15_纯蛋白_vs_复合物.png`、`fig3_总体脱靶负荷.png`、`fig5_D组控制变量布局.png`
- **写出**：—

### `docx_build.py`

- **用途**：docx_build.py —— 用「已知可用 DOCX 作为模板 + 注入 document.xml」的方式生成 DOCX
- **规模**：238 行｜仅标准库
- **读取**：`导师汇报_APOBEC_保G排A优化_研究总结.docx`
- **写出**：—

### `export_drylab_plotdata.py`

- **用途**：导出 Dry Lab 页面全部绘图所需数据，打包给绘图同学。
- **规模**：549 行｜第三方依赖：openpyxl
- **读取**：`AiCE过滤器_位点级.csv`、`CP偏离_汇总.csv`、`GCG_vs_off_ranking_WT.csv`、`experimental_ranking.csv`、`figure_01_workflow.png`、`figure_02_cp_deviation.csv`
- **写出**：`manifest.json`

### `gen_report_docx.py`

- **用途**：gen_report_docx.py —— 生成完整研究结果 Word 文档
- **规模**：780 行｜仅标准库
- **读取**：`23_combo_master_table.csv`、`23_pair_score_matrix.csv`、`23_site_master_table.csv`、`APOBEC保G排A_研究结果完整整理与最佳位点对清单.docx`
- **写出**：—
- **依赖本项目模块**：docx_build

### `gen_report_pptx.py`

- **用途**：gen_report_pptx.py —— 生成组会汇报 PPT
- **规模**：354 行｜仅标准库
- **读取**：`23_combo_master_table.csv`、`23_site_master_table.csv`、`APOBEC保G排A优化_组会汇报.pptx`、`数据文件：results/23_site_master_table.csv · 23_combo_master_table.csv · 23_pair_score_matrix.csv`
- **写出**：—
- **依赖本项目模块**：pptx_build, pptx_slides

### `make_bilingual_docx.py`

- **用途**：把中英对照版 Markdown 转成 Word。
- **规模**：185 行｜第三方依赖：docx
- **读取**：`APOBEC_DryLab_Complete_中英对照.docx`
- **写出**：—
- **备注**：（原位于 文案数据图表整理/）

### `make_drylab_docx.py`

- **用途**：把 Dry Lab 页面的 Markdown 转成 Word（iGEM wiki 交付用）。
- **规模**：167 行｜第三方依赖：docx
- **读取**：`APOBEC_DryLab_Complete.docx`
- **写出**：—
- **备注**：（原位于 文案数据图表整理/）

### `make_mutability_report.py`

- **用途**：生成 Word 版「可突变性与突变方向分析」实验报告
- **规模**：201 行｜第三方依赖：docx
- **读取**：`已生成：可突变性与突变方向分析_实验报告.docx`
- **写出**：`可突变性与突变方向分析_实验报告.docx`

### `make_presentation.py`

- **用途**：生成组会汇报 PPT（严谨科学风，含 +1 特异性结果与两篇文献借鉴）
- **规模**：285 行｜第三方依赖：pptx
- **读取**：—
- **写出**：`可突变性与突变方向分析_组会汇报_含文献.pptx`

### `make_presentation_combined.py`

- **用途**：本周组会汇报稿 = 第一期（三维证据整合）+ 第二期（P1-1/P1-2 执行）合并
- **规模**：672 行｜第三方依赖：pptx
- **读取**：—
- **写出**：`APOBEC保G排A优化_组会汇报_综合稿.pptx`

### `make_presentation_v2.py`

- **用途**：生成组会汇报 PPT（第二期）
- **规模**：507 行｜第三方依赖：pptx
- **读取**：—
- **写出**：`APOBEC保G排A优化_组会汇报_第二期.pptx`

### `make_tutor_report.py`

- **用途**：生成导师阶段汇报 Word：
- **规模**：276 行｜第三方依赖：docx
- **读取**：`results/mut_cp_summary_保G排A_合并.csv`、`results/mutation_site_cross_region_bridges.csv`、`results/mutation_site_spatial_distances.csv`、`results/targetC_catalytic_dist_summary.csv`、`导师汇报_APOBEC_保G排A优化_研究总结.docx`
- **写出**：—

### `make_wiki_docx.py`

- **用途**：把 wiki 文案（Markdown）转成 Word，便于与队友的 docx 流程对接。
- **规模**：101 行｜第三方依赖：docx
- **读取**：`APOBEC_Wiki_文案_{variant}.docx`
- **写出**：—
- **备注**：（原位于 文案数据图表整理/）

### `make_word_report.py`

- **用途**：生成 Word 版完整工作流与结果报告。
- **规模**：221 行｜第三方依赖：docx
- **读取**：`APOBEC_保G排A优化_完整工作报告.docx`、`combinations_top1000.csv`、`contacts_long/frequency.csv`、`manifest.csv、qc_report.csv`、`mcsm_*_rerank.csv`、`prempri_*_rerank.csv`
- **写出**：—

### `pptx_build.py`

- **用途**：pptx_build.py —— 用 PowerPoint COM 作为「渲染/组装引擎」构建 PPTX
- **规模**：126 行｜仅标准库
- **读取**：`_tpl.pptx`
- **写出**：—

### `pptx_slides.py`

- **用途**：pptx_slides.py —— 生成 slide XML（纯 OOXML），并配合 pptx_build 组装成可打开的 PPTX
- **规模**：272 行｜仅标准库
- **读取**：—
- **写出**：—

## `_cancelled/` 已废止脚本

### `39_make_protein_only_submit.py`（已废止）

- **原用途**：阶段 39 —— 生成「纯蛋白模型」AF3 提交文件（只给蛋白链，不给 RNA）
- **废止原因**：由 `45_make_pure_protein_submit.py` / `46_pure_protein_analysis.py` 取代。

### `40_protein_only_pca.py`（已废止）

- **原用途**：阶段 40 —— 「纯蛋白模型」CP 的 PCA 与分离度检验（对照 38 的复合物模型）
- **废止原因**：由 `45_make_pure_protein_submit.py` / `46_pure_protein_analysis.py` 取代。
