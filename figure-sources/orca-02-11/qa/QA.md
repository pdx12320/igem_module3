# QA · 2026-09-27

- 10/10 final PNG figures inspected at 1200 px preview width, including all panel layouts, legends and annotations. Main text targets approximately 18–22 CSS px at 960 px figure width; heatmap cell values are a recorded smaller-font exception and require zoom for detailed reading.
- PDF pages rendered with PyMuPDF and visually reviewed. SVG files rendered with Sharp/librsvg; functional hatches and priority hatches verified. PyMuPDF SVG rendering was not used for approval because it does not correctly render these SVG patterns.
- Fixed clipping, overlapping PCA labels, crowded candidate labels and heatmap annotations in working drafts. Final visible text bounds check: no out-of-canvas text on any figure.
- Figure 3 changed from raster image cells to vector mesh cells; matrix values and order are unchanged. All PNG, PDF and SVG formats agree in the final rendering.
- 16/16 original CSV snapshot SHA-256 values match the received data dictionary. Original package untouched.
- Plotting exclusions are explicit: four missing activities in Figure 2B; unavailable E72A distance in Figure 4A (row retained); 31Y and parent scatter exclusion in Figure 8 (parent represented by line); one parent and nine undefined ratios in Figure 9.
- Matplotlib-generated PDF: one page per figure, 15.8 in wide; PNG: 4740 px wide at 300 dpi. SVG: text as outlines. Primary font Futura Medium; math subscripts use DejaVu Sans and certain Greek symbols use Arial Unicode MS, as recorded by the PDF font inspection.
- No raw repeat-level data, error bars, uncertainty intervals or significance marks were fabricated. Supplied PCA, model distances and classification scores are plotted without refitting.
- Existing Figures 1 and 12–14 were not altered. No Wiki publishing or Word/PPTX editing performed.
