#!/usr/bin/env python3
"""Run three isolated Terra CMACM extractions on an unseen frozen sample."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import threading
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from causal_multiomics_aging_review.llm import CodexCliProvider, ProviderError


ROOT = Path(__file__).resolve().parents[1]
VERSION = "v1.0.3"
REPEATS = (1, 2, 3)
LOCK = threading.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(template: str, record: dict[str, Any]) -> str:
    values = {
        "REPORT_ID": record["record_id"],
        "DOI": record["doi"],
        "TITLE": record["title"],
        "SOURCE": record["source"],
        "YEAR": record["year"],
        "FULL_MARKDOWN": record["sections"][0]["text"],
    }
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def validate_semantics(answer: dict[str, Any], record: dict[str, Any], linearizations: dict[str, str]) -> list[str]:
    errors = []
    if answer.get("report_id") != record["record_id"]:
        errors.append("report_id does not match input")
    ids: dict[str, set[str]] = {}
    collections = {
        "report_version": [answer.get("report_version", {})],
        "study": answer.get("studies", []),
        "workflow": answer.get("workflows", []),
        "link": answer.get("links", []),
        "contrast": answer.get("contrasts", []),
        "validation": answer.get("validations", []),
        "evidence": answer.get("evidence", []),
        "assertion": [answer.get("extraction_assertion", {})],
    }
    all_ids: set[str] = set()
    for kind, values in collections.items():
        current = {value.get("id") for value in values if value.get("id")}
        if len(current) != len(values):
            errors.append(f"duplicate or missing {kind} identifier")
        if all_ids & current:
            errors.append(f"identifier reused across entity types: {sorted(all_ids & current)}")
        all_ids.update(current)
        ids[kind] = current

    if answer.get("report_version", {}).get("doi", "").lower() != record["doi"].lower():
        errors.append("report-version DOI does not match input")
    evidence = {item["id"]: item for item in answer.get("evidence", [])}
    markdown = record["sections"][0]["text"]
    for item in answer.get("evidence", []):
        if item["source_locator"] != "chunk:0000":
            errors.append(f"evidence {item['id']} has invalid source locator")
        if item["verbatim_quote"] not in markdown:
            errors.append(f"evidence {item['id']} quote is not an exact document substring")
        for supported in item["supports_ids"]:
            if supported not in all_ids:
                errors.append(f"evidence {item['id']} references unknown supported id {supported}")

    for workflow in answer.get("workflows", []):
        if workflow["study_id"] not in ids["study"]:
            errors.append(f"workflow {workflow['id']} references unknown study")
        if not workflow["source_evidence_ids"]:
            errors.append(f"workflow {workflow['id']} has no source evidence")
        for evidence_id in workflow["source_evidence_ids"]:
            if evidence_id not in evidence:
                errors.append(f"workflow {workflow['id']} references unknown evidence")
    for link in answer.get("links", []):
        if link["workflow_id"] not in ids["workflow"]:
            errors.append(f"link {link['id']} references unknown workflow")
        if not link["source_evidence_ids"]:
            errors.append(f"link {link['id']} has no source evidence")
        for evidence_id in link["source_evidence_ids"]:
            if evidence_id not in evidence:
                errors.append(f"link {link['id']} references unknown evidence")
    for contrast in answer.get("contrasts", []):
        if contrast["link_id"] not in ids["link"]:
            errors.append(f"contrast {contrast['id']} references unknown link")
        for evidence_id in contrast["source_evidence_ids"]:
            if evidence_id not in evidence:
                errors.append(f"contrast {contrast['id']} references unknown evidence")
    for validation in answer.get("validations", []):
        if validation["target_id"] not in ids["workflow"] | ids["link"] | ids["contrast"]:
            errors.append(f"validation {validation['id']} references unknown target")
        for evidence_id in validation["source_evidence_ids"]:
            if evidence_id not in evidence:
                errors.append(f"validation {validation['id']} references unknown evidence")

    views = {item["id"]: item for item in answer.get("linearizations", [])}
    if set(views) != set(linearizations):
        errors.append("linearization set differs from CMACM specification")
    expected_members = {
        "prisma_report_view": ids["report_version"],
        "evidence_base_view": ids["study"],
        "causal_leverage_view": ids["workflow"],
        "multiomics_contribution_view": {
            workflow["id"] for workflow in answer.get("workflows", []) if workflow["omics_layers"]
        },
        "aging_outcome_view": ids["link"],
        "strength_transport_view": ids["validation"],
        "audit_view": ids["assertion"],
    }
    for view_id, expected_unit in linearizations.items():
        view = views.get(view_id)
        if not view:
            continue
        if view["counting_unit"] != expected_unit:
            errors.append(f"{view_id} has wrong counting unit")
        members = set(view["member_ids"])
        if view_id == "aging_outcome_view":
            if not members <= ids["link"]:
                errors.append(f"{view_id} contains non-link member ids")
        elif members != expected_members[view_id]:
            errors.append(f"{view_id} member ids do not match Foundation entities")
    return errors


def run_call(record: dict[str, Any], repeat: int, schema: dict[str, Any], validator: Draft202012Validator, template: str, linearizations: dict[str, str], out: Path) -> dict[str, Any]:
    call_root = out / "records" / record["document_id"] / f"repeat_{repeat}"
    call_root.mkdir(parents=True, exist_ok=True)
    prompt = render(template, record)
    (call_root / "prompt_sha256.txt").write_text(hashlib.sha256(prompt.encode()).hexdigest() + "\n")
    provider = CodexCliProvider(
        "gpt-5.6-terra",
        timeout=3600,
        reasoning_effort="medium",
        context_window=None,
        max_tokens=None,
        audit_directory=call_root / "provider_audit",
    )
    failures = []
    for attempt in (1, 2):
        started = now()
        try:
            parsed, raw = provider.complete_json(prompt, schema, schema_name="cmacm_foundation_extraction")
            (call_root / f"raw_response_attempt_{attempt}.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n")
            (call_root / f"parsed_attempt_{attempt}.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n")
            errors = [error.message for error in validator.iter_errors(parsed)]
            if not errors:
                errors = validate_semantics(parsed, record, linearizations)
            if errors:
                failure = {"attempt": attempt, "kind": "validation", "errors": errors, "started_at": started, "finished_at": now()}
                failures.append(failure)
                (call_root / f"failure_attempt_{attempt}.json").write_text(json.dumps(failure, ensure_ascii=False, indent=2) + "\n")
                continue
            result_path = call_root / "result.json"
            result_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n")
            validation = {"valid": True, "attempt": attempt, "started_at": started, "finished_at": now(), "result_sha256": sha256(result_path)}
            (call_root / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n")
            return {"record_id": record["record_id"], "repeat": repeat, "status": "valid", "attempt": attempt, "result_path": str(result_path.relative_to(ROOT))}
        except ProviderError as error:
            failure = {"attempt": attempt, "kind": "provider", "error": str(error), "raw_response": error.raw_response, "started_at": started, "finished_at": now()}
            failures.append(failure)
            (call_root / f"failure_attempt_{attempt}.json").write_text(json.dumps(failure, ensure_ascii=False, indent=2) + "\n")
    (call_root / "validation.json").write_text(json.dumps({"valid": False, "failures": failures}, ensure_ascii=False, indent=2) + "\n")
    return {"record_id": record["record_id"], "repeat": repeat, "status": "failed"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=VERSION)
    parser.add_argument("--run-name", default="terra_three_runs")
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--repeats", type=int, choices=(1, 3), default=3)
    args = parser.parse_args()
    model = ROOT / f"protocol/content_model/{args.version}"
    base = ROOT / f"analysis/content_model_validation/{args.version}"
    input_path = base / "input.jsonl"
    out = base / args.run_name
    if out.exists():
        raise ValueError(f"Refuse to overwrite CMACM Terra validation: {out}")
    records = list(map(json.loads, input_path.open()))
    if args.max_records is not None:
        records = records[:args.max_records]
    schema = json.loads((model / "foundation_extraction.schema.json").read_text())
    template = (model / "foundation_extraction_prompt.txt").read_text()
    linearizations = {item["id"]: item["counting_unit"] for item in json.loads((model / "linearizations.json").read_text())["linearizations"]}
    validator = Draft202012Validator(schema)
    out.mkdir(parents=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_call, record, repeat, schema, validator, template, linearizations, out) for record in records for repeat in REPEATS[:args.repeats]]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    completion = {"status": "complete" if all(item["status"] == "valid" for item in results) else "complete_with_failures", "model": "gpt-5.6-terra", "reasoning_effort": "medium", "fresh_isolated_session_per_run": True, "repeat_count": args.repeats, "records": len(records), "results": sorted(results, key=lambda item: (item["record_id"], item["repeat"])), "finished_at": now()}
    (out / "completion.json").write_text(json.dumps(completion, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": completion["status"], "valid": sum(item["status"] == "valid" for item in results), "planned": len(records) * args.repeats}, ensure_ascii=False))
    raise SystemExit(0 if completion["status"] == "complete" else 1)


if __name__ == "__main__":
    main()
