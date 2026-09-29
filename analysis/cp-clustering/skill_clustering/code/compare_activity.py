"""Post-hoc annotation of frozen clusters; never feeds labels back into fitting."""
from pathlib import Path
import json
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';OLD=ROOT.parent/'variance_cp/results'
a=pd.read_csv(OLD/'manifest_with_cluster_comparison.csv');l=pd.read_csv(R/'pipeline_labels.csv');um=json.loads((R/'umap_summary.json').read_text())
extra=[]
for method,labels in um['baseline_partitions'].items():
 for c,k in labels.items():extra.append(dict(pipeline=method,construct=c,cluster=k-1 if k>=0 else -1))
l=pd.concat([l,pd.DataFrame(extra)],ignore_index=True);l.to_csv(R/'all_pipeline_labels.csv',index=False)
usecols=['construct','manifest_construct','observed_display_name','sequence_matches_manifest','mapping_status','observed_seed_count','requested_seed_count','wet_activity_raw','wet_activity_value','wet_activity_missing','eligible_for_activity_comparison','activity_exclusion_reason']
out=a[usecols].merge(l.pivot(index='construct',columns='pipeline',values='cluster'),on='construct',validate='one_to_one');out.to_csv(R/'construct_activity_and_all_clusters.csv',index=False)
rows=[];composition=[]
for pid,ls in l.groupby('pipeline',sort=False):
 merged=ls.merge(a[usecols],on='construct',validate='one_to_one');by=merged.set_index('construct');la=int(by.loc['t31a','cluster']);ld=int(by.loc['t31d','cluster']);pair='同簇' if la==ld and la>=0 else '不同簇' if la>=0 and ld>=0 else '至少一个为噪声/未分组'
 rows.append(dict(pipeline=pid,T31A_cluster=la,T31D_cluster=ld,T31_pair_state=pair,T31A_activity=.970,T31D_activity=.000,clean_activity_labels=int(merged.eligible_for_activity_comparison.sum()),clean_nonnoise_activity_labels=int((merged.eligible_for_activity_comparison & (merged.cluster>=0)).sum())))
 for cluster,g in merged.groupby('cluster'):
  eligible=g[g.eligible_for_activity_comparison]
  composition.append(dict(pipeline=pid,cluster=cluster,is_noise=cluster<0,constructs=';'.join(g.observed_display_name),clean_activity_values=';'.join(f'{r.observed_display_name}:{r.wet_activity_value:.3f}' for _,r in eligible.iterrows()),missing_or_mismatched_n=len(g)-len(eligible),caution='noise entries do not constitute a biological cluster' if cluster<0 else 'post-hoc descriptive comparison only'))
r=pd.DataFrame(rows);r.to_csv(R/'T31_activity_pair_across_pipelines.csv',index=False);pd.DataFrame(composition).to_csv(R/'activity_cluster_composition.csv',index=False)
summary={'n_baseline_pipelines':len(r),'T31_pair_states':r.T31_pair_state.value_counts().to_dict(),'clean_activity_constructs':a.loc[a.eligible_for_activity_comparison,'construct'].tolist(),'missing_activity_constructs':a.loc[a.wet_activity_missing,'construct'].tolist(),'mismatched_constructs':a.loc[~a.sequence_matches_manifest,'construct'].tolist(),'activity_units':'unspecified; values preserved, not converted to percentages','no_C_specific_labels':True,'analysis_freeze':'Clustering and hotspot ranking were complete before this file reads activity values'}
(R/'activity_comparison_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False));print(summary)
