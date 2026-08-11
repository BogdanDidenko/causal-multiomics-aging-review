# Full-Text Retrieval: 65 Frozen Records

Targets are the records in `oversized_20k_seek_full_text_followup` from the supplied frozen cohort. `targets.csv`, `retrieval_manifest.jsonl`, and `summary.json` are the audit trail. `files/` contains locally downloaded PDFs, XML, or public full-text HTML and is intentionally excluded from Git. `selected_files/` is the canonical local view: it contains links only to files selected in the manifest. `raw_metadata/` contains source metadata responses and is also local.

Retrieval uses OpenAlex and Unpaywall OA locations (including explicit publisher PDF links found on verified OA landing pages), Europe PMC free PDFs/full-text XML, Crossref, Semantic Scholar, OpenAIRE, and explicitly recorded public copies, including browser-visible official open full-text HTML. It does not bypass paywalls; `unavailable.csv` lists records without a retrieved legal open full text.

This retrieval obtained 21 PDFs and 14 XML and 9 public HTML full texts. The remaining 21 records are listed in `unavailable.csv`.

## Three-Strategy Recovery Addendum

The 21 initially unavailable records were independently retried with
repository/API-first, version/author-copy, and publisher/browser-first
strategies. The frozen combined selection recovered 17 additional target
reports, leaving 4 not retrieved. Eleven recovered files are standalone
reports, an accepted manuscript, or a thesis; six are exact non-article target
contents (proceedings, conference abstracts, or a title index) retained so the
report-type criterion can be resolved during screening. See
`agent_recovery/prisma_recovery_addendum.json` and
`agent_recovery/combined/manifest.jsonl`.
