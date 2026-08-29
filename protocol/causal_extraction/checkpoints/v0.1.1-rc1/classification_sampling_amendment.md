# Classification stability checkpoint feasibility amendment

## Timing and scope

This amendment was frozen after complete discovery in checkpoint A and before
the first fixed-candidate classifier call in either checkpoint. Checkpoint B
had received no model calls. The prompts, schemas, codebook, model, reasoning
effort, five-repeat contract, deterministic section coverage, and candidate
inventories are unchanged.

## Trigger

Exhaustive discovery in the 15 checkpoint-A reports produced 1,288 distinct
atomic candidate nominations after exact duplicate collapse. The frozen
contract would therefore require 6,440 classifier calls for checkpoint A
alone. One randomized trial contributed 313 candidates because endpoint,
comparator, time-point, and direction differences are intentionally atomic.
This is a feasibility result rather than evidence of classifier instability.

## Amended checkpoint estimand

The immediate experiment estimates repeated-run stability of the fixed
candidate classifier across reports and discovery routes. It does not estimate
claim-discovery recall, full-report extraction completeness, or production
cost.

For each of the 15 reports in each checkpoint, Python selects at most two
frozen candidates before any classifier output exists:

1. one candidate nominated by `open_claim_discovery`, ranked by SHA-256;
2. one candidate nominated by `dense_claim_coverage`, ranked by SHA-256;
3. if either route is absent, remaining positions are filled by SHA-256 rank.

The fixed seed is `20260829-route-balanced-stability`. Candidate text, evidence,
model output, and scientific labels are never used in selection. Every selected
candidate receives five independent Terra Medium classifications. All frozen
candidates remain in the inventory and denominator audit.

## Interpretation

Results are reported separately for checkpoints A and B. Exact five-run and
first-three-run agreement use only the prespecified classifier sample. Reports
with any residual discovery grounding or technical failure remain routed to
manual review regardless of classifier agreement. Full-corpus extraction will
require a separately frozen scaling design, such as validated candidate
consolidation or batching, before production deployment.
