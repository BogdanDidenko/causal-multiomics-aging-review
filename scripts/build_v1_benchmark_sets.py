#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "protocol" / "screening" / "benchmarks" / "v1.0.0"
TITLE_SPLITS = (
    ("codebook_pilot_30.csv", 30),
    ("title_abstract_development_80.csv", 80),
    ("title_abstract_sealed_100.csv", 100),
)
TITLE_EXPERT_FIELDS = (
    "report_type",
    "bio_health_scope",
    "aging_process_relevance",
    "multiomics_evidence",
    "current_report_layer_use",
    "causal_basis",
    "primary_design_family",
    "expected_route",
    "first_failed_criterion",
)
FULL_TEXT_EXPERT_FIELDS = (
    "eligible",
    "aging_process_relevance",
    "multiomics_status",
    "identification_status",
    "primary_design_family",
    "causal_evidence_level",
    "final_study_label",
)
DESIGN_PATTERNS = (
    ("genetic_instrument", r"mendelian random|instrumental variable|\bsmr\b|\bheidi\b"),
    ("perturbation", r"crispr|knockout|knockdown|overexpression|perturb"),
    ("intervention", r"randomi[sz]ed|intervention|natural experiment|target trial"),
    ("mediation", r"mediat"),
    ("directed_model", r"causal discovery|bayesian network|structural equation|lingam|notears"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def record_id(row: dict[str, str]) -> str:
    for field in ("record_id", "canonical_id", "doi", "pmid", "source_record_id"):
        if value := row.get(field, "").strip():
            return value.lower()
    raise ValueError("Every benchmark candidate requires a stable identifier")


def design_stratum(text: str) -> str:
    for family, pattern in DESIGN_PATTERNS:
        if re.search(pattern, text, re.I):
            return family
    return "other_causal_anchor"


def retrieval_stratum(row: dict[str, str]) -> str:
    explicit = row.get("local_explicit_multiomics_match", "").lower() in {
        "1",
        "true",
        "yes",
    }
    pair = row.get("local_layer_pair_match", "").lower() in {"1", "true", "yes"}
    if explicit and pair:
        branch = "both"
    elif explicit:
        branch = "explicit"
    elif pair:
        branch = "layer_pair"
    else:
        branch = "unknown"
    abstract = row.get("abstract", "")
    thickness = "thin" if len(abstract) < 500 else "full"
    text = f"{row.get('title', '')} {abstract}"
    return f"{branch}|{thickness}|{design_stratum(text)}"


def deterministic_stratified_order(
    rows: list[dict[str, str]], seed: str
) -> list[dict[str, str]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[retrieval_stratum(row)].append(row)
    queues = {
        stratum: deque(
            sorted(
                items,
                key=lambda row: hashlib.sha256(
                    f"{seed}|{record_id(row)}".encode()
                ).hexdigest(),
            )
        )
        for stratum, items in groups.items()
    }
    ordered = []
    active = sorted(queues)
    while active:
        next_active = []
        for stratum in active:
            queue = queues[stratum]
            if queue:
                ordered.append(queue.popleft())
            if queue:
                next_active.append(stratum)
        active = next_active
    return ordered


def annotation_row(
    row: dict[str, str], split: str, expert_fields: tuple[str, ...]
) -> dict[str, str]:
    output = {
        "record_id": record_id(row),
        "split": split,
        "source": row.get("source", ""),
        "title": row.get("title", ""),
        "abstract": row.get("abstract", ""),
        "year": row.get("year", ""),
        "doi": row.get("doi", ""),
        "retrieval_stratum": retrieval_stratum(row),
        "full_text_path": row.get("full_text_path", ""),
    }
    for prefix in ("expert_1", "expert_2", "adjudicated"):
        output.update({f"{prefix}_{field}": "" for field in expert_fields})
    output.update(
        {
            "adjudication_reason": "",
            "human_override_of_model": "",
            "human_override_reason": "",
        }
    )
    return output


def write_rows(path: Path, rows: list[dict[str, str]], force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {path}; pass --force explicitly")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build disjoint v1 expert-annotation benchmark files"
    )
    parser.add_argument("input", type=Path, help="v1 candidate-frame CSV")
    parser.add_argument("--stage", choices=("title_abstract", "full_text"), required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", default="causal-multiomics-aging-v1")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source_rows = read_csv(args.input)
    unique: dict[str, dict[str, str]] = {}
    for row in source_rows:
        unique.setdefault(record_id(row), row)
    ordered = deterministic_stratified_order(list(unique.values()), args.seed)
    required = 210 if args.stage == "title_abstract" else 60
    if len(ordered) < required:
        raise SystemExit(f"Need {required} unique records; found {len(ordered)}")

    outputs: list[Path] = []
    cursor = 0
    if args.stage == "title_abstract":
        for filename, count in TITLE_SPLITS:
            split_rows = ordered[cursor : cursor + count]
            cursor += count
            path = args.output_dir / filename
            write_rows(
                path,
                [annotation_row(row, filename, TITLE_EXPERT_FIELDS) for row in split_rows],
                args.force,
            )
            outputs.append(path)
    else:
        path = args.output_dir / "full_text_benchmark_60.csv"
        write_rows(
            path,
            [
                annotation_row(row, "full_text_benchmark_60", FULL_TEXT_EXPERT_FIELDS)
                for row in ordered[:60]
            ],
            args.force,
        )
        outputs.append(path)

    manifest: dict[str, Any] = {
        "version": "1.0.0",
        "stage": args.stage,
        "sampling_method": "deterministic_round_robin_across_retrieval_strata",
        "seed": args.seed,
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "source_unique_records": len(unique),
        "outputs": [
            {
                "path": str(path),
                "sha256": sha256(path),
                "records": sum(1 for _ in path.open(encoding="utf-8")) - 1,
            }
            for path in outputs
        ],
        "gold_status": "pending_two_independent_experts_and_adjudication",
    }
    manifest_path = args.output_dir / f"{args.stage}_split_manifest.json"
    if manifest_path.exists() and not args.force:
        raise FileExistsError(f"Refusing to overwrite {manifest_path}")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"built stage={args.stage} records={required} outputs={len(outputs)}")


if __name__ == "__main__":
    main()
