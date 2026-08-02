#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

DESIGN_PATTERNS = (
    (
        "genetic_instrument",
        re.compile(
            r"Mendelian randomi[sz]ation|\bSMR\b|summary-data-based Mendelian|"
            r"instrumental variable|\bHEIDI\b",
            re.I,
        ),
    ),
    (
        "randomized_intervention",
        re.compile(
            r"randomi[sz]ed controlled trial|randomly assigned|random allocation",
            re.I,
        ),
    ),
    (
        "quasi_experiment",
        re.compile(
            r"natural experiment|difference.in.differences|regression discontinuity|"
            r"interrupted time series|target trial|marginal structural model",
            re.I,
        ),
    ),
    (
        "direct_perturbation",
        re.compile(
            r"\bCRISPR\b|knockout|knockdown|overexpression|gene deletion|"
            r"siRNA|shRNA|RNAi|genetic perturbation",
            re.I,
        ),
    ),
    (
        "formal_mediation",
        re.compile(
            r"causal mediation|mediation analysis|natural indirect effect|"
            r"mediated proportion|two-step Mendelian",
            re.I,
        ),
    ),
    (
        "temporal_identification",
        re.compile(r"Granger causality|cross-lagged|temporal causal", re.I),
    ),
    (
        "dag_scm",
        re.compile(r"directed acyclic graph|structural causal model|causal graph", re.I),
    ),
    (
        "sem",
        re.compile(r"genomic structural equation|structural equation model", re.I),
    ),
    (
        "bayesian_network",
        re.compile(r"causal Bayesian network|Bayesian network", re.I),
    ),
    (
        "causal_discovery_algorithm",
        re.compile(
            r"causal discovery|\bLiNGAM\b|\bNOTEARS\b|PC algorithm|FCI algorithm",
            re.I,
        ),
    ),
)
AGING_PATTERN = re.compile(
    r"biological ag(?:e|ing)|epigenetic ag(?:e|ing)|age acceleration|"
    r"longevity|life[- ]?span|health[- ]?span|cellular senescence|"
    r"rejuvenat|geroprotect|aging clock|ageing clock|ovarian aging|"
    r"reproductive aging|brain aging|proteomic aging",
    re.I,
)
CURRENT_REPORT_PATTERN = re.compile(
    r"\b(?:we|this study|here,? we)\s+(?:used|performed|applied|integrated|"
    r"analy[sz]ed|conducted|show|demonstrate|identify|investigated|employed|"
    r"examined|developed|report)",
    re.I,
)
NONEMPIRICAL_TITLE_PATTERN = re.compile(
    r"\b(?:review|protocol|perspective|editorial|commentary|knowledgebase|"
    r"database|resource|framework for predictive|insights from the .*symposium)\b",
    re.I,
)
NONEMPIRICAL_TYPE_PATTERN = re.compile(
    r"\b(?:review|editorial|commentary|protocol)\b", re.I
)
FAMILY_TARGETS = {
    "genetic_instrument": 55,
    "direct_perturbation": 35,
    "formal_mediation": 10,
    "randomized_intervention": 6,
    "quasi_experiment": 4,
    "temporal_identification": 3,
    "dag_scm": 2,
    "sem": 3,
    "bayesian_network": 1,
    "causal_discovery_algorithm": 1,
}
OUTPUT_FIELDS = (
    "candidate_id",
    "doi",
    "title",
    "year",
    "sources",
    "proposed_design_family",
    "omics_layers",
    "explicit_multiomics_match",
    "layer_pair_match",
    "formal_method_evidence",
    "aging_evidence",
    "algorithmic_score",
    "candidate_status",
    "expert_1_empirical_primary",
    "expert_1_aging_eligible",
    "expert_1_multiomics_eligible",
    "expert_1_causal_method_eligible",
    "expert_1_overall",
    "expert_2_empirical_primary",
    "expert_2_aging_eligible",
    "expert_2_multiomics_eligible",
    "expert_2_causal_method_eligible",
    "expert_2_overall",
    "adjudicated_empirical_primary",
    "adjudicated_aging_eligible",
    "adjudicated_multiomics_eligible",
    "adjudicated_causal_method_eligible",
    "adjudicated_status",
    "adjudicated_design_family",
    "adjudication_notes",
)
PENDING_ANNOTATION_FIELDS = (
    "expert_1_empirical_primary",
    "expert_1_aging_eligible",
    "expert_1_multiomics_eligible",
    "expert_1_causal_method_eligible",
    "expert_1_overall",
    "expert_2_empirical_primary",
    "expert_2_aging_eligible",
    "expert_2_multiomics_eligible",
    "expert_2_causal_method_eligible",
    "expert_2_overall",
    "adjudicated_empirical_primary",
    "adjudicated_aging_eligible",
    "adjudicated_multiomics_eligible",
    "adjudicated_causal_method_eligible",
    "adjudicated_status",
)


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def identifier(row: dict[str, str]) -> str:
    doi = row.get("doi", "").strip().casefold()
    return f"doi:{doi}" if doi else f"title:{normalized_title(row.get('title', ''))}"


def shortest_sentence(text: str, pattern: re.Pattern[str]) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    matching = [sentence.strip() for sentence in sentences if pattern.search(sentence)]
    return min(matching, key=len)[:500] if matching else ""


def score(row: dict[str, str], family: str, pattern: re.Pattern[str]) -> int:
    title = row.get("title", "")
    abstract = row.get("abstract", "")
    value = min(int(row.get("local_omics_layer_count") or 0), 4)
    value += 3 * bool(pattern.search(title))
    value += 3 * bool(AGING_PATTERN.search(title))
    value += 2 * truthy(row.get("local_explicit_multiomics_match", ""))
    value += 2 * bool(CURRENT_REPORT_PATTERN.search(abstract))
    value += family in {"genetic_instrument", "direct_perturbation"}
    return value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build an auditable, non-gold canonical-positive candidate pool"
    )
    parser.add_argument("input", type=Path, help="combined normalized pilot CSV")
    parser.add_argument("output", type=Path)
    parser.add_argument("--size", type=int, default=120)
    parser.add_argument("--minimum-verified-positives", type=int, default=100)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--generated-date", default=date.today().isoformat())
    parser.add_argument("--seed", default="causal-multiomics-aging-canonical-v1")
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        grouped[identifier(row)].append(row)

    by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for stable_id, occurrences in grouped.items():
        row = max(
            occurrences,
            key=lambda item: (
                not truthy(item.get("is_preprint", "")),
                bool(item.get("doi", "")),
                len(item.get("abstract", "")),
            ),
        )
        title = row.get("title", "")
        abstract = row.get("abstract", "")
        text = f"{title}. {abstract}"
        if not abstract or not AGING_PATTERN.search(text):
            continue
        if NONEMPIRICAL_TITLE_PATTERN.search(title):
            continue
        if NONEMPIRICAL_TYPE_PATTERN.search(row.get("document_type", "")):
            continue
        if not (
            truthy(row.get("local_explicit_multiomics_match", ""))
            or truthy(row.get("local_layer_pair_match", ""))
        ):
            continue
        matched = next(
            ((family, pattern) for family, pattern in DESIGN_PATTERNS if pattern.search(text)),
            None,
        )
        if not matched:
            continue
        family, pattern = matched
        if family != "genetic_instrument" and not CURRENT_REPORT_PATTERN.search(abstract):
            continue
        candidate_score = score(row, family, pattern)
        candidate = {
                "candidate_id": (
                    f"doi:{row['doi'].casefold()}" if row.get("doi") else stable_id
                ),
                "doi": row.get("doi", ""),
                "title": title,
                "year": row.get("year", ""),
                "sources": ";".join(sorted({item["source"] for item in occurrences})),
                "proposed_design_family": family,
                "omics_layers": row.get("local_omics_layers", ""),
                "explicit_multiomics_match": row.get(
                    "local_explicit_multiomics_match", ""
                ),
                "layer_pair_match": row.get("local_layer_pair_match", ""),
                "formal_method_evidence": shortest_sentence(text, pattern),
                "aging_evidence": shortest_sentence(text, AGING_PATTERN),
                "algorithmic_score": str(candidate_score),
                "candidate_status": "unreviewed_candidate_not_gold",
                "adjudicated_design_family": "",
                "adjudication_notes": "",
            }
        candidate.update({field: "pending" for field in PENDING_ANNOTATION_FIELDS})
        by_family[family].append(candidate)

    for candidates in by_family.values():
        candidates.sort(
            key=lambda row: (
                -int(row["algorithmic_score"]),
                hashlib.sha256(
                    f"{args.seed}|{row['candidate_id']}".encode()
                ).hexdigest(),
            )
        )

    selected = []
    selected_ids = set()
    for family, target in FAMILY_TARGETS.items():
        family_count = 0
        for row in by_family.get(family, []):
            if row["candidate_id"] in selected_ids:
                continue
            selected.append(row)
            selected_ids.add(row["candidate_id"])
            family_count += 1
            if family_count == target:
                break
    if len(selected) < args.size:
        remainder = [
            row
            for candidates in by_family.values()
            for row in candidates
            if row["candidate_id"] not in selected_ids
        ]
        remainder.sort(
            key=lambda row: (
                -int(row["algorithmic_score"]),
                hashlib.sha256(
                    f"{args.seed}|fill|{row['candidate_id']}".encode()
                ).hexdigest(),
            )
        )
        selected.extend(remainder[: args.size - len(selected)])
    selected = selected[: args.size]
    selected.sort(key=lambda row: (row["proposed_design_family"], row["title"]))

    if len(selected) < args.size:
        raise SystemExit(f"Requested {args.size} candidates; found {len(selected)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(selected)
    counts = {family: 0 for family in FAMILY_TARGETS}
    for row in selected:
        counts[row["proposed_design_family"]] += 1
    manifest_path = args.manifest or args.output.with_suffix(".manifest.json")
    manifest = {
        "protocol_version": "1.0.0",
        "generated_date": args.generated_date,
        "status": "pending_two_expert_adjudication",
        "candidate_pool_is_gold_standard": False,
        "candidate_count": len(selected),
        "required_adjudicated_positive_count": args.minimum_verified_positives,
        "selection_seed": args.seed,
        "source": {
            "path": str(args.input),
            "sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
            "record_count": len(source_rows),
        },
        "candidate_pool": {
            "path": str(args.output),
            "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        },
        "design_family_counts": counts,
        "represented_design_families": [
            family for family, count in counts.items() if count
        ],
        "unrepresented_design_families": [
            family for family, count in counts.items() if not count
        ],
        "expert_fields": {
            field: "pending" for field in PENDING_ANNOTATION_FIELDS
        },
        "freeze_rule": (
            "Do not freeze database queries until at least "
            f"{args.minimum_verified_positives} candidates are "
            "independently reviewed by two experts and adjudicated as eligible "
            "canonical positives, with supplemental retrieval for missing design "
            "families."
        ),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(f"candidate_pool={len(selected)} family_counts={counts}")


if __name__ == "__main__":
    main()
