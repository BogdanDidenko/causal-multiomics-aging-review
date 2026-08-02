#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT
    / "data/searches/pilots/2026-08-02-v1.0.0/normalized/all_sources.csv"
)
DEFAULT_OUTPUT = ROOT / "protocol/screening/ablations/v1.1.0/samples"
SEED = "causal-multiomics-aging-ablation-v1.1.0"
DESIGN_PATTERNS = (
    ("genetic_instrument", r"mendelian random|instrumental variable|\bsmr\b|\bheidi\b"),
    ("direct_perturbation", r"crispr|knockout|knockdown|overexpression|perturb"),
    (
        "randomized_or_quasi_intervention",
        r"randomi[sz]ed|natural experiment|target trial|difference.in.difference|"
        r"regression discontinuity|interrupted time series",
    ),
    ("formal_mediation", r"mediat"),
    (
        "formal_directed_model",
        r"causal discovery|bayesian network|structural equation|\blingam\b|"
        r"\bnotears\b|directed acyclic|\bpc algorithm\b|\bfci\b|\bges\b",
    ),
    ("other_intervention", r"intervention|treatment|trial"),
)
OUTPUT_FIELDS = (
    "record_id",
    "source",
    "title",
    "abstract",
    "year",
    "document_type",
    "doi",
    "source_record_id",
    "retrieval_stratum",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_doi(value: str) -> str:
    normalized = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    return normalized


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def identity_keys(row: dict[str, str]) -> set[str]:
    keys = set()
    if doi := normalize_doi(row.get("doi", "")):
        keys.add(f"doi:{doi}")
    if title := normalize_title(row.get("title", "")):
        keys.add(f"title:{title}")
    return keys


def stable_id(row: dict[str, str]) -> str:
    doi = normalize_doi(row.get("doi", ""))
    if doi:
        return f"doi:{doi}"
    source_id = row.get("source_record_id", "").strip()
    if source_id:
        return f"{row.get('source', 'source').casefold()}:{source_id}"
    title = normalize_title(row.get("title", ""))
    return "title:" + hashlib.sha256(title.encode()).hexdigest()[:20]


def truthy(value: str) -> bool:
    return value.strip().casefold() in {"1", "true", "yes"}


def retrieval_stratum(row: dict[str, str]) -> str:
    explicit = truthy(row.get("local_explicit_multiomics_match", ""))
    pair = truthy(row.get("local_layer_pair_match", ""))
    if explicit and pair:
        branch = "both"
    elif explicit:
        branch = "explicit_only"
    elif pair:
        branch = "layer_pair_only"
    else:
        branch = "neither"

    text = f"{row.get('title', '')} {row.get('abstract', '')}"
    family = "other_causal_or_boundary"
    for label, pattern in DESIGN_PATTERNS:
        if re.search(pattern, text, re.I):
            family = label
            break
    abstract_length = len(row.get("abstract", ""))
    thickness = "thin" if abstract_length < 700 else "medium" if abstract_length < 1600 else "long"
    aging = "aging_anchor" if truthy(row.get("local_aging_match", "")) else "aging_boundary"
    causal = (
        "causal_anchor"
        if truthy(row.get("local_causal_anchor_match", ""))
        else "causal_boundary"
    )
    return "|".join((branch, family, thickness, aging, causal))


def exclusion_keys() -> tuple[set[str], list[dict[str, Any]]]:
    paths = sorted((ROOT / "protocol/screening/benchmarks").rglob("*.csv"))
    paths.append(
        ROOT / "protocol/search_calibration/v1.0.0/canonical_positive_candidates_120.csv"
    )
    keys: set[str] = set()
    audit = []
    for path in paths:
        rows = read_csv(path)
        before = len(keys)
        for row in rows:
            keys.update(identity_keys(row))
        audit.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "rows": len(rows),
                "new_identity_keys": len(keys) - before,
            }
        )
    return keys, audit


def stratified_order(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[retrieval_stratum(row)].append(row)
    queues = {
        stratum: deque(
            sorted(
                items,
                key=lambda row: hashlib.sha256(
                    f"{SEED}|{stable_id(row)}".encode()
                ).hexdigest(),
            )
        )
        for stratum, items in groups.items()
    }
    ordered = []
    active = sorted(queues)
    while active:
        following = []
        for stratum in active:
            queue = queues[stratum]
            if queue:
                ordered.append(queue.popleft())
            if queue:
                following.append(stratum)
        active = following
    return ordered


def output_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "record_id": stable_id(row),
        "source": row.get("source", ""),
        "title": row.get("title", ""),
        "abstract": row.get("abstract", ""),
        "year": row.get("year", ""),
        "document_type": row.get("document_type", ""),
        "doi": normalize_doi(row.get("doi", "")),
        "source_record_id": row.get("source_record_id", ""),
        "retrieval_stratum": retrieval_stratum(row),
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build disjoint prompt-ablation sets")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--records-per-set", type=int, default=60)
    args = parser.parse_args()

    source_rows = read_csv(args.input)
    excluded, exclusion_audit = exclusion_keys()
    unique: dict[str, dict[str, str]] = {}
    removed_prior = 0
    removed_incomplete = 0
    for row in source_rows:
        if not row.get("title", "").strip() or len(row.get("abstract", "").strip()) < 200:
            removed_incomplete += 1
            continue
        if identity_keys(row) & excluded:
            removed_prior += 1
            continue
        key = sorted(identity_keys(row))[0] if identity_keys(row) else stable_id(row)
        incumbent = unique.get(key)
        if incumbent is None or len(row.get("abstract", "")) > len(incumbent.get("abstract", "")):
            unique[key] = row

    ordered = stratified_order(list(unique.values()))
    required = 2 * args.records_per_set
    if len(ordered) < required:
        raise SystemExit(f"Need {required} eligible unique records; found {len(ordered)}")
    selected = ordered[:required]
    development = [output_row(row) for row in selected[0::2]][: args.records_per_set]
    holdout = [output_row(row) for row in selected[1::2]][: args.records_per_set]
    development_ids = {row["record_id"] for row in development}
    holdout_ids = {row["record_id"] for row in holdout}
    if development_ids & holdout_ids:
        raise AssertionError("Development and holdout sets are not disjoint")

    development_path = args.output_dir / f"development_{args.records_per_set}.csv"
    holdout_path = args.output_dir / f"sealed_holdout_{args.records_per_set}.csv"
    write_csv(development_path, development)
    write_csv(holdout_path, holdout)
    manifest = {
        "experiment_id": "title_abstract_prompt_ablation_v1.1.0",
        "sampling_seed": SEED,
        "sampling_method": (
            "deterministic_round_robin_over_retrieval_strata_then_paired_alternation"
        ),
        "input": str(args.input.resolve().relative_to(ROOT)),
        "input_sha256": sha256(args.input),
        "source_rows": len(source_rows),
        "eligible_unique_after_exclusions": len(unique),
        "removed_incomplete_abstract_rows": removed_incomplete,
        "removed_prior_sample_rows": removed_prior,
        "prior_sample_exclusions": exclusion_audit,
        "development": {
            "path": str(development_path.relative_to(ROOT)),
            "sha256": sha256(development_path),
            "records": len(development),
            "strata": dict(
                sorted(
                    Counter(row["retrieval_stratum"] for row in development).items()
                )
            ),
        },
        "sealed_holdout": {
            "path": str(holdout_path.relative_to(ROOT)),
            "sha256": sha256(holdout_path),
            "records": len(holdout),
            "strata": dict(sorted(Counter(row["retrieval_stratum"] for row in holdout).items())),
            "status": "sealed_unopened_until_prompt_freeze",
        },
        "identity_overlap_count": 0,
        "gold_labels": "none; stability experiment only",
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"development={len(development)} holdout={len(holdout)} "
        f"eligible_unique={len(unique)}"
    )


if __name__ == "__main__":
    main()
