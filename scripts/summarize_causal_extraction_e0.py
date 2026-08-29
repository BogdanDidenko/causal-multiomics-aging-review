#!/usr/bin/env python3
"""Build compact, non-textual audit outputs for the E0 grounding bake-off."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    read_json,
    sha256_file,
    sha256_text,
    write_json,
    write_text,
)

REPO = Path(__file__).resolve().parents[1]
DEFAULT_RUN = REPO / "data/causal_extraction/e0_grounding/v0.1.0_run1"
DEFAULT_OUTPUT = REPO / "analysis/causal_extraction/e0_grounding/v0.1.0_run1"
SUITE = REPO / "protocol/causal_extraction/e0_grounding/v0.1.0"
AUDIT_SEED = "20260829-e0-semantic-anchor-audit-v1"


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path.resolve())


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> dict[str, Any]:
    if total == 0:
        return {"successes": successes, "total": total, "estimate": None, "low": None, "high": None}
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = proportion + z * z / (2 * total)
    margin = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total))
    return {
        "successes": successes,
        "total": total,
        "estimate": proportion,
        "low": (centre - margin) / denominator,
        "high": (centre + margin) / denominator,
    }


def _terminal_rows(run: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((run / "calls").glob("*/*/*/repeat-*/terminal.json")):
        terminal = read_json(path)
        terminal["terminal_path"] = relative(path)
        rows.append(terminal)
    return rows


def _resolved_anchors(
    terminal: dict[str, Any], sample_by_report: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if terminal["status"] != "ok":
        return [], []
    response = read_json(REPO / terminal["resolved_response_path"])
    analyses = response.get("analyses", [])
    anchors = []
    report = sample_by_report[terminal["report_id"]]
    for analysis_index, analysis in enumerate(analyses):
        summary = {
            key: analysis[key]
            for key in (
                "analysis_basis",
                "design_family",
                "method_name",
                "exposure_construct",
                "outcome_construct",
                "biological_system",
                "analysis_completeness",
            )
        }
        for role in ("method_evidence", "result_evidence"):
            for anchor_index, anchor in enumerate(analysis.get(f"{role}_resolved", [])):
                occurrence = {
                    "arm": terminal["arm"],
                    "report_id": terminal["report_id"],
                    "doi": report["doi"],
                    "title": report["title"],
                    "work_unit_id": terminal["work_unit_id"],
                    "repeat": terminal["repeat"],
                    "analysis_index": analysis_index,
                    "anchor_index": anchor_index,
                    "evidence_role": role,
                    **summary,
                    **anchor,
                }
                occurrence["occurrence_id"] = sha256_text(
                    canonical_json(
                        {
                            key: occurrence[key]
                            for key in (
                                "arm",
                                "report_id",
                                "work_unit_id",
                                "repeat",
                                "analysis_index",
                                "anchor_index",
                                "evidence_role",
                                "evidence_atom_id",
                                "raw_start",
                                "raw_end",
                            )
                        }
                    )
                )[:24]
                anchors.append(occurrence)
    return analyses, anchors


def _inventory_payload(
    analyses: list[dict[str, Any]], *, decision_only: bool
) -> list[dict[str, Any]]:
    items = []
    for analysis in analyses:
        if decision_only:
            item = {
                key: analysis[key]
                for key in (
                    "analysis_basis",
                    "design_family",
                    "analysis_completeness",
                )
            }
        else:
            item = {
                key: analysis[key]
                for key in (
                    "analysis_basis",
                    "design_family",
                    "method_name",
                    "exposure_construct",
                    "outcome_construct",
                    "biological_system",
                    "analysis_completeness",
                )
            }
        for role in ("method_evidence", "result_evidence"):
            item[f"{role}_atom_ids"] = sorted(
                anchor["evidence_atom_id"] for anchor in analysis.get(f"{role}_resolved", [])
            )
        items.append(item)
    return sorted(items, key=canonical_json)


def _select_audit(anchors: list[dict[str, Any]], target: int = 60) -> list[dict[str, Any]]:
    unique = {}
    for anchor in anchors:
        scientific_key = (
            anchor["arm"],
            anchor["report_id"],
            anchor["evidence_role"],
            anchor["evidence_atom_id"],
            anchor["quote_sha256"],
        )
        unique.setdefault(scientific_key, anchor)
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for anchor in unique.values():
        groups[(anchor["arm"], anchor["evidence_role"], anchor["report_id"])].append(anchor)
    for key, values in groups.items():
        values.sort(
            key=lambda item: hashlib.sha256(
                f"{AUDIT_SEED}|{key}|{item['occurrence_id']}".encode()
            ).hexdigest()
        )

    selected = []
    group_keys = sorted(groups)
    while len(selected) < target and any(groups[key] for key in group_keys):
        for key in group_keys:
            if groups[key] and len(selected) < target:
                selected.append(groups[key].pop(0))
    return selected


def _write_audit_files(
    run: Path,
    anchors: list[dict[str, Any]],
    sample_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    selected = _select_audit(anchors)
    key_path = run / "human_audit" / "semantic_anchor_audit_key.csv"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    shared_form_fields = [
        "audit_id",
        "report_id",
        "doi",
        "title",
        "section_id",
        "evidence_role",
        "analysis_basis",
        "design_family",
        "method_name",
        "exposure_construct",
        "outcome_construct",
        "biological_system",
        "quote",
    ]
    key_fields = [
        "audit_id",
        "arm",
        "work_unit_id",
        "repeat",
        "analysis_index",
        "anchor_index",
        "evidence_atom_id",
        "raw_start",
        "raw_end",
        "quote_sha256",
        "occurrence_id",
    ]
    reviewer_forms = []
    for reviewer in (1, 2):
        form_path = run / "human_audit" / f"semantic_anchor_audit_reviewer_{reviewer}.csv"
        form_fields = [
            *shared_form_fields,
            "support_judgment",
            "additional_context_atom_ids",
            "reviewer_note",
        ]
        with form_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=form_fields)
            writer.writeheader()
            for index, anchor in enumerate(selected, start=1):
                writer.writerow(
                    {
                        "audit_id": f"E0-AUDIT-{index:03d}",
                        **{
                            field: anchor.get(field, "")
                            for field in shared_form_fields
                            if field != "audit_id"
                        },
                        "support_judgment": "",
                        "additional_context_atom_ids": "",
                        "reviewer_note": "",
                    }
                )
        reviewer_forms.append(
            {
                "reviewer": reviewer,
                "path": relative(form_path),
                "sha256": sha256_file(form_path),
            }
        )
    with key_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=key_fields)
        writer.writeheader()
        for index, anchor in enumerate(selected, start=1):
            writer.writerow(
                {
                    "audit_id": f"E0-AUDIT-{index:03d}",
                    **{field: anchor.get(field, "") for field in key_fields if field != "audit_id"},
                }
            )

    adjudication_path = run / "human_audit" / "semantic_anchor_adjudication.csv"
    with adjudication_path.open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "audit_id",
            "reviewer_1_support",
            "reviewer_2_support",
            "adjudicated_support",
            "adjudication_note",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index in range(1, len(selected) + 1):
            writer.writerow({"audit_id": f"E0-AUDIT-{index:03d}"})

    inventory_fields = [
        "reviewer_id",
        "report_id",
        "doi",
        "gold_analysis_id",
        "report_inventory_status",
        "analysis_basis",
        "design_family",
        "method_name",
        "exposure_construct",
        "outcome_construct",
        "biological_system",
        "method_evidence_atom_ids",
        "result_evidence_atom_ids",
        "reviewer_note",
    ]
    inventory_paths = []
    for reviewer in (1, 2):
        inventory_path = run / "human_audit" / f"analysis_inventory_reviewer_{reviewer}.csv"
        with inventory_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=inventory_fields)
            writer.writeheader()
            for report in sample_reports:
                writer.writerow(
                    {
                        "reviewer_id": f"reviewer_{reviewer}",
                        "report_id": report["report_id"],
                        "doi": report["doi"],
                        "report_inventory_status": "",
                    }
                )
        inventory_paths.append(
            {
                "reviewer": reviewer,
                "path": relative(inventory_path),
                "sha256": sha256_file(inventory_path),
            }
        )
    return {
        "target": 60,
        "selected": len(selected),
        "selection_seed": AUDIT_SEED,
        "reviewer_forms": reviewer_forms,
        "key_path": relative(key_path),
        "key_sha256": sha256_file(key_path),
        "adjudication_path": relative(adjudication_path),
        "adjudication_sha256": sha256_file(adjudication_path),
        "analysis_inventory_templates": inventory_paths,
        "status": "pending_two_human_reviewers",
    }


def _raw_inventory(run: Path) -> dict[str, Any]:
    files = []
    for path in sorted(item for item in run.rglob("*") if item.is_file()):
        files.append(
            {
                "path": str(path.relative_to(run)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "run_path": relative(run),
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "tree_sha256": sha256_text(canonical_json(files)),
        "files": files,
    }


def summarize(run: Path, output: Path) -> dict[str, Any]:
    run = run.resolve()
    output = output.resolve()
    runtime = read_json(SUITE / "runtime.json")
    sample = read_json(SUITE / "sample.json")
    sample_by_report = {item["report_id"]: item for item in sample["reports"]}
    orchestrator = read_json(run / "orchestrator_manifest.json")
    prompt_inventory = read_json(run / "preflight/prompt_inventory.json")
    terminals = _terminal_rows(run)
    planned = int(prompt_inventory["planned_calls"])
    status_counts = Counter(item["status"] for item in terminals)
    arm_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    call_rows = []
    anchors = []
    pair_payloads: dict[tuple[str, str, str], dict[int, tuple[str, str]]] = defaultdict(dict)
    cross_arm_payloads: dict[tuple[str, str, int], dict[str, tuple[str, str]]] = defaultdict(dict)
    for terminal in terminals:
        analyses, call_anchors = _resolved_anchors(terminal, sample_by_report)
        anchors.extend(call_anchors)
        validation = (
            read_json(REPO / terminal["validation_path"]) if terminal.get("validation_path") else {}
        )
        first_validation_path = (
            run
            / "calls"
            / terminal["arm"]
            / terminal["document_id"]
            / terminal["work_unit_id"]
            / f"repeat-{int(terminal['repeat']):02d}"
            / "attempt-01"
            / "validation.json"
        )
        first_validation = (
            read_json(first_validation_path) if first_validation_path.is_file() else {}
        )
        returned_reference_count = 0
        if terminal.get("response_path"):
            raw_response = read_json(REPO / terminal["response_path"])
            returned_reference_count = sum(
                len(analysis.get(field, []))
                for analysis in raw_response.get("analyses", [])
                if isinstance(analysis, dict)
                for field in ("method_evidence", "result_evidence")
                if isinstance(analysis.get(field, []), list)
            )
        all_hash = (
            sha256_text(canonical_json(_inventory_payload(analyses, decision_only=False)))
            if terminal["status"] == "ok"
            else ""
        )
        decision_hash = (
            sha256_text(canonical_json(_inventory_payload(analyses, decision_only=True)))
            if terminal["status"] == "ok"
            else ""
        )
        row = {
            "arm": terminal["arm"],
            "report_id": terminal["report_id"],
            "document_id": terminal["document_id"],
            "work_unit_id": terminal["work_unit_id"],
            "repeat": terminal["repeat"],
            "status": terminal["status"],
            "attempts": terminal.get("attempts", ""),
            "first_attempt_schema_valid": first_validation.get("schema_valid", False),
            "first_attempt_grounding_valid": first_validation.get("grounding_valid", False),
            "terminal_schema_valid": validation.get("schema_valid", False),
            "terminal_grounding_valid": validation.get("grounding_valid", False),
            "analysis_count": len(analyses),
            "returned_evidence_reference_count": returned_reference_count,
            "resolved_evidence_reference_count": len(call_anchors),
            "all_field_inventory_sha256": all_hash,
            "decision_and_grounding_sha256": decision_hash,
            "terminal_path": terminal["terminal_path"],
        }
        call_rows.append(row)
        arm_rows[terminal["arm"]].append(row)
        if terminal["status"] == "ok":
            pair_payloads[(terminal["arm"], terminal["report_id"], terminal["work_unit_id"])][
                int(terminal["repeat"])
            ] = (all_hash, decision_hash)
            cross_key = (
                terminal["report_id"],
                terminal["work_unit_id"],
                int(terminal["repeat"]),
            )
            cross_arm_payloads[cross_key][terminal["arm"]] = (
                all_hash,
                decision_hash,
            )

    failure_reasons = Counter()
    for terminal in terminals:
        if not terminal.get("validation_path"):
            if terminal["status"] != "ok":
                failure_reasons[terminal["status"]] += 1
            continue
        validation = read_json(REPO / terminal["validation_path"])
        for failure in validation.get("grounding_failures", []):
            failure_reasons[failure["reason"]] += 1
        if validation.get("schema_errors"):
            failure_reasons["schema_error"] += 1

    by_arm = {}
    for arm in runtime["arms"]:
        rows = arm_rows[arm]
        ok = sum(row["status"] == "ok" for row in rows)
        first_ok = sum(
            row["first_attempt_schema_valid"] and row["first_attempt_grounding_valid"]
            for row in rows
        )
        arm_anchors = [anchor for anchor in anchors if anchor["arm"] == arm]
        returned_references = sum(int(row["returned_evidence_reference_count"]) for row in rows)
        pairs = [
            values
            for key, values in pair_payloads.items()
            if key[0] == arm and set(values) == {1, 2}
        ]
        by_arm[arm] = {
            "terminal_calls": len(rows),
            "ok_calls": ok,
            "terminal_valid_wilson_95": wilson(ok, len(rows)),
            "first_attempt_valid_calls": first_ok,
            "first_attempt_valid_wilson_95": wilson(first_ok, len(rows)),
            "retry_calls": sum(int(row["attempts"] or 0) > 1 for row in rows),
            "analyses_returned": sum(int(row["analysis_count"]) for row in rows),
            "returned_evidence_references": returned_references,
            "resolved_evidence_references": len(arm_anchors),
            "resolution_wilson_95": wilson(len(arm_anchors), returned_references),
            "complete_repeat_pairs": len(pairs),
            "all_field_exact_repeat_pairs": sum(values[1][0] == values[2][0] for values in pairs),
            "decision_and_grounding_exact_repeat_pairs": sum(
                values[1][1] == values[2][1] for values in pairs
            ),
        }

    cross_pairs = [
        values
        for values in cross_arm_payloads.values()
        if set(values) == {"verbatim_quote", "evidence_atom_id"}
    ]
    cross_arm = {
        "complete_arm_pairs": len(cross_pairs),
        "all_field_exact_pairs": sum(
            values["verbatim_quote"][0] == values["evidence_atom_id"][0] for values in cross_pairs
        ),
        "decision_and_grounding_exact_pairs": sum(
            values["verbatim_quote"][1] == values["evidence_atom_id"][1] for values in cross_pairs
        ),
    }

    audit = _write_audit_files(run, anchors, sample["reports"])
    coverage_files = list((run / "inputs").glob("*/coverage.json"))
    coverage = [read_json(path) for path in coverage_files]
    technical_pass = (
        len(terminals) == planned
        and status_counts.get("ok", 0) == planned
        and all(item["all_atoms_core_exactly_once"] for item in coverage)
        and by_arm["evidence_atom_id"]["returned_evidence_references"]
        == by_arm["evidence_atom_id"]["resolved_evidence_references"]
        and failure_reasons["unknown_atom_id"] == 0
    )
    verdict = "technical_pass_pending_human_semantic_audit" if technical_pass else "technical_fail"
    summary = {
        "experiment_id": runtime["experiment_id"],
        "version": runtime["version"],
        "development_only": True,
        "scientific_accuracy_claim_allowed": False,
        "model": runtime["model"],
        "reasoning_effort": runtime["reasoning_effort"],
        "sample_reports": len(sample["reports"]),
        "planned_calls": planned,
        "terminal_calls": len(terminals),
        "terminal_status_counts": dict(status_counts),
        "failure_reasons": dict(failure_reasons),
        "coverage_reports": len(coverage),
        "coverage_complete_reports": sum(item["all_atoms_core_exactly_once"] for item in coverage),
        "by_arm": by_arm,
        "cross_arm": cross_arm,
        "human_semantic_audit": audit,
        "verdict": verdict,
        "verdict_limit": (
            "Semantic support and analysis-boundary recall require two-human gold "
            "adjudication; technical grounding alone cannot approve the instrument."
        ),
        "run_manifest_sha256": sha256_file(run / "orchestrator_manifest.json"),
        "suite_manifest_sha256": sha256_file(SUITE / "artifact_manifest.json"),
        "git_revision_at_run_start": orchestrator["git_revision_at_start"],
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "summary.json", summary)

    call_ledger_path = output / "call_ledger.csv"
    if call_rows:
        with call_ledger_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(call_rows[0]))
            writer.writeheader()
            writer.writerows(call_rows)
    raw_inventory = _raw_inventory(run)
    write_json(output / "raw_artifact_inventory.json", raw_inventory)
    write_text(
        output / "report.md",
        _report_markdown(summary, raw_inventory),
    )
    return summary


def _percentage(value: int, total: int) -> str:
    return f"{100 * value / total:.1f}%" if total else "NA"


def _report_markdown(summary: dict[str, Any], inventory: dict[str, Any]) -> str:
    lines = [
        "# E0 deterministic grounding bake-off",
        "",
        f"Verdict: `{summary['verdict']}`.",
        "",
        "This is a six-report development experiment. Every eligible report had "
        "prior Luna Light graph-profile exposure, so this result is not a sealed "
        "accuracy evaluation.",
        "",
        "## Technical results",
        "",
        f"- Planned/terminal calls: {summary['planned_calls']}/{summary['terminal_calls']}.",
        f"- Complete atom coverage: {summary['coverage_complete_reports']}/"
        f"{summary['coverage_reports']} reports.",
    ]
    for arm, metrics in summary["by_arm"].items():
        lines.extend(
            [
                f"- `{arm}` terminal validity: {metrics['ok_calls']}/"
                f"{metrics['terminal_calls']} "
                f"({_percentage(metrics['ok_calls'], metrics['terminal_calls'])}); "
                f"first-attempt validity {metrics['first_attempt_valid_calls']}/"
                f"{metrics['terminal_calls']}.",
                f"- `{arm}` repeat agreement: all-field "
                f"{metrics['all_field_exact_repeat_pairs']}/"
                f"{metrics['complete_repeat_pairs']}; decision-plus-grounding "
                f"{metrics['decision_and_grounding_exact_repeat_pairs']}/"
                f"{metrics['complete_repeat_pairs']}.",
            ]
        )
    cross_arm = summary["cross_arm"]
    lines.append(
        "- Cross-arm agreement after Python atom resolution: all-field "
        f"{cross_arm['all_field_exact_pairs']}/{cross_arm['complete_arm_pairs']}; "
        "decision-plus-grounding "
        f"{cross_arm['decision_and_grounding_exact_pairs']}/"
        f"{cross_arm['complete_arm_pairs']}."
    )
    lines.append(
        "- Wilson intervals in `summary.json` are call- or reference-level "
        "technical descriptions; scientific uncertainty will be clustered by report."
    )
    lines.extend(
        [
            "",
            "## Audit status",
            "",
            f"A blinded {summary['human_semantic_audit']['selected']}-reference "
            "audit set and separate reviewer forms were generated locally. Two "
            "independent human judgments and "
            "adjudication remain pending. Until then, this experiment establishes "
            "technical resolvability only.",
            "",
            "## Raw trace",
            "",
            f"The ignored raw run contains {inventory['file_count']} files "
            f"({inventory['total_bytes']} bytes). Its deterministic tree hash is "
            f"`{inventory['tree_sha256']}`. The accompanying JSON inventory records "
            "the path, byte size, and SHA-256 of every raw artifact.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    value = summarize(args.run, args.output)
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
