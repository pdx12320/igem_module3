"""CP clustering workflow adapted from K-Dense scikit-learn skill.
All feature selection and cluster fitting are independent of assay annotations.
"""
from pathlib import Path
import json,warnings,time,sys
import numpy as np,pandas as pd
from scipy.spatial.distance import pdist,squareform
from scipy.cluster.hierarchy import linkage,cut_tree
from sklearn.cluster import KMeans,SpectralClustering,HDBSCAN,DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score,adjusted_rand_score,calinski_harabasz_score,davies_bouldin_score
from threadpoolctl import threadpool_limits
threadpool_limits(1)
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results';OUT.mkdir(parents=True,exist_ok=True)
INPUT=ROOT/'inputs'/'variance_features.npz'
if not INPUT.exists():INPUT=ROOT.parent/'variance_cp/results/variance_features.npz'
z=np.load(INPUT);X=z['construct_features'];SX=z['seed_features'];names=z['constructs'].tolist();ii=z['feature_i'];jj=z['feature_j'];P=z['construct_plddt'];groups=[np.where(z['seed_groups']==c)[0] for c in names];F=X.shape[1];N=len(names);B=200;SEED=20260915;eps=1e-12
specs=[]
for subset in ['variable_all','variable_top10','variable_top20','variable_top30']:
    for method in ['ward','average','complete','kmeans','pca95_kmeans','spectral']:
        specs.append(dict(id=f'{subset}__{method}',subset=subset,method=method,category='main'))
for method in ['gmm_pca3','hdbscan2','hdbscan3','dbscan_q50','dbscan_q75']:
    specs.append(dict(id=f'variable_all__{method}',subset='variable_all',method=method,category='exploratory'))
for subset in ['zscore_variable','confidence70','core70_153']:
    specs.append(dict(id=f'{subset}__ward',subset=subset,method='ward',category='sensitivity'))
SIZES={'variable_top10':77,'variable_top20':154,'variable_top30':230}
# These analyses/parameters are frozen before viewing the activity table.
plan={'skills':['scikit-learn','umap-learn','statistical-analysis'],'upstream_commit':'330c8e764435a731eff571e3efdda70b363d0792','n_constructs':N,'n_seeds':len(SX),'n_models':280,'feature_unit':'raw contact probability; seed CP symmetrized upstream','aggregation':'5 samples averaged within seed, equal seeds within construct','independent_unit':'construct; seeds only computational repetitions','k_range':[2,3,4],'main_methods':['Ward','average linkage','complete linkage','KMeans','PCA95 + KMeans','spectral RBF'],'common_validation_space':'all nonlocal CP in original probability units','k_selection':'silhouette in method input space; spectral uses selected CP space, PCA KMeans uses PCA space; GMM uses BIC at fixed 3 PC; density has no chosen k','feature_selection':'sample variance over construct means, no assay labels; top counts77/154/230 fixed; re-rank per bootstrap','B':B,'seed':SEED,'bootstrap':'whole seeds resampled independently within each construct; refit features/preprocessing/model; report both reselected-k and fixed-baseline-k agreement','scale_sensitivity':'StandardScaler only in named zscore workflow','confidence_mask':'both endpoints minimum construct-mean CA pLDDT >=70; mask fixed at baseline','core_mask':'both endpoints70..153; source-derived core sensitivity, not complete domain boundary','singleton_policy':'retained and counted','density_policy':'retain all-noise/one-cluster cases; metrics exclude noise and coverage is reported','GMM':'PCA3, spherical covariance, k1..4, reg_covar=.01*mean PC variance, 30 initializations; exploratory n=11','DBSCAN':'min_samples=2; eps = q50 or q75 of nearest-other-neighbor distances; recalculated in resamples','spectral':'fully connected RBF, sigma=median nonzero pairwise distance, assign_labels=cluster_qr','adaptations':'source example k2..10 reduced to2..4, no global warning suppression, no omission of degenerate density results','specs':specs}
(OUT/'analysis_plan.json').write_text(json.dumps(plan,indent=2))

def indices(x,subset):
    mask=np.ptp(x,axis=0)>eps;v=x.var(axis=0,ddof=1);v[~mask]=0;order=np.lexsort((jj,ii,-v))
    if subset in SIZES:return order[:SIZES[subset]]
    if subset=='confidence70':mask &= (P[:,ii].min(0)>=70)&(P[:,jj].min(0)>=70)
    if subset=='core70_153':mask &= (ii>=69)&(ii<=152)&(jj>=69)&(jj<=152)
    return np.flatnonzero(mask)

def canon(lab):
    out=np.full(N,-1,dtype=int);j=0
    for c in lab:
        if c>=0 and not np.any(out[lab==c]>=0):out[lab==c]=j;j+=1
    return out

def score(a,lab,d=None):
    keep=lab>=0;ll=lab[keep];nc=len(set(ll));n=int(keep.sum());out=dict(n_clusters=nc,n_noise=N-n,coverage=n/N,singletons=sum(np.sum(ll==c)==1 for c in set(ll)),silhouette=np.nan,calinski_harabasz=np.nan,davies_bouldin=np.nan)
    if 1<nc<n:
        dd=squareform(pdist(a)) if d is None else d
        out.update(silhouette=float(silhouette_score(dd[np.ix_(keep,keep)],ll,metric='precomputed')),calinski_harabasz=float(calinski_harabasz_score(a[keep],ll)),davies_bouldin=float(davies_bouldin_score(a[keep],ll)))
    return out

def fit(spec,x,seed=SEED,forced_k=None):
    ix=indices(x,spec['subset']);a=x[:,ix];meta=dict(n_features=len(ix),pca_components=None,pca_retained_variance=None)
    if spec['subset']=='zscore_variable':
        pipe=Pipeline([('scale',StandardScaler())]);a=pipe.fit_transform(a)
    method=spec['method']
    if method in ['pca95_kmeans','gmm_pca3']:
        pipe=Pipeline([('pca',PCA(n_components=.95 if method=='pca95_kmeans' else 3,svd_solver='full'))]);a=pipe.fit_transform(a);meta.update(pca_components=a.shape[1],pca_retained_variance=float(pipe.named_steps['pca'].explained_variance_ratio_.sum()))
    d=squareform(pdist(a));scan=[];solutions={};warn=[]
    with warnings.catch_warnings(record=True) as ww:
        warnings.simplefilter('always')
        if method.startswith('hdbscan'):
            model=HDBSCAN(min_cluster_size=int(method[-1]),min_samples=2,metric='precomputed',cluster_selection_method='eom',allow_single_cluster=False);lab=canon(model.fit_predict(d.copy()));meta['membership_strength']=model.probabilities_.tolist();chosen=None
        elif method.startswith('dbscan'):
            near=np.sort(d,axis=1)[:,1];ee=float(np.quantile(near,.50 if method.endswith('50') else .75));model=DBSCAN(eps=max(ee,1e-12),min_samples=2,metric='precomputed');lab=canon(model.fit_predict(d.copy()));meta['eps']=ee;chosen=None
        else:
            ks=[forced_k] if forced_k is not None else list(range(1,5) if method=='gmm_pca3' else range(2,5))
            if method in ['ward','average','complete']:zz=linkage(squareform(d,checks=False),method=method,optimal_ordering=True)
            if method=='spectral':
                sigma=float(np.median(d[np.triu_indices(N,1)]));aff=np.exp(-d*d/(2*sigma*sigma));meta['rbf_sigma']=sigma
            for k in ks:
                extra={}
                if method in ['ward','average','complete']:ll=canon(cut_tree(zz,n_clusters=k).ravel())
                elif method in ['kmeans','pca95_kmeans']:
                    model=KMeans(n_clusters=k,random_state=seed,n_init=30,max_iter=1000);ll=canon(model.fit_predict(a));extra['inertia']=float(model.inertia_)
                elif method=='spectral':
                    ll=canon(SpectralClustering(n_clusters=k,affinity='precomputed',assign_labels='cluster_qr',random_state=seed).fit_predict(aff))
                elif method=='gmm_pca3':
                    reg=max(.01*float(a.var(0).mean()),1e-8);model=GaussianMixture(n_components=k,covariance_type='spherical',reg_covar=reg,n_init=30,max_iter=1000,random_state=seed);ll=canon(model.fit_predict(a));extra.update(bic=float(model.bic(a)),aic=float(model.aic(a)),reg_covar=reg,converged=bool(model.converged_),min_posterior_confidence=float(model.predict_proba(a).max(1).min()))
                row=dict(k=k,**score(a,ll,d),**extra);scan.append(row);solutions[k]=ll
            chosen=min(scan,key=lambda r:(r['bic'],r['k']))['k'] if method=='gmm_pca3' else max(scan,key=lambda r:(r['silhouette'] if np.isfinite(r['silhouette']) else -2,-r['k']))['k'];lab=solutions[chosen]
        warn=[str(w.message) for w in ww]
    common=x[:,np.ptp(x,axis=0)>eps];com=score(common,lab);native=score(a,lab,d)
    meta.update(chosen_k=chosen,**{f'common_{k}':v for k,v in com.items()},**{f'native_{k}':v for k,v in native.items()},warnings=warn,cluster_sizes=sorted([int(np.sum(lab==c)) for c in set(lab) if c>=0],reverse=True))
    return lab,meta,scan,ix,a

base={};records=[];scans=[];labs=[];arrays={};warnrows=[]
for spec in specs:
    lab,m,scan,ix,a=fit(spec,X);base[spec['id']]=dict(labels=lab,meta=m);arrays[spec['id']+'__features']=ix
    if a.shape[1]<=10:arrays[spec['id']+'__embedding']=a
    for q in scan:scans.append(dict(pipeline=spec['id'],**q))
    records.append(dict(pipeline=spec['id'],**spec,**m))
    for i,c in enumerate(names):labs.append(dict(pipeline=spec['id'],construct=c,cluster=int(lab[i])))
    for w in m['warnings']:warnrows.append(dict(stage='baseline',pipeline=spec['id'],warning=w))
pd.DataFrame(records).drop(columns=['id']).to_csv(OUT/'pipeline_baseline.csv',index=False);pd.DataFrame(labs).to_csv(OUT/'pipeline_labels.csv',index=False);pd.DataFrame(scans).to_csv(OUT/'pipeline_k_scan.csv',index=False);np.savez_compressed(OUT/'pipeline_baseline_arrays.npz',**arrays)
print('Baseline complete:',len(specs),'pipelines',flush=True)
# Persist baseline before resampling so independent interpretation can start.
boot=[];coc={s['id']:np.zeros((N,N)) for s in specs};rng=np.random.default_rng(SEED);start=time.time()
for b in range(B):
    xb=np.stack([SX[rng.choice(g,size=len(g),replace=True)].mean(0) for g in groups])
    for spec in specs:
        pid=spec['id'];lab,m,scan,ix,a=fit(spec,xb);bl=base[pid]['labels'];k=base[pid]['meta']['chosen_k']
        if k is not None:
            if m['chosen_k']==k:fl=lab
            else:fl=fit(spec,xb,forced_k=k)[0]
        else:fl=lab
        ari=adjusted_rand_score(bl,lab);fixed=adjusted_rand_score(bl,fl)
        coc[pid]+=(lab[:,None]==lab[None,:])&(lab[:,None]>=0)&(lab[None,:]>=0)
        boot.append(dict(replicate=b,pipeline=pid,selected_k=m['chosen_k'],n_clusters=m['common_n_clusters'],n_noise=m['common_n_noise'],ARI_reselected=float(ari),exact_reselected=int(ari==1),ARI_fixed_k=float(fixed),exact_fixed_k=int(fixed==1),T31_same_cluster=bool(lab[names.index('t31a')]==lab[names.index('t31d')] and lab[names.index('t31a')]>=0),labels=json.dumps(lab.tolist())))
        for w in m['warnings']:warnrows.append(dict(stage=f'bootstrap{b}',pipeline=pid,warning=w))
    if (b+1)%25==0:print('Bootstrap',b+1,'/',B,'elapsed',round(time.time()-start,1),flush=True)
br=pd.DataFrame(boot);br.to_csv(OUT/'pipeline_seed_bootstrap.csv',index=False)
summary=pd.DataFrame(records).drop(columns=['id'])
for row,r in summary.iterrows():
    bs=br[br.pipeline==r.pipeline];summary.loc[row,'bootstrap_exact_reselected']=bs.exact_reselected.mean();summary.loc[row,'bootstrap_mean_ARI_reselected']=bs.ARI_reselected.mean();summary.loc[row,'bootstrap_exact_fixed_k']=bs.exact_fixed_k.mean();summary.loc[row,'bootstrap_mean_ARI_fixed_k']=bs.ARI_fixed_k.mean();summary.loc[row,'bootstrap_T31_same_cluster']=bs.T31_same_cluster.mean();summary.loc[row,'bootstrap_k_counts']=json.dumps({str(int(k)):int(v) for k,v in bs.n_clusters.value_counts().sort_index().items()});summary.loc[row,'bootstrap_mean_noise']=bs.n_noise.mean()
summary.to_csv(OUT/'pipeline_summary.csv',index=False)
np.savez_compressed(OUT/'pipeline_coclustering.npz',constructs=np.array(names),**{k:v/B for k,v in coc.items()})
pd.DataFrame(warnrows,columns=['stage','pipeline','warning']).to_csv(OUT/'warnings.csv',index=False)
(OUT/'baseline_details.json').write_text(json.dumps({k:dict(labels=v['labels'].tolist(),meta=v['meta']) for k,v in base.items()},indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)))
print(summary[['pipeline','chosen_k','common_n_noise','common_silhouette','bootstrap_exact_reselected','bootstrap_exact_fixed_k']].to_string(index=False),flush=True)
