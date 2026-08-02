import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis/v1_methodology"
RUN_ROOT = ROOT / "data/screening/v1_canonical_ai_preliminary"
FINAL_CSV = ANALYSIS / "canonical_candidate_final_ai_annotation_2026-08-02.csv"
FINAL_SUMMARY = (
    ANALYSIS / "canonical_candidate_final_ai_annotation_2026-08-02.summary.json"
)
PRELIMINARY_SUMMARY = (
    ANALYSIS / "canonical_candidate_ai_annotation_2026-08-02.summary.json"
)
ELIGIBILITY_ADJUDICATION = (
    ANALYSIS / "canonical_candidate_assistant_adjudication_2026-08-02.csv"
)
DESIGN_ADJUDICATION = (
    ANALYSIS / "canonical_candidate_design_family_adjudication_2026-08-02.csv"
)
SOURCE_RECORDS = RUN_ROOT / "study_deduplicated/input.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_final_assistant_annotation_has_complete_non_gold_coverage() -> None:
    rows = read_csv(FINAL_CSV)
    assert len(rows) == 120
    assert len({row["record_id"] for row in rows}) == 120
    assert Counter(row["assistant_final_status"] for row in rows) == {
        "include": 95,
        "exclude": 23,
        "seek_full_text": 2,
    }
    assert {row["human_expert_status"] for row in rows} == {"pending"}
    included = [row for row in rows if row["assistant_final_status"] == "include"]
    assert all(
        row["assistant_primary_design_family"] not in {"", "unclear", "not_assessed"}
        for row in included
    )


def test_assistant_adjudication_quotes_are_verbatim() -> None:
    sources = {row["record_id"]: row for row in read_csv(SOURCE_RECORDS)}
    eligibility = read_csv(ELIGIBILITY_ADJUDICATION)
    design = read_csv(DESIGN_ADJUDICATION)
    assert len(eligibility) == 34
    assert len(design) == 24
    for row in [*eligibility, *design]:
        source = sources[row["record_id"]]
        assert row["evidence_quote"] in source["title"] + source["abstract"]


def test_annotation_summary_preserves_stability_failure_and_hashes() -> None:
    preliminary = json.loads(PRELIMINARY_SUMMARY.read_text(encoding="utf-8"))
    final = json.loads(FINAL_SUMMARY.read_text(encoding="utf-8"))
    assert preliminary["all_assessed_fields_5_of_5_count"] == 86
    assert preliminary["all_assessed_fields_5_of_5_rate"] == 86 / 120
    assert preliminary["provider_attempts"] == {
        "attempt_ok": 1097,
        "attempt_error": 90,
        "retry_attempts": 82,
    }
    assert final["gold_standard"] is False
    assert final["human_expert_status"] == "pending"
    assert final["output"]["sha256"] == sha256(FINAL_CSV)
    assert final["included_primary_design_family_counts"] == {
        "direct_perturbation": 27,
        "genetic_instrument": 57,
        "nonrandomized_intervention": 8,
        "randomized_intervention": 2,
        "sem": 1,
    }


def test_all_frozen_raw_run_artifacts_match_preliminary_manifest() -> None:
    summary = json.loads(PRELIMINARY_SUMMARY.read_text(encoding="utf-8"))
    artifacts = summary["raw_run_artifacts"]
    assert len(artifacts) == 42
    for artifact in artifacts:
        path = ROOT / artifact["path"]
        assert path.is_file()
        assert path.stat().st_size == artifact["bytes"]
        assert sha256(path) == artifact["sha256"]
