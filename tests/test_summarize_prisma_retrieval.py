from pathlib import Path

from scripts.summarize_prisma_retrieval import build_summary


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/full_text/v1.1.2_priority_1_nonpreprint_119"


def test_priority_retrieval_prisma_flow_balances() -> None:
    summary = build_summary(DATASET)
    flow = summary["flow"]

    assert flow["priority_queue_records"] == 135
    assert flow["preprints_outside_this_retrieval_batch"] == 16
    assert flow["nonpreprint_candidate_records_audited"] == 119
    assert flow["records_excluded_before_report_retrieval"] == 6
    assert flow["reports_sought_for_retrieval"] == 113
    assert flow["reports_not_retrieved"] == 15
    assert flow["reports_retrieved_and_available_for_assessment"] == 98
    assert flow["reports_assessed_for_eligibility"] is None
    assert (
        flow["reports_sought_for_retrieval"]
        == flow["reports_not_retrieved"]
        + flow["reports_retrieved_and_available_for_assessment"]
    )


def test_priority_retrieval_has_no_unclassified_residuals() -> None:
    summary = build_summary(DATASET)

    assert summary["verification"]["unresolved_records_classified"] == 21
    assert summary["verification"]["unclassified_unresolved_records"] == 0
    assert summary["retrieved_format_counts"] == {
        "pdf": 86,
        "html": 11,
        "xml": 1,
    }
    assert summary["scope"]["is_final_review_prisma_denominator"] is False
