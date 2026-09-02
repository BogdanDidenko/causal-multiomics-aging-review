#!/usr/bin/env python3
"""Summarize three-repeat and five-repeat v0.3 extraction stability."""

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
SUITE = REPO / "protocol/causal_extraction/v0.3.0"
RAW = REPO / "data/causal_extraction/v0.3.0_development/terra_5repeat"
OUTPUT = REPO / "analysis/causal_extraction/v0.3.0_development/terra_5repeat"
REFERENCE = (
    REPO
    / "analysis/causal_extraction/v0.3.0_development/reference_inventory.json"
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


def analysis_anchor(analysis: dict[str, Any]) -> tuple[str, str]:
    return analysis["method_atom_id"], analysis["result_atom_id"]


def normalized_hash(output: dict[str, Any]) -> str:
    return sha256_text(canonical_json(output))


def prefix_metrics(outputs: list[dict[str, Any]], repeat_count: int) -> dict[str, Any]:
    prefix = outputs[:repeat_count]
    hashes = [normalized_hash(output) for output in prefix]
    anchor_sets = [
        sorted(analysis_anchor(analysis) for analysis in output["analyses"])
        for output in prefix
    ]
    common_anchors = set(anchor_sets[0]) if anchor_sets else set()
    for anchors in anchor_sets[1:]:
        common_anchors &= set(anchors)
    field_names = [
        field
        for field in read_json(SUITE / "stability_contract.json")["all_tracked_fields"]
        if field not in {"source_status", "method_atom_id", "result_atom_id"}
    ]
    field_exact: dict[str, dict[str, int]] = {
        field: {"eligible_common_anchors": 0, "unanimous_common_anchors": 0}
        for field in field_names
    }
    maps = [
        {analysis_anchor(analysis): analysis for analysis in output["analyses"]}
        for output in prefix
    ]
    for anchor in common_anchors:
        records = [mapping[anchor] for mapping in maps]
        for field in field_names:
            values = [canonical_json(record[field]) for record in records]
            field_exact[field]["eligible_common_anchors"] += 1
            if len(set(values)) == 1:
                field_exact[field]["unanimous_common_anchors"] += 1
    for metrics in field_exact.values():
        denominator = metrics["eligible_common_anchors"]
        metrics["rate"] = (
            metrics["unanimous_common_anchors"] / denominator if denominator else None
        )
    return {
        "repeat_count": repeat_count,
        "report_exact_agreement": len(set(hashes)) == 1,
        "analysis_anchor_set_exact_agreement": len(
            {canonical_json(anchors) for anchors in anchor_sets}
        )
        == 1,
        "source_status_exact_agreement": len(
            {output["source_status"] for output in prefix}
        )
        == 1,
        "distinct_normalized_outputs": len(set(hashes)),
        "analysis_counts": [len(output["analyses"]) for output in prefix],
        "common_analysis_anchor_count": len(common_anchors),
        "field_agreement_on_common_anchors": field_exact,
    }


def reference_records() -> dict[str, dict[str, Any]]:
    inventory = read_json(REFERENCE)
    return {report["document_id"]: report for report in inventory["reports"]}


def evidence_overlap_score(
    predicted: dict[str, Any], reference: dict[str, Any]
) -> tuple[int, bool]:
    method_ids = set(reference["method_evidence_atom_ids"])
    result_ids = set(reference["result_evidence_atom_ids"])
    validation_ids = set(reference["validation_evidence_atom_ids"])
    method_match = predicted["method_atom_id"] in method_ids
    result_match = predicted["result_atom_id"] in result_ids
    validation_match = bool(
        set(predicted["validation_atom_ids"]) & validation_ids
    )
    score = 4 * int(method_match) + 6 * int(result_match) + int(validation_match)
    return score, method_match or result_match


def align_to_reference(
    predicted: list[dict[str, Any]], report_reference: dict[str, Any]
) -> dict[str, Any]:
    references = report_reference["causal_analyses"]
    candidates: list[tuple[int, int, int]] = []
    for predicted_index, prediction in enumerate(predicted):
        for reference_index, reference in enumerate(references):
            score, eligible = evidence_overlap_score(prediction, reference)
            if eligible:
                candidates.append((score, predicted_index, reference_index))
    matched_predictions: set[int] = set()
    matched_references: set[int] = set()
    matches = []
    for score, predicted_index, reference_index in sorted(candidates, reverse=True):
        if predicted_index in matched_predictions or reference_index in matched_references:
            continue
        matched_predictions.add(predicted_index)
        matched_references.add(reference_index)
        matches.append(
            {
                "predicted_anchor": list(analysis_anchor(predicted[predicted_index])),
                "reference_analysis_id": references[reference_index]["analysis_id"],
                "evidence_overlap_score": score,
            }
        )
    excluded_atom_ids = {
        atom_id
        for candidate in report_reference["excluded_candidates"]
        for atom_id in candidate["evidence_atom_ids"]
    }
    boundary_promotions = [
        list(analysis_anchor(prediction))
        for prediction in predicted
        if prediction["method_atom_id"] in excluded_atom_ids
        or prediction["result_atom_id"] in excluded_atom_ids
    ]
    true_positive = len(matches)
    reference_total = len(references)
    predicted_total = len(predicted)
    recall = true_positive / reference_total if reference_total else 1.0
    precision = true_positive / predicted_total if predicted_total else (
        1.0 if reference_total == 0 else 0.0
    )
    return {
        "reference_total": reference_total,
        "predicted_total": predicted_total,
        "evidence_overlap_matches": true_positive,
        "reference_alignment_recall": recall,
        "reference_alignment_precision": precision,
        "unmatched_reference_analysis_ids": [
            reference["analysis_id"]
            for index, reference in enumerate(references)
            if index not in matched_references
        ],
        "unmatched_predicted_anchors": [
            list(analysis_anchor(prediction))
            for index, prediction in enumerate(predicted)
            if index not in matched_predictions
        ],
        "direct_boundary_promotions": boundary_promotions,
        "matches": sorted(matches, key=lambda item: item["reference_analysis_id"]),
    }


def summarize(raw: Path) -> dict[str, Any]:
    sample = read_json(SUITE / "sample.json")
    runtime = read_json(SUITE / "runtime.json")
    references = reference_records()
    repeat_count = int(runtime["repeats"])
    reports = []
    valid_calls = 0
    for sampled in sample["reports"]:
        document_id = sampled["document_id"]
        outputs = []
        missing_repeats = []
        for repeat in range(1, repeat_count + 1):
            path = raw / "calls" / document_id / f"repeat-{repeat:02d}" / "normalized.json"
            if not path.is_file():
                missing_repeats.append(repeat)
                continue
            outputs.append(read_json(path))
            valid_calls += 1
        report = {
            "sample_order": sampled["sample_order"],
            "report_id": sampled["report_id"],
            "document_id": document_id,
            "doi": sampled["doi"],
            "valid_repeat_count": len(outputs),
            "missing_repeats": missing_repeats,
        }
        if not missing_repeats:
            report["three_repeat"] = prefix_metrics(outputs, 3)
            report["five_repeat"] = prefix_metrics(outputs, 5)
            report["reference_alignment_by_repeat"] = [
                {
                    "repeat": repeat,
                    **align_to_reference(
                        output["analyses"], references[document_id]
                    ),
                }
                for repeat, output in enumerate(outputs, start=1)
            ]
        reports.append(report)

    complete = [report for report in reports if not report["missing_repeats"]]
    summary: dict[str, Any] = {
        "experiment_id": runtime["experiment_id"],
        "development_only": True,
        "expert_gold_standard": False,
        "reference_status": "ai_assisted_analyst_draft_pending_human_verification",
        "planned_reports": len(sample["reports"]),
        "planned_calls": len(sample["reports"]) * repeat_count,
        "valid_calls": valid_calls,
        "complete_reports": len(complete),
        "reports": reports,
    }
    for label in ("three_repeat", "five_repeat"):
        exact = sum(report[label]["report_exact_agreement"] for report in complete)
        anchors = sum(
            report[label]["analysis_anchor_set_exact_agreement"] for report in complete
        )
        summary[label] = {
            "reports": len(complete),
            "report_exact_agreement_count": exact,
            "report_exact_agreement_rate": exact / len(complete) if complete else None,
            "report_exact_agreement_wilson_95": wilson_interval(exact, len(complete)),
            "analysis_anchor_set_exact_agreement_count": anchors,
            "analysis_anchor_set_exact_agreement_rate": (
                anchors / len(complete) if complete else None
            ),
            "passes_prespecified_exact_agreement_gate": exact == len(sample["reports"]),
        }
    alignments = [
        alignment
        for report in complete
        for alignment in report["reference_alignment_by_repeat"]
    ]
    summary["reference_alignment"] = {
        "report_repeat_evaluations": len(alignments),
        "mean_recall": (
            sum(item["reference_alignment_recall"] for item in alignments)
            / len(alignments)
            if alignments
            else None
        ),
        "mean_precision": (
            sum(item["reference_alignment_precision"] for item in alignments)
            / len(alignments)
            if alignments
            else None
        ),
        "direct_boundary_promotions": sum(
            len(item["direct_boundary_promotions"]) for item in alignments
        ),
        "interpretation": "Development alignment only; this is not expert-gold accuracy.",
    }
    return summary


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Causal extraction v0.3 stability report",
        "",
        "Status: development-only; analyst reference draft, no expert-gold accuracy claim.",
        "",
        "## Completion",
        "",
        f"- Valid calls: {summary['valid_calls']}/{summary['planned_calls']}",
        f"- Complete reports: {summary['complete_reports']}/{summary['planned_reports']}",
        "",
        "## Stability",
        "",
        "| View | Exact reports | Rate | Anchor-set exact | Gate |",
        "|---|---:|---:|---:|---|",
    ]
    for label, display in (("three_repeat", "3 repeats"), ("five_repeat", "5 repeats")):
        item = summary[label]
        rate = item["report_exact_agreement_rate"]
        anchor_rate = item["analysis_anchor_set_exact_agreement_rate"]
        lines.append(
            f"| {display} | {item['report_exact_agreement_count']}/{item['reports']} | "
            f"{rate:.1%} | {anchor_rate:.1%} | "
            f"{'PASS' if item['passes_prespecified_exact_agreement_gate'] else 'FAIL'} |"
        )
    alignment = summary["reference_alignment"]
    lines.extend(
        [
            "",
            "## Reference alignment",
            "",
            f"- Mean evidence-overlap recall: {alignment['mean_recall']:.1%}",
            f"- Mean evidence-overlap precision: {alignment['mean_precision']:.1%}",
            f"- Direct boundary promotions: {alignment['direct_boundary_promotions']}",
            "- Interpretation: development diagnostics against an AI-assisted analyst draft.",
            "",
            "## Reports",
            "",
            "| DOI | 3-run exact | 5-run exact | Counts across five runs |",
            "|---|---|---|---|",
        ]
    )
    for report in summary["reports"]:
        if report["missing_repeats"]:
            lines.append(
                f"| {report['doi']} | incomplete | incomplete | missing "
                f"{report['missing_repeats']} |"
            )
            continue
        lines.append(
            f"| {report['doi']} | "
            f"{'yes' if report['three_repeat']['report_exact_agreement'] else 'no'} | "
            f"{'yes' if report['five_repeat']['report_exact_agreement'] else 'no'} | "
            f"{report['five_repeat']['analysis_counts']} |"
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
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
