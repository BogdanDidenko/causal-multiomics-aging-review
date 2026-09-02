from __future__ import annotations

from causal_multiomics_aging_review.causal_role_classification import (
    combine_role_outputs,
    derive_eligibility,
    filter_candidate_report,
    normalize_role_response,
    validate_role_response,
)


def scaffold() -> dict:
    return {
        "candidates": [
            {
                "candidate_id": "cc_v031_001_01",
                "candidate_label": "candidate one",
                "candidate_evidence_atom_ids": ["ea_one"],
            },
            {
                "candidate_id": "cc_v031_001_02",
                "candidate_label": "candidate two",
                "candidate_evidence_atom_ids": ["ea_two"],
            },
        ]
    }


def test_eligibility_uses_first_no_in_frozen_order() -> None:
    criteria = {
        "current_report_attribution": "yes",
        "empirical_result": "yes",
        "aging_relevance": "no",
        "named_causal_basis": "no",
        "multiomics_workflow": "yes",
        "distinct_design_unit": "yes",
    }
    assert derive_eligibility(criteria) == ("exclude", "no_aging_relevance")
    criteria["aging_relevance"] = "unclear"
    criteria["named_causal_basis"] = "yes"
    assert derive_eligibility(criteria) == ("unclear", "insufficient_evidence")


def test_role_response_coverage_and_normalization() -> None:
    report = filter_candidate_report(scaffold(), ["cc_v031_001_01"])
    response = {
        "report_id": "doi:test",
        "candidates": [
            {
                "candidate_id": "cc_v031_001_01",
                "causal_basis": "effect_identification_design",
                "design_family": "genetic_instrument",
                "variation_source": "genetic_instrument",
            }
        ],
    }
    assert not validate_role_response(
        response,
        expected_report_id="doi:test",
        candidate_report=report,
        role_id="design_identity",
    )
    normalized = normalize_role_response(
        response, candidate_report=report, role_id="design_identity"
    )
    assert normalized["candidates"][0]["candidate_evidence_atom_ids"] == [
        "ea_one"
    ]


def test_combine_roles_derives_level() -> None:
    report = scaffold()
    eligibility = {
        "report_id": "doi:test",
        "candidates": [
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_evidence_atom_ids": candidate[
                    "candidate_evidence_atom_ids"
                ],
                "current_report_attribution": "yes",
                "empirical_result": "yes",
                "aging_relevance": "yes",
                "named_causal_basis": "yes",
                "multiomics_workflow": "yes",
                "distinct_design_unit": "yes",
                "python_qualification": "include",
                "python_first_failed_condition": "none",
            }
            for candidate in report["candidates"]
        ],
    }
    selected_id = "cc_v031_001_01"
    outputs = {
        "eligibility": eligibility,
        "design_identity": {
            "report_id": "doi:test",
            "candidates": [
                {
                    "candidate_id": selected_id,
                    "causal_basis": "effect_identification_design",
                    "design_family": "genetic_instrument",
                    "variation_source": "genetic_instrument",
                }
            ],
        },
        "review_context": {
            "report_id": "doi:test",
            "candidates": [
                {
                    "candidate_id": selected_id,
                    "aging_role": "biological_or_chronological_aging_outcome",
                    "multiomics_role": "omics_exposure_in_causal_design",
                }
            ],
        },
        "effect_appraisal": {
            "report_id": "doi:test",
            "candidates": [
                {
                    "candidate_id": selected_id,
                    "contrast_status": "implicit",
                    "assumptions_reviewability": "reviewable",
                    "result_status": "positive",
                }
            ],
        },
        "validation": {
            "report_id": "doi:test",
            "candidates": [
                {"candidate_id": selected_id, "validation_strength": "none"}
            ],
        },
    }
    combined = combine_role_outputs(
        outputs,
        all_candidate_report=report,
        eligible_candidate_ids=[selected_id],
    )
    assert combined["candidates"][0]["python_derived_level"] == 3
    assert "python_derived_level" not in combined["candidates"][1]
