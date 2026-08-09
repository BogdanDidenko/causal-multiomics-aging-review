#!/usr/bin/env python3
"""Run frozen full-text JSONL shards with resumable parallel workers."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.audit import git_revision
from causal_multiomics_aging_review.config import REPO_ROOT


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def jsonl_count(path: Path) -> int:
    return sum(1 for line in path.open(encoding="utf-8") if line.strip())


def repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def verify(item: dict[str, Any]) -> Path:
    path = repo_path(str(item["path"]))
    if not path.is_file() or sha256(path) != item["sha256"]:
        raise ValueError(f"Frozen input missing or changed: {path}")
    if "records" in item and jsonl_count(path) != int(item["records"]):
        raise ValueError(f"Record count changed: {path}")
    return path


def write_state(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run_shard(
    shard: dict[str, Any], output: Path, suite: Path, resume: bool
) -> dict[str, Any]:
    source = repo_path(str(shard["path"]))
    target = output / "runs" / source.stem
    logs = output / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts/run_screening.py"),
        str(source),
        str(target),
        "--stage",
        "full_text",
        "--suite-config",
        str(suite),
    ]
    if resume:
        command.append("--resume")
    started_at = now()
    completed = subprocess.run(
        command, cwd=REPO_ROOT, check=False, capture_output=True, text=True
    )
    (logs / f"{source.stem}.stdout.log").write_text(completed.stdout, encoding="utf-8")
    (logs / f"{source.stem}.stderr.log").write_text(completed.stderr, encoding="utf-8")
    result_path = target / "screening_results.jsonl"
    result_records = jsonl_count(result_path) if result_path.is_file() else 0
    return {
        "shard": source.stem,
        "expected_records": int(shard["records"]),
        "result_records": result_records,
        "returncode": completed.returncode,
        "started_at": started_at,
        "completed_at": now(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--suite-config", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--allow-unvalidated-suite", action="store_true")
    args = parser.parse_args()
    input_dir = args.input_dir.resolve()
    output = args.output_dir.resolve()
    suite_path = args.suite_config.resolve()
    input_manifest_path = input_dir / "input_manifest.json"
    manifest = read_json(input_manifest_path)
    suite = read_json(suite_path)
    if suite.get("approval_status") != "active" and not args.allow_unvalidated_suite:
        raise SystemExit("Suite is not active; pass --allow-unvalidated-suite for evaluation")
    input_path = verify(manifest["input"])
    if jsonl_count(input_path) != int(manifest["records"]):
        raise SystemExit("Frozen input count does not match manifest")
    shards = manifest["shards"]
    for shard in shards:
        verify(shard)
    if sum(int(row["records"]) for row in shards) != int(manifest["records"]):
        raise SystemExit("Shard counts do not cover frozen input")
    if output.exists() and any(output.iterdir()) and not args.resume:
        raise SystemExit(f"Refusing to overwrite: {output}")
    output.mkdir(parents=True, exist_ok=True)
    state_path = output / "orchestrator_manifest.json"
    state: dict[str, Any] = {
        "status": "running",
        "run_classification": "full_corpus_evaluation_pending_expert_gold",
        "started_at": now(),
        "git_revision": git_revision(REPO_ROOT),
        "input_manifest": str(input_manifest_path.relative_to(REPO_ROOT)),
        "input_manifest_sha256": sha256(input_manifest_path),
        "records": int(manifest["records"]),
        "unique_doi": int(manifest["unique_doi"]),
        "suite_config": str(suite_path.relative_to(REPO_ROOT)),
        "suite_config_sha256": sha256(suite_path),
        "suite_approval_status": suite["approval_status"],
        "model": suite["provider"]["model"],
        "reasoning_effort": suite["runtime"]["reasoning_effort"],
        "roles": list(suite["stages"]["full_text"]["roles"]),
        "repeats_per_role": suite["stages"]["full_text"]["decision_repeats"],
        "workers": args.workers,
        "shards": [],
    }
    write_state(state_path, state)
    completed_rows: list[dict[str, Any]] = []
    failures: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(run_shard, row, output, suite_path, args.resume): row
            for row in shards
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            completed_rows.append(result)
            if result["returncode"] or result["result_records"] != result["expected_records"]:
                failures.append(result["shard"])
            state["shards"] = sorted(completed_rows, key=lambda row: row["shard"])
            state["completed_shards"] = len(completed_rows)
            state["failed_shards"] = sorted(failures)
            write_state(state_path, state)
            print(
                f"{result['shard']} returncode={result['returncode']} "
                f"records={result['result_records']}/{result['expected_records']}",
                flush=True,
            )
    state["status"] = "failed" if failures else "complete"
    state["completed_at"] = now()
    state["result_records"] = sum(row["result_records"] for row in completed_rows)
    write_state(state_path, state)
    if failures:
        raise SystemExit(f"Failed shards: {', '.join(sorted(failures))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
