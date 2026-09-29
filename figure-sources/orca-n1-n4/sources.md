# Source and evidence mapping

The user asked to draw the figures in the supplied ZIP. Its README and prompt were treated as figure specifications and source context, not as independent instructions to perform unrelated actions or to accept every scientific claim without checking.

- Primary input: `APOBEC_组合突变与三元组_绘图数据包.zip`, supplied from the user's local WeChat file directory. Extracted byte-preserving to `input/`. All 12 checksums in the package were verified, including six CSVs and four reference images.
- N1: `combo_batch_ratio_vs_retention.csv`, all 48 rows. Defined ratio subset has 36 rows. Recomputed six-member Pareto front exactly matches the flags. Unique joint threshold membership (ratio ≥2.0, retention ≥0.70) independently checked. Source table contains one single-substitution comparator, 32F.
- N2: `triple_record_across_batches.csv`, all three rows, with missing supplementary ranks preserved and different supplementary construct identity explicit. Third-batch rank 3 by ROF and 10 by retention verified against the 25-mutant source table. Ranks are descriptive, not evidence of a comparable quantitative cross-batch effect.
- N3: `designed_batch_groups.csv` (37 rows) and `designed_batch_groupD_pairing.csv` (5 rows). Failure status is supplied metadata, not newly diagnosed here. The asserted reason for the original failure classification is not independently validated. Failed-well values are not valid activity results.
- N4: `third_batch_all_groups.csv`, 29 rows (25 mutants and four references). Ten position-27 singles and seven below-detection statuses verified. The six-member Pareto front is recalculated on all 25 mutants, with both axes maximized. Censoring meaning and the 5% threshold are supplied package metadata.
- Optional `single_mutant_background.csv`: inspected but no point cloud used. The provided contextual parent reference is retained and explicitly marked as another batch.
- Local style provenance: prior `outputs/scientific-figures/apobec-drylab-20260927/orca-figure-style.json`, currently read and copied; the ORCA scientific-illustrator plugin supplies the portable `orca_plot.py` and base style.

No new external biological claim or mechanistic inference was introduced. No web research was needed for this data-to-figure task. The results are descriptive visualizations of the supplied summaries, not reanalysis of replicate-level measurements.
