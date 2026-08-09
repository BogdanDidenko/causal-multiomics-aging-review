#!/usr/bin/env python3
"""Audit graph integrity, provenance grounding, and model-provided evidence quotes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import unicodedata
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
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def latest_by_document(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        latest[str(row["document_id"])] = row
    return latest


def normalized_text(value: str) -> str:
    value = html.unescape(unicodedata.normalize("NFKC", value))
    value = re.sub(r"[*_`#]+", "", value)
    value = value.replace("\u00ad", "")
    value = re.sub(r"\s+", " ", value)
    return value.strip().casefold()


def evidence_quotes(value: Any) -> list[str]:
    quotes: list[str] = []
    if isinstance(value, dict):
        quote = value.get("quote")
        if isinstance(quote, str) and quote.strip():
            quotes.append(quote.strip())
        for child in value.values():
            quotes.extend(evidence_quotes(child))
    elif isinstance(value, list):
        for child in value:
            quotes.extend(evidence_quotes(child))
    return quotes


def audit_success(attempt: dict[str, Any]) -> dict[str, Any]:
    graph_path = REPO / str(attempt["graph_path"])
    provenance_path = REPO / str(attempt["provenance_path"])
    graph_hash_valid = graph_path.is_file() and sha256_file(graph_path) == attempt["graph_sha256"]
    provenance_hash_valid = (
        provenance_path.is_file() and sha256_file(provenance_path) == attempt["provenance_sha256"]
    )
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = graph.get("nodes", [])
    provenance_matches = Counter()
    unresolved = 0
    for node in nodes:
        provenance = node.get("__provenance__") or {}
        match = str(provenance.get("match") or provenance.get("scope") or "missing")
        provenance_matches[match] += 1
        if match in {"missing", "unresolved"}:
            unresolved += 1

    conversions = latest_by_document(
        read_jsonl(graph_path.parents[4] / "conversion_manifest.jsonl")
    )
    conversion = conversions[attempt["document_id"]]
    markdown_path = REPO / str(conversion["markdown_path"])
    markdown = markdown_path.read_text(encoding="utf-8")
    normalized_markdown = normalized_text(markdown)
    quotes = evidence_quotes(nodes)
    exact_quotes = sum(quote in markdown for quote in quotes)
    normalized_quotes = sum(normalized_text(quote) in normalized_markdown for quote in quotes)
    return {
        "document_id": attempt["document_id"],
        "doi": attempt["doi"],
        "status": "success",
        "graph_nodes": len(nodes),
        "graph_edges": len(graph.get("edges", [])),
        "grounded_nodes": len(nodes) - unresolved,
        "unresolved_nodes": unresolved,
        "all_nodes_grounded": unresolved == 0,
        "verbatim_nodes": provenance_matches["verbatim"],
        "observed_nodes": provenance_matches["observed"],
        "document_scope_nodes": provenance_matches["document"],
        "evidence_quotes": len(quotes),
        "evidence_quotes_exact": exact_quotes,
        "evidence_quotes_normalized": normalized_quotes,
        "evidence_quote_exact_fraction": exact_quotes / len(quotes) if quotes else None,
        "evidence_quote_normalized_fraction": (normalized_quotes / len(quotes) if quotes else None),
        "graph_hash_valid": graph_hash_valid,
        "provenance_hash_valid": provenance_hash_valid,
        "model_quotes_require_source_resolution": exact_quotes != len(quotes),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = json.loads(args.config.resolve().read_text(encoding="utf-8"))
    output_root = (REPO / config["runtime"]["output_root"]).resolve()
    attempts = latest_by_document(read_jsonl(output_root / "run_manifest.jsonl"))
    rows: list[dict[str, Any]] = []
    for attempt in attempts.values():
        if attempt.get("status") == "success":
            rows.append(audit_success(attempt))
        else:
            rows.append(
                {
                    "document_id": attempt["document_id"],
                    "doi": attempt["doi"],
                    "status": attempt.get("status", "missing"),
                }
            )

    rows.sort(key=lambda row: str(row["doi"]))
    csv_path = output_root / "graph_quality.csv"
    fieldnames = sorted({key for row in rows for key in row})
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    success = [row for row in rows if row["status"] == "success"]
    summary = {
        "schema_version": "1.0.0",
        "documents_audited": len(rows),
        "graphs_audited": len(success),
        "insufficient_full_text": sum(row["status"] == "insufficient_full_text" for row in rows),
        "graphs_with_all_nodes_grounded": sum(bool(row["all_nodes_grounded"]) for row in success),
        "nodes": sum(int(row["graph_nodes"]) for row in success),
        "unresolved_nodes": sum(int(row["unresolved_nodes"]) for row in success),
        "evidence_quotes": sum(int(row["evidence_quotes"]) for row in success),
        "evidence_quotes_exact": sum(int(row["evidence_quotes_exact"]) for row in success),
        "evidence_quotes_normalized": sum(
            int(row["evidence_quotes_normalized"]) for row in success
        ),
        "all_graph_hashes_valid": all(bool(row["graph_hash_valid"]) for row in success),
        "all_provenance_hashes_valid": all(bool(row["provenance_hash_valid"]) for row in success),
        "interpretation": (
            "Graph entities are evidence-index candidates only. Model-provided quotes "
            "must be resolved to deterministic source chunks before screening citations."
        ),
        "detail_csv": str(csv_path.relative_to(REPO)),
    }
    (output_root / "graph_quality_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_graph_hashes_valid"] and summary["all_provenance_hashes_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
