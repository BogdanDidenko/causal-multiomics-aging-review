import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO_ROOT / "scripts/build_causal_extraction_methodology.py"
SPEC = importlib.util.spec_from_file_location(
    "causal_extraction_methodology_builder", BUILDER_PATH
)
assert SPEC is not None and SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)

PACKAGE = (
    REPO_ROOT / "protocol/causal_extraction/prompt_suite/v0.1.0-rc1"
)


def load(relative: str) -> dict:
    return json.loads((PACKAGE / relative).read_text())


def property_names(value: object) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict):
            names.update(properties)
        for child in value.values():
            names.update(property_names(child))
    elif isinstance(value, list):
        for child in value:
            names.update(property_names(child))
    return names


def test_frozen_package_is_fully_reproducible() -> None:
    assert BUILDER.validate_package() == []


def test_all_agent_roles_use_terra_medium() -> None:
    runtime = load("runtime.json")
    assert runtime["model"] == "gpt-5.6-terra"
    assert runtime["reasoning_effort"] == "medium"
    assert runtime["provider"] == "codex_cli"
    assert runtime["generation"]["technical_retry_limit"] == 1
    assert runtime["stages"]["fixed_candidate_classifier"]["repeats"] == 5
    assert runtime["stages"]["final_claim_adjudicator"]["repeats"] == 5
    assert runtime["decision_policy"]["majority_vote_allowed"] is False
    assert runtime["decision_policy"]["python_assigns_level"] is True
    assert runtime["decision_policy"]["model_assigns_level"] is False


def test_coverage_contract_prohibits_ranked_omission() -> None:
    coverage = load("coverage_contract.json")
    rules = coverage["global_rules"]
    assert rules["page_limit_allowed"] is False
    assert rules["relevance_ranking_allowed"] is False
    assert rules["graph_ranking_allowed"] is False
    assert rules["section_truncation_allowed"] is False
    assert rules["section_omission_allowed"] is False
    assertions = coverage["pre_classification_assertions"]
    assert assertions["canonical_section_coverage_ratio"] == 1.0
    assert assertions["open_core_coverage_ratio"] == 1.0
    assert assertions["dense_core_coverage_ratio"] == 1.0


def test_discovery_schema_accepts_grounded_empty_window() -> None:
    schema = load("schemas/open_claim_discovery.schema.json")
    instance = {
        "report_id": "10.1000/example",
        "document_sha256": "a" * 64,
        "stage": "open_claim_discovery",
        "work_unit_id": "window-001",
        "core_section_ids": ["sec-001"],
        "context_section_ids": [],
        "candidates": [],
        "evidence_atoms": [],
        "coverage_note": "No claim candidate in this window.",
    }
    assert list(Draft202012Validator(schema).iter_errors(instance)) == []


def test_fixed_classifier_requires_claim_for_valid_status() -> None:
    schema = load("schemas/fixed_candidate_classifier.schema.json")
    invalid = {
        "report_id": "10.1000/example",
        "candidate_ref": "cand-001",
        "candidate_status": "valid_single_claim",
        "status_evidence_anchors": [
            {
                "section_id": "sec-001",
                "quote": "Treatment reduced the measured outcome.",
                "support_role": "result",
            }
        ],
        "claim_records": [],
        "split_proposals": [],
        "duplicate_candidate_refs": [],
        "manual_review_reason": "",
        "reviewer_note": "",
    }
    assert list(Draft202012Validator(schema).iter_errors(invalid))


def test_model_output_schemas_cannot_contain_derived_level_fields() -> None:
    prohibited = {
        "level",
        "causal_level",
        "causal_evidence_level",
        "level4_validation_status",
    }
    for filename in (
        "open_claim_discovery.schema.json",
        "dense_claim_coverage.schema.json",
        "fixed_candidate_classifier.schema.json",
        "final_claim_adjudicator.schema.json",
    ):
        schema = load(f"schemas/{filename}")
        assert property_names(schema).isdisjoint(prohibited)


def test_stability_contract_covers_claim_decision_fields() -> None:
    stability = load("stability_contract.json")
    fields = set(stability["decision_driving_fields"])
    expected = {
        "claim_records[].primary_design_or_method",
        "claim_records[].variation_sources",
        "claim_records[].assignment_mechanism",
        "claim_records[].contrast_components",
        "claim_records[].assumption_judgments",
        "claim_records[].diagnostics",
        "claim_records[].reviewer_identification_assessment",
        "claim_records[].result_status",
        "claim_records[].validations",
    }
    assert expected <= fields
    assert stability["repeat_count"] == 5
    assert stability["majority_vote_allowed"] is False
    assert "causal_evidence_level" in stability["derived_outputs"]


def test_audit_contract_preserves_exact_rendered_prompts() -> None:
    contract = (PACKAGE / "run_artifact_contract.md").read_text()
    assert "rendered_prompt.txt" in contract
    assert "raw_provider_response.json" in contract
    assert "input_payload.sha256" in contract
    assert "candidate lacks a final disposition" in contract


def test_freeze_precedes_first_model_call() -> None:
    freeze = load("freeze.json")
    assert freeze["status"] == "frozen_before_first_terra_checkpoint"
    assert freeze["model_calls_before_freeze"] == 0
    assert freeze["first_checkpoint_report_count"] == 15


def test_checkpoint_is_fixed_and_not_mislabeled_as_independent_accuracy() -> None:
    checkpoint = load("checkpoint_inventory.json")
    assert checkpoint["report_count"] == 15
    assert len(checkpoint["reports"]) == 15
    assert checkpoint["selected_before_suite_terra_outputs"] is True
    assert checkpoint["prior_human_codebook_annotations_exist"] is True
    assert checkpoint["independent_accuracy_set"] is False
    assert len({report["doi"] for report in checkpoint["reports"]}) == 15
    for report in checkpoint["reports"]:
        assert len(report["canonical_docling_sha256"]) == 64
