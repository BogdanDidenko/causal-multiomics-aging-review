# Canonical-candidate AI annotation, 2026-08-02

## Status and purpose

This run provides a complete assistant annotation of the 120-record
canonical-positive candidate queue. It is a prioritization and instrument-
development artifact, not an expert gold standard. It does not populate the
`expert_1_*`, `expert_2_*`, or adjudicated gold fields and cannot satisfy the
two-independent-expert query-freeze requirement.

## Input QA

The queue was derived from the 3,000-record v1 database pilot. A post-selection
study-version check identified five preprint/publication pairs with different
DOIs. The journal versions were retained, the preprints were logged as
superseded, and five replacement candidates were screened. The final input
therefore contains 120 distinct study-level records. The exact mappings are in
`protocol/search_calibration/v1.0.0/study_version_deduplication_log.csv`.

## Repeated model annotation

Every record was evaluated with the frozen v1 `scope_reviewer` and, when scope
passed, `causal_method_reviewer`. Each assessed role ran five times with GPT
5.6 Terra Medium through Codex CLI 0.145.0 at `reasoning.effort=medium`. Raw
provider responses, retry errors, result JSONL files, and runtime manifests are
preserved under `data/screening/v1_canonical_ai_preliminary/runs/`.

Before assistant review, the repeated model outputs produced:

| Preliminary result | Records |
| --- | ---: |
| Include | 86 |
| Exclude | 19 |
| Unclear or technical manual review | 15 |

Exact agreement across all assessed tracked fields occurred in 86/120 records
(71.7%). This fails the prespecified 100% stability gate. Field-level agreement
was:

| Field | Exact / assessed | Rate |
| --- | ---: | ---: |
| Report type | 116/116 | 100.0% |
| Biological/health scope | 116/116 | 100.0% |
| Aging-process relevance | 114/116 | 98.3% |
| Multi-omics evidence | 106/116 | 91.4% |
| Current-report layer use | 114/116 | 98.3% |
| Current-report causal application | 89/90 | 98.9% |
| Causal basis | 89/90 | 98.9% |
| Design families | 73/90 | 81.1% |
| Causal-information sufficiency | 90/90 | 100.0% |

The provider produced 1,097 schema-valid role outputs. Ninety failed attempts
were retained, including 82 retry attempts. Four records still had a role-
execution failure after retry; their exact failure text remains in the raw
logs. Technical failures and scientific disagreement were not recoded as
stable after manual review.

## Assistant adjudication

The assistant reviewed all 15 preliminary-unclear records against the complete
title and abstract and independently confirmed all 19 preliminary exclusions.
This produced 34 criterion-level eligibility adjudications. The assistant also
resolved 24 primary-design-family disagreements. Every manual evidence quote
is validated as an exact title/abstract substring.

| Final assistant status | Records |
| --- | ---: |
| Include | 95 |
| Exclude | 23 |
| Seek full text | 2 |

Exclusions comprised 11 EC3 aging-scope failures, 11 EC4 multi-omics failures,
and one EC5 causal-method failure. The 95 included candidates were classified
into 57 genetic-instrument, 27 direct-perturbation, eight nonrandomized-
intervention, two randomized-intervention, and one SEM primary design.

The two unresolved records concern premature ovarian failure/ovarian aging
(`10.1007/s12031-025-02314-x`) and roX-mediated heterochromatinization
(`10.1038/s44319-026-00791-8`). Their abstracts do not resolve aging-role and
omics-scale assay boundaries, respectively, so both require full text.

## Interpretation

The candidate queue is useful: 95 records are high-priority title/abstract
inclusions after assistant review. It is still five below the planned minimum
of 100 even before independent expert verification. More importantly, the
prompt suite fails the 100% repeated-run stability requirement, driven mainly
by molecular-layer classification and design-family assignment. Queries remain
unfrozen, expert fields remain pending, and these labels must not be reported as
gold-standard accuracy.

## Reproduction

```bash
python scripts/summarize_canonical_ai_annotation.py \
  data/screening/v1_canonical_ai_preliminary/study_deduplicated/input.csv \
  data/screening/v1_canonical_ai_preliminary/runs \
  analysis/v1_methodology/canonical_candidate_ai_annotation_2026-08-02.csv \
  analysis/v1_methodology/canonical_candidate_ai_annotation_2026-08-02.summary.json \
  --allow-superseded

python scripts/finalize_canonical_ai_annotation.py \
  analysis/v1_methodology/canonical_candidate_ai_annotation_2026-08-02.csv \
  data/screening/v1_canonical_ai_preliminary/study_deduplicated/input.csv \
  analysis/v1_methodology/canonical_candidate_assistant_adjudication_2026-08-02.csv \
  analysis/v1_methodology/canonical_candidate_design_family_adjudication_2026-08-02.csv \
  analysis/v1_methodology/canonical_candidate_final_ai_annotation_2026-08-02.csv \
  analysis/v1_methodology/canonical_candidate_final_ai_annotation_2026-08-02.summary.json
```
