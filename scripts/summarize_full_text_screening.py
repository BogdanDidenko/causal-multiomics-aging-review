#!/usr/bin/env python3
"""Create compact stability and PRISMA audits from full-text shard outputs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.grading import derive_evidence_level


def read_rows(paths: list[Path]) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def level_sequence(row: dict[str, Any]) -> list[int | None]:
    runs = row.get("role_runs", {})
    eligibility = runs.get("eligibility_reviewer", [])
    causal = runs.get("causal_evidence_reviewer", [])
    sequence: list[int | None] = []
    for left, right in zip(eligibility, causal, strict=False):
        grade = derive_evidence_level({**left, **right})
        sequence.append(grade[0] if grade else None)
    return sequence


def summarize(run_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    runs_root = run_root / "runs"
    results = read_rows(sorted(runs_root.glob("*/screening_results.jsonl")))
    attempts = read_rows(sorted(runs_root.glob("*/raw_provider_responses.jsonl")))
    field_counts: dict[str, Counter[str]] = defaultdict(Counter)
    ledger = []
    stable_levels: Counter[str] = Counter()
    for row in results:
        disagreements = []
        for role, fields in row.get("role_agreement", {}).items():
            for field, audit in fields.items():
                key = f"{role}.{field}"
                field_counts[key]["evaluated"] += 1
                if audit["unanimous"]:
                    field_counts[key]["unanimous"] += 1
                else:
                    disagreements.append(key)
        sequence = level_sequence(row)
        signature_exact = len(sequence) == 5 and len(set(sequence)) == 1
        level_exact = signature_exact and sequence[0] is not None
        stable_level = sequence[0] if level_exact else None
        stable_levels[str(stable_level) if level_exact else "unstable_or_unresolved"] += 1
        ledger.append(
            {
                "record_id": row["record_id"],
                "title": row.get("title", ""),
                "strict_final_decision": row["final_decision"],
                "manual_review_reason": row.get("manual_review_reason") or "",
                "strict_causal_evidence_level": row.get("causal_evidence_level"),
                "five_run_level_sequence": json.dumps(sequence),
                "five_run_level_signature_exact": signature_exact,
                "five_run_level_exact": level_exact,
                "five_run_stable_level": stable_level,
                "disagreement_fields": ";".join(sorted(disagreements)),
            }
        )
    repair_calls = [
        row
        for row in attempts
        if row.get("post_validation", {}).get("evidence_quote_repairs")
    ]
    summary = {
        "status": "complete_full_corpus_evaluation_pending_expert_gold",
        "records": len(results),
        "strict_decision_counts": dict(Counter(row["final_decision"] for row in results)),
        "manual_review_reason_counts": dict(
            Counter(
                row.get("manual_review_reason") or "none"
                for row in results
            )
        ),
        "strict_level_counts": dict(
            Counter(
                str(row["causal_evidence_level"])
                for row in results
                if row.get("causal_evidence_level") is not None
            )
        ),
        "five_run_level_exact_records": sum(
            row["five_run_level_exact"] for row in ledger
        ),
        "five_run_level_exact_rate": (
            sum(row["five_run_level_exact"] for row in ledger) / len(ledger)
            if ledger
            else 0
        ),
        "five_run_stable_level_counts": dict(stable_levels),
        "five_run_signature_exact_including_unresolved": sum(
            row["five_run_level_signature_exact"] for row in ledger
        ),
        "model_attempts": len(attempts),
        "successful_attempts": sum(row.get("status") == "ok" for row in attempts),
        "failed_attempts_before_retry_or_manual_review": sum(
            row.get("status") != "ok" for row in attempts
        ),
        "attempt_error_rate": (
            sum(row.get("status") != "ok" for row in attempts) / len(attempts)
            if attempts
            else 0
        ),
        "calls_with_deterministic_quote_repair": len(repair_calls),
        "deterministic_quote_repairs": sum(
            len(row["post_validation"]["evidence_quote_repairs"])
            for row in repair_calls
        ),
        "criterion_agreement": {
            key: {
                "evaluated_records": counts["evaluated"],
                "unanimous_records": counts["unanimous"],
                "unanimous_rate": counts["unanimous"] / counts["evaluated"],
            }
            for key, counts in sorted(field_counts.items())
        },
        "interpretation": (
            "Strict assessment requires unanimity on every configured decision field. "
            "Five-run level exactness is reported separately and does not override the "
            "frozen strict route. Outputs are not expert-gold validation."
        ),
    }
    return summary, sorted(ledger, key=lambda row: row["record_id"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    root = args.run_root.resolve()
    summary, ledger = summarize(root)
    summary_path = root / "stability_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    ledger_path = root / "stability_ledger.csv"
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ledger[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(ledger)
    prisma = {
        "stage": "full_text_screening",
        "run_status": summary["status"],
        "reports_assessed_by_model_pipeline": summary["records"],
        "reports_with_strict_unanimous_assessment": summary["strict_decision_counts"].get(
            "assessed", 0
        ),
        "reports_pending_human_adjudication": summary["strict_decision_counts"].get(
            "manual_review", 0
        ),
        "reports_excluded_after_full_text": None,
        "studies_included_in_synthesis": None,
        "note": (
            "Final PRISMA exclusion and inclusion counts remain unset until human "
            "adjudication and expert-gold validation."
        ),
    }
    (root / "prisma_full_text_screening.json").write_text(
        json.dumps(prisma, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
