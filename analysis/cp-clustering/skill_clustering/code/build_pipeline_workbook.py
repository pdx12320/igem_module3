"""Prepare typed source/result data for artifact-tool workbook authoring."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = Path('/tmp/cp_pipeline_workbook_c18fccb23287')
TMP.mkdir(exist_ok=True)

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def num(value):
    return float(value) if value not in ('', None) else None

summary = read(ROOT/'results/pipeline_summary.csv')
labels = read(ROOT/'results/pipeline_labels.csv')
manifest = read(ROOT.parent/'variance_cp/results/manifest_with_cluster_comparison.csv')
provenance = json.loads((ROOT/'skills_provenance.json').read_text())
by_label = {(r['pipeline'],r['construct']): int(r['cluster']) for r in labels}
assert len(summary) == 32 and len(manifest) == 11

methods = {'ward':'Ward','average':'平均连接','complete':'完全连接','kmeans':'K-means','pca95_kmeans':'PCA95 + K-means','spectral':'RBF 谱聚类','gmm_pca3':'PCA3 + GMM','hdbscan2':'HDBSCAN min=2','hdbscan3':'HDBSCAN min=3','dbscan_q50':'DBSCAN q50','dbscan_q75':'DBSCAN q75'}
subsets = {'variable_all':'全部可变 CP','variable_top10':'可变 CP 前 10%','variable_top20':'可变 CP 前 20%','variable_top30':'可变 CP 前 30%','zscore_variable':'逐 CP 标准化','confidence70':'双端 pLDDT≥70','core70_153':'双端位于 70–153'}
categories = {'main':'主要比较','exploratory':'探索性','sensitivity':'敏感性'}
pipeline_rows=[]
for r in summary:
    note = ''
    if r['common_n_clusters']=='0': note='全部为噪声，100%重复无有效分组'
    elif num(r['common_n_noise'])>0: note='轮廓系数仅计算非噪声构建'
    elif num(r['common_singletons'])>0: note='含单构建簇，需结合覆盖与稳定性'
    if r['subset']=='core70_153': note='核心局部分组，原始全 CP 轮廓系数为负'
    pipeline_rows.append([r['pipeline'],subsets[r['subset']],methods[r['method']],categories[r['category']],num(r['n_features']),num(r['chosen_k']),num(r['common_n_clusters']),num(r['common_n_noise']),num(r['common_coverage']),num(r['common_singletons']),num(r['common_silhouette']),num(r['native_silhouette']),num(r['bootstrap_exact_reselected']),num(r['bootstrap_exact_fixed_k']),num(r['bootstrap_mean_ARI_reselected']),num(r['bootstrap_mean_ARI_fixed_k']),r['cluster_sizes'],num(r['pca_components']),num(r['pca_retained_variance']),note])

selected = ['variable_all__'+m for m in ['ward','average','complete','kmeans','pca95_kmeans','spectral','gmm_pca3','hdbscan2','hdbscan3','dbscan_q50','dbscan_q75']] + ['variable_top10__spectral','confidence70__ward','core70_153__ward']
construct_rows=[]
construct_order=['wt','e72a','g27dm130g','g27tk30hq58m','k30h','m132d','m132e','n57a','n57w','t31a','t31d']
for name in construct_order:
    r=next(r for r in manifest if r['construct']==name)
    act=num(r['wet_activity_value'])
    flag='可对照' if r['eligible_for_activity_comparison']=='True' else ('活性缺失' if act is None else '序列命名不符')
    note=''
    if name=='g27dm130g': note='提交 G27D+M130G，结构实际 G27D+W130G；活性 0.000 暂不纳入定量比较'
    elif act is None: note='原表活性为空，保留缺失'
    elif name in ('t31a','t31d'): note='T31A/D 活性 0.970/0.000；多流程仍同簇'
    construct_rows.append([r['manifest_construct'],r['actual_mutations'],act,flag,int(r['observed_seed_count'])]+[by_label[p,name] for p in selected]+[note])

candidate_path=ROOT/'results/prior_candidate_crosscheck.csv'
if not candidate_path.exists():
    raise SystemExit('Candidate crosscheck is not ready; re-run when final data exists.')
candidates=read(candidate_path)
candidate_keys=['residue','prior_variance_rank','unique_partition_equal_rank','unique_partition_top20_fraction','LOCO_rank_min','LOCO_rank_max','LOCO_top20_fraction','principal_contact_by_unique_BCSS','source_region','catalytic_role','min_construct_CA_pLDDT','low_confidence_any_construct_CA_pLDDT_lt70','interpretation']
numeric_candidate_keys=[]
for k in candidate_keys:
    vals=[r[k] for r in candidates if r[k]!='']
    try:
        [float(v) for v in vals]
        if vals: numeric_candidate_keys.append(k)
    except ValueError:
        pass
candidate_rows=[[num(r[k]) if k in numeric_candidate_keys else r[k] for k in candidate_keys] for r in candidates]

method_rows=[
 ['样本单位','11 个独立构建。280 个结构聚合为 56 个 seed，再按构建取均值。seed 反映计算重复。'],
 ['CP 范围','199 aa。非局部接触要求 |i−j|≥4。全部 19,110 对中有 766 对跨构建变化。'],
 ['特征筛选','可变 CP 前 10%/20%/30% 对应 77/154/230 对。筛选依据为构建均值间方差。'],
 ['无监督约束','活性未参与特征筛选、聚类、类数选择或热点排序。提交清单仅作事后对照。'],
 ['主流程','Ward、平均连接、完全连接、K-means、PCA95 + K-means、RBF 谱聚类各比较 4 组特征，共 24 流程。'],
 ['其他流程','PCA3 + GMM、HDBSCAN 两参数、DBSCAN 两参数及标准化、置信度、核心区域 3 项敏感性，共 8 流程。'],
 ['类数选择','主流程 k=2–4，按拟合输入空间轮廓系数选择。GMM 固定 PCA3 后以 BIC 比较 k=1–4。密度法不指定 k。'],
 ['统一原始空间','common 指完整非局部 CP 的原始概率空间。用于跨流程比较分组几何。'],
 ['拟合输入空间','native 指各流程实际拟合的 CP 子集、PCA 或标准化空间。与 common 同列保留，避免混用。'],
 ['密度法指标','噪声标签为 −1。轮廓系数排除噪声。覆盖率为非噪声构建数 / 11。零簇时轮廓系数为空。'],
 ['簇编号','簇编号仅在同一流程内有效。两个 −1 都代表未归入簇，不能据此认为它们同簇。'],
 ['重采样方法','200 次 seed bootstrap：在每个构建内有放回抽样整个 seed，并重做特征排序、变换与聚类。'],
 ['重选 k 完全重复率','每次重采样重新选择 k，检验完整流程与基线分组的一致性。固定 k 重复率固定基线 k。'],
 ['ARI 与噪声','ARI 是分组一致性指标。密度结果计算 ARI 时把 −1 作为一个类别；解释必须同时看噪声人数与覆盖率。'],
 ['稳定性的含义','重复率衡量当前结构计算对 seed 的稳健性，不能换算为活性预测准确率或实验成功率。'],
 ['UMAP 补充','另做 5 维 UMAP + HDBSCAN/K-means，100 次 seed 重采样；邻居数 3/5/8，各 20 个随机种子敏感性分析。详见结果包。'],
 ['局部核心','70–153 是上传序列与 APOBEC1 匹配的核心片段。来源分段不能定义完整催化结构域边界。'],
 ['候选一致性','6 个主算法产生 3 种唯一分区。按唯一分区等权汇总接触间簇平方和 BCSS，再按残基汇总。相同分组不会重复投票。'],
 ['候选排名敏感性','LOCO 每次去掉 1 个构建，重算剩余 10 个构建的原始方差残基排名，共 11 次。该列与 BCSS 排名不同，用于检查面板依赖。'],
 ['催化对照','同源映射提示 H70、E72、C102、C105 为直接催化或配位残基。热点排名仅表示现有突变面板的结构响应。'],
 ['活性缺失','WT、N57A、E72A 活性空白。单位、实验重复与三个 C 位点对应关系未提供。'],
 ['命名不符','G27DM130G 的结构为 G27D+W130G。保留原表活性数值并标记，排除该项定量比较。'],
 ['复现输入','本文件数字来自 pipeline_summary.csv、pipeline_labels.csv、prior_candidate_crosscheck.csv 与上传提交清单。Excel 保存外部分析结果，不在单元格内重新拟合聚类。'],
 ['技能固定版本','K-Dense-AI/scientific-agent-skills commit '+provenance['skills'][0]['source_commit']],
]
for s in provenance['skills']: method_rows.append([s['name'],s['source_url']])
method_rows += [['scikit-learn 文档','https://scikit-learn.org/stable/modules/clustering.html'],['UMAP 文档','https://umap-learn.readthedocs.io/en/latest/clustering.html'],['催化注释来源','https://www.uniprot.org/uniprotkb/P41238/entry']]

data={'pipeline_rows':pipeline_rows,'construct_rows':construct_rows,'selected_pipelines':selected,'candidate_keys':candidate_keys,'candidate_numeric_keys':numeric_candidate_keys,'candidate_rows':candidate_rows,'method_rows':method_rows}
(TMP/'workbook_data.json').write_text(json.dumps(data,ensure_ascii=False,allow_nan=False))
print(json.dumps({'rows':[len(pipeline_rows),len(construct_rows),len(candidates)],'candidate_columns':candidate_keys},ensure_ascii=False))
