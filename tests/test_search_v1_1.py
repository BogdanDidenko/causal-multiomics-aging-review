from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "protocol"
CONFIG = PROTOCOL / "search_config_v1.1.1.json"


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def test_springer_is_excluded_from_identification() -> None:
    databases = {item["id"]: item for item in load_config()["databases"]}
    springer = databases["springernature"]
    assert springer["mode"] == "excluded"
    assert springer["active_for_identification"] is False
    assert springer["role"] == "excluded_from_identification"


def test_default_automated_sources_do_not_include_springer() -> None:
    databases = load_config()["databases"]
    active = {
        item["id"]
        for item in databases
        if item["mode"] == "automated"
        and item.get("active_for_identification", True)
    }
    assert active == {
        "pubmed",
        "scopus",
        "europepmc",
        "semantic_scholar",
        "openalex",
    }


def test_openalex_uses_six_scoped_query_branches() -> None:
    databases = {item["id"]: item for item in load_config()["databases"]}
    query_files = databases["openalex"]["query_files"]
    assert set(query_files) == {
        "explicit_multiomics",
        "genomics_plus_other",
        "epigenomics_plus_downstream",
        "transcriptomics_plus_downstream",
        "proteomics_plus_downstream",
        "metabolomics_plus_microbiomics",
    }
    for path_text in query_files.values():
        query = (PROTOCOL / path_text).read_text(encoding="utf-8")
        assert "has_abstract:true" in query
        assert "to_publication_date:2026-08-02" in query
        assert "is_retracted:false" in query
        assert "type:article|preprint" in query
        assert any(term in query for term in ("aging", "ageing", "longevity"))
        assert "Mendelian randomization" in query
        assert "causal discovery" in query


def test_pairwise_openalex_queries_require_two_layer_filters() -> None:
    databases = {item["id"]: item for item in load_config()["databases"]}
    query_files = databases["openalex"]["query_files"]
    for branch, path_text in query_files.items():
        if branch == "explicit_multiomics":
            continue
        query = (PROTOCOL / path_text).read_text(encoding="utf-8")
        layer_filters = re.findall(r"title_and_abstract\.search:[^,]+", query)
        assert len(layer_filters) >= 3
        assert "title_and_abstract.search.exact:aging|" in query


def test_openalex_does_not_use_bare_generic_causal_anchors() -> None:
    databases = {item["id"]: item for item in load_config()["databases"]}
    for path_text in databases["openalex"]["query_files"].values():
        query = (PROTOCOL / path_text).read_text(encoding="utf-8")
        causal_filter = query.split("title_and_abstract.search:")[-1].split(",")[0]
        values = {value.strip('"') for value in causal_filter.split("|")}
        assert not values & {
            "causal",
            "causality",
            "intervention",
            "mediation",
            "perturbation",
        }


def test_openalex_uses_exact_aging_search() -> None:
    databases = {item["id"]: item for item in load_config()["databases"]}
    for path_text in databases["openalex"]["query_files"].values():
        query = (PROTOCOL / path_text).read_text(encoding="utf-8")
        assert "title_and_abstract.search.exact:aging|" in query
        assert "title_and_abstract.search:aging|" not in query
