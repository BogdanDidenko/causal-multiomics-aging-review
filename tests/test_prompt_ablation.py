import csv
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "analyze_prompt_ablation",
    ROOT / "scripts/analyze_prompt_ablation.py",
)
assert SPEC and SPEC.loader
ANALYSIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYSIS)
evaluate_record = ANALYSIS.evaluate_record
exact_mcnemar = ANALYSIS.exact_mcnemar
select_arm = ANALYSIS.select_arm
ABLATION_ROOT = ROOT / "protocol/screening/ablations/v1.1.0"
SAMPLE_ROOT = ABLATION_ROOT / "samples"
BASELINE_PROMPT_ROOT = ROOT / "protocol/screening/prompts/title_abstract/v1.0.0"
ABLATION_PROMPT_ROOT = (
    ROOT / "protocol/screening/prompts/title_abstract/ablation_v1.1.0"
)


def scope_answer(**overrides):
    answer = {
        "report_type": "empirical_primary",
        "bio_health_scope": "yes",
        "aging_process_relevance": "yes",
        "multiomics_evidence": "two_or_more_layers",
        "current_report_layer_use": "yes",
    }
    answer.update(overrides)
    return answer


def causal_answer(**overrides):
    answer = {
        "current_report_application": "yes",
        "causal_basis": "named_causal_effect_design",
        "design_families": ["genetic_instrument"],
        "causal_information_sufficiency": "sufficient",
    }
    answer.update(overrides)
    return answer


def role_result(rows):
    return {
        "status": "ok",
        "runs": rows,
        "retry_success_count": 0,
    }


def test_ablation_changes_only_one_prompt_per_factor() -> None:
    experiment = json.loads((ABLATION_ROOT / "experiment.json").read_text())
    assert experiment["design"] == "2x2_factorial"
    assert experiment["arms"] == {
        "A0": {"scope": "baseline", "causal": "baseline"},
        "M": {"scope": "M", "causal": "baseline"},
        "D": {"scope": "baseline", "causal": "D"},
        "M+D": {"scope": "M", "causal": "D"},
    }
    assert experiment["factors"]["M"]["role"] == "scope_reviewer"
    assert experiment["factors"]["D"]["role"] == "causal_method_reviewer"
    assert (BASELINE_PROMPT_ROOT / "scope_reviewer.txt").read_text() != (
        ABLATION_PROMPT_ROOT / "M/scope_reviewer.txt"
    ).read_text()
    assert (BASELINE_PROMPT_ROOT / "causal_method_reviewer.txt").read_text() != (
        ABLATION_PROMPT_ROOT / "D/causal_method_reviewer.txt"
    ).read_text()


def test_second_cycle_is_predeclared_from_first_cycle_results() -> None:
    experiment = json.loads(
        (ROOT / "protocol/screening/ablations/v1.2.0/experiment.json").read_text()
    )
    assert experiment["parent_result_commit"] == "1701cc7"
    assert experiment["arms"] == {
        "A0": {"scope": "baseline", "causal": "baseline"},
        "S": {"scope": "S", "causal": "baseline"},
        "C": {"scope": "baseline", "causal": "C"},
        "S+C": {"scope": "S", "causal": "C"},
    }


def test_third_cycle_changes_only_residual_scope_contract() -> None:
    experiment = json.loads(
        (ROOT / "protocol/screening/ablations/v1.3.0/experiment.json").read_text()
    )
    assert experiment["parent_result_commit"] == "3a27309"
    assert experiment["reference_arm"] == "S+C"
    assert experiment["arms"] == {
        "S+C": {"scope": "S", "causal": "C"},
        "T+C": {"scope": "T", "causal": "C"},
    }


def test_final_micro_ablation_has_a_stop_rule() -> None:
    experiment = json.loads(
        (ROOT / "protocol/screening/ablations/v1.3.1/experiment.json").read_text()
    )
    assert experiment["parent_result_commit"] == "69b2a4d"
    assert experiment["reference_arm"] == "T+C"
    assert "No further development-set prompt tuning" in experiment["stop_rule"]
    assert len(experiment["factor"]["R"]["semantic_deltas"]) == 2


def test_release_candidate_keeps_acceptance_at_exact_agreement() -> None:
    suite = json.loads(
        (
            ROOT
            / "protocol/screening/configs/prompt_suite_v1.4.0-rc1.json"
        ).read_text()
    )
    assert suite["approval_status"] == "sealed_holdout_pending_not_active"
    assert suite["stability_policy"]["acceptance"][
        "all_tracked_criteria_exact_agreement"
    ] == 1.0
    assert suite["stages"]["title_abstract"]["decision_repeats"] == 5


def test_release_candidate_freeze_hashes_match() -> None:
    freeze = json.loads(
        (
            ROOT / "protocol/screening/ablations/v1.4.0-rc1/freeze.json"
        ).read_text()
    )
    assert freeze["sealed_holdout"]["status_at_freeze"] == "unopened"
    assert freeze["sealed_holdout"]["post_holdout_tuning_permitted"] is False
    for artifact in freeze["frozen_artifacts"].values():
        digest = hashlib.sha256((ROOT / artifact["path"]).read_bytes()).hexdigest()
        assert digest == artifact["sha256"]


def test_release_candidate_is_rejected_after_one_shot_holdout() -> None:
    evaluation = json.loads(
        (
            ROOT / "protocol/screening/ablations/v1.4.0-rc1/evaluation.json"
        ).read_text()
    )
    assert evaluation["frozen_commit"] == "d025544"
    assert evaluation["evaluation_phase"] == "one_shot_sealed_holdout"
    assert evaluation["holdout"]["rc1_all_tracked_exact_rate"] == 0.8
    assert evaluation["acceptance"]["passed"] is False
    assert evaluation["disposition"] == "rejected_not_active"
    assert evaluation["validity_status"] == "not_assessed_no_expert_gold"
    for name, artifact in evaluation["artifacts"].items():
        if name == "raw_runs":
            continue
        digest = hashlib.sha256((ROOT / artifact["path"]).read_bytes()).hexdigest()
        assert digest == artifact["sha256"]


def test_ablation_study_summary_accounts_for_every_planned_repeat() -> None:
    summary = json.loads(
        (
            ROOT / "analysis/prompt_ablation_study_2026-08-02/summary.json"
        ).read_text()
    )
    assert summary["run_accounting"]["planned_repeat_responses"] == 3600
    assert summary["run_accounting"]["valid_repeat_responses"] == 3594
    assert summary["sealed_holdout"]["disposition"] == "rejected_not_active"
    assert summary["holdout_reuse_policy"] == "report_only_no_prompt_tuning"


def test_ablation_sets_are_disjoint_and_prior_samples_are_excluded() -> None:
    manifest = json.loads((SAMPLE_ROOT / "manifest.json").read_text())
    with (SAMPLE_ROOT / "development_60.csv").open(newline="", encoding="utf-8") as handle:
        development = list(csv.DictReader(handle))
    with (SAMPLE_ROOT / "sealed_holdout_60.csv").open(newline="", encoding="utf-8") as handle:
        holdout = list(csv.DictReader(handle))
    assert len(development) == len(holdout) == 60
    assert not ({row["record_id"] for row in development} & {row["record_id"] for row in holdout})
    assert manifest["identity_overlap_count"] == 0
    assert manifest["sealed_holdout"]["status"] == "sealed_unopened_until_prompt_freeze"
    assert manifest["gold_labels"] == "none; stability experiment only"


def test_design_anchor_drift_is_descriptive_not_routing_drift() -> None:
    scope_runs = [scope_answer() for _ in range(5)]
    causal_runs = [causal_answer() for _ in range(5)]
    causal_runs[-1]["design_families"] = ["formal_mediation"]
    result = evaluate_record(
        "r1", role_result(scope_runs), role_result(causal_runs)
    )
    assert result["all_tracked_fields_exact"] is False
    assert result["decision_driving_fields_exact"] is True
    assert result["single_repeat_route_exact"] is True


def test_exact_mcnemar_and_selection_rule() -> None:
    assert exact_mcnemar(0, 0) == 1.0
    assert exact_mcnemar(5, 0) == 0.0625
    summaries = {}
    rates = {
        "A0": (0.70, 0.90, 0.90),
        "M": (0.75, 0.89, 0.95),
        "D": (0.80, 0.90, 0.90),
        "M+D": (0.85, 0.92, 0.95),
    }
    for arm, (all_tracked, decision, route) in rates.items():
        summaries[arm] = {
            "all_tracked_fields_exact": {"rate": all_tracked},
            "decision_driving_fields_exact": {"rate": decision},
            "single_repeat_route_exact": {"rate": route},
            "retry_success_count": 0,
        }
    assert select_arm(summaries) == "M+D"
