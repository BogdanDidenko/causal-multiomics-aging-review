#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "protocol"
SEARCH_CONFIG = PROTOCOL / "search_config.json"
QUERY_FILES: dict[str, Path] = {}
QUERY_BRANCH_FILES: dict[str, dict[str, Path]] = {}
MAX_RECORDS_PER_SOURCE: int | None = None
SAMPLE_SEED: int | None = None

PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
EUROPEPMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
SCOPUS_SEARCH = "https://api.elsevier.com/content/search/scopus"
SEMANTIC_SCHOLAR_BULK = (
    "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
)
SPRINGER_META = "https://api.springernature.com/meta/v2/json"
OPENALEX_WORKS = "https://api.openalex.org/works"

KEYCHAIN = {
    "PUBMED_API_KEY": ("eutils.ncbi.nlm.nih.gov", "PubMed API Key"),
    "SCOPUS_API_KEY": ("api.elsevier.com", "Scopus API Key"),
    "SEMANTIC_SCHOLAR_API_KEY": (
        "api.semanticscholar.org",
        "Semantic Scholar API Key",
    ),
    "SPRINGERNATURE_META_API_KEY": ("api.springernature.com", "Meta API Key"),
    "OPENALEX_API_KEY": ("api.openalex.org", "OpenAlex API Key"),
}

FIELDS = [
    "source",
    "source_record_id",
    "title",
    "abstract",
    "year",
    "publication_date",
    "doi",
    "pmid",
    "pmcid",
    "authors",
    "venue",
    "document_type",
    "language",
    "url",
    "is_preprint",
    "raw_page",
    "query_branches",
    "local_multiomics_match",
    "local_explicit_multiomics_match",
    "local_layer_pair_match",
    "local_omics_layer_count",
    "local_omics_layers",
    "local_aging_match",
    "local_causal_anchor_match",
    "local_three_block_match",
]

MULTIOMICS_RE = re.compile(
    r"\b(?:multi[-\s\u2010-\u2015]?omics?|multiome|integrative[-\s]+omics|"
    r"integrated[-\s]+omics|cross[-\s]+omics|pan[-\s]?omics)\b",
    re.I,
)
OMICS_LAYER_RES = {
    "genomics": re.compile(
        r"\b(?:genom(?:e|ic|ics|wide)|GWAS|genetic[-\s]+variant|"
        r"quantitative[-\s]+trait[-\s]+loc|[emp]QTL|QTL)\w*",
        re.I,
    ),
    "epigenomics": re.compile(
        r"\b(?:epigenom|DNA[-\s]+methyl|methylom|chromatin|ATAC[-\s]?seq)\w*",
        re.I,
    ),
    "transcriptomics": re.compile(
        r"\b(?:transcriptom|RNA[-\s]?seq|gene[-\s]+expression)\w*",
        re.I,
    ),
    "proteomics": re.compile(r"\b(?:proteom|protein[-\s]+abundance)\w*", re.I),
    "metabolomics": re.compile(
        r"\b(?:metabolom|lipidom|metabolite|lipoprotein)\w*",
        re.I,
    ),
    "microbiomics": re.compile(
        r"\b(?:microbiom|metagenom|microbial[-\s]+community)\w*",
        re.I,
    ),
}
AGING_RE = re.compile(
    r"\b(?:aging|ageing|biological[-\s]+ag(?:e|ing|eing)|"
    r"epigenetic[-\s]+ag(?:e|ing|eing)|age[-\s]+acceleration|"
    r"(?:aging|ageing|epigenetic)[-\s]+clock|longevity|life[-\s]?span|"
    r"health[-\s]?span|centenarian|geroscience|geroprotect|rejuvenat|"
    r"hallmarks?[-\s]+of[-\s]+ag(?:ing|eing)|cellular[-\s]+senescence|"
    r"senolytic|senomorphic)\w*",
    re.I,
)
CAUSAL_ANCHOR_RE = re.compile(
    r"\b(?:causal|causality|Mendelian[-\s]+randomi[sz]ation|"
    r"\bSMR\b|\bHEIDI\b|genetic[-\s]+instruments?|"
    r"instrumental[-\s]+variables?|mediat(?:e|ed|es|ing|ion)|"
    r"natural[-\s]+(?:direct|indirect)[-\s]+effect|"
    r"controlled[-\s]+direct[-\s]+effect|randomi[sz]ed[-\s]+"
    r"(?:controlled[-\s]+)?trial|controlled[-\s]+clinical[-\s]+trial|"
    r"intervention|perturb|CRISPR[-\s]+(?:screen|perturbation)|"
    r"knockout|knockdown|overexpression|natural[-\s]+experiment|"
    r"quasi[-\s]?experiment|difference[-\s]+in[-\s]+differences|"
    r"regression[-\s]+discontinuity|interrupted[-\s]+time[-\s]+series|"
    r"Granger[-\s]+causality|directed[-\s]+acyclic[-\s]+graph|"
    r"Bayesian[-\s]+network|structural[-\s]+equation[-\s]+model|"
    r"causal[-\s]+(?:graph|network))\w*",
    re.I,
)


class HttpError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    value = html.unescape(re.sub(r"<[^>]+>", " ", str(value)))
    return re.sub(r"\s+", " ", value).strip()


def normalize_doi(value: Any) -> str:
    doi = clean_text(value).lower()
    doi = re.sub(r"^(?:doi:|https?://(?:dx\.)?doi\.org/)", "", doi)
    return doi.rstrip(" .")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def read_query(source: str) -> str:
    if source in QUERY_BRANCH_FILES:
        raise ValueError(f"{source} uses branch query files")
    path = QUERY_FILES.get(source, PROTOCOL / "queries" / f"{source}.txt")
    return path.read_text(encoding="utf-8").strip()


def read_query_paths(source: str) -> dict[str, Path]:
    if source in QUERY_BRANCH_FILES:
        return QUERY_BRANCH_FILES[source]
    return {"combined": read_query_path(source)}


def record_limit(reported_count: int) -> int:
    if MAX_RECORDS_PER_SOURCE is None:
        return reported_count
    return min(reported_count, MAX_RECORDS_PER_SOURCE)


def get_credential(name: str) -> str:
    if value := os.environ.get(name):
        return value
    server, account = KEYCHAIN[name]
    completed = subprocess.run(
        [
            "security",
            "find-internet-password",
            "-a",
            account,
            "-s",
            server,
            "-w",
        ],
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0 and completed.stdout.strip():
        return completed.stdout.strip()
    raise RuntimeError(
        f"Missing {name}; set it in the environment or macOS Keychain "
        f"(server={server}, account={account})"
    )


def request(
    url: str,
    params: dict[str, str],
    *,
    headers: dict[str, str] | None = None,
    post: bool = False,
    attempts: int = 8,
) -> bytes:
    for attempt in range(attempts):
        command = [
            "curl",
            "-sS",
            "--max-time",
            "180",
            "-w",
            "\n__HTTP_STATUS__:%{http_code}",
        ]
        if post:
            command += ["-X", "POST"]
        else:
            command += ["-G"]
        for key, value in params.items():
            command += ["--data-urlencode", f"{key}={value}"]
        for key, value in (headers or {}).items():
            command += ["-H", f"{key}: {value}"]
        command.append(url)
        completed = subprocess.run(command, capture_output=True)
        payload, marker, status_raw = completed.stdout.rpartition(
            b"\n__HTTP_STATUS__:"
        )
        status = int(status_raw or 0) if marker else 0
        if completed.returncode == 0 and 200 <= status < 300:
            return payload
        message = clean_text(payload[-1000:] or completed.stderr[-1000:])
        if status not in {429, 500, 502, 503, 504} or attempt + 1 == attempts:
            raise HttpError(status, message)
        time.sleep(min(60, 5 * (attempt + 1)))
    raise AssertionError("unreachable")


def request_json(
    url: str,
    params: dict[str, str],
    *,
    headers: dict[str, str] | None = None,
    post: bool = False,
) -> dict[str, Any]:
    value = json.loads(request(url, params, headers=headers, post=post))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object from {url}")
    return value


def write_gzip(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb", compresslevel=9) as handle:
        handle.write(payload)


def write_json_gzip(path: Path, payload: dict[str, Any]) -> None:
    write_gzip(
        path,
        (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )


def joined_text(element: ET.Element | None) -> str:
    return clean_text(" ".join(element.itertext()) if element is not None else "")


def pubmed_date(pubmed_article: ET.Element) -> str:
    article_date = pubmed_article.find(".//ArticleDate")
    pub_date = pubmed_article.find(".//JournalIssue/PubDate")
    node = article_date if article_date is not None else pub_date
    if node is None:
        return ""
    year = clean_text(node.findtext("Year"))
    if not year:
        year = clean_text(node.findtext("MedlineDate"))[:4]
    if not year.isdigit():
        return ""
    month_raw = clean_text(node.findtext("Month")) or "01"
    month_lookup = {
        name.lower(): index
        for index, name in enumerate(
            [
                "",
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
        )
    }
    month = int(month_raw) if month_raw.isdigit() else month_lookup.get(month_raw[:3].lower(), 1)
    day_raw = clean_text(node.findtext("Day")) or "1"
    day = int(day_raw) if day_raw.isdigit() else 1
    try:
        return datetime(int(year), month, day).date().isoformat()
    except ValueError:
        return f"{year}-01-01"


def classify_local(record: dict[str, Any]) -> dict[str, Any]:
    text = f"{record.get('title', '')} {record.get('abstract', '')}"
    explicit_multiomics = bool(MULTIOMICS_RE.search(text))
    layers = sorted(
        layer for layer, pattern in OMICS_LAYER_RES.items() if pattern.search(text)
    )
    layer_pair = len(layers) >= 2
    multiomics = explicit_multiomics or layer_pair
    aging = bool(AGING_RE.search(text))
    causal = bool(CAUSAL_ANCHOR_RE.search(text))
    record["local_multiomics_match"] = multiomics
    record["local_explicit_multiomics_match"] = explicit_multiomics
    record["local_layer_pair_match"] = layer_pair
    record["local_omics_layer_count"] = len(layers)
    record["local_omics_layers"] = ";".join(layers)
    record["local_aging_match"] = aging
    record["local_causal_anchor_match"] = causal
    record["local_three_block_match"] = multiomics and aging and causal
    return record


def parse_pubmed(xml_payload: bytes, raw_page: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_payload)
    records = []
    for pubmed_article in root.findall(".//PubmedArticle"):
        article = pubmed_article.find(".//Article")
        if article is None:
            continue
        pmid = clean_text(pubmed_article.findtext(".//PMID"))
        ids = pubmed_article.findall(".//ArticleId")
        doi = next(
            (
                clean_text(node.text)
                for node in ids
                if node.attrib.get("IdType") == "doi"
            ),
            "",
        )
        pmcid = next(
            (
                clean_text(node.text)
                for node in ids
                if node.attrib.get("IdType") == "pmc"
            ),
            "",
        )
        authors = []
        for author in article.findall("AuthorList/Author"):
            collective = clean_text(author.findtext("CollectiveName"))
            if collective:
                authors.append(collective)
                continue
            name = " ".join(
                part
                for part in [
                    clean_text(author.findtext("ForeName")),
                    clean_text(author.findtext("LastName")),
                ]
                if part
            )
            if name:
                authors.append(name)
        date = pubmed_date(pubmed_article)
        publication_types = [
            clean_text(node.text)
            for node in pubmed_article.findall(".//PublicationType")
        ]
        abstract = " ".join(
            joined_text(node) for node in article.findall("Abstract/AbstractText")
        )
        records.append(
            classify_local(
                {
                    "source": "pubmed",
                    "source_record_id": pmid,
                    "title": joined_text(article.find("ArticleTitle")),
                    "abstract": clean_text(abstract),
                    "year": date[:4],
                    "publication_date": date,
                    "doi": normalize_doi(doi),
                    "pmid": pmid,
                    "pmcid": pmcid,
                    "authors": "; ".join(authors),
                    "venue": clean_text(article.findtext(".//Journal/Title")),
                    "document_type": "; ".join(publication_types),
                    "language": "; ".join(
                        clean_text(node.text) for node in article.findall("Language")
                    ),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "is_preprint": any(
                        "preprint" in value.lower() for value in publication_types
                    ),
                    "raw_page": raw_page,
                }
            )
        )
    return records


def collect_pubmed(raw_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    query = read_query("pubmed")
    api_key = get_credential("PUBMED_API_KEY")
    search = request_json(
        PUBMED_ESEARCH,
        {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": "0",
            "usehistory": "y",
            "api_key": api_key,
        },
        post=True,
    )
    write_json_gzip(raw_dir / "search.json.gz", search)
    result = search["esearchresult"]
    count = int(result["count"])
    records = []
    for start in range(0, record_limit(count), 200):
        name = f"page_{start // 200 + 1:04d}.xml.gz"
        payload = request(
            PUBMED_EFETCH,
            {
                "db": "pubmed",
                "WebEnv": result["webenv"],
                "query_key": result["querykey"],
                "retstart": str(start),
                "retmax": str(min(200, record_limit(count) - start)),
                "rettype": "abstract",
                "retmode": "xml",
                "api_key": api_key,
            },
            post=True,
        )
        write_gzip(raw_dir / name, payload)
        records.extend(parse_pubmed(payload, name))
        time.sleep(0.12)
    return records, {"reported_count": count}


def parse_europepmc(item: dict[str, Any], raw_page: str) -> dict[str, Any]:
    publication_types = item.get("pubTypeList", {}).get("pubType", [])
    if isinstance(publication_types, str):
        publication_types = [publication_types]
    source_id = f"{item.get('source', '')}:{item.get('id', '')}"
    return classify_local(
        {
            "source": "europepmc",
            "source_record_id": source_id,
            "title": clean_text(item.get("title")),
            "abstract": clean_text(item.get("abstractText")),
            "year": str(item.get("pubYear") or item.get("firstPublicationDate", "")[:4]),
            "publication_date": clean_text(item.get("firstPublicationDate")),
            "doi": normalize_doi(item.get("doi")),
            "pmid": clean_text(item.get("pmid")),
            "pmcid": clean_text(item.get("pmcid")),
            "authors": clean_text(item.get("authorString")),
            "venue": clean_text(item.get("journalTitle")),
            "document_type": "; ".join(map(clean_text, publication_types)),
            "language": clean_text(item.get("language")),
            "url": f"https://europepmc.org/article/{source_id.replace(':', '/')}",
            "is_preprint": item.get("source") == "PPR",
            "raw_page": raw_page,
        }
    )


def collect_europepmc(
    raw_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    query = read_query("europepmc")
    cursor = "*"
    records = []
    expected = 0
    page_index = 0
    while True:
        page_index += 1
        page = request_json(
            EUROPEPMC_SEARCH,
            {
                "query": query,
                "format": "json",
                "pageSize": str(
                    min(1000, MAX_RECORDS_PER_SOURCE or 1000)
                ),
                "cursorMark": cursor,
                "resultType": "core",
            },
        )
        name = f"page_{page_index:04d}.json.gz"
        write_json_gzip(raw_dir / name, page)
        expected = int(page.get("hitCount", expected))
        items = page.get("resultList", {}).get("result", [])
        records.extend(parse_europepmc(item, name) for item in items)
        next_cursor = page.get("nextCursorMark")
        if (
            not next_cursor
            or next_cursor == cursor
            or len(records) >= record_limit(expected)
        ):
            break
        cursor = next_cursor
    return records[: record_limit(expected)], {"reported_count": expected}


def parse_scopus(item: dict[str, Any], raw_page: str) -> dict[str, Any]:
    authors = item.get("author", [])
    author_names = []
    if isinstance(authors, list):
        author_names = [
            clean_text(
                author.get("authname")
                or author.get("preferred-name", {}).get("ce:indexed-name")
            )
            for author in authors
            if isinstance(author, dict)
        ]
    source_id = clean_text(item.get("dc:identifier") or item.get("eid"))
    date = clean_text(item.get("prism:coverDate"))
    subtype = clean_text(item.get("subtypeDescription") or item.get("subtype"))
    return classify_local(
        {
            "source": "scopus",
            "source_record_id": source_id,
            "title": clean_text(item.get("dc:title")),
            "abstract": clean_text(item.get("dc:description")),
            "year": date[:4],
            "publication_date": date,
            "doi": normalize_doi(item.get("prism:doi")),
            "pmid": clean_text(item.get("pubmed-id")),
            "pmcid": "",
            "authors": "; ".join(filter(None, author_names))
            or clean_text(item.get("dc:creator")),
            "venue": clean_text(item.get("prism:publicationName")),
            "document_type": subtype,
            "language": clean_text(item.get("language")),
            "url": next(
                (
                    link.get("@href", "")
                    for link in item.get("link", [])
                    if isinstance(link, dict) and link.get("@ref") == "scopus"
                ),
                "",
            ),
            "is_preprint": "preprint" in subtype.lower(),
            "raw_page": raw_page,
        }
    )


def collect_scopus(raw_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    query = read_query("scopus")
    headers = {
        "X-ELS-APIKey": get_credential("SCOPUS_API_KEY"),
        "Accept": "application/json",
    }
    records = []
    expected = 0
    start = 0
    page_index = 0
    view = "COMPLETE"
    while start == 0 or start < record_limit(expected):
        page_index += 1
        params = {
            "query": query,
            "start": str(start),
            "count": str(min(25, MAX_RECORDS_PER_SOURCE or 25)),
            "view": view,
            "sort": "citedby-count",
        }
        try:
            page = request_json(SCOPUS_SEARCH, params, headers=headers)
        except HttpError as error:
            if start != 0 or error.status not in {401, 403} or view != "COMPLETE":
                raise
            view = "STANDARD"
            params["view"] = view
            page = request_json(SCOPUS_SEARCH, params, headers=headers)
        name = f"page_{page_index:04d}.json.gz"
        write_json_gzip(raw_dir / name, page)
        search_results = page.get("search-results", {})
        expected = int(search_results.get("opensearch:totalResults", 0))
        items = search_results.get("entry", [])
        records.extend(parse_scopus(item, name) for item in items)
        if not items:
            break
        start += len(items)
        time.sleep(0.15)
    return records[: record_limit(expected)], {
        "reported_count": expected,
        "view": view,
        "abstract_entitlement": view == "COMPLETE",
    }


def parse_semantic_scholar(
    item: dict[str, Any], raw_page: str
) -> dict[str, Any]:
    external_ids = item.get("externalIds") or {}
    date = clean_text(item.get("publicationDate"))
    publication_types = item.get("publicationTypes") or []
    return classify_local(
        {
            "source": "semantic_scholar",
            "source_record_id": clean_text(item.get("paperId")),
            "title": clean_text(item.get("title")),
            "abstract": clean_text(item.get("abstract")),
            "year": str(item.get("year") or date[:4]),
            "publication_date": date,
            "doi": normalize_doi(external_ids.get("DOI")),
            "pmid": clean_text(external_ids.get("PubMed")),
            "pmcid": clean_text(external_ids.get("PubMedCentral")),
            "authors": "; ".join(
                clean_text(author.get("name"))
                for author in item.get("authors", [])
                if isinstance(author, dict)
            ),
            "venue": clean_text(item.get("venue")),
            "document_type": "; ".join(map(clean_text, publication_types)),
            "language": "",
            "url": clean_text(item.get("url")),
            "is_preprint": "preprint" in " ".join(publication_types).lower(),
            "raw_page": raw_page,
        }
    )


def collect_semantic_scholar(
    raw_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    query = read_query("semantic_scholar")
    headers = {"x-api-key": get_credential("SEMANTIC_SCHOLAR_API_KEY")}
    token = ""
    records = []
    expected = 0
    page_index = 0
    while True:
        page_index += 1
        params = {
            "query": query,
            "year": "1800-2026",
            "limit": str(min(1000, MAX_RECORDS_PER_SOURCE or 1000)),
            "sort": "citationCount:desc",
            "fields": (
                "title,abstract,authors,year,venue,externalIds,publicationTypes,"
                "publicationDate,url,openAccessPdf"
            ),
        }
        if token:
            params["token"] = token
        page = request_json(
            SEMANTIC_SCHOLAR_BULK,
            params,
            headers=headers,
        )
        name = f"page_{page_index:04d}.json.gz"
        write_json_gzip(raw_dir / name, page)
        expected = int(page.get("total", expected))
        items = page.get("data", [])
        records.extend(parse_semantic_scholar(item, name) for item in items)
        token = clean_text(page.get("token"))
        if not token or not items or len(records) >= record_limit(expected):
            break
        time.sleep(1.1)
    return records[: record_limit(expected)], {"reported_count": expected}


def parse_springer(item: dict[str, Any], raw_page: str) -> dict[str, Any]:
    creators = item.get("creators") or []
    if isinstance(creators, dict):
        creators = [creators]
    genre = item.get("genre") or []
    if isinstance(genre, str):
        genre = [genre]
    date = clean_text(item.get("publicationDate") or item.get("onlineDate"))
    source_id = clean_text(item.get("identifier") or item.get("doi"))
    urls = item.get("url") or []
    if isinstance(urls, dict):
        urls = [urls]
    return classify_local(
        {
            "source": "springernature",
            "source_record_id": source_id,
            "title": clean_text(item.get("title")),
            "abstract": clean_text(item.get("abstract")),
            "year": date[:4],
            "publication_date": date,
            "doi": normalize_doi(item.get("doi") or source_id),
            "pmid": "",
            "pmcid": "",
            "authors": "; ".join(
                clean_text(creator.get("creator") or creator.get("name"))
                for creator in creators
                if isinstance(creator, dict)
            ),
            "venue": clean_text(item.get("publicationName")),
            "document_type": "; ".join(map(clean_text, genre)),
            "language": clean_text(item.get("language")),
            "url": next(
                (
                    clean_text(url.get("value"))
                    for url in urls
                    if isinstance(url, dict) and url.get("value")
                ),
                "",
            ),
            "is_preprint": "preprint" in " ".join(genre).lower(),
            "raw_page": raw_page,
        }
    )


def collect_springernature(
    raw_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    query = read_query("springernature")
    api_key = get_credential("SPRINGERNATURE_META_API_KEY")
    start = 1
    expected = 0
    records = []
    page_index = 0
    while start == 1 or start <= record_limit(expected):
        page_index += 1
        page = request_json(
            SPRINGER_META,
            {
                "q": query,
                "s": str(start),
                "p": str(min(25, MAX_RECORDS_PER_SOURCE or 25)),
                "api_key": api_key,
            },
        )
        name = f"page_{page_index:04d}.json.gz"
        write_json_gzip(raw_dir / name, page)
        result = page.get("result") or []
        if isinstance(result, dict):
            result = [result]
        expected = int(result[0].get("total", 0)) if result else 0
        items = page.get("records", [])
        records.extend(parse_springer(item, name) for item in items)
        if not items:
            break
        start += len(items)
        time.sleep(0.12)
    return records[: record_limit(expected)], {"reported_count": expected}


def reconstruct_openalex_abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words = [
        (position, word)
        for word, positions in index.items()
        for position in positions
    ]
    return clean_text(" ".join(word for _, word in sorted(words)))


def parse_openalex(item: dict[str, Any], raw_page: str) -> dict[str, Any]:
    location = item.get("primary_location") or {}
    source = location.get("source") or {}
    authors = [
        clean_text((authorship.get("author") or {}).get("display_name"))
        for authorship in item.get("authorships", [])
        if isinstance(authorship, dict)
    ]
    date = clean_text(item.get("publication_date"))
    work_type = clean_text(item.get("type"))
    return classify_local(
        {
            "source": "openalex",
            "source_record_id": clean_text(item.get("id")),
            "title": clean_text(item.get("title") or item.get("display_name")),
            "abstract": reconstruct_openalex_abstract(
                item.get("abstract_inverted_index")
            ),
            "year": str(item.get("publication_year") or date[:4]),
            "publication_date": date,
            "doi": normalize_doi(item.get("doi")),
            "pmid": "",
            "pmcid": "",
            "authors": "; ".join(filter(None, authors)),
            "venue": clean_text(source.get("display_name")),
            "document_type": work_type,
            "language": clean_text(item.get("language")),
            "url": clean_text(item.get("id")),
            "is_preprint": work_type == "preprint",
            "raw_page": raw_page,
        }
    )


def collect_openalex(raw_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    api_key = get_credential("OPENALEX_API_KEY")
    query_paths = read_query_paths("openalex")
    branch_counts: dict[str, int] = {}
    branch_retrieved_counts: dict[str, int] = {}
    records_by_id: dict[str, dict[str, Any]] = {}
    branch_hits = 0

    for branch, query_path in query_paths.items():
        query_filter = query_path.read_text(encoding="utf-8").strip()
        cursor = "*"
        branch_records: list[dict[str, Any]] = []
        expected = 0
        page_index = 0

        if MAX_RECORDS_PER_SOURCE is not None and SAMPLE_SEED is not None:
            count_page = request_json(
                OPENALEX_WORKS,
                {
                    "filter": query_filter,
                    "per_page": "1",
                    "select": "id",
                    "api_key": api_key,
                },
            )
            write_json_gzip(raw_dir / branch / "count.json.gz", count_page)
            expected = int(count_page.get("meta", {}).get("count", 0))
            sample_size = min(MAX_RECORDS_PER_SOURCE, expected)
            if sample_size:
                page = request_json(
                    OPENALEX_WORKS,
                    {
                        "filter": query_filter,
                        "sample": str(sample_size),
                        "seed": str(SAMPLE_SEED),
                        "per_page": str(sample_size),
                        "select": (
                            "id,doi,title,display_name,publication_year,"
                            "publication_date,type,language,authorships,"
                            "primary_location,abstract_inverted_index"
                        ),
                        "api_key": api_key,
                    },
                )
                name = f"{branch}/sample_seed_{SAMPLE_SEED}.json.gz"
                write_json_gzip(raw_dir / name, page)
                for item in page.get("results", []):
                    record = parse_openalex(item, name)
                    record["query_branches"] = branch
                    branch_records.append(record)
            cursor = ""

        while cursor:
            page_index += 1
            page = request_json(
                OPENALEX_WORKS,
                {
                    "filter": query_filter,
                    "per_page": str(min(100, MAX_RECORDS_PER_SOURCE or 100)),
                    "cursor": cursor,
                    "sort": "cited_by_count:desc",
                    "select": (
                        "id,doi,title,display_name,publication_year,"
                        "publication_date,type,language,authorships,"
                        "primary_location,abstract_inverted_index"
                    ),
                    "api_key": api_key,
                },
            )
            name = f"{branch}/page_{page_index:04d}.json.gz"
            write_json_gzip(raw_dir / name, page)
            expected = int(page.get("meta", {}).get("count", expected))
            items = page.get("results", [])
            for item in items:
                record = parse_openalex(item, name)
                record["query_branches"] = branch
                branch_records.append(record)
            cursor = clean_text(page.get("meta", {}).get("next_cursor"))
            if not items or len(branch_records) >= record_limit(expected):
                break

        branch_records = branch_records[: record_limit(expected)]
        branch_counts[branch] = expected
        branch_retrieved_counts[branch] = len(branch_records)
        branch_hits += len(branch_records)
        for record in branch_records:
            key = record["source_record_id"] or record["doi"]
            if key not in records_by_id:
                records_by_id[key] = record
                continue
            branches = set(records_by_id[key]["query_branches"].split(";"))
            branches.add(branch)
            records_by_id[key]["query_branches"] = ";".join(sorted(branches))

    records = sorted(
        records_by_id.values(),
        key=lambda row: (row["publication_date"], row["source_record_id"]),
    )
    return records, {
        "reported_count": sum(branch_counts.values()),
        "reported_count_semantics": "sum_of_branch_counts_before_deduplication",
        "branch_counts": branch_counts,
        "branch_retrieved_counts": branch_retrieved_counts,
        "retrieved_branch_hits_before_deduplication": branch_hits,
        "duplicate_branch_hits_removed": branch_hits - len(records),
        "unique_retrieved_count": len(records),
        "sampling_seed": SAMPLE_SEED,
    }


COLLECTORS: dict[
    str, Callable[[Path], tuple[list[dict[str, Any]], dict[str, Any]]]
] = {
    "pubmed": collect_pubmed,
    "europepmc": collect_europepmc,
    "scopus": collect_scopus,
    "semantic_scholar": collect_semantic_scholar,
    "springernature": collect_springernature,
    "openalex": collect_openalex,
}


def write_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=FIELDS,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(records)


def run_source(
    source: str, output: Path, canonical_doi: str
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    started = datetime.now(UTC)
    query_paths = read_query_paths(source)
    raw_dir = output / "raw" / source
    records, details = COLLECTORS[source](raw_dir)
    normalized_path = output / "normalized" / f"{source}.csv"
    write_records(normalized_path, records)
    canonical = [
        record for record in records if normalize_doi(record.get("doi")) == canonical_doi
    ]
    raw_responses = [
        {
            "path": str(path.relative_to(output)),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(raw_dir.rglob("*"))
        if path.is_file()
    ]
    manifest = {
        "source": source,
        "started_at": started.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "query_files": {
            branch: str(path.relative_to(ROOT))
            for branch, path in query_paths.items()
        },
        "query_sha256": {
            branch: sha256_file(path) for branch, path in query_paths.items()
        },
        "reported_count": details.get("reported_count"),
        "source_details": {
            key: value
            for key, value in details.items()
            if key != "reported_count"
        },
        "retrieved_count": len(records),
        "local_three_block_count": sum(
            bool(record["local_three_block_match"]) for record in records
        ),
        "local_explicit_multiomics_count": sum(
            bool(record["local_explicit_multiomics_match"]) for record in records
        ),
        "local_layer_pair_count": sum(
            bool(record["local_layer_pair_match"]) for record in records
        ),
        "canonical_positive_doi": canonical_doi,
        "canonical_positive_found": bool(canonical),
        "canonical_positive_local_three_block_match": any(
            bool(record["local_three_block_match"]) for record in canonical
        ),
        "normalized_file": str(normalized_path.relative_to(output)),
        "normalized_sha256": sha256_file(normalized_path),
        "raw_responses": raw_responses,
    }
    (output / "manifests").mkdir(parents=True, exist_ok=True)
    (output / "manifests" / f"{source}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return source, records, manifest


def read_query_path(source: str) -> Path:
    return QUERY_FILES.get(source, PROTOCOL / "queries" / f"{source}.txt")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run and freeze database-native academic searches"
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--search-config",
        type=Path,
        default=SEARCH_CONFIG,
        help="versioned search configuration; defaults to the legacy active config",
    )
    parser.add_argument(
        "--sources",
        help=(
            "comma-separated source subset; by default, run automated sources "
            "marked active_for_identification in the search config"
        ),
    )
    parser.add_argument("--parallel", type=int, default=4)
    parser.add_argument(
        "--max-records-per-source",
        type=int,
        help="pilot-only cap; omit for a complete final retrieval",
    )
    parser.add_argument(
        "--sample-seed",
        type=int,
        help=(
            "fixed OpenAlex random-sample seed; requires "
            "--max-records-per-source"
        ),
    )
    args = parser.parse_args()

    global MAX_RECORDS_PER_SOURCE, SAMPLE_SEED
    if args.max_records_per_source is not None and args.max_records_per_source < 1:
        raise SystemExit("--max-records-per-source must be positive")
    if args.sample_seed is not None and args.max_records_per_source is None:
        raise SystemExit("--sample-seed requires --max-records-per-source")
    MAX_RECORDS_PER_SOURCE = args.max_records_per_source
    SAMPLE_SEED = args.sample_seed

    search_config_path = args.search_config.resolve()
    config = json.loads(search_config_path.read_text(encoding="utf-8"))
    configured_databases = {item["id"]: item for item in config["databases"]}
    QUERY_FILES.clear()
    QUERY_FILES.update(
        {
            source: (PROTOCOL / item["query_file"]).resolve()
            for source, item in configured_databases.items()
            if item.get("query_file")
        }
    )
    QUERY_BRANCH_FILES.clear()
    QUERY_BRANCH_FILES.update(
        {
            source: {
                branch: (PROTOCOL / path).resolve()
                for branch, path in item["query_files"].items()
            }
            for source, item in configured_databases.items()
            if item.get("query_files")
        }
    )
    canonical_doi = normalize_doi(config["canonical_positive_doi"])
    if args.sources:
        sources = [
            source.strip() for source in args.sources.split(",") if source.strip()
        ]
    else:
        sources = [
            source
            for source, item in configured_databases.items()
            if item.get("mode") == "automated"
            and item.get("active_for_identification", True)
        ]
    unknown = sorted(set(sources) - set(COLLECTORS))
    if unknown:
        raise SystemExit(f"Unknown sources: {', '.join(unknown)}")

    args.output.mkdir(parents=True, exist_ok=True)
    all_records: list[dict[str, Any]] = []
    manifests: dict[str, dict[str, Any]] = {}
    failures: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as executor:
        futures = {
            executor.submit(run_source, source, args.output, canonical_doi): source
            for source in sources
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                _, records, manifest = future.result()
                all_records.extend(records)
                manifests[source] = manifest
                print(
                    f"{source}: reported={manifest['reported_count']} "
                    f"retrieved={manifest['retrieved_count']} "
                    f"local_three_block={manifest['local_three_block_count']} "
                    f"canonical={manifest['canonical_positive_found']}",
                    flush=True,
                )
            except Exception as error:
                failures[source] = f"{type(error).__name__}: {error}"
                print(f"{source}: FAILED {failures[source]}", flush=True)

    all_records.sort(
        key=lambda row: (
            row["source"],
            row["publication_date"],
            row["source_record_id"],
        )
    )
    combined = args.output / "normalized" / "all_sources.csv"
    write_records(combined, all_records)
    run_manifest = {
        "manifest_version": "1.0.0",
        "protocol_version": config["protocol_version"],
        "created_at": datetime.now(UTC).isoformat(),
        "git_revision": git_revision(),
        "search_config_path": str(search_config_path.relative_to(ROOT)),
        "search_config_sha256": hashlib.sha256(search_config_path.read_bytes()).hexdigest(),
        "sources_requested": sources,
        "sources_completed": sorted(manifests),
        "failures": failures,
        "pilot_max_records_per_source": MAX_RECORDS_PER_SOURCE,
        "openalex_pilot_limit_semantics": (
            "per_query_branch" if "openalex" in QUERY_BRANCH_FILES else None
        ),
        "openalex_sample_seed": SAMPLE_SEED,
        "complete_retrieval": MAX_RECORDS_PER_SOURCE is None,
        "source_manifests": manifests,
        "total_source_records": len(all_records),
        "total_local_three_block_records": sum(
            bool(record["local_three_block_match"]) for record in all_records
        ),
        "combined_file": str(combined.relative_to(args.output)),
        "google_scholar_status": "manual_pending",
    }
    (args.output / "search_run_manifest.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if failures:
        raise SystemExit(
            "One or more sources failed: "
            + ", ".join(f"{source}={message}" for source, message in failures.items())
        )


if __name__ == "__main__":
    main()
