# Methodology architecture sources

Five independent GPT-5.6 Terra Medium sessions read the complete local source
documents in separate ephemeral Codex sessions. The run used no section
selection, splitting, truncation, or size-based exclusion. Each result is a
source-specific architectural memo with source locators.

The sources are WHO-FIC Content Model, SEI Views and Beyond, GO annotations,
the Nickerson, Varshney and Muntermann taxonomy-development paper, and W3C
PROV-DM. Their convergent
implication for this review is captured in `architecture_synthesis.md`.

The raw source files and full prompt/session audit remain local in `raw/` and
`terra_sessions/calls/`. The source manifest records URLs and hashes; compact
Terra memos, run completion state, and the cross-source synthesis are suitable
for version control.
