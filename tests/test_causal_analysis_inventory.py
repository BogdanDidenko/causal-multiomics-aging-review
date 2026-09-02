from __future__ import annotations

import json
from pathlib import Path

from causal_multiomics_aging_review.causal_analysis_inventory import (
    build_compact_report_packet,
    derive_causal_level,
    normalize_inventory,
    packet_atom_ids,
    validate_inventory_semantics,
)

REPO = Path(__file__).resolve().parents[1]
ATOM_INDEX = (
    REPO
    / "data/causal_extraction/v0.3.0_development/inputs/doi_4b54110a1a6ace81"
    / "evidence_atom_index.json"
)


def load_index() -> dict:
    return json.loads(ATOM_INDEX.read_text(encoding="utf-8"))


def valid_analysis() -> dict:
    return {
        "method_atom_id": "ea_bbcab105163b31eb6888976a",
        "result_atom_id": "ea_385bf91174e35a7be6e8c0f0",
        "validation_atom_ids": [],
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


def test_compact_packet_preserves_every_atom_in_order() -> None:
    index = load_index()
    packet = build_compact_report_packet(index)
    assert packet_atom_ids(packet) == [
        atom["evidence_atom_id"] for atom in index["atoms"]
    ]


def test_semantic_validation_and_normalization() -> None:
    index = load_index()
    response = {
        "report_id": index["report_id"],
        "source_status": "sufficient",
        "analyses": [valid_analysis()],
    }
    assert not validate_inventory_semantics(
        response, expected_report_id=index["report_id"], atom_index=index
    )
    normalized = normalize_inventory(response, index)
    assert normalized["analyses"][0]["python_derived_level"] == 3


def test_python_level_rules() -> None:
    analysis = valid_analysis()
    assert derive_causal_level(analysis) == 3
    analysis["validation_strength"] = "orthogonal_same_link"
    assert derive_causal_level(analysis) == 4
    analysis["causal_basis"] = "formal_directed_hypothesis"
    assert derive_causal_level(analysis) == 2
