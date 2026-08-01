#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

FIELDS = (
    "source",
    "branch",
    "record_id",
    "title",
    "abstract",
    "year",
    "doi",
    "local_omics_layers",
    "local_aging_match",
    "local_causal_anchor_match",
    "local_three_block_match",
    "reviewer_retrieval_relevant",
    "reviewer_aging_relevant",
    "reviewer_multiomics_valid",
    "reviewer_formal_causal_basis",
    "reviewer_design_family",
    "reviewer_notes",
)


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def stable_key(seed: str, source: str, branch: str, row: dict[str, str]) -> str:
    identifier = row.get("doi") or row.get("source_record_id") or row.get("title", "")
    return hashlib.sha256(f"{seed}|{source}|{branch}|{identifier}".encode()).hexdigest()


def output_row(row: dict[str, str], branch: str) -> dict[str, str]:
    return {
        "source": row.get("source", ""),
        "branch": branch,
        "record_id": row.get("source_record_id", ""),
        "title": row.get("title", ""),
        "abstract": row.get("abstract", ""),
        "year": row.get("year", ""),
        "doi": row.get("doi", ""),
        "local_omics_layers": row.get("local_omics_layers", ""),
        "local_aging_match": row.get("local_aging_match", ""),
        "local_causal_anchor_match": row.get("local_causal_anchor_match", ""),
        "local_three_block_match": row.get("local_three_block_match", ""),
        "reviewer_retrieval_relevant": "",
        "reviewer_aging_relevant": "",
        "reviewer_multiomics_valid": "",
        "reviewer_formal_causal_basis": "",
        "reviewer_design_family": "",
        "reviewer_notes": "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build deterministic 50-record QA sheets per search branch"
    )
    parser.add_argument("search_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--records-per-branch", type=int, default=50)
    parser.add_argument("--seed", default="causal-multiomics-aging-search-v1")
    args = parser.parse_args()

    normalized_dir = args.search_dir / "normalized"
    source_files = sorted(
        path for path in normalized_dir.glob("*.csv") if path.name != "all_sources.csv"
    )
    if not source_files:
        raise SystemExit(f"No normalized source CSVs found in {normalized_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"version": "1.0.0", "samples": []}
    for source_file in source_files:
        with source_file.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        source = source_file.stem
        branches = {
            "explicit_multiomics": [
                row for row in rows if truthy(row["local_explicit_multiomics_match"])
            ],
            "layer_pair": [
                row for row in rows if truthy(row["local_layer_pair_match"])
            ],
        }
        for branch, candidates in branches.items():
            candidates.sort(key=lambda row: stable_key(args.seed, source, branch, row))
            sample = candidates[: args.records_per_branch]
            output = args.output_dir / f"{source}_{branch}_qa.csv"
            with output.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=FIELDS, lineterminator="\n"
                )
                writer.writeheader()
                writer.writerows(output_row(row, branch) for row in sample)
            manifest["samples"].append(
                {
                    "source": source,
                    "branch": branch,
                    "available": len(candidates),
                    "sampled": len(sample),
                    "path": str(output),
                    "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                    "status": "pending_manual_quality_review",
                }
            )
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"built samples={len(manifest['samples'])}")


if __name__ == "__main__":
    main()
