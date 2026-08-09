from __future__ import annotations

import json
import re
from typing import Any

POSITIVE_CAUSAL_BASES = {
    "named_causal_effect_design",
    "formal_directed_hypothesis",
    "causal_analysis_method_unspecified",
}
NEGATIVE_CAUSAL_BASES = {
    "association_or_prediction_only",
    "causal_wording_only",
    "none",
}
FORMAL_HYPOTHESIS_FAMILIES = {
    "formal_mediation",
    "dag_scm",
    "sem",
    "bayesian_network",
    "causal_discovery_algorithm",
    "other_formal_causal_design",
}

SCOPE_DECISION_FIELDS = (
    "report_type",
    "bio_health_scope",
    "aging_process_relevance",
    "multiomics_evidence",
    "current_report_layer_use",
)
CAUSAL_DECISION_FIELDS = (
    "current_report_application",
    "causal_basis",
    "design_families",
    "causal_information_sufficiency",
)
FULL_TEXT_ELIGIBILITY_FIELDS = (
    "report_type",
    "empirical_primary",
    "bio_health_scope",
    "aging_process_relevance",
    "aging_role",
    "multiomics_status",
    "integration_mode",
    "relevant_causal_design",
    "full_text_sufficient",
    "first_failed_criterion",
)
FULL_TEXT_CAUSAL_FIELDS = (
    "causal_claim_present",
    "identification_status",
    "primary_design_family",
    "supporting_design_families",
    "design_role",
    "estimand_complete",
    "assumptions_assessable",
    "validation_strength",
)


def validate_title_evidence_spans(answer: dict[str, Any], record: dict[str, Any]) -> None:
    for item in answer.get("evidence_spans", []):
        source = item.get("source")
        quote = item.get("quote")
        if source not in {"title", "abstract"} or not isinstance(quote, str):
            raise ValueError("Invalid title/abstract evidence span")
        if quote not in str(record.get(source, "")):
            raise ValueError(f"Evidence quote is not an exact substring of {source}: {quote!r}")


def validate_scope_answer_consistency(answer: dict[str, Any]) -> None:
    evidence = answer.get("multiomics_evidence")
    layers = answer.get("layer_candidates", [])
    current_use = answer.get("current_report_layer_use")
    if evidence == "two_or_more_layers" and len(set(layers)) < 2:
        raise ValueError("two_or_more_layers requires at least two layer candidates")
    if evidence == "single_or_no_layer" and len(set(layers)) > 1:
        raise ValueError("single_or_no_layer cannot list multiple layer candidates")
    if evidence in {"explicit_multiomics", "two_or_more_layers"} and current_use == "no":
        raise ValueError("current multi-omics evidence conflicts with external-only use")


def validate_causal_answer_consistency(answer: dict[str, Any]) -> None:
    basis = answer.get("causal_basis")
    application = answer.get("current_report_application")
    families = set(answer.get("design_families", []))
    if basis in POSITIVE_CAUSAL_BASES and application != "yes":
        raise ValueError("a positive causal basis requires current-report application")
    if basis in NEGATIVE_CAUSAL_BASES and application != "no":
        raise ValueError("a negative causal basis requires no causal-method application")
    if basis == "named_causal_effect_design" and not families:
        raise ValueError("named_causal_effect_design requires a design family")
    if basis == "formal_directed_hypothesis" and not (families & FORMAL_HYPOTHESIS_FAMILIES):
        raise ValueError("formal_directed_hypothesis requires a directed-method family")
    if basis == "causal_analysis_method_unspecified" and families:
        raise ValueError("an unspecified method cannot have a named design family")
    if basis in NEGATIVE_CAUSAL_BASES | {"none", "unclear"} and families:
        raise ValueError("negative or unresolved causal basis cannot name design families")


def validate_full_text_evidence_spans(
    answer: dict[str, Any], sections: list[dict[str, Any]]
) -> None:
    section_text = {
        str(section["section_id"]): str(section.get("text", "")) for section in sections
    }
    for item in answer.get("evidence_spans", []):
        section_id = item.get("section_id")
        quote = item.get("quote")
        if section_id not in section_text or not isinstance(quote, str):
            raise ValueError("Invalid full-text evidence span")
        if quote not in section_text[section_id]:
            raise ValueError(
                f"Evidence quote is not an exact substring of section {section_id}: {quote!r}"
            )


def repair_full_text_evidence_spans(
    answer: dict[str, Any], sections: list[dict[str, Any]], minimum_words: int = 3
) -> list[dict[str, str]]:
    """Anchor near-verbatim model quotes without interpreting article content."""
    section_text = {
        str(section["section_id"]): str(section.get("text", "")) for section in sections
    }
    repairs: list[dict[str, str]] = []
    for item in answer.get("evidence_spans", []):
        section_id = item.get("section_id")
        quote = item.get("quote")
        text = section_text.get(str(section_id))
        if not text or not isinstance(quote, str) or quote in text:
            continue
        replacement = _whitespace_exact_span(quote, text)
        if replacement is None:
            replacement = _longest_exact_word_span(quote, text, minimum_words)
        if replacement is None:
            continue
        item["quote"] = replacement
        repairs.append(
            {
                "section_id": str(section_id),
                "original_quote": quote,
                "repaired_quote": replacement,
            }
        )
    return repairs


def _whitespace_exact_span(quote: str, text: str) -> str | None:
    parts = re.split(r"\s+", quote.strip())
    if not parts:
        return None
    match = re.search(r"\s+".join(re.escape(part) for part in parts), text)
    return match.group(0) if match else None


def _longest_exact_word_span(quote: str, text: str, minimum_words: int) -> str | None:
    tokens = list(re.finditer(r"\S+", quote))
    for width in range(len(tokens), minimum_words - 1, -1):
        for start in range(len(tokens) - width + 1):
            candidate = quote[tokens[start].start() : tokens[start + width - 1].end()]
            replacement = _whitespace_exact_span(candidate, text)
            if replacement is not None:
                return replacement
    return None


def scope_status(answer: dict[str, Any]) -> tuple[str, str]:
    if answer.get("report_type") == "nonempirical":
        return "exclude", "EC1"
    if answer.get("bio_health_scope") == "no":
        return "exclude", "EC2"
    if answer.get("aging_process_relevance") == "no":
        return "exclude", "EC3"
    if answer.get("multiomics_evidence") == "single_or_no_layer":
        return "exclude", "EC4"
    if (
        answer.get("report_type") == "unclear"
        or answer.get("bio_health_scope") == "unclear"
        or answer.get("aging_process_relevance") == "unclear"
        or answer.get("multiomics_evidence") == "unclear"
        or answer.get("current_report_layer_use") != "yes"
    ):
        return "unresolved", "none"
    return "pass", "none"


def causal_status(answer: dict[str, Any]) -> tuple[str, str]:
    basis = answer.get("causal_basis")
    if basis in POSITIVE_CAUSAL_BASES:
        return "retain", "none"
    if (
        basis in NEGATIVE_CAUSAL_BASES
        and answer.get("causal_information_sufficiency") == "sufficient"
    ):
        return "exclude", "EC5"
    return "unresolved", "none"


def unanimous_value(rows: list[dict[str, Any]], field: str) -> Any:
    values = [row.get(field) for row in rows]
    serialized = {json.dumps(value, sort_keys=True) for value in values}
    return values[0] if len(serialized) == 1 else "unclear"


def agreement_audit(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> dict[str, Any]:
    audit: dict[str, Any] = {}
    for field in fields:
        values = [row.get(field) for row in rows]
        serialized = {json.dumps(value, sort_keys=True) for value in values}
        audit[field] = {
            "unanimous": len(serialized) == 1,
            "values": values,
        }
    return audit


def decisive_fields_unanimous(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bool:
    """Retained for non-v1 title/full-text contracts that require field unanimity."""
    return all(
        len({json.dumps(row.get(field), sort_keys=True) for row in rows}) == 1 for field in fields
    )


def derive_title_result(
    scope_runs: list[dict[str, Any]],
    causal_runs: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    scope_paths = [scope_status(row) for row in scope_runs]
    same_scope_exclusion = len(set(scope_paths)) == 1 and scope_paths[0][0] == "exclude"
    selected = {field: unanimous_value(scope_runs, field) for field in SCOPE_DECISION_FIELDS}
    selected["layer_candidates"] = sorted(
        {
            layer
            for row in scope_runs
            for layer in row.get("layer_candidates", [])
            if isinstance(layer, str)
        }
    )
    selected["multiomics_status"] = _multiomics_status(selected)
    selected["omics_layers"] = selected["layer_candidates"]

    if same_scope_exclusion:
        return {
            "selected_criteria": selected,
            "final_decision": "exclude",
            "final_exclusion_code": scope_paths[0][1],
            "decision_reason": "five_of_five_same_scope_exclusion",
        }
    if any(status != "pass" for status, _ in scope_paths):
        return {
            "selected_criteria": selected,
            "final_decision": "seek_full_text",
            "final_exclusion_code": "none",
            "decision_reason": "scope_unresolved_or_nonunanimous_exclusion",
        }
    if not causal_runs:
        raise ValueError("causal_runs are required after unanimous scope pass")

    selected.update(
        {field: unanimous_value(causal_runs, field) for field in CAUSAL_DECISION_FIELDS}
    )
    causal_paths = [causal_status(row) for row in causal_runs]
    same_causal_exclusion = len(set(causal_paths)) == 1 and causal_paths[0] == ("exclude", "EC5")
    if same_causal_exclusion:
        decision = "exclude"
        exclusion_code = "EC5"
        reason = "five_of_five_same_sufficient_causal_exclusion"
    else:
        decision = "seek_full_text"
        exclusion_code = "none"
        reason = (
            "positive_causal_basis"
            if any(status == "retain" for status, _ in causal_paths)
            else "causal_unresolved_or_nonunanimous_exclusion"
        )
    return {
        "selected_criteria": selected,
        "final_decision": decision,
        "final_exclusion_code": exclusion_code,
        "decision_reason": reason,
    }


def package_full_text_sections(
    sections: list[dict[str, Any]], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    max_chars = int(config.get("max_chars", 60000))
    max_section_chars = int(config.get("max_section_chars", 12000))
    heading_terms = tuple(str(item).casefold() for item in config.get("required_heading_terms", []))
    text_terms = tuple(str(item).casefold() for item in config.get("priority_text_terms", []))
    graph_priority_score = int(config.get("graph_priority_score", 0))
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, section in enumerate(sections):
        heading = str(section.get("heading", ""))
        text = str(section.get("text", ""))
        heading_folded = heading.casefold()
        text_folded = text.casefold()
        score = 100 * sum(term in heading_folded for term in heading_terms)
        score += 20 * sum(term in heading_folded for term in text_terms)
        score += sum(term in text_folded for term in text_terms)
        if section.get("graph_priority") is True:
            score += graph_priority_score
        ranked.append((score, index, section))

    selected_by_index: dict[int, dict[str, Any]] = {}
    truncated_ids: list[str] = []
    used_chars = 0
    for _, index, section in sorted(ranked, key=lambda item: (-item[0], item[1])):
        if used_chars >= max_chars:
            break
        text = str(section.get("text", ""))
        allowance = min(max_section_chars, max_chars - used_chars)
        packaged_text = text[:allowance]
        if not packaged_text:
            continue
        packaged = {**section, "text": packaged_text}
        if len(packaged_text) < len(text):
            packaged["packaging_truncated"] = True
            truncated_ids.append(str(section["section_id"]))
        selected_by_index[index] = packaged
        used_chars += len(packaged_text)

    selected = [selected_by_index[index] for index in sorted(selected_by_index)]
    selected_ids = {str(section["section_id"]) for section in selected}
    audit = {
        "selection_method": "deterministic_heading_keyword_v1",
        "graph_priority_score": graph_priority_score,
        "graph_priority_selected": sum(
            section.get("graph_priority") is True for section in selected
        ),
        "coverage_status": "sufficient" if selected else "insufficient",
        "selected_sections": [
            {
                "section_id": str(section["section_id"]),
                "heading": str(section.get("heading", "")),
            }
            for section in selected
        ],
        "omitted_section_ids": [
            str(section["section_id"])
            for section in sections
            if str(section["section_id"]) not in selected_ids
        ],
        "truncated_section_ids": truncated_ids,
        "selected_chars": used_chars,
        "max_chars": max_chars,
    }
    return selected, audit


def _multiomics_status(answer: dict[str, Any]) -> str:
    evidence = answer.get("multiomics_evidence")
    if (
        evidence in {"explicit_multiomics", "two_or_more_layers"}
        and answer.get("current_report_layer_use") == "yes"
    ):
        return "yes"
    if evidence == "single_or_no_layer":
        return "no"
    return "unclear"
