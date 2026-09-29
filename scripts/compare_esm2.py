"""Execute analysis/esm2/PLAN.md with local weights and no network access."""
from pathlib import Path
import argparse, hashlib, importlib.metadata, json, os, platform, re
os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ.setdefault('HF_HOME',str(Path(__file__).resolve().parents[1]/'work/hf-cache'))
import numpy as np
import pandas as pd
import torch
from transformers import EsmModel, EsmTokenizer
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.decomposition import PCA
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def cluster(d,k): return AgglomerativeClustering(n_clusters=k,metric='precomputed',linkage='average').fit_predict(d)

def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    torch.set_num_threads(2);torch.set_num_interop_threads(1);threadpool_limits(2)
    torch.manual_seed(20260929);np.random.seed(20260929)
    cp=ROOT/'analysis/cp-clustering'; manifest=cp/'variance_cp/results/manifest_with_cluster_comparison.csv'
    wtfile=cp/'variance_cp/annotation/uploaded_wt.fasta';wt=''.join(l.strip() for l in wtfile.read_text().splitlines() if not l.startswith('>'))
    meta=pd.read_csv(manifest);names=meta.construct.tolist(); seqs=[]
    for r in meta.itertuples():
        seq=list(wt)
        if r.actual_mutations!='WT':
            for mutation in r.actual_mutations.split(';'):
                old,pos,new=re.fullmatch(r'([A-Z])(\d+)([A-Z])',mutation).groups();pos=int(pos)-1
                assert seq[pos]==old,(r.construct,mutation)
                seq[pos]=new
        seqs.append(''.join(seq))
    assert len(set(seqs))==11 and all(len(s)==199 for s in seqs)
    tokenizer=EsmTokenizer.from_pretrained(a.model,local_files_only=True)
    model=EsmModel.from_pretrained(a.model,local_files_only=True,add_pooling_layer=False).float().eval()
    embeddings={6:[],12:[]}
    with torch.inference_mode():
        for name,seq in zip(names,seqs):
            encoded=tokenizer(seq,return_tensors='pt',return_special_tokens_mask=True)
            residue=(encoded.pop('special_tokens_mask')==0)&encoded['attention_mask'].bool()
            assert int(residue.sum())==199
            result=model(**encoded,output_hidden_states=True)
            for layer in embeddings: embeddings[layer].append(result.hidden_states[layer][residue].mean(0).cpu().numpy())
            print('embedded',name,flush=True)
    emb={f'layer{k}':np.stack(v) for k,v in embeddings.items()}
    source_labels=pd.read_csv(cp/'skill_clustering/results/pipeline_labels.csv')
    frozen=source_labels[source_labels.pipeline=='variable_top10__spectral'].set_index('construct').loc[names,'cluster'].to_numpy(int)
    dists={k:squareform(pdist(v,metric='cosine')) for k,v in emb.items()}
    dists['sequence_hamming']=squareform(pdist(np.array([list(s.encode('ascii')) for s in seqs]),metric='hamming'))
    a.output.mkdir(parents=True)
    rows=[];scans=[];loco=[];labs={}
    for label,d in dists.items():
        d=np.maximum(d,0);np.fill_diagonal(d,0)
        assert np.isfinite(d).all() and np.allclose(d,d.T)
        candidates=[]
        for k in [2,3,4]:
            c=cluster(d,k);sil=silhouette_score(d,c,metric='precomputed');candidates.append((sil,k,c))
            scans.append({'representation':label,'k':k,'full_space_silhouette':sil,'cluster_sizes':json.dumps(np.bincount(c).tolist())})
        sil,k,c=max(candidates,key=lambda z:(z[0],-z[1]));labs[label]=c
        aris=[]
        for omit,name in enumerate(names):
            keep=np.arange(len(names))!=omit;sub=cluster(d[np.ix_(keep,keep)],k)
            ari=adjusted_rand_score(c[keep],sub);aris.append(ari)
            loco.append({'representation':label,'omitted':name,'fixed_k':k,'ARI_to_restricted_baseline':ari})
        rows.append({'representation':label,'selected_k':k,'full_space_silhouette':sil,
                     'cluster_sizes':json.dumps(np.bincount(c).tolist()),'singletons':int((np.bincount(c)==1).sum()),
                     'ARI_to_CP_spectral':adjusted_rand_score(frozen,c),
                     'T31A_T31D_same_cluster':bool(c[names.index('t31a')]==c[names.index('t31d')]),
                     'LOCO_mean_ARI':float(np.mean(aris)),'LOCO_min_ARI':min(aris),
                     'LOCO_exact_count':int(np.isclose(aris,1).sum()),'LOCO_runs':11})
        pd.DataFrame(d,index=names,columns=names).to_csv(a.output/f'{label}_distances.csv')
    pd.DataFrame(rows).to_csv(a.output/'summary.csv',index=False)
    pd.DataFrame(scans).to_csv(a.output/'k_scan.csv',index=False)
    pd.DataFrame(loco).to_csv(a.output/'leave_one_out.csv',index=False)
    labtable=pd.DataFrame({'construct':names,'observed_name':meta.observed_display_name,'CP_spectral':frozen,**labs})
    labtable.to_csv(a.output/'labels.csv',index=False)
    pca=PCA(n_components=2).fit(emb['layer12']);xy=pca.transform(emb['layer12'])
    pd.DataFrame({'construct':names,'PC1':xy[:,0],'PC2':xy[:,1]}).to_csv(a.output/'pca_display.csv',index=False)
    np.savez_compressed(a.output/'embeddings.npz',constructs=np.array(names),**emb)
    (a.output/'sequences.fasta').write_text(''.join(f'>{n}\n{s}\n' for n,s in zip(names,seqs)))
    versions={x:importlib.metadata.version(x) for x in ['torch','transformers','tokenizers','safetensors','numpy','pandas','scipy','scikit-learn']}
    provenance={'model':'facebook/esm2_t12_35M_UR50D','device':'CPU','threads':2,'python':platform.python_version(),
                'versions':versions,'input_sha256':{'manifest':sha(manifest),'wt_fasta':sha(wtfile),'plan':sha(ROOT/'analysis/esm2/PLAN.md')},
                'model_sha256':{p.name:sha(p) for p in a.model.iterdir() if p.is_file() and p.name in ['config.json','model.safetensors','vocab.txt','tokenizer_config.json']},
                'pooling':'mean of 199 residue embeddings; special tokens excluded','layers':[6,12],
                'network':'disabled during inference','activity_labels_used_for_fitting':False,
                'PCA_display_explained_variance':pca.explained_variance_ratio_.tolist(),
                'primary_vs_layer6_ARI':adjusted_rand_score(labs['layer12'],labs['layer6']),
                'primary_vs_sequence_hamming_ARI':adjusted_rand_score(labs['layer12'],labs['sequence_hamming']),
                'limitations':['11 near-identical engineered sequences','no held-out functional validation','LOCO sensitivity is not experimental replication']}
    (a.output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(pd.DataFrame(rows).to_string(index=False))

if __name__=='__main__':main()
