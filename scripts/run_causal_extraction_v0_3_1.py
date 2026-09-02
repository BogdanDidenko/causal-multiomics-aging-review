#!/usr/bin/env python3
"""Run the frozen v0.3.1 fixed-candidate classification ablation."""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.metadata
import json
import platform
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_analysis_inventory import (
    build_compact_report_packet,
    packet_atom_ids,
)
from causal_multiomics_aging_review.causal_candidate_classification import (
    normalize_candidate_response,
    render_candidate_scaffold,
    validate_candidate_response,
    validate_candidate_scaffold,
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

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = REPO / "protocol/causal_extraction/v0.3.1"
DEFAULT_OUTPUT = (
    REPO / "data/causal_extraction/v0.3.1_development/terra_5repeat"
)
INPUTS = REPO / "data/causal_extraction/v0.3.0_development/inputs"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_revision() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()


def git_dirty() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def atomic_append(path: Path, value: dict[str, Any], lock: threading.Lock) -> None:
    line = json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n"
    with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


@dataclass(frozen=True)
class CallSpec:
    report_id: str
    document_id: str
    repeat: int
    call_dir: Path
    prompt: str
    prompt_sha256: str
    candidate_report: dict[str, Any]


class V031Runner:
    def __init__(
        self,
        *,
        suite: Path,
        output: Path,
        workers: int | None,
        resume: bool,
        max_calls: int | None,
    ) -> None:
        self.suite = suite.resolve()
        self.output = output.resolve()
        self.runtime = read_json(self.suite / "runtime.json")
        self.sample = read_json(self.suite / "sample.json")
        self.freeze = read_json(self.suite / "freeze.json")
        self.manifest = read_json(self.suite / "artifact_manifest.json")
        self.scaffold = read_json(
            self.suite / str(self.runtime["candidate_scaffold"])
        )
        self.scaffold_reports = {
            report["document_id"]: report for report in self.scaffold["reports"]
        }
        self.source_schema = read_json(self.suite / str(self.runtime["schema"]))
        self.runtime_schema = codex_runtime_schema(self.source_schema)
        self.prompt_template = (self.suite / str(self.runtime["prompt"])).read_text(
            encoding="utf-8"
        )
        self.codebook = (self.suite / str(self.runtime["codebook"])).read_text(
            encoding="utf-8"
        )
        self.workers = workers or int(self.runtime["workers"])
        self.resume = resume
        self.max_calls = max_calls
        self.ledger_lock = threading.Lock()
        self.call_ledger = self.output / "call_ledger.jsonl"
        self.provider: CodexCliProvider | None = None

    def verify_freeze(self) -> None:
        manifest_path = self.suite / "artifact_manifest.json"
        if self.freeze["artifact_manifest_sha256"] != sha256_file(manifest_path):
            raise ValueError("v0.3.1 artifact manifest changed after freeze")
        if self.freeze["status"] != "frozen_before_first_v0_3_1_terra_output":
            raise ValueError("v0.3.1 suite is not frozen for model execution")
        for group in ("artifacts", "source_data"):
            for item in self.manifest[group]:
                path = REPO / item["path"]
                if not path.is_file() or sha256_file(path) != item["sha256"]:
                    raise ValueError(f"Frozen artifact changed: {item['path']}")

    def preflight(self) -> None:
        self.verify_freeze()
        if not self.resume and git_dirty():
            raise ValueError("Git worktree must be clean before a new v0.3.1 run")
        if self.output.exists() and any(self.output.iterdir()) and not self.resume:
            raise ValueError(f"Refusing to overwrite nonempty output: {self.output}")
        self.output.mkdir(parents=True, exist_ok=True)
        self.provider = CodexCliProvider(
            str(self.runtime["model"]),
            timeout=int(self.runtime["timeout_seconds"]),
            reasoning_effort=str(self.runtime["reasoning_effort"]),
            context_window=int(self.runtime["context_window"]),
            sandbox="read-only",
            approval_policy="never",
            ephemeral=True,
            ignore_user_config=True,
            ignore_rules=True,
            isolated_home=True,
            disabled_features=("plugins",),
            required_cli_version=str(self.runtime["codex_cli_version"]),
        )
        revision = git_revision()
        manifest_path = self.output / "orchestrator_manifest.json"
        if self.resume and manifest_path.is_file():
            previous = read_json(manifest_path)
            if previous["git_revision_at_start"] != revision:
                raise ValueError("Resume revision differs from the original run revision")
            if previous["suite_manifest_sha256"] != sha256_file(
                self.suite / "artifact_manifest.json"
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
                "status": "running",
                "started_at": now(),
                "development_only": True,
                "sample_reports": len(self.sample["reports"]),
                "candidate_count": sum(
                    len(report["candidates"])
                    for report in self.scaffold["reports"]
                ),
                "planned_calls": len(self.sample["reports"])
                * int(self.runtime["repeats"]),
                "model": self.runtime["model"],
                "reasoning_effort": self.runtime["reasoning_effort"],
                "provider": self.runtime["provider"],
                "codex_cli_version": self.provider.codex_version,
                "workers": self.workers,
                "git_revision_at_start": revision,
                "git_worktree_dirty_at_start": False,
                "suite_manifest_sha256": sha256_file(
                    self.suite / "artifact_manifest.json"
                ),
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
        for sampled in self.sample["reports"]:
            document_id = sampled["document_id"]
            atom_index = read_json(INPUTS / document_id / "evidence_atom_index.json")
            if atom_index["report_id"] != sampled["report_id"]:
                raise ValueError(f"Input report mismatch: {document_id}")
            if sha256_text(canonical_json(atom_index)) != sampled[
                "evidence_atom_index_sha256"
            ]:
                raise ValueError(f"Evidence-atom index changed: {document_id}")
            packet = build_compact_report_packet(atom_index)
            expected_atom_ids = [atom["evidence_atom_id"] for atom in atom_index["atoms"]]
            if packet_atom_ids(packet) != expected_atom_ids:
                raise ValueError(f"Compact packet omitted or reordered atoms: {document_id}")
            candidate_report = self.scaffold_reports[document_id]
            scaffold_errors = validate_candidate_scaffold(candidate_report, atom_index)
            if scaffold_errors:
                raise ValueError(f"Invalid scaffold for {document_id}: {scaffold_errors}")
            rendered_scaffold = render_candidate_scaffold(candidate_report)
            prompt = render_prompt(
                self.prompt_template,
                {
                    "REPORT_ID": str(sampled["report_id"]),
                    "CODEBOOK": self.codebook,
                    "CANDIDATE_SCAFFOLD": rendered_scaffold,
                    "REPORT_PACKET": packet,
                },
            )
            if token_count(prompt) > int(self.runtime["max_rendered_prompt_tokens"]):
                raise ValueError(f"Rendered prompt exceeds token limit: {document_id}")
            input_dir = self.output / "inputs" / document_id
            write_text(input_dir / "report_packet.txt", packet)
            write_text(input_dir / "candidate_scaffold.txt", rendered_scaffold)
            write_json(
                input_dir / "input_manifest.json",
                {
                    "report_id": sampled["report_id"],
                    "document_id": document_id,
                    "atom_count": len(expected_atom_ids),
                    "candidate_count": len(candidate_report["candidates"]),
                    "atom_ids_sha256": sha256_text(canonical_json(expected_atom_ids)),
                    "packet_sha256": sha256_text(packet),
                    "candidate_scaffold_sha256": sha256_text(rendered_scaffold),
                    "rendered_prompt_sha256": sha256_text(prompt),
                    "rendered_prompt_tokens": token_count(prompt),
                },
            )
            for repeat in range(1, int(self.runtime["repeats"]) + 1):
                calls.append(
                    CallSpec(
                        report_id=str(sampled["report_id"]),
                        document_id=document_id,
                        repeat=repeat,
                        call_dir=(
                            self.output
                            / "calls"
                            / document_id
                            / f"repeat-{repeat:02d}"
                        ),
                        prompt=prompt,
                        prompt_sha256=sha256_text(prompt),
                        candidate_report=candidate_report,
                    )
                )
        return calls[: self.max_calls] if self.max_calls is not None else calls

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

    def run_call(self, spec: CallSpec) -> dict[str, Any]:
        if self.call_complete(spec):
            return {
                "report_id": spec.report_id,
                "document_id": spec.document_id,
                "repeat": spec.repeat,
                "status": "already_complete",
            }
        spec.call_dir.mkdir(parents=True, exist_ok=True)
        write_text(spec.call_dir / "rendered_prompt.txt", spec.prompt)
        write_json(
            spec.call_dir / "request.json",
            {
                "report_id": spec.report_id,
                "document_id": spec.document_id,
                "repeat": spec.repeat,
                "model": self.runtime["model"],
                "reasoning_effort": self.runtime["reasoning_effort"],
                "prompt_sha256": spec.prompt_sha256,
                "schema_sha256": sha256_file(self.suite / self.runtime["schema"]),
                "technical_retry_limit": self.runtime["technical_retry_limit"],
            },
        )
        maximum_attempts = 1 + int(self.runtime["technical_retry_limit"])
        failures: list[dict[str, Any]] = []
        for attempt in range(1, maximum_attempts + 1):
            started = now()
            try:
                assert self.provider is not None
                parsed, raw = self.provider.complete_json(
                    spec.prompt,
                    self.runtime_schema,
                    schema_name="causal_candidate_classification_v0_3_1",
                )
                schema_errors = validate_schema(parsed, self.source_schema)
                semantic_errors = (
                    validate_candidate_response(
                        parsed,
                        expected_report_id=spec.report_id,
                        candidate_report=spec.candidate_report,
                    )
                    if not schema_errors
                    else []
                )
                errors = schema_errors + semantic_errors
                write_json(spec.call_dir / f"raw_response_attempt_{attempt}.json", raw)
                write_json(spec.call_dir / f"parsed_attempt_{attempt}.json", parsed)
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
                normalized = normalize_candidate_response(
                    parsed, spec.candidate_report
                )
                write_json(spec.call_dir / "normalized.json", normalized)
                validation = {
                    "valid": True,
                    "attempt": attempt,
                    "schema_errors": [],
                    "semantic_errors": [],
                    "prompt_sha256": spec.prompt_sha256,
                    "normalized_sha256": sha256_text(canonical_json(normalized)),
                    "finished_at": now(),
                }
                write_json(spec.call_dir / "validation.json", validation)
                ledger = {
                    "report_id": spec.report_id,
                    "document_id": spec.document_id,
                    "repeat": spec.repeat,
                    "status": "valid",
                    "attempts": attempt,
                    "candidate_count": len(normalized["candidates"]),
                    "included_count": sum(
                        item["qualification"] == "include"
                        for item in normalized["candidates"]
                    ),
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
            "report_id": spec.report_id,
            "document_id": spec.document_id,
            "repeat": spec.repeat,
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
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-calls", type=int)
    args = parser.parse_args()
    runner = V031Runner(
        suite=args.suite,
        output=args.output,
        workers=args.workers,
        resume=args.resume,
        max_calls=args.max_calls,
    )
    raise SystemExit(runner.run())


if __name__ == "__main__":
    main()
