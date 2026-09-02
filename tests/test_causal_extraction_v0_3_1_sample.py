from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/v0.3.1"
ANALYSIS = REPO / "analysis/causal_extraction/v0.3.1_development"


def test_sample_is_inherited_unchanged_from_v0_3_0() -> None:
    parent = json.loads(
        (REPO / "protocol/causal_extraction/v0.3.0/sample.json").read_text(
            encoding="utf-8"
        )
    )
    inherited = json.loads((SUITE / "sample.json").read_text(encoding="utf-8"))
    assert inherited["reports"] == parent["reports"]
    assert inherited["parent_sample"]["sample_id"] == parent["sample_id"]
    assert inherited["sampling_frame"] == parent["sampling_frame"]


def test_candidate_scaffold_has_complete_neutral_coverage() -> None:
    scaffold = json.loads(
        (SUITE / "candidate_scaffold.json").read_text(encoding="utf-8")
    )
    reference = json.loads(
        (ANALYSIS / "candidate_reference_key.json").read_text(encoding="utf-8")
    )
    prompt_candidates = [
        item for report in scaffold["reports"] for item in report["candidates"]
    ]
    key_candidates = [
        item for report in reference["reports"] for item in report["candidates"]
    ]
    assert len(prompt_candidates) == 45
    assert len(key_candidates) == 45
    assert len({item["candidate_id"] for item in prompt_candidates}) == 45
    assert {item["candidate_id"] for item in prompt_candidates} == {
        item["candidate_id"] for item in key_candidates
    }
    assert all(
        set(item)
        == {"candidate_id", "candidate_label", "candidate_evidence_atom_ids"}
        for item in prompt_candidates
    )
    assert sum(
        item["expected_qualification"] == "include" for item in key_candidates
    ) == 28
    assert sum(
        item["expected_qualification"] == "exclude" for item in key_candidates
    ) == 17
