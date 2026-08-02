#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "protocol"
SCREENING = PROTOCOL / "screening"
SEARCH_CONFIG = PROTOCOL / "search_config_v1.0.0.json"
SUITE_CONFIG = SCREENING / "configs" / "prompt_suite_v1.0.0.json"
MANIFEST = SCREENING / "prompt_manifest_v1.0.0.json"
SEARCH_CALIBRATION = PROTOCOL / "search_calibration" / "v1.0.0"
SEARCH_POLICY = SEARCH_CALIBRATION / "policy.json"
CANDIDATE_POOL = SEARCH_CALIBRATION / "canonical_positive_candidates_120.csv"
CANDIDATE_MANIFEST = SEARCH_CALIBRATION / "canonical_positive_candidates_120.manifest.json"
AI_ANNOTATION = (
    ROOT
    / "analysis/v1_methodology/canonical_candidate_final_ai_annotation_2026-08-02.csv"
)
AI_ANNOTATION_SUMMARY = AI_ANNOTATION.with_suffix(".summary.json")
PENDING_CANDIDATE_FIELDS = (
    "expert_1_empirical_primary",
    "expert_1_aging_eligible",
    "expert_1_multiomics_eligible",
    "expert_1_causal_method_eligible",
    "expert_1_overall",
    "expert_2_empirical_primary",
    "expert_2_aging_eligible",
    "expert_2_multiomics_eligible",
    "expert_2_causal_method_eligible",
    "expert_2_overall",
    "adjudicated_empirical_primary",
    "adjudicated_aging_eligible",
    "adjudicated_multiomics_eligible",
    "adjudicated_causal_method_eligible",
    "adjudicated_status",
)
DATABASES = {
    "pubmed",
    "scopus",
    "europepmc",
    "semantic_scholar",
    "springernature",
    "openalex",
    "google_scholar",
}
FORBIDDEN_CAUSAL_ANCHORS = {"affects", "regulates", "drives", "influences"}
TITLE_PLACEHOLDERS = {
    "{{RECORD_ID}}",
    "{{SOURCE}}",
    "{{YEAR}}",
    "{{TITLE}}",
    "{{ABSTRACT}}",
}
FULL_TEXT_PLACEHOLDERS = TITLE_PLACEHOLDERS | {"{{SELECTED_SECTIONS}}"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_queries(errors: list[str]) -> int:
    config = load(SEARCH_CONFIG)
    databases = config.get("databases", [])
    ids = {item.get("id") for item in databases}
    if ids != DATABASES:
        errors.append(f"v1 search config database set is {sorted(ids)}")
    if config.get("status") != "calibration_pending_expert_query_review":
        errors.append("v1 search must remain calibration_pending_expert_query_review")
    if config.get("search_end_date") != "2026-08-02":
        errors.append("v1 search end date must be 2026-08-02")
    for database in databases:
        query_path = PROTOCOL / database["query_file"]
        if not query_path.is_file():
            errors.append(f"{database['id']}: missing query file")
            continue
        query = query_path.read_text(encoding="utf-8").lower()
        if not re.search(r"multi.?omic|multiome|integrat(?:ed|ive).?omics", query):
            errors.append(f"{database['id']}: missing explicit multi-omics branch")
        layer_families = sum(
            token in query
            for token in (
                "genom",
                "epigenom",
                "transcriptom",
                "proteom",
                "metabolom",
                "microbiom",
            )
        )
        if layer_families < 4:
            errors.append(f"{database['id']}: incomplete molecular-layer branch")
        if not any(term in query for term in ("aging", "ageing", "longevity")):
            errors.append(f"{database['id']}: missing aging block")
        if not any(
            term in query
            for term in (
                "mendelian random",
                "intervention",
                "perturb",
                "mediation",
                "causal discovery",
            )
        ):
            errors.append(f"{database['id']}: incomplete causal-design block")
        words = set(re.findall(r"[a-z]+", query))
        forbidden = sorted(words & FORBIDDEN_CAUSAL_ANCHORS)
        if forbidden:
            errors.append(f"{database['id']}: forbidden anchors {forbidden}")
    return len(databases)


def validate_prompt(
    errors: list[str], stage: str, role: str, config: dict[str, str]
) -> None:
    prompt_path = SCREENING / config["prompt"]
    schema_path = SCREENING / config["schema"]
    if not prompt_path.is_file() or not schema_path.is_file():
        errors.append(f"{stage}.{role}: missing prompt or schema")
        return
    prompt = prompt_path.read_text(encoding="utf-8")
    placeholders = TITLE_PLACEHOLDERS if stage == "title_abstract" else FULL_TEXT_PLACEHOLDERS
    missing = sorted(item for item in placeholders if item not in prompt)
    if missing:
        errors.append(f"{stage}.{role}: missing placeholders {missing}")
    if "PROMPT_VERSION: 1.0.0" not in prompt or "PROMPT_ID:" not in prompt:
        errors.append(f"{stage}.{role}: invalid prompt header")
    if "STABILITY CONTRACT" not in prompt:
        errors.append(f"{stage}.{role}: missing stability contract")
    try:
        Draft202012Validator.check_schema(load(schema_path))
    except Exception as error:
        errors.append(f"{stage}.{role}: invalid schema: {error}")


def validate_suite(errors: list[str]) -> int:
    suite = load(SUITE_CONFIG)
    if suite.get("approval_status") != "calibration_pending_expert_gold":
        errors.append("v1 suite must remain pending expert gold validation")
    provider = suite.get("provider", {})
    runtime = suite.get("runtime", {})
    if provider.get("protocol") != "codex_cli":
        errors.append("v1 provider must be Codex CLI")
    if provider.get("model") != "gpt-5.6-terra":
        errors.append("v1 model must be gpt-5.6-terra")
    if runtime.get("reasoning_effort") != "medium":
        errors.append("v1 reasoning effort must be medium")
    if runtime.get("max_retries") != 1:
        errors.append("v1 runtime must allow exactly one retry")

    stages = suite.get("stages", {})
    title = stages.get("title_abstract", {})
    full_text = stages.get("full_text", {})
    if title.get("architecture") != "v1_two_role_unanimous":
        errors.append("invalid v1 title architecture")
    if set(title.get("roles", {})) != {"scope_reviewer", "causal_method_reviewer"}:
        errors.append("v1 title stage must contain exactly two model roles")
    if title.get("decision_repeats") != 5:
        errors.append("v1 title roles require five runs")
    if full_text.get("architecture") != "v1_deterministic_sections_unanimous":
        errors.append("invalid v1 full-text architecture")
    if set(full_text.get("roles", {})) != {
        "eligibility_reviewer",
        "causal_evidence_reviewer",
    }:
        errors.append("v1 full-text stage must contain exactly two model roles")
    if full_text.get("decision_repeats") != 5:
        errors.append("v1 full-text roles require five runs")
    serialized = json.dumps(stages).lower()
    for removed in ("directional_result_reviewer", "section_selector", "adjudicator"):
        if removed in serialized:
            errors.append(f"removed v1 role still configured: {removed}")

    expected_acceptance = {
        "schema_success_rate": 1.0,
        "final_decision_exact_agreement": 1.0,
        "decisive_criteria_exact_agreement": 1.0,
        "all_tracked_criteria_exact_agreement": 1.0,
        "causal_evidence_level_exact_agreement": 1.0,
        "internal_decision_field_unanimity_rate": 1.0,
        "manual_review_rate": 0.0,
    }
    if suite.get("stability_policy", {}).get("acceptance") != expected_acceptance:
        errors.append("v1 stability gates must require exact agreement")

    artifacts = []
    for stage, stage_config in stages.items():
        for role, role_config in stage_config.get("roles", {}).items():
            validate_prompt(errors, stage, role, role_config)
            artifacts.append((stage, role, role_config))
    return len(artifacts)


def validate_manifest(errors: list[str]) -> None:
    if not MANIFEST.is_file():
        errors.append("missing v1 candidate prompt manifest")
        return
    manifest = load(MANIFEST)
    if manifest.get("approval_status") != "calibration_pending_expert_gold":
        errors.append("v1 manifest approval status is not pending")
    suite_entry = manifest.get("suite_config", {})
    if suite_entry.get("sha256") != sha256(SUITE_CONFIG):
        errors.append("v1 manifest has stale suite hash")
    for artifact in manifest.get("artifacts", []):
        prompt_path = SCREENING / artifact["prompt_path"]
        schema_path = SCREENING / artifact["schema_path"]
        if sha256(prompt_path) != artifact.get("prompt_sha256"):
            errors.append(f"stale prompt hash: {artifact.get('prompt_id')}")
        if sha256(schema_path) != artifact.get("schema_sha256"):
            errors.append(f"stale schema hash: {artifact.get('prompt_id')}")


def validate_search_calibration(errors: list[str]) -> int:
    policy = load(SEARCH_POLICY)
    if policy.get("candidate_pool_target") != 120:
        errors.append("v1 candidate pool target must be 120")
    if policy.get("canonical_positive_freeze_minimum") != 100:
        errors.append("v1 query freeze requires 100 adjudicated positives")
    if not CANDIDATE_POOL.is_file() or not CANDIDATE_MANIFEST.is_file():
        errors.append("missing v1 canonical-positive candidate pool or manifest")
        return 0

    with CANDIDATE_POOL.open(encoding="utf-8", newline="") as handle:
        candidates = list(csv.DictReader(handle))
    if len(candidates) != 120:
        errors.append(f"v1 candidate pool contains {len(candidates)} records")
    candidate_ids = [row["candidate_id"] for row in candidates]
    if len(set(candidate_ids)) != len(candidate_ids):
        errors.append("v1 candidate pool contains duplicate study identifiers")
    for field in PENDING_CANDIDATE_FIELDS:
        if {row[field] for row in candidates} != {"pending"}:
            errors.append(f"v1 candidate pool has non-pending {field} values")
    if {row["candidate_status"] for row in candidates} != {
        "unreviewed_candidate_not_gold"
    }:
        errors.append("v1 candidate pool is incorrectly represented as gold")

    manifest = load(CANDIDATE_MANIFEST)
    if manifest.get("candidate_pool_is_gold_standard") is not False:
        errors.append("v1 candidate manifest must explicitly deny gold status")
    if manifest.get("candidate_count") != len(candidates):
        errors.append("v1 candidate manifest has stale record count")
    if manifest.get("required_adjudicated_positive_count") != 100:
        errors.append("v1 candidate manifest has wrong freeze minimum")
    if manifest.get("candidate_pool", {}).get("sha256") != sha256(CANDIDATE_POOL):
        errors.append("v1 candidate manifest has stale pool hash")
    if not AI_ANNOTATION.is_file() or not AI_ANNOTATION_SUMMARY.is_file():
        errors.append("missing v1 assistant annotation artifacts")
        return len(candidates)
    with AI_ANNOTATION.open(encoding="utf-8", newline="") as handle:
        annotations = list(csv.DictReader(handle))
    annotation_counts = {
        status: sum(row["assistant_final_status"] == status for row in annotations)
        for status in ("include", "exclude", "seek_full_text")
    }
    if annotation_counts != {"include": 95, "exclude": 23, "seek_full_text": 2}:
        errors.append(f"unexpected v1 assistant annotation counts: {annotation_counts}")
    if {row["human_expert_status"] for row in annotations} != {"pending"}:
        errors.append("assistant annotations must not populate expert-gold status")
    annotation_summary = load(AI_ANNOTATION_SUMMARY)
    if annotation_summary.get("gold_standard") is not False:
        errors.append("v1 assistant annotation is incorrectly represented as gold")
    if annotation_summary.get("output", {}).get("sha256") != sha256(AI_ANNOTATION):
        errors.append("v1 assistant annotation summary has stale output hash")
    return len(candidates)


def main() -> None:
    errors: list[str] = []
    database_count = validate_queries(errors)
    prompt_count = validate_suite(errors)
    validate_manifest(errors)
    candidate_count = validate_search_calibration(errors)
    if errors:
        raise SystemExit("v1 protocol validation failed:\n- " + "\n- ".join(errors))
    print(
        f"v1_protocol_ok databases={database_count} prompts={prompt_count} "
        f"canonical_candidates={candidate_count}"
    )


if __name__ == "__main__":
    main()
