#!/usr/bin/env python3
"""Freeze the effective 20k-rerun seek-full-text cohort."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl_tree(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result_path in sorted(path.glob("shard_*/screening_results.jsonl")):
        with result_path.open(encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("Refusing to write an empty CSV")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("screening_input", type=Path)
    parser.add_argument("primary_rerun", type=Path)
    parser.add_argument("role_retry", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--resolutions", type=Path, required=True)
    parser.add_argument("--existing-targets", type=Path)
    parser.add_argument("--expected", type=int, default=66)
    parser.add_argument("--expected-unique", type=int, default=65)
    args = parser.parse_args()

    source_rows = read_csv(args.screening_input)
    source_by_id = {row["record_id"]: row for row in source_rows}
    results = read_jsonl_tree(args.primary_rerun)
    result_by_id = {str(row["record_id"]): row for row in results}
    retry = read_jsonl_tree(args.role_retry)
    for row in retry:
        result_by_id[str(row["record_id"])] = row

    selected_results = [
        row
        for row in result_by_id.values()
        if row.get("final_decision") == "seek_full_text"
        and row.get("decision_reason") != "oversized_abstract_metadata"
    ]
    if len(selected_results) != args.expected:
        raise SystemExit(
            f"Expected {args.expected} effective seek-full-text records, "
            f"found {len(selected_results)}"
        )

    resolutions = {row["record_id"]: row for row in read_csv(args.resolutions)}
    cohort: list[dict[str, str]] = []
    triage: list[dict[str, str]] = []
    resolution_audit: list[dict[str, str]] = []
    for result in sorted(selected_results, key=lambda row: str(row["record_id"])):
        identifier = str(result["record_id"])
        source = dict(source_by_id[identifier])
        original_doi = source.get("doi", "").strip().casefold()
        resolution = resolutions.get(identifier)
        resolved_doi = resolution.get("resolved_doi", "").strip().casefold() if resolution else ""
        if original_doi and resolved_doi and original_doi != resolved_doi:
            raise SystemExit(f"Resolution conflicts with source DOI: {identifier}")
        source["original_doi"] = original_doi
        source["doi"] = original_doi or resolved_doi
        source["doi_resolution_basis"] = resolution.get("basis", "") if resolution else ""
        source["doi_resolution_evidence"] = resolution.get("evidence_url", "") if resolution else ""
        cohort.append(source)

        roles = result.get("role_runs") or {}
        causal_runs = roles.get("causal_method_reviewer") or []
        families = causal_runs[0].get("design_families", []) if causal_runs else []
        triage.append(
            {
                "record_id": identifier,
                "doi": source["doi"],
                "title": source.get("title", ""),
                "source": source.get("source", ""),
                "year": source.get("year", ""),
                "design_anchor": str(families[0]) if families else "not_assessed",
                "manual_triage_queue": "oversized_20k_seek_full_text_followup",
                "title_abstract_reason": str(result.get("decision_reason", "")),
            }
        )
        if resolution:
            resolution_audit.append(
                {
                    "record_id": identifier,
                    "original_doi": original_doi,
                    **resolution,
                }
            )

    deduplicated_cohort: list[dict[str, str]] = []
    deduplicated_triage: list[dict[str, str]] = []
    position_by_key: dict[str, int] = {}
    duplicate_aliases: list[dict[str, str]] = []
    for source, route in zip(cohort, triage, strict=True):
        key = source["doi"] or source["record_id"]
        if key not in position_by_key:
            position_by_key[key] = len(deduplicated_cohort)
            source["duplicate_record_ids"] = ""
            deduplicated_cohort.append(source)
            deduplicated_triage.append(route)
            continue
        position = position_by_key[key]
        existing = deduplicated_cohort[position]
        existing_route = deduplicated_triage[position]
        prefer_source = bool(source.get("original_doi")) and not bool(existing.get("original_doi"))
        kept = source if prefer_source else existing
        kept_route = route if prefer_source else existing_route
        alias = existing if prefer_source else source
        kept["duplicate_record_ids"] = ";".join(
            value for value in (kept.get("duplicate_record_ids", ""), alias["record_id"]) if value
        )
        deduplicated_cohort[position] = kept
        deduplicated_triage[position] = kept_route
        duplicate_aliases.append(
            {
                "normalized_identifier": key,
                "kept_record_id": kept["record_id"],
                "collapsed_record_id": alias["record_id"],
                "basis": "resolved DOI identity",
            }
        )

    cohort = deduplicated_cohort
    triage = deduplicated_triage
    if len(cohort) != args.expected_unique:
        raise SystemExit(f"Expected {args.expected_unique} unique reports, found {len(cohort)}")
    dois = [row["doi"] for row in cohort if row["doi"]]
    record_ids = [row["record_id"] for row in cohort]
    if len(dois) != len(set(dois)):
        raise SystemExit("Duplicate normalized DOI in cohort")
    if len(record_ids) != len(set(record_ids)):
        raise SystemExit("Duplicate record ID in cohort")
    existing_dois: set[str] = set()
    if args.existing_targets:
        existing_dois = {
            row["doi"].strip().casefold()
            for row in read_csv(args.existing_targets)
            if row.get("doi")
        }
    overlap = sorted(set(dois) & existing_dois)
    if overlap:
        raise SystemExit(f"Cohort overlaps existing full-text targets: {overlap[:5]}")

    output = args.output_dir
    cohort_path = output / "cohort.csv"
    triage_path = output / "triage.csv"
    resolution_path = output / "identifier_resolution_audit.csv"
    duplicate_path = output / "duplicate_resolution_audit.csv"
    write_csv(cohort_path, cohort)
    write_csv(triage_path, triage)
    if resolution_audit:
        write_csv(resolution_path, resolution_audit)
    if duplicate_aliases:
        write_csv(duplicate_path, duplicate_aliases)
    manifest = {
        "status": "frozen_full_text_followup_cohort",
        "selection_rule": (
            "effective 20,000-character title/abstract rerun route is seek_full_text, "
            "excluding records still routed solely as oversized metadata"
        ),
        "input_records": len(selected_results),
        "records": len(cohort),
        "duplicate_records_collapsed": len(duplicate_aliases),
        "records_with_doi": len(dois),
        "unique_normalized_doi": len(set(dois)),
        "records_without_doi": len(cohort) - len(dois),
        "unique_record_ids": len(set(record_ids)),
        "preprints_included": sum(row.get("is_preprint") == "True" for row in cohort),
        "reason_counts": dict(
            sorted(Counter(row["title_abstract_reason"] for row in triage).items())
        ),
        "overlap_with_existing_119_dois": len(overlap),
        "artifacts": {
            "cohort": {"path": str(cohort_path), "sha256": sha256(cohort_path)},
            "triage": {"path": str(triage_path), "sha256": sha256(triage_path)},
            "identifier_resolution_audit": {
                "path": str(resolution_path),
                "sha256": sha256(resolution_path),
            },
            "duplicate_resolution_audit": {
                "path": str(duplicate_path),
                "sha256": sha256(duplicate_path),
            },
            "source_screening_input": {
                "path": str(args.screening_input),
                "sha256": sha256(args.screening_input),
            },
            "resolution_source": {
                "path": str(args.resolutions),
                "sha256": sha256(args.resolutions),
            },
        },
    }
    manifest_path = output / "cohort_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
