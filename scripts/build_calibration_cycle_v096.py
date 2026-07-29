#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from build_screening_benchmarks import (
    diverse_sample,
    prepare_rows,
    stratum_counts,
    write_csv,
)

from causal_multiomics_aging_review.metadata_quality import (
    title_abstract_metadata_issue,
)

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "protocol" / "screening" / "benchmarks"
SOURCE = ROOT / "data" / "normalized" / "canonical.csv"
DEVELOPMENT = BENCHMARKS / "title_abstract_calibration_v0.96.0_50.csv"
HOLDOUT = BENCHMARKS / "title_abstract_stability_holdout_v8_v0.96.0_25.csv"
MANIFEST = BENCHMARKS / "calibration_cycle_v0.96.0_manifest.json"
SEED = "causal-multiomics-aging|independent-cycle-v0.96.0"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def id_set_sha256(values: set[str]) -> str:
    payload = "\n".join(sorted(values)).encode()
    return hashlib.sha256(payload).hexdigest()


def benchmark_exclusions() -> tuple[set[str], list[dict[str, Any]]]:
    excluded: set[str] = set()
    metadata: list[dict[str, Any]] = []
    outputs = {DEVELOPMENT.resolve(), HOLDOUT.resolve()}
    for path in sorted(BENCHMARKS.glob("*.csv")):
        if path.resolve() in outputs:
            continue
        rows = read_csv(path)
        ids = {
            row.get("canonical_id", "").strip()
            for row in rows
            if row.get("canonical_id", "").strip()
        }
        excluded.update(ids)
        metadata.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "record_count": len(rows),
                "canonical_id_count": len(ids),
            }
        )
    return excluded, metadata


def prior_screening_exclusions() -> tuple[set[str], dict[str, Any]]:
    excluded: set[str] = set()
    paths = sorted(
        (ROOT / "data" / "screening" / "stability").glob(
            "**/screening_results.jsonl"
        )
    )
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                record_id = str(record.get("record_id", "")).strip()
                if record_id:
                    excluded.add(record_id)
    return excluded, {
        "file_count": len(paths),
        "distinct_canonical_id_count": len(excluded),
        "canonical_ids_sha256": id_set_sha256(excluded),
    }


def ids(rows: list[dict[str, str]]) -> set[str]:
    return {row["canonical_id"] for row in rows}


def main() -> None:
    source_rows = read_csv(SOURCE)
    prepared_rows = [
        row
        for row in prepare_rows(source_rows)
        if title_abstract_metadata_issue(row) is None
    ]
    benchmark_ids, benchmark_metadata = benchmark_exclusions()
    screening_ids, screening_metadata = prior_screening_exclusions()
    excluded_ids = benchmark_ids | screening_ids

    holdout_rows = diverse_sample(
        prepared_rows,
        25,
        f"{SEED}|sealed-v8",
        excluded_ids,
    )
    holdout_ids = ids(holdout_rows)
    development_rows = diverse_sample(
        prepared_rows,
        50,
        f"{SEED}|development",
        excluded_ids | holdout_ids,
    )
    development_ids = ids(development_rows)

    if holdout_ids & development_ids:
        raise ValueError("Development and sealed v8 sets overlap")
    if (holdout_ids | development_ids) & excluded_ids:
        raise ValueError("New cycle overlaps prior benchmark or screening records")

    holdout_rows.sort(key=lambda row: row["canonical_id"])
    development_rows.sort(key=lambda row: row["canonical_id"])
    write_csv(HOLDOUT, holdout_rows)
    write_csv(DEVELOPMENT, development_rows)

    eligible_unseen_count = sum(
        row["canonical_id"] not in excluded_ids for row in prepared_rows
    )
    manifest = {
        "cycle_version": "0.96.0",
        "created_date": date.today().isoformat(),
        "selection_seed": SEED,
        "selection_method": (
            "stratum_round_robin_then_ascending_sha256_of_seed_and_canonical_id"
        ),
        "source": {
            "path": str(SOURCE.relative_to(ROOT)),
            "sha256": sha256(SOURCE),
            "source_record_count": len(source_rows),
            "eligible_title_abstract_count": len(prepared_rows),
            "eligible_unseen_count_before_split": eligible_unseen_count,
        },
        "exclusions": {
            "policy": (
                "exclude every canonical_id present in any prior benchmark CSV "
                "or prior stability screening result"
            ),
            "benchmark_files": benchmark_metadata,
            "benchmark_distinct_canonical_id_count": len(benchmark_ids),
            "benchmark_canonical_ids_sha256": id_set_sha256(benchmark_ids),
            "prior_screening_results": screening_metadata,
            "combined_distinct_canonical_id_count": len(excluded_ids),
            "combined_canonical_ids_sha256": id_set_sha256(excluded_ids),
        },
        "development_set": {
            "path": str(DEVELOPMENT.relative_to(ROOT)),
            "sha256": sha256(DEVELOPMENT),
            "record_count": len(development_rows),
            "status": "visible_after_split_freeze",
            "strata": stratum_counts(development_rows),
        },
        "sealed_holdout": {
            "path": str(HOLDOUT.relative_to(ROOT)),
            "sha256": sha256(HOLDOUT),
            "record_count": len(holdout_rows),
            "status": "sealed_do_not_inspect_before_candidate_freeze",
            "strata": stratum_counts(holdout_rows),
        },
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "cycle_v0.96.0 "
        f"source={len(source_rows)} eligible={len(prepared_rows)} "
        f"excluded={len(excluded_ids)} unseen={eligible_unseen_count} "
        f"development={len(development_rows)} sealed={len(holdout_rows)}"
    )


if __name__ == "__main__":
    main()
