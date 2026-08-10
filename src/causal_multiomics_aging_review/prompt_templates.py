from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PLACEHOLDER_PATTERN = re.compile(r"{{([A-Z][A-Z0-9_]*)}}")


def load_evidence_profile(path: str | Path) -> dict[str, Any]:
    profile = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(profile, dict):
        raise ValueError(f"Evidence profile must be a JSON object: {path}")
    for key in ("profile_id", "values", "role_values", "allowed_runtime_placeholders"):
        if key not in profile:
            raise ValueError(f"Evidence profile is missing {key!r}: {path}")
    return profile


def render_evidence_template(
    template: str,
    profile: dict[str, Any],
    role: str,
) -> str:
    common = profile.get("values")
    role_values = profile.get("role_values", {}).get(role)
    if not isinstance(common, dict) or not isinstance(role_values, dict):
        raise ValueError(f"Evidence profile has no values for role {role!r}")

    values = {**common, **role_values}
    rendered = template
    for key, value in values.items():
        if not isinstance(value, str):
            raise ValueError(f"Template value {key!r} must be a string")
        rendered = rendered.replace("{{" + key + "}}", value)

    remaining = set(PLACEHOLDER_PATTERN.findall(rendered))
    allowed = set(profile.get("allowed_runtime_placeholders", []))
    unexpected = sorted(remaining - allowed)
    if unexpected:
        raise ValueError(
            f"Unresolved evidence-profile placeholders for {role}: {unexpected}"
        )
    return rendered
