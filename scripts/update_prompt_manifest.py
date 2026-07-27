#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCREENING = ROOT / "protocol" / "screening"
SUITE_PATH = SCREENING / "configs" / "prompt_suite_v0.16.0.json"
OUTPUT = SCREENING / "prompt_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def add_artifact(
    artifacts: list[dict[str, str]],
    stage: str,
    role: str,
    config: dict[str, str],
) -> None:
    prompt_path = SCREENING / config["prompt"]
    schema_path = SCREENING / config["schema"]
    prompt = prompt_path.read_text(encoding="utf-8")
    prompt_id = re.search(r"^PROMPT_ID:\s*(.+)$", prompt, re.M)
    version = re.search(r"^PROMPT_VERSION:\s*(.+)$", prompt, re.M)
    if not prompt_id or not version:
        raise ValueError(f"Missing prompt ID/version in {prompt_path}")
    artifacts.append(
        {
            "prompt_id": prompt_id.group(1).strip(),
            "version": version.group(1).strip(),
            "stage": stage,
            "role": role,
            "prompt_path": str(prompt_path.relative_to(SCREENING)),
            "prompt_sha256": sha256(prompt_path),
            "schema_path": str(schema_path.relative_to(SCREENING)),
            "schema_sha256": sha256(schema_path),
        }
    )


def main() -> None:
    suite = load(SUITE_PATH)
    artifacts: list[dict[str, str]] = []
    for stage in ("title_abstract", "full_text"):
        stage_config = suite["stages"][stage]
        if "section_selector" in stage_config:
            add_artifact(
                artifacts,
                stage,
                "section_selector",
                stage_config["section_selector"],
            )
        for role, config in stage_config["roles"].items():
            add_artifact(artifacts, stage, role, config)
        add_artifact(artifacts, stage, "adjudicator", stage_config["adjudication"])
    manifest = {
        "manifest_version": "1.0.0",
        "active_suite": f"{suite['suite_id']}@{suite['suite_version']}",
        "suite_config": {
            "path": str(SUITE_PATH.relative_to(SCREENING)),
            "sha256": sha256(SUITE_PATH),
        },
        "approval_status": "title_abstract_holdout_failed_new_cycle_required",
        "approval_date": None,
        "benchmark_version": "stability_holdout_v3_evaluated",
        "created_date": date.today().isoformat(),
        "change_note": (
            "Title/abstract v0.16.0 adds a substantive-aging-analysis exception "
            "to method-first report typing and excludes ordinary regulatory or "
            "co-expression networks from causal graphical designs. Python "
            "derives aging role and integration mode using fixed precedence "
            "tables. The frozen suite passed the 25-record development pilot "
            "but failed its first sealed 25-record holdout at 92% final-routing "
            "and 72% decisive-path exact agreement across five runs. It must "
            "not be approved or tuned against that holdout within the same "
            "calibration cycle. Full-text prompts remain v0.1.0 and unvalidated."
        ),
        "artifacts": artifacts,
    }
    OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
