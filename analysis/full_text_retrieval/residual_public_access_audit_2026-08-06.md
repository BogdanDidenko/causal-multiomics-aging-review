# Residual Public-Access Audit (2026-08-06)

This audit covers the 29 records in the frozen 119-record priority-1 full-text
queue that did not have a locally validated full text after the retrieval run
recorded in `data/full_text/v1.1.2_priority_1_nonpreprint_119/`.

## Publicly labelled but not retrievable automatically

The following records have an open-access signal from OpenAlex, Unpaywall, or
Semantic Scholar, but those resolvers expose only the publisher DOI/landing
page, not a repository copy. The publisher endpoints did not provide a
machine-readable full text. No access control or anti-bot challenge was
bypassed.

| DOI | Resolver signal | Result |
| --- | --- | --- |
| `10.1016/j.exger.2025.112815` | Gold, CC BY-NC-ND | ScienceDirect presented a CAPTCHA. No independent public copy located. |
| `10.1016/j.ijbiomac.2026.151713` | Hybrid, CC BY | DOI-only publisher location; no public repository copy located. |
| `10.1016/j.intimp.2026.116452` | Hybrid, CC BY-NC-ND | DOI-only publisher location; no public repository copy located. |
| `10.1016/j.jare.2026.07.047` | Gold, CC BY-NC-ND | ScienceDirect presented a CAPTCHA. No independent public copy located. |
| `10.1016/j.jhazmat.2026.142949` | Hybrid, CC BY | DOI-only publisher location; no public repository copy located. |
| `10.1016/j.phymed.2025.156697` | Hybrid, CC BY-NC-ND | DOI-only publisher location; no public repository copy located. |
| `10.1111/jcpe.14040` | Publisher PDF reported by resolvers | Wiley landing page exposed the abstract but not the complete article without access. |

Two further records are conference/supplement abstracts. Their publisher pages
provide the complete abstract, but not a full research article with methods,
results, and references. They therefore remain unavailable for full-text
screening rather than being misclassified as retrieved studies:

| DOI | Record type |
| --- | --- |
| `10.1093/jimmun/vkag141.260` | Journal supplement abstract |
| `10.1182/blood-2025-3244` | Blood supplement abstract |

## Confirmed non-open records

The remaining 20 records had no OA location in OpenAlex/Unpaywall and no
public full text in Semantic Scholar or OpenAIRE at the time of retrieval.
They remain in `unavailable.csv` with `no_open_full_text_found` and are not
treated as paywall-bypass candidates.

## Independent repository check

For `10.1038/s42255-020-0200-2`, OpenAIRE supplied a Max Planck PuRe handle.
The handle resolved to a public repository anti-bot challenge rather than a
document. The challenge was not solved or circumvented. No other repository
location was returned by the metadata services.
