import json
from pathlib import Path

import pytest

from causal_multiomics_aging_review.screening import run_stage_screening
from causal_multiomics_aging_review.v1 import (
    derive_title_result,
    package_full_text_sections,
    validate_causal_answer_consistency,
    validate_full_text_evidence_spans,
    validate_scope_answer_consistency,
    validate_title_evidence_spans,
)

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "protocol/screening/configs/prompt_suite_v1.0.0.json"


class QueueProvider:
    model = "gpt-5.6-terra"
    url = "codex://cli"
    max_tokens = 16000
    response_format = "json_schema"

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def complete_json(self, prompt, schema=None, schema_name="screening_response"):
        self.calls.append(schema_name)
        answer = self.answers[schema_name].pop(0)
        return answer, {"answer": answer}


def scope_answer(**overrides):
    answer = {
        "report_type": "empirical_primary",
        "bio_health_scope": "yes",
        "aging_process_relevance": "yes",
        "multiomics_evidence": "two_or_more_layers",
        "layer_candidates": ["genomics", "transcriptomics"],
        "current_report_layer_use": "yes",
    }
    answer.update(overrides)
    return answer


def causal_answer(**overrides):
    answer = {
        "current_report_application": "yes",
        "causal_basis": "named_causal_effect_design",
        "design_families": ["genetic_instrument"],
        "causal_information_sufficiency": "sufficient",
    }
    answer.update(overrides)
    return answer


def repeated(answer):
    return [dict(answer) for _ in range(5)]


def test_title_evidence_must_be_verbatim() -> None:
    record = {"title": "Aging study", "abstract": "We integrated two omics layers."}
    validate_title_evidence_spans(
        {
            "evidence_spans": [
                {
                    "source": "abstract",
                    "quote": "integrated two omics layers",
                }
            ]
        },
        record,
    )
    with pytest.raises(ValueError, match="exact substring"):
        validate_title_evidence_spans(
            {"evidence_spans": [{"source": "abstract", "quote": "two layers"}]},
            record,
        )


def test_scope_consistency_requires_two_named_layers() -> None:
    with pytest.raises(ValueError, match="at least two"):
        validate_scope_answer_consistency(
            scope_answer(layer_candidates=["genomics"])
        )


def test_causal_consistency_rejects_wording_as_applied_method() -> None:
    with pytest.raises(ValueError, match="requires no"):
        validate_causal_answer_consistency(
            causal_answer(
                causal_basis="causal_wording_only",
                current_report_application="yes",
                design_families=[],
            )
        )


def test_causal_consistency_allows_unspecified_current_analysis() -> None:
    validate_causal_answer_consistency(
        causal_answer(
            causal_basis="causal_analysis_method_unspecified",
            design_families=[],
        )
    )


def test_five_identical_scope_failures_exclude() -> None:
    result = derive_title_result(
        repeated(scope_answer(aging_process_relevance="no")), None
    )
    assert result["final_decision"] == "exclude"
    assert result["final_exclusion_code"] == "EC3"


def test_nonunanimous_scope_failure_seeks_full_text() -> None:
    runs = repeated(scope_answer(aging_process_relevance="no"))
    runs[-1]["aging_process_relevance"] = "unclear"
    result = derive_title_result(runs, None)
    assert result["final_decision"] == "seek_full_text"
    assert result["final_exclusion_code"] == "none"


def test_same_scope_path_with_downstream_field_drift_seeks_full_text() -> None:
    runs = repeated(scope_answer(aging_process_relevance="no"))
    runs[-1]["multiomics_evidence"] = "unclear"
    result = derive_title_result(runs, None)
    assert result["final_decision"] == "seek_full_text"


@pytest.mark.parametrize(
    "basis",
    [
        "named_causal_effect_design",
        "formal_directed_hypothesis",
        "causal_analysis_method_unspecified",
    ],
)
def test_positive_causal_bases_seek_full_text(basis: str) -> None:
    result = derive_title_result(
        repeated(scope_answer()), repeated(causal_answer(causal_basis=basis))
    )
    assert result["final_decision"] == "seek_full_text"
    assert result["final_exclusion_code"] == "none"


def test_sufficient_causal_wording_only_excludes_only_when_unanimous() -> None:
    negative = causal_answer(
        causal_basis="causal_wording_only",
        current_report_application="no",
        design_families=[],
    )
    result = derive_title_result(repeated(scope_answer()), repeated(negative))
    assert result["final_decision"] == "exclude"
    assert result["final_exclusion_code"] == "EC5"

    mixed = repeated(negative)
    mixed[-1]["causal_information_sufficiency"] = "insufficient"
    result = derive_title_result(repeated(scope_answer()), mixed)
    assert result["final_decision"] == "seek_full_text"


def test_full_text_evidence_quote_must_match_its_section() -> None:
    sections = [
        {"section_id": "S1", "heading": "Methods", "text": "We used MR."},
        {"section_id": "S2", "heading": "Results", "text": "The effect was null."},
    ]
    validate_full_text_evidence_spans(
        {"evidence_spans": [{"section_id": "S1", "quote": "used MR"}]},
        sections,
    )
    with pytest.raises(ValueError, match="section S2"):
        validate_full_text_evidence_spans(
            {"evidence_spans": [{"section_id": "S2", "quote": "used MR"}]},
            sections,
        )


def test_deterministic_section_packaging_is_stable_and_bounded() -> None:
    sections = [
        {"section_id": "S1", "heading": "Introduction", "text": "x" * 50},
        {
            "section_id": "S2",
            "heading": "Mendelian randomization methods",
            "text": "causal " * 20,
        },
        {"section_id": "S3", "heading": "References", "text": "z" * 50},
    ]
    config = {
        "max_chars": 60,
        "max_section_chars": 40,
        "required_heading_terms": ["method"],
        "priority_text_terms": ["mendelian random", "causal"],
    }
    first = package_full_text_sections(sections, config)
    second = package_full_text_sections(sections, config)
    assert first == second
    selected, audit = first
    assert selected[0]["section_id"] == "S1"
    assert {item["section_id"] for item in selected} == {"S1", "S2"}
    assert audit["selected_chars"] == 60
    assert "S2" in audit["truncated_section_ids"]


def test_v1_suite_has_only_two_model_roles_per_stage() -> None:
    suite = json.loads(
        (ROOT / "protocol/screening/configs/prompt_suite_v1.0.0.json").read_text()
    )
    title = suite["stages"]["title_abstract"]
    full_text = suite["stages"]["full_text"]
    assert set(title["roles"]) == {"scope_reviewer", "causal_method_reviewer"}
    assert set(full_text["roles"]) == {
        "eligibility_reviewer",
        "causal_evidence_reviewer",
    }
    assert title["decision_repeats"] == 5
    assert full_text["decision_repeats"] == 5
    serialized = json.dumps(suite).lower()
    assert "directional_result_reviewer" not in serialized
    assert "section_selector" not in serialized
    assert "adjudicator" not in serialized


def test_v1_queries_have_both_omics_branches_without_directional_verbs() -> None:
    forbidden = {"affects", "regulates", "drives", "influences"}
    for path in sorted((ROOT / "protocol/queries/v1.0.0").glob("*.txt")):
        query = path.read_text().lower()
        assert "multi" in query and "omic" in query
        assert "genom" in query and "transcriptom" in query
        assert "aging" in query or "ageing" in query
        assert not any(term in query.split() for term in forbidden)


def test_v1_title_stage_runs_each_role_five_times(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    abstract = (
        "We integrated GWAS and transcriptomic eQTL data for biological aging "
        "using Mendelian randomization."
    )
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        f'r1,"Multi-omics aging MR","{abstract}",2024,PubMed\n',
        encoding="utf-8",
    )
    scope = {
        **scope_answer(),
        "evidence_spans": [
            {
                "criterion": "multiomics_evidence",
                "source": "abstract",
                "quote": "GWAS and transcriptomic eQTL",
            }
        ],
        "uncertainty_reason": "",
        "concise_rationale": "The current aging analysis uses two layers.",
    }
    causal = {
        **causal_answer(),
        "evidence_spans": [
            {
                "criterion": "causal_basis",
                "source": "abstract",
                "quote": "using Mendelian randomization",
            }
        ],
        "uncertainty_reason": "",
        "concise_rationale": "A named genetic-instrument design is applied.",
    }
    provider = QueueProvider(
        {
            "scope_reviewer": repeated(scope),
            "causal_method_reviewer": repeated(causal),
        }
    )
    output = tmp_path / "run"
    counts = run_stage_screening(
        input_path,
        output,
        provider,
        suite_config_path=SUITE,
    )
    result = json.loads((output / "screening_results.jsonl").read_text())
    assert counts == {"seek_full_text": 1}
    assert provider.calls == ["scope_reviewer"] * 5 + [
        "causal_method_reviewer"
    ] * 5
    assert result["role_agreement"]["scope_reviewer"]["report_type"][
        "unanimous"
    ]
    assert result["selected_criteria"]["causal_basis"] == (
        "named_causal_effect_design"
    )


def test_v1_full_text_uses_deterministic_sections_and_five_runs(tmp_path) -> None:
    record = {
        "record_id": "r1",
        "title": "Multi-omics aging MR",
        "abstract": "GWAS and eQTL data were analyzed by MR.",
        "year": 2024,
        "source": "PubMed",
        "sections": [
            {"section_id": "S1", "heading": "Methods", "text": "GWAS and eQTL data."},
            {
                "section_id": "S2",
                "heading": "Results",
                "text": "We estimated a two-sample MR effect on lifespan.",
            },
        ],
    }
    input_path = tmp_path / "fulltext.jsonl"
    input_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    eligibility = {
        "report_type": "empirical_primary",
        "empirical_primary": "yes",
        "bio_health_scope": "yes",
        "aging_process_relevance": "yes",
        "aging_role": "longevity_or_healthspan",
        "multiomics_status": "yes",
        "integration_mode": "cross_dataset_integrated",
        "omics_layers": [
            {
                "layer": "genomics",
                "assay_or_data_source": "GWAS",
                "cohort_or_system": "consortium",
                "origin": "external_dataset_analyzed",
                "analytic_role": "outcome",
                "section_ids": ["S1"],
            },
            {
                "layer": "transcriptomics",
                "assay_or_data_source": "eQTL",
                "cohort_or_system": "reference cohort",
                "origin": "external_dataset_analyzed",
                "analytic_role": "exposure",
                "section_ids": ["S1"],
            },
        ],
        "relevant_causal_design": "yes",
        "full_text_sufficient": "yes",
        "first_failed_criterion": "none",
        "evidence_spans": [
            {"criterion": "IC3", "section_id": "S1", "quote": "GWAS and eQTL"}
        ],
        "uncertainty_reason": "",
        "concise_rationale": "The empirical report integrates two layers.",
    }
    causal = {
        "causal_claim_present": "yes",
        "identification_status": "identified",
        "primary_design_family": "genetic_instrument",
        "supporting_design_families": [],
        "design_role": "primary_identification",
        "population_or_model": "consortium participants",
        "exposure_or_intervention": "genetically predicted expression",
        "comparator": "per expression unit",
        "outcome": "lifespan",
        "time_horizon": "lifelong",
        "estimand": {
            "statement": "effect of expression on lifespan",
            "effect_measure_or_contrast": "effect per expression unit",
        },
        "estimand_complete": "yes",
        "assumptions_assessable": "yes",
        "assumptions": [
            {
                "name": "instrument relevance",
                "status": "addressed",
                "assessment": "reported",
                "section_ids": ["S2"],
            }
        ],
        "diagnostics_and_sensitivity": [],
        "validations": [
            {
                "type": "independent_cohort",
                "independence": "independent",
                "alignment": "same_causal_link",
                "what_it_validates": "expression to lifespan link",
                "section_ids": ["S2"],
            }
        ],
        "validation_strength": "independent_same_link",
        "limitations": [],
        "evidence_spans": [
            {
                "criterion": "identification_status",
                "section_id": "S2",
                "quote": "two-sample MR effect",
            }
        ],
        "uncertainty_reason": "",
        "concise_rationale": "An assessable MR effect has independent validation.",
    }
    provider = QueueProvider(
        {
            "eligibility_reviewer": repeated(eligibility),
            "causal_evidence_reviewer": repeated(causal),
        }
    )
    output = tmp_path / "run"
    counts = run_stage_screening(
        input_path,
        output,
        provider,
        stage="full_text",
        suite_config_path=SUITE,
    )
    result = json.loads((output / "screening_results.jsonl").read_text())
    assert counts == {"assessed": 1}
    assert provider.calls == ["eligibility_reviewer"] * 5 + [
        "causal_evidence_reviewer"
    ] * 5
    assert result["section_selection"]["selection_method"] == (
        "deterministic_heading_keyword_v1"
    )
    assert result["causal_evidence_level"] == 4
    assert result["final_study_label"] == "causal_evidence_validated"
