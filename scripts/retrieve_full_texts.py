#!/usr/bin/env python3
"""Retrieve lawful open full texts for a frozen review target set.

The script selects non-preprint records from a named manual-triage queue,
queries OpenAlex and Europe PMC by identifier, and downloads only open PDF
locations or Europe PMC full-text XML. It does not bypass publisher access
controls. All identifiers, source URLs, responses, checksums, and failures are
recorded in the output directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import ssl
import time
from collections import Counter
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

import certifi

OPENALEX_WORK = "https://api.openalex.org/works/https://doi.org/"
EUROPEPMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EUROPEPMC_XML = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
USER_AGENT = "causal-multiomics-aging-review/1.0 full-text-retrieval"
PDF_MAGIC = b"%PDF-"
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
LANDING_PAGE_TIMEOUT_SECONDS = 12


class PdfLinkParser(HTMLParser):
    """Collect explicit PDF links exposed by an OA landing page."""

    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.casefold(): value or "" for name, value in attrs}
        if tag == "meta" and attributes.get("name", "").casefold() == "citation_pdf_url":
            self.urls.append(attributes.get("content", ""))
        if tag == "a" and (
            attributes.get("type", "").casefold() == "application/pdf"
            or ".pdf" in attributes.get("href", "").casefold()
        ):
            self.urls.append(attributes.get("href", ""))


@dataclass(frozen=True)
class Target:
    record_id: str
    doi: str
    title: str
    source: str
    year: str
    design_anchor: str
    pmid: str
    pmcid: str

    @property
    def file_stem(self) -> str:
        return hashlib.sha256(self.doi.encode("utf-8")).hexdigest()[:16]


def normalize_doi(value: str) -> str:
    return value.strip().casefold().removeprefix("https://doi.org/").removeprefix("doi:")


def normalize_pmcid(value: str) -> str:
    normalized = value.strip().upper()
    return normalized if normalized.startswith("PMC") else f"PMC{normalized}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, str]]) -> None:
    materialized = list(rows)
    if not materialized:
        raise ValueError("Refusing to write an empty target CSV")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(materialized[0]))
        writer.writeheader()
        writer.writerows(materialized)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def http_get(url: str, timeout: int) -> tuple[int, dict[str, str], bytes]:
    request_url = quote(url, safe=":/?&=%#[];,+")
    request = Request(
        request_url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urlopen(request, timeout=timeout, context=ssl_context) as response:  # noqa: S310
            payload = response.read(MAX_DOWNLOAD_BYTES + 1)
            if len(payload) > MAX_DOWNLOAD_BYTES:
                raise ValueError(f"response_exceeds_{MAX_DOWNLOAD_BYTES}_bytes")
            return response.status, dict(response.headers.items()), payload
    except HTTPError as error:
        return error.code, dict(error.headers.items()) if error.headers else {}, error.read()
    except (URLError, TimeoutError) as error:
        raise ConnectionError(str(error)) from error


def fetch_json(url: str, timeout: int) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    try:
        status, headers, payload = http_get(url, timeout)
    except (ConnectionError, ValueError) as error:
        return None, {"url": url, "status": "error", "error": str(error)}
    if status != 200:
        return None, {"url": url, "status": status, "bytes": len(payload)}
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        return None, {
            "url": url,
            "status": status,
            "bytes": len(payload),
            "error": f"invalid_json:{error.msg}",
        }
    if not isinstance(value, dict):
        return None, {"url": url, "status": status, "error": "json_not_object"}
    return value, {
        "url": url,
        "status": status,
        "bytes": len(payload),
        "content_type": headers.get("Content-Type", ""),
    }


def openalex_pdf_locations(metadata: dict[str, Any]) -> list[dict[str, str]]:
    locations: list[dict[str, str]] = []
    seen: set[str] = set()
    candidates = [metadata.get("best_oa_location"), *(metadata.get("locations") or [])]
    for location in candidates:
        if not isinstance(location, dict) or not location.get("is_oa"):
            continue
        pdf_url = location.get("pdf_url")
        if not isinstance(pdf_url, str) or not pdf_url or pdf_url in seen:
            continue
        seen.add(pdf_url)
        source = location.get("source") or {}
        locations.append(
            {
                "url": pdf_url,
                "source": str(source.get("display_name", "OpenAlex OA location")),
                "license": str(location.get("license") or ""),
                "version": str(location.get("version") or ""),
            }
        )
    return locations


def openalex_oa_landing_urls(metadata: dict[str, Any]) -> list[str]:
    """Return OA landing pages when OpenAlex has no direct PDF location."""
    urls: list[str] = []
    seen: set[str] = set()
    candidates = [metadata.get("best_oa_location"), *(metadata.get("locations") or [])]
    for location in candidates:
        if not isinstance(location, dict) or not location.get("is_oa"):
            continue
        landing_url = location.get("landing_page_url")
        if isinstance(landing_url, str) and landing_url and landing_url not in seen:
            seen.add(landing_url)
            urls.append(landing_url)
    oa_url = metadata.get("open_access", {}).get("oa_url")
    if isinstance(oa_url, str) and oa_url and oa_url not in seen:
        urls.append(oa_url)
    return urls


def landing_page_pdf_locations(
    url: str, timeout: int
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Find publisher-declared PDF links on an OpenAlex-confirmed OA page."""
    try:
        status, headers, payload = http_get(url, timeout)
    except (ConnectionError, ValueError) as error:
        return [], {"kind": "oa_landing_page", "url": url, "status": "error", "error": str(error)}
    audit = {
        "kind": "oa_landing_page",
        "url": url,
        "status": status,
        "content_type": headers.get("Content-Type", ""),
        "bytes": len(payload),
    }
    if status != 200 or b"<html" not in payload[:2048].lower():
        return [], audit
    parser = PdfLinkParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    locations: list[dict[str, str]] = []
    seen: set[str] = set()
    for href in parser.urls:
        pdf_url = urljoin(url, href)
        parsed = urlparse(pdf_url)
        if parsed.scheme not in {"http", "https"} or pdf_url in seen:
            continue
        seen.add(pdf_url)
        locations.append(
            {
                "url": pdf_url,
                "source": "OpenAlex-confirmed OA landing page",
                "license": "",
                "version": "publisher-declared PDF link",
            }
        )
    return locations, audit


def europepmc_pdf_locations(metadata: dict[str, Any]) -> list[dict[str, str]]:
    locations: list[dict[str, str]] = []
    seen: set[str] = set()
    urls = metadata.get("fullTextUrlList", {}).get("fullTextUrl", [])
    for item in urls if isinstance(urls, list) else []:
        if not isinstance(item, dict):
            continue
        if item.get("documentStyle") != "pdf":
            continue
        if item.get("availabilityCode") not in {"OA", "F"}:
            continue
        url = item.get("url")
        if not isinstance(url, str) or not url or url in seen:
            continue
        seen.add(url)
        locations.append(
            {
                "url": url,
                "source": f"Europe PMC ({item.get('site', 'free PDF')})",
                "license": str(metadata.get("license") or ""),
                "version": "Europe PMC free PDF",
            }
        )
    return locations


def europepmc_record(doi: str, timeout: int) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    query = quote(f'DOI:"{doi}"', safe=":")
    url = f"{EUROPEPMC_SEARCH}?query={query}&format=json&pageSize=1&resultType=core"
    response, audit = fetch_json(url, timeout)
    if not response:
        return None, audit
    results = response.get("resultList", {}).get("result", [])
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        return None, {**audit, "error": "no_europepmc_record"}
    return results[0], audit


def valid_xml(payload: bytes) -> bool:
    prefix = payload.lstrip()[:512].lower()
    return prefix.startswith(b"<?xml") or b"<article" in prefix


def try_download(
    target: Target,
    url: str,
    kind: str,
    source: str,
    license_name: str,
    version: str,
    files_dir: Path,
    timeout: int,
) -> tuple[dict[str, Any], bytes | None, str | None]:
    attempt: dict[str, Any] = {
        "kind": kind,
        "source": source,
        "url": url,
        "license": license_name,
        "version": version,
    }
    extension = "pdf" if kind == "pdf" else "xml"
    destination = files_dir / f"{target.file_stem}.{extension}"
    if destination.exists():
        payload = destination.read_bytes()
        valid = payload.startswith(PDF_MAGIC) if kind == "pdf" else valid_xml(payload)
        if valid:
            return (
                {
                    **attempt,
                    "status": "reused",
                    "bytes": len(payload),
                    "path": str(destination),
                    "sha256": sha256_bytes(payload),
                },
                payload,
                str(destination),
            )
        destination.unlink()
    try:
        status, headers, payload = http_get(url, timeout)
    except (ConnectionError, ValueError) as error:
        return {**attempt, "status": "error", "error": str(error)}, None, None

    attempt.update(
        {
            "status": status,
            "content_type": headers.get("Content-Type", ""),
            "bytes": len(payload),
        }
    )
    if status != 200:
        return attempt, None, None
    valid = payload.startswith(PDF_MAGIC) if kind == "pdf" else valid_xml(payload)
    if not valid:
        return {**attempt, "status": "invalid_content"}, None, None

    destination.write_bytes(payload)
    return (
        {
            **attempt,
            "status": "downloaded",
            "path": str(destination),
            "sha256": sha256_bytes(payload),
        },
        payload,
        str(destination),
    )


def select_targets(
    triage_path: Path,
    screening_input_path: Path,
    queue: str,
    expected_count: int,
) -> list[Target]:
    triage = read_csv(triage_path)
    input_by_id = {row["record_id"]: row for row in read_csv(screening_input_path)}
    targets: list[Target] = []
    for row in triage:
        if row.get("manual_triage_queue") != queue:
            continue
        source = input_by_id.get(row["record_id"])
        if not source:
            raise ValueError(f"Missing screening-input record: {row['record_id']}")
        if source.get("is_preprint") == "True":
            continue
        doi = normalize_doi(row.get("doi", ""))
        if not doi:
            raise ValueError(f"Target record lacks DOI: {row['record_id']}")
        targets.append(
            Target(
                record_id=row["record_id"],
                doi=doi,
                title=row["title"],
                source=row["source"],
                year=row["year"],
                design_anchor=row["design_anchor"],
                pmid=source.get("pmid", ""),
                pmcid=source.get("pmcid", ""),
            )
        )
    if len(targets) != expected_count:
        raise ValueError(
            f"Expected {expected_count} non-preprint {queue} records, found {len(targets)}"
        )
    dois = [target.doi for target in targets]
    if len(dois) != len(set(dois)):
        raise ValueError("Target list contains duplicate normalized DOIs")
    return sorted(targets, key=lambda target: target.doi)


def retrieve_one(target: Target, output_dir: Path, timeout: int, dry_run: bool) -> dict[str, Any]:
    metadata_dir = output_dir / "raw_metadata"
    files_dir = output_dir / "files"
    attempts: list[dict[str, Any]] = []
    metadata_audit: list[dict[str, Any]] = []
    openalex_url = OPENALEX_WORK + quote(target.doi, safe="")
    openalex, audit = fetch_json(openalex_url, timeout)
    metadata_audit.append({"source": "openalex", **audit})
    if openalex:
        (metadata_dir / f"{target.file_stem}.openalex.json").write_text(
            json.dumps(openalex, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    europepmc, audit = europepmc_record(target.doi, timeout)
    metadata_audit.append({"source": "europepmc", **audit})
    if europepmc:
        (metadata_dir / f"{target.file_stem}.europepmc.json").write_text(
            json.dumps(europepmc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    if dry_run:
        return {
            "record_id": target.record_id,
            "doi": target.doi,
            "title": target.title,
            "target_status": "metadata_only",
            "metadata_attempts": metadata_audit,
            "content_attempts": attempts,
        }

    if openalex:
        for location in openalex_pdf_locations(openalex):
            attempt, _, path = try_download(
                target,
                location["url"],
                "pdf",
                location["source"],
                location["license"],
                location["version"],
                files_dir,
                timeout,
            )
            attempts.append(attempt)
            if path:
                return {
                    "record_id": target.record_id,
                    "doi": target.doi,
                    "title": target.title,
                    "target_status": "downloaded_pdf",
                    "selected_file": path,
                    "metadata_attempts": metadata_audit,
                    "content_attempts": attempts,
                }

        # OpenAlex sometimes confirms OA but only exposes a landing page.  Inspect
        # that page solely for an explicit publisher PDF link; do not probe paywalls.
        for landing_url in openalex_oa_landing_urls(openalex):
            locations, landing_audit = landing_page_pdf_locations(
                landing_url, min(timeout, LANDING_PAGE_TIMEOUT_SECONDS)
            )
            attempts.append(landing_audit)
            for location in locations:
                attempt, _, path = try_download(
                    target,
                    location["url"],
                    "pdf",
                    location["source"],
                    location["license"],
                    location["version"],
                    files_dir,
                    timeout,
                )
                attempts.append(attempt)
                if path:
                    return {
                        "record_id": target.record_id,
                        "doi": target.doi,
                        "title": target.title,
                        "target_status": "downloaded_pdf",
                        "selected_file": path,
                        "metadata_attempts": metadata_audit,
                        "content_attempts": attempts,
                    }

    if europepmc:
        for location in europepmc_pdf_locations(europepmc):
            attempt, _, path = try_download(
                target,
                location["url"],
                "pdf",
                location["source"],
                location["license"],
                location["version"],
                files_dir,
                timeout,
            )
            attempts.append(attempt)
            if path:
                return {
                    "record_id": target.record_id,
                    "doi": target.doi,
                    "title": target.title,
                    "target_status": "downloaded_pdf",
                    "selected_file": path,
                    "metadata_attempts": metadata_audit,
                    "content_attempts": attempts,
                }

    pmcid = target.pmcid or str((europepmc or {}).get("pmcid") or "")
    if pmcid:
        url = EUROPEPMC_XML.format(pmcid=quote(normalize_pmcid(pmcid), safe=""))
        attempt, _, path = try_download(
            target,
            url,
            "xml",
            "Europe PMC",
            str((europepmc or {}).get("license") or ""),
            "fullTextXML",
            files_dir,
            timeout,
        )
        attempts.append(attempt)
        if path:
            return {
                "record_id": target.record_id,
                "doi": target.doi,
                "title": target.title,
                "target_status": "downloaded_xml",
                "selected_file": path,
                "metadata_attempts": metadata_audit,
                "content_attempts": attempts,
            }

    oa_status = (openalex or {}).get("open_access", {}).get("is_oa")
    return {
        "record_id": target.record_id,
        "doi": target.doi,
        "title": target.title,
        "target_status": "open_location_unavailable" if oa_status else "no_open_full_text_found",
        "metadata_attempts": metadata_audit,
        "content_attempts": attempts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("triage", type=Path)
    parser.add_argument("screening_input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--queue", default="priority_1_textually_focused")
    parser.add_argument("--expected-count", type=int, default=119)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 8:
        raise ValueError("workers must be between 1 and 8")

    targets = select_targets(args.triage, args.screening_input, args.queue, args.expected_count)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "files").mkdir(exist_ok=True)
    (args.output_dir / "raw_metadata").mkdir(exist_ok=True)
    write_csv(
        args.output_dir / "targets.csv",
        [
            {
                "record_id": target.record_id,
                "doi": target.doi,
                "title": target.title,
                "year": target.year,
                "source": target.source,
                "design_anchor": target.design_anchor,
                "pmid": target.pmid,
                "pmcid": target.pmcid,
                "is_preprint": "false",
            }
            for target in targets
        ],
    )

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_target = {
            executor.submit(
                retrieve_one, target, args.output_dir, args.timeout, args.dry_run
            ): target
            for target in targets
        }
        for future in as_completed(future_to_target):
            target = future_to_target[future]
            try:
                results.append(future.result())
            except Exception as error:  # Keep every target in the audit trail.
                results.append(
                    {
                        "record_id": target.record_id,
                        "doi": target.doi,
                        "title": target.title,
                        "target_status": "retrieval_error",
                        "error": repr(error),
                        "metadata_attempts": [],
                        "content_attempts": [],
                    }
                )
            time.sleep(0.05)
    results.sort(key=lambda row: str(row["doi"]))
    with (args.output_dir / "retrieval_manifest.jsonl").open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")

    unavailable_rows = [
        {
            "record_id": str(result["record_id"]),
            "doi": str(result["doi"]),
            "title": str(result["title"]),
            "retrieval_status": str(result["target_status"]),
        }
        for result in results
        if result["target_status"] not in {"downloaded_pdf", "downloaded_xml"}
    ]
    if unavailable_rows:
        write_csv(args.output_dir / "unavailable.csv", unavailable_rows)

    selected_dir = args.output_dir / "selected_files"
    selected_dir.mkdir(exist_ok=True)
    for result in results:
        selected_file = result.get("selected_file")
        if not isinstance(selected_file, str):
            continue
        source = Path(selected_file)
        destination = selected_dir / source.name
        if destination.exists() or destination.is_symlink():
            destination.unlink()
        destination.symlink_to(source.resolve())

    statuses = Counter(str(result["target_status"]) for result in results)
    summary = {
        "status": "dry_run_complete" if args.dry_run else "retrieval_complete",
        "target_count": len(targets),
        "queue": args.queue,
        "excluded_preprints": 16,
        "workers": args.workers,
        "timeout_seconds": args.timeout,
        "status_counts": dict(sorted(statuses.items())),
        "retrieval_policy": (
            "OpenAlex OA PDF locations and explicit publisher PDF links from "
            "OpenAlex-confirmed OA landing pages, followed by Europe PMC free PDFs "
            "and full-text XML. "
            "No publisher access controls were bypassed."
        ),
        "target_list_sha256": sha256_bytes((args.output_dir / "targets.csv").read_bytes()),
        "manifest_sha256": sha256_bytes(
            (args.output_dir / "retrieval_manifest.jsonl").read_bytes()
        ),
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "README.md").write_text(
        "# Full-Text Retrieval: 119 Non-Preprint Priority-1 Records\n\n"
        "Targets are the 119 non-preprint records in `priority_1_textually_focused`: "
        "the previous 135-record manual title/abstract queue minus 16 preprints. "
        "`targets.csv`, `retrieval_manifest.jsonl`, and `summary.json` are the audit "
        "trail. `files/` contains locally downloaded open PDFs or Europe PMC XML and "
        "is intentionally excluded from Git. `selected_files/` is the canonical local "
        "view: it contains links only to files selected in the manifest. `raw_metadata/` "
        "contains source metadata responses and is also local.\n\n"
        "Retrieval uses OpenAlex-confirmed OA locations (including explicit publisher "
        "PDF links found on their OA landing pages) and Europe PMC free PDFs/full-text "
        "XML. It does not bypass paywalls; `unavailable.csv` lists records without a "
        "retrieved legal open full text.\n\n"
        f"This retrieval obtained {statuses.get('downloaded_pdf', 0)} PDFs and "
        f"{statuses.get('downloaded_xml', 0)} XML full texts. "
        f"The remaining {len(unavailable_rows)} records are listed in `unavailable.csv`.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
