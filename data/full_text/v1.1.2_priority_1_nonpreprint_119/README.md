# Full-Text Retrieval: 119 Non-Preprint Priority-1 Records

Targets are the 119 non-preprint records in `priority_1_textually_focused`: the previous 135-record manual title/abstract queue minus 16 preprints. `targets.csv`, `retrieval_manifest.jsonl`, and `summary.json` are the audit trail. `files/` contains locally downloaded open PDFs or Europe PMC XML and is intentionally excluded from Git. `selected_files/` is the canonical local view: it contains links only to files selected in the manifest. `raw_metadata/` contains source metadata responses and is also local.

Retrieval uses OpenAlex-confirmed OA locations (including explicit publisher PDF links found on their OA landing pages) and Europe PMC free PDFs/full-text XML. It does not bypass paywalls; `unavailable.csv` lists records without a retrieved legal open full text.

This retrieval obtained 78 PDFs and 1 XML full text. The remaining 40 records are listed in `unavailable.csv`.
