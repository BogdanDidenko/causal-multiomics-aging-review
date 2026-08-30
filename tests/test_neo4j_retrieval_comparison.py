from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "protocol/neo4j/retrieval_comparison_v0.1.0.json"


def load_comparison():
    path = REPO / "scripts/neo4j/compare_retrieval.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_comparison_protocol_freezes_five_information_needs() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    needs = config["information_needs"]

    assert config["status"] == "frozen_exploratory_protocol_before_execution"
    assert config["unit_of_comparison"] == "unique_report_doi"
    assert len(needs) == 5
    assert len({item["id"] for item in needs}) == 5
    assert all(item["graph_design_families"] for item in needs)
    assert all(item["lexical_anchors"] for item in needs)
    assert config["interpretive_limits"]["precision_or_recall_claims_allowed"] is False
    assert config["interpretive_limits"]["retrieval_absence_can_exclude"] is False


def test_comparison_does_not_restore_directional_wording_anchors() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    serialized = json.dumps(config["information_needs"]).lower()

    for rejected_anchor in ("affects", "regulates", "drives", "influences"):
        assert rejected_anchor not in serialized


def test_docling_lexical_baseline_excludes_reference_sections() -> None:
    comparison = load_comparison()

    assert comparison.is_reference_section(
        {"heading": "Paper title > References", "text": "irrelevant"}
    )
    assert comparison.is_reference_section(
        {"heading": "Paper title > Bibliography", "text": "irrelevant"}
    )
    assert not comparison.is_reference_section(
        {"heading": "Paper title > Results", "text": "relevant"}
    )


def test_frozen_regexes_match_spelling_variants() -> None:
    comparison = load_comparison()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    need = next(item for item in config["information_needs"] if item["id"] == "genetic_instrument")
    anchors = comparison.compile_anchors(need)

    count_us, matched_us = comparison.regex_hits("Mendelian randomization study", anchors)
    count_uk, matched_uk = comparison.regex_hits("Mendelian randomisation study", anchors)

    assert count_us == 1
    assert count_uk == 1
    assert matched_us == {"mendelian_randomization"}
    assert matched_uk == {"mendelian_randomization"}


def test_saved_result_preserves_profile_equivalence_when_present() -> None:
    result = REPO / "analysis/neo4j/retrieval_comparison_v0.1.0/summary.json"
    if not result.exists():
        return
    summary = json.loads(result.read_text(encoding="utf-8"))

    assert summary["corpus_reports"] == 101
    assert summary["historical_reports"] == 30
    assert all(item["exact_report_set_equivalence"] for item in summary["profile_equivalence"])
