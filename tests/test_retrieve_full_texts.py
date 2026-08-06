import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "retrieve_full_texts.py"
SPEC = importlib.util.spec_from_file_location("retrieve_full_texts", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

PdfLinkParser = MODULE.PdfLinkParser
canonical_publisher_pdf_locations = MODULE.canonical_publisher_pdf_locations
crossref_pdf_locations = MODULE.crossref_pdf_locations
openalex_oa_landing_urls = MODULE.openalex_oa_landing_urls
openaire_repository_locations = MODULE.openaire_repository_locations
public_copy_locations = MODULE.public_copy_locations
semantic_scholar_pdf_locations = MODULE.semantic_scholar_pdf_locations
pmc_fulltext_html_locations = MODULE.pmc_fulltext_html_locations
unpaywall_locations = MODULE.unpaywall_locations


def test_openalex_oa_landing_urls_excludes_non_oa_locations() -> None:
    metadata = {
        "best_oa_location": {
            "is_oa": True,
            "landing_page_url": "https://example.org/open",
        },
        "locations": [
            {
                "is_oa": False,
                "landing_page_url": "https://example.org/paywalled",
            },
            {
                "is_oa": True,
                "landing_page_url": "https://example.org/open",
            },
        ],
        "open_access": {"oa_url": "https://example.org/open"},
    }

    assert openalex_oa_landing_urls(metadata) == ["https://example.org/open"]


def test_pdf_link_parser_accepts_only_explicit_pdf_urls() -> None:
    parser = PdfLinkParser()
    parser.feed(
        """
        <meta name="citation_pdf_url" content="/article.pdf">
        <a href="/download" type="application/pdf">Download</a>
        <a href="/supplement.pdf">Supplement</a>
        <a href="/html">HTML</a>
        """
    )

    assert parser.urls == ["/article.pdf", "/download", "/supplement.pdf"]


def test_crossref_and_semantic_scholar_locations_require_a_real_pdf() -> None:
    crossref = {
        "link": [
            {"URL": "https://publisher.example/article.pdf", "content-type": "application/pdf"},
            {"URL": "https://publisher.example/article.html", "content-type": "text/html"},
        ]
    }
    semantic_scholar = {
        "openAccessPdf": {
            "url": "https://repository.example/manuscript.pdf",
            "status": "GREEN",
            "license": "CC BY",
        }
    }

    assert [location["url"] for location in crossref_pdf_locations(crossref)] == [
        "https://publisher.example/article.pdf"
    ]
    assert [location["url"] for location in semantic_scholar_pdf_locations(semantic_scholar)] == [
        "https://repository.example/manuscript.pdf"
    ]
    assert semantic_scholar_pdf_locations(
        {"openAccessPdf": {"url": "https://doi.org/10.1/example", "status": "GOLD"}}
    ) == []


def test_canonical_publisher_routes_are_limited_to_known_patterns() -> None:
    assert canonical_publisher_pdf_locations("10.1038/s43587-026-01100-7")[0]["url"] == (
        "https://www.nature.com/articles/s43587-026-01100-7.pdf"
    )
    assert canonical_publisher_pdf_locations("10.1186/s13578-026-01594-z")[0]["url"] == (
        "https://link.springer.com/content/pdf/10.1186/s13578-026-01594-z.pdf"
    )
    assert canonical_publisher_pdf_locations("10.1016/j.example.2026.1") == []


def test_openaire_repository_locations_excludes_closed_and_doi_instances() -> None:
    metadata = {
        "children": {
            "instance": [
                {
                    "accessright": {"@classid": "OPEN"},
                    "hostedby": {"@name": "Institutional Repository"},
                    "webresource": {"url": {"$": "https://repository.example/item/1"}},
                },
                {
                    "accessright": {"@classid": "CLOSED"},
                    "url": {"$": "https://repository.example/item/2"},
                },
                {
                    "accessright": {"@classid": "OPEN"},
                    "url": {"$": "https://doi.org/10.1/example"},
                },
            ]
        }
    }

    assert [location["url"] for location in openaire_repository_locations(metadata)] == [
        "https://repository.example/item/1"
    ]


def test_public_copy_locations_match_normalized_doi_and_validate_urls(tmp_path: Path) -> None:
    copy_list = tmp_path / "public_copies.csv"
    copy_list.write_text(
        "doi,url,source,access_basis\n"
        "https://doi.org/10.1016/J.EXAMPLE.1,https://authors.example/paper.pdf,"
        "Author lab,Public copy\n"
        "10.1016/j.other,https://authors.example/other.pdf,Other lab,Public copy\n",
        encoding="utf-8",
    )

    assert public_copy_locations(copy_list, "10.1016/j.example.1") == [
        {
            "url": "https://authors.example/paper.pdf",
            "source": "Author lab",
            "license": "",
            "version": "Public copy",
        }
    ]


def test_unpaywall_locations_preserve_direct_pdfs_and_repository_pages() -> None:
    metadata = {
        "best_oa_location": {
            "host_type": "repository",
            "license": "cc-by",
            "version": "acceptedVersion",
            "url_for_pdf": "https://repository.example/paper.pdf",
            "url": "https://repository.example/item/1",
        },
        "oa_locations": [
            {
                "host_type": "publisher",
                "url": "https://publisher.example/article",
            },
            {"url_for_pdf": "ftp://invalid.example/paper.pdf"},
        ],
    }

    assert unpaywall_locations(metadata) == [
        {
            "url": "https://repository.example/paper.pdf",
            "kind": "pdf",
            "source": "Unpaywall repository location",
            "license": "cc-by",
            "version": "acceptedVersion",
        },
        {
            "url": "https://repository.example/item/1",
            "kind": "landing",
            "source": "Unpaywall repository location",
            "license": "cc-by",
            "version": "acceptedVersion",
        },
        {
            "url": "https://publisher.example/article",
            "kind": "landing",
            "source": "Unpaywall publisher location",
            "license": "",
            "version": "",
        },
    ]


def test_pmc_fulltext_html_locations_exclude_pdf_only_and_non_pmc_locations() -> None:
    metadata = {
        "oa_locations": [
            {
                "host_type": "repository",
                "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/",
                "version": "submittedVersion",
            },
            {
                "host_type": "repository",
                "url_for_pdf": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf/a.pdf",
            },
            {
                "host_type": "repository",
                "url": "https://repository.example/item/123",
            },
        ]
    }

    assert pmc_fulltext_html_locations(metadata) == [
        {
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/",
            "kind": "landing",
            "source": "PubMed Central public author manuscript HTML",
            "license": "",
            "version": "submittedVersion",
        }
    ]


def test_pmc_fulltext_html_locations_derives_article_page_from_pdf_url() -> None:
    metadata = {
        "oa_locations": [
            {
                "host_type": "repository",
                "url_for_pdf": (
                    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7654321/pdf/manuscript.pdf"
                ),
                "version": "submittedVersion",
            }
        ]
    }

    assert pmc_fulltext_html_locations(metadata)[0]["url"] == (
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC7654321/"
    )
