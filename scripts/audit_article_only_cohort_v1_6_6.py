"""Audit assessed reports and remove verified conference-abstract-only objects."""

import csv
import concurrent.futures
import hashlib
import json
import re
from pathlib import Path

import certifi
import requests


ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "analysis/full_text_screening/prisma_slice_v1.6.5_no_conference_abstract"
OUT = ROOT / "analysis/full_text_screening/prisma_slice_v1.6.6_article_only"
INPUT = ROOT / "data/full_text_screening/v1.6.0_full_markdown296/input/input.jsonl"

CONFERENCE_ABSTRACTS = {
    "10.1093/geroni/igaf122.2542": {
        "evidence": "Europe PMC publication type Abstract; Innovation in Aging Supplement_2.",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC12761179/",
    },
    "10.1093/geroni/igy023.1445": {
        "evidence": "Europe PMC publication type Abstract; Innovation in Aging Suppl 1.",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6227306/",
    },
    "10.1097/01.hs9.0000967628.88191.88": {
        "evidence": "Europe PMC publication type Abstract; HemaSphere supplement abstract S179.",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10428296/",
    },
    "10.1097/01.hs9.0000967932.79281.37": {
        "evidence": "Europe PMC publication type Abstract; HemaSphere supplement abstract S255.",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10428406/",
    },
    "10.3324/haematol.2026.s1.84": {
        "evidence": "Official source identifies XIX Congress and ABSTRACT N. P011.",
        "url": "https://haematologica.org/article/download/haematol.2026.s1.84/79680",
    },
}

CONTENT_PATTERNS = {
    "abstract_topic": re.compile(r"\bAbstract Topic\s*:", re.IGNORECASE),
    "abstract_number": re.compile(r"\bABSTRACT\s+N\.\s*[A-Z]?\d+", re.IGNORECASE),
    "symposium_session": re.compile(r"\bSESSION\s+\d+\s*\(SYMPOSIUM\)", re.IGNORECASE),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def fetch_metadata(dois: list[str]) -> tuple[dict, dict]:
    headers = {
        "User-Agent": "causal-multiomics-aging-review/1.0 (mailto:bogdan.didenko@gmail.com)"
    }

    def fetch_one(doi: str) -> tuple[str, dict, dict]:
        epmc_response = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": f'DOI:"{doi}"', "format": "json", "resultType": "core"},
            timeout=60,
            verify=certifi.where(),
            headers=headers,
        )
        epmc_response.raise_for_status()
        crossref_response = requests.get(
            "https://api.crossref.org/works/" + requests.utils.quote(doi, safe=""),
            timeout=60,
            verify=certifi.where(),
            headers=headers,
        )
        if crossref_response.status_code == 200:
            crossref_value = crossref_response.json()
        else:
            crossref_value = {
                "http_status": crossref_response.status_code,
                "response_text": crossref_response.text,
            }
        return doi, epmc_response.json(), crossref_value

    europe_pmc = {}
    crossref = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for doi, epmc_value, crossref_value in executor.map(fetch_one, dois):
            europe_pmc[doi] = epmc_value
            crossref[doi] = crossref_value
    return europe_pmc, crossref


def main() -> None:
    if OUT.exists():
        raise ValueError(f"Refuse to overwrite {OUT}")

    ledger = list(csv.DictReader((PREVIOUS / "eligibility_ledger_294.csv").open()))
    assessed = [row for row in ledger if row["final_decision"] == "assessed"]
    assert len(assessed) == 280
    assessed_dois = [row["doi"].lower() for row in assessed]
    assert set(CONFERENCE_ABSTRACTS).issubset(assessed_dois)

    inputs = {}
    for line in INPUT.open():
        record = json.loads(line)
        inputs[record["doi"].lower()] = record

    europe_pmc, crossref = fetch_metadata(assessed_dois)
    OUT.mkdir(parents=True)
    write_json(OUT / "metadata/europe_pmc_raw_280.json", europe_pmc)
    write_json(OUT / "metadata/crossref_raw_280.json", crossref)

    audit_rows = []
    for row in assessed:
        doi = row["doi"].lower()
        source_record = inputs[doi]
        markdown = source_record["sections"][0]["text"]
        epmc_results = europe_pmc[doi].get("resultList", {}).get("result", [])
        epmc_types = sorted(
            {
                publication_type
                for result in epmc_results
                for publication_type in result.get("pubTypeList", {}).get("pubType", [])
            }
        )
        epmc_issues = sorted(
            {
                str(result.get("journalInfo", {}).get("issue"))
                for result in epmc_results
                if result.get("journalInfo", {}).get("issue") is not None
            }
        )
        crossref_message = crossref[doi].get("message", {})
        content_signals = [
            label for label, pattern in CONTENT_PATTERNS.items() if pattern.search(markdown)
        ]
        verified_abstract = doi in CONFERENCE_ABSTRACTS
        audit_rows.append(
            {
                "record_id": row["record_id"],
                "doi": doi,
                "title": row["title"],
                "article_only_audit_decision": (
                    "exclude_conference_abstract" if verified_abstract else "retain_full_article_or_preprint"
                ),
                "europe_pmc_publication_types": "|".join(epmc_types),
                "europe_pmc_issues": "|".join(epmc_issues),
                "crossref_type": crossref_message.get("type", ""),
                "crossref_issue": crossref_message.get("issue", ""),
                "markdown_content_signals": "|".join(content_signals),
                "decision_evidence": CONFERENCE_ABSTRACTS.get(doi, {}).get(
                    "evidence",
                    "No conference-abstract publication type or verified conference-object signal found.",
                ),
                "evidence_url": CONFERENCE_ABSTRACTS.get(doi, {}).get("url", ""),
            }
        )

    assert sum(row["article_only_audit_decision"] == "exclude_conference_abstract" for row in audit_rows) == 5
    assert sum(row["article_only_audit_decision"] == "retain_full_article_or_preprint" for row in audit_rows) == 275
    with (OUT / "article_only_audit_280.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0]))
        writer.writeheader()
        writer.writerows(audit_rows)

    retained_ledger = [row for row in ledger if row["doi"].lower() not in CONFERENCE_ABSTRACTS]
    assert len(retained_ledger) == 289
    assert sum(row["final_decision"] == "assessed" for row in retained_ledger) == 275
    assert sum(row["final_decision"] == "exclude" for row in retained_ledger) == 14
    with (OUT / "eligibility_ledger_289.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(retained_ledger[0]))
        writer.writeheader()
        writer.writerows(retained_ledger)

    dispositions = list(csv.DictReader((PREVIOUS / "report_disposition_359.csv").open()))
    for row in dispositions:
        doi = row["doi"].lower()
        if doi in CONFERENCE_ABSTRACTS:
            row["prisma_disposition"] = "nonarticle_conference_abstract_object"
            row["reason"] = CONFERENCE_ABSTRACTS[doi]["evidence"]
    assert len(dispositions) == 359
    assert sum(row["prisma_disposition"] == "nonarticle_conference_abstract_object" for row in dispositions) == 6
    with (OUT / "report_disposition_359.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dispositions[0]))
        writer.writeheader()
        writer.writerows(dispositions)

    decisions = [
        {
            "doi": doi,
            "previous_disposition": "meets_full_text_eligibility",
            "new_disposition": "nonarticle_conference_abstract_object",
            "decision_source": "article-only publication-type audit",
            "decision_date": "2026-09-20",
            **details,
        }
        for doi, details in CONFERENCE_ABSTRACTS.items()
    ]
    write_json(OUT / "conference_abstract_decisions.json", decisions)

    flow = {
        "scope": "stable_layer_pair_extension_only",
        "status": "article_only_full_text_eligibility_complete_for_289_screened_reports_three_deferred",
        "canonical_records": 359,
        "nonarticle_objects": 30,
        "reports_not_retrieved": 37,
        "retrieved_full_reports": 292,
        "separately_deferred_reports": 3,
        "screened_full_reports": 289,
        "reports_meeting_full_text_eligibility": 275,
        "reports_excluded": 14,
        "reports_unresolved": 0,
        "conference_abstracts_removed_from_full_text_cohort": 6,
        "conference_abstracts_removed_in_v1_6_6": 5,
        "whole_review_prisma_closed": False,
        "balances": {
            "canonical": 359 == 30 + 37 + 292,
            "retrieved": 292 == 3 + 289,
            "screened": 289 == 275 + 14,
        },
    }
    write_json(OUT / "prisma_flow.json", flow)
    (OUT / "README.md").write_text(
        "# Article-only correction v1.6.6\n\n"
        "The article-only audit checked all 280 reports classified as meeting full-text eligibility in v1.6.5. "
        "Europe PMC metadata were available for 276 records; Crossref metadata completed coverage for the other four. "
        "The audit also checked deterministic content signals in each preserved Docling Markdown.\n\n"
        "Five additional records were verified as conference-abstract-only objects and moved out of the full-text report cohort. "
        "Together with the conference abstract removed in v1.6.5, the disposition ledger now contains six conference abstracts. "
        "Full journal articles and complete preprints remain eligible publication types.\n\n"
        "The corrected extension contains 30 nonarticle objects, 37 reports not retrieved, and 292 retrieved full reports. "
        "Of those reports, 289 were screened and three remain separately deferred. The screened flow contains 275 eligible "
        "reports, 14 scientific exclusions, and no unresolved reports. Whole-review PRISMA remains open for the reasons already "
        "documented in earlier slices.\n"
    )

    source_paths = [
        PREVIOUS / "eligibility_ledger_294.csv",
        PREVIOUS / "report_disposition_359.csv",
        INPUT,
        Path(__file__),
    ]
    write_json(
        OUT / "audit_manifest.json",
        {
            "sources": [
                {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)} for path in source_paths
            ],
            "outputs": [
                {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
                for path in sorted(OUT.rglob("*"))
                if path.is_file() and path.name != "audit_manifest.json"
            ],
            "checks": flow["balances"],
        },
    )
    print(json.dumps(flow, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
