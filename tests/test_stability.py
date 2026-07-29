import json
import subprocess
import sys

from causal_multiomics_aging_review.audit import sha256_file
from causal_multiomics_aging_review.config import DEFAULT_SUITE_CONFIG, REPO_ROOT
from causal_multiomics_aging_review.stability import assess_stability

TITLE_ACCEPTANCE = {
    "schema_success_rate": 1.0,
    "final_decision_exact_agreement": 1.0,
    "decisive_criteria_exact_agreement": 1.0,
    "all_tracked_criteria_exact_agreement": 1.0,
    "causal_evidence_level_exact_agreement": 1.0,
    "manual_review_rate": 0.0,
}


def title_result(
    identification_status: str = "causal_candidate",
) -> dict[str, object]:
    return {
        "record_id": "r1",
        "final_decision": "seek_full_text",
        "final_exclusion_code": "none",
        "selected_criteria": {
            "report_type": "empirical_primary",
            "bio_health_scope": "yes",
            "aging_process_relevance": "yes",
            "multiomics_status": "yes",
            "omics_layers": [],
            "completed_current_report": "yes",
            "applied_design_signal": "yes",
            "directional_result_signal": "no",
            "identification_status": identification_status,
            "evidence_spans": [{"quote": "Different phrasing is ignored."}],
        },
    }


def test_stability_uses_decisive_criteria_not_free_text() -> None:
    runs = {f"replicate-{index}": {"r1": title_result()} for index in range(1, 6)}
    rows, summary = assess_stability(runs, "title_abstract", TITLE_ACCEPTANCE)
    assert rows[0]["stable"] is True
    assert summary["acceptance"]["overall"] == "pass"


def test_stability_localizes_disagreeing_criterion() -> None:
    runs = {f"replicate-{index}": {"r1": title_result()} for index in range(1, 6)}
    runs["replicate-5"] = {"r1": title_result("unclear")}
    rows, summary = assess_stability(runs, "title_abstract", TITLE_ACCEPTANCE)
    assert rows[0]["stable"] is False
    assert (
        "selected_criteria.identification_status"
        in rows[0]["decisive_disagreements"]
    )
    assert summary["acceptance"]["overall"] == "fail"


def test_stability_tracks_atomic_causal_signals() -> None:
    runs = {f"replicate-{index}": {"r1": title_result()} for index in range(1, 6)}
    runs["replicate-5"]["r1"]["selected_criteria"]["directional_result_signal"] = "yes"
    rows, summary = assess_stability(runs, "title_abstract", TITLE_ACCEPTANCE)
    assert rows[0]["stable"] is False
    assert (
        "selected_criteria.directional_result_signal"
        in rows[0]["decisive_disagreements"]
    )
    assert summary["acceptance"]["overall"] == "fail"


def test_stability_reports_raw_draft_drift_separately() -> None:
    runs = {f"replicate-{index}": {"r1": title_result()} for index in range(1, 6)}
    for result_by_id in runs.values():
        result_by_id["r1"]["draft_round_a"] = {
            "scope_reviewer": {
                "report_type": "empirical_primary",
                "bio_health_scope": "yes",
                "aging_process_relevance": "yes",
                "multiomics_status": "yes",
            },
            "causal_design_reviewer": {
                "completed_current_report": "yes",
                "genetic_instrument_signal": "yes",
                "manipulation_design_signal": "no",
                "directed_model_signal": "no",
            },
            "directional_result_reviewer": {
                "directional_language_signal": "no",
            },
        }
    runs["replicate-5"]["r1"]["draft_round_a"]["causal_design_reviewer"][
        "directed_model_signal"
    ] = "yes"

    rows, summary = assess_stability(runs, "title_abstract", TITLE_ACCEPTANCE)

    assert summary["acceptance"]["overall"] == "pass"
    assert summary["metrics"]["all_tracked_criteria_exact_agreement"] == 1.0
    assert summary["metrics"]["raw_reviewer_draft_exact_agreement"] == 0.0
    assert rows[0]["diagnostic_raw_reviewer_drafts_stable"] is False
    assert (
        "draft_round_a.causal_design_reviewer.directed_model_signal"
        in rows[0]["raw_reviewer_draft_disagreements"]
    )


def test_stability_reports_contract_verifier_field_unanimity() -> None:
    runs = {f"replicate-{index}": {"r1": title_result()} for index in range(1, 6)}
    for index, result_by_id in enumerate(runs.values(), start=1):
        result_by_id["r1"]["contract_consensus"] = {
            "scope_reviewer": {
                "fields": {
                    "report_type": {
                        "unanimous": index != 5,
                    }
                }
            }
        }

    _, summary = assess_stability(runs, "title_abstract", TITLE_ACCEPTANCE)

    assert summary["acceptance"]["overall"] == "pass"
    assert summary["metrics"]["contract_verifier_field_unanimity_rate"] == 0.8


def test_stability_ignores_downstream_fields_after_same_exclusion_path() -> None:
    runs = {}
    for index in range(1, 6):
        result = title_result()
        result["final_decision"] = "exclude"
        result["final_exclusion_code"] = "EC3"
        result["selected_criteria"]["aging_process_relevance"] = "no"
        result["selected_criteria"]["multiomics_status"] = (
            "yes" if index == 5 else "unclear"
        )
        runs[f"replicate-{index}"] = {"r1": result}
    rows, summary = assess_stability(runs, "title_abstract", TITLE_ACCEPTANCE)
    assert rows[0]["decisive_criteria_stable"] is True
    assert rows[0]["diagnostic_all_tracked_criteria_stable"] is False
    assert (
        "selected_criteria.multiomics_status"
        in rows[0]["diagnostic_disagreements"]
    )
    assert summary["acceptance"]["overall"] == "fail"


def test_stability_defers_exact_title_layer_inventory() -> None:
    runs = {f"replicate-{index}": {"r1": title_result()} for index in range(1, 6)}
    runs["replicate-5"]["r1"]["selected_criteria"]["omics_layers"] = [
        {"layer": "genomics", "raw_term": "genetic variants"}
    ]
    rows, summary = assess_stability(runs, "title_abstract", TITLE_ACCEPTANCE)
    assert rows[0]["stable"] is True
    assert rows[0]["diagnostic_all_tracked_criteria_stable"] is True
    assert summary["acceptance"]["overall"] == "pass"


def test_stability_cli_requires_matching_terra_manifests(tmp_path) -> None:
    run_args: list[str] = []
    for index in range(1, 6):
        run_dir = tmp_path / f"replicate-{index:02d}"
        run_dir.mkdir()
        result_path = run_dir / "screening_results.jsonl"
        result_path.write_text(json.dumps(title_result()) + "\n", encoding="utf-8")
        (run_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "model": "gpt-5.6-terra",
                    "suite_config_sha256": sha256_file(DEFAULT_SUITE_CONFIG),
                    "runtime": {
                        "api_protocol": "codex_cli",
                        "reasoning_effort": "medium",
                        "context_window": 32768,
                        "response_format": "json_schema",
                        "sandbox": "read-only",
                        "approval_policy": "never",
                        "ephemeral": True,
                        "ignore_user_config": True,
                        "ignore_rules": True,
                        "isolated_home": True,
                        "disabled_features": ["plugins"],
                        "codex_cli_version": "codex-cli 0.145.0",
                    },
                }
            ),
            encoding="utf-8",
        )
        run_args.extend(("--run", f"replicate-{index:02d}={result_path}"))
    output_dir = tmp_path / "assessment"
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "assess_screening_stability.py"),
            "--stage",
            "title_abstract",
            "--output-dir",
            str(output_dir),
            *run_args,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads((output_dir / "stability_summary.json").read_text())
    assert completed.stdout.strip() == "pass"
    assert summary["acceptance"]["overall"] == "pass"


def test_stability_cli_rejects_reasoning_effort_drift(tmp_path) -> None:
    run_args: list[str] = []
    for index in range(1, 6):
        run_dir = tmp_path / f"replicate-{index:02d}"
        run_dir.mkdir()
        result_path = run_dir / "screening_results.jsonl"
        result_path.write_text(json.dumps(title_result()) + "\n", encoding="utf-8")
        reasoning_effort = "high" if index == 5 else "medium"
        (run_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "model": "gpt-5.6-terra",
                    "suite_config_sha256": sha256_file(DEFAULT_SUITE_CONFIG),
                    "runtime": {
                        "api_protocol": "codex_cli",
                        "reasoning_effort": reasoning_effort,
                        "context_window": 32768,
                        "response_format": "json_schema",
                        "sandbox": "read-only",
                        "approval_policy": "never",
                        "ephemeral": True,
                        "ignore_user_config": True,
                        "ignore_rules": True,
                        "isolated_home": True,
                        "disabled_features": ["plugins"],
                        "codex_cli_version": "codex-cli 0.145.0",
                    },
                }
            ),
            encoding="utf-8",
        )
        run_args.extend(("--run", f"replicate-{index:02d}={result_path}"))

    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "assess_screening_stability.py"),
            "--stage",
            "title_abstract",
            "--output-dir",
            str(tmp_path / "assessment"),
            *run_args,
        ],
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "reasoning_effort='high'" in completed.stderr
