#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from causal_multiomics_aging_review.metadata_quality import (
    title_abstract_metadata_issue,
)

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "protocol" / "screening" / "benchmarks"
SOURCE = BENCHMARKS / "title_abstract_boundary_pilot_v0.2.0_25.csv"
FILL = BENCHMARKS / "high_signal_development_25.csv"
OUTPUT = BENCHMARKS / "title_abstract_boundary_pilot_v0.3.0_25.csv"
MANIFEST = BENCHMARKS / "title_abstract_boundary_pilot_v0.3.0_manifest.json"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source_rows = read_rows(SOURCE)
    rejected = [
        row for row in source_rows if title_abstract_metadata_issue(row) is not None
    ]
    retained = [
        row for row in source_rows if title_abstract_metadata_issue(row) is None
    ]
    existing = {row["canonical_id"] for row in retained}
    candidates = [
        row
        for row in read_rows(FILL)
        if row["canonical_id"] not in existing
        and title_abstract_metadata_issue(row) is None
    ]
    candidates.sort(key=lambda row: hashlib.sha256(row["canonical_id"].encode()).hexdigest())
    replacements = candidates[: len(rejected)]
    if len(replacements) != len(rejected):
        raise RuntimeError("Not enough visible development records to refill pilot")

    output_rows = retained + replacements
    output_rows.sort(key=lambda row: row["canonical_id"])
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(source_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)

    manifest = {
        "benchmark_version": "boundary_pilot_v0.3.0",
        "record_count": len(output_rows),
        "source_path": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE),
        "fill_path": str(FILL.relative_to(ROOT)),
        "fill_sha256": sha256(FILL),
        "output_path": str(OUTPUT.relative_to(ROOT)),
        "output_sha256": sha256(OUTPUT),
        "rejected": [
            {
                "canonical_id": row["canonical_id"],
                "reason": title_abstract_metadata_issue(row)[0],
            }
            for row in rejected
        ],
        "replacement_ids": [row["canonical_id"] for row in replacements],
        "sealed_holdout_accessed": False,
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
