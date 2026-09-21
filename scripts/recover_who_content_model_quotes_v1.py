#!/usr/bin/env python3
"""Recover CMACM evidence quotes without changing model entity outputs."""

import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

from causal_multiomics_aging_review.full_quote_grounding import QuoteIndex
from run_who_content_model_validation_v1 import validate_semantics


ROOT = Path(__file__).resolve().parents[1]
VERSION = "v1.0.3"
MODEL = ROOT / f"protocol/content_model/{VERSION}"
BASE = ROOT / f"analysis/content_model_validation/{VERSION}"
RUN = BASE / "terra_three_runs"
OUT = BASE / "quote_recovery"


def main() -> None:
    if OUT.exists():
        raise ValueError(f"Refuse to overwrite quote recovery: {OUT}")
    records = {record["record_id"]: record for record in map(json.loads, (BASE / "input.jsonl").open())}
    records_by_document = {record["document_id"]: record for record in records.values()}
    schema = json.loads((MODEL / "foundation_extraction.schema.json").read_text())
    validator = Draft202012Validator(schema)
    linearizations = {item["id"]: item["counting_unit"] for item in json.loads((MODEL / "linearizations.json").read_text())["linearizations"]}
    OUT.mkdir(parents=True)
    outcomes = []
    methods = Counter()
    for validation_path in sorted(RUN.rglob("validation.json")):
        validation = json.loads(validation_path.read_text())
        if validation.get("valid") is not False:
            continue
        document_id = validation_path.parent.parent.name
        repeat = validation_path.parent.name
        record = records_by_document[document_id]
        record_id = record["record_id"]
        parsed_paths = sorted(validation_path.parent.glob("parsed_attempt_*.json"))
        if not parsed_paths:
            outcomes.append({"record_id": record_id, "repeat": repeat, "status": "no_parseable_model_output"})
            continue
        answer = json.loads(parsed_paths[-1].read_text())
        index = QuoteIndex(record)
        repaired = json.loads(json.dumps(answer))
        evidence_audit = []
        for item in repaired["evidence"]:
            original_quote = item["verbatim_quote"]
            match = index.align(item["source_locator"], original_quote)
            audit = {"evidence_id": item["id"], "original_quote": original_quote}
            if match is None:
                audit["valid"] = False
            else:
                source, start, end, method = match
                item["source_locator"] = source
                item["verbatim_quote"] = index.sources[source][start:end]
                audit.update({"valid": True, "method": method, "source": source, "start": start, "end": end, "quote": item["verbatim_quote"]})
                methods[method] += 1
            evidence_audit.append(audit)
        errors = [error.message for error in validator.iter_errors(repaired)]
        if not errors:
            errors.extend(validate_semantics(repaired, record, linearizations))
        if any(not audit["valid"] for audit in evidence_audit):
            errors.append("one_or_more_quotes_unresolved_after_deterministic_alignment")
        destination = OUT / "records" / record["document_id"] / repeat
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "repaired_result.json").write_text(json.dumps(repaired, ensure_ascii=False, indent=2) + "\n")
        (destination / "evidence_audit.json").write_text(json.dumps(evidence_audit, ensure_ascii=False, indent=2) + "\n")
        (destination / "validation.json").write_text(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2) + "\n")
        outcomes.append({"record_id": record_id, "repeat": repeat, "status": "valid" if not errors else "unresolved", "repaired_path": str((destination / "repaired_result.json").relative_to(ROOT))})
    summary = {"model_calls": 0, "attempted": len(outcomes), "valid": sum(item["status"] == "valid" for item in outcomes), "unresolved": sum(item["status"] != "valid" for item in outcomes), "alignment_methods": dict(methods), "outcomes": outcomes}
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in ("attempted", "valid", "unresolved", "alignment_methods")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
