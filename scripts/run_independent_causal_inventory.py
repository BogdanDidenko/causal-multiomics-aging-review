#!/usr/bin/env python3
"""Run frozen, independent causal-analysis inventories for 15 reports."""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.metadata
import json
import os
import platform
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_analysis_inventory import (
    build_compact_report_packet,
    normalize_reference_inventory,
    packet_atom_ids,
    validate_reference_inventory_semantics,
)
from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    codex_runtime_schema,
    read_json,
    render_prompt,
    sha256_file,
    sha256_text,
    token_count,
    validate_schema,
    write_json,
    write_text,
)
from causal_multiomics_aging_review.llm import CodexCliProvider, ProviderError
from causal_multiomics_aging_review.runtime_schema import inline_local_json_schema

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = REPO / "protocol/causal_extraction/validation/v0.3.1-independent-15-v1.0.0"
DEFAULT_INPUTS = REPO / "data/causal_extraction/v0.3.1_independent_validation/inputs"
DEFAULT_OUTPUT = (
    REPO / "data/causal_extraction/v0.3.1_independent_validation/independent_inventories"
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()


def git_dirty() -> bool:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    return bool(completed.stdout.strip())


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def executable_version(executable: str, timeout: int) -> str:
    completed = subprocess.run(
        [executable, "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=min(timeout, 30),
    )
    if completed.returncode:
        raise RuntimeError(f"Could not determine {executable} version: {completed.stderr.strip()}")
    return completed.stdout.strip()


def strip_code_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return text.strip()


def parse_claude_output(stdout: str) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise ProviderError(f"Invalid Claude CLI envelope: {error}") from error
    if not isinstance(envelope, dict):
        raise ProviderError("Claude CLI envelope is not a JSON object")

    structured = envelope.get("structured_output")
    if isinstance(structured, dict):
        return structured, envelope

    result = envelope.get("result")
    if isinstance(result, dict):
        return result, envelope
    if isinstance(result, str):
        try:
            parsed = json.loads(strip_code_fence(result))
        except json.JSONDecodeError as error:
            raise ProviderError(f"Invalid Claude CLI result JSON: {error}") from error
        if isinstance(parsed, dict):
            return parsed, envelope
    raise ProviderError("Claude CLI envelope has no structured JSON object")


def complete_claude_json(
    *,
    prompt: str,
    schema: dict[str, Any],
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    executable = str(config["executable"])
    command = [
        executable,
        "--print",
        "--output-format",
        "json",
        "--json-schema",
        canonical_json(schema),
        "--effort",
        str(config["effort"]),
        "--tools",
        "",
        "--safe-mode",
        "--no-session-persistence",
        "--permission-mode",
        "dontAsk",
        "--no-chrome",
        "--disable-slash-commands",
        "--prompt-suggestions",
        "false",
    ]
    with tempfile.TemporaryDirectory(prefix="causal-inventory-opus-") as directory:
        environment = os.environ.copy()
        environment["CLAUDE_CODE_SAFE_MODE"] = "1"
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                cwd=directory,
                env=environment,
                timeout=int(config["timeout_seconds"]),
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raw = {
                "transport": "claude_code_cli",
                "stdout": error.stdout.decode(errors="replace")
                if isinstance(error.stdout, bytes)
                else error.stdout,
                "stderr": error.stderr.decode(errors="replace")
                if isinstance(error.stderr, bytes)
                else error.stderr,
            }
            raise ProviderError(
                f"Claude CLI timed out after {config['timeout_seconds']} seconds",
                raw_response=raw,
            ) from error
        except OSError as error:
            raise ProviderError(f"Claude CLI execution failed: {error}") from error
    raw = {
        "transport": "claude_code_cli",
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode:
        raise ProviderError(
            f"Claude CLI exited with {completed.returncode}: {completed.stderr.strip()[:1000]}",
            raw_response=raw,
        )
    try:
        parsed, envelope = parse_claude_output(completed.stdout)
    except ProviderError as error:
        error.raw_response = raw
        raise
    raw["envelope"] = envelope
    return parsed, raw


def atomic_append(path: Path, value: dict[str, Any], lock: threading.Lock) -> None:
    line = json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n"
    with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


@dataclass(frozen=True)
class CallSpec:
    reviewer_id: str
    report_id: str
    document_id: str
    doi: str
    call_dir: Path
    prompt: str
    prompt_sha256: str
    atom_index: dict[str, Any]


class IndependentInventoryRunner:
    def __init__(
        self,
        *,
        suite: Path,
        inputs: Path,
        output: Path,
        reviewer_id: str,
        workers: int | None,
        resume: bool,
        max_reports: int | None,
    ) -> None:
        self.suite = suite.resolve()
        self.inputs = inputs.resolve()
        self.output_root = output.resolve()
        self.reviewer_id = reviewer_id
        self.runtime = read_json(self.suite / "runtime.json")
        self.config = self.runtime["reviewers"][reviewer_id]
        self.output = self.output_root / reviewer_id
        self.sample = read_json(self.suite / str(self.runtime["sample"]))
        self.source_schema = read_json(self.suite / str(self.runtime["schema"]))
        self.cli_schema = inline_local_json_schema(self.source_schema)
        self.codex_schema = codex_runtime_schema(self.cli_schema)
        self.task = (self.suite / str(self.runtime["task"])).read_text(encoding="utf-8")
        self.manual = (self.suite / str(self.runtime["annotation_manual"])).read_text(
            encoding="utf-8"
        )
        self.codebook = (self.suite / str(self.runtime["inherited_codebook"])).read_text(
            encoding="utf-8"
        )
        self.workers = workers or int(self.config["workers"])
        self.resume = resume
        self.max_reports = max_reports
        self.ledger_lock = threading.Lock()
        self.call_ledger = self.output / "call_ledger.jsonl"
        self.codex_provider: CodexCliProvider | None = None

    def verify_freeze(self) -> None:
        manifest_path = self.suite / "phase1b_artifact_manifest.json"
        freeze = read_json(self.suite / "phase1b_freeze.json")
        manifest = read_json(manifest_path)
        if freeze["artifact_manifest_sha256"] != sha256_file(manifest_path):
            raise ValueError("Independent-inventory phase-1b manifest changed after freeze")
        if freeze["status"] != "frozen_after_schema_fix_before_valid_outputs":
            raise ValueError("Independent-inventory suite is not in its frozen phase")
        for group in ("protocol_artifacts", "source_artifacts", "evidence_atom_indices"):
            for item in manifest[group]:
                path = REPO / item["path"]
                if not path.is_file() or sha256_file(path) != item["sha256"]:
                    raise ValueError(f"Frozen artifact changed: {item['path']}")

    def preflight(self) -> None:
        self.verify_freeze()
        if not self.resume and git_dirty():
            raise ValueError("Git worktree must be clean before independent annotations")
        if self.output.exists() and any(self.output.iterdir()) and not self.resume:
            raise ValueError(f"Refusing to overwrite nonempty output: {self.output}")
        self.output.mkdir(parents=True, exist_ok=True)

        required_version = str(self.config["required_cli_version"])
        observed_version = executable_version(
            str(self.config["executable"]), int(self.config["timeout_seconds"])
        )
        if observed_version != required_version:
            raise ValueError(
                f"{self.reviewer_id} CLI version {observed_version!r} does not match "
                f"frozen version {required_version!r}"
            )
        if self.config["provider"] == "codex_cli":
            self.codex_provider = CodexCliProvider(
                str(self.config["model"]),
                timeout=int(self.config["timeout_seconds"]),
                reasoning_effort=str(self.config["reasoning_effort"]),
                context_window=int(self.config["context_window"]),
                sandbox=str(self.config["session_policy"]["sandbox"]),
                approval_policy="never",
                ephemeral=True,
                ignore_user_config=True,
                ignore_rules=True,
                isolated_home=True,
                disabled_features=("plugins",),
                required_cli_version=required_version,
            )

        revision = git_revision()
        manifest_path = self.output / "orchestrator_manifest.json"
        if self.resume and manifest_path.is_file():
            previous = read_json(manifest_path)
            if previous["git_revision_at_start"] != revision:
                raise ValueError("Resume revision differs from the original run revision")
            if previous["suite_manifest_sha256"] != sha256_file(
                self.suite / "phase1b_artifact_manifest.json"
            ):
                raise ValueError("Resume suite manifest mismatch")
            previous["status"] = "running"
            previous["resumed_at"] = now()
            write_json(manifest_path, previous)
            return

        write_json(
            manifest_path,
            {
                "experiment_id": self.runtime["experiment_id"],
                "reviewer_id": self.reviewer_id,
                "status": "running",
                "started_at": now(),
                "sample_reports": len(self.sample["reports"]),
                "planned_calls": len(self.sample["reports"]),
                "provider": self.config["provider"],
                "model": self.config["model"],
                "effort": self.config.get("reasoning_effort", self.config.get("effort")),
                "cli_version": observed_version,
                "workers": self.workers,
                "git_revision_at_start": revision,
                "git_worktree_dirty_at_start": False,
                "suite_manifest_sha256": sha256_file(self.suite / "phase1b_artifact_manifest.json"),
                "runner_path": relative(Path(__file__)),
                "runner_sha256": sha256_file(Path(__file__)),
                "environment": {
                    "python": platform.python_version(),
                    "jsonschema": importlib.metadata.version("jsonschema"),
                    "tiktoken": importlib.metadata.version("tiktoken"),
                },
            },
        )

    def build_calls(self) -> list[CallSpec]:
        calls: list[CallSpec] = []
        maximum_tokens = int(self.runtime["packaging"]["max_rendered_prompt_tokens"])
        for sampled in self.sample["reports"]:
            document_id = sampled["document_id"]
            atom_index = read_json(self.inputs / document_id / "evidence_atom_index.json")
            if atom_index["report_id"] != sampled["report_id"]:
                raise ValueError(f"Input report mismatch: {document_id}")
            if sha256_text(canonical_json(atom_index)) != sampled["evidence_atom_index_sha256"]:
                raise ValueError(f"Evidence-atom index changed: {document_id}")
            packet = build_compact_report_packet(atom_index)
            source_ids = [atom["evidence_atom_id"] for atom in atom_index["atoms"]]
            if packet_atom_ids(packet) != source_ids:
                raise ValueError(f"Compact packet coverage mismatch: {document_id}")
            prompt = render_prompt(
                self.task,
                {
                    "REVIEWER_ID": self.reviewer_id,
                    "REPORT_ID": str(sampled["report_id"]),
                    "ANNOTATION_MANUAL": self.manual,
                    "CODEBOOK": self.codebook,
                    "REPORT_PACKET": packet,
                },
            )
            prompt_tokens = token_count(prompt)
            if prompt_tokens > maximum_tokens:
                raise ValueError(f"Rendered prompt exceeds token limit: {document_id}")
            input_dir = self.output / "inputs" / document_id
            write_text(input_dir / "report_packet.txt", packet)
            write_json(
                input_dir / "input_manifest.json",
                {
                    "report_id": sampled["report_id"],
                    "document_id": document_id,
                    "doi": sampled["doi"],
                    "atom_count": len(source_ids),
                    "atom_ids_sha256": sha256_text(canonical_json(source_ids)),
                    "packet_sha256": sha256_text(packet),
                    "rendered_prompt_sha256": sha256_text(prompt),
                    "rendered_prompt_tokens": prompt_tokens,
                },
            )
            calls.append(
                CallSpec(
                    reviewer_id=self.reviewer_id,
                    report_id=str(sampled["report_id"]),
                    document_id=document_id,
                    doi=str(sampled["doi"]),
                    call_dir=self.output / "calls" / document_id,
                    prompt=prompt,
                    prompt_sha256=sha256_text(prompt),
                    atom_index=atom_index,
                )
            )
        return calls[: self.max_reports] if self.max_reports is not None else calls

    def call_complete(self, spec: CallSpec) -> bool:
        if not self.resume:
            return False
        validation = spec.call_dir / "validation.json"
        normalized = spec.call_dir / "normalized.json"
        return (
            validation.is_file()
            and normalized.is_file()
            and read_json(validation).get("valid") is True
        )

    def complete_json(self, prompt: str) -> tuple[dict[str, Any], dict[str, Any]]:
        if self.config["provider"] == "codex_cli":
            assert self.codex_provider is not None
            return self.codex_provider.complete_json(
                prompt,
                self.codex_schema,
                schema_name="independent_causal_inventory_v1_0_0",
            )
        if self.config["provider"] == "claude_code_cli":
            return complete_claude_json(
                prompt=prompt,
                schema=self.cli_schema,
                config=self.config,
            )
        raise ValueError(f"Unsupported provider: {self.config['provider']}")

    def run_call(self, spec: CallSpec) -> dict[str, Any]:
        if self.call_complete(spec):
            return {
                "report_id": spec.report_id,
                "document_id": spec.document_id,
                "doi": spec.doi,
                "status": "already_complete",
            }
        spec.call_dir.mkdir(parents=True, exist_ok=True)
        write_text(spec.call_dir / "rendered_prompt.txt", spec.prompt)
        write_json(
            spec.call_dir / "request.json",
            {
                "reviewer_id": spec.reviewer_id,
                "report_id": spec.report_id,
                "document_id": spec.document_id,
                "doi": spec.doi,
                "model": self.config["model"],
                "effort": self.config.get("reasoning_effort", self.config.get("effort")),
                "prompt_sha256": spec.prompt_sha256,
                "schema_sha256": sha256_file(self.suite / self.runtime["schema"]),
                "technical_retry_limit": self.runtime["technical_retry_limit"],
            },
        )
        failures: list[dict[str, Any]] = []
        maximum_attempts = 1 + int(self.runtime["technical_retry_limit"])
        for attempt in range(1, maximum_attempts + 1):
            started = now()
            try:
                parsed, raw = self.complete_json(spec.prompt)
                write_json(spec.call_dir / f"raw_response_attempt_{attempt}.json", raw)
                write_json(spec.call_dir / f"parsed_attempt_{attempt}.json", parsed)
                schema_errors = validate_schema(parsed, self.source_schema)
                semantic_errors = (
                    validate_reference_inventory_semantics(
                        parsed,
                        expected_reviewer_id=spec.reviewer_id,
                        expected_report_id=spec.report_id,
                        atom_index=spec.atom_index,
                    )
                    if not schema_errors
                    else []
                )
                errors = schema_errors + semantic_errors
                if errors:
                    failure = {
                        "attempt": attempt,
                        "started_at": started,
                        "finished_at": now(),
                        "kind": "validation_error",
                        "errors": errors,
                    }
                    failures.append(failure)
                    write_json(spec.call_dir / f"failure_attempt_{attempt}.json", failure)
                    continue

                normalized = normalize_reference_inventory(parsed, spec.atom_index)
                write_json(spec.call_dir / "normalized.json", normalized)
                validation = {
                    "valid": True,
                    "attempt": attempt,
                    "schema_errors": [],
                    "semantic_errors": [],
                    "prompt_sha256": spec.prompt_sha256,
                    "normalized_sha256": sha256_text(canonical_json(normalized)),
                    "started_at": started,
                    "finished_at": now(),
                }
                write_json(spec.call_dir / "validation.json", validation)
                ledger = {
                    "reviewer_id": spec.reviewer_id,
                    "report_id": spec.report_id,
                    "document_id": spec.document_id,
                    "doi": spec.doi,
                    "status": "valid",
                    "attempts": attempt,
                    "qualifying_analysis_count": len(normalized["qualifying_analyses"]),
                    "boundary_candidate_count": len(normalized["excluded_boundary_candidates"]),
                    "normalized_sha256": validation["normalized_sha256"],
                    "finished_at": validation["finished_at"],
                }
                atomic_append(self.call_ledger, ledger, self.ledger_lock)
                return ledger
            except ProviderError as error:
                failure = {
                    "attempt": attempt,
                    "started_at": started,
                    "finished_at": now(),
                    "kind": "provider_error",
                    "message": str(error),
                    "raw_response": error.raw_response,
                }
                failures.append(failure)
                write_json(spec.call_dir / f"failure_attempt_{attempt}.json", failure)

        validation = {
            "valid": False,
            "attempts": maximum_attempts,
            "failures": failures,
            "prompt_sha256": spec.prompt_sha256,
            "finished_at": now(),
        }
        write_json(spec.call_dir / "validation.json", validation)
        ledger = {
            "reviewer_id": spec.reviewer_id,
            "report_id": spec.report_id,
            "document_id": spec.document_id,
            "doi": spec.doi,
            "status": "failed",
            "attempts": maximum_attempts,
            "finished_at": validation["finished_at"],
        }
        atomic_append(self.call_ledger, ledger, self.ledger_lock)
        return ledger

    def run(self) -> int:
        self.preflight()
        calls = self.build_calls()
        results: list[dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.run_call, spec): spec for spec in calls}
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        failed = [result for result in results if result["status"] == "failed"]
        manifest_path = self.output / "orchestrator_manifest.json"
        manifest = read_json(manifest_path)
        manifest.update(
            {
                "status": "complete" if not failed else "complete_with_failures",
                "finished_at": now(),
                "executed_or_resumed_calls": len(results),
                "valid_or_existing_calls": len(results) - len(failed),
                "failed_calls": len(failed),
            }
        )
        write_json(manifest_path, manifest)
        write_json(
            self.output / "completion.json",
            {
                "status": manifest["status"],
                "calls": len(results),
                "failed_calls": len(failed),
                "finished_at": manifest["finished_at"],
            },
        )
        return 1 if failed else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer", choices=("codex", "claude_opus_4_8"), required=True)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-reports", type=int)
    args = parser.parse_args()
    runner = IndependentInventoryRunner(
        suite=args.suite,
        inputs=args.inputs,
        output=args.output,
        reviewer_id=args.reviewer,
        workers=args.workers,
        resume=args.resume,
        max_reports=args.max_reports,
    )
    raise SystemExit(runner.run())


if __name__ == "__main__":
    main()
