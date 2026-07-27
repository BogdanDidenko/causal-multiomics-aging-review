#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from causal_multiomics_aging_review.metadata_quality import (
    title_abstract_metadata_issue,
)

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "protocol" / "screening" / "benchmarks"
SOURCE = BENCHMARKS / "title_abstract_regression_v0.24.0_remaining_91.csv"
VISIBLE = BENCHMARKS / "title_abstract_calibration_v0.24.0_50.csv"
FAILED_HOLDOUT = (
    BENCHMARKS
    / "title_abstract_stability_holdout_v4_metadata_v0.24.0_25.csv"
)
HOLDOUT = BENCHMARKS / "title_abstract_stability_holdout_v5_v0.41.0_25.csv"
REMAINDER = BENCHMARKS / "title_abstract_regression_v0.41.0_remaining_66.csv"
MANIFEST = BENCHMARKS / "calibration_cycle_v0.41.0_manifest.json"
SEED = "causal-multiomics-aging|sealed-holdout-v5|v0.41.0"


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {path}")
        return list(reader.fieldnames), list(reader)


def write_rows(
    path: Path, fieldnames: list[str], rows: list[dict[str, str]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def ids(rows: list[dict[str, str]]) -> set[str]:
    return {row["canonical_id"] for row in rows}


def stable_key(row: dict[str, str], stratum: str) -> str:
    value = f"{SEED}|{stratum}|{row['canonical_id']}".encode()
    return hashlib.sha256(value).hexdigest()


def diverse_sealed_sample(
    rows: list[dict[str, str]], count: int
) -> list[dict[str, str]]:
    eligible = [
        row for row in rows if title_abstract_metadata_issue(row) is None
    ]
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in eligible:
        buckets[row["sampling_stratum"]].append(row)
    for stratum, bucket in buckets.items():
        bucket.sort(key=lambda row: stable_key(row, stratum))

    selected: list[dict[str, str]] = []
    active = sorted(buckets)
    while active and len(selected) < count:
        next_active: list[str] = []
        for stratum in active:
            if buckets[stratum] and len(selected) < count:
                selected.append(buckets[stratum].pop(0))
            if buckets[stratum]:
                next_active.append(stratum)
        active = next_active
    if len(selected) != count:
        raise ValueError(f"Expected {count} holdout records, found {len(selected)}")
    return selected


def stratum_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["sampling_stratum"]] += 1
    return dict(sorted(counts.items()))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    fieldnames, source_rows = read_rows(SOURCE)
    _, visible_rows = read_rows(VISIBLE)
    _, failed_rows = read_rows(FAILED_HOLDOUT)
    visible_ids = ids(visible_rows)
    failed_ids = ids(failed_rows)
    source_ids = ids(source_rows)
    if visible_ids & source_ids:
        raise ValueError("Regression source overlaps visible development set")
    if failed_ids & source_ids:
        raise ValueError("Regression source overlaps failed holdout v4")

    holdout_rows = sorted(
        diverse_sealed_sample(source_rows, 25),
        key=lambda row: row["canonical_id"],
    )
    holdout_ids = ids(holdout_rows)
    remainder_rows = sorted(
        [
            row
            for row in source_rows
            if row["canonical_id"] not in holdout_ids
        ],
        key=lambda row: row["canonical_id"],
    )
    if len(remainder_rows) != 66:
        raise ValueError(
            f"Expected 66 untouched remainder records, found {len(remainder_rows)}"
        )
    if ids(holdout_rows) & (visible_ids | failed_ids):
        raise ValueError("New holdout overlaps an accessed set")
    if ids(holdout_rows) & ids(remainder_rows):
        raise ValueError("New holdout overlaps the untouched remainder")

    write_rows(HOLDOUT, fieldnames, holdout_rows)
    write_rows(REMAINDER, fieldnames, remainder_rows)
    manifest = {
        "cycle_version": "0.41.0",
        "created_date": date.today().isoformat(),
        "selection_seed": SEED,
        "selection_method": "ascending_sha256_of_seed_and_canonical_id",
        "source": {
            "path": str(SOURCE.relative_to(ROOT)),
            "sha256": sha256(SOURCE),
            "record_count": len(source_rows),
        },
        "excluded_accessed_sets": [
            {
                "path": str(VISIBLE.relative_to(ROOT)),
                "sha256": sha256(VISIBLE),
                "record_count": len(visible_rows),
            },
            {
                "path": str(FAILED_HOLDOUT.relative_to(ROOT)),
                "sha256": sha256(FAILED_HOLDOUT),
                "record_count": len(failed_rows),
            },
        ],
        "sealed_holdout": {
            "path": str(HOLDOUT.relative_to(ROOT)),
            "sha256": sha256(HOLDOUT),
            "record_count": len(holdout_rows),
            "status": "sealed_do_not_inspect_before_candidate_freeze",
            "strata": stratum_counts(holdout_rows),
        },
        "untouched_remainder": {
            "path": str(REMAINDER.relative_to(ROOT)),
            "sha256": sha256(REMAINDER),
            "record_count": len(remainder_rows),
        },
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "cycle_v0.41.0 "
        f"source={len(source_rows)} prior_holdout_disjoint={len(failed_rows)} "
        f"sealed={len(holdout_rows)} remainder={len(remainder_rows)}"
    )


if __name__ == "__main__":
    main()
