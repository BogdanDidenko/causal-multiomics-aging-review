# Primary analyst self-audit

## Pilot result

The v0.1.0 contract was applied to 20 normalized claims from 15 reports. The
deterministic validator passed:

- 15/15 sampled DOI represented;
- 20/20 records valid against the JSON Schema;
- 0 duplicate claim IDs;
- 0 unresolved evidence-anchor references;
- 0 unsupported evidence quotations;
- 0 deterministic Level-mapping errors.

Candidate levels were Level 1: 1 claim, Level 2: 6 claims, Level 3: 13 claims,
and Level 4: 0 claims. This distribution is descriptive of the purposive pilot,
not of the eligible corpus.

## Decisions that worked as intended

### Claims, not papers

The contract prevented a report's strongest experiment from upgrading every
result. The Cell Systems paper was split into a Level 2 stabilized-regression
hypothesis and a Level 3 worm perturbation. The cordycepin paper was split into
a Level 3 lifespan intervention and a Level 1 direct-target docking claim.

### Operation-specific perturbations

CASP8 catalytic inhibition and CASP8 transcript knockdown were retained as
separate claims. The positive inhibitor result and null siRNA result therefore
remain visible without treating either as replication of the other.

### Assessability versus credibility

The TPE clock contrast remained assessable at Level 3 even though allocation
was sequential rather than random, baseline clock imbalance was substantial,
and the result was time-specific. By contrast, the losartan dose claim was not
assessable because dose was deterministically confounded with cumulative time
on treatment. This distinction avoids using evidence level as a hidden
risk-of-bias score.

### Package effects

FMT and parabiosis were coded as effects of transferred biological packages.
Neither claim was silently narrowed to a single microbe, metabolite, or young
circulating factor.

### Strict Level 4 boundary

No pilot claim received Level 4. Alternate MR instruments, colocalization,
another methylation platform, a repeat experiment, in-vivo follow-up of a cell
claim, and cross-species perturbation all failed at least one same-link or
independence dimension. This is conservative by design, but a future pilot must
include genuine positive Level 4 examples to test sensitivity.

## Ambiguities exposed by the pilot

1. `rescue_or_epistasis` combines two distinct logical operations despite the
   codebook's instruction not to collapse necessity, sufficiency, and rescue.
   A later version should consider separate `rescue` and `effect_modification_or_epistasis`
   values.
2. `formal_basis_present` is used only to map an unassessable effect claim to
   Level 1 or 2, but its definition is less explicit than the four core fields.
   It may be derivable from method and output fields rather than independently
   annotated.
3. `contrast_complete` captures whether the target contrast is stated, not
   whether its assumptions hold. This was clear to the primary analyst but may
   be confused with `effect_assessable` by another reviewer.
4. A null perturbation is coded `author_claim_type=causal_effect` because the
   tested contrast is causal even when its estimate is null. The definition
   should state this explicitly.
5. The exact threshold between `formal_hypothesis_only` and
   `effect_claim_not_assessable` can be disputed for observational mediation.
   The pilot used `formal_hypothesis_only` when the report itself denied causal
   identification, and `effect_claim_not_assessable` when authors asserted a
   treatment effect whose operational contrast was structurally confounded.
6. The pilot annotates selected decision-informative claims and is not an
   exhaustive extraction of every causal statement in the 15 reports. A claim
   enumeration protocol is still needed before corpus-wide use.
7. The schema permits an empty assumption list even though the codebook asks
   for design-specific modules. Minimum required domains should be generated
   deterministically from the selected primary design.

## Questions for independent challenge

- Are the four core fields mutually distinguishable in all 20 records?
- Should observational mediation always be `formal_hypothesis_only`, or can an
  explicitly defended mediation design be `effect_assessable`?
- Is the TPE contrast correctly classified as assessable despite invalid
  randomized terminology and baseline imbalance?
- Does any validation in the sample satisfy Level 4 under a defensible
  same-link definition?
- Does the MR coding distinguish a genetically proxied effect from a drug or
  behavioral intervention strongly enough?
- Which fields can be deterministic derivations rather than additional model
  judgments?
