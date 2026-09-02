#!/usr/bin/env python3
"""Freeze or verify the complete pre-model v0.3 extraction instrument."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_analysis_inventory import (
    build_compact_report_packet,
    packet_atom_ids,
)
from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    read_json,
    render_prompt,
    sha256_file,
    sha256_text,
    token_count,
    write_json,
)

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/v0.3.0"
INPUTS = REPO / "data/causal_extraction/v0.3.0_development/inputs"
MODEL_OUTPUT = REPO / "data/causal_extraction/v0.3.0_development/terra_5repeat"

ARTIFACT_PATHS = (
    "protocol/causal_extraction/v0.3.0/analysis_inventory.schema.json",
    "protocol/causal_extraction/v0.3.0/codebook.md",
    "protocol/causal_extraction/v0.3.0/lifecycle.json",
    "protocol/causal_extraction/v0.3.0/methodology.md",
    "protocol/causal_extraction/v0.3.0/packaging_audit.json",
    "protocol/causal_extraction/v0.3.0/prompt.txt",
    "protocol/causal_extraction/v0.3.0/runtime.json",
    "protocol/causal_extraction/v0.3.0/sample.json",
    "protocol/causal_extraction/v0.3.0/sampling_protocol.md",
    "protocol/causal_extraction/v0.3.0/stability_contract.json",
    "analysis/causal_extraction/v0.3.0_development/README.md",
    "analysis/causal_extraction/v0.3.0_development/reference_inventory.json",
    "analysis/causal_extraction/v0.3.0_development/reference_inventory_resolved.json",
    "scripts/freeze_causal_extraction_v0_3.py",
    "scripts/run_causal_extraction_v0_3.py",
    "scripts/summarize_causal_extraction_v0_3.py",
    "scripts/validate_causal_extraction_v0_3_inventory.py",
    "src/causal_multiomics_aging_review/causal_analysis_inventory.py",
    "tests/test_causal_analysis_inventory.py",
    "tests/test_causal_extraction_v0_3_inventory.py",
    "tests/test_causal_extraction_v0_3_sample.py",
    "tests/test_causal_extraction_v0_3_summary.py",
)


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def build_packaging_audit() -> dict[str, Any]:
    sample = read_json(SUITE / "sample.json")
    runtime = read_json(SUITE / "runtime.json")
    prompt_template = (SUITE / runtime["prompt"]).read_text(encoding="utf-8")
    codebook = (SUITE / runtime["codebook"]).read_text(encoding="utf-8")
    reports = []
    for sampled in sample["reports"]:
        document_id = sampled["document_id"]
        atom_path = INPUTS / document_id / "evidence_atom_index.json"
        atom_index = read_json(atom_path)
        if sha256_text(canonical_json(atom_index)) != sampled[
            "evidence_atom_index_sha256"
        ]:
            raise ValueError(f"Evidence index hash mismatch: {document_id}")
        packet = build_compact_report_packet(atom_index)
        source_ids = [atom["evidence_atom_id"] for atom in atom_index["atoms"]]
        serialized_ids = packet_atom_ids(packet)
        if source_ids != serialized_ids:
            raise ValueError(f"Packet coverage mismatch: {document_id}")
        rendered = render_prompt(
            prompt_template,
            {
                "REPORT_ID": sampled["report_id"],
                "CODEBOOK": codebook,
                "REPORT_PACKET": packet,
            },
        )
        rendered_tokens = token_count(rendered)
        if rendered_tokens > int(runtime["max_rendered_prompt_tokens"]):
            raise ValueError(
                f"Prompt for {document_id} has {rendered_tokens} tokens; limit is "
                f"{runtime['max_rendered_prompt_tokens']}"
            )
        reports.append(
            {
                "sample_order": sampled["sample_order"],
                "report_id": sampled["report_id"],
                "document_id": document_id,
                "atom_count": len(source_ids),
                "serialized_atom_count": len(serialized_ids),
                "atom_order_exact": source_ids == serialized_ids,
                "atom_ids_sha256": sha256_text(
                    json.dumps(source_ids, separators=(",", ":"))
                ),
                "packet_characters": len(packet),
                "packet_tokens": token_count(packet),
                "rendered_prompt_tokens": rendered_tokens,
                "rendered_prompt_sha256": sha256_text(rendered),
            }
        )
    return {
        "packaging_version": "all_evidence_atoms_compact_v1",
        "report_count": len(reports),
        "coverage_complete": all(item["atom_order_exact"] for item in reports),
        "omitted_atom_count": 0,
        "model_selected_content": False,
        "graph_selected_content": False,
        "context_window": runtime["context_window"],
        "max_rendered_prompt_tokens": runtime["max_rendered_prompt_tokens"],
        "observed_max_rendered_prompt_tokens": max(
            item["rendered_prompt_tokens"] for item in reports
        ),
        "reports": reports,
    }


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": relative(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def build_manifest() -> dict[str, Any]:
    artifacts = [file_record(REPO / path) for path in ARTIFACT_PATHS]
    sample = read_json(SUITE / "sample.json")
    source_data = [
        file_record(INPUTS / item["document_id"] / "evidence_atom_index.json")
        for item in sample["reports"]
    ]
    return {
        "manifest_version": "0.3.0",
        "suite_id": "causal_extraction_v0.3.0_development",
        "artifacts": artifacts,
        "source_data": source_data,
    }


def model_output_count() -> int:
    if not MODEL_OUTPUT.exists():
        return 0
    return sum(1 for path in MODEL_OUTPUT.rglob("normalized.json") if path.is_file())


def write_freeze() -> None:
    existing_outputs = model_output_count()
    if existing_outputs:
        raise ValueError(
            f"Refusing pre-model freeze after {existing_outputs} normalized outputs exist"
        )
    audit = build_packaging_audit()
    write_json(SUITE / "packaging_audit.json", audit)
    manifest = build_manifest()
    write_json(SUITE / "artifact_manifest.json", manifest)
    write_json(
        SUITE / "freeze.json",
        {
            "freeze_version": "0.3.0",
            "status": "frozen_before_first_v0_3_terra_output",
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "artifact_manifest_sha256": sha256_file(
                SUITE / "artifact_manifest.json"
            ),
            "model_output_count_at_freeze": existing_outputs,
            "development_only": True,
            "expert_gold_standard": False,
        },
    )


def check_freeze() -> None:
    expected_audit = build_packaging_audit()
    if read_json(SUITE / "packaging_audit.json") != expected_audit:
        raise ValueError("Packaging audit is stale")
    expected_manifest = build_manifest()
    if read_json(SUITE / "artifact_manifest.json") != expected_manifest:
        raise ValueError("Artifact manifest is stale")
    freeze = read_json(SUITE / "freeze.json")
    if freeze["status"] != "frozen_before_first_v0_3_terra_output":
        raise ValueError("Unexpected freeze status")
    if freeze["artifact_manifest_sha256"] != sha256_file(
        SUITE / "artifact_manifest.json"
    ):
        raise ValueError("Freeze does not match artifact manifest")


def main() -> None:
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
    print("v0.3 causal extraction freeze verified")


if __name__ == "__main__":
    main()
