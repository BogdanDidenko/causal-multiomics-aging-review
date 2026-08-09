#!/usr/bin/env python3
"""Freeze the locally available full-text corpus for Docling Graph processing."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def document_id(doi: str) -> str:
    return "doi_" + hashlib.sha256(doi.casefold().encode()).hexdigest()[:16]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def build_rows(config_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source_path = REPO / config["corpus"]["retrieval_manifest"]
    accepted = set(config["corpus"]["accepted_statuses"])
    source_rows = read_jsonl(source_path)
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for source in source_rows:
        if source.get("target_status") not in accepted or not source.get("selected_file"):
            continue
        doi = str(source["doi"]).strip().casefold()
        if not doi or doi in seen:
            raise ValueError(f"Missing or duplicate selected DOI: {doi!r}")
        seen.add(doi)
        local_path = REPO / str(source["selected_file"])
        if not local_path.is_file():
            raise FileNotFoundError(local_path)
        rows.append(
            {
                "document_id": document_id(doi),
                "doi": doi,
                "title": str(source.get("title", "")),
                "record_id": str(source.get("record_id", "")),
                "source_format": local_path.suffix.lstrip(".").lower(),
                "source_path": str(local_path.relative_to(REPO)),
                "source_bytes": local_path.stat().st_size,
                "source_sha256": sha256_file(local_path),
                "retrieval_status": str(source["target_status"]),
            }
        )
    rows.sort(key=lambda row: row["doi"])
    expected = int(config["corpus"]["expected_retrieval_candidates"])
    if len(rows) != expected:
        raise ValueError(f"Expected {expected} selected full texts, found {len(rows)}")
    return config, rows


def write_manifest(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config, rows = build_rows(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "corpus_manifest.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "schema_version": "1.0.0",
        "status": "frozen_for_docling_graph_processing",
        "documents": len(rows),
        "format_counts": {
            suffix: sum(row["source_format"] == suffix for row in rows)
            for suffix in sorted({row["source_format"] for row in rows})
        },
        "source_bytes": sum(int(row["source_bytes"]) for row in rows),
        "config_path": str(config_path.relative_to(REPO)),
        "config_sha256": sha256_file(config_path),
        "retrieval_manifest": config["corpus"]["retrieval_manifest"],
        "retrieval_manifest_sha256": sha256_file(REPO / config["corpus"]["retrieval_manifest"]),
        "corpus_manifest": str(csv_path.relative_to(REPO)),
        "corpus_manifest_sha256": sha256_file(csv_path),
    }
    (output_dir / "corpus_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=REPO / "protocol/full_text/docling_graph_v1.0.0.json"
    )
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir = args.output_dir or REPO / config["runtime"]["output_root"]
    summary = write_manifest(config_path, output_dir.resolve())
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
