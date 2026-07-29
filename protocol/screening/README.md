# Screening Prompt Suite

The active suite combines:

- title/abstract `v0.99.0`: three narrow specialist drafts, three independent
  source-only verifier votes per role, conservative categorical consensus,
  ordered scope gates, and selective adjudication;
- full text `v0.1.0`: section selection, eligibility, causal evidence, and
  adjudication.

All prompts are model-neutral JSON contracts executed with GPT 5.6 Terra
Medium through Codex CLI at `reasoning.effort=medium`. Python applies routing,
ordered PRISMA consistency rules, three-valued aggregation, exclusion codes,
and full-text evidence levels. Raw provider JSON, specialist drafts, every
verifier vote, consensus counts, unanimity flags, and categorical corrections
are retained unchanged.

Title/abstract screening is intentionally high-sensitivity. A completed report
is a causal candidate when it applies a causal or directed design or makes an
explicit current-report directional/mechanistic claim. Full text determines
whether that signal is associational, hypothesis-level, or identified causal
evidence.

The title stage does not classify exact omics layers, integration provenance,
aging role, design family, effect strength, assumptions, or validation
strength. Those fields are resolved from full text because they do not change
title-stage routing and were unstable in short abstracts.

Stability requires five independent sessions with:

- 100% JSON schema success;
- 100% exact agreement on every tracked categorical field;
- 100% exact agreement on decisive criteria and final route;
- 0% runtime-triggered manual review.

`v0.99.0` was calibrated on a new 50-record development set sampled only from
records absent from every earlier benchmark and stability run. Across five
Terra Medium sessions it achieved `1.00` schema, final-route, decisive-path,
and all-tracked agreement with `0.00` manual review. Raw draft agreement was
`0.66` and verifier-field unanimity was `0.9791`; these diagnostics are
reported separately and do not replace the canonical gate.

The verifier prompts no longer receive the specialist draft. Python selects a
field majority, maps a three-way categorical tie to the schema's existing
`unclear` value, and requires all three votes before accepting exclusionary
`no` or `nonempirical` values. These are fixed aggregation rules over model
outputs, not semantic keyword rules.

The 25-record `v6` holdout was run once after candidate freeze commit
`1dd685d`. Its SHA-256 is
`283d2ebffcbb797c0cec30db80b3176bfa4f19d20155283b8733f9b166d0f46f`.
It failed strict stability with `0.84` all-tracked and `0.96` decisive
agreement, although final-route agreement was `1.00`. `v0.91.0` is rejected
and `v6` must not be used for calibration.

After the v6 rejection, the untouched 41-record remainder was split
deterministically into a visible 16-record calibration set and a sealed
25-record `v7` set. `v7` has SHA-256
`17fa64ed5893f6a9c44803d18b87dae9677b760e1d6e264a761b4066270faca5`
and was reserved for the one-time evaluation of the frozen `v0.95.0`
candidate.

The candidate was frozen at commit `6a6f1a7` and run exactly once on `v7`.
The sealed run passed schema success, causal-evidence-level agreement, and
manual-review gates, but failed strict stability: final-route agreement was
`0.96`, decisive agreement was `0.80`, and all-tracked agreement was `0.80`.
Five of 25 records were unstable; only one changed the final route. The
remaining disagreements involved report type, aging relevance, directional
language, or the resulting exclusion code. `v0.95.0` is rejected, and `v7`
is now accessed evaluation evidence that must not be used for calibration.

The independent `v0.96` calibration cycle was frozen before inspection at
commit `15bcde0`. Its disjoint `v8` holdout has SHA-256
`72049f3f6ad74babdd9c2e819ed7b1e9e4800147d044f0efaacccd420d5c6443`.
The complete `v0.99.0` candidate was frozen at commit `d5646a9` and evaluated
exactly once on `v8`. The run failed strict stability: schema and causal-level
agreement were `1.00`, final-route agreement was `0.96`, decisive and
all-tracked agreement were `0.92`, and manual review was `0.00`. Two records
were unstable and one changed final route. `v0.99.0` is rejected and `v8` is
now accessed evaluation evidence that must not be used for calibration.

Stability is not accuracy. Expert criterion-level annotation and the full-text
benchmarks remain pending. Full-text `v0.1.0` has not yet undergone its planned
stability or accuracy evaluation.
