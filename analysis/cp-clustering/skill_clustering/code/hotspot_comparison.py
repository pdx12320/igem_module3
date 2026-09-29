#!/usr/bin/env python3
"""Unsupervised contact/residue attribution and leave-one-construct-out sensitivity.

BCSS is a descriptive decomposition of clusters fitted to the same CP data.
No experimental activity, outcome labels, or hypothesis-test p-values are used.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent
OUT = ROOT / 'results'
OUT.mkdir(parents=True, exist_ok=True)
F = np.load(BASE / 'variance_cp/results/variance_features.npz')
X = F['construct_features']
I, J = F['feature_i'], F['feature_j']
NAMES = F['constructs'].astype(str).tolist()
VARIABLE = np.ptp(X, axis=0) > 1e-12
ANNO = pd.read_csv(BASE / 'variance_cp/results/annotated_all_residues.csv').sort_values('position')
SEQ = dict(zip(ANNO.position, ANNO.WT_aa))
N_RES = len(ANNO)
BASELINE = pd.read_csv(OUT / 'pipeline_baseline.csv')
LABELS = pd.read_csv(OUT / 'pipeline_labels.csv')
FEATURES = np.load(OUT / 'pipeline_baseline_arrays.npz')


def label_vector(pipeline):
    s = LABELS[LABELS.pipeline.eq(pipeline)].set_index('construct').cluster
    assert len(s) == len(NAMES) and not s.index.duplicated().any()
    labels = s.reindex(NAMES).to_numpy(dtype=int)
    assert not (labels < 0).any(), 'Main/sensitivity attribution requires assigned constructs.'
    return labels


def signature(labels):
    mapping = {}
    return tuple(mapping.setdefault(int(k), len(mapping)) for k in labels)


def bcss(labels):
    center = X.mean(axis=0)
    score = np.zeros(X.shape[1])
    for k in np.unique(labels):
        selected = X[labels == k]
        score += len(selected) * (selected.mean(axis=0) - center) ** 2
    score[~VARIABLE] = 0
    return score


def residue_sum(score):
    return np.bincount(I, score, minlength=N_RES) + np.bincount(J, score, minlength=N_RES)


def ranks(score):
    # Competition ranking prevents arbitrary ordering of equal/zero scores.
    return rankdata(-np.asarray(score), method='min').astype(int)


def fraction_top(scores, limit):
    return np.mean([(ranks(score) <= limit) & (score > 0) for score in scores], axis=0)


def save(frame, name):
    frame.to_csv(OUT / name, index=False, encoding='utf-8-sig')


MAIN = BASELINE[BASELINE.category.eq('main') & BASELINE.subset.eq('variable_all')]
ALL_MAIN = BASELINE[BASELINE.category.eq('main')]
assert len(MAIN) == 6 and len(ALL_MAIN) == 24
partitions, partition_methods = {}, {}
method_contacts, method_residues = {}, {}
for _, row in MAIN.iterrows():
    labels = label_vector(row.pipeline)
    sig = signature(labels)
    if sig not in partitions:
        partitions[sig] = bcss(labels)
        partition_methods[sig] = []
    partition_methods[sig].append(row.method)
    method_contacts[row.method] = partitions[sig]
    method_residues[row.method] = residue_sum(partitions[sig])

UNIQUE_CP = list(partitions.values())
UNIQUE_RES = [residue_sum(s) for s in UNIQUE_CP]
mean_cp = np.mean(UNIQUE_CP, axis=0)
mean_res = residue_sum(mean_cp)
var_cp = np.var(X, axis=0, ddof=1)
var_cp[~VARIABLE] = 0
var_res = residue_sum(var_cp)
assert np.allclose(var_res, ANNO.contact_variance_sum, atol=1e-12)
assert np.all(mean_cp <= var_cp * (len(NAMES)-1) + 1e-12)

contact = pd.DataFrame({
    'position_i': I + 1, 'position_j': J + 1,
    'contact': [f'{SEQ[i+1]}{i+1}–{SEQ[j+1]}{j+1}' for i,j in zip(I,J)],
    'between_construct_variance': var_cp,
    'prior_variance_rank': ranks(var_cp),
    'unique_partition_equal_BCSS': mean_cp,
    'unique_partition_equal_rank': ranks(mean_cp),
    'algorithm_equal_BCSS': np.mean(list(method_contacts.values()), axis=0),
    'algorithm_equal_rank': ranks(np.mean(list(method_contacts.values()), axis=0)),
    'unique_partition_top20_fraction': fraction_top(UNIQUE_CP, 20),
    'unique_partition_top50_fraction': fraction_top(UNIQUE_CP, 50),
    'algorithm_top20_fraction': fraction_top(list(method_contacts.values()), 20),
    'algorithm_top50_fraction': fraction_top(list(method_contacts.values()), 50),
    'n_main_algorithms': len(MAIN), 'n_unique_partitions': len(partitions),
})
residue = ANNO[['position', 'WT_aa', 'source_region', 'reference_accession',
                'reference_position', 'catalytic_role', 'annotation_basis',
                'WT_CA_pLDDT', 'min_construct_CA_pLDDT',
                'already_mutated_in_uploaded_structures']].copy()
residue['residue'] = [f'{aa}{p}' for p, aa in zip(residue.position, residue.WT_aa)]
residue['prior_variance_rank'] = ranks(var_res)
residue['prior_variance_sum'] = var_res
residue['unique_partition_equal_BCSS'] = mean_res
residue['unique_partition_equal_rank'] = ranks(mean_res)
residue['algorithm_equal_BCSS'] = np.mean(list(method_residues.values()), axis=0)
residue['algorithm_equal_rank'] = ranks(residue.algorithm_equal_BCSS)
residue['unique_partition_top20_fraction'] = fraction_top(UNIQUE_RES, 20)
residue['algorithm_top20_fraction'] = fraction_top(list(method_residues.values()), 20)
residue['n_main_algorithms'] = len(MAIN)
residue['n_unique_partitions'] = len(partitions)
residue['low_confidence_any_construct_CA_pLDDT_lt70'] = residue.min_construct_CA_pLDDT < 70

for method in method_contacts:
    contact[f'{method}_BCSS'] = method_contacts[method]
    contact[f'{method}_rank'] = ranks(method_contacts[method])
    residue[f'{method}_BCSS'] = method_residues[method]
    residue[f'{method}_rank'] = ranks(method_residues[method])
for count, (sig, cp) in enumerate(partitions.items(), 1):
    contact[f'partition{count}_BCSS'] = cp
    contact[f'partition{count}_rank'] = ranks(cp)
    residue[f'partition{count}_BCSS'] = residue_sum(cp)
    residue[f'partition{count}_rank'] = ranks(residue_sum(cp))

principal, top3 = [], []
for p in range(N_RES):
    touching = np.flatnonzero((I == p) | (J == p))
    order = touching[np.lexsort((J[touching], I[touching], -mean_cp[touching]))]
    names = contact.iloc[order[mean_cp[order] > 0]].contact.tolist()
    principal.append(names[0] if names else '')
    top3.append('; '.join(names[:3]))
residue['principal_contact_by_unique_BCSS'] = principal
residue['top3_contacts_by_unique_BCSS'] = top3

# Recompute purely unsupervised variance ranks after omitting each construct.
loco_scores, loco_ranks, loco_rows = [], [], []
for omit_idx, omit in enumerate(NAMES):
    reduced = np.delete(X, omit_idx, axis=0)
    reduced_var = np.var(reduced, axis=0, ddof=1)
    reduced_var[np.ptp(reduced, axis=0) <= 1e-12] = 0
    score = residue_sum(reduced_var)
    rank = ranks(score)
    loco_scores.append(score)
    loco_ranks.append(rank)
    for p in range(N_RES):
        loco_rows.append({'omitted_construct': omit, 'position': p+1,
                          'residue': f'{SEQ[p+1]}{p+1}', 'variance_sum': score[p],
                          'rank': rank[p], 'in_top20': bool(rank[p] <= 20 and score[p] > 0)})
loco_ranks = np.asarray(loco_ranks)
residue['LOCO_top20_fraction'] = fraction_top(loco_scores, 20)
residue['LOCO_rank_min'] = loco_ranks.min(axis=0)
residue['LOCO_rank_median'] = np.median(loco_ranks, axis=0)
residue['LOCO_rank_max'] = loco_ranks.max(axis=0)
residue['LOCO_rank_span'] = residue.LOCO_rank_max - residue.LOCO_rank_min
residue['LOCO_worst_rank_omitted_constructs'] = [
    '; '.join(name for name, r in zip(NAMES, loco_ranks[:,p]) if r == loco_ranks[:,p].max())
    for p in range(N_RES)]
save(pd.DataFrame(loco_rows), 'hotspot_LOCO_residue_ranks.csv')

# Report subsets separately. Common CP space isolates the effect of the partition;
# native feature masks additionally show consequences of removing contacts.
sensitivity_rows, subset_rows = [], []
for subset, rows in ALL_MAIN.groupby('subset', sort=False):
    sigs = {}
    native_sigs = {}
    for _, row in rows.iterrows():
        labels = label_vector(row.pipeline)
        sig = signature(labels)
        cp = bcss(labels)
        native = np.zeros_like(cp)
        idx = FEATURES[row.pipeline + '__features']
        native[idx] = cp[idx]
        sigs[sig] = cp
        native_sigs[sig] = native
        common_r = residue_sum(cp)
        native_r = residue_sum(native)
        for p in range(N_RES):
            sensitivity_rows.append({
                'pipeline': row.pipeline, 'subset': subset, 'method': row.method,
                'position': p+1, 'residue': f'{SEQ[p+1]}{p+1}',
                'common_space_BCSS': common_r[p], 'common_space_rank': ranks(common_r)[p],
                'native_feature_BCSS': native_r[p],
                'native_feature_rank': int(ranks(native_r)[p]) if native_r[p] > 0 else np.nan,
                'native_incident_selected_contacts': int(np.sum((I[idx] == p) | (J[idx] == p))),
                'n_native_contacts': len(idx), 'partition_signature': str(sig),
            })
    common_mean = residue_sum(np.mean(list(sigs.values()), axis=0))
    native_mean = residue_sum(np.mean(list(native_sigs.values()), axis=0))
    for p in range(N_RES):
        subset_rows.append({
            'subset': subset, 'position': p+1, 'residue': f'{SEQ[p+1]}{p+1}',
            'n_methods': len(rows), 'n_unique_partitions': len(sigs),
            'common_space_unique_equal_BCSS': common_mean[p],
            'common_space_unique_equal_rank': ranks(common_mean)[p],
            'native_feature_unique_equal_BCSS': native_mean[p],
            'native_feature_unique_equal_rank': int(ranks(native_mean)[p]) if native_mean[p] > 0 else np.nan,
        })
save(pd.DataFrame(sensitivity_rows), 'hotspot_pipeline_residue_ranks.csv')
save(pd.DataFrame(subset_rows), 'hotspot_subset_comparison.csv')

# Separate biological/confidence/scaling sensitivity, excluded from main consensus.
extra_rows = []
for _, row in BASELINE[BASELINE.category.eq('sensitivity')].iterrows():
    labels = label_vector(row.pipeline)
    cp = bcss(labels)
    common = residue_sum(cp)
    native_cp = np.zeros_like(cp)
    idx = FEATURES[row.pipeline + '__features']
    native_cp[idx] = cp[idx]
    native = residue_sum(native_cp)
    for p in range(N_RES):
        extra_rows.append({'pipeline': row.pipeline, 'position': p+1,
                           'residue': f'{SEQ[p+1]}{p+1}',
                           'common_space_BCSS': common[p], 'common_space_rank': ranks(common)[p],
                           'native_feature_BCSS': native[p],
                           'native_feature_rank': int(ranks(native)[p]) if native[p] > 0 else np.nan,
                           'native_incident_selected_contacts': int(np.sum((I[idx] == p) | (J[idx] == p)))})
save(pd.DataFrame(extra_rows), 'hotspot_representation_sensitivity.csv')

prior = pd.read_csv(BASE / 'variance_cp/results/candidate_residues.csv')
candidate = prior[['position','screening_category','screening_reason']].merge(
    residue, on='position', validate='one_to_one')
subset_frame = pd.DataFrame(subset_rows)
for subset in ['variable_all', 'variable_top10', 'variable_top20', 'variable_top30']:
    s = subset_frame[subset_frame.subset.eq(subset)].set_index('position')
    candidate[f'{subset}_native_unique_equal_rank'] = candidate.position.map(s.native_feature_unique_equal_rank)
    candidate[f'{subset}_common_unique_equal_rank'] = candidate.position.map(s.common_space_unique_equal_rank)
candidate['interpretation'] = np.where(candidate.unique_partition_top20_fraction.eq(1),
    '三种唯一主分区均进入前20；描述结构分组差异',
    np.where(candidate.unique_partition_top20_fraction.gt(0),
    '进入前20依赖于分组；保留局部接触或机制依据',
    '主分区BCSS前20未覆盖；依据原局部接触/催化注释单独评估'))
candidate.loc[candidate.low_confidence_any_construct_CA_pLDDT_lt70, 'interpretation'] += '；部分构建局部pLDDT低于70'
save(contact[VARIABLE].sort_values(['unique_partition_equal_rank','position_i','position_j']), 'contact_consensus.csv')
save(residue.sort_values(['unique_partition_equal_rank','position']), 'residue_consensus.csv')
save(candidate, 'prior_candidate_crosscheck.csv')

partition_rows = []
for idx, (sig, cp) in enumerate(partitions.items(), 1):
    partition_rows.append({'partition': idx, 'methods': partition_methods[sig],
                           'groups': [[name for name, label in zip(NAMES, sig) if label == k] for k in sorted(set(sig))],
                           'n_clusters': len(set(sig)), 'total_BCSS': float(cp.sum()),
                           'variance_explained_fraction': float(cp.sum() / ((len(NAMES)-1)*var_cp.sum()))})
main_partition_sigs = {signature(label_vector(p)) for p in ALL_MAIN.pipeline}
summary = {
    'n_constructs': len(NAMES), 'n_nonlocal_CP': X.shape[1], 'n_variable_CP': int(VARIABLE.sum()),
    'n_main_algorithms': len(MAIN), 'n_unique_main_partitions': len(partitions),
    'n_related_main_subset_pipelines': len(ALL_MAIN), 'n_unique_partitions_across_24_pipelines': len(main_partition_sigs),
    'BCSS_formula': 'sum_k n_k * (mean_CP_in_cluster_k - overall_mean_CP)^2, raw CP probability units squared',
    'residue_formula': 'sum of incident contact BCSS; each contact contributes to both endpoints',
    'equal_weight_consensus': 'arithmetic mean raw BCSS across unique partitions, each counted once',
    'LOCO_definition': 'omit each construct, recompute sample variance across remaining ten construct means and incident-residue variance ranks',
    'rank_ties': 'competition rank (min); zero scores never selected as top20',
    'activity_used': False,
    'partitions': partition_rows,
    'rank_correlation_prior_variance_vs_unique_BCSS': float(spearmanr(var_res, mean_res).statistic),
    'top20_overlap_prior_variance_vs_unique_BCSS': int(np.sum((ranks(var_res)<=20)&(ranks(mean_res)<=20))),
    'sequence_W95_check': SEQ[95],
}
(OUT / 'hotspot_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))

lines = [
    '# 关键接触和残基：不同聚类流程的一致性', '',
    '输入为11个构建的等权均值，每个构建内先平均同一seed的5个结构，再平均seed。'
    '全部统计均未读取活性标签。', '',
    f'主比较覆盖6种方法，但仅有{len(partitions)}种唯一分区；24个“方法×CP子集”组合也只有'
    f'{len(main_partition_sigs)}种唯一分区。算法重复输出的分组不构成独立证据。', '',
    '接触重要度为原始CP尺度的簇间平方和 BCSS = Σₖ nₖ(簇均值−总均值)²；'
    '残基分数为所有相接CP的BCSS之和。主排名将每个唯一分区等权计入一次。'
    '没有计算ANOVA显著性或把这些自同一数据导出的分组视为外部验证。', '',
    '不同CP子集的分组先在共同的全部原始CP空间计算BCSS，另列仅保留该子集CP的native排名。'
    '固定相同分区时，共同空间排名一致；native排名可反映删去接触本身的影响。', '',
    '## 先前候选的对照', '',
    '| 残基 | 先前方差排名 | 唯一分区等权BCSS排名 | 3种分区前20覆盖 | 留一构建方差排名范围 | 前20覆盖 |',
    '|---|---:|---:|---:|---:|---:|',
]
for p in [74,129,28,99,23,33,32,21,108,68,66,61,70,72,102,105]:
    r = residue[residue.position.eq(p)].iloc[0]
    lines.append(f'| {r.residue} | {r.prior_variance_rank} | {r.unique_partition_equal_rank} | '
                 f'{round(r.unique_partition_top20_fraction*3)}/3 | {r.LOCO_rank_min}–{r.LOCO_rank_max} | '
                 f'{round(r.LOCO_top20_fraction*11)}/11 |')
lines += ['',
    'N74和L33的结果最一致：分别为唯一分区等权BCSS第5、12名，三种分区均在前20；'
    '保留77/154/230个CP时native排名分别为7/7/5与13/13/12。'
    'N74连接Q58、L33等识别邻域，单独限制两端均位于70–153时，这些跨边界接触会被剔除；'
    '该受限分析的N74排名为46，不能用它支持跨所有表示都稳定的结论。', '',
    'F129在共同原始CP空间的BCSS排名为56，三种主分区均未进入前20，'
    '其保留依据来自先前T31–F129局部对照。局部差异可存在于同一全局簇内部。'
    'F129的留一构建方差排名为10–38，去掉T31D时最靠后。', '',
    'R28/W99的等权BCSS排名为25/26，仅一种主分区进入前20；'
    'R28–W99接触本身为第18。保留77/154/230个CP时两残基排名分别为19/19/25和22/21/26，'
    '显示一定分组和表示依赖。去掉G27D+W130G构建时两者的方差排名均最靠后。', '',
    'N23的总方差排名保持靠前：留一构建后仍为2–7名。'
    '其等权BCSS排名为7，但仅在将G27组合单列的三类分区中进入残基前20。'
    'N23–G27接触的等权BCSS仍居第1；应区分单个强接触与按多个接触累计的残基排名。', '',
    '对766、77、154、230个CP的表示敏感性以及每个算法的具体排名详见 '
    '`hotspot_subset_comparison.csv` 和 `hotspot_pipeline_residue_ranks.csv`。', '',
    '## 边界和解释', '',
    'LOCO仅衡量当前突变面板对热点排名的影响：每次去掉一个构建，重算剩余10个构建的无监督方差。'
    '它没有预测被留出的构建，也没有评价实验泛化能力。', '',
    '高BCSS说明接触能够描述当前结构分组；方差热点和BCSS热点都受已有突变设计影响。'
    'N23–G27受G27组合变化驱动，N57附近的热点受N57W/N57A分组驱动。'
    '局部接触依据和直接催化注释应与全局BCSS排名并列解释。', '',
    '分子来源和催化角色沿用已核对的序列映射表。APOBEC1来源核心区为70–153，'
    '直接催化/锌配位残基为H70、E72、C102、C105。'
    'APOBEC3A来源部分也参与整个脱氨酶折叠。序列95位动态读取为W。', '',
    '低置信标记定义为任一构建均值Cα pLDDT <70，属于模型置信度标记，无法直接解释为实验柔性。'
    '没有生成具体氨基酸替换建议或编辑效率预测。', '',
    '参考来源：[APOBEC1 / P41238](https://www.uniprot.org/uniprotkb/P41238/entry)，'
    '[APOBEC3A / P31941](https://www.uniprot.org/uniprotkb/P31941/entry)。',
]
(OUT / 'hotspot_notes.md').write_text('\n'.join(lines) + '\n')
print(json.dumps(summary, ensure_ascii=False, indent=2))
print(candidate[['residue','prior_variance_rank','unique_partition_equal_rank','unique_partition_top20_fraction',
                 'LOCO_rank_min','LOCO_rank_max','LOCO_top20_fraction']].to_string(index=False))
