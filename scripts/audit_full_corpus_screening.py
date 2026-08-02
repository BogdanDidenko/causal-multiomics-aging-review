#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.v1 import (
    CAUSAL_DECISION_FIELDS,
    SCOPE_DECISION_FIELDS,
    derive_title_result,
    validate_causal_answer_consistency,
    validate_scope_answer_consistency,
    validate_title_evidence_spans,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"Expected JSON objects in {path}")
                rows.append(value)
    return rows


def exact_fields(runs: list[dict[str, Any]], fields: tuple[str, ...]) -> bool:
    return all(
        len({json.dumps(run.get(field), sort_keys=True) for run in runs}) == 1 for field in fields
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit coverage, identity, evidence, routing, and stability"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("missing_abstract", type=Path)
    parser.add_argument("runs_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-repeats", type=int, default=5)
    args = parser.parse_args()

    inputs = read_csv(args.input)
    missing_abstract = read_csv(args.missing_abstract)
    input_by_id = {row["record_id"]: row for row in inputs}
    input_ids = [row["record_id"] for row in inputs]
    missing_ids = [row["record_id"] for row in missing_abstract]

    results = []
    raw_attempts = []
    shard_manifests = []
    for shard_dir in sorted(args.runs_dir.glob("shard_*")):
        results.extend(read_jsonl(shard_dir / "screening_results.jsonl"))
        raw_attempts.extend(read_jsonl(shard_dir / "raw_provider_responses.jsonl"))
        shard_manifests.append(read_json(shard_dir / "manifest.json"))

    result_ids = [str(row["record_id"]) for row in results]
    result_counts = Counter(result_ids)
    duplicate_result_ids = sorted(key for key, count in result_counts.items() if count > 1)
    missing_result_ids = sorted(set(input_ids) - set(result_ids))
    unexpected_result_ids = sorted(set(result_ids) - set(input_ids))

    input_dois = [row["doi"] for row in inputs if row.get("doi")]
    missing_dois = [row["doi"] for row in missing_abstract if row.get("doi")]
    all_dois = input_dois + missing_dois
    doi_record_id_mismatches = sorted(
        row["record_id"]
        for row in inputs + missing_abstract
        if row.get("doi") and row["record_id"] != f"doi:{row['doi']}"
    )

    evidence_errors = []
    routing_errors = []
    repeat_errors = []
    scope_assessed = 0
    causal_assessed = 0
    scope_exact = 0
    causal_exact = 0
    all_assessed_exact = 0
    accepted_evidence_spans = 0
    for result in results:
        source = input_by_id[result["record_id"]]
        role_runs = result.get("role_runs") or {}
        scope_runs = role_runs.get("scope_reviewer") or []
        causal_runs = role_runs.get("causal_method_reviewer") or []
        if not scope_runs:
            continue
        scope_assessed += 1
        if len(scope_runs) != args.expected_repeats:
            repeat_errors.append(f"{result['record_id']}:scope={len(scope_runs)}")
        scope_is_exact = exact_fields(scope_runs, SCOPE_DECISION_FIELDS)
        scope_exact += scope_is_exact
        for answer in scope_runs:
            try:
                validate_title_evidence_spans(answer, source)
                validate_scope_answer_consistency(answer)
                accepted_evidence_spans += len(answer.get("evidence_spans", []))
            except ValueError as error:
                evidence_errors.append(f"{result['record_id']}:scope:{error}")

        causal_is_exact = True
        if causal_runs:
            causal_assessed += 1
            if len(causal_runs) != args.expected_repeats:
                repeat_errors.append(f"{result['record_id']}:causal={len(causal_runs)}")
            causal_is_exact = exact_fields(causal_runs, CAUSAL_DECISION_FIELDS)
            causal_exact += causal_is_exact
            for answer in causal_runs:
                try:
                    validate_title_evidence_spans(answer, source)
                    validate_causal_answer_consistency(answer)
                    accepted_evidence_spans += len(answer.get("evidence_spans", []))
                except ValueError as error:
                    evidence_errors.append(f"{result['record_id']}:causal:{error}")
        all_assessed_exact += scope_is_exact and causal_is_exact

        recomputed = derive_title_result(scope_runs, causal_runs or None)
        for field in ("final_decision", "final_exclusion_code", "decision_reason"):
            if result.get(field) != recomputed.get(field):
                routing_errors.append(f"{result['record_id']}:{field}")

    orchestrator = read_json(args.runs_dir / "orchestrator_manifest.json")
    manifest_suite_hashes = Counter(
        str(manifest.get("suite_config_sha256")) for manifest in shard_manifests
    )
    manifest_models = Counter(str(manifest.get("model")) for manifest in shard_manifests)
    manifest_record_total = sum(int(manifest["input_record_count"]) for manifest in shard_manifests)
    manifest_decision_total = Counter()
    for manifest in shard_manifests:
        manifest_decision_total.update(manifest.get("decision_counts", {}))

    decision_counts = Counter(str(row["final_decision"]) for row in results)
    exclusion_counts = Counter(str(row.get("final_exclusion_code", "none")) for row in results)
    reason_counts = Counter(
        str(row.get("decision_reason") or row.get("manual_review_reason") or "unknown")
        for row in results
    )
    manual_reason_counts = Counter(
        str(row.get("manual_review_reason", "unknown"))
        for row in results
        if row["final_decision"] == "manual_review"
    )
    attempt_status = Counter(str(row.get("status", "unknown")) for row in raw_attempts)
    retry_attempts = sum(int(row.get("attempt", 1)) > 1 for row in raw_attempts)

    integrity_errors = {
        "duplicate_input_record_ids": len(input_ids) - len(set(input_ids)),
        "duplicate_missing_abstract_record_ids": len(missing_ids) - len(set(missing_ids)),
        "input_missing_queue_overlap": len(set(input_ids) & set(missing_ids)),
        "duplicate_result_record_ids": len(duplicate_result_ids),
        "missing_result_record_ids": len(missing_result_ids),
        "unexpected_result_record_ids": len(unexpected_result_ids),
        "duplicate_normalized_doi": len(all_dois) - len(set(all_dois)),
        "doi_record_id_mismatches": len(doi_record_id_mismatches),
        "evidence_or_consistency_errors": len(evidence_errors),
        "routing_recomputation_errors": len(routing_errors),
        "repeat_count_errors": len(repeat_errors),
        "shard_manifest_count_mismatch": int(len(shard_manifests) != 96),
        "shard_manifest_record_total_mismatch": int(manifest_record_total != len(inputs)),
        "shard_manifest_decision_mismatch": int(manifest_decision_total != decision_counts),
        "suite_hash_mismatch": int(
            len(manifest_suite_hashes) != 1
            or next(iter(manifest_suite_hashes), None) != orchestrator.get("suite_config_sha256")
        ),
        "model_mismatch": int(
            len(manifest_models) != 1
            or next(iter(manifest_models), None) != orchestrator.get("model")
        ),
    }
    core_integrity_passed = not any(integrity_errors.values())
    model_assessed_stability_rate = all_assessed_exact / scope_assessed if scope_assessed else None
    full_input_stability_rate = all_assessed_exact / len(inputs) if inputs else None

    report = {
        "status": (
            "complete_integrity_passed_stability_failed"
            if core_integrity_passed and model_assessed_stability_rate != 1.0
            else "complete_integrity_and_stability_passed"
            if core_integrity_passed
            else "integrity_failed"
        ),
        "core_integrity_passed": core_integrity_passed,
        "stability_gate_passed": model_assessed_stability_rate == 1.0,
        "production_instrument_accepted": False,
        "interpretation": (
            "The complete corpus may be routed conservatively because only unanimous "
            "exclusions are automatic. The prompt suite remains unvalidated because the "
            "predeclared 100% all-tracked-field stability gate was not met."
        ),
        "population": {
            "canonical_records": len(inputs) + len(missing_abstract),
            "records_with_abstract": len(inputs),
            "records_missing_abstract": len(missing_abstract),
            "records_with_doi": len(all_dois),
            "unique_normalized_doi": len(set(all_dois)),
            "records_without_doi": len(inputs) + len(missing_abstract) - len(all_dois),
        },
        "coverage": {
            "result_records": len(results),
            "unique_result_record_ids": len(set(result_ids)),
            "shard_manifests": len(shard_manifests),
            "orchestrator_status": orchestrator.get("status"),
            "failed_shards": orchestrator.get("failed_shards"),
        },
        "routing": {
            "decision_counts": dict(sorted(decision_counts.items())),
            "exclusion_code_counts": dict(sorted(exclusion_counts.items())),
            "decision_reason_counts": dict(sorted(reason_counts.items())),
            "manual_review_reason_counts": dict(sorted(manual_reason_counts.items())),
        },
        "stability": {
            "expected_repeats": args.expected_repeats,
            "scope_assessed_records": scope_assessed,
            "scope_all_tracked_exact_records": scope_exact,
            "scope_all_tracked_exact_rate": scope_exact / scope_assessed,
            "causal_assessed_records": causal_assessed,
            "causal_all_tracked_exact_records": causal_exact,
            "causal_all_tracked_exact_rate": causal_exact / causal_assessed,
            "all_assessed_fields_exact_records": all_assessed_exact,
            "all_assessed_fields_exact_rate_among_model_assessed": model_assessed_stability_rate,
            "all_assessed_fields_exact_rate_among_full_abstract_input": full_input_stability_rate,
        },
        "provider_attempts": {
            "total": len(raw_attempts),
            "status_counts": dict(sorted(attempt_status.items())),
            "retry_attempts": retry_attempts,
        },
        "evidence_audit": {
            "accepted_evidence_spans_checked": accepted_evidence_spans,
            "unsupported_or_inconsistent": len(evidence_errors),
        },
        "runtime": {
            "model": orchestrator.get("model"),
            "reasoning_effort": orchestrator.get("reasoning_effort"),
            "suite_version": orchestrator.get("suite_version"),
            "suite_approval_status": orchestrator.get("suite_approval_status"),
            "suite_config_sha256": orchestrator.get("suite_config_sha256"),
            "git_revision": orchestrator.get("git_revision"),
            "started_at": orchestrator.get("started_at"),
            "completed_at": orchestrator.get("completed_at"),
            "workers": orchestrator.get("workers"),
        },
        "integrity_errors": integrity_errors,
        "error_examples": {
            "evidence": evidence_errors[:10],
            "routing": routing_errors[:10],
            "repeats": repeat_errors[:10],
            "duplicate_results": duplicate_result_ids[:10],
            "missing_results": missing_result_ids[:10],
            "unexpected_results": unexpected_result_ids[:10],
            "doi_record_id_mismatches": doi_record_id_mismatches[:10],
        },
        "artifacts": {
            "input": {"path": str(args.input), "sha256": sha256(args.input)},
            "missing_abstract": {
                "path": str(args.missing_abstract),
                "sha256": sha256(args.missing_abstract),
            },
            "runs_dir": str(args.runs_dir),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"integrity={core_integrity_passed} stability={report['stability_gate_passed']} "
        f"records={len(results)} decisions={dict(decision_counts)}"
    )
    if not core_integrity_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
