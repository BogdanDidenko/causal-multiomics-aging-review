#!/usr/bin/env python3
"""Freeze two disjoint 15-report causal-extraction checkpoints before execution."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/prompt_suite/v0.1.0-rc1"
ELIGIBILITY = (
    REPO
    / "analysis/full_text_screening/final_eligibility_v1.5.4"
    / "final_eligibility_ledger_158.csv"
)
CORPUS = REPO / "data/full_text_screening/v1.5.3_deterministic_full_text_158/input.jsonl"
OUTPUT = (
    REPO
    / "protocol/causal_extraction/checkpoints/v0.1.0-rc1"
    / "two_sample_design.json"
)
SEED = "20260829"

# These preprints have eligible journal versions in the same corpus. Sampling
# uses the journal report so one underlying study cannot occupy two slots.
SUPERSEDED_REPORT_VERSIONS = {
    "10.21203/rs.3.rs-1264931/v1": "10.26508/lsa.202201492",
    "10.1101/2025.10.29.685384": "10.1002/advs.202521633",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def load_corpus() -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        doi = str(record.get("doi", "")).strip().casefold()
        if doi:
            records[doi] = record
    return records


def record_entry(
    *,
    order: int,
    doi: str,
    title: str,
    record: dict[str, Any],
    design_role: str = "",
) -> dict[str, Any]:
    sections = record["sections"]
    return {
        "checkpoint_order": order,
        "report_id": record["record_id"],
        "doi": doi,
        "title": title,
        "design_diversity_role": design_role,
        "document_id": record["document_id"],
        "canonical_section_count": len(sections),
        "canonical_section_characters": sum(len(section["text"]) for section in sections),
        "canonical_sections_sha256": canonical_json_sha256(sections),
        "source_chunk_artifact": record["input_provenance"]["source_chunk_artifact"],
    }


def build_design() -> dict[str, Any]:
    corpus = load_corpus()
    checkpoint_a = json.loads((SUITE / "checkpoint_inventory.json").read_text())
    a_reports = []
    for report in checkpoint_a["reports"]:
        doi = report["doi"].casefold()
        a_reports.append(
            record_entry(
                order=report["checkpoint_order"],
                doi=report["doi"],
                title=report["title"],
                record=corpus[doi],
                design_role=report["design_diversity_role"],
            )
        )

    with ELIGIBILITY.open(newline="", encoding="utf-8") as handle:
        eligible = [
            row
            for row in csv.DictReader(handle)
            if row["final_decision"] == "assessed" and row["doi"].strip()
        ]
    a_dois = {report["doi"].casefold() for report in a_reports}
    eligible = [
        row
        for row in eligible
        if row["doi"].casefold() not in a_dois
        and row["doi"].casefold() not in SUPERSEDED_REPORT_VERSIONS
    ]
    eligible.sort(
        key=lambda row: hashlib.sha256(
            f"{SEED}|{row['doi'].casefold()}".encode()
        ).hexdigest()
    )
    selected_b = eligible[:15]
    b_reports = [
        record_entry(
            order=index,
            doi=row["doi"],
            title=row["title"],
            record=corpus[row["doi"].casefold()],
        )
        for index, row in enumerate(selected_b, start=1)
    ]
    if len(b_reports) != 15:
        raise ValueError("Checkpoint B must contain 15 reports")
    if a_dois & {report["doi"].casefold() for report in b_reports}:
        raise ValueError("Checkpoint A and B overlap")

    return {
        "design_id": "causal_extraction_v0.1.0-rc1_two_samples_15_each",
        "status": "frozen_before_any_two_sample_terra_output",
        "freeze_date": "2026-08-29",
        "freeze_revision": "the Git commit containing this file",
        "suite": {
            "version": "0.1.0-rc1",
            "artifact_manifest_path": str(
                (SUITE / "artifact_manifest.json").relative_to(REPO)
            ),
            "artifact_manifest_sha256": sha256(SUITE / "artifact_manifest.json"),
        },
        "source": {
            "eligibility_ledger_path": str(ELIGIBILITY.relative_to(REPO)),
            "eligibility_ledger_sha256": sha256(ELIGIBILITY),
            "eligible_reports": 101,
            "canonical_corpus_path": str(CORPUS.relative_to(REPO)),
            "canonical_corpus_sha256": sha256(CORPUS),
        },
        "sampling": {
            "sample_size_each": 15,
            "overlap": 0,
            "checkpoint_a": (
                "Purposive heterogeneous codebook-development sample frozen before "
                "suite model outputs; prior human annotations exist."
            ),
            "checkpoint_b": (
                "Deterministic hash sample from eligible reports outside A after "
                "superseded report-version removal."
            ),
            "checkpoint_b_seed": SEED,
            "checkpoint_b_order_key": "sha256(seed + '|' + normalized_doi)",
            "superseded_report_versions": SUPERSEDED_REPORT_VERSIONS,
            "independent_accuracy_claim_allowed": False,
        },
        "checkpoints": {
            "A": {
                "purpose": "instrument_development_and_stability",
                "prior_human_codebook_annotations_exist": True,
                "reports": a_reports,
            },
            "B": {
                "purpose": "disjoint_stability_generalization",
                "prior_human_codebook_annotations_exist": False,
                "reports": b_reports,
            },
        },
    }


def main() -> int:
    value = build_design()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

