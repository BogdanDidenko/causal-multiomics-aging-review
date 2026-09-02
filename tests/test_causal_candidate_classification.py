from __future__ import annotations

import json
from pathlib import Path

from causal_multiomics_aging_review.causal_candidate_classification import (
    CLASSIFICATION_FIELDS,
    normalize_candidate_response,
    render_candidate_scaffold,
    validate_candidate_response,
    validate_candidate_scaffold,
)

REPO = Path(__file__).resolve().parents[1]
ATOM_INDEX = (
    REPO
    / "data/causal_extraction/v0.3.0_development/inputs/doi_4b54110a1a6ace81"
    / "evidence_atom_index.json"
)


def load_index() -> dict:
    return json.loads(ATOM_INDEX.read_text(encoding="utf-8"))


def candidate_report() -> dict:
    index = load_index()
    return {
        "candidates": [
            {
                "candidate_id": "cc_v031_003_01",
                "candidate_label": "Assigned exercise intervention",
                "candidate_evidence_atom_ids": [
                    index["atoms"][0]["evidence_atom_id"]
                ],
            }
        ]
    }


def included_decision() -> dict:
    return {
        "candidate_id": "cc_v031_003_01",
        "qualification": "include",
        "first_failed_condition": "none",
        "causal_basis": "effect_identification_design",
        "design_family": "nonrandomized_controlled_intervention",
        "variation_source": "behavioral_or_environmental_intervention",
        "aging_role": "cellular_senescence_outcome",
        "multiomics_role": "multiomics_outcomes_under_causal_design",
        "contrast_status": "explicit",
        "assumptions_reviewability": "reviewable",
        "result_status": "positive",
        "validation_strength": "none",
    }


def test_scaffold_is_valid_and_neutral() -> None:
    report = candidate_report()
    assert not validate_candidate_scaffold(report, load_index())
    rendered = render_candidate_scaffold(report)
    assert "expected_qualification" not in rendered
    assert "source_reason_code" not in rendered
    assert "cc_v031_003_01" in rendered


def test_include_response_is_normalized_with_frozen_evidence() -> None:
    index = load_index()
    report = candidate_report()
    response = {
        "report_id": index["report_id"],
        "source_status": "sufficient",
        "candidates": [included_decision()],
    }
    assert not validate_candidate_response(
        response,
        expected_report_id=index["report_id"],
        candidate_report=report,
    )
    normalized = normalize_candidate_response(response, report)
    decision = normalized["candidates"][0]
    assert decision["candidate_evidence_atom_ids"] == report["candidates"][0][
        "candidate_evidence_atom_ids"
    ]
    assert decision["python_derived_level"] == 3


def test_noninclude_response_must_use_not_applicable_fields() -> None:
    index = load_index()
    report = candidate_report()
    decision = included_decision()
    decision["qualification"] = "exclude"
    decision["first_failed_condition"] = "no_named_causal_basis"
    for field in CLASSIFICATION_FIELDS:
        decision[field] = "not_applicable"
    response = {
        "report_id": index["report_id"],
        "source_status": "sufficient",
        "candidates": [decision],
    }
    assert not validate_candidate_response(
        response,
        expected_report_id=index["report_id"],
        candidate_report=report,
    )
    response["candidates"][0]["design_family"] = "genetic_instrument"
    assert validate_candidate_response(
        response,
        expected_report_id=index["report_id"],
        candidate_report=report,
    )
