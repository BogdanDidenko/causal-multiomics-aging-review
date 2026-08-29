# Causal Extraction Analysis Plan v0.1.1-rc1

## Objective

Evaluate whether the frozen extraction instrument produces complete, traceable, stable, and expert-valid causal claim records. Stability and validity are reported as separate properties.

## Frozen checkpoint

The first checkpoint contains 15 heterogeneous eligible reports selected before model outputs are inspected. Selection must cover genetic instruments, interventions, perturbations, mediation or directed methods, null or conflicting findings, human and nonhuman systems, and reports with multiple causal claims.

Changing a prompt, schema, codebook, coverage rule, normalization rule, or Python level rule after inspecting checkpoint outputs creates a new suite version. A tuned version is evaluated on a disjoint checkpoint set.

## Discovery-route ablation

For every report, report these counts before adjudication:

- open-discovery candidates;
- dense-coverage candidates;
- exact overlap after deterministic normalization;
- open-only candidates;
- dense-only candidates;
- candidates from each route accepted as final claims;
- candidates from each route excluded for each reason.

The primary coverage statistic is the proportion of final claims nominated by both routes. Dense-only accepted claims quantify the incremental yield of the dense pass. Open-only accepted claims quantify complementary yield. No route is treated as a gold standard.

## Repeated-run stability

For fixed-candidate classification, report:

- five-of-five exact agreement on the normalized decision-driving payload;
- five-of-five agreement on candidate status;
- five-of-five agreement on each criterion-level field;
- five-of-five agreement on Python-derived Level;
- distribution of disagreement patterns, including 4:1, 3:2, and more fragmented outcomes;
- pairwise agreement and Jaccard similarity for set-valued fields;
- schema validity before and after the single technical retry;
- quote-grounding validity;
- technical failure and manual-review rates.

Use record-level and claim-level denominators explicitly. Report Wilson 95% confidence intervals for proportions. Preserve raw numerators and denominators.

## Run-count sensitivity

Recompute the frozen decision rule using the first three repeats and all five repeats. Compare:

- proportion resolved by exact agreement;
- candidate status;
- derived Level;
- manual-review burden;
- false stability against expert labels when available.

The five-run result remains primary. The three-run analysis is a prespecified sensitivity analysis. Seven-run claims are prohibited because only five runs are collected in this release.

## Adjudication analysis

Report the number of reports and candidates entering model adjudication for disagreement, split, merge, duplicate, source inadequacy, invalid quote, schema failure, and technical failure. Report five-run adjudicator agreement and the number remaining for human adjudication.

Every frozen candidate must have exactly one final disposition. Report any violation as an incomplete run.

## Expert validity

At least two domain experts independently annotate a stratified claim sample using codebook v0.2.0 without seeing model outputs. Report criterion-level confusion matrices, macro-F1 for design or method family, exact Level agreement, weighted kappa, within-one-Level agreement, claim-boundary precision and recall, and quote-grounding accuracy.

Prompt stability results cannot be described as accuracy without this expert comparison. Codebook pilot and prompt-development records are identified separately from expert-held-out records.

## Provenance and PRISMA-trAIc reporting

Report the model and reasoning effort, prompt and schema hashes, runtime version, repeat and retry rules, source representation, section-coverage statistics, missing-text handling, human overrides, raw response retention, and Git revision. Causal extraction is a post-eligibility synthesis stage, so Levels 0-4 do not change PRISMA inclusion counts.

## Release decision

Technical checkpoint acceptance requires:

- 100% canonical, open-core, and dense-core section coverage;
- zero silently omitted or truncated nonempty sections;
- 100% schema-valid terminal outputs after at most one retry;
- 100% verbatim quote grounding;
- 100% final candidate disposition completeness.

Stability is reported rather than repaired within the same frozen checkpoint. Any revised instrument receives a new version and a disjoint evaluation set.

