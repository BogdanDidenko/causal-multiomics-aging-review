# Browser PDF Recovery Follow-up (2026-08-08)

This follow-up records a browser-assisted check of seven publisher links that
metadata resolvers had labelled as open or as having a publisher PDF. The check
used the publisher pages and their normal PDF controls. No access control,
anti-bot challenge, or paywall was bypassed.

## Recovered publisher PDFs

Four complete publisher PDFs were available through the ScienceDirect browser
PDF viewer and were validated locally before ingestion.

| DOI | Pages | Bytes | Manifest status |
| --- | ---: | ---: | --- |
| `10.1016/j.exger.2025.112815` | 12 | 8,034,790 | `downloaded_pdf` |
| `10.1016/j.jare.2026.07.047` | 20 | 6,977,796 | `downloaded_pdf` |
| `10.1016/j.jhazmat.2026.142949` | 21 | 25,770,831 | `downloaded_pdf` |
| `10.1016/j.phymed.2025.156697` | 17 | 16,858,835 | `downloaded_pdf` |

Each selected file begins with the PDF magic bytes, is readable by `pdfinfo`,
and is recorded in `retrieval_manifest.jsonl` with its SHA-256 digest.

## Resolver false-positive access signals

Three records were not publicly downloadable despite resolver metadata that
suggested a publisher PDF or an open/hybrid location.

| DOI | Publisher result |
| --- | --- |
| `10.1016/j.ijbiomac.2026.151713` | ScienceDirect displayed `Purchase PDF` and institutional access only. |
| `10.1016/j.intimp.2026.116452` | ScienceDirect displayed `Purchase PDF` and institutional access only. |
| `10.1111/jcpe.14040` | Wiley displayed institutional login and paid PDF access. |

These remain `open_location_unavailable`; resolver licence and location fields
must not be treated as proof of unauthenticated full-text availability.

## Updated retrieval denominator

The frozen queue remains 119 records. After this recovery pass, 98 have a
locally validated full text: 86 PDFs, 11 complete publisher HTML files, and one
XML full text. The remaining 21 records comprise 16 with no open full text found
and five with an open-location signal that did not yield an eligible full text.
