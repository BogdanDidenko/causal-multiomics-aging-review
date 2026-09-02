#!/usr/bin/env python3
"""Create or verify checksum inventories for restricted causal-extraction logs."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    read_json,
    sha256_file,
    sha256_text,
    write_json,
)

REPO = Path(__file__).resolve().parents[1]
EXPERIMENTS = {
    "v0.3.0": {
        "raw": REPO / "data/causal_extraction/v0.3.0_development/terra_5repeat",
        "output": REPO
        / "analysis/causal_extraction/v0.3.0_development/terra_5repeat"
        / "raw_artifact_inventory.json",
    },
    "v0.3.1": {
        "raw": REPO / "data/causal_extraction/v0.3.1_development/terra_5repeat",
        "output": REPO
        / "analysis/causal_extraction/v0.3.1_development/terra_5repeat"
        / "raw_artifact_inventory.json",
    },
    "v0.3.2": {
        "raw": REPO / "data/causal_extraction/v0.3.2_development/terra_5repeat",
        "output": REPO
        / "analysis/causal_extraction/v0.3.2_development/terra_5repeat"
        / "raw_artifact_inventory.json",
    },
}


def artifact_kind(path: Path) -> str:
    name = path.name
    if name.startswith("raw_response_attempt_"):
        return "raw_response"
    if name.startswith("parsed_attempt_"):
        return "parsed_response"
    if name.startswith("failure_attempt_"):
        return "failed_attempt"
    if name in {
        "normalized.json",
        "rendered_prompt.txt",
        "request.json",
        "validation.json",
        "input_manifest.json",
        "report_packet.txt",
        "candidate_scaffold.txt",
    }:
        return name.rsplit(".", 1)[0]
    return "orchestrator"


def build_inventory(version: str) -> dict[str, Any]:
    raw = EXPERIMENTS[version]["raw"]
    if not raw.is_dir():
        raise ValueError(f"Raw experiment directory is missing: {raw}")
    records = []
    kinds: Counter[str] = Counter()
    for path in sorted(item for item in raw.rglob("*") if item.is_file()):
        relative = str(path.relative_to(REPO))
        kind = artifact_kind(path)
        kinds[kind] += 1
        records.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "kind": kind,
            }
        )
    root_sha256 = sha256_text(canonical_json(records))
    return {
        "inventory_version": "1.0.0",
        "experiment_version": version,
        "restricted_raw_content_committed": False,
        "raw_root": str(raw.relative_to(REPO)),
        "file_count": len(records),
        "total_bytes": sum(item["bytes"] for item in records),
        "counts_by_kind": dict(sorted(kinds.items())),
        "root_sha256": root_sha256,
        "files": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--versions",
        nargs="+",
        choices=sorted(EXPERIMENTS),
        default=sorted(EXPERIMENTS),
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("Choose exactly one of --write or --check")
    for version in args.versions:
        inventory = build_inventory(version)
        output = EXPERIMENTS[version]["output"]
        if args.write:
            write_json(output, inventory)
        elif not output.is_file() or read_json(output) != inventory:
            raise ValueError(f"Raw artifact inventory is stale: {output}")
        print(
            f"{version}: {inventory['file_count']} files, "
            f"{inventory['total_bytes']} bytes, {inventory['root_sha256']}"
        )


if __name__ == "__main__":
    main()
