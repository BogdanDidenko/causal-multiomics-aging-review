#!/usr/bin/env python3
"""Measure entity-set stability for documents with repeated successful graphs."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "protocol/full_text/docling_graph_v1.0.0.json"


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def jaccard(left: set[Any], right: set[Any]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def graph_profile(path: Path) -> dict[str, set[Any]]:
    graph = json.loads(path.read_text(encoding="utf-8"))
    nodes = graph.get("nodes", [])
    return {
        "omics_layers": {
            (normalize(node.get("normalized_layer")), normalize(node.get("reported_name")))
            for node in nodes
            if node.get("label") == "OmicsLayer"
        },
        "omics_layer_types": {
            normalize(node.get("normalized_layer"))
            for node in nodes
            if node.get("label") == "OmicsLayer"
        },
        "causal_methods": {
            (
                normalize(node.get("method_name")),
                normalize(node.get("design_family")),
                normalize(node.get("identification_status")),
            )
            for node in nodes
            if node.get("label") == "CausalAnalysis"
        },
        "causal_family_status": {
            (
                normalize(node.get("design_family")),
                normalize(node.get("identification_status")),
            )
            for node in nodes
            if node.get("label") == "CausalAnalysis"
        },
        "aging_constructs": {
            (normalize(node.get("reported_name")), normalize(node.get("role")))
            for node in nodes
            if node.get("label") == "AgingConstruct"
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = json.loads(args.config.resolve().read_text(encoding="utf-8"))
    output_root = (REPO / config["runtime"]["output_root"]).resolve()
    attempts = [
        json.loads(line)
        for line in (output_root / "run_manifest.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for attempt in attempts:
        if attempt.get("status") == "success":
            grouped.setdefault(str(attempt["document_id"]), []).append(attempt)

    rows: list[dict[str, Any]] = []
    dimensions = (
        "omics_layers",
        "omics_layer_types",
        "causal_methods",
        "causal_family_status",
        "aging_constructs",
    )
    for successes in grouped.values():
        if len(successes) < 2:
            continue
        first, second = successes[-2:]
        left = graph_profile(REPO / str(first["graph_path"]))
        right = graph_profile(REPO / str(second["graph_path"]))
        row: dict[str, Any] = {
            "document_id": second["document_id"],
            "doi": second["doi"],
            "first_graph_sha256": first["graph_sha256"],
            "second_graph_sha256": second["graph_sha256"],
            "whole_graph_hash_exact": first["graph_sha256"] == second["graph_sha256"],
        }
        for dimension in dimensions:
            row[f"{dimension}_exact"] = left[dimension] == right[dimension]
            row[f"{dimension}_jaccard"] = jaccard(left[dimension], right[dimension])
        rows.append(row)

    rows.sort(key=lambda row: str(row["doi"]))
    detail_path = output_root / "graph_repeat_stability.csv"
    fieldnames = list(rows[0]) if rows else ["document_id", "doi"]
    with detail_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary: dict[str, Any] = {
        "schema_version": "1.0.0",
        "repeated_documents": len(rows),
        "whole_graph_hash_exact": sum(bool(row["whole_graph_hash_exact"]) for row in rows),
        "interpretation": (
            "This quantifies preprocessing nondeterminism only. Graph agreement is not "
            "an eligibility acceptance gate because graphs do not make exclusions."
        ),
        "detail_csv": str(detail_path.relative_to(REPO)),
    }
    for dimension in dimensions:
        summary[f"{dimension}_exact"] = sum(bool(row[f"{dimension}_exact"]) for row in rows)
        summary[f"{dimension}_mean_jaccard"] = (
            mean(float(row[f"{dimension}_jaccard"]) for row in rows) if rows else None
        )
    (output_root / "graph_repeat_stability_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
