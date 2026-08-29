# E0 semantic evidence audit codebook

## Purpose

The deterministic validator proves only that an evidence reference resolves to
frozen text. Two reviewers independently determine whether the cited passage
supports the model's stated causal-analysis inventory item.

Reviewers receive an opaque audit ID, report metadata, the proposed analysis
summary, evidence role, section ID, and exact source passage. They do not
receive the grounding arm, repeat number, model output from another run, or the
other reviewer's judgment.

## Judgment

Use one value per reference:

- `supported`: the passage directly supports the stated method or result for
  the same current-report analysis;
- `unsupported`: the passage is real but does not support that role or belongs
  to background, another analysis, or future work;
- `unclear`: the supplied passage cannot be judged without additional local
  context.

For the prespecified precision gate, `unclear` is counted as not supported.
Reviewers may inspect adjacent frozen Docling text to resolve an `unclear`
judgment, but must record that action and the additional atom IDs.

## Analysis-inventory gold

Separately from reference auditing, each reviewer reads all six frozen reports
and lists every qualifying causal analysis under the E0 unit definition. A gold
analysis consists of design implementation, exposure construct, outcome
construct, biological system, and at least one method or result evidence atom.
Endpoint rows, estimates, time points, strata, instruments, and diagnostics stay
within an analysis unless one of those four boundary dimensions changes
materially.

Association, prediction, enrichment, colocalization alone, undirected networks,
causal wording alone, cited prior findings, and proposed work are excluded.

## Adjudication and scoring

Reviewers finish and freeze their files independently. Disagreements are then
adjudicated with a reason and retained original judgments. Report:

- inter-reviewer agreement before adjudication;
- adjudicated supported-reference precision by arm;
- analysis-boundary precision, recall, and F1 by arm;
- report-clustered uncertainty;
- every human override and all technical failures.

E0 requires supported-reference precision of at least 0.98 and no lower
expert-gold analysis recall for the evidence-ID arm than the quote arm.
