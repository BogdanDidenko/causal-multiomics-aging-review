#!/usr/bin/env python3
"""Build the PRISMA-aligned full-text preprocessing record from frozen ledgers."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "protocol/full_text/docling_graph_v1.0.0.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def latest_counts(path: Path) -> Counter[str]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        latest[str(row["document_id"])] = row
    return Counter(str(row["status"]) for row in latest.values())


def artifact(path: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(REPO)), "sha256": sha256_file(path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_root = (REPO / config["runtime"]["output_root"]).resolve()
    retrieval_path = REPO / config["corpus"]["retrieval_manifest"]
    retrieval_prisma_path = retrieval_path.with_name("prisma_retrieval.json")
    retrieval_prisma = json.loads(retrieval_prisma_path.read_text(encoding="utf-8"))
    original = retrieval_prisma["flow"]

    conversion_path = output_root / "conversion_manifest.jsonl"
    run_path = output_root / "run_manifest.jsonl"
    quality_path = output_root / "graph_quality_summary.json"
    stability_path = output_root / "graph_repeat_stability_summary.json"
    correction_path = output_root / "full_text_sufficiency_audit.csv"
    corpus_path = output_root / "corpus_manifest.csv"
    conversion = latest_counts(conversion_path)
    runs = latest_counts(run_path)
    quality = json.loads(quality_path.read_text(encoding="utf-8"))

    insufficient = runs["insufficient_full_text"]
    sufficient = runs["success"]
    corrected_not_retrieved = int(original["reports_not_retrieved"]) + insufficient
    complete = (
        sufficient == config["corpus"]["expected_sufficient_full_texts_after_conversion"]
        and insufficient == 1
        and runs["failed"] == 0
        and quality["graphs_audited"] == sufficient
    )
    result = {
        "schema_version": "1.0.0",
        "status": "full_text_preprocessing_complete" if complete else "in_progress",
        "prisma_counts": {
            "reports_sought_for_retrieval": original["reports_sought_for_retrieval"],
            "reports_not_retrieved_or_insufficient": corrected_not_retrieved,
            "reports_retrieved_and_sufficient_for_assessment": sufficient,
            "reports_assessed_for_eligibility": "pending",
        },
        "processing_counts": {
            "retrieval_candidates_presented_to_conversion": config["corpus"][
                "expected_retrieval_candidates"
            ],
            "canonical_docling_conversions": conversion["success"],
            "conversion_failures_due_to_insufficient_full_text": conversion["failed"],
            "luna_light_graphs_built": sufficient,
            "graph_extraction_failures": runs["failed"],
            "graph_nodes": quality["nodes"],
            "unresolved_graph_nodes": quality["unresolved_nodes"],
        },
        "methodological_boundary": (
            "Docling conversion and Luna Light graph extraction are preprocessing, not "
            "eligibility assessment. Graph absence cannot produce a PRISMA exclusion."
        ),
        "artifacts": {
            "config": artifact(config_path),
            "retrieval_snapshot": artifact(retrieval_prisma_path),
            "corpus_manifest": artifact(corpus_path),
            "conversion_manifest": artifact(conversion_path),
            "run_manifest": artifact(run_path),
            "quality_summary": artifact(quality_path),
            "repeat_stability_summary": artifact(stability_path),
            "sufficiency_correction": artifact(correction_path),
        },
    }
    output_path = output_root / "prisma_full_text_processing.json"
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
