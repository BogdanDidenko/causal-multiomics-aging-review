from __future__ import annotations

import copy
from typing import Any


def _resolve_pointer(root: dict[str, Any], pointer: str) -> Any:
    if not pointer.startswith("#/"):
        raise ValueError(f"Only local JSON Schema references are supported: {pointer}")
    value: Any = root
    for raw_part in pointer[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"Unresolved local JSON Schema reference: {pointer}")
        value = value[part]
    return value


def _merge_schema(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(left)
    for key, value in right.items():
        if key not in merged:
            merged[key] = copy.deepcopy(value)
        elif key == "required":
            merged[key] = list(dict.fromkeys([*merged[key], *value]))
        elif key == "properties":
            merged[key] = {**merged[key], **copy.deepcopy(value)}
        elif merged[key] != value:
            raise ValueError(f"Conflicting JSON Schema values for {key!r}")
    return merged


def inline_local_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Inline local refs/allOf and remove dialect metadata for CLI adapters."""
    root = copy.deepcopy(schema)

    def expand(value: Any) -> Any:
        if isinstance(value, list):
            return [expand(item) for item in value]
        if not isinstance(value, dict):
            return value

        siblings = {
            key: item
            for key, item in value.items()
            if key not in {"$schema", "$id", "$defs", "$ref", "allOf"}
        }
        expanded: dict[str, Any] = {}
        if "$ref" in value:
            target = _resolve_pointer(root, str(value["$ref"]))
            expanded = _merge_schema(expanded, expand(target))
        if "allOf" in value:
            for member in value["allOf"]:
                expanded = _merge_schema(expanded, expand(member))
        return _merge_schema(expanded, {key: expand(item) for key, item in siblings.items()})

    compiled = expand(root)
    if not isinstance(compiled, dict):
        raise ValueError("Compiled JSON Schema is not an object")
    return compiled
