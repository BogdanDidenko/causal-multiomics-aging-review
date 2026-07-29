from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREENING = ROOT / "protocol" / "screening"
SUITE_PATH = SCREENING / "configs" / "prompt_suite_v0.96.0.json"
SUITE_V097_PATH = SCREENING / "configs" / "prompt_suite_v0.97.0.json"
SUITE_V098_PATH = SCREENING / "configs" / "prompt_suite_v0.98.0.json"
SUITE_V099_PATH = SCREENING / "configs" / "prompt_suite_v0.99.0.json"


def test_v096_contract_verifiers_are_independent_of_specialist_drafts() -> None:
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    title_stage = suite["stages"]["title_abstract"]

    assert (
        title_stage["contract_verification"]["verifier_context"]
        == "source_record_only_no_specialist_draft"
    )
    for role_config in title_stage["roles"].values():
        path = SCREENING / role_config["verification_prompt"]
        prompt = path.read_text(encoding="utf-8")
        assert "{{DRAFT_REVIEW}}" not in prompt
        assert "No specialist draft, previous classification" in prompt


def test_v097_consensus_uses_categorical_unclear_for_three_way_ties() -> None:
    suite = json.loads(SUITE_V097_PATH.read_text(encoding="utf-8"))
    verification = suite["stages"]["title_abstract"]["contract_verification"]

    assert verification["aggregation"] == "strict_field_majority_else_unclear"
    assert verification["unresolved_policy"] == "categorical_unclear"


def test_v098_applies_ellipsis_boundary_to_reviewers_and_adjudicator() -> None:
    suite = json.loads(SUITE_V098_PATH.read_text(encoding="utf-8"))
    title_stage = suite["stages"]["title_abstract"]
    paths = [
        title_stage["roles"]["scope_reviewer"]["prompt"],
        title_stage["roles"]["scope_reviewer"]["verification_prompt"],
        title_stage["roles"]["causal_design_reviewer"]["prompt"],
        title_stage["roles"]["causal_design_reviewer"]["verification_prompt"],
        title_stage["adjudication"]["prompt"],
    ]

    for relative_path in paths:
        prompt = (SCREENING / relative_path).read_text(encoding="utf-8")
        normalized = " ".join(prompt.casefold().split())
        assert "title words such as `exploring`" in normalized


def test_v099_requires_unanimity_for_exclusionary_consensus_values() -> None:
    suite = json.loads(SUITE_V099_PATH.read_text(encoding="utf-8"))
    verification = suite["stages"]["title_abstract"]["contract_verification"]

    assert verification["exclusionary_values_require_unanimity"] == [
        "no",
        "nonempirical",
    ]
