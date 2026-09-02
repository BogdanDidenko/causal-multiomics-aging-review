from __future__ import annotations

import copy
import json
from typing import Any

from causal_multiomics_aging_review.causal_extraction import canonical_json

QUALIFYING_LEVEL_FOUR_VALIDATION = {
    "link_specific_colocalization",
    "orthogonal_same_link",
    "independent_replication",
}
FORMAL_DIRECTED_DESIGNS = {
    "mediation",
    "temporal_design",
    "graphical_or_structural_model",
    "causal_discovery_algorithm",
    "other_named_design",
}


def _json_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def build_compact_report_packet(atom_index: dict[str, Any]) -> str:
    """Serialize every evidence atom once, preserving canonical document order."""
    lines = [
        "FORMAT\tall_evidence_atoms_compact_v1",
        f"REPORT_ID\t{_json_string(str(atom_index['report_id']))}",
        f"DOI\t{_json_string(str(atom_index.get('doi', '')))}",
        f"TITLE\t{_json_string(str(atom_index.get('title', '')))}",
    ]
    current_section: str | None = None
    for atom in atom_index["atoms"]:
        section_id = str(atom["section_id"])
        if section_id != current_section:
            lines.append("S\t" + section_id + "\t" + _json_string(str(atom.get("heading", ""))))
            current_section = section_id
        lines.append(
            "A\t"
            + str(atom["evidence_atom_id"])
            + "\t"
            + str(atom["atom_type"])
            + "\t"
            + _json_string(str(atom["raw_text"]))
        )
    return "\n".join(lines) + "\n"


def packet_atom_ids(packet: str) -> list[str]:
    return [line.split("\t", 3)[1] for line in packet.splitlines() if line.startswith("A\t")]


def atom_map(atom_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {atom["evidence_atom_id"]: atom for atom in atom_index["atoms"]}


def derive_causal_level(analysis: dict[str, Any]) -> int:
    if analysis["causal_basis"] == "formal_directed_hypothesis":
        return 2
    if (
        analysis["contrast_status"] == "unclear"
        or analysis["assumptions_reviewability"] == "not_reviewable"
    ):
        return 2
    if analysis["validation_strength"] in QUALIFYING_LEVEL_FOUR_VALIDATION:
        return 4
    return 3


def validate_inventory_semantics(
    response: dict[str, Any],
    *,
    expected_report_id: str,
    atom_index: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if response.get("report_id") != expected_report_id:
        errors.append("report_id does not match the supplied report")
    analyses = response.get("analyses", [])
    if response.get("source_status") == "insufficient_or_corrupt" and analyses:
        errors.append("insufficient_or_corrupt source must have no analyses")
    atoms = atom_map(atom_index)
    seen: set[str] = set()
    for index, analysis in enumerate(analyses):
        prefix = f"analyses[{index}]"
        referenced = [analysis.get("method_atom_id"), analysis.get("result_atom_id")]
        referenced.extend(analysis.get("validation_atom_ids", []))
        for atom_id in referenced:
            if atom_id not in atoms:
                errors.append(f"{prefix}: unknown evidence atom {atom_id}")
        identity = canonical_json(analysis)
        if identity in seen:
            errors.append(f"{prefix}: duplicate analysis record")
        seen.add(identity)

        validation_ids = analysis.get("validation_atom_ids", [])
        validation_strength = analysis.get("validation_strength")
        if validation_strength == "none" and validation_ids:
            errors.append(f"{prefix}: validation_strength none requires no validation atom")
        if validation_strength != "none" and len(validation_ids) != 1:
            errors.append(f"{prefix}: non-none validation requires exactly one atom")
        if (
            analysis.get("causal_basis") == "formal_directed_hypothesis"
            and analysis.get("design_family") not in FORMAL_DIRECTED_DESIGNS
        ):
            errors.append(f"{prefix}: formal directed hypothesis has incompatible design")
        if (
            analysis.get("design_family") == "genetic_instrument"
            and analysis.get("variation_source") != "genetic_instrument"
        ):
            errors.append(f"{prefix}: genetic-instrument design has incompatible variation")
    return errors


def normalize_inventory(response: dict[str, Any], atom_index: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(response)
    atoms = atom_map(atom_index)
    for analysis in value["analyses"]:
        analysis["validation_atom_ids"] = sorted(analysis["validation_atom_ids"])
        analysis["python_derived_level"] = derive_causal_level(analysis)
    value["analyses"].sort(
        key=lambda analysis: (
            atoms[analysis["method_atom_id"]]["document_atom_order"],
            atoms[analysis["result_atom_id"]]["document_atom_order"],
            canonical_json(analysis),
        )
    )
    return value


def validate_reference_inventory_semantics(
    response: dict[str, Any],
    *,
    expected_reviewer_id: str,
    expected_report_id: str,
    atom_index: dict[str, Any],
) -> list[str]:
    """Validate identifiers and evidence grounding without interpreting prose."""
    errors: list[str] = []
    if response.get("reviewer_id") != expected_reviewer_id:
        errors.append("reviewer_id does not match the assigned reviewer")
    if response.get("report_id") != expected_report_id:
        errors.append("report_id does not match the supplied report")

    qualifying = response.get("qualifying_analyses", [])
    boundaries = response.get("excluded_boundary_candidates", [])
    if response.get("source_status") == "insufficient_or_corrupt" and (qualifying or boundaries):
        errors.append("insufficient_or_corrupt source must have empty candidate inventories")

    atoms = atom_map(atom_index)
    seen_candidate_ids: set[str] = set()
    seen_qualifying: set[str] = set()
    for index, analysis in enumerate(qualifying):
        prefix = f"qualifying_analyses[{index}]"
        candidate_id = str(analysis.get("reviewer_candidate_id", ""))
        if candidate_id in seen_candidate_ids:
            errors.append(f"{prefix}: duplicate reviewer_candidate_id {candidate_id}")
        seen_candidate_ids.add(candidate_id)

        evidence_ids = (
            list(analysis.get("method_evidence_atom_ids", []))
            + list(analysis.get("result_evidence_atom_ids", []))
            + list(analysis.get("validation_evidence_atom_ids", []))
        )
        for atom_id in evidence_ids:
            if atom_id not in atoms:
                errors.append(f"{prefix}: unknown evidence atom {atom_id}")

        identity = canonical_json(
            {
                key: value
                for key, value in analysis.items()
                if key not in {"reviewer_candidate_id", "analysis_label", "boundary_note"}
            }
        )
        if identity in seen_qualifying:
            errors.append(f"{prefix}: duplicate qualifying analysis")
        seen_qualifying.add(identity)

    seen_boundaries: set[str] = set()
    for index, boundary in enumerate(boundaries):
        prefix = f"excluded_boundary_candidates[{index}]"
        candidate_id = str(boundary.get("reviewer_candidate_id", ""))
        if candidate_id in seen_candidate_ids:
            errors.append(f"{prefix}: duplicate reviewer_candidate_id {candidate_id}")
        seen_candidate_ids.add(candidate_id)

        for atom_id in boundary.get("evidence_atom_ids", []):
            if atom_id not in atoms:
                errors.append(f"{prefix}: unknown evidence atom {atom_id}")

        identity = canonical_json(
            {
                key: value
                for key, value in boundary.items()
                if key not in {"reviewer_candidate_id", "candidate_label", "boundary_note"}
            }
        )
        if identity in seen_boundaries:
            errors.append(f"{prefix}: duplicate boundary candidate")
        seen_boundaries.add(identity)
    return errors


def normalize_reference_inventory(
    response: dict[str, Any], atom_index: dict[str, Any]
) -> dict[str, Any]:
    """Canonicalize collection order while preserving every reviewer field."""
    value = copy.deepcopy(response)
    atoms = atom_map(atom_index)

    def evidence_order(atom_id: str) -> tuple[int, str]:
        atom = atoms[atom_id]
        return int(atom["document_atom_order"]), atom_id

    for analysis in value["qualifying_analyses"]:
        for field in (
            "method_evidence_atom_ids",
            "result_evidence_atom_ids",
            "validation_evidence_atom_ids",
        ):
            analysis[field] = sorted(analysis[field], key=evidence_order)
        analysis["outcome_constructs"] = sorted(analysis["outcome_constructs"])

    for boundary in value["excluded_boundary_candidates"]:
        boundary["evidence_atom_ids"] = sorted(boundary["evidence_atom_ids"], key=evidence_order)

    def earliest(ids: list[str]) -> int:
        return min(int(atoms[atom_id]["document_atom_order"]) for atom_id in ids)

    value["qualifying_analyses"].sort(
        key=lambda analysis: (
            earliest(analysis["method_evidence_atom_ids"] + analysis["result_evidence_atom_ids"]),
            analysis["reviewer_candidate_id"],
        )
    )
    value["excluded_boundary_candidates"].sort(
        key=lambda boundary: (
            earliest(boundary["evidence_atom_ids"]),
            boundary["reviewer_candidate_id"],
        )
    )
    return value
