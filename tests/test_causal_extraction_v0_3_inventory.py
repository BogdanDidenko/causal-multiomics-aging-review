from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/validate_causal_extraction_v0_3_inventory.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_v0_3_inventory", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_inventory_matches_frozen_sample_and_atoms() -> None:
    module = load_validator()
    resolved, summary = module.validate_and_resolve()

    assert summary == {
        "reports": 12,
        "causal_analyses": 28,
        "excluded_candidates": 17,
        "evidence_references": 232,
    }
    assert resolved["provenance"]["v0_3_model_outputs_seen"] is False
    assert resolved["provenance"]["gold_standard_claim"] is False


def test_resolved_inventory_contains_exact_atom_text() -> None:
    module = load_validator()
    resolved, _ = module.validate_and_resolve()

    first = resolved["reports"][0]["causal_analyses"][0]
    method_atom = first["method_evidence_atom"]
    assert method_atom[0]["evidence_atom_id"].startswith("ea_")
    assert method_atom[0]["raw_text"]
    assert method_atom[0]["atom_sha256"]
