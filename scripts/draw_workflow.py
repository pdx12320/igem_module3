"""Draw the ORCA-styled conceptual workflow as editable SVG, PDF and PNG.

Uses ordinary vector shapes/text plus one disclosed illustrative bitmap.
No data points, structural coordinates or experimental images are synthesized.
"""
from pathlib import Path
import argparse, hashlib, json, platform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True); a=p.parse_args()
    if a.output.exists(): raise FileExistsError(a.output)
    a.output.mkdir(parents=True)
    plt.rcParams.update({'font.family':['Futura','Arial','DejaVu Sans'], 'svg.fonttype':'none', 'pdf.fonttype':42})
    ink='#171536'; indigo='#2E267C'; pale='#E9E8FF'; orange='#E89B3C'; teal='#27877F'
    fig,ax=plt.subplots(figsize=(12,7.4)); fig.subplots_adjust(0,0,1,1)
    ax.set(xlim=(0,12),ylim=(0,7.4));ax.set_axis_off()
    nodes=[(2,5.95,'Compare RNA','+1 base and context',indigo),
           (6,5.95,'Audit models','Contacts and controls',indigo),
           (10,5.95,'Screen mutants','Ratio and retention',teal),
           (10,1.45,'Combine hits','Joint objectives',teal),
           (6,1.45,'Test each batch','Normalize to parent',teal),
           (2,1.45,'Update designs','Keep, revise, retest',orange)]
    # Clockwise logical loop; no dated chronology or claimed causal mechanism.
    for start,end in [((3.52,5.95),(4.47,5.95)),((7.52,5.95),(8.47,5.95)),
                      ((10,5.05),(10,2.36)),((8.48,1.45),(7.53,1.45)),
                      ((4.48,1.45),(3.53,1.45)),((2,2.35),(2,5.04))]:
        ax.add_patch(FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=23,
                                    linewidth=2.3,color=indigo,zorder=1))
    for i,(x,y,title,sub,color) in enumerate(nodes,1):
        ax.add_patch(FancyBboxPatch((x-1.48,y-.83),2.96,1.66,boxstyle='round,pad=0.015,rounding_size=.16',
                                    facecolor=pale if color==indigo else '#F5F8F8' if color==teal else '#FFF6E8',
                                    edgecolor=color,linewidth=1.5,zorder=2))
        ax.text(x,y+.5,f'{i:02}',ha='center',va='center',fontsize=13,color=color)
        ax.text(x,y+.07,title,ha='center',va='center',fontsize=20,color=ink,fontweight='medium')
        ax.text(x,y-.4,sub,ha='center',va='center',fontsize=14,color=ink)
    asset=ROOT/'wiki/figures/workflow/assets/protein-rna.png'
    im=Image.open(asset)
    ax.imshow(im,extent=(4.35,7.65,2.72,4.92),aspect='auto',zorder=0)
    ax.text(6,2.72,'APOBEC–RNA editing',fontsize=16,ha='center',va='top',color=ink)
    for ext in ['svg','pdf','png']:
        fig.savefig(a.output/f'workflow.{ext}',dpi=240,facecolor='white')
    fig.canvas.draw()
    bounds=fig.bbox; renderer=fig.canvas.get_renderer()
    outside=[t.get_text() for t in ax.texts if not bounds.contains(*t.get_window_extent(renderer).get_points()[0])
             or not bounds.contains(*t.get_window_extent(renderer).get_points()[1])]
    assert not outside, outside
    manifest={'type':'conceptual schematic; not a structure or experimental image','style':'ORCA palette and Futura typography',
              'composition':'Matplotlib vector shapes, arrows and SVG text; user requested no native PowerPoint',
              'python':platform.python_version(),'matplotlib':matplotlib.__version__,
              'png_pixels':list(Image.open(a.output/'workflow.png').size),
              'editable_svg_text':True,'illustrative_asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),
              'text_outside_canvas':outside,'biological_data_encoded':False}
    (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
