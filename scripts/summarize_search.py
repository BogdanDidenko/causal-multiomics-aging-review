#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the frozen search and PRISMA identification summary"
    )
    parser.add_argument("--search-dir", required=True, type=Path)
    parser.add_argument("--canonical", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    run_manifest = json.loads(
        (args.search_dir / "search_run_manifest.json").read_text(encoding="utf-8")
    )
    canonical = read_csv(args.canonical)
    source_manifests = run_manifest["source_manifests"]
    automated_sources = sorted(
        source
        for source, manifest in source_manifests.items()
        if manifest.get("source_details", {}).get("mode") != "manual_browser_export"
    )
    manual_sources = sorted(set(source_manifests) - set(automated_sources))
    total = int(run_manifest["total_source_records"])
    unique = len(canonical)
    duplicate_instances = total - unique
    local_unique = sum(
        row.get("local_three_block_match", "").lower() == "true" for row in canonical
    )
    missing_abstract = sum(not row.get("abstract", "").strip() for row in canonical)
    oversized_abstract = sum(len(row.get("abstract", "")) > 5000 for row in canonical)
    provenance_cardinality = Counter(
        len(row.get("provenance_sources", "").split(";")) for row in canonical
    )
    anchor = next(
        (
            row
            for row in canonical
            if row.get("doi") == "10.1038/s41467-023-37729-w"
        ),
        None,
    )
    if anchor is None:
        raise ValueError("Canonical positive missing after deduplication")

    summary = {
        "schema_version": "1.0.0",
        "created_at": datetime.now(UTC).isoformat(),
        "search_date": "2026-07-27",
        "automated_database_records": sum(
            source_manifests[source]["retrieved_count"] for source in automated_sources
        ),
        "manual_supplementary_records": sum(
            source_manifests[source]["retrieved_count"] for source in manual_sources
        ),
        "total_records_identified": total,
        "duplicate_instances_removed": duplicate_instances,
        "unique_records_for_title_abstract_screening": unique,
        "unique_records_with_local_three_block_signal": local_unique,
        "unique_records_missing_abstract": missing_abstract,
        "unique_records_with_oversized_abstract_metadata": oversized_abstract,
        "screening_status": "pending",
        "source_counts": {
            source: {
                "reported": source_manifests[source]["reported_count"],
                "retrieved": source_manifests[source]["retrieved_count"],
                "local_three_block": source_manifests[source][
                    "local_three_block_count"
                ],
                "canonical_positive_found": source_manifests[source][
                    "canonical_positive_found"
                ],
            }
            for source in sorted(source_manifests)
        },
        "provenance_source_count_distribution": {
            str(count): records for count, records in sorted(provenance_cardinality.items())
        },
        "canonical_positive": {
            "doi": anchor["doi"],
            "title": anchor["title"],
            "provenance_sources": anchor["provenance_sources"].split(";"),
        },
        "notes": [
            "Local three-block matching is metadata QA, not an eligibility decision.",
            (
                "Google Scholar's reported count is approximate; all 18 accessible "
                "result pages were frozen."
            ),
            (
                "Scopus STANDARD-view records lack abstracts under the available API "
                "entitlement; deduplication backfills abstracts when another source "
                "provides one."
            ),
            (
                "Records without abstracts route to metadata enrichment or manual "
                "review and are not silently discarded."
            ),
            (
                "Source records with abstract metadata over 5,000 characters route "
                "to metadata enrichment or manual review to prevent full-text leakage "
                "into title/abstract screening."
            ),
        ],
    }
    prisma_path = args.search_dir / "prisma_identification.json"
    prisma_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Search Execution: 2026-07-27",
        "",
        "## Frozen identification counts",
        "",
        "| Source | Reported | Retrieved | Local three-block QA | Canonical positive |",
        "|---|---:|---:|---:|:---:|",
    ]
    for source, values in summary["source_counts"].items():
        reported = values["reported"]
        lines.append(
            f"| {source} | {reported:,} | {values['retrieved']:,} | "
            f"{values['local_three_block']:,} | "
            f"{'yes' if values['canonical_positive_found'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## PRISMA identification",
            "",
            f"- Automated database/API records: **{summary['automated_database_records']:,}**.",
            (
                "- Manual supplementary Google Scholar records: "
                f"**{summary['manual_supplementary_records']:,}**."
            ),
            f"- Total source records: **{total:,}**.",
            f"- Duplicate instances removed: **{duplicate_instances:,}**.",
            f"- Unique records entering title/abstract screening: **{unique:,}**.",
            (
                f"- Unique records without an abstract: **{missing_abstract:,}**; "
                "these route to metadata enrichment or manual review."
            ),
            (
                "- Unique records with oversized abstract metadata: "
                f"**{oversized_abstract:,}**; these also route to enrichment or "
                "manual review."
            ),
            "",
            (
                "The local three-block count is a retrieval-quality diagnostic only. "
                "It does not remove records and is not a PRISMA inclusion count."
            ),
            "",
            "## Calibration control",
            "",
            (
                "DOI `10.1038/s41467-023-37729-w` was retrieved by all seven sources "
                "and merged into one canonical record."
            ),
            "",
            "## Source limitations",
            "",
            (
                "- Google Scholar has no official search API. Its `About 180` count is "
                "approximate; 180 displayed records across 18 pages were frozen "
                "through a manual browser session."
            ),
            (
                "- The available Scopus API key permits `STANDARD`, not `COMPLETE`, "
                "view. Scopus abstracts are therefore absent and are backfilled only "
                "when another source supplies them."
            ),
            (
                "- Springer Nature Meta searches full text, so its raw pool is broader "
                "than title/abstract databases. Proximity constraints and local QA "
                "fields are preserved for audit."
            ),
            (
                "- Semantic Scholar intermittently returned HTTP 500 for long Boolean "
                "expressions. The frozen compact three-concept query retained the "
                "canonical positive."
            ),
            "",
            (
                "Title/abstract screening, full-text retrieval, eligibility, and "
                "synthesis counts remain pending and must be appended without "
                "rewriting this identification snapshot."
            ),
            "",
        ]
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"identified={total} duplicates={duplicate_instances} "
        f"screening={unique} missing_abstract={missing_abstract} "
        f"oversized_abstract={oversized_abstract}"
    )


if __name__ == "__main__":
    main()
