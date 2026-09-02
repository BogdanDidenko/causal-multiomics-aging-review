#!/usr/bin/env python3
"""Freeze or verify the pre-model v0.3.1 fixed-candidate ablation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_analysis_inventory import (
    build_compact_report_packet,
    packet_atom_ids,
)
from causal_multiomics_aging_review.causal_candidate_classification import (
    render_candidate_scaffold,
    validate_candidate_scaffold,
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
SUITE = REPO / "protocol/causal_extraction/v0.3.1"
INPUTS = REPO / "data/causal_extraction/v0.3.0_development/inputs"
MODEL_OUTPUT = REPO / "data/causal_extraction/v0.3.1_development/terra_5repeat"

ARTIFACT_PATHS = (
    "protocol/causal_extraction/v0.3.1/CHANGELOG.md",
    "protocol/causal_extraction/v0.3.1/candidate_classification.schema.json",
    "protocol/causal_extraction/v0.3.1/candidate_scaffold.json",
    "protocol/causal_extraction/v0.3.1/codebook.md",
    "protocol/causal_extraction/v0.3.1/lifecycle.json",
    "protocol/causal_extraction/v0.3.1/methodology.md",
    "protocol/causal_extraction/v0.3.1/packaging_audit.json",
    "protocol/causal_extraction/v0.3.1/prompt.txt",
    "protocol/causal_extraction/v0.3.1/runtime.json",
    "protocol/causal_extraction/v0.3.1/sample.json",
    "protocol/causal_extraction/v0.3.1/stability_contract.json",
    "analysis/causal_extraction/v0.3.1_development/candidate_reference_key.json",
    "scripts/freeze_causal_extraction_v0_3_1.py",
    "scripts/prepare_causal_extraction_v0_3_1.py",
    "scripts/run_causal_extraction_v0_3_1.py",
    "scripts/summarize_causal_extraction_v0_3_1.py",
    "src/causal_multiomics_aging_review/causal_candidate_classification.py",
    "tests/test_causal_candidate_classification.py",
    "tests/test_causal_extraction_v0_3_1_sample.py",
    "tests/test_causal_extraction_v0_3_1_summary.py",
)


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def build_packaging_audit() -> dict[str, Any]:
    sample = read_json(SUITE / "sample.json")
    runtime = read_json(SUITE / "runtime.json")
    scaffold = read_json(SUITE / runtime["candidate_scaffold"])
    scaffold_reports = {
        report["document_id"]: report for report in scaffold["reports"]
    }
    prompt_template = (SUITE / runtime["prompt"]).read_text(encoding="utf-8")
    codebook = (SUITE / runtime["codebook"]).read_text(encoding="utf-8")
    reports = []
    for sampled in sample["reports"]:
        document_id = sampled["document_id"]
        atom_index = read_json(INPUTS / document_id / "evidence_atom_index.json")
        if sha256_text(canonical_json(atom_index)) != sampled[
            "evidence_atom_index_sha256"
        ]:
            raise ValueError(f"Evidence index hash mismatch: {document_id}")
        packet = build_compact_report_packet(atom_index)
        source_ids = [atom["evidence_atom_id"] for atom in atom_index["atoms"]]
        if packet_atom_ids(packet) != source_ids:
            raise ValueError(f"Packet coverage mismatch: {document_id}")
        candidate_report = scaffold_reports[document_id]
        errors = validate_candidate_scaffold(candidate_report, atom_index)
        if errors:
            raise ValueError(f"Candidate scaffold mismatch: {document_id}: {errors}")
        rendered_scaffold = render_candidate_scaffold(candidate_report)
        rendered = render_prompt(
            prompt_template,
            {
                "REPORT_ID": sampled["report_id"],
                "CODEBOOK": codebook,
                "CANDIDATE_SCAFFOLD": rendered_scaffold,
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
                "serialized_atom_count": len(packet_atom_ids(packet)),
                "candidate_count": len(candidate_report["candidates"]),
                "atom_order_exact": packet_atom_ids(packet) == source_ids,
                "candidate_scaffold_sha256": sha256_text(rendered_scaffold),
                "packet_sha256": sha256_text(packet),
                "rendered_prompt_tokens": rendered_tokens,
                "rendered_prompt_sha256": sha256_text(rendered),
            }
        )
    return {
        "packaging_version": "fixed_candidate_scaffold_v1_plus_all_evidence_atoms_compact_v1",
        "report_count": len(reports),
        "candidate_count": sum(item["candidate_count"] for item in reports),
        "coverage_complete": all(item["atom_order_exact"] for item in reports),
        "omitted_report_atom_count": 0,
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
        "manifest_version": "0.3.1",
        "suite_id": "causal_extraction_v0.3.1_fixed_candidate_ablation",
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
    write_json(SUITE / "packaging_audit.json", build_packaging_audit())
    write_json(SUITE / "artifact_manifest.json", build_manifest())
    write_json(
        SUITE / "freeze.json",
        {
            "freeze_version": "0.3.1",
            "status": "frozen_before_first_v0_3_1_terra_output",
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "artifact_manifest_sha256": sha256_file(
                SUITE / "artifact_manifest.json"
            ),
            "model_output_count_at_freeze": existing_outputs,
            "development_only": True,
            "expert_gold_standard": False,
            "conditional_on_fixed_candidate_scaffold": True,
        },
    )


def check_freeze() -> None:
    if read_json(SUITE / "packaging_audit.json") != build_packaging_audit():
        raise ValueError("Packaging audit is stale")
    if read_json(SUITE / "artifact_manifest.json") != build_manifest():
        raise ValueError("Artifact manifest is stale")
    freeze = read_json(SUITE / "freeze.json")
    if freeze["status"] != "frozen_before_first_v0_3_1_terra_output":
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
    print("v0.3.1 causal extraction freeze verified")


if __name__ == "__main__":
    main()
