from __future__ import annotations

from causal_multiomics_aging_review.causal_analysis_inventory import (
    normalize_reference_inventory,
    validate_reference_inventory_semantics,
)


def atom_index() -> dict:
    return {
        "report_id": "report-1",
        "atoms": [
            {"evidence_atom_id": "ea_000000000000000000000001", "document_atom_order": 1},
            {"evidence_atom_id": "ea_000000000000000000000002", "document_atom_order": 2},
            {"evidence_atom_id": "ea_000000000000000000000003", "document_atom_order": 3},
        ],
    }


def response() -> dict:
    return {
        "reviewer_id": "codex",
        "report_id": "report-1",
        "source_status": "sufficient",
        "qualifying_analyses": [
            {
                "reviewer_candidate_id": "analysis_1",
                "analysis_label": "Assigned intervention",
                "identifying_variation_or_assignment": "random assignment",
                "exposure_or_intervention_construct": "treatment",
                "comparator": "control",
                "biological_system": "mouse",
                "outcome_constructs": ["lifespan", "healthspan"],
                "causal_basis": "effect_identification_design",
                "design_family": "randomized_intervention",
                "method_evidence_atom_ids": ["ea_000000000000000000000002"],
                "result_evidence_atom_ids": ["ea_000000000000000000000003"],
                "validation_evidence_atom_ids": [],
                "boundary_note": "One design-level unit.",
            }
        ],
        "excluded_boundary_candidates": [
            {
                "reviewer_candidate_id": "boundary_1",
                "candidate_label": "Association",
                "first_failed_condition": "no_named_causal_basis",
                "evidence_atom_ids": ["ea_000000000000000000000001"],
                "boundary_note": "No identifying design.",
            }
        ],
        "coverage_note": "Complete packet reviewed.",
    }


def test_reference_inventory_semantics_accept_grounded_inventory() -> None:
    errors = validate_reference_inventory_semantics(
        response(),
        expected_reviewer_id="codex",
        expected_report_id="report-1",
        atom_index=atom_index(),
    )
    assert errors == []


def test_reference_inventory_semantics_rejects_unknown_atom_and_duplicate_id() -> None:
    value = response()
    value["excluded_boundary_candidates"][0]["reviewer_candidate_id"] = "analysis_1"
    value["excluded_boundary_candidates"][0]["evidence_atom_ids"] = ["ea_ffffffffffffffffffffffff"]
    errors = validate_reference_inventory_semantics(
        value,
        expected_reviewer_id="codex",
        expected_report_id="report-1",
        atom_index=atom_index(),
    )
    assert any("duplicate reviewer_candidate_id" in error for error in errors)
    assert any("unknown evidence atom" in error for error in errors)


def test_reference_inventory_normalization_uses_document_order() -> None:
    value = response()
    value["qualifying_analyses"][0]["method_evidence_atom_ids"] = [
        "ea_000000000000000000000002",
        "ea_000000000000000000000001",
    ]
    normalized = normalize_reference_inventory(value, atom_index())
    assert normalized["qualifying_analyses"][0]["method_evidence_atom_ids"] == [
        "ea_000000000000000000000001",
        "ea_000000000000000000000002",
    ]
