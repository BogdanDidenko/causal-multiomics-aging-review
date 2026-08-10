#!/usr/bin/env python3
"""Apply auditable human adjudications to a provisional eligibility ledger."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.audit import sha256_file


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    parser.add_argument("adjudications", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    with args.ledger.open(encoding="utf-8", newline="") as handle:
        ledger = list(csv.DictReader(handle))
    decisions = {row["record_id"]: row for row in read_jsonl(args.adjudications)}
    pending_ids = {
        row["record_id"] for row in ledger if row["final_decision"] == "manual_review"
    }
    if set(decisions) != pending_ids:
        raise SystemExit(
            "Adjudications must exactly cover pending records: "
            f"pending={sorted(pending_ids)}, supplied={sorted(decisions)}"
        )

    for row in ledger:
        decision = decisions.get(row["record_id"])
        row["adjudication_applied"] = "False"
        row["adjudication_status"] = ""
        if decision:
            row["model_final_decision"] = row["final_decision"]
            row["final_decision"] = decision["final_decision"]
            row["final_exclusion_code"] = decision["final_exclusion_code"]
            row["decision_reason"] = "manual_full_text_adjudication"
            row["adjudication_applied"] = "True"
            row["adjudication_status"] = decision["decision_status"]
        else:
            row["model_final_decision"] = row["final_decision"]

    counts = Counter(row["final_decision"] for row in ledger)
    exclusions = Counter(
        row["final_exclusion_code"]
        for row in ledger
        if row["final_decision"] == "exclude"
    )
    args.output.mkdir(parents=True, exist_ok=False)
    ledger_path = args.output / "eligibility_ledger_adjudicated.csv"
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ledger[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(ledger)

    summary = {
        "status": "complete_working_adjudication_pending_second_human_verification",
        "records": len(ledger),
        "decision_counts": dict(sorted(counts.items())),
        "exclusion_code_counts": dict(sorted(exclusions.items())),
        "adjudicated_records": len(decisions),
        "source_ledger": str(args.ledger),
        "source_ledger_sha256": sha256_file(args.ledger),
        "adjudications": str(args.adjudications),
        "adjudications_sha256": sha256_file(args.adjudications),
        "output_ledger_sha256": sha256_file(ledger_path),
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    prisma = {
        "stage": "full_text_eligibility_screening",
        "reports_assessed": len(ledger),
        "reports_meeting_eligibility": counts["assessed"],
        "reports_excluded": counts["exclude"],
        "reports_pending_adjudication": counts["manual_review"],
        "full_text_exclusion_reasons": dict(sorted(exclusions.items())),
        "status": "working_counts_pending_second_human_verification_and_expert_gold_validation",
    }
    (args.output / "prisma_working.json").write_text(
        json.dumps(prisma, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
