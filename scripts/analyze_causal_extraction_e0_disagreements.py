#!/usr/bin/env python3
"""Describe E0 inventory disagreement without exporting article text."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    read_json,
    sha256_file,
    write_json,
    write_text,
)

REPO = Path(__file__).resolve().parents[1]
DEFAULT_RUN = REPO / "data/causal_extraction/e0_grounding/v0.1.0_run1"
DEFAULT_OUTPUT = REPO / "analysis/causal_extraction/e0_grounding/v0.1.0_run1"
CLOSED_FIELDS = ("analysis_basis", "design_family", "analysis_completeness")
SCIENTIFIC_FIELDS = (
    "analysis_basis",
    "design_family",
    "method_name",
    "exposure_construct",
    "outcome_construct",
    "biological_system",
    "analysis_completeness",
)
EVIDENCE_FIELDS = ("method_evidence_resolved", "result_evidence_resolved")


def _resolved_response(terminal: dict[str, Any]) -> dict[str, Any]:
    return read_json(REPO / terminal["resolved_response_path"])


def _payload(response: dict[str, Any], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    items = []
    for analysis in response.get("analyses", []):
        item = {field: analysis[field] for field in fields}
        for evidence_field in EVIDENCE_FIELDS:
            item[f"{evidence_field}_atom_ids"] = sorted(
                anchor["evidence_atom_id"] for anchor in analysis.get(evidence_field, [])
            )
        items.append(item)
    return sorted(items, key=canonical_json)


def _field_payload(response: dict[str, Any], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    return sorted(
        [{field: analysis[field] for field in fields} for analysis in response.get("analyses", [])],
        key=canonical_json,
    )


def _evidence_ids(response: dict[str, Any]) -> set[str]:
    return {
        anchor["evidence_atom_id"]
        for analysis in response.get("analyses", [])
        for field in EVIDENCE_FIELDS
        for anchor in analysis.get(field, [])
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def _comparison(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_count = len(left.get("analyses", []))
    right_count = len(right.get("analyses", []))
    left_evidence = _evidence_ids(left)
    right_evidence = _evidence_ids(right)
    return {
        "left_analysis_count": left_count,
        "right_analysis_count": right_count,
        "both_empty": left_count == right_count == 0,
        "at_least_one_nonempty": left_count > 0 or right_count > 0,
        "analysis_count_exact": left_count == right_count,
        "closed_field_multiset_exact": (
            _field_payload(left, CLOSED_FIELDS) == _field_payload(right, CLOSED_FIELDS)
        ),
        "scientific_field_multiset_exact": (
            _field_payload(left, SCIENTIFIC_FIELDS) == _field_payload(right, SCIENTIFIC_FIELDS)
        ),
        "evidence_atom_union_exact": left_evidence == right_evidence,
        "evidence_atom_jaccard": _jaccard(left_evidence, right_evidence),
        "closed_plus_grounding_exact": (
            _payload(left, CLOSED_FIELDS) == _payload(right, CLOSED_FIELDS)
        ),
        "all_fields_plus_grounding_exact": (
            _payload(left, SCIENTIFIC_FIELDS) == _payload(right, SCIENTIFIC_FIELDS)
        ),
    }


def _terminals(run: Path) -> list[dict[str, Any]]:
    terminals = []
    for path in sorted((run / "calls").glob("*/*/*/repeat-*/terminal.json")):
        terminal = read_json(path)
        terminal["terminal_path"] = str(path.relative_to(run))
        if terminal["status"] == "ok":
            terminal["response"] = _resolved_response(terminal)
        terminals.append(terminal)
    return terminals


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    boolean_fields = (
        "both_empty",
        "analysis_count_exact",
        "closed_field_multiset_exact",
        "scientific_field_multiset_exact",
        "evidence_atom_union_exact",
        "closed_plus_grounding_exact",
        "all_fields_plus_grounding_exact",
    )
    nonempty = [row for row in rows if row["at_least_one_nonempty"]]

    def metrics(items: list[dict[str, Any]]) -> dict[str, Any]:
        jaccards = [float(item["evidence_atom_jaccard"]) for item in items]
        return {
            "pairs": len(items),
            **{field: sum(bool(item[field]) for item in items) for field in boolean_fields},
            "mean_evidence_atom_jaccard": (statistics.fmean(jaccards) if jaccards else None),
            "median_evidence_atom_jaccard": (statistics.median(jaccards) if jaccards else None),
        }

    return {"all_pairs": metrics(rows), "nonempty_pairs": metrics(nonempty)}


def analyze(run: Path, output: Path) -> dict[str, Any]:
    run = run.resolve()
    output = output.resolve()
    summary_path = output / "summary.json"
    summary = read_json(summary_path)
    terminals = _terminals(run)
    if any(terminal["status"] != "ok" for terminal in terminals):
        raise ValueError("Post-hoc disagreement analysis requires all E0 terminal calls")

    repeated: dict[tuple[str, str, str], dict[int, dict[str, Any]]] = defaultdict(dict)
    crossed: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for terminal in terminals:
        repeated[(terminal["arm"], terminal["report_id"], terminal["work_unit_id"])][
            int(terminal["repeat"])
        ] = terminal
        crossed[
            (
                terminal["report_id"],
                terminal["work_unit_id"],
                int(terminal["repeat"]),
            )
        ][terminal["arm"]] = terminal

    repeat_rows = []
    for (arm, report_id, work_unit_id), pair in sorted(repeated.items()):
        if set(pair) != {1, 2}:
            raise ValueError(f"Incomplete repeat pair: {arm} {report_id} {work_unit_id}")
        repeat_rows.append(
            {
                "arm": arm,
                "report_id": report_id,
                "work_unit_id": work_unit_id,
                **_comparison(pair[1]["response"], pair[2]["response"]),
            }
        )

    cross_rows = []
    for (report_id, work_unit_id, repeat), pair in sorted(crossed.items()):
        if set(pair) != {"verbatim_quote", "evidence_atom_id"}:
            raise ValueError(f"Incomplete cross-arm pair: {report_id} {work_unit_id} {repeat}")
        cross_rows.append(
            {
                "report_id": report_id,
                "work_unit_id": work_unit_id,
                "repeat": repeat,
                **_comparison(
                    pair["verbatim_quote"]["response"],
                    pair["evidence_atom_id"]["response"],
                ),
            }
        )

    retry_reasons = Counter()
    retry_rows = []
    for terminal in terminals:
        if int(terminal["attempts"]) <= 1:
            continue
        attempt_one = (run / terminal["terminal_path"]).parent / "attempt-01" / "validation.json"
        validation = read_json(attempt_one)
        reasons = [failure["reason"] for failure in validation.get("grounding_failures", [])]
        retry_reasons.update(reasons)
        retry_rows.append(
            {
                "arm": terminal["arm"],
                "report_id": terminal["report_id"],
                "work_unit_id": terminal["work_unit_id"],
                "repeat": terminal["repeat"],
                "attempts": terminal["attempts"],
                "first_attempt_schema_valid": validation.get("schema_valid", False),
                "first_attempt_grounding_valid": validation.get("grounding_valid", False),
                "first_attempt_failure_reasons": "|".join(reasons),
            }
        )

    by_arm = {
        arm: _aggregate([row for row in repeat_rows if row["arm"] == arm])
        for arm in ("verbatim_quote", "evidence_atom_id")
    }
    by_report = {}
    for report_id in sorted({row["report_id"] for row in repeat_rows}):
        by_report[report_id] = {
            arm: _aggregate(
                [row for row in repeat_rows if row["report_id"] == report_id and row["arm"] == arm]
            )
            for arm in ("verbatim_quote", "evidence_atom_id")
        }

    result = {
        "analysis_id": "causal_extraction_e0_posthoc_disagreement_v1",
        "status": "exploratory_posthoc_not_prefrozen",
        "development_only": True,
        "source_run_verdict": summary["verdict"],
        "source_summary_sha256": sha256_file(summary_path),
        "source_raw_tree_sha256": read_json(output / "raw_artifact_inventory.json")["tree_sha256"],
        "repeat_agreement_by_arm": by_arm,
        "repeat_agreement_by_report": by_report,
        "cross_arm_agreement": _aggregate(cross_rows),
        "retry_analysis": {
            "retry_calls": len(retry_rows),
            "reasons": dict(retry_reasons),
            "rows": retry_rows,
        },
        "registered_interpretation": {
            "evidence_id_grounding_technical_result": (
                "The evidence-ID arm eliminated first-attempt grounding failures "
                "and resolved every returned ID."
            ),
            "inventory_stability_result": (
                "All exact all-field repeat pairs were empty windows. No nonempty "
                "work unit reproduced the full scientific inventory exactly."
            ),
            "instrument_decision": (
                "Retain evidence_atom_id as the grounding interface for the next "
                "development instrument; reject open window-level causal-analysis "
                "inventory as a stable extraction method."
            ),
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "disagreement_analysis.json", result)
    _write_csv(output / "repeat_pair_ledger.csv", repeat_rows)
    _write_csv(output / "cross_arm_pair_ledger.csv", cross_rows)
    write_text(output / "disagreement_report.md", _report(result))
    return result


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _percent(numerator: int, denominator: int) -> str:
    return f"{100 * numerator / denominator:.1f}%" if denominator else "NA"


def _report(result: dict[str, Any]) -> str:
    lines = [
        "# E0 post-hoc disagreement audit",
        "",
        "Status: exploratory post-hoc analysis of the frozen E0 run. The metrics "
        "below were not used to alter E0 prompts, schemas, runtime, or outputs.",
        "",
        "## Main result",
        "",
    ]
    for arm, aggregate in result["repeat_agreement_by_arm"].items():
        all_pairs = aggregate["all_pairs"]
        nonempty = aggregate["nonempty_pairs"]
        lines.extend(
            [
                f"- `{arm}`: full repeat agreement "
                f"{all_pairs['all_fields_plus_grounding_exact']}/"
                f"{all_pairs['pairs']} "
                f"({_percent(all_pairs['all_fields_plus_grounding_exact'], all_pairs['pairs'])}).",
                f"- `{arm}` nonempty windows: full repeat agreement "
                f"{nonempty['all_fields_plus_grounding_exact']}/"
                f"{nonempty['pairs']}; analysis-count agreement "
                f"{nonempty['analysis_count_exact']}/{nonempty['pairs']}; closed-field "
                f"agreement {nonempty['closed_field_multiset_exact']}/"
                f"{nonempty['pairs']}.",
            ]
        )
    cross = result["cross_arm_agreement"]
    lines.extend(
        [
            "",
            "Every full exact repeat pair was an empty window. The grounding "
            "interface solved citation transport but did not localize the open "
            "scientific inventory task.",
            "",
            f"Across arms, nonempty full agreement was "
            f"{cross['nonempty_pairs']['all_fields_plus_grounding_exact']}/"
            f"{cross['nonempty_pairs']['pairs']}. This shows that changing the "
            "grounding output contract also changed upstream inventory behavior.",
            "",
            "## Grounding result",
            "",
            f"The quote arm required {result['retry_analysis']['retry_calls']} "
            "retries. All recorded first-attempt failures were character-exact "
            "substring failures caused by model-reproduced text. The evidence-ID "
            "arm required no retry and every returned ID resolved to frozen text.",
            "",
            "## Boundary audit",
            "",
            "Manual inspection of disagreement summaries identified three recurring "
            "boundary choices:",
            "",
            "1. One perturbation was split by histology, molecular assay, or phenotype "
            "in one repeat and grouped as one experiment in another.",
            "2. Multi-gene SMR estimates were represented as one screen in one repeat "
            "and as separate exposure-specific analyses in another.",
            "3. The same experimental contrast received different design-family labels "
            "when transfer, intervention, and perturbation descriptions overlapped.",
            "",
            "Representative audit locations were DOI `10.1038/s41413-025-00422-3`, "
            "window 002; DOI `10.1186/s12967-026-07766-2`, window 002; and DOI "
            "`10.1016/j.ccell.2024.09.002`, window 003. No article quotation is "
            "exported in this compact report.",
            "",
            "## Decision",
            "",
            "Retain `evidence_atom_id` for the next development instrument. Reject "
            "open window-level causal-analysis inventory. The next unit should be a "
            "design instance keyed by identifying variation or assignment, exposure, "
            "and biological system; outcomes and assay readouts should be child "
            "contrasts. Fixed atom-level role tagging should precede analysis assembly.",
            "",
            "The two-human semantic audit and analysis-inventory gold remain pending. "
            "E0 therefore remains a technical result rather than an accuracy claim.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = analyze(args.run, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
