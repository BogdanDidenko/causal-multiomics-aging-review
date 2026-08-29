#!/usr/bin/env python3
"""Build a compact two-checkpoint causal-extraction audit package."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_extraction import canonical_json

REPO = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def wilson(successes: int, total: int) -> dict[str, float | int]:
    if total == 0:
        return {"successes": successes, "total": total, "proportion": 0.0}
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    radius = (
        z
        * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
        / denominator
    )
    return {
        "successes": successes,
        "total": total,
        "proportion": p,
        "wilson_95_low": max(0.0, centre - radius),
        "wilson_95_high": min(1.0, centre + radius),
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
    five_exact = sum(row["five_run_exact"] for row in completed)
    first_three_exact = sum(
        exact(row["decision_hashes"][:3]) for row in completed
    )
    status_exact = sum(exact(row["candidate_statuses"]) for row in completed)
    level_exact = sum(exact(row["derived_outputs"]) for row in completed)
    lost_after_three = sum(
        exact(row["decision_hashes"][:3]) and not row["five_run_exact"]
        for row in completed
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
        "sampled_candidates": len(candidates),
        "sampled_candidates_with_five_valid_runs": len(completed),
        "discovery_terminal_statuses": dict(discovery_statuses),
        "discovery_primary_grounding_failures": primary_grounding_failures,
        "discovery_retry_recoveries": (
            primary_grounding_failures
            - discovery_statuses.get("grounding_failure", 0)
        ),
        "classification_terminal_statuses": dict(classifier_statuses),
        "five_run_all_tracked_fields_exact": wilson(five_exact, len(completed)),
        "first_three_all_tracked_fields_exact": wilson(
            first_three_exact, len(completed)
        ),
        "five_run_candidate_status_exact": wilson(status_exact, len(completed)),
        "five_run_derived_level_exact": wilson(level_exact, len(completed)),
        "candidates_exact_after_three_but_not_five": lost_after_three,
        "selected_candidates": selected,
        "raw_artifact_inventory": tree_inventory(root),
    }


def pct(metric: dict[str, Any]) -> str:
    return f"{100 * metric['proportion']:.1f}%"


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
        "quote-grounding and five-run exact-agreement gates. These checkpoints "
        "measure stability and technical validity; they contain no expert gold "
        "labels and make no accuracy claim.",
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
    ]
    for label, key in rows:
        lines.append(f"| {label} | {a[key]} | {b[key]} |")
    for label, key in (
        ("All tracked fields exact, 5 runs", "five_run_all_tracked_fields_exact"),
        ("All tracked fields exact, first 3 runs", "first_three_all_tracked_fields_exact"),
        ("Candidate status exact, 5 runs", "five_run_candidate_status_exact"),
        ("Derived Level exact, 5 runs", "five_run_derived_level_exact"),
    ):
        lines.append(
            f"| {label} | {a[key]['successes']}/{a[key]['total']} "
            f"({pct(a[key])}) | {b[key]['successes']}/{b[key]['total']} "
            f"({pct(b[key])}) |"
        )
    lines.extend(
        [
            "",
            "Wilson 95% intervals are stored in the JSON report for every "
            "proportion. A lost 2 candidates between the three-run and five-run "
            "all-field gates; B lost 1.",
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
            "## Interpretation",
            "",
            "Derived Levels were much more stable than complete criterion-level "
            "profiles. This does not rescue the instrument because detailed fields "
            "are required for auditable evidence synthesis. The atomic discovery "
            "contract also generated too many candidates for a five-run production "
            "deployment without a separately validated consolidation or batching "
            "stage.",
            "",
            "Checkpoint A was used to identify runner defects and the feasibility "
            "amendment. Checkpoint B received classifier outputs only after those "
            "Python-only fixes were committed. Prompts, schemas, codebook, model, "
            "reasoning effort, and selected reports were unchanged.",
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
    (args.output / "two_sample_stability.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
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
