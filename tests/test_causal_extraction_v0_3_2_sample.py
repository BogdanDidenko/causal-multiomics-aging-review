from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/v0.3.2"


def test_v0_3_2_inherits_reports_and_candidates() -> None:
    parent_sample = json.loads(
        (REPO / "protocol/causal_extraction/v0.3.1/sample.json").read_text(
            encoding="utf-8"
        )
    )
    sample = json.loads((SUITE / "sample.json").read_text(encoding="utf-8"))
    parent_scaffold = json.loads(
        (REPO / "protocol/causal_extraction/v0.3.1/candidate_scaffold.json").read_text(
            encoding="utf-8"
        )
    )
    scaffold = json.loads(
        (SUITE / "candidate_scaffold.json").read_text(encoding="utf-8")
    )
    assert sample["reports"] == parent_sample["reports"]
    assert scaffold == parent_scaffold


def test_detailed_role_set_contains_28_unanimous_candidates() -> None:
    selected = json.loads(
        (SUITE / "eligible_candidate_set.json").read_text(encoding="utf-8")
    )
    assert selected["report_count"] == 12
    assert selected["eligible_candidate_count"] == 28
    assert selected["majority_vote_used"] is False
    assert sum(
        len(report["eligible_candidate_ids"]) for report in selected["reports"]
    ) == 28
    assert all(len(report["parent_normalized_sha256"]) == 5 for report in selected["reports"])
