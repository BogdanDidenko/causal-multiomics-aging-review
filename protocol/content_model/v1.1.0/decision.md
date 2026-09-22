# Production Methodology Decision: WHO Content Model

Date: 2026-09-22

## Decision

The review adopts the WHO Content Model as its single primary methodology for
representing complex causal multi-omics evidence. The domain adaptation is
named the **Causal Multi-omics Aging Content Model (CMACM) v1.1.0**.

Version 1.1.0 responds to the rejected v1.0.3 development test. Models no
longer instantiate or count Foundation entities. They emit typed atomic
attributes with deterministic evidence-atom identifiers. Python derives every
Foundation entity and linearization count from frozen identity keys.

The WHO concepts used as primary methodology are Foundation, entity,
polyhierarchy, linearization, postcoordination, value set, logical definition,
necessary condition, inclusion/exclusion boundary, lifecycle status, and
backwards compatibility.

GO, SEI Views and Beyond, W3C PROV-DM, and the Nickerson taxonomy-development
method are comparative sources. They do not define a co-equal methodology for
this review. Their specific ideas may appear as domain requirements inside
CMACM only when expressed as a WHO-compatible entity, relation, axis, value,
constraint, or lifecycle rule.

## Named Domain Amendments

1. Preserve model and human extraction assertions as lifecycle-managed evidence
   records until adjudication; do not overwrite disagreement.
2. Represent `supported`, `null`, `challenged`, `unclear`, and `not_assessed`
   explicitly. Absence of a record is never negative evidence.
3. Store audit provenance as controlled Foundation content rather than adopting
   a second provenance formalism.
4. Apply the mandatory individuation rule before counting: a new base entity is
   created only when an identity-defining study, workflow, exposure/instrument,
   outcome construct, or biological system changes. Arms, doses, estimators,
   time points, sensitivity tests, rescues, and orthogonal checks are axes or
   validations unless they meet that rule.
5. Preserve known cross-view inconsistencies as explicit extraction assertions.
6. Default to postcoordination. Precoordinate a workflow pattern only after it
   is recurrent, has a stable fully specified name, and its combination is
   useful across multiple review views.
7. `ResultMeasurement` is a non-countable Foundation leaf entity. It stores
   individual endpoint, assay, estimate and statistic records under a derived
   link and contrast.
8. `Contrast` is a postcoordination axis cluster, not a Foundation entity.

## Scope

This decision changes neither frozen screening outputs nor PRISMA counts. It
defines the production data model for prospective causal-evidence extraction.
