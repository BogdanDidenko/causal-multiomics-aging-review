#!/usr/bin/env python3
"""Build a compact two-checkpoint causal-extraction audit package."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_extraction import canonical_json

REPO = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def observed_rate(successes: int, total: int) -> dict[str, float | int | None | str]:
    """Return a descriptive rate without an invalid candidate-level interval."""

    return {
        "successes": successes,
        "total": total,
        "proportion": successes / total if total else None,
        "confidence_interval": None,
        "confidence_interval_reason": ("not_computed: candidates are clustered within reports"),
    }


def tree_inventory(root: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    suffixes: Counter[str] = Counter()
    total_bytes = 0
    for path in files:
        content = path.read_bytes()
        relative = str(path.relative_to(root))
        file_hash = hashlib.sha256(content).hexdigest()
        digest.update(f"{relative}\t{file_hash}\n".encode())
        suffixes[path.suffix or "<none>"] += 1
        total_bytes += len(content)
    return {
        "root": str(root.relative_to(REPO)),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "tree_sha256": digest.hexdigest(),
        "suffix_counts": dict(sorted(suffixes.items())),
    }


def exact(values: list[Any]) -> bool:
    return len({canonical_json(value) for value in values}) == 1


def repeated_nonempty_exact(values: list[Any]) -> bool:
    """Require every repeat to contain an output before testing exact agreement."""

    return bool(values) and all(bool(value) for value in values) and exact(values)


def checkpoint_summary(checkpoint: str, root: Path) -> dict[str, Any]:
    candidates = read_jsonl(root / "reports/candidate_stability.jsonl")
    reports = read_jsonl(root / "reports/report_stability.jsonl")
    completed = [row for row in candidates if row["valid_response_runs"] == 5]
    classifier_statuses = Counter(
        read_json(path)["status"]
        for path in root.glob("fixed_candidate_classifier/**/terminal.json")
    )
    discovery_statuses = Counter(
        read_json(path)["status"]
        for stage in ("open_claim_discovery", "dense_claim_coverage")
        for path in root.glob(f"{stage}/**/terminal.json")
    )
    primary_grounding_failures = sum(
        not read_json(path).get("grounding_valid", False)
        and read_json(path).get("schema_valid", False)
        and read_json(path).get("identity_valid", False)
        for stage in ("open_claim_discovery", "dense_claim_coverage")
        for path in root.glob(f"{stage}/**/attempt-01/validation.json")
    )
    inventory_candidates = sum(row["inventory_candidate_count"] for row in reports)
    incomplete_inventory_candidates = sum(
        row["inventory_candidate_count"]
        for row in reports
        if not row["grounded_discovery_complete"]
    )
    five_exact = sum(row["five_run_exact"] for row in completed)
    status_exact = sum(exact(row["candidate_statuses"]) for row in completed)
    level_evaluable = [
        row
        for row in completed
        if len(row["derived_outputs"]) == 5
        and all(bool(output) for output in row["derived_outputs"])
    ]
    level_exact = sum(repeated_nonempty_exact(row["derived_outputs"]) for row in level_evaluable)
    completed_statuses = Counter(
        status for row in completed for status in row["candidate_statuses"]
    )
    selected = []
    for path in sorted(root.glob("frozen_candidates/*/classification_sample.json")):
        selected.append(read_json(path))
    return {
        "checkpoint": checkpoint,
        "reports": len(reports),
        "reports_with_incomplete_grounded_discovery": sum(
            row["manual_review_required"] for row in reports
        ),
        "inventory_candidates": inventory_candidates,
        "inventory_candidates_in_incomplete_discovery_reports": (incomplete_inventory_candidates),
        "inventory_fraction_in_incomplete_discovery_reports": (
            incomplete_inventory_candidates / inventory_candidates if inventory_candidates else None
        ),
        "sampled_candidates": len(candidates),
        "sampled_candidates_with_five_valid_runs": len(completed),
        "sampled_candidates_excluded_from_five_run_analysis": (len(candidates) - len(completed)),
        "discovery_terminal_statuses": dict(discovery_statuses),
        "discovery_primary_grounding_failures": primary_grounding_failures,
        "discovery_retry_recoveries": (
            primary_grounding_failures - discovery_statuses.get("grounding_failure", 0)
        ),
        "classification_terminal_statuses": dict(classifier_statuses),
        "analysis_set_candidate_statuses": dict(completed_statuses),
        "five_run_legacy_payload_exact": observed_rate(five_exact, len(completed)),
        "five_run_candidate_status_exact": observed_rate(status_exact, len(completed)),
        "five_run_level_evaluable_candidates": len(level_evaluable),
        "five_run_derived_level_exact": observed_rate(level_exact, len(level_evaluable)),
        "first_three_policy_comparison": {
            "status": "withdrawn",
            "reason": (
                "the legacy comparison conditioned the three-run estimate on "
                "survival through five valid grounded runs"
            ),
        },
        "selected_candidates": selected,
        "raw_artifact_inventory": tree_inventory(root),
    }


def pct(metric: dict[str, Any]) -> str:
    proportion = metric["proportion"]
    if proportion is None:
        return "not estimable"
    return f"{100 * proportion:.1f}%"


def metric_cell(metric: dict[str, Any]) -> str:
    if metric["total"] == 0:
        return "not estimable (0 candidates)"
    return f"{metric['successes']}/{metric['total']} ({pct(metric)})"


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Two-sample causal-extraction stability checkpoint",
        "",
        f"Instrument: `{result['instrument']}`. Model: `{result['model']}` with "
        f"reasoning effort `{result['reasoning_effort']}`.",
        "",
        "## Verdict",
        "",
        "**FAIL.** The release candidate did not satisfy the prespecified 100% "
        "quote-grounding and five-run exact-agreement gates. Its scientific "
        "classification behaviour was not measured adequately. All v0.1.1 "
        "candidate records and derived Levels are excluded from scientific "
        "synthesis.",
        "",
        "This report was corrected after an independent Opus 5 audit found that "
        "the legacy derived-Level statistic treated repeated empty outputs as "
        "agreement. The raw artifacts and Git history remain unchanged.",
        "",
        "## Results",
        "",
        "| Metric | A (15 reports) | B (15 reports) |",
        "|---|---:|---:|",
    ]
    a, b = result["checkpoints"]
    rows = [
        ("Frozen atomic candidates", "inventory_candidates"),
        ("Classifier sample", "sampled_candidates"),
        ("Candidates with 5 valid runs", "sampled_candidates_with_five_valid_runs"),
        (
            "Reports with incomplete grounded discovery",
            "reports_with_incomplete_grounded_discovery",
        ),
        (
            "Candidates excluded from the 5-run analysis",
            "sampled_candidates_excluded_from_five_run_analysis",
        ),
    ]
    for label, key in rows:
        lines.append(f"| {label} | {a[key]} | {b[key]} |")
    for label, key in (
        (
            "Legacy payload exact among 5-run survivors",
            "five_run_legacy_payload_exact",
        ),
        ("Candidate status exact among 5-run survivors", "five_run_candidate_status_exact"),
        (
            "Derived Level exact where all 5 runs produced a claim record",
            "five_run_derived_level_exact",
        ),
    ):
        lines.append(f"| {label} | {metric_cell(a[key])} | {metric_cell(b[key])} |")
    lines.extend(
        [
            "",
            "The legacy payload metric includes free-text fields and candidate-boundary "
            "payloads. It is retained only as an instrument-development observation. "
            "No confidence intervals are reported because candidates are clustered "
            "within reports.",
            "",
            "The prior three-versus-five comparison is withdrawn because it estimated "
            "the three-run rate only among candidates that survived five grounded runs.",
            "",
            "## Corrected derived-Level interpretation",
            "",
            f"Checkpoint A produced a claim record in all five runs for "
            f"{a['five_run_level_evaluable_candidates']} candidates. Checkpoint B "
            f"did so for {b['five_run_level_evaluable_candidates']} candidate; its "
            "Levels were `3, 3, 3, 2, 3`. The previous `20/20` and `15/16` figures "
            "compared empty derived-output lists and are withdrawn.",
            "",
            "Candidate-status distributions within the five-valid-run analysis sets "
            f"were `{a['analysis_set_candidate_statuses']}` for A and "
            f"`{b['analysis_set_candidate_statuses']}` for B. Agreement was dominated "
            "by `duplicate_or_overlapping`, so it does not estimate stability of the "
            "criterion-level causal classification.",
            "",
            "## Technical audit",
            "",
            f"Discovery produced {a['inventory_candidates']} candidates in A and "
            f"{b['inventory_candidates']} in B. Primary quote-grounding failures "
            f"were {a['discovery_primary_grounding_failures']} and "
            f"{b['discovery_primary_grounding_failures']}; one retry recovered "
            f"{a['discovery_retry_recoveries']} and "
            f"{b['discovery_retry_recoveries']}, respectively.",
            "",
            f"Classifier terminal statuses were `{a['classification_terminal_statuses']}` "
            f"for A and `{b['classification_terminal_statuses']}` for B. Invalid "
            "responses remain in denominators and are excluded from automatic "
            "scientific synthesis.",
            "",
            f"Reports with known-incomplete discovery contained "
            f"{a['inventory_candidates_in_incomplete_discovery_reports']}/"
            f"{a['inventory_candidates']} "
            f"({a['inventory_fraction_in_incomplete_discovery_reports']:.1%}) "
            f"of A's inventory and "
            f"{b['inventory_candidates_in_incomplete_discovery_reports']}/"
            f"{b['inventory_candidates']} "
            f"({b['inventory_fraction_in_incomplete_discovery_reports']:.1%}) "
            "of B's inventory.",
            "",
            "## Interpretation",
            "",
            "The atomic discovery contract generated 86 to 103 candidates per report "
            "on average and made duplicate disposition the classifier's dominant task. "
            "The next instrument must use a causal analysis as its primary unit, with "
            "reported contrasts represented as child rows.",
            "",
            "Checkpoint A is the same 15-report sample used for codebook development "
            "and prompt smoke testing. It is in-sample. Checkpoint B is disjoint but "
            "remains a technical-feasibility checkpoint without expert gold labels. "
            "The A-versus-B comparison is not a replication estimate.",
            "",
            "These artifacts remain useful for the methodological postmortem: atomic "
            "unit infeasibility, grounding-failure taxonomy, runner defects, and the "
            "failure of free-text exact-agreement gates. They provide no scientific "
            "causal findings.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--a",
        type=Path,
        default=REPO / "data/causal_extraction/v0.1.1-rc1/checkpoint_A_15_run1",
    )
    parser.add_argument(
        "--b",
        type=Path,
        default=REPO / "data/causal_extraction/v0.1.1-rc1/checkpoint_B_15_run1",
    )
    args = parser.parse_args()
    result = {
        "instrument": "causal_extraction/v0.1.1-rc1",
        "model": "gpt-5.6-terra",
        "reasoning_effort": "medium",
        "classification_repeats": 5,
        "classification_sampling": {
            "reports_per_checkpoint": 15,
            "candidates_per_report": 2,
            "seed": "20260829-route-balanced-stability",
        },
        "correction": {
            "date": "2026-08-29",
            "status": "corrected_after_independent_audit",
            "reason": (
                "legacy derived-level agreement counted repeated empty outputs as "
                "successful agreement"
            ),
            "scientific_synthesis_permission": "rejected",
        },
        "checkpoints": [
            checkpoint_summary("A", args.a.resolve()),
            checkpoint_summary("B", args.b.resolve()),
        ],
        "acceptance": {
            "quote_grounding_100_percent": False,
            "five_run_all_tracked_fields_100_percent": False,
            "overall": "fail",
        },
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "two_sample_stability.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output / "two_sample_stability.md").write_text(render_markdown(result), encoding="utf-8")
    for checkpoint, source in (("A", args.a), ("B", args.b)):
        destination = args.output / f"checkpoint_{checkpoint}"
        destination.mkdir(exist_ok=True)
        for name in (
            "candidate_stability.jsonl",
            "report_stability.jsonl",
            "stability_summary.json",
        ):
            (destination / name).write_bytes((source / "reports" / name).read_bytes())
        (destination / "orchestrator_manifest.json").write_bytes(
            (source / "orchestrator_manifest.json").read_bytes()
        )
    print(json.dumps(result["acceptance"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
