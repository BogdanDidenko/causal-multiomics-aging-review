#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "protocol"
SCREENING = PROTOCOL / "screening"
SUITE_PATH = SCREENING / "configs" / "prompt_suite_v0.50.0.json"
SEARCH_CONFIG_PATH = PROTOCOL / "search_config.json"
MANIFEST_PATH = SCREENING / "prompt_manifest.json"

BASE_PLACEHOLDERS = {"{{RECORD_ID}}", "{{TITLE}}", "{{ABSTRACT}}", "{{YEAR}}", "{{SOURCE}}"}
TITLE_ABSTRACT_PLACEHOLDERS = {"{{DOCUMENT_TYPE}}"}
EXTRA_PLACEHOLDERS = {
    ("title_abstract", "adjudicator"): {"{{SCOPE_REVIEW}}", "{{CAUSAL_REVIEW}}"},
    ("full_text", "section_selector"): {"{{SECTION_CATALOG}}"},
    ("full_text", "eligibility_reviewer"): {"{{SELECTED_SECTIONS}}"},
    ("full_text", "causal_evidence_reviewer"): {
        "{{SELECTED_SECTIONS}}",
        "{{ELIGIBILITY_REVIEW}}",
    },
    ("full_text", "adjudicator"): {
        "{{SELECTED_SECTIONS}}",
        "{{ELIGIBILITY_REVIEW}}",
        "{{CAUSAL_REVIEW}}",
    },
}


def load_object(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifacts(suite: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    items = []
    for stage, stage_config in suite["stages"].items():
        for role, config in stage_config.get("roles", {}).items():
            items.append((stage, role, config))
        items.append((stage, "adjudicator", stage_config["adjudication"]))
        if "section_selector" in stage_config:
            items.append((stage, "section_selector", stage_config["section_selector"]))
    return items


def main() -> None:
    errors: list[str] = []
    search_config = load_object(SEARCH_CONFIG_PATH)
    databases = search_config.get("databases", [])
    expected_ids = {
        "pubmed",
        "scopus",
        "europepmc",
        "semantic_scholar",
        "springernature",
        "openalex",
        "google_scholar",
    }
    actual_ids = {item.get("id") for item in databases}
    if actual_ids != expected_ids:
        errors.append(
            f"expected seven databases {sorted(expected_ids)}, "
            f"found {sorted(actual_ids)}"
        )
    for database in databases:
        query_path = PROTOCOL / database["query_file"]
        if not query_path.is_file() or not query_path.read_text(encoding="utf-8").strip():
            errors.append(f"{database['id']}: missing query {query_path}")
            continue
        query = query_path.read_text(encoding="utf-8").lower()
        if not any(term in query for term in ("multi-omics", "multiomics", "multi-omic")):
            errors.append(f"{database['id']}: no multi-omics anchor")
        if not any(term in query for term in ("aging", "ageing", "longevity", "healthspan")):
            errors.append(f"{database['id']}: no aging anchor")
        if not any(
            term in query
            for term in (
                "causal",
                "mendelian random",
                "mediation",
                "intervention",
                "perturb",
            )
        ):
            errors.append(f"{database['id']}: no broad causal-design anchor")

    suite = load_object(SUITE_PATH)
    expected_provider = {
        "protocol": "codex_cli",
        "codex_cli_version": "codex-cli 0.145.0",
        "model": "gpt-5.6-terra",
        "sandbox": "read-only",
        "approval_policy": "never",
        "ephemeral": True,
        "ignore_user_config": True,
        "ignore_rules": True,
        "isolated_home": True,
        "disabled_features": ["plugins"],
    }
    for key, expected in expected_provider.items():
        if suite.get("provider", {}).get(key) != expected:
            errors.append(f"suite provider {key} must be {expected!r}")
    runtime = suite.get("runtime", {})
    if runtime.get("reasoning_effort") != "medium":
        errors.append("runtime reasoning_effort must be medium")
    if runtime.get("max_retries") != 1:
        errors.append("runtime must allow exactly one retry")
    title_stage = suite.get("stages", {}).get("title_abstract", {})
    if title_stage.get("max_input_abstract_chars") != 5000:
        errors.append("title/abstract metadata must be capped at 5,000 characters")
    if title_stage.get("identification_status_contract") != "causal_candidate_v1":
        errors.append("title/abstract must use the causal_candidate_v1 contract")
    if title_stage.get("prisma_scope_short_circuit_round_a") is not True:
        errors.append("round-A title screening must apply the PRISMA scope short-circuit")
    if title_stage.get("title_layer_inventory") != "deferred_to_full_text":
        errors.append("title-stage molecular-layer inventory must be deferred")
    title_routing = title_stage.get("routing", {})
    if title_routing.get("round_a_any_exclude") != "exclude":
        errors.append("clear title/abstract exclusions must bypass adjudication")
    if title_routing.get("round_a_any_unclear") != "adjudicate":
        errors.append("unclear title/abstract criteria must be adjudicated")

    stability = suite.get("stability_policy", {})
    if stability.get("model") != "gpt-5.6-terra":
        errors.append("stability model must be gpt-5.6-terra")
    if stability.get("repeats") != 5:
        errors.append("stability requires five runs")
    exact_acceptance = {
        "schema_success_rate": 1.0,
        "final_decision_exact_agreement": 1.0,
        "decisive_criteria_exact_agreement": 1.0,
        "all_tracked_criteria_exact_agreement": 1.0,
        "causal_evidence_level_exact_agreement": 1.0,
        "manual_review_rate": 0.0,
    }
    if stability.get("acceptance") != exact_acceptance:
        errors.append("stability acceptance must require exact agreement")

    for stage, role, config in artifacts(suite):
        prompt_path = SCREENING / config["prompt"]
        schema_path = SCREENING / config["schema"]
        if not prompt_path.is_file():
            errors.append(f"{stage}.{role}: missing prompt")
            continue
        if not schema_path.is_file():
            errors.append(f"{stage}.{role}: missing schema")
            continue
        prompt = prompt_path.read_text(encoding="utf-8")
        missing = (
            BASE_PLACEHOLDERS
            | (TITLE_ABSTRACT_PLACEHOLDERS if stage == "title_abstract" else set())
            | EXTRA_PLACEHOLDERS.get((stage, role), set())
        )
        missing = {item for item in missing if item not in prompt}
        if missing:
            errors.append(f"{stage}.{role}: missing placeholders {sorted(missing)}")
        expected_prompt_version = Path(config["prompt"]).parent.name.removeprefix("v")
        if (
            "PROMPT_ID:" not in prompt
            or f"PROMPT_VERSION: {expected_prompt_version}" not in prompt
        ):
            errors.append(f"{stage}.{role}: invalid prompt header")
        if "STABILITY CONTRACT" not in prompt:
            errors.append(f"{stage}.{role}: missing stability contract")
        if stage == "title_abstract" and role in {"scope_reviewer", "adjudicator"}:
            if "aging_process_relevance" not in prompt:
                errors.append(f"{stage}.{role}: missing atomic aging contract")
        try:
            Draft202012Validator.check_schema(load_object(schema_path))
        except Exception as error:
            errors.append(f"{stage}.{role}: invalid schema: {error}")

    if MANIFEST_PATH.is_file():
        manifest = load_object(MANIFEST_PATH)
        if manifest.get("suite_config", {}).get("sha256") != sha256(SUITE_PATH):
            errors.append("prompt manifest has stale suite hash")
        for artifact in manifest.get("artifacts", []):
            prompt_path = SCREENING / artifact["prompt_path"]
            schema_path = SCREENING / artifact["schema_path"]
            if sha256(prompt_path) != artifact["prompt_sha256"]:
                errors.append(f"stale prompt hash for {artifact['prompt_id']}")
            if sha256(schema_path) != artifact["schema_sha256"]:
                errors.append(f"stale schema hash for {artifact['prompt_id']}")
    else:
        errors.append("missing prompt_manifest.json")

    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or ".git" in path.parts
            or ".venv" in path.parts
            or path == Path(__file__).resolve()
        ):
            continue
        if path.suffix in {".md", ".txt", ".json", ".py"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "/Users/" in text:
                errors.append(f"absolute local path in {path.relative_to(ROOT)}")
            for secret_name in (
                "SCOPUS_API_KEY=",
                "PUBMED_API_KEY=",
                "OPENALEX_API_KEY=",
                "SEMANTIC_SCHOLAR_API_KEY=",
            ):
                if secret_name in text and path.name != ".env.example":
                    errors.append(f"possible credential assignment in {path.relative_to(ROOT)}")

    if errors:
        raise SystemExit("Protocol validation failed:\n- " + "\n- ".join(errors))
    print(
        f"protocol_ok databases={len(databases)} "
        f"stages={len(suite['stages'])} prompts={len(artifacts(suite))}"
    )


if __name__ == "__main__":
    main()
