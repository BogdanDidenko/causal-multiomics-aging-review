# Full-Corpus Title/Abstract Screening Report

## Run definition

- Corpus: 7,858 DOI-first deduplicated records.
- DOI audit: 7,580 records with 7,580 unique normalized DOI values; 278 without DOI.
- Abstract-bearing input: 5,022 records, including 4,913 unique DOI values and 109
  stable SHA-based identifiers.
- Missing-abstract queue: 2,836 records; not screened or excluded.
- Runtime: GPT 5.6 Terra Medium through Codex CLI 0.145.0,
  `reasoning.effort=medium`, five independent runs per assessed role.
- Prompt suite: `v1.4.0-rc1`, approval status
  `sealed_holdout_pending_not_active`.
- Frozen runtime revision: `b73c7b21c66de7ee87f266ddaa69f1cab8eab648`.
- Run interval: 2026-08-02 11:58:39 to 15:04:50 UTC.

## Routing results

| Route | Records |
|---|---:|
| Automatic exclude | 2,978 |
| Seek full text | 1,972 |
| Manual review | 72 |
| **Total abstract outputs** | **5,022** |

Automatic exclusions required five-of-five agreement on the same decisive fields
and first-failed criterion. Counts by code were EC1 939, EC2 0, EC3 1,433, EC4 425,
and EC5 181.

The 1,972 full-text routes comprised 700 positive causal bases, 824 unresolved or
non-unanimous scope decisions, 47 unresolved or non-unanimous causal decisions, 397
oversized abstract metadata records, and four conference-metadata issues. All 72
manual-review records failed a role contract after the one allowed retry and were
retained rather than excluded.

## Integrity audit

- Output coverage: 5,022/5,022 records, all record IDs unique.
- Missing, unexpected, or duplicated outputs: 0.
- Duplicate DOI across the 7,858-record canonical corpus: 0.
- Shards completed: 96/96; failed shards: 0.
- Routing recomputation mismatches: 0.
- Accepted evidence spans checked: 130,467; unsupported spans: 0.
- Provider attempts: 28,589 total, 27,539 accepted and 1,050 errors.
- Retry attempts: 978; records still requiring manual review after retry: 72.

## Stability finding

The run passed integrity checks but failed the predeclared 100% all-tracked-field
agreement gate. Exact agreement across all assessed decision fields was 3,624/4,549
(79.7%) among records with completed model assessment, or 72.2% when expressed over
the complete 5,022-record abstract input. Scope agreement was 81.5%; causal-method
agreement was 91.1%.

This distinction is important: conservative routing protects recall because any
disagreement is retained, but it does not make the measurement instrument stable.
The outputs are suitable for prioritization and audit, while `v1.4.0-rc1` remains
unvalidated and inactive pending further prompt calibration and independent gold
evaluation.

The machine-readable sources of truth are `audit.json`, `summary.json`, the 96 shard
manifests, and the raw provider-response JSONL files.
