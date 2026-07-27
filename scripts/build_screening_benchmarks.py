#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.audit import sha256_file, write_manifest

FIELDS = [
    "canonical_id",
    "title",
    "abstract",
    "year",
    "doi",
    "pmid",
    "provenance_sources",
    "sampling_stratum",
    "expert_report_type",
    "expert_bio_health_scope",
    "expert_aging_process_relevance",
    "expert_aging_role",
    "expert_multiomics_status",
    "expert_integration_mode",
    "expert_identification_status",
    "expert_design_families",
    "expert_expected_decision",
    "expert_exclusion_code",
    "expert_notes",
]
MAX_ABSTRACT_CHARS = 5000

GENETIC_INSTRUMENT_RE = re.compile(
    r"\b(?:Mendelian randomi[sz]ation|instrumental variable|genetic instrument|"
    r"\bSMR\b|\bHEIDI\b)\b",
    re.IGNORECASE,
)
INTERVENTION_RE = re.compile(
    r"\b(?:randomi[sz]ed|trial|intervention|treatment|supplement|dietary|"
    r"perturb|CRISPR|knockout|knockdown|overexpression|rejuvenat|senolytic)\w*",
    re.IGNORECASE,
)
MEDIATION_DIRECTED_RE = re.compile(
    r"\b(?:mediat(?:e|ed|es|ing|ion)|Bayesian network|directed acyclic graph|"
    r"structural equation|Granger causality|causal network)\b",
    re.IGNORECASE,
)
CAUSAL_RE = re.compile(r"\b(?:causal|causality)\w*", re.IGNORECASE)
NONEMPIRICAL_RE = re.compile(
    r"\b(?:review|editorial|perspective|commentary|protocol|bibliometric|"
    r"framework|software|resource|database)\b",
    re.IGNORECASE,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def normalized_text(value: str) -> str:
    return " ".join(value.split())


def canonical_id(row: dict[str, str]) -> str:
    if doi := row.get("doi", "").strip().lower():
        return f"doi:{doi}"
    if pmid := row.get("pmid", "").strip():
        return f"pmid:{pmid}"
    title = normalized_text(row.get("title", "")).casefold()
    year = row.get("year", "").strip()
    digest = hashlib.sha256(f"{title}|{year}".encode()).hexdigest()[:20]
    return f"title-year-sha256:{digest}"


def stable_key(identifier: str, seed: str) -> str:
    return hashlib.sha256(f"{seed}|{identifier}".encode()).hexdigest()


def is_true(row: dict[str, str], field: str) -> bool:
    return row.get(field, "").strip().lower() == "true"


def sampling_stratum(row: dict[str, str]) -> str:
    text = f"{row.get('title', '')} {row.get('abstract', '')}"
    if len(normalized_text(row.get("abstract", ""))) < 400:
        return "thin_abstract_boundary"
    if NONEMPIRICAL_RE.search(row.get("title", "")):
        return "possible_nonempirical"
    if GENETIC_INSTRUMENT_RE.search(text):
        return "genetic_instrument"
    if INTERVENTION_RE.search(text):
        return "intervention_or_perturbation"
    if MEDIATION_DIRECTED_RE.search(text):
        return "mediation_or_directed_model"
    if CAUSAL_RE.search(text):
        return "other_explicit_causal"
    missing = [
        name
        for name, field in (
            ("multiomics", "local_multiomics_match"),
            ("aging", "local_aging_match"),
            ("causal", "local_causal_anchor_match"),
        )
        if not is_true(row, field)
    ]
    if missing:
        return "metadata_boundary_missing_" + "_".join(missing)
    return "other_three_block"


def prepare_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    prepared: list[dict[str, str]] = []
    for row in rows:
        title = normalized_text(row.get("title", ""))
        abstract = normalized_text(row.get("abstract", ""))
        if not title or not abstract or len(abstract) > MAX_ABSTRACT_CHARS:
            continue
        prepared.append(
            {
                **row,
                "canonical_id": canonical_id(row),
                "title": title,
                "abstract": abstract,
                "sampling_stratum": sampling_stratum(row),
            }
        )
    return prepared


def diverse_sample(
    rows: list[dict[str, str]],
    count: int,
    seed: str,
    excluded_ids: set[str],
) -> list[dict[str, str]]:
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["canonical_id"] in excluded_ids:
            continue
        buckets[row["sampling_stratum"]].append(row)
    for name, bucket in buckets.items():
        bucket.sort(key=lambda row: stable_key(row["canonical_id"], f"{seed}|{name}"))

    selected: list[dict[str, str]] = []
    active = sorted(buckets)
    while active and len(selected) < count:
        remaining: list[str] = []
        for name in active:
            if buckets[name] and len(selected) < count:
                selected.append(buckets[name].pop(0))
            if buckets[name]:
                remaining.append(name)
        active = remaining
    if len(selected) != count:
        raise ValueError(f"Requested {count} records but selected {len(selected)}")
    return selected


def annotation_row(row: dict[str, str]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in FIELDS}


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(annotation_row(row) for row in rows)


def stratum_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["sampling_stratum"]] += 1
    return dict(sorted(counts.items()))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build clean, disjoint annotation candidates from the aging corpus"
    )
    parser.add_argument("corpus", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--seed", default="causal-multiomics-aging-v0.1.0")
    args = parser.parse_args()

    source_rows = read_csv(args.corpus)
    rows = prepare_rows(source_rows)
    canonical_doi = "10.1038/s41467-023-37729-w"
    anchor = next((row for row in rows if row.get("doi") == canonical_doi), None)
    if anchor is None:
        raise ValueError(f"Canonical positive missing: {canonical_doi}")

    development = [anchor]
    development.extend(
        diverse_sample(
            rows,
            24,
            f"{args.seed}|development",
            {anchor["canonical_id"]},
        )
    )
    used = {row["canonical_id"] for row in development}
    regression = diverse_sample(
        rows,
        116,
        f"{args.seed}|regression",
        used,
    )
    used.update(row["canonical_id"] for row in regression)
    boundary_pilot = diverse_sample(
        rows,
        25,
        f"{args.seed}|sealed-holdout",
        used,
    )
    used.update(row["canonical_id"] for row in boundary_pilot)
    quarantined_holdout = diverse_sample(
        rows,
        25,
        f"{args.seed}|sealed-holdout-v2",
        used,
    )
    used.update(row["canonical_id"] for row in quarantined_holdout)
    holdout = diverse_sample(
        rows,
        25,
        f"{args.seed}|sealed-holdout-v3",
        used,
    )

    outputs = {
        "high_signal_development_25.csv": development,
        "title_abstract_boundary_pilot_25.csv": boundary_pilot,
        "title_abstract_regression_116.csv": regression,
        "title_abstract_holdout_v2_quarantined_25.csv": quarantined_holdout,
        "title_abstract_stability_holdout_25.csv": holdout,
    }
    for name, selected in outputs.items():
        write_csv(args.output_dir / name, selected)

    write_manifest(
        args.output_dir / "manifest.json",
        {
            "benchmark_version": "candidate_sets_v0.1.0",
            "status": "expert_annotation_pending",
            "source_policy": (
                "Fresh deterministic sampling from the 2026-07-27 aging search "
                "corpus; no legacy decisions or labels were imported."
            ),
            "input_file": str(args.corpus),
            "input_sha256": sha256_file(args.corpus),
            "eligible_sampling_pool": len(rows),
            "sampling_input_limits": {
                "requires_title": True,
                "requires_abstract": True,
                "maximum_abstract_chars": MAX_ABSTRACT_CHARS,
                "oversized_abstract_records_excluded_from_sampling": sum(
                    len(normalized_text(row.get("abstract", ""))) > MAX_ABSTRACT_CHARS
                    for row in source_rows
                ),
            },
            "seed": args.seed,
            "disjoint_sets": True,
            "canonical_positive_in_development": canonical_doi,
            "counts": {name: len(selected) for name, selected in outputs.items()},
            "strata": {
                name: stratum_counts(selected) for name, selected in outputs.items()
            },
            "output_sha256": {
                name: sha256_file(args.output_dir / name) for name in outputs
            },
            "ground_truth_policy": (
                "All expert fields are blank. Development and boundary pilot may be "
                "inspected during prompt iteration. Holdout v2 was quarantined after "
                "accidental partial disclosure. Regression and holdout v3 remain "
                "unseen until the corresponding evaluation phase."
            ),
        },
    )


if __name__ == "__main__":
    main()
