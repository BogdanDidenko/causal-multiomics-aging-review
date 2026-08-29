# Two-sample causal-extraction stability checkpoint

Instrument: `causal_extraction/v0.1.1-rc1`. Model: `gpt-5.6-terra` with reasoning effort `medium`.

## Verdict

**FAIL.** The release candidate did not satisfy the prespecified 100% quote-grounding and five-run exact-agreement gates. These checkpoints measure stability and technical validity; they contain no expert gold labels and make no accuracy claim.

## Results

| Metric | A (15 reports) | B (15 reports) |
|---|---:|---:|
| Frozen atomic candidates | 1288 | 1541 |
| Classifier sample | 30 | 30 |
| Candidates with 5 valid runs | 20 | 16 |
| Reports with incomplete grounded discovery | 11 | 11 |
| All tracked fields exact, 5 runs | 9/20 (45.0%) | 8/16 (50.0%) |
| All tracked fields exact, first 3 runs | 11/20 (55.0%) | 9/16 (56.2%) |
| Candidate status exact, 5 runs | 18/20 (90.0%) | 14/16 (87.5%) |
| Derived Level exact, 5 runs | 20/20 (100.0%) | 15/16 (93.8%) |

Wilson 95% intervals are stored in the JSON report for every proportion. A lost 2 candidates between the three-run and five-run all-field gates; B lost 1.

## Technical audit

Discovery produced 1288 candidates in A and 1541 in B. Primary quote-grounding failures were 50 and 55; one retry recovered 19 and 19, respectively.

Classifier terminal statuses were `{'technical_failure': 3, 'grounding_failure': 29, 'ok': 118}` for A and `{'ok': 107, 'grounding_failure': 43}` for B. Invalid responses remain in denominators and are excluded from automatic scientific synthesis.

## Interpretation

Derived Levels were much more stable than complete criterion-level profiles. This does not rescue the instrument because detailed fields are required for auditable evidence synthesis. The atomic discovery contract also generated too many candidates for a five-run production deployment without a separately validated consolidation or batching stage.

Checkpoint A was used to identify runner defects and the feasibility amendment. Checkpoint B received classifier outputs only after those Python-only fixes were committed. Prompts, schemas, codebook, model, reasoning effort, and selected reports were unchanged.
