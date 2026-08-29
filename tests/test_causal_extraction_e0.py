import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from causal_multiomics_aging_review.causal_extraction import sha256_file
from causal_multiomics_aging_review.evidence_atoms import (
    build_evidence_atom_index,
    build_evidence_atom_windows,
)

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/e0_grounding/v0.1.0"
SPEC = importlib.util.spec_from_file_location(
    "freeze_causal_extraction_e0", REPO / "scripts/freeze_causal_extraction_e0.py"
)
assert SPEC is not None and SPEC.loader is not None
freezer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freezer)
SUMMARY_SPEC = importlib.util.spec_from_file_location(
    "summarize_causal_extraction_e0",
    REPO / "scripts/summarize_causal_extraction_e0.py",
)
assert SUMMARY_SPEC is not None and SUMMARY_SPEC.loader is not None
summarizer = importlib.util.module_from_spec(SUMMARY_SPEC)
SUMMARY_SPEC.loader.exec_module(summarizer)


def load(relative: str) -> dict:
    return json.loads((SUITE / relative).read_text(encoding="utf-8"))


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


def test_sample_freeze_is_reproducible_and_development_only() -> None:
    sample = load("sample.json")
    assert sample == freezer.build_sample()
    assert len(sample["reports"]) == 6
    assert sample["sampling_frame"]["genuinely_sealed"] is False
    assert {item["evaluation_role"] for item in sample["reports"]} == {"development_only"}
    checkpoints = freezer.checkpoint_membership()
    assert {item["report_id"] for item in sample["reports"]}.isdisjoint(checkpoints)
    for tercile in (1, 2, 3):
        items = [item for item in sample["reports"] if item["document_size_tercile"] == tercile]
        assert len(items) == 2
        assert {item["table_density_role"] for item in items} == {
            "low_within_tercile",
            "high_within_tercile",
        }


def test_contamination_audit_covers_every_eligible_report() -> None:
    audit = load("contamination_audit.json")
    assert audit == freezer.exposure_audit()
    assert audit["eligible_reports"] == 101
    assert audit["reports_with_prior_luna_graph_profile"] == 101
    assert audit["reports_outside_checkpoints_a_b"] == 71
    assert audit["genuinely_sealed_internal_reports"] == 0


def test_frozen_artifact_manifest_resolves_exactly() -> None:
    freeze = load("freeze.json")
    manifest_path = SUITE / "artifact_manifest.json"
    assert freeze["artifact_manifest_sha256"] == sha256_file(manifest_path)
    manifest = load("artifact_manifest.json")
    for group in ("artifacts", "source_data"):
        for item in manifest[group]:
            path = REPO / item["path"]
            assert path.stat().st_size == item["bytes"]
            assert sha256_file(path) == item["sha256"]


def test_runtime_is_two_repeat_terra_medium_grounding_only() -> None:
    runtime = load("runtime.json")
    assert runtime["model"] == "gpt-5.6-terra"
    assert runtime["reasoning_effort"] == "medium"
    assert runtime["provider"] == "codex_cli"
    assert runtime["repeats_per_arm"] == 2
    assert runtime["technical_retry_limit"] == 1
    assert set(runtime["arms"]) == {"verbatim_quote", "evidence_atom_id"}
    assert runtime["packaging"]["section_omission_allowed"] is False
    assert runtime["packaging"]["relevance_ranking_allowed"] is False


def test_pre_model_packaging_calibration_is_reproducible() -> None:
    calibration = load("packaging_calibration.json")
    assert calibration == freezer.build_packaging_calibration()
    assert calibration["model_calls"] == 0
    assert calibration["selected_candidate_id"] == "bounded_24k_250_atoms"
    selected = next(
        item
        for item in calibration["candidates"]
        if item["candidate_id"] == calibration["selected_candidate_id"]
    )
    assert selected["planned_calls"] == 132
    assert selected["maximum_rendered_prompt_tokens"] <= 23000


def test_schemas_are_valid_and_do_not_assign_causal_levels() -> None:
    id_schema = load("schemas/inventory_evidence_atom_id.schema.json")
    quote_schema = load("schemas/inventory_verbatim_quote.schema.json")
    Draft202012Validator.check_schema(id_schema)
    Draft202012Validator.check_schema(quote_schema)
    prohibited = {
        "level",
        "causal_level",
        "causal_evidence_level",
        "identification_assessment",
        "risk_of_bias",
    }
    assert property_names(id_schema).isdisjoint(prohibited)
    assert property_names(quote_schema).isdisjoint(prohibited)
    assert id_schema["$defs"]["evidence_atom_id"]["type"] == "string"
    assert quote_schema["$defs"]["evidence_anchor"]["type"] == "object"


def test_actual_sample_has_complete_bounded_atom_windows() -> None:
    runtime = load("runtime.json")
    sample = load("sample.json")
    corpus = freezer.load_corpus()
    for item in sample["reports"]:
        index = build_evidence_atom_index(
            corpus[item["report_id"]],
            max_atom_characters=runtime["atomization"]["max_atom_characters"],
        )
        windows = build_evidence_atom_windows(
            index,
            max_core_characters=runtime["packaging"]["max_core_characters"],
            context_characters_per_side=runtime["packaging"]["context_characters_per_side"],
            max_core_atoms=runtime["packaging"]["max_core_atoms"],
            max_context_atoms_per_side=runtime["packaging"]["max_context_atoms_per_side"],
        )
        expected = {atom["evidence_atom_id"] for atom in index["atoms"]}
        observed = [atom_id for window in windows for atom_id in window["core_atom_ids"]]
        assert set(observed) == expected
        assert len(observed) == len(set(observed))
        assert max(window["core_character_count"] for window in windows) <= 30000
        assert max(window["core_atom_count"] for window in windows) <= 300


def test_prompt_template_has_only_declared_placeholders() -> None:
    template = (SUITE / "prompts/inventory_template.txt").read_text(encoding="utf-8")
    assert "{{GROUNDING_CONTRACT}}" in template
    assert "{{SECTION_INDEX_JSON}}" in template
    assert "{{EVIDENCE_ATOMS_JSON}}" in template
    assert "causal evidence Levels" in template
    id_contract = (SUITE / "prompts/grounding_evidence_atom_id.txt").read_text(encoding="utf-8")
    assert "Do not return quote text" in id_contract
    assert "Python will recover" in id_contract


def test_semantic_audit_uses_separate_blinded_reviewer_forms(tmp_path: Path) -> None:
    anchor = {
        "arm": "evidence_atom_id",
        "report_id": "doi:10.1000/test",
        "doi": "10.1000/test",
        "title": "Test report",
        "work_unit_id": "analysis-window-001",
        "repeat": 1,
        "analysis_index": 0,
        "anchor_index": 0,
        "evidence_role": "method_evidence",
        "analysis_basis": "effect_identification_design",
        "design_family": "targeted_genetic_perturbation",
        "method_name": "CRISPRi",
        "exposure_construct": "target knockdown",
        "outcome_construct": "senescence",
        "biological_system": "cells",
        "evidence_atom_id": "ea_" + "a" * 24,
        "section_id": "chunk:0001",
        "raw_start": 10,
        "raw_end": 28,
        "quote": "CRISPRi reduced X.",
        "quote_sha256": "b" * 64,
        "occurrence_id": "c" * 24,
    }
    audit = summarizer._write_audit_files(
        tmp_path,
        [anchor],
        [
            {
                "report_id": anchor["report_id"],
                "doi": anchor["doi"],
            }
        ],
    )
    assert len(audit["reviewer_forms"]) == 2
    for item in audit["reviewer_forms"]:
        header = Path(item["path"]).read_text(encoding="utf-8").splitlines()[0]
        assert "support_judgment" in header
        assert "arm" not in header
    key_header = Path(audit["key_path"]).read_text(encoding="utf-8").splitlines()[0]
    assert "arm" in key_header


def test_semantic_audit_selection_stratifies_by_report_arm_and_role() -> None:
    anchors = []
    for report in range(6):
        for arm in ("verbatim_quote", "evidence_atom_id"):
            for role in ("method_evidence", "result_evidence"):
                for occurrence in range(3):
                    anchors.append(
                        {
                            "arm": arm,
                            "report_id": f"report-{report}",
                            "evidence_role": role,
                            "evidence_atom_id": f"ea_{report:02d}{occurrence:02d}" + "a" * 20,
                            "quote_sha256": f"{report}{occurrence}" + "b" * 62,
                            "occurrence_id": f"{report}{occurrence}{arm}{role}",
                        }
                    )
    selected = summarizer._select_audit(anchors)
    assert len(selected) == 60
    assert {item["report_id"] for item in selected} == {f"report-{report}" for report in range(6)}
    assert {item["arm"] for item in selected} == {
        "verbatim_quote",
        "evidence_atom_id",
    }
    assert {item["evidence_role"] for item in selected} == {
        "method_evidence",
        "result_evidence",
    }
