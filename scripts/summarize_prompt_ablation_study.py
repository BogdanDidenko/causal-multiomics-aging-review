#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis/prompt_ablation_study_2026-08-02"
TRAJECTORY = (
    (
        "development_v1.1.0",
        ROOT / "analysis/prompt_ablation_v1.1.0/development/summary.json",
        ("A0", "M", "D", "M+D"),
    ),
    (
        "development_v1.2.0",
        ROOT / "analysis/prompt_ablation_v1.2.0/development/summary.json",
        ("A0", "S", "C", "S+C"),
    ),
    (
        "development_v1.3.0",
        ROOT / "analysis/prompt_ablation_v1.3.0/development/summary.json",
        ("S+C", "T+C"),
    ),
    (
        "development_v1.3.1",
        ROOT / "analysis/prompt_ablation_v1.3.1/development/summary.json",
        ("T+C", "R+C"),
    ),
    (
        "sealed_holdout_v1.4.0-rc1",
        ROOT / "analysis/prompt_ablation_v1.4.0-rc1/sealed_holdout/summary.json",
        ("A0", "RC1"),
    ),
)
RUN_GROUPS = (
    (
        "development_v1.1.0",
        ROOT / "data/screening/prompt_ablation_v1.1.0/development/roles",
        ("scope_A0", "scope_M", "causal_A0", "causal_D"),
    ),
    (
        "development_v1.2.0",
        ROOT / "data/screening/prompt_ablation_v1.2.0/development/roles",
        ("scope_S", "causal_C"),
    ),
    (
        "development_v1.3.0",
        ROOT / "data/screening/prompt_ablation_v1.3.0/development/roles",
        ("scope_T",),
    ),
    (
        "development_v1.3.1",
        ROOT / "data/screening/prompt_ablation_v1.3.1/development/roles",
        ("scope_R",),
    ),
    (
        "sealed_holdout_v1.4.0-rc1",
        ROOT / "data/screening/prompt_ablation_v1.4.0-rc1/sealed_holdout/roles",
        ("scope_A0", "causal_A0", "scope_RC1", "causal_RC1"),
    ),
)
ROLE_FIELDS = {
    "scope_RC1": (
        "report_type",
        "bio_health_scope",
        "aging_process_relevance",
        "multiomics_evidence",
        "current_report_layer_use",
    ),
    "causal_RC1": (
        "current_report_application",
        "causal_basis",
        "design_families",
        "causal_information_sufficiency",
    ),
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def trajectory_rows() -> list[dict[str, Any]]:
    rows = []
    for phase, path, arms in TRAJECTORY:
        report = load_json(path)
        baseline = report.get("baseline_arm", "A0")
        paired = report.get("paired_vs_baseline", report.get("paired_vs_A0", {}))
        for arm in arms:
            metrics = report["arms"][arm]
            comparison = paired.get(arm, {}).get("all_tracked_fields_exact", {})
            rows.append(
                {
                    "phase": phase,
                    "arm": arm,
                    "baseline_arm": baseline,
                    "records": report["records"],
                    "all_tracked_exact_n": metrics["all_tracked_fields_exact"]["successes"],
                    "all_tracked_exact_rate": metrics["all_tracked_fields_exact"]["rate"],
                    "all_tracked_wilson_low": metrics["all_tracked_fields_exact"]["low"],
                    "all_tracked_wilson_high": metrics["all_tracked_fields_exact"]["high"],
                    "decision_fields_exact_rate": metrics["decision_driving_fields_exact"]["rate"],
                    "route_exact_rate": metrics["single_repeat_route_exact"]["rate"],
                    "valid_five_runs_rate": metrics["valid_five_runs"]["rate"],
                    "paired_gains": comparison.get("gains", ""),
                    "paired_losses": comparison.get("losses", ""),
                    "exact_mcnemar_p": comparison.get("exact_mcnemar_p_value", ""),
                }
            )
    return rows


def run_accounting_rows() -> list[dict[str, Any]]:
    rows = []
    for phase, root, artifacts in RUN_GROUPS:
        for artifact in artifacts:
            results = read_jsonl(root / artifact / "role_results.jsonl")
            raw = read_jsonl(root / artifact / "raw_provider_responses.jsonl")
            rows.append(
                {
                    "phase": phase,
                    "artifact": artifact,
                    "records": len(results),
                    "planned_repeat_responses": 5 * len(results),
                    "valid_repeat_responses": sum(
                        row["repeat_count_valid"] for row in results
                    ),
                    "provider_attempts": len(raw),
                    "error_attempts": sum(row["status"] == "error" for row in raw),
                    "records_manual_review": sum(
                        row["status"] != "ok" for row in results
                    ),
                }
            )
    return rows


def holdout_field_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = ROOT / "data/screening/prompt_ablation_v1.4.0-rc1/sealed_holdout/roles"
    rows = []
    taxonomy: dict[str, Any] = {}
    for artifact, fields in ROLE_FIELDS.items():
        results = read_jsonl(root / artifact / "role_results.jsonl")
        valid = [row for row in results if row["status"] == "ok"]
        role_taxonomy: dict[str, Any] = {
            "records": len(results),
            "valid_five_run_records": len(valid),
            "manual_review_records": len(results) - len(valid),
            "fields": {},
        }
        for field in fields:
            signatures: Counter[tuple[tuple[str, int], ...]] = Counter()
            stable = 0
            for result in valid:
                values = [json.dumps(run.get(field), sort_keys=True) for run in result["runs"]]
                counts = Counter(values)
                if len(counts) == 1:
                    stable += 1
                else:
                    signatures[tuple(sorted(counts.items()))] += 1
            rows.append(
                {
                    "artifact": artifact,
                    "field": field,
                    "stable_n": stable,
                    "assessed_n": len(valid),
                    "stable_rate": stable / len(valid) if valid else "",
                    "unstable_n": len(valid) - stable,
                }
            )
            role_taxonomy["fields"][field] = {
                "stable_n": stable,
                "assessed_n": len(valid),
                "unstable_n": len(valid) - stable,
                "value_count_signatures": [
                    {"signature": dict(signature), "records": count}
                    for signature, count in signatures.most_common()
                ],
            }
        taxonomy[artifact] = role_taxonomy
    return rows, taxonomy


def manuscript_text(summary: dict[str, Any]) -> str:
    development = summary["development_selected"]
    holdout = summary["sealed_holdout"]
    accounting = summary["run_accounting"]
    regression = summary["secondary_regression_test_120"]
    methods_1 = (
        "We evaluated repeated-run reproducibility of title/abstract screening "
        "with GPT 5.6 Terra Medium through Codex CLI "
        "(`reasoning.effort=medium`). Each role-record pair was classified five "
        "times under an unchanged JSON schema and one-retry policy. A "
        "deterministic, stratified 60-record development set and a disjoint "
        "60-record sealed holdout were sampled from the search frame after "
        "excluding all prior benchmark and canonical-candidate records. No "
        "expert-gold labels were used in this experiment; the estimand was "
        "reproducibility, not screening validity."
    )
    methods_2 = (
        "Prompt changes were evaluated as pre-specified ablations. Cycle "
        "v1.1.0 used a 2x2 design for a multi-omics decision procedure (`M`) "
        "and a singleton design anchor (`D`). Cycle v1.2.0 tested closed scope "
        "tables (`S`) and mutually exclusive causal-basis tables (`C`). Cycle "
        "v1.3.0 added analytic-role boundaries for aging terms (`T`). A final "
        "two-definition micro-ablation (`R`) was tested under an explicit stop "
        "rule. Every experiment definition and prompt was committed before its "
        "model runs. The selected `T+C` contract was materialized as "
        "`v1.4.0-rc1` and frozen before the holdout was opened."
    )
    methods_3 = (
        "The primary endpoint was the proportion of records with exact "
        "agreement across all five runs for every tracked field required by "
        "the pre-specified sequential routing path. Secondary endpoints were "
        "agreement for decision-driving fields excluding the descriptive "
        "design anchor, repeat-level route agreement, schema validity after "
        "retry, field-level agreement, paired gains and losses, exact McNemar "
        "tests, and Wilson 95% intervals. Any missing valid repeat counted as "
        "failure. The pre-specified acceptance threshold was 100%."
    )
    methods_4 = (
        f"Across all cycles, {accounting['planned_repeat_responses']} repeat "
        f"responses were planned and {accounting['provider_attempts']} provider "
        f"attempts were made, including {accounting['error_attempts']} "
        "validation or provider-error attempts. Raw responses, retries, prompt "
        "hashes, schema hashes, model/runtime metadata, and Git revisions were "
        "retained."
    )
    development_text = (
        "The v1.0.0 baseline achieved 36/60 exact records (60.0%). The first "
        "`M` and `D` factorial did not improve the primary endpoint. The `S+C` "
        "arm increased exact agreement to 52/60 (86.7%). The `T+C` arm "
        f"increased it further to {development['exact_n']}/60 "
        f"({100 * development['exact_rate']:.1f}%; Wilson 95% CI "
        f"{100 * development['wilson_low']:.1f}-"
        f"{100 * development['wilson_high']:.1f}) and was selected. The final "
        "`R+C` micro-ablation decreased exact agreement to 57/60 (95.0%) and "
        "was rejected, demonstrating that additional specification did not "
        "monotonically improve reproducibility."
    )
    holdout_text = (
        "On the one-shot sealed holdout, baseline exact agreement was "
        f"{holdout['baseline_exact_n']}/60 "
        f"({100 * holdout['baseline_exact_rate']:.1f}%). The frozen RC1 "
        f"achieved {holdout['rc1_exact_n']}/60 "
        f"({100 * holdout['rc1_exact_rate']:.1f}%; Wilson 95% CI "
        f"{100 * holdout['wilson_low']:.1f}-"
        f"{100 * holdout['wilson_high']:.1f}). Relative to baseline, RC1 "
        f"produced {holdout['paired_gains']} paired gains and "
        f"{holdout['paired_losses']} losses (exact McNemar "
        f"p={holdout['mcnemar_p']:.3g}). Decision-field exact agreement was "
        f"{100 * holdout['decision_rate']:.1f}% and repeat-level route "
        f"agreement was {100 * holdout['route_rate']:.1f}%."
    )
    disposition = (
        "RC1 therefore improved reproducibility substantially but failed the "
        "pre-specified 100% gate and was not activated. The sealed holdout will "
        "not be used for subsequent prompt tuning. These results do not "
        "establish sensitivity, specificity, or scientific validity against "
        "expert judgments; a separate expert-gold benchmark remains required."
    )
    regression_text = (
        "The established 120-record corpus was evaluated as a secondary "
        "regression test, not as production and not as an independent sealed "
        "holdout. Baseline exact agreement was "
        f"{regression['baseline_exact_n']}/120 "
        f"({100 * regression['baseline_exact_rate']:.1f}%), whereas frozen RC1 "
        f"achieved {regression['rc1_exact_n']}/120 "
        f"({100 * regression['rc1_exact_rate']:.1f}%; Wilson 95% CI "
        f"{100 * regression['wilson_low']:.1f}-"
        f"{100 * regression['wilson_high']:.1f}). There were "
        f"{regression['paired_gains']} paired gains and "
        f"{regression['paired_losses']} losses (exact McNemar "
        f"p={regression['mcnemar_p']:.3g}). Because this corpus had informed "
        "the initial instability diagnosis, these results are regression "
        "evidence only and do not override the sealed-holdout rejection."
    )
    return "\n\n".join(
        (
            "# Prompt ablation study: methods and results",
            "## Methods",
            methods_1,
            methods_2,
            methods_3,
            methods_4,
            "## Development results",
            development_text,
            "## Sealed-holdout results",
            holdout_text,
            disposition,
            "## Secondary 120-record regression test",
            regression_text,
        )
    ) + "\n"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    trajectory = trajectory_rows()
    accounting = run_accounting_rows()
    field_rows, taxonomy = holdout_field_rows()
    write_csv(OUTPUT / "ablation_trajectory.csv", trajectory)
    write_csv(OUTPUT / "run_accounting.csv", accounting)
    write_csv(OUTPUT / "holdout_field_stability.csv", field_rows)
    (OUTPUT / "holdout_disagreement_taxonomy.json").write_text(
        json.dumps(taxonomy, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    development_report = load_json(
        ROOT / "analysis/prompt_ablation_v1.3.0/development/summary.json"
    )
    holdout_report = load_json(
        ROOT
        / "analysis/prompt_ablation_v1.4.0-rc1/sealed_holdout/summary.json"
    )
    regression_report = load_json(
        ROOT
        / "analysis/prompt_ablation_v1.4.0-rc1/regression_test_120/comparison.json"
    )
    development = development_report["arms"]["T+C"]["all_tracked_fields_exact"]
    holdout_baseline = holdout_report["arms"]["A0"]["all_tracked_fields_exact"]
    holdout_rc1 = holdout_report["arms"]["RC1"]
    holdout_exact = holdout_rc1["all_tracked_fields_exact"]
    paired = holdout_report["paired_vs_baseline"]["RC1"][
        "all_tracked_fields_exact"
    ]
    summary = {
        "experiment": "title_abstract_prompt_ablation_study",
        "model": "gpt-5.6-terra",
        "reasoning_effort": "medium",
        "development_selected": {
            "arm": "T+C",
            "exact_n": development["successes"],
            "exact_rate": development["rate"],
            "wilson_low": development["low"],
            "wilson_high": development["high"],
        },
        "sealed_holdout": {
            "records": 60,
            "baseline_exact_n": holdout_baseline["successes"],
            "baseline_exact_rate": holdout_baseline["rate"],
            "rc1_exact_n": holdout_exact["successes"],
            "rc1_exact_rate": holdout_exact["rate"],
            "wilson_low": holdout_exact["low"],
            "wilson_high": holdout_exact["high"],
            "decision_rate": holdout_rc1["decision_driving_fields_exact"]["rate"],
            "route_rate": holdout_rc1["single_repeat_route_exact"]["rate"],
            "paired_gains": paired["gains"],
            "paired_losses": paired["losses"],
            "mcnemar_p": paired["exact_mcnemar_p_value"],
            "acceptance_100_percent_met": False,
            "disposition": "rejected_not_active",
        },
        "run_accounting": {
            "planned_repeat_responses": sum(
                row["planned_repeat_responses"] for row in accounting
            ),
            "valid_repeat_responses": sum(
                row["valid_repeat_responses"] for row in accounting
            ),
            "provider_attempts": sum(row["provider_attempts"] for row in accounting),
            "error_attempts": sum(row["error_attempts"] for row in accounting),
            "records_manual_review_across_artifacts": sum(
                row["records_manual_review"] for row in accounting
            ),
        },
        "secondary_regression_test_120": {
            "set_role": "secondary_regression_test_not_production",
            "independence": "previously_inspected_not_confirmatory",
            "baseline_exact_n": regression_report["baseline"]["successes"],
            "baseline_exact_rate": regression_report["baseline"]["rate"],
            "rc1_exact_n": regression_report["candidate"]["successes"],
            "rc1_exact_rate": regression_report["candidate"]["rate"],
            "wilson_low": regression_report["candidate"]["low"],
            "wilson_high": regression_report["candidate"]["high"],
            "paired_gains": regression_report["paired"]["gains"],
            "paired_losses": regression_report["paired"]["losses"],
            "mcnemar_p": regression_report["paired"]["exact_mcnemar_p"],
            "provider_attempts": (
                regression_report["candidate_provider_attempts"]["attempt_ok"]
                + regression_report["candidate_provider_attempts"]["attempt_error"]
            ),
            "valid_responses": regression_report["candidate_provider_attempts"][
                "attempt_ok"
            ],
            "error_attempts": regression_report["candidate_provider_attempts"][
                "attempt_error"
            ],
            "sealed_holdout_disposition_unchanged": "rejected_not_active",
            "tuning_permitted": False,
        },
        "validity_status": "not_assessed_no_expert_gold",
        "holdout_reuse_policy": "report_only_no_prompt_tuning",
    }
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUTPUT / "methods_results.md").write_text(
        manuscript_text(summary), encoding="utf-8"
    )
    print(
        f"development={100 * development['rate']:.1f}% "
        f"holdout={100 * holdout_exact['rate']:.1f}% "
        "disposition=rejected_not_active"
    )


if __name__ == "__main__":
    main()
