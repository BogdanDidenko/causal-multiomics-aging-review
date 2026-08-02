#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import csv
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
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def row_count(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def verify_file(item: dict[str, Any]) -> Path:
    path = repo_path(str(item["path"]))
    if not path.is_file():
        raise ValueError(f"Missing frozen input: {path}")
    actual_hash = sha256(path)
    if actual_hash != item["sha256"]:
        raise ValueError(
            f"SHA-256 mismatch for {path}: expected {item['sha256']}, got {actual_hash}"
        )
    if "records" in item and row_count(path) != int(item["records"]):
        raise ValueError(f"Record-count mismatch for {path}")
    return path


def write_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run_shard(
    shard: dict[str, Any],
    output_dir: Path,
    suite_config: Path,
    resume: bool,
) -> dict[str, Any]:
    input_path = repo_path(str(shard["path"]))
    name = input_path.stem
    run_dir = output_dir / name
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_screening.py"),
        str(input_path),
        str(run_dir),
        "--stage",
        "title_abstract",
        "--suite-config",
        str(suite_config),
    ]
    if resume:
        command.append("--resume")
    started_at = now()
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    (log_dir / f"{name}.stdout.log").write_text(completed.stdout, encoding="utf-8")
    (log_dir / f"{name}.stderr.log").write_text(completed.stderr, encoding="utf-8")
    result_path = run_dir / "screening_results.jsonl"
    result_records = 0
    if result_path.is_file():
        result_records = sum(1 for line in result_path.open(encoding="utf-8") if line.strip())
    return {
        "shard": name,
        "input_path": str(input_path.relative_to(REPO_ROOT)),
        "input_sha256": shard["sha256"],
        "expected_records": int(shard["records"]),
        "result_records": result_records,
        "returncode": completed.returncode,
        "started_at": started_at,
        "completed_at": now(),
        "stdout_log": str((log_dir / f"{name}.stdout.log").relative_to(REPO_ROOT)),
        "stderr_log": str((log_dir / f"{name}.stderr.log").relative_to(REPO_ROOT)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen full-corpus title/abstract shards with resume support"
    )
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--suite-config", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--allow-unvalidated-suite",
        action="store_true",
        help="explicitly permit a full-corpus evaluation with a non-active prompt suite",
    )
    args = parser.parse_args()
    if args.workers < 1:
        raise SystemExit("--workers must be positive")

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    suite_config = args.suite_config.resolve()
    input_manifest_path = input_dir / "input_manifest.json"
    input_manifest = read_json(input_manifest_path)
    suite = read_json(suite_config)
    approval_status = str(suite.get("approval_status", "unknown"))
    if approval_status != "active" and not args.allow_unvalidated_suite:
        raise SystemExit(
            f"Suite approval_status={approval_status!r}; pass "
            "--allow-unvalidated-suite to label this as a full-corpus evaluation"
        )

    verify_file(input_manifest["screening_input"])
    verify_file(input_manifest["missing_abstract_queue"])
    shards = list(input_manifest.get("shards", []))
    if not shards:
        raise SystemExit("Input manifest contains no shards")
    for shard in shards:
        verify_file(shard)
    if sum(int(shard["records"]) for shard in shards) != int(
        input_manifest["screening_input"]["records"]
    ):
        raise SystemExit("Shard record counts do not cover the screening input")

    if output_dir.exists() and any(output_dir.iterdir()) and not args.resume:
        raise SystemExit(f"Refusing to overwrite non-empty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "orchestrator_manifest.json"
    state: dict[str, Any] = {
        "status": "running",
        "run_classification": (
            "validated_production" if approval_status == "active" else "full_corpus_evaluation"
        ),
        "started_at": now(),
        "git_revision": git_revision(REPO_ROOT),
        "input_manifest": str(input_manifest_path.relative_to(REPO_ROOT)),
        "input_manifest_sha256": sha256(input_manifest_path),
        "screening_records": int(input_manifest["screening_input"]["records"]),
        "missing_abstract_records": int(input_manifest["missing_abstract_queue"]["records"]),
        "suite_config": str(suite_config.relative_to(REPO_ROOT)),
        "suite_config_sha256": sha256(suite_config),
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_approval_status": approval_status,
        "model": suite["provider"]["model"],
        "reasoning_effort": suite["runtime"]["reasoning_effort"],
        "repeats": suite["stages"]["title_abstract"]["decision_repeats"],
        "workers": args.workers,
        "resume": args.resume,
        "shards": [],
    }
    write_state(state_path, state)

    failures = []
    completed_results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(run_shard, shard, output_dir, suite_config, args.resume): shard
            for shard in shards
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            completed_results.append(result)
            if result["returncode"] != 0 or result["result_records"] != result["expected_records"]:
                failures.append(result["shard"])
            state["shards"] = sorted(completed_results, key=lambda item: item["shard"])
            state["completed_shards"] = len(completed_results)
            state["failed_shards"] = sorted(failures)
            write_state(state_path, state)
            print(
                f"{result['shard']} returncode={result['returncode']} "
                f"records={result['result_records']}/{result['expected_records']}",
                flush=True,
            )

    state["completed_at"] = now()
    state["status"] = "failed" if failures else "complete"
    state["completed_shards"] = len(completed_results)
    state["failed_shards"] = sorted(failures)
    state["result_records"] = sum(item["result_records"] for item in completed_results)
    write_state(state_path, state)
    if failures:
        raise SystemExit(f"Failed shards: {', '.join(sorted(failures))}")
    print(
        f"status=complete shards={len(completed_results)} records={state['result_records']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
