#!/usr/bin/env python3
"""Compare first-three and first-five repeated title/abstract screening outputs.

The analysis is retrospective and uses only saved JSONL results. It is a
stability diagnostic, not an accuracy analysis or an estimate for seven runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.v1 import (
    CAUSAL_DECISION_FIELDS,
    SCOPE_DECISION_FIELDS,
    causal_status,
    derive_title_result,
    scope_status,
)

PathStatus = tuple[str, str]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def role_runs(row: dict[str, Any], role: str) -> list[dict[str, Any]]:
    runs = (row.get("role_runs") or {}).get(role) or []
    return runs if all(isinstance(item, dict) for item in runs) else []


def unanimous_path(
    runs: list[dict[str, Any]], classifier: Callable[[dict[str, Any]], PathStatus]
) -> PathStatus | None:
    paths = [classifier(run) for run in runs]
    return paths[0] if paths and len(set(paths)) == 1 else None


def exact_fields(runs: list[dict[str, Any]], fields: tuple[str, ...]) -> bool:
    return all(
        len({json.dumps(run.get(field), sort_keys=True) for run in runs}) == 1
        for field in fields
    )


def exclusion_summary(
    rows: list[dict[str, Any]],
    role: str,
    classifier: Callable[[dict[str, Any]], PathStatus],
) -> dict[str, Any]:
    first_three = Counter()
    first_five = Counter()
    early_not_sustained = Counter()
    complete = 0
    for row in rows:
        runs = role_runs(row, role)
        if len(runs) != 5:
            continue
        complete += 1
        path_three = unanimous_path(runs[:3], classifier)
        path_five = unanimous_path(runs, classifier)
        if path_three and path_three[0] == "exclude":
            first_three[path_three[1]] += 1
        if path_five and path_five[0] == "exclude":
            first_five[path_five[1]] += 1
        if path_three and path_three[0] == "exclude" and path_three != path_five:
            early_not_sustained[path_three[1]] += 1
    return {
        "records_with_five_completed_runs": complete,
        "first_three_unanimous_exclusions": dict(sorted(first_three.items())),
        "first_five_unanimous_exclusions": dict(sorted(first_five.items())),
        "first_three_exclusions_not_sustained_by_runs_four_and_five": dict(
            sorted(early_not_sustained.items())
        ),
        "first_three_exclusions_not_sustained_total": sum(early_not_sustained.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs_dir", type=Path)
    parser.add_argument("suite_config", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for shard in sorted(args.runs_dir.glob("shard_*")):
        rows.extend(read_jsonl(shard / "screening_results.jsonl"))

    scope_rows = [row for row in rows if len(role_runs(row, "scope_reviewer")) == 5]
    causal_rows = [
        row for row in rows if len(role_runs(row, "causal_method_reviewer")) == 5
    ]
    combined_three = sum(
        exact_fields(role_runs(row, "scope_reviewer")[:3], SCOPE_DECISION_FIELDS)
        and (
            not role_runs(row, "causal_method_reviewer")
            or exact_fields(
                role_runs(row, "causal_method_reviewer")[:3], CAUSAL_DECISION_FIELDS
            )
        )
        for row in scope_rows
    )
    combined_five = sum(
        exact_fields(role_runs(row, "scope_reviewer"), SCOPE_DECISION_FIELDS)
        and (
            not role_runs(row, "causal_method_reviewer")
            or exact_fields(
                role_runs(row, "causal_method_reviewer"), CAUSAL_DECISION_FIELDS
            )
        )
        for row in scope_rows
    )

    route_three = Counter()
    route_five = Counter()
    route_changes = Counter()
    for row in causal_rows:
        scope_runs = role_runs(row, "scope_reviewer")
        causal_runs = role_runs(row, "causal_method_reviewer")
        first_three = derive_title_result(scope_runs[:3], causal_runs[:3])
        first_five = derive_title_result(scope_runs, causal_runs)
        route_three_key = (
            first_three["final_decision"],
            first_three["final_exclusion_code"],
        )
        route_five_key = (
            first_five["final_decision"],
            first_five["final_exclusion_code"],
        )
        route_three["|".join(route_three_key)] += 1
        route_five["|".join(route_five_key)] += 1
        if route_three_key != route_five_key:
            route_changes["|".join(route_three_key) + " -> " + "|".join(route_five_key)] += 1

    scope = exclusion_summary(rows, "scope_reviewer", scope_status)
    causal = exclusion_summary(rows, "causal_method_reviewer", causal_status)
    report = {
        "status": "complete_saved_output_sensitivity_only",
        "model_calls": 0,
        "interpretation": (
            "Five was a frozen operational stability gate before the full-corpus run. "
            "This prefix comparison describes what extra runs four and five detected; "
            "it does not establish an optimal repeat count, assume independent calls, "
            "validate accuracy, or estimate a seven-run result."
        ),
        "frozen_configuration": {
            "suite_config": str(args.suite_config),
            "suite_config_sha256": sha256(args.suite_config),
            "configured_repeats": json.loads(args.suite_config.read_text(encoding="utf-8"))[
                "stability_policy"
            ]["repeats"],
        },
        "population": {
            "result_records": len(rows),
            "scope_completed_five_runs": len(scope_rows),
            "causal_completed_five_runs": len(causal_rows),
        },
        "all_tracked_field_stability": {
            "first_three_exact_records": combined_three,
            "first_three_exact_rate": combined_three / len(scope_rows),
            "first_five_exact_records": combined_five,
            "first_five_exact_rate": combined_five / len(scope_rows),
        },
        "scope_criterion_paths": scope,
        "causal_criterion_paths": causal,
        "causal_completed_route_comparison": {
            "first_three_route_counts": dict(sorted(route_three.items())),
            "first_five_route_counts": dict(sorted(route_five.items())),
            "route_changes_after_runs_four_and_five": dict(sorted(route_changes.items())),
            "route_changes_after_runs_four_and_five_total": sum(route_changes.values()),
        },
        "artifacts": {"runs_dir": str(args.runs_dir)},
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "repeat_count_sensitivity.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    scope_withdrawn = report["scope_criterion_paths"][
        "first_three_exclusions_not_sustained_total"
    ]
    causal_withdrawn = report["causal_criterion_paths"][
        "first_three_exclusions_not_sustained_total"
    ]
    stability = report["all_tracked_field_stability"]
    (args.output_dir / "README.md").write_text(
        "# Repeat-Count Sensitivity From Saved Outputs\n\n"
        "This retrospective prefix comparison makes **zero model calls**. Five runs "
        "were specified in the frozen suite before the corpus run; the analysis does "
        "not claim that five is mathematically optimal or estimate a seven-run result.\n\n"
        "Among 4,549 records with five completed scope runs, all-tracked agreement was "
        f"{stability['first_three_exact_records']}/4,549 "
        f"({stability['first_three_exact_rate']:.1%}) after the first three and "
        f"{stability['first_five_exact_records']}/4,549 "
        f"({stability['first_five_exact_rate']:.1%}) after all five. Runs four and "
        f"five prevented {scope_withdrawn} early unanimous scope exclusions and "
        f"{causal_withdrawn} early unanimous EC5 exclusions that would not have been "
        "unanimous across all five.\n\n"
        "The report is a stability diagnostic only. It does not establish accuracy, "
        "safety, false-exclusion risk, or independent Bernoulli trials.\n",
        encoding="utf-8",
    )
    print(json.dumps(report["all_tracked_field_stability"], sort_keys=True))
    print(json.dumps(report["scope_criterion_paths"], sort_keys=True))
    print(json.dumps(report["causal_criterion_paths"], sort_keys=True))


if __name__ == "__main__":
    main()
