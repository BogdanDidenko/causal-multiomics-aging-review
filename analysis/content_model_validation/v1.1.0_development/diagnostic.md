# CMACM v1.1.0 Atom-First Development Retest

Status: rejected as a production extraction contract; retained as development
evidence.

## Question

CMACM v1.1.0 tested the Opus reassessment on the same 15 reports used for the
rejected v1.0.3 development run. Models emitted atomic attributes and document
atom identifiers; Python derived workflows, links, result measurements,
validations and linearization counts from frozen identity keys.

## Results

| Outcome | v1.0.3 | v1.1.0 |
|---|---:|---:|
| Valid evidence-grounded outputs | 30/45 after recovery | 45/45 |
| Exact complete structure, three runs | 1/15 | 0/15 |
| Workflow count agreement | 8/15 | 11/15 |
| Link count agreement | 5/15 | 7/15 |
| Procedure/design-family set agreement | 10/15 | 11/15 |

The deterministic evidence-atom interface removed all free-quotation failures.
The deterministic identity functions modestly improved workflow and link
counts. They did not yield production-level agreement.

## Why the strong Opus prediction did not hold

The model still controls atomic recall and attribute assignment. Examples:

- In the PDAP1 study, one repeat emitted a mediation procedure while another
  did not. Two repeats emitted a PDAP1 biological-age-clock link while the third
  did not.
- In the drug-target MR study, the same targets were variously classified as
  genetically proxied molecular exposures, pharmacologic interventions, or
  gene perturbations. Dataset-context sets also varied between one and two
  procedure atoms.
- In several intervention studies, measurement atoms differed because the model
  selected different endpoint sets, even after workflow and link identity were
  derived by Python.

Therefore Python can only make counts deterministic conditional on stable atom
attributes. It cannot recover targets, procedures or outcome domains omitted by
one run, and it cannot resolve semantically inconsistent attributes by hashing.

## Consequence

WHO Content Model remains a coherent representation architecture, but neither
v1.0.3 direct entity extraction nor v1.1.0 atom-first classification is ready
for corpus-scale autonomous enumeration. A new method must address atomic
candidate recall and attribute adjudication before a new unseen holdout is
drawn. The current 15 reports remain development material and may not serve as
the next holdout.

No eligibility, PRISMA or synthesis count changed.
