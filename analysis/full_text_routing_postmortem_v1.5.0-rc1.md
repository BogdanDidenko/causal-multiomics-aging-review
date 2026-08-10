# Full-text routing postmortem: v1.5.0-rc1

## Status

The `v1.5.0-rc1` shared-template full-text run is retained as a **rejected
routing implementation**. Its model responses remain valid experimental
observations, but its Python-derived terminal decisions must not be used as
final eligibility or PRISMA counts.

This postmortem does not overwrite prompts, responses, manifests, ledgers, or
the original stability report.

## Intended invariant

The full-text eligibility stage applies the same criterion contracts and
status functions used at title/abstract screening:

- a causal reviewer is run when all five scope outputs map to `pass`;
- an automatic scope exclusion requires five identical exclusion paths;
- an automatic EC5 exclusion requires five identical sufficient causal
  exclusion paths;
- a positive full-text eligibility route requires five causal outputs that
  map to `retain`;
- unresolved or route-status disagreement is sent to human review;
- taxonomy and inventory fields remain in the audit trail but do not alter a
  route when all five status paths agree.

The final full-text label differs from title/abstract only because this is a
terminal stage: positive records become `assessed` instead of
`seek_full_text`.

## Accidental deviations

Two stricter conditions were introduced in the new full-text processor:

1. The causal reviewer was launched only when all scope decision fields and
   `layer_candidates` were exactly identical across five calls. The intended
   condition was five scope statuses equal to `pass`.
2. A positive result required exact agreement on every causal field, including
   `design_families`. The intended condition was five causal statuses equal to
   `retain`; design-family disagreement should be recorded, not converted into
   a routing disagreement.

These were implementation defects, not planned methodological changes.

## Impact on the frozen 97-record run

- 14 records had five passing scope paths but did not receive causal-reviewer
  calls because non-routing scope details differed.
- 11 records received causal review and had five positive causal paths, but
  were sent to manual review because `design_families` differed.
- Replaying only the corrected deterministic routing function over the stored
  primary outputs changes the primary counts from 69 assessed / 28 manual to
  80 assessed / 17 manual. This replay still leaves the 14 missing causal
  evaluations unresolved and is not a final corrected corpus result.
- Two additional records had separately preserved technical grounding retries.
  They must be reconciled by provenance rather than silently substituted.

## Contract audit

The audit found no other scientific-criterion drift:

- rendering the canonical templates with the title/abstract evidence profile
  is byte-identical to both frozen `v1.4.0-rc1` title/abstract prompts;
- report type, biological scope, aging, multi-omics, causal-basis definitions,
  value enums, criterion order, and consistency rules are unchanged;
- full-text schemas differ from title/abstract schemas only by the intended
  evidence-source domain: `title|abstract` is expanded to
  `title|abstract|chunk:NNNN`;
- five repeats, one retry, Terra Medium, and reasoning effort medium are
  unchanged.

Intended full-text adaptations are deterministic Docling section packaging,
source-grounded section quotes, a full-text evidence-mode instruction, and a
terminal full-text route.

## Reproducibility limitation discovered

The original run manifests recorded the Git revision and prompt, schema,
configuration, and input hashes. The run was executed from a dirty worktree,
but the manifests did not record dirty-worktree state or hashes of the
execution code. Therefore, the Git revision alone does not reconstruct the
exact routing implementation.

Starting with `v1.5.1-rc1`, manifests also record `git_worktree_dirty` and
SHA-256 hashes for the runner, screening, routing, prompt-template, and model
provider modules. Runs should preferably start from a clean committed tree.

## Corrective action

- `v1.5.0-rc1` remains immutable experimental history and is marked rejected
  by this postmortem, not by editing its run artifacts.
- `v1.5.1-rc1` uses route-parity rules and preserves taxonomy disagreement as
  an audit variable.
- Stored model outputs can be deterministically replayed under the corrected
  routing function.
- The 14 records with missing causal calls require a separately versioned
  recovery run. Reconciled results must cite every source run and hash and must
  never replace the source artifacts.
