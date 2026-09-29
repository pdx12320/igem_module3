"""Chinese figures for unsupervised CP workflow comparisons.
Reads immutable analysis outputs. No fitting, parameter selection or numeric edits.
General report figures, not a journal-specific submission.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from fontTools.ttLib import TTFont

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results'; O=ROOT/'figures'; O.mkdir(parents=True,exist_ok=True)
FONT=Path('/root/.local/share/fonts/NotoSansCJKsc-Regular.otf')
if not FONT.exists(): FONT=Path('/root/.local/share/fonts/NotoSerifCJKsc-Regular.otf')
fm.fontManager.addfont(str(FONT)); FNAME=fm.FontProperties(fname=str(FONT)).get_name()
plt.rcParams.update({'font.family':FNAME,'font.size':10,'axes.titlesize':12,
    'axes.labelsize':10,'axes.spines.top':False,'axes.spines.right':False,
    'axes.unicode_minus':False,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'path',
    'savefig.facecolor':'white','figure.facecolor':'white','axes.facecolor':'white'})
S=pd.read_csv(R/'pipeline_summary.csv').set_index('pipeline')
L=pd.read_csv(R/'pipeline_labels.csv').pivot(index='pipeline',columns='construct',values='cluster')
B=np.load(R/'pipeline_coclustering.npz')
NAMES=['wt','k30h','m132d','m132e','e72a','t31a','t31d','g27dm130g','g27tk30hq58m','n57a','n57w']
DISPLAY={'wt':'WT','k30h':'K30H','m132d':'M132D','m132e':'M132E','e72a':'E72A','t31a':'T31A','t31d':'T31D','g27dm130g':'G27D+W130G*','g27tk30hq58m':'G27T+K30H+Q58M','n57a':'N57A','n57w':'N57W'}
METHOD={'ward':'Ward','average':'平均连接','complete':'完全连接','kmeans':'K-means','pca95_kmeans':'PCA 95% + K-means','spectral':'谱聚类','gmm_pca3':'PCA 3 + GMM','hdbscan2':'HDBSCAN (最小簇 2)','hdbscan3':'HDBSCAN (最小簇 3)','dbscan_q50':'DBSCAN (q50)','dbscan_q75':'DBSCAN (q75)'}
MAIN=['ward','average','complete','kmeans','pca95_kmeans','spectral']
BLUE='#246A9A'; ORANGE='#B46A19'; GREEN='#347565'; GREY='#64748B'; INK='#18334B'
manifest=[]

def desc(pid):
 row=S.loc[pid]; m=METHOD.get(row.method,row.method)
 if pid=='variable_top10__spectral': return '前 77 对 CP · 谱聚类'
 if row.subset=='zscore_variable':return '标准化 CP · Ward'
 if row.subset=='confidence70':return '高置信接触 · Ward'
 if row.subset=='core70_153':return '70–153 内部接触 · Ward'
 return m

def check_fonts(fig):
 cm=TTFont(FONT).getBestCmap()
 chars=set(''.join(t.get_text() for t in fig.findobj(matplotlib.text.Text)))
 missing=sorted(c for c in chars if not c.isspace() and ord(c) not in cm)
 if missing:raise RuntimeError('Missing font glyphs: '+''.join(missing))

def save(fig,name,alt,notes,sources):
 fig.canvas.draw();check_fonts(fig)
 files=[]
 for ext in ['png','pdf','svg']:
  p=O/f'{name}.{ext}';fig.savefig(p,dpi=300,facecolor='white',bbox_inches=None);files.append(str(p.relative_to(ROOT)))
 manifest.append(dict(figure=name,files=files,width_inches=fig.get_figwidth(),height_inches=fig.get_figheight(),dpi_png=300,font=FNAME,svg_text='paths',alt_text=alt,caption=notes,source_data=sources))
 plt.close(fig)

def grid(ax,nr,nc):
 ax.set_xticks(np.arange(nc)-.5,minor=True);ax.set_yticks(np.arange(nr)-.5,minor=True)
 ax.grid(which='minor',color='white',lw=.85);ax.tick_params(which='minor',bottom=False,left=False)

# 1. Every declared workflow is retained, including the all-noise result.
pids=S.index.tolist(); mat=L.loc[pids,NAMES].to_numpy(); n=len(pids)
fig=plt.figure(figsize=(16,14.2))
ax=fig.add_axes([.258,.18,.536,.69]); metric=fig.add_axes([.816,.18,.16,.69],sharey=ax)
cmap=ListedColormap(['#E8EAEE','#D6E6F2','#F4D5B6','#D0E6DE','#DCCFEA'])
norm=BoundaryNorm([-1.5,-.5,.5,1.5,2.5,3.5],cmap.N)
ax.imshow(mat,cmap=cmap,norm=norm,aspect='auto',interpolation='nearest')
for i in range(n):
 for j in range(len(NAMES)):
  v=int(mat[i,j]);ax.text(j,i,'−1' if v<0 else str(v+1),ha='center',va='center',fontsize=10,color='#273444')
ax.set_xticks(range(len(NAMES)),[DISPLAY[c] for c in NAMES],rotation=52,ha='right',rotation_mode='anchor',fontsize=10)
labels=[]
for pid in pids:
 row=S.loc[pid]
 prefix={'variable_all':'全部可变','variable_top10':'前 10%','variable_top20':'前 20%','variable_top30':'前 30%','zscore_variable':'','confidence70':'','core70_153':''}[row.subset]
 labels.append((prefix+' · ' if prefix else '')+(METHOD[row.method] if pid=='variable_top10__spectral' else desc(pid)))
ax.set_yticks(range(n),labels,fontsize=10);ax.tick_params(axis='both',length=0,pad=7)
grid(ax,n,len(NAMES))
metric.set_xlim(0,3);metric.set_ylim(ax.get_ylim());metric.axis('off')
for x,t in zip([.35,1.4,2.52],['CP 对数','原 CP\n轮廓系数','覆盖率']):metric.text(x,-1.05,t,ha='center',va='bottom',fontsize=10,color=INK)
for i,pid in enumerate(pids):
 row=S.loc[pid];score=row.common_silhouette;noise=int(row.common_n_noise)
 metric.text(.35,i,str(int(row.n_features)),ha='center',va='center',fontsize=10)
 metric.text(1.4,i,'缺失' if np.isnan(score) else f'{score:.3f}'+('†' if noise else ''),ha='center',va='center',fontsize=10,color=ORANGE if noise else INK)
 metric.text(2.52,i,f'{int(round(row.common_coverage*11))}/11',ha='center',va='center',fontsize=10,color=ORANGE if noise else INK)
for k in [5.5,11.5,17.5,23.5,28.5]:
 ax.axhline(k,color='#7E8D99',lw=1.4);metric.axhline(k,color='#7E8D99',lw=1.4)
for j in [NAMES.index('t31a'),NAMES.index('t31d')]:
 ax.add_patch(Rectangle((j-.5,-.5),1,n,fill=False,edgecolor='#3D4F5A',lw=1.2))
fig.text(.03,.965,'32 条无监督流程：构建分组与覆盖范围',fontsize=20,color=INK)
fig.text(.03,.931,'11 个构建；56 个 seed；每个 seed 内 5 个结构先平均，再按构建平均。活性标签不参与 CP 筛选、参数选择与聚类拟合。',fontsize=11,color=GREY)
fig.text(.03,.082,'数字 1–4 是每一行内部的簇编号，跨行同号不保证同一分组；−1 表示噪声，两个噪声点不构成同簇。',fontsize=11)
fig.text(.03,.055,'† 轮廓系数仅在非噪声构建上计算，应结合覆盖率读取。黑框标出 T31A 与 T31D；全噪声流程仍完整保留。',fontsize=11)
fig.text(.03,.028,'* 上传目录名为 G27DM130G，当前序列为 G27D+W130G；图按当前序列标注。',fontsize=10,color=GREY)
save(fig,'pipeline_membership_matrix','32 条流程的 11 个构建簇标签矩阵，显示 T31A 与 T31D 始终同簇或同时被视为噪声；密度聚类覆盖率下降。',
 '各行独立编号；所有原 CP 指标采用共同原始接触概率空间。噪声不计入轮廓系数，覆盖率保留其影响。', ['results/pipeline_labels.csv','results/pipeline_summary.csv'])

# 2. Parallel metrics, shown in declared method order (no performance ranking).
sel=[f'variable_all__{m}' for m in MAIN]+['variable_top10__spectral']+[f'variable_all__{m}' for m in ['gmm_pca3','hdbscan2','hdbscan3','dbscan_q50','dbscan_q75']]+['confidence70__ward','core70_153__ward']
a=S.loc[sel]; y=np.arange(len(sel))
fig=plt.figure(figsize=(15.8,9.1));gs=fig.add_gridspec(1,3,left=.255,right=.972,bottom=.24,top=.79,width_ratios=[1,1.03,.75],wspace=.20)
axs=[fig.add_subplot(gs[0,i]) for i in range(3)]
for ax2 in axs:
 ax2.set_ylim(len(sel)-.45,-.75);ax2.set_yticks(y);ax2.tick_params(axis='y',length=0)
 ax2.spines['left'].set_visible(False);ax2.spines['bottom'].set_color('#A6B2BD')
 ax2.set_axisbelow(True);ax2.grid(axis='x',color='#DDE3E8',lw=.7)
 for k in [5.5,6.5,7.5,11.5]:ax2.axhline(k,color='#C5CED6',lw=.7)
axs[0].set_yticklabels([desc(p) for p in sel],fontsize=10.5)
axs[1].set_yticklabels([]);axs[2].set_yticklabels([])
for i,(pid,row) in enumerate(a.iterrows()):
 noise=row.common_n_noise>0; col=ORANGE if noise else BLUE
 v=row.common_silhouette
 if np.isfinite(v):
  axs[0].plot([0,v],[i,i],color=col,lw=1.3,alpha=.55)
  axs[0].plot(v,i,marker='^' if noise else 'o',color=col,ms=7)
  axs[0].text(v+.025,i,f'{v:.3f}',va='center',fontsize=9,color=col)
 else:axs[0].text(.015,i,'全噪声 · 无可评估簇',va='center',fontsize=9,color=ORANGE)
 r=row.bootstrap_exact_reselected; f=row.bootstrap_exact_fixed_k
 if np.isfinite(row.chosen_k):
  axs[1].plot([r,f],[i,i],color='#A6B2BD',lw=1.5)
  axs[1].plot(f,i,'o',ms=8,mfc='white',mec=GREY,mew=1.4)
 axs[1].plot(r,i,'D',ms=5.8,color=col)
 axs[1].text(r-.025 if r>.91 else r+.023,i-.17,f'{r:.1%}',ha='right' if r>.91 else 'left',fontsize=9,color=col)
 cov=row.common_coverage
 axs[2].barh(i,cov,height=.43,color=col,alpha=.74)
 axs[2].text(max(.025,cov-.035),i,f'{int(round(cov*11))}/11',ha='right' if cov>.1 else 'left',va='center',color='white' if cov>.1 else ORANGE,fontsize=10)
 if row.common_n_clusters==0:axs[2].text(.22,i,'0 个簇',va='center',fontsize=9,color=ORANGE)
axs[0].set(xlim=(-.1,.85),xlabel='原始 CP 空间轮廓系数');axs[0].set_title('A  共同空间的结构分离度',loc='left',pad=15)
axs[1].set(xlim=(0,1.04),xlabel='完整分组复现率');axs[1].set_xticks([0,.25,.5,.75,1],['0','25%','50%','75%','100%']);axs[1].set_title('B  200 次 seed 重采样',loc='left',pad=15)
axs[2].set(xlim=(0,1.04),xlabel='保留为簇成员的构建比例');axs[2].set_xticks([0,.5,1],['0','50%','100%']);axs[2].set_title('C  覆盖率',loc='left',pad=15)
fig.text(.035,.952,'分离度、稳定性与覆盖率需要共同读取',fontsize=20,color=INK)
fig.text(.035,.907,'全部可变 CP 主方法使用 766 对接触；另列前 77 对 CP 谱聚类、密度及敏感性流程。流程顺序固定，未按分数排名。',fontsize=11,color=GREY)
handles=[Line2D([],[],marker='D',color='none',markerfacecolor=BLUE,markeredgecolor=BLUE,label='重选簇数后的复现率'),Line2D([],[],marker='o',color='none',markerfacecolor='white',markeredgecolor=GREY,label='固定原簇数的复现率'),Line2D([],[],marker='^',color='none',markerfacecolor=ORANGE,markeredgecolor=ORANGE,label='存在噪声：分离度为条件值')]
fig.legend(handles=handles,loc='lower left',bbox_to_anchor=(.25,.135),frameon=False,ncol=3,fontsize=10)
fig.text(.035,.095,'每次在各构建内按整个 seed 重采样，重新选择 CP、拟合预处理与聚类；统计计算重复性，不代表实验预测准确率。',fontsize=10.5)
fig.text(.035,.062,'密度方法不预设簇数，空心圆不适用。HDBSCAN 最小簇 3 的 100% 复现率对应“全部为噪声”，无有效聚类。',fontsize=10.5)
fig.text(.035,.029,'高置信接触：两端最小构建均值 pLDDT ≥ 70；70–153：APOBEC1 同源片段内接触，范围限于此敏感性分析。',fontsize=10,color=GREY)
save(fig,'pipeline_metrics_and_stability','代表性流程的共同空间轮廓系数、200 次 seed 重采样分组复现率与覆盖率；高分密度结果仅覆盖部分构建。',
 '完整复现率依照主分析的原始簇标签比较计算，含噪声标签；全噪声复现不构成可用分组。实心为重选簇数，空心为固定基准簇数。', ['results/pipeline_summary.csv','results/pipeline_seed_bootstrap.csv'])

# 3. Pairwise association avoids assuming cluster labels are comparable across methods.
main=[f'variable_all__{m}' for m in MAIN];aa=L.loc[main,NAMES].to_numpy()
base=np.mean([(v[:,None]==v[None,:])&(v[:,None]>=0)&(v[None,:]>=0) for v in aa],axis=0)
order=[B['constructs'].tolist().index(c) for c in NAMES]
boot=np.mean([B[p][np.ix_(order,order)] for p in main],axis=0)
fig=plt.figure(figsize=(16.8,9.5));gs=fig.add_gridspec(1,2,left=.13,right=.94,bottom=.28,top=.79,wspace=.34)
ax0=fig.add_subplot(gs[0,0]);ax1=fig.add_subplot(gs[0,1])
for panel,dd,title in [(ax0,base,'A  原始构建均值：6 个主方法'),(ax1,boot,'B  各方法重选簇数：200 次 seed 重采样')]:
 im=panel.imshow(dd,vmin=0,vmax=1,cmap='Blues',interpolation='nearest')
 panel.set_xticks(range(11),[DISPLAY[c] for c in NAMES],rotation=58,ha='right',rotation_mode='anchor',fontsize=9.3)
 panel.set_yticks(range(11),[DISPLAY[c] for c in NAMES],fontsize=9.3);panel.tick_params(length=0,pad=4)
 panel.set_title(title,loc='left',pad=15,fontsize=12)
 for i in range(11):
  for j in range(11):panel.text(j,i,f'{int(round(dd[i,j]*6))}/6' if panel is ax0 else f'{dd[i,j]*100:.0f}',ha='center',va='center',fontsize=8,color='white' if dd[i,j]>.57 else '#16334C')
 grid(panel,11,11)
 t1=NAMES.index('t31a');t2=NAMES.index('t31d')
 for u,v in [(t1,t2),(t2,t1)]:panel.add_patch(Rectangle((v-.5,u-.5),1,1,fill=False,edgecolor='#D99024',lw=2.3))
cax=fig.add_axes([.956,.34,.012,.37]);cb=fig.colorbar(im,cax=cax,ticks=[0,.25,.5,.75,1]);cb.ax.set_title('同簇\n比例',fontsize=10,pad=12);cb.ax.set_yticklabels(['0','25%','50%','75%','100%'])
fig.text(.035,.954,'跨方法共同分组：T31A 与 T31D 保持一致，N57A 的归属较敏感',fontsize=20,color=INK)
fig.text(.035,.91,'6 个主方法等权：Ward、平均连接、完全连接、K-means、PCA 95% + K-means、谱聚类；全部使用 766 对可变 CP。',fontsize=11,color=GREY)
fig.text(.035,.12,'左图分子为将该对构建放入同一簇的方法数；右图为各方法重采样同簇频率的等权平均（单元格单位：%，取整显示）。',fontsize=11)
fig.text(.035,.083,'橙框：T31A 与 T31D 在这些主流程中始终同簇。清单活性分别为 0.970 和 0.000，仅作事后对照，未用于聚类。',fontsize=11)
fig.text(.035,.046,'六种方法共享同一组数据，彼此相关；平均频率用于描述流程一致性。* G27DM130G 当前序列为 G27D+W130G。',fontsize=10,color=GREY)
save(fig,'main_methods_pairwise_consensus','六种主要聚类方法的构建同簇比例，以及 200 次 seed 重采样的平均同簇比例。T31A 和 T31D 的同簇关系为 100%，N57A 与 N57W 的共同分组依赖方法。',
 '六方法等权，方法并非独立重复。左图为基准结果的 6 方法投票；右图为每方法 200 次重选簇数后同簇矩阵的均值。', ['results/pipeline_labels.csv','results/pipeline_coclustering.npz'])
(O/'figure_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps({'figures':[m['figure'] for m in manifest],'font':str(FONT)},ensure_ascii=False,indent=2))
