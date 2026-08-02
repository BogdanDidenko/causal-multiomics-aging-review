#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.v1 import (
    CAUSAL_DECISION_FIELDS,
    SCOPE_DECISION_FIELDS,
    causal_status,
    derive_title_result,
    scope_status,
)

ARM_CYCLES = {
    "v1.1.0": {
        "A0": ("scope_A0", "causal_A0"),
        "M": ("scope_M", "causal_A0"),
        "D": ("scope_A0", "causal_D"),
        "M+D": ("scope_M", "causal_D"),
    },
    "v1.2.0": {
        "A0": ("scope_A0", "causal_A0"),
        "S": ("scope_S", "causal_A0"),
        "C": ("scope_A0", "causal_C"),
        "S+C": ("scope_S", "causal_C"),
    },
    "v1.3.0": {
        "S+C": ("scope_S", "causal_C"),
        "T+C": ("scope_T", "causal_C"),
    },
    "v1.3.1": {
        "T+C": ("scope_T", "causal_C"),
        "R+C": ("scope_R", "causal_C"),
    },
}
CYCLE_BASELINES = {
    "v1.1.0": "A0",
    "v1.2.0": "A0",
    "v1.3.0": "S+C",
    "v1.3.1": "T+C",
}
CAUSAL_ROUTING_FIELDS = tuple(
    field for field in CAUSAL_DECISION_FIELDS if field != "design_families"
)


def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                rows[str(row["record_id"])] = row
    return rows


def exact(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bool:
    if not rows:
        return False
    return all(
        len({json.dumps(row.get(field), sort_keys=True) for row in rows}) == 1
        for field in fields
    )


def single_run_route(
    scope: dict[str, Any], causal: dict[str, Any] | None
) -> tuple[str, str]:
    scope_route, scope_code = scope_status(scope)
    if scope_route == "exclude":
        return "exclude", scope_code
    if scope_route != "pass" or causal is None:
        return "seek_full_text", "none"
    causal_route, causal_code = causal_status(causal)
    if causal_route == "exclude":
        return "exclude", causal_code
    return "seek_full_text", "none"


def evaluate_record(
    identifier: str,
    scope_result: dict[str, Any],
    causal_result: dict[str, Any],
) -> dict[str, Any]:
    scope_runs = scope_result.get("runs", [])
    causal_runs = causal_result.get("runs", [])
    valid = (
        scope_result.get("status") == "ok"
        and causal_result.get("status") == "ok"
        and len(scope_runs) == 5
        and len(causal_runs) == 5
    )
    scope_exact = valid and exact(scope_runs, SCOPE_DECISION_FIELDS)
    causal_required = valid and all(
        scope_status(row)[0] == "pass" for row in scope_runs
    )
    causal_all_exact = valid and exact(causal_runs, CAUSAL_DECISION_FIELDS)
    causal_routing_exact = valid and exact(causal_runs, CAUSAL_ROUTING_FIELDS)
    all_tracked_exact = bool(
        scope_exact and (not causal_required or causal_all_exact)
    )
    decision_driving_exact = bool(
        scope_exact and (not causal_required or causal_routing_exact)
    )
    paired_routes = (
        [
            single_run_route(scope_runs[index], causal_runs[index])
            for index in range(5)
        ]
        if valid
        else []
    )
    route_exact = bool(
        paired_routes
        and len({json.dumps(value) for value in paired_routes}) == 1
    )
    if valid:
        decision = derive_title_result(
            scope_runs,
            causal_runs if causal_required else None,
        )
        final_decision = decision["final_decision"]
        exclusion_code = decision["final_exclusion_code"]
    else:
        final_decision = "manual_review"
        exclusion_code = "none"
    return {
        "record_id": identifier,
        "valid_five_runs": valid,
        "scope_all_tracked_exact": scope_exact,
        "causal_role_required": causal_required,
        "causal_all_tracked_exact": causal_all_exact,
        "causal_routing_fields_exact": causal_routing_exact,
        "all_tracked_fields_exact": all_tracked_exact,
        "decision_driving_fields_exact": decision_driving_exact,
        "single_repeat_route_exact": route_exact,
        "final_decision": final_decision,
        "final_exclusion_code": exclusion_code,
        "retry_success_count": scope_result.get("retry_success_count", 0)
        + causal_result.get("retry_success_count", 0),
    }


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> dict[str, Any]:
    if total == 0:
        return {"successes": successes, "total": total, "rate": None, "low": None, "high": None}
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(
        proportion * (1 - proportion) / total + z * z / (4 * total * total)
    ) / denominator
    return {
        "successes": successes,
        "total": total,
        "rate": proportion,
        "low": max(0.0, center - margin),
        "high": min(1.0, center + margin),
    }


def exact_mcnemar(gains: int, losses: int) -> float:
    discordant = gains + losses
    if discordant == 0:
        return 1.0
    lower = min(gains, losses)
    tail = sum(math.comb(discordant, k) for k in range(lower + 1)) / (2**discordant)
    return min(1.0, 2 * tail)


def summarize_arm(
    rows: list[dict[str, Any]],
    scope_results: dict[str, dict[str, Any]],
    causal_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    endpoints = (
        "valid_five_runs",
        "all_tracked_fields_exact",
        "decision_driving_fields_exact",
        "single_repeat_route_exact",
    )
    summary = {
        endpoint: wilson(sum(bool(row[endpoint]) for row in rows), len(rows))
        for endpoint in endpoints
    }
    summary["final_decisions"] = dict(
        sorted(Counter(row["final_decision"] for row in rows).items())
    )
    summary["retry_success_count"] = sum(row["retry_success_count"] for row in rows)
    summary["field_level"] = {}
    for field in SCOPE_DECISION_FIELDS:
        eligible = [result for result in scope_results.values() if result.get("status") == "ok"]
        successes = sum(exact(result["runs"], (field,)) for result in eligible)
        summary["field_level"][f"scope.{field}"] = wilson(successes, len(eligible))
    required_ids = {
        row["record_id"] for row in rows if row["causal_role_required"]
    }
    for field in CAUSAL_DECISION_FIELDS:
        eligible = [causal_results[identifier] for identifier in required_ids]
        successes = sum(exact(result["runs"], (field,)) for result in eligible)
        summary["field_level"][f"causal.{field}"] = wilson(successes, len(eligible))
    return summary


def paired_comparison(
    baseline: list[dict[str, Any]], variant: list[dict[str, Any]], endpoint: str
) -> dict[str, Any]:
    base = {row["record_id"]: bool(row[endpoint]) for row in baseline}
    candidate = {row["record_id"]: bool(row[endpoint]) for row in variant}
    gains = sum(not base[key] and candidate[key] for key in base)
    losses = sum(base[key] and not candidate[key] for key in base)
    return {
        "gains": gains,
        "losses": losses,
        "unchanged_success": sum(base[key] and candidate[key] for key in base),
        "unchanged_failure": sum(not base[key] and not candidate[key] for key in base),
        "exact_mcnemar_p_value": exact_mcnemar(gains, losses),
    }


def rate(summary: dict[str, Any], endpoint: str) -> float:
    return float(summary[endpoint]["rate"] or 0.0)


def select_arm(
    summaries: dict[str, dict[str, Any]],
    arms: dict[str, tuple[str, str]] | None = None,
    baseline_arm: str = "A0",
) -> str:
    arms = arms or ARM_CYCLES["v1.1.0"]
    baseline_decision = rate(
        summaries[baseline_arm], "decision_driving_fields_exact"
    )
    baseline_route = rate(summaries[baseline_arm], "single_repeat_route_exact")
    admissible = [
        arm
        for arm, summary in summaries.items()
        if rate(summary, "decision_driving_fields_exact") >= baseline_decision
        and rate(summary, "single_repeat_route_exact") >= baseline_route
    ]
    baseline_roles = arms[baseline_arm]
    change_count = {
        arm: sum(
            actual != baseline
            for actual, baseline in zip(roles, baseline_roles, strict=True)
        )
        for arm, roles in arms.items()
    }
    return max(
        admissible,
        key=lambda arm: (
            rate(summaries[arm], "all_tracked_fields_exact"),
            rate(summaries[arm], "decision_driving_fields_exact"),
            -summaries[arm]["retry_success_count"],
            -change_count[arm],
        ),
    )


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Title/abstract prompt ablation",
        "",
        f"Phase: `{report['phase']}`. Records: {report['records']}.",
        "",
        "This experiment measures repeated-run reproducibility. It does not "
        "establish model-to-expert validity.",
        "",
        "| Arm | All tracked exact | Decision fields exact | Route exact | Valid 5/5 |",
        "|---|---:|---:|---:|---:|",
    ]
    for arm, summary in report["arms"].items():
        values = []
        for endpoint in (
            "all_tracked_fields_exact",
            "decision_driving_fields_exact",
            "single_repeat_route_exact",
            "valid_five_runs",
        ):
            item = summary[endpoint]
            values.append(f"{item['successes']}/{item['total']} ({100 * item['rate']:.1f}%)")
        lines.append(f"| {arm} | " + " | ".join(values) + " |")
    lines.extend(("", "## Paired comparisons", ""))
    for arm, endpoints in report.get("paired_vs_baseline", {}).items():
        item = endpoints["all_tracked_fields_exact"]
        lines.append(
            f"- `{arm}` vs `{report['baseline_arm']}`: {item['gains']} gains, "
            f"{item['losses']} losses; "
            f"exact McNemar p={item['exact_mcnemar_p_value']:.4g}."
        )
    if report.get("selected_arm"):
        lines.extend(("", f"Development selection: `{report['selected_arm']}`."))
    lines.extend(
        (
            "",
            "Wilson 95% intervals, field-level estimates, retry counts, and "
            "record-level outcomes are stored in the JSON/CSV audit artifacts.",
            "",
        )
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a frozen prompt ablation")
    parser.add_argument("role_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--phase", choices=("development", "sealed_holdout", "transport"), required=True
    )
    parser.add_argument("--cycle", choices=sorted(ARM_CYCLES), default="v1.1.0")
    parser.add_argument("--selected-arm")
    parser.add_argument(
        "--baseline-role-root",
        type=Path,
        help="fallback directory for immutable role artifacts reused from a prior cycle",
    )
    args = parser.parse_args()

    arms = ARM_CYCLES[args.cycle]
    baseline_arm = CYCLE_BASELINES[args.cycle]
    if args.selected_arm and args.selected_arm not in arms:
        raise SystemExit(f"Unknown selected arm for {args.cycle}: {args.selected_arm}")
    arms_to_report = list(arms)
    if args.phase == "sealed_holdout":
        if not args.selected_arm:
            raise SystemExit("--selected-arm is required for sealed_holdout")
        arms_to_report = [baseline_arm]
        if args.selected_arm != baseline_arm:
            arms_to_report.append(args.selected_arm)
    required_artifacts = {
        artifact for arm in arms_to_report for artifact in arms[arm]
    }
    artifacts = {}
    for artifact in required_artifacts:
        path = args.role_root / artifact / "role_results.jsonl"
        if not path.is_file() and args.baseline_role_root:
            path = args.baseline_role_root / artifact / "role_results.jsonl"
        if not path.is_file():
            raise SystemExit(f"Missing role artifact: {artifact}")
        artifacts[artifact] = read_jsonl(path)
    identifier_sets = [set(rows) for rows in artifacts.values()]
    if not identifier_sets or any(items != identifier_sets[0] for items in identifier_sets[1:]):
        raise SystemExit("Role artifacts contain different record IDs")
    identifiers = sorted(identifier_sets[0])
    arm_rows: dict[str, list[dict[str, Any]]] = {}
    summaries = {}
    for arm in arms_to_report:
        scope_key, causal_key = arms[arm]
        rows = [
            evaluate_record(
                identifier,
                artifacts[scope_key][identifier],
                artifacts[causal_key][identifier],
            )
            for identifier in identifiers
        ]
        arm_rows[arm] = rows
        summaries[arm] = summarize_arm(
            rows, artifacts[scope_key], artifacts[causal_key]
        )

    paired = {}
    for arm in arms_to_report:
        if arm == baseline_arm:
            continue
        paired[arm] = {
            endpoint: paired_comparison(
                arm_rows[baseline_arm], arm_rows[arm], endpoint
            )
            for endpoint in (
                "all_tracked_fields_exact",
                "decision_driving_fields_exact",
                "single_repeat_route_exact",
            )
        }
    report: dict[str, Any] = {
        "experiment_id": f"title_abstract_prompt_ablation_{args.cycle}",
        "phase": args.phase,
        "records": len(identifiers),
        "baseline_arm": baseline_arm,
        "arms": summaries,
        "paired_vs_baseline": paired,
        "interpretation_constraint": "Reproducibility only; no expert-gold accuracy inference.",
    }
    if args.phase == "development":
        if len(arms) == 4 and baseline_arm == "A0":
            factor_1, factor_2 = [
                arm for arm in arms if arm != "A0" and "+" not in arm
            ]
            combined = next(arm for arm in arms if "+" in arm)
            report["factorial_effects"] = {
                f"{factor_1}_main_effect": (
                    rate(summaries[factor_1], "all_tracked_fields_exact")
                    + rate(summaries[combined], "all_tracked_fields_exact")
                    - rate(summaries["A0"], "all_tracked_fields_exact")
                    - rate(summaries[factor_2], "all_tracked_fields_exact")
                )
                / 2,
                f"{factor_2}_main_effect": (
                    rate(summaries[factor_2], "all_tracked_fields_exact")
                    + rate(summaries[combined], "all_tracked_fields_exact")
                    - rate(summaries["A0"], "all_tracked_fields_exact")
                    - rate(summaries[factor_1], "all_tracked_fields_exact")
                )
                / 2,
                "interaction": (
                    rate(summaries[combined], "all_tracked_fields_exact")
                    - rate(summaries[factor_1], "all_tracked_fields_exact")
                    - rate(summaries[factor_2], "all_tracked_fields_exact")
                    + rate(summaries["A0"], "all_tracked_fields_exact")
                ),
            }
        report["selected_arm"] = select_arm(summaries, arms, baseline_arm)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "report.md").write_text(markdown_report(report), encoding="utf-8")
    with (args.output_dir / "record_outcomes.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fieldnames = [
            "record_id",
            "arm",
            "valid_five_runs",
            "scope_all_tracked_exact",
            "causal_role_required",
            "causal_all_tracked_exact",
            "causal_routing_fields_exact",
            "all_tracked_fields_exact",
            "decision_driving_fields_exact",
            "single_repeat_route_exact",
            "final_decision",
            "final_exclusion_code",
            "retry_success_count",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for arm, rows in arm_rows.items():
            for row in rows:
                writer.writerow({"arm": arm, **row})
    print(
        " ".join(
            f"{arm}={100 * rate(summary, 'all_tracked_fields_exact'):.1f}%"
            for arm, summary in summaries.items()
        )
        + (f" selected={report['selected_arm']}" if report.get("selected_arm") else "")
    )


if __name__ == "__main__":
    main()
