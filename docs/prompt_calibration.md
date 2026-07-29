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

Each specialist output is followed by three self-contained verifier runs that
reapply only the matching contract. A verifier receives the source record but
not the specialist draft, prior classifications, or final route. Its votes are
aggregated field by field. All responses, parse attempts, evidence spans,
votes, counts, and applied aggregation rules remain in the audit trail.

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
- A new independent cycle was created from the 2,406 eligible corpus records
  absent from every prior benchmark and stability run. Its split was frozen
  before inspection at commit `15bcde0`.
- `title_abstract_calibration_v0.96.0_50.csv` is the only development set used
  to calibrate `v0.96.0` through `v0.99.0`.
- `title_abstract_stability_holdout_v8_v0.96.0_25.csv` is disjoint, remains
  sealed, and has SHA-256
  `72049f3f6ad74babdd9c2e819ed7b1e9e4800147d044f0efaacccd420d5c6443`.

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
| v0.96.0 | independent development, 50 x 5 | 1.00 | 0.90 | 0.88 | 0.88 | 0.66 | fail |
| v0.97.0 | unstable focus, 6 x 5 | 1.00 | 0.8333 | 0.6667 | 0.6667 | 0.00 | fail |
| v0.98.0 | unstable focus, 6 x 5 | 1.00 | 0.8333 | 0.8333 | 0.8333 | 0.00 | fail |
| v0.99.0 | unstable focus, 6 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.3333 | pass |
| v0.99.0 | independent development, 50 x 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.66 | pass |

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

`v0.96.0` removes shared-draft anchoring: each contract verifier sees only the
source record. `v0.97.0` maps a three-way categorical verifier tie to the
contract's existing `unclear` value. `v0.98.0` aligns the general
current-report attribution rule across reviewers and adjudication for
ellipsized metadata fragments. `v0.99.0` requires verifier unanimity for
exclusionary `no` and `nonempirical` values; a 2/3 exclusionary vote becomes
`unclear` and is retained for full text. Python performs only these declared
categorical aggregation and consistency rules.

## Current Status

Title/abstract `v0.99.0` passed the complete independent 50-record development
set across five sessions: schema, final-route, decisive, all-tracked, and
causal-level exact agreement were all `1.00`; manual review was `0.00`.
Raw-draft agreement was `0.66`, verifier-field unanimity was `0.9791`, and
every run routed the same 35 records to exclusion and 15 to full text.

This is a development stability result, not a final independent estimate and
not an accuracy result. The candidate must be frozen in Git before `v8` is
opened exactly once. No `v6`, `v7`, or `v8` record wording was used for this
calibration.

Full-text `v0.1.0` remains unvalidated. The planned expert-labelled
title/abstract benchmark, 60-paper full-text benchmark, and 20-paper
section-selector gold subset are still required for accuracy and full-text
stability assessment.
