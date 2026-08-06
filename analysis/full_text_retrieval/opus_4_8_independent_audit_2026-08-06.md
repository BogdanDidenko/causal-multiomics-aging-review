# Independent Opus Retrieval Audit: Five Unresolved OA Records

Date: 2026-08-06

## Purpose

An independent Claude Opus 4.8 agent audited five unresolved records after the
project retrieval pipeline had exhausted OpenAlex, Europe PMC, Crossref,
Semantic Scholar, OpenAIRE, Unpaywall, canonical publisher routes, and explicit
author-hosted copies. The agent was restricted to lawful public sources and was
explicitly prohibited from using credentialed access, paywall bypasses,
ResearchGate downloads, Sci-Hub, LibGen, or document-sharing services.

## Result

No new stable, lawful, machine-retrievable full-text URL was found. The agent
queried Crossref, Unpaywall, Europe PMC, DOI resolution, and official publisher
pages. Unpaywall confirmed that all five records are OA at the publisher, but
did not provide a distinct repository full text. Ordinary HTTP retrieval of the
publisher pages produced anti-bot/challenge HTML instead of the article PDF or
full-text HTML.

| DOI | Unpaywall OA status | License | Independent finding |
| --- | --- | --- | --- |
| `10.1016/j.celrep.2024.115099` | gold | CC BY-NC-ND | No repository copy; Elsevier route returned non-article HTML. |
| `10.1016/j.exger.2025.112815` | gold | CC BY-NC-ND | No repository copy; Elsevier route returned non-article HTML. |
| `10.1016/j.jare.2026.07.047` | gold | CC BY-NC-ND | No repository copy; Elsevier route returned non-article HTML. |
| `10.1093/brain/awaf282` | hybrid | CC BY | Official PDF location known, but it returned anti-bot HTML to the HTTP client. |
| `10.1186/s13578-026-01594-z` | gold | CC BY-NC-ND | Official Springer page returned a challenge page; no stable public PDF URL was exposed. |

This is a negative retrieval-control result. It does not alter the frozen
119-DOI target set, the 85 downloaded full-text artifacts, or the unresolved
record classifications in the retrieval manifest.
