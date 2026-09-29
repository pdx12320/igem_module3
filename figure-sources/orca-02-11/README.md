# APOBEC Dry Lab · ORCA figures 2–11

本目录交付 10 张重绘图。打开 `index.html` 可逐图浏览；`APOBEC_Figures_02–11.pdf` 可一次查看全部矢量图。

每张图的子目录包含 300 dpi PNG、SVG、PDF、英文图注、替代文本、来源数据、绘图记录及适用的排除清单。SVG 文字已转路径，PDF 嵌入字体子集。图形通过 Python 与 CSV 复现，不是 PowerPoint 原生统计图对象。

## 样式与呈现决定

- 实际主字体：系统 Futura Medium；数学下标与个别希腊符号分别由 DejaVu Sans 和 Arial Unicode MS 补充，详见字体检查记录。没有将商业字体文件打包。
- 白底、靛紫主色、青绿比较色、暖橙强调；无图内标题或长图注。所有图内文字为英文。
- 多面板图仍为左右排列。Figure 2A 与 Figure 4 改为横向柱条，保留全部构建体名称和原有顺序。
- Figure 3 保留 22 × 21 矩阵及所有需标注数值的原始精度。为避免相邻数字重叠，单元格数值纵向显示；该高密度图请使用可放大的 SVG/PDF 查看细节。主轴标签 21 pt，单元格标注 13.5 pt，为这一图记录的字号例外。
- 描述量固定映射：Internal CP (long-range) 为紫色，Pocket CP 为青绿，Protein–target-C CP 为橙色；Figure 6 新增 Internal CP (all) 为深靛紫。同一指标不跨图换色。
- 功能类别固定映射：Active 为青绿；Inactive 为橙色；Partially inactive 为紫色；Not tested 为灰色；未实测的设计失活对照用空心/斜线橙色；WT reference 为深靛紫。
- Figure 10 用颜色区分优先级层级、纹理区分子类别，保留全部 11 类及原始堆叠顺序。

## 数据处理与说明修正

原数据包未修改；`source-data/` 是原 CSV 的逐字节副本，校验值写入每张图的 manifest。

- Figure 2：A 面板 14 个构建体；B 面板 10 个有活性结果的点，Pearson r = −0.150886。缺失活性不补零。
- Figure 3：从全长 199 残基表复核最大绝对变化前 22 个残基；排序按序列位置，色标 ±0.395，147 个格子满足标注阈值。
- Figure 4：保留 29 行，A 面板 28 个有距离结果的柱条。WT 参考线为本表 2.599 Å。E72A 标记为 Distance unavailable，不由缺失结果推断“没有建模”。
- Figure 5：28 个点与 28 个排名条目。WT (GCA substrate) 映射到共同的 Wild-type reference 类别。11 个 Active 中有 7 个 D_M >1.57。
- Figure 6：原样展示三项准确率；数据包未说明分类评估方案、标签分母和不确定性，图注不将其称为独立验证性能。
- Figure 7：保留两种模型条件的 D_M 与已有百分比。不把两种距离之比解释为 RNA 的因果贡献比例。
- Figure 8：101 个有效突变体点；31Y 无定义比值排除并记录，亲本只用参考线表示。K30H 单独星标，数值 1.71、0.84；亲本 1.3707 显示为 1.371。
- Figure 9：排除 1 个亲本及 9 个无定义比值，两个面板各 41 点。Pearson r = −0.390128；Spearman ρ = −0.557017，使用平均秩处理并列值。低/高活性层中位数 2.528 / 1.203，显示为 2.53 / 1.20。拟合仅为描述性 OLS，不新增置信区间或显著性检验。比值与其分母之间存在数学耦合，不仅凭该相关性断言因果机制。
- Figure 10：61 个候选清单条目；A–E 各为 18/6/12/5/20。未去重或将候选描述成已完成实验。
- Figure 11：由 199 位点频率表核对全部 40 个阈值曲线点。四个替换均超过所提供的 0.5 阈值；作为回顾性比较呈现。

`source-specifications/` 保留收到的原说明，含此前指出的旧释义；实际绘图口径以本 README、各图 caption 和 manifest 为准。P0/P1/P2 表示候选数量，不是 ΔΔCP；activity retention 表示相对于同批亲本的活性保留率，不是 GCG/GCA 比值。原文没有包含在绘图包内，本交付不声称已同步修改 Wiki 正文。

## 复现

需要 Python 3、Matplotlib、NumPy；已安装 Futura 时自动使用 Futura，否则按配置回退 Arial。用于复核 PDF/SVG 的 PyMuPDF 与 Pillow 不影响绘图本身。

```sh
python3 plot.py --output figures-reproduced
```

指定新的输出目录，脚本会拒绝覆盖已有导出。`orca_plot.py` 和 `orca-style.json` 一并保留，因此无需依赖插件缓存路径。

正式输出为 `figures/`；`_work/` 仅为本次制作过程的草稿，不进入交付 ZIP。
