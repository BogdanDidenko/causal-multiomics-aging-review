#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.stability import assess_stability

ROOT = Path(__file__).resolve().parents[1]
STABILITY_ROOT = ROOT / "data" / "screening" / "stability"
OUTPUT_ROOT = ROOT / "analysis" / "prompt_calibration_effects"

RUN_SPECS = (
    {
        "phase": "preliminary_baseline",
        "suite_version": "0.95.0",
        "set_name": "new_development_baseline_10",
        "comparability_group": "preliminary_only",
        "directory": "development-v096-baseline-v0.95.0",
        "change": "Draft-conditioned contract verifiers; ten-record baseline.",
    },
    {
        "phase": "initial_focus",
        "suite_version": "0.96.0",
        "set_name": "new_development_focus_5",
        "comparability_group": "preliminary_only",
        "directory": "development-v096-focus5-v0.96.0",
        "change": "Contract verifiers receive the source record without the specialist draft.",
    },
    {
        "phase": "development",
        "suite_version": "0.96.0",
        "set_name": "independent_development_50",
        "comparability_group": "development_50",
        "directory": "development-full-50-v0.96.0",
        "change": "Source-only verifier architecture evaluated on the full development set.",
    },
    {
        "phase": "focused_iteration",
        "suite_version": "0.96.0",
        "set_name": "unstable_focus_6_derived",
        "comparability_group": "same_focus_6",
        "directory": "development-full-50-v0.96.0",
        "change": "Post hoc subset of the six records unstable under v0.96.0.",
        "derived_focus": True,
    },
    {
        "phase": "focused_iteration",
        "suite_version": "0.97.0",
        "set_name": "unstable_focus_6",
        "comparability_group": "same_focus_6",
        "directory": "development-v096-unstable6-v0.97.0",
        "change": (
            "Three-way categorical ties map to unclear; development-derived "
            "class boundaries were clarified."
        ),
    },
    {
        "phase": "focused_iteration",
        "suite_version": "0.98.0",
        "set_name": "unstable_focus_6",
        "comparability_group": "same_focus_6",
        "directory": "development-v096-unstable6-v0.98.0",
        "change": (
            "Ellipsis and current-report attribution rules were aligned across "
            "reviewers, verifiers, and adjudication."
        ),
    },
    {
        "phase": "focused_iteration",
        "suite_version": "0.99.0",
        "set_name": "unstable_focus_6",
        "comparability_group": "same_focus_6",
        "directory": "development-v096-unstable6-v0.99.0",
        "change": (
            "Exclusionary no and nonempirical verifier values require unanimity."
        ),
    },
    {
        "phase": "development_confirmation",
        "suite_version": "0.99.0",
        "set_name": "independent_development_50",
        "comparability_group": "development_50",
        "directory": "development-full-50-v0.99.0",
        "change": "Frozen candidate rerun on the complete development set.",
    },
    {
        "phase": "sealed_evaluation",
        "suite_version": "0.99.0",
        "set_name": "sealed_v8_25",
        "comparability_group": "sealed_evaluation",
        "directory": "sealed-v8-v0.99.0",
        "change": "One-time evaluation after candidate freeze commit d5646a9.",
    },
)

METRIC_FIELDS = (
    "schema_success_rate",
    "final_decision_exact_agreement",
    "decisive_criteria_exact_agreement",
    "all_tracked_criteria_exact_agreement",
    "raw_reviewer_draft_exact_agreement",
    "contract_verifier_field_unanimity_rate",
    "manual_review_rate",
)

UNCERTAINTY_SPECS = (
    {
        "suite_version": "0.99.0",
        "set_name": "independent_development_50",
        "evaluation_role": "development_confirmation",
        "directory": "development-full-50-v0.99.0",
    },
    {
        "suite_version": "0.99.0",
        "set_name": "sealed_v8_25",
        "evaluation_role": "one_time_sealed_evaluation",
        "directory": "sealed-v8-v0.99.0",
    },
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected object in {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_replicates(directory: Path) -> dict[str, dict[str, dict[str, Any]]]:
    runs: dict[str, dict[str, dict[str, Any]]] = {}
    for path in sorted(directory.glob("replicates/replicate-*/screening_results.jsonl")):
        rows = load_jsonl(path)
        runs[path.parent.name] = {str(row["record_id"]): row for row in rows}
    return runs


def derived_v096_focus() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    focus_path = (
        STABILITY_ROOT
        / "development-v096-unstable6-v0.97.0"
        / "stability_results.jsonl"
    )
    focus_ids = {str(row["record_id"]) for row in load_jsonl(focus_path)}
    full_runs = load_replicates(STABILITY_ROOT / "development-full-50-v0.96.0")
    subset_runs = {
        label: {record_id: row for record_id, row in rows.items() if record_id in focus_ids}
        for label, rows in full_runs.items()
    }
    return assess_stability(subset_runs, "title_abstract", {})


def metric_row(spec: dict[str, Any]) -> dict[str, Any]:
    directory = STABILITY_ROOT / str(spec["directory"])
    if spec.get("derived_focus"):
        stability_rows, summary = derived_v096_focus()
        result = "diagnostic_derived_subset"
    else:
        stability_rows = load_jsonl(directory / "stability_results.jsonl")
        summary = load_json(directory / "stability_summary.json")
        result = summary["acceptance"]["overall"]
    metrics = summary["metrics"]
    row = {
        key: spec[key]
        for key in (
            "phase",
            "suite_version",
            "set_name",
            "comparability_group",
            "change",
        )
    }
    row.update(
        {
            "record_count": summary["record_count"],
            "run_count": summary["run_count"],
            **{field: metrics[field] for field in METRIC_FIELDS},
            "unstable_record_count": sum(not item["stable"] for item in stability_rows),
            "final_route_unstable_record_count": sum(
                not item["final_decision_stable"] for item in stability_rows
            ),
            "acceptance_result": result,
            "artifact_directory": str(directory.relative_to(ROOT)),
        }
    )
    return row


def log_inventory() -> list[dict[str, Any]]:
    directories = sorted({str(spec["directory"]) for spec in RUN_SPECS})
    inventory = []
    for name in directories:
        directory = STABILITY_ROOT / name
        raw_paths = sorted(directory.glob("replicates/*/raw_provider_responses.jsonl"))
        result_paths = sorted(directory.glob("replicates/*/screening_results.jsonl"))
        manifest_paths = sorted(directory.glob("replicates/*/manifest.json"))
        all_paths = [path for path in directory.rglob("*") if path.is_file()]
        inventory.append(
            {
                "artifact_directory": str(directory.relative_to(ROOT)),
                "replicate_manifest_count": len(manifest_paths),
                "screening_outcome_count": sum(
                    len(load_jsonl(path)) for path in result_paths
                ),
                "raw_provider_response_count": sum(
                    len(load_jsonl(path)) for path in raw_paths
                ),
                "file_count": len(all_paths),
                "total_bytes": sum(path.stat().st_size for path in all_paths),
            }
        )
    return inventory


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def wilson_interval(
    event_count: int,
    observation_count: int,
    z: float = 1.959963984540054,
) -> tuple[float, float]:
    """Return a two-sided Wilson score interval for a binomial proportion."""
    if observation_count <= 0:
        raise ValueError("observation_count must be positive")
    if not 0 <= event_count <= observation_count:
        raise ValueError("event_count must be between zero and observation_count")
    proportion = event_count / observation_count
    z_squared = z**2
    denominator = 1 + z_squared / observation_count
    center = (proportion + z_squared / (2 * observation_count)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / observation_count
            + z_squared / (4 * observation_count**2)
        )
        / denominator
    )
    lower = 0.0 if event_count == 0 else max(0.0, center - margin)
    upper = 1.0 if event_count == observation_count else min(1.0, center + margin)
    return lower, upper


def uncertainty_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in UNCERTAINTY_SPECS:
        directory = STABILITY_ROOT / str(spec["directory"])
        stability_rows = load_jsonl(directory / "stability_results.jsonl")
        summary = load_json(directory / "stability_summary.json")
        record_count = int(summary["record_count"])
        outcome_count = record_count * int(summary["run_count"])
        measures = (
            (
                "final_route_instability",
                "record",
                sum(not row["final_decision_stable"] for row in stability_rows),
                record_count,
            ),
            (
                "decisive_criteria_instability",
                "record",
                sum(not row["decisive_criteria_stable"] for row in stability_rows),
                record_count,
            ),
            (
                "all_tracked_criteria_instability",
                "record",
                sum(
                    not row["diagnostic_all_tracked_criteria_stable"]
                    for row in stability_rows
                ),
                record_count,
            ),
            (
                "raw_specialist_draft_instability",
                "record",
                sum(
                    not row["diagnostic_raw_reviewer_drafts_stable"]
                    for row in stability_rows
                ),
                record_count,
            ),
            (
                "schema_failure",
                "record_run_outcome",
                round((1 - summary["metrics"]["schema_success_rate"]) * outcome_count),
                outcome_count,
            ),
            (
                "manual_review",
                "record_run_outcome",
                round(summary["metrics"]["manual_review_rate"] * outcome_count),
                outcome_count,
            ),
        )
        for measure, unit, event_count, observation_count in measures:
            ci_low, ci_high = wilson_interval(event_count, observation_count)
            rows.append(
                {
                    "suite_version": spec["suite_version"],
                    "set_name": spec["set_name"],
                    "evaluation_role": spec["evaluation_role"],
                    "measure": measure,
                    "unit": unit,
                    "event_count": event_count,
                    "observation_count": observation_count,
                    "observed_rate": event_count / observation_count,
                    "wilson_95_ci_low": ci_low,
                    "wilson_95_ci_high": ci_high,
                    "artifact_directory": str(directory.relative_to(ROOT)),
                }
            )
    return rows


def main() -> None:
    metric_rows = [metric_row(spec) for spec in RUN_SPECS]
    inventory_rows = log_inventory()
    interval_rows = uncertainty_rows()
    write_csv(OUTPUT_ROOT / "calibration_metrics.csv", metric_rows)
    write_csv(OUTPUT_ROOT / "log_inventory.csv", inventory_rows)
    write_csv(OUTPUT_ROOT / "reproducibility_uncertainty.csv", interval_rows)
    raw_response_count = sum(
        row["raw_provider_response_count"] for row in inventory_rows
    )
    print(
        "prompt_calibration_effects_ok "
        f"metric_rows={len(metric_rows)} "
        f"uncertainty_rows={len(interval_rows)} "
        f"screening_outcomes={sum(row['screening_outcome_count'] for row in inventory_rows)} "
        f"raw_provider_responses={raw_response_count}"
    )


if __name__ == "__main__":
    main()
