#!/usr/bin/env python3
"""Unsupervised 5D UMAP sensitivity for seed-averaged CP profiles.

Adapted to 11 constructs from K-Dense umap-learn skill. Features are contact
probabilities on a common scale; the metric is raw CP RMS, without per-contact
standardisation. Activity labels are never loaded. UMAP can distort density;
selection/evaluation also use original CP distances. All attempted outcomes,
including no-cluster/noise outcomes and warnings, are retained.
"""
import os
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS'):
    os.environ[name] = '1'

import argparse
import importlib.metadata as im
import json
from pathlib import Path
import platform
import time
import warnings

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from threadpoolctl import threadpool_limits
import umap


def canonical(labels):
    """Stable labels in input construct order; noise always -1."""
    remap = {}
    out = []
    for label in labels:
        label = int(label)
        if label < 0:
            out.append(-1)
        else:
            if label not in remap:
                remap[label] = len(remap) + 1
            out.append(remap[label])
    return np.array(out, dtype=int)


def safe_silhouette(distance, labels):
    keep = labels >= 0
    retained = labels[keep]
    k = len(set(retained))
    if not 2 <= k < len(retained):
        return None
    return float(silhouette_score(distance[np.ix_(keep, keep)], retained, metric='precomputed'))


def pair_same(labels, ai, di):
    if labels[ai] < 0 or labels[di] < 0:
        return None
    return bool(labels[ai] == labels[di])


def raw_distances(features):
    mask = np.ptp(features, axis=0) > 1e-12
    if mask.sum() == 0:
        raise ValueError('No variable CP features remain.')
    distance = squareform(pdist(features[:, mask], metric='euclidean')) / np.sqrt(mask.sum())
    np.fill_diagonal(distance, 0)
    return distance, int(mask.sum())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=str(Path(__file__).resolve().parents[2] / 'variance_cp/results/variance_features.npz'))
    parser.add_argument('--output', default=str(Path(__file__).resolve().parents[1] / 'results'))
    parser.add_argument('--bootstrap', type=int, default=100)
    parser.add_argument('--random-repeats', type=int, default=20)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    data = np.load(args.input, allow_pickle=False)
    constructs = data['constructs'].astype(str)
    x = data['construct_features']
    seed_x = data['seed_features']
    seed_groups = data['seed_groups'].astype(str)
    seed_index = [np.flatnonzero(seed_groups == c) for c in constructs]
    if not np.allclose(np.stack([seed_x[ix].mean(0) for ix in seed_index]), x, atol=1e-12, rtol=0):
        raise AssertionError('Input construct means do not equal equally weighted seed means.')
    ai, di = [int(np.flatnonzero(constructs == c)[0]) for c in ('t31a', 't31d')]
    raw_distance, n_variable = raw_distances(x)
    base_seed = 20260915
    records, candidate_records, labels_records, warning_records = [], [], [], []
    baseline, embeddings = {}, {}
    started = time.time()

    def fit(distance, variable_pairs, stage, neighbors, random_state, replicate):
        context = dict(stage=stage, n_neighbors=neighbors, random_state=random_state, replicate=replicate,
                       variable_pairs=variable_pairs)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            embedding = umap.UMAP(n_neighbors=neighbors, n_components=5, min_dist=0.0,
                                  metric='precomputed', random_state=random_state,
                                  n_jobs=1, n_epochs=500, init='spectral').fit_transform(distance.copy())
            if not np.isfinite(embedding).all():
                raise ValueError('UMAP returned nonfinite embedding.')
            embedded_distance = squareform(pdist(embedding))
            models = []
            for k in (2, 3, 4):
                labels = canonical(KMeans(n_clusters=k, n_init=30, random_state=base_seed).fit_predict(embedding))
                raw_sil = safe_silhouette(distance, labels)
                emb_sil = safe_silhouette(embedded_distance, labels)
                models.append((k, labels, raw_sil, emb_sil))
            best = max(models, key=lambda m: (m[2] if m[2] is not None else -np.inf, -m[0]))
            for k, labels, raw_sil, emb_sil in models:
                candidate_records.append({**context, 'k': k, 'silhouette_raw_CP': raw_sil,
                                          'silhouette_embedding': emb_sil, 'selected': k == best[0],
                                          'T31A_T31D_same_cluster': pair_same(labels, ai, di)})
            hlabels = canonical(HDBSCAN(min_cluster_size=2, min_samples=2, cluster_selection_method='eom',
                                        metric='euclidean', n_jobs=1).fit_predict(embedding))
        for w in caught:
            warning_records.append({**context, 'warning_category': w.category.__name__, 'warning': str(w.message)})
        for algorithm, labels in [('umap_kmeans', best[1]), ('umap_hdbscan', hlabels)]:
            if stage == 'sensitivity' and neighbors == 5 and random_state == base_seed:
                baseline[algorithm] = labels.copy()
                embeddings['baseline'] = embedding.copy()
            row = {**context, 'algorithm': algorithm, 'n_clusters': len(set(labels) - {-1}),
                   'n_noise': int((labels < 0).sum()), 'noise_fraction': float((labels < 0).mean()),
                   'silhouette_raw_CP': safe_silhouette(distance, labels),
                   'silhouette_embedding': safe_silhouette(embedded_distance, labels),
                   'T31A_T31D_same_cluster': pair_same(labels, ai, di),
                   'T31A_noise': bool(labels[ai] < 0), 'T31D_noise': bool(labels[di] < 0)}
            if algorithm in baseline:
                row['ARI_to_baseline_noise_as_category'] = float(adjusted_rand_score(baseline[algorithm], labels))
                mask = (labels >= 0) & (baseline[algorithm] >= 0)
                row['ARI_to_baseline_common_nonnoise'] = (float(adjusted_rand_score(baseline[algorithm][mask], labels[mask]))
                                                          if mask.sum() >= 2 else None)
                row['exact_baseline_partition'] = bool(row['ARI_to_baseline_noise_as_category'] > 1 - 1e-12)
            records.append(row)
            for name, label in zip(constructs, labels):
                labels_records.append({**context, 'algorithm': algorithm, 'construct': name, 'cluster': int(label)})
        return embedding

    with threadpool_limits(limits=1):
        # Baseline first, then the complete predeclared grid.
        fit(raw_distance, n_variable, 'sensitivity', 5, base_seed, 0)
        for nn in (3, 5, 8):
            for rep in range(args.random_repeats):
                if nn == 5 and rep == 0:
                    continue
                fit(raw_distance, n_variable, 'sensitivity', nn, base_seed + rep, rep)
            print(f'Finished UMAP random-state grid n_neighbors={nn}', flush=True)
        rng = np.random.default_rng(base_seed + 1000)
        for rep in range(args.bootstrap):
            bx = np.stack([seed_x[rng.choice(ix, size=len(ix), replace=True)].mean(0) for ix in seed_index])
            bd, nv = raw_distances(bx)
            fit(bd, nv, 'seed_bootstrap', 5, base_seed, rep)
            if (rep + 1) % 20 == 0:
                print(f'Finished UMAP seed bootstrap {rep + 1}/{args.bootstrap}', flush=True)

    results = pd.DataFrame(records).sort_values(['stage', 'n_neighbors', 'replicate', 'algorithm'])
    results.to_csv(output / 'umap_runs.csv', index=False)
    pd.DataFrame(candidate_records).to_csv(output / 'umap_kmeans_k_selection.csv', index=False)
    pd.DataFrame(labels_records).to_csv(output / 'umap_labels_long.csv', index=False)
    pd.DataFrame(warning_records).to_csv(output / 'umap_warnings.csv', index=False)
    bdf = pd.DataFrame(embeddings['baseline'], columns=[f'UMAP_{i}' for i in range(1, 6)])
    bdf.insert(0, 'construct', constructs)
    for algorithm in baseline:
        bdf[algorithm + '_cluster'] = baseline[algorithm]
    bdf.to_csv(output / 'umap_baseline_5D_embedding.csv', index=False)
    pd.DataFrame(raw_distance, index=constructs, columns=constructs).to_csv(output / 'umap_original_CP_RMS_distance.csv')

    summary_rows = []
    for (stage, nn, algorithm), group in results.groupby(['stage', 'n_neighbors', 'algorithm']):
        available = group['T31A_T31D_same_cluster'].dropna()
        summary_rows.append(dict(stage=stage, n_neighbors=int(nn), algorithm=algorithm, runs=len(group),
            cluster_count_distribution=json.dumps(group.n_clusters.value_counts().sort_index().to_dict()),
            mean_raw_CP_silhouette=float(group.silhouette_raw_CP.mean()),
            min_raw_CP_silhouette=float(group.silhouette_raw_CP.min()),
            max_raw_CP_silhouette=float(group.silhouette_raw_CP.max()),
            mean_embedding_silhouette=float(group.silhouette_embedding.mean()),
            mean_noise_fraction=float(group.noise_fraction.mean()),
            runs_all_noise=int((group.n_noise == len(constructs)).sum()),
            runs_fewer_than_two_clusters=int((group.n_clusters < 2).sum()),
            T31_pair_both_nonnoise_runs=len(available),
            T31_pair_same_cluster_fraction_among_both_nonnoise=float(available.astype(float).mean()) if len(available) else None,
            T31_pair_any_noise_fraction=float((group.T31A_noise | group.T31D_noise).mean()),
            mean_ARI_to_baseline_noise_as_category=float(group.ARI_to_baseline_noise_as_category.mean()),
            exact_baseline_partition_fraction=float(group.exact_baseline_partition.mean())))
    summaries = pd.DataFrame(summary_rows)
    summaries.to_csv(output / 'umap_summary.csv', index=False)
    versions = {name: im.version(name) for name in ('umap-learn','numpy','scipy','scikit-learn','numba','llvmlite','pynndescent','pandas')}
    (output / 'umap_requirements.txt').write_text(''.join(f'{name}=={version}\n' for name, version in versions.items()), encoding='utf8')
    metadata = dict(
        input=str(Path(args.input).resolve()), n_constructs=len(constructs), n_seed_jobs=len(seed_x),
        constructs=constructs.tolist(), n_nonlocal_pairs=x.shape[1], n_variable_pairs=n_variable,
        preprocessing='Equally weighted seed means; retain ptp across construct means > 1e-12; raw CP RMS distances; no per-CP z score.',
        independence_unit='construct; bootstrap resamples whole seed jobs within construct, preserving seed count and averaging five sample predictions within each seed',
        feature_selection='No activity labels loaded; variable CP mask recomputed for each seed bootstrap.',
        parameters=dict(umap_n_components=5, umap_min_dist=0, umap_n_neighbors=[3,5,8],
                        umap_n_epochs=500, umap_init='spectral', umap_metric='precomputed', umap_n_jobs=1,
                        umap_random_states=list(range(base_seed, base_seed + args.random_repeats)),
                        kmeans_k=[2,3,4], kmeans_n_init=30, kmeans_random_state=base_seed,
                        kmeans_selection='maximum silhouette in original CP distance; ties prefer lower k',
                        hdbscan_implementation='sklearn.cluster.HDBSCAN', hdbscan_min_cluster_size=2,
                        hdbscan_min_samples=2, hdbscan_cluster_selection_method='eom'),
        baseline=dict(n_neighbors=5, random_state=base_seed), seed_bootstrap=args.bootstrap,
        versions=versions, python_version=platform.python_version(),
        version_verification='pip index versions umap-learn confirmed 0.5.12; installed exact pin in independent --system-site-packages venv; global packages unchanged.',
        dependency_compatibility='Initially resolved numba 0.67.0 / llvmlite 0.49.0 produced a Bus error at numba import. Fixed independent venv to numba 0.63.1 / llvmlite 0.46.0; UMAP remains 0.5.12. Results require successful import and full actual execution.',
        caution=['11 constructs only: exploratory sensitivity, no validated biological or activity clusters.',
                 'UMAP alters geometry and density; embedding silhouette can inflate separation relative to original CP.',
                 'HDBSCAN silhouettes exclude noise, so retained sample sets can differ; n_noise is always reported.',
                 'ARI with noise treats -1 as a category; common-nonnoise ARI is separately reported.',
                 'T31 pair coincidence is a post-hoc structural descriptor; two noise assignments do not count as a shared cluster.',
                 'Seed bootstrap reflects prediction repeatability conditional on these constructs, not experimental uncertainty.'],
        runtime_seconds=time.time() - started, warning_counts=pd.Series([r['warning'] for r in warning_records]).value_counts().to_dict(),
        baseline_partitions={key:{str(c):int(l) for c,l in zip(constructs,labels)} for key, labels in baseline.items()},
        summary=summary_rows)
    def clean_json(obj):
        if isinstance(obj, dict):
            return {str(k): clean_json(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [clean_json(v) for v in obj]
        if isinstance(obj, float) and not np.isfinite(obj):
            return None
        return obj
    metadata = clean_json(metadata)
    (output / 'umap_summary.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf8')
    print(json.dumps({'runtime_seconds':metadata['runtime_seconds'], 'versions':versions, 'summary':summary_rows}, indent=2), flush=True)


if __name__ == '__main__':
    main()
