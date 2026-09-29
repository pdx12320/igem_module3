# APOBEC Dry Lab figure captions

## Figure 2. Contact-probability deviation

Panel A shows three contact-probability (CP) deviation descriptors for all 14 constructs; the shaded interval is the supplied ±3 SD reference band. Panel B shows the 10 constructs with reported activity retention against protein–target-C deviation (Pearson r = -0.151). Four missing activity values are excluded only from panel B and are not imputed. Each point/bar is a supplied construct-level summary; no error bars or significance tests are inferred. The association is descriptive and does not establish predictive validity.

## Figure 3. Per-residue ΔΔCP

ΔΔCP is shown for the 22 residues with the largest maximum absolute change across the 21 mutant constructs, selected from the supplied 199-residue table. Rows are sorted by sequence position. The color scale is symmetric about zero (±0.3950); only cells with |ΔΔCP| ≥0.05 are labelled, preserving supplied decimal precision. The supplied task specification reports an independent WT rerun maximum |ΔΔCP| of 0.0265; that rerun is not included in this plotting package. Near-zero values indicate little change in this descriptor, rather than evidence of unchanged function. The full-resolution SVG/PDF is recommended for cell labels.

## Figure 4. Negative-control diagnosis

Panel A shows reported target C4N4–E72 distances for 27 control constructs and two WT references (29 rows). Functional class determines the bar fill; the dashed line is the WT–GCG value in this table, 2.599 Å. E72A has no supplied distance and is labelled “Distance unavailable”; a missing value does not establish that no model exists. E72A and N57A are designed inactive controls with no reported activity measurement and are distinguished from measured inactive constructs by an unfilled, hatched style. Panel B shows three CP deviation descriptors, with an independent descriptor legend and a ±3 SD band. Both panels use horizontal bars to keep every construct name readable. No missing value is converted to zero.

## Figure 5. PCA and distance from WT

Panel A shows the supplied PC1 and PC2 coordinates for 28 controls; seven specified constructs are labelled. Panel B ranks the supplied Mahalanobis distances to WT in ascending order, with the supplied WT-null 95th percentile of 1.57. Functional categories are encoded consistently across panels; designed but unmeasured E72A and N57A are separate from measured inactive controls. The WT (GCA substrate) category is mapped to the shared Wild-type reference color. Seven of 11 constructs labelled Active exceed 1.57, showing that exceeding this reference does not identify inactivity. PCA coordinates and distances are supplied results and are not recomputed here.

## Figure 6. Protein-only models

Panel A compares supplied protein-only Mahalanobis distances for 10 constructs using three internal-contact feature sets. Panel B shows the three reported dead/active classification accuracies and the supplied 0.50 chance reference. The plotting package does not specify the classification evaluation design, labelled sample denominator, or uncertainty; these bars reproduce the supplied summaries and must not be interpreted as independently validated generalization performance. No new classification analysis or error bars are added.

## Figure 7. Complex versus protein only

Ten constructs are compared using the supplied distances under complex-with-RNA and protein-only modelling conditions, sorted by protein-only distance. The 1.57 reference is reproduced from the task specification. Annotations for T31D and E72A are the supplied protein-only/complex distance ratios expressed as percentages. E72A is the only construct in this set with a larger protein-only distance. These are descriptive comparisons of model-derived distances; the ratios do not quantify a causal fraction of structural deviation explained by RNA binding.

## Figure 8. Single-site saturation

Each point represents one of 101 plotted single mutants, using the supplied construct-level summaries. Of 102 mutants, 31Y is excluded because its GCA editing was undetected and its ratio is undefined; the same-batch parent is shown as a vertical reference line (1.3707, displayed as 1.371). K30H is starred: it has the highest +1 ratio among mutants retaining at least 70% activity (ratio 1.71; retention 0.84). Three mutants exceed a ratio of 2.0 (130G, 60Q and 31G) but retain only 0.32, 0.17 and 0.13 of parent activity. No mutant meets both ratio ≥2.0 and retention ≥0.70. Retention is a cellular editing measure relative to the parent, not purified enzyme activity. No uncertainty estimates or significance tests are shown.

## Figure 9. Targeting ratio

Both panels contain 41 mutant constructs with defined targeting ratios, after excluding one parent and nine mutants with a zero denominator. Panel A relates the ratio to on-target editing; shaded activity strata are 10–20% (n=13, median 2.528, shown as 2.53) and 35–60% (n=14, median 1.203, shown as 1.20). Panel B relates the ratio to summed non-GCG editing and includes a descriptive ordinary least-squares fit, Pearson r = -0.390 and Spearman ρ = -0.557. Correlations use complete pairs and average ranks for ties. A ratio plotted against its own denominator has mathematical coupling; the association alone does not establish a causal detection-floor mechanism. No undefined ratio is plotted as zero and no confidence interval is inferred.

## Figure 10. Next-cycle candidates

Panel A shows the 61 candidate-list entries assigned to groups A–E (18, 6, 12, 5 and 20). Panel B shows the priority composition using the supplied 11 priority categories and specified stacking order. Colors encode broad priority tiers and hatches distinguish subcategories. Counts were cross-checked against all 61 raw candidate-list entries; entries are counted as supplied, without deduplication. These are proposed next-cycle candidates, not completed experiments or measured outcomes.

## Figure 11. Retrospective AiCE filter

Panel A counts positions whose most frequent amino acid meets each sampling-frequency threshold; all 40 supplied curve points were verified against the 199-position frequency table. The task specification identifies 48 ProteinMPNN samples at temperature 0.3 and supplies thresholds γ=0.5 for coil and β=0.8 for structured regions. Panel B reproduces the supplied frequencies for H29P, K30T, N57D and A59P; all four are annotated as coil and exceed their applicable threshold of 0.5. Display precision follows the supplied tables. This is a retrospective filter comparison, not prospective validation of activity or specificity.
