# Secondary 120-record regression test

This corpus is a regression/test set, not a production corpus and not an independent sealed holdout. Its earlier baseline outputs informed the initial instability diagnosis.

Baseline exact agreement was 86/120 (71.7%). Frozen RC1 exact agreement was 100/120 (83.3%; Wilson 95% CI 75.7-88.9). The paired comparison contained 26 gains and 12 losses (exact McNemar p=0.03355).

This secondary result does not override the failed sealed-holdout gate, does not activate RC1, and will not be used for prompt tuning.
