# Independent validation sample for v0.3.1

## Purpose

This sample evaluates the frozen `v0.3.1` fixed-candidate classifier outside
the 12 reports used to design it. It also creates a reference inventory for
measuring candidate-discovery recall. No result from this sample may be used to
edit `v0.3.1` before the prespecified evaluation is complete.

## Composition

The sample contains 15 reports:

- 12 reports selected from the 101 full-text-eligible reports and disjoint from
  every prior causal-extraction E0, checkpoint, and v0.3 development sample;
- 3 targeted challenge reports selected from the broader v1.1.2 search frame
  because the remaining independent eligible frame contained no clear positive
  example of a formal directed-hypothesis method.

The targeted challenges test formal mediation, a mediation/molecular-omics
boundary, and a Bayesian-network/current-result boundary. They are validation
records and do not enter the final PRISMA denominator through this experiment.

## Selection information

Selection may use title, abstract, document length, prior full-text eligibility,
and previously generated graph labels strictly as diversity cues. Reviewers do
not receive graph-derived causal analyses, prior model outputs, expected
qualification, or expected Levels.

The sample spans genetic instruments, colocalization boundaries, inherited
loss-of-function variation, assigned interventions, direct genetic and
pharmacologic perturbations, animal and plant longevity, cellular senescence,
formal mediation, network language, thin reports, and association/prediction
boundaries.

## Independence

The two inventory reviewers work from the same frozen annotation manual,
schema, codebook, and complete evidence-atom packet. They cannot inspect each
other's outputs. Reconciliation starts only after all 30 independent report
annotations are terminal and their hashes are frozen.

This is a disjoint validation sample, not an expert-gold sample. Codex and
Claude outputs remain AI-assisted analyst drafts until a domain expert verifies
the reconciled inventory.

## Evaluation order

1. Freeze sample, source hashes, annotation contract, and inherited v0.3.1
   hashes.
2. Produce independent Codex and Claude inventories.
3. Freeze both raw inventory sets.
4. Reconcile candidate boundaries and evidence IDs without changing v0.3.1.
5. Freeze an opaque fixed-candidate scaffold.
6. Run unchanged v0.3.1 five times.
7. Report candidate qualification, field stability, and alignment with the
   reconciled draft separately.
