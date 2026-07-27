#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from causal_multiomics_aging_review.audit import sha256_file

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "protocol" / "screening" / "benchmarks"
CANONICAL = ROOT / "data" / "normalized" / "canonical.csv"

INPUTS = {
    "development": BENCHMARKS / "title_abstract_calibration_v0.17.0_50.csv",
    "sealed_holdout_v4": (
        BENCHMARKS / "title_abstract_stability_holdout_v4_25.csv"
    ),
    "regression_remainder": (
        BENCHMARKS / "title_abstract_regression_v0.17.0_remaining_91.csv"
    ),
}
OUTPUTS = {
    "development": BENCHMARKS / "title_abstract_calibration_v0.24.0_50.csv",
    "sealed_holdout_v4": (
        BENCHMARKS / "title_abstract_stability_holdout_v4_metadata_v0.24.0_25.csv"
    ),
    "regression_remainder": (
        BENCHMARKS / "title_abstract_regression_v0.24.0_remaining_91.csv"
    ),
}
MANIFEST = BENCHMARKS / "calibration_cycle_v0.24.0_manifest.json"
METADATA_FIELDS = ("document_type",)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def canonical_id(row: dict[str, str]) -> str:
    doi = row.get("doi", "").strip().lower()
    if doi:
        return f"doi:{doi}"
    pmid = row.get("pmid", "").strip()
    if pmid:
        return f"pmid:{pmid}"
    if identifier := row.get("canonical_id", "").strip():
        return identifier
    title = " ".join(row.get("title", "").split()).casefold()
    year = row.get("year", "").strip()
    if not title:
        return ""
    digest = hashlib.sha256(f"{title}|{year}".encode()).hexdigest()[:20]
    return f"title-year-sha256:{digest}"


def metadata_index() -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for row in read_rows(CANONICAL):
        identifier = canonical_id(row)
        if identifier:
            index[identifier] = {
                field: row.get(field, "").strip() for field in METADATA_FIELDS
            }
    return index


def enrich(
    source: Path,
    output: Path,
    metadata: dict[str, dict[str, str]],
) -> int:
    rows = read_rows(source)
    if not rows:
        raise RuntimeError(f"No records in {source}")
    fieldnames = list(rows[0])
    for field in METADATA_FIELDS:
        if field not in fieldnames:
            insert_at = fieldnames.index("provenance_sources") + 1
            fieldnames.insert(insert_at, field)
    missing = []
    for row in rows:
        identifier = row["canonical_id"].strip()
        values = metadata.get(identifier)
        if values is None:
            missing.append(identifier)
            values = {field: "" for field in METADATA_FIELDS}
        row.update(values)
    if missing:
        raise RuntimeError(
            f"Missing canonical metadata for {len(missing)} records"
        )
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    metadata = metadata_index()
    counts = {
        name: enrich(INPUTS[name], OUTPUTS[name], metadata) for name in INPUTS
    }
    manifest = {
        "calibration_cycle": "title_abstract_v0.24.0",
        "created_date": "2026-07-27",
        "operation": "machine_only_document_type_enrichment",
        "metadata_fields": list(METADATA_FIELDS),
        "canonical_source": {
            "path": str(CANONICAL.relative_to(ROOT)),
            "sha256": sha256_file(CANONICAL),
        },
        "sets": {
            name: {
                "status": (
                    "sealed_uninspected_machine_enriched"
                    if name == "sealed_holdout_v4"
                    else "visible_development"
                    if name == "development"
                    else "uninspected"
                ),
                "record_count": counts[name],
                "input_path": str(INPUTS[name].relative_to(ROOT)),
                "input_sha256": sha256_file(INPUTS[name]),
                "output_path": str(OUTPUTS[name].relative_to(ROOT)),
                "output_sha256": sha256_file(OUTPUTS[name]),
            }
            for name in INPUTS
        },
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "metadata_enrichment_ready "
        f"development={counts['development']} "
        f"sealed_holdout={counts['sealed_holdout_v4']} "
        f"regression_remainder={counts['regression_remainder']}"
    )


if __name__ == "__main__":
    main()
