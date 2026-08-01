# v0.99.0 Methodological Postmortem

## What the pilot established

The rejected `v0.99.0` instrument generated 790 screening outcomes and 9,515
raw model responses. It demonstrated that exact repeated-run agreement can be
measured, audited, and improved through narrower contracts and deterministic
routing. Those artifacts remain immutable instrument-development history.

## Why it cannot support the review conclusions

First, `directional_result_reviewer` treated explicit directional or
mechanistic wording as a positive causal-candidate signal. Phrases such as
“drives,” “causal processes,” or a directed network statement could therefore
retain a paper even when the current study applied no causal-effect or formal
causal-discovery method. This mixed linguistic claims with study design.

Second, the calibration sets did not contain completed, independently produced
expert criterion-level gold labels. The measured outcome was consistency
between repeated model outputs, not sensitivity, precision, or evidence-level
validity against a human reference standard.

Third, reproducibility and validity are different properties. A model can
return the same wrong category five times. Conversely, stochastic variation
can reveal a poorly localized criterion, but eliminating that variation does
not prove the resulting criterion is scientifically correct.

## Corrective action in v1

`v1.0.0` removes directional-language routing entirely. It separates formal
causal-hypothesis methods from assessable causal-effect designs, uses two
self-contained title/abstract contracts, and permits direct exclusion only
after five identical criterion paths. Accuracy is evaluated against two-expert
gold labels on development and sealed sets; stability remains a simultaneous,
not substitute, requirement.

The old outputs are retained for a transparent methods section describing
instrument iteration and uncertainty. They are not mixed into the v1 ledger,
not used as expert labels, and not counted in the final PRISMA flow.
