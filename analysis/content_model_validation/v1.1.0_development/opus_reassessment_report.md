Direct answer up front: the v1.1.0 result changes my conclusion. The prior reassessment was right that WHO is not falsified by this failure and right to strip the model's discretion over counting. It was wrong in the strong prediction that doing so would reach production-level agreement. I owe you that plainly. I moved the discretion from segmentation to recall and classification, then predicted the second would be stable. It was not, and that was foreseeable.

## 1. Was the failure predictable?

Yes. I flagged the risk once (the "model-discretion signature" note) and then underweighted it. Atom-first extraction removes exactly one of three discretions, how many objects to mint. It does nothing about the other two, which atom emission still fully owns:

- Recall: whether a given procedure, target, or link appears in a run at all.
- Attribute assignment: which closed-vocabulary value a recalled atom receives.

Run-to-run recall variance is a documented property of LLM extraction, not an artifact of your contract. Python hashing cannot recover an atom a run never emitted, and cannot reconcile two runs that classify the same target as "pharmacologic intervention" versus "genetic proxy," because those are different identity keys, not two renderings of one key. So 45/45 on the evidence interface and 0/15 on exact structure is the expected shape once you accept that determinism was applied downstream of the actual variance source. Predictable.

## 2. Does WHO remain useful as the single methodology?

WHO remains a coherent representation, but the finding relocates the binding constraint off the representation entirely. The bottleneck is population (recall plus classification), and no content model supplies recall. Asking "is WHO the right framework" is now a question the evidence has answered sideways: framework choice is no longer where the failure lives, so no swap moves the number.

WHO is still useful, but as a schema, not as an autonomous extraction engine. Its operational representation cannot be populated reproducibly by the current model without a candidate inventory, and that is a property of the model, not a gap you can author away inside WHO.

## 3. Is a human candidate inventory required, or is there an unused WHO mechanism?

They are the same thing, and this is worth stating clearly: the WHO Content Model has always assumed a human-authored Foundation. The Foundation is a curated inventory. ICD-11 never asks a machine to discover entities; it asks humans to author entities and postcoordination axes, then classify instances against them. The mechanism you have not used is the one WHO actually specifies, human authoring of the candidate content with classification against it.

So a deterministic candidate inventory is required, and framing it as a departure from WHO is backwards. It is the missing WHO component. You automated the one step WHO never delegates to a machine.

Separate two layers:

- Global closed vocabularies (attribute values): already frozen in v1.1.0.
- Per-report candidate set (which workflows, links, targets, endpoints exist in this paper): the recall layer that failed and that WHO expects a curator to establish.

## 4. One next method that genuinely tests the WHO design

Human curation for candidate enumeration, model classification for attributes, deterministic parsing for the collapse. One combined method, in that order:

1. A curator enumerates the candidate atoms per report. This is bounded reading against a fixed atom taxonomy, not free extraction, and it fixes recall.
2. Three isolated model runs classify each supplied candidate against the frozen closed vocabularies. The model never enumerates and never counts; it only assigns attribute values to a given list.
3. Python runs the v1.1.0 identity-key collapse unchanged.

Why this tests WHO rather than replacing it: it holds recall constant and isolates the one remaining question, whether WHO's postcoordination classification is reproducible once the candidate set is fixed. Measure Krippendorff's alpha per attribute field and exact three-run agreement on the derived counts. Two clean outcomes:

- Classification is reproducible: WHO's representation works, and the only non-automatable step is recall, which you then report honestly as human-curated.
- Classification still varies: the failure is in specific attribute vocabularies, and alpha names the field. That is a fixable authoring problem, not an open recall wall.

Either result is diagnostic and publishable, which neither autonomous run was.

## 5. Continue CMACM, simplify, or drop the single-methodology requirement?

Stop investing in CMACM as an autonomous extraction contract. Keep WHO as the schema of a human-curated, model-assisted evidence table.

Honestly, briefly:

- Autonomous enumeration has failed twice at the same boundary, and the second failure isolates the cause as a model recall property that contract engineering cannot reach. Further contract iteration spends against a wall.
- "Simplify to a conventional evidence table" and "keep WHO" are not in tension. A rigorous systematic-review evidence table is a human-curated, LLM-assisted instrument with fixed columns. WHO's Content Model, populated by a curator, is exactly that schema. You keep the representation and drop only the claim that a machine populates it alone.
- The single-methodology requirement can stay, but its meaning shifts from "one autonomous extraction engine" to "one data model." That is the version the evidence supports.
- The review's contribution is the biological synthesis over 357 reports, not the extraction architecture. The architecture should be as rigorous as the synthesis needs and no more. A human-curated WHO-schema table with the question 4 reproducibility check as QA clears that bar. Autonomous enumeration was always a larger claim than the review requires.

Concrete next step: convert the frozen v1.1.0 vocabularies and identity functions into the QA layer for a human-curated table, run the question 4 method on the 15 development reports to set attribute-level alpha baselines, and only then decide whether model classification is trustworthy enough to carry any part of the load on the untouched holdout. Keep the 15 as development.

---

This is a consultation response, not a repo change. If you want it recorded alongside the prior ones under `analysis/content_model_validation/`, give me the target path and I will write it in sentence case to match the existing files.
