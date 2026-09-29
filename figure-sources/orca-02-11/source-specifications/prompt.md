# 绘图任务说明｜APOBEC Dry Lab 页面

> 交付对象：绘图负责同学
> 目的：按本包内的数据与规格，重绘 Dry Lab 页面上的图，使全页风格统一
> 配套文件：`data/`（每图一份 CSV）、`reference/`（现图，供版式参考）、`data_dictionary.md`（列名释义）、`manifest.json`（清单与校验）

---

## 1. 这份包在解决什么

Dry Lab 页面上有 14 张图。其中 **4 张是你此前画的聚类分析图**（第 1、12–14 张），另外 **10 张是本次需要重绘的**（第 2–11 张）。

这 10 张图原本已经画好，但它们的尺寸、配色与标注规范是另一套，与页面上你那 4 张不一致。本次的目标是：**用你的绘图规范重画这 10 张，让整页 14 张看起来像一套**。

因此本包提供了三样东西：
1. **每张图的作图数据**（`data/`），已整理成自包含的 tidy CSV，列名自解释，你不需要进入项目目录；
2. **每张图的作图规格**（本文第 4 节），写明面板划分、坐标轴、颜色与标记编码、参考线、需要标注的点；
3. **现图**（`reference/`），供你比对版式与信息量。

**最重要的一条约束：数值不能改。** 所有数字都已与文章正文核对一致；重绘时只调整视觉呈现，不要重新计算、不要四舍五入到不同精度、不要删改数据点。

---

## 2. 需要重绘的图（10 张）

| 图号 | 标题 | 数据文件 | 现图 | 面板数 |
|---|---|---|---|---|
| Figure 2 | Diagnosis of contact-probability deviation | `figure_02_cp_deviation.csv` | `figure_02_cp_deviation.png` | 2 |
| Figure 3 | Per-residue contact-probability change | `figure_03_ddcp_matrix.csv` | `figure_03_ddcp_heatmap.png` | 1 |
| Figure 4 | Negative-control deviation diagnosis | `figure_04_negctrl_diagnosis.csv` | `figure_04_negctrl_diagnosis.png` | 2 |
| Figure 5 | Control constructs in PC space and by D_M | `figure_05_negctrl_pca.csv` | `figure_05_negctrl_pca.png` | 2 |
| Figure 6 | Protein-only models across feature sets | `figure_06a/06b` | `figure_06_protein_only.png` | 2 |
| Figure 7 | Complex vs protein-only deviation | `figure_07_protein_only_vs_complex.csv` | `figure_07_...png` | 1 |
| Figure 8 | Single-site saturation | `figure_08_single_site.csv` | `figure_08_single_site.png` | 1 |
| Figure 9 | Behaviour of the targeting ratio | `figure_09_targeting_ratio.csv` | `figure_09_targeting_ratio.png` | 2 |
| Figure 10 | Next-round candidate overview | `figure_10a/10b/10c` | `figure_10_candidates.png` | 2 |
| Figure 11 | Retrospective test of the AiCE filter | `figure_11a/11b/11c` | `figure_11_aice_filter.png` | 2 |

`reference/` 里另外 4 张（`figure_01`、`figure_12`–`figure_14`）是你原有的聚类图，**本次不需重画**，放在包里是为了让你看到整页的视觉上下文。

---

## 3. 样式规范（沿用你现有那 4 张图的规范）

以下是我从你的绘图脚本里提取的规格，请确认无误后照此执行；若你的规范已有更新，以你的为准，并在交付说明里注明差异。

| 项目 | 规格 |
|---|---|
| 字体 | Noto Sans CJK SC（本机若无，用同族 Noto Sans SC / 微软雅黑替代） |
| 基础字号 | `font.size = 10`，`axes.titlesize = 12` |
| 画布宽度 | 15.8 in（多面板图同宽，横向铺满） |
| 导出 | PNG dpi 300、白底、`bbox_inches=None`（版面由 gridspec 显式控制）；另出 SVG 与 PDF |
| 主色 | 蓝 `#246A9A`、橙 `#B46A19`、绿 `#347565`、灰 `#64748B`、墨 `#18334B` |
| 浅色填充 | `#D6E6F2`、`#F4D5B6`、`#D0E6DE`、`#E8EAEE`、`#DCCFEA` |
| 网格与轴线 | 网格 `#DDE3E8` lw 0.7；轴线 `#A6B2BD`；`tick length = 0, pad = 7` |
| 版式 | 左上 `fig.text` 标题（20, 墨）→ 副标题（11, 灰）→ 底部脚注行 |
| 图例 | **统一置于面板下方**（图级图例、`frameon=False`），不放进坐标轴区域 |
| 图内文字 | **全英文**（页面正文为英文） |
| 面板字母 | A / B，置于坐标轴左上外侧 |

**版面要求（重要）**：每张图最多 2 个面板，一律 **1 行 × 2 列**横向排列，不要用 2×2 排布——这是为了避免图例与数据点重叠、并保证小图也能看清。单面板图直接横向铺满。

---

## 4. 逐图规格

### Figure 2｜Diagnosis of contact-probability deviation

**数据**：`data/figure_02_cp_deviation.csv`（14 行）

- **面板 A — Deviation descriptors**
  - 横轴：`construct`（14 个，建议旋转 45°）
  - 纵轴：z-score vs wild type (SD)
  - 内容：三个 z 描述量分组柱状图，每组 3 根柱 → `z_internal_cp_longrange`（蓝）、`z_pocket_cp`（橙）、`z_protein_targetC_cp`（绿）
  - 参考线：灰带 **±3 SD**（表示该描述量自身的噪声下限）
- **面板 B — Deviation against measured activity**
  - 横轴：`z_protein_targetC_cp`
  - 纵轴：`activity_retention_fraction`
  - 散点，并在左上角标注 Pearson r 与 n（由数据自行计算）

**图注（英文，请与图一致）**：Panel A gives the three deviation descriptors per construct, with the grey band marking the ±3 SD noise floor of the descriptor itself. Panel B plots the protein–target-C deviation against measured activity retention. Together they show that deviation computed from contact probabilities is not ordered by whether a construct is active, which is what first indicated the limits of this descriptor.

---

### Figure 3｜Per-residue contact-probability change

**数据**：`data/figure_03_ddcp_matrix.csv`（22 行 × 21 列，宽表：行=残基，列=构建体）

- 单面板热图：`imshow`
- 行标签：`wt_aa` + `residue_position`（如 `H29`），按序列位置排列
- 列标签：构建体名（旋转 45°）
- 发散配色（如 `RdBu_r`），**以 0 为中心对称**，色标范围取 `±max|ΔΔCP|`
- **仅标注 |ΔΔCP| ≥ 0.05 的格**（格子内写数值，文字颜色按底色深浅切换黑白）
- 右侧加颜色条，标签 `ΔΔCP vs wild type`

> 若你想自行挑选残基，用 `figure_03_all_residues_ddcp.csv`（完整 199 残基）；但请保持与现图一致的「变化最大的 22 个残基」这一选择规则，否则与正文表述不符。

**图注**：The matrix shows ΔΔCP for the 22 residues with the largest change, across all mutant constructs, computed as the difference between each mutant's ΔCP and the wild-type baseline. Only values with |ΔΔCP| ≥ 0.05 are labelled. Values near zero indicate that the mutation does not change how the residue is organised against the two substrates. Re-running the wild-type construct independently sets the interpretation threshold at max|ΔΔCP| = 0.0265.

---

### Figure 4｜Negative-control deviation diagnosis

**数据**：`data/figure_04_negctrl_diagnosis.csv`（**29 行** = 27 个对照 + 2 个野生型参照）

> ⚠ **两个面板用两套互不相干的编码，必须各配一条图例，不能合并**：
> - **面板 A 的柱** 按 `functional_class` 着色 → **功能类别图例**
> - **面板 B 的柱** 按描述量着色 → **描述量图例**（Internal CP (long-range) 蓝 / Pocket CP 橙 / Protein–target-C CP 绿）
>
> 图注旧版本曾写「全图按功能类别着色」，那是错的，已改。

- **面板 A — Catalytic geometry**
  - 横轴：`construct`（旋转 45°）；纵轴：target C4N4 – E72 distance (Å)
  - 柱体按功能类别着色
  - **参考线 = 本表内野生型（GCG 亲本）的值 2.599 Å**，虚线。**不要用 2.88 Å**——那个值出自另一套几何测量（`results/dE72_regression.csv` 的 2.884 Å），与本表不同源；两者不可混用。
  - **`target_C4N4_to_E72_distance_A` 为空的行（E72A）**：该构建体未做几何建模。**不要补 0**，不要画成 0 高的柱子；建议不画柱，在对应位置标一个「not modelled」的叉号或文字。
- **面板 B — Deviation descriptors**
  - 三色分组柱（同 Figure 2 面板 A）＋ ±3 SD 灰带

**功能类别配色（共 6 类，缺一不可）**：

| 类别 | 编码 |
|---|---|
| Active | 绿 `#347565` |
| Inactive | 橙 `#B46A19` |
| Partially inactive | 蓝 `#246A9A` |
| Not tested | 灰 `#64748B` |
| **New inactive control (not measured)** | **白底 + 橙描边 + 斜线阴影** |
| Wild-type reference | 紫 `#6D4C8E` |

> **「New inactive control (not measured)」是设计但未实测的失活对照（E72A、N57A），不得并入已实测的 Inactive 组。** 用白底+橙描边斜线阴影，与实心橙在视觉上明确区分。
> 散点图（如 Figure 5）用同义编码：该类别画成**空心、橙描边**的点。

**图注**：The two panels use independent encodings and therefore carry separate legends. Panel A gives the catalytic distance to E72 for each control construct, with bars coloured by functional class and the dashed line marking the wild-type value of this table (2.599 Å); panel B gives the three deviation descriptors, with bars coloured by descriptor against the ±3 SD noise floor. E72A was not geometrically modelled, so its distance is absent rather than zero; E72A and N57A are designed inactive controls that have not been assayed and are kept distinct from the measured inactive group. Among the constructs that were modelled, E72A is among the least deviant, whereas the substrate-only control is among the most deviant.

---

### Figure 5｜Control constructs in PC space and by D_M

**数据**：`data/figure_05_negctrl_pca.csv`（28 行）

- **面板 A — Principal-component space**：`PC1`（横）对 `PC2`（纵）散点，按 `functional_class` 着色；**仅标注这 7 个点**：E72A、N57W、N57A、T31D、T31A、WT-GCA、Y32F（28 个全标会糊掉，这是刻意只标关键对照）
- **面板 B — Deviation from wild type**：`D_M_mahalanobis_to_WT` 横向柱状图，按 D_M 升序排列，柱体按功能类别着色（同 Figure 4 的 6 类配色），图例一套；参考线 **1.57**（野生型零假设 95 分位）
- 类别编码同 Figure 4；其中 **New inactive control (not measured)**（E72A、N57A）在散点里画成**空心＋橙描边**，与已实测失活组区分

**图注**：Including the controls reorganises the principal-component space, and the D_M ranking is shown alongside. The leading components separate constructs by which substrate was modelled rather than by whether the construct is functional. E72A and N57A, which were designed but not assayed, are shown as their own class (hollow, orange outline) rather than merged into the measured inactive group.

---

### Figure 6｜Protein-only models across feature sets

**数据**：`data/figure_06a_protein_only_deviation.csv`（10 行）、`data/figure_06b_protein_only_classification.csv`（3 行）

- **面板 A**：三个特征集的分组柱状图 → `D_M_internal_cp_all`（蓝）、`D_M_internal_cp_longrange`（橙）、`D_M_pocket_cp`（绿）；横轴 `construct`（旋转 45°），纵轴 D_M within the protein-only models
- **面板 B**：`classification_accuracy` 柱状图，横轴 `feature_set`（三个：Internal CP (all) / Internal CP (long-range) / Pocket CP），纵轴 dead / active classification accuracy，柱顶标数值；参考线 `chance_level = 0.50`

**图注**：Panel A gives the deviation from wild type within the protein-only models, computed separately for three internal-contact feature sets; panel B gives the accuracy with which a construct can be assigned to the dead or active group from those models. With the RNA removed, the constructs separate according to changes in the protein itself, and comparison with the complex-based analysis isolates how much of the original grouping was attributable to the bound substrate.

---

### Figure 7｜Deviation in the complex and protein-only conditions

**数据**：`data/figure_07_protein_only_vs_complex.csv`（10 行）

- 单面板，每构建体一对柱：`D_M_complex_with_RNA`（蓝）、`D_M_protein_only_no_RNA`（橙）
- 横轴 `construct`，按 `D_M_protein_only_no_RNA` 升序（数据已排好）；纵轴 D_M
- 参考线 **1.57**
- **仅在 T31D 与 E72A 上方标注** `fraction_retained_pct`（写成如「22% retained」）

**图注**：Each construct is shown under both modelling conditions. T31D loses most of its deviation when RNA is removed, whereas E72A is the single construct whose deviation increases, indicating that its interface deviation had been suppressed rather than caused by RNA binding.

---

### Figure 8｜Single-site saturation of the APOBEC domain

**数据**：`data/figure_08_single_site.csv`（103 行 = 102 个单点突变体 + 1 行亲本）

- 单面板散点：横轴 `plus1_ratio_GCG_over_GCA`，纵轴 `activity_retention_vs_same_batch_parent`
- 点着色：`activity_retention ≥ 0.70` 用蓝、其余用灰（正文的保留下限）
- **星标 = K30H**（`mutant = "30H"`），旁标数值「(1.71, 0.84)」
  - ⚠ **K30H 的定义要写准**：它是「**保留率 ≥ 0.70 的突变体中 +1 比最高者**」。它**既不是全图纵坐标最高点**（最高点是 25F，保留 1.04），**也不是全图比值最高点**（最高是 130G 的 3.00）。旧图注写「K30H is the highest point in the panel」是错的，已改。
- 参考线三条：亲本 **1.371**（点线）、目标 **2.0**（橙虚线）、保留下限 **0.70**（绿虚线）
  - 亲本取值用 `is_parent = TRUE` 行的 `plus1_ratio_GCG_over_GCA`（= 1.3707，显示为 **1.371**，与正文一致；源表里的 1.37 是同一个数的两位小数写法，请统一用 1.371）
- **比值超过 2.0 的三个点**（130G 3.00、60Q 2.55、31G 2.22）保留率只有 0.32 / 0.17 / 0.13，请确保它们以灰点呈现并加浅色标注，**不要**在图上让它们看起来像达标点
- **`plus1_ratio_defined = FALSE` 的行（31Y）不入图**：其 GCA 检出为 0，比值不可定义（源表记为 0 属编码歧义，不是零值）。请勿当作 0 值点绘制
- 图例置于面板下方

**图注**：Each point is a single mutant, plotted as specificity against activity retention, with the same-batch parent and the target threshold marked. The starred point is **K30H, the highest +1 ratio among mutants retaining at least 70% activity (1.71)**; it is neither the highest point of the panel nor the highest ratio in it. Three substitutions exceed the 2.0 target in raw ratio (130G 3.00, 60Q 2.55, 31G 2.22) but retain under 40% activity, and 31Y is not plotted because its GCA editing was undetected, making the ratio undefined rather than zero. Most substitutions reduce activity without changing specificity.

---

### Figure 9｜Behaviour of the targeting ratio across the amplicon

**数据**：`data/figure_09_targeting_ratio.csv`（51 行，**作画前先筛掉 `is_wildtype_parent = TRUE`，剩 50 行**）

- **面板 A**：横轴 `on_target_C388_pct`，纵轴 `targeting_ratio`；灰/浅色带标出两个活性层（10–20% 与 35–60%），并画该层中位数粗线（**2.53** 与 **1.20**）
- **面板 B**：横轴 `sum_nonGCG_editing_pct`，纵轴 `targeting_ratio`；加线性拟合线，并在左上角标出 Pearson r、Spearman ρ、n（由数据自行计算）

> **`targeting_ratio_defined = FALSE` 的 9 行**：这些构建体的脱靶编辑全在检出线下，分母为零、比值无定义。**这些行的 `targeting_ratio` 单元格是空的，请勿当作 0 参与拟合或在图上画成 0 点。** 正文以「∞」记述，不入图。

**图注**：Panel A shows the ratio against on-target editing, with the low- and high-activity strata marked; panel B shows the ratio against total off-target editing, with both correlation coefficients. The ratio rises as on-target activity falls, because low-activity constructs lose their off-target signal to the detection floor.

---

### Figure 10｜Overview of the candidate set for the next engineering cycle

**数据**：`figure_10b_candidate_group_sizes.csv`（面板 A）、`figure_10c_candidate_priority_matrix.csv`（面板 B）、`figure_10a_candidate_groups_raw.csv`（61 条原始清单，供核对）

- **面板 A**：各组规模柱状图。横轴 `group`（A–E），纵轴候选数；柱顶标数值（A=18、B=6、C=12、D=5、E=20，合计 61）。分组标签建议在轴上多行显示：A replication / B new single / C new combinations / D controls / E relaxed pairing
- **面板 B**：组内优先级堆叠柱状图，堆叠顺序 `Required → P0 (top pick) → P0 (gold standard) → P0 (control) → P0 → P1 (control) → P1 (mechanism) → P1 → P2 (mechanism) → P2 (reference) → P2`，图例置于面板下方

**图注**：Panel A gives the size of each group, and panel B the priority composition within each group. The control group converts two contested mechanisms into measured comparisons rather than arguments from structure.

---

### Figure 11｜Retrospective application of the AiCE structural-constraint filter

**数据**：`figure_11b_positions_passing_threshold.csv`（面板 A）、`figure_11c_contested_substitutions.csv`（面板 B）、`figure_11a_sampling_frequency_by_position.csv`（逐位点频率原始表，供你复核曲线）

- **面板 A**：横轴 `sampling_frequency_threshold`，纵轴 `n_positions_passing`；折线图，两条参考线 **γ = 0.5**（绿，卷曲区）与 **β = 0.8**（橙，结构化区）
- **面板 B**：四个争议替换（H29P 0.771 / K30T 0.562 / N57D 0.875 / A59P 0.896）的柱状图，柱顶标数值；参考线 **γ = 0.5**，纵轴 0–1

> 采样来源为 48 条 ProteinMPNN 序列（T = 0.3）；曲线上每一点的算法是「该位点最高氨基酸频率 ≥ 阈值」的位点计数，如需复核请用 `figure_11a`。

**图注**：Panel A shows how many positions survive the frequency threshold as the threshold is raised, with the thresholds recommended for coil and structured regions marked; panel B shows the sampling frequency of the substitutions previously nominated as strongly preferred. All of them exceed the permissive threshold, so none would be removed by the filter.

---

## 5. 数据使用约定

- **编码**：全部 CSV 为 UTF-8 with BOM，逗号分隔，首行为列名。
- **空缺**：空白单元格表示「该值无定义或不可靠」，**不要补 0**。已用布尔列显式标注，例如 `targeting_ratio_defined`、`is_reference_wildtype`、`is_parent`、`is_wildtype_parent`、`exceeds_threshold`。
- **布尔列**：取值为字符串 `TRUE` / `FALSE`。
- **单位**：列名已带单位（`_A` = 埃、`_pct` = 百分比、`_fraction` = 0–1 小数、`_distance_A` = 埃）。百分比与小数请勿混用。
- **精度**：保留到 CSV 中给出的位数即可，不要为「好看」再四舍五入。
- 每份文件的 SHA-256 见 `data_dictionary.md`，可校验你拿到的数据未被改动。

---

## 6. 交付要求

1. 每张图输出 **PNG（300 dpi）+ SVG + PDF**，命名沿用 `figure_NN_短名`（如 `figure_02_cp_deviation.png`）。
2. **图内文字全英文**，与本文第 4 节给出的图注一致；图注本身外置（不放进图内）。
3. 每张图附一份 `caption.md`（用第 4 节的英文图注）与 `alt-text.txt`（一句话无障碍描述）。
4. 若某张图的**数据或规格你认为有问题**，请先提出再动手，不要自行改数或改结论——这些数字都与正文绑定。
5. 交回时请附一份简短说明：实际使用的字体与配色、与本文规格的差异、以及任何你改动过的呈现决定。

---

## 7. 本轮修正记录（2026-09-24）

上一版交付后，队里审出 6 个问题，已全部修正。列出以便你核对，也避免同类错误再出现：

| # | 问题 | 处理 |
|---|---|---|
| 1 | **31Y** 的 GCA 检出为 0，但 `plus1_ratio` 被填成 0 | 比值不可定义≠0。该行 `plus1_ratio` 已**留空**，并加 `plus1_ratio_defined = FALSE`；规格里明确**不入图** |
| 2 | **Figure 8 图注与参考图不一致**：图注要求突出 K30H，参考图星标却在 130G | 星标改为 **K30H**，并把定义写准为「保留率 ≥ 0.70 中比值最高者」；同时说明它并非全图纵坐标最高点、也非比值最高点 |
| 3 | 亲本比值 **1.37 / 1.371 精度不统一** | 统一为 **1.371**（由亲本 GCG÷GCA 未舍入值得出，与正文一致）；源表的 1.37 是同一数的两位写法 |
| 4 | Figure 4 参考线用 **2.88 Å**，而同表 WT(GCG) 是 **2.599 Å** | 参考线改用**本表内**野生型值 **2.599 Å**；2.88 出自另一套几何测量，规格中已注明不可混用 |
| 5 | **E72A 的距离为 nan**，有被补 0 的风险 | 该单元格**留空**；规格要求不画柱、标「not modelled」，绝不补 0 |
| 6 | Figure 4 **颜色编码冲突**：面板 B 按描述量三色，图注却说全图按功能类别着色 | 明确两套编码、**两条独立图例**；图注已改。另：E72A/N57A 的类别是「**New inactive control (not measured)**」，**不得并入已实测失活组**，用白底+橙描边+斜线阴影与实心橙区分 |

顺带修正了正文中两处同类事实问题（已同步到文章与中英对照版）：
- 「无单点达到 2.0」→ 实为 3 个原始比值超 2.0（130G/60Q/31G），但保留率均 <40%；准确表述是「**保留活性者中无人达到 2.0**」。
- 「28 个中只有 4 个既超阈值又确证失活」→ 与该表不符，改为可核验的「**11 个保留活性者中有 7 个也超过 1.57 阈值**」，同样支撑「偏离不按功能排序」。

**为防再犯**，规格里对易错点一律显式写明「不要补 0」「不要用另一个表的数值」「这条线取自哪张表」，数据表中所有无定义值都留空并配布尔列标注。如你发现仍有歧义，请直接指出。

## 8. 需要你先确认的两点

1. **Figure 4 的行数**：正文写「28 constructs」，而本图数据是 29 行（27 个对照 + 2 个野生型参照）。我按 29 行准备数据，与现图一致。若你认为应统一为 28，请告知，我会同时调整正文与图注。
2. **紫色 `#6D4C8E`**：Figure 4 / Figure 5 需要区分 6 个功能类别，你的调色板里没有对应主色，我加了紫色作「野生型参照」一类。若你有既定做法，请替换。

---

## 9. 包内文件

```
APOBEC_DryLab_绘图数据包/
├── prompt.md                      ← 本文件
├── data_dictionary.md             ← 每份 CSV 的列名释义与 SHA-256
├── manifest.json                  ← 清单（含全部数据文件的行数、列名、说明）
├── data/                          ← 16 份数据表
│   ├── figure_02_cp_deviation.csv
│   ├── figure_03_ddcp_matrix.csv / figure_03_all_residues_ddcp.csv
│   ├── figure_04_negctrl_diagnosis.csv
│   ├── figure_05_negctrl_pca.csv
│   ├── figure_06a_protein_only_deviation.csv / figure_06b_protein_only_classification.csv
│   ├── figure_07_protein_only_vs_complex.csv
│   ├── figure_08_single_site.csv
│   ├── figure_09_targeting_ratio.csv
│   ├── figure_10a_candidate_groups_raw.csv / figure_10b_..._sizes.csv / figure_10c_..._matrix.csv
│   └── figure_11a_..._by_position.csv / figure_11b_..._threshold.csv / figure_11c_contested_substitutions.csv
└── reference/                     ← 14 张现图（Figure 2–11 待重绘；1、12–14 为你的原图）
```
