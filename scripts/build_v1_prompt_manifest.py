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
SUITE_PATH = SCREENING / "configs" / "prompt_suite_v1.0.0.json"
OUTPUT = SCREENING / "prompt_manifest_v1.0.0.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    suite = load(SUITE_PATH)
    artifacts = []
    for stage, stage_config in suite["stages"].items():
        for role, config in stage_config["roles"].items():
            prompt_path = SCREENING / config["prompt"]
            schema_path = SCREENING / config["schema"]
            prompt = prompt_path.read_text(encoding="utf-8")
            prompt_id = re.search(r"^PROMPT_ID:\s*(.+)$", prompt, re.M)
            version = re.search(r"^PROMPT_VERSION:\s*(.+)$", prompt, re.M)
            if not prompt_id or not version:
                raise ValueError(f"Missing prompt metadata in {prompt_path}")
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
    manifest = {
        "manifest_version": "1.0.0",
        "candidate_suite": f"{suite['suite_id']}@{suite['suite_version']}",
        "suite_config": {
            "path": str(SUITE_PATH.relative_to(SCREENING)),
            "sha256": sha256(SUITE_PATH),
        },
        "approval_status": "calibration_pending_expert_gold",
        "benchmark_version": "v1_pending_codebook_and_disjoint_sets",
        "created_date": date.today().isoformat(),
        "change_note": (
            "Major-version candidate removes directional-language routing, model "
            "verifiers, model adjudication, and model section selection. It is not "
            "active until expert-gold accuracy and five-run stability gates pass."
        ),
        "artifacts": artifacts,
    }
    OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
