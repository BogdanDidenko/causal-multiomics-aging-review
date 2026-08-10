#!/usr/bin/env python3
"""Audit the rejected v1.5.0 full-text routing against the fixed truth table."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.v1 import (
    derive_full_text_eligibility_route,
    scope_status,
)


def read_results(run_root: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for path in sorted((run_root / "runs").glob("*/screening_results.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def audit(run_root: Path, repeat_count: int = 5) -> dict[str, Any]:
    rows = read_results(run_root)
    original_counts = Counter(row["final_decision"] for row in rows)
    replay_counts: Counter[str] = Counter()
    changed_routes: list[dict[str, str]] = []
    missing_causal: list[str] = []

    for row in rows:
        role_runs = row.get("role_runs") or {}
        scope_runs = role_runs.get("scope_reviewer") or []
        causal_runs = role_runs.get("causal_method_reviewer") or []
        replay = derive_full_text_eligibility_route(
            scope_runs,
            causal_runs,
            repeat_count=repeat_count,
        )
        replay_counts[str(replay["final_decision"])] += 1
        if replay["final_decision"] != row["final_decision"]:
            changed_routes.append(
                {
                    "record_id": row["record_id"],
                    "original_decision": row["final_decision"],
                    "replayed_decision": str(replay["final_decision"]),
                    "original_reason": row.get("decision_reason", ""),
                    "replayed_reason": str(replay["decision_reason"]),
                }
            )
        if (
            len(scope_runs) == repeat_count
            and all(scope_status(answer)[0] == "pass" for answer in scope_runs)
            and not causal_runs
        ):
            missing_causal.append(row["record_id"])

    return {
        "status": "rejected_routing_implementation_audit",
        "source_run": str(run_root),
        "records": len(rows),
        "repeat_count": repeat_count,
        "original_decision_counts": dict(sorted(original_counts.items())),
        "corrected_route_replay_counts": dict(sorted(replay_counts.items())),
        "records_changed_by_route_replay": len(changed_routes),
        "route_changes": sorted(changed_routes, key=lambda row: row["record_id"]),
        "records_missing_causal_calls_after_five_scope_passes": len(missing_causal),
        "missing_causal_record_ids": sorted(missing_causal),
        "interpretation": (
            "Route replay reuses stored model outputs and changes no model judgment. "
            "Records missing causal calls remain unresolved and require a separately "
            "versioned recovery run."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repeat-count", type=int, default=5)
    args = parser.parse_args()
    result = audit(args.run_root, args.repeat_count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
