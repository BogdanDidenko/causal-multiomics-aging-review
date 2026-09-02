# Causal extraction v0.3.1 fixed-candidate ablation

Status: development-only; conditional classification stability, no expert-gold accuracy claim.

## Completion

- Valid calls: 60/60
- Complete reports: 12/12

## Stability

| View | Exact reports | Qualification-exact candidates | All-field-exact candidates | Gate |
|---|---:|---:|---:|---|
| 3 repeats | 2/12 (16.7%) | 45/45 (100.0%) | 22/45 (48.9%) | FAIL |
| 5 repeats | 1/12 (8.3%) | 45/45 (100.0%) | 17/45 (37.8%) | FAIL |

## Provisional reference alignment

- Include sensitivity: 100.0%
- Exclude specificity: 100.0%
- Interpretation: comparison with an AI-assisted analyst draft, not expert gold.

## Reports

| DOI | 3-run exact | 5-run exact | Includes across five runs |
|---|---|---|---|
| 10.3389/fendo.2025.1661666 | no | no | [6, 6, 6, 6, 6] |
| 10.1038/s41467-025-59964-z | no | no | [2, 2, 2, 2, 2] |
| 10.3390/microorganisms13061379 | yes | yes | [1, 1, 1, 1, 1] |
| 10.1002/advs.202514269 | no | no | [2, 2, 2, 2, 2] |
| 10.1172/jci.insight.154089 | no | no | [4, 4, 4, 4, 4] |
| 10.1007/s13238-021-00894-z | no | no | [3, 3, 3, 3, 3] |
| 10.7554/elife.71624 | no | no | [1, 1, 1, 1, 1] |
| 10.1093/plphys/kiaa034 | no | no | [1, 1, 1, 1, 1] |
| 10.1016/j.devcel.2023.05.015 | no | no | [2, 2, 2, 2, 2] |
| 10.1186/s40364-023-00458-9 | yes | no | [2, 2, 2, 2, 2] |
| 10.3892/or.2026.9080 | no | no | [2, 2, 2, 2, 2] |
| 10.1016/j.exger.2025.112815 | no | no | [2, 2, 2, 2, 2] |
