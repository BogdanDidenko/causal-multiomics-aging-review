#!/usr/bin/env python3
"""Build a deterministic graph index for article-structure exploration.

The output is exploratory. Docling Graph nodes are evidence-location candidates,
not final causal extraction or eligibility judgments.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


GRAPH_ROOTS = (
    "data/full_text_graph/v1.0.0_luna_light",
    "data/full_text_graph/v1.1.0_oversized_20k_seek65_luna_light",
    "data/full_text_graph/v1.2.0_agent_recovery17_luna_light",
)


def normalize_doi(value: str) -> str:
    return value.strip().lower().removeprefix("https://doi.org/").removeprefix("doi:")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def graph_candidates(repo: Path) -> dict[str, list[dict[str, Any]]]:
    by_doi: dict[str, list[dict[str, Any]]] = {}
    for relative_root in GRAPH_ROOTS:
        graph_root = repo / relative_root
        for row in load_jsonl(graph_root / "run_manifest.jsonl"):
            if row.get("status") != "success" or not row.get("graph_path"):
                continue
            doi = normalize_doi(str(row.get("doi", "")))
            graph_path = repo / str(row["graph_path"])
            if not doi or not graph_path.is_file():
                continue
            candidate = dict(row)
            candidate["graph_root"] = relative_root
            by_doi.setdefault(doi, []).append(candidate)
    return by_doi


def select_canonical(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Use the earliest successful production graph for deterministic selection."""
    return min(
        candidates,
        key=lambda row: (
            float(row.get("started_at_unix", float("inf"))),
            int(row.get("retry_index", 0)),
            str(row.get("graph_path", "")),
        ),
    )


def compact_node(node: dict[str, Any]) -> dict[str, Any]:
    excluded = {"id", "type", "__provenance__", "__class__"}
    return {key: value for key, value in node.items() if key not in excluded}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument(
        "--eligibility-ledger",
        type=Path,
        default=Path(
            "analysis/full_text_screening/final_eligibility_v1.5.4/"
            "final_eligibility_ledger_158.csv"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/article_design/corpus_grounding_v1.0.0"),
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    ledger_path = repo / args.eligibility_ledger
    output_dir = repo / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    with ledger_path.open(encoding="utf-8-sig", newline="") as handle:
        eligible = [
            row for row in csv.DictReader(handle) if row.get("final_decision") == "assessed"
        ]

    candidates_by_doi = graph_candidates(repo)
    profiles: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    design_families: Counter[str] = Counter()
    identification_statuses: Counter[str] = Counter()
    aging_roles: Counter[str] = Counter()
    omics_layers: Counter[str] = Counter()
    reports_with_causal_nodes = 0

    for ledger_row in sorted(eligible, key=lambda row: normalize_doi(row.get("doi", ""))):
        doi = normalize_doi(ledger_row.get("doi", ""))
        candidates = candidates_by_doi.get(doi, [])
        if not candidates:
            raise RuntimeError(f"No successful graph found for eligible DOI {doi}")
        run = select_canonical(candidates)
        graph_path = repo / str(run["graph_path"])
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        nodes = graph.get("nodes", [])

        paper_nodes = [node for node in nodes if node.get("label") == "CausalMultiomicsAgingPaper"]
        aging_nodes = [compact_node(node) for node in nodes if node.get("label") == "AgingConstruct"]
        omics_nodes = [compact_node(node) for node in nodes if node.get("label") == "OmicsLayer"]
        causal_nodes = [compact_node(node) for node in nodes if node.get("label") == "CausalAnalysis"]

        if causal_nodes:
            reports_with_causal_nodes += 1
        for node in causal_nodes:
            design_families[str(node.get("design_family", "missing"))] += 1
            identification_statuses[str(node.get("identification_status", "missing"))] += 1
        for node in aging_nodes:
            aging_roles[str(node.get("role", "missing"))] += 1
        for node in omics_nodes:
            omics_layers[str(node.get("normalized_layer", "missing"))] += 1

        document_root = graph_path.parent.parent
        docling_markdown = document_root / "docling" / "document.md"
        profile = {
            "record_id": ledger_row.get("record_id", ""),
            "doi": doi,
            "title": ledger_row.get("title", ""),
            "graph_root": run["graph_root"],
            "graph_path": str(graph_path.relative_to(repo)),
            "graph_sha256": sha256_file(graph_path),
            "docling_markdown_path": (
                str(docling_markdown.relative_to(repo)) if docling_markdown.is_file() else ""
            ),
            "source_path": str(run.get("source_path", "")),
            "source_sha256": str(run.get("source_sha256", "")),
            "graph_candidate_count": len(candidates),
            "paper": compact_node(paper_nodes[0]) if paper_nodes else {},
            "aging_constructs": aging_nodes,
            "omics_layers": omics_nodes,
            "causal_analyses": causal_nodes,
            "graph_node_count": len(nodes),
            "graph_edge_count": len(graph.get("edges", [])),
        }
        profiles.append(profile)
        manifest_rows.append(
            {
                "record_id": profile["record_id"],
                "doi": doi,
                "title": profile["title"],
                "graph_root": profile["graph_root"],
                "graph_path": profile["graph_path"],
                "docling_markdown_path": profile["docling_markdown_path"],
                "source_path": profile["source_path"],
                "graph_candidate_count": profile["graph_candidate_count"],
                "aging_construct_nodes": len(aging_nodes),
                "omics_layer_nodes": len(omics_nodes),
                "causal_analysis_nodes": len(causal_nodes),
            }
        )

    manifest_path = output_dir / "eligible_graph_manifest_101.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(manifest_rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    profiles_path = output_dir / "eligible_graph_profiles_101.jsonl"
    with profiles_path.open("w", encoding="utf-8") as handle:
        for profile in profiles:
            handle.write(json.dumps(profile, ensure_ascii=False, sort_keys=True) + "\n")

    corpus_fingerprint = hashlib.sha256(
        "\n".join(f"{profile['doi']}\t{profile['graph_sha256']}" for profile in profiles).encode()
    ).hexdigest()
    summary = {
        "schema_version": "1.0.0",
        "purpose": "exploratory_article_structure_grounding",
        "methodological_boundary": (
            "Docling Graph nodes are model-generated evidence-index candidates. "
            "They may guide corpus orientation and representative full-text checks, "
            "but cannot determine eligibility, final causal levels, or synthesis claims."
        ),
        "eligibility_ledger": str(args.eligibility_ledger),
        "eligible_reports": len(eligible),
        "eligible_reports_with_canonical_graph": len(profiles),
        "eligible_reports_with_causal_analysis_nodes": reports_with_causal_nodes,
        "reports_with_multiple_successful_graph_candidates": sum(
            profile["graph_candidate_count"] > 1 for profile in profiles
        ),
        "graph_roots": list(GRAPH_ROOTS),
        "corpus_fingerprint_sha256": corpus_fingerprint,
        "node_counts": {
            "aging_constructs": sum(len(profile["aging_constructs"]) for profile in profiles),
            "omics_layers": sum(len(profile["omics_layers"]) for profile in profiles),
            "causal_analyses": sum(len(profile["causal_analyses"]) for profile in profiles),
        },
        "design_family_counts": dict(sorted(design_families.items())),
        "identification_status_counts": dict(sorted(identification_statuses.items())),
        "aging_role_counts": dict(sorted(aging_roles.items())),
        "omics_layer_counts": dict(sorted(omics_layers.items())),
        "outputs": {
            "manifest": str(manifest_path.relative_to(repo)),
            "profiles": str(profiles_path.relative_to(repo)),
        },
    }
    summary_path = output_dir / "corpus_graph_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
