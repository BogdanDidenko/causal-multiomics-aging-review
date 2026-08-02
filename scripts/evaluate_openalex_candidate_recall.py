#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import search_databases as search


def batches(values: list[str], size: int = 40) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit OpenAlex query recall against a non-gold candidate pool"
    )
    parser.add_argument("--search-config", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    config = json.loads(args.search_config.read_text(encoding="utf-8"))
    openalex = next(item for item in config["databases"] if item["id"] == "openalex")
    query_paths = {
        branch: search.PROTOCOL / path
        for branch, path in openalex["query_files"].items()
    }
    with args.candidates.open(encoding="utf-8", newline="") as handle:
        candidates = [
            row
            for row in csv.DictReader(handle)
            if row.get("assistant_final_status") in {"include", "seek_full_text"}
            and row.get("doi")
        ]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.output_dir / "raw"
    key = search.get_credential("OPENALEX_API_KEY")
    dois = [search.normalize_doi(row["doi"]) for row in candidates]
    indexed: dict[str, dict[str, Any]] = {}
    raw_paths: list[Path] = []
    for index, batch in enumerate(batches(dois), start=1):
        page = search.request_json(
            search.OPENALEX_WORKS,
            {
                "filter": "doi:" + "|".join(batch),
                "per_page": "100",
                "select": "id,doi,title,abstract_inverted_index",
                "api_key": key,
            },
        )
        path = raw_dir / "indexed" / f"batch_{index:02d}.json.gz"
        search.write_json_gzip(path, page)
        raw_paths.append(path)
        for item in page.get("results", []):
            doi = search.normalize_doi(item.get("doi"))
            if doi:
                indexed[doi] = item

    matched_branches: dict[str, set[str]] = {doi: set() for doi in dois}
    for branch, query_path in query_paths.items():
        query = query_path.read_text(encoding="utf-8").strip()
        for index, batch in enumerate(batches(dois), start=1):
            page = search.request_json(
                search.OPENALEX_WORKS,
                {
                    "filter": query + ",doi:" + "|".join(batch),
                    "per_page": "100",
                    "select": "id,doi",
                    "api_key": key,
                },
            )
            path = raw_dir / branch / f"batch_{index:02d}.json.gz"
            search.write_json_gzip(path, page)
            raw_paths.append(path)
            for item in page.get("results", []):
                doi = search.normalize_doi(item.get("doi"))
                if doi:
                    matched_branches.setdefault(doi, set()).add(branch)

    audit_rows = []
    for candidate in candidates:
        doi = search.normalize_doi(candidate["doi"])
        item = indexed.get(doi, {})
        abstract = search.reconstruct_openalex_abstract(
            item.get("abstract_inverted_index")
        )
        local = search.classify_local(
            {"title": item.get("title") or candidate["title"], "abstract": abstract}
        )
        branches = sorted(matched_branches.get(doi, set()))
        audit_rows.append(
            {
                "record_id": candidate["record_id"],
                "doi": doi,
                "title": candidate["title"],
                "assistant_final_status": candidate["assistant_final_status"],
                "assistant_primary_design_family": candidate.get(
                    "assistant_primary_design_family", ""
                ),
                "openalex_indexed": bool(item),
                "openalex_has_abstract": bool(abstract),
                "query_match": bool(branches),
                "matched_branches": ";".join(branches),
                "local_multiomics_match": local["local_multiomics_match"],
                "local_aging_match": local["local_aging_match"],
                "local_causal_anchor_match": local["local_causal_anchor_match"],
                "local_three_block_match": local["local_three_block_match"],
            }
        )

    audit_path = args.output_dir / "candidate_recall.csv"
    search.write_records_with_fields(audit_path, audit_rows)
    indexed_count = sum(row["openalex_indexed"] for row in audit_rows)
    abstract_count = sum(row["openalex_has_abstract"] for row in audit_rows)
    matched_count = sum(row["query_match"] for row in audit_rows)
    summary = {
        "protocol_version": config["protocol_version"],
        "candidate_source": str(args.candidates),
        "candidate_interpretation": (
            "Assistant-selected development candidates; not expert gold and not an "
            "accuracy denominator."
        ),
        "candidates_with_doi": len(audit_rows),
        "openalex_indexed": indexed_count,
        "openalex_has_abstract": abstract_count,
        "query_matched": matched_count,
        "query_recall_among_indexed": matched_count / indexed_count,
        "query_recall_among_records_with_openalex_abstract": (
            matched_count / abstract_count
        ),
        "query_files": {
            branch: {
                "path": str(path.relative_to(search.ROOT)),
                "sha256": search.sha256_file(path),
            }
            for branch, path in query_paths.items()
        },
        "raw_responses": [
            {
                "path": str(path.relative_to(args.output_dir)),
                "sha256": search.sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(raw_paths)
        ],
        "candidate_recall_file": str(audit_path.relative_to(args.output_dir)),
        "candidate_recall_sha256": search.sha256_file(audit_path),
        "git_revision": search.git_revision(),
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
