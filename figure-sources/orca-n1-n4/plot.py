"""Reproduce N1–N4 from the supplied CSVs. No data imputation or inference.

Usage: python3 plot.py [--out figures]
Outputs must not already exist; use a new --out directory for another render.
"""
from pathlib import Path
import os, tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'orca-combo-mpl'))
import argparse, csv, hashlib, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from orca_plot import Theme, export

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--out', default='figures')
ARGS = parser.parse_args()
OUT = ROOT / ARGS.out
OUT.mkdir(parents=True, exist_ok=True)
THEME = Theme(ROOT / 'orca-figure-style.json')
C = THEME.c
X = 'activity_retention_fraction'
Y = 'on_target_GCG_over_offtarget_GCA_ratio'
R = 'ROF_ratio_over_same_batch_parent'
TRIPLE = '27T-30H-58M'
RED = '#AD344C'  # darker coral for the explicitly invalid failed-well marker
HASHES = {}
for line in (ROOT/'input/SHA256SUMS.txt').read_text().splitlines():
    h, name = line.split(None, 1)
    name = name.strip()
    actual = hashlib.sha256((ROOT/'input'/name).read_bytes()).hexdigest()
    assert actual == h, name
    HASHES[name] = h

def read(name):
    d = pd.read_csv(ROOT/'input/data'/name, encoding='utf-8-sig')
    d.insert(0, 'source_row', np.arange(2, len(d)+2))
    d.insert(0, 'source_file', name)
    return d

combo = read('combo_batch_ratio_vs_retention.csv')
triple = read('triple_record_across_batches.csv')
design = read('designed_batch_groups.csv')
pair = read('designed_batch_groupD_pairing.csv').sort_values('bar_order')
third = read('third_batch_all_groups.csv')
single = read('single_mutant_background.csv')

def pareto(d, y):
    a = d[[X, y]].to_numpy()
    mask = np.array([not ((a >= v).all(axis=1) & (a > v).any(axis=1)).any() for v in a])
    return d.loc[mask].sort_values(X)

valid1 = combo[combo[Y].notna()].copy()
front1 = pareto(valid1, Y)
assert len(combo) == 48 and len(valid1) == 36
assert set(front1.construct) == set(combo.loc[combo.on_pareto_front, 'construct'])
assert list(valid1.loc[(valid1[X] >= .70) & (valid1[Y] >= 2), 'construct']) == [TRIPLE]
valid3 = design[design.ratio_defined & ~design.excluded_failed_well].copy()
assert len(valid3) == 35
valid4 = third[~third.is_reference_group].copy()
front4 = pareto(valid4, R)
sat = valid4[(valid4.group_type == 'single') & valid4.construct.str.startswith('27')].copy()
assert len(valid4) == 25 and len(sat) == 10 and sat.C295_not_detected.sum() == 7
assert valid4.loc[valid4[X] >= .95].sort_values(R, ascending=False).iloc[0].construct == TRIPLE
assert valid4.loc[valid4[R] >= 1.20].sort_values(X, ascending=False).iloc[0].construct == TRIPLE
assert set(sat.loc[sat[R] >= 1.13, 'construct']) == {'27I','27V','27E'}
assert valid4[R].rank(ascending=False, method='min')[valid4.construct == TRIPLE].iloc[0] == 3
assert valid4[X].rank(ascending=False, method='min')[valid4.construct == TRIPLE].iloc[0] == 10

RECORDS = []
AUDITS = []
def point(ax, data, y, color, marker='o', size=95, **kwargs):
    return ax.scatter(data[X], data[y], s=size, c=color, marker=marker,
                      edgecolors=C['ink'], linewidths=.65, zorder=4, **kwargs)

def label(ax, d, y, name, xytext, *, emphasis=False, text=None):
    r = d.set_index('construct').loc[name]
    return ax.annotate(text or name, (r[X], r[y]), xytext=xytext,
                       fontsize=22 if emphasis else 18, ha='left', va='center',
                       arrowprops=dict(arrowstyle='-', color=C['muted'], lw=.9,
                                       shrinkA=4, shrinkB=8),
                       bbox=dict(facecolor='white', edgecolor='none', alpha=.92, pad=2),
                       zorder=6)

def setup(ax, *, y='ROF (ratio / same-batch parent)', x=True):
    ax.set_ylabel(y, labelpad=12)
    if x:
        ax.set_xlabel('Activity retention\n(c.388 / same-batch parent)', labelpad=12)
    ax.tick_params(length=6, pad=7)

def lines(ax, floor, parent=1):
    ax.axhline(parent, color=C['muted'], ls=':', lw=1.6, zorder=1)
    ax.axvline(floor, color=C['teal600'], ls='--', lw=1.6, zorder=1)

def save(fig, name, caption, alt, frames, parameters):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    # Catch canvas clipping; interpretive label checks are also performed visually.
    from matplotlib.text import Text
    clipped = []
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text().strip(): continue
        b = t.get_window_extent(renderer)
        if b.x0 < -1 or b.y0 < -1 or b.x1 > fig.bbox.width+1 or b.y1 > fig.bbox.height+1:
            clipped.append(t.get_text())
    if clipped:
        raise ValueError(f'{name}: text outside canvas: {clipped}')
    directory = OUT/name
    prov = {'sources': HASHES, 'input_scope': 'Entire supplied CSV files; source_row is the original CSV line number.',
            'experimental_unit': 'One supplied construct-level summary per point/bar; replicate-level values are unavailable.',
            'statistics': 'Descriptive display only; no estimated uncertainty, regression, significance tests or imputation.',
            'source_values': 'unchanged', 'parameters': parameters,
            'n_rows_by_output': {k:len(v) for k,v in frames.items()},
            'versions': {'pandas':pd.__version__}}
    paths = export(fig, directory, THEME, caption=caption, alt_text=alt, provenance=prov, stem=name)
    # The helper always uses @2x in its filename; this set uses 300 dpi and explicit names.
    old = Path(paths['png']); new = old.with_name(f'{name}.png'); old.rename(new); paths['png']=str(new)
    for fname, frame in frames.items():
        frame.to_csv(directory/f'{fname}.csv', index=False)
    # Independent 960px preview for real wiki display-size inspection.
    im = Image.open(new)
    im.resize((960, round(im.height*960/im.width)), Image.Resampling.LANCZOS).save(directory/'preview-960.png')
    # Track scientific artists as well as file output, without counting legends as data.
    artist_counts = [{'points':sum(len(c.get_offsets()) for c in ax.collections), 'bars':sum(isinstance(p, Rectangle) for p in ax.patches)} for ax in fig.axes]
    AUDITS.append({'figure':name,'canvas_text_clipping':clipped,'axes_artist_counts':artist_counts,'png_pixels':list(im.size)})
    RECORDS.append({'name':name, 'paths':paths})
    plt.close(fig)

with THEME.context():
    # N1: Keep the view within one batch; optional other-batch point cloud omitted.
    fig = plt.figure(figsize=(12,9))
    ax = fig.add_axes([.135,.31,.82,.64])
    ax.set(xlim=(0,1.04), ylim=(0,4.1), xticks=np.arange(0,1.01,.2), yticks=np.arange(0,4.1,1))
    ax.add_patch(Rectangle((.7,2), .34,2.1,facecolor=C['orange500'], alpha=.07, edgecolor='none',zorder=0))
    ax.axhline(2, color=C['orange500'],ls='--',lw=1.7,zorder=1)
    ax.axvline(.7, color=C['teal600'],ls='--',lw=1.7,zorder=1)
    ax.axhline(1.371, color=C['muted'],ls=':',lw=1.4,zorder=1)
    ax.plot(front1[X],front1[Y], ls='--', color=C['muted'], lw=1.8,zorder=2)
    for n in (1,2,3):
        s = THEME.style(f'Batch: {n} substitution'+('s' if n!=1 else ''))
        point(ax,valid1[(valid1.n_substitutions==n)&~valid1.is_the_triple],Y,s['color'],s['marker'])
    point(ax,valid1[valid1.is_the_triple],Y,C['orange500'],'*',560)
    label(ax,valid1,Y,TRIPLE,(.57,2.78),emphasis=True,text=TRIPLE+'\n2.156 ratio | 0.773 retention')
    label(ax,valid1,Y,'58M-130G',(.32,3.91))
    label(ax,valid1,Y,'27D-30H-32F',(.44,3.52))
    label(ax,valid1,Y,'32F-132E',(.41,2.40))
    label(ax,valid1,Y,'32F-58M',(.84,1.87))
    label(ax,valid1,Y,'32F',(.87,1.54))
    ax.text(.022,2.035,'Target: 2.0',fontsize=17,va='bottom',bbox=dict(facecolor='white',edgecolor='none',pad=2))
    ax.text(.02,1.32,'Other-batch parent: 1.371',fontsize=16,va='top',bbox=dict(facecolor='white',edgecolor='none',pad=2))
    ax.text(.715,3.99,'Retention ≥0.70',fontsize=17,va='top')
    setup(ax,y='+1 ratio\n(c.388 GCG / c.871 GCA)')
    handles=[Line2D([],[],marker=THEME.style(f'Batch: {n} substitution'+('s' if n!=1 else ''))['marker'],
                    color='none',markerfacecolor=THEME.style(f'Batch: {n} substitution'+('s' if n!=1 else ''))['color'],
                    markeredgecolor=C['ink'],markersize=9,label=f'{n} substitution'+('s' if n!=1 else '')) for n in (1,2,3)]
    handles.append(Line2D([],[],color=C['muted'],ls='--',label='Pareto front'))
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.54,.04),ncol=2,columnspacing=2,handlelength=1.6)
    excl1 = combo[combo[Y].isna()].copy();excl1['reason']='Undefined +1 ratio: c.871 denominator recorded as undetected/zero; not plotted.'
    save(fig,'N1_combinatorial_pareto',
         '# N1. Combinatorial-batch ratio–retention trade-off\n\n'
         'The supplied batch contains 48 constructs, including the single-substitution comparator 32F. Each plotted point is one construct-level summary; 36 have a defined +1 ratio. Twelve rows have an undefined ratio because c.871 is recorded as undetected/zero and are omitted from the scatter, not imputed as zero. Point shape distinguishes one, two and three substitutions; the orange star identifies 27T-30H-58M. No replicate-level uncertainty was supplied, so no error bars or significance tests are shown.\n\n'
         'The dashed Pareto front joins six non-dominated constructs, maximizing both activity retention and +1 ratio. The star has ratio 2.156 and retention 0.773 in this CSV and is the only construct with ratio ≥2.0 and retention ≥0.70; among constructs above this retention floor, the next-highest ratio is 1.851. The shaded region marks these thresholds. Activity retention is c.388 editing relative to the same-batch parent; it is not a purified-enzyme activity measurement. The same-batch parent has ratio 1.192 and retention 1.000. The dotted 1.371 line is the rounded parent level from the separate single-mutant batch, included only as the requested contextual reference. It does not establish cross-batch comparability. The optional other-batch single-mutant point cloud is omitted. The values in this figure are unchanged from its source; the separate N2/N3 tables report retention 0.772 for the earlier triple record.',
         'Scatter of 36 defined construct ratios against activity retention. An orange star marks 27T-30H-58M at 0.773 retention and 2.156 ratio, the only point in the upper-right threshold region. Six points form the Pareto front. Twelve undefined ratios are not plotted.',
         {'plotted-data':valid1,'pareto-front':front1,'exclusions':excl1},
         {'x':X,'y':Y,'pareto':'Both axes maximized; strict dominance; recomputed and matched to supplied flags',
          'reference_lines':{'retention_floor':.7,'target_ratio':2,'other_batch_parent_ratio':1.371},
          'same_batch_parent_ratio':1.192,'optional_background':'Entire single-mutant background omitted, not selectively filtered.'})

    # N2: Ranks alone; supplementary row is an unavailable rank, not an observation at zero.
    fig=plt.figure(figsize=(12,7.5)); ax=fig.add_axes([.37,.30,.58,.64])
    ax.set(xlim=(0,39),ylim=(-.6,2.6),xticks=[1,10,20,30,36])
    for yi, idx in [(2,0),(0,2)]:
        row=triple.iloc[idx];n=int(row.n_constructs_in_batch);rank=int(row.rank_by_ROF_within_batch)
        ax.plot([1,n],[yi,yi],color=C['line'],lw=4,zorder=1)
        ax.plot([1,n],[yi,yi],ls='none',marker='|',color=C['muted'],markersize=11)
        ax.scatter([rank],[yi],marker='*',s=450,c=C['orange500'],edgecolors=C['ink'],linewidths=.65,zorder=4)
        ax.text(rank+.8,yi+.24,f'{rank} / {n}',fontsize=22,va='center')
    ax.text(1,1.12,'Rank unavailable',fontsize=20,va='center')
    ax.text(1,.83,'132E variant only; triple well failed',fontsize=16,va='center')
    ax.set_yticks([2,1,0],['Combinatorial\n27T-30H-58M','Supplementary\n27T-30H-58M-132E','Third batch\n27T-30H-58M'])
    ax.tick_params(axis='y',length=0,pad=14,labelsize=18)
    ax.spines['left'].set_visible(False)
    ax.set_xlabel('Within-batch ROF rank (1 = highest)',labelpad=15)
    fig.text(.08,.13,'Third batch: different library background.',fontsize=18)
    fig.text(.08,.075,'Ranks describe separate panels, not cross-batch effect sizes.',fontsize=18)
    save(fig,'N2_within_batch_rank',
         '# N2. Within-batch position of the triple and its supplementary variant\n\n'
         'Stars locate 27T-30H-58M by the supplied within-batch ROF rank: 14 of 36 ratio-defined constructs in the combinatorial batch and 3 of 25 mutant constructs in the third batch. Horizontal tracks span ranks 1 to the relevant panel size; they are not uncertainty intervals. The supplementary row has no rank and no data marker: its measured entry is the different construct 27T-30H-58M-132E, while the unmodified triple well failed. The supplied supplementary panel size is 37 groups, including unavailable/failed entries, and is not used as a rank denominator.\n\n'
         'The third batch has a different library background. Ranks describe the composition of each separate candidate panel and are not a quantitative cross-batch effect size or proof of replication. No cross-batch absolute-ratio chart, ROF effect-size comparison or statistical test is shown. ROF is each construct ratio divided by its own batch-parent ratio. All three source records, including the differing construct identity, missing ranks and raw values, are retained in the accompanying CSV and table. The source table gives earlier retention 0.772, whereas the N1 source gives 0.773; each is preserved without reconciliation.',
         'Two orange stars show within-batch ranks: 14 out of 36 in the combinatorial batch and 3 out of 25 in the third batch. The supplementary row is marked rank unavailable and identifies the 132E variant. The third-batch background differs.',
         {'source-records':triple},
         {'x':'rank_by_ROF_within_batch','tracks':'1 to n_constructs_in_batch; not an error interval',
          'unavailable_rank':'Supplementary row is text only; no zero, no inferred rank',
          'cross_batch':'No comparison of absolute ratios or ROF effect size'})

    # N3: Designed batch and the five source entries, keeping invalid data explicit.
    fig=plt.figure(figsize=(12,17)); ax=fig.add_axes([.14,.59,.80,.31]); bx=fig.add_axes([.14,.14,.80,.29])
    ax.set(xlim=(0,1.02),ylim=(.75,2.72),xticks=np.arange(0,1.01,.2),yticks=[1,1.5,2,2.5]);lines(ax,.7)
    handles=[]
    for group in ['A replication','B new single substitutions','C new combinations','D control variants','E relaxed / anomalous','not in candidate list']:
        s=THEME.style(group);q=valid3[valid3.design_group_label_en==group]
        point(ax,q,R,s['color'],s['marker'],115)
        short={'A replication':'A  Replication','B new single substitutions':'B  New singles','C new combinations':'C  New combinations','D control variants':'D  Controls','E relaxed / anomalous':'E  Relaxed / anomalous','not in candidate list':'Outside candidate list'}[group]
        handles.append(Line2D([],[],marker=s['marker'],color='none',markerfacecolor=s['color'],markeredgecolor=C['ink'],markersize=9,label=short))
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,.992),ncol=2,columnspacing=2.4,fontsize=18)
    label(ax,valid3,R,'25E-30H-58M-132D',(.025,2.59),text='25E-30H-58M-132D')
    label(ax,valid3,R,'130G-32F',(.55,2.48))
    label(ax,valid3,R,'27T-30H-58M-132E',(.36,2.14),text='27T-30H-58M-132E')
    label(ax,valid3,R,'25E-30H-58M-132E',(.75,1.80),text='25E-30H-\n58M-132E')
    ax.text(.015,1.025,'Same-batch parent',fontsize=17,va='bottom')
    setup(ax)
    fig.text(.055,.912,'A',fontsize=26)
    fig.text(.14,.492,'27T-30H-58M: failed well, excluded',color=RED,fontsize=19)
    fig.text(.14,.469,'26N-31G: ratio undefined; retention unavailable',color=C['muted'],fontsize=18)
    fig.text(.055,.442,'B',fontsize=26)
    positions=[0,1.3,3,4.3,6]
    colors=[C['orange500'],C['teal600'],C['indigo700'],C['teal600'],'white']
    for i,(_,row) in enumerate(pair.iterrows()):
        failed=bool(row.excluded_failed_well)
        bx.bar(positions[i],row[X],width=.76,color=colors[i],edgecolor=RED if failed else C['ink'],
               linewidth=1.5,hatch='///' if failed else None,zorder=3)
        bx.text(positions[i],row[X]+.028,str(row[X]),ha='center',va='bottom',fontsize=19,color=RED if failed else C['ink'])
    bx.set(xlim=(-.65,6.65),ylim=(0,1.03),yticks=np.arange(0,1.01,.2))
    bx.axhline(.7,color=C['teal600'],ls='--',lw=1.5,zorder=2)
    bx.text(5.85,.725,'0.70',fontsize=17,ha='center')
    bx.set_xticks(positions,['27T-30H-\n58M\nEarlier batch','27T-30H-\n58M-132E\nThis batch','25E-30H-\n58M-132D\nThis batch','25E-30H-\n58M-132E\nThis batch','27T-30H-\n58M\nThis batch'],fontsize=17)
    bx.set_ylabel('Activity retention\n(c.388 / same-batch parent)',labelpad=12)
    bx.tick_params(axis='x',length=0,pad=10)
    bx.text(6,.27,'Failed well,\nexcluded',color=RED,ha='center',va='center',fontsize=18)
    fig.text(.14,.055,'First two bars differ by 132E and batch.',fontsize=18)
    fig.text(.14,.031,'Hatched bar is an invalid record, not an activity result.',fontsize=18,color=RED)
    exc3=design[~design.ratio_defined | design.excluded_failed_well].copy()
    exc3['reason']=np.where(exc3.excluded_failed_well,'Failed well; all values invalid for interpretation','Undefined ratio and unavailable retention')
    save(fig,'N3_designed_batch',
         '# N3. Designed-batch summaries and position-132 comparisons\n\n'
         '**A.** Of 37 source groups, 35 valid, ratio-defined construct summaries are plotted by design category. ROF is the +1 ratio divided by the same-batch parent ratio; reference lines mark ROF 1.00 and retention 0.70. 27T-30H-58M is a failed well and is listed outside the axes, not shown as a low-activity data point. 26N-31G has an undefined ratio and no retention value and is also listed outside the axes.\n\n'
         '**B.** The five entries follow the supplied bar order. Valid activity-retention values are 0.772, 0.6727, 0.3398 and 0.7517. The first bar is the triple from the earlier combinatorial batch; the second is the different 132E-containing construct from the designed batch. They share a three-mutation core but differ by both construct and batch and are not repeated measurements of an identical construct. The third and fourth bars are 25E-30H-58M-132D and 25E-30H-58M-132E in the same designed batch. The fifth bar is an explicitly invalid failed-well source record (0.0789), shown only as a white, red-hatched ghost bar for provenance; it is excluded from scientific interpretation. No uncertainty intervals or tests are inferred from summary data. All bar heights are the exact supplied values; the earlier triple value differs from the separate N1 file (0.773).\n\n'
         'These observations support a within-batch descriptive comparison of the 132D and 132E variants, not an estimate of purified-enzyme activity or a statistically demonstrated replication of the triple.',
         'Panel A plots 35 valid designed-batch summaries, colored and shaped by six design categories; failed and undefined rows are identified outside the axes. Panel B shows four valid retention bars and one invalid hatched failed-well record. The first two valid bars differ by 132E and by batch.',
         {'panel-A-plotted-data':valid3,'panel-B-source-records':pair,'exclusions':exc3},
         {'panel_A':{'x':X,'y':R,'n_valid':35,'n_source':37,'floor':.7,'parent_rof':1},
          'panel_B':{'y':X,'order':'bar_order','n_valid':4,'n_invalid_ghost':1,
                     'ghost_interpretation':'Source provenance only; all failed-well values are invalid results.'}})

    # N4: Three panels, all compared only within the third batch.
    fig=plt.figure(figsize=(12,23)); ax=fig.add_axes([.14,.70,.80,.24]); bx=fig.add_axes([.14,.395,.80,.235]); cx=fig.add_axes([.14,.085,.80,.24])
    for q,m,col in [('single','o',C['indigo700']),('combo','^',C['indigo500'])]:
        point(ax,valid4[(valid4.group_type==q)&(valid4.construct!=TRIPLE)],R,col,m,100)
    ax.plot(front4[X],front4[R],ls='--',color=C['muted'],lw=1.8,zorder=2)
    point(ax,valid4[valid4.construct==TRIPLE],R,C['orange500'],'*',580)
    ax.set(xlim=(.58,1.07),ylim=(.985,1.305),xticks=[.6,.7,.8,.9,1.0],yticks=[1,1.1,1.2,1.3]);lines(ax,.95)
    label(ax,valid4,R,TRIPLE,(.805,1.287),emphasis=True,text=TRIPLE+'\nROF 1.2185 | retention 0.9799')
    label(ax,valid4,R,'27I',(.67,1.274))
    label(ax,valid4,R,'27D-30H',(.665,1.237))
    label(ax,valid4,R,'30H-58M',(.865,1.173))
    label(ax,valid4,R,'132E',(.95,1.09))
    label(ax,valid4,R,'25F',(1.023,1.014))
    setup(ax)
    fig.text(.055,.951,'A',fontsize=26)
    fig.legend(handles=[Line2D([],[],marker='o',color='none',markerfacecolor=C['indigo700'],markeredgecolor=C['ink'],label='Single substitution',markersize=9),
                        Line2D([],[],marker='^',color='none',markerfacecolor=C['indigo500'],markeredgecolor=C['ink'],label='Combination',markersize=9),
                        Line2D([],[],ls='--',color=C['muted'],label='Pareto front')],
               loc='upper center',bbox_to_anchor=(.54,.985),ncol=3,fontsize=17,columnspacing=1.1,handlelength=1.5)
    ax.text(.596,1.004,'Same-batch parent',fontsize=16,va='bottom')
    ax.text(.953,1.007,'0.95',fontsize=16,va='bottom',color=C['teal600'])
    low=sat[sat[R]<1.13];high=sat[sat[R]>=1.13]
    point(bx,low,R,C['indigo700'],'o',115);point(bx,high,R,C['teal600'],'D',135)
    bx.set(xlim=(.71,1.06),ylim=(.985,1.305),xticks=[.75,.85,.95,1.05],yticks=[1,1.1,1.2,1.3]);lines(bx,.9)
    pos={'27I':(.76,1.273),'27V':(.817,1.172),'27E':(.817,1.134),'27Q':(.905,1.074),
         '27T':(.918,1.009),'27L':(.982,1.015),'27P':(.930,1.107),'27D':(.991,1.084),
         '27M':(.986,1.051),'27W':(1.019,1.035)}
    for name,xy in pos.items():label(bx,sat,R,name,xy)
    setup(bx);fig.text(.055,.641,'B',fontsize=26)
    bx.text(.72,1.297,'◆  ROF ≥1.13',fontsize=18,color=C['teal600'],va='top')
    bx.text(.903,1.21,'0.90 retention',fontsize=17,color=C['teal600'])
    # Sort detected values descending then preserve source order for all censored entries.
    sat_c=pd.concat([sat[~sat.C295_not_detected].sort_values('ACA_class_C295_fraction',ascending=False),sat[sat.C295_not_detected]])
    sat_c=sat_c.copy();sat_c['display_order']=np.arange(1,11)
    sat_c['plotted_fraction']=sat_c.ACA_class_C295_fraction.where(~sat_c.C295_not_detected,np.nan)
    sat_c['display_status']=np.where(sat_c.C295_not_detected,'n.d. (<0.05); no quantitative bar','Detected; exact supplied value')
    parent=float(third.loc[third.construct=='PUF12','ACA_class_C295_fraction'].iloc[0])
    for i,(_,row) in enumerate(sat_c.iterrows()):
        if row.C295_not_detected:
            # Censoring annotation deliberately has no numeric marker or bar.
            cx.text(i,.021,'n.d.',ha='center',va='center',fontsize=18,color=C['muted'])
        else:
            cx.bar(i,row.ACA_class_C295_fraction,width=.62,color=C['indigo700'],edgecolor=C['ink'],lw=1.1,zorder=3)
            cx.text(i,row.ACA_class_C295_fraction+.011,str(row.ACA_class_C295_fraction),ha='center',va='bottom',fontsize=17)
    cx.axhline(parent,color=C['muted'],ls='--',lw=1.7)
    cx.axhline(.05,color=C['line'],ls=':',lw=1.5)
    cx.text(9.3,parent+.008,'PUF12 parent: 0.3091',ha='right',va='bottom',fontsize=18)
    cx.text(9.3,.056,'Detection threshold: 0.05',ha='right',va='bottom',fontsize=17,color=C['muted'])
    cx.set(xlim=(-.65,9.65),ylim=(0,.355),yticks=[0,.1,.2,.3])
    cx.set_xticks(range(10),sat_c.construct,fontsize=18)
    cx.set_ylabel('c.295 editing fraction (ACA)',labelpad=12)
    cx.set_xlabel('Position-27 substitution',labelpad=14)
    fig.text(.055,.336,'C',fontsize=26)
    fig.text(.14,.032,'n.d.: both samples below 5% detection threshold; not zero.',fontsize=18)
    save(fig,'N4_third_batch',
         '# N4. Third-batch trade-off and position-27 substitutions\n\n'
         'All three panels use the supplied third-batch summaries. This batch has a different library background from the earlier batches, so interpretation is within this batch only. ROF is the construct +1 ratio divided by the same-batch parent ratio (1.0489). Activity retention is c.388 editing divided by the same-batch parent editing level. Each plotted observation is a construct-level summary, not a replicate-level point; n_samples is preserved in the data (2 for most mutants and 4 for 27D-30H). Replicate type and replicate-level variability were not supplied; no error bars or statistical tests are inferred.\n\n'
         '**A.** Twenty-five mutant constructs are plotted; four reference groups are not mutant observations. A dashed line joins the six non-dominated constructs, recalculated by maximizing both axes. The orange star identifies 27T-30H-58M (ROF 1.2185, retention 0.9799), ranked third by ROF and tenth by retention. It has the highest ROF among constructs retaining at least 0.95 activity and the highest retention among constructs with ROF ≥1.20. Reference lines indicate ROF 1.00 and retention 0.95. The scatter axes are restricted to the complete observed mutant range with padding; no valid mutant points are hidden.\n\n'
         '**B.** Ten single substitutions at position 27 are shown. 27I, 27V and 27E have ROF ≥1.13 and are distinguished by teal diamonds. Reference lines show ROF 1.00 and retention 0.90.\n\n'
         '**C.** c.295 ACA-class editing for the same ten substitutions. Three detected values are plotted as bars (27M 0.111, 27L 0.09 and 27I 0.0823). For seven substitutions, C295_not_detected is TRUE, meaning both samples are below the supplied 5% detection threshold. Their source zeros are preserved in the source column but are displayed only as n.d., with no zero-height bars or inferred values. n.d. is not editing efficiency zero. The dashed parent line is 0.3091; the dotted line is the 0.05 detection threshold. Detected values are ordered from high to low, followed by undetected entries in source order. No hypothesis test is reported.',
         'Three vertically arranged panels. A shows all 25 mutant construct summaries in the third batch and highlights the triple with an orange star on the Pareto front. B shows ten position-27 substitutions, highlighting 27I, 27V and 27E. C shows three measured c.295 editing bars and seven n.d. labels below the 5% detection threshold, with a parent reference at 0.3091.',
         {'panel-A-plotted-data':valid4,'panel-A-pareto-front':front4,'panel-B-plotted-data':sat,'panel-C-display-data':sat_c,
          'reference-groups':third[third.is_reference_group]},
         {'panel_A':{'x':X,'y':R,'floor':.95,'n':25,'pareto':'Recomputed, strict dominance, both axes maximized'},
          'panel_B':{'n':10,'floor':.9,'highlight_rof_min':1.13},
          'panel_C':{'n_detected':3,'n_censored':7,'censor_threshold':.05,'parent':parent,
                     'numeric_bars':'Detected values only; censored source zeros have no bar'},
          'reference_groups':'All four reference rows retained separately; PUF12 supplies reference levels'})

# A compact exact-value table accompanies N2; it is not a cross-batch metric plot.
lines_table=['# N2 source records (values reproduced exactly)','','Absolute ratios must not be compared across different library backgrounds. The supplementary row is a different construct.','',
             '| Batch | Construct | +1 ratio | Retention | Parent ratio | ROF | ROF rank | Retention rank | Source panel size |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|']
with (ROOT/'input/data/triple_record_across_batches.csv').open(encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        lines_table.append('| '+' | '.join(row[k] or 'Unavailable' for k in ['batch','construct','on_target_ratio',X,'same_batch_parent_ratio','ROF','rank_by_ROF_within_batch','rank_by_retention_within_batch','n_constructs_in_batch'])+' |')
lines_table += ['', 'The denominators differ: combinatorial 36 ratio-defined constructs; supplementary 37 source groups (rank unavailable); third batch 25 mutants. No pooled estimate is made.',
                'Third-batch library background differs. Supplementary measurements are for the 132E variant; the triple well failed.']
(OUT/'N2_within_batch_rank/source-table.md').write_text('\n'.join(lines_table)+'\n')
(OUT/'audit.json').write_text(json.dumps({'hash_checks':12,'figures':AUDITS,'pareto_N1':front1.construct.tolist(),'pareto_N4':front4.construct.tolist()},indent=2)+'\n')
(OUT/'manifest.json').write_text(json.dumps(RECORDS,indent=2)+'\n')
print(json.dumps({'output':str(OUT),'figures':len(RECORDS),'hash_checks':12,'audit':AUDITS},indent=2))
