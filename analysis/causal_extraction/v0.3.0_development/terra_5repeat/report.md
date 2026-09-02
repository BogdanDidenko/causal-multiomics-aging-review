# Causal extraction v0.3 stability report

Status: development-only; analyst reference draft, no expert-gold accuracy claim.

## Completion

- Valid calls: 60/60
- Complete reports: 12/12

## Stability

| View | Exact reports | Rate | Anchor-set exact | Gate |
|---|---:|---:|---:|---|
| 3 repeats | 1/12 | 8.3% | 33.3% | FAIL |
| 5 repeats | 1/12 | 8.3% | 8.3% | FAIL |

## Reference alignment

- Mean evidence-overlap recall: 90.4%
- Mean evidence-overlap precision: 80.0%
- Direct boundary promotions: 7
- Interpretation: development diagnostics against an AI-assisted analyst draft.

## Reports

| DOI | 3-run exact | 5-run exact | Counts across five runs |
|---|---|---|---|
| 10.3389/fendo.2025.1661666 | no | no | [6, 6, 9, 6, 6] |
| 10.1038/s41467-025-59964-z | no | no | [2, 2, 2, 2, 2] |
| 10.3390/microorganisms13061379 | yes | yes | [1, 1, 1, 1, 1] |
| 10.1002/advs.202514269 | no | no | [3, 3, 3, 2, 3] |
| 10.1172/jci.insight.154089 | no | no | [4, 5, 5, 4, 5] |
| 10.1007/s13238-021-00894-z | no | no | [3, 3, 3, 3, 3] |
| 10.7554/elife.71624 | no | no | [1, 1, 2, 1, 2] |
| 10.1093/plphys/kiaa034 | no | no | [1, 1, 1, 1, 1] |
| 10.1016/j.devcel.2023.05.015 | no | no | [6, 4, 6, 5, 7] |
| 10.1186/s40364-023-00458-9 | no | no | [2, 2, 2, 2, 2] |
| 10.3892/or.2026.9080 | no | no | [2, 2, 2, 2, 2] |
| 10.1016/j.exger.2025.112815 | no | no | [2, 2, 2, 2, 2] |
