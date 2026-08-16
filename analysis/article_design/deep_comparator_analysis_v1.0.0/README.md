# Deep comparator analysis v1.0.0

This package records a full-text, role-separated analysis of two article-design
comparators for the causal multi-omics aging review:

1. Castro-Fernandez et al., *A systematic review on age-related macular
   degeneration: New insights from multi-omics studies*.
2. Kerr et al., *A scoping review and proposed workflow for multi-omic rare
   disease research*.

The exact local source files, licenses, provenance, byte sizes, and SHA-256
hashes are recorded in
`data/full_text/article_design_comparators_v1.0.0/manifest.json`. The downloaded
PDF and XML files are intentionally gitignored.

Four independent agents read both complete articles and examined different
parts of article design:

- review methodology and evidence appraisal;
- Results, tables, figures, and synthesis units;
- scientific narrative and section architecture;
- skeptical peer review and overclaiming risks.

Their role-specific conclusions are preserved in `independent_reviews.md`.
`synthesis.md` contains the integrated recommendation, and
`table_figure_spec.md` defines the proposed displays and their data units.
`comparator_inventory.md` records the source structures that support those
recommendations. `agent_manifest.json` identifies the independent runs and their
shared inputs.

This is an article-design analysis, not a screening stage. It does not alter the
PRISMA denominator or the full-text eligibility ledger.

## Central decision

The paper should be a systematic evidence map organized first by evidence
function and causal design family:

1. formal causal hypothesis/discovery;
2. causal-effect evidence;
3. independent validation or triangulation of the same causal link.

Aging constructs, systems, tissues, omics layers, and mechanisms are dimensions
of this map. They are not the primary evidence hierarchy. Levels 0-4 remain
internal coding variables and must not become article headings or a universal
quality scale.

## Current evidence boundary

The current full-text flow is 162 reports sought, 4 not retrieved, 158 assessed,
57 excluded, and 101 meeting full-text eligibility. These 101 are candidates
entering causal evidence extraction. They are not yet 101 independent studies,
101 independent causal links, or the final Level 2-4 synthesis set.
