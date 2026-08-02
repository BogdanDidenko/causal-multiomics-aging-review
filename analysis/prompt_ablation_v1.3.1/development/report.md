# Title/abstract prompt ablation

Phase: `development`. Records: 60.

This experiment measures repeated-run reproducibility. It does not establish model-to-expert validity.

| Arm | All tracked exact | Decision fields exact | Route exact | Valid 5/5 |
|---|---:|---:|---:|---:|
| T+C | 58/60 (96.7%) | 58/60 (96.7%) | 59/60 (98.3%) | 60/60 (100.0%) |
| R+C | 57/60 (95.0%) | 57/60 (95.0%) | 59/60 (98.3%) | 60/60 (100.0%) |

## Paired comparisons

- `R+C` vs `T+C`: 2 gains, 3 losses; exact McNemar p=1.

Development selection: `T+C`.

Wilson 95% intervals, field-level estimates, retry counts, and record-level outcomes are stored in the JSON/CSV audit artifacts.
