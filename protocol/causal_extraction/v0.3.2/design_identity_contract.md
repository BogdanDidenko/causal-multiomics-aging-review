# Design identity contract

Classify only the fixed candidate's causal basis, design family, and source of
identifying variation. Use the same definitions as v0.3.0.

`causal_basis`:

- `effect_identification_design`: intervention, instrument, perturbation, or
  another design intended to estimate an exposure-outcome contrast;
- `formal_directed_hypothesis`: a formal directed method proposes a testable
  causal structure without sufficient effect identification.

`design_family`:

- `genetic_instrument`
- `randomized_intervention`
- `nonrandomized_controlled_intervention`
- `targeted_perturbation`
- `mediation`
- `temporal_design`
- `graphical_or_structural_model`
- `causal_discovery_algorithm`
- `other_named_design`

`variation_source`:

- `randomized_assignment`
- `genetic_instrument`
- `genetic_perturbation`
- `molecular_perturbation`
- `pharmacologic_intervention`
- `behavioral_or_environmental_intervention`
- `surgical_or_model_induction`
- `temporal_ordering`
- `modeled_directionality`
- `other_named_source`

Return one value per field and candidate. Do not appraise result direction,
validation, aging role, multi-omics role, assumptions, or contrast wording.
