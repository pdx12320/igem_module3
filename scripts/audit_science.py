"""Audit frozen figure inputs and CP clustering without changing scientific settings.

Run from the repository: python scripts/audit_science.py --output work/science-audit.json
Existing output files are never overwritten. No AF3 inference or wet-lab reanalysis.
"""
from pathlib import Path
import argparse, csv, hashlib, json, platform
import numpy as np
import pandas as pd
import scipy
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import SpectralClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score
import sklearn
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    threadpool_limits(1)
    report = {'scope': 'Independent numerical audit of supplied summaries; not experimental validation',
              'versions': {'python': platform.python_version(), 'numpy': np.__version__,
                           'pandas': pd.__version__, 'scipy': scipy.__version__, 'sklearn': sklearn.__version__},
              'checks': {}, 'input_hashes': {}}
    def read(p):
        report['input_hashes'][str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
        return pd.read_csv(p)
    check = report['checks']
    d = ROOT / 'data/plot-tables'
    single = read(d / 'figure_08_single_site.csv')
    mutants = single[~single.is_parent]
    valid = mutants[mutants.plus1_ratio_defined]
    assert len(mutants) == 102 and len(valid) == 101
    high = valid[valid.activity_retention_vs_same_batch_parent >= .70]
    best = high.loc[high.plus1_ratio_GCG_over_GCA.idxmax()]
    assert best.mutant == '30H' and np.isclose(best.plus1_ratio_GCG_over_GCA, 1.71)
    assert not ((valid.plus1_ratio_GCG_over_GCA >= 2) & (valid.activity_retention_vs_same_batch_parent >= .7)).any()
    check['single_mutants'] = {'total': 102, 'defined': 101, 'best_at_retention_0_70': 'K30H', 'ratio': 1.71, 'retention': .84}
    matrix = read(d / 'figure_03_ddcp_matrix.csv')
    full = read(d / 'figure_03_all_residues_ddcp.csv')
    # Input matrix schemas contain two residue annotation columns.
    numeric = full.iloc[:, 2:].to_numpy(float)
    top = np.argsort(-np.nanmax(np.abs(numeric), axis=1))[:22]
    assert set(matrix.iloc[:, 0]) == set(full.iloc[top, 0])
    assert np.isclose(np.nanmax(np.abs(numeric)), .395)
    check['ddcp'] = {'all_residues': len(full), 'displayed_residues': len(matrix), 'constructs': numeric.shape[1], 'symmetric_limit': .395}
    targeting = read(d / 'figure_09_targeting_ratio.csv')
    v = targeting[(~targeting.is_wildtype_parent) & targeting.targeting_ratio_defined]
    assert len(v) == 41
    pearson = v.targeting_ratio.corr(v.sum_nonGCG_editing_pct)
    spearman = v.targeting_ratio.corr(v.sum_nonGCG_editing_pct, method='spearman')
    assert np.isclose(pearson, -.390128, atol=1e-6) and np.isclose(spearman, -.557017, atol=1e-6)
    check['targeting_ratio'] = {'defined_mutants': len(v), 'pearson': pearson, 'spearman': spearman, 'interpretation': 'descriptive; ratio and denominator are mathematically coupled'}
    candidates = read(d / 'figure_10a_candidate_groups_raw.csv')
    assert candidates.groupby('group').size().to_dict() == {'A':18,'B':6,'C':12,'D':5,'E':20}
    check['candidate_entries'] = 61
    nroot = ROOT / 'figure-sources/orca-n1-n4/input/data'
    combo = read(nroot / 'combo_batch_ratio_vs_retention.csv')
    # The source uses undetected/zero c.871 to flag undefined ratios.
    ratio = 'on_target_GCG_over_offtarget_GCA_ratio'; ret = 'activity_retention_fraction'
    valid_combo = combo[combo[ratio].notna()]
    assert len(combo) == 48 and len(valid_combo) == 36
    hits = valid_combo[(valid_combo[ratio] >= 2) & (valid_combo[ret] >= .7)]
    assert hits.construct.tolist() == ['27T-30H-58M']
    a = valid_combo[[ret,ratio]].to_numpy(float)
    pareto = np.array([not np.any(np.all(a >= p, axis=1) & np.any(a > p, axis=1)) for p in a])
    assert int(pareto.sum()) == 6
    check['combinatorial'] = {'records':48,'defined':36,'pareto':6,'threshold_hit':hits[['construct',ratio,ret]].to_dict('records')}
    designed = read(nroot / 'designed_batch_groups.csv')
    usable = designed[designed.ratio_defined & ~designed.excluded_failed_well]
    assert len(designed) == 37 and len(usable) == 35
    check['designed_batch'] = {'records':37,'usable':35,'failed_well_policy':'inherited from source; lab-level failure has not been independently established'}
    cp = ROOT / 'analysis/cp-clustering'
    zpath = cp / 'variance_cp/results/variance_features.npz'
    report['input_hashes'][str(zpath.relative_to(ROOT))] = hashlib.sha256(zpath.read_bytes()).hexdigest()
    z = np.load(zpath, allow_pickle=False)
    x, sx, names = z['construct_features'], z['seed_features'], z['constructs'].tolist()
    assert x.shape == (11,19110) and sx.shape == (56,19110)
    assert np.isfinite(x).all() and np.all((x >= 0) & (x <= 1))
    for i,name in enumerate(names):
        assert np.allclose(x[i], sx[z['seed_groups'] == name].mean(0), rtol=1e-6, atol=1e-8)
    assert int((np.ptp(x,axis=0) > 1e-12).sum()) == 766
    summary = read(cp / 'skill_clustering/results/pipeline_summary.csv')
    labels = read(cp / 'skill_clustering/results/pipeline_labels.csv')
    boot = read(cp / 'skill_clustering/results/pipeline_seed_bootstrap.csv')
    assert len(summary) == 32 and len(boot) == 6400
    max_sil_error = 0.0
    for row in summary.itertuples():
        lab = labels[labels.pipeline == row.pipeline].set_index('construct').loc[names, 'cluster'].to_numpy(int)
        mask = lab >= 0
        if 1 < len(set(lab[mask])) < mask.sum():
            score = silhouette_score(x[mask], lab[mask])
            max_sil_error = max(max_sil_error, abs(score - row.common_silhouette))
        b = boot[boot.pipeline == row.pipeline]
        assert len(b) == 200
        assert np.isclose(b.exact_reselected.mean(), row.bootstrap_exact_reselected)
        assert np.isclose(b.exact_fixed_k.mean(), row.bootstrap_exact_fixed_k)
        for r in b.itertuples():
            bl = np.array(json.loads(r.labels))
            assert np.isclose(adjusted_rand_score(lab, bl), r.ARI_reselected)
    assert max_sil_error < 1e-5
    # Independently refit the source-selected spectral baseline. No parameter search is added.
    v = x.var(0,ddof=1); v[np.ptp(x,axis=0) <= 1e-12] = 0
    ix = np.lexsort((z['feature_j'],z['feature_i'],-v))[:77]
    a = x[:,ix]; dist = squareform(pdist(a)); sigma = np.median(dist[np.triu_indices(11,1)])
    affinity = np.exp(-dist**2/(2*sigma**2))
    scan = []
    for k in [2,3,4]:
        lab = SpectralClustering(n_clusters=k, affinity='precomputed', assign_labels='cluster_qr', random_state=20260915).fit_predict(affinity)
        scan.append((silhouette_score(a,lab),k,lab))
    best = max(scan,key=lambda q:(q[0],-q[1]))
    frozen = labels[labels.pipeline == 'variable_top10__spectral'].set_index('construct').loc[names,'cluster'].to_numpy(int)
    assert best[1] == 3 and adjusted_rand_score(best[2],frozen) == 1
    assert frozen[names.index('t31a')] == frozen[names.index('t31d')]
    check['cp_clustering'] = {'constructs':11,'seeds':56,'features':19110,'variable_features':766,
        'audited_baselines':32,'audited_stored_bootstrap_partitions':6400,'max_common_silhouette_error':max_sil_error,
        'spectral_baseline_refit_ARI':1.0,'selected_k':3,'T31A_T31D_same_cluster':True,
        'not_rerun':'AF3 inference, 6400 bootstrap fits and UMAP embeddings; stored records audited instead'}
    report['status'] = 'passed'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(check,indent=2,ensure_ascii=False))


if __name__ == '__main__':
    main()
