import copy
import json
from pathlib import Path

import pytest

from causal_multiomics_aging_review.prompt_templates import (
    load_evidence_profile,
    render_evidence_template,
)
from causal_multiomics_aging_review.screening import _load_stage_artifacts

ROOT = Path(__file__).resolve().parents[1]
SCREENING = ROOT / "protocol" / "screening"
ROLES = ("scope_reviewer", "causal_method_reviewer")


@pytest.mark.parametrize("role", ROLES)
def test_title_abstract_profile_is_byte_identical_to_screened_prompt(role: str) -> None:
    template = (
        SCREENING / "prompt_templates" / "v1.4.0-rc1" / f"{role}.txt"
    ).read_text(encoding="utf-8")
    profile = load_evidence_profile(
        SCREENING / "evidence_profiles" / "v1.4.0-rc1" / "title_abstract.json"
    )
    expected = (
        SCREENING / "prompts" / "title_abstract" / "v1.4.0-rc1" / f"{role}.txt"
    ).read_text(encoding="utf-8")

    assert render_evidence_template(template, profile, role) == expected


@pytest.mark.parametrize("role", ROLES)
def test_full_text_profile_resolves_only_runtime_record_placeholders(role: str) -> None:
    template = (
        SCREENING / "prompt_templates" / "v1.4.0-rc1" / f"{role}.txt"
    ).read_text(encoding="utf-8")
    profile = load_evidence_profile(
        SCREENING / "evidence_profiles" / "v1.4.0-rc1" / "full_text_sections.json"
    )

    rendered = render_evidence_template(template, profile, role)

    assert "{{SELECTED_SECTIONS}}" in rendered
    assert "FULL-TEXT EVIDENCE CONTRACT" in rendered
    assert "graph relations are retrieval provenance" in rendered
    assert "title/abstract screening record" not in rendered


def test_stage_artifact_loader_records_template_and_profile() -> None:
    stage_config = {
        "roles": {
            "scope_reviewer": {
                "template": "prompt_templates/v1.4.0-rc1/scope_reviewer.txt",
                "template_role": "scope_reviewer",
                "evidence_profile": (
                    "evidence_profiles/v1.4.0-rc1/title_abstract.json"
                ),
                "schema": (
                    "schemas/title_abstract/v1.0.0/scope_reviewer.schema.json"
                ),
            }
        }
    }

    artifact = _load_stage_artifacts(stage_config)["scope_reviewer"]
    expected = (
        SCREENING
        / "prompts"
        / "title_abstract"
        / "v1.4.0-rc1"
        / "scope_reviewer.txt"
    ).read_text(encoding="utf-8")

    assert artifact["prompt"] == expected
    assert artifact["evidence_profile_id"] == "title_abstract"


@pytest.mark.parametrize("role", ROLES)
def test_full_text_schema_changes_only_evidence_source_domain(role: str) -> None:
    abstract_schema = json.loads(
        (
            SCREENING / "schemas" / "title_abstract" / "v1.0.0" / f"{role}.schema.json"
        ).read_text(encoding="utf-8")
    )
    full_text_schema = json.loads(
        (
            SCREENING / "schemas" / "full_text" / "v1.4.0-rc1" / f"{role}.schema.json"
        ).read_text(encoding="utf-8")
    )
    normalized = copy.deepcopy(full_text_schema)
    normalized["$defs"]["evidence"]["properties"]["source"] = abstract_schema[
        "$defs"
    ]["evidence"]["properties"]["source"]

    assert normalized == abstract_schema
