#!/usr/bin/env python3
"""Validate and resolve the v0.3 development reference inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/v0.3.0"
ANALYSIS = REPO / "analysis/causal_extraction/v0.3.0_development"
INPUTS = REPO / "data/causal_extraction/v0.3.0_development/inputs"
INVENTORY = ANALYSIS / "reference_inventory.json"
RESOLVED = ANALYSIS / "reference_inventory_resolved.json"

EVIDENCE_FIELDS = (
    "method_evidence_atom_ids",
    "result_evidence_atom_ids",
    "validation_evidence_atom_ids",
)
DESIGN_FAMILIES = {
    "genetic_instrument",
    "randomized_assignment",
    "controlled_intervention",
    "targeted_perturbation",
    "temporal_or_quasi_experimental",
    "formal_directed_model",
}
CAUSAL_BASES = {"effect_identification_design", "formal_directed_hypothesis"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def atom_lookup(document_id: str) -> dict[str, dict[str, Any]]:
    path = INPUTS / document_id / "evidence_atom_index.json"
    index = load_json(path)
    return {atom["evidence_atom_id"]: atom for atom in index["atoms"]}


def resolved_atom(atom: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_atom_id": atom["evidence_atom_id"],
        "section_id": atom["section_id"],
        "heading": atom["heading"],
        "document_atom_order": atom["document_atom_order"],
        "page_numbers": atom["page_numbers"],
        "raw_text": atom["raw_text"],
        "atom_sha256": atom["atom_sha256"],
    }


def validate_and_resolve() -> tuple[dict[str, Any], dict[str, int]]:
    sample = load_json(SUITE / "sample.json")
    inventory = load_json(INVENTORY)
    if inventory["provenance"]["v0_3_model_outputs_seen"] is not False:
        raise ValueError("Reference inventory must remain independent of v0.3 outputs")
    if inventory["provenance"]["gold_standard_claim"] is not False:
        raise ValueError("Analyst draft cannot claim expert gold-standard status")

    expected = {
        item["document_id"]: (item["sample_order"], item["doi"])
        for item in sample["reports"]
    }
    observed_ids = [report["document_id"] for report in inventory["reports"]]
    if set(observed_ids) != set(expected):
        raise ValueError("Inventory reports do not exactly match the frozen sample")
    if len(observed_ids) != len(set(observed_ids)):
        raise ValueError("Duplicate report in reference inventory")

    analysis_ids: set[str] = set()
    resolved_reports: list[dict[str, Any]] = []
    evidence_references = 0
    excluded_candidates = 0
    for report in inventory["reports"]:
        document_id = report["document_id"]
        expected_order, expected_doi = expected[document_id]
        if report["sample_order"] != expected_order or report["doi"] != expected_doi:
            raise ValueError(f"Frozen sample metadata mismatch: {document_id}")
        atoms = atom_lookup(document_id)
        resolved_report = {key: value for key, value in report.items() if key != "causal_analyses"}
        resolved_analyses = []
        for analysis in report["causal_analyses"]:
            analysis_id = analysis["analysis_id"]
            if analysis_id in analysis_ids:
                raise ValueError(f"Duplicate analysis_id: {analysis_id}")
            analysis_ids.add(analysis_id)
            if analysis["design_family"] not in DESIGN_FAMILIES:
                raise ValueError(f"Unknown design family: {analysis_id}")
            if analysis["causal_basis"] not in CAUSAL_BASES:
                raise ValueError(f"Unknown causal basis: {analysis_id}")
            if not analysis["method_evidence_atom_ids"]:
                raise ValueError(f"Missing method evidence: {analysis_id}")
            if not analysis["result_evidence_atom_ids"]:
                raise ValueError(f"Missing result evidence: {analysis_id}")
            resolved_analysis = {
                key: value for key, value in analysis.items() if key not in EVIDENCE_FIELDS
            }
            for field in EVIDENCE_FIELDS:
                ids = analysis[field]
                if len(ids) != len(set(ids)):
                    raise ValueError(f"Duplicate atom within {analysis_id}.{field}")
                resolved = []
                for atom_id in ids:
                    if atom_id not in atoms:
                        raise ValueError(
                            f"Unknown or cross-report atom {atom_id} in {analysis_id}.{field}"
                        )
                    atom = atoms[atom_id]
                    if "> References" in atom["heading"]:
                        raise ValueError(f"Reference-list atom used in {analysis_id}: {atom_id}")
                    resolved.append(resolved_atom(atom))
                    evidence_references += 1
                resolved_analysis[field.replace("_ids", "")] = resolved
            resolved_analyses.append(resolved_analysis)

        resolved_excluded = []
        for candidate in report["excluded_candidates"]:
            excluded_candidates += 1
            ids = candidate["evidence_atom_ids"]
            if not ids:
                raise ValueError(f"Excluded candidate lacks evidence: {document_id}")
            item = {key: value for key, value in candidate.items() if key != "evidence_atom_ids"}
            item["evidence_atoms"] = []
            for atom_id in ids:
                if atom_id not in atoms:
                    raise ValueError(
                        f"Unknown or cross-report atom {atom_id} in excluded candidate "
                        f"for {document_id}"
                    )
                atom = atoms[atom_id]
                if "> References" in atom["heading"]:
                    raise ValueError(
                        f"Reference-list atom used in excluded candidate: {atom_id}"
                    )
                item["evidence_atoms"].append(resolved_atom(atom))
                evidence_references += 1
            resolved_excluded.append(item)
        resolved_report["causal_analyses"] = resolved_analyses
        resolved_report["excluded_candidates"] = resolved_excluded
        resolved_reports.append(resolved_report)

    resolved_inventory = {
        key: value for key, value in inventory.items() if key != "reports"
    }
    resolved_inventory["reports"] = resolved_reports
    summary = {
        "reports": len(resolved_reports),
        "causal_analyses": len(analysis_ids),
        "excluded_candidates": excluded_candidates,
        "evidence_references": evidence_references,
    }
    resolved_inventory["validation_summary"] = summary
    return resolved_inventory, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-resolved", action="store_true")
    args = parser.parse_args()
    resolved, summary = validate_and_resolve()
    if args.write_resolved:
        RESOLVED.parent.mkdir(parents=True, exist_ok=True)
        RESOLVED.write_text(
            json.dumps(resolved, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
