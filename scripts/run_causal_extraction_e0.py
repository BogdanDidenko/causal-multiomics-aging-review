#!/usr/bin/env python3
"""Run the frozen E0 quote-versus-evidence-ID grounding experiment."""

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

from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    canonical_sections,
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
from causal_multiomics_aging_review.evidence_atoms import (
    build_evidence_atom_index,
    build_evidence_atom_windows,
    evidence_packet,
    resolve_atom_grounding,
    resolve_quote_grounding,
    validate_atom_grounding,
    validate_quote_grounding,
)
from causal_multiomics_aging_review.llm import CodexCliProvider, ProviderError

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = REPO / "protocol/causal_extraction/e0_grounding/v0.1.0"
DEFAULT_OUTPUT = REPO / "data/causal_extraction/e0_grounding/v0.1.0_run1"
CORPUS = REPO / "data/full_text_screening/v1.5.3_deterministic_full_text_158/input.jsonl"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()


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
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path.resolve())


def load_corpus() -> dict[str, dict[str, Any]]:
    return {
        record["record_id"]: record
        for record in (
            json.loads(line)
            for line in CORPUS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def atomic_append_jsonl(path: Path, value: dict[str, Any], lock: threading.Lock) -> None:
    line = json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n"
    with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


@dataclass(frozen=True)
class CallSpec:
    arm: str
    report_id: str
    document_id: str
    work_unit_id: str
    repeat: int
    output_dir: Path
    prompt: str
    source_schema: dict[str, Any]
    runtime_schema: dict[str, Any]
    packet: list[dict[str, Any]]
    core_atom_ids: set[str]
    atom_index: dict[str, Any]


class E0Runner:
    def __init__(
        self,
        *,
        suite: Path,
        output: Path,
        workers: int | None,
        resume: bool,
        max_calls: int | None,
        prepare_only: bool,
    ) -> None:
        self.suite = suite.resolve()
        self.output = output.resolve()
        self.runtime = read_json(self.suite / "runtime.json")
        self.sample = read_json(self.suite / "sample.json")
        self.freeze = read_json(self.suite / "freeze.json")
        self.manifest = read_json(self.suite / "artifact_manifest.json")
        self.corpus = load_corpus()
        self.records = [self.corpus[item["report_id"]] for item in self.sample["reports"]]
        self.workers = workers or int(self.runtime["workers"])
        self.resume = resume
        self.max_calls = max_calls
        self.prepare_only = prepare_only
        self.ledger_lock = threading.Lock()
        self.call_ledger = self.output / "call_ledger.jsonl"
        self.provider: CodexCliProvider | None = None

    def _verify_freeze(self) -> None:
        manifest_path = self.suite / "artifact_manifest.json"
        if self.freeze["artifact_manifest_sha256"] != sha256_file(manifest_path):
            raise ValueError("E0 artifact manifest changed after freeze")
        for group in ("artifacts", "source_data"):
            for item in self.manifest[group]:
                path = REPO / item["path"]
                if not path.is_file() or sha256_file(path) != item["sha256"]:
                    raise ValueError(f"Frozen E0 artifact changed: {item['path']}")
        if self.freeze["status"] != "frozen_before_any_e0_terra_output":
            raise ValueError("E0 package is not in a runnable frozen state")
        if self.sample["sampling_frame"]["genuinely_sealed"] is not False:
            raise ValueError("E0 must remain explicitly development-only")

    def preflight(self) -> None:
        self._verify_freeze()
        if not self.resume and git_dirty():
            raise ValueError("Git worktree must be clean before a new E0 run")
        if self.output.exists() and any(self.output.iterdir()) and not self.resume:
            raise ValueError(f"Refusing to overwrite {self.output}")
        self.output.mkdir(parents=True, exist_ok=True)
        if not self.prepare_only:
            self.provider = CodexCliProvider(
                self.runtime["model"],
                timeout=900,
                reasoning_effort=self.runtime["reasoning_effort"],
                context_window=self.runtime["context_window"],
                sandbox="read-only",
                approval_policy="never",
                ephemeral=True,
                ignore_user_config=True,
                ignore_rules=True,
                isolated_home=True,
                disabled_features=("plugins",),
            )
        current_revision = git_revision()
        manifest_path = self.output / "orchestrator_manifest.json"
        if self.resume and manifest_path.is_file():
            previous = read_json(manifest_path)
            if previous["git_revision_at_start"] != current_revision:
                raise ValueError("Resume revision differs from the frozen run revision")
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
                "suite_version": self.runtime["version"],
                "status": "prepared" if self.prepare_only else "running",
                "started_at": now(),
                "development_only": True,
                "sample_reports": len(self.records),
                "model": self.runtime["model"],
                "reasoning_effort": self.runtime["reasoning_effort"],
                "provider": self.runtime["provider"],
                "codex_cli_version": (
                    self.provider.codex_version if self.provider is not None else None
                ),
                "workers": self.workers,
                "git_revision_at_start": current_revision,
                "git_worktree_dirty_at_start": False,
                "suite_manifest_sha256": sha256_file(self.suite / "artifact_manifest.json"),
                "runner_path": relative(Path(__file__)),
                "runner_sha256": sha256_file(Path(__file__)),
                "environment": {
                    "python": platform.python_version(),
                    "jsonschema": importlib.metadata.version("jsonschema"),
                    "tiktoken": importlib.metadata.version("tiktoken"),
                },
            },
        )

    def prepare_inputs(self) -> dict[str, dict[str, Any]]:
        indexes: dict[str, dict[str, Any]] = {}
        inventory = []
        atom_config = self.runtime["atomization"]
        window_config = self.runtime["packaging"]
        for record in self.records:
            expected = next(
                item for item in self.sample["reports"] if item["report_id"] == record["record_id"]
            )
            section_hash = sha256_text(canonical_json(record["sections"]))
            if section_hash != expected["canonical_sections_sha256"]:
                raise ValueError(f"Sampled report changed: {record['record_id']}")
            atom_index = build_evidence_atom_index(
                record,
                max_atom_characters=int(atom_config["max_atom_characters"]),
            )
            windows = build_evidence_atom_windows(
                atom_index,
                max_core_characters=int(window_config["max_core_characters"]),
                context_characters_per_side=int(window_config["context_characters_per_side"]),
                max_core_atoms=int(window_config["max_core_atoms"]),
                max_context_atoms_per_side=int(window_config["max_context_atoms_per_side"]),
            )
            indexes[record["record_id"]] = atom_index
            report_dir = self.output / "inputs" / record["document_id"]
            write_json(
                report_dir / "record_metadata.json",
                {
                    key: record.get(key)
                    for key in (
                        "record_id",
                        "document_id",
                        "doi",
                        "title",
                        "year",
                        "source",
                    )
                },
            )
            write_text(
                report_dir / "canonical_sections.jsonl",
                "".join(
                    json.dumps(section, ensure_ascii=False, sort_keys=True) + "\n"
                    for section in canonical_sections(record)
                ),
            )
            write_json(report_dir / "evidence_atom_index.json", atom_index)
            write_json(report_dir / "work_units.json", windows)
            core_ids = [atom_id for window in windows for atom_id in window["core_atom_ids"]]
            expected_ids = [atom["evidence_atom_id"] for atom in atom_index["atoms"]]
            coverage = {
                **atom_index["coverage"],
                "work_unit_count": len(windows),
                "core_atom_occurrences": len(core_ids),
                "core_atom_unique": len(set(core_ids)),
                "all_atoms_core_exactly_once": (
                    sorted(core_ids) == sorted(expected_ids) and len(core_ids) == len(set(core_ids))
                ),
                "maximum_core_characters_observed": max(
                    window["core_character_count"] for window in windows
                ),
                "maximum_core_atoms_observed": max(window["core_atom_count"] for window in windows),
            }
            if not coverage["all_atoms_core_exactly_once"]:
                raise ValueError(f"Incomplete E0 coverage: {record['record_id']}")
            write_json(report_dir / "coverage.json", coverage)
            inventory.append(
                {
                    "report_id": record["record_id"],
                    "document_id": record["document_id"],
                    "doi": record["doi"],
                    "document_sha256": atom_index["document_sha256"],
                    "atom_count": len(atom_index["atoms"]),
                    "work_unit_count": len(windows),
                    "coverage_complete": True,
                }
            )
        write_json(
            self.output / "preflight" / "source_inventory.json",
            {"reports": inventory},
        )
        return indexes

    def build_specs(self, indexes: dict[str, dict[str, Any]]) -> list[CallSpec]:
        template = (self.suite / "prompts/inventory_template.txt").read_text(encoding="utf-8")
        specs: list[CallSpec] = []
        prompt_inventory = []
        for record in self.records:
            atom_index = indexes[record["record_id"]]
            report_dir = self.output / "inputs" / record["document_id"]
            windows = json.loads((report_dir / "work_units.json").read_text(encoding="utf-8"))
            for window in windows:
                packet = evidence_packet(atom_index, window)
                packet_json = json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
                for arm, config in self.runtime["arms"].items():
                    grounding = (self.suite / config["grounding_contract"]).read_text(
                        encoding="utf-8"
                    )
                    source_schema = read_json(self.suite / config["schema"])
                    runtime_schema = codex_runtime_schema(source_schema)
                    prompt = render_prompt(
                        template,
                        {
                            "GROUNDING_CONTRACT": grounding,
                            "REPORT_TITLE": record["title"],
                            "SECTION_INDEX_JSON": json.dumps(
                                [
                                    {
                                        "section_id": section["section_id"],
                                        "heading": section["heading"],
                                        "page_numbers": section["page_numbers"],
                                    }
                                    for section in atom_index["sections"]
                                    if section["section_id"]
                                    in {
                                        *window["core_section_ids"],
                                        *window["context_section_ids"],
                                    }
                                ],
                                ensure_ascii=False,
                                separators=(",", ":"),
                            ),
                            "CORE_SECTION_IDS_JSON": json.dumps(
                                window["core_section_ids"], ensure_ascii=False
                            ),
                            "CONTEXT_SECTION_IDS_JSON": json.dumps(
                                window["context_section_ids"], ensure_ascii=False
                            ),
                            "EVIDENCE_ATOMS_JSON": packet_json,
                        },
                    )
                    prompt_tokens = token_count(prompt)
                    if prompt_tokens > int(
                        self.runtime["packaging"]["maximum_rendered_prompt_tokens"]
                    ):
                        raise ValueError(
                            f"Rendered prompt exceeds frozen limit: {record['record_id']} "
                            f"{window['work_unit_id']} {arm} {prompt_tokens}"
                        )
                    prompt_inventory.append(
                        {
                            "arm": arm,
                            "report_id": record["record_id"],
                            "work_unit_id": window["work_unit_id"],
                            "prompt_sha256": sha256_text(prompt),
                            "prompt_tokens": prompt_tokens,
                            "packet_sha256": sha256_text(packet_json),
                            "packet_atom_count": len(packet),
                        }
                    )
                    for repeat in range(1, int(self.runtime["repeats_per_arm"]) + 1):
                        specs.append(
                            CallSpec(
                                arm=arm,
                                report_id=record["record_id"],
                                document_id=record["document_id"],
                                work_unit_id=window["work_unit_id"],
                                repeat=repeat,
                                output_dir=(
                                    self.output
                                    / "calls"
                                    / arm
                                    / record["document_id"]
                                    / window["work_unit_id"]
                                    / f"repeat-{repeat:02d}"
                                ),
                                prompt=prompt,
                                source_schema=source_schema,
                                runtime_schema=runtime_schema,
                                packet=packet,
                                core_atom_ids=set(window["core_atom_ids"]),
                                atom_index=atom_index,
                            )
                        )
        write_json(
            self.output / "preflight" / "prompt_inventory.json",
            {
                "unique_arm_work_units": len(prompt_inventory),
                "planned_calls": len(specs),
                "items": prompt_inventory,
            },
        )
        return specs

    def _terminal_reusable(self, path: Path) -> bool:
        if not path.is_file():
            return False
        return read_json(path).get("status") in {
            "ok",
            "technical_failure",
            "schema_failure",
            "grounding_failure",
        }

    def execute_call(self, spec: CallSpec) -> dict[str, Any]:
        terminal_path = spec.output_dir / "terminal.json"
        if self.resume and self._terminal_reusable(terminal_path):
            return read_json(terminal_path)
        if self.provider is None:
            raise RuntimeError("Provider is unavailable in prepare-only mode")

        last_terminal: dict[str, Any] | None = None
        for attempt in range(1, int(self.runtime["technical_retry_limit"]) + 2):
            attempt_dir = spec.output_dir / f"attempt-{attempt:02d}"
            attempt_dir.mkdir(parents=True, exist_ok=True)
            write_text(attempt_dir / "rendered_prompt.txt", spec.prompt)
            write_text(
                attempt_dir / "rendered_prompt.sha256",
                sha256_text(spec.prompt) + "\n",
            )
            write_json(attempt_dir / "output_schema.json", spec.runtime_schema)
            write_text(
                attempt_dir / "output_schema.sha256",
                sha256_text(canonical_json(spec.runtime_schema)) + "\n",
            )
            write_json(
                attempt_dir / "request_metadata.json",
                {
                    "experiment_id": self.runtime["experiment_id"],
                    "arm": spec.arm,
                    "report_id": spec.report_id,
                    "document_id": spec.document_id,
                    "work_unit_id": spec.work_unit_id,
                    "repeat": spec.repeat,
                    "attempt": attempt,
                    "model": self.runtime["model"],
                    "reasoning_effort": self.runtime["reasoning_effort"],
                    "git_revision": git_revision(),
                    "started_at": now(),
                    "prompt_sha256": sha256_text(spec.prompt),
                    "packet_sha256": sha256_text(
                        json.dumps(
                            spec.packet,
                            ensure_ascii=False,
                            separators=(",", ":"),
                        )
                    ),
                },
            )
            try:
                response, raw = self.provider.complete_json(
                    spec.prompt,
                    spec.runtime_schema,
                    schema_name=f"e0_{spec.arm}",
                )
            except ProviderError as error:
                raw = error.raw_response or {}
                if isinstance(raw, dict):
                    write_json(attempt_dir / "raw_provider_response.json", raw)
                    write_text(attempt_dir / "raw_stdout.txt", str(raw.get("stdout", "")))
                    write_text(attempt_dir / "raw_stderr.txt", str(raw.get("stderr", "")))
                else:
                    write_text(attempt_dir / "raw_provider_response.txt", str(raw))
                write_json(
                    attempt_dir / "validation.json",
                    {
                        "schema_valid": False,
                        "grounding_valid": False,
                        "provider_error": str(error),
                    },
                )
                last_terminal = {
                    "status": "technical_failure",
                    "arm": spec.arm,
                    "report_id": spec.report_id,
                    "document_id": spec.document_id,
                    "work_unit_id": spec.work_unit_id,
                    "repeat": spec.repeat,
                    "attempts": attempt,
                    "error": str(error),
                }
                write_json(attempt_dir / "exit_status.json", last_terminal)
                continue

            write_json(attempt_dir / "raw_provider_response.json", raw)
            write_text(attempt_dir / "raw_stdout.txt", str(raw.get("stdout", "")))
            write_text(attempt_dir / "raw_stderr.txt", str(raw.get("stderr", "")))
            write_json(attempt_dir / "parsed_response.json", response)
            schema_errors = validate_schema(response, spec.source_schema)
            if spec.arm == "evidence_atom_id":
                grounding_failures = validate_atom_grounding(
                    response,
                    spec.packet,
                    core_atom_ids=spec.core_atom_ids,
                )
            else:
                grounding_failures = validate_quote_grounding(
                    response,
                    spec.packet,
                    core_atom_ids=spec.core_atom_ids,
                )
            validation = {
                "schema_valid": not schema_errors,
                "schema_errors": schema_errors,
                "grounding_valid": not grounding_failures,
                "grounding_failures": grounding_failures,
            }
            write_json(attempt_dir / "validation.json", validation)
            if schema_errors:
                status = "schema_failure"
            elif grounding_failures:
                status = "grounding_failure"
            else:
                status = "ok"
                if spec.arm == "evidence_atom_id":
                    resolved = resolve_atom_grounding(response, spec.atom_index)
                else:
                    resolved = resolve_quote_grounding(
                        response,
                        spec.atom_index,
                        allowed_atom_ids={atom["evidence_atom_id"] for atom in spec.packet},
                    )
                write_json(attempt_dir / "resolved_response.json", resolved)
            last_terminal = {
                "status": status,
                "arm": spec.arm,
                "report_id": spec.report_id,
                "document_id": spec.document_id,
                "work_unit_id": spec.work_unit_id,
                "repeat": spec.repeat,
                "attempts": attempt,
                "prompt_sha256": sha256_text(spec.prompt),
                "response_path": relative(attempt_dir / "parsed_response.json"),
                "resolved_response_path": (
                    relative(attempt_dir / "resolved_response.json") if status == "ok" else None
                ),
                "validation_path": relative(attempt_dir / "validation.json"),
            }
            write_json(attempt_dir / "exit_status.json", last_terminal)
            if status == "ok":
                break

        assert last_terminal is not None
        write_json(terminal_path, last_terminal)
        atomic_append_jsonl(
            self.call_ledger,
            {**last_terminal, "completed_at": now()},
            self.ledger_lock,
        )
        return last_terminal

    def execute(self, specs: list[CallSpec]) -> list[dict[str, Any]]:
        if self.max_calls is not None:
            specs = specs[: self.max_calls]
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.execute_call, spec): spec for spec in specs}
            for completed, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                spec = futures[future]
                try:
                    result = future.result()
                except Exception as error:
                    result = {
                        "status": "runner_exception",
                        "arm": spec.arm,
                        "report_id": spec.report_id,
                        "document_id": spec.document_id,
                        "work_unit_id": spec.work_unit_id,
                        "repeat": spec.repeat,
                        "error": repr(error),
                    }
                    write_json(spec.output_dir / "terminal.json", result)
                    atomic_append_jsonl(
                        self.call_ledger,
                        {**result, "completed_at": now()},
                        self.ledger_lock,
                    )
                results.append(result)
                print(
                    f"E0 {completed}/{len(specs)} {spec.arm} {spec.report_id} "
                    f"{spec.work_unit_id} repeat={spec.repeat} "
                    f"status={result['status']}",
                    flush=True,
                )
        return results

    def run(self) -> int:
        self.preflight()
        indexes = self.prepare_inputs()
        specs = self.build_specs(indexes)
        if self.prepare_only:
            print(f"prepared {len(specs)} calls without model execution")
            return 0
        results = self.execute(specs)
        status_counts: dict[str, int] = {}
        for result in results:
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        manifest = read_json(self.output / "orchestrator_manifest.json")
        manifest.update(
            {
                "status": "complete",
                "completed_at": now(),
                "planned_calls": len(specs),
                "executed_or_resumed_calls": len(results),
                "terminal_status_counts": status_counts,
            }
        )
        write_json(self.output / "orchestrator_manifest.json", manifest)
        return 0 if status_counts.get("ok", 0) == len(results) else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-calls", type=int)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    runner = E0Runner(
        suite=args.suite,
        output=args.output,
        workers=args.workers,
        resume=args.resume,
        max_calls=args.max_calls,
        prepare_only=args.prepare_only,
    )
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
