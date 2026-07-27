# Prompt Calibration

## Objective

The title/abstract suite performs reproducible PRISMA routing for causal
multi-omics studies of aging with GPT 5.6 Terra Medium through Codex CLI.
Acceptance is deliberately strict: five independent sessions must produce
100% exact agreement for every tracked categorical routing field, the decisive
criterion path, the final route, and the exclusion code. Schema success must
be 100% and no record may fall into manual review because of runtime failure.

Free-text rationales and the wording of evidence spans remain in the audit
trail but are not exact-matched. Stability does not establish screening
accuracy; expert-labelled sensitivity and precision evaluation remains
separate.

## Tracked Contract

Title/abstract screening now tracks only fields needed for routing:

- report type;
- biological or health scope;
- aging-process relevance;
- multi-omics candidate status;
- causal-candidate status;
- final route and exclusion code.

Exact omics-layer inventory, aging-role subtyping, design family, effect
strength, integration provenance, assumptions, validation strength, and causal
evidence level are deferred to full text. This prevents unstable abstract-level
subtyping from deciding a route.

Scope criteria are sequential. Python applies only this logical consistency
rule:

1. A report type other than `empirical_primary` makes later scope criteria
   `not_assessed`.
2. Biological scope other than `yes` makes aging and multi-omics
   `not_assessed`.
3. Aging relevance other than `yes` makes multi-omics `not_assessed`.
4. An unresolved upstream value still routes to adjudication or full text; it
   is not converted into an exclusion.

The unmodified provider JSON is retained separately from normalized output.

## Data Separation

- `title_abstract_calibration_v0.24.0_50.csv` is the visible 50-record
  development set.
- The frozen `v0.40.0` suite was evaluated once on sealed holdout `v4`.
- After that evaluation, `v4` became an accessed diagnostic set and was used
  only for calibration and regression testing.
- Fresh holdout `v5` was deterministically sampled from a separate untouched
  91-record remainder after excluding the 50-record development set and
  25-record `v4`.
- `v5` contains 25 records and has SHA-256
  `3caaa4406ece8ca0ac147b20f9e4b912f1323fbf925165517a790082c000f06c`.
  It remains uninspected and unevaluated until `v0.50.0` is frozen in Git.
- A further 66-record remainder remains untouched for a future cycle if `v5`
  fails.

## Calibration History

Prompt and schema versions are immutable after execution.

| Suite | Set | Schema | Final route | Decisive path | All tracked | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| v0.40.0 | visible development, 50 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | pass |
| v0.40.0 | sealed holdout v4, 25 x 5 | 1.00 | 0.96 | 0.92 | 0.88 | fail |
| v0.46.0 | accessed v4 diagnostic, 25 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | pass |
| v0.46.0 | visible development, 50 x 5 | 1.00 | 0.96 | 0.96 | 0.96 | fail |
| v0.47.0 | visible development, 50 x 5 | 1.00 | 0.98 | 0.98 | 0.96 | fail |
| v0.48.0 | visible development, 50 x 5 | 1.00 | 1.00 | 1.00 | 0.98 | fail |
| v0.49.0 | accessed v4 diagnostic, 25 x 5 | 1.00 | 1.00 | 1.00 | 0.96 | fail |
| v0.50.0 | accessed v4 diagnostic, 25 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | pass |
| v0.50.0 | visible development, 50 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | pass |

The calibration failures localized four recurring sources of nondeterminism:

- distinguishing causal evidence from a high-sensitivity causal candidate;
- inconsistent treatment of literal directional claims such as
  `X-driven Y` or `impact of X on Y`;
- chronological-age prediction versus analysis of an aging process;
- downstream criteria being evaluated after an upstream PRISMA criterion was
  already negative or unresolved.

The final causal-candidate prompt uses a closed trigger check for explicit
current-report directional clauses. This retains hypotheses for full-text
assessment without claiming that causality is identified.

## Current Status

Title/abstract `v0.50.0` is a frozen-candidate pending one evaluation on fresh
holdout `v5`. It is not production-approved until that evaluation passes all
100% stability gates.

Full-text `v0.1.0` remains unvalidated. The planned expert-labelled
title/abstract benchmark, 60-paper full-text benchmark, and 20-paper
section-selector gold subset are still required for accuracy and full-text
stability assessment.
