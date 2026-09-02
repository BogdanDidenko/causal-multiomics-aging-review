#!/usr/bin/env python3
"""Summarize the v0.3.1 fixed-candidate stability ablation."""

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

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/v0.3.1"
RAW = REPO / "data/causal_extraction/v0.3.1_development/terra_5repeat"
OUTPUT = REPO / "analysis/causal_extraction/v0.3.1_development/terra_5repeat"
REFERENCE = REPO / "analysis/causal_extraction/v0.3.1_development/candidate_reference_key.json"

MODEL_FIELDS = (
    "qualification",
    "first_failed_condition",
    "causal_basis",
    "design_family",
    "variation_source",
    "aging_role",
    "multiomics_role",
    "contrast_status",
    "assumptions_reviewability",
    "result_status",
    "validation_strength",
)


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


def candidate_map(output: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["candidate_id"]: item for item in output["candidates"]}


def prefix_metrics(outputs: list[dict[str, Any]], repeat_count: int) -> dict[str, Any]:
    prefix = outputs[:repeat_count]
    maps = [candidate_map(output) for output in prefix]
    candidate_ids = list(maps[0])
    qualification_exact = 0
    decision_path_exact = 0
    all_fields_exact = 0
    field_agreement = {
        field: {"unanimous_candidates": 0, "candidate_total": len(candidate_ids)}
        for field in (*MODEL_FIELDS, "python_derived_level")
    }
    for candidate_id in candidate_ids:
        records = [mapping[candidate_id] for mapping in maps]
        if len({item["qualification"] for item in records}) == 1:
            qualification_exact += 1
        paths = {
            canonical_json(
                {
                    "qualification": item["qualification"],
                    "first_failed_condition": item["first_failed_condition"],
                    "python_derived_level": item["python_derived_level"],
                }
            )
            for item in records
        }
        if len(paths) == 1:
            decision_path_exact += 1
        if len({canonical_json(item) for item in records}) == 1:
            all_fields_exact += 1
        for field in field_agreement:
            if len({canonical_json(item[field]) for item in records}) == 1:
                field_agreement[field]["unanimous_candidates"] += 1
    for field in field_agreement.values():
        field["rate"] = field["unanimous_candidates"] / len(candidate_ids)
    hashes = [normalized_hash(output) for output in prefix]
    return {
        "repeat_count": repeat_count,
        "report_exact_agreement": len(set(hashes)) == 1,
        "source_status_exact_agreement": len(
            {output["source_status"] for output in prefix}
        )
        == 1,
        "distinct_normalized_outputs": len(set(hashes)),
        "candidate_total": len(candidate_ids),
        "qualification_exact_count": qualification_exact,
        "decision_path_exact_count": decision_path_exact,
        "all_fields_exact_count": all_fields_exact,
        "included_counts": [
            sum(item["qualification"] == "include" for item in output["candidates"])
            for output in prefix
        ],
        "field_agreement": field_agreement,
    }


def summarize(raw: Path) -> dict[str, Any]:
    sample = read_json(SUITE / "sample.json")
    runtime = read_json(SUITE / "runtime.json")
    reference = read_json(REFERENCE)
    keys = {
        report["document_id"]: {
            item["candidate_id"]: item for item in report["candidates"]
        }
        for report in reference["reports"]
    }
    reports = []
    valid_calls = 0
    confusion = {
        "reference_include": {"include": 0, "exclude": 0, "unclear": 0},
        "reference_exclude": {"include": 0, "exclude": 0, "unclear": 0},
    }
    for sampled in sample["reports"]:
        document_id = sampled["document_id"]
        outputs = []
        missing = []
        for repeat in range(1, int(runtime["repeats"]) + 1):
            path = raw / "calls" / document_id / f"repeat-{repeat:02d}" / "normalized.json"
            if path.is_file():
                outputs.append(read_json(path))
                valid_calls += 1
            else:
                missing.append(repeat)
        report: dict[str, Any] = {
            "sample_order": sampled["sample_order"],
            "report_id": sampled["report_id"],
            "document_id": document_id,
            "doi": sampled["doi"],
            "valid_repeat_count": len(outputs),
            "missing_repeats": missing,
        }
        if not missing:
            report["three_repeat"] = prefix_metrics(outputs, 3)
            report["five_repeat"] = prefix_metrics(outputs, 5)
            report["reference_alignment_by_repeat"] = []
            for repeat, output in enumerate(outputs, start=1):
                matches = 0
                for item in output["candidates"]:
                    expected = keys[document_id][item["candidate_id"]][
                        "expected_qualification"
                    ]
                    confusion[f"reference_{expected}"][item["qualification"]] += 1
                    matches += item["qualification"] == expected
                report["reference_alignment_by_repeat"].append(
                    {
                        "repeat": repeat,
                        "matching_qualifications": matches,
                        "candidate_total": len(output["candidates"]),
                        "rate": matches / len(output["candidates"]),
                    }
                )
        reports.append(report)

    complete = [report for report in reports if not report["missing_repeats"]]
    summary: dict[str, Any] = {
        "experiment_id": runtime["experiment_id"],
        "development_only": True,
        "conditional_on_fixed_candidate_scaffold": True,
        "expert_gold_standard": False,
        "reference_status": "ai_assisted_analyst_draft_pending_human_verification",
        "planned_reports": len(sample["reports"]),
        "planned_calls": len(sample["reports"]) * int(runtime["repeats"]),
        "valid_calls": valid_calls,
        "complete_reports": len(complete),
        "reports": reports,
    }
    for label in ("three_repeat", "five_repeat"):
        report_exact = sum(report[label]["report_exact_agreement"] for report in complete)
        candidate_total = sum(report[label]["candidate_total"] for report in complete)
        qualification_exact = sum(
            report[label]["qualification_exact_count"] for report in complete
        )
        decision_path_exact = sum(
            report[label]["decision_path_exact_count"] for report in complete
        )
        all_fields_exact = sum(
            report[label]["all_fields_exact_count"] for report in complete
        )
        summary[label] = {
            "reports": len(complete),
            "report_exact_agreement_count": report_exact,
            "report_exact_agreement_rate": report_exact / len(complete) if complete else None,
            "report_exact_agreement_wilson_95": wilson_interval(
                report_exact, len(complete)
            ),
            "candidate_total": candidate_total,
            "qualification_exact_count": qualification_exact,
            "qualification_exact_rate": (
                qualification_exact / candidate_total if candidate_total else None
            ),
            "decision_path_exact_count": decision_path_exact,
            "decision_path_exact_rate": (
                decision_path_exact / candidate_total if candidate_total else None
            ),
            "all_fields_exact_count": all_fields_exact,
            "all_fields_exact_rate": (
                all_fields_exact / candidate_total if candidate_total else None
            ),
            "passes_prespecified_exact_agreement_gate": (
                report_exact == len(sample["reports"])
                and all_fields_exact == candidate_total
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
        "# Causal extraction v0.3.1 fixed-candidate ablation",
        "",
        "Status: development-only; conditional classification stability, "
        "no expert-gold accuracy claim.",
        "",
        "## Completion",
        "",
        f"- Valid calls: {summary['valid_calls']}/{summary['planned_calls']}",
        f"- Complete reports: {summary['complete_reports']}/{summary['planned_reports']}",
        "",
        "## Stability",
        "",
        "| View | Exact reports | Qualification-exact candidates | "
        "All-field-exact candidates | Gate |",
        "|---|---:|---:|---:|---|",
    ]
    for label, display in (("three_repeat", "3 repeats"), ("five_repeat", "5 repeats")):
        item = summary[label]
        lines.append(
            f"| {display} | {item['report_exact_agreement_count']}/{item['reports']} "
            f"({item['report_exact_agreement_rate']:.1%}) | "
            f"{item['qualification_exact_count']}/{item['candidate_total']} "
            f"({item['qualification_exact_rate']:.1%}) | "
            f"{item['all_fields_exact_count']}/{item['candidate_total']} "
            f"({item['all_fields_exact_rate']:.1%}) | "
            f"{'PASS' if item['passes_prespecified_exact_agreement_gate'] else 'FAIL'} |"
        )
    reference = summary["reference_alignment"]
    lines.extend(
        [
            "",
            "## Provisional reference alignment",
            "",
            f"- Include sensitivity: {reference['include_sensitivity']:.1%}",
            f"- Exclude specificity: {reference['exclude_specificity']:.1%}",
            "- Interpretation: comparison with an AI-assisted analyst draft, not expert gold.",
            "",
            "## Reports",
            "",
            "| DOI | 3-run exact | 5-run exact | Includes across five runs |",
            "|---|---|---|---|",
        ]
    )
    for report in summary["reports"]:
        if report["missing_repeats"]:
            lines.append(
                f"| {report['doi']} | incomplete | incomplete | "
                f"missing {report['missing_repeats']} |"
            )
            continue
        lines.append(
            f"| {report['doi']} | "
            f"{'yes' if report['three_repeat']['report_exact_agreement'] else 'no'} | "
            f"{'yes' if report['five_repeat']['report_exact_agreement'] else 'no'} | "
            f"{report['five_repeat']['included_counts']} |"
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
                "three_repeat_exact": summary["three_repeat"][
                    "report_exact_agreement_rate"
                ],
                "five_repeat_exact": summary["five_repeat"][
                    "report_exact_agreement_rate"
                ],
                "five_repeat_qualification_exact": summary["five_repeat"][
                    "qualification_exact_rate"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
