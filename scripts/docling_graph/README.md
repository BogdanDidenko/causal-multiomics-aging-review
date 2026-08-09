# Docling Graph full-text evidence index

This stage transforms the 98 locally available reports in the frozen
priority-1 retrieval subset into provenance-bearing knowledge graphs. It is a
preprocessing and evidence-localization stage, not an eligibility decision.

The implementation follows the prior review's operational Docling pattern:
isolated environment, corpus manifest, source hashes, per-document artifacts,
one retry, streaming attempt ledger, and resume. It uses Docling Graph 1.9.1
for schema-constrained extraction and deterministic provenance.

## Runtime

```bash
python3 -m venv .venv-docling-graph
.venv-docling-graph/bin/python -m pip install --upgrade pip
.venv-docling-graph/bin/python -m pip install -r scripts/docling_graph/requirements.txt

.venv-docling-graph/bin/python scripts/docling_graph/build_corpus_manifest.py
.venv-docling-graph/bin/python scripts/docling_graph/convert_corpus.py
.venv-docling-graph/bin/python scripts/docling_graph/run_corpus.py --limit 3
.venv-docling-graph/bin/python scripts/docling_graph/run_corpus.py
.venv-docling-graph/bin/python scripts/docling_graph/audit_graph_outputs.py
```

`run_corpus.py` starts a localhost adapter automatically. Every graph call is
executed through the authenticated Codex CLI with:

```text
model: gpt-5.6-luna
reasoning effort: low (Luna Light)
sandbox: read-only
structured output: JSON Schema
```

Raw requests, responses, converted documents, graphs, and provenance ledgers
remain local under `data/full_text_graph/v1.0.0_luna_light/`. The corpus
manifest, corpus summary, attempt ledger, and run summary are versioned.

For faster execution, one adapter may serve deterministic non-overlapping
document shards. Sharding changes scheduling only; every document retains the
same frozen source, template, model, reasoning effort, and extraction contract:

```bash
.venv-docling-graph/bin/python scripts/docling_graph/codex_openai_compat_server.py \
  --port 8766 --model gpt-5.6-luna --reasoning-effort low --timeout 600 \
  --audit-dir data/full_text_graph/v1.0.0_luna_light/audit --quiet

.venv-docling-graph/bin/python scripts/docling_graph/run_corpus.py \
  --external-server --shard-count 3 --shard-index 0
```

Run the last command concurrently for shard indices `0`, `1`, and `2`.

PDF conversion uses one reusable `DocumentConverter` with OCR disabled. Its
lossless Docling JSON is the canonical graph input, so extraction retries do
not repeat layout parsing. Existing successful Docling Graph conversions are
reused by hash when available.

## Methodological boundary

The graph may retrieve evidence but cannot exclude a report. The later
full-text reviewers receive frozen graph artifacts plus source-grounded text.
Eligibility, identification status, and causal evidence Level 0-4 remain
separate criterion-level judgments. A missing graph entity is never treated as
evidence that a criterion failed.

Model-provided evidence quotes are candidate anchors, not final citations. The
quality audit measures exact and formatting-normalized quote support, while
later screening must resolve every decisive citation to canonical Docling
chunks or section IDs.

The completed v1.0.0 run processed 98 retrieval candidates: 97 graphs were
built, one source failed the deterministic full-text sufficiency gate, and no
graph extraction failed. See
[`execution_report_v1.0.0.md`](../../analysis/docling_graph/execution_report_v1.0.0.md).
