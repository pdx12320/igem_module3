# Final checks

Final figures were inspected at 960 px display width. PNG previews and all four PDF page renders were opened and reviewed. All four SVG renders were inspected in the comparison sheet and compared numerically with their corresponding PNGs. PDF rendering: Poppler `pdftoppm`. SVG rendering: sharp/librsvg. No PowerPoint rendering was used or needed.

- All 12 input checksums match. The original ZIP and the extracted input files were not modified.
- N1: 36 plotted construct summaries, 12 explicitly recorded undefined-ratio omissions, 6 recomputed Pareto points matching the supplied flags. Exactly one joint-threshold construct. The single-substitution comparator is preserved. The one rectangular patch in the artist audit is the threshold-region shading, not a data bar.
- N2: 2 rank observations, 1 text-only unavailable-rank row; third-batch ranks independently match the third-batch table. Panel sizes and different construct identity are explicit.
- N3A: 35 valid points from 37 input groups. Two unavailable/failed rows are not assigned artificial coordinates. N3B: four valid bars plus one expressly invalid, hatched provenance bar. The first two bars are not called identical-construct repeats.
- N4A: 25 mutant observations, 6 recalculated Pareto points; four reference groups retained separately. N4B: 10 position-27 summaries. N4C: 3 numeric bars and 7 censored text annotations, with no fake zero bars.
- All four PNGs are 3600 px wide at 300 dpi. Final canvas checks found no text outside the figure bounds. Actual chart labels, legend placement, reference lines and source-value annotations were visually reviewed.
- Draft N1 had an axis-label/legend collision and N3 had tight label spacing. These were fixed, regenerated and checked in the final exports.
- PDFs each have one page, the expected physical canvas size, embedded Futura Medium and no raster images. N4 additionally embeds Arial Unicode MS for a diamond glyph.
- SVGs contain vector paths and no raster images; text is outlined. Render differences against PNGs are minor antialiasing/backend differences (mean absolute RGB difference ~0.8–1.5 / 255 for SVG, ~1.7–3.1 / 255 for PDF). These comparisons supplement, not replace, visual review.
- No inferred error bars, hypothesis tests, synthetic values or replicate-level measurements were introduced.

Numerical records are in `../figures/audit.json`, `pdf-metadata.json` and `render-comparison.json`. Source-table differences and presentation decisions are listed in `../README.md`.
