#!/usr/bin/env python3
"""Recover causal-role calls skipped by the rejected v1.5.0 routing code."""

from __future__ import annotations

import argparse
import io
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.audit import (
    git_revision,
    git_worktree_dirty,
    sha256_file,
)
from causal_multiomics_aging_review.config import REPO_ROOT, load_stage_config
from causal_multiomics_aging_review.llm import CodexCliProvider
from causal_multiomics_aging_review.screening import (
    _execution_code_manifest,
    _format_sections,
    _load_stage_artifacts,
    _manifest_artifacts,
    run_shared_template_causal_role,
)
from causal_multiomics_aging_review.v1 import (
    agreement_audit,
    package_full_text_sections,
    scope_status,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(paths: list[Path]) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("primary_run", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--suite-config",
        type=Path,
        default=Path("protocol/screening/configs/prompt_suite_v1.5.1-rc1.json"),
    )
    parser.add_argument("--workers", type=int, default=7)
    args = parser.parse_args()

    suite, stage_config = load_stage_config("full_text", args.suite_config)
    artifacts = _load_stage_artifacts(stage_config)
    records = {
        row["record_id"]: row for row in read_jsonl([args.input])
    }
    primary_paths = sorted(
        (args.primary_run / "runs").glob("*/screening_results.jsonl")
    )
    primary = read_jsonl(primary_paths)
    recovery_targets: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for row in primary:
        role_runs = row.get("role_runs") or {}
        scope_runs = role_runs.get("scope_reviewer") or []
        causal_runs = role_runs.get("causal_method_reviewer") or []
        if (
            len(scope_runs) == int(stage_config["decision_repeats"])
            and all(scope_status(answer)[0] == "pass" for answer in scope_runs)
            and not causal_runs
        ):
            recovery_targets.append((records[row["record_id"]], scope_runs))

    expected = 14
    if len(recovery_targets) != expected:
        raise SystemExit(
            f"Expected {expected} missing causal evaluations, found "
            f"{len(recovery_targets)}"
        )

    provider_config = suite["provider"]
    runtime = suite["runtime"]
    provider = CodexCliProvider(
        provider_config["model"],
        codex_bin=provider_config.get("codex_bin", "codex"),
        timeout=runtime.get("codex_timeout_seconds", 900),
        reasoning_effort=runtime["reasoning_effort"],
        context_window=runtime["context_window"],
        sandbox=provider_config["sandbox"],
        approval_policy=provider_config["approval_policy"],
        ephemeral=provider_config["ephemeral"],
        ignore_user_config=provider_config["ignore_user_config"],
        ignore_rules=provider_config["ignore_rules"],
        isolated_home=provider_config["isolated_home"],
        disabled_features=tuple(provider_config.get("disabled_features", [])),
        required_cli_version=provider_config["codex_cli_version"],
        max_tokens=stage_config["max_tokens"],
    )

    minimum_words = int(
        stage_config["deterministic_evidence_grounding"]["minimum_words"]
    )
    repeats = int(stage_config["decision_repeats"])

    def recover(
        target: tuple[dict[str, Any], list[dict[str, Any]]],
    ) -> tuple[dict[str, Any], str]:
        record, scope_runs = target
        selected_sections, selection = package_full_text_sections(
            record["sections"], stage_config["deterministic_section_packaging"]
        )
        if selection["coverage_status"] != "sufficient":
            raise RuntimeError(f"Insufficient package for {record['record_id']}")
        raw = io.StringIO()
        causal_runs = run_shared_template_causal_role(
            record,
            selected_sections,
            _format_sections(selected_sections),
            artifacts,
            provider,
            raw,
            max_retries=int(runtime["max_retries"]),
            repeat_count=repeats,
            minimum_words=minimum_words,
            phase="v1.5.1-rc1_missing_causal_recovery",
        )
        result = {
            "record_id": record["record_id"],
            "title": record.get("title", ""),
            "source_scope_run": "v1.5.0-rc1_shared_templates",
            "scope_runs": scope_runs,
            "causal_method_reviewer_runs": causal_runs,
            "causal_role_agreement": agreement_audit(
                causal_runs,
                (
                    "current_report_application",
                    "causal_basis",
                    "design_families",
                    "causal_information_sufficiency",
                ),
            ),
            "section_selection": selection,
        }
        return result, raw.getvalue()

    args.output.mkdir(parents=True, exist_ok=False)
    started_at = now()
    recovered: list[dict[str, Any]] = []
    raw_by_id: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(recover, target): target[0]["record_id"]
            for target in recovery_targets
        }
        for future in as_completed(futures):
            result, raw = future.result()
            recovered.append(result)
            raw_by_id[result["record_id"]] = raw
            print(f"completed {result['record_id']}", flush=True)

    recovered.sort(key=lambda row: row["record_id"])
    results_path = args.output / "causal_recovery_results.jsonl"
    results_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in recovered),
        encoding="utf-8",
    )
    raw_path = args.output / "raw_provider_responses.jsonl"
    raw_path.write_text(
        "".join(raw_by_id[key] for key in sorted(raw_by_id)), encoding="utf-8"
    )
    manifest = {
        "status": "complete_missing_causal_recovery",
        "started_at": started_at,
        "completed_at": now(),
        "git_revision": git_revision(REPO_ROOT),
        "git_worktree_dirty": git_worktree_dirty(REPO_ROOT),
        "suite_version": suite["suite_version"],
        "suite_config": str(args.suite_config),
        "suite_config_sha256": sha256_file(args.suite_config),
        "model": provider.model,
        "reasoning_effort": provider.reasoning_effort,
        "input": str(args.input),
        "input_sha256": sha256_file(args.input),
        "primary_run": str(args.primary_run),
        "primary_result_files": {
            str(path): sha256_file(path) for path in primary_paths
        },
        "artifacts": _manifest_artifacts(artifacts),
        "execution_code": _execution_code_manifest(),
        "recovery_runner_sha256": sha256_file(Path(__file__)),
        "records": len(recovered),
        "calls_per_record": repeats,
        "planned_model_calls": len(recovered) * repeats,
        "workers": args.workers,
        "result_sha256": sha256_file(results_path),
        "raw_provider_responses_sha256": sha256_file(raw_path),
        "record_ids": [row["record_id"] for row in recovered],
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
