# Title/abstract prompt ablation

Phase: `development`. Records: 60.

This experiment measures repeated-run reproducibility. It does not establish model-to-expert validity.

| Arm | All tracked exact | Decision fields exact | Route exact | Valid 5/5 |
|---|---:|---:|---:|---:|
| A0 | 36/60 (60.0%) | 38/60 (63.3%) | 55/60 (91.7%) | 59/60 (98.3%) |
| S | 49/60 (81.7%) | 51/60 (85.0%) | 56/60 (93.3%) | 60/60 (100.0%) |
| C | 38/60 (63.3%) | 38/60 (63.3%) | 54/60 (90.0%) | 59/60 (98.3%) |
| S+C | 52/60 (86.7%) | 52/60 (86.7%) | 56/60 (93.3%) | 60/60 (100.0%) |

## Paired comparisons

- `S` vs `A0`: 17 gains, 4 losses; exact McNemar p=0.007197.
- `C` vs `A0`: 3 gains, 1 losses; exact McNemar p=0.625.
- `S+C` vs `A0`: 20 gains, 4 losses; exact McNemar p=0.001544.

Development selection: `S+C`.

Wilson 95% intervals, field-level estimates, retry counts, and record-level outcomes are stored in the JSON/CSV audit artifacts.
