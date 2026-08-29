import importlib.util
import json
import sys
from pathlib import Path

from causal_multiomics_aging_review.causal_extraction import (
    build_coverage_ledger,
    build_dense_batches,
    build_open_windows,
    classifier_decision_payload,
    codex_runtime_schema,
    freeze_candidates,
    select_stability_candidates,
    split_text_at_boundaries,
    token_count,
    validate_classifier_grounding,
)

REPO = Path(__file__).resolve().parents[1]
FREEZER_PATH = REPO / "scripts/freeze_causal_extraction_checkpoints.py"
SPEC = importlib.util.spec_from_file_location("checkpoint_freezer", FREEZER_PATH)
assert SPEC is not None and SPEC.loader is not None
FREEZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FREEZER)
RUNNER_PATH = REPO / "scripts/run_causal_extraction_checkpoint.py"
sys.path.insert(0, str(REPO))
RUNNER_SPEC = importlib.util.spec_from_file_location("checkpoint_runner", RUNNER_PATH)
assert RUNNER_SPEC is not None and RUNNER_SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(RUNNER_SPEC)
sys.modules[RUNNER_SPEC.name] = RUNNER
RUNNER_SPEC.loader.exec_module(RUNNER)


def sections() -> list[dict]:
    return [
        {
            "section_id": f"chunk:{index:04d}",
            "heading": "Results",
            "page_numbers": [index + 1],
            "source_order": index,
            "text": text,
        }
        for index, text in enumerate(
            [
                "Short introduction.",
                ("Treatment reduced senescence markers. " * 300).strip(),
                "No effect was observed for lifespan.",
            ]
        )
    ]


def test_token_split_is_lossless_and_bounded() -> None:
    text = ("First sentence. Second sentence with evidence.\n\n" * 500).strip()
    parts = split_text_at_boundaries(text, 128)
    assert "".join(parts) == text
    assert len(parts) > 1
    assert all(token_count(part) <= 128 for part in parts)


def test_open_and_dense_packaging_cover_every_section() -> None:
    source = sections()
    open_windows = build_open_windows(
        source, max_core_characters=2500, context_characters=400
    )
    dense_batches = build_dense_batches(
        source, max_chunk_tokens=64, max_batch_tokens=128
    )
    ledger = build_coverage_ledger(source, open_windows, dense_batches)
    assert ledger["coverage_complete"] is True
    assert ledger["missing_open_sections"] == []
    assert ledger["missing_dense_sections"] == []
    assert ledger["truncated_section_count"] == 0
    assert ledger["omitted_nonempty_section_count"] == 0


def test_exact_duplicate_nominations_are_collapsed_without_semantic_merge() -> None:
    report = {
        "record_id": "doi:10.1000/example",
        "document_id": "doi_example",
        "doi": "10.1000/example",
        "title": "Example",
        "sections": sections(),
    }
    candidate = {
        "candidate_local_id": "candidate_001",
        "current_report_attribution": "yes",
        "normalized_claim": "Treatment reduced senescence markers.",
        "exposure_or_intervention": "treatment",
        "exposure_operation": "administered",
        "comparator": "control",
        "outcome": "senescence markers",
        "population_or_model": "cells",
        "biological_system": "cell culture",
        "time_horizon": "",
        "split_note": "",
        "candidate_kind": "effect",
        "result_signal": "supports",
        "evidence_anchors": [
            {
                "section_id": "chunk:0001",
                "quote": "Treatment reduced senescence markers.",
                "support_role": "result",
            }
        ],
    }
    outputs = [
        {
            "stage": stage,
            "work_unit_id": f"{stage}-001",
            "candidates": [candidate],
            "evidence_atoms": [],
        }
        for stage in ("open_claim_discovery", "dense_claim_coverage")
    ]
    frozen, _ = freeze_candidates(report, outputs)
    assert len(frozen) == 1
    assert frozen[0]["exact_duplicate_nomination_count"] == 2
    assert frozen[0]["discovery_routes"] == [
        "dense_claim_coverage",
        "open_claim_discovery",
    ]


def test_decision_payload_excludes_ids_notes_and_provenance() -> None:
    response = {
        "report_id": "doi:10.1000/example",
        "candidate_ref": "candidate-001",
        "candidate_status": "valid_single_claim",
        "claim_records": [
            {
                "report_id": "doi:10.1000/example",
                "doi": "10.1000/example",
                "claim_id": "claim-001",
                "primary_design_or_method": "genetic_instrument",
                "field_anchors": {"method": []},
                "evidence_anchors": [],
                "reviewer_note": "Variable note",
            }
        ],
        "split_proposals": [],
        "duplicate_candidate_refs": [],
        "manual_review_reason": "",
        "reviewer_note": "Variable note",
        "status_evidence_anchors": [],
    }
    payload = classifier_decision_payload(response)
    claim = payload["claim_records"][0]
    assert claim == {"primary_design_or_method": "genetic_instrument"}


def test_two_sample_design_is_reproducible_and_disjoint() -> None:
    expected = FREEZER.build_design()
    path = (
        REPO
        / "protocol/causal_extraction/checkpoints/v0.1.0-rc1"
        / "two_sample_design.json"
    )
    assert json.loads(path.read_text()) == expected
    a = {report["doi"] for report in expected["checkpoints"]["A"]["reports"]}
    b = {report["doi"] for report in expected["checkpoints"]["B"]["reports"]}
    assert len(a) == len(b) == 15
    assert not a & b
    assert expected["sampling"]["independent_accuracy_claim_allowed"] is False
    assert set(expected["sampling"]["superseded_report_versions"]).isdisjoint(b)


def test_codex_schema_compilation_adds_const_type_and_removes_conditionals() -> None:
    source = {
        "type": "object",
        "properties": {"stage": {"const": "open"}},
        "allOf": [{"if": {}, "then": {}}],
        "uniqueItems": True,
    }
    compiled = codex_runtime_schema(source)
    assert compiled["properties"]["stage"] == {"const": "open", "type": "string"}
    assert "allOf" not in compiled
    assert "uniqueItems" not in compiled


def test_grounding_failure_resumes_at_second_attempt(tmp_path: Path) -> None:
    (tmp_path / "attempt-01").mkdir()
    (tmp_path / "terminal.json").write_text(
        json.dumps({"status": "grounding_failure", "attempts": 1})
    )
    runner = object.__new__(RUNNER.CheckpointRunner)
    runner.resume = True
    assert runner._attempt_is_reusable(tmp_path) is False
    assert runner._first_attempt(tmp_path) == 2


def test_valid_call_is_reusable(tmp_path: Path) -> None:
    (tmp_path / "terminal.json").write_text(json.dumps({"status": "ok"}))
    runner = object.__new__(RUNNER.CheckpointRunner)
    runner.resume = True
    assert runner._attempt_is_reusable(tmp_path) is True


def test_residual_grounding_failure_after_retry_is_reusable(tmp_path: Path) -> None:
    (tmp_path / "terminal.json").write_text(
        json.dumps({"status": "grounding_failure", "attempts": 2})
    )
    runner = object.__new__(RUNNER.CheckpointRunner)
    runner.resume = True
    assert runner._attempt_is_reusable(tmp_path) is True


def test_stability_sample_is_reproducible_and_route_balanced() -> None:
    candidates = [
        {
            "candidate_ref": f"candidate-{index:03d}",
            "discovery_routes": [route],
        }
        for index, route in enumerate(
            [
                "open_claim_discovery",
                "open_claim_discovery",
                "dense_claim_coverage",
                "dense_claim_coverage",
            ],
            start=1,
        )
    ]
    first = select_stability_candidates(candidates, limit=2, seed="fixed")
    second = select_stability_candidates(candidates, limit=2, seed="fixed")
    assert first == second
    assert len(first) == 2
    routes = {candidate["discovery_routes"][0] for candidate in first}
    assert routes == {"open_claim_discovery", "dense_claim_coverage"}


def test_classifier_field_anchors_are_section_ids() -> None:
    response = {
        "status_evidence_anchors": [],
        "claim_records": [
            {
                "field_anchors": {"primary_design_or_method": ["chunk:0001"]},
                "evidence_anchors": [
                    {
                        "section_id": "chunk:0001",
                        "quote": "randomized intervention",
                    }
                ],
            }
        ],
        "split_proposals": [],
    }
    packet = {
        "canonical_sections": [
            {"section_id": "chunk:0001", "text": "A randomized intervention."}
        ]
    }
    assert validate_classifier_grounding(response, packet) == []
