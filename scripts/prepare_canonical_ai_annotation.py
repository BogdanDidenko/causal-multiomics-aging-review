#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

INPUT_FIELDS = (
    "record_id",
    "source",
    "title",
    "abstract",
    "year",
    "document_type",
    "doi",
    "proposed_design_family",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare complete title/abstract records for preliminary AI review"
    )
    parser.add_argument("candidate_pool", type=Path)
    parser.add_argument("search_records", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--shards", type=int, default=12)
    args = parser.parse_args()

    if args.shards < 1:
        raise SystemExit("--shards must be positive")
    candidates = read_csv(args.candidate_pool)
    source_rows = read_csv(args.search_records)
    by_doi: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_title: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        if doi := row.get("doi", "").strip().casefold():
            by_doi[doi].append(row)
        by_title[normalized_title(row.get("title", ""))].append(row)

    records = []
    for candidate in candidates:
        doi = candidate.get("doi", "").strip().casefold()
        occurrences = by_doi.get(doi, []) if doi else []
        if not occurrences:
            occurrences = by_title.get(normalized_title(candidate["title"]), [])
        if not occurrences:
            raise SystemExit(f"No source record for {candidate['candidate_id']}")
        source = max(occurrences, key=lambda row: len(row.get("abstract", "")))
        if not source.get("abstract", "").strip():
            raise SystemExit(f"Missing abstract for {candidate['candidate_id']}")
        records.append(
            {
                "record_id": candidate["candidate_id"],
                "source": source.get("source", ""),
                "title": source.get("title", "") or candidate["title"],
                "abstract": source["abstract"],
                "year": source.get("year", "") or candidate.get("year", ""),
                "document_type": source.get("document_type", ""),
                "doi": candidate.get("doi", ""),
                "proposed_design_family": candidate.get(
                    "proposed_design_family", ""
                ),
            }
        )

    records.sort(key=lambda row: row["record_id"])
    input_path = args.output_dir / "input.csv"
    write_csv(input_path, records)
    shard_paths = []
    for index in range(args.shards):
        shard = records[index :: args.shards]
        if not shard:
            continue
        path = args.output_dir / "shards" / f"shard_{index + 1:02d}.csv"
        write_csv(path, shard)
        shard_paths.append(path)

    manifest = {
        "status": "prepared_for_ai_preliminary_annotation",
        "candidate_pool": {
            "path": str(args.candidate_pool),
            "sha256": sha256(args.candidate_pool),
            "records": len(candidates),
        },
        "search_records": {
            "path": str(args.search_records),
            "sha256": sha256(args.search_records),
            "records": len(source_rows),
        },
        "input": {
            "path": str(input_path),
            "sha256": sha256(input_path),
            "records": len(records),
        },
        "shards": [
            {
                "path": str(path),
                "sha256": sha256(path),
                "records": len(read_csv(path)),
            }
            for path in shard_paths
        ],
        "gold_standard": False,
        "interpretation": (
            "These records are inputs to repeated model screening. Model outputs "
            "must not be represented as independent expert or gold labels."
        ),
    }
    (args.output_dir / "input_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"prepared={len(records)} shards={len(shard_paths)}")


if __name__ == "__main__":
    main()
