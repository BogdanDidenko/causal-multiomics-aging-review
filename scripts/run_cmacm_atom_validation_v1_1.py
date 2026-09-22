#!/usr/bin/env python3
"""Run CMACM v1.1.0 atom classification and derive WHO Foundation entities."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from causal_multiomics_aging_review.llm import CodexCliProvider, ProviderError


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "protocol/content_model/v1.1.0"
BASE = ROOT / "analysis/content_model_validation/v1.1.0_development"
REPEATS = (1, 2, 3)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_id(prefix: str, parts: tuple[Any, ...]) -> str:
    encoded = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(encoded.encode()).hexdigest()[:16]}"


def canonical_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def render(template: str, record: dict[str, Any]) -> str:
    values = {"REPORT_ID": record["record_id"], "DOI": record["doi"], "TITLE": record["title"], "SOURCE": record["source"], "YEAR": record["year"], "ANNOTATED_FULL_MARKDOWN": record["annotated_full_markdown"]}
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def validate_atoms(answer: dict[str, Any], record: dict[str, Any]) -> list[str]:
    errors = []
    if answer.get("report_id") != record["record_id"]:
        errors.append("report_id does not match input")
    entities = {"procedure": answer.get("procedure_atoms", []), "link": answer.get("link_atoms", []), "measurement": answer.get("measurement_atoms", []), "validation": answer.get("validation_atoms", []), "evidence": answer.get("evidence_atoms", []), "assertion": [answer.get("extraction_assertion", {})]}
    all_ids = set()
    for kind, values in entities.items():
        current = {value.get("id") for value in values if value.get("id")}
        if len(current) != len(values):
            errors.append(f"duplicate or missing {kind} atom identifier")
        if all_ids & current:
            errors.append(f"atom identifier reused across entity types: {sorted(all_ids & current)}")
        all_ids.update(current)
    document_atom_ids = {atom["id"] for atom in record["document_atoms"]}
    evidence = {item["id"]: item for item in answer.get("evidence_atoms", [])}
    for item in evidence.values():
        if item["document_atom_id"] not in document_atom_ids:
            errors.append(f"evidence atom {item['id']} references unknown document atom")
        for target in item["supports_atom_ids"]:
            if target not in all_ids:
                errors.append(f"evidence atom {item['id']} references unknown model atom {target}")
    for procedure in answer.get("procedure_atoms", []):
        if not procedure["evidence_atom_ids"]:
            errors.append(f"procedure atom {procedure['id']} has no evidence")
        if any(item not in evidence for item in procedure["evidence_atom_ids"]):
            errors.append(f"procedure atom {procedure['id']} has unknown evidence")
    for link in answer.get("link_atoms", []):
        if link["procedure_atom_id"] not in entities["procedure"] and link["procedure_atom_id"] not in {item["id"] for item in entities["procedure"]}:
            errors.append(f"link atom {link['id']} references unknown procedure atom")
        if not link["evidence_atom_ids"] or any(item not in evidence for item in link["evidence_atom_ids"]):
            errors.append(f"link atom {link['id']} has invalid evidence")
    link_ids = {item["id"] for item in answer.get("link_atoms", [])}
    for measurement in answer.get("measurement_atoms", []):
        if measurement["link_atom_id"] not in link_ids:
            errors.append(f"measurement atom {measurement['id']} references unknown link atom")
        if not measurement["evidence_atom_ids"] or any(item not in evidence for item in measurement["evidence_atom_ids"]):
            errors.append(f"measurement atom {measurement['id']} has invalid evidence")
    target_ids = {item["id"] for item in answer.get("procedure_atoms", [])} | link_ids | {item["id"] for item in answer.get("measurement_atoms", [])}
    for validation in answer.get("validation_atoms", []):
        if validation["target_atom_id"] not in target_ids:
            errors.append(f"validation atom {validation['id']} references unknown target atom")
        if not validation["evidence_atom_ids"] or any(item not in evidence for item in validation["evidence_atom_ids"]):
            errors.append(f"validation atom {validation['id']} has invalid evidence")
    return errors


def derive_foundation(answer: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    procedure_ids = {}
    workflows = {}
    for atom in answer["procedure_atoms"]:
        key = (record["record_id"], atom["causal_procedure_class"], tuple(sorted(atom["dataset_context"])), atom["biological_system"])
        derived_id = stable_id("workflow", key)
        procedure_ids[atom["id"]] = derived_id
        workflows.setdefault(derived_id, {"id": derived_id, "identity_key": key, "source_atoms": []})["source_atoms"].append(atom["id"])
    link_ids = {}
    links = {}
    procedure_atoms = {atom["id"]: atom for atom in answer["procedure_atoms"]}
    for atom in answer["link_atoms"]:
        procedure = procedure_atoms[atom["procedure_atom_id"]]
        key = (procedure_ids[atom["procedure_atom_id"]], atom["exposure_intervention_family"], canonical_text(atom["exposure_key"]), atom["normalized_outcome_domain"], atom["direction"], procedure["biological_system"])
        derived_id = stable_id("link", key)
        link_ids[atom["id"]] = derived_id
        item = links.setdefault(derived_id, {"id": derived_id, "identity_key": key, "polarity": set(), "source_atoms": []})
        item["polarity"].add(atom["assertion_polarity"])
        item["source_atoms"].append(atom["id"])
    measurements = {}
    measurement_ids = {}
    for atom in answer["measurement_atoms"]:
        axes = tuple(sorted((axis["axis"], tuple(sorted(canonical_text(value) for value in axis["values"]))) for axis in atom["contrast_axes"]))
        key = (link_ids[atom["link_atom_id"]], canonical_text(atom["endpoint_specification"]), canonical_text(atom["assay_or_instrument"]), axes)
        derived_id = stable_id("measurement", key)
        measurement_ids[atom["id"]] = derived_id
        measurements.setdefault(derived_id, {"id": derived_id, "identity_key": key, "source_atoms": []})["source_atoms"].append(atom["id"])
    validations = {}
    for atom in answer["validation_atoms"]:
        target = link_ids.get(atom["target_atom_id"], procedure_ids.get(atom["target_atom_id"], measurement_ids.get(atom["target_atom_id"], atom["target_atom_id"])))
        key = (target, atom["validation_type"], canonical_text(atom["dataset_or_assay_context"]))
        derived_id = stable_id("validation", key)
        validations.setdefault(derived_id, {"id": derived_id, "identity_key": key, "result": set(), "source_atoms": []})["result"].add(atom["result"])
        validations[derived_id]["source_atoms"].append(atom["id"])
    aging_domains = {"lifespan_survival", "healthspan_function", "biological_age_clock", "cellular_senescence", "tissue_function_or_pathology", "reproductive_aging", "plant_senescence"}
    multiomics_workflows = {procedure_ids[atom["id"]] for atom in answer["procedure_atoms"] if atom["omics_layers"]}
    aging_links = {link_id for link_id, link in links.items() if link["identity_key"][3] in aging_domains}
    return {"report_version_count": 1, "study_count": 1, "workflow_count": len(workflows), "link_count": len(links), "measurement_count": len(measurements), "validation_count": len(validations), "linearization_counts": {"prisma_report_view": 1, "evidence_base_view": 1, "causal_leverage_view": len(workflows), "multiomics_contribution_view": len(multiomics_workflows), "aging_outcome_view": len(aging_links), "strength_transport_view": len(validations), "audit_view": 1}, "design_family_set": sorted({atom["causal_procedure_class"] for atom in answer["procedure_atoms"]}), "workflows": sorted(workflows), "links": sorted(links), "measurements": sorted(measurements), "validations": sorted(validations)}


def run_one(record: dict[str, Any], repeat: int, schema: dict[str, Any], validator: Draft202012Validator, template: str, out: Path) -> dict[str, Any]:
    destination = out / "records" / record["document_id"] / f"repeat_{repeat}"
    destination.mkdir(parents=True, exist_ok=True)
    prompt = render(template, record)
    provider = CodexCliProvider("gpt-5.6-terra", timeout=3600, reasoning_effort="medium", context_window=None, max_tokens=None, audit_directory=destination / "provider_audit")
    failures = []
    for attempt in (1, 2):
        try:
            parsed, raw = provider.complete_json(prompt, schema, schema_name="cmacm_atom_classification")
            (destination / f"raw_response_attempt_{attempt}.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n")
            (destination / f"parsed_attempt_{attempt}.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n")
            errors = [error.message for error in validator.iter_errors(parsed)]
            if not errors:
                errors = validate_atoms(parsed, record)
            if errors:
                failures.append({"attempt": attempt, "kind": "validation", "errors": errors})
                continue
            derived = derive_foundation(parsed, record)
            (destination / "atom_result.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n")
            (destination / "derived_foundation.json").write_text(json.dumps(derived, ensure_ascii=False, indent=2) + "\n")
            (destination / "validation.json").write_text(json.dumps({"valid": True, "attempt": attempt, "derived_sha256": sha256(destination / "derived_foundation.json")}, ensure_ascii=False, indent=2) + "\n")
            return {"record_id": record["record_id"], "repeat": repeat, "status": "valid", "derived_path": str((destination / "derived_foundation.json").relative_to(ROOT))}
        except ProviderError as error:
            failures.append({"attempt": attempt, "kind": "provider", "error": str(error), "raw_response": error.raw_response})
    (destination / "validation.json").write_text(json.dumps({"valid": False, "failures": failures}, ensure_ascii=False, indent=2) + "\n")
    return {"record_id": record["record_id"], "repeat": repeat, "status": "failed"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", default="terra_three_runs")
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--repeats", type=int, choices=(1, 3), default=3)
    args = parser.parse_args()
    out = BASE / args.run_name
    if out.exists():
        raise ValueError(f"Refuse to overwrite atom validation run: {out}")
    records = list(map(json.loads, (BASE / "input.jsonl").open()))
    if args.max_records is not None:
        records = records[:args.max_records]
    schema = json.loads((MODEL / "atom_classification.schema.json").read_text())
    template = (MODEL / "atom_classification_prompt.txt").read_text()
    validator = Draft202012Validator(schema)
    out.mkdir(parents=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_one, record, repeat, schema, validator, template, out) for record in records for repeat in REPEATS[:args.repeats]]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    completion = {"status": "complete" if all(result["status"] == "valid" for result in results) else "complete_with_failures", "model": "gpt-5.6-terra", "reasoning_effort": "medium", "records": len(records), "repeat_count": args.repeats, "results": sorted(results, key=lambda result: (result["record_id"], result["repeat"])), "finished_at": now()}
    (out / "completion.json").write_text(json.dumps(completion, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": completion["status"], "valid": sum(result["status"] == "valid" for result in results), "planned": len(records) * args.repeats}, ensure_ascii=False))
    raise SystemExit(0 if completion["status"] == "complete" else 1)


if __name__ == "__main__":
    main()
