import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "analyze_causal_extraction_e0_disagreements",
    REPO / "scripts/analyze_causal_extraction_e0_disagreements.py",
)
assert SPEC is not None and SPEC.loader is not None
analyzer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analyzer)


def analysis(
    *,
    outcome: str = "senescence",
    atom_id: str = "ea_aaaaaaaaaaaaaaaaaaaaaaaa",
) -> dict:
    return {
        "analysis_basis": "effect_identification_design",
        "design_family": "targeted_genetic_perturbation",
        "method_name": "CRISPRi",
        "exposure_construct": "target knockdown",
        "outcome_construct": outcome,
        "biological_system": "cells",
        "analysis_completeness": "method_and_result",
        "method_evidence_resolved": [{"evidence_atom_id": atom_id}],
        "result_evidence_resolved": [],
    }


def test_empty_repeat_pair_is_explicitly_separated() -> None:
    comparison = analyzer._comparison({"analyses": []}, {"analyses": []})
    assert comparison["both_empty"] is True
    assert comparison["at_least_one_nonempty"] is False
    assert comparison["all_fields_plus_grounding_exact"] is True


def test_closed_agreement_does_not_hide_scientific_field_disagreement() -> None:
    left = {"analyses": [analysis(outcome="senescence")]}
    right = {"analyses": [analysis(outcome="lifespan")]}
    comparison = analyzer._comparison(left, right)
    assert comparison["analysis_count_exact"] is True
    assert comparison["closed_field_multiset_exact"] is True
    assert comparison["scientific_field_multiset_exact"] is False
    assert comparison["evidence_atom_union_exact"] is True
    assert comparison["all_fields_plus_grounding_exact"] is False


def test_evidence_overlap_is_reported_without_exact_match() -> None:
    left = {"analyses": [analysis(atom_id="ea_aaaaaaaaaaaaaaaaaaaaaaaa")]}
    right_analysis = analysis(atom_id="ea_aaaaaaaaaaaaaaaaaaaaaaaa")
    right_analysis["result_evidence_resolved"] = [
        {"evidence_atom_id": "ea_bbbbbbbbbbbbbbbbbbbbbbbb"}
    ]
    comparison = analyzer._comparison(left, {"analyses": [right_analysis]})
    assert comparison["evidence_atom_union_exact"] is False
    assert comparison["evidence_atom_jaccard"] == 0.5
