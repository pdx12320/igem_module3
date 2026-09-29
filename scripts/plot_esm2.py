"""ORCA-styled display of the frozen primary embedding distance matrix."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args()
if a.output.exists():raise FileExistsError(a.output)
a.output.mkdir(parents=True)
r=ROOT/'analysis/esm2/results';d=pd.read_csv(r/'layer12_distances.csv',index_col=0)
labels=pd.read_csv(r/'labels.csv').set_index('construct').loc[d.index,'observed_name'].tolist()
plt.rcParams.update({'font.family':['Futura','Arial','DejaVu Sans'],'svg.fonttype':'none','font.size':18,'text.color':'#171536','axes.labelcolor':'#171536','xtick.color':'#171536','ytick.color':'#171536'})
fig,ax=plt.subplots(figsize=(12,8.5));fig.subplots_adjust(left=.37,right=.81,bottom=.13,top=.97)
im=ax.imshow(d.to_numpy(),vmin=0,vmax=d.to_numpy().max(),interpolation='none',cmap=LinearSegmentedColormap.from_list('orca',['#FFFFFF','#9D9CF4','#2E267C']))
ax.set_yticks(range(11),[f'{i+1:02}  {s}' for i,s in enumerate(labels)])
ax.set_xticks(range(11),[f'{i+1:02}' for i in range(11)]);ax.tick_params(length=0,pad=10)
ax.set_xlabel('Construct (same order as rows)',labelpad=15)
for s in ax.spines.values():s.set_visible(False)
cax=fig.add_axes([.84,.25,.018,.50]);cb=fig.colorbar(im,cax=cax);cb.set_label('Cosine distance',labelpad=10,fontsize=16);cb.ax.tick_params(labelsize=13)
for ext in ['png','svg']:fig.savefig(a.output/f'esm2_distances.{ext}',dpi=240,facecolor='white')
(a.output/'caption.md').write_text('**ESM-2 primary representation.** Cosine distances compare mean layer-12 embeddings for 11 constructs in fixed source order. These sequence similarities do not establish editing-function prediction.\n')
(a.output/'alt-text.txt').write_text('Symmetric eleven-by-eleven ESM-2 cosine-distance matrix. E72A is relatively distant from the other constructs; T31A and T31D are not assigned separate clusters by the predeclared primary analysis. White is zero and indigo indicates larger distance.\n')
(a.output/'manifest.json').write_text(json.dumps({'source':'analysis/esm2/results/layer12_distances.csv','shape':list(d.shape),'vmin':0,'vmax':float(d.to_numpy().max()),'ordering':'original source order','interpolation':'none','matplotlib':matplotlib.__version__},indent=2)+'\n')
