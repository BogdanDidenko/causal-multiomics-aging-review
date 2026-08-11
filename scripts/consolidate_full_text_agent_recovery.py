#!/usr/bin/env python3
"""Validate and consolidate independent full-text recovery agent outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
STRATEGIES = ("repository_api", "version_resolution", "publisher_browser")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def target_doi(row: dict[str, Any]) -> str:
    return str(row.get("target_doi") or row.get("input_doi") or "").casefold()


def source_file(strategy_root: Path, row: dict[str, Any]) -> Path | None:
    value = row.get("local_path") or row.get("local_file") or row.get("file")
    if not value:
        return None
    path = Path(str(value))
    return (REPO / path if str(path).startswith("data/") else strategy_root / path).resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO / "data/full_text/v1.1.2_oversized_20k_seek66/agent_recovery",
    )
    parser.add_argument(
        "--targets",
        type=Path,
        default=REPO / "data/full_text/v1.1.2_oversized_20k_seek66/unavailable.csv",
    )
    parser.add_argument(
        "--selection",
        type=Path,
        default=REPO / "protocol/full_text/oversized_20k_agent_recovery_selection.csv",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    targets = {row["doi"].casefold(): row for row in read_csv(args.targets.resolve())}
    selections = read_csv(args.selection.resolve())
    if len(selections) != len(targets) or {row["target_doi"] for row in selections} != set(
        targets
    ):
        raise SystemExit("Selection must cover every unavailable DOI exactly once")

    manifests: dict[str, dict[str, dict[str, Any]]] = {}
    for strategy in STRATEGIES:
        rows = read_jsonl(root / strategy / "manifest.jsonl")
        if len(rows) != len(targets):
            raise SystemExit(f"{strategy} manifest does not contain 21 records")
        manifests[strategy] = {target_doi(row): row for row in rows}

    combined_dir = root / "combined"
    files_dir = combined_dir / "files"
    if combined_dir.exists():
        shutil.rmtree(combined_dir)
    files_dir.mkdir(parents=True)

    output: list[dict[str, Any]] = []
    for selection in selections:
        doi = selection["target_doi"]
        strategy = selection["strategy"]
        base = {
            "record_id": targets[doi]["record_id"],
            "doi": doi,
            "title": targets[doi]["title"],
            "report_form": selection["report_form"],
            "decision_note": selection["decision_note"],
        }
        if not strategy:
            output.append({**base, "status": "unresolved"})
            continue

        source = manifests[strategy][doi]
        if source.get("status") != "recovered":
            raise SystemExit(f"Selected source is not recovered: {doi} via {strategy}")
        path = source_file(root / strategy, source)
        expected = Path(selection["source_file"]).resolve()
        if path != expected or not path.is_file():
            raise SystemExit(f"Selected source path mismatch or missing: {doi}")
        actual_hash = sha256(path)
        if actual_hash != source.get("sha256"):
            raise SystemExit(f"Source hash mismatch: {doi}")
        if path.stat().st_size < 1000:
            raise SystemExit(f"Selected source is unexpectedly small: {doi}")
        if path.suffix.casefold() == ".pdf" and path.read_bytes()[:5] != b"%PDF-":
            raise SystemExit(f"Invalid PDF signature: {doi}")

        canonical = files_dir / f"{hashlib.sha256(doi.encode()).hexdigest()[:16]}{path.suffix}"
        shutil.copyfile(path, canonical)
        output.append(
            {
                **base,
                "status": "recovered",
                "strategy": strategy,
                "source_url": source.get("source_url"),
                "source_manifest": str(
                    (root / strategy / "manifest.jsonl").relative_to(REPO)
                ),
                "source_file": str(path.relative_to(REPO)),
                "canonical_file": str(canonical.relative_to(REPO)),
                "format": source.get("format"),
                "bytes": path.stat().st_size,
                "sha256": actual_hash,
            }
        )

    manifest_path = combined_dir / "manifest.jsonl"
    with manifest_path.open("w", encoding="utf-8") as handle:
        for row in output:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    statuses = Counter(row["status"] for row in output)
    forms = Counter(row["report_form"] for row in output if row["status"] == "recovered")
    summary = {
        "status": "complete",
        "target_count": len(output),
        "recovered_target_reports": statuses["recovered"],
        "unresolved_target_reports": statuses["unresolved"],
        "report_form_counts": dict(sorted(forms.items())),
        "standalone_article_or_report_files": sum(
            forms[value]
            for value in ("standalone_report", "accepted_manuscript", "thesis")
        ),
        "non_article_target_contents": sum(
            forms[value]
            for value in (
                "proceedings_collection",
                "conference_abstract",
                "conference_abstract_in_supplement",
                "title_index",
            )
        ),
        "strategy_selected_counts": dict(
            sorted(Counter(row.get("strategy") for row in output if row["status"] == "recovered").items())
        ),
        "manifest": str(manifest_path.relative_to(REPO)),
        "manifest_sha256": sha256(manifest_path),
        "selection": str(args.selection.resolve().relative_to(REPO)),
        "selection_sha256": sha256(args.selection.resolve()),
        "validation": {
            "all_targets_covered_once": True,
            "all_selected_source_hashes_match": True,
            "all_pdf_signatures_valid": True,
        },
    }
    (combined_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    baseline = json.loads((root.parent / "summary.json").read_text(encoding="utf-8"))
    baseline_retrieved = sum(
        int(count)
        for status, count in baseline["status_counts"].items()
        if status.startswith("downloaded_")
    )
    baseline_not_retrieved = int(baseline["target_count"]) - baseline_retrieved
    if baseline_not_retrieved != len(output):
        raise SystemExit("Recovery target count does not match baseline unavailable count")
    prisma = {
        "schema_version": "1.0.0",
        "status": "agent_recovery_complete_pending_incremental_full_text_screening",
        "flow": {
            "reports_sought_for_retrieval": int(baseline["target_count"]),
            "reports_retrieved_before_agent_recovery": baseline_retrieved,
            "reports_not_retrieved_before_agent_recovery": baseline_not_retrieved,
            "additional_target_reports_recovered": statuses["recovered"],
            "reports_retrieved_after_agent_recovery": (
                baseline_retrieved + statuses["recovered"]
            ),
            "reports_not_retrieved_after_agent_recovery": statuses["unresolved"],
            "additional_reports_pending_full_text_screening": statuses["recovered"],
        },
        "content_boundary": {
            "additional_standalone_article_or_report_files": summary[
                "standalone_article_or_report_files"
            ],
            "additional_non_article_target_contents": summary[
                "non_article_target_contents"
            ],
            "note": (
                "Non-article target contents are exact proceedings, abstract, or "
                "index records retained so report type can be resolved during screening."
            ),
        },
        "artifacts": {
            "combined_manifest": {
                "path": summary["manifest"],
                "sha256": summary["manifest_sha256"],
            },
            "selection": {
                "path": summary["selection"],
                "sha256": summary["selection_sha256"],
            },
        },
    }
    (root / "prisma_recovery_addendum.json").write_text(
        json.dumps(prisma, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
