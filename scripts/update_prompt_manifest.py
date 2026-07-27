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
SUITE_PATH = SCREENING / "configs" / "prompt_suite_v0.50.0.json"
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
        "approval_status": "draft_title_abstract_v0.50.0_calibration",
        "approval_date": None,
        "benchmark_version": "calibration_cycle_v0.41.0",
        "created_date": date.today().isoformat(),
        "change_note": (
            "Title/abstract v0.50.0 follows the frozen v0.40.0 sealed-holdout "
            "failure and the diagnostic v0.41.0 focus run. It limits model "
            "classification to fields "
            "that determine title/abstract PRISMA routing: report type, "
            "biological or health scope, aging-process relevance, multi-omics "
            "candidate status, and causal-candidate status. A causal candidate "
            "is retained when the current report "
            "applies a causal/directed design or makes a directional/mechanistic "
            "result claim; full text determines whether evidence is merely "
            "associational, hypothesis-level, or identified. Aging-role and "
            "design-family subtyping, effect strength, design role, "
            "integration provenance, and validation strength are deferred to "
            "full text because abstracts can support multiple equally valid "
            "subtypes and those fields do not alter title-stage routing. "
            "Clear specialist exclusions route directly; adjudication is "
            "reserved for unclear criteria. Exact molecular-layer inventory is "
            "deferred to full text; an explicit current-report multi-omics claim "
            "is sufficient for title-stage retention. Python is limited to "
            "logical consistency rules: sequential PRISMA scope "
            "short-circuiting, title-layer-inventory deferral, and "
            "review-specific causal-status normalization. Stability "
            "requires exact agreement for every returned categorical field; "
            "free-text rationales and evidence-span wording are audited but not "
            "exact-matched. Codex CLI runs GPT 5.6 Terra at medium reasoning "
            "with plugins disabled. Full-text prompts remain v0.1.0 and "
            "unvalidated."
        ),
        "artifacts": artifacts,
    }
    OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
