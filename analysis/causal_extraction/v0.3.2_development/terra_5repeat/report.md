# Causal extraction v0.3.2 role-contract ablation

Status: development-only; no expert-gold accuracy claim.

## Completion

- Valid calls: 300/300
- Complete reports: 12/12

## Role stability

| Role | 3-run exact candidates | 5-run exact candidates | 5-run exact reports |
|---|---:|---:|---:|
| `eligibility` | 38/45 (84.4%) | 36/45 (80.0%) | 5/12 (41.7%) |
| `design_identity` | 25/28 (89.3%) | 24/28 (85.7%) | 8/12 (66.7%) |
| `review_context` | 23/28 (82.1%) | 22/28 (78.6%) | 7/12 (58.3%) |
| `effect_appraisal` | 18/28 (64.3%) | 12/28 (42.9%) | 4/12 (33.3%) |
| `validation` | 20/28 (71.4%) | 15/28 (53.6%) | 7/12 (58.3%) |

## Composite stability

| View | Exact reports | Exact candidates | Qualification exact | Level exact | Gate |
|---|---:|---:|---:|---:|---|
| 3 repeats | 0/12 (0.0%) | 17/45 (37.8%) | 41/45 (91.1%) | 23/28 (82.1%) | FAIL |
| 5 repeats | 0/12 (0.0%) | 14/45 (31.1%) | 40/45 (88.9%) | 22/28 (78.6%) | FAIL |

## Provisional eligibility alignment

- Include sensitivity: 95.0%
- Exclude specificity: 97.6%
- Reference: AI-assisted analyst draft pending human verification.
