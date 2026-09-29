# 逐图规格｜组合突变与三元组（N1–N4）

> 样式沿用你既有的规范（`orca_plot.py` / `orca-figure-style.json`），本文只写**面板划分、坐标轴、参考线、标注点**。
> 数据在 `data/`，参考图在 `reference/`。图内文字一律英文，图注外置。

---

## N1｜Combinatorial batch: +1 ratio against activity retention

**数据**：`data/combo_batch_ratio_vs_retention.csv`（48 行，其中 36 行比值可定义）
可选背景层：`data/single_mutant_background.csv`（101 个单点）

**单面板散点图**（也可做成 A/B 两个面板：A = 全景，B = 保留率 ≥0.70 的放大视图）。

- **横轴**：`activity_retention_fraction`（0–1），标签 `activity retention (c.388 vs the batch parent)`
- **纵轴**：`on_target_GCG_over_offtarget_GCA_ratio`（0–4），标签 `+1 ratio (c.388 GCG ÷ c.871 GCA)`
- **点**：每个构建体一个点；建议按 `n_substitutions`（2 或 3）用**不同形状或深浅**区分双点与三点
- **帕累托前沿**：把 `on_pareto_front = TRUE` 的 6 个点连成虚线
  （顺序：`32F` → `32F-58M` → `32F-132E` → `27T-30H-58M` → `27D-30H-32F` → `58M-130G`）
- **参考线**：
  - `y = 2.0`（达标线，暖橙虚线）
  - `y = 1.371`（单点批亲本比值，灰点线）——用于说明「单点的起点」
  - `x = 0.70`（保留率下限，青绿虚线）
  - **两条线的交点即「达标区」**，本批唯一落入该区的点就是三元组
- **必须凸显的三元组**：`is_the_triple = TRUE` 的那一点用**星形 + 更大的尺寸 + 加粗标注**
  （`27T-30H-58M`，比值 2.156 / 保留率 0.773）。这是本图的视觉焦点。
  - 建议在星标旁加一行小字：`only construct with ratio ≥2.0 and retention ≥0.70`
- **可选背景层**：把 `single_mutant_background.csv` 的点画成**浅灰小点**（不带描边），置于组合点之下。
  若采用，请加一句图例说明单点是**另一批次**的数据，仅作对照。
- **不要做的事**：
  - 不要把 `on_target_GCG_over_offtarget_GCA_ratio` 为空的那 12 行画成 0 —— 它们是「c.871 未检出、比值不可定义」，请**不绘制**（或在图外用一行小字说明被排除的个数）
  - 不要给点加误差棒（原始数据没有提供重复级不确定度）

**图注（英文，供外置使用）**：
> 48 combinatorial constructs from a single transfection batch; 36 have a defined +1 ratio (in 12, c.871 was undetected, so the ratio is undefined and those constructs are not plotted). The dashed line joins the six constructs on the Pareto front of ratio against retention. Reference lines mark the 2.0 target ratio, the single-mutant parent level (1.371) and a 0.70 retention floor. The star marks 27T-30H-58M (ratio 2.156, retention 0.773), the only construct in the batch satisfying both ratio ≥2.0 and retention ≥0.70; among constructs retaining at least 0.70 activity it has the highest ratio (next: 1.851). The ratio–activity trade-off is visible across the rest of the batch. Ratios are not comparable across batches built in different library backgrounds.

---

## N2｜Where the triple sits within each batch

**数据**：`data/triple_record_across_batches.csv`（3 行）

> ⚠ **先读 README 第 4 节。** 第三批建库背景与前两批不同，三个绝对比值**不可横比**。

**推荐做法（二选一）**：

**(a) 只画批内名次（推荐）**——单面板水平柱状或点阵：
- 纵轴三个批次（combinatorial / supplementary / third），横轴为**批内名次**
  （用 `rank_by_ROF_within_batch`，并标出所在批次的总构建体数 `n_constructs_in_batch`）
- 注意补充批的名次列为空（该批三元组自身所在孔失败，只有其 132E 版本），**该行请只标数值不标名次**，并在图注说明

**(b) 不画图，只作附表**——把 `triple_record_across_batches.csv` 整理成一张表放进正文。
**若你对口径没有把握，选 (b)。**

**不要做的事**：不要把 2.156 / 2.083 / 1.278 三个绝对比值并排画成柱状图。
第三批的 1.278 是背景差异造成的，并排会误导读者以为特异性掉了近一半。

---

## N3｜Results of the designed batch（用你的规范重绘）

**数据**：`data/designed_batch_groups.csv`（37 行）、`data/designed_batch_groupD_pairing.csv`（5 行）

**面板 A**：37 个突变组，横轴 `activity_retention_fraction`，纵轴 `ROF_ratio_over_same_batch_parent`，
按 `design_group_label_en` 着色（A 复验 / B 新单点 / C 新组合 / D 控制 / E 放宽与异常 / 不在候选表）。
参考线 `y = 1.00`（同批亲本）与 `x = 0.70`（保留率下限）。
**`ratio_defined = FALSE` 的组不得画在 y = 0**；`excluded_failed_well = TRUE` 的那一组
（`27T-30H-58M`，所在孔判为测量失败）请用醒目方式单独标注为 `failed well, excluded`，**不作为数据点解读**。

**面板 B**：5 根柱，主量 `activity_retention_fraction`，
按 `bar_order` 排序：同骨架跨两批的两次测量（0.772 / 0.673）+ 同背景 132D/132E 配对（0.340 / 0.752）
+ 第 5 根为幽灵柱（0.079，`excluded_failed_well = TRUE`，白底红描边斜线阴影，标 `failed well, excluded`）。
第 1 根的比值/ROF 取自组合批，请在图中注明该柱来自另一批次。

---

## N4｜Third batch: within-batch rank and position-27 saturation

**数据**：`data/third_batch_all_groups.csv`（29 行）

**面板 A（推荐的三面板之一）**：全部突变体（`is_reference_group = FALSE`，25 个）
按 `ROF_ratio_over_same_batch_parent` 对 `activity_retention_fraction` 散点，画帕累托前沿，
**把 `construct = 27T-30H-58M` 用星形凸显**——它是该批的枢纽点：
保留率 ≥0.95 者中 ROF 最高（1.218 对 1.146），ROF ≥1.20 者中保留率最高（0.980 对 0.745/0.783/0.619）。
参考线 `y = 1.00`、`x = 0.95`。

**面板 B**：`group_type = single` 且组名以 `27` 开头的 10 行（27 位饱和），
`ROF` 对 `activity_retention_fraction` 散点，参考线 `y = 1.00`、`x = 0.90`，
**把 ROF ≥1.13 的三个（27I / 27V / 27E）用另一种颜色或形状区分**。

**面板 C**：同样这 10 个替换的 `ACA_class_C295_fraction` 柱状图，
参考线取 `construct = PUF12` 的 **0.3091**。
**`C295_not_detected = TRUE` 的 7 根柱不得画成 0 高度**——请标 `n.d.`（低于 5% 检测线），
并加图例说明「未检出 ≠ 编辑效率为 0」。这 7 根柱是本图最重要的信息。

---

## 5. 数据字典

| 列名 | 说明 |
|---|---|
| `construct` | 构建体名（如 `27T-30H-58M`） |
| `n_substitutions` | 该构建体含几个取代（2 = 双点，3 = 三点） |
| `on_target_GCG_over_offtarget_GCA_ratio` | **+1 比** = c.388（GCG）编辑率 ÷ c.871（GCA）编辑率；**仅可同批比较** |
| `activity_retention_fraction` | 活性保留率（相对**同批亲本**，0–1 小数；混合了表达、稳定性与催化，非纯化酶活） |
| `ROF_ratio_over_same_batch_parent` | ROF = 本构建体比值 ÷ **同批亲本**比值；跨批唯一可比量 |
| `on_pareto_front` | TRUE = 位于「比值与保留率同时最大化」的帕累托前沿 |
| `rank_by_ROF` / `rank_by_retention` | 批内名次（1 = 最高） |
| `on_pareto_front` / `is_the_triple` | 布尔列，取值字符串 `TRUE` / `FALSE` |
| `ratio_defined` | FALSE = 分母（c.871）未检出，比值无定义，**请勿当 0** |
| `excluded_failed_well` | TRUE = 该孔判为测量失败予以剔除，**其全部数值都不是有效读数** |
| `C295_not_detected` | TRUE = 两个重复均低于 5% 检测线；属有效读数但**不得画成 0** |
| `cross_batch_value_comparable` | FALSE = 该批与前几批建库背景不同，**比值不可横比** |
| `is_reference_group` / `is_reference_parent` | TRUE = 该行是参照（PUF 变体 / 同批亲本），作参考线而非数据点 |

**契约**：CSV 为 UTF-8 with BOM；空白单元格 = 无定义或不可用，**不要补 0**；布尔列为字符串 `TRUE`/`FALSE`；
数值请保留 CSV 中给出的位数，不要为「好看」再四舍五入。

`data/` 内 6 个文件的 SHA-256 见随包的 `SHA256SUMS.txt`，可校验数据未被改动。

---

## 6. 交付要求

1. 每张图输出 PNG（300 dpi）+ SVG + PDF，命名 `N1_...`/`N2_...`/`N3_...`/`N4_...`（或沿用你既有的 `figure_XX_...` 命名，只要与正文引用一致）
2. 每张图附 `caption.md`（用本文的英文图注）与 `alt-text.txt`
3. **图内文字全英文**
4. 若某张图的**数据或规格你认为有问题，请先提出再动手**——这些数字都与正文绑定，尤其 N2 的口径
5. 交回时附一份简短说明：实际使用的字体与配色、与本文规格的差异、以及任何你改动过的呈现决定
