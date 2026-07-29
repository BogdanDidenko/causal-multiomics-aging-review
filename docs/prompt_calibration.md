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
- `v6` remains sealed and must not be inspected or executed until the complete
  `v0.91.0` candidate is frozen in Git.
- A separate 41-record remainder remains untouched for a future independent
  cycle.

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

The calibration failures localized recurring sources of nondeterminism:

- distinguishing causal evidence from a high-sensitivity causal candidate;
- inconsistent treatment of literal directional claims such as
  `X-driven Y` or `impact of X on Y`;
- chronological-age prediction versus analysis of an aging process;
- downstream criteria being evaluated after an upstream PRISMA criterion was
  already negative or unresolved;
- stochastic noncompliance with explicit atomic boundaries, such as ordinary
  methods containing `path` versus structural equation models.

The final title/abstract suite retains hypotheses for full-text assessment
without claiming that causality is identified. The `v0.91.0` change is a
general method boundary: an applied genomic structural equation model,
including genomic SEM, is a directed-model positive; ordinary path-like
method names remain negative.

## Current Status

Title/abstract `v0.91.0` is the frozen candidate pending its one-time sealed
`v6` evaluation. It passed all strict stability gates on 100 accessed records
across 500 record-runs. The raw specialist metric was lower on development and
`v4`, which documents model nondeterminism rather than hiding it.

Full-text `v0.1.0` remains unvalidated. The planned expert-labelled
title/abstract benchmark, 60-paper full-text benchmark, and 20-paper
section-selector gold subset are still required for accuracy and full-text
stability assessment.
