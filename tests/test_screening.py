import json

from causal_multiomics_aging_review.screening import run_screening


class FakeProvider:
    model = "fake-model"
    url = "https://example.test/v1/chat/completions"

    def complete_json(self, prompt: str):
        if "scope reviewer" in prompt:
            answer = {
                "report_type": "empirical_primary",
                "bio_health_scope": "yes",
                "aging_process_relevance": "yes",
                "aging_role": "aging_intervention_target",
                "multiomics_status": "yes",
                "integration_mode": "same_study_joint_integration",
                "omics_layers": [
                    {
                        "layer": "transcriptomics",
                        "raw_term": "RNA",
                        "use_status": "measured_in_study",
                        "analytic_role": "perturbation response",
                    },
                    {
                        "layer": "proteomics",
                        "raw_term": "proteins",
                        "use_status": "measured_in_study",
                        "analytic_role": "perturbation response",
                    },
                ],
                "evidence_spans": [
                    {
                        "criterion": "aging_process_relevance",
                        "source": "abstract",
                        "quote": "aging intervention",
                    }
                ],
                "boundary_case": "clear_scope",
                "uncertainty_reason": "",
                "concise_rationale": "Primary multi-omics aging study.",
            }
        elif "causal-design reviewer" in prompt:
            answer = {
                "causal_claim_present": "yes",
                "identification_status": "identified",
                "design_families": ["direct_perturbation"],
                "design_role": "primary_identification",
                "exposure_or_intervention": "CRISPR perturbation",
                "comparator": "control cells",
                "outcome": "cellular aging phenotype",
                "estimand_or_contrast": "perturbed versus control cells",
                "evidence_spans": [
                    {
                        "criterion": "identification_status",
                        "source": "abstract",
                        "quote": "CRISPR perturbation",
                    }
                ],
                "boundary_case": "clear_identified",
                "uncertainty_reason": "",
                "concise_rationale": "The report applies a controlled perturbation.",
            }
        else:
            raise AssertionError("Adjudication should not be needed")
        return answer, {"fake": True}


def test_run_screening_writes_audited_result(tmp_path) -> None:
    input_path = tmp_path / "records.csv"
    input_path.write_text(
        "record_id,title,abstract,year,source\n"
        'r1,"Perturb-seq multi-omics aging",'
        '"We tested an aging intervention with RNA and proteins.",2024,PubMed\n',
        encoding="utf-8",
    )
    output = tmp_path / "run"
    counts = run_screening(input_path, output, FakeProvider())

    result = json.loads((output / "screening_results.jsonl").read_text())
    manifest = json.loads((output / "manifest.json").read_text())
    assert counts == {"seek_full_text": 1}
    assert result["final_decision"] == "seek_full_text"
    assert manifest["record_count"] == 1
    assert manifest["artifacts"]["scope_reviewer"]["prompt_sha256"]
