"""Build the report-level master corpus and exact-title version-linkage queue."""

import csv
import concurrent.futures
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import certifi
import requests


ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / "analysis/full_text_screening/final_eligibility_v1.5.4/final_eligibility_ledger_158.csv"
EXTENSION = ROOT / "analysis/full_text_screening/prisma_slice_v1.6.6_article_only/eligibility_ledger_289.csv"
EXTENSION_CROSSREF = ROOT / "analysis/full_text_screening/prisma_slice_v1.6.6_article_only/metadata/crossref_raw_280.json"
OUT = ROOT / "analysis/review_synthesis/master_corpus_v1.0.0"

PREPRINT_PREFIXES = (
    "10.1101/",
    "10.20944/",
    "10.21203/",
    "10.64898/",
)

# Crossref omits relations for these pairs. They were confirmed from matching
# titles/research targets, author lists, chronology, and existing source-identity
# records where available.
CURATED_VERSION_PAIRS = {
    tuple(sorted(pair)): evidence
    for pair, evidence in {
        ("10.1101/2025.10.29.685384", "10.1002/advs.202521633"): "matching_authors_and_research_target",
        ("10.1101/2020.11.02.364760", "10.1038/s41598-022-07397-9"): "matching_authors_and_research_target",
        ("10.1101/2021.01.22.427837", "10.1038/s43587-021-00159-8"): "matching_authors_and_research_target",
        ("10.1101/2025.10.08.681100", "10.1093/eurheartj/ehaf1063"): "matching_authors_and_research_target",
        ("10.21203/rs.3.rs-1264931/v1", "10.26508/lsa.202201492"): "existing_source_identity_map_and_matching_research_target",
        ("10.1101/2025.06.19.660635", "10.1161/circresaha.125.327427"): "existing_source_identity_map_and_matching_authors",
        ("10.1101/2022.11.14.516438", "10.1093/genetics/iyad073"): "exact_title_and_matching_authors",
        ("10.21203/rs.3.rs-4373201/v1", "10.1186/s13024-025-00802-7"): "exact_title_and_matching_authors",
    }.items()
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_doi(value: str) -> str:
    value = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
    return value


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def publication_form(doi: str) -> str:
    return "repository_preprint" if doi.startswith(PREPRINT_PREFIXES) else "publisher_platform_report"


def read_eligible(path: Path, cohort: str) -> list[dict[str, str]]:
    rows = list(csv.DictReader(path.open()))
    eligible = []
    for row in rows:
        if row["final_decision"] != "assessed":
            continue
        doi = normalize_doi(row["doi"])
        eligible.append(
            {
                "record_id": row["record_id"],
                "doi": doi,
                "title": row["title"],
                "normalized_title": normalize_title(row["title"]),
                "source_cohort": cohort,
                "publication_form_initial": publication_form(doi),
                "eligibility_ledger": str(path.relative_to(ROOT)),
                "eligibility_decision": row["final_decision"],
            }
        )
    return eligible


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fetch_missing_crossref(dois: list[str], existing: dict[str, dict]) -> dict[str, dict]:
    headers = {
        "User-Agent": "causal-multiomics-aging-review/1.0 (mailto:bogdan.didenko@gmail.com)"
    }

    def fetch(doi: str) -> tuple[str, dict]:
        response = requests.get(
            "https://api.crossref.org/works/" + requests.utils.quote(doi, safe=""),
            timeout=60,
            verify=certifi.where(),
            headers=headers,
        )
        if response.status_code == 200:
            return doi, response.json()
        return doi, {"http_status": response.status_code, "response_text": response.text}

    missing = [doi for doi in dois if doi not in existing]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for doi, value in executor.map(fetch, missing):
            existing[doi] = value
    return existing


def relation_pairs(crossref: dict[str, dict], eligible_dois: set[str]) -> dict[tuple[str, str], set[str]]:
    pairs: dict[tuple[str, str], set[str]] = defaultdict(set)
    for doi, response in crossref.items():
        if doi not in eligible_dois:
            continue
        relations = response.get("message", {}).get("relation", {})
        for relation_type, items in relations.items():
            for item in items:
                other = normalize_doi(str(item.get("id", "")))
                if other in eligible_dois and other != doi:
                    pair = tuple(sorted((doi, other)))
                    pairs[pair].add(relation_type)
    return pairs


def components(edges: set[tuple[str, str]]) -> list[set[str]]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    found = []
    visited = set()
    for start in sorted(adjacency):
        if start in visited:
            continue
        stack = [start]
        component = set()
        while stack:
            value = stack.pop()
            if value in component:
                continue
            component.add(value)
            stack.extend(adjacency[value] - component)
        visited.update(component)
        found.append(component)
    return found


def main() -> None:
    if OUT.exists():
        raise ValueError(f"Refuse to overwrite frozen master corpus: {OUT}")

    reports = read_eligible(PRIOR, "prior_162_report_flow")
    reports.extend(read_eligible(EXTENSION, "stable_layer_pair_extension"))
    assert len(reports) == 376
    assert len({row["record_id"] for row in reports}) == 376
    assert len({row["doi"] for row in reports}) == 376

    report_by_doi = {row["doi"]: row for row in reports}
    eligible_dois = set(report_by_doi)
    crossref = json.loads(EXTENSION_CROSSREF.read_text())
    crossref = fetch_missing_crossref(sorted(eligible_dois), crossref)

    by_title: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in reports:
        by_title[row["normalized_title"]].append(row)

    duplicate_groups = [group for group in by_title.values() if len(group) > 1]
    exact_pairs = {
        tuple(sorted((group[0]["doi"], group[1]["doi"])))
        for group in duplicate_groups
        if len(group) == 2
    }
    registry_pairs = relation_pairs(crossref, eligible_dois)
    curated_pairs = {pair for pair in CURATED_VERSION_PAIRS if set(pair).issubset(eligible_dois)}
    all_edges = exact_pairs | set(registry_pairs) | curated_pairs
    version_components = components(all_edges)
    assert all(len(component) == 2 for component in version_components)

    linkage_rows = []
    group_by_record = {}
    canonical_by_group = {}
    for index, component in enumerate(sorted(version_components, key=lambda value: sorted(value)), 1):
        group_id = f"version_candidate_{index:03d}"
        group = [report_by_doi[doi] for doi in sorted(component)]
        preprints = [row for row in group if row["publication_form_initial"] == "repository_preprint"]
        publisher_reports = [row for row in group if row["publication_form_initial"] == "publisher_platform_report"]
        assert len(preprints) == 1 and len(publisher_reports) == 1
        preprint = preprints[0]
        publisher_report = publisher_reports[0]
        pair = tuple(sorted(component))
        relation_types = sorted(registry_pairs.get(pair, set()))
        exact_title = pair in exact_pairs
        curated_evidence = CURATED_VERSION_PAIRS.get(pair, "")
        if relation_types:
            status = "confirmed_crossref_relation"
        elif curated_evidence:
            status = "confirmed_bibliographic_version_match"
        else:
            status = "requires_full_text_version_confirmation"
        for row in group:
            group_by_record[row["record_id"]] = group_id
        canonical_by_group[group_id] = publisher_report["record_id"]
        linkage_rows.append(
            {
                "version_candidate_id": group_id,
                "preprint_record_id": preprint["record_id"],
                "preprint_doi": preprint["doi"],
                "publisher_record_id": publisher_report["record_id"],
                "publisher_doi": publisher_report["doi"],
                "exact_normalized_title_match": str(exact_title).lower(),
                "crossref_relation_types": "|".join(relation_types),
                "curated_linkage_evidence": curated_evidence,
                "candidate_basis": (
                    "crossref_relation"
                    if relation_types
                    else "curated_bibliographic_match"
                    if curated_evidence
                    else "exact_normalized_title"
                ),
                "verification_status": status,
                "provisional_canonical_record_id": publisher_report["record_id"],
                "synthesis_action": "use_publisher_report_after_version_confirmation",
            }
        )

    report_rows = []
    for row in sorted(reports, key=lambda value: (value["source_cohort"], value["doi"])):
        report_rows.append(
            {
                **row,
                "version_candidate_id": group_by_record.get(row["record_id"], ""),
                "provisional_canonical_report": (
                    str(canonical_by_group.get(group_by_record.get(row["record_id"], "")) == row["record_id"]).lower()
                    if row["record_id"] in group_by_record
                    else "true"
                ),
                "study_id": "",
                "report_to_study_status": (
                    "confirmed_version_group"
                    if row["record_id"] in group_by_record
                    else "single_report_pending_study_linkage"
                ),
                "synthesis_inclusion_status": "pending_causal_evidence_extraction",
            }
        )

    OUT.mkdir(parents=True)
    (OUT / "metadata").mkdir()
    (OUT / "metadata/crossref_raw_376.json").write_text(
        json.dumps(crossref, ensure_ascii=False, indent=2) + "\n"
    )
    report_fields = list(report_rows[0])
    linkage_fields = list(linkage_rows[0])
    write_csv(OUT / "eligible_report_ledger_376.csv", report_rows, report_fields)
    write_csv(OUT / "version_linkage_candidates.csv", linkage_rows, linkage_fields)

    summary = {
        "status": "report_master_corpus_version_linkage_complete_study_linkage_pending",
        "prior_eligible_reports": 101,
        "extension_eligible_reports": 275,
        "eligible_reports_total": 376,
        "cross_cohort_doi_overlap": 0,
        "cross_cohort_exact_normalized_title_overlap": 0,
        "exact_normalized_title_pairs": len(exact_pairs),
        "crossref_relation_pairs": len(registry_pairs),
        "curated_bibliographic_pairs": len(curated_pairs),
        "confirmed_report_version_groups": len(version_components),
        "reports_in_confirmed_version_groups": sum(len(component) for component in version_components),
        "canonical_reports_after_version_collapse": 376 - len(version_components),
        "final_unique_study_count": None,
        "final_causal_analysis_count": None,
        "final_normalized_link_count": None,
        "next_step": "Assign study IDs and populate the source-checked biological evidence table, retaining report-version provenance.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (OUT / "README.md").write_text(
        "# Master synthesis corpus v1.0.0\n\n"
        "This package starts the scientific synthesis after full-text eligibility. It combines the 101 eligible reports from the prior 162-report flow with the 275 eligible reports from the article-only stable-layer-pair extension. There is no DOI or exact-title overlap between the two cohorts.\n\n"
        f"The combined unit is 376 eligible reports. This is not yet a count of independent studies or final synthesis inclusions. Crossref relations plus curated bibliographic linkage identify {len(version_components)} confirmed two-report version groups. The publisher-platform report is the provisional canonical synthesis report while both versions remain in provenance. Before broader cohort-dependency linkage, the report-version-collapsed maximum is {376 - len(version_components)} records.\n\n"
        "The next scientific deliverable is the source-checked evidence table used in the six-report pilot: aging finding, biological system and endpoint, verified omics contribution, causal leverage, supported contrast, validation, and inferential boundary. Failed causal-extraction instruments remain outside synthesis.\n"
    )

    output_paths = sorted(path for path in OUT.iterdir() if path.is_file())
    manifest = {
        "inputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for path in (PRIOR, EXTENSION, EXTENSION_CROSSREF, Path(__file__))
        ],
        "outputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for path in output_paths + [OUT / "metadata/crossref_raw_376.json"]
        ],
    }
    (OUT / "artifact_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
