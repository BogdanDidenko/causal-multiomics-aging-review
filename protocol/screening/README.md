# Screening Prompt Suite

The active suite combines:

- title/abstract `v0.91.0`: three narrow specialist drafts, separate matching
  contract-verification passes, sequential scope gates, and selective
  adjudication;
- full text `v0.1.0`: section selection, eligibility, causal evidence, and
  adjudication.

All prompts are model-neutral JSON contracts executed with GPT 5.6 Terra
Medium through Codex CLI at `reasoning.effort=medium`. Python applies routing,
ordered PRISMA consistency rules, three-valued aggregation, exclusion codes,
and full-text evidence levels. Raw provider JSON, specialist drafts, verifier
outputs, and categorical corrections are retained unchanged.

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

`v0.91.0` passed the visible 50-record development set and both accessed
25-record regression sets (`v4` and `v5`) with `1.00` schema, final-route,
decisive-path, and all-tracked agreement and `0.00` manual review. Raw draft
agreement was `0.92`, `0.92`, and `1.00`; this diagnostic is reported
separately and does not replace the canonical gate.

The 25-record `v6` holdout was run once after candidate freeze commit
`1dd685d`. Its SHA-256 is
`283d2ebffcbb797c0cec30db80b3176bfa4f19d20155283b8733f9b166d0f46f`.
It failed strict stability with `0.84` all-tracked and `0.96` decisive
agreement, although final-route agreement was `1.00`. `v0.91.0` is rejected
and `v6` must not be used for calibration.

Stability is not accuracy. Expert criterion-level annotation and the full-text
benchmarks remain pending. Full-text `v0.1.0` has not yet undergone its planned
stability or accuracy evaluation.
