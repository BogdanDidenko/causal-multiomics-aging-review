#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

FINAL_FIELDS = (
    "assistant_final_status",
    "assistant_first_failed_criterion",
    "assistant_primary_design_family",
    "assistant_supporting_design_families",
    "assistant_eligibility_adjudication_mode",
    "assistant_design_adjudication_mode",
    "assistant_evidence_quote",
    "assistant_rationale",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge repeated-model labels and assistant adjudications"
    )
    parser.add_argument("preliminary", type=Path)
    parser.add_argument("source_records", type=Path)
    parser.add_argument("eligibility_adjudication", type=Path)
    parser.add_argument("design_adjudication", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("output_summary", type=Path)
    args = parser.parse_args()

    preliminary = read_csv(args.preliminary)
    sources = {row["record_id"]: row for row in read_csv(args.source_records)}
    eligibility = {
        row["record_id"]: row for row in read_csv(args.eligibility_adjudication)
    }
    design = {row["record_id"]: row for row in read_csv(args.design_adjudication)}
    review_required = {
        row["record_id"]
        for row in preliminary
        if row["ai_preliminary_status"]
        in {"preliminary_unclear", "preliminary_exclude"}
    }
    if set(eligibility) != review_required:
        raise SystemExit(
            "Eligibility adjudication coverage mismatch: "
            f"missing={sorted(review_required - set(eligibility))} "
            f"unexpected={sorted(set(eligibility) - review_required)}"
        )
    manually_included = {
        record_id
        for record_id, row in eligibility.items()
        if row["assistant_status"] == "include"
    }
    design_required = {
        row["record_id"]
        for row in preliminary
        if row["ai_preliminary_status"] == "preliminary_include"
        and row["design_families_consensus"] == "disagreement"
    } | manually_included
    if set(design) != design_required:
        raise SystemExit(
            "Design adjudication coverage mismatch: "
            f"missing={sorted(design_required - set(design))} "
            f"unexpected={sorted(set(design) - design_required)}"
        )

    for row in [*eligibility.values(), *design.values()]:
        source = sources[row["record_id"]]
        evidence = row["evidence_quote"]
        if evidence not in source["title"] and evidence not in source["abstract"]:
            raise SystemExit(f"Unsupported assistant quote: {row['record_id']}")

    output_rows = []
    for row in preliminary:
        record_id = row["record_id"]
        eligibility_review = eligibility.get(record_id)
        design_review = design.get(record_id)
        if eligibility_review:
            status = eligibility_review["assistant_status"]
            first_failed = eligibility_review["first_failed_criterion"]
            eligibility_mode = "assistant_full_abstract_review"
            evidence = eligibility_review["evidence_quote"]
            rationale = eligibility_review["rationale"]
        else:
            status = "include"
            first_failed = "none"
            eligibility_mode = "five_run_eligibility_consensus"
            evidence = ""
            rationale = "All eligibility criteria were unanimous across five runs."

        if design_review:
            primary_family = design_review["assistant_primary_design_family"]
            supporting_families = design_review["assistant_supporting_design_families"]
            design_mode = "assistant_full_abstract_review"
        elif status == "include" and row["design_families_consensus"] not in {
            "disagreement",
            "not_assessed",
            "",
        }:
            families = [
                family
                for family in row["design_families_consensus"].split(";")
                if family
            ]
            primary_family = families[0] if families else "unclear"
            supporting_families = ";".join(families[1:])
            design_mode = "five_run_consensus"
        else:
            primary_family = "unclear" if status != "exclude" else "not_assessed"
            supporting_families = ""
            design_mode = "pending_full_text" if status != "exclude" else "not_assessed"

        final = dict(row)
        final.update(
            {
                "assistant_final_status": status,
                "assistant_first_failed_criterion": first_failed,
                "assistant_primary_design_family": primary_family,
                "assistant_supporting_design_families": supporting_families,
                "assistant_eligibility_adjudication_mode": eligibility_mode,
                "assistant_design_adjudication_mode": design_mode,
                "assistant_evidence_quote": evidence,
                "assistant_rationale": rationale,
            }
        )
        output_rows.append(final)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [*preliminary[0], *FINAL_FIELDS]
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    included = [row for row in output_rows if row["assistant_final_status"] == "include"]
    summary = {
        "status": "assistant_annotation_complete_not_expert_gold",
        "records": len(output_rows),
        "final_status_counts": dict(
            sorted(Counter(row["assistant_final_status"] for row in output_rows).items())
        ),
        "first_failed_criterion_counts": dict(
            sorted(
                Counter(
                    row["assistant_first_failed_criterion"]
                    for row in output_rows
                    if row["assistant_first_failed_criterion"] != "none"
                ).items()
            )
        ),
        "included_primary_design_family_counts": dict(
            sorted(
                Counter(
                    row["assistant_primary_design_family"] for row in included
                ).items()
            )
        ),
        "assistant_eligibility_reviews": len(eligibility),
        "assistant_design_family_reviews": len(design),
        "preliminary_all_assessed_fields_5_of_5_count": sum(
            row["all_assessed_fields_5_of_5"] == "true" for row in preliminary
        ),
        "preliminary_all_assessed_fields_5_of_5_rate": sum(
            row["all_assessed_fields_5_of_5"] == "true" for row in preliminary
        )
        / len(preliminary),
        "inputs": {
            "preliminary": sha256(args.preliminary),
            "source_records": sha256(args.source_records),
            "eligibility_adjudication": sha256(args.eligibility_adjudication),
            "design_adjudication": sha256(args.design_adjudication),
        },
        "output": {"path": str(args.output_csv), "sha256": sha256(args.output_csv)},
        "gold_standard": False,
        "human_expert_status": "pending",
        "interpretation": (
            "This is a complete assistant annotation for prioritization. It does "
            "not replace two independent expert labels and does not satisfy the "
            "query-freeze gold-standard gate."
        ),
    }
    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"records={len(output_rows)} statuses={summary['final_status_counts']}")


if __name__ == "__main__":
    main()
