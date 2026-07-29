# Prompt Calibration Effects

This directory contains the reproducible numerical summary and manuscript-ready
description of title/abstract prompt calibration from `v0.95.0` through the
one-time sealed `v8` evaluation of `v0.99.0`.

Regenerate the CSV files from committed run artifacts:

```bash
uv run python scripts/summarize_prompt_calibration_effects.py
```

Outputs:

- `calibration_metrics.csv`: version, set, sample size, agreement metrics,
  unstable-record counts, and artifact paths;
- `log_inventory.csv`: replicate manifests, screening outcomes, raw provider
  responses, file counts, and byte totals;
- `manuscript_section.md`: Methods, Results, interpretation, limitations, and a
  compact results table ready for adaptation into the review manuscript.

The analysis describes reproducibility rather than screening accuracy. Focused
development runs are not treated as independent evaluation, and sealed `v8`
records are not calibration data.
