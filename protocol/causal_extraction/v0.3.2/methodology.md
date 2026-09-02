# Causal extraction methodology v0.3.2

## Purpose

This prospective ablation tests whether splitting the compound `v0.3.1`
classification into narrow role contracts improves repeated-run agreement.
The experiment remains development-only.

## Inputs

The 12 reports and 45 neutral candidates are inherited unchanged from the
frozen `v0.3.1` suite. Eligibility is evaluated for all 45 candidates. Detailed
roles are evaluated for the 28 candidates that received `include` in all five
prior `v0.3.1` runs. This set was generated mechanically and frozen before the
first `v0.3.2` output; majority voting was not used.

Every role receives the complete deterministic evidence-atom packet for the
report and the relevant fixed candidate scaffold. No model, graph, embedding,
lexical filter, or section selector chooses the source text.

## Roles

1. `eligibility` returns six atomic criteria. Python derives qualification and
   the first failed criterion in a frozen order.
2. `design_identity` returns causal basis, design family, and variation source.
3. `review_context` returns aging role and multi-omics role.
4. `effect_appraisal` returns contrast status, assumptions reviewability, and
   result status.
5. `validation` returns validation strength.

The role contracts retain the `v0.3.1` field definitions. No paper-specific
examples or labels were added. Python validates candidate coverage, attaches
frozen evidence IDs, combines role records, and derives Level. It does not
classify source text.

## Runtime and evaluation

Each report-role pair is run five times in isolated Codex CLI sessions with
GPT-5.6 Terra Medium. The design contains 300 planned calls. Runs 1-3 and 1-5
form the prespecified stability views. Exact agreement is reported per field,
per candidate, per role, and for the combined record. Majority voting is
prohibited.

Passing this experiment would establish conditional extraction stability on
the development sample. Automated candidate discovery and independent expert
accuracy validation remain separate gates before production.
