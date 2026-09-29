# 数据字典｜Dry Lab 绘图数据包

每张图的数据表见 `data/`，列名自解释并含单位。所有数值与文章正文一致，重绘时请勿改动数值本身。

布尔列取值为字符串 `TRUE` / `FALSE`；空白单元格表示「无定义或不可靠」，请勿补 0。

## `data/figure_02_cp_deviation.csv`

面板 A = 前三个 z 列分组柱状图（灰带 ±3）；面板 B = z_protein_targetC_cp 对 activity_retention_fraction 散点。仅 GCG 底物。

| 列名 | 说明 |
|---|---|
| `construct` | 构建体名（突变体/组合/对照） |
| `z_internal_cp_longrange` | 蛋白内部长程接触概率相对野生型的 z 值（SD 数） |
| `z_pocket_cp` | 活性口袋内部接触概率相对野生型的 z 值 |
| `z_protein_targetC_cp` | 蛋白–靶位 C 接触概率相对野生型的 z 值 |
| `target_C4N4_to_E72_distance_A` | 靶碱基 C4N4 原子到催化谷氨酸 E72 的距离（埃）；野生型参考值 2.88 |
| `activity_retention_fraction` | 活性保留率（相对同批亲本，0–1 小数；混合了表达、稳定性与催化，非纯化活性） |

SHA-256：`227c452d55f7b2de0f3287aa6b8bf07ba30fde0660402cb0b5a52e6fc011e5cb`

## `data/figure_03_ddcp_matrix.csv`

ΔΔCP 宽表（行=残基，列=构建体）。已按 |ΔΔCP| 最大值选出变化最大的 22 个残基，与文章图一致。

| 列名 | 说明 |
|---|---|
| `residue_position` | 残基序号（1-based，对应 199 aa 编号） |
| `wt_aa` | 该位点的野生型氨基酸（单字母） |
| `G25E` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G25E-K30H` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27T` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27D` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27T-K30H` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27D-K30H` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27T-K30H-Q58M` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27D-K30H-Q58M` | 该构建体的 ΔΔCP（相对野生型基线） |
| `K30H` | 该构建体的 ΔΔCP（相对野生型基线） |
| `K30H-Q58M` | 该构建体的 ΔΔCP（相对野生型基线） |
| `Q58M` | 该构建体的 ΔΔCP（相对野生型基线） |
| `R28A` | 该构建体的 ΔΔCP（相对野生型基线） |
| `R28S` | 该构建体的 ΔΔCP（相对野生型基线） |
| `T31V` | 该构建体的 ΔΔCP（相对野生型基线） |
| `T31I` | 该构建体的 ΔΔCP（相对野生型基线） |
| `T31L` | 该构建体的 ΔΔCP（相对野生型基线） |
| `Y32F` | 该构建体的 ΔΔCP（相对野生型基线） |
| `A59P` | 该构建体的 ΔΔCP（相对野生型基线） |
| `K60R` | 该构建体的 ΔΔCP（相对野生型基线） |
| `M132D` | 该构建体的 ΔΔCP（相对野生型基线） |
| `M132E` | 该构建体的 ΔΔCP（相对野生型基线） |

SHA-256：`cf0cece09886f9147521a0182683b6a804300d703fdf41061e6e023c9c4faab1`

## `data/figure_03_all_residues_ddcp.csv`

完整 199 残基 × 全部构建体的 ΔΔCP，供需要自行挑选残基时使用。

| 列名 | 说明 |
|---|---|
| `residue_position` | 残基序号（1-based，对应 199 aa 编号） |
| `wt_aa` | 该位点的野生型氨基酸（单字母） |
| `G25E` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G25E-K30H` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27T` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27D` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27T-K30H` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27D-K30H` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27T-K30H-Q58M` | 该构建体的 ΔΔCP（相对野生型基线） |
| `G27D-K30H-Q58M` | 该构建体的 ΔΔCP（相对野生型基线） |
| `K30H` | 该构建体的 ΔΔCP（相对野生型基线） |
| `K30H-Q58M` | 该构建体的 ΔΔCP（相对野生型基线） |
| `Q58M` | 该构建体的 ΔΔCP（相对野生型基线） |
| `R28A` | 该构建体的 ΔΔCP（相对野生型基线） |
| `R28S` | 该构建体的 ΔΔCP（相对野生型基线） |
| `T31V` | 该构建体的 ΔΔCP（相对野生型基线） |
| `T31I` | 该构建体的 ΔΔCP（相对野生型基线） |
| `T31L` | 该构建体的 ΔΔCP（相对野生型基线） |
| `Y32F` | 该构建体的 ΔΔCP（相对野生型基线） |
| `A59P` | 该构建体的 ΔΔCP（相对野生型基线） |
| `K60R` | 该构建体的 ΔΔCP（相对野生型基线） |
| `M132D` | 该构建体的 ΔΔCP（相对野生型基线） |
| `M132E` | 该构建体的 ΔΔCP（相对野生型基线） |

SHA-256：`f4fe729a608f0c972a2879ec57c07d067836edddcfbf28ddc7e8c8010d8da91a`

## `data/figure_04_negctrl_diagnosis.csv`

**两套编码，必须各配一套图例**：面板 A 的柱按 `functional_class` 着色（功能类别图例）；面板 B 的柱按描述量着色——Internal CP (long-range) 蓝、Pocket CP 橙、Protein–target-C CP 绿（描述量图例）。两条图例不可合并为一条。共 29 行 = 27 个突变体/组合对照 + 2 个野生型参照（is_reference_wildtype = TRUE）。类别取值共 6 种：Active / Inactive / Partially inactive / Not tested / New inactive control (not measured) / Wild-type reference；其中「New inactive control (not measured)」是设计但未实测的失活对照，**不得并入已实测的 Inactive 组**。面板 A 的参考线请取**本表内**野生型（GCG 亲本）的值 = 2.599 Å；不要使用 2.88 Å —— 那个值来自另一套几何测量（results/dE72_regression.csv 的野生型 2.884 Å），与本表不同源。E72A 的该列**留空**（未做几何建模），请勿补 0，也请勿在图上画成 0 点。另：正文「28 constructs」指的是 阴性对照_DM.csv 那一套（含 WT 换底物），与本表行数不同，作图按本表 29 行。

| 列名 | 说明 |
|---|---|
| `construct` | 构建体名（突变体/组合/对照） |
| `is_reference_wildtype` | TRUE = 该行是野生型参照，不是突变体对照 |
| `functional_class` | 功能类别：Active / Inactive / Partially inactive / Not tested / WT (GCA substrate) |
| `target_C4N4_to_E72_distance_A` | 靶碱基 C4N4 原子到催化谷氨酸 E72 的距离（埃）；野生型参考值 2.88 |
| `z_internal_cp_longrange` | 蛋白内部长程接触概率相对野生型的 z 值（SD 数） |
| `z_pocket_cp` | 活性口袋内部接触概率相对野生型的 z 值 |
| `z_protein_targetC_cp` | 蛋白–靶位 C 接触概率相对野生型的 z 值 |
| `activity_retention_fraction` | 活性保留率（相对同批亲本，0–1 小数；混合了表达、稳定性与催化，非纯化活性） |

SHA-256：`9745edaac9f762d546a48b93ae4a64d58ffbdd44397e06104681ba0bc362671a`

## `data/figure_05_negctrl_pca.csv`

面板 A = PC1–PC2 散点（仅标注 E72A / N57W / N57A / T31D / T31A / WT-GCA / Y32F）；面板 B = D_M 横向柱状（参考线 1.57）。

| 列名 | 说明 |
|---|---|
| `construct` | 构建体名（突变体/组合/对照） |
| `PC1` | 第一主成分坐标（白化基仅由野生型 seed 定义） |
| `PC2` | 第二主成分坐标 |
| `PC3` | 第三主成分坐标 |
| `D_M_mahalanobis_to_WT` | 相对野生型的马氏距离 D_M；零假设 95 分位 = 1.57 |
| `activity_retention_fraction` | 活性保留率（相对同批亲本，0–1 小数；混合了表达、稳定性与催化，非纯化活性） |
| `functional_class` | 功能类别：Active / Inactive / Partially inactive / Not tested / WT (GCA substrate) |

SHA-256：`c85f486429c45c4d2283640ca67adf922d8ee8f0374b0c8335471f82595cf1dd`

## `data/figure_06a_protein_only_deviation.csv`

面板 A：三个特征集的分组柱状图。

| 列名 | 说明 |
|---|---|
| `construct` | 构建体名（突变体/组合/对照） |
| `D_M_internal_cp_all` | 纯蛋白条件下、以全部内部 CP 为特征集的 D_M |
| `D_M_internal_cp_longrange` | 纯蛋白条件下、仅用长程内部 CP 的 D_M |
| `D_M_pocket_cp` | 纯蛋白条件下、仅用口袋内部 CP 的 D_M |
| `activity_retention_fraction` | 活性保留率（相对同批亲本，0–1 小数；混合了表达、稳定性与催化，非纯化活性） |
| `functional_class` | 功能类别：Active / Inactive / Partially inactive / Not tested / WT (GCA substrate) |

SHA-256：`456867fe8f41d5756ff30c16cfaa7979af5c53e4128ec582885cd97d009888c2`

## `data/figure_06b_protein_only_classification.csv`

面板 B：柱状图，参考线 = 随机水平 0.50。

| 列名 | 说明 |
|---|---|
| `feature_set` | 特征集名称 |
| `classification_accuracy` | 把构建体判入失活组/活性组的准确率（0–1） |
| `chance_level` | 随机水平参考线 = 0.50 |

SHA-256：`8ca20ae9b52fcecc52e4c6e8277b1ee2ae23671ea214277d5bfe9109c51dedd5`

## `data/figure_07_protein_only_vs_complex.csv`

成对柱状图；参考线 1.57；仅在 T31D 与 E72A 上标注 fraction_retained_pct。

| 列名 | 说明 |
|---|---|
| `construct` | 构建体名（突变体/组合/对照） |
| `D_M_complex_with_RNA` | 复合物（含 RNA）条件下的 D_M |
| `D_M_protein_only_no_RNA` | 纯蛋白（无 RNA）条件下的 D_M |
| `fraction_retained_pct` | 纯蛋白 D_M ÷ 复合物 D_M（%），即未被 RNA 解释的那部分偏离占比 |
| `activity_retention_fraction` | 活性保留率（相对同批亲本，0–1 小数；混合了表达、稳定性与催化，非纯化活性） |

SHA-256：`20f58586b1778522367eaf3337c085a8855d3290078892030602e8186399bc94`

## `data/figure_08_single_site.csv`

散点：横轴 plus1_ratio，纵轴 activity_retention。参考线：亲本 1.371（点线，= 亲本 GCG ÷ GCA，未舍入）、目标 2.0（橙虚线）、保留下限 0.70（绿虚线）。**星标 = K30H**，定义是「保留率 ≥ 0.70 的突变体中 +1 比最高者」——它既不是全图纵坐标最高点，也不是全图比值最高点。比值最高的三个点为 130G (3.00)、60Q (2.55)、31G (2.22)，但保留率分别只有 0.32 / 0.17 / 0.13，请在图上以灰点呈现并考虑加浅色标注，避免被读成「已达标」。**plus1_ratio_defined = FALSE 的行（31Y）**：其 GCA 检出为 0，比值不可定义（原表记为 0 属编码歧义），该行 plus1_ratio 已留空，请勿当作 0 值点绘制。

| 列名 | 说明 |
|---|---|
| `mutant` | 单点突变体名（如 30H = K30H） |
| `on_target_GCG_fraction` | 靶点 c.388（GCG）编辑率（0–1 小数） |
| `off_target_GCA_fraction` | 脱靶 c.871（GCA）编辑率（0–1 小数） |
| `ACA_fraction` | c.295（ACA）编辑率（0–1 小数） |
| `plus1_ratio_GCG_over_GCA` | +1 比 = c.388 编辑率 ÷ c.871 编辑率 |
| `plus1_ratio_defined` | — |
| `activity_retention_vs_same_batch_parent` | 同上，列为该批次口径 |
| `read_depth` | 该样本测序深度 |
| `is_parent` | TRUE = 该行是亲本（用于定位参考线） |
| `reported_active` | 原表标注是否有活性（True/False） |

SHA-256：`bc7a10de5ffcd5979728e0a0973ed9262197eebcd557927b5937c1c9c78be589`

## `data/figure_09_targeting_ratio.csv`

面板 A：targeting_ratio 对 on_target_C388_pct（灰带 10–20% 与 35–60%，并标层中位数 2.53 / 1.20）；面板 B：对 sum_nonGCG_editing_pct 散点并加线性拟合。作图时请排除 is_wildtype_parent = TRUE 的行。targeting_ratio_defined = FALSE 表示分母为零、比值无定义，该单元格已留空请勿当 0 处理，这 9 行只在文中以「∞」记述、不入图。

| 列名 | 说明 |
|---|---|
| `construct` | 构建体名（突变体/组合/对照） |
| `is_wildtype_parent` | TRUE = 该行是同批亲本，作画时应排除 |
| `on_target_C388_pct` | 靶点 c.388 编辑率（%） |
| `sum_GCG_editing_pct` | 全部 GCG 位点编辑率之和（%） |
| `sum_nonGCG_editing_pct` | 全部非 GCG 位点编辑率之和（%） |
| `targeting_ratio` | 靶向比 = Σ(GCG) ÷ Σ(非 GCG)；分母为零时无定义（留空） |
| `targeting_ratio_defined` | FALSE = 分母为零，比值无定义，请勿当 0 处理 |
| `n_nonGCG_sites_detected` | 检出编辑的非 GCG 位点数 |
| `activity_retention_fraction` | 活性保留率（相对同批亲本，0–1 小数；混合了表达、稳定性与催化，非纯化活性） |

SHA-256：`7588a9de5730a8aa4933676b97fbf239dec9034cbceb4a4be5cbe07740e3261d`

## `data/figure_10a_candidate_groups_raw.csv`

61 条候选的原始清单，供核对条目。group = A–E。

| 列名 | 说明 |
|---|---|
| `candidate_id` | 候选编号 C01–C61 |
| `group` | 候选分组字母 A–E |
| `group_label` | 候选分组全称（原表中文） |
| `mutant` | 单点突变体名（如 30H = K30H） |
| `priority_en` | 优先级（已译为英文，如 P0 (top pick)） |

SHA-256：`e1ffaa5a086968508720b0ff0eb9b7f2c10ead309f1da22cd7fea97288dc2413`

## `data/figure_10b_candidate_group_sizes.csv`

面板 A：各组规模柱状图。

| 列名 | 说明 |
|---|---|
| `group` | 候选分组字母 A–E |
| `group_label_en` | 候选分组英文标签（作图用） |
| `n_candidates` | 该组候选数 |

SHA-256：`1b1e0290b3899906c7ffcb8a4260c118500c409d19678984938e404b828bbd0c`

## `data/figure_10c_candidate_priority_matrix.csv`

面板 B：组内优先级堆叠柱状图（列即优先级类别）。

| 列名 | 说明 |
|---|---|
| `group` | 候选分组字母 A–E |
| `P0` | 该构建体的 ΔΔCP（相对野生型基线） |
| `P0 (control)` | 该优先级下的候选数 |
| `P0 (gold standard)` | 该优先级下的候选数 |
| `P0 (top pick)` | 该优先级下的候选数 |
| `P1` | 该构建体的 ΔΔCP（相对野生型基线） |
| `P1 (control)` | 该优先级下的候选数 |
| `P1 (mechanism)` | 该优先级下的候选数 |
| `P2` | 该构建体的 ΔΔCP（相对野生型基线） |
| `P2 (mechanism)` | 该优先级下的候选数 |
| `P2 (reference)` | 该优先级下的候选数 |
| `Required` | 该优先级下的候选数 |

SHA-256：`f042069fca889bd9d889489b35f213db187a66743b70d485bb4b16e5c2cf2a08`

## `data/figure_11a_sampling_frequency_by_position.csv`

ProteinMPNN 采样（48 条序列）逐位点最高频率，供自行重算「通过阈值位点数」曲线。

| 列名 | 说明 |
|---|---|
| `position` | 残基序号（1-based） |
| `most_frequent_aa` | ProteinMPNN 采样中该位点出现最多的氨基酸 |
| `frequency` | 该氨基酸在采样序列中的频率（0–1） |

SHA-256：`b89370c40f189b819508f28d193188598acda2a2febd720c0e84e369f7e2c7c0`

## `data/figure_11b_positions_passing_threshold.csv`

面板 A 的曲线数据；参考线 γ = 0.5（卷曲区）与 β = 0.8（结构化区）。

| 列名 | 说明 |
|---|---|
| `sampling_frequency_threshold` | 采样频率阈值（横轴） |
| `n_positions_passing` | 最高频率 ≥ 阈值的位点数量 |

SHA-256：`4773d3eaedd96d6ebd8749becf4ae7b9d2a8a46b1d5f16d1e52d620592ed5d6c`

## `data/figure_11c_contested_substitutions.csv`

面板 B：柱状图，参考线 γ = 0.5。

| 列名 | 说明 |
|---|---|
| `substitution` | 替换名（如 H29P） |
| `sampling_frequency` | 该替换在 ProteinMPNN 采样中的频率（0–1） |
| `applicable_threshold_gamma` | 该位点适用的频率阈值（卷曲区 γ = 0.5） |
| `secondary_structure` | 二级结构：C = 无规卷曲，E = 折叠 |
| `exceeds_threshold` | TRUE = 频率超过适用阈值，因此不会被过滤器剔除 |

SHA-256：`062638b9832bbcb0d7a39eb624707865ba30d4704dd578e84f3a7576c0c391c2`

