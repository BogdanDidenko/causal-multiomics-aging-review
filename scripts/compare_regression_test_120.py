#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["record_id"]: row for row in csv.DictReader(handle)}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> dict[str, Any]:
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare baseline and frozen-candidate stability on 120 records"
    )
    parser.add_argument("--baseline-csv", type=Path, required=True)
    parser.add_argument("--candidate-csv", type=Path, required=True)
    parser.add_argument("--baseline-summary", type=Path, required=True)
    parser.add_argument("--candidate-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    baseline = read_csv(args.baseline_csv)
    candidate = read_csv(args.candidate_csv)
    if set(baseline) != set(candidate):
        raise SystemExit("Baseline and candidate record IDs differ")
    identifiers = sorted(baseline)
    paired_rows = []
    for identifier in identifiers:
        baseline_stable = baseline[identifier]["all_assessed_fields_5_of_5"] == "true"
        candidate_stable = candidate[identifier]["all_assessed_fields_5_of_5"] == "true"
        disposition = (
            "gain"
            if not baseline_stable and candidate_stable
            else "loss"
            if baseline_stable and not candidate_stable
            else "stable_both"
            if baseline_stable
            else "unstable_both"
        )
        paired_rows.append(
            {
                "record_id": identifier,
                "baseline_stable": str(baseline_stable).lower(),
                "candidate_stable": str(candidate_stable).lower(),
                "paired_disposition": disposition,
                "baseline_preliminary_status": baseline[identifier][
                    "ai_preliminary_status"
                ],
                "candidate_preliminary_status": candidate[identifier][
                    "ai_preliminary_status"
                ],
                "baseline_model_route": baseline[identifier]["model_route"],
                "candidate_model_route": candidate[identifier]["model_route"],
            }
        )

    paired_counts = Counter(row["paired_disposition"] for row in paired_rows)
    baseline_summary = load_json(args.baseline_summary)
    candidate_summary = load_json(args.candidate_summary)
    field_rows = []
    for role in ("scope_reviewer", "causal_method_reviewer"):
        for field, candidate_metric in candidate_summary["field_stability"][role].items():
            baseline_metric = baseline_summary["field_stability"][role][field]
            field_rows.append(
                {
                    "role": role,
                    "field": field,
                    "baseline_assessed": baseline_metric["assessed"],
                    "baseline_exact": baseline_metric["exact_5_of_5"],
                    "baseline_rate": baseline_metric["rate"],
                    "candidate_assessed": candidate_metric["assessed"],
                    "candidate_exact": candidate_metric["exact_5_of_5"],
                    "candidate_rate": candidate_metric["rate"],
                    "rate_delta": candidate_metric["rate"] - baseline_metric["rate"],
                }
            )

    baseline_exact = baseline_summary["all_assessed_fields_5_of_5_count"]
    candidate_exact = candidate_summary["all_assessed_fields_5_of_5_count"]
    gains = paired_counts["gain"]
    losses = paired_counts["loss"]
    comparison = {
        "evaluation_id": "v1.4.0-rc1_secondary_regression_test_120",
        "set_role": "secondary_regression_test_not_production",
        "records": len(identifiers),
        "baseline": wilson(baseline_exact, len(identifiers)),
        "candidate": wilson(candidate_exact, len(identifiers)),
        "paired": {
            "gains": gains,
            "losses": losses,
            "stable_both": paired_counts["stable_both"],
            "unstable_both": paired_counts["unstable_both"],
            "exact_mcnemar_p": exact_mcnemar(gains, losses),
        },
        "baseline_status_counts": baseline_summary["preliminary_status_counts"],
        "candidate_status_counts": candidate_summary["preliminary_status_counts"],
        "candidate_provider_attempts": candidate_summary["provider_attempts"],
        "candidate_manual_review_count": sum(
            row["candidate_model_route"] == "manual_review" for row in paired_rows
        ),
        "sealed_holdout_disposition_unchanged": "rejected_not_active",
        "tuning_permitted": False,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (args.output_dir / "paired_outcomes.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(paired_rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(paired_rows)
    with (args.output_dir / "field_comparison.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(field_rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(field_rows)
    report = (
        "# Secondary 120-record regression test\n\n"
        "This corpus is a regression/test set, not a production corpus and not "
        "an independent sealed holdout. Its earlier baseline outputs informed "
        "the initial instability diagnosis.\n\n"
        f"Baseline exact agreement was {baseline_exact}/120 "
        f"({100 * comparison['baseline']['rate']:.1f}%). Frozen RC1 exact "
        f"agreement was {candidate_exact}/120 "
        f"({100 * comparison['candidate']['rate']:.1f}%; Wilson 95% CI "
        f"{100 * comparison['candidate']['low']:.1f}-"
        f"{100 * comparison['candidate']['high']:.1f}). The paired comparison "
        f"contained {gains} gains and {losses} losses (exact McNemar "
        f"p={comparison['paired']['exact_mcnemar_p']:.4g}).\n\n"
        "This secondary result does not override the failed sealed-holdout gate, "
        "does not activate RC1, and will not be used for prompt tuning.\n"
    )
    (args.output_dir / "report.md").write_text(report, encoding="utf-8")
    print(
        f"baseline={baseline_exact}/120 candidate={candidate_exact}/120 "
        f"gains={gains} losses={losses}"
    )


if __name__ == "__main__":
    main()
