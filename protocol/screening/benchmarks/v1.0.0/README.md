# v1 Gold-standard Benchmarks

The v1 benchmark records must be sampled from the newly frozen v1 search
corpus, not from the rejected v0.x prompt outcomes. Run:

```bash
python scripts/build_v1_benchmark_sets.py data/normalized/v1_canonical.csv \
  --stage title_abstract
```

This creates a 30-record codebook pilot, an 80-record development set, and a
100-record sealed set. The three files are disjoint. After eligible full texts
are acquired, create the separate 60-paper benchmark with `--stage full_text`.

Sampling strata are retrieval branch, abstract thickness, and broad
design-anchor family. These fields are used only to diversify sampling; they
are not gold labels and never determine eligibility.

Two experts independently complete every `expert_1_*` and `expert_2_*` field.
They then resolve disagreements in the corresponding `adjudicated_*` fields.
Model outputs must not be shown during initial annotation. The sealed set may
be opened only once after prompts, schemas, code, runtime, and acceptance
thresholds are frozen in Git.

No benchmark CSV is committed yet because the v1 retrieval has not been
frozen. Creating placeholder records or model-generated expert labels would
invalidate the planned accuracy evaluation.
