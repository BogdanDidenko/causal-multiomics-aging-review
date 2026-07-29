import json

from causal_multiomics_aging_review.screening import (
    _derive_title_identification_status,
    _logical_any_signal,
    _title_role_consensus,
    run_stage_screening,
)


class QueueProvider:
    model = "fake-model"
    url = "https://example.test/v1/chat/completions"
    temperature = 0.7
    top_p = 1.0
    seed = 0
    n = 1
    max_tokens = 16000
    response_format = "json_schema"

    def __init__(self, answers: dict[str, list[dict[str, object]]]) -> None:
        self.answers = answers
        self.calls: list[str] = []
        self.latest: dict[str, dict[str, object]] = {}

    def complete_json(self, prompt, schema=None, schema_name="screening_response"):
        self.calls.append(schema_name)
        if (
            schema_name.endswith("_contract_verifier")
            and (
                schema_name not in self.answers
                or not self.answers[schema_name]
            )
        ):
            if schema_name in self.latest:
                answer = dict(self.latest[schema_name])
            else:
                source_role = schema_name.removesuffix("_contract_verifier")
                answer = dict(self.latest[source_role])
        elif schema_name == "contract_verifier" and schema_name not in self.answers:
            answer = contract_verifier_answer(
                self.latest["scope_reviewer"],
                self.latest["causal_design_reviewer"],
                self.latest["directional_result_reviewer"],
            )
        else:
            answer = self.answers[schema_name].pop(0)
        self.latest[schema_name] = answer
        return answer, {"role": schema_name, "answer": answer}


def scope_answer() -> dict[str, object]:
    return {
        "report_type": "empirical_primary",
        "bio_health_scope": "yes",
        "aging_process_relevance": "yes",
        "multiomics_status": "yes",
        "omics_layers": [],
        "evidence_spans": [
            {"criterion": "multiomics_status", "source": "abstract", "quote": "GWAS and eQTL"}
        ],
        "boundary_case": "cross_dataset_multiomics",
        "uncertainty_reason": "",
        "concise_rationale": "Two molecular layers are analyzed together.",
    }


def causal_title_answer() -> dict[str, object]:
    return {
        "completed_current_report": "yes",
        "genetic_instrument_signal": "yes",
        "manipulation_design_signal": "no",
        "directed_model_signal": "no",
        "evidence_spans": [
            {
                "criterion": "completed_current_report",
                "source": "abstract",
                "quote": "analysis",
            }
        ],
        "uncertainty_reason": "",
        "concise_rationale": "The current report completed an analysis.",
    }


def directional_language_answer(signal: str = "no") -> dict[str, object]:
    return {
        "directional_language_signal": signal,
        "evidence_spans": [],
        "concise_rationale": "The directional language criterion is resolved.",
    }


def contract_verifier_answer(
    scope: dict[str, object] | None = None,
    causal: dict[str, object] | None = None,
    directional: dict[str, object] | None = None,
    **overrides: object,
) -> dict[str, object]:
    scope = scope or scope_answer()
    causal = causal or causal_title_answer()
    directional = directional or directional_language_answer()
    answer = {
        "report_type": scope["report_type"],
        "bio_health_scope": scope["bio_health_scope"],
        "aging_process_relevance": scope["aging_process_relevance"],
        "multiomics_status": scope["multiomics_status"],
        "omics_layers": [],
        "completed_current_report": causal["completed_current_report"],
        "genetic_instrument_signal": causal["genetic_instrument_signal"],
        "manipulation_design_signal": causal["manipulation_design_signal"],
        "directed_model_signal": causal["directed_model_signal"],
        "directional_language_signal": directional["directional_language_signal"],
        "boundary_case": scope["boundary_case"],
        "evidence_spans": [],
        "corrected_draft_fields": [],
        "uncertainty_reason": "",
        "concise_rationale": "The atomic contracts were verified.",
    }
    answer.update(overrides)
    return answer


def test_atomic_causal_signal_derivation_truth_table() -> None:
    cases = [
        ("no", "yes", "yes", "noncausal"),
        ("yes", "yes", "no", "causal_candidate"),
        ("yes", "no", "yes", "causal_candidate"),
        ("yes", "no", "no", "noncausal"),
        ("unclear", "no", "no", "unclear"),
        ("yes", "unclear", "no", "unclear"),
    ]
    for completed, applied, directional, expected in cases:
        answer = {
            "completed_current_report": completed,
            "applied_design_signal": applied,
            "directional_result_signal": directional,
        }
        changed = _derive_title_identification_status(
            answer,
            status_contract="causal_candidate_split_v4",
        )
        assert changed is True
        assert answer["identification_status"] == expected


def test_logical_any_signal_truth_table() -> None:
    assert _logical_any_signal(["no", "no"]) == "no"
    assert _logical_any_signal(["no", "unclear"]) == "unclear"
    assert _logical_any_signal(["unclear", "yes"]) == "yes"


def test_title_role_consensus_uses_field_majorities_and_preserves_votes() -> None:
    yes = directional_language_answer("yes")
    no = directional_language_answer("no")
    consensus, audit = _title_role_consensus(
        "directional_result_reviewer",
        [yes, no, yes],
    )

    assert consensus["directional_language_signal"] == "yes"
    assert audit["vote_count"] == 3
    assert audit["all_fields_unanimous"] is False
    assert audit["fields"]["directional_language_signal"] == {
        "votes": ["yes", "no", "yes"],
        "counts": {"no": 1, "yes": 2},
        "selected": "yes",
        "unanimous": False,
    }


def title_adjudication_answer(resolution_status: str) -> dict[str, object]:
    answer = {
        **scope_answer(),
        "completed_current_report": "yes",
        "applied_design_signal": "unclear",
        "directional_result_signal": "unclear",
        "exposure_or_intervention": "genetically predicted expression",
        "comparator": "per allele expression contrast",
        "outcome": "healthspan",
        "estimand_or_contrast": "effect of predicted expression on healthspan",
        "boundary_cases": ["thin_abstract"],
        "resolution_status": resolution_status,
        "uncertainty_reason": "The abstract does not report identification details.",
    }
    answer.pop("boundary_case")
    return answer


def selector_answer() -> dict[str, object]:
    return {
        "selected_sections": [
            {
                "section_id": "S1",
                "purposes": ["study_design", "omics_data"],
                "priority": "required",
            },
            {
                "section_id": "S2",
                "purposes": ["identification", "validation"],
                "priority": "required",
            },
        ],
        "coverage_status": "sufficient",
        "missing_evidence_categories": [],
        "concise_rationale": "Methods and Results contain decisive evidence.",
    }


def eligibility_answer() -> dict[str, object]:
    return {
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
                "assay_or_data_source": "disease GWAS",
                "cohort_or_system": "consortium",
                "origin": "external_dataset_analyzed",
                "analytic_role": "outcome",
                "section_ids": ["S1"],
            },
            {
                "layer": "transcriptomics",
                "assay_or_data_source": "cis-eQTL",
                "cohort_or_system": "GTEx",
                "origin": "external_dataset_analyzed",
                "analytic_role": "exposure",
                "section_ids": ["S1"],
            },
        ],
        "relevant_causal_design": "yes",
        "full_text_sufficient": "yes",
        "first_failed_criterion": "none",
        "evidence_spans": [{"criterion": "IC2", "section_id": "S1", "quote": "GWAS and eQTL"}],
        "uncertainty_reason": "",
        "concise_rationale": "The report is eligible.",
    }


def causal_full_text_answer() -> dict[str, object]:
    return {
        "causal_claim_present": "yes",
        "identification_status": "identified",
        "primary_design_family": "genetic_instrument",
        "supporting_design_families": [],
        "design_role": "primary_identification",
        "population_or_model": "European ancestry participants",
        "exposure_or_intervention": "genetically predicted expression",
        "comparator": "per allele contrast",
        "outcome": "healthspan",
        "time_horizon": "lifelong genetic exposure",
        "estimand": {
            "statement": "effect of predicted expression on healthspan",
            "effect_measure_or_contrast": "odds ratio per expression unit",
        },
        "estimand_complete": "yes",
        "assumptions_assessable": "yes",
        "assumptions": [
            {
                "name": "instrument relevance",
                "status": "addressed",
                "assessment": "F statistics exceeded 10",
                "section_ids": ["S2"],
            }
        ],
        "diagnostics_and_sensitivity": [
            {"name": "MR-Egger", "result_or_role": "pleiotropy check", "section_ids": ["S2"]}
        ],
        "validations": [
            {
                "type": "colocalization",
                "independence": "independent",
                "alignment": "same_causal_link",
                "what_it_validates": "shared variant for expression and disease",
                "section_ids": ["S2"],
            }
        ],
        "validation_strength": "independent_same_link",
        "limitations": ["Ancestry transportability is limited."],
        "evidence_spans": [
            {"criterion": "identification_status", "section_id": "S2", "quote": "two-sample MR"}
        ],
        "uncertainty_reason": "",
        "concise_rationale": "MR with aligned independent validation.",
    }


def test_title_stage_retries_invalid_response_and_resumes(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"Multi-omics MR","GWAS and eQTL Mendelian randomization.",2024,PubMed\n',
        encoding="utf-8",
    )
    invalid_scope = {**scope_answer(), "multiomics_status": "maybe"}
    provider = QueueProvider(
        {
            "scope_reviewer": [invalid_scope, scope_answer()],
            "causal_design_reviewer": [causal_title_answer()],
            "directional_result_reviewer": [directional_language_answer()],
        }
    )
    output = tmp_path / "run"
    counts = run_stage_screening(input_path, output, provider)
    assert counts == {"seek_full_text": 1}
    assert provider.calls.count("scope_reviewer") == 2
    raw_rows = [
        json.loads(line)
        for line in (output / "raw_provider_responses.jsonl").read_text().splitlines()
    ]
    assert raw_rows[0]["status"] == "error"
    assert raw_rows[0]["response"]["answer"]["multiomics_status"] == "maybe"
    assert raw_rows[1]["status"] == "ok"

    resumed_provider = QueueProvider({})
    resumed_counts = run_stage_screening(
        input_path,
        output,
        resumed_provider,
        resume=True,
    )
    assert resumed_counts == {"seek_full_text": 1}
    assert resumed_provider.calls == []


def test_full_text_stage_derives_level_four_and_ledger_fields(tmp_path) -> None:
    input_path = tmp_path / "fulltext.jsonl"
    record = {
        "record_id": "r1",
        "title": "Multi-omics MR study",
        "abstract": "GWAS and eQTL MR analysis.",
        "year": 2024,
        "source": "PubMed",
        "sections": [
            {"section_id": "S1", "heading": "Methods", "text": "GWAS and eQTL data."},
            {"section_id": "S2", "heading": "Results", "text": "MR and colocalization results."},
        ],
    }
    input_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    provider = QueueProvider(
        {
            "section_selector": [selector_answer()],
            "eligibility_reviewer": [eligibility_answer()],
            "causal_evidence_reviewer": [causal_full_text_answer()],
        }
    )
    output = tmp_path / "run"
    counts = run_stage_screening(
        input_path,
        output,
        provider,
        stage="full_text",
    )
    result = json.loads((output / "screening_results.jsonl").read_text())
    assert counts == {"assessed": 1}
    assert result["causal_evidence_level"] == 4
    assert result["final_study_label"] == "causal_evidence"
    assert result["ledger_fields"]["identification_source"] == "genetic_instrument"


def test_missing_abstract_routes_to_manual_review_without_model_call(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\nr1,No abstract,,2024,Scopus\n",
        encoding="utf-8",
    )
    provider = QueueProvider({})
    output = tmp_path / "run"
    counts = run_stage_screening(input_path, output, provider)
    result = json.loads((output / "screening_results.jsonl").read_text())
    assert counts == {"manual_review": 1}
    assert result["manual_review_reason"] == "missing_abstract"
    assert provider.calls == []


def test_oversized_abstract_metadata_routes_to_manual_review(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        f'r1,"Possible full-text leakage","{"a" * 5001}",2024,OpenAlex\n',
        encoding="utf-8",
    )
    provider = QueueProvider({})
    output = tmp_path / "run"
    counts = run_stage_screening(input_path, output, provider)
    result = json.loads((output / "screening_results.jsonl").read_text())
    assert counts == {"manual_review": 1}
    assert result["manual_review_reason"] == "oversized_abstract_metadata"
    assert result["manual_review_details"] == {
        "abstract_chars": 5001,
        "maximum": 5000,
    }
    assert provider.calls == []


def test_conference_abstract_number_mismatch_routes_to_manual_review(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"117 Target abstract","114 Different abstract body.",2024,Scopus\n',
        encoding="utf-8",
    )
    provider = QueueProvider({})
    output = tmp_path / "run"
    counts = run_stage_screening(input_path, output, provider)
    result = json.loads((output / "screening_results.jsonl").read_text())
    assert counts == {"manual_review": 1}
    assert result["manual_review_reason"] == "conference_abstract_number_mismatch"
    assert result["manual_review_details"] == {
        "title_abstract_number": "117",
        "body_abstract_number": "114",
    }
    assert provider.calls == []


def test_conference_abstract_body_fragment_routes_to_manual_review(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"P1-272: Multi-omics study","from 2005 to 2012 unrelated data.",2024,Scopus\n',
        encoding="utf-8",
    )
    provider = QueueProvider({})
    output = tmp_path / "run"
    counts = run_stage_screening(input_path, output, provider)
    result = json.loads((output / "screening_results.jsonl").read_text())
    assert counts == {"manual_review": 1}
    assert result["manual_review_reason"] == "conference_abstract_body_fragment"
    assert provider.calls == []


def test_record_filter_runs_only_requested_identifier(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"First","GWAS and eQTL were integrated.",2024,PubMed\n'
        'r2,"Second","GWAS and pQTL MR were integrated.",2024,PubMed\n',
        encoding="utf-8",
    )
    provider = QueueProvider(
        {
            "scope_reviewer": [scope_answer()],
            "causal_design_reviewer": [causal_title_answer()],
            "directional_result_reviewer": [directional_language_answer()],
        }
    )
    output = tmp_path / "run"
    counts = run_stage_screening(
        input_path,
        output,
        provider,
        record_ids={"r2"},
    )
    result = json.loads((output / "screening_results.jsonl").read_text())
    manifest = json.loads((output / "manifest.json").read_text())
    assert counts == {"seek_full_text": 1}
    assert result["record_id"] == "r2"
    assert manifest["record_ids"] == ["r2"]
    assert manifest["input_record_count"] == 1


def test_directional_language_signal_merges_into_causal_status(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"Multi-omics mechanism","X drives healthy aging.",2024,PubMed\n',
        encoding="utf-8",
    )
    provider = QueueProvider(
        {
            "scope_reviewer": [scope_answer()],
            "causal_design_reviewer": [
                {
                    **causal_title_answer(),
                    "genetic_instrument_signal": "no",
                }
            ],
            "directional_result_reviewer": [directional_language_answer("yes")],
        }
    )
    output = tmp_path / "run"
    counts = run_stage_screening(input_path, output, provider)
    result = json.loads((output / "screening_results.jsonl").read_text())
    raw_rows = [
        json.loads(line)
        for line in (output / "raw_provider_responses.jsonl").read_text().splitlines()
    ]

    assert counts == {"seek_full_text": 1}
    assert provider.calls.count("directional_result_reviewer") == 1
    assert result["selected_criteria"]["directional_result_signal"] == "yes"
    assert any(
        row["role"] == "directional_result_reviewer"
        and row["status"] == "ok"
        for row in raw_rows
    )


def test_contract_verifier_canonicalizes_draft_and_preserves_audit(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"Path model","A path model maps associations.",2024,PubMed\n',
        encoding="utf-8",
    )
    draft_causal = {
        **causal_title_answer(),
        "genetic_instrument_signal": "no",
        "directed_model_signal": "yes",
    }
    verified = contract_verifier_answer(
        causal=draft_causal,
        genetic_instrument_signal="no",
        directed_model_signal="no",
    )
    provider = QueueProvider(
        {
            "scope_reviewer": [scope_answer()],
            "causal_design_reviewer": [draft_causal],
            "directional_result_reviewer": [directional_language_answer()],
            "causal_design_reviewer_contract_verifier": [
                {
                    key: value
                    for key, value in verified.items()
                    if key
                    in {
                        "completed_current_report",
                        "genetic_instrument_signal",
                        "manipulation_design_signal",
                        "directed_model_signal",
                    }
                }
                | {
                    "evidence_spans": [],
                    "uncertainty_reason": "",
                    "concise_rationale": "The causal contract was verified.",
                }
            ],
        }
    )
    output = tmp_path / "run"
    counts = run_stage_screening(input_path, output, provider)
    result = json.loads((output / "screening_results.jsonl").read_text())
    raw_rows = [
        json.loads(line)
        for line in (output / "raw_provider_responses.jsonl").read_text().splitlines()
    ]

    assert counts == {"exclude": 1}
    assert (
        result["draft_round_a"]["causal_design_reviewer"]["directed_model_signal"]
        == "yes"
    )
    assert (
        result["round_a"]["causal_design_reviewer"]["directed_model_signal"]
        == "no"
    )
    assert result["contract_corrections"] == [
        "causal_design_reviewer.directed_model_signal"
    ]
    assert any(
        row.get("phase") == "contract_verification"
        and row["role"] == "causal_design_reviewer_contract_verifier"
        for row in raw_rows
    )


def test_thin_abstract_uncertainty_proceeds_to_full_text(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"Thin multi-omics study","GWAS and eQTL were integrated.",2024,PubMed\n',
        encoding="utf-8",
    )
    unclear_causal = {
        **causal_title_answer(),
        "completed_current_report": "unclear",
        "genetic_instrument_signal": "unclear",
    }
    provider = QueueProvider(
        {
            "scope_reviewer": [scope_answer()],
            "causal_design_reviewer": [unclear_causal],
            "directional_result_reviewer": [directional_language_answer()],
            "adjudicator": [title_adjudication_answer("insufficient_title_abstract")],
        }
    )
    counts = run_stage_screening(input_path, tmp_path / "run", provider)
    assert counts == {"seek_full_text": 1}


def test_title_consistency_rules_short_circuit_nonaging_design(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"Disease time points","Age marks sampling time in a disease study.",2024,PubMed\n',
        encoding="utf-8",
    )
    scope = {
        **scope_answer(),
        "aging_process_relevance": "no",
    }
    causal = {
        **causal_title_answer(),
    }
    adjudication = {
        **title_adjudication_answer("resolved"),
        "aging_process_relevance": "no",
        "applied_design_signal": "no",
        "directional_result_signal": "no",
    }
    provider = QueueProvider(
        {
            "scope_reviewer": [scope],
            "causal_design_reviewer": [causal],
            "directional_result_reviewer": [directional_language_answer()],
            "adjudicator": [adjudication],
        }
    )
    output = tmp_path / "run"
    counts = run_stage_screening(input_path, output, provider)
    result = json.loads((output / "screening_results.jsonl").read_text())
    assert counts == {"exclude": 1}
    assert (
        result["round_a"]["causal_design_reviewer"]["identification_status"]
        == "noncausal"
    )
    assert "primary_design_family" not in result["round_a"]["causal_design_reviewer"]
    assert "design_role" not in result["round_a"]["causal_design_reviewer"]
    assert result["round_a"]["scope_reviewer"]["multiomics_status"] == "not_assessed"
    assert "primary_design_family" not in result["selected_criteria"]
    assert "design_role" not in result["selected_criteria"]
    assert result["selected_criteria"]["multiomics_status"] == "not_assessed"
    assert (
        result["round_a"]["causal_design_reviewer"]["completed_current_report"]
        == "not_assessed"
    )
    assert (
        result["round_a"]["directional_result_reviewer"][
            "directional_language_signal"
        ]
        == "not_assessed"
    )
    assert result["consistency_rules_applied"] == [
        "downstream_scope_criteria_normalized_from_prisma_sequence",
        "title_omics_layer_inventory_deferred_to_full_text",
        "excluded_scope_short_circuits_causal_criteria",
        "applied_design_signal_derived_from_atomic_design_signals",
        "directional_result_signal_copied_from_language_specialist",
        "identification_status_derived_from_atomic_causal_signals",
        "ineligible_scope_implies_no_relevant_causal_design",
        "title_effect_strength_and_design_subtyping_deferred_to_full_text",
    ]


def test_title_multiomics_author_claim_does_not_require_title_inventory(
    tmp_path,
) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"Mixed provenance","Multi-omics plus external GWAS.",2024,PubMed\n',
        encoding="utf-8",
    )
    scope = scope_answer()
    provider = QueueProvider(
        {
            "scope_reviewer": [scope],
            "causal_design_reviewer": [causal_title_answer()],
            "directional_result_reviewer": [directional_language_answer()],
        }
    )
    output = tmp_path / "run"
    counts = run_stage_screening(input_path, output, provider)
    result = json.loads((output / "screening_results.jsonl").read_text())
    assert counts == {"seek_full_text": 1}
    assert result["round_a"]["scope_reviewer"]["multiomics_status"] == "yes"
    assert result["selected_criteria"]["multiomics_status"] == "yes"
    assert result["selected_criteria"]["omics_layers"] == []
    raw_rows = [
        json.loads(line)
        for line in (output / "raw_provider_responses.jsonl").read_text().splitlines()
    ]
    assert raw_rows[0]["response"]["answer"]["multiomics_status"] == "yes"


def test_title_sequence_skips_scope_fields_after_nonempirical_report(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"Aging meeting report","Discussions covered healthspan.",2024,PubMed\n',
        encoding="utf-8",
    )
    scope = {
        **scope_answer(),
        "report_type": "nonempirical",
        "bio_health_scope": "yes",
        "aging_process_relevance": "yes",
        "multiomics_status": "yes",
    }
    provider = QueueProvider(
        {
            "scope_reviewer": [scope],
            "causal_design_reviewer": [causal_title_answer()],
            "directional_result_reviewer": [directional_language_answer()],
        }
    )
    output = tmp_path / "run"
    counts = run_stage_screening(input_path, output, provider)
    result = json.loads((output / "screening_results.jsonl").read_text())
    normalized = result["round_a"]["scope_reviewer"]

    assert counts == {"exclude": 1}
    assert normalized["report_type"] == "nonempirical"
    assert normalized["bio_health_scope"] == "not_assessed"
    assert normalized["aging_process_relevance"] == "not_assessed"
    assert normalized["multiomics_status"] == "not_assessed"
    assert result["final_exclusion_code"] == "EC1"


def test_title_sequential_scope_short_circuit_defers_multiomics_after_unclear_aging(
    tmp_path,
) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"Senescence genes","Multi-omics study of senescence-related genes.",'
        "2024,PubMed\n",
        encoding="utf-8",
    )
    scope = {
        **scope_answer(),
        "aging_process_relevance": "unclear",
        "multiomics_status": "yes",
    }
    adjudication = {
        **title_adjudication_answer("insufficient_title_abstract"),
        "aging_process_relevance": "unclear",
        "multiomics_status": "yes",
        "applied_design_signal": "yes",
        "directional_result_signal": "no",
    }
    provider = QueueProvider(
        {
            "scope_reviewer": [scope],
            "causal_design_reviewer": [causal_title_answer()],
            "directional_result_reviewer": [directional_language_answer()],
            "adjudicator": [adjudication],
        }
    )
    output = tmp_path / "run"
    counts = run_stage_screening(input_path, output, provider)
    result = json.loads((output / "screening_results.jsonl").read_text())

    assert counts == {"seek_full_text": 1}
    assert result["round_a"]["scope_reviewer"]["multiomics_status"] == "not_assessed"
    assert (
        result["round_a"]["causal_design_reviewer"]["identification_status"]
        == "unclear"
    )
    assert result["selected_criteria"]["multiomics_status"] == "not_assessed"
    assert (
        result["selected_criteria"]["identification_status"] == "unclear"
    )
    assert result["adjudication"] is None
    assert (
        result["gates"]["scope_short_circuit"] == "seek_full_text"
    )


def test_unresolved_decisive_conflict_routes_to_manual_review(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"Ambiguous study","GWAS and eQTL analysis.",2024,PubMed\n',
        encoding="utf-8",
    )
    unclear_causal = {
        **causal_title_answer(),
        "completed_current_report": "unclear",
        "genetic_instrument_signal": "unclear",
    }
    provider = QueueProvider(
        {
            "scope_reviewer": [scope_answer()],
            "causal_design_reviewer": [unclear_causal],
            "directional_result_reviewer": [directional_language_answer()],
            "adjudicator": [title_adjudication_answer("conflict_unresolved")],
        }
    )
    counts = run_stage_screening(input_path, tmp_path / "run", provider)
    assert counts == {"manual_review": 1}


def test_malformed_jsonl_and_missing_identifier_are_not_lost(tmp_path) -> None:
    input_path = tmp_path / "fulltext.jsonl"
    input_path.write_text(
        '{"title": "Missing identifier", "abstract": "Present"}\n{bad json}\n',
        encoding="utf-8",
    )
    provider = QueueProvider({})
    output = tmp_path / "run"
    counts = run_stage_screening(
        input_path,
        output,
        provider,
        stage="full_text",
    )
    results = [
        json.loads(line)
        for line in (output / "screening_results.jsonl").read_text().splitlines()
    ]
    assert counts == {"manual_review": 2}
    assert [row["record_id"] for row in results] == [
        "invalid-full_text-record-000001",
        "invalid-jsonl-line-000002",
    ]
    assert all(row["manual_review_reason"] == "invalid_input_record" for row in results)
    assert provider.calls == []
