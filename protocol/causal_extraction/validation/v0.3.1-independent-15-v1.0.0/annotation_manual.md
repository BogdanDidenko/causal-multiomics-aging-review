# Independent causal-analysis inventory manual v1.0.0

## Objective

Create an exhaustive inventory of design-level causal analyses and plausible
boundary candidates in one report. Use the frozen v0.3 causal-analysis codebook
without adding scientific eligibility rules.

## Qualifying analysis

A qualifying unit must satisfy all four codebook conditions:

1. a current-report empirical result, including a null result;
2. direct relevance to aging, lifespan, senescence, age-related decline, or a
   mechanistic experiment supporting the report's focal aging link;
3. a named source of identifying variation or a formal directed-hypothesis
   method;
4. a role in the report's multi-omics workflow.

Use the design-level boundary from the codebook. Do not split a shared design
by gene, metabolite, outcome, dose, time point, subgroup, or omics-table row.
Separate units when the identifying variation, exposure/intervention, or
population/biological system changes.

## Boundary inventory

Record every plausible item that a reviewer could confuse with a qualifying
analysis, including:

- causal wording without a formal method;
- association, prediction, enrichment, or differential abundance;
- network centrality or an undirected network;
- colocalization without another identifying design;
- a method proposed for future work;
- cited external work;
- a causal design unrelated to aging or to the multi-omics workflow;
- a duplicated fragment of another design unit.

Assign the first failed condition from the frozen v0.3.1 vocabulary. Boundary
items are required because the later fixed-candidate classifier must see both
qualifying and nonqualifying candidates.

## Evidence

Read the complete packet. Cite only exact `evidence_atom_id` values from that
packet. A qualifying analysis requires at least one method atom and one result
atom. Validation atoms are optional and must concern the same normalized causal
link. Boundary candidates require at least one atom that establishes why the
item was considered.

Use enough atoms to make the unit and decision independently auditable. Do not
choose an atom merely because it contains causal vocabulary. Do not quote or
paraphrase source text in place of an evidence ID.

## Independence and output

Do not inspect graph profiles, screening decisions, v0.3 outputs, the other
reviewer's inventory, or an expected answer. Return one JSON object conforming
to the frozen schema. Notes must be concise boundary explanations, without
hidden reasoning or article-level synthesis. Do not assign Levels.
