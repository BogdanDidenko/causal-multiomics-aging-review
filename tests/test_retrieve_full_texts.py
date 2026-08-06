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
openalex_oa_landing_urls = MODULE.openalex_oa_landing_urls


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
