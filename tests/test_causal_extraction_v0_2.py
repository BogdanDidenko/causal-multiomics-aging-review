import importlib.util
from pathlib import Path

import pytest

VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1] / "scripts/validate_causal_claim_records_v0_2.py"
)
SPEC = importlib.util.spec_from_file_location("causal_extraction_v0_2", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

candidate_level = VALIDATOR.candidate_level
contrast_complete = VALIDATOR.contrast_complete
level4_status = VALIDATOR.level4_status


def claim_record(
    *,
    assessment: str = "effect_assessable",
    method: str = "targeted_pharmacologic_perturbation",
    validations: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    return {
        "reviewer_identification_assessment": assessment,
        "primary_design_or_method": method,
        "validations": validations or [],
        "contrast_components": {
            "exposure_or_intervention": "yes",
            "operation": "yes",
            "comparator": "yes",
            "outcome": "yes",
            "population_or_system": "yes",
            "time_horizon": "not_applicable",
        },
    }


def validation(
    validation_type: str,
    *,
    operation: str,
    data: str = "independent",
    experiment: str = "independent",
    threshold: str = "not_applicable",
) -> dict[str, str]:
    return {
        "validation_type": validation_type,
        "same_link_alignment": "exact",
        "operation_alignment": operation,
        "data_independence": data,
        "experimental_independence": experiment,
        "purpose": "identification",
        "result_status": "supports_claim",
        "colocalization_threshold_met": threshold,
    }


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        (
            claim_record(
                validations=[
                    validation("independent_same_link_replication", operation="same")
                ]
            ),
            "yes",
        ),
        (
            claim_record(
                validations=[
                    validation("orthogonal_same_link_identification", operation="orthogonal")
                ]
            ),
            "yes",
        ),
        (
            claim_record(
                method="genetic_instrument",
                validations=[
                    validation(
                        "appropriate_colocalization",
                        operation="unclear",
                        data="unclear",
                        experiment="unclear",
                        threshold="yes",
                    )
                ],
            ),
            "yes",
        ),
    ],
)
def test_level4_qualifying_paths(record: dict[str, object], expected: str) -> None:
    assert level4_status(record) == expected
    assert candidate_level(record) == (4, "yes")


def test_irrelevant_unclear_field_does_not_block_replication() -> None:
    record = claim_record(
        validations=[
            validation(
                "independent_same_link_replication",
                operation="same",
                threshold="unclear",
            )
        ]
    )
    assert level4_status(record) == "yes"


def test_relevant_unclear_field_requires_level4_review() -> None:
    record = claim_record(
        validations=[
            validation(
                "orthogonal_same_link_identification",
                operation="orthogonal",
                experiment="unclear",
            )
        ]
    )
    assert level4_status(record) == "unclear"
    assert candidate_level(record) == (3, "unclear")


def test_related_mechanism_cannot_create_level4_uncertainty() -> None:
    record = claim_record(
        validations=[
            validation(
                "related_mechanism",
                operation="unclear",
                data="unclear",
                experiment="unclear",
                threshold="unclear",
            )
        ]
    )
    assert level4_status(record) == "no"
    assert candidate_level(record) == (3, "no")


@pytest.mark.parametrize(
    ("assessment", "method", "expected"),
    [
        ("no_identification", "candidate_prioritization", (1, "not_applicable")),
        ("effect_claim_not_assessable", "candidate_prioritization", (1, "not_applicable")),
        ("effect_claim_not_assessable", "mediation_analysis", (2, "not_applicable")),
        ("formal_hypothesis_only", "sem", (2, "not_applicable")),
        ("unclear", "genetic_instrument", ("manual_review", "not_applicable")),
    ],
)
def test_lower_level_and_manual_routes(
    assessment: str, method: str, expected: tuple[int | str, str]
) -> None:
    assert candidate_level(claim_record(assessment=assessment, method=method)) == expected


def test_contrast_completeness_is_derived_from_atomic_components() -> None:
    record = claim_record()
    assert contrast_complete(record) == "yes"
    record["contrast_components"]["comparator"] = "unclear"
    assert contrast_complete(record) == "unclear"
    record["contrast_components"]["comparator"] = "no"
    assert contrast_complete(record) == "no"
