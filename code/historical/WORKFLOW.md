# 工作流主线｜APOBEC 编辑模块 "保 G 排 A"

> 本文按**数据流**说明 12 个阶段各自解决什么问题、吃什么、吐什么。
> 逐脚本的用途与读写文件见 `MANIFEST.md`；数据目录与外部工具见 `DATA.md`。

---

## 整体数据流

```
                    ┌─ AlphaFold3 服务器 ─┐
原始 cif/JSON ──────►│  (GUGCGCG/ACG/AGC)  │──── 预测结构
                    └─────────────────────┘
                              │
                     S0 清单归一化  →  results/manifest.csv
                              │
              ┌───────────────┼────────────────┬──────────────┐
              ▼               ▼                ▼              ▼
        S1 结构质控与     S4 接触分解/      S5 CP·ΔCP      S2 AF3 任务生成
        界面刻画          保守性/共进化     与几何          （对照/纯蛋白）
              │               │                │              │
              └───────────────┴────────────────┴──────────────┘
                              │
                     S3 设计模型复核（mCSM-NA / PremPRI）
                              │
                     S6 阴性对照与纯蛋白对照 ← 检验描述量到底在衡量什么
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
  S7 湿实验整合          S8 脱靶扫描与            S9 候选设计与
  干湿互证              指标偏倚检验              回溯检验
        │                     │                      │
        └─────────────────────┴──────────────────────┘
                              │
                     S10 批次实测分析（三批补充突变）
                              │
                     S11 绘图 ──► S12 文档与交付物
```

**一句话概括这条流程**：先问「这个界面上有没有可改造的读取元件」（S0–S6），
再把干实验预测放进湿实验里裁决（S7–S8），最后据此设计下一轮并复盘失败的方法（S9–S10），
产出图表与文稿（S11–S12）。

---

## S0 环境、清单与共享工具

**解决的问题**：AF3 输出是一堆散落的 `*_model_*.cif` 与 `*_summary_confidences_*.json`，
下游任何分析都需要先有一份统一清单，并且需要一个共用的解析层。

| 脚本 | 作用 |
|---|---|
| `af_utils.py` | **全局共享模块**（153 行，纯标准库）：cif 解析、质控、接触统计。S1/S4/S5/S6 多数脚本 `import af_utils` |
| `00_manifest.py` | 扫描 AF3 输出目录 → `results/manifest.csv` |
| `shell/00_setup_reference.sh` | 准备参考序列 |
| `shell/01_download_align.sh` | 下载并比对（BAM） |

**输出**：`results/manifest.csv`（下游几乎所有脚本的入口）

---

## S1 结构解析与界面刻画

**解决的问题**：把预测结构变成可比较的界面描述——哪些残基在接触、接触多紧、埋藏多深。

| 脚本 | 输入 | 输出 |
|---|---|---|
| `01_qc.py` | `manifest.csv` + `*_summary_confidences_*.json` | `results/qc_report.csv` |
| `02_contacts.py` | `manifest.csv`、`qc_report.csv` | `results/contacts_long.csv`、`key_distances.csv` |
| `03_summary.py` | 上一步结果 | `contacts_frequency.csv`、`g_a_comparison.csv` |
| `04_interactions.py` | `manifest.csv`、`qc_report.csv` | `hbonds_per_residue.csv`、`buried_area_per_residue.csv`、`filtered_residues.csv` |
| `05_combinations.py` | 单点库 | `results/combinations_top1000.csv` |
| `06_cif2pdb.py` | `manifest.csv`、`qc_report.csv` | **pdb 文件**（给 mCSM-NA 等服务器用，故不进 results/） |
| `make_pml.py` | `manifest.csv` | PyMOL `.pml` 抽查脚本（人工可视化用） |

**关键约定**：三个 RNA 底物 `GUGCGCG`（靶点）、`GUGCACG`（+1 换 A）、`AUGCAGC`（完整脱靶）
全程并排分析——这是把「+1 位效应」与「侧翼效应」分开的前提。

---

## S2 AF3 任务生成

**解决的问题**：不同分析需要不同形态的模型输入，用脚本保证提交文件的一致性与可追溯性。

| 脚本 | 生成什么 | 落盘位置 |
|---|---|---|
| `18_make_af3_submit.py` | 突变体 × 两种 RNA 的复合物提交 JSON | `af3_submit/` |
| `42_make_negctrl_submit.py` | 阴性对照提交 JSON（+ `_panel.csv` 面板清单） | `af3_submit_negctrl/` |
| `44_split_seeds.py` | 把多 seed 提交拆成「一 JSON 一 seed」 | `submit/` + `提交清单_AF3.csv` |
| `45_make_pure_protein_submit.py` | **纯蛋白**（不给 RNA）提交 JSON，共 60 个单 seed | `af3_submit_pure/` |

> 这三个目录里的 JSON **保留在包外**（属数据）。重新提交会覆盖它们，而下游 S6 依赖其内容。

---

## S3 设计模型复核（mCSM-NA / PremPRI）

**解决的问题**：用两个已发表的分子设计/稳定性预测服务器，独立复核「哪些替换可能可行」，
并与湿实验对照——这是项目里最早被证伪的一条路线（见 `51_metric_reevaluation.py`）。

| 脚本 | 作用 |
|---|---|
| `make_mcsmna_lists.py` | 生成 mCSM-NA 输入表（三组 RNA 各一份） |
| `07_mcsm_rerank.py` | 回收 mCSM 结果 → `results/mcsm_single_rerank.csv`、`mcsm_combos_rerank.csv` |
| `08_prempri_rerank.py` | 同上，PremPRI → `results/prempri_*.csv` |

**注意**：这两个脚本读的是**人工从网页下载的 `.txt` 结果**（`GUGCGCG.txt` 等），
服务器本身不能脚本化提交。统合时这是流程中第一个必须人工介入的点。

---

## S4 接触分解、保守性与共进化

**解决的问题**：项目最核心的一组生物学问题——
**哪些残基在「读」碱基（而不只是贴着它）？某个位点能不能动？能动的话朝哪个方向变？**

| 脚本 | 回答什么 | 输出 |
|---|---|---|
| `10_contact_decomposition.py` | 把每个残基与 +1 碱基的接触拆成侧链/主链 × 碱基/糖磷酸四类 | `contact_decomposition.csv` |
| `11_conservation_coevolution.py` | 3,504 条同源序列的保守性 + 与催化核心的共进化 MI | `conservation.csv`、`coevolution_with_core.csv` |
| `12_mutation_direction.py` | PSSM 序列谱 → 每个位点的「允许/禁止」替换方向 | `pssm_direction.csv` |
| `13_pssm_validation.py` | PSSM 预测与湿实验逐条核对（可信度评估） | `pssm_validation.csv`、`pssm_confusion.csv` |
| `14_coevolution_combo.py` | 共进化配对 → 组合位点初筛 | `coevolution_pairs.csv` |

**这一阶段产出了项目最重要的一条结构结论**：H29 与 +1 碱基的接触 94% 走主链（不是读取器），
K30 是全蛋白唯一以侧链读 +1 的残基，T31 在 +1=A 时形成频率 1.00 的氢键（后经实验证伪为功能驱动力）。

---

## S5 接触概率（CP/ΔCP）与结构几何

**解决的问题**：建立以 AF3 接触概率为核心的结构描述量体系，并检验它能不能当功能指标。

| 脚本 | 作用 |
|---|---|
| `15_cp_dcp_analysis.py` | 基线 CP / ΔCP 分析 → `cp_dcp.csv`、`cp_dcp_ranking.csv` |
| `16_test_contact_cp.py` / `17_test2_dcp.py` | 11nt 测试模型的 CP 与 ΔCP（模型间对照） |
| `19_mut_cp.py` | 突变体 CP/ΔCP → `mut_cp_dcp.csv` |
| `20_site_spatial.py` | 突变位点的空间距离聚类（区分序列邻居 vs 三维长程接近） |
| `21_targetC_catalytic_dist.py` | 靶点 C 到催化中心的距离 |
| `22_best_combo_pairs.py` | 最佳组合位点对综合筛选 |
| `23_dE72_regression.py` | Δd_E72 补齐 + 与实测 +1 比的回归 |
| `52_mutant_baseline_dcp.py` | 导出全 199 残基的突变体基线 ΔCP 矩阵（xlsx） |

**产出**：`results/cp_dcp.csv` 与 `results/mut_cp_dcp.csv` 是后续几乎所有结构类分析的公共底表。

---

## S6 阴性对照与纯蛋白对照

**解决的问题**：CP / 偏离度 / 马氏距离这套描述量，**究竟在衡量什么？**
引入一组答案已知的对照（催化敲除 E72A、已知失活体、以及最关键的「WT 只换底物」），
并另做不含 RNA 的纯蛋白建模。

| 脚本 | 作用 |
|---|---|
| `36_intra_cp_compare.py` | 蛋白内部 CP 与蛋白–靶 C CP 的偏离对比 → `CP偏离_汇总.csv`、`CP偏离_零假设.csv` |
| `37_cp_diagnosis_fig.py` | 「CP 偏离能否解释活性」诊断图 |
| `38_cp_pca.py` | 以 CP 为特征的 PCA |
| `41_negative_controls.py` | 阴性对照候选表 |
| `43_negctrl_analysis.py` | 把阴性对照并入偏离诊断与 PCA，重做一次 |
| `46_pure_protein_analysis.py` | 纯蛋白模型的内部 CP 能否分开聚类 |
| `47_pc_interpretation.py` | 每个主成分到底在编码什么 |
| `48_lr_and_pos31.py` | 长程 CP 统计 + T31 替换系列 |
| `49_verify_intra_cp.py` | 核验内部 CP 的算法 + 修正一处残基编号标注错误 |

**这一阶段推翻了项目前期的一个默认假设**：结构偏离并不与功能丧失同步；
CP 的方差被「喂进去哪条 RNA」主导，蛋白信号被淹没。这一步直接改变了后续所有结构解读。

---

## S7 湿实验数据整合与干湿互证

**解决的问题**：把测序结果变成可与干实验对照的表，然后做预测 vs 实测。

| 脚本 | 输入 | 输出 |
|---|---|---|
| `09_experimental_validation.py` | 第一批单点饱和数据（xlsx） | `experimental_ranking.csv`、`cross_validation.csv` |
| `23_integrate_all.py` | 全部结构+实测表 | `23_combo_master_table.csv`、`23_site_master_table.csv`、`23_pair_score_matrix.csv`、`23_final_recommendation.csv` |
| `28_GCG_target_analysis.py` | `Seq/Var/*.var.xls` | `GCG_sites_matrix.csv` 等 |
| `29_GCG_sum_ranking.py` | 同上 | `GCG_vs_off_ranking.csv` |
| `30_GCG_vs_off_WT.py` | 同上（P 部分仅保留 WT） | `GCG_vs_off_ranking_WT.csv`（**靶向比的权威表**） |
| `31_wetlab_mutation_list.py` | 实测表 | 引物设计用突变清单 |
| `35_dry_vs_wet_ranking.py` | 干/湿两套排序 | `干湿排序对照表.xlsx` |
| `50_ml_fitness_prediction.py` | 特征 + 适应度 | `ML适应度_交叉验证.csv`、`ML适应度_候选预测.csv` |
| `51_metric_reevaluation.py` | 全部方法的预测 | `方法重评价_topN.csv`（top-N 回收率重评价） |

**注意**：`28/29/30/31` 读的是**湿实验侧的 `.var.xls`**（`Seq/Var/` 下），
这属于实验室产出的原始数据，本包不含。

---

## S8 脱靶扫描与指标偏倚

**解决的问题**：把观察窗口从「388 vs 871 两个位点」放大到「整段扩增子」，
并检验新定义的指标本身是否可靠。

| 脚本 | 输入 | 输出 |
|---|---|---|
| `02_find_CU_offtarget.py` | BAM（需 `pysam`） | `CU_offtarget_all.txt` |
| `24_offtarget_scan.py` | `Seq/Var/*.var.xls` | `offtarget_by_mutant.csv`、`offtarget_hotspots.csv` |
| `25_offtarget_screen.py` | 同上 | `offtarget_screen_final.csv` |
| `26_offtarget_matrix.py` | 同上 | `offtarget_matrix.csv` + 热图 |
| `27_offtarget_matrix_noP.py` | 同上 | 去 P 域后的矩阵与热图 |
| `58_targeting_ratio_rerank.py` | 三张主表 | 靶向比偏倚的**回补检验**与校正后重排 |

**这一阶段产出了项目的一条方法论规则**：靶向比会被检测下限污染（活性下降时脱靶先掉到线下，
分母塌缩、比值虚高），因此解读全局脱靶必须设 `on-target ≥ 0.30` 的活性下限。
**如果当时直接按靶向比排序挑候选，榜单第一名会是活性 0.000 的死构建体。**

---

## S9 候选设计与回溯检验

| 脚本 | 作用 |
|---|---|
| `33_next_round_candidates.py` | 产出 61 组下一轮候选表（A 复验 / B 新单点 / C 新组合 / D 控制 / E 异常配对） |
| `analyze_pos29_screen.py` | 位点 29（及 30）近饱和扫描的数据分析 |
| `55_aice_beta_gamma_retro.py` | 回溯应用 AiCE 的 β/γ 结构约束过滤器（需 `pydssp`） |

**AiCE 回溯检验的结论**：该过滤器**没能剔除任何一个争议替换**，
也不会提名实际有效的替换（K30H 的采样频率为 0.000）。原因在定义层面——
它的差异化阈值对「结构化区严、卷曲区松」，而本项目的目标界面 18 个候选位点中 16 个是卷曲区。

---

## S10 批次实测数据分析

**解决的问题**：两批补充突变（37 组 / 64 样本）的逐组分析，并导出绘图用表。

| 脚本 | 输入 | 输出 |
|---|---|---|
| `analyze_new_batch.py` | `merged_data_C295_C388_C871.xlsx` | `results/下一批突变_分组分析.csv`、`下一批突变_绘图用表.csv` |
| `analyze_batch3.py` | `merged_data_64样本_同名分组_*.xlsx` | `results/第三批_分组分析.csv`、`第三批_绘图用表.csv` |

**注意**：这两个脚本读取的 xlsx **路径写死在脚本里**（指向 `CherryStudio/Data/Files/` 下的下载文件）。
统合时建议改为命令行参数或统一放进 `data/` 目录。这是本包中唯一两处硬编码外部路径。

**这两批分析出的关键口径**（写进了报告，统合时请保留）：
- 跨批比较必须用 **ROF**（构建体比值 ÷ 同批亲本比值），因为亲本比值本身在批次间漂移；
- **建库背景不同的批次之间不能横向比较比值**，能跨批传递的是**秩**；
- c.871 未检出时比值**不可定义**，不得按 0 处理。

---

## S11 绘图

| 脚本 | 作用 |
|---|---|
| `orca_plot.py` | **绘图基元**（来自队友的 wiki 配图工具链，本项目复用其规范） |
| `orca_drylab_style.py` | 严格对齐该规范的共享样式模块（配色、画布、图例、`save_checked` 守卫） |
| `plot_drylab_figures.py` | Dry Lab 页面的图（figure 2–11、15、16） |
| `plot_cycles.py` | wiki 五个循环的数据图 |
| `57_make_wiki_figures.py` | wiki 展示级图表 |
| `34_report_figures.py` | 汇报用图（6 张，供 PPT/报告直接插入） |
| `plot_distances.py` | +1 位接触的距离分布图 |
| `collect_redrawn.py` | 把重绘的图收集到独立交付文件夹并生成清单 |

**两条硬性守卫**（在 `orca_drylab_style.py` 中）：
- `assert_english()`：写盘前断言图内无中日韩字符（wiki 页面为英文）；
- `assert_drawn()`：断言没有空面板（曾出现 Figure 11 面板 B 空白的事故）。

---

## S12 文档与交付物生成

| 脚本 | 产出 |
|---|---|
| `docx_build.py` | DOCX 底层：以已知可用文档为模板、注入 `document.xml` |
| `pptx_build.py` / `pptx_slides.py` | PPTX 底层：生成 slide XML + PowerPoint COM 组装（**仅 Windows**） |
| `56_make_dbtl.py` | **《DBTL 迭代整理》**（docx + md + 数据支撑表 xlsx）——iGEM Engineering Success 素材 |
| `32_drylab_note.py` | 《干实验记录》 |
| `make_wiki_docx.py` | wiki 文案（中英双语 / SONAR 体）→ Word |
| `make_drylab_docx.py` / `make_bilingual_docx.py` | Dry Lab 页面 md → Word；中英对照版 Word |
| `53_make_full_chain_report.py` / `54_make_full_chain_ppt.py` | 实验全程汇报 Word / PPT |
| `export_drylab_plotdata.py` | **绘图数据包**：导出 20 份 tidy CSV + 16 张参考图 + manifest + 数据字典 |
| `gen_report_docx.py` / `gen_report_pptx.py` / `make_*report.py` / `make_presentation*.py` | 各阶段汇报稿 |

**交付物之间的依赖关系**：`56_make_dbtl.py` 是 **DBTL 稿的唯一真源**；
`make_wiki_docx.py` 是 wiki 两份文案 Word 版的生成器；
Dry Lab 的 md 是页面正文的真源，docx 由它生成。**改文稿请改 md / 脚本，不要直接改 docx。**

---

## S13 已废止

`_cancelled/39_make_protein_only_submit.py`、`_cancelled/40_protein_only_pca.py`
是早期纯蛋白分析的两个脚本，已被 `45_make_pure_protein_submit.py` / `46_pure_protein_analysis.py` 取代。
保留是为了让早期报告里的引用仍可追溯，**请勿使用，也请勿删除**。

---

## 流程中的三处人工介入点

| 位置 | 为什么不能脚本化 |
|---|---|
| **AF3 服务器提交** | S2 只生成 JSON，实际上传与回收模型在网页端 |
| **mCSM-NA / PremPRI** | S3 只生成输入清单、只解析下载回来的 `.txt` |
| **湿实验数据回收** | S7/S8/S10 读的是测序结果（`.var.xls`）与补充突变的 xlsx，需人工放入指定位置 |

因此本包**不提供一键式 `run_all`**——那会造成「跑通了但用的是旧数据」的假象。
