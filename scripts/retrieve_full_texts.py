#!/usr/bin/env python3
"""Retrieve lawful open full texts for a frozen review target set.

The script selects non-preprint records from a named manual-triage queue,
queries scholarly OA resolvers by identifier, and downloads only publicly
available PDFs, full-text XML, or public PMC author-manuscript HTML. It does
not bypass publisher access controls. All identifiers, source URLs, responses,
checksums, and failures are recorded in the output directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
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
CROSSREF_WORK = "https://api.crossref.org/works/"
OPENAIRE_SEARCH = "https://api.openaire.eu/search/publications"
SEMANTIC_SCHOLAR_PAPER = "https://api.semanticscholar.org/graph/v1/paper/DOI:"
UNPAYWALL_WORK = "https://api.unpaywall.org/v2/"
USER_AGENT = "causal-multiomics-aging-review/1.0 full-text-retrieval"
PDF_MAGIC = b"%PDF-"
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
LANDING_PAGE_TIMEOUT_SECONDS = 12
FULL_TEXT_STATUSES = {"downloaded_pdf", "downloaded_xml", "downloaded_html"}


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


def public_copy_locations(path: Path | None, doi: str) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    locations: list[dict[str, str]] = []
    for row in read_csv(path):
        if normalize_doi(row.get("doi", "")) != doi:
            continue
        url = row.get("url", "").strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"Invalid public-copy URL for {doi}: {url}")
        locations.append(
            {
                "url": url,
                "source": row.get("source", "Public author-hosted copy").strip(),
                "license": "",
                "version": row.get("access_basis", "public author-hosted copy").strip(),
            }
        )
    return locations


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
            deadline = time.monotonic() + timeout
            chunks: list[bytes] = []
            received = 0
            while True:
                if time.monotonic() > deadline:
                    raise TimeoutError(f"response_read_exceeded_{timeout}_seconds")
                chunk = response.read(min(64 * 1024, MAX_DOWNLOAD_BYTES + 1 - received))
                if not chunk:
                    break
                chunks.append(chunk)
                received += len(chunk)
                if received > MAX_DOWNLOAD_BYTES:
                    raise ValueError(f"response_exceeds_{MAX_DOWNLOAD_BYTES}_bytes")
            payload = b"".join(chunks)
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
    url: str, source: str, timeout: int
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Find explicitly declared PDF links on a scholarly repository or OA page."""
    try:
        status, headers, payload = http_get(url, timeout)
    except (ConnectionError, ValueError) as error:
        return [], {
            "kind": "landing_page",
            "source": source,
            "url": url,
            "status": "error",
            "error": str(error),
        }
    audit = {
        "kind": "landing_page",
        "source": source,
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
                "source": source,
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


def crossref_record(doi: str, timeout: int) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    response, audit = fetch_json(CROSSREF_WORK + quote(doi, safe=""), timeout)
    message = (response or {}).get("message")
    if not isinstance(message, dict):
        return None, {**audit, "error": "no_crossref_record"}
    return message, audit


def crossref_pdf_locations(metadata: dict[str, Any]) -> list[dict[str, str]]:
    locations: list[dict[str, str]] = []
    seen: set[str] = set()
    links = metadata.get("link") or []
    for link in links if isinstance(links, list) else []:
        if not isinstance(link, dict) or link.get("content-type") != "application/pdf":
            continue
        url = link.get("URL")
        if not isinstance(url, str) or not url or url in seen:
            continue
        seen.add(url)
        locations.append(
            {
                "url": url,
                "source": "Crossref publisher content link",
                "license": "",
                "version": str(link.get("content-version") or ""),
            }
        )
    return locations


def unpaywall_record(
    doi: str, email: str | None, timeout: int
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Retrieve OA locations without persisting the required contact email."""
    if not email:
        return None, {"status": "skipped", "error": "unpaywall_email_not_configured"}
    url = f"{UNPAYWALL_WORK}{quote(doi, safe='')}?email={quote(email, safe='')}"
    response, audit = fetch_json(url, timeout)
    audit["url"] = f"{UNPAYWALL_WORK}{quote(doi, safe='')}?email=[redacted]"
    return response, audit


def unpaywall_locations(metadata: dict[str, Any]) -> list[dict[str, str]]:
    """Return direct PDFs and repository landing pages reported by Unpaywall."""
    locations: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    candidates = [metadata.get("best_oa_location"), *(metadata.get("oa_locations") or [])]
    for location in candidates:
        if not isinstance(location, dict):
            continue
        host_type = str(location.get("host_type") or "")
        license_value = str(location.get("license") or "")
        version = str(location.get("version") or "")
        for kind, field in (("pdf", "url_for_pdf"), ("landing", "url")):
            url = location.get(field)
            if not isinstance(url, str) or not url or (kind, url) in seen:
                continue
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                continue
            seen.add((kind, url))
            locations.append(
                {
                    "url": url,
                    "kind": kind,
                    "source": f"Unpaywall {host_type or 'OA'} location",
                    "license": license_value,
                    "version": version,
                }
            )
    return locations


def pmc_fulltext_html_locations(metadata: dict[str, Any]) -> list[dict[str, str]]:
    """Return public PMC full-text pages when a manuscript has no retrievable PDF."""
    locations: list[dict[str, str]] = []
    seen: set[str] = set()
    for location in unpaywall_locations(metadata):
        parsed = urlparse(location["url"])
        if parsed.netloc != "pmc.ncbi.nlm.nih.gov":
            continue
        parts = parsed.path.strip("/").split("/")
        if len(parts) < 2 or parts[0] != "articles" or not parts[1].startswith("PMC"):
            continue
        html_url = f"https://pmc.ncbi.nlm.nih.gov/articles/{parts[1]}/"
        if html_url in seen:
            continue
        seen.add(html_url)
        locations.append(
            {
                **location,
                "url": html_url,
                "kind": "landing",
                "source": "PubMed Central public author manuscript HTML",
                "version": location["version"] or "author manuscript",
            }
        )
    return locations


def canonical_publisher_pdf_locations(doi: str) -> list[dict[str, str]]:
    """Known publisher PDF routes that are not consistently present in metadata APIs."""
    if doi.startswith("10.1038/"):
        return [
            {
                "url": f"https://www.nature.com/articles/{doi.removeprefix('10.1038/')}.pdf",
                "source": "Nature canonical article PDF",
                "license": "",
                "version": "publisher version of record",
            }
        ]
    if doi.startswith(("10.1007/", "10.1186/")):
        return [
            {
                "url": f"https://link.springer.com/content/pdf/{doi}.pdf",
                "source": "Springer Nature canonical article PDF",
                "license": "",
                "version": "publisher version of record",
            }
        ]
    return []


def semantic_scholar_record(
    doi: str, timeout: int
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    fields = "title,openAccessPdf,publicationTypes,publicationDate,url"
    url = f"{SEMANTIC_SCHOLAR_PAPER}{quote(doi, safe='')}?fields={fields}"
    return fetch_json(url, timeout)


def semantic_scholar_pdf_locations(metadata: dict[str, Any]) -> list[dict[str, str]]:
    pdf = metadata.get("openAccessPdf")
    if not isinstance(pdf, dict):
        return []
    url = pdf.get("url")
    status = str(pdf.get("status") or "").upper()
    parsed = urlparse(url) if isinstance(url, str) else None
    if (
        not isinstance(url, str)
        or not url
        or not parsed
        or parsed.scheme not in {"http", "https"}
        or parsed.netloc.casefold() in {"doi.org", "dx.doi.org"}
        or status not in {"BRONZE", "GOLD", "GREEN", "HYBRID"}
    ):
        return []
    return [
        {
            "url": url,
            "source": "Semantic Scholar open-access PDF",
            "license": str(pdf.get("license") or ""),
            "version": f"Semantic Scholar {status}",
        }
    ]


def openaire_record(doi: str, timeout: int) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    url = f"{OPENAIRE_SEARCH}?doi={quote(doi, safe='')}&format=json&size=1"
    return fetch_json(url, timeout)


def openaire_text(value: Any) -> str:
    if isinstance(value, dict):
        candidate = value.get("$")
        return candidate if isinstance(candidate, str) else ""
    return value if isinstance(value, str) else ""


def openaire_repository_locations(metadata: dict[str, Any]) -> list[dict[str, str]]:
    """Use repository instance links exposed by OpenAIRE, not publisher DOI links."""
    locations: list[dict[str, str]] = []
    seen: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if not isinstance(value, dict):
            return
        nested_instance = value.get("instance")
        if isinstance(nested_instance, list):
            instances = [item for item in nested_instance if isinstance(item, dict)]
        elif isinstance(nested_instance, dict):
            instances = [nested_instance]
        elif "accessright" in value:
            instances = [value]
        else:
            instances = []
        for instance in instances:
            accessright = instance.get("accessright")
            access_class = (
                str(accessright.get("@classid") or "").upper()
                if isinstance(accessright, dict)
                else ""
            )
            hosted = instance.get("hostedby")
            host_name = (
                openaire_text(hosted.get("@name")) if isinstance(hosted, dict) else "repository"
            )
            webresource = instance.get("webresource")
            resource_url = (
                openaire_text(webresource.get("url")) if isinstance(webresource, dict) else ""
            )
            direct_url = openaire_text(instance.get("url")) or resource_url
            parsed = urlparse(direct_url)
            if (
                access_class != "CLOSED"
                and parsed.scheme in {"http", "https"}
                and parsed.netloc.casefold()
                not in {"doi.org", "dx.doi.org", "pubmed.ncbi.nlm.nih.gov"}
                and direct_url not in seen
            ):
                seen.add(direct_url)
                locations.append(
                    {
                        "url": direct_url,
                        "source": f"OpenAIRE repository ({host_name})",
                        "license": "",
                        "version": f"OpenAIRE {access_class or 'unknown'} access",
                    }
                )
        for child in value.values():
            visit(child)

    visit(metadata)
    return locations


def valid_xml(payload: bytes) -> bool:
    prefix = payload.lstrip()[:512].lower()
    return prefix.startswith(b"<?xml") or b"<article" in prefix


def valid_fulltext_html(payload: bytes) -> bool:
    prefix = payload[:2_000_000].lower()
    return b"<html" in prefix[:2048] and b"article-body" in prefix


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
    extension = {"pdf": "pdf", "xml": "xml", "html": "html"}[kind]
    destination = files_dir / f"{target.file_stem}.{extension}"
    if destination.exists():
        payload = destination.read_bytes()
        valid = (
            payload.startswith(PDF_MAGIC)
            if kind == "pdf"
            else valid_xml(payload)
            if kind == "xml"
            else valid_fulltext_html(payload)
        )
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
    valid = (
        payload.startswith(PDF_MAGIC)
        if kind == "pdf"
        else valid_xml(payload)
        if kind == "xml"
        else valid_fulltext_html(payload)
    )
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


def retrieve_one(
    target: Target,
    output_dir: Path,
    timeout: int,
    dry_run: bool,
    public_copy_list: Path | None,
    unpaywall_email: str | None,
) -> dict[str, Any]:
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

    crossref, audit = crossref_record(target.doi, timeout)
    metadata_audit.append({"source": "crossref", **audit})
    if crossref:
        (metadata_dir / f"{target.file_stem}.crossref.json").write_text(
            json.dumps(crossref, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    semantic_scholar, audit = semantic_scholar_record(target.doi, timeout)
    metadata_audit.append({"source": "semantic_scholar", **audit})
    if semantic_scholar:
        (metadata_dir / f"{target.file_stem}.semantic_scholar.json").write_text(
            json.dumps(semantic_scholar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    openaire, audit = openaire_record(target.doi, timeout)
    metadata_audit.append({"source": "openaire", **audit})
    if openaire:
        (metadata_dir / f"{target.file_stem}.openaire.json").write_text(
            json.dumps(openaire, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    unpaywall, audit = unpaywall_record(target.doi, unpaywall_email, timeout)
    metadata_audit.append({"source": "unpaywall", **audit})
    if unpaywall:
        (metadata_dir / f"{target.file_stem}.unpaywall.json").write_text(
            json.dumps(unpaywall, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
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
                landing_url,
                "OpenAlex-confirmed OA landing page",
                min(timeout, LANDING_PAGE_TIMEOUT_SECONDS),
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

    if crossref:
        for location in crossref_pdf_locations(crossref):
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

    if unpaywall:
        for location in unpaywall_locations(unpaywall):
            if location["kind"] == "pdf":
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
                continue

            locations, landing_audit = landing_page_pdf_locations(
                location["url"], location["source"], min(timeout, LANDING_PAGE_TIMEOUT_SECONDS)
            )
            attempts.append(landing_audit)
            for pdf_location in locations:
                attempt, _, path = try_download(
                    target,
                    pdf_location["url"],
                    "pdf",
                    pdf_location["source"],
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

        for location in pmc_fulltext_html_locations(unpaywall):
            attempt, _, path = try_download(
                target,
                location["url"],
                "html",
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
                    "target_status": "downloaded_html",
                    "selected_file": path,
                    "metadata_attempts": metadata_audit,
                    "content_attempts": attempts,
                }

    for location in canonical_publisher_pdf_locations(target.doi):
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

    for location in public_copy_locations(public_copy_list, target.doi):
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

    if semantic_scholar:
        for location in semantic_scholar_pdf_locations(semantic_scholar):
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

    if openaire:
        for location in openaire_repository_locations(openaire):
            locations, landing_audit = landing_page_pdf_locations(
                location["url"], location["source"], min(timeout, LANDING_PAGE_TIMEOUT_SECONDS)
            )
            attempts.append(landing_audit)
            for pdf_location in locations:
                attempt, _, path = try_download(
                    target,
                    pdf_location["url"],
                    "pdf",
                    pdf_location["source"],
                    pdf_location["license"],
                    pdf_location["version"],
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

    # A transient OpenAlex error must not relabel a verified OA record as closed.
    # Unpaywall is an independent DOI-level OA resolver and is sufficient here.
    oa_status = bool((openalex or {}).get("open_access", {}).get("is_oa")) or bool(
        (unpaywall or {}).get("is_oa")
    )
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
    parser.add_argument(
        "--public-copy-list",
        type=Path,
        help="CSV of publicly hosted author copies: doi,url,source,access_basis.",
    )
    parser.add_argument(
        "--unpaywall-email",
        default=os.environ.get("UNPAYWALL_EMAIL"),
        help="Contact email required by Unpaywall; defaults to UNPAYWALL_EMAIL.",
    )
    parser.add_argument(
        "--resume-unavailable",
        action="store_true",
        help="Retry only records that were not downloaded in the current manifest.",
    )
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
    retry_targets = targets
    if args.resume_unavailable:
        manifest_path = args.output_dir / "retrieval_manifest.jsonl"
        if not manifest_path.exists():
            raise ValueError("--resume-unavailable requires an existing retrieval manifest")
        existing_by_doi = {
            str(row["doi"]): row
            for row in (json.loads(line) for line in manifest_path.open(encoding="utf-8"))
        }
        if set(existing_by_doi) != {target.doi for target in targets}:
            raise ValueError("Existing manifest does not match the frozen target DOI set")
        results.extend(
            row
            for row in existing_by_doi.values()
            if row.get("target_status") in FULL_TEXT_STATUSES
        )
        retry_targets = [
            target
            for target in targets
            if existing_by_doi[target.doi].get("target_status")
            not in FULL_TEXT_STATUSES
        ]

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_target = {
            executor.submit(
                retrieve_one,
                target,
                args.output_dir,
                args.timeout,
                args.dry_run,
                args.public_copy_list,
                args.unpaywall_email,
            ): target
            for target in retry_targets
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
        if result["target_status"] not in FULL_TEXT_STATUSES
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
        "retried_count": len(retry_targets),
        "queue": args.queue,
        "excluded_preprints": 16,
        "workers": args.workers,
        "timeout_seconds": args.timeout,
        "status_counts": dict(sorted(statuses.items())),
        "retrieval_policy": (
            "OpenAlex, Unpaywall, Europe PMC, Crossref, Semantic Scholar, and OpenAIRE "
            "metadata routes; explicit publisher PDF links from verified OA landing pages; "
            "and explicitly recorded public author-hosted copies. "
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
        "trail. `files/` contains locally downloaded PDFs, XML, or public PMC author-"
        "manuscript HTML and is intentionally excluded from Git. `selected_files/` is "
        "the canonical local view: it contains links only to files selected in the "
        "manifest. `raw_metadata/` "
        "contains source metadata responses and is also local.\n\n"
        "Retrieval uses OpenAlex and Unpaywall OA locations (including explicit publisher "
        "PDF links found on verified OA landing pages), Europe PMC free PDFs/full-text "
        "XML, Crossref, Semantic Scholar, OpenAIRE, and explicitly recorded public "
        "author-hosted copies. It does not bypass paywalls; `unavailable.csv` lists "
        "records without a retrieved legal open full text.\n\n"
        f"This retrieval obtained {statuses.get('downloaded_pdf', 0)} PDFs and "
        f"{statuses.get('downloaded_xml', 0)} XML and "
        f"{statuses.get('downloaded_html', 0)} public PMC HTML full texts. "
        f"The remaining {len(unavailable_rows)} records are listed in `unavailable.csv`.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
