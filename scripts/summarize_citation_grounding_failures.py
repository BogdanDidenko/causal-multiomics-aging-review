#!/usr/bin/env python3
"""Summarize exact-quote grounding failures from frozen raw attempts."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for path in sorted(args.run_root.glob("runs/*/raw_provider_responses.jsonl")):
        rows.extend(
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )

    slots: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (str(row["record_id"]), str(row["role"]), int(row["repeat_index"]))
        slots[key].append(row)

    phrase = "Evidence quote is not an exact substring"
    citation_slots = {
        key: attempts
        for key, attempts in slots.items()
        if any(phrase in str(attempt.get("error", "")) for attempt in attempts)
    }
    unrecovered = {
        key: attempts
        for key, attempts in citation_slots.items()
        if not any(attempt.get("status") == "ok" for attempt in attempts)
    }
    status_counts = Counter(str(row.get("status")) for row in rows)
    citation_failed_attempts = sum(
        phrase in str(row.get("error", "")) for row in rows
    )
    records = {str(row["record_id"]) for row in rows}
    affected_records = {key[0] for key in citation_slots}
    unrecovered_records = {key[0] for key in unrecovered}

    def rate(numerator: int, denominator: int) -> float:
        return numerator / denominator if denominator else 0.0

    summary = {
        "raw_attempts": len(rows),
        "attempt_status_counts": dict(sorted(status_counts.items())),
        "logical_role_repeat_slots": len(slots),
        "records": len(records),
        "citation_failed_attempts": citation_failed_attempts,
        "citation_failed_attempt_rate": rate(citation_failed_attempts, len(rows)),
        "citation_affected_slots": len(citation_slots),
        "citation_affected_slot_rate": rate(len(citation_slots), len(slots)),
        "citation_slots_recovered_by_retry": len(citation_slots) - len(unrecovered),
        "citation_slot_retry_recovery_rate": rate(
            len(citation_slots) - len(unrecovered), len(citation_slots)
        ),
        "citation_slots_unrecovered": len(unrecovered),
        "citation_unrecovered_slot_rate": rate(len(unrecovered), len(slots)),
        "records_with_any_citation_failure": len(affected_records),
        "records_with_any_citation_failure_rate": rate(len(affected_records), len(records)),
        "records_with_unrecovered_citation_failure": len(unrecovered_records),
        "records_with_unrecovered_citation_failure_rate": rate(
            len(unrecovered_records), len(records)
        ),
        "unrecovered_slots": [
            {
                "record_id": key[0],
                "role": key[1],
                "repeat_index": key[2],
                "attempts": len(attempts),
                "route": "manual_review",
            }
            for key, attempts in sorted(unrecovered.items())
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
