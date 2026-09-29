# GitHub skills CP 聚类流程对比

先阅读 `skill_clustering/deliverables/CP_clustering_workflow_report.html`。报告内嵌图片可离线打开；工作簿 `CP_clustering_workflow_comparison.xlsx` 提供32流程、11构建及17候选对照。

## 复现

解压后保留目录关系，在根目录依次执行：

```bash
python skill_clustering/code/compare_pipelines.py
python skill_clustering/code/hotspot_comparison.py
python skill_clustering/code/umap_sensitivity.py
python skill_clustering/code/compare_activity.py
python skill_clustering/code/plot_pipeline_comparison.py
python skill_clustering/code/build_workflow_report.py
```

数值主流程需要 numpy、pandas、scipy、scikit-learn、threadpoolctl；绘图需要 matplotlib 和完整 Noto Sans CJK SC 字体。运行版本保存在 `skill_clustering/results/runtime_versions.json`。UMAP 的完整版本见 `umap_requirements.txt`，建议独立环境，固定 umap-learn0.5.12、numba0.63.1、llvmlite0.46.0。最初较新 numba 导入失败的兼容性处理已记录，最终160次UMAP拟合全部完成。

绘图代码中字体路径为本次环境的安装位置；在其他系统可将路径改为完整 Noto Sans CJK SC 的实际位置。官方字体：[Noto CJK](https://github.com/notofonts/noto-cjk)。报告中的PDF/SVG已嵌入或转曲文字，阅读现有图无需安装字体。

Excel文件已经生成并验证，排版脚本使用本次运行环境的 @oai/artifact-tool。普通Python环境不需要执行工作簿脚本即可复现数值。工作簿源码作为排版记录保留。

## 数据和统计定义

`variance_cp/results/variance_features.npz` 包含11构建与56seed的完整19110对非局部CP、CαpLDDT、残基索引；本轮从已提取的数组开始复现，原ZIP提取流程见上一轮交付包。
其余 `variance_cp/results` 文件保留上一轮候选、残基注释、活性匹配和T31A/D局部差异；`upload/_提交清单.csv` 为原始提交表副本。

本轮32配置×200次seedbootstrap=6400条；60次UMAP邻域/随机敏感性与100次seedbootstrap各运行2算法，共320条结果。seed是计算重复，独立生物学单元只有11个构建。
共同CP空间 silhouette 与各输入/嵌入空间 silhouette 分开保存；密度方法的指标剔除噪声，必须连同覆盖率解读。噪声-1不表示这些点同簇；ARI字段把-1作为一种类别，相关局限保留在报告和结果说明。
固定k和重选k复现率分开；置信度mask固定于基线，其他特征/预处理在bootstrap内重拟合。

热点BCSS衡量对结构分区的贡献；6主算法仅产生3个唯一分区，所以重点看唯一分区等权结果。LOCO指每次省略一个已有构建后重算方差排名，不能解释为新构建预测验证。

## Skills 来源

已安装 K-Dense-AI/scientific-agent-skills 的 scikit-learn1.3、umap-learn1.3、statistical-analysis1.2，固定commit330c8e764435a731eff571e3efdda70b363d0792。完整上游来源、文件hash、安装版本和安装页见 `skills_provenance.json`。本包保留的是依指南改写的分析代码；用户账户内skills已单独保存，无需重新安装才能阅读结果。

参考：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. https://doi.org/10.48550/arXiv.2609.00065

## 校验记录

已独立复核全部共同CP silhouette、6400条ARI/精确复现率、共聚矩阵、簇数选择及部分重采样特征重建；UMAP记录和热点BCSS守恒校验通过。主脚本末尾曾有 NumPy int64 的JSON导出错误，数值CSV/NPZ已全部完成；JSON导出已修复并从完成的CSV补齐，不影响数值结果。状态见 `run_status.json`。

`SHA256SUMS.json` 包含包内除自身之外全部文件哈希。报告没有从活性选择参数，没有填补WT/N57A/E72A空白，也没有将G27命名错配的0.000直接映射到结构。
