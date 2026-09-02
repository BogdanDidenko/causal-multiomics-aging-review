#!/usr/bin/env python3
"""Summarize role-level and composite stability for v0.3.2."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    read_json,
    sha256_text,
    write_json,
    write_text,
)
from causal_multiomics_aging_review.causal_role_classification import (
    ROLE_FIELDS,
    combine_role_outputs,
)

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/v0.3.2"
RAW = REPO / "data/causal_extraction/v0.3.2_development/terra_5repeat"
OUTPUT = REPO / "analysis/causal_extraction/v0.3.2_development/terra_5repeat"
REFERENCE = REPO / "analysis/causal_extraction/v0.3.1_development/candidate_reference_key.json"


def wilson_interval(successes: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total + z * z / (4 * total * total)
        )
        / denominator
    )
    return [center - margin, center + margin]


def normalized_hash(output: dict[str, Any]) -> str:
    return sha256_text(canonical_json(output))


def output_map(output: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["candidate_id"]: item for item in output["candidates"]}


def role_prefix_metrics(
    outputs: list[dict[str, Any]], role_id: str, repeat_count: int
) -> dict[str, Any]:
    prefix = outputs[:repeat_count]
    maps = [output_map(output) for output in prefix]
    candidate_ids = list(maps[0])
    fields = list(ROLE_FIELDS[role_id])
    if role_id == "eligibility":
        fields.extend(("python_qualification", "python_first_failed_condition"))
    exact_candidates = 0
    field_metrics = {
        field: {"unanimous_candidates": 0, "candidate_total": len(candidate_ids)}
        for field in fields
    }
    for candidate_id in candidate_ids:
        records = [mapping[candidate_id] for mapping in maps]
        compared = [
            {field: record[field] for field in fields} for record in records
        ]
        if len({canonical_json(record) for record in compared}) == 1:
            exact_candidates += 1
        for field in fields:
            if len({canonical_json(record[field]) for record in records}) == 1:
                field_metrics[field]["unanimous_candidates"] += 1
    for metrics in field_metrics.values():
        metrics["rate"] = (
            metrics["unanimous_candidates"] / metrics["candidate_total"]
        )
    hashes = [normalized_hash(output) for output in prefix]
    return {
        "repeat_count": repeat_count,
        "report_exact_agreement": len(set(hashes)) == 1,
        "distinct_normalized_outputs": len(set(hashes)),
        "candidate_total": len(candidate_ids),
        "all_field_exact_candidate_count": exact_candidates,
        "all_field_exact_candidate_rate": exact_candidates / len(candidate_ids),
        "field_agreement": field_metrics,
    }


def composite_prefix_metrics(
    outputs: list[dict[str, Any]], repeat_count: int
) -> dict[str, Any]:
    prefix = outputs[:repeat_count]
    maps = [output_map(output) for output in prefix]
    candidate_ids = list(maps[0])
    exact_candidates = 0
    qualification_exact = 0
    level_eligible = 0
    level_exact = 0
    for candidate_id in candidate_ids:
        records = [mapping[candidate_id] for mapping in maps]
        if len({canonical_json(record) for record in records}) == 1:
            exact_candidates += 1
        if len({record["python_qualification"] for record in records}) == 1:
            qualification_exact += 1
        if "python_derived_level" in records[0]:
            level_eligible += 1
            if len({record["python_derived_level"] for record in records}) == 1:
                level_exact += 1
    hashes = [normalized_hash(output) for output in prefix]
    return {
        "repeat_count": repeat_count,
        "report_exact_agreement": len(set(hashes)) == 1,
        "distinct_normalized_outputs": len(set(hashes)),
        "candidate_total": len(candidate_ids),
        "all_field_exact_candidate_count": exact_candidates,
        "all_field_exact_candidate_rate": exact_candidates / len(candidate_ids),
        "qualification_exact_count": qualification_exact,
        "qualification_exact_rate": qualification_exact / len(candidate_ids),
        "level_eligible_candidate_count": level_eligible,
        "level_exact_count": level_exact,
        "level_exact_rate": level_exact / level_eligible if level_eligible else None,
    }


def summarize(raw: Path) -> dict[str, Any]:
    sample = read_json(SUITE / "sample.json")
    runtime = read_json(SUITE / "runtime.json")
    scaffold = read_json(SUITE / runtime["candidate_scaffold"])
    scaffold_reports = {
        report["document_id"]: report for report in scaffold["reports"]
    }
    eligible = read_json(SUITE / runtime["eligible_candidate_set"])
    eligible_ids = {
        report["document_id"]: report["eligible_candidate_ids"]
        for report in eligible["reports"]
    }
    reference = read_json(REFERENCE)
    reference_maps = {
        report["document_id"]: {
            item["candidate_id"]: item["expected_qualification"]
            for item in report["candidates"]
        }
        for report in reference["reports"]
    }
    role_ids = [role["role_id"] for role in runtime["roles"]]
    valid_calls = 0
    reports = []
    confusion = {
        "reference_include": {"include": 0, "exclude": 0, "unclear": 0},
        "reference_exclude": {"include": 0, "exclude": 0, "unclear": 0},
    }
    for sampled in sample["reports"]:
        document_id = sampled["document_id"]
        role_outputs: dict[str, list[dict[str, Any]]] = {}
        missing: dict[str, list[int]] = {}
        for role_id in role_ids:
            outputs = []
            role_missing = []
            for repeat in range(1, int(runtime["repeats"]) + 1):
                path = (
                    raw
                    / "calls"
                    / role_id
                    / document_id
                    / f"repeat-{repeat:02d}"
                    / "normalized.json"
                )
                if path.is_file():
                    outputs.append(read_json(path))
                    valid_calls += 1
                else:
                    role_missing.append(repeat)
            role_outputs[role_id] = outputs
            if role_missing:
                missing[role_id] = role_missing
        report: dict[str, Any] = {
            "sample_order": sampled["sample_order"],
            "report_id": sampled["report_id"],
            "document_id": document_id,
            "doi": sampled["doi"],
            "missing_repeats": missing,
        }
        if not missing:
            report["roles"] = {}
            for role_id in role_ids:
                report["roles"][role_id] = {
                    "three_repeat": role_prefix_metrics(
                        role_outputs[role_id], role_id, 3
                    ),
                    "five_repeat": role_prefix_metrics(
                        role_outputs[role_id], role_id, 5
                    ),
                }
            composite = []
            for repeat_index in range(int(runtime["repeats"])):
                by_role = {
                    role_id: role_outputs[role_id][repeat_index]
                    for role_id in role_ids
                }
                combined = combine_role_outputs(
                    by_role,
                    all_candidate_report=scaffold_reports[document_id],
                    eligible_candidate_ids=eligible_ids[document_id],
                )
                composite.append(combined)
                for item in by_role["eligibility"]["candidates"]:
                    expected = reference_maps[document_id][item["candidate_id"]]
                    observed = item["python_qualification"]
                    confusion[f"reference_{expected}"][observed] += 1
            report["composite"] = {
                "three_repeat": composite_prefix_metrics(composite, 3),
                "five_repeat": composite_prefix_metrics(composite, 5),
            }
        reports.append(report)

    complete = [report for report in reports if not report["missing_repeats"]]
    summary: dict[str, Any] = {
        "experiment_id": runtime["experiment_id"],
        "development_only": True,
        "conditional_on_fixed_candidate_scaffold": True,
        "expert_gold_standard": False,
        "reference_status": "ai_assisted_analyst_draft_pending_human_verification",
        "planned_reports": len(sample["reports"]),
        "planned_calls": len(sample["reports"])
        * len(role_ids)
        * int(runtime["repeats"]),
        "valid_calls": valid_calls,
        "complete_reports": len(complete),
        "roles": {},
        "reports": reports,
    }
    for role_id in role_ids:
        summary["roles"][role_id] = {}
        for label in ("three_repeat", "five_repeat"):
            report_exact = sum(
                report["roles"][role_id][label]["report_exact_agreement"]
                for report in complete
            )
            candidate_total = sum(
                report["roles"][role_id][label]["candidate_total"]
                for report in complete
            )
            candidate_exact = sum(
                report["roles"][role_id][label]["all_field_exact_candidate_count"]
                for report in complete
            )
            summary["roles"][role_id][label] = {
                "report_exact_count": report_exact,
                "report_total": len(complete),
                "report_exact_rate": (
                    report_exact / len(complete) if complete else None
                ),
                "candidate_exact_count": candidate_exact,
                "candidate_total": candidate_total,
                "candidate_exact_rate": (
                    candidate_exact / candidate_total if candidate_total else None
                ),
            }
    summary["composite"] = {}
    for label in ("three_repeat", "five_repeat"):
        report_exact = sum(
            report["composite"][label]["report_exact_agreement"]
            for report in complete
        )
        candidate_total = sum(
            report["composite"][label]["candidate_total"] for report in complete
        )
        candidate_exact = sum(
            report["composite"][label]["all_field_exact_candidate_count"]
            for report in complete
        )
        qualification_exact = sum(
            report["composite"][label]["qualification_exact_count"]
            for report in complete
        )
        level_total = sum(
            report["composite"][label]["level_eligible_candidate_count"]
            for report in complete
        )
        level_exact = sum(
            report["composite"][label]["level_exact_count"]
            for report in complete
        )
        summary["composite"][label] = {
            "report_exact_count": report_exact,
            "report_total": len(complete),
            "report_exact_rate": report_exact / len(complete) if complete else None,
            "report_exact_wilson_95": wilson_interval(report_exact, len(complete)),
            "candidate_exact_count": candidate_exact,
            "candidate_total": candidate_total,
            "candidate_exact_rate": (
                candidate_exact / candidate_total if candidate_total else None
            ),
            "qualification_exact_count": qualification_exact,
            "qualification_exact_rate": qualification_exact / candidate_total,
            "level_exact_count": level_exact,
            "level_total": level_total,
            "level_exact_rate": level_exact / level_total if level_total else None,
            "passes_prespecified_gate": (
                report_exact == len(complete)
                and candidate_exact == candidate_total
                and qualification_exact == candidate_total
                and level_exact == level_total
            ),
        }
    expected_include = sum(confusion["reference_include"].values())
    expected_exclude = sum(confusion["reference_exclude"].values())
    summary["reference_alignment"] = {
        "confusion": confusion,
        "include_sensitivity": (
            confusion["reference_include"]["include"] / expected_include
            if expected_include
            else None
        ),
        "exclude_specificity": (
            confusion["reference_exclude"]["exclude"] / expected_exclude
            if expected_exclude
            else None
        ),
        "interpretation": "Development alignment only; this is not expert-gold accuracy.",
    }
    return summary


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Causal extraction v0.3.2 role-contract ablation",
        "",
        "Status: development-only; no expert-gold accuracy claim.",
        "",
        "## Completion",
        "",
        f"- Valid calls: {summary['valid_calls']}/{summary['planned_calls']}",
        f"- Complete reports: {summary['complete_reports']}/{summary['planned_reports']}",
        "",
        "## Role stability",
        "",
        "| Role | 3-run exact candidates | 5-run exact candidates | "
        "5-run exact reports |",
        "|---|---:|---:|---:|",
    ]
    for role_id, views in summary["roles"].items():
        three = views["three_repeat"]
        five = views["five_repeat"]
        lines.append(
            f"| `{role_id}` | {three['candidate_exact_count']}/"
            f"{three['candidate_total']} ({three['candidate_exact_rate']:.1%}) | "
            f"{five['candidate_exact_count']}/{five['candidate_total']} "
            f"({five['candidate_exact_rate']:.1%}) | "
            f"{five['report_exact_count']}/{five['report_total']} "
            f"({five['report_exact_rate']:.1%}) |"
        )
    lines.extend(
        [
            "",
            "## Composite stability",
            "",
            "| View | Exact reports | Exact candidates | Qualification exact | "
            "Level exact | Gate |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for label, display in (("three_repeat", "3 repeats"), ("five_repeat", "5 repeats")):
        item = summary["composite"][label]
        lines.append(
            f"| {display} | {item['report_exact_count']}/{item['report_total']} "
            f"({item['report_exact_rate']:.1%}) | "
            f"{item['candidate_exact_count']}/{item['candidate_total']} "
            f"({item['candidate_exact_rate']:.1%}) | "
            f"{item['qualification_exact_count']}/{item['candidate_total']} "
            f"({item['qualification_exact_rate']:.1%}) | "
            f"{item['level_exact_count']}/{item['level_total']} "
            f"({item['level_exact_rate']:.1%}) | "
            f"{'PASS' if item['passes_prespecified_gate'] else 'FAIL'} |"
        )
    reference = summary["reference_alignment"]
    lines.extend(
        [
            "",
            "## Provisional eligibility alignment",
            "",
            f"- Include sensitivity: {reference['include_sensitivity']:.1%}",
            f"- Exclude specificity: {reference['exclude_specificity']:.1%}",
            "- Reference: AI-assisted analyst draft pending human verification.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    summary = summarize(args.raw.resolve())
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "summary.json", summary)
    write_text(args.output / "report.md", markdown(summary))
    print(
        json.dumps(
            {
                "valid_calls": summary["valid_calls"],
                "five_repeat_candidate_exact": summary["composite"][
                    "five_repeat"
                ]["candidate_exact_rate"],
                "five_repeat_qualification_exact": summary["composite"][
                    "five_repeat"
                ]["qualification_exact_rate"],
                "five_repeat_level_exact": summary["composite"]["five_repeat"][
                    "level_exact_rate"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
