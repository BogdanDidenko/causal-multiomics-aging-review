from __future__ import annotations

import json
from pathlib import Path

from causal_multiomics_aging_review.causal_extraction import sha256_file

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/validation/v0.3.1-independent-15-v1.0.0"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def prior_report_ids_and_dois() -> tuple[set[str], set[str]]:
    report_ids: set[str] = set()
    dois: set[str] = set()
    paths = (
        REPO / "protocol/causal_extraction/e0_grounding/v0.1.0/sample.json",
        REPO / "protocol/causal_extraction/checkpoints/v0.1.1-rc1/two_sample_design.json",
        REPO / "protocol/causal_extraction/v0.3.0/sample.json",
    )
    for path in paths:
        value = read_json(path)
        if "checkpoints" in value:
            reports = [
                report
                for checkpoint in value["checkpoints"].values()
                for report in checkpoint["reports"]
            ]
        else:
            reports = value["reports"]
        report_ids.update(str(report["report_id"]) for report in reports)
        dois.update(str(report["doi"]).casefold() for report in reports if report.get("doi"))
    return report_ids, dois


def test_validation_sample_is_unique_and_disjoint() -> None:
    sample = read_json(SUITE / "sample.json")
    reports = sample["reports"]
    report_ids = [report["report_id"] for report in reports]
    dois = [report["doi"].casefold() for report in reports]
    prior_ids, prior_dois = prior_report_ids_and_dois()

    assert len(reports) == 15
    assert len(set(report_ids)) == 15
    assert len(set(dois)) == 15
    assert not set(report_ids) & prior_ids
    assert not set(dois) & prior_dois
    assert sample["composition"] == {
        "disjoint_full_text_eligible_reports": 12,
        "targeted_search_frame_challenges": 3,
    }


def test_validation_packaging_is_complete_and_within_context() -> None:
    audit = read_json(SUITE / "phase1_packaging_audit.json")

    assert audit["report_count"] == 15
    assert audit["coverage_complete"] is True
    assert audit["omitted_report_atom_count"] == 0
    assert audit["model_selected_content"] is False
    assert audit["graph_selected_content"] is False
    assert audit["observed_max_rendered_prompt_tokens"] <= audit["max_rendered_prompt_tokens"]
    assert all(
        report["atom_count"] == report["serialized_atom_count"] for report in audit["reports"]
    )


def test_validation_freeze_hashes_all_artifacts() -> None:
    manifest_path = SUITE / "phase1_artifact_manifest.json"
    manifest = read_json(manifest_path)
    freeze = read_json(SUITE / "phase1_freeze.json")

    assert freeze["artifact_manifest_sha256"] == sha256_file(manifest_path)
    assert freeze["inherits_v0_3_1_without_modification"] is True
    for group in ("protocol_artifacts", "source_artifacts", "evidence_atom_indices"):
        for artifact in manifest[group]:
            path = REPO / artifact["path"]
            assert path.is_file()
            assert sha256_file(path) == artifact["sha256"]
