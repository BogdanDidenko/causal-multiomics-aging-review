# Primary analyst cross-audit of the Claude Opus 5 review

## Scope

The primary analyst checked the complete Opus review against the 15 frozen
Docling sources and the v0.1.0 contract. This is an adjudication between one
analyst and one advisory model reviewer, not independent expert gold labeling.

The Opus runtime was successful and used canonical `claude-opus-5` for the
substantive review: 69 turns, 1,599,645 ms wall time, and 51,683 characters of
final review. The full unedited response and provenance are in
`opus_review.md`.

## Agreement interpretation

Opus reported 90-100% agreement for every individual decision-driving field:

| Field | Agreement |
| --- | ---: |
| author claim type | 95% |
| primary design or method | 100% |
| source of variation | 95% |
| reviewer identification assessment | 90% |
| result status | 90% |
| candidate level | 90% |
| negative Level 4 determination | 100% |

Its 35% all-field agreement includes claim segmentation and therefore mixes two
questions. The primary pilot intentionally selected boundary claims and stated
that it was not exhaustive, while Opus treated every unextracted claim as a
segmentation disagreement. This does not invalidate its central finding: four
selected records genuinely merged operations or endpoint families that the
v0.1.0 unit rule required to be split. v0.2.0 therefore declares
`boundary_case_pilot` versus `exhaustive_report` before annotation. Production
and reliability studies use the exhaustive mode.

## Source-level decisions

### Accepted

1. **FOCUS/TWAS is Level 1 prioritization.** A posterior inclusion rank is not a
   directed hypothesis or an effect estimate. The v0.1.0 Level 2 coding was
   inconsistent with its own prohibition on candidate ranking.
2. **HOTAIRM1 is manual review.** The frozen document explicitly says it is a
   subscription preview and contains no article Methods, Results, Discussion,
   or Limitations. Extended-data captions do not make the causal contrast fully
   assessable.
3. **PESA explicitly addresses sequential ignorability.** The correct status is
   `addressed`, with an assessment explaining why age/sex matching is
   insufficient. The MESA analysis is external validation of the association,
   not independent validation of the mediated causal effect.
4. **The CASP8 quote lost polarity.** The short fragment omitted “do not” and
   cannot support operation non-equivalence. v0.2.0 requires sufficient
   polarity-preserving spans and field-level anchor references.
5. **Losartan contrast specification and validity were conflated.** Dose,
   comparator, outcome, population, time, and model are stated, so the contrast
   is complete. Dose remains unidentifiable because dose and time are
   inseparable.
6. **Assignment and transferred material are orthogonal.** Randomized
   parabiosis and nonrandom FMT must not collapse to one provenance category.
7. **Assumption modules require closed domains and complete coverage.** Missing
   reporting is now an explicit `not_reported` judgment with a search note.
8. **Candidate level, formal basis, and Level 4 qualification are derived.** A
   reviewer no longer writes these outcomes into the scientific record.
9. **Endpoint and operation splitting needs stronger enforcement.** D+Q endpoint
   families, HOTAIRM1 operations, FMT behavior versus synapse outcomes, and the
   combined AhR/Sirt2 epistasis record require splitting.
10. **Omics layers need controlled names.** Non-omics assays and network
    databases cannot occupy the molecular-layer field.

### Accepted with modification

1. **Level 4 derivation.** Opus proposed only exact independent replication.
   The frozen review protocol also allows an orthogonal identification design
   and appropriate colocalization of a molecular-proxy link. v0.2.0 preserves
   those three explicit paths and derives them from validation dimensions.
2. **FMT comparator integrity.** The Methods clearly say recipients received
   antibiotics and young controls received PBS, but “recipients” may include a
   control recipient group not fully described in the extracted text. The
   defensible code is `unclear`, not definitely `violated`, until group-level
   pretreatment is resolved.
3. **Multi-node provenance.** Opus proposed assigning an indirect effect to the
   mediator-outcome link. An indirect effect depends on both exposure-mediator
   and mediator-outcome links; v0.2.0 records link-specific variation sources
   for both rather than choosing one.
4. **Quote threshold.** A 60-character minimum is arbitrary and can reject a
   complete short sentence. The validator uses a six-token floor plus exact
   heading and field-anchor checks; scientific support still requires review.

### Rejected

1. **Same-lab replication is not automatically data-dependent.** A new sample
   from a complete experimental repeat can have independent data while the
   experiment remains only partially independent. These dimensions are kept
   separate.
2. **The scoped 0.1-0.5 mg/mL cordycepin claim is not mixed.** The high-dose harm
   at 10 mg/mL is a separate dose-range claim under the split rule. Exhaustive
   extraction must retain it, but it does not reverse the result status of the
   explicitly scoped low-dose claim.
3. **Diagnostics are not removed.** Negative controls, target-engagement tests,
   pleiotropy checks, colocalization, and model fit are analytically useful.
   v0.2.0 retains them under a closed diagnostic type vocabulary instead of a
   free-text duplicate of assumptions.

## Corrected decision set

Two of 20 v0.1.0 claims change decision-driving classification after source
adjudication:

- `natcom_2023_twas_focus_prioritization`: Level 2 to Level 1;
- `nataging_2026_hotairm1_crispri_senescence`: Level 3 to manual review pending
  full text.

The other 18 retain their candidate level, although several require claim
splitting, narrower normalization, corrected assumptions, or stronger anchors.
The complete row-level dispositions are in `adjudicated_decisions.csv`.

## Methodological conclusion

The pilot supports the conceptual separation among author claim, design,
variation provenance, identification assessment, and result direction. It does
not yet validate production extraction. Before an independent human pilot,
v0.2.0 must be re-applied in exhaustive mode and the positive Level 4 paths
must be exercised on deliberately sampled examples.
