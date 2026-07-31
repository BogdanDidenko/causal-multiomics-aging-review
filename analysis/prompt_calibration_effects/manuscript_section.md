# Prompt-contract refinement and repeated-run stability

## Methods

### Prompt-instrument development and data separation

We treated the title/abstract prompt suite as a versioned measurement
instrument and separated prompt development from held-out stability evaluation.
The source frame contained 2,620 records with sufficient title/abstract
metadata. Before inspecting the new development data, we excluded every record
identifier present in any earlier benchmark or screening-stability result
(216 distinct identifiers), leaving 2,406 previously unseen eligible records.
We then used deterministic, seed-based, stratum-balanced sampling to select a
50-record development set and a disjoint 25-record holdout. The split,
selection manifest, record identifiers, and file hashes were frozen in Git
commit `15bcde0`. The 25-record holdout remained sealed until the complete
candidate was frozen.

All agent stages used GPT 5.6 Terra Medium (`gpt-5.6-terra`) through isolated
Codex CLI sessions with `reasoning.effort=medium`. Each stability experiment
comprised five independent runs. The title/abstract pipeline used three
specialist roles (scope and aging, causal design, and directional biological
wording), three contract-verifier calls per role, deterministic criterion
gates, and selective adjudication. A single retry was allowed for invalid JSON.
Raw provider responses, parsed specialist outputs, verifier votes, consensus
counts, evidence spans, corrections, adjudication outputs, and final routes
were retained.

The prespecified stability criterion required 100% JSON-schema success, 100%
exact agreement across the five runs for the final route, decisive criteria,
and all tracked categorical fields, and 0% manual review. Free-text rationales
and evidence-span wording were excluded from exact matching. Specialist-draft
agreement and verifier-field unanimity were reported as diagnostics and did
not replace the canonical acceptance criterion.

### Iterative refinement

Version 0.96.0 removed shared-draft anchoring: contract verifiers received the
source record but not the preceding specialist draft. Its full 50-record
development run localized six unstable records. Subsequent development used
these six records as a focus subset. Version 0.97.0 mapped a three-way
categorical verifier tie to the schema's existing `unclear` state and clarified
development-derived class boundaries. Version 0.98.0 aligned ellipsis and
current-report attribution rules across specialists, verifiers, and
adjudication. Version 0.99.0 required unanimity before accepting exclusionary
`no` or `nonempirical` verifier values; Python otherwise performed only
declared categorical aggregation and logical consistency rules.

After version 0.99.0 passed the focus subset and the complete development set,
the prompts, schemas, runtime configuration, code, and development artifacts
were frozen in commit `d5646a9`. The 25-record holdout was then opened and
evaluated exactly once. Holdout records were not used for subsequent prompt
revision.

## Results

On the complete 50-record development set, version 0.96.0 achieved 0.90 exact
agreement for the final route and 0.88 for both decisive and all tracked
criteria. Six records were unstable, five changed route across runs, and the
manual-review rate was 0.02. In the directly comparable six-record focus
subset, final-route agreement increased from 0.167 under version 0.96.0 to
0.833 under versions 0.97.0 and 0.98.0, and to 1.00 under version 0.99.0.
Decisive and all-tracked agreement increased from 0 under version 0.96.0 to
0.667 under version 0.97.0, 0.833 under version 0.98.0, and 1.00 under version
0.99.0.

When version 0.99.0 was rerun on all 50 development records, schema success,
final-route agreement, decisive agreement, and all-tracked agreement were all
1.00, with no manual reviews. All five runs routed the same 35 records to
exclusion and 15 to full-text assessment. Comparing modal routes on the same
50 records, 49 remained in the same route between versions 0.96.0 and 0.99.0;
one record moved from an unresolved modal state under version 0.96.0 to
full-text assessment under version 0.99.0. Specialist-draft agreement remained
0.66 and verifier-field unanimity was 0.979, indicating that canonical
agreement was achieved despite variability in unverified intermediate model
outputs.

The one-time held-out evaluation did not reproduce the perfect development
result. On the 25 sealed records, schema success remained 1.00 and the
manual-review rate remained 0, but final-route agreement was 0.96 and decisive
and all-tracked agreement were 0.92. Two records were unstable and one changed
the final route. Specialist-draft agreement was 0.72 and verifier-field
unanimity was 0.964. Under the prespecified 100% criterion, version 0.99.0 was
therefore rejected.

| Suite | Evaluation set | Records x runs | Final route | Decisive | All tracked | Raw drafts | Verifier unanimity | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| v0.96.0 | Full development | 50 x 5 | 0.900 | 0.880 | 0.880 | 0.660 | 0.965 | Fail |
| v0.96.0 | Six-record focus, derived | 6 x 5 | 0.167 | 0.000 | 0.000 | 0.167 | 0.778 | Diagnostic |
| v0.97.0 | Same six-record focus | 6 x 5 | 0.833 | 0.667 | 0.667 | 0.000 | 0.885 | Fail |
| v0.98.0 | Same six-record focus | 6 x 5 | 0.833 | 0.833 | 0.833 | 0.000 | 0.970 | Fail |
| v0.99.0 | Same six-record focus | 6 x 5 | 1.000 | 1.000 | 1.000 | 0.333 | 0.959 | Pass |
| v0.99.0 | Full development | 50 x 5 | 1.000 | 1.000 | 1.000 | 0.660 | 0.979 | Pass |
| v0.99.0 | Sealed holdout v8 | 25 x 5 | 0.960 | 0.920 | 0.920 | 0.720 | 0.964 | Fail |

### Uncertainty of observed instability

To quantify sampling uncertainty around the observed reproducibility failures,
we report two-sided Wilson 95% confidence intervals for binomial proportions.
The unit for exact-agreement failures was the record; the unit for schema
failure and manual review was the record-run outcome. On the 50-record
development confirmation, no canonical instability was observed: final-route,
decisive-criterion, and all-tracked instability were each 0/50 (0%; Wilson 95%
CI, 0%-7.1%). On the sealed 25-record evaluation, final-route instability was
1/25 (4%; 95% CI, 0.7%-19.5%), while decisive-criterion and all-tracked
instability were each 2/25 (8%; 95% CI, 2.2%-25.0%). Schema failure and manual
review were each 0/125 sealed record-run outcomes (0%; 95% CI, 0%-3.0%).

These intervals quantify uncertainty in the observed instability rate under
this repeated-run protocol. They are not error rates against a human gold
standard and do not estimate screening sensitivity, specificity, or semantic
correctness.

## Interpretation

The refinement sequence was associated with substantial improvement in
within-development reproducibility, including perfect canonical agreement on
the complete development set. However, the held-out failure shows that
development-set stability did not fully generalize under the prespecified
criterion. This distinction is central: prompt refinement localized and
reduced observed nondeterminism, but it did not establish a universally stable
classifier.

These experiments assess reproducibility, not screening accuracy. The
development and holdout records did not have independent expert criterion-level
labels, so sensitivity, specificity, correctness, or false-exclusion risk
cannot be inferred. Moreover, versions 0.97.0 and 0.98.0 bundled wording and
aggregation changes, and focused experiments intentionally reused records that
were unstable under version 0.96.0. The sequence therefore supports
descriptive attribution to versioned prompt-contract changes, not a causal
estimate of the effect of each individual edit. The sealed holdout was used
only for one-time evaluation and must not be used to tune a subsequent version.

## Audit-trail availability

Every experiment retains five replicate manifests,
`raw_provider_responses.jsonl`, `screening_results.jsonl`,
`stability_results.jsonl`, and `stability_summary.json`. Machine-readable
summary tables are generated by
`scripts/summarize_prompt_calibration_effects.py` and stored in
`analysis/prompt_calibration_effects/`, including event counts and Wilson 95%
confidence intervals in `reproducibility_uncertainty.csv`. Prompt and schema
versions are immutable and checksummed in
`protocol/screening/prompt_manifest.json`.
