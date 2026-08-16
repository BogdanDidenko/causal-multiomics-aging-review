# Full-text routing v1.5.4-rc1

This deterministic amendment reuses the frozen v1.5.3-rc1 model outputs. No
model call, prompt, schema, evidence package, or raw response was changed.

The original route contained 100 assessed reports, 33 exclusions, and 25
manual-review records. Criterion-level short-circuiting moved 19 records with
a five-of-five unanimous decisive failure to exclusion: 13 as EC3 and 6 as
EC4. The amended route contains 100 assessed reports, 52 exclusions, and 6
manual-review records.

`routing_ledger.csv` preserves both routes for every report.
`remaining_manual_review_6.csv` is the active adjudication queue.
`human_adjudication_decisions.csv` records user decisions separately from the
immutable blank form in the v1.5.3-rc1 audit snapshot. All six active records
have been confirmed: one was assessed as eligible and five were excluded.

The resulting full-text eligibility counts are 101 reports meeting eligibility,
57 reports excluded after assessment, and zero pending decisions. The final
ledger and the 162-report retrieval-to-eligibility flow are generated in
`../final_eligibility_v1.5.4/`.

`citation_grounding_audit.json` reports exact-quote validation failures. These
failures never produce an automatic scientific decision: one retry is allowed,
and an unrecovered role slot is routed to adjudication.
