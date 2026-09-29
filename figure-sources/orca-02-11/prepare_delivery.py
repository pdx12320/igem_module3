from pathlib import Path
import csv, json, hashlib, html, zipfile
import fitz
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
def read(prefix):
    f=next((ROOT/'source-data').glob(prefix+'*.csv'))
    return list(csv.DictReader(f.open(encoding='utf-8-sig')))
def yes(v):return v.lower()=='true'
def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

plots={
2:{'A':read('figure_02'),'B':[r for r in read('figure_02') if r['activity_retention_fraction']]},
3:{'single':sorted(read('figure_03_ddcp'),key=lambda r:int(r['residue_position']))},
4:{'A':[r for r in read('figure_04') if r['target_C4N4_to_E72_distance_A']],'B':read('figure_04')},
5:{'A':read('figure_05'),'B':sorted(read('figure_05'),key=lambda r:float(r['D_M_mahalanobis_to_WT']))},
6:{'A':read('figure_06a'),'B':read('figure_06b')},
7:{'single':sorted(read('figure_07'),key=lambda r:float(r['D_M_protein_only_no_RNA']))},
8:{'single':[r for r in read('figure_08') if not yes(r['is_parent']) and yes(r['plus1_ratio_defined'])]},
9:{k:[r for r in read('figure_09') if not yes(r['is_wildtype_parent']) and yes(r['targeting_ratio_defined'])] for k in ['A','B']},
10:{'A':read('figure_10b'),'B':read('figure_10c')},
11:{'A':read('figure_11b'),'B':read('figure_11c')}}
titles={2:'Contact-probability deviation',3:'Per-residue ΔΔCP',4:'Negative-control diagnosis',5:'PCA and distance from WT',6:'Protein-only models',7:'Complex versus protein only',8:'Single-site saturation',9:'Targeting ratio',10:'Next-cycle candidates',11:'Retrospective AiCE filter'}
parts=[];merged=fitz.open();toc=[];formats=[];caps=[]
for folder in sorted((ROOT/'figures').iterdir()):
    n=int(folder.name.split('_')[1]);stem=folder.name
    for panel,rows in plots[n].items():write_csv(folder/f'plotted-panel-{panel.lower()}.csv',rows)
    pdf=fitz.open(folder/f'{stem}.pdf');merged.insert_pdf(pdf);toc.append([1,f'Figure {n}: {titles[n]}',len(merged)])
    page=pdf[0];page.get_pixmap(matrix=fitz.Matrix(1200/page.rect.width,1200/page.rect.width),alpha=False).save(ROOT/'qa'/f'{stem}_pdf.png')
    manifest=json.loads((folder/'figure-manifest.json').read_text())
    manifest['provenance']['plotted_tables']={k:f'plotted-panel-{k.lower()}.csv' for k in plots[n]}
    manifest['provenance']['panel_row_counts']={k:len(v) for k,v in plots[n].items()}
    manifest['provenance']['render_validation']={'PNG':'Matplotlib Agg; opened and visually checked','PDF':'PyMuPDF render','SVG':'Sharp / librsvg render; hatch patterns checked'}
    (folder/'figure-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    im=Image.open(folder/f'{stem}.png')
    assert im.width==4740 and abs(im.info['dpi'][0]-300)<.01
    assert abs(page.rect.width/72-15.8)<.0001
    formats.append({'figure':n,'png_pixels':im.size,'dpi':im.info['dpi'],'PDF_pages':len(pdf),'PDF_points':list(page.rect),'fonts':[x[3] for x in page.get_fonts()],'SVG_renderer':'librsvg','rows':manifest['provenance']['panel_row_counts']})
    alt=(folder/'alt-text.txt').read_text().strip();caption=(folder/'caption.md').read_text().strip();caps.append(f'## Figure {n}. {titles[n]}\n\n{caption}\n')
    pre='figures/'+stem+'/'+stem
    parts.append(f'<section id="f{n}"><h2>Figure {n} · {html.escape(titles[n])}</h2><div class="downloads"><a href="{pre}.png">PNG · 300 dpi</a><a href="{pre}.svg">SVG · 放大查看</a><a href="{pre}.pdf">PDF</a></div><a href="{pre}.svg"><img loading="lazy" src="{pre}.svg" alt="{html.escape(alt,quote=True)}"></a><details><summary>English caption</summary><p>{html.escape(caption)}</p></details></section>')
merged.set_toc(toc);merged.save(ROOT/'APOBEC_Figures_02–11.pdf',garbage=4,deflate=True)
(ROOT/'captions.md').write_text('# APOBEC Dry Lab figure captions\n\n'+'\n'.join(caps))
(ROOT/'qa'/'format-checks.json').write_text(json.dumps(formats,indent=2)+'\n')
nav=' '.join(f'<a href="#f{n}">{n:02}</a>' for n in range(2,12))
(ROOT/'index.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>APOBEC · ORCA figures</title><style>body{font:17px/1.6 Arial,sans-serif;color:#171536;background:#f8f7fc;margin:0}main{max-width:1040px;margin:auto;padding:36px 24px}h1{font-size:34px;margin-bottom:4px}h2{font-size:23px}nav{position:sticky;top:0;background:#fff;padding:12px;z-index:2;border-bottom:1px solid #d9d7e5}a{color:#2e267c}nav a,.downloads a{display:inline-block;margin-right:22px}section{background:white;padding:22px;margin:28px 0;scroll-margin-top:70px}img{width:100%;height:auto;margin-top:18px}details{border-top:1px solid #d9d7e5;padding-top:12px}summary{cursor:pointer}.lead{color:#6b6880}footer{margin:40px 0}</style><main><h1>APOBEC Dry Lab</h1><p class="lead">Figure 2–11 · ORCA 科研图 · 点击图片查看可放大的 SVG</p><p><a href="APOBEC_Figures_02–11.pdf">全部图 PDF</a>　<a href="captions.md">英文图注合集</a>　<a href="README.md">数据与呈现说明</a></p><nav>'''+nav+'</nav>'+''.join(parts)+'<footer>原始数据数值保持不变。Figure 1、12–14 不属于本次重绘范围。</footer></main></html>')
# Overview for browsing, not for judging final-size label readability.
sheet=Image.new('RGB',(1800,2600),'#F3F2F8');draw=ImageDraw.Draw(sheet)
for i,n in enumerate(range(2,12)):
    tile=Image.new('RGB',(870,500),'white');pic=Image.open(ROOT/'qa'/f'figure_{n:02d}_preview.png');pic.thumbnail((830,450))
    tile.paste(pic,((870-pic.width)//2,40));ImageDraw.Draw(tile).text((15,12),f'Figure {n:02d} | {titles[n]}',fill='#171536')
    sheet.paste(tile,((i%2)*900+15,(i//2)*520+10))
sheet.save(ROOT/'overview.png')
# Re-check copied source bytes against the source specifications.
dictionary=(ROOT/'source-specifications/data_dictionary.md').read_text(encoding='utf-8-sig')
source_results={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT/'source-data').glob('*.csv')}
assert all(h in dictionary for h in source_results.values())
(ROOT/'qa/source-hashes.json').write_text(json.dumps(source_results,indent=2)+'\n')
qa='''# QA · 2026-09-27

- 10/10 final PNG figures inspected at 1200 px preview width, including all panel layouts, legends and annotations. Main text targets approximately 18–22 CSS px at 960 px figure width; heatmap cell values are a recorded smaller-font exception and require zoom for detailed reading.
- PDF pages rendered with PyMuPDF and visually reviewed. SVG files rendered with Sharp/librsvg; functional hatches and priority hatches verified. PyMuPDF SVG rendering was not used for approval because it does not correctly render these SVG patterns.
- Fixed clipping, overlapping PCA labels, crowded candidate labels and heatmap annotations in working drafts. Final visible text bounds check: no out-of-canvas text on any figure.
- Figure 3 changed from raster image cells to vector mesh cells; matrix values and order are unchanged. All PNG, PDF and SVG formats agree in the final rendering.
- 16/16 original CSV snapshot SHA-256 values match the received data dictionary. Original package untouched.
- Plotting exclusions are explicit: four missing activities in Figure 2B; unavailable E72A distance in Figure 4A (row retained); 31Y and parent scatter exclusion in Figure 8 (parent represented by line); one parent and nine undefined ratios in Figure 9.
- Matplotlib-generated PDF: one page per figure, 15.8 in wide; PNG: 4740 px wide at 300 dpi. SVG: text as outlines. Primary font Futura Medium; math subscripts use DejaVu Sans and certain Greek symbols use Arial Unicode MS, as recorded by the PDF font inspection.
- No raw repeat-level data, error bars, uncertainty intervals or significance marks were fabricated. Supplied PCA, model distances and classification scores are plotted without refitting.
- Existing Figures 1 and 12–14 were not altered. No Wiki publishing or Word/PPTX editing performed.
'''
(ROOT/'qa/QA.md').write_text(qa)
print('Prepared ten figures, HTML gallery, merged PDF, per-panel plot tables, captions and QA records.')
