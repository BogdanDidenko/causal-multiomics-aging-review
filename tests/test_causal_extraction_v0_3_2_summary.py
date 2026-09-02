from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/summarize_causal_extraction_v0_3_2.py"


def load_summary_module():
    spec = importlib.util.spec_from_file_location("summarize_v0_3_2", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_role_metrics_detect_one_late_field_change() -> None:
    module = load_summary_module()
    outputs = []
    for repeat in range(5):
        outputs.append(
            {
                "report_id": "doi:test",
                "candidates": [
                    {
                        "candidate_id": "cc_v031_001_01",
                        "candidate_evidence_atom_ids": ["ea_one"],
                        "aging_role": "cellular_senescence_outcome",
                        "multiomics_role": (
                            "omics_candidate_followed_by_perturbation"
                            if repeat < 4
                            else "report_level_multiomics_support"
                        ),
                    }
                ],
            }
        )
    three = module.role_prefix_metrics(outputs, "review_context", 3)
    five = module.role_prefix_metrics(outputs, "review_context", 5)
    assert three["report_exact_agreement"] is True
    assert five["report_exact_agreement"] is False
    assert five["field_agreement"]["aging_role"]["rate"] == 1
    assert five["field_agreement"]["multiomics_role"]["rate"] == 0
