#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "protocol" / "screening" / "benchmarks"
SOURCES = (
    BENCHMARKS / "title_abstract_calibration_v0.24.0_50.csv",
    BENCHMARKS / "title_abstract_stability_holdout_v4_metadata_v0.24.0_25.csv",
    BENCHMARKS / "title_abstract_stability_holdout_v5_v0.41.0_25.csv",
)
OUTPUT = BENCHMARKS / "title_abstract_atomic_focus_v0.78.0_8.csv"
RECORD_IDS = (
    "doi:10.1038/s41380-021-01266-z",
    "doi:10.1101/2023.10.09.23296765",
    "doi:10.1186/s12967-022-03377-9",
    "doi:10.1016/j.envint.2025.109495",
    "doi:10.1038/s41698-025-01010-8",
    "doi:10.64898/2026.07.22.739782",
    "doi:10.1002/jmv.70730",
    "doi:10.1038/s42256-025-01052-4",
)


def main() -> None:
    records: dict[str, dict[str, str]] = {}
    fieldnames: list[str] | None = None
    for path in SOURCES:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if fieldnames is None:
                fieldnames = list(reader.fieldnames or [])
            for row in reader:
                identifier = row.get("canonical_id", "")
                if identifier in RECORD_IDS and identifier not in records:
                    records[identifier] = row

    missing = set(RECORD_IDS) - records.keys()
    if missing:
        raise ValueError(f"Missing focus records: {sorted(missing)}")
    if not fieldnames:
        raise ValueError("Focus source has no CSV header")

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records[identifier] for identifier in RECORD_IDS)
    print(f"wrote {OUTPUT.relative_to(ROOT)} records={len(records)}")


if __name__ == "__main__":
    main()
