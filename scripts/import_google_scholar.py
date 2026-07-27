#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

from search_databases import (
    PROTOCOL,
    SEARCH_CONFIG,
    classify_local,
    normalize_doi,
    sha256_text,
    write_records,
)

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", re.IGNORECASE)
NATURE_ARTICLE_RE = re.compile(
    r"(?:www\.)?nature\.com/articles/([^/?#]+)", re.IGNORECASE
)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
LEADING_FORMAT = re.compile(r"^\[[^\]]+\]\s*")


def load_pages(raw_dir: Path) -> list[dict[str, object]]:
    pages: list[dict[str, object]] = []
    for path in sorted(raw_dir.glob("page_*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            page = json.load(handle)
        page["_raw_page"] = path.name
        pages.append(page)
    if not pages:
        raise SystemExit(f"No Google Scholar browser exports found in {raw_dir}")
    return pages


def extract_doi(url: str) -> str:
    decoded = unquote(url)
    if match := DOI_RE.search(decoded):
        return normalize_doi(match.group(0))
    if match := NATURE_ARTICLE_RE.search(decoded):
        return normalize_doi(f"10.1038/{match.group(1)}")
    return ""


def normalize_pages(pages: list[dict[str, object]]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for page in pages:
        raw_page = str(page["_raw_page"])
        for raw in page.get("results", []):
            result = dict(raw)
            title = LEADING_FORMAT.sub("", str(result.get("title", ""))).strip()
            url = str(result.get("url", "")).strip()
            publication_info = str(result.get("publication_info", "")).strip()
            years = YEAR_RE.findall(publication_info)
            year = years[-1] if years else ""
            source_record_id = str(result.get("result_id", "")).strip()
            identity = (source_record_id, title.casefold())
            if identity in seen:
                continue
            seen.add(identity)
            record = {
                "source": "google_scholar",
                "source_record_id": source_record_id or f"title:{title}",
                "title": title,
                "abstract": str(result.get("snippet", "")).strip(),
                "year": year,
                "publication_date": f"{year}-01-01" if year else "",
                "doi": extract_doi(url),
                "pmid": "",
                "pmcid": "",
                "authors": publication_info.split(" - ", 1)[0],
                "venue": publication_info,
                "document_type": "",
                "language": "",
                "url": url,
                "is_preprint": False,
                "raw_page": f"google_scholar/{raw_page}",
            }
            records.append(classify_local(record))
    return records


def read_records(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize a manually frozen Google Scholar browser export"
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    raw_dir = args.output / "raw" / "google_scholar"
    pages = load_pages(raw_dir)
    records = normalize_pages(pages)
    normalized_path = args.output / "normalized" / "google_scholar.csv"
    write_records(normalized_path, records)

    query_path = PROTOCOL / "queries" / "google_scholar.txt"
    query = query_path.read_text(encoding="utf-8").strip()
    config = json.loads(SEARCH_CONFIG.read_text(encoding="utf-8"))
    canonical_doi = normalize_doi(config["canonical_positive_doi"])
    canonical = [
        record for record in records if normalize_doi(record.get("doi")) == canonical_doi
    ]
    reported_text = str(pages[0].get("reported_count_text", ""))
    reported_match = re.search(r"[\d,]+", reported_text)
    reported_count = (
        int(reported_match.group(0).replace(",", "")) if reported_match else None
    )
    completed_at = datetime.now(UTC).isoformat()
    manifest = {
        "source": "google_scholar",
        "started_at": str(pages[0].get("retrieved_at", completed_at)),
        "completed_at": completed_at,
        "query_file": "protocol/queries/google_scholar.txt",
        "query_sha256": sha256_text(query),
        "reported_count": reported_count,
        "source_details": {
            "mode": "manual_browser_export",
            "reported_count_is_approximate": reported_text.lower().startswith("about"),
            "reported_count_text": reported_text,
            "pages_retrieved": len(pages),
            "official_api_available": False,
        },
        "retrieved_count": len(records),
        "local_three_block_count": sum(
            bool(record["local_three_block_match"]) for record in records
        ),
        "canonical_positive_doi": canonical_doi,
        "canonical_positive_found": bool(canonical),
        "canonical_positive_local_three_block_match": any(
            bool(record["local_three_block_match"]) for record in canonical
        ),
        "normalized_file": str(normalized_path.relative_to(args.output)),
    }
    manifests_dir = args.output / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    (manifests_dir / "google_scholar.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    source_files = sorted(
        path
        for path in (args.output / "normalized").glob("*.csv")
        if path.name not in {"all_sources.csv"}
    )
    all_records = [
        row
        for path in source_files
        for row in read_records(path)
    ]
    all_records.sort(
        key=lambda row: (
            row["source"],
            row["publication_date"],
            row["source_record_id"],
        )
    )
    combined_path = args.output / "normalized" / "all_sources.csv"
    write_records(combined_path, all_records)

    run_manifest_path = args.output / "search_run_manifest.json"
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    run_manifest["updated_at"] = completed_at
    run_manifest["sources_requested"] = sorted(
        set(run_manifest["sources_requested"]) | {"google_scholar"}
    )
    run_manifest["sources_completed"] = sorted(
        set(run_manifest["sources_completed"]) | {"google_scholar"}
    )
    run_manifest["source_manifests"]["google_scholar"] = manifest
    run_manifest["total_source_records"] = len(all_records)
    run_manifest["total_local_three_block_records"] = sum(
        str(record["local_three_block_match"]).lower() == "true"
        for record in all_records
    )
    run_manifest["google_scholar_status"] = "manual_complete"
    run_manifest_path.write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"google_scholar: reported={reported_count} retrieved={len(records)} "
        f"local_three_block={manifest['local_three_block_count']} "
        f"canonical={manifest['canonical_positive_found']}"
    )
    print(f"all_sources={len(all_records)}")


if __name__ == "__main__":
    main()
