# Prompt Calibration

## Objective

The title/abstract suite performs reproducible PRISMA routing for causal
multi-omics studies of aging with GPT 5.6 Terra Medium through Codex CLI.
Acceptance is deliberately strict: five independent sessions must produce
100% exact agreement for every canonical categorical routing field, the
decisive criterion path, the final route, and the exclusion code. Schema
success must be 100% and no record may fall into manual review because of
runtime failure.

Free-text rationales and the wording of evidence spans remain in the audit
trail but are not exact-matched. The unverified specialist drafts are
exact-matched separately as a diagnostic and are never substituted for the
canonical metric. Stability does not establish screening accuracy;
expert-labelled sensitivity and precision evaluation remains separate.

## Runtime Architecture

Every agent call uses `gpt-5.6-terra` with `reasoning.effort=medium` through an
ephemeral, isolated Codex CLI session. Title/abstract screening uses three
narrow specialists:

1. scope and aging;
2. causal design;
3. directional biological wording.

Each specialist output is followed by a separate self-contained verifier that
reapplies only the matching contract. The verifier receives the source record
and the draft, but no final route. Its categorical output becomes canonical.
Both responses, parse attempts, evidence spans, and any changed categorical
fields remain in the audit trail.

Python does not classify semantic wording. It applies only ordered PRISMA
short-circuits, three-valued logical aggregation, consistency rules, exclusion
codes, and exact-agreement calculations.

## Tracked Contract

Title/abstract screening now tracks only fields needed for routing:

- report type;
- biological or health scope;
- aging-process relevance;
- multi-omics candidate status;
- completed current report;
- genetic-instrument, manipulation, and directed-model signals;
- directional-language signal;
- derived applied-design, directional-result, and causal-candidate status;
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

The unmodified provider JSON and every specialist draft are retained separately
from canonical normalized output.

## Data Separation

- `title_abstract_calibration_v0.24.0_50.csv` is the visible 50-record
  development set.
- `v4` and `v5` were previously opened as sealed holdouts. Both are now
  accessed regression sets and are not independent tests.
- `v5` contains 25 records and has SHA-256
  `3caaa4406ece8ca0ac147b20f9e4b912f1323fbf925165517a790082c000f06c`.
- `v6` was deterministically sampled from the untouched 66-record remainder
  before `v0.91.0` was developed. It contains 25 records and has SHA-256
  `283d2ebffcbb797c0cec30db80b3176bfa4f19d20155283b8733f9b166d0f46f`.
- `v6` remained sealed until the complete `v0.91.0` candidate was frozen in
  Git. It was opened exactly once after freeze commit `1dd685d` and is now an
  accessed evaluation set, not calibration data.
- After the v6 rejection, the untouched 41-record remainder was split
  deterministically into
  `title_abstract_calibration_v0.92.0_16.csv` and the sealed
  `title_abstract_stability_holdout_v7_v0.92.0_25.csv`.
- The visible 16-record set is the only new calibration data used for
  `v0.92.0` through `v0.95.0`.
- `v7` contains 25 disjoint records and has SHA-256
  `17fa64ed5893f6a9c44803d18b87dae9677b760e1d6e264a761b4066270faca5`.
  It was evaluated exactly once after the complete `v0.95.0` candidate was
  frozen at commit `6a6f1a7`. It is now accessed evaluation data and must not
  be used for calibration.

## Calibration History

Prompt and schema versions are immutable after execution. The table lists
major calibration milestones; all intermediate prompt versions and run
artifacts remain versioned in the repository.

| Suite | Set | Schema | Final | Decisive | All tracked | Raw drafts | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| v0.40.0 | visible development, 50 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | n/a | pass |
| v0.40.0 | sealed holdout v4, 25 x 5 | 1.00 | 0.96 | 0.92 | 0.88 | n/a | fail |
| v0.50.0 | visible development, 50 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | n/a | pass |
| v0.50.0 | sealed holdout v5, 25 x 5 | 1.00 | 0.92 | 0.92 | 0.92 | n/a | fail |
| v0.89.0 | development, 50 x 5 | 1.00 | 1.00 | 1.00 | 0.98 | 0.88 | fail |
| v0.90.0 | development, 50 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.92 | pass |
| v0.90.0 | accessed v4, 25 x 5 | 1.00 | 1.00 | 1.00 | 0.96 | 0.84 | fail |
| v0.90.0 | accessed v5, 25 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.96 | pass |
| v0.91.0 | development, 50 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.92 | pass |
| v0.91.0 | accessed v4, 25 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.92 | pass |
| v0.91.0 | accessed v5, 25 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | pass |
| v0.91.0 | sealed v6, 25 x 5 | 1.00 | 1.00 | 0.96 | 0.84 | 0.68 | fail |
| v0.91.0 | new calibration, 16 x 5 | 1.00 | 0.875 | 0.875 | 0.8125 | 0.75 | fail |
| v0.92.0 | new calibration, 16 x 5 | 1.00 | 0.9375 | 0.9375 | 0.875 | 0.6875 | fail |
| v0.93.0 | new calibration, 16 x 5 | 1.00 | 0.9375 | 0.9375 | 0.9375 | 0.625 | fail |
| v0.94.0 | new calibration, 16 x 5 | 1.00 | 0.9375 | 0.9375 | 0.9375 | 0.875 | fail |
| v0.95.0 | new calibration, 16 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.8125 | pass |
| v0.95.0 | development, 50 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.94 | pass |
| v0.95.0 | accessed v4, 25 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.92 | pass |
| v0.95.0 | accessed v5, 25 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.92 | pass |
| v0.95.0 | sealed v7, 25 x 5 | 1.00 | 0.96 | 0.80 | 0.80 | 0.56 | fail |

The calibration failures localized recurring sources of nondeterminism:

- distinguishing causal evidence from a high-sensitivity causal candidate;
- inconsistent treatment of literal directional claims such as
  `X-driven Y` or `impact of X on Y`;
- chronological-age prediction versus analysis of an aging process;
- downstream criteria being evaluated after an upstream PRISMA criterion was
  already negative or unresolved;
- stochastic noncompliance with explicit atomic boundaries, such as ordinary
  methods containing `path` versus structural equation models.

The title/abstract suite retains hypotheses for full-text assessment without
claiming that causality is identified. `v0.92.0` adds three independent
verifier votes per role and strict field-majority consensus. `v0.93.0`
applies the ordered PRISMA scope result before downstream causal criteria:
clear exclusions become `not_assessed`, while unresolved upstream scope
proceeds directly to full text. `v0.94.0` defines a general biological
X-role-Y clause, including epistemically qualified role predicates.
`v0.95.0` removes a contradictory report-type boundary: missing current
methods or results in a thin fragment is not evidence that a report is
nonempirical.

## Current Status

Title/abstract `v0.95.0` passed all strict gates on 116 accessible
calibration/development/regression records:
all-tracked, decisive, final-route, and schema agreement were `1.00`, and
manual review was `0.00` on every set. Raw-draft agreement was `0.8125`,
`0.94`, `0.92`, and `0.92`; verifier field unanimity was `0.9847`, `0.9982`,
`0.9982`, and `1.00`.

After freeze commit `6a6f1a7`, the candidate was evaluated exactly once on
sealed `v7`. It failed with `1.00` schema success, `1.00` causal-level
agreement, `0.96` final-route agreement, `0.80` decisive agreement, `0.80`
all-tracked agreement, `0.56` raw-draft agreement, `0.9573` verifier-field
unanimity, and `0.00` manual review. Five of 25 records were unstable. Two
involved report-type classification, two involved aging relevance, and one
involved directional-result wording; only one changed the final route.
`v0.95.0` is therefore rejected. No `v6` or `v7` wording may be used for
subsequent prompt calibration.

Full-text `v0.1.0` remains unvalidated. The planned expert-labelled
title/abstract benchmark, 60-paper full-text benchmark, and 20-paper
section-selector gold subset are still required for accuracy and full-text
stability assessment.
