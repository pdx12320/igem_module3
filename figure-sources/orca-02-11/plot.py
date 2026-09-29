"""Reproduce APOBEC Figures 2–11 from immutable supplied CSV snapshots.
Run: python3 plot.py --output renders-v2 (new directory required).
No input values are changed. Dependencies: matplotlib, numpy; scipy not required.
"""
from pathlib import Path
import argparse, csv, hashlib, json, math, os, statistics
os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/apobec-mpl-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np
from orca_plot import Theme, export

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output', default='figures')
parser.add_argument('--only', type=int)
args = parser.parse_args()
OUT = ROOT / args.output
OUT.mkdir(exist_ok=True,parents=True)
style_path = ROOT / 'orca-figure-style.json'
if not style_path.exists():
    style = json.loads((ROOT/'orca-style.json').read_text())
    style['figure'].update(width_in=15.8, height_in=10, display_width_px=960,
                           export_scale=4740/960)
    style['text'].update(label_pt=24,tick_pt=22,legend_pt=21,annotation_pt=21,emphasis_pt=26)
    style['chart_settings'] = {'dpi':300,'source_values':'unchanged',
        'functional_class_aliases':{'WT (GCA substrate)':'Wild-type reference'},
        'panels':'One row, two columns where applicable',
        'figure_04_orientation':'Horizontal bars, preserving all 29 rows',
        'figure_08_parent':'Reference line only; 101 defined mutant points',
        'figure_09':'Exclude parent and nine undefined ratios; 41 points',
        'statistics':'Pearson and average-tie Spearman; descriptive OLS, no CI'}
    style['group_styles'] = {
        'Active':{'color':'#27877F','marker':'o'},
        'Inactive':{'color':'#E89B3C','marker':'s'},
        'Partially inactive':{'color':'#5D5AD7','marker':'^'},
        'Not tested':{'color':'#9693A6','marker':'D'},
        'New inactive control (not measured)':{'color':'#E89B3C','marker':'o','fill':'white','hatch':'///'},
        'Wild-type reference':{'color':'#2E267C','marker':'P'}}
    style['group_order'] = list(style['group_styles'])
    style_path.write_text(json.dumps(style,indent=2)+'\n')
theme = Theme(style_path)
C=theme.c
IND=C['indigo700']; ORANGE=C['orange500']; TEAL=C['teal600']; INK=C['ink']; GRAY='#9693A6'
LONG=C['indigo500']; POCKET=TEAL; TARGET=ORANGE
records=[]
source_hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT/'source-data').glob('*.csv')}

def read(stem):
    return list(csv.DictReader((ROOT/'source-data'/f'{stem}.csv').open(encoding='utf-8-sig')))
def nums(rows,key):return np.array([float(r[key]) for r in rows])
def yes(v):return v.lower()=='true'
def cls(row):
    return {'WT (GCA substrate)':'Wild-type reference'}.get(row['functional_class'],row['functional_class'])
def rank(a):
    s=sorted(a)
    return [(s.index(v)+1+len(s)-s[::-1].index(v))/2 for v in a]
def construct(s):return s.replace('WT (GCG parent)','WT–GCG').replace('WT (GCA substrate)','WT–GCA')
def clean(ax,grid='y'):
    ax.set_axisbelow(True)
    ax.grid(axis=grid,color=C['line'],linewidth=.75,alpha=.65)
    ax.tick_params(length=0,pad=8)
    ax.spines[['top','right']].set_visible(False)
    for k in ['left','bottom']:ax.spines[k].set_color(C['line'])
def panel(ax,letter):ax.text(-.12,1.035,letter,transform=ax.transAxes,fontsize=29,fontweight='medium',va='bottom')
def base(height=10,two=False):
    if two:
        fig,axs=plt.subplots(1,2,figsize=(15.8,height))
        fig.subplots_adjust(left=.075,right=.98,bottom=.24,top=.92,wspace=.37)
        for ax,letter in zip(axs,'AB'):clean(ax);panel(ax,letter)
        return fig,axs
    fig,ax=plt.subplots(figsize=(15.8,height))
    fig.subplots_adjust(left=.11,right=.96,bottom=.24,top=.95)
    clean(ax)
    return fig,ax
def legend(fig,handles,labels=None,y=.045,ncol=3,fontsize=21):
    if labels is None:labels=[h.get_label() for h in handles]
    return fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,y),ncol=ncol,
                      fontsize=fontsize,frameon=False,columnspacing=1.5,handlelength=1.6)
def class_handles():
    result=[]
    for k in theme.config['group_order']:
        st=theme.config['group_styles'][k]
        label={'New inactive control (not measured)':'Designed inactive control\n(not measured)',
               'Wild-type reference':'Wild-type reference'}.get(k,k)
        result.append(Patch(facecolor=st.get('fill',st['color']),edgecolor=st['color'],
                            hatch=st.get('hatch'),label=label,linewidth=1.5))
    return result
def colorbar(ax,rows,values):
    for i,(r,v) in enumerate(zip(rows,values)):
        st=theme.config['group_styles'][cls(r)]
        ax.barh(i,v,height=.69,color=st.get('fill',st['color']),edgecolor=st['color'],
                hatch=st.get('hatch'),linewidth=1.2)
def groups(ax,rows,keys,colors,labels,horizontal=False):
    x=np.arange(len(rows));width=.24
    for j,(key,col,lab) in enumerate(zip(keys,colors,labels)):
        if horizontal:ax.barh(x+(j-1)*width,nums(rows,key),height=width,color=col,label=lab)
        else:ax.bar(x+(j-1)*width,nums(rows,key),width=width,color=col,label=lab)
    labs=[construct(r['construct']) for r in rows]
    if horizontal:
        ax.set_yticks(x,labs);ax.invert_yaxis();clean(ax,'x')
    else:ax.set_xticks(x,labs,rotation=55,ha='right',rotation_mode='anchor')
def save(n,slug,fig,caption,alt,sources,checks,exclusions=(),extra=None):
    folder=OUT/f'figure_{n:02d}_{slug}'
    fig.canvas.draw()
    # Matplotlib creates extra locator ticks outside the view; they are not drawn.
    # Hide their labels explicitly so canvas-bound checks inspect visible content only.
    for ax in fig.axes:
        for axis,limits in [(ax.xaxis,ax.get_xlim()),(ax.yaxis,ax.get_ylim())]:
            lo,hi=sorted(limits)
            for tick in axis.get_major_ticks()+axis.get_minor_ticks():
                if not lo<=tick.get_loc()<=hi:
                    tick.label1.set_visible(False);tick.label2.set_visible(False)
    provenance={'source_files':[{'file':'source-data/'+f+'.csv','sha256':source_hashes[f+'.csv']} for f in sources],
        'data_kind':'Supplied construct-level or model-level summaries; no invented repeats or error bars',
        'checks':checks,'exclusions':list(exclusions),'processing':extra or {},'source_values_modified':False}
    paths=export(fig,folder,theme,caption=caption,alt_text=alt,provenance=provenance,stem=folder.name)
    old=Path(paths['png']); new=old.with_name(old.name.replace('@2x',''));old.rename(new)
    fig.savefig(ROOT/'qa'/f'figure_{n:02d}_preview.png',dpi=1200/15.8,facecolor='white')
    # Check text bounds; report candidates, because rotated tick boxes may overlap even when glyphs do not.
    fig.canvas.draw();renderer=fig.canvas.get_renderer();bounds=fig.bbox
    outside=[]
    for obj in fig.findobj(matplotlib.text.Text):
        if not obj.get_visible() or not obj.get_text():continue
        box=obj.get_window_extent(renderer)
        if box.x0 < -1 or box.y0 < -1 or box.x1>bounds.width+1 or box.y1>bounds.height+1:
            outside.append(obj.get_text())
    for stem in sources:
        import shutil
        shutil.copy2(ROOT/'source-data'/f'{stem}.csv',folder/f'{stem}.csv')
    if exclusions:
        with (folder/'exclusions.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['id','panel','reason']);w.writeheader();w.writerows(exclusions)
    records.append({'figure':n,'folder':str(folder.relative_to(ROOT)),'text_outside_canvas':outside,'checks':checks})
    plt.close(fig)

def figure8():
    stem='figure_08_single_site';rows=read(stem);parent=next(r for r in rows if yes(r['is_parent']))
    valid=[r for r in rows if not yes(r['is_parent']) and yes(r['plus1_ratio_defined'])]
    fig,ax=base(10)
    for active,col,label in [(False,GRAY,'Activity retention < 0.70'),(True,IND,'Activity retention ≥ 0.70')]:
        subset=[r for r in valid if (float(r['activity_retention_vs_same_batch_parent'])>=.7)==active and r['mutant']!='30H']
        ax.scatter(nums(subset,'plus1_ratio_GCG_over_GCA'),nums(subset,'activity_retention_vs_same_batch_parent'),s=115,
                   c=col,edgecolors='white',linewidth=.9,alpha=.9,label=label,zorder=3)
    ax.axvline(float(parent['plus1_ratio_GCG_over_GCA']),color=GRAY,ls=':',lw=2)
    ax.axvline(2,color=ORANGE,ls='--',lw=2)
    ax.axhline(.7,color=TEAL,ls='--',lw=2)
    ax.text(float(parent['plus1_ratio_GCG_over_GCA'])-.025,1.105,'Parent 1.371',ha='right',va='bottom',fontsize=21)
    ax.text(2.025,1.105,'Target 2.0',va='bottom',fontsize=21)
    ax.text(.48,.72,'Retention floor 0.70',color=TEAL,fontsize=21)
    k=next(r for r in valid if r['mutant']=='30H');ax.scatter([1.71],[.84],marker='*',s=420,color=ORANGE,edgecolors=INK,lw=.7,zorder=5)
    ax.annotate('K30H\n(1.71, 0.84)',(1.71,.84),xytext=(2.13,.96),fontsize=24,ha='left',
                arrowprops={'arrowstyle':'-','color':INK,'lw':1.1},bbox={'facecolor':'white','edgecolor':'none','pad':2})
    for name in ['130G','60Q','31G']:
        r=next(r for r in valid if r['mutant']==name)
        ax.annotate(name,(float(r['plus1_ratio_GCG_over_GCA']),float(r['activity_retention_vs_same_batch_parent'])),
                    xytext=(0,-26),textcoords='offset points',ha='center',fontsize=21,color=C['muted'])
    ax.set(xlim=(.38,3.12),ylim=(-.04,1.18),xlabel='+1 ratio (GCG / GCA)',ylabel='Activity retention\n(relative to same-batch parent)')
    h,l=ax.get_legend_handles_labels();h.append(Line2D([],[],marker='*',color='none',markerfacecolor=ORANGE,markeredgecolor=INK,markersize=17));l.append('K30H')
    legend(fig,h,l,ncol=2)
    assert len(valid)==101 and max((r for r in valid if float(r['activity_retention_vs_same_batch_parent'])>=.7),key=lambda r:float(r['plus1_ratio_GCG_over_GCA']))['mutant']=='30H'
    exclusions=[{'id':'31Y','panel':'single','reason':'Undefined GCG/GCA ratio: GCA editing recorded as zero'},
                {'id':parent['mutant'],'panel':'single','reason':'Parent represented by reference line, not mutant scatter point'}]
    save(8,'single_site',fig,
         'Each point represents one of 101 plotted single mutants, using the supplied construct-level summaries. Of 102 mutants, 31Y is excluded because its GCA editing was undetected and its ratio is undefined; the same-batch parent is shown as a vertical reference line (1.3707, displayed as 1.371). K30H is starred: it has the highest +1 ratio among mutants retaining at least 70% activity (ratio 1.71; retention 0.84). Three mutants exceed a ratio of 2.0 (130G, 60Q and 31G) but retain only 0.32, 0.17 and 0.13 of parent activity. No mutant meets both ratio ≥2.0 and retention ≥0.70. Retention is a cellular editing measure relative to the parent, not purified enzyme activity. No uncertainty estimates or significance tests are shown.',
         'Scatter plot of 101 mutants, highlighting K30H and showing that none meets both specificity and activity-retention thresholds.',
         [stem],{'mutant_points':101,'parent_lines':1,'undefined_mutants':1,'joint_threshold_pass':0},exclusions)

def figure2():
    stem='figure_02_cp_deviation';rows=read(stem);valid=[r for r in rows if r['activity_retention_fraction']]
    fig,(a,b)=base(13,True);fig.subplots_adjust(left=.21,bottom=.23,wspace=.4)
    groups(a,rows,['z_internal_cp_longrange','z_pocket_cp','z_protein_targetC_cp'],[LONG,POCKET,TARGET],
           ['Internal CP (long-range)','Pocket CP','Protein–target-C CP'],True)
    a.axvspan(-3,3,color=C['line'],alpha=.4,zorder=0);a.axvline(0,color=C['muted'],lw=.8)
    a.set_xlabel('Deviation from WT (SD)');a.set_ylim(len(rows)-.5,-.7)
    b.scatter(nums(valid,'z_protein_targetC_cp'),nums(valid,'activity_retention_fraction'),s=125,c=IND,edgecolors='white',lw=.8,zorder=3)
    r=statistics.correlation(nums(valid,'z_protein_targetC_cp'),nums(valid,'activity_retention_fraction'))
    b.set(xlabel='Protein–target-C\ndeviation (SD)',ylabel='Activity retention\n(relative to parent)',ylim=(-.02,1.1))
    b.text(.05,.95,f'Pearson r = {r:.3f}\nn = {len(valid)}',transform=b.transAxes,va='top',fontsize=23)
    h,l=a.get_legend_handles_labels();h.append(Patch(facecolor=C['line'],alpha=.5));l.append('±3 SD band');legend(fig,h,l,ncol=2,y=.015)
    save(2,'cp_deviation',fig,'Panel A shows three contact-probability (CP) deviation descriptors for all 14 constructs; the shaded interval is the supplied ±3 SD reference band. Panel B shows the 10 constructs with reported activity retention against protein–target-C deviation (Pearson r = %.3f). Four missing activity values are excluded only from panel B and are not imputed. Each point/bar is a supplied construct-level summary; no error bars or significance tests are inferred. The association is descriptive and does not establish predictive validity.'%r,
         'Three CP descriptors for 14 constructs, paired with a scatter plot of activity retention for the 10 measured constructs.',[stem],{'A_constructs':14,'A_bars':42,'B_points':10,'pearson_r':r},
         [{'id':r['construct'],'panel':'B','reason':'Activity retention missing'} for r in rows if not r['activity_retention_fraction']])

def figure3():
    stem='figure_03_ddcp_matrix';rows=sorted(read(stem),key=lambda r:int(r['residue_position']));cols=list(rows[0])[2:]
    mat=np.array([[float(r[k]) for k in cols] for r in rows]);mx=float(np.abs(mat).max())
    fig,ax=base(22);fig.subplots_adjust(left=.11,right=.89,bottom=.22,top=.97)
    cmap=LinearSegmentedColormap.from_list('orca_diverging',[IND,'#FFFFFF',ORANGE])
    im=ax.pcolormesh(np.arange(len(cols)+1)-.5,np.arange(len(rows)+1)-.5,mat,
                     cmap=cmap,norm=TwoSlopeNorm(vmin=-mx,vcenter=0,vmax=mx),shading='flat',rasterized=False)
    ax.invert_yaxis()
    ax.grid(False);ax.set_xticks(range(len(cols)),cols,rotation=65,ha='right',rotation_mode='anchor')
    ax.set_yticks(range(len(rows)),[r['wt_aa']+r['residue_position'] for r in rows]);ax.tick_params(labelsize=21)
    for i in range(len(rows)):
        for j in range(len(cols)):
            v=mat[i,j]
            if abs(v)>=.05:
                rgb=cmap(im.norm(v))[:3];lum=sum(a*b for a,b in zip(rgb,[.2126,.7152,.0722]))
                ax.text(j,i,format(v,'.4f').rstrip('0').rstrip('.'),ha='center',va='center',rotation=90,fontsize=13.5,color='white' if lum<.46 else INK)
    cb=fig.colorbar(im,ax=ax,fraction=.035,pad=.035);cb.set_label('ΔΔCP relative to WT',labelpad=17);cb.ax.tick_params(labelsize=20)
    allrows=read('figure_03_all_residues_ddcp');top=sorted(allrows,key=lambda r:max(abs(float(r[k])) for k in cols),reverse=True)[:22]
    assert {r['residue_position'] for r in rows}=={r['residue_position'] for r in top}
    save(3,'ddcp_heatmap',fig,'ΔΔCP is shown for the 22 residues with the largest maximum absolute change across the 21 mutant constructs, selected from the supplied 199-residue table. Rows are sorted by sequence position. The color scale is symmetric about zero (±%.4f); only cells with |ΔΔCP| ≥0.05 are labelled, preserving supplied decimal precision. The supplied task specification reports an independent WT rerun maximum |ΔΔCP| of 0.0265; that rerun is not included in this plotting package. Near-zero values indicate little change in this descriptor, rather than evidence of unchanged function. The full-resolution SVG/PDF is recommended for cell labels.'%mx,
         'Diverging heatmap of 22 residues and 21 constructs with numerical annotations for absolute ΔΔCP values of at least 0.05.',
         [stem,'figure_03_all_residues_ddcp'],{'rows':22,'columns':21,'top22_verified':True,'symmetric_limit':mx,'annotated_cells':int((abs(mat)>=.05).sum())},extra={'annotation_font_pt':13.5,'dense_heatmap_exception':'Exact four-decimal cell values require zoom; axis labels remain 21 pt'})

def figure4():
    stem='figure_04_negctrl_diagnosis';rows=read(stem);fig,(a,b)=base(21,True)
    fig.subplots_adjust(left=.245,right=.98,bottom=.22,top=.93,wspace=.22)
    clean(a,'x');clean(b,'x')
    for i,r in enumerate(rows):
        if r['target_C4N4_to_E72_distance_A']:
            st=theme.config['group_styles'][cls(r)];a.barh(i,float(r['target_C4N4_to_E72_distance_A']),height=.69,color=st.get('fill',st['color']),edgecolor=st['color'],hatch=st.get('hatch'),lw=1.2)
        else:a.text(.2,i,'Distance unavailable',va='center',fontsize=19,color=C['muted'],bbox={'facecolor':'white','edgecolor':'none','pad':1},zorder=5)
    a.set_yticks(range(len(rows)),[construct(r['construct']) for r in rows]);a.set_ylim(len(rows)-.5,-.7);a.set_xlim(0,7.7)
    a.axvline(2.599,color=IND,ls='--',lw=2);a.set_xlabel('Target C4N4–E72\ndistance (Å)')
    a.text(.96,1.006,'WT 2.599 Å',transform=a.transAxes,ha='right',fontsize=21)
    groups(b,rows,['z_internal_cp_longrange','z_pocket_cp','z_protein_targetC_cp'],[LONG,POCKET,TARGET],['Internal CP (long-range)','Pocket CP','Protein–target-C CP'],True)
    b.set_yticks(range(len(rows)),['']*len(rows));b.set_ylim(len(rows)-.5,-.7);b.axvspan(-3,3,color=C['line'],alpha=.4,zorder=0);b.axvline(0,color=C['muted'],lw=.7)
    b.set_xlabel('Deviation from WT (SD)');b.set_xlim(-5,65)
    legend(fig,class_handles(),ncol=3,y=.062,fontsize=21)
    h,l=b.get_legend_handles_labels();h.append(Patch(facecolor=C['line']));l.append('±3 SD band');legend(fig,h,l,ncol=2,y=.005,fontsize=21)
    save(4,'negctrl_diagnosis',fig,'Panel A shows reported target C4N4–E72 distances for 27 control constructs and two WT references (29 rows). Functional class determines the bar fill; the dashed line is the WT–GCG value in this table, 2.599 Å. E72A has no supplied distance and is labelled “Distance unavailable”; a missing value does not establish that no model exists. E72A and N57A are designed inactive controls with no reported activity measurement and are distinguished from measured inactive constructs by an unfilled, hatched style. Panel B shows three CP deviation descriptors, with an independent descriptor legend and a ±3 SD band. Both panels use horizontal bars to keep every construct name readable. No missing value is converted to zero.',
         'Aligned horizontal panels compare available catalytic distances and three CP descriptors for 29 rows, retaining unmeasured controls as a separate class.',[stem],{'rows':29,'A_distance_bars':28,'B_descriptor_bars':87,'WT_reference_A':2.599,'functional_classes':6},
         [{'id':'E72A','panel':'A','reason':'Distance unavailable; row and category retained'}],extra={'orientation_change':'Vertical to horizontal to preserve readable labels'})

def figure5():
    stem='figure_05_negctrl_pca';rows=read(stem);ordered=sorted(rows,key=lambda r:float(r['D_M_mahalanobis_to_WT']))
    fig=plt.figure(figsize=(15.8,19));a=fig.add_axes([.08,.48,.36,.41]);b=fig.add_axes([.7,.13,.27,.8]);clean(a);clean(b,'x');panel(a,'A');panel(b,'B')
    for r in rows:
        st=theme.config['group_styles'][cls(r)];a.scatter(float(r['PC1']),float(r['PC2']),s=150,
            marker=st['marker'],facecolors=st.get('fill',st['color']),edgecolors=st['color'],linewidths=1.6,zorder=3)
    offsets={'E72A':(-.1,-1.02),'N57W':(1.7,.6),'N57A':(1.4,.94),'T31D':(1.0,-.38),'T31A':(-1.75,-.83),'WT-GCA':(.0,.73),'Y32F':(-1.85,-.3)}
    for r in rows:
        if r['construct'] in offsets:
            dx,dy=offsets[r['construct']];a.annotate(r['construct'],(float(r['PC1']),float(r['PC2'])),xytext=(dx,dy),textcoords='data',ha='left',fontsize=21,
                arrowprops={'arrowstyle':'-','color':C['muted'],'lw':.8},bbox={'facecolor':'white','edgecolor':'none','pad':1.2})
    a.set(xlabel='PC1',ylabel='PC2',xlim=(-2.4,2.75),ylim=(-1.35,2.65))
    colorbar(b,ordered,nums(ordered,'D_M_mahalanobis_to_WT'));b.set_yticks(range(28),[construct(r['construct']) for r in ordered]);b.set_ylim(27.7,-.7)
    b.axvline(1.57,color=IND,ls='--',lw=1.7);b.set_xlabel('Distance from WT, D$_M$');b.text(.98,1.007,'WT null 95th percentile: 1.57',transform=b.transAxes,ha='right',fontsize=19)
    # A compact legend under the PCA panel preserves the full height of the ranking.
    fig.legend(handles=class_handles(),loc='upper left',bbox_to_anchor=(.07,.4),ncol=1,fontsize=21,frameon=False,labelspacing=1.1)
    save(5,'negctrl_pca',fig,'Panel A shows the supplied PC1 and PC2 coordinates for 28 controls; seven specified constructs are labelled. Panel B ranks the supplied Mahalanobis distances to WT in ascending order, with the supplied WT-null 95th percentile of 1.57. Functional categories are encoded consistently across panels; designed but unmeasured E72A and N57A are separate from measured inactive controls. The WT (GCA substrate) category is mapped to the shared Wild-type reference color. Seven of 11 constructs labelled Active exceed 1.57, showing that exceeding this reference does not identify inactivity. PCA coordinates and distances are supplied results and are not recomputed here.',
         'PCA scatter and ascending Mahalanobis-distance ranking of 28 controls, with unmeasured controls shown separately.',[stem],{'PCA_points':28,'rank_bars':28,'active_constructs':11,'active_above_threshold':7},extra={'class_alias':'WT (GCA substrate) → Wild-type reference'})

def figure6():
    s1='figure_06a_protein_only_deviation';s2='figure_06b_protein_only_classification';rows=read(s1);scores=read(s2)
    fig,(a,b)=base(11,True);fig.subplots_adjust(bottom=.31)
    groups(a,rows,['D_M_internal_cp_all','D_M_internal_cp_longrange','D_M_pocket_cp'],[IND,LONG,POCKET],['Internal CP (all)','Internal CP (long-range)','Pocket CP'])
    a.set_ylabel('Protein-only distance, D$_M$')
    vals=nums(scores,'classification_accuracy');b.bar(range(3),vals,color=[IND,LONG,POCKET],width=.6)
    b.set_xticks(range(3),['Internal CP\n(all)','Internal CP\n(long-range)','Pocket CP']);b.tick_params(axis='x',labelsize=20)
    b.set_ylim(0,1.07);b.set_ylabel('Reported classification accuracy');b.axhline(.5,color=GRAY,ls='--',lw=1.7)
    b.text(.97,.51,'Chance 0.50',transform=b.get_yaxis_transform(),ha='right',va='bottom',fontsize=20)
    for i,v in enumerate(vals):b.text(i,v+.025,str(scores[i]['classification_accuracy']),ha='center',fontsize=23)
    h,l=a.get_legend_handles_labels();legend(fig,h,l,ncol=2,y=.015)
    save(6,'protein_only',fig,'Panel A compares supplied protein-only Mahalanobis distances for 10 constructs using three internal-contact feature sets. Panel B shows the three reported dead/active classification accuracies and the supplied 0.50 chance reference. The plotting package does not specify the classification evaluation design, labelled sample denominator, or uncertainty; these bars reproduce the supplied summaries and must not be interpreted as independently validated generalization performance. No new classification analysis or error bars are added.',
         'Protein-only distances across three feature sets and the corresponding reported classification accuracies.',[s1,s2],{'A_constructs':10,'A_bars':30,'B_bars':3,'chance_reference':.5})

def figure7():
    stem='figure_07_protein_only_vs_complex';rows=sorted(read(stem),key=lambda r:float(r['D_M_protein_only_no_RNA']))
    fig,ax=base(10);fig.subplots_adjust(bottom=.29)
    x=np.arange(10);ax.bar(x-.18,nums(rows,'D_M_complex_with_RNA'),width=.35,color=IND,label='Complex with RNA');ax.bar(x+.18,nums(rows,'D_M_protein_only_no_RNA'),width=.35,color=TEAL,label='Protein only')
    ax.set_xticks(x,[r['construct'] for r in rows],rotation=45,ha='right',rotation_mode='anchor');ax.set_ylabel('Distance from WT, D$_M$');ax.axhline(1.57,color=GRAY,ls='--',lw=1.5)
    for i,r in enumerate(rows):
        if r['construct'] in ['T31D','E72A']:ax.text(i,max(float(r['D_M_complex_with_RNA']),float(r['D_M_protein_only_no_RNA']))+.3,r['fraction_retained_pct']+'%\nretained',ha='center',fontsize=21)
    ax.set_ylim(0,max(nums(rows,'D_M_complex_with_RNA'))*1.15);h,l=ax.get_legend_handles_labels();h.append(Line2D([],[],color=GRAY,ls='--'));l.append('Reference 1.57');legend(fig,h,l,y=.01)
    save(7,'protein_only_vs_complex',fig,'Ten constructs are compared using the supplied distances under complex-with-RNA and protein-only modelling conditions, sorted by protein-only distance. The 1.57 reference is reproduced from the task specification. Annotations for T31D and E72A are the supplied protein-only/complex distance ratios expressed as percentages. E72A is the only construct in this set with a larger protein-only distance. These are descriptive comparisons of model-derived distances; the ratios do not quantify a causal fraction of structural deviation explained by RNA binding.',
         'Paired bars compare complex and protein-only distances for 10 constructs, highlighting T31D and E72A.',[stem],{'constructs':10,'bars':20,'increased_without_RNA':['E72A']})

def figure9():
    stem='figure_09_targeting_ratio';rows=read(stem);valid=[r for r in rows if not yes(r['is_wildtype_parent']) and yes(r['targeting_ratio_defined'])]
    x=nums(valid,'sum_nonGCG_editing_pct');y=nums(valid,'targeting_ratio');r=statistics.correlation(x,y);rho=statistics.correlation(rank(x),rank(y));coef=np.polyfit(x,y,1)
    fig,(a,b)=base(10.5,True);fig.subplots_adjust(bottom=.21)
    for lo,hi,col in [(10,20,C['lavender100']),(35,60,'#E3F0EE')]:
        a.axvspan(lo,hi,color=col,zorder=0)
        subset=[float(t['targeting_ratio']) for t in valid if lo<=float(t['on_target_C388_pct'])<=hi];med=statistics.median(subset)
        a.hlines(med,lo,hi,color=IND if lo==10 else TEAL,lw=4,zorder=4)
        a.text((lo+hi)/2,7.1,f'Median\n{med:.2f}',ha='center',fontsize=21,color=IND if lo==10 else TEAL)
    a.scatter(nums(valid,'on_target_C388_pct'),y,s=90,c=IND,edgecolors='white',lw=.8,zorder=3)
    b.scatter(x,y,s=90,c=IND,edgecolors='white',lw=.8,zorder=3)
    xx=np.linspace(x.min(),x.max(),100);b.plot(xx,np.polyval(coef,xx),color=ORANGE,lw=2.3)
    b.text(.96,.96,f'Pearson r = {r:.3f}\nSpearman ρ = {rho:.3f}\nn = {len(valid)}',transform=b.transAxes,ha='right',va='top',fontsize=21,bbox={'facecolor':'white','edgecolor':'none','alpha':.9})
    a.set(xlabel='On-target C388 editing (%)',ylabel='Targeting ratio');b.set(xlabel='Summed non-GCG editing (%)',ylabel='Targeting ratio')
    for ax in [a,b]:ax.set_ylim(-.6,8)
    legend(fig,[Patch(facecolor=C['lavender100']),Patch(facecolor='#E3F0EE'),Line2D([],[],color=ORANGE)],['10–20% on-target','35–60% on-target','Linear fit (panel B)'],ncol=2,y=.015)
    excl=[{'id':t['construct'],'panel':'A and B','reason':'Parent excluded by specification' if yes(t['is_wildtype_parent']) else 'Undefined targeting ratio; zero denominator'} for t in rows if yes(t['is_wildtype_parent']) or not yes(t['targeting_ratio_defined'])]
    save(9,'targeting_ratio',fig,'Both panels contain 41 mutant constructs with defined targeting ratios, after excluding one parent and nine mutants with a zero denominator. Panel A relates the ratio to on-target editing; shaded activity strata are 10–20%% (n=13, median 2.528, shown as 2.53) and 35–60%% (n=14, median 1.203, shown as 1.20). Panel B relates the ratio to summed non-GCG editing and includes a descriptive ordinary least-squares fit, Pearson r = %.3f and Spearman ρ = %.3f. Correlations use complete pairs and average ranks for ties. A ratio plotted against its own denominator has mathematical coupling; the association alone does not establish a causal detection-floor mechanism. No undefined ratio is plotted as zero and no confidence interval is inferred.'%(r,rho),
         'Two scatter panels show targeting ratio against on-target editing and summed non-GCG editing for 41 mutants.',[stem],{'points_per_panel':41,'excluded_parent':1,'undefined_mutants':9,'pearson_r':r,'spearman_rho':rho,'OLS_slope':float(coef[0]),'OLS_intercept':float(coef[1])},excl)

def figure10():
    s1='figure_10a_candidate_groups_raw';s2='figure_10b_candidate_group_sizes';s3='figure_10c_candidate_priority_matrix';raw=read(s1);sizes=read(s2);mat=read(s3)
    fig,(a,b)=base(12,True);fig.subplots_adjust(bottom=.43)
    labels=['A replication','B new single','C new combinations','D controls','E relaxed pairing'];x=np.arange(5)
    a.bar(x,nums(sizes,'n_candidates'),color=IND,width=.6)
    for i,r in enumerate(sizes):a.text(i,int(r['n_candidates'])+.5,r['n_candidates'],ha='center',fontsize=24)
    order=['Required','P0 (top pick)','P0 (gold standard)','P0 (control)','P0','P1 (control)','P1 (mechanism)','P1','P2 (mechanism)','P2 (reference)','P2']
    colors=[INK,ORANGE,ORANGE,ORANGE,ORANGE,IND,IND,IND,'#9D9CF4','#9D9CF4','#9D9CF4'];hatches=['','..','xx','///','','///','xx','','xx','..','']
    bottom=np.zeros(5);handles=[]
    for key,col,hatch in zip(order,colors,hatches):
        vals=nums(mat,key);b.bar(x,vals,bottom=bottom,width=.6,color=col,edgecolor='white',lw=.8,hatch=hatch,label=key);bottom+=vals
        handles.append(Patch(facecolor=col,edgecolor='white',hatch=hatch,label=key))
    for ax in [a,b]:ax.set_xticks(x,labels,rotation=55,ha='right',rotation_mode='anchor');ax.tick_params(axis='x',labelsize=20);ax.set_ylim(0,22);ax.set_yticks([0,5,10,15,20]);ax.set_ylabel('Number of candidates')
    legend(fig,handles,ncol=3,y=.015,fontsize=21)
    assert np.array_equal(bottom,nums(sizes,'n_candidates'))
    save(10,'candidates',fig,'Panel A shows the 61 candidate-list entries assigned to groups A–E (18, 6, 12, 5 and 20). Panel B shows the priority composition using the supplied 11 priority categories and specified stacking order. Colors encode broad priority tiers and hatches distinguish subcategories. Counts were cross-checked against all 61 raw candidate-list entries; entries are counted as supplied, without deduplication. These are proposed next-cycle candidates, not completed experiments or measured outcomes.',
         'Group sizes and priority composition for 61 proposed next-cycle candidate entries.',[s1,s2,s3],{'entries':61,'groups':5,'priority_categories':11,'group_counts':[18,6,12,5,20]})

def figure11():
    s1='figure_11a_sampling_frequency_by_position';s2='figure_11b_positions_passing_threshold';s3='figure_11c_contested_substitutions';freq=read(s1);curve=read(s2);subs=read(s3)
    fig,(a,b)=base(10.5,True);fig.subplots_adjust(bottom=.25)
    a.plot(nums(curve,'sampling_frequency_threshold'),nums(curve,'n_positions_passing'),color=IND,lw=2.5,marker='o',ms=4)
    a.axvline(.5,color=TEAL,ls='--');a.axvline(.8,color=ORANGE,ls='--');a.set(xlim=(0,1),ylim=(0,210),xlabel='Sampling-frequency threshold',ylabel='Positions passing threshold')
    a.text(.48,195,'γ = 0.5',rotation=90,va='top',ha='right',color=TEAL,fontsize=21);a.text(.82,195,'β = 0.8',rotation=90,va='top',color=INK,fontsize=21)
    vals=nums(subs,'sampling_frequency');b.bar(range(4),vals,color=IND,width=.62);b.set_xticks(range(4),[r['substitution'] for r in subs]);b.axhline(.5,color=TEAL,ls='--');b.set(ylim=(0,1),ylabel='Sampling frequency')
    for i,r in enumerate(subs):b.text(i,float(r['sampling_frequency'])+.025,r['sampling_frequency'],ha='center',fontsize=23)
    legend(fig,[Line2D([],[],color=TEAL,ls='--'),Line2D([],[],color=ORANGE,ls='--')],['Coil threshold γ = 0.5','Structured-region threshold β = 0.8'],ncol=1,y=.015)
    assert all(int(r['n_positions_passing'])==sum(float(t['frequency'])>=float(r['sampling_frequency_threshold']) for t in freq) for r in curve)
    save(11,'aice_filter',fig,'Panel A counts positions whose most frequent amino acid meets each sampling-frequency threshold; all 40 supplied curve points were verified against the 199-position frequency table. The task specification identifies 48 ProteinMPNN samples at temperature 0.3 and supplies thresholds γ=0.5 for coil and β=0.8 for structured regions. Panel B reproduces the supplied frequencies for H29P, K30T, N57D and A59P; all four are annotated as coil and exceed their applicable threshold of 0.5. Display precision follows the supplied tables. This is a retrospective filter comparison, not prospective validation of activity or specificity.',
         'Threshold curve for 199 positions and sampling frequencies of four substitutions that all pass the supplied coil threshold.',[s1,s2,s3],{'positions':199,'curve_points':40,'curve_recount_verified':True,'substitutions':4,'passing_coil_threshold':4})

with theme.context():
    for number,fn in [(8,figure8),(2,figure2),(3,figure3),(4,figure4),(5,figure5),(6,figure6),(7,figure7),(9,figure9),(10,figure10),(11,figure11)]:
        if args.only and args.only!=number:continue
        print('Rendering Figure',number,flush=True);fn()
(ROOT/'qa'/('checks-'+str(args.only or 'all')+'.json')).write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
