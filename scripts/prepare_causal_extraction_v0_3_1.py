#!/usr/bin/env python3
"""Build the neutral fixed-candidate scaffold for the v0.3.1 ablation."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_extraction import read_json, write_json

REPO = Path(__file__).resolve().parents[1]
V030_SAMPLE = REPO / "protocol/causal_extraction/v0.3.0/sample.json"
V030_REFERENCE = (
    REPO
    / "analysis/causal_extraction/v0.3.0_development/reference_inventory.json"
)
INPUTS = REPO / "data/causal_extraction/v0.3.0_development/inputs"
SUITE = REPO / "protocol/causal_extraction/v0.3.1"
ANALYSIS = REPO / "analysis/causal_extraction/v0.3.1_development"


def ordered_unique_atom_ids(
    groups: list[list[str]], atom_orders: dict[str, int]
) -> list[str]:
    atom_ids = {atom_id for group in groups for atom_id in group}
    return sorted(atom_ids, key=lambda atom_id: atom_orders[atom_id])


def report_candidates(
    report: dict[str, Any], atom_index: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    atom_orders = {
        atom["evidence_atom_id"]: atom["document_atom_order"]
        for atom in atom_index["atoms"]
    }
    combined: list[dict[str, Any]] = []
    for analysis in report["causal_analyses"]:
        evidence = ordered_unique_atom_ids(
            [
                analysis["method_evidence_atom_ids"],
                analysis["result_evidence_atom_ids"],
                analysis["validation_evidence_atom_ids"],
            ],
            atom_orders,
        )
        combined.append(
            {
                "candidate_label": analysis["analysis_label"],
                "candidate_evidence_atom_ids": evidence,
                "source_order": min(atom_orders[item] for item in evidence),
                "reference": {
                    "expected_qualification": "include",
                    "source_reference_id": analysis["analysis_id"],
                    "source_reason_code": None,
                },
            }
        )
    for excluded_index, candidate in enumerate(report["excluded_candidates"], start=1):
        evidence = ordered_unique_atom_ids(
            [candidate["evidence_atom_ids"]], atom_orders
        )
        combined.append(
            {
                "candidate_label": candidate["candidate_label"],
                "candidate_evidence_atom_ids": evidence,
                "source_order": min(atom_orders[item] for item in evidence),
                "reference": {
                    "expected_qualification": "exclude",
                    "source_reference_id": (
                        f"excluded_{report['sample_order']:03d}_{excluded_index:02d}"
                    ),
                    "source_reason_code": candidate["reason_code"],
                },
            }
        )
    combined.sort(key=lambda item: (item["source_order"], item["candidate_label"]))

    prompt_candidates: list[dict[str, Any]] = []
    reference_key: list[dict[str, Any]] = []
    for candidate_index, candidate in enumerate(combined, start=1):
        candidate_id = (
            f"cc_v031_{report['sample_order']:03d}_{candidate_index:02d}"
        )
        prompt_candidates.append(
            {
                "candidate_id": candidate_id,
                "candidate_label": candidate["candidate_label"],
                "candidate_evidence_atom_ids": candidate[
                    "candidate_evidence_atom_ids"
                ],
            }
        )
        reference_key.append(
            {
                "candidate_id": candidate_id,
                **candidate["reference"],
            }
        )
    return prompt_candidates, reference_key


def main() -> None:
    sample = read_json(V030_SAMPLE)
    reference = read_json(V030_REFERENCE)
    references = {report["document_id"]: report for report in reference["reports"]}
    scaffold_reports = []
    key_reports = []
    for sampled in sample["reports"]:
        document_id = sampled["document_id"]
        atom_index = read_json(INPUTS / document_id / "evidence_atom_index.json")
        candidates, key = report_candidates(references[document_id], atom_index)
        scaffold_reports.append(
            {
                "sample_order": sampled["sample_order"],
                "report_id": sampled["report_id"],
                "document_id": document_id,
                "doi": sampled["doi"],
                "candidates": candidates,
            }
        )
        key_reports.append(
            {
                "sample_order": sampled["sample_order"],
                "report_id": sampled["report_id"],
                "document_id": document_id,
                "doi": sampled["doi"],
                "candidates": key,
            }
        )

    v031_sample = copy.deepcopy(sample)
    v031_sample["sample_id"] = (
        "causal_extraction_v0.3.1_inherited_twelve_report_development_sample"
    )
    v031_sample["status"] = "inherited_unchanged_from_frozen_v0.3.0_sample"
    v031_sample["parent_sample"] = {
        "path": "protocol/causal_extraction/v0.3.0/sample.json",
        "sample_id": sample["sample_id"],
    }
    write_json(SUITE / "sample.json", v031_sample)
    write_json(
        SUITE / "candidate_scaffold.json",
        {
            "scaffold_version": "fixed_candidate_scaffold_v1",
            "status": "neutral_prompt_input",
            "expert_gold_standard": False,
            "prompt_visible_fields": [
                "candidate_id",
                "candidate_label",
                "candidate_evidence_atom_ids",
            ],
            "reports": scaffold_reports,
        },
    )
    write_json(
        ANALYSIS / "candidate_reference_key.json",
        {
            "reference_key_version": "0.3.1",
            "status": "ai_assisted_analyst_draft_pending_human_verification",
            "expert_gold_standard": False,
            "model_prompt_input": False,
            "reports": key_reports,
        },
    )
    total = sum(len(report["candidates"]) for report in scaffold_reports)
    included = sum(
        item["expected_qualification"] == "include"
        for report in key_reports
        for item in report["candidates"]
    )
    print(
        f"prepared {total} fixed candidates across {len(scaffold_reports)} reports "
        f"({included} reference includes, {total - included} boundaries)"
    )


if __name__ == "__main__":
    main()
