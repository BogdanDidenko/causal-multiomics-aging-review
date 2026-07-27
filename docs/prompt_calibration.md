# Prompt Calibration

## Objective

The title/abstract suite is calibrated for reproducible PRISMA routing of
causal multi-omics aging studies with GPT 5.6 Terra Medium. The acceptance rule
is deliberately strict: five independent runs must produce 100% exact
agreement on the final routing decision and the decisive criterion path.

The decisive path contains the criteria required to reach the final PRISMA
route. Fields downstream of an agreed exclusion are non-decisive and are
reported separately as a diagnostic. This prevents irrelevant downstream
variation from failing the route while preserving it in the audit trail.

## Data Separation

- The 25-record high-signal and boundary sets were visible during development.
- Two malformed conference-abstract records leaked body fragments or mismatched
  titles. They were replaced before the final development pilot; both
  replacements and hashes are recorded in curation manifests.
- Holdout v2 was quarantined after accidental partial disclosure and was never
  used as final evidence.
- Holdout v3 was sampled disjointly, remained uninspected while versions
  `v0.1.0` through `v0.16.0` were developed, and was launched once after
  `v0.16.0` was frozen.
- The separate 116-record regression candidate set remains uninspected and
  unannotated.

## Development History

Prompt versions are immutable. Iterations localized report type, aging-process
relevance, molecular-layer integration, current-report causal design, and
validation-versus-identification boundaries. Representative full-pilot results
are:

| Suite | Set | Schema | Final route | Decisive path | All tracked | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| v0.10.0 | development | 1.00 | 0.92 | 0.28 | not recorded | fail |
| v0.12.0 | development | 1.00 | 1.00 | 0.84 | 0.32 | fail |
| v0.14.0 | development | 1.00 | 0.92 | 0.88 | 0.48 | fail |
| v0.15.0 | development | 1.00 | 0.96 | 0.92 | 0.40 | fail |
| v0.16.0 | development | 1.00 | 1.00 | 1.00 | 0.40 | pass |

The `all_tracked` metric includes non-decisive atomic and diagnostic fields.
The development pass therefore means exact PRISMA-path stability, not identical
raw model JSON.

## Sealed Holdout

The frozen `v0.16.0` suite failed its first sealed evaluation:

| Records | Runs | Schema | Final route | Decisive path | All tracked | Manual review |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 25 | 5 | 1.00 | 0.92 | 0.72 | 0.52 | 0.00 |

All five runs returned the same aggregate counts, 22 exclusions and 3 records
sent to full text, but two individual records swapped routes. Aggregate counts
therefore concealed record-level instability.

Seven records had an unstable decisive path:

- two changed between exclusion and full-text retrieval at the boundary
  between aging context or an induced aging-like model and a directly analyzed
  aging process;
- four were always excluded but received different exclusion codes when more
  than one eligibility criterion was unmet;
- one retained the same route but varied in whether a validation intervention
  counted as an additional design family beside genetic-instrument analysis.

The holdout was not used to revise `v0.16.0`. Any successor must start a new
calibration cycle, may use these failures only as development evidence, and
must be evaluated on a newly sealed, disjoint set.

## Interpretation

`v0.16.0` is not approved for production screening. Stability is also distinct
from accuracy: even a future 100%-stable suite still requires criterion-level
expert labels to estimate sensitivity, exclusion precision, design-family F1,
and agreement with human decisions.

Pending work:

- expert annotation of title/abstract records;
- a new prompt-calibration cycle with a newly sealed stability test;
- the 60-paper full-text benchmark and 20-paper section-selector gold subset;
- stability and accuracy evaluation of the full-text `v0.1.0` suite.
