from __future__ import annotations

import json
from typing import Any

TITLE_DECISIVE_PATHS = (
    "contract_verification.scope_reviewer.report_type",
    "contract_verification.scope_reviewer.bio_health_scope",
    "contract_verification.scope_reviewer.aging_process_relevance",
    "contract_verification.scope_reviewer.multiomics_status",
    "contract_verification.causal_design_reviewer.completed_current_report",
    "contract_verification.causal_design_reviewer.genetic_instrument_signal",
    "contract_verification.causal_design_reviewer.manipulation_design_signal",
    "contract_verification.causal_design_reviewer.directed_model_signal",
    "contract_verification.directional_result_reviewer.directional_language_signal",
    "contract_verification.report_type",
    "contract_verification.bio_health_scope",
    "contract_verification.aging_process_relevance",
    "contract_verification.multiomics_status",
    "contract_verification.completed_current_report",
    "contract_verification.genetic_instrument_signal",
    "contract_verification.manipulation_design_signal",
    "contract_verification.directed_model_signal",
    "contract_verification.directional_language_signal",
    "round_a.scope_reviewer.report_type",
    "round_a.scope_reviewer.bio_health_scope",
    "round_a.scope_reviewer.aging_process_relevance",
    "round_a.scope_reviewer.multiomics_status",
    "round_a.causal_design_reviewer.completed_current_report",
    "round_a.causal_design_reviewer.genetic_instrument_signal",
    "round_a.causal_design_reviewer.manipulation_design_signal",
    "round_a.causal_design_reviewer.directed_model_signal",
    "round_a.causal_design_reviewer.applied_design_signal",
    "round_a.directional_result_reviewer.directional_language_signal",
    "round_a.directional_result_reviewer.directional_result_signal",
    "round_a.causal_design_reviewer.identification_status",
    "adjudication.report_type",
    "adjudication.bio_health_scope",
    "adjudication.aging_process_relevance",
    "adjudication.multiomics_status",
    "adjudication.completed_current_report",
    "adjudication.applied_design_signal",
    "adjudication.directional_result_signal",
    "adjudication.identification_status",
    "selected_criteria.report_type",
    "selected_criteria.bio_health_scope",
    "selected_criteria.aging_process_relevance",
    "selected_criteria.multiomics_status",
    "selected_criteria.completed_current_report",
    "selected_criteria.genetic_instrument_signal",
    "selected_criteria.manipulation_design_signal",
    "selected_criteria.directed_model_signal",
    "selected_criteria.applied_design_signal",
    "selected_criteria.directional_language_signal",
    "selected_criteria.directional_result_signal",
    "selected_criteria.identification_status",
    "final_decision",
    "final_exclusion_code",
)

TITLE_DRAFT_PATHS = (
    "draft_round_a.scope_reviewer.report_type",
    "draft_round_a.scope_reviewer.bio_health_scope",
    "draft_round_a.scope_reviewer.aging_process_relevance",
    "draft_round_a.scope_reviewer.multiomics_status",
    "draft_round_a.causal_design_reviewer.completed_current_report",
    "draft_round_a.causal_design_reviewer.genetic_instrument_signal",
    "draft_round_a.causal_design_reviewer.manipulation_design_signal",
    "draft_round_a.causal_design_reviewer.directed_model_signal",
    "draft_round_a.directional_result_reviewer.directional_language_signal",
)

FULL_TEXT_DECISIVE_PATHS = (
    "section_selection.selected_sections",
    "section_selection.coverage_status",
    "round_a.eligibility_reviewer.empirical_primary",
    "round_a.eligibility_reviewer.bio_health_scope",
    "round_a.eligibility_reviewer.aging_process_relevance",
    "round_a.eligibility_reviewer.aging_role",
    "round_a.eligibility_reviewer.multiomics_status",
    "round_a.eligibility_reviewer.full_text_sufficient",
    "round_a.causal_evidence_reviewer.identification_status",
    "round_a.causal_evidence_reviewer.primary_design_family",
    "round_a.causal_evidence_reviewer.supporting_design_families",
    "round_a.causal_evidence_reviewer.estimand_complete",
    "round_a.causal_evidence_reviewer.assumptions_assessable",
    "round_a.causal_evidence_reviewer.validation_strength",
    "adjudication.empirical_primary",
    "adjudication.bio_health_scope",
    "adjudication.aging_process_relevance",
    "adjudication.aging_role",
    "adjudication.multiomics_status",
    "adjudication.identification_status",
    "adjudication.primary_design_family",
    "adjudication.estimand_complete",
    "adjudication.assumptions_assessable",
    "adjudication.validation_strength",
    "selected_criteria.empirical_primary",
    "selected_criteria.bio_health_scope",
    "selected_criteria.aging_process_relevance",
    "selected_criteria.aging_role",
    "selected_criteria.multiomics_status",
    "selected_criteria.full_text_sufficient",
    "selected_criteria.identification_status",
    "selected_criteria.primary_design_family",
    "selected_criteria.supporting_design_families",
    "selected_criteria.estimand_complete",
    "selected_criteria.assumptions_assessable",
    "selected_criteria.validation_strength",
    "causal_evidence_level",
    "final_study_label",
    "final_decision",
    "final_exclusion_code",
)

TITLE_SELECTED_DECISIVE_FIELDS = (
    "report_type",
    "bio_health_scope",
    "aging_process_relevance",
    "multiomics_status",
    "completed_current_report",
    "applied_design_signal",
    "directional_result_signal",
    "identification_status",
)

V1_TITLE_DECISIVE_PATHS = (
    "selected_criteria.report_type",
    "selected_criteria.bio_health_scope",
    "selected_criteria.aging_process_relevance",
    "selected_criteria.multiomics_evidence",
    "selected_criteria.current_report_layer_use",
    "selected_criteria.multiomics_status",
    "selected_criteria.causal_basis",
    "selected_criteria.design_families",
    "selected_criteria.causal_information_sufficiency",
    "selected_criteria.identification_status",
    "decision_reason",
    "final_decision",
    "final_exclusion_code",
)

V1_TITLE_SELECTED_DECISIVE_FIELDS = (
    "report_type",
    "bio_health_scope",
    "aging_process_relevance",
    "multiomics_evidence",
    "current_report_layer_use",
    "multiomics_status",
    "causal_basis",
    "design_families",
    "causal_information_sufficiency",
    "identification_status",
)


def decisive_paths(stage: str, architecture: str | None = None) -> tuple[str, ...]:
    if architecture == "v1_two_role_unanimous":
        return V1_TITLE_DECISIVE_PATHS
    if stage == "title_abstract":
        return TITLE_DECISIVE_PATHS
    if stage == "full_text":
        return FULL_TEXT_DECISIVE_PATHS
    raise ValueError(f"Unsupported screening stage: {stage}")


def assess_stability(
    run_results: dict[str, dict[str, dict[str, Any]]],
    stage: str,
    acceptance: dict[str, float],
    architecture: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(run_results) < 2:
        raise ValueError("Stability assessment requires at least two runs")
    labels = sorted(run_results)
    identifier_sets = [set(run_results[label]) for label in labels]
    if any(items != identifier_sets[0] for items in identifier_sets[1:]):
        raise ValueError("Stability runs contain different record IDs")

    paths = decisive_paths(stage, architecture)
    rows: list[dict[str, Any]] = []
    schema_successes = 0
    manual_results = 0
    contract_correction_results = 0
    contract_verifier_fields = 0
    unanimous_contract_verifier_fields = 0
    internal_decision_fields = 0
    unanimous_internal_decision_fields = 0
    for identifier in sorted(identifier_sets[0]):
        by_run = {label: run_results[label][identifier] for label in labels}
        for row in by_run.values():
            role_agreement = row.get("role_agreement")
            if isinstance(role_agreement, dict):
                for role_fields in role_agreement.values():
                    if not isinstance(role_fields, dict):
                        continue
                    for field_audit in role_fields.values():
                        if not isinstance(field_audit, dict):
                            continue
                        unanimous = field_audit.get("unanimous")
                        if isinstance(unanimous, bool):
                            internal_decision_fields += 1
                            unanimous_internal_decision_fields += int(unanimous)
            consensus = row.get("contract_consensus")
            if not isinstance(consensus, dict):
                continue
            for role_audit in consensus.values():
                if not isinstance(role_audit, dict):
                    continue
                fields = role_audit.get("fields")
                if not isinstance(fields, dict):
                    continue
                for field_audit in fields.values():
                    if not isinstance(field_audit, dict):
                        continue
                    unanimous = field_audit.get("unanimous")
                    if not isinstance(unanimous, bool):
                        continue
                    contract_verifier_fields += 1
                    unanimous_contract_verifier_fields += int(unanimous)
        values = {
            path: {label: _normalized_path(row, path) for label, row in by_run.items()}
            for path in paths
        }
        diagnostic_disagreements = {
            path: run_values
            for path, run_values in values.items()
            if len({_json(value) for value in run_values.values()}) > 1
        }
        draft_disagreements: dict[str, dict[str, Any]] = {}
        if stage == "title_abstract" and architecture != "v1_two_role_unanimous":
            draft_values = {
                path: {
                    label: _normalized_path(row, path)
                    for label, row in by_run.items()
                }
                for path in TITLE_DRAFT_PATHS
            }
            draft_disagreements = {
                path: run_values
                for path, run_values in draft_values.items()
                if len({_json(value) for value in run_values.values()}) > 1
            }
        correction_labels = [
            label
            for label, row in by_run.items()
            if row.get("contract_corrections")
        ]
        contract_correction_results += len(correction_labels)
        decisive_values = {
            label: _decisive_signature(row, stage, architecture)
            for label, row in by_run.items()
        }
        decisive_stable = len({_json(value) for value in decisive_values.values()}) == 1
        decisive_disagreements = (
            {} if decisive_stable else _signature_disagreements(decisive_values)
        )
        manual_labels = [
            label
            for label, row in by_run.items()
            if row.get("final_decision") == "manual_review"
        ]
        schema_successes += sum(
            row.get("manual_review_reason") != "role_execution_failed"
            for row in by_run.values()
        )
        manual_results += len(manual_labels)
        rows.append(
            {
                "record_id": identifier,
                "stage": stage,
                "stable": decisive_stable and not manual_labels,
                "decisive_criteria_stable": decisive_stable,
                "diagnostic_all_tracked_criteria_stable": not diagnostic_disagreements,
                "diagnostic_raw_reviewer_drafts_stable": not draft_disagreements,
                "final_decision_stable": (
                    "final_decision" not in diagnostic_disagreements
                ),
                "causal_evidence_level_stable": (
                    "causal_evidence_level" not in diagnostic_disagreements
                    if stage == "full_text"
                    else True
                ),
                "manual_review_runs": manual_labels,
                "contract_correction_runs": correction_labels,
                "decisive_disagreements": decisive_disagreements,
                "diagnostic_disagreements": diagnostic_disagreements,
                "raw_reviewer_draft_disagreements": draft_disagreements,
            }
        )

    record_count = len(rows)
    run_count = len(labels)
    metrics = {
        "schema_success_rate": schema_successes / (record_count * run_count),
        "final_decision_exact_agreement": _rate(
            row["final_decision_stable"] for row in rows
        ),
        "decisive_criteria_exact_agreement": _rate(
            row["decisive_criteria_stable"] for row in rows
        ),
        "causal_evidence_level_exact_agreement": _rate(
            row["causal_evidence_level_stable"] for row in rows
        ),
        "manual_review_rate": manual_results / (record_count * run_count),
        "fully_stable_record_rate": _rate(row["stable"] for row in rows),
        "all_tracked_criteria_exact_agreement": _rate(
            row["diagnostic_all_tracked_criteria_stable"] for row in rows
        ),
        "raw_reviewer_draft_exact_agreement": (
            None
            if architecture == "v1_two_role_unanimous"
            else _rate(row["diagnostic_raw_reviewer_drafts_stable"] for row in rows)
        ),
        "contract_correction_rate": (
            contract_correction_results / (record_count * run_count)
            if stage == "title_abstract"
            else 0.0
        ),
        "contract_verifier_field_unanimity_rate": (
            unanimous_contract_verifier_fields / contract_verifier_fields
            if contract_verifier_fields
            else None
        ),
        "internal_decision_field_unanimity_rate": (
            unanimous_internal_decision_fields / internal_decision_fields
            if internal_decision_fields
            else None
        ),
    }
    gates = {
        metric: {
            "value": metrics[metric],
            "threshold": threshold,
            "passed": (
                metrics[metric] <= threshold
                if metric == "manual_review_rate"
                else metrics[metric] >= threshold
            ),
        }
        for metric, threshold in acceptance.items()
    }
    return rows, {
        "stage": stage,
        "run_labels": labels,
        "record_count": record_count,
        "run_count": run_count,
        "metrics": metrics,
        "acceptance": {
            "overall": "pass" if all(gate["passed"] for gate in gates.values()) else "fail",
            "gates": gates,
        },
    }


def _decisive_signature(
    row: dict[str, Any], stage: str, architecture: str | None = None
) -> dict[str, Any]:
    decision = row.get("final_decision")
    signature = {
        "final_decision": decision,
        "final_exclusion_code": row.get("final_exclusion_code"),
    }
    if decision == "manual_review":
        signature["manual_review_reason"] = row.get("manual_review_reason")
        return _normalize(signature)
    if stage == "title_abstract" and decision == "exclude":
        return _normalize(signature)

    if stage == "title_abstract":
        selected = row.get("selected_criteria", {})
        fields = (
            V1_TITLE_SELECTED_DECISIVE_FIELDS
            if architecture == "v1_two_role_unanimous"
            else TITLE_SELECTED_DECISIVE_FIELDS
        )
        for field in fields:
            signature[f"selected_criteria.{field}"] = (
                _omics_layer_categories(selected)
                if field == "omics_layer_categories"
                else _normalize(selected.get(field))
            )
    else:
        selected_prefix = "selected_criteria."
        for path in decisive_paths(stage, architecture):
            if path.startswith(selected_prefix):
                signature[path] = _normalized_path(row, path)
    if stage == "full_text":
        signature["causal_evidence_level"] = row.get("causal_evidence_level")
        signature["final_study_label"] = row.get("final_study_label")
    return _normalize(signature)


def _signature_disagreements(
    signatures: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    keys = sorted({key for signature in signatures.values() for key in signature})
    return {
        key: {label: signature.get(key) for label, signature in signatures.items()}
        for key in keys
        if len({_json(signature.get(key)) for signature in signatures.values()}) > 1
    }


def _normalized_path(row: dict[str, Any], path: str) -> Any:
    if path.endswith(".omics_layer_categories"):
        parent_path = path.rsplit(".", 1)[0]
        value: Any = row
        for part in parent_path.split("."):
            if not isinstance(value, dict):
                return []
            value = value.get(part)
        return _omics_layer_categories(value)
    value: Any = row
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return _normalize(value)


def _omics_layer_categories(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    layers = value.get("omics_layers", [])
    if not isinstance(layers, list):
        return []
    return sorted(
        {
            str(item["layer"])
            for item in layers
            if isinstance(item, dict) and item.get("layer")
        }
    )


def _normalize(value: Any) -> Any:
    if isinstance(value, list):
        return sorted((_normalize(item) for item in value), key=_json)
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in sorted(value.items())}
    return value


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _rate(values: Any) -> float:
    items = list(values)
    return sum(bool(item) for item in items) / len(items) if items else 0.0
