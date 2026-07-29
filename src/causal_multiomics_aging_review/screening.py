from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .audit import git_revision, sha256_file, write_manifest
from .config import (
    DEFAULT_SUITE_CONFIG,
    REPO_ROOT,
    load_gate_config,
    load_json,
    load_stage_config,
    resolve_screening_artifact,
    resolve_suite_artifact,
)
from .gates import route_adjudicated, route_round_a
from .grading import (
    EvidenceReferenceError,
    build_ledger_fields,
    derive_evidence_level,
    derive_exclusion_code,
    validate_evidence_references,
)
from .llm import OpenAICompatibleProvider, ProviderError
from .metadata_quality import title_abstract_metadata_issue
from .schema import SchemaError, validate_object

PLACEHOLDERS = (
    "RECORD_ID",
    "TITLE",
    "ABSTRACT",
    "YEAR",
    "SOURCE",
    "DOCUMENT_TYPE",
)


def render_prompt(
    template: str,
    record: dict[str, Any],
    extra: dict[str, str] | None = None,
) -> str:
    values = {
        "RECORD_ID": record_id(record),
        "TITLE": str(record.get("title", "")),
        "ABSTRACT": str(record.get("abstract", "")),
        "YEAR": str(record.get("year", "")),
        "SOURCE": str(record.get("source", record.get("provenance_sources", ""))),
        "DOCUMENT_TYPE": str(record.get("document_type", "")),
        **(extra or {}),
    }
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def record_id(record: dict[str, Any]) -> str:
    for field in ("record_id", "canonical_id", "source_record_id", "id", "doi", "pmid"):
        if str(record.get(field, "")).strip():
            return str(record[field]).strip()
    raise ValueError(
        "Record has no record_id, canonical_id, source_record_id, id, DOI, or PMID"
    )


def audit_input_path(path: str | Path) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return f"external/{resolved.name}"


def read_records(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_jsonl_records(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                records.append(
                    {
                        "record_id": f"invalid-jsonl-line-{line_number:06d}",
                        "_input_error": f"JSONL line {line_number}: {error}",
                    }
                )
                continue
            if not isinstance(value, dict):
                records.append(
                    {
                        "record_id": f"invalid-jsonl-line-{line_number:06d}",
                        "_input_error": f"JSONL line {line_number} is not an object",
                    }
                )
                continue
            records.append(value)
    return records


def run_screening(
    input_path: str | Path,
    output_dir: str | Path,
    provider: OpenAICompatibleProvider,
    config_path: str | Path | None = None,
    limit: int | None = None,
) -> dict[str, int]:
    config_path = Path(config_path).resolve() if config_path else None
    config = load_gate_config(config_path)
    records = read_records(input_path)
    if limit is not None:
        records = records[:limit]

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "screening_results.jsonl"
    raw_path = output / "raw_provider_responses.jsonl"
    counts: dict[str, int] = {}

    artifacts: dict[str, dict[str, Any]] = {}
    for role, role_config in {**config["round_a"], "adjudicator": config["adjudication"]}.items():
        prompt_path = resolve_screening_artifact(role_config["prompt"], config_path)
        schema_path = resolve_screening_artifact(role_config["schema"], config_path)
        artifacts[role] = {
            "prompt_path": str(prompt_path.relative_to(REPO_ROOT)),
            "prompt_sha256": sha256_file(prompt_path),
            "schema_path": str(schema_path.relative_to(REPO_ROOT)),
            "schema_sha256": sha256_file(schema_path),
            "prompt": prompt_path.read_text(encoding="utf-8"),
            "schema": load_json(schema_path),
        }

    with result_path.open("w", encoding="utf-8") as results, raw_path.open(
        "w", encoding="utf-8"
    ) as raw_results:
        for record in records:
            answers: dict[str, dict[str, Any]] = {}
            role_gates: dict[str, str] = {}
            for role in config["round_a"]:
                prompt = render_prompt(artifacts[role]["prompt"], record)
                answer, raw = provider.complete_json(prompt)
                validate_object(answer, artifacts[role]["schema"])
                answers[role] = answer
                raw_results.write(
                    json.dumps(
                        {"record_id": record_id(record), "role": role, "response": raw}
                    )
                    + "\n"
                )

            route, decisions = route_round_a(answers, config)
            role_gates.update(decisions)
            adjudication = None
            if route == "adjudicate":
                causal_review = _merge_answers(
                    answers["causal_design_reviewer"],
                    answers.get("directional_result_reviewer", {}),
                )
                extra = {
                    "SCOPE_REVIEW": json.dumps(answers["scope_reviewer"], ensure_ascii=False),
                    "CAUSAL_REVIEW": json.dumps(causal_review, ensure_ascii=False),
                }
                prompt = render_prompt(artifacts["adjudicator"]["prompt"], record, extra)
                adjudication, raw = provider.complete_json(prompt)
                validate_object(adjudication, artifacts["adjudicator"]["schema"])
                raw_results.write(
                    json.dumps(
                        {
                            "record_id": record_id(record),
                            "role": "adjudicator",
                            "response": raw,
                        }
                    )
                    + "\n"
                )
                route, adjudication_gate = route_adjudicated(adjudication, config)
                role_gates["adjudicator"] = adjudication_gate

            result = {
                "record_id": record_id(record),
                "title": record.get("title", ""),
                "round_a": answers,
                "gates": role_gates,
                "adjudication": adjudication,
                "final_decision": route,
            }
            results.write(json.dumps(result, ensure_ascii=False) + "\n")
            counts[route] = counts.get(route, 0) + 1
            results.flush()
            raw_results.flush()

    write_manifest(
        output / "manifest.json",
        {
            "git_revision": git_revision(REPO_ROOT),
            "input_path": audit_input_path(input_path),
            "input_sha256": sha256_file(input_path),
            "model": provider.model,
            "provider_url": provider.url,
            "temperature": getattr(provider, "temperature", 0),
            "gate_config_sha256": sha256_file(
                config_path or REPO_ROOT / "protocol" / "screening" / "gate_config.json"
            ),
            "artifacts": {
                role: {
                    key: value
                    for key, value in artifact.items()
                    if key not in {"prompt", "schema"}
                }
                for role, artifact in artifacts.items()
            },
            "record_count": len(records),
            "decision_counts": counts,
        },
    )
    return counts


class RoleExecutionError(RuntimeError):
    def __init__(self, role: str, errors: list[str]) -> None:
        self.role = role
        self.errors = errors
        super().__init__(f"{role} failed after {len(errors)} attempts: {errors[-1]}")


class ContractConsensusError(RuntimeError):
    def __init__(self, role: str, unresolved_fields: list[str]) -> None:
        self.role = role
        self.unresolved_fields = unresolved_fields
        super().__init__(
            f"{role} has no strict verifier majority for "
            f"{', '.join(unresolved_fields)}"
        )


def run_stage_screening(
    input_path: str | Path,
    output_dir: str | Path,
    provider: OpenAICompatibleProvider,
    stage: str = "title_abstract",
    suite_config_path: str | Path | None = None,
    limit: int | None = None,
    resume: bool = False,
    record_ids: set[str] | None = None,
) -> dict[str, int]:
    config_path = Path(suite_config_path or DEFAULT_SUITE_CONFIG).resolve()
    suite, stage_config = load_stage_config(stage, config_path)
    records: list[dict[str, Any]]
    if stage_config["input_format"] == "csv":
        records = list(read_records(input_path))
    elif stage_config["input_format"] == "jsonl":
        records = read_jsonl_records(input_path)
    else:
        raise ValueError(f"Unsupported input format: {stage_config['input_format']}")
    if record_ids:
        records = [
            record
            for record in records
            if _record_matches_filter(record, record_ids)
        ]
        found_ids = {record_id(record) for record in records}
        missing_ids = sorted(record_ids - found_ids)
        if missing_ids:
            raise ValueError(f"Requested record IDs not found: {', '.join(missing_ids)}")
    if limit is not None:
        records = records[:limit]

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "screening_results.jsonl"
    raw_path = output / "raw_provider_responses.jsonl"
    completed_ids = _completed_record_ids(result_path) if resume else set()
    mode = "a" if resume else "w"
    artifacts = _load_stage_artifacts(stage_config)
    counts = _existing_decision_counts(result_path) if resume else {}
    processed_now = 0

    with result_path.open(mode, encoding="utf-8") as results, raw_path.open(
        mode, encoding="utf-8"
    ) as raw_results:
        for position, source_record in enumerate(records, start=1):
            record = source_record
            try:
                identifier = record_id(record)
            except ValueError as error:
                identifier = f"invalid-{stage}-record-{position:06d}"
                record = {**record, "record_id": identifier, "_input_error": str(error)}
            if identifier in completed_ids:
                continue
            processed_now += 1
            try:
                if record.get("_input_error"):
                    result = _manual_review_result(
                        record,
                        stage,
                        "invalid_input_record",
                        {"error": str(record["_input_error"])},
                    )
                elif not str(record.get("abstract", "")).strip():
                    result = _manual_review_result(
                        record,
                        stage,
                        "missing_abstract",
                    )
                elif (
                    stage == "title_abstract"
                    and len(str(record.get("abstract", "")))
                    > stage_config["max_input_abstract_chars"]
                ):
                    result = _manual_review_result(
                        record,
                        stage,
                        "oversized_abstract_metadata",
                        {
                            "abstract_chars": len(str(record.get("abstract", ""))),
                            "maximum": stage_config["max_input_abstract_chars"],
                        },
                    )
                elif stage == "title_abstract":
                    metadata_issue = title_abstract_metadata_issue(record)
                    if metadata_issue:
                        reason, details = metadata_issue
                        result = _manual_review_result(
                            record,
                            stage,
                            reason,
                            details,
                        )
                    else:
                        result = _process_title_abstract_record(
                            record,
                            stage_config,
                            artifacts,
                            provider,
                            raw_results,
                            suite["runtime"]["max_retries"],
                        )
                elif stage == "full_text":
                    result = _process_full_text_record(
                        record,
                        stage_config,
                        artifacts,
                        provider,
                        raw_results,
                        suite["runtime"]["max_retries"],
                    )
                else:
                    raise ValueError(f"Unsupported stage: {stage}")
            except RoleExecutionError as error:
                result = _manual_review_result(
                    record,
                    stage,
                    "role_execution_failed",
                    {"role": error.role, "errors": error.errors},
                )
            except ContractConsensusError as error:
                result = _manual_review_result(
                    record,
                    stage,
                    "contract_consensus_unresolved",
                    {
                        "role": error.role,
                        "fields": error.unresolved_fields,
                    },
                )
            except (ValueError, EvidenceReferenceError) as error:
                result = _manual_review_result(
                    record,
                    stage,
                    "record_validation_failed",
                    {"error": str(error)},
                )

            results.write(json.dumps(result, ensure_ascii=False) + "\n")
            results.flush()
            decision = str(result["final_decision"])
            counts[decision] = counts.get(decision, 0) + 1

    write_manifest(
        output / "manifest.json",
        {
            "git_revision": git_revision(REPO_ROOT),
            "suite_id": suite["suite_id"],
            "suite_version": suite["suite_version"],
            "stage": stage,
            "suite_config_path": str(config_path.relative_to(REPO_ROOT)),
            "suite_config_sha256": sha256_file(config_path),
            "input_path": audit_input_path(input_path),
            "input_sha256": sha256_file(input_path),
            "model": provider.model,
            "provider_url": provider.url,
            "runtime": _provider_runtime(provider),
            "artifacts": _manifest_artifacts(artifacts),
            "resume": resume,
            "record_ids": sorted(record_ids or []),
            "input_record_count": len(records),
            "processed_now": processed_now,
            "decision_counts": counts,
        },
    )
    return counts


def _record_matches_filter(record: dict[str, Any], record_ids: set[str]) -> bool:
    try:
        return record_id(record) in record_ids
    except ValueError:
        return False


def _process_title_abstract_record(
    record: dict[str, Any],
    stage_config: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    provider: OpenAICompatibleProvider,
    raw_results: Any,
    max_retries: int,
) -> dict[str, Any]:
    verification_config = stage_config.get("contract_verification", {})
    verification_mode = verification_config.get("mode")
    draft_answers: dict[str, dict[str, Any]] = {}
    verified_answers: dict[str, dict[str, Any]] = {}
    verification_runs: dict[str, list[dict[str, Any]]] = {}
    consensus_audit: dict[str, dict[str, Any]] = {}
    per_role_verification = verification_mode in {
        "per_role_second_pass",
        "per_role_consensus",
    }
    for role in stage_config["roles"]:
        if (
            role == "directional_effect_reviewer"
            and stage_config.get("directional_family_precedence")
            == "action_then_effect"
            and draft_answers.get("directional_result_reviewer", {}).get(
                "directional_action_signal"
            )
            == "yes"
        ):
            draft_answers[role] = {
                "directional_effect_signal": "not_assessed",
                "evidence_spans": [],
                "uncertainty_reason": "",
                "concise_rationale": (
                    "Not assessed because the higher-precedence directional "
                    "action criterion was positive."
                ),
            }
            raw_results.write(
                json.dumps(
                    {
                        "record_id": record_id(record),
                        "role": role,
                        "attempt": 0,
                        "status": "not_assessed",
                        "reason": "directional_action_signal_yes",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            raw_results.flush()
            continue
        prompt = render_prompt(artifacts[role]["prompt"], record)
        draft_answers[role] = _call_role(
            provider,
            role,
            prompt,
            artifacts[role]["schema"],
            record_id(record),
            raw_results,
            max_retries,
            post_validate=_title_model_role_validator(role),
            phase="draft_round_a",
        )
        if verification_config.get("enabled") and per_role_verification:
            verifier_role = f"{role}_contract_verifier"
            repeat_count = (
                int(verification_config.get("repeats", 3))
                if verification_mode == "per_role_consensus"
                else 1
            )
            role_votes: list[dict[str, Any]] = []
            for repeat_index in range(1, repeat_count + 1):
                verifier_extra = {}
                if (
                    verification_config.get("verifier_context")
                    != "source_record_only_no_specialist_draft"
                ):
                    verifier_extra["DRAFT_REVIEW"] = json.dumps(
                        draft_answers[role],
                        ensure_ascii=False,
                    )
                verifier_prompt = render_prompt(
                    artifacts[verifier_role]["prompt"],
                    record,
                    verifier_extra,
                )
                role_votes.append(
                    _call_role(
                        provider,
                        verifier_role,
                        verifier_prompt,
                        artifacts[verifier_role]["schema"],
                        record_id(record),
                        raw_results,
                        max_retries,
                        post_validate=_title_model_role_validator(role),
                        phase="contract_verification",
                        repeat_index=repeat_index,
                    )
                )
            verification_runs[role] = role_votes
            if verification_mode == "per_role_consensus":
                no_majority_fallback = (
                    "unclear"
                    if verification_config.get("aggregation")
                    == "strict_field_majority_else_unclear"
                    else None
                )
                unanimous_required_values = set(
                    verification_config.get(
                        "exclusionary_values_require_unanimity",
                        [],
                    )
                )
                verified_answers[role], consensus_audit[role] = (
                    _title_role_consensus(
                        role,
                        role_votes,
                        no_majority_fallback=no_majority_fallback,
                        unanimous_required_values=unanimous_required_values,
                    )
                )
            else:
                verified_answers[role] = role_votes[0]

    verification: dict[str, Any] | None = None
    answers = (
        verified_answers
        if per_role_verification
        else draft_answers
    )
    contract_corrections: list[str] = []
    if verification_config.get("enabled") and per_role_verification:
        verification = verified_answers
        contract_corrections = _title_contract_corrections(
            draft_answers,
            answers,
        )
    elif verification_config.get("enabled"):
        extra = {
            "SCOPE_DRAFT": json.dumps(
                draft_answers["scope_reviewer"], ensure_ascii=False
            ),
            "CAUSAL_DRAFT": json.dumps(
                draft_answers["causal_design_reviewer"], ensure_ascii=False
            ),
            "DIRECTIONAL_DRAFT": json.dumps(
                draft_answers["directional_result_reviewer"], ensure_ascii=False
            ),
        }
        prompt = render_prompt(
            artifacts["contract_verifier"]["prompt"],
            record,
            extra,
        )
        verification = _call_role(
            provider,
            "contract_verifier",
            prompt,
            artifacts["contract_verifier"]["schema"],
            record_id(record),
            raw_results,
            max_retries,
            phase="contract_verification",
        )
        answers = _title_answers_from_contract_verification(verification)
        contract_corrections = _title_contract_corrections(
            draft_answers,
            answers,
        )
        verification["corrected_draft_fields"] = contract_corrections

    consistency_rules = _normalize_title_round_a(answers, stage_config)
    route, role_gates = route_round_a(answers, stage_config)
    adjudication = None
    selected = _merge_answers(*answers.values())
    scope_resolution = _title_scope_resolution(answers["scope_reviewer"])
    if (
        route == "adjudicate"
        and scope_resolution == "unresolved"
        and stage_config.get("unresolved_upstream_scope_route")
        == "seek_full_text"
    ):
        route = "seek_full_text"
        role_gates["scope_short_circuit"] = "seek_full_text"
        consistency_rules.append(
            "unresolved_upstream_scope_routes_directly_to_full_text"
        )
    elif route == "adjudicate":
        causal_review = _merge_answers(
            *(
                answer
                for role, answer in answers.items()
                if role != "scope_reviewer"
            )
        )
        extra = {
            "SCOPE_REVIEW": json.dumps(answers["scope_reviewer"], ensure_ascii=False),
            "CAUSAL_REVIEW": json.dumps(causal_review, ensure_ascii=False),
        }
        prompt = render_prompt(artifacts["adjudicator"]["prompt"], record, extra)
        adjudication = _call_role(
            provider,
            "adjudicator",
            prompt,
            artifacts["adjudicator"]["schema"],
            record_id(record),
            raw_results,
            max_retries,
            phase="selective_adjudication",
        )
        consistency_rules.extend(
            _normalize_title_adjudication(adjudication, stage_config)
        )
        route, adjudicator_gate = route_adjudicated(adjudication, stage_config)
        role_gates["adjudicator"] = adjudicator_gate
        selected = adjudication
        if adjudication.get("resolution_status") == "conflict_unresolved":
            route = "manual_review"

    return {
        "record_id": record_id(record),
        "stage": "title_abstract",
        "title": record.get("title", ""),
        "draft_round_a": draft_answers,
        "contract_verification_runs": (
            verification_runs if verification_runs else None
        ),
        "contract_consensus": consensus_audit if consensus_audit else None,
        "contract_verification": verification,
        "contract_corrections": contract_corrections,
        "round_a": answers,
        "gates": role_gates,
        "adjudication": adjudication,
        "selected_criteria": selected,
        "consistency_rules_applied": consistency_rules,
        "final_decision": route,
        "final_exclusion_code": derive_exclusion_code(selected) if route == "exclude" else "none",
    }


def _title_answers_from_contract_verification(
    verification: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    evidence = list(verification.get("evidence_spans", []))
    rationale = str(verification.get("concise_rationale", ""))
    uncertainty = str(verification.get("uncertainty_reason", ""))
    return {
        "scope_reviewer": {
            "report_type": verification["report_type"],
            "bio_health_scope": verification["bio_health_scope"],
            "aging_process_relevance": verification["aging_process_relevance"],
            "multiomics_status": verification["multiomics_status"],
            "omics_layers": [],
            "evidence_spans": evidence,
            "boundary_case": verification["boundary_case"],
            "uncertainty_reason": uncertainty,
            "concise_rationale": rationale,
        },
        "causal_design_reviewer": {
            "completed_current_report": verification["completed_current_report"],
            "genetic_instrument_signal": verification["genetic_instrument_signal"],
            "manipulation_design_signal": verification["manipulation_design_signal"],
            "directed_model_signal": verification["directed_model_signal"],
            "evidence_spans": evidence,
            "uncertainty_reason": uncertainty,
            "concise_rationale": rationale,
        },
        "directional_result_reviewer": {
            "directional_language_signal": verification[
                "directional_language_signal"
            ],
            "evidence_spans": evidence,
            "concise_rationale": rationale,
        },
    }


def _title_contract_corrections(
    drafts: dict[str, dict[str, Any]],
    verified: dict[str, dict[str, Any]],
) -> list[str]:
    corrections: list[str] = []
    for role, fields in _TITLE_VERIFIED_FIELDS.items():
        for field in fields:
            if drafts.get(role, {}).get(field) != verified.get(role, {}).get(field):
                corrections.append(f"{role}.{field}")
    return corrections


def _title_role_consensus(
    role: str,
    votes: list[dict[str, Any]],
    no_majority_fallback: str | None = None,
    unanimous_required_values: set[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if role not in _TITLE_VERIFIED_FIELDS:
        raise ValueError(f"Unsupported title consensus role: {role}")
    if len(votes) < 3 or len(votes) % 2 == 0:
        raise ValueError("Verifier consensus requires an odd number of at least 3 votes")

    consensus = dict(votes[0])
    field_audit: dict[str, Any] = {}
    unresolved: list[str] = []
    for field in _TITLE_VERIFIED_FIELDS[role]:
        values = [str(vote[field]) for vote in votes]
        counts = Counter(values)
        selected, count = counts.most_common(1)[0]
        has_majority = count > len(votes) // 2
        nonunanimous_exclusion = (
            has_majority
            and selected in (unanimous_required_values or set())
            and count < len(votes)
            and field in _TITLE_UNCLEAR_CONSENSUS_FIELDS
        )
        field_audit[field] = {
            "votes": values,
            "counts": dict(sorted(counts.items())),
            "selected": (
                "unclear"
                if nonunanimous_exclusion
                else selected if has_majority else None
            ),
            "unanimous": count == len(votes),
            "selection_basis": (
                "nonunanimous_exclusion_to_unclear"
                if nonunanimous_exclusion
                else "strict_majority" if has_majority else None
            ),
        }
        if nonunanimous_exclusion:
            consensus[field] = "unclear"
        elif has_majority:
            consensus[field] = selected
        elif (
            no_majority_fallback == "unclear"
            and field in _TITLE_UNCLEAR_CONSENSUS_FIELDS
        ):
            consensus[field] = "unclear"
            field_audit[field]["selected"] = "unclear"
            field_audit[field]["selection_basis"] = (
                "no_majority_categorical_unclear"
            )
        else:
            unresolved.append(field)

    if unresolved:
        raise ContractConsensusError(role, unresolved)

    evidence: list[dict[str, Any]] = []
    seen_evidence: set[str] = set()
    for vote in votes:
        for item in vote.get("evidence_spans", []):
            key = json.dumps(item, ensure_ascii=False, sort_keys=True)
            if key not in seen_evidence:
                evidence.append(item)
                seen_evidence.add(key)
    consensus["evidence_spans"] = evidence
    return consensus, {
        "vote_count": len(votes),
        "all_fields_unanimous": all(
            item["unanimous"] for item in field_audit.values()
        ),
        "fields": field_audit,
    }


def _title_model_role_validator(
    role: str,
) -> Callable[[dict[str, Any]], None] | None:
    fields = _TITLE_VERIFIED_FIELDS.get(role)
    if role == "scope_reviewer" or fields is None:
        return None

    def validate(answer: dict[str, Any]) -> None:
        invalid = [field for field in fields if answer.get(field) == "not_assessed"]
        if invalid:
            raise ValueError(
                "not_assessed is reserved for Python scope consistency: "
                + ", ".join(invalid)
            )

    return validate


def _normalize_title_round_a(
    answers: dict[str, dict[str, Any]],
    stage_config: dict[str, Any],
) -> list[str]:
    rules: list[str] = []
    scope = answers["scope_reviewer"]
    causal = answers["causal_design_reviewer"]
    status_contract = stage_config.get("identification_status_contract")
    defer_layers = stage_config.get("title_layer_inventory") == "deferred_to_full_text"
    if stage_config.get("title_scope_sequential_short_circuit") and (
        _normalize_title_scope_sequence(scope)
    ):
        rules.append("downstream_scope_criteria_normalized_from_prisma_sequence")
    if _normalize_title_multiomics(
        scope,
        defer_inventory=defer_layers,
        sequential_short_circuit=stage_config.get(
            "title_scope_sequential_short_circuit", False
        ),
    ):
        rules.append(
            "multiomics_status_normalized_from_scope_short_circuit"
            if defer_layers
            else "multiomics_status_normalized_from_used_layer_count"
        )
    if defer_layers:
        rules.append("title_omics_layer_inventory_deferred_to_full_text")

    scope_resolution = _title_scope_resolution(scope)
    if (
        scope_resolution in {"excluded", "unresolved"}
        and status_contract == "causal_candidate_design_bundle_v7"
        and stage_config.get("causal_short_circuit_after_scope")
        == "clear_exclusion_or_unresolved"
    ):
        directional = answers["directional_result_reviewer"]
        causal["completed_current_report"] = (
            "unclear" if scope_resolution == "unresolved" else "not_assessed"
        )
        for field in (
            "genetic_instrument_signal",
            "manipulation_design_signal",
            "directed_model_signal",
        ):
            causal[field] = "not_assessed"
        directional["directional_language_signal"] = "not_assessed"
        rules.append(
            f"{scope_resolution}_scope_short_circuits_causal_criteria"
        )

    if status_contract == "causal_candidate_design_bundle_v7":
        design_fields = (
            "genetic_instrument_signal",
            "manipulation_design_signal",
            "directed_model_signal",
        )
        directional = answers["directional_result_reviewer"]
        if causal.get("completed_current_report") == "no":
            for field in design_fields:
                causal[field] = "no"
            directional["directional_language_signal"] = "no"
            rules.append("incomplete_report_implies_no_applied_or_directional_signal")
        causal["applied_design_signal"] = _logical_any_signal(
            causal[field] for field in design_fields
        )
        directional["directional_result_signal"] = directional[
            "directional_language_signal"
        ]
        causal["directional_result_signal"] = directional[
            "directional_result_signal"
        ]
        rules.extend(
            [
                "applied_design_signal_derived_from_atomic_design_signals",
                "directional_result_signal_copied_from_language_specialist",
            ]
        )
    elif status_contract == "causal_candidate_atomic_bundle_v6":
        design_fields = (
            "genetic_instrument_signal",
            "manipulation_design_signal",
            "directed_model_signal",
        )
        directional_fields = (
            "directional_action_signal",
            "directional_effect_signal",
        )
        if causal.get("completed_current_report") == "no":
            for field in (*design_fields, *directional_fields):
                causal[field] = "no"
            rules.append("incomplete_report_implies_no_applied_or_directional_signal")
        elif causal.get("directional_action_signal") == "yes":
            causal["directional_effect_signal"] = "not_assessed"
            rules.append(
                "directional_effect_not_assessed_after_positive_action_signal"
            )
        elif causal.get("directional_effect_signal") == "not_assessed":
            causal["directional_effect_signal"] = "no"
            rules.append(
                "directional_effect_assessed_when_action_signal_not_positive"
            )
        causal["applied_design_signal"] = _logical_any_signal(
            causal[field] for field in design_fields
        )
        causal["directional_result_signal"] = _logical_any_signal(
            causal[field] for field in directional_fields
        )
        rules.extend(
            [
                "applied_design_signal_derived_from_atomic_design_signals",
                "directional_result_signal_derived_from_ordered_directional_signals",
            ]
        )
    elif status_contract == "causal_candidate_families_v5":
        design_signals = {
            "genetic_instrument_signal": answers["genetic_instrument_reviewer"][
                "genetic_instrument_signal"
            ],
            "manipulation_design_signal": answers["manipulation_reviewer"][
                "manipulation_design_signal"
            ],
            "directed_model_signal": answers["directed_model_reviewer"][
                "directed_model_signal"
            ],
        }
        directional_signals = {
            "directional_action_signal": answers["directional_result_reviewer"][
                "directional_action_signal"
            ],
            "directional_effect_signal": answers["directional_effect_reviewer"][
                "directional_effect_signal"
            ],
        }
        if causal.get("completed_current_report") == "no":
            design_signals = dict.fromkeys(design_signals, "no")
            directional_signals = dict.fromkeys(directional_signals, "no")
            rules.append("incomplete_report_implies_no_applied_or_directional_signal")
        for field, value in design_signals.items():
            role = _TITLE_DESIGN_SIGNAL_ROLES[field]
            answers[role][field] = value
        for field, value in directional_signals.items():
            role = _TITLE_DIRECTIONAL_SIGNAL_ROLES[field]
            answers[role][field] = value
        causal["applied_design_signal"] = _logical_any_signal(
            design_signals.values()
        )
        directional = answers["directional_result_reviewer"]
        directional["directional_result_signal"] = _logical_any_signal(
            directional_signals.values()
        )
        causal["directional_result_signal"] = directional[
            "directional_result_signal"
        ]
        rules.extend(
            [
                "applied_design_signal_derived_from_design_family_signals",
                "directional_result_signal_derived_from_directional_family_signals",
            ]
        )
    elif status_contract == "causal_candidate_split_v4":
        directional = answers["directional_result_reviewer"]
        causal["directional_result_signal"] = directional[
            "directional_result_signal"
        ]
        rules.append("directional_result_signal_merged_from_specialist")
    if _derive_title_identification_status(
        causal,
        status_contract=status_contract,
    ):
        rules.append(
            "causal_signals_and_status_derived_from_categorical_bases"
            if status_contract == "causal_candidate_basis_v3"
            else (
                "identification_status_derived_from_split_causal_signals"
                if status_contract
                in {
                    "causal_candidate_split_v4",
                    "causal_candidate_families_v5",
                }
                else "identification_status_derived_from_atomic_causal_signals"
            )
        )
    if stage_config.get("prisma_scope_short_circuit_round_a") and (
        scope.get("aging_process_relevance") == "no"
        or scope.get("report_type")
        in {
            "nonempirical",
            "review_editorial",
            "protocol",
            "methods_only",
            "resource",
        }
    ):
        causal["identification_status"] = "noncausal"
        rules.append("ineligible_scope_implies_no_relevant_causal_design")
    if _normalize_title_design(causal, status_contract=status_contract):
        rules.extend(
            [
                "primary_design_family_normalized_from_identification_status",
                "design_role_derived_from_identification_status",
                "legacy_design_families_derived_from_primary_family",
            ]
        )
    else:
        rules.append(
            "title_effect_strength_and_design_subtyping_deferred_to_full_text"
            if status_contract
            else "title_design_subtyping_deferred_to_full_text"
        )
    return rules


def _title_scope_resolution(scope: dict[str, Any]) -> str:
    report_type = scope.get("report_type")
    if report_type != "empirical_primary":
        return "unresolved" if report_type == "unclear" else "excluded"

    for field in (
        "bio_health_scope",
        "aging_process_relevance",
        "multiomics_status",
    ):
        value = scope.get(field)
        if value != "yes":
            return "unresolved" if value in {"unclear", "not_assessed"} else "excluded"
    return "eligible"


def _normalize_title_adjudication(
    answer: dict[str, Any],
    stage_config: dict[str, Any],
) -> list[str]:
    rules: list[str] = []
    defer_layers = stage_config.get("title_layer_inventory") == "deferred_to_full_text"
    if stage_config.get("title_scope_sequential_short_circuit") and (
        _normalize_title_scope_sequence(answer)
    ):
        rules.append("downstream_scope_criteria_normalized_from_prisma_sequence")
    if _normalize_title_multiomics(
        answer,
        defer_inventory=defer_layers,
        sequential_short_circuit=stage_config.get(
            "title_scope_sequential_short_circuit", False
        ),
    ):
        rules.append(
            "multiomics_status_normalized_from_scope_short_circuit"
            if defer_layers
            else "multiomics_status_normalized_from_used_layer_count"
        )
    if defer_layers:
        rules.append("title_omics_layer_inventory_deferred_to_full_text")
    status_contract = stage_config.get("identification_status_contract")
    if _derive_title_identification_status(
        answer,
        status_contract=status_contract,
    ):
        rules.append(
            "causal_signals_and_status_derived_from_categorical_bases"
            if status_contract == "causal_candidate_basis_v3"
            else (
                "identification_status_derived_from_split_causal_signals"
                if status_contract
                in {
                    "causal_candidate_split_v4",
                    "causal_candidate_families_v5",
                }
                else "identification_status_derived_from_atomic_causal_signals"
            )
        )
    if answer.get("aging_process_relevance") == "no" or answer.get(
        "report_type"
    ) in {"nonempirical", "review_editorial", "protocol", "methods_only", "resource"}:
        answer["identification_status"] = "noncausal"
        if "primary_design_family" in answer:
            answer.update(
                {
                    "causal_claim_present": "no",
                    "primary_design_family": "none",
                    "design_role": "mentioned_only",
                }
            )
        rules.append("ineligible_scope_implies_no_relevant_causal_design")
    if _normalize_title_design(answer, status_contract=status_contract):
        rules.extend(
            [
                "primary_design_family_normalized_from_identification_status",
                "design_role_derived_from_identification_status",
                "legacy_design_families_derived_from_primary_family",
            ]
        )
    else:
        rules.append(
            "title_effect_strength_and_design_subtyping_deferred_to_full_text"
            if status_contract
            else "title_design_subtyping_deferred_to_full_text"
        )
    return rules


def _derive_title_identification_status(
    answer: dict[str, Any],
    *,
    status_contract: str | None,
) -> bool:
    if status_contract not in {
        "causal_candidate_atomic_v2",
        "causal_candidate_basis_v3",
        "causal_candidate_split_v4",
        "causal_candidate_families_v5",
        "causal_candidate_atomic_bundle_v6",
        "causal_candidate_design_bundle_v7",
    }:
        return False

    previous = (
        answer.get("applied_design_signal"),
        answer.get("directional_result_signal"),
        answer.get("identification_status"),
    )
    completed = answer.get("completed_current_report", "unclear")
    if status_contract == "causal_candidate_basis_v3":
        applied = _signal_from_basis(answer.get("applied_design_basis"))
        directional = _signal_from_basis(answer.get("directional_result_basis"))
        answer["applied_design_signal"] = applied
        answer["directional_result_signal"] = directional
    else:
        applied = answer.get("applied_design_signal", "unclear")
        directional = answer.get("directional_result_signal", "unclear")

    if completed == "no":
        status = "noncausal"
    elif applied == "yes" or directional == "yes":
        status = "causal_candidate"
    elif "unclear" in {completed, applied, directional}:
        status = "unclear"
    else:
        status = "noncausal"

    answer["identification_status"] = status
    current = (
        answer.get("applied_design_signal"),
        answer.get("directional_result_signal"),
        answer.get("identification_status"),
    )
    return current != previous


_TITLE_DESIGN_SIGNAL_ROLES = {
    "genetic_instrument_signal": "genetic_instrument_reviewer",
    "manipulation_design_signal": "manipulation_reviewer",
    "directed_model_signal": "directed_model_reviewer",
}

_TITLE_DIRECTIONAL_SIGNAL_ROLES = {
    "directional_action_signal": "directional_result_reviewer",
    "directional_effect_signal": "directional_effect_reviewer",
}

_TITLE_VERIFIED_FIELDS = {
    "scope_reviewer": (
        "report_type",
        "bio_health_scope",
        "aging_process_relevance",
        "multiomics_status",
    ),
    "causal_design_reviewer": (
        "completed_current_report",
        "genetic_instrument_signal",
        "manipulation_design_signal",
        "directed_model_signal",
    ),
    "directional_result_reviewer": ("directional_language_signal",),
}

_TITLE_UNCLEAR_CONSENSUS_FIELDS = {
    field
    for role in ("scope_reviewer", "causal_design_reviewer")
    for field in _TITLE_VERIFIED_FIELDS[role]
}


def _logical_any_signal(values: Any) -> str:
    signals = set(values)
    if "yes" in signals:
        return "yes"
    if "unclear" in signals:
        return "unclear"
    return "no"


def _signal_from_basis(value: Any) -> str:
    if value == "none":
        return "no"
    if value in {None, "unclear"}:
        return "unclear"
    return "yes"


def _normalize_title_design(
    answer: dict[str, Any],
    *,
    status_contract: str | None = None,
) -> bool:
    status = str(answer.get("identification_status", "unclear"))
    if status in {"association_only", "no_relevant_design"}:
        status = "noncausal"
        answer["identification_status"] = status
    if status_contract == "causal_or_directed_v1" and status in {
        "identified",
        "hypothesis_only",
    }:
        status = "causal_or_directed"
        answer["identification_status"] = status
    if status_contract == "causal_candidate_v1" and status in {
        "identified",
        "hypothesis_only",
        "causal_or_directed",
    }:
        status = "causal_candidate"
        answer["identification_status"] = status
    if "primary_design_family" not in answer:
        return False

    role_by_status = {
        "identified": "primary_identification",
        "hypothesis_only": "hypothesis_generation",
        "noncausal": "mentioned_only",
        "association_only": "mentioned_only",
        "no_relevant_design": "mentioned_only",
        "unclear": "unclear",
    }
    family = str(answer.get("primary_design_family", "unclear"))
    if status in {"noncausal", "association_only", "no_relevant_design"}:
        family = "none"
    elif status == "unclear":
        family = "unclear"
    elif status == "hypothesis_only" and family in {"none", "unclear"}:
        family = "other"
    elif status == "identified" and family in {"none", "unclear"}:
        status = "unclear"
        family = "unclear"
        answer["identification_status"] = status
    claim_by_status = {
        "identified": "yes",
        "hypothesis_only": "yes",
        "noncausal": "no",
        "association_only": "no",
        "no_relevant_design": "no",
        "unclear": "unclear",
    }
    answer["causal_claim_present"] = claim_by_status[status]
    answer["primary_design_family"] = family
    answer["design_role"] = role_by_status[status]
    answer["design_families"] = [] if family in {"none", "unclear"} else [family]
    return True


def _normalize_title_multiomics(
    answer: dict[str, Any],
    *,
    defer_inventory: bool = False,
    sequential_short_circuit: bool = False,
) -> bool:
    status = answer.get("multiomics_status")
    failed_scope = answer.get("aging_process_relevance") == "no" or answer.get(
        "report_type"
    ) in {"nonempirical", "review_editorial", "protocol", "methods_only", "resource"}
    unresolved_or_failed_scope = (
        answer.get("report_type") != "empirical_primary"
        or answer.get("bio_health_scope") != "yes"
        or answer.get("aging_process_relevance") != "yes"
    )
    if failed_scope or (sequential_short_circuit and unresolved_or_failed_scope):
        answer["multiomics_status"] = "not_assessed"
        answer["omics_layers"] = []
        return status != "not_assessed"
    if defer_inventory:
        answer["omics_layers"] = []
        return False
    layers = answer.get("omics_layers", [])
    used_layers = {
        item.get("layer")
        for item in layers
        if isinstance(item, dict)
        and (
            "use_status" not in item
            or item.get("use_status")
            in {"measured_in_study", "external_dataset_analyzed"}
        )
    }
    used_layers.discard(None)
    normalized = status
    if len(used_layers) >= 2:
        normalized = "yes"
    elif status == "yes":
        normalized = "unclear"
    answer["multiomics_status"] = normalized
    return normalized != status


def _normalize_title_scope_sequence(answer: dict[str, Any]) -> bool:
    original = (
        answer.get("bio_health_scope"),
        answer.get("aging_process_relevance"),
        answer.get("multiomics_status"),
    )
    if answer.get("report_type") != "empirical_primary":
        answer["bio_health_scope"] = "not_assessed"
        answer["aging_process_relevance"] = "not_assessed"
        answer["multiomics_status"] = "not_assessed"
        answer["omics_layers"] = []
    elif answer.get("bio_health_scope") != "yes":
        answer["aging_process_relevance"] = "not_assessed"
        answer["multiomics_status"] = "not_assessed"
        answer["omics_layers"] = []
    elif answer.get("aging_process_relevance") != "yes":
        answer["multiomics_status"] = "not_assessed"
        answer["omics_layers"] = []
    normalized = (
        answer.get("bio_health_scope"),
        answer.get("aging_process_relevance"),
        answer.get("multiomics_status"),
    )
    return normalized != original


def _process_full_text_record(
    record: dict[str, Any],
    stage_config: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    provider: OpenAICompatibleProvider,
    raw_results: Any,
    max_retries: int,
) -> dict[str, Any]:
    sections = record.get("sections")
    if not isinstance(sections, list) or not sections:
        return _manual_review_result(record, "full_text", "missing_full_text_sections")
    valid_section_ids = _validate_sections(sections)
    selector_prompt = render_prompt(
        artifacts["section_selector"]["prompt"],
        record,
        {"SECTION_CATALOG": _format_sections(sections)},
    )
    selection = _call_role(
        provider,
        "section_selector",
        selector_prompt,
        artifacts["section_selector"]["schema"],
        record_id(record),
        raw_results,
        max_retries,
        lambda answer: validate_evidence_references(answer, valid_section_ids),
    )
    if selection["coverage_status"] != "sufficient":
        return _manual_review_result(
            record,
            "full_text",
            "insufficient_selected_full_text",
            {"section_selection": selection},
        )

    selected_ids = {
        item["section_id"] for item in selection["selected_sections"]
    }
    selected_sections = [
        section for section in sections if section["section_id"] in selected_ids
    ]
    selected_context = _format_sections(selected_sections)
    answers: dict[str, dict[str, Any]] = {}

    eligibility_prompt = render_prompt(
        artifacts["eligibility_reviewer"]["prompt"],
        record,
        {"SELECTED_SECTIONS": selected_context},
    )
    answers["eligibility_reviewer"] = _call_role(
        provider,
        "eligibility_reviewer",
        eligibility_prompt,
        artifacts["eligibility_reviewer"]["schema"],
        record_id(record),
        raw_results,
        max_retries,
        lambda answer: validate_evidence_references(answer, selected_ids),
    )

    causal_prompt = render_prompt(
        artifacts["causal_evidence_reviewer"]["prompt"],
        record,
        {
            "SELECTED_SECTIONS": selected_context,
            "ELIGIBILITY_REVIEW": json.dumps(
                answers["eligibility_reviewer"], ensure_ascii=False
            ),
        },
    )
    answers["causal_evidence_reviewer"] = _call_role(
        provider,
        "causal_evidence_reviewer",
        causal_prompt,
        artifacts["causal_evidence_reviewer"]["schema"],
        record_id(record),
        raw_results,
        max_retries,
        lambda answer: validate_evidence_references(answer, selected_ids),
    )

    route, role_gates = route_round_a(answers, stage_config)
    adjudication = None
    selected = _merge_answers(*answers.values())
    if route == "adjudicate":
        prompt = render_prompt(
            artifacts["adjudicator"]["prompt"],
            record,
            {
                "SELECTED_SECTIONS": selected_context,
                "ELIGIBILITY_REVIEW": json.dumps(
                    answers["eligibility_reviewer"], ensure_ascii=False
                ),
                "CAUSAL_REVIEW": json.dumps(
                    answers["causal_evidence_reviewer"], ensure_ascii=False
                ),
            },
        )
        adjudication = _call_role(
            provider,
            "adjudicator",
            prompt,
            artifacts["adjudicator"]["schema"],
            record_id(record),
            raw_results,
            max_retries,
            lambda answer: validate_evidence_references(answer, selected_ids),
        )
        route, adjudicator_gate = route_adjudicated(adjudication, stage_config)
        role_gates["adjudicator"] = adjudicator_gate
        selected = adjudication

    grade = derive_evidence_level(selected)
    if route == "manual_review" or grade is None:
        final_decision = "manual_review"
        ledger_fields = None
        level = None
        label = "pending"
    else:
        level, label = grade
        final_decision = "assessed"
        ledger_fields = build_ledger_fields(selected, level, label)

    return {
        "record_id": record_id(record),
        "stage": "full_text",
        "title": record.get("title", ""),
        "section_selection": selection,
        "round_a": answers,
        "gates": role_gates,
        "adjudication": adjudication,
        "selected_criteria": selected,
        "causal_evidence_level": level,
        "final_study_label": label,
        "ledger_fields": ledger_fields,
        "final_exclusion_code": derive_exclusion_code(selected),
        "final_decision": final_decision,
    }


def _call_role(
    provider: OpenAICompatibleProvider,
    role: str,
    prompt: str,
    schema: dict[str, Any],
    identifier: str,
    raw_results: Any,
    max_retries: int,
    post_validate: Callable[[dict[str, Any]], None] | None = None,
    phase: str | None = None,
    repeat_index: int | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    for attempt in range(max_retries + 1):
        raw: Any | None = None
        attempt_prompt = prompt
        if attempt:
            attempt_prompt += (
                "\n\nCORRECTION: The previous response failed validation: "
                f"{errors[-1]}. Return a corrected JSON object only."
            )
        try:
            answer, raw = provider.complete_json(
                attempt_prompt,
                schema=schema,
                schema_name=role,
            )
            validate_object(answer, schema)
            if post_validate:
                post_validate(answer)
            audit_row = {
                "record_id": identifier,
                "role": role,
                "attempt": attempt + 1,
                "status": "ok",
                "response": raw,
            }
            if phase:
                audit_row["phase"] = phase
            if repeat_index is not None:
                audit_row["repeat_index"] = repeat_index
            raw_results.write(
                json.dumps(audit_row, ensure_ascii=False)
                + "\n"
            )
            raw_results.flush()
            return answer
        except (ProviderError, SchemaError, EvidenceReferenceError, ValueError) as error:
            errors.append(str(error))
            failed_response = raw
            if isinstance(error, ProviderError) and error.raw_response is not None:
                failed_response = error.raw_response
            audit_row = {
                "record_id": identifier,
                "role": role,
                "attempt": attempt + 1,
                "status": "error",
                "error": str(error),
            }
            if phase:
                audit_row["phase"] = phase
            if repeat_index is not None:
                audit_row["repeat_index"] = repeat_index
            if failed_response is not None:
                audit_row["response"] = failed_response
            raw_results.write(
                json.dumps(
                    audit_row,
                    ensure_ascii=False,
                )
                + "\n"
            )
            raw_results.flush()
    raise RoleExecutionError(role, errors)


def _load_stage_artifacts(stage_config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    role_configs: dict[str, dict[str, Any]] = dict(stage_config["roles"])
    role_configs["adjudicator"] = stage_config["adjudication"]
    verification_config = stage_config.get("contract_verification", {})
    if verification_config.get("mode") in {
        "per_role_second_pass",
        "per_role_consensus",
    }:
        for role, role_config in stage_config["roles"].items():
            role_configs[f"{role}_contract_verifier"] = {
                "prompt": role_config["verification_prompt"],
                "schema": role_config["schema"],
            }
    elif verification_config.get("enabled"):
        role_configs["contract_verifier"] = stage_config["contract_verification"]
    if "section_selector" in stage_config:
        role_configs["section_selector"] = stage_config["section_selector"]

    artifacts: dict[str, dict[str, Any]] = {}
    for role, role_config in role_configs.items():
        prompt_path = resolve_suite_artifact(role_config["prompt"])
        schema_path = resolve_suite_artifact(role_config["schema"])
        artifacts[role] = {
            "prompt_path": prompt_path,
            "schema_path": schema_path,
            "prompt": prompt_path.read_text(encoding="utf-8"),
            "schema": load_json(schema_path),
        }
    return artifacts


def _manifest_artifacts(
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, dict[str, str]]:
    return {
        role: {
            "prompt_path": str(artifact["prompt_path"].relative_to(REPO_ROOT)),
            "prompt_sha256": sha256_file(artifact["prompt_path"]),
            "schema_path": str(artifact["schema_path"].relative_to(REPO_ROOT)),
            "schema_sha256": sha256_file(artifact["schema_path"]),
        }
        for role, artifact in artifacts.items()
    }


def _provider_runtime(provider: OpenAICompatibleProvider) -> dict[str, Any]:
    return {
        "api_protocol": getattr(provider, "api_protocol", "unknown"),
        "temperature": getattr(provider, "temperature", None),
        "top_p": getattr(provider, "top_p", None),
        "seed": getattr(provider, "seed", None),
        "n": getattr(provider, "n", None),
        "max_tokens": getattr(provider, "max_tokens", None),
        "response_format": getattr(provider, "response_format", None),
        "reasoning_effort": getattr(provider, "reasoning_effort", None),
        "text_verbosity": getattr(provider, "text_verbosity", None),
        "context_window": getattr(provider, "context_window", None),
        "codex_bin": getattr(provider, "codex_bin", None),
        "codex_cli_version": getattr(provider, "codex_version", None),
        "codex_timeout_seconds": getattr(provider, "timeout", None),
        "sandbox": getattr(provider, "sandbox", None),
        "approval_policy": getattr(provider, "approval_policy", None),
        "ephemeral": getattr(provider, "ephemeral", None),
        "ignore_user_config": getattr(provider, "ignore_user_config", None),
        "ignore_rules": getattr(provider, "ignore_rules", None),
        "isolated_home": getattr(provider, "isolated_home", None),
        "disabled_features": list(getattr(provider, "disabled_features", ())),
    }


def _merge_answers(*answers: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    evidence: list[dict[str, Any]] = []
    for answer in answers:
        for key, value in answer.items():
            if key == "evidence_spans":
                evidence.extend(value)
            elif key in {"uncertainty_reason", "concise_rationale"} and key in merged:
                merged[key] = " | ".join(filter(None, [str(merged[key]), str(value)]))
            else:
                merged[key] = value
    if evidence:
        merged["evidence_spans"] = evidence
    return merged


def _validate_sections(sections: list[Any]) -> set[str]:
    identifiers: list[str] = []
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ValueError(f"Section {index} is not an object")
        identifier = str(section.get("section_id", "")).strip()
        if not identifier:
            raise ValueError(f"Section {index} has no section_id")
        if not str(section.get("text", "")).strip():
            raise ValueError(f"Section {identifier} has no text")
        identifiers.append(identifier)
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Full-text section IDs must be unique")
    return set(identifiers)


def _format_sections(sections: list[dict[str, Any]]) -> str:
    blocks = []
    for section in sections:
        identifier = str(section["section_id"])
        heading = str(section.get("heading", ""))
        text = str(section.get("text", ""))
        blocks.append(
            f'<section id="{identifier}" heading="{heading}">\n{text}\n</section>'
        )
    return "\n\n".join(blocks)


def _manual_review_result(
    record: dict[str, Any],
    stage: str,
    reason: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "record_id": record_id(record),
        "stage": stage,
        "title": record.get("title", ""),
        "final_decision": "manual_review",
        "manual_review_reason": reason,
        "manual_review_details": details or {},
    }


def _completed_record_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as handle:
        return {
            str(row["record_id"])
            for line in handle
            if line.strip() and (row := json.loads(line))
        }


def _existing_decision_counts(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not path.exists():
        return counts
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            decision = str(json.loads(line)["final_decision"])
            counts[decision] = counts.get(decision, 0) + 1
    return counts
