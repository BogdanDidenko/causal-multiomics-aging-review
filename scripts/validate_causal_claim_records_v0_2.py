#!/usr/bin/env python3
"""Validate v0.2.0 causal claim records and derive evidence levels."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = (
    REPO_ROOT / "protocol/causal_extraction/v0.2.0/claim_record.schema.json"
)

ASSIGNED = {
    "allocation_mechanism",
    "comparator_integrity",
    "adherence_and_contamination",
    "attrition_and_analysis_population",
    "baseline_balance",
    "assigned_contrast_analysis",
    "outcome_timing_and_multiplicity",
}
PERTURBATION = {
    "manipulated_operation_and_target",
    "matched_control",
    "intervention_specificity_or_off_target",
    "functional_target_engagement",
    "timing_relative_to_outcome",
    "replication",
    "necessity_sufficiency_or_rescue_logic",
    "outcome_relevance_to_aging",
}
TRANSFER = {
    "donor_and_recipient_definition",
    "transfer_procedure_and_control",
    "recipient_assignment",
    "compositional_specificity",
    "co_transferred_material_and_interference",
    "transfer_timing_and_outcome",
}
GENETIC_INSTRUMENT = {
    "instrument_relevance_and_strength",
    "independence_and_ld_handling",
    "exclusion_restriction_and_pleiotropy",
    "directionality",
    "population_and_sample_overlap",
    "ancestry_and_tissue_relevance",
    "heterogeneity_and_robust_estimators",
    "colocalization",
    "replication",
}
MEDIATION = {
    "exposure_precedes_mediator_and_outcome",
    "exposure_outcome_exchangeability",
    "exposure_mediator_exchangeability",
    "mediator_outcome_exchangeability",
    "no_exposure_induced_confounder",
    "interaction_handling",
    "direct_and_indirect_estimands",
    "sensitivity_analysis",
}
DIRECTED = {
    "temporal_spacing_and_lag",
    "stationarity",
    "time_varying_confounding",
    "acyclicity_and_faithfulness",
    "causal_sufficiency",
    "markov_equivalence",
    "edge_orientation_basis",
    "interventional_or_instrumental_anchors",
    "stability_and_external_checks",
}

REQUIRED_DOMAINS = {
    "randomized_intervention": ASSIGNED,
    "controlled_nonrandomized_intervention": ASSIGNED,
    "quasi_experiment": ASSIGNED,
    "targeted_genetic_perturbation": PERTURBATION,
    "targeted_pharmacologic_perturbation": PERTURBATION,
    "biological_transfer": TRANSFER,
    "genetic_instrument": GENETIC_INSTRUMENT,
    "mediation_analysis": MEDIATION,
    "temporal_model": DIRECTED,
    "dag_scm": DIRECTED,
    "sem": DIRECTED,
    "bayesian_network": DIRECTED,
    "causal_discovery_algorithm": DIRECTED,
    "invariance_or_environment_based_model": DIRECTED,
}

LEVEL_2_METHODS = set(REQUIRED_DOMAINS) | {"other_formal_design"}
PARTIAL_MARKERS = (
    "preview of subscription content",
    "access via your institution",
    "purchase this article",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return records


def contrast_complete(record: dict[str, Any]) -> str:
    values = record["contrast_components"].values()
    applicable = [value for value in values if value != "not_applicable"]
    if any(value == "unclear" for value in applicable):
        return "unclear"
    return "yes" if applicable and all(value == "yes" for value in applicable) else "no"


def level4_status(record: dict[str, Any]) -> str:
    potential_unclear = False
    for validation in record["validations"]:
        if validation["purpose"] != "identification":
            continue
        kind = validation["validation_type"]
        if kind not in {
            "independent_same_link_replication",
            "orthogonal_same_link_identification",
            "appropriate_colocalization",
        }:
            continue
        relevant_fields = [
            validation["same_link_alignment"],
            validation["result_status"],
        ]
        if kind in {
            "independent_same_link_replication",
            "orthogonal_same_link_identification",
        }:
            relevant_fields.extend(
                [
                    validation["operation_alignment"],
                    validation["data_independence"],
                    validation["experimental_independence"],
                ]
            )
        else:
            relevant_fields.append(validation["colocalization_threshold_met"])
        if "unclear" in relevant_fields:
            potential_unclear = True
            continue
        common = (
            validation["same_link_alignment"] == "exact"
            and validation["result_status"] == "supports_claim"
        )
        independent = (
            kind == "independent_same_link_replication"
            and common
            and validation["operation_alignment"] == "same"
            and validation["data_independence"] == "independent"
            and validation["experimental_independence"] == "independent"
        )
        orthogonal = (
            kind == "orthogonal_same_link_identification"
            and common
            and validation["operation_alignment"] == "orthogonal"
            and validation["data_independence"] == "independent"
            and validation["experimental_independence"] == "independent"
        )
        coloc = (
            kind == "appropriate_colocalization"
            and common
            and record["primary_design_or_method"] == "genetic_instrument"
            and validation["colocalization_threshold_met"] == "yes"
        )
        if independent or orthogonal or coloc:
            return "yes"
    return "unclear" if potential_unclear else "no"


def candidate_level(record: dict[str, Any]) -> tuple[int | str, str]:
    assessment = record["reviewer_identification_assessment"]
    if assessment == "unclear":
        return "manual_review", "not_applicable"
    if assessment == "no_identification":
        return 1, "not_applicable"
    if assessment == "formal_hypothesis_only":
        return 2, "not_applicable"
    if assessment == "effect_claim_not_assessable":
        level = 2 if record["primary_design_or_method"] in LEVEL_2_METHODS else 1
        return level, "not_applicable"
    status = level4_status(record)
    return (4 if status == "yes" else 3), status


def heading_offsets(text: str) -> list[tuple[int, str]]:
    offsets: list[tuple[int, str]] = []
    cursor = 0
    for line in text.splitlines(keepends=True):
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line.rstrip("\n"))
        if match:
            offsets.append((cursor, match.group(1)))
        cursor += len(line)
    return offsets


def nearest_heading(offsets: list[tuple[int, str]], quote_offset: int) -> str | None:
    preceding = [heading for offset, heading in offsets if offset <= quote_offset]
    return preceding[-1] if preceding else None


def main() -> int:
    args = parse_args()
    records = load_jsonl(args.jsonl.resolve())
    schema = json.loads(args.schema.resolve().read_text())
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    derived: list[dict[str, Any]] = []
    claim_ids: set[str] = set()
    document_cache: dict[Path, tuple[str, list[tuple[int, str]]]] = {}

    for record in records:
        claim_id = record.get("claim_id", "<missing>")
        for error in validator.iter_errors(record):
            location = ".".join(str(part) for part in error.absolute_path)
            errors.append(f"{claim_id}: schema {location}: {error.message}")
        if claim_id in claim_ids:
            errors.append(f"duplicate claim_id: {claim_id}")
        claim_ids.add(claim_id)

        anchors = {item["anchor_id"]: item for item in record.get("evidence_anchors", [])}
        references: set[str] = set()
        for ids in record.get("field_anchors", {}).values():
            references.update(ids)
        for item in record.get("assumption_judgments", []):
            references.update(item["evidence_anchor_ids"])
            if item["status"] == "not_reported" and not item["search_note"].strip():
                errors.append(f"{claim_id}/{item['domain']}: not_reported needs search_note")
            if (
                item["status"] in {"addressed", "violated", "unclear"}
                and not item["evidence_anchor_ids"]
            ):
                errors.append(f"{claim_id}/{item['domain']}: status needs evidence anchor")
        for group in ("diagnostics", "validations"):
            for item in record.get(group, []):
                references.update(item["evidence_anchor_ids"])
        unknown = references - set(anchors)
        if unknown:
            errors.append(f"{claim_id}: unknown evidence anchors {sorted(unknown)}")

        domains = {item["domain"] for item in record.get("assumption_judgments", [])}
        required = set(REQUIRED_DOMAINS.get(record.get("primary_design_or_method"), set()))
        for supporting in record.get("supporting_designs_or_methods", []):
            required.update(REQUIRED_DOMAINS.get(supporting, set()))
        missing_domains = required - domains
        if missing_domains:
            errors.append(f"{claim_id}: missing assumption domains {sorted(missing_domains)}")

        for anchor_id, anchor in anchors.items():
            path = (REPO_ROOT / anchor["document_path"]).resolve()
            try:
                path.relative_to(REPO_ROOT)
            except ValueError:
                errors.append(f"{claim_id}/{anchor_id}: document outside repository")
                continue
            if not path.is_file():
                errors.append(f"{claim_id}/{anchor_id}: missing document {path}")
                continue
            text, offsets = document_cache.setdefault(
                path, (path.read_text(), heading_offsets(path.read_text()))
            )
            quote = anchor["quote"]
            quote_offset = text.find(quote)
            if quote_offset < 0:
                errors.append(f"{claim_id}/{anchor_id}: quote is not exact substring")
                continue
            if len(quote.split()) < 6:
                errors.append(f"{claim_id}/{anchor_id}: quote has fewer than six tokens")
            expected_heading = nearest_heading(offsets, quote_offset)
            if expected_heading != anchor["nearest_section_heading"]:
                errors.append(
                    f"{claim_id}/{anchor_id}: nearest heading is {expected_heading!r}, "
                    f"not {anchor['nearest_section_heading']!r}"
                )

        source = record.get("source_adequacy", {})
        source_texts = [
            document_cache[(REPO_ROOT / anchor["document_path"]).resolve()][0].lower()
            for anchor in anchors.values()
            if (REPO_ROOT / anchor["document_path"]).resolve() in document_cache
        ]
        has_partial_marker = any(
            marker in text for marker in PARTIAL_MARKERS for text in source_texts
        )
        if has_partial_marker and source.get("full_text_status") == "full_text":
            errors.append(f"{claim_id}: source marked full_text despite preview marker")

        level, level4 = candidate_level(record)
        derived.append(
            {
                "claim_id": claim_id,
                "contrast_complete": contrast_complete(record),
                "candidate_level": level,
                "level4_qualification": level4,
            }
        )

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS")
    print(json.dumps(derived, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
