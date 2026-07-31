# Current prompt status

## Title/abstract screening

The latest configured candidate is `v0.99.0`. It is the most stable candidate
on the independent development set, but it is **not approved for production**:
the one-time sealed `v8` evaluation failed the prespecified 100% exact-agreement
criterion. The manifest status is
`rejected_v0.99.0_sealed_v8_failed`.

The seven current title/abstract prompts are:

- `scope_reviewer.txt` and `scope_reviewer_verifier.txt`;
- `causal_design_reviewer.txt` and `causal_design_reviewer_verifier.txt`;
- `directional_result_reviewer.txt` and
  `directional_result_reviewer_verifier.txt`;
- `adjudicator.txt`.

All are stored under
`protocol/screening/prompts/title_abstract/v0.99.0/`. Their schemas are under
`protocol/screening/schemas/title_abstract/v0.99.0/`, and their immutable hashes
are recorded in `protocol/screening/prompt_manifest.json`.

The runtime uses GPT 5.6 Terra Medium through isolated Codex CLI sessions with
`reasoning.effort=medium`. Three source-only verifier calls independently
evaluate each specialist contract. Python maps a three-way categorical tie to
`unclear`, requires verifier unanimity for exclusionary `no` or `nonempirical`
values, and otherwise performs only declared aggregation, consistency, and
routing rules.

## Stability evidence

Version `v0.99.0` achieved the strongest development result: 100% exact
agreement on final route, decisive criteria, and all tracked categorical fields
across 50 records and five runs. On the sealed 25-record `v8` set, agreement was
96% for final route and 92% for decisive and all tracked criteria. Two records
were unstable and one changed route, so the candidate was rejected.

Earlier one-time sealed tests used different record sets and therefore are not
head-to-head model comparisons:

| Suite | Sealed set | Final route | Decisive | All tracked | Status |
| --- | --- | ---: | ---: | ---: | --- |
| `v0.91.0` | `v6`, 25 records x 5 runs | 1.00 | 0.96 | 0.84 | Rejected |
| `v0.95.0` | `v7`, 25 records x 5 runs | 0.96 | 0.80 | 0.80 | Rejected |
| `v0.99.0` | `v8`, 25 records x 5 runs | 0.96 | 0.92 | 0.92 | Rejected |

Thus `v0.99.0` has the highest observed held-out all-tracked agreement among
these cycles, while `v0.91.0` has the highest observed final-route agreement.
Because each version was evaluated on a different sealed sample, neither fact
establishes that one prompt suite is universally more stable.

## Full-text screening

The current full-text prompts are `v0.1.0`: `section_selector.txt`,
`eligibility_reviewer.txt`, `causal_evidence_reviewer.txt`, and
`adjudicator.txt`. They are stored under
`protocol/screening/prompts/full_text/v0.1.0/`. This suite has not yet completed
its planned full-text stability validation and must be treated as unvalidated.
