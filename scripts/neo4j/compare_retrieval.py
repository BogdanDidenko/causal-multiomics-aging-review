#!/usr/bin/env python3
"""Compare Neo4j retrieval with frozen graph, Docling, and legacy candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "protocol/neo4j/retrieval_comparison_v0.1.0.json"
NEO4J_CONFIG = REPO / "protocol/neo4j/retrieval_v0.1.0.json"
ACTIVE_METHODS = (
    "neo4j_structured",
    "neo4j_graph_text",
    "deterministic_docling_lexical",
)
FULL_METHODS = (
    "neo4j_structured",
    "frozen_profile_structured",
    "neo4j_graph_text",
    "deterministic_docling_lexical",
)
REFERENCE_HEADINGS = {
    "bibliography",
    "ereferences",
    "literature cited",
    "reference",
    "references",
    "works cited",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_command(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def run_cypher(container: str, query: str) -> list[dict[str, str]]:
    output = run_command(["docker", "exec", container, "cypher-shell", "--format", "plain", query])
    if not output:
        return []
    parsed = list(csv.reader(output.splitlines(), skipinitialspace=True))
    if not parsed:
        return []
    header = parsed[0]
    return [dict(zip(header, row, strict=True)) for row in parsed[1:]]


def cypher_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def normalized_doi(value: str) -> str:
    return value.strip().lower().removeprefix("https://doi.org/").removeprefix("doi:")


def leaf_heading(value: str) -> str:
    return value.rsplit(" > ", maxsplit=1)[-1].strip().rstrip(":").lower()


def is_reference_section(section: dict[str, Any]) -> bool:
    return leaf_heading(str(section.get("heading", ""))) in REFERENCE_HEADINGS


def compile_anchors(need: dict[str, Any]) -> list[tuple[str, re.Pattern[str]]]:
    return [
        (item["id"], re.compile(item["regex"], re.IGNORECASE | re.UNICODE))
        for item in need["lexical_anchors"]
    ]


def regex_hits(text: str, anchors: list[tuple[str, re.Pattern[str]]]) -> tuple[int, set[str]]:
    count = 0
    matched: set[str] = set()
    for anchor_id, pattern in anchors:
        occurrences = sum(1 for _ in pattern.finditer(text))
        if occurrences:
            matched.add(anchor_id)
            count += occurrences
    return count, matched


def source_strings(value: Any) -> list[str]:
    output: list[str] = []
    if isinstance(value, str):
        output.append(value)
    elif isinstance(value, list):
        for item in value:
            output.extend(source_strings(item))
    elif isinstance(value, dict):
        for key in sorted(value):
            output.extend(source_strings(value[key]))
    return output


def aggregate_rows(
    rows: list[dict[str, Any]],
    *,
    need_id: str,
    method: str,
    unit_type: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        doi = normalized_doi(str(row["doi"]))
        record = grouped.setdefault(
            doi,
            {
                "information_need": need_id,
                "method": method,
                "doi": doi,
                "title": row.get("title", ""),
                "retrieval_unit_type": unit_type,
                "retrieval_unit_count": 0,
                "matched_anchors": set(),
                "source_ids": set(),
                "provenance_complete": True,
            },
        )
        record["retrieval_unit_count"] += int(row.get("unit_count", 1))
        record["matched_anchors"].update(row.get("matched_anchors", []))
        if row.get("source_id"):
            record["source_ids"].add(str(row["source_id"]))
        if row.get("provenance_complete") is False:
            record["provenance_complete"] = False
    output = []
    for doi in sorted(grouped):
        row = grouped[doi]
        row["matched_anchors"] = ";".join(sorted(row["matched_anchors"]))
        row["source_ids"] = ";".join(sorted(row["source_ids"]))
        row["provenance_complete"] = "yes" if row["provenance_complete"] else "no"
        output.append(row)
    return output


def structured_cypher(corpus_id: str, families: list[str]) -> str:
    family_list = "[" + ", ".join(cypher_string(item) for item in families) + "]"
    return (
        "MATCH (report:CausalMultiomicsAgingPaper)-[:INVESTIGATES_AGING_CONSTRUCT]->"
        "(:AgingConstruct) "
        f"WHERE report.corpus_id = {cypher_string(corpus_id)} "
        "WITH DISTINCT report "
        "MATCH (report)-[:USES_OMICS_LAYER]->(omics:OmicsLayer) "
        "WITH report, count(DISTINCT omics.normalized_layer) AS layer_count "
        "WHERE layer_count >= 2 "
        "MATCH (report)-[:REPORTS_CAUSAL_ANALYSIS]->(analysis:CausalAnalysis) "
        f"WHERE analysis.design_family IN {family_list} "
        "RETURN report.doi AS doi, report.title AS title, "
        "analysis.node_key AS source_id, analysis.design_family AS design_family, "
        "CASE WHEN analysis.provenance_json IS NULL OR analysis.provenance_json = '' "
        "THEN 'no' ELSE 'yes' END AS provenance_complete "
        "ORDER BY doi, source_id;"
    )


def graph_text_cypher(corpus_id: str, lucene_query: str) -> str:
    return (
        "CALL db.index.fulltext.queryNodes('review_graph_text', "
        f"{cypher_string(lucene_query)}) YIELD node, score "
        f"WHERE node.corpus_id = {cypher_string(corpus_id)} "
        "MATCH (report:CausalMultiomicsAgingPaper) "
        "WHERE report.corpus_id = node.corpus_id AND report.doi = node.doi "
        "MATCH (report)-[:INVESTIGATES_AGING_CONSTRUCT]->(:AgingConstruct) "
        "WITH DISTINCT node, score, report "
        "MATCH (report)-[:USES_OMICS_LAYER]->(omics:OmicsLayer) "
        "WITH node, score, report, count(DISTINCT omics.normalized_layer) AS layer_count "
        "WHERE layer_count >= 2 "
        "RETURN report.doi AS doi, report.title AS title, node.node_key AS source_id, "
        "node.node_label AS node_label, score, "
        "CASE WHEN node.provenance_json IS NULL OR node.provenance_json = '' "
        "THEN 'no' ELSE 'yes' END AS provenance_complete "
        "ORDER BY doi, source_id;"
    )


def neo4j_rows(
    config: dict[str, Any], container: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output: list[dict[str, Any]] = []
    query_log: list[dict[str, Any]] = []
    corpus_id = config["corpus"]["corpus_id"]
    for need in config["information_needs"]:
        query = structured_cypher(corpus_id, need["graph_design_families"])
        raw = run_cypher(container, query)
        query_log.append(
            {
                "information_need": need["id"],
                "method": "neo4j_structured",
                "cypher": query,
                "cypher_sha256": sha256_bytes(query.encode()),
                "returned_rows": len(raw),
            }
        )
        output.extend(
            aggregate_rows(
                [
                    {
                        "doi": row["doi"],
                        "title": row["title"],
                        "source_id": row["source_id"],
                        "matched_anchors": [row["design_family"]],
                        "provenance_complete": row["provenance_complete"] == "yes",
                    }
                    for row in raw
                ],
                need_id=need["id"],
                method="neo4j_structured",
                unit_type="causal_analysis_node",
            )
        )

        query = graph_text_cypher(corpus_id, need["lucene_query"])
        raw = run_cypher(container, query)
        query_log.append(
            {
                "information_need": need["id"],
                "method": "neo4j_graph_text",
                "cypher": query,
                "cypher_sha256": sha256_bytes(query.encode()),
                "returned_rows": len(raw),
            }
        )
        output.extend(
            aggregate_rows(
                [
                    {
                        "doi": row["doi"],
                        "title": row["title"],
                        "source_id": row["source_id"],
                        "matched_anchors": ["lucene_query"],
                        "provenance_complete": row["provenance_complete"] == "yes",
                    }
                    for row in raw
                ],
                need_id=need["id"],
                method="neo4j_graph_text",
                unit_type="matching_graph_node",
            )
        )
    return output, query_log


def profile_rows(config: dict[str, Any], profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for need in config["information_needs"]:
        families = set(need["graph_design_families"])
        raw: list[dict[str, Any]] = []
        for profile in profiles:
            layers = {
                item.get("normalized_layer", "")
                for item in profile.get("omics_layers", [])
                if item.get("normalized_layer")
            }
            if len(layers) < 2 or not profile.get("aging_constructs"):
                continue
            for index, analysis in enumerate(profile.get("causal_analyses", []), start=1):
                family = analysis.get("design_family", "")
                if family in families:
                    raw.append(
                        {
                            "doi": profile["doi"],
                            "title": profile["title"],
                            "source_id": f"profile-analysis-{index:03d}",
                            "matched_anchors": [family],
                        }
                    )
        output.extend(
            aggregate_rows(
                raw,
                need_id=need["id"],
                method="frozen_profile_structured",
                unit_type="causal_analysis_object",
            )
        )
    return output


def docling_rows(
    config: dict[str, Any], records: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for need in config["information_needs"]:
        anchors = compile_anchors(need)
        raw: list[dict[str, Any]] = []
        for doi, record in records.items():
            for section in record.get("sections", []):
                if is_reference_section(section):
                    continue
                count, matched = regex_hits(str(section.get("text", "")), anchors)
                if count:
                    raw.append(
                        {
                            "doi": doi,
                            "title": record.get("title", ""),
                            "source_id": section.get("section_id", ""),
                            "unit_count": count,
                            "matched_anchors": matched,
                        }
                    )
        output.extend(
            aggregate_rows(
                raw,
                need_id=need["id"],
                method="deterministic_docling_lexical",
                unit_type="regex_occurrence",
            )
        )
    return output


def load_legacy_inventories(config: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for root_value in config["corpus"]["legacy_candidate_roots"]:
        root = REPO / root_value
        checkpoint = "A" if "checkpoint_A" in root_value else "B"
        for path in sorted(root.glob("*/candidate_inventory.json")):
            inventory = read_json(path)
            inventory["_checkpoint"] = checkpoint
            inventory["_path"] = path.relative_to(REPO).as_posix()
            output.append(inventory)
    return output


def legacy_rows(
    config: dict[str, Any], inventories: list[dict[str, Any]], titles: dict[str, str]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for need in config["information_needs"]:
        anchors = compile_anchors(need)
        raw: list[dict[str, Any]] = []
        for inventory in inventories:
            doi = normalized_doi(inventory["doi"])
            for candidate in inventory.get("candidates", []):
                candidate_payload = candidate.get("candidate", {})
                text = "\n".join(source_strings(candidate_payload))
                count, matched = regex_hits(text, anchors)
                if count:
                    raw.append(
                        {
                            "doi": doi,
                            "title": titles.get(doi, candidate.get("title", "")),
                            "source_id": candidate.get("candidate_ref", ""),
                            "unit_count": 1,
                            "matched_anchors": matched,
                        }
                    )
        output.extend(
            aggregate_rows(
                raw,
                need_id=need["id"],
                method="legacy_llm_candidate_text",
                unit_type="matching_legacy_candidate",
            )
        )
    return output


def row_sets(
    rows: list[dict[str, Any]], subset: set[str] | None = None
) -> dict[tuple[str, str], set[str]]:
    output: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        doi = row["doi"]
        if subset is None or doi in subset:
            output[(row["information_need"], row["method"])].add(doi)
    return output


def pairwise_rows(
    rows: list[dict[str, Any]],
    *,
    scope: str,
    methods: tuple[str, ...],
    subset: set[str] | None = None,
) -> list[dict[str, Any]]:
    sets = row_sets(rows, subset)
    needs = sorted({row["information_need"] for row in rows})
    output: list[dict[str, Any]] = []
    for need_id in needs:
        for method_a, method_b in itertools.combinations(methods, 2):
            first = sets[(need_id, method_a)]
            second = sets[(need_id, method_b)]
            intersection = first & second
            union = first | second
            output.append(
                {
                    "scope": scope,
                    "information_need": need_id,
                    "method_a": method_a,
                    "method_b": method_b,
                    "reports_a": len(first),
                    "reports_b": len(second),
                    "intersection": len(intersection),
                    "union": len(union),
                    "jaccard": f"{len(intersection) / len(union):.6f}" if union else "1.000000",
                    "a_only": len(first - second),
                    "b_only": len(second - first),
                }
            )
    return output


def unique_rows(
    rows: list[dict[str, Any]],
    *,
    scope: str,
    methods: tuple[str, ...],
    titles: dict[str, str],
    subset: set[str] | None = None,
) -> list[dict[str, Any]]:
    sets = row_sets(rows, subset)
    needs = sorted({row["information_need"] for row in rows})
    output: list[dict[str, Any]] = []
    for need_id in needs:
        for method in methods:
            others: set[str] = set()
            for other in methods:
                if other != method:
                    others.update(sets[(need_id, other)])
            for doi in sorted(sets[(need_id, method)] - others):
                output.append(
                    {
                        "scope": scope,
                        "information_need": need_id,
                        "unique_to_method": method,
                        "doi": doi,
                        "title": titles.get(doi, ""),
                    }
                )
    return output


def method_counts(
    rows: list[dict[str, Any]],
    methods: tuple[str, ...],
    subset: set[str] | None = None,
) -> dict[str, dict[str, dict[str, int]]]:
    sets = row_sets(rows, subset)
    unit_counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        if subset is None or row["doi"] in subset:
            unit_counts[(row["information_need"], row["method"])] += int(
                row["retrieval_unit_count"]
            )
    needs = sorted({row["information_need"] for row in rows})
    return {
        need: {
            method: {
                "reports": len(sets[(need, method)]),
                "method_specific_units": unit_counts[(need, method)],
            }
            for method in methods
        }
        for need in needs
    }


def historical_burden_rows(
    inventories: list[dict[str, Any]], profiles: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    output = []
    for inventory in sorted(inventories, key=lambda item: (item["_checkpoint"], item["doi"])):
        doi = normalized_doi(inventory["doi"])
        profile = profiles[doi]
        graph_count = len(profile.get("causal_analyses", []))
        legacy_count = int(inventory["candidate_count"])
        output.append(
            {
                "checkpoint": inventory["_checkpoint"],
                "doi": doi,
                "title": profile["title"],
                "legacy_frozen_candidates": legacy_count,
                "neo4j_causal_analysis_nodes": graph_count,
                "legacy_to_graph_count_ratio": f"{legacy_count / graph_count:.3f}"
                if graph_count
                else "undefined",
                "legacy_discovery_grounding_failures": len(
                    inventory.get("discovery_grounding_failures", [])
                ),
                "legacy_discovery_technical_failures": len(
                    inventory.get("discovery_technical_failures", [])
                ),
                "legacy_inventory_path": inventory["_path"],
            }
        )
    return output


def exact_profile_checks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sets = row_sets(rows)
    output = []
    for need_id in sorted({row["information_need"] for row in rows}):
        neo = sets[(need_id, "neo4j_structured")]
        profile = sets[(need_id, "frozen_profile_structured")]
        output.append(
            {
                "information_need": need_id,
                "neo4j_reports": len(neo),
                "profile_reports": len(profile),
                "exact_report_set_equivalence": neo == profile,
                "neo4j_only_dois": sorted(neo - profile),
                "profile_only_dois": sorted(profile - neo),
            }
        )
    return output


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Neo4j retrieval comparison v0.1.0",
        "",
        "Status: **exploratory; no expert retrieval gold standard**",
        "",
        f"- Frozen eligible corpus: {summary['corpus_reports']} reports",
        f"- Shared historical subset: {summary['historical_reports']} reports",
        f"- Corpus fingerprint: `{summary['corpus_fingerprint']}`",
        "- Comparison unit: unique DOI",
        "- References/Bibliography were excluded from the Docling lexical baseline.",
        "",
        "## Full 101-report corpus",
        "",
        "Method-specific units are graph nodes, regex occurrences, or profile objects and",
        "must not be compared as though they were the same scientific unit.",
        "",
        "| Information need | Neo4j structured | Frozen profile | Neo4j graph text | "
        "Docling lexical | Active-method union |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    full = summary["full_corpus"]
    for need_id, values in full.items():
        active_union = set(summary["doi_sets"][need_id]["neo4j_structured"])
        active_union.update(summary["doi_sets"][need_id]["neo4j_graph_text"])
        active_union.update(summary["doi_sets"][need_id]["deterministic_docling_lexical"])
        lines.append(
            f"| `{need_id}` | {values['neo4j_structured']['reports']} | "
            f"{values['frozen_profile_structured']['reports']} | "
            f"{values['neo4j_graph_text']['reports']} | "
            f"{values['deterministic_docling_lexical']['reports']} | {len(active_union)} |"
        )

    lines.extend(
        [
            "",
            "## Key overlaps",
            "",
            "| Information need | Structured vs graph-text Jaccard | Structured vs Docling "
            "Jaccard | Graph-text vs Docling Jaccard |",
            "|---|---:|---:|---:|",
        ]
    )
    lookup = {
        (row["information_need"], row["method_a"], row["method_b"]): row
        for row in summary["pairwise"]
        if row["scope"] == "eligible_101"
    }
    for need_id in full:
        sg = lookup[(need_id, "neo4j_structured", "neo4j_graph_text")]["jaccard"]
        sd = lookup[(need_id, "neo4j_structured", "deterministic_docling_lexical")]["jaccard"]
        gd = lookup[(need_id, "neo4j_graph_text", "deterministic_docling_lexical")]["jaccard"]
        lines.append(f"| `{need_id}` | {sg} | {sd} | {gd} |")

    lines.extend(
        [
            "",
            "## Shared 30-report historical subset",
            "",
            "| Information need | Neo4j structured | Neo4j graph text | Docling lexical | "
            "Rejected legacy LLM candidates |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for need_id, values in summary["historical_subset"].items():
        lines.append(
            f"| `{need_id}` | {values['neo4j_structured']['reports']} | "
            f"{values['neo4j_graph_text']['reports']} | "
            f"{values['deterministic_docling_lexical']['reports']} | "
            f"{values['legacy_llm_candidate_text']['reports']} |"
        )

    burden = summary["historical_candidate_burden"]
    lines.extend(
        [
            "",
            "## Historical candidate burden",
            "",
            f"Across the same 30 reports, the rejected open+dense LLM discovery produced "
            f"{burden['legacy_candidates']} frozen candidates. The current graph contains "
            f"{burden['neo4j_causal_analysis_nodes']} CausalAnalysis nodes for those reports "
            f"({burden['legacy_to_graph_count_ratio']} legacy candidates per graph node).",
            "These are different candidate definitions, so this quantifies workload rather "
            "than recall.",
            "",
            "## Frozen-profile equivalence",
            "",
        ]
    )
    if all(item["exact_report_set_equivalence"] for item in summary["profile_equivalence"]):
        lines.append(
            "Neo4j structured Cypher and direct filtering of the same frozen graph profiles "
            "returned identical DOI sets for all five information needs."
        )
    else:
        lines.append("At least one Neo4j/profile set mismatch requires investigation.")

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Neo4j adds deterministic relationship composition, indexed exploration, and stable",
            "provenance lookup. It does not add new scientific evidence beyond the model-generated",
            "Docling graphs. Graph-text and Docling lexical retrieval are candidate generators;",
            "their unique hits require human-gold assessment before precision or recall can "
            "be stated.",
            "No missing hit can support exclusion.",
            "",
        ]
    )
    return "\n".join(lines)


def compare(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    neo4j_config = read_json(NEO4J_CONFIG)
    graph_profiles_path = REPO / config["corpus"]["graph_profiles"]
    full_text_path = REPO / config["corpus"]["deterministic_full_text"]
    manifest_path = REPO / config["corpus"]["graph_manifest"]

    profiles_list = read_jsonl(graph_profiles_path)
    profiles = {normalized_doi(row["doi"]): row for row in profiles_list}
    if len(profiles) != config["corpus"]["expected_reports"]:
        raise RuntimeError(f"Expected 101 profile reports, found {len(profiles)}")

    full_text_candidates = read_jsonl(full_text_path)
    full_text_records = {
        normalized_doi(row["doi"]): row
        for row in full_text_candidates
        if normalized_doi(row.get("doi", "")) in profiles
    }
    if set(full_text_records) != set(profiles):
        raise RuntimeError("Deterministic full-text DOI inventory does not match eligible profiles")

    titles = {doi: row["title"] for doi, row in profiles.items()}
    inventories = load_legacy_inventories(config)
    if len(inventories) != 30:
        raise RuntimeError(f"Expected 30 historical inventories, found {len(inventories)}")
    historical_dois = {normalized_doi(row["doi"]) for row in inventories}
    legacy_candidate_total = sum(int(row["candidate_count"]) for row in inventories)
    expected_legacy_total = config["historical_comparison"]["legacy_frozen_candidates"]
    if legacy_candidate_total != expected_legacy_total:
        raise RuntimeError(
            f"Expected {expected_legacy_total} legacy candidates, found {legacy_candidate_total}"
        )

    neo_rows, cypher_log = neo4j_rows(config, neo4j_config["neo4j"]["container_name"])
    all_rows = neo_rows
    all_rows.extend(profile_rows(config, profiles_list))
    all_rows.extend(docling_rows(config, full_text_records))
    all_rows.extend(legacy_rows(config, inventories, titles))
    all_rows.sort(key=lambda row: (row["information_need"], row["method"], row["doi"]))

    profile_checks = exact_profile_checks(all_rows)
    if not all(item["exact_report_set_equivalence"] for item in profile_checks):
        raise RuntimeError("Neo4j structured retrieval differs from frozen-profile filtering")

    pairwise = pairwise_rows(all_rows, scope="eligible_101", methods=FULL_METHODS)
    pairwise.extend(
        pairwise_rows(
            all_rows,
            scope="historical_30",
            methods=ACTIVE_METHODS + ("legacy_llm_candidate_text",),
            subset=historical_dois,
        )
    )
    pairwise.sort(
        key=lambda row: (
            row["scope"],
            row["information_need"],
            row["method_a"],
            row["method_b"],
        )
    )
    unique = unique_rows(
        all_rows,
        scope="eligible_101",
        methods=ACTIVE_METHODS,
        titles=titles,
    )
    unique.extend(
        unique_rows(
            all_rows,
            scope="historical_30",
            methods=ACTIVE_METHODS + ("legacy_llm_candidate_text",),
            titles=titles,
            subset=historical_dois,
        )
    )
    unique.sort(
        key=lambda row: (
            row["scope"],
            row["information_need"],
            row["unique_to_method"],
            row["doi"],
        )
    )
    burden_rows = historical_burden_rows(inventories, profiles)
    graph_node_total = sum(int(row["neo4j_causal_analysis_nodes"]) for row in burden_rows)

    full_counts = method_counts(all_rows, FULL_METHODS)
    historical_counts = method_counts(
        all_rows,
        ACTIVE_METHODS + ("legacy_llm_candidate_text",),
        historical_dois,
    )
    doi_sets = row_sets(all_rows)
    doi_sets_json = {
        need["id"]: {method: sorted(doi_sets[(need["id"], method)]) for method in FULL_METHODS}
        for need in config["information_needs"]
    }
    reference_doi = normalized_doi(config["reference_control"]["doi"])
    reference_control = {
        need["id"]: {
            method: reference_doi in doi_sets[(need["id"], method)] for method in FULL_METHODS
        }
        for need in config["information_needs"]
    }

    input_paths = [config_path, NEO4J_CONFIG, graph_profiles_path, full_text_path, manifest_path]
    input_hashes = {path.relative_to(REPO).as_posix(): sha256_file(path) for path in input_paths}
    git_revision = run_command(["git", "rev-parse", "HEAD"])
    query_log = {
        "analysis_id": config["analysis_id"],
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "git_revision": git_revision,
        "neo4j_container": neo4j_config["neo4j"]["container_name"],
        "neo4j_image": run_command(
            [
                "docker",
                "inspect",
                neo4j_config["neo4j"]["container_name"],
                "--format",
                "{{.Config.Image}}",
            ]
        ),
        "input_hashes": input_hashes,
        "queries": cypher_log,
    }
    summary: dict[str, Any] = {
        "schema_version": config["schema_version"],
        "analysis_id": config["analysis_id"],
        "status": "exploratory_complete_no_gold",
        "executed_at": query_log["executed_at"],
        "git_revision": git_revision,
        "corpus_fingerprint": config["corpus"]["fingerprint"],
        "corpus_reports": len(profiles),
        "historical_reports": len(historical_dois),
        "full_corpus": full_counts,
        "historical_subset": historical_counts,
        "profile_equivalence": profile_checks,
        "pairwise": pairwise,
        "historical_candidate_burden": {
            "legacy_candidates": legacy_candidate_total,
            "neo4j_causal_analysis_nodes": graph_node_total,
            "legacy_to_graph_count_ratio": round(legacy_candidate_total / graph_node_total, 3)
            if graph_node_total
            else None,
        },
        "reference_control": reference_control,
        "doi_sets": doi_sets_json,
        "interpretive_limits": config["interpretive_limits"],
        "input_hashes": input_hashes,
    }

    outputs = config["outputs"]
    retrieval_fields = [
        "information_need",
        "method",
        "doi",
        "title",
        "retrieval_unit_type",
        "retrieval_unit_count",
        "matched_anchors",
        "source_ids",
        "provenance_complete",
    ]
    write_csv(REPO / outputs["retrieval_rows"], all_rows, retrieval_fields)
    write_csv(
        REPO / outputs["pairwise"],
        pairwise,
        [
            "scope",
            "information_need",
            "method_a",
            "method_b",
            "reports_a",
            "reports_b",
            "intersection",
            "union",
            "jaccard",
            "a_only",
            "b_only",
        ],
    )
    write_csv(
        REPO / outputs["method_unique_hits"],
        unique,
        ["scope", "information_need", "unique_to_method", "doi", "title"],
    )
    write_csv(
        REPO / outputs["historical_burden"],
        burden_rows,
        [
            "checkpoint",
            "doi",
            "title",
            "legacy_frozen_candidates",
            "neo4j_causal_analysis_nodes",
            "legacy_to_graph_count_ratio",
            "legacy_discovery_grounding_failures",
            "legacy_discovery_technical_failures",
            "legacy_inventory_path",
        ],
    )
    write_json(REPO / outputs["query_log"], query_log)
    write_json(REPO / outputs["summary"], summary)
    report_path = REPO / outputs["report"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    summary = compare(args.config.resolve())
    print(
        json.dumps(
            {
                "status": summary["status"],
                "corpus_reports": summary["corpus_reports"],
                "historical_reports": summary["historical_reports"],
                "profile_equivalence": all(
                    item["exact_report_set_equivalence"] for item in summary["profile_equivalence"]
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
