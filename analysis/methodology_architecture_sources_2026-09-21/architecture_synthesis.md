# Architecture Patterns for the Review Data Model

Date: 2026-09-21

## Why these sources matter here

The disagreement in the transfer check was concentrated in the count of flat
`causal analysis` records. The models consistently recognized whether a report
contained causal work and what broad design family it used. They differed when
deciding whether treatment arms, separate targets, reverse directions,
replication, or sensitivity estimators were independent analyses.

The five methodology sources converge on a useful resolution: preserve a rich,
canonical graph of distinct entities and relations, then generate simple,
purpose-specific views for screening, Results tables, PRISMA, and validation.
The canonical graph may be many-to-many; a table view may deliberately use
mutually exclusive categories.

## Proposed canonical entities

`ReportVersion -> Study -> CausalWorkflow -> CausalLink -> Contrast`

`Validation` and `SourceEvidence` attach to the entity or relation they assess.
`ExtractionAssertion` records what a reviewer or model asserted from a source,
and preserves competing interpretations instead of overwriting them.

| Entity | Meaning | Why it stays separate |
|---|---|---|
| `ReportVersion` | One citable preprint, publisher article, supplement, correction, or revision. | A report is not necessarily an independent study. Version linkage is provenance, not scientific duplication. |
| `Study` | A bounded empirical investigation, cohort, experiment, or dataset application. | One study can generate several reports and workflows. |
| `CausalWorkflow` | A coherent causal procedure within a study, such as an intervention analysis, bidirectional MR, or mediation workflow. | It is the parent for related links and distinguishes method-level identity from individual results. |
| `CausalLink` | One directed, normalized relationship between exposure/intervention and outcome in a stated system. | This is the biological synthesis unit. It may have several contrasts and several supporting tests. |
| `Contrast` | The exact comparison, estimand, direction, time point, arm, dosage, or subgroup used for a link. | A link can be evaluated through several contrasts without becoming several unrelated biological claims. |
| `Validation` | A replication, rescue, orthogonal assay, sensitivity analysis, negative control, or challenge. | Validation has a target and result; a study-level Boolean loses that information. |
| `SourceEvidence` | A local quotation, table, figure, method, supplement, or data statement. | Every substantive extracted assertion needs a traceable locator. |
| `ExtractionAssertion` | A model or human interpretation of a source item. | Competing or corrected extractions remain auditable. |

## How this resolves the four observed disagreements

| Example | Canonical representation | Reader-facing synthesis view |
|---|---|---|
| Urolithin A in worms and human cells | One UA workflow with multiple links and target-specific child contrasts; mammalian validation linked as a separate validation activity. | One biological mechanism row, with a countable set of validated links if needed. |
| High- and low-temperature pear storage | One temperature-intervention workflow, two treatment contrasts, and separate targeted Novel_188/Pbr027651.1 links. | One intervention row plus one validated regulatory-link row. |
| mtDNA and epigenetic aging | One mediation workflow and one bidirectional MR workflow; forward/reverse directions are links or contrasts according to their input/instrument change. | Separate forward and reverse results, including the reverse null, without inflating the workflow count. |
| BAMA and univariate mediation | One mediation workflow with an exploratory BAMA result and a univariate validation/challenge result. | One hypothesis-level row whose credibility field records the failed univariate confirmation. |

## Views, not a universal table

The model should generate several linked linearizations rather than force every
question into one table:

1. **PRISMA/report view:** reports, retrieval, eligibility, versions and study linkage.
2. **Evidence-base view:** studies, systems, aging constructs, publication form and workflow families.
3. **Causal-link view:** exposure, outcome, direction, contrast, causal basis, design and result.
4. **Multi-omics view:** layer provenance, integration operator and the role each layer plays in a workflow.
5. **Validation/transport view:** target link, validation activity, result, independence, species/tissue/time transfer.
6. **Audit view:** reviewer assertion, source evidence, version, adjudication and provenance.

Each view uses its own controlled vocabulary and cardinalities. The mapping
between views is first-class data. A PRISMA report count must never be labeled
as a causal-link count, and a sensitivity test must not automatically be
counted as a new workflow.

## Provenance pattern

Use the W3C PROV distinction:

- an `Entity` is a report version, evidence passage, causal-link assertion, or validation result;
- an `Activity` is screening, extraction, causal estimation, source checking, or validation;
- an `Agent` is an author group, human curator, Terra session, Opus session, or deterministic script;
- `used`, `generated`, `wasDerivedFrom`, and `wasAssociatedWith` preserve the path from source text to review conclusion.

This makes it possible to state, for example: a human-adjudicated causal-link
assertion was generated by reconciliation, used a specific report version and
evidence atoms, and was informed by two independent model drafts. That is much
more precise than attaching a generic confidence score to a paper.

## Taxonomy discipline

The Nickerson taxonomy-development paper adds an important constraint: every controlled field
must serve the review meta-characteristic:

> How was a causal multi-omics aging claim produced, contrasted, checked, and evidenced?

Fields that do not help answer that question belong in optional context views,
not in the minimum extraction record. Within one dimension, values should be
mutually exclusive and exhaustive. Features that genuinely co-occur belong in
separate dimensions or linked records.

The codebook should retain a split/merge history. A change is acceptable only
when it improves coverage or explanatory value and its effect on prior
extractions is recorded.

## Decision pending

This memo recommends a hierarchical canonical model and multiple derived
views. It does not yet alter the frozen eligibility ledger, PRISMA flow,
accepted five-question article structure, or existing source-checked tables.
The next decision is whether to adopt this entity model as the basis for the
production evidence table and extraction codebook.
