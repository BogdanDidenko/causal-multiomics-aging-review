# Full-Text Retrieval: 119 Non-Preprint Priority-1 Records

Targets are the 119 non-preprint records in `priority_1_textually_focused`: the previous 135-record manual title/abstract queue minus 16 preprints. `targets.csv`, `retrieval_manifest.jsonl`, `retrieval_adjudication.csv`, `prisma_retrieval.json`, and `summary.json` are the audit trail. `files/` contains locally downloaded PDFs, XML, or public full-text HTML and is intentionally excluded from Git. `selected_files/` is the canonical local view: it contains links only to files selected in the manifest. `raw_metadata/` contains source metadata responses and is also local.

Retrieval uses OpenAlex and Unpaywall OA locations (including explicit publisher PDF links found on verified OA landing pages), Europe PMC free PDFs/full-text XML, Crossref, Semantic Scholar, OpenAIRE, and explicitly recorded public copies, including browser-visible official open full-text HTML. It does not bypass paywalls; `unavailable.csv` lists records without a retrieved legal open full text.

## PRISMA-aligned retrieval subflow

- Priority-1 candidate records: **135**.
- Preprints outside this non-preprint retrieval batch: **16**.
- Non-preprint candidate records audited: **119**.
- Abstract-only reports excluded before report retrieval: **6**.
- Reports sought for retrieval: **113**.
- Reports not retrieved because of verified publisher access controls: **15**.
- Reports retrieved and available for full-text assessment: **98**.
- Reports assessed for eligibility: **pending**.

The 98 retrieved reports comprise 86 PDFs, 11 complete publisher HTML files,
and one XML full text. The equality `113 = 98 + 15` is validated by
`scripts/summarize_prisma_retrieval.py`.

**Post-snapshot correction (2026-08-09):** Docling conversion QA established
that one presumed-complete Springer HTML (`10.1186/s13578-026-01594-z`) has no
article body. The immutable retrieval snapshot above remains reproducible, but
the active downstream PRISMA flow uses 97 sufficient full texts and 16 not
retrieved or insufficient. See
`analysis/docling_graph/full_text_sufficiency_correction_v1.0.0.md`.

This is an interim PRISMA-aligned subflow for the frozen priority-1 manual
queue, not the final review PRISMA denominator. Records outside this priority
queue remain unresolved upstream and must not be represented as excluded. The
16 preprints are outside this batch and are not declared finally excluded by
this retrieval snapshot.
