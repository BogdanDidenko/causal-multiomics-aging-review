# Effect appraisal contract

Classify only the fixed candidate's contrast, assumptions reviewability, and
result status. Use the same definitions as v0.3.0.

`contrast_status`:

- `explicit`: exposure or intervention and comparator are stated;
- `implicit`: the design defines a contrast, but comparator wording is
  incomplete;
- `unclear`: the available text does not define the contrast.

`assumptions_reviewability`:

- `reviewable`: the design and data source are sufficiently described to state
  and inspect the main identification assumptions;
- `partly_reviewable`: some essential design or data-source detail is missing;
- `not_reviewable`: the text does not permit an identification assessment.

`result_status`:

- `positive`
- `null`
- `mixed`

Retain null results. Apply result status to the complete fixed design unit, not
to an arbitrarily selected molecule or child contrast. Return one value per
field and candidate. Do not classify validation strength or causal Level.
