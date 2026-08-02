# Prompt ablation study: methods and results

## Methods

We evaluated repeated-run reproducibility of title/abstract screening with GPT 5.6 Terra Medium through Codex CLI (`reasoning.effort=medium`). Each role-record pair was classified five times under an unchanged JSON schema and one-retry policy. A deterministic, stratified 60-record development set and a disjoint 60-record sealed holdout were sampled from the search frame after excluding all prior benchmark and canonical-candidate records. No expert-gold labels were used in this experiment; the estimand was reproducibility, not screening validity.

Prompt changes were evaluated as pre-specified ablations. Cycle v1.1.0 used a 2x2 design for a multi-omics decision procedure (`M`) and a singleton design anchor (`D`). Cycle v1.2.0 tested closed scope tables (`S`) and mutually exclusive causal-basis tables (`C`). Cycle v1.3.0 added analytic-role boundaries for aging terms (`T`). A final two-definition micro-ablation (`R`) was tested under an explicit stop rule. Every experiment definition and prompt was committed before its model runs. The selected `T+C` contract was materialized as `v1.4.0-rc1` and frozen before the holdout was opened.

The primary endpoint was the proportion of records with exact agreement across all five runs for every tracked field required by the pre-specified sequential routing path. Secondary endpoints were agreement for decision-driving fields excluding the descriptive design anchor, repeat-level route agreement, schema validity after retry, field-level agreement, paired gains and losses, exact McNemar tests, and Wilson 95% intervals. Any missing valid repeat counted as failure. The pre-specified acceptance threshold was 100%.

Across all cycles, 3600 repeat responses were planned and 3735 provider attempts were made, including 141 validation or provider-error attempts. Raw responses, retries, prompt hashes, schema hashes, model/runtime metadata, and Git revisions were retained.

## Development results

The v1.0.0 baseline achieved 36/60 exact records (60.0%). The first `M` and `D` factorial did not improve the primary endpoint. The `S+C` arm increased exact agreement to 52/60 (86.7%). The `T+C` arm increased it further to 58/60 (96.7%; Wilson 95% CI 88.6-99.1) and was selected. The final `R+C` micro-ablation decreased exact agreement to 57/60 (95.0%) and was rejected, demonstrating that additional specification did not monotonically improve reproducibility.

## Sealed-holdout results

On the one-shot sealed holdout, baseline exact agreement was 29/60 (48.3%). The frozen RC1 achieved 48/60 (80.0%; Wilson 95% CI 68.2-88.2). Relative to baseline, RC1 produced 21 paired gains and 2 losses (exact McNemar p=6.6e-05). Decision-field exact agreement was 80.0% and repeat-level route agreement was 83.3%.

RC1 therefore improved reproducibility substantially but failed the pre-specified 100% gate and was not activated. The sealed holdout will not be used for subsequent prompt tuning. These results do not establish sensitivity, specificity, or scientific validity against expert judgments; a separate expert-gold benchmark remains required.

## Secondary 120-record regression test

The established 120-record corpus was evaluated as a secondary regression test, not as production and not as an independent sealed holdout. Baseline exact agreement was 86/120 (71.7%), whereas frozen RC1 achieved 100/120 (83.3%; Wilson 95% CI 75.7-88.9). There were 26 paired gains and 12 losses (exact McNemar p=0.0336). Because this corpus had informed the initial instability diagnosis, these results are regression evidence only and do not override the sealed-holdout rejection.
