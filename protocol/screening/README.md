# Screening Prompt Suite

The active suite combines:

- title/abstract `v0.16.0`: scope plus aging, causal design, adjudication;
- full text `v0.1.0`: section selection, eligibility, causal evidence,
  adjudication.

Executed title/abstract `v0.1.0` through `v0.15.0` artifacts remain immutable
for audit and are not active.

All prompts are model-neutral contracts executed with GPT 5.6 Terra Medium via
Codex CLI. Models return criterion-level JSON only. Python applies routing,
consistency rules, exclusion codes, and evidence levels.

Prompt changes create a new version and refresh
`prompt_manifest.json`. Stability requires five independent runs with 100%
exact agreement on the final selected criterion path and routing. Fields after
an agreed exclusion criterion are non-decisive; their agreement is still
reported separately as `all_tracked_criteria_exact_agreement` for diagnosis.

Current status: `v0.16.0` passed the cleaned 25-record development pilot but
failed its first sealed 25-record holdout. Exact final-routing agreement was
`0.92`, decisive-path agreement was `0.72`, schema success was `1.00`, and
manual-review rate was `0.00`. The suite is not approved. The failed holdout is
now an accessed diagnostic set and cannot be reused as a sealed evaluation set
for a tuned successor.

Stability does not establish screening accuracy. The separate 116-record
regression candidate set remains uninspected and expert annotation is pending.
Full-text `v0.1.0` has not yet undergone its planned stability or accuracy
evaluation.
