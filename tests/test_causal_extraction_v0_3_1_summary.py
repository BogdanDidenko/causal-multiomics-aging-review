from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/summarize_causal_extraction_v0_3_1.py"


def load_summary_module():
    spec = importlib.util.spec_from_file_location("summarize_v0_3_1", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decision(candidate_id: str, *, qualification: str = "include") -> dict:
    included = qualification == "include"
    value = "not_applicable"
    return {
        "candidate_id": candidate_id,
        "qualification": qualification,
        "first_failed_condition": "none" if included else "no_named_causal_basis",
        "causal_basis": "effect_identification_design" if included else value,
        "design_family": "genetic_instrument" if included else value,
        "variation_source": "genetic_instrument" if included else value,
        "aging_role": "biological_or_chronological_aging_outcome" if included else value,
        "multiomics_role": "omics_exposure_in_causal_design" if included else value,
        "contrast_status": "implicit" if included else value,
        "assumptions_reviewability": "reviewable" if included else value,
        "result_status": "positive" if included else value,
        "validation_strength": "none" if included else value,
        "candidate_evidence_atom_ids": ["ea_000000000000000000000000"],
        "python_derived_level": 3 if included else None,
    }


def test_prefix_metrics_separate_qualification_and_all_field_agreement() -> None:
    module = load_summary_module()
    outputs = []
    for repeat in range(5):
        item = decision("cc_v031_001_01")
        if repeat == 4:
            item["validation_strength"] = "supportive_same_experiment"
        outputs.append(
            {
                "report_id": "doi:test",
                "source_status": "sufficient",
                "candidates": [item],
            }
        )
    three = module.prefix_metrics(outputs, 3)
    five = module.prefix_metrics(outputs, 5)
    assert three["report_exact_agreement"] is True
    assert five["report_exact_agreement"] is False
    assert five["qualification_exact_count"] == 1
    assert five["all_fields_exact_count"] == 0
