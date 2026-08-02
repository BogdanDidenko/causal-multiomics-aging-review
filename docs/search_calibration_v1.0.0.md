# Search Calibration v1.0.0

## Pilot status

The 2026-08-02 API pilot tested the combined v1 database-native queries with a
cap of 500 retrieved records per source. It is a count/quality pilot, not the
final search and not a PRISMA denominator. The complete retrieval remains
blocked on manual branch QA and verification of at least 100 canonical
positives by two independent experts.

| Database | Reported count | Pilot records | Local three-block | Explicit branch available | Layer-pair branch available |
| --- | ---: | ---: | ---: | ---: | ---: |
| PubMed | 2,133 | 500 | 460 | 232 | 365 |
| Europe PMC | 1,651 | 500 | 493 | 320 | 363 |
| Scopus | 3,887 | 500 | 1 | 11 | 22 |
| Semantic Scholar | 3,494 | 500 | 170 | 164 | 333 |
| Springer Nature | 11,896 | 500 | 32 | 123 | 149 |
| OpenAlex | 32,273 | 500 | 51 | 5 | 120 |

The source total is 3,000 sampled records; 1,207 satisfy the local explicit-or-
pairwise multi-omics, aging, and causal-anchor check. Local checks are retrieval
diagnostics only and do not determine study eligibility.

The deterministic QA sheets provide 50 records per available branch. Before
human review, the local three-block diagnostic was 49/50 and 49/50 for Europe
PMC, 47/50 and 47/50 for PubMed, 21/50 and 23/50 for Semantic Scholar, 6/50 and
4/50 for Springer Nature, and 2/5 and 21/50 for OpenAlex (explicit and
layer-pair respectively). Scopus supplied 11 and 22 title-only candidates.
These differences confirm that one numeric count cannot be interpreted as one
common retrieval precision across databases.

Every source manifest records the exact query and hash, reported and retrieved
counts, branch diagnostics, normalized CSV hash, and SHA-256/size of every raw
response. The run manifest is
`data/searches/pilots/2026-08-02-v1.0.0/search_run_manifest.json`.

The initial canonical article passed exact inclusion tests in PubMed, Europe
PMC, Scopus, Springer Nature, and OpenAlex (`combined query AND DOI`) and was
also present in the Semantic Scholar combined-query sample and DOI endpoint.
This verifies one anchor only; it does not satisfy the 100-record
two-expert-adjudicated freeze gate.

## Expanded canonical-positive candidate pool

The pilot corpus was algorithmically stratified into 120 study-level
candidates for expert review. The pool uses formal causal-design terms, an
aging construct, and explicit or pairwise multi-omics evidence only as
prioritization signals. All expert and adjudication fields remain `pending`;
these records are candidates, not confirmed positives or gold labels.

The current pool contains 68 genetic-instrument, 45 direct-perturbation, three
formal-mediation, three structural-equation-model, and one randomized-
intervention candidates. No sufficiently strong candidates were recovered for
the prespecified quasi-experimental, temporal-identification, DAG/SCM,
Bayesian-network, or causal-discovery-algorithm families. Those absences are a
trigger for targeted supplemental retrieval, not evidence that the families
are absent from the literature.

The auditable pool and generation metadata are stored in
`protocol/search_calibration/v1.0.0/canonical_positive_candidates_120.csv` and
its adjacent manifest. Query freeze requires at least 100 eligible positives
after independent criterion-level review by two experts and adjudication of
disagreements.

The frozen candidate queue can be regenerated from the pilot snapshot with:

```bash
python scripts/build_canonical_candidate_pool.py \
  data/searches/pilots/2026-08-02-v1.0.0/normalized/all_sources.csv \
  protocol/search_calibration/v1.0.0/canonical_positive_candidates_120.csv \
  --size 120 \
  --minimum-verified-positives 100 \
  --generated-date 2026-08-02
```

## Unresolved quality gates

- Manual relevance fields in all QA sheets are blank and must be completed.
- Scopus fell back to the `STANDARD` API view because this key has no abstract
  entitlement. Title-only local classification undercounts both branches and
  yielded fewer than 50 QA candidates.
- The broad OpenAlex query produced only five explicit-multiomics candidates
  in the top 500. A branch-specific or deeper deterministic sample is required
  to reach 50.
- Google Scholar manual calibration is pending.
- The canonical-positive registry contains one pending anchor. The expanded
  120-record review queue remains unadjudicated, below the required 100
  confirmed positives.

Queries therefore remain `calibration_pending_expert_query_review`; they must
not be labelled frozen or used for final extraction yet.
