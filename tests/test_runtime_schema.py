from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from causal_multiomics_aging_review.causal_extraction import codex_runtime_schema
from causal_multiomics_aging_review.runtime_schema import inline_local_json_schema

REPO = Path(__file__).resolve().parents[1]
SCHEMA = (
    REPO
    / "protocol/causal_extraction/validation/v0.3.1-independent-15-v1.0.0"
    / "reference_inventory.schema.json"
)


def has_key(value: object, target: str) -> bool:
    if isinstance(value, dict):
        return target in value or any(has_key(item, target) for item in value.values())
    if isinstance(value, list):
        return any(has_key(item, target) for item in value)
    return False


def test_runtime_schema_inlines_local_composition() -> None:
    source = json.loads(SCHEMA.read_text(encoding="utf-8"))
    compiled = inline_local_json_schema(source)

    Draft202012Validator.check_schema(compiled)
    assert not has_key(compiled, "$ref")
    assert not has_key(compiled, "allOf")
    assert not has_key(compiled, "$schema")
    assert not has_key(compiled, "$defs")
    method_ids = compiled["properties"]["qualifying_analyses"]["items"]["properties"][
        "method_evidence_atom_ids"
    ]
    assert method_ids["type"] == "array"
    assert method_ids["minItems"] == 1


def test_codex_runtime_schema_keeps_array_type() -> None:
    source = json.loads(SCHEMA.read_text(encoding="utf-8"))
    compiled = codex_runtime_schema(inline_local_json_schema(source))
    method_ids = compiled["properties"]["qualifying_analyses"]["items"]["properties"][
        "method_evidence_atom_ids"
    ]
    assert method_ids["type"] == "array"
    assert "uniqueItems" not in method_ids
