# Title/abstract prompt ablation

Phase: `sealed_holdout`. Records: 60.

This experiment measures repeated-run reproducibility. It does not establish model-to-expert validity.

| Arm | All tracked exact | Decision fields exact | Route exact | Valid 5/5 |
|---|---:|---:|---:|---:|
| A0 | 29/60 (48.3%) | 33/60 (55.0%) | 47/60 (78.3%) | 57/60 (95.0%) |
| RC1 | 48/60 (80.0%) | 48/60 (80.0%) | 50/60 (83.3%) | 59/60 (98.3%) |

## Paired comparisons

- `RC1` vs `A0`: 21 gains, 2 losses; exact McNemar p=6.604e-05.

Wilson 95% intervals, field-level estimates, retry counts, and record-level outcomes are stored in the JSON/CSV audit artifacts.
