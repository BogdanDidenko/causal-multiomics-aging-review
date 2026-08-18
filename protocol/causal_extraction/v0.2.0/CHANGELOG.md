# Causal extraction codebook v0.2.0 change log

## Status

Instrument-development revision. This version has passed source-grounded
boundary regression checks, but it is not a frozen production instrument or an
expert gold standard.

## Basis for revision

Version 0.1.0 was drafted by the primary analyst and applied to 20 claims from
15 purposively heterogeneous reports. Claude Opus 5 then reviewed the draft,
all claim records, and the frozen source texts in read-only mode. The primary
analyst checked every substantive recommendation against the sources and
recorded the disposition in the cross-audit.

## Accepted changes

- Separate exhaustive report extraction from boundary-case testing.
- Split compound claims by operation, endpoint family, and materially different
  population or time stratum.
- Distinguish variation source from assignment mechanism.
- Record link-specific variation sources for multi-link mediation claims.
- Replace free-text assumptions with closed, design-specific domains.
- Derive contrast completeness from six atomic components.
- Distinguish rescue from effect modification or epistasis.
- Use controlled molecular-layer and analytical-role vocabularies.
- Record source adequacy and field-level evidence anchors.
- Derive Levels and Level 4 qualification in Python rather than asking the
  reviewer to set them.
- Restrict Level 4 to three frozen same-link paths: independent replication,
  independent orthogonal identification, or appropriate colocalization of a
  genetic-instrument claim.

## Adjudicated pilot changes

- FOCUS candidate prioritization was recoded from Level 2 to Level 1 because it
  ranks candidate genes but does not identify a directed effect.
- The HOTAIRM1 record was routed to manual review because the frozen document is
  a subscription preview, not a sufficient full text.
- The PESA mediation assumptions were corrected to reflect the assumptions and
  sensitivity analyses explicitly reported by the authors.
- The CASP8 result anchor was expanded to preserve the reported negation and
  therefore the polarity of the result.

## Evidence trail

The frozen v0.1.0 records, primary self-audit, complete Claude output, primary
cross-audit, and row-level adjudications remain under
`analysis/causal_extraction/codebook_pilot_v0.1.0/`. They are not overwritten
by this revision.
