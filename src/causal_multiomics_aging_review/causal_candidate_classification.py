from __future__ import annotations

import copy
import json
from typing import Any

from causal_multiomics_aging_review.causal_analysis_inventory import (
    derive_causal_level,
)

CLASSIFICATION_FIELDS = (
    "causal_basis",
    "design_family",
    "variation_source",
    "aging_role",
    "multiomics_role",
    "contrast_status",
    "assumptions_reviewability",
    "result_status",
    "validation_strength",
)


def _json_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def render_candidate_scaffold(report: dict[str, Any]) -> str:
    """Render a neutral candidate list without reference classifications."""
    lines = ["FORMAT\tfixed_candidate_scaffold_v1"]
    for candidate in report["candidates"]:
        lines.append(
            "C\t"
            + candidate["candidate_id"]
            + "\t"
            + _json_string(candidate["candidate_label"])
            + "\t"
            + json.dumps(
                candidate["candidate_evidence_atom_ids"],
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
    return "\n".join(lines) + "\n"


def validate_candidate_scaffold(
    report: dict[str, Any], atom_index: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    known_atoms = {
        atom["evidence_atom_id"]: atom["document_atom_order"]
        for atom in atom_index["atoms"]
    }
    candidate_ids: set[str] = set()
    prior_first_order = -1
    for index, candidate in enumerate(report["candidates"]):
        candidate_id = candidate["candidate_id"]
        if candidate_id in candidate_ids:
            errors.append(f"duplicate candidate_id: {candidate_id}")
        candidate_ids.add(candidate_id)
        evidence_ids = candidate["candidate_evidence_atom_ids"]
        if not evidence_ids:
            errors.append(f"{candidate_id}: no candidate evidence")
            continue
        unknown = [atom_id for atom_id in evidence_ids if atom_id not in known_atoms]
        if unknown:
            errors.append(f"{candidate_id}: unknown evidence IDs {unknown}")
            continue
        orders = [known_atoms[atom_id] for atom_id in evidence_ids]
        if orders != sorted(orders):
            errors.append(f"{candidate_id}: evidence IDs are not in document order")
        if orders[0] < prior_first_order:
            errors.append(f"candidate {index} is not in source order")
        prior_first_order = orders[0]
    return errors


def validate_candidate_response(
    response: dict[str, Any],
    *,
    expected_report_id: str,
    candidate_report: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if response.get("report_id") != expected_report_id:
        errors.append("report_id does not match the supplied report")
    expected_ids = [item["candidate_id"] for item in candidate_report["candidates"]]
    decisions = response.get("candidates", [])
    returned_ids = [item.get("candidate_id") for item in decisions]
    if len(returned_ids) != len(set(returned_ids)):
        errors.append("candidate_id values must be unique")
    if set(returned_ids) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(returned_ids))
        extra = sorted(set(returned_ids) - set(expected_ids))
        errors.append(f"candidate coverage mismatch; missing={missing}, extra={extra}")

    source_status = response.get("source_status")
    for index, decision in enumerate(decisions):
        prefix = f"candidates[{index}]"
        qualification = decision.get("qualification")
        failed = decision.get("first_failed_condition")
        values = [decision.get(field) for field in CLASSIFICATION_FIELDS]
        if qualification == "include":
            if failed != "none":
                errors.append(f"{prefix}: include requires first_failed_condition none")
            if "not_applicable" in values:
                errors.append(f"{prefix}: include requires every classification field")
        elif qualification == "exclude":
            if failed in {"none", "insufficient_evidence"}:
                errors.append(f"{prefix}: exclude requires a decisive failed condition")
            if any(value != "not_applicable" for value in values):
                errors.append(f"{prefix}: exclude fields must be not_applicable")
        elif qualification == "unclear":
            if failed != "insufficient_evidence":
                errors.append(f"{prefix}: unclear requires insufficient_evidence")
            if any(value != "not_applicable" for value in values):
                errors.append(f"{prefix}: unclear fields must be not_applicable")
        if source_status == "insufficient_or_corrupt" and qualification != "unclear":
            errors.append(f"{prefix}: corrupt source requires unclear qualification")
    return errors


def normalize_candidate_response(
    response: dict[str, Any], candidate_report: dict[str, Any]
) -> dict[str, Any]:
    value = copy.deepcopy(response)
    scaffold = {
        candidate["candidate_id"]: candidate
        for candidate in candidate_report["candidates"]
    }
    order = {
        candidate["candidate_id"]: index
        for index, candidate in enumerate(candidate_report["candidates"])
    }
    for decision in value["candidates"]:
        candidate = scaffold[decision["candidate_id"]]
        decision["candidate_evidence_atom_ids"] = candidate[
            "candidate_evidence_atom_ids"
        ]
        decision["python_derived_level"] = (
            derive_causal_level(decision)
            if decision["qualification"] == "include"
            else None
        )
    value["candidates"].sort(key=lambda item: order[item["candidate_id"]])
    return value
