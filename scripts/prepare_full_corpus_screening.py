#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from causal_multiomics_aging_review.deduplication import (
    normalize_doi,
    normalize_title,
)

FIELDS = (
    "record_id",
    "canonical_id",
    "source",
    "provenance_sources",
    "source_record_id",
    "doi",
    "pmid",
    "pmcid",
    "title",
    "abstract",
    "year",
    "publication_date",
    "document_type",
    "language",
    "url",
    "is_preprint",
    "duplicate_count",
    "query_branches",
    "local_multiomics_match",
    "local_aging_match",
    "local_causal_anchor_match",
    "local_three_block_match",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fallback_id(row: dict[str, str]) -> str:
    identity = "|".join(
        (
            row.get("source", ""),
            row.get("source_record_id", ""),
            normalize_title(row.get("title")),
            row.get("year", "").strip(),
        )
    )
    return "no-doi:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def prepare_record(row: dict[str, str]) -> dict[str, str]:
    doi = normalize_doi(row.get("doi"))
    identifier = f"doi:{doi}" if doi else fallback_id(row)
    prepared = {field: row.get(field, "") for field in FIELDS}
    prepared["record_id"] = identifier
    prepared["canonical_id"] = identifier
    prepared["doi"] = doi
    return prepared


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare DOI-unique deduplicated abstracts for full-corpus screening"
    )
    parser.add_argument("canonical", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--shards", type=int, default=24)
    args = parser.parse_args()
    if args.shards < 1:
        raise SystemExit("--shards must be positive")
    if args.output_dir.exists():
        raise SystemExit(f"Refusing to overwrite: {args.output_dir}")

    source_rows = read_csv(args.canonical)
    prepared = [prepare_record(row) for row in source_rows]
    if any(not row["title"].strip() for row in prepared):
        raise SystemExit("Canonical corpus contains a missing title")

    dois = [row["doi"] for row in prepared if row["doi"]]
    duplicate_dois = {
        doi: count for doi, count in Counter(dois).items() if count > 1
    }
    if duplicate_dois:
        raise SystemExit(f"Duplicate normalized DOI values: {len(duplicate_dois)}")
    record_ids = [row["record_id"] for row in prepared]
    if len(record_ids) != len(set(record_ids)):
        raise SystemExit("Generated record_id values are not unique")

    title_year = [
        (normalize_title(row["title"]), row["year"].strip()) for row in prepared
    ]
    duplicate_title_year = {
        key: count for key, count in Counter(title_year).items() if count > 1
    }
    if duplicate_title_year:
        raise SystemExit(
            f"Duplicate normalized title-year clusters: {len(duplicate_title_year)}"
        )

    abstract_records = sorted(
        (row for row in prepared if row["abstract"].strip()),
        key=lambda row: row["record_id"],
    )
    missing_abstract = sorted(
        (row for row in prepared if not row["abstract"].strip()),
        key=lambda row: row["record_id"],
    )
    input_path = args.output_dir / "input.csv"
    missing_path = args.output_dir / "missing_abstract.csv"
    write_csv(input_path, abstract_records)
    write_csv(missing_path, missing_abstract)

    shard_paths = []
    for index in range(args.shards):
        shard = abstract_records[index :: args.shards]
        if not shard:
            continue
        path = args.output_dir / "shards" / f"shard_{index + 1:02d}.csv"
        write_csv(path, shard)
        shard_paths.append(path)

    manifest = {
        "status": "frozen_full_corpus_screening_input",
        "canonical_source": {
            "path": str(args.canonical),
            "sha256": sha256(args.canonical),
            "records": len(source_rows),
        },
        "doi_audit": {
            "nonempty_doi_rows": len(dois),
            "unique_normalized_doi": len(set(dois)),
            "duplicate_normalized_doi": 0,
            "missing_doi_rows": len(prepared) - len(dois),
        },
        "bibliographic_audit": {
            "unique_record_ids": len(set(record_ids)),
            "duplicate_record_ids": 0,
            "duplicate_normalized_title_year": 0,
        },
        "screening_input": {
            "path": str(input_path),
            "sha256": sha256(input_path),
            "records": len(abstract_records),
        },
        "missing_abstract_queue": {
            "path": str(missing_path),
            "sha256": sha256(missing_path),
            "records": len(missing_abstract),
            "route": "metadata_enrichment_then_full_text_or_manual_review",
        },
        "shards": [
            {
                "path": str(path),
                "sha256": sha256(path),
                "records": len(read_csv(path)),
            }
            for path in shard_paths
        ],
        "model_screening_status": "not_started",
        "gold_standard": False,
    }
    (args.output_dir / "input_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"canonical={len(prepared)} abstracts={len(abstract_records)} "
        f"missing_abstract={len(missing_abstract)} doi_unique={len(set(dois))} "
        f"shards={len(shard_paths)}"
    )


if __name__ == "__main__":
    main()
