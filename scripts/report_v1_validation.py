#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.benchmark import (
    FULL_TEXT_ACCEPTANCE,
    TITLE_ACCEPTANCE,
    acceptance_report,
    evaluate_full_text,
    evaluate_title,
)
from causal_multiomics_aging_review.validation import inter_rater_summary

TITLE_FIELDS = (
    "report_type",
    "bio_health_scope",
    "aging_process_relevance",
    "multiomics_evidence",
    "current_report_layer_use",
    "causal_basis",
    "primary_design_family",
    "expected_route",
    "first_failed_criterion",
)
FULL_TEXT_FIELDS = (
    "eligible",
    "aging_process_relevance",
    "multiomics_status",
    "identification_status",
    "primary_design_family",
    "causal_evidence_level",
    "final_study_label",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                rows[str(row["record_id"])] = row
    return rows


def internal_stability(predicted: dict[str, dict[str, Any]]) -> dict[str, Any]:
    fields = 0
    unanimous_fields = 0
    records_with_disagreement = []
    for identifier, row in predicted.items():
        record_unanimous = True
        for role in (row.get("role_agreement") or {}).values():
            if not isinstance(role, dict):
                continue
            for audit in role.values():
                if not isinstance(audit, dict) or not isinstance(
                    audit.get("unanimous"), bool
                ):
                    continue
                fields += 1
                unanimous_fields += int(audit["unanimous"])
                record_unanimous &= audit["unanimous"]
        if not record_unanimous:
            records_with_disagreement.append(identifier)
    return {
        "decision_fields": fields,
        "unanimous_decision_fields": unanimous_fields,
        "field_unanimity_rate": unanimous_fields / fields if fields else None,
        "records_with_five_run_disagreement": records_with_disagreement,
        "record_disagreement_count": len(records_with_disagreement),
    }


def require_complete_gold(
    rows: list[dict[str, str]], fields: tuple[str, ...]
) -> None:
    missing = [
        row.get("record_id", "")
        for row in rows
        if any(not row.get(f"adjudicated_{field}", "").strip() for field in fields)
    ]
    if missing:
        preview = ", ".join(missing[:5])
        raise SystemExit(
            f"Gold annotation is incomplete for {len(missing)} records: {preview}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report v1 expert agreement, model validity, stability, and overrides"
    )
    parser.add_argument("--stage", choices=("title_abstract", "full_text"), required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predicted", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    gold_rows = read_csv(args.gold)
    predicted = read_jsonl(args.predicted)
    fields = TITLE_FIELDS if args.stage == "title_abstract" else FULL_TEXT_FIELDS
    require_complete_gold(gold_rows, fields)
    expected: dict[str, dict[str, str]] = {}
    for row in gold_rows:
        identifier = row["record_id"]
        if args.stage == "title_abstract":
            expected[identifier] = {
                "expert_expected_decision": row["adjudicated_expected_route"],
                "expert_canonical_positive": row.get("canonical_positive", "no"),
            }
        else:
            expected[identifier] = {
                "expert_causal_evidence_level": row[
                    "adjudicated_causal_evidence_level"
                ],
                "expert_primary_design_family": row[
                    "adjudicated_primary_design_family"
                ],
            }

    if args.stage == "title_abstract":
        metrics = evaluate_title(expected, predicted)
        gates = acceptance_report(metrics, TITLE_ACCEPTANCE)
    else:
        metrics = evaluate_full_text(expected, predicted)
        gates = acceptance_report(metrics, FULL_TEXT_ACCEPTANCE)
    overrides = [
        {
            "record_id": row["record_id"],
            "reason": row.get("human_override_reason", ""),
        }
        for row in gold_rows
        if row.get("human_override_of_model", "").strip().lower()
        in {"1", "true", "yes"}
    ]
    report = {
        "stage": args.stage,
        "gold_records": len(gold_rows),
        "model_records": len(predicted),
        "inter_rater": inter_rater_summary(gold_rows, fields),
        "model_to_gold": metrics,
        "five_run_stability": internal_stability(predicted),
        "human_overrides": overrides,
        "human_override_count": len(overrides),
        "acceptance": gates,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(gates["overall"])


if __name__ == "__main__":
    main()
