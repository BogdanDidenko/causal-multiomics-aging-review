# Two-sample causal-extraction stability checkpoint

Instrument: `causal_extraction/v0.1.1-rc1`. Model: `gpt-5.6-terra` with reasoning effort `medium`.

## Verdict

**FAIL.** The release candidate did not satisfy the prespecified 100% quote-grounding and five-run exact-agreement gates. Its scientific classification behaviour was not measured adequately. All v0.1.1 candidate records and derived Levels are excluded from scientific synthesis.

This report was corrected after an independent Opus 5 audit found that the legacy derived-Level statistic treated repeated empty outputs as agreement. The raw artifacts and Git history remain unchanged.

## Results

| Metric | A (15 reports) | B (15 reports) |
|---|---:|---:|
| Frozen atomic candidates | 1288 | 1541 |
| Classifier sample | 30 | 30 |
| Candidates with 5 valid runs | 20 | 16 |
| Reports with incomplete grounded discovery | 11 | 11 |
| Candidates excluded from the 5-run analysis | 10 | 14 |
| Legacy payload exact among 5-run survivors | 9/20 (45.0%) | 8/16 (50.0%) |
| Candidate status exact among 5-run survivors | 18/20 (90.0%) | 14/16 (87.5%) |
| Derived Level exact where all 5 runs produced a claim record | not estimable (0 candidates) | 0/1 (0.0%) |

The legacy payload metric includes free-text fields and candidate-boundary payloads. It is retained only as an instrument-development observation. No confidence intervals are reported because candidates are clustered within reports.

The prior three-versus-five comparison is withdrawn because it estimated the three-run rate only among candidates that survived five grounded runs.

## Corrected derived-Level interpretation

Checkpoint A produced a claim record in all five runs for 0 candidates. Checkpoint B did so for 1 candidate; its Levels were `3, 3, 3, 2, 3`. The previous `20/20` and `15/16` figures compared empty derived-output lists and are withdrawn.

Candidate-status distributions within the five-valid-run analysis sets were `{'split_required': 16, 'duplicate_or_overlapping': 79, 'no_current_report_empirical_result': 5}` for A and `{'duplicate_or_overlapping': 65, 'split_required': 8, 'valid_single_claim': 5, 'no_current_report_empirical_result': 2}` for B. Agreement was dominated by `duplicate_or_overlapping`, so it does not estimate stability of the criterion-level causal classification.

## Technical audit

Discovery produced 1288 candidates in A and 1541 in B. Primary quote-grounding failures were 50 and 55; one retry recovered 19 and 19, respectively.

Classifier terminal statuses were `{'technical_failure': 3, 'grounding_failure': 29, 'ok': 118}` for A and `{'ok': 107, 'grounding_failure': 43}` for B. Invalid responses remain in denominators and are excluded from automatic scientific synthesis.

Reports with known-incomplete discovery contained 1141/1288 (88.6%) of A's inventory and 1040/1541 (67.5%) of B's inventory.

## Interpretation

The atomic discovery contract generated 86 to 103 candidates per report on average and made duplicate disposition the classifier's dominant task. The next instrument must use a causal analysis as its primary unit, with reported contrasts represented as child rows.

Checkpoint A is the same 15-report sample used for codebook development and prompt smoke testing. It is in-sample. Checkpoint B is disjoint but remains a technical-feasibility checkpoint without expert gold labels. The A-versus-B comparison is not a replication estimate.

These artifacts remain useful for the methodological postmortem: atomic unit infeasibility, grounding-failure taxonomy, runner defects, and the failure of free-text exact-agreement gates. They provide no scientific causal findings.
