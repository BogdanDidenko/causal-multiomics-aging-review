#!/usr/bin/env python3
"""Audit technical failure 001 and freeze its schema-only correction."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    read_json,
    sha256_file,
    sha256_text,
    write_json,
)
from causal_multiomics_aging_review.runtime_schema import inline_local_json_schema

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/validation/v0.3.1-independent-15-v1.0.0"
FAILED_OUTPUT = REPO / "data/causal_extraction/v0.3.1_independent_validation/technical_failure_001"
ACTIVE_OUTPUT = (
    REPO / "data/causal_extraction/v0.3.1_independent_validation/independent_inventories"
)
SOURCE_COMMIT = "80f6659d2ee7909e947f7a0d0a15e2cfbf359898"

ALLOWED_CHANGED_PHASE1_PATHS = {
    "scripts/run_independent_causal_inventory.py",
    "tests/test_causal_extraction_v0_3_1_validation_sample.py",
}


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": relative(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def failed_file_inventory() -> list[dict[str, Any]]:
    paths = []
    for path in FAILED_OUTPUT.rglob("*"):
        if not path.is_file():
            continue
        if path.name in {"rendered_prompt.txt", "report_packet.txt"}:
            continue
        paths.append(path)
    return [file_record(path) for path in sorted(paths)]


def build_incident() -> dict[str, Any]:
    reviewers: dict[str, Any] = {}
    for reviewer_id in ("codex", "claude_opus_4_8"):
        root = FAILED_OUTPUT / reviewer_id
        calls = sorted((root / "calls").glob("*"))
        validations = [read_json(path / "validation.json") for path in calls]
        if len(calls) != 15:
            raise ValueError(f"Expected 15 failed calls for {reviewer_id}")
        if any(value.get("valid") is True for value in validations):
            raise ValueError(f"Technical incident contains a valid output: {reviewer_id}")
        if any((path / "normalized.json").exists() for path in calls):
            raise ValueError(f"Technical incident contains normalized output: {reviewer_id}")
        failures = [failure for value in validations for failure in value["failures"]]
        if len(failures) != 30 or any(failure["kind"] != "provider_error" for failure in failures):
            raise ValueError(f"Unexpected failure shape for {reviewer_id}")
        reviewers[reviewer_id] = {
            "assigned_calls": len(calls),
            "failed_calls": len(calls),
            "failed_attempts": len(failures),
            "valid_scientific_outputs": 0,
            "unique_prompt_hashes": len(
                {read_json(path / "request.json")["prompt_sha256"] for path in calls}
            ),
        }

    return {
        "incident_id": "independent_inventory_technical_failure_001",
        "classification": "pre_inference_json_schema_rejection",
        "source_freeze_commit": SOURCE_COMMIT,
        "scientific_outputs": 0,
        "reviewers": reviewers,
        "root_causes": {
            "codex": "allOf removal left array fields without type",
            "claude_opus_4_8": "CLI could not resolve Draft 2020-12 metaschema URI",
        },
        "scientific_contract_changed": False,
        "correction": "inline local refs/allOf and remove dialect metadata in CLI copy",
        "failed_artifact_inventory": failed_file_inventory(),
    }


def assert_original_scientific_artifacts_unchanged() -> None:
    original = read_json(SUITE / "phase1_artifact_manifest.json")
    for group in ("protocol_artifacts", "source_artifacts", "evidence_atom_indices"):
        for artifact in original[group]:
            if artifact["path"] in ALLOWED_CHANGED_PHASE1_PATHS:
                continue
            path = REPO / artifact["path"]
            if not path.is_file() or sha256_file(path) != artifact["sha256"]:
                raise ValueError(f"Original scientific artifact changed: {artifact['path']}")


def build_manifest() -> dict[str, Any]:
    original = read_json(SUITE / "phase1_artifact_manifest.json")
    technical_files = [
        SUITE / "technical_failure_001.md",
        SUITE / "technical_failure_001.json",
        REPO / "scripts/run_independent_causal_inventory.py",
        Path(__file__),
        REPO / "src/causal_multiomics_aging_review/runtime_schema.py",
        REPO / "tests/test_runtime_schema.py",
        REPO / "tests/test_causal_extraction_v0_3_1_validation_sample.py",
    ]
    scientific_protocol = [
        artifact
        for artifact in original["protocol_artifacts"]
        if artifact["path"] not in ALLOWED_CHANGED_PHASE1_PATHS
    ]
    scientific_contract = {
        "protocol_artifacts": scientific_protocol,
        "source_artifacts": original["source_artifacts"],
        "evidence_atom_indices": original["evidence_atom_indices"],
    }
    return {
        "manifest_version": "1.0.1-technical-revision-1",
        "source_phase1_manifest_sha256": sha256_file(SUITE / "phase1_artifact_manifest.json"),
        "source_phase1_freeze_sha256": sha256_file(SUITE / "phase1_freeze.json"),
        "scientific_contract_sha256": sha256_text(canonical_json(scientific_contract)),
        "protocol_artifacts": scientific_protocol + [file_record(path) for path in technical_files],
        "source_artifacts": original["source_artifacts"],
        "evidence_atom_indices": original["evidence_atom_indices"],
    }


def output_count() -> int:
    if not ACTIVE_OUTPUT.exists():
        return 0
    return sum(1 for path in ACTIVE_OUTPUT.rglob("normalized.json") if path.is_file())


def write_freeze() -> None:
    if output_count():
        raise ValueError("Refusing phase-1b freeze after valid outputs exist")
    assert_original_scientific_artifacts_unchanged()
    schema = read_json(SUITE / "reference_inventory.schema.json")
    compiled = inline_local_json_schema(schema)
    serialized = canonical_json(compiled)
    if any(key in serialized for key in ('"$ref"', '"allOf"', '"$schema"')):
        raise ValueError("CLI schema compilation still contains unsupported composition")
    write_json(SUITE / "technical_failure_001.json", build_incident())
    write_json(SUITE / "phase1b_artifact_manifest.json", build_manifest())
    write_json(
        SUITE / "phase1b_freeze.json",
        {
            "freeze_version": "1.0.1-technical-revision-1",
            "status": "frozen_after_schema_fix_before_valid_outputs",
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "artifact_manifest_sha256": sha256_file(SUITE / "phase1b_artifact_manifest.json"),
            "valid_output_count_at_freeze": 0,
            "scientific_contract_changed": False,
        },
    )


def check_freeze() -> None:
    assert_original_scientific_artifacts_unchanged()
    if read_json(SUITE / "technical_failure_001.json") != build_incident():
        raise ValueError("Technical incident audit is stale")
    if read_json(SUITE / "phase1b_artifact_manifest.json") != build_manifest():
        raise ValueError("Phase-1b manifest is stale")
    freeze = read_json(SUITE / "phase1b_freeze.json")
    if freeze["artifact_manifest_sha256"] != sha256_file(SUITE / "phase1b_artifact_manifest.json"):
        raise ValueError("Phase-1b freeze does not match its manifest")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("Choose exactly one of --write or --check")
    if args.write:
        write_freeze()
    else:
        check_freeze()
    print(json.dumps({"status": "verified", "valid_outputs": output_count()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
