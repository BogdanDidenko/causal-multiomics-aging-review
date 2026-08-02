# Title/abstract prompt ablation

Phase: `development`. Records: 60.

This experiment measures repeated-run reproducibility. It does not establish model-to-expert validity.

| Arm | All tracked exact | Decision fields exact | Route exact | Valid 5/5 |
|---|---:|---:|---:|---:|
| A0 | 36/60 (60.0%) | 38/60 (63.3%) | 55/60 (91.7%) | 59/60 (98.3%) |
| M | 36/60 (60.0%) | 38/60 (63.3%) | 55/60 (91.7%) | 59/60 (98.3%) |
| D | 36/60 (60.0%) | 37/60 (61.7%) | 55/60 (91.7%) | 59/60 (98.3%) |
| M+D | 36/60 (60.0%) | 37/60 (61.7%) | 55/60 (91.7%) | 59/60 (98.3%) |

## Paired comparisons

- `M` vs `A0`: 8 gains, 8 losses; exact McNemar p=1.
- `D` vs `A0`: 1 gains, 1 losses; exact McNemar p=1.
- `M+D` vs `A0`: 9 gains, 9 losses; exact McNemar p=1.

Development selection: `M`.

Wilson 95% intervals, field-level estimates, retry counts, and record-level outcomes are stored in the JSON/CSV audit artifacts.
