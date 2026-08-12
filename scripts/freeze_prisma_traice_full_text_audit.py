#!/usr/bin/env python3
"""Freeze PRISMA-trAIce audit metadata and manual-adjudication packets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.config import REPO_ROOT
from causal_multiomics_aging_review.v1 import package_full_text_sections


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def file_row(path: Path, category: str, restricted: bool) -> dict[str, Any]:
    return {
        "path": relative(path),
        "category": category,
        "restricted": restricted,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    parser.add_argument("input_root", type=Path)
    parser.add_argument("suite_config", type=Path)
    parser.add_argument("public_output", type=Path)
    args = parser.parse_args()

    run_root = args.run_root.resolve()
    input_root = args.input_root.resolve()
    suite_path = args.suite_config.resolve()
    public = args.public_output.resolve()
    restricted = run_root / "restricted_audit"
    restricted.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)

    suite = read_json(suite_path)
    full_text = suite["stages"]["full_text"]
    input_rows = read_jsonl(input_root / "input.jsonl")
    inputs = {str(row["record_id"]): row for row in input_rows}

    results: dict[str, dict[str, Any]] = {}
    attempts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    attempt_refs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    raw_files = sorted((run_root / "runs").glob("*/raw_provider_responses.jsonl"))
    result_files = sorted((run_root / "runs").glob("*/screening_results.jsonl"))
    for path in result_files:
        for row in read_jsonl(path):
            results[str(row["record_id"])] = row
    for path in raw_files:
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            row = json.loads(line)
            identifier = str(row["record_id"])
            attempts[identifier].append(row)
            response = row.get("response", {})
            stderr = response.get("stderr", "") if isinstance(response, dict) else ""
            attempt_refs[identifier].append(
                {
                    "path": relative(path),
                    "line": line_number,
                    "role": row.get("role"),
                    "repeat_index": row.get("repeat_index"),
                    "attempt": row.get("attempt"),
                    "status": row.get("status"),
                    "error": row.get("error", ""),
                    "response_sha256": hashlib.sha256(
                        json.dumps(response, sort_keys=True).encode("utf-8")
                    ).hexdigest(),
                    "rendered_prompt_preserved": "\nuser\n" in stderr,
                }
            )

    manual_ids = sorted(
        identifier
        for identifier, row in results.items()
        if row["final_decision"] == "manual_review"
    )
    if len(manual_ids) != 25:
        raise SystemExit(f"Expected 25 manual-review records, found {len(manual_ids)}")

    restricted_packets = []
    public_index = []
    form_rows = []
    for identifier in manual_ids:
        record = inputs[identifier]
        result = results[identifier]
        selected, selection = package_full_text_sections(
            record["sections"], full_text["deterministic_section_packaging"]
        )
        refs = attempt_refs[identifier]
        restricted_packets.append(
            {
                "record": record,
                "deterministic_selected_sections": selected,
                "section_selection": selection,
                "screening_result": result,
                "raw_attempts": attempts[identifier],
                "raw_attempt_references": refs,
            }
        )
        disagreement_fields = sorted(
            f"{role}.{field}"
            for role, fields in result.get("role_agreement", {}).items()
            for field, audit in fields.items()
            if not audit.get("unanimous", False)
        )
        public_index.append(
            {
                "record_id": identifier,
                "doi": record.get("doi", ""),
                "title": record.get("title", ""),
                "manual_review_reason": result.get("manual_review_reason", ""),
                "decision_reason": result.get("decision_reason", ""),
                "disagreement_fields": disagreement_fields,
                "scope_runs": len(result.get("role_runs", {}).get("scope_reviewer", [])),
                "causal_runs": len(
                    result.get("role_runs", {}).get("causal_method_reviewer", [])
                ),
                "attempt_references": refs,
            }
        )
        form_rows.append(
            {
                "record_id": identifier,
                "doi": record.get("doi", ""),
                "title": record.get("title", ""),
                "human_reviewer_id": "",
                "human_decision": "",
                "first_failed_criterion": "",
                "human_rationale": "",
                "supporting_section_ids": "",
                "adjudication_status": "pending",
            }
        )

    packet_path = restricted / "manual_adjudication_packets_25.jsonl"
    write_jsonl(packet_path, restricted_packets)
    index_path = public / "manual_adjudication_queue_25_index.jsonl"
    write_jsonl(index_path, public_index)
    form_path = public / "manual_adjudication_form_25.csv"
    with form_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(form_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(form_rows)

    inventory = []
    for path in raw_files:
        inventory.append(file_row(path, "raw_model_attempts", True))
    for path in result_files:
        inventory.append(file_row(path, "record_results", True))
    for path in sorted((run_root / "logs").glob("*")):
        if path.is_file():
            inventory.append(file_row(path, "orchestrator_logs", True))
    inventory.extend(
        [
            file_row(input_root / "input.jsonl", "full_text_input", True),
            file_row(input_root / "input_manifest.json", "input_manifest", False),
            file_row(run_root / "orchestrator_manifest.json", "run_manifest", False),
            file_row(run_root / "stability_summary.json", "aggregate_result", False),
            file_row(run_root / "stability_ledger.csv", "aggregate_result", False),
            file_row(run_root / "prisma_full_text_screening.json", "aggregate_result", False),
            file_row(suite_path, "suite_config", False),
            file_row(packet_path, "manual_adjudication_packet", True),
            file_row(index_path, "manual_adjudication_index", False),
            file_row(form_path, "manual_adjudication_form", False),
        ]
    )
    for role_config in full_text["roles"].values():
        for key in ("template", "evidence_profile", "schema"):
            path = REPO_ROOT / "protocol/screening" / role_config[key]
            inventory.append(file_row(path, key, False))
    for path in [
        REPO_ROOT / "scripts/run_full_text_corpus_screening.py",
        REPO_ROOT / "scripts/run_screening.py",
        REPO_ROOT / "scripts/build_deterministic_full_text_corpus.py",
        REPO_ROOT / "scripts/summarize_shared_template_full_text.py",
        REPO_ROOT / "src/causal_multiomics_aging_review/screening.py",
        REPO_ROOT / "src/causal_multiomics_aging_review/v1.py",
        REPO_ROOT / "src/causal_multiomics_aging_review/prompt_templates.py",
    ]:
        inventory.append(file_row(path, "execution_code", False))

    status_counts = Counter(
        row.get("status") for rows in attempts.values() for row in rows
    )
    prompt_preserved = sum(
        ref["rendered_prompt_preserved"]
        for refs in attempt_refs.values()
        for ref in refs
    )
    manifest = {
        "manifest_version": "1.0.0",
        "method_version": suite["suite_version"],
        "run_root": relative(run_root),
        "restricted_content_policy": (
            "Raw rendered prompts and packets contain copyrighted article text; "
            "they remain in restricted local storage. Public artifacts preserve "
            "paths, counts, SHA-256 hashes, and nontext adjudication provenance."
        ),
        "records": len(results),
        "manual_adjudication_records": len(manual_ids),
        "raw_attempts": sum(status_counts.values()),
        "raw_attempt_status_counts": dict(status_counts),
        "attempts_with_exact_rendered_prompt_preserved": prompt_preserved,
        "attempts_with_transport_response": sum(len(rows) for rows in attempts.values()),
        "manual_packet": file_row(packet_path, "manual_adjudication_packet", True),
        "manual_index": file_row(index_path, "manual_adjudication_index", False),
        "human_form": file_row(form_path, "manual_adjudication_form", False),
        "inventory": sorted(inventory, key=lambda row: row["path"]),
    }
    manifest_path = public / "prisma_traice_audit_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "manifest": relative(manifest_path),
                "inventory_files": len(inventory),
                "raw_attempts": sum(status_counts.values()),
                "rendered_prompts_preserved": prompt_preserved,
                "manual_records": len(manual_ids),
                "restricted_packet_sha256": sha256(packet_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
