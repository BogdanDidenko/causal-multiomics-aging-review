# Full-Text Retrieval: 119 Non-Preprint Priority-1 Records

Targets are the 119 non-preprint records in `priority_1_textually_focused`: the previous 135-record manual title/abstract queue minus 16 preprints. `targets.csv`, `retrieval_manifest.jsonl`, and `summary.json` are the audit trail. `files/` contains locally downloaded PDFs, XML, or public full-text HTML and is intentionally excluded from Git. `selected_files/` is the canonical local view: it contains links only to files selected in the manifest. `raw_metadata/` contains source metadata responses and is also local.

Retrieval uses OpenAlex and Unpaywall OA locations (including explicit publisher PDF links found on verified OA landing pages), Europe PMC free PDFs/full-text XML, Crossref, Semantic Scholar, OpenAIRE, and explicitly recorded public copies, including browser-visible official open full-text HTML. It does not bypass paywalls; `unavailable.csv` lists records without a retrieved legal open full text.

This retrieval obtained 82 PDFs and 1 XML and 7 public HTML full texts. The remaining 29 records are listed in `unavailable.csv`.
