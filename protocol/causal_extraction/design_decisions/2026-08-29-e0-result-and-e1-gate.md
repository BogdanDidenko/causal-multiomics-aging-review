# E0 result and E1 gate

Date: 2026-08-29

Status: E0 technical result accepted; E0 scientific proceed gate remains
pending; E1 has not been frozen or run.

## Frozen E0 execution

E0 was frozen in Git revision `328abcf839e4cfd270fa3980f798238d11b8f37d`
before any E0 model call. It used six development-only reports, 33 complete
atom windows, two grounding arms, and two independent Terra Medium repeats per
arm and window. All 132 planned calls and every failed first attempt remain in
the restricted raw trace.

The six reports are outside causal-extraction checkpoints A and B but are not
sealed. Luna Light generated profiles for all 101 eligible reports, and earlier
article-design agents inspected all profiles and overlapping full texts.

## Preregistered technical result

- Planned calls: 132; terminal calls: 132; valid terminal calls: 132.
- Reports with complete exact-once core atom coverage: 6/6.
- Evidence-ID arm: 66/66 first-attempt valid calls, zero retries, 642/642
  returned evidence references resolved by Python.
- Verbatim-quote arm: 62/66 first-attempt valid calls, four retries, 393/393
  terminal references resolved.
- All four quote-arm first-attempt failures were
  `quote_not_substring_of_supplied_atom`.

Both arms met terminal resolution after one allowed retry. The evidence-ID arm
also provides the stronger structural guarantee: the model cannot author the
citation text; Python retrieves exact text, offsets, and hashes from the frozen
atom index. `evidence_atom_id` is therefore selected as the grounding interface
for subsequent development.

This selection concerns citation transport. It does not establish semantic
support, analysis recall, causal validity, or inventory stability.

## Post-hoc stability signal

The exploratory disagreement analysis was written after the run and was not an
E0 acceptance gate.

| Metric | Quote arm | Evidence-ID arm |
|---|---:|---:|
| Repeat pairs | 33 | 33 |
| Both-empty pairs | 15 | 15 |
| Full exact pairs, all windows | 15 | 15 |
| Nonempty pairs | 18 | 18 |
| Full exact pairs, nonempty windows | 0 | 0 |
| Analysis-count exact, nonempty windows | 6 | 7 |
| Closed-field multiset exact, nonempty windows | 3 | 4 |

All full exact repeat pairs were empty windows. Across grounding arms, full
agreement was also 0/36 nonempty arm pairs. Manual inspection of administrative
analysis summaries found recurring boundary choices:

1. the same manipulation was split by assay or readout in one run and grouped
   in another;
2. a multi-gene SMR screen was represented as one screen or as separate
   exposure-specific analyses;
3. overlapping transfer, intervention, and perturbation descriptions received
   different design-family labels.

These findings support a development hypothesis that the open window-level unit
is insufficiently localized. They do not prove general failure: the analysis
is post-hoc, gold-free, clustered in six reports, and confounded because the
grounding output contract itself changed upstream model behavior.

## Independent critique

A read-only `claude-opus-4-8` audit agreed that evidence-ID grounding should be
retained and that E1 may test a design-instance unit. It rejected stronger E0
claims because the stability threshold was not preregistered, the nonempty
denominator was small, output contracts were coupled, and human gold remains
pending.

The complete audit and provenance manifest are in
`analysis/causal_extraction/consultations/2026-08-29-opus-e0-audit/`.

## E0 gate still pending

E0 cannot receive a full pass until:

- two humans independently audit the frozen 60-reference semantic sample;
- the adjudicated supported-reference precision is at least 0.98;
- two humans independently define the six-report analysis inventory;
- analysis-boundary precision and recall are scored by arm;
- the evidence-ID arm has no lower expert-gold recall than the quote arm.

Model reviewers, including Opus, do not count as either human annotator.

## E1 hypothesis

E1 will test whether changing the primary unit improves reproducibility without
reducing expert-gold recall. The candidate unit is a design instance keyed by:

- source of identifying variation or assignment implementation;
- exposure, intervention, or perturbation construct;
- study population, dataset, or biological system.

Outcomes, assay readouts, endpoints, time points, and strata become child
contrasts and must remain registered decision fields rather than ungated prose.

The unit needs explicit conditional rules before freeze:

- interventions and perturbations: one assignment or manipulation in one
  system is one instance; readouts are child contrasts;
- multi-exposure MR/SMR screens: one fitted screen is one instance;
  exposure-specific reported hits are child contrasts;
- mediation: store exposure, mediator, outcome, and indirect/direct paths
  explicitly;
- causal discovery: distinguish one fitted directed model from its reported
  directed edges; the final instance/edge rule must be frozen after codebook
  piloting and before E1 model calls.

## Prospective E1 requirements

E1 is blocked until one commit freezes all of the following:

1. a new 6-12 report development sample disjoint from E0 and checkpoints A/B,
   selected by document structure and a published hash seed;
2. two independent human analysis-boundary annotations created before model
   outputs are viewed;
3. evidence-ID grounding in every arm;
4. a one-factor comparison between the current outcome-keyed unit and the
   design-instance unit, with all other runtime and packaging fields fixed;
5. two repeats per arm; repeat-count policy is a later ablation;
6. primary exact agreement on registered instance and child-contrast fields
   among nonempty-both pairs, with report-clustered uncertainty;
7. separate empty-window rate, all-window agreement, technical failures,
   precision, recall, and all human overrides;
8. an auditable reason code for every empty window.

Fixed atom-role tagging may be held constant as a pre-pass or tested in a later
separate ablation. It must not be introduced in only one unit arm, because that
would confound the E1 unit comparison.

## Decision

- Retain deterministic sentence/table-row atoms and evidence-ID grounding.
- Preserve E0 raw outputs and compact checksums unchanged.
- Treat the design-instance definition as an E1 hypothesis.
- Do not run E1, activate codebook v0.3.0, or process all 101 reports until the
  prospective E1 package and pre-model human boundary gold are frozen.
