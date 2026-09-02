from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/summarize_causal_extraction_v0_3.py"


def load_summary_module():
    spec = importlib.util.spec_from_file_location("summarize_v0_3", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_wilson_interval_bounds_rate() -> None:
    module = load_summary_module()
    low, high = module.wilson_interval(8, 10)
    assert 0 < low < 0.8 < high < 1


def test_reference_alignment_uses_evidence_ids() -> None:
    module = load_summary_module()
    reference = {
        "causal_analyses": [
            {
                "analysis_id": "ca_1",
                "method_evidence_atom_ids": ["ea_method"],
                "result_evidence_atom_ids": ["ea_result"],
                "validation_evidence_atom_ids": [],
            }
        ],
        "excluded_candidates": [
            {"evidence_atom_ids": ["ea_boundary"]}
        ],
    }
    predicted = [
        {
            "method_atom_id": "ea_method",
            "result_atom_id": "ea_result",
            "validation_atom_ids": [],
        },
        {
            "method_atom_id": "ea_boundary",
            "result_atom_id": "ea_other",
            "validation_atom_ids": [],
        },
    ]
    aligned = module.align_to_reference(predicted, reference)
    assert aligned["evidence_overlap_matches"] == 1
    assert aligned["reference_alignment_recall"] == 1
    assert aligned["reference_alignment_precision"] == 0.5
    assert aligned["direct_boundary_promotions"] == [
        ["ea_boundary", "ea_other"]
    ]
