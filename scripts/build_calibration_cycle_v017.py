#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from causal_multiomics_aging_review.audit import sha256_file
from causal_multiomics_aging_review.metadata_quality import (
    title_abstract_metadata_issue,
)

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "protocol" / "screening" / "benchmarks"
VISIBLE_DEVELOPMENT = (
    BENCHMARKS / "title_abstract_boundary_pilot_v0.3.0_25.csv"
)
ACCESSED_HOLDOUT_V3 = BENCHMARKS / "title_abstract_stability_holdout_25.csv"
UNINSPECTED_REGRESSION = BENCHMARKS / "title_abstract_regression_116.csv"

DEVELOPMENT_OUTPUT = BENCHMARKS / "title_abstract_calibration_v0.17.0_50.csv"
SEALED_HOLDOUT_OUTPUT = BENCHMARKS / "title_abstract_stability_holdout_v4_25.csv"
REGRESSION_REMAINDER_OUTPUT = (
    BENCHMARKS / "title_abstract_regression_v0.17.0_remaining_91.csv"
)
MANIFEST_OUTPUT = BENCHMARKS / "calibration_cycle_v0.17.0_manifest.json"
SEED = "causal-multiomics-aging-title-v0.17.0-holdout-v4"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_rows(
    path: Path,
    rows: list[dict[str, str]],
    fieldnames: list[str],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_key(identifier: str, salt: str) -> str:
    return hashlib.sha256(f"{SEED}|{salt}|{identifier}".encode()).hexdigest()


def diverse_sealed_sample(
    rows: list[dict[str, str]],
    count: int,
) -> list[dict[str, str]]:
    eligible = [
        row for row in rows if title_abstract_metadata_issue(row) is None
    ]
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in eligible:
        buckets[row["sampling_stratum"]].append(row)
    for stratum, bucket in buckets.items():
        bucket.sort(
            key=lambda row: stable_key(row["canonical_id"], stratum)
        )

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
        raise RuntimeError(f"Expected {count} holdout records, found {len(selected)}")
    return selected


def stratum_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["sampling_stratum"]] += 1
    return dict(sorted(counts.items()))


def main() -> None:
    visible_rows = read_rows(VISIBLE_DEVELOPMENT)
    accessed_rows = read_rows(ACCESSED_HOLDOUT_V3)
    regression_rows = read_rows(UNINSPECTED_REGRESSION)
    fieldnames = list(regression_rows[0])

    development_by_id = {
        row["canonical_id"]: row for row in visible_rows + accessed_rows
    }
    if len(development_by_id) != 50:
        raise RuntimeError("Development sources are not disjoint 25-record sets")
    development = sorted(
        development_by_id.values(),
        key=lambda row: row["canonical_id"],
    )

    holdout = diverse_sealed_sample(regression_rows, 25)
    holdout_ids = {row["canonical_id"] for row in holdout}
    remainder = [
        row for row in regression_rows if row["canonical_id"] not in holdout_ids
    ]
    if len(remainder) != 91:
        raise RuntimeError("Regression split must contain 25 holdout and 91 remainder")

    write_rows(DEVELOPMENT_OUTPUT, development, fieldnames)
    write_rows(SEALED_HOLDOUT_OUTPUT, holdout, fieldnames)
    write_rows(REGRESSION_REMAINDER_OUTPUT, remainder, fieldnames)

    manifest = {
        "calibration_cycle": "title_abstract_v0.17.0",
        "created_date": "2026-07-27",
        "seed": SEED,
        "development": {
            "status": "visible",
            "record_count": len(development),
            "sources": [
                {
                    "path": str(VISIBLE_DEVELOPMENT.relative_to(ROOT)),
                    "sha256": sha256_file(VISIBLE_DEVELOPMENT),
                    "status": "visible_development",
                },
                {
                    "path": str(ACCESSED_HOLDOUT_V3.relative_to(ROOT)),
                    "sha256": sha256_file(ACCESSED_HOLDOUT_V3),
                    "status": "failed_holdout_v3_now_development_only",
                },
            ],
            "output_path": str(DEVELOPMENT_OUTPUT.relative_to(ROOT)),
            "output_sha256": sha256_file(DEVELOPMENT_OUTPUT),
            "strata": stratum_counts(development),
        },
        "sealed_holdout_v4": {
            "status": "sealed_uninspected",
            "record_count": len(holdout),
            "source_path": str(UNINSPECTED_REGRESSION.relative_to(ROOT)),
            "source_sha256": sha256_file(UNINSPECTED_REGRESSION),
            "selection_policy": (
                "Deterministic round-robin across existing sampling strata after "
                "machine-only metadata-quality filtering; record content was not "
                "printed or manually inspected."
            ),
            "output_path": str(SEALED_HOLDOUT_OUTPUT.relative_to(ROOT)),
            "output_sha256": sha256_file(SEALED_HOLDOUT_OUTPUT),
            "strata": stratum_counts(holdout),
        },
        "regression_remainder": {
            "status": "uninspected",
            "record_count": len(remainder),
            "output_path": str(REGRESSION_REMAINDER_OUTPUT.relative_to(ROOT)),
            "output_sha256": sha256_file(REGRESSION_REMAINDER_OUTPUT),
        },
        "disjoint": {
            "development_vs_holdout_v4": not (
                set(development_by_id) & holdout_ids
            ),
            "holdout_v4_vs_regression_remainder": not (
                holdout_ids
                & {row["canonical_id"] for row in remainder}
            ),
        },
    }
    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "calibration_cycle_ready "
        f"development={len(development)} "
        f"sealed_holdout={len(holdout)} "
        f"regression_remainder={len(remainder)}"
    )


if __name__ == "__main__":
    main()
