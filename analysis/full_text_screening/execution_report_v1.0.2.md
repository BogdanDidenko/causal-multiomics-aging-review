# Full-text screening evaluation v1.0.2

## Status

This is a complete 97-report corpus evaluation of a candidate instrument. It
is not expert-gold validation and does not provide final PRISMA exclusion or
synthesis counts.

- Model: GPT 5.6 Terra Medium (`gpt-5.6-terra`), reasoning effort `medium`.
- Roles: eligibility reviewer and causal-evidence reviewer.
- Repeats: five independent runs per role and report.
- Input: 97 DOI-unique sufficient full texts.
- Evidence source: deterministic Docling chunks; frozen Luna Light graphs were
  used only to prioritize grounded chunks.
- Execution: 24/24 shards complete, 97/97 records, no failed shard.
- Git revision: `66eae77995ffcae478a15d23dcdd96394fc1f704`.

## Citation ablation

One fixed smoke-test report was used only to verify runtime contracts before
the corpus evaluation. It was not used to assess scientific accuracy.

| Candidate | Attempts | Validation errors | Valid outputs | Result |
|---|---:|---:|---:|---|
| v1.0.0 | 14 | 5 | 9 | role execution failed |
| v1.0.1 short-quote instruction | 12 | 5 | 7 | role execution failed |
| v1.0.2 deterministic grounding | 10 | 0 | 10 | valid; criterion disagreement |

The v1.0.2 repair is non-semantic. It may preserve source whitespace or select
the longest contiguous source-word span of at least three words from the same
chunk. It cannot change a section ID, use semantic similarity, or create an
unsupported citation. Raw output, repaired span, and both forms are retained
in the local audit.

## Corpus result

- Strict all-configured-field route: 3/97 assessed; 94/97 manual review.
- Manual reasons: 88 five-run criterion disagreements and 6 exhausted role
  executions.
- Strict levels: one Level 2 and two Level 3 reports.
- Numeric Level 0-4 exact across all five runs: 43/97 (44.3%).
- Exact run-level signature including four consistently unresolved records:
  47/97 (48.5%).
- Stable numeric levels: Level 0, 5; Level 2, 6; Level 3, 32.
- Model attempts: 1,033; failed attempts before retry/manual routing: 93 (9.0%).
- Calls requiring deterministic quote repair: 486; repaired spans: 1,291.

The three strict assessments were StackAge (Level 2), Midkine as a driver of
age-related mammary change (Level 3), and senolytic rejuvenation of the aged
kidney (Level 3). These labels remain provisional until expert adjudication.

## Criterion stability

Rates below use the 91 reports with complete outputs from both roles.

| Field | Five-run unanimity |
|---|---:|
| causal claim present | 100.0% |
| relevant causal design | 100.0% |
| aging-process relevance | 100.0% |
| multi-omics status | 95.6% |
| assumptions assessable | 92.3% |
| full text sufficient | 91.2% |
| identification status | 90.1% |
| primary design family | 89.0% |
| first failed criterion | 87.9% |
| integration mode | 70.3% |
| validation strength | 68.1% |
| aging role | 56.0% |
| estimand complete | 52.7% |
| supporting design families | 46.2% |

## Interpretation

The candidate does not satisfy the predeclared stability gate. In particular,
the strict route blocks assessment on descriptive fields such as aging role,
integration mode, and supporting design families even when the derived causal
Level is stable. This corpus must not be used to tune a replacement prompt.
The next calibration should use a separate development set and predeclare
which atomic fields affect eligibility, causal Level, design-family reporting,
or descriptive extraction. The 97 records remain an evaluation set.

Machine-readable artifacts:

- `data/full_text_screening/v1.0.0_graph_chunks_97/evaluation_v1.0.2/stability_summary.json`
- `data/full_text_screening/v1.0.0_graph_chunks_97/evaluation_v1.0.2/stability_ledger.csv`
- `data/full_text_screening/v1.0.0_graph_chunks_97/evaluation_v1.0.2/prisma_full_text_screening.json`
