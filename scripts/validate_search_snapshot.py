#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected object in {path}")
    return value


def csv_rows(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify hashes and counts in a frozen or pilot search snapshot"
    )
    parser.add_argument("search_dir", type=Path)
    args = parser.parse_args()
    manifest_path = args.search_dir / "search_run_manifest.json"
    manifest = load(manifest_path)
    errors = []

    config_path = ROOT / manifest["search_config_path"]
    if sha256(config_path) != manifest.get("search_config_sha256"):
        errors.append("search config hash mismatch")
    total = 0
    for source, source_manifest in manifest.get("source_manifests", {}).items():
        normalized = args.search_dir / source_manifest["normalized_file"]
        if sha256(normalized) != source_manifest.get("normalized_sha256"):
            errors.append(f"{source}: normalized hash mismatch")
        count = csv_rows(normalized)
        total += count
        if count != source_manifest.get("retrieved_count"):
            errors.append(f"{source}: normalized count mismatch")
        for raw in source_manifest.get("raw_responses", []):
            path = args.search_dir / raw["path"]
            if not path.is_file():
                errors.append(f"{source}: missing raw response {raw['path']}")
                continue
            if sha256(path) != raw.get("sha256"):
                errors.append(f"{source}: raw hash mismatch {raw['path']}")
            if path.stat().st_size != raw.get("bytes"):
                errors.append(f"{source}: raw size mismatch {raw['path']}")
    combined = args.search_dir / manifest["combined_file"]
    combined_count = csv_rows(combined)
    if combined_count != total or total != manifest.get("total_source_records"):
        errors.append("combined source-record count mismatch")
    if errors:
        raise SystemExit("search snapshot validation failed:\n- " + "\n- ".join(errors))
    mode = "complete" if manifest.get("complete_retrieval") else "pilot"
    print(
        f"search_snapshot_ok mode={mode} sources={len(manifest['source_manifests'])} "
        f"records={total}"
    )


if __name__ == "__main__":
    main()
