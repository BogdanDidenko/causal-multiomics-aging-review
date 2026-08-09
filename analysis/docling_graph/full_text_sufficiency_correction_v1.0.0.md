# Full-text sufficiency correction

Date: 2026-08-09  
Stage: Docling conversion before full-text screening  
Affected DOI: `10.1186/s13578-026-01594-z`

## Finding

The frozen retrieval snapshot classified the local Springer HTML as a complete
publisher full text. Deterministic Docling conversion produced an unexpectedly
small document. Manual source inspection then found only 719 visible body-text
characters: the archived file contains article metadata, styles, and an
access/challenge shell, but no article body.

The publisher PDF endpoint returned HTTP 404. The identifier-based Springer
Nature Open Access API response contained the abstract and back matter but no
article body. OpenAlex identified the journal article as gold open access but
did not provide a public PDF or repository copy. Therefore the local artifact
is insufficient for full-text assessment.

## PRISMA correction

The original retrieval snapshot remains unchanged as an audit artifact. The
active downstream flow applies this correction:

| Item | Original snapshot | Corrected active count |
|---|---:|---:|
| Reports sought for retrieval | 113 | 113 |
| Reports retrieved and sufficient for full-text assessment | 98 | 97 |
| Reports not retrieved or insufficient | 15 | 16 |

This is a retrieval-status correction, not a scientific eligibility exclusion.
The report is recorded under EC7 only if the full text remains unavailable at
the final retrieval update. It is not submitted to graph extraction or model
eligibility review using abstract-only content.

The machine-readable check is
[`full_text_sufficiency_audit.csv`](../../data/full_text_graph/v1.0.0_luna_light/full_text_sufficiency_audit.csv).
