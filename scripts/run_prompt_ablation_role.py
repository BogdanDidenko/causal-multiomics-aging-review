#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.audit import git_revision, sha256_file
from causal_multiomics_aging_review.config import REPO_ROOT, load_json
from causal_multiomics_aging_review.llm import CodexCliProvider, ProviderError
from causal_multiomics_aging_review.schema import SchemaError, validate_object
from causal_multiomics_aging_review.screening import render_prompt
from causal_multiomics_aging_review.v1 import (
    CAUSAL_DECISION_FIELDS,
    SCOPE_DECISION_FIELDS,
    agreement_audit,
    validate_causal_answer_consistency,
    validate_scope_answer_consistency,
    validate_title_evidence_spans,
)

SUITE_PATH = REPO_ROOT / "protocol/screening/configs/prompt_suite_v1.0.0.json"
ARTIFACTS = {
    "scope_A0": {
        "role": "scope_reviewer",
        "prompt": REPO_ROOT
        / "protocol/screening/prompts/title_abstract/v1.0.0/scope_reviewer.txt",
    },
    "scope_M": {
        "role": "scope_reviewer",
        "prompt": REPO_ROOT
        / "protocol/screening/prompts/title_abstract/ablation_v1.1.0/M/scope_reviewer.txt",
    },
    "causal_A0": {
        "role": "causal_method_reviewer",
        "prompt": REPO_ROOT
        / "protocol/screening/prompts/title_abstract/v1.0.0/causal_method_reviewer.txt",
    },
    "causal_D": {
        "role": "causal_method_reviewer",
        "prompt": REPO_ROOT
        / "protocol/screening/prompts/title_abstract/ablation_v1.1.0/D/causal_method_reviewer.txt",
    },
    "scope_S": {
        "role": "scope_reviewer",
        "prompt": REPO_ROOT
        / "protocol/screening/prompts/title_abstract/ablation_v1.2.0/S/scope_reviewer.txt",
    },
    "causal_C": {
        "role": "causal_method_reviewer",
        "prompt": REPO_ROOT
        / "protocol/screening/prompts/title_abstract/ablation_v1.2.0/C/causal_method_reviewer.txt",
    },
    "scope_T": {
        "role": "scope_reviewer",
        "prompt": REPO_ROOT
        / "protocol/screening/prompts/title_abstract/ablation_v1.3.0/T/scope_reviewer.txt",
    },
}
SCHEMAS = {
    "scope_reviewer": REPO_ROOT
    / "protocol/screening/schemas/title_abstract/v1.0.0/scope_reviewer.schema.json",
    "causal_method_reviewer": REPO_ROOT
    / "protocol/screening/schemas/title_abstract/v1.0.0/causal_method_reviewer.schema.json",
}


def read_records(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def execute_record(
    record: dict[str, str],
    *,
    provider: CodexCliProvider,
    role: str,
    prompt_template: str,
    schema: dict[str, Any],
    repeats: int,
    max_retries: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    identifier = record["record_id"]
    prompt = render_prompt(prompt_template, record)
    validator = (
        validate_scope_answer_consistency
        if role == "scope_reviewer"
        else validate_causal_answer_consistency
    )
    answers = []
    raw_rows = []
    failed_repeats = []
    retry_count = 0
    for repeat_index in range(1, repeats + 1):
        errors = []
        completed = False
        for attempt in range(1, max_retries + 2):
            attempt_prompt = prompt
            if errors:
                attempt_prompt += (
                    "\n\nCORRECTION: The previous response failed validation: "
                    f"{errors[-1]}. Return a corrected JSON object only."
                )
            raw: Any | None = None
            try:
                answer, raw = provider.complete_json(
                    attempt_prompt,
                    schema=schema,
                    schema_name=role,
                )
                validate_object(answer, schema)
                validate_title_evidence_spans(answer, record)
                validator(answer)
                answers.append(answer)
                raw_rows.append(
                    {
                        "record_id": identifier,
                        "role": role,
                        "repeat_index": repeat_index,
                        "attempt": attempt,
                        "status": "ok",
                        "response": raw,
                    }
                )
                retry_count += int(attempt > 1)
                completed = True
                break
            except (ProviderError, SchemaError, ValueError) as error:
                errors.append(str(error))
                failed_raw = raw
                if isinstance(error, ProviderError) and error.raw_response is not None:
                    failed_raw = error.raw_response
                audit = {
                    "record_id": identifier,
                    "role": role,
                    "repeat_index": repeat_index,
                    "attempt": attempt,
                    "status": "error",
                    "error": str(error),
                }
                if failed_raw is not None:
                    audit["response"] = failed_raw
                raw_rows.append(audit)
        if not completed:
            failed_repeats.append(
                {"repeat_index": repeat_index, "errors": errors}
            )

    fields = (
        SCOPE_DECISION_FIELDS
        if role == "scope_reviewer"
        else CAUSAL_DECISION_FIELDS
    )
    status = "ok" if len(answers) == repeats else "manual_review"
    return (
        {
            "record_id": identifier,
            "title": record.get("title", ""),
            "role": role,
            "status": status,
            "runs": answers,
            "agreement": agreement_audit(answers, fields) if answers else {},
            "repeat_count_expected": repeats,
            "repeat_count_valid": len(answers),
            "retry_success_count": retry_count,
            "failed_repeats": failed_repeats,
        },
        raw_rows,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one frozen role/prompt artifact for a prompt ablation"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--artifact", choices=sorted(ARTIFACTS), required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--codex-timeout", type=int)
    args = parser.parse_args()

    suite = load_json(SUITE_PATH)
    runtime = suite["runtime"]
    provider_config = suite["provider"]
    artifact = ARTIFACTS[args.artifact]
    role = artifact["role"]
    prompt_path = artifact["prompt"]
    schema_path = SCHEMAS[role]
    prompt = prompt_path.read_text(encoding="utf-8")
    schema = load_json(schema_path)
    records = read_records(args.input)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    result_path = args.output_dir / "role_results.jsonl"
    raw_path = args.output_dir / "raw_provider_responses.jsonl"
    completed_ids = set()
    if args.resume and result_path.exists():
        with result_path.open(encoding="utf-8") as handle:
            completed_ids = {
                str(json.loads(line)["record_id"])
                for line in handle
                if line.strip()
            }
    elif result_path.exists() or raw_path.exists():
        raise SystemExit(
            f"Refusing to overwrite {args.output_dir}; pass --resume or use a new directory"
        )
    pending = [row for row in records if row["record_id"] not in completed_ids]

    provider = CodexCliProvider(
        provider_config["model"],
        codex_bin=provider_config.get("codex_bin", "codex"),
        timeout=args.codex_timeout or runtime["codex_timeout_seconds"],
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
        max_tokens=suite["stages"]["title_abstract"]["max_tokens"],
    )
    lock = threading.Lock()
    modes = "a" if args.resume else "w"
    status_counts: dict[str, int] = {}
    with result_path.open(modes, encoding="utf-8") as result_handle, raw_path.open(
        modes, encoding="utf-8"
    ) as raw_handle:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            futures = {
                executor.submit(
                    execute_record,
                    record,
                    provider=provider,
                    role=role,
                    prompt_template=prompt,
                    schema=schema,
                    repeats=suite["stability_policy"]["repeats"],
                    max_retries=runtime["max_retries"],
                ): record["record_id"]
                for record in pending
            }
            for future in as_completed(futures):
                result, raw_rows = future.result()
                with lock:
                    for row in raw_rows:
                        raw_handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    result_handle.write(json.dumps(result, ensure_ascii=False) + "\n")
                    raw_handle.flush()
                    result_handle.flush()
                status = result["status"]
                status_counts[status] = status_counts.get(status, 0) + 1

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": "title_abstract_prompt_ablation_v1.1.0",
        "artifact": args.artifact,
        "role": role,
        "git_revision": git_revision(REPO_ROOT),
        "input_path": str(args.input.resolve().relative_to(REPO_ROOT)),
        "input_sha256": sha256_file(args.input),
        "input_records": len(records),
        "completed_before_resume": len(completed_ids),
        "processed_now": len(pending),
        "status_counts_now": status_counts,
        "prompt_path": str(prompt_path.relative_to(REPO_ROOT)),
        "prompt_sha256": sha256_file(prompt_path),
        "schema_path": str(schema_path.relative_to(REPO_ROOT)),
        "schema_sha256": sha256_file(schema_path),
        "suite_config_sha256": sha256_file(SUITE_PATH),
        "model": provider.model,
        "codex_cli_version": provider.codex_version,
        "reasoning_effort": provider.reasoning_effort,
        "context_window": provider.context_window,
        "repeats": suite["stability_policy"]["repeats"],
        "max_retries": runtime["max_retries"],
        "workers": args.workers,
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"artifact={args.artifact} processed={len(pending)} "
        + " ".join(f"{key}={value}" for key, value in sorted(status_counts.items()))
    )


if __name__ == "__main__":
    main()
