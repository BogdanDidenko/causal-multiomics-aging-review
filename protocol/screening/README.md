# Screening Prompt Suite

The active suite combines:

- title/abstract `v0.50.0`: sequential scope review, causal-candidate review,
  and selective adjudication;
- full text `v0.1.0`: section selection, eligibility, causal evidence, and
  adjudication.

All prompts are model-neutral JSON contracts executed with GPT 5.6 Terra
Medium through Codex CLI at `reasoning.effort=medium`. Python applies routing,
ordered PRISMA consistency rules, exclusion codes, and full-text evidence
levels. Raw provider JSON is retained unchanged.

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

`v0.50.0` passed both the visible 50-record development set and the accessed
25-record `v4` diagnostic set, but failed the fresh 25-record `v5` holdout.
Final-route, decisive-path, and all-tracked exact agreement were each `0.92`;
schema success was `1.00` and manual-review rate was `0.00`. The suite is not
approved. `v5` is now diagnostic evidence, and the 66-record remainder is
reserved for a new independent cycle.

Stability is not accuracy. Expert criterion-level annotation and the full-text
benchmarks remain pending. Full-text `v0.1.0` has not yet undergone its planned
stability or accuracy evaluation.
