# Workflow figure

## Design plan

Six stages form a clockwise logical loop: compare RNA → audit models → screen mutants → combine hits → test each batch → update designs. The layout connects evidence to the next design decision. It does not imply a dated chronology or a proven molecular mechanism.

ORCA styling uses white space, Futura typography, ink `#171536`, indigo `#2E267C`, lavender `#E9E8FF`, teal `#27877F` and orange `#E89B3C`. Captions stay outside the canvas. The six nodes and their arrows are vector objects; SVG text remains text. No PowerPoint dependency is used, following the user's later preference.

## Files

- [PNG, 2880 ×1776](rendered/workflow.png)
- [Editable SVG](rendered/workflow.svg)
- [PDF](rendered/workflow.pdf): mixed vector and bitmap, not a purely vector illustration
- [Export metadata](rendered/manifest.json)
- [Python source](../../../scripts/draw_workflow.py)
- [Standalone protein–RNA asset](assets/protein-rna.png)

## Caption and alt text

**Caption:** The Module 3 workflow links substrate-context comparisons, model auditing, single-mutant screening, combination selection, within-batch testing and revised designs. The central protein–RNA image is a conceptual illustration, not an experimentally resolved structure.

**Alt text:** Six rounded boxes form a clockwise cycle. The top row compares RNA, audits models and screens mutants. The bottom row, read right to left, combines hits, tests each batch and updates designs. A stylized APOBEC–RNA complex sits inside the loop.

## Asset-generation prompt

The asset was generated independently before the composition method changed from PowerPoint to SVG. The original prompt was:

> Use case: scientific-educational. Asset type: a single reusable scientific illustration component for an iGEM Wiki workflow assembled in Microsoft PowerPoint. Primary request: one simplified globular protein bound to a short single-stranded RNA, shown as a conceptual molecular complex, not an experimentally resolved structure. Protein is one softly lobed silhouette with a shallow cleft; RNA is one short curved single strand with a few simple base tabs, one warm orange tab near the cleft. Flat vector-look scientific illustration, crisp consistent indigo #2E267C outlines, restrained solid lavender #9D9CF4 and #E9E8FF protein fills, teal #27877F RNA and orange #E89B3C focal base. One isolated component, fully visible, compact horizontal composition with a little padding. Genuinely transparent alpha background. No text, letters, numbers, arrows, connectors, legends, frames, watermarks, checkerboard, white rectangular backdrop, shadows, photorealism, 3D or gradients. Original illustration; scientific simplification, no atomistic or sequence-specific claims.

Generated asset: RGBA PNG, 1536 ×1024 pixels; retained without changing its pixel data. Tool: OpenAI image generation. No model-version identifier was returned. Asset hash is recorded in the export metadata.

## Verification

The actual PNG was inspected; labels, arrow directions and overall composition were checked. The actual PDF was rendered with Poppler and inspected separately for font and transparency differences. The SVG retains text elements. The export is an illustrative workflow, with no encoded experimental numerical values.
