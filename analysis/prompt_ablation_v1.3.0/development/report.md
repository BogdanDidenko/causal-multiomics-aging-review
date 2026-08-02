# Title/abstract prompt ablation

Phase: `development`. Records: 60.

This experiment measures repeated-run reproducibility. It does not establish model-to-expert validity.

| Arm | All tracked exact | Decision fields exact | Route exact | Valid 5/5 |
|---|---:|---:|---:|---:|
| S+C | 52/60 (86.7%) | 52/60 (86.7%) | 56/60 (93.3%) | 60/60 (100.0%) |
| T+C | 58/60 (96.7%) | 58/60 (96.7%) | 59/60 (98.3%) | 60/60 (100.0%) |

## Paired comparisons

- `T+C` vs `S+C`: 8 gains, 2 losses; exact McNemar p=0.1094.

Development selection: `T+C`.

Wilson 95% intervals, field-level estimates, retry counts, and record-level outcomes are stored in the JSON/CSV audit artifacts.
