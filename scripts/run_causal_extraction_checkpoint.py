#!/usr/bin/env python3
"""Run frozen causal-extraction discovery and five-run classification checkpoints."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_extraction import (
    build_coverage_ledger,
    build_dense_batches,
    build_evidence_packets,
    build_open_windows,
    canonical_json,
    canonical_sections,
    classifier_decision_payload,
    freeze_candidates,
    read_json,
    render_prompt,
    sha256_file,
    sha256_text,
    strip_unique_items,
    validate_classifier_grounding,
    validate_discovery_grounding,
    validate_schema,
    write_json,
    write_text,
)
from causal_multiomics_aging_review.llm import CodexCliProvider, ProviderError
from scripts.validate_causal_claim_records_v0_2 import (
    candidate_level,
    contrast_complete,
    level4_status,
)

REPO = Path(__file__).resolve().parents[1]
DEFAULT_DESIGN = (
    REPO
    / "protocol/causal_extraction/checkpoints/v0.1.0-rc1"
    / "two_sample_design.json"
)
SUITE = REPO / "protocol/causal_extraction/prompt_suite/v0.1.0-rc1"
CORPUS = REPO / "data/full_text_screening/v1.5.3_deterministic_full_text_158/input.jsonl"


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


def load_corpus() -> dict[str, dict[str, Any]]:
    records = {}
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            records[record["record_id"]] = record
    return records


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path.resolve())


def atomic_append_jsonl(path: Path, value: dict[str, Any], lock: threading.Lock) -> None:
    line = json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n"
    with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


@dataclass(frozen=True)
class CallSpec:
    stage: str
    report_id: str
    work_id: str
    output_dir: Path
    template_path: Path
    schema_path: Path
    substitutions: dict[str, str]
    identity_validator: Callable[[dict[str, Any]], list[str]]
    grounding_validator: Callable[[dict[str, Any]], list[dict[str, str]]]
    repeat: int | None = None


class CheckpointRunner:
    def __init__(
        self,
        *,
        design_path: Path,
        checkpoint: str,
        output: Path,
        workers: int,
        resume: bool,
        max_calls: int | None,
    ) -> None:
        self.design_path = design_path.resolve()
        self.design = read_json(self.design_path)
        self.checkpoint = checkpoint
        self.output = output.resolve()
        self.workers = workers
        self.resume = resume
        self.max_calls = max_calls
        self.runtime = read_json(SUITE / "runtime.json")
        self.coverage = read_json(SUITE / "coverage_contract.json")
        self.codebook = (REPO / self.runtime["codebook"]["path"]).read_text(
            encoding="utf-8"
        )
        self.corpus = load_corpus()
        self.reports = [
            self.corpus[item["report_id"]]
            for item in self.design["checkpoints"][checkpoint]["reports"]
        ]
        self.ledger_lock = threading.Lock()
        self.call_ledger = self.output / "call_ledger.jsonl"
        self.provider = CodexCliProvider(
            self.runtime["model"],
            timeout=900,
            reasoning_effort=self.runtime["reasoning_effort"],
            context_window=self.runtime["generation"]["max_context_tokens"],
            sandbox="read-only",
            approval_policy="never",
            ephemeral=True,
            ignore_user_config=True,
            ignore_rules=True,
            isolated_home=True,
            disabled_features=("plugins",),
        )

    def preflight(self) -> None:
        if self.checkpoint not in {"A", "B"}:
            raise ValueError("Checkpoint must be A or B")
        if self.design["suite"]["artifact_manifest_sha256"] != sha256_file(
            SUITE / "artifact_manifest.json"
        ):
            raise ValueError("Suite artifact manifest changed after sample freeze")
        if self.design["source"]["canonical_corpus_sha256"] != sha256_file(CORPUS):
            raise ValueError("Canonical corpus changed after sample freeze")
        if not self.resume and git_dirty():
            raise ValueError("Git worktree must be clean before a new checkpoint run")
        if self.output.exists() and any(self.output.iterdir()) and not self.resume:
            raise ValueError(f"Refusing to overwrite {self.output}")
        self.output.mkdir(parents=True, exist_ok=True)
        manifest = {
            "status": "running",
            "started_at": now(),
            "checkpoint": self.checkpoint,
            "checkpoint_design": relative(self.design_path),
            "checkpoint_design_sha256": sha256_file(self.design_path),
            "suite_version": self.runtime["suite_version"],
            "suite_manifest_sha256": sha256_file(SUITE / "artifact_manifest.json"),
            "git_revision_at_start": git_revision(),
            "git_worktree_dirty_at_start": False,
            "model": self.runtime["model"],
            "reasoning_effort": self.runtime["reasoning_effort"],
            "codex_cli_version": self.provider.codex_version,
            "workers": self.workers,
            "reports": len(self.reports),
            "technical_retry_limit": 1,
            "classification_repeats": 5,
            "runner": {
                "path": relative(Path(__file__)),
                "sha256": sha256_file(Path(__file__)),
            },
            "library": {
                "path": "src/causal_multiomics_aging_review/causal_extraction.py",
                "sha256": sha256_file(
                    REPO
                    / "src/causal_multiomics_aging_review/causal_extraction.py"
                ),
            },
        }
        if self.resume and (self.output / "orchestrator_manifest.json").is_file():
            previous = read_json(self.output / "orchestrator_manifest.json")
            for key in (
                "checkpoint_design_sha256",
                "suite_manifest_sha256",
                "git_revision_at_start",
                "model",
                "reasoning_effort",
            ):
                if previous.get(key) != manifest.get(key):
                    raise ValueError(f"Resume manifest mismatch: {key}")
            manifest = previous
            manifest["resumed_at"] = now()
            manifest["status"] = "running"
        write_json(self.output / "orchestrator_manifest.json", manifest)

    def prepare_inputs(self) -> None:
        open_config = self.coverage["open_claim_discovery"]
        dense_config = self.coverage["dense_claim_coverage"]
        for report in self.reports:
            report_dir = self.output / "inputs" / report["document_id"]
            sections = canonical_sections(report)
            open_windows = build_open_windows(
                sections,
                max_core_characters=open_config["max_core_characters"],
                context_characters=open_config[
                    "max_adjacent_context_characters_per_side"
                ],
            )
            dense_batches = build_dense_batches(
                sections,
                max_chunk_tokens=dense_config["max_chunk_tokens"],
                max_batch_tokens=dense_config["max_batch_tokens"],
            )
            coverage = build_coverage_ledger(sections, open_windows, dense_batches)
            if not coverage["coverage_complete"]:
                raise ValueError(f"Incomplete coverage for {report['record_id']}")
            write_json(report_dir / "record_metadata.json", {
                key: report[key]
                for key in ("record_id", "document_id", "doi", "title", "year", "source")
            })
            write_text(
                report_dir / "canonical_sections.jsonl",
                "".join(
                    json.dumps(section, ensure_ascii=False, sort_keys=True) + "\n"
                    for section in sections
                ),
            )
            write_json(report_dir / "open_work_units.json", open_windows)
            write_json(report_dir / "dense_work_units.json", dense_batches)
            write_json(report_dir / "coverage_ledger.json", coverage)
        write_json(
            self.output / "preflight" / "source_inventory.json",
            {
                "checkpoint": self.checkpoint,
                "reports": [
                    {
                        "record_id": report["record_id"],
                        "document_id": report["document_id"],
                        "doi": report["doi"],
                        "sections_sha256": sha256_text(canonical_json(report["sections"])),
                    }
                    for report in self.reports
                ],
            },
        )

    def _attempt_is_reusable(self, directory: Path) -> bool:
        terminal = directory / "terminal.json"
        if not terminal.is_file():
            return False
        value = read_json(terminal)
        return value.get("status") in {"ok", "grounding_failure"}

    def execute_call(self, spec: CallSpec) -> dict[str, Any]:
        if self.resume and self._attempt_is_reusable(spec.output_dir):
            return read_json(spec.output_dir / "terminal.json")
        template = spec.template_path.read_text(encoding="utf-8")
        source_schema = read_json(spec.schema_path)
        runtime_schema = strip_unique_items(source_schema)
        rendered = render_prompt(template, spec.substitutions)
        last_terminal: dict[str, Any] | None = None
        for attempt in (1, 2):
            attempt_dir = spec.output_dir / f"attempt-{attempt:02d}"
            attempt_dir.mkdir(parents=True, exist_ok=True)
            write_text(attempt_dir / "rendered_prompt.txt", rendered)
            write_text(
                attempt_dir / "rendered_prompt.sha256",
                sha256_text(rendered) + "\n",
            )
            write_text(
                attempt_dir / "template.sha256",
                sha256_file(spec.template_path) + "\n",
            )
            write_json(attempt_dir / "output_schema.json", runtime_schema)
            write_text(
                attempt_dir / "output_schema.sha256",
                sha256_text(canonical_json(runtime_schema)) + "\n",
            )
            input_payload = {
                "substitutions": spec.substitutions,
                "prompt_sha256": sha256_text(rendered),
            }
            write_json(attempt_dir / "input_payload.json", input_payload)
            write_text(
                attempt_dir / "input_payload.sha256",
                sha256_text(canonical_json(input_payload)) + "\n",
            )
            started = now()
            metadata = {
                "suite_version": self.runtime["suite_version"],
                "stage": spec.stage,
                "report_id": spec.report_id,
                "work_id": spec.work_id,
                "repeat": spec.repeat,
                "attempt": attempt,
                "model": self.runtime["model"],
                "reasoning_effort": self.runtime["reasoning_effort"],
                "codex_cli_version": self.provider.codex_version,
                "git_revision": git_revision(),
                "started_at": started,
            }
            write_json(attempt_dir / "request_metadata.json", metadata)
            try:
                response, raw = self.provider.complete_json(
                    rendered,
                    runtime_schema,
                    schema_name=spec.stage,
                )
            except ProviderError as error:
                raw = error.raw_response or {}
                if isinstance(raw, dict):
                    write_json(attempt_dir / "raw_provider_response.json", raw)
                    write_text(attempt_dir / "raw_stdout.txt", str(raw.get("stdout", "")))
                    write_text(attempt_dir / "raw_stderr.txt", str(raw.get("stderr", "")))
                else:
                    write_text(attempt_dir / "raw_provider_response.txt", str(raw))
                validation = {
                    "schema_valid": False,
                    "identity_valid": False,
                    "grounding_valid": False,
                    "provider_error": str(error),
                }
                write_json(attempt_dir / "validation.json", validation)
                last_terminal = {
                    "status": "technical_failure",
                    "stage": spec.stage,
                    "report_id": spec.report_id,
                    "work_id": spec.work_id,
                    "repeat": spec.repeat,
                    "attempts": attempt,
                    "error": str(error),
                }
                write_json(attempt_dir / "exit_status.json", last_terminal)
                if attempt == 1:
                    continue
                break

            write_json(attempt_dir / "raw_provider_response.json", raw)
            write_text(attempt_dir / "raw_stdout.txt", str(raw.get("stdout", "")))
            write_text(attempt_dir / "raw_stderr.txt", str(raw.get("stderr", "")))
            write_json(attempt_dir / "parsed_response.json", response)
            schema_errors = validate_schema(response, source_schema)
            identity_errors = spec.identity_validator(response)
            grounding_failures = spec.grounding_validator(response)
            validation = {
                "schema_valid": not schema_errors,
                "schema_errors": schema_errors,
                "identity_valid": not identity_errors,
                "identity_errors": identity_errors,
                "grounding_valid": not grounding_failures,
                "grounding_failures": grounding_failures,
            }
            write_json(attempt_dir / "validation.json", validation)
            if schema_errors or identity_errors:
                last_terminal = {
                    "status": "technical_failure",
                    "stage": spec.stage,
                    "report_id": spec.report_id,
                    "work_id": spec.work_id,
                    "repeat": spec.repeat,
                    "attempts": attempt,
                    "schema_errors": schema_errors,
                    "identity_errors": identity_errors,
                }
                write_json(attempt_dir / "exit_status.json", last_terminal)
                if attempt == 1:
                    continue
                break
            status = "ok" if not grounding_failures else "grounding_failure"
            last_terminal = {
                "status": status,
                "stage": spec.stage,
                "report_id": spec.report_id,
                "work_id": spec.work_id,
                "repeat": spec.repeat,
                "attempts": attempt,
                "response_path": relative(attempt_dir / "parsed_response.json"),
                "validation_path": relative(attempt_dir / "validation.json"),
                "prompt_sha256": sha256_text(rendered),
            }
            write_json(attempt_dir / "exit_status.json", last_terminal)
            break
        assert last_terminal is not None
        write_json(spec.output_dir / "terminal.json", last_terminal)
        atomic_append_jsonl(
            self.call_ledger,
            {**last_terminal, "completed_at": now()},
            self.ledger_lock,
        )
        return last_terminal

    def _run_specs(self, specs: list[CallSpec], label: str) -> list[dict[str, Any]]:
        if self.max_calls is not None:
            specs = specs[: self.max_calls]
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.execute_call, spec): spec for spec in specs}
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                spec = futures[future]
                try:
                    result = future.result()
                except Exception as error:
                    result = {
                        "status": "runner_exception",
                        "stage": spec.stage,
                        "report_id": spec.report_id,
                        "work_id": spec.work_id,
                        "repeat": spec.repeat,
                        "error": repr(error),
                    }
                    write_json(spec.output_dir / "terminal.json", result)
                results.append(result)
                completed += 1
                print(
                    f"{label} {completed}/{len(specs)} {spec.report_id} "
                    f"{spec.work_id} status={result['status']}",
                    flush=True,
                )
        return results

    def run_discovery(self) -> None:
        specs: list[CallSpec] = []
        for report in self.reports:
            inputs = self.output / "inputs" / report["document_id"]
            document_sha = sha256_text(canonical_json(report["sections"]))
            for stage, filename, template_name, schema_name in (
                (
                    "open_claim_discovery",
                    "open_work_units.json",
                    "open_claim_discovery.txt",
                    "open_claim_discovery.schema.json",
                ),
                (
                    "dense_claim_coverage",
                    "dense_work_units.json",
                    "dense_claim_coverage.txt",
                    "dense_claim_coverage.schema.json",
                ),
            ):
                units = json.loads((inputs / filename).read_text(encoding="utf-8"))
                for unit in units:
                    core_ids = [section["section_id"] for section in unit["core_sections"]]
                    context_ids = [
                        section["section_id"] for section in unit["context_sections"]
                    ]
                    supplied_sections = [
                        {**section, "evidence_scope": "context"}
                        for section in unit["context_sections"]
                    ] + [
                        {**section, "evidence_scope": "core"}
                        for section in unit["core_sections"]
                    ]
                    expected = {
                        "report_id": report["record_id"],
                        "document_sha256": document_sha,
                        "stage": stage,
                        "work_unit_id": unit["work_unit_id"],
                        "core_section_ids": core_ids,
                        "context_section_ids": context_ids,
                    }

                    def identity(
                        response: dict[str, Any],
                        expected: dict[str, Any] = expected,
                    ) -> list[str]:
                        return [
                            f"{key}: expected {value!r}, found {response.get(key)!r}"
                            for key, value in expected.items()
                            if response.get(key) != value
                        ]

                    specs.append(
                        CallSpec(
                            stage=stage,
                            report_id=report["record_id"],
                            work_id=unit["work_unit_id"],
                            output_dir=(
                                self.output
                                / stage
                                / report["document_id"]
                                / unit["work_unit_id"]
                            ),
                            template_path=SUITE / "prompts" / template_name,
                            schema_path=SUITE / "schemas" / schema_name,
                            substitutions={
                                "REPORT_ID": report["record_id"],
                                "DOCUMENT_SHA256": document_sha,
                                "WORK_UNIT_ID": unit["work_unit_id"],
                                "CORE_SECTION_IDS_JSON": json.dumps(core_ids),
                                "CONTEXT_SECTION_IDS_JSON": json.dumps(context_ids),
                                "CANONICAL_SECTIONS_JSON": json.dumps(
                                    supplied_sections, ensure_ascii=False
                                ),
                            },
                            identity_validator=identity,
                            grounding_validator=lambda response, supplied=supplied_sections: (
                                validate_discovery_grounding(response, supplied)
                            ),
                        )
                    )
        self._run_specs(specs, "discovery")

    def freeze_candidate_inventories(self) -> None:
        for report in self.reports:
            outputs = []
            failures = []
            grounding_failures = []
            for stage in ("open_claim_discovery", "dense_claim_coverage"):
                root = self.output / stage / report["document_id"]
                for terminal_path in sorted(root.glob("*/terminal.json")):
                    terminal = read_json(terminal_path)
                    if terminal["status"] not in {"ok", "grounding_failure"}:
                        failures.append(terminal)
                        continue
                    response = read_json(REPO / terminal["response_path"])
                    outputs.append(response)
                    if terminal["status"] == "grounding_failure":
                        grounding_failures.append(terminal)
            candidates, atoms = freeze_candidates(report, outputs)
            packets = build_evidence_packets(report, candidates, atoms)
            root = self.output / "frozen_candidates" / report["document_id"]
            inventory = {
                "report_id": report["record_id"],
                "doi": report["doi"],
                "document_id": report["document_id"],
                "candidate_count": len(candidates),
                "candidates": candidates,
                "discovery_technical_failures": failures,
                "discovery_grounding_failures": grounding_failures,
            }
            write_json(root / "candidate_inventory.json", inventory)
            write_text(
                root / "evidence_packets.jsonl",
                "".join(
                    json.dumps(packet, ensure_ascii=False, sort_keys=True) + "\n"
                    for packet in packets
                ),
            )
            freeze = {
                "status": "frozen_before_fixed_candidate_classification",
                "frozen_at": now(),
                "candidate_inventory_sha256": sha256_file(
                    root / "candidate_inventory.json"
                ),
                "evidence_packets_sha256": sha256_file(root / "evidence_packets.jsonl"),
                "candidate_count": len(candidates),
            }
            write_json(root / "freeze.json", freeze)

    def run_classification(self) -> None:
        specs: list[CallSpec] = []
        for report in self.reports:
            root = self.output / "frozen_candidates" / report["document_id"]
            inventory = read_json(root / "candidate_inventory.json")
            packets = {
                packet["candidate_ref"]: packet
                for packet in (
                    json.loads(line)
                    for line in (root / "evidence_packets.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                )
            }
            for candidate in inventory["candidates"]:
                candidate_ref = candidate["candidate_ref"]
                packet = packets[candidate_ref]
                provisional_claim_id = candidate_ref.replace("candidate", "claim")
                for repeat in range(1, 6):
                    expected = {
                        "report_id": report["record_id"],
                        "candidate_ref": candidate_ref,
                    }

                    def identity(
                        response: dict[str, Any],
                        expected: dict[str, Any] = expected,
                        provisional: str = provisional_claim_id,
                    ) -> list[str]:
                        errors = [
                            f"{key}: expected {value!r}, found {response.get(key)!r}"
                            for key, value in expected.items()
                            if response.get(key) != value
                        ]
                        for claim in response.get("claim_records", []):
                            if claim.get("claim_id") != provisional:
                                errors.append(
                                    f"claim_id: expected {provisional!r}, "
                                    f"found {claim.get('claim_id')!r}"
                                )
                        return errors

                    specs.append(
                        CallSpec(
                            stage="fixed_candidate_classifier",
                            report_id=report["record_id"],
                            work_id=candidate_ref,
                            repeat=repeat,
                            output_dir=(
                                self.output
                                / "fixed_candidate_classifier"
                                / report["document_id"]
                                / candidate_ref.rsplit("::", 1)[-1]
                                / f"repeat-{repeat:02d}"
                            ),
                            template_path=(
                                SUITE / "prompts" / "fixed_candidate_classifier.txt"
                            ),
                            schema_path=(
                                SUITE
                                / "schemas"
                                / "fixed_candidate_classifier.schema.json"
                            ),
                            substitutions={
                                "REPORT_ID": report["record_id"],
                                "CANDIDATE_REF": candidate_ref,
                                "PROVISIONAL_CLAIM_ID": provisional_claim_id,
                                "FROZEN_CANDIDATE_JSON": json.dumps(
                                    {
                                        "candidate": candidate,
                                        "other_frozen_candidates": packet[
                                            "other_frozen_candidates"
                                        ],
                                    },
                                    ensure_ascii=False,
                                ),
                                "EVIDENCE_PACKET_JSON": json.dumps(
                                    packet, ensure_ascii=False
                                ),
                                "CODEBOOK_TEXT": self.codebook,
                            },
                            identity_validator=identity,
                            grounding_validator=lambda response, packet=packet: (
                                validate_classifier_grounding(response, packet)
                            ),
                        )
                    )
        self._run_specs(specs, "classification")

    def analyze(self) -> dict[str, Any]:
        report_rows = []
        candidate_rows = []
        for report in self.reports:
            root = self.output / "frozen_candidates" / report["document_id"]
            inventory = read_json(root / "candidate_inventory.json")
            report_candidate_rows = []
            for candidate in inventory["candidates"]:
                candidate_ref = candidate["candidate_ref"]
                run_root = (
                    self.output
                    / "fixed_candidate_classifier"
                    / report["document_id"]
                    / candidate_ref.rsplit("::", 1)[-1]
                )
                terminals = [
                    read_json(run_root / f"repeat-{repeat:02d}" / "terminal.json")
                    for repeat in range(1, 6)
                    if (run_root / f"repeat-{repeat:02d}" / "terminal.json").is_file()
                ]
                responses = []
                for terminal in terminals:
                    if terminal["status"] in {"ok", "grounding_failure"}:
                        responses.append(read_json(REPO / terminal["response_path"]))
                payloads = [classifier_decision_payload(response) for response in responses]
                hashes = [sha256_text(canonical_json(payload)) for payload in payloads]
                statuses = [response["candidate_status"] for response in responses]
                derived = []
                for response in responses:
                    claims = []
                    for claim in response.get("claim_records", []):
                        level, level4 = candidate_level(claim)
                        claims.append(
                            {
                                "claim_id": claim["claim_id"],
                                "contrast_completeness": contrast_complete(claim),
                                "level4_validation_status": level4_status(claim),
                                "causal_evidence_level": level,
                                "candidate_level_level4_status": level4,
                            }
                        )
                    derived.append(claims)
                row = {
                    "checkpoint": self.checkpoint,
                    "report_id": report["record_id"],
                    "doi": report["doi"],
                    "candidate_ref": candidate_ref,
                    "discovery_routes": candidate["discovery_routes"],
                    "terminal_runs": len(terminals),
                    "valid_response_runs": len(responses),
                    "terminal_statuses": [terminal["status"] for terminal in terminals],
                    "candidate_statuses": statuses,
                    "decision_hashes": hashes,
                    "five_run_exact": len(hashes) == 5 and len(set(hashes)) == 1,
                    "first_three_exact": len(hashes) >= 3 and len(set(hashes[:3])) == 1,
                    "grounding_valid_all": len(terminals) == 5
                    and all(terminal["status"] == "ok" for terminal in terminals),
                    "derived_outputs": derived,
                }
                candidate_rows.append(row)
                report_candidate_rows.append(row)
            report_rows.append(
                {
                    "checkpoint": self.checkpoint,
                    "report_id": report["record_id"],
                    "doi": report["doi"],
                    "title": report["title"],
                    "candidate_count": len(report_candidate_rows),
                    "all_candidates_five_run_exact": bool(report_candidate_rows)
                    and all(row["five_run_exact"] for row in report_candidate_rows),
                    "all_candidates_first_three_exact": bool(report_candidate_rows)
                    and all(row["first_three_exact"] for row in report_candidate_rows),
                    "discovery_technical_failures": len(
                        inventory["discovery_technical_failures"]
                    ),
                    "discovery_grounding_failures": len(
                        inventory["discovery_grounding_failures"]
                    ),
                }
            )

        write_text(
            self.output / "reports" / "candidate_stability.jsonl",
            "".join(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                for row in candidate_rows
            ),
        )
        write_text(
            self.output / "reports" / "report_stability.jsonl",
            "".join(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                for row in report_rows
            ),
        )
        completed_candidates = [
            row for row in candidate_rows if row["valid_response_runs"] == 5
        ]
        summary = {
            "checkpoint": self.checkpoint,
            "reports": len(report_rows),
            "reports_with_candidates": sum(row["candidate_count"] > 0 for row in report_rows),
            "candidates": len(candidate_rows),
            "candidates_with_five_valid_runs": len(completed_candidates),
            "candidates_five_run_exact": sum(
                row["five_run_exact"] for row in candidate_rows
            ),
            "candidates_first_three_exact": sum(
                row["first_three_exact"] for row in candidate_rows
            ),
            "reports_all_candidates_five_run_exact": sum(
                row["all_candidates_five_run_exact"] for row in report_rows
            ),
            "reports_all_candidates_first_three_exact": sum(
                row["all_candidates_first_three_exact"] for row in report_rows
            ),
            "all_grounding_valid_candidates": sum(
                row["grounding_valid_all"] for row in candidate_rows
            ),
            "discovery_technical_failures": sum(
                row["discovery_technical_failures"] for row in report_rows
            ),
            "discovery_grounding_failures": sum(
                row["discovery_grounding_failures"] for row in report_rows
            ),
        }
        write_json(self.output / "reports" / "stability_summary.json", summary)
        manifest = read_json(self.output / "orchestrator_manifest.json")
        manifest["status"] = "classification_checkpoint_complete"
        manifest["completed_at"] = now()
        manifest["summary"] = summary
        write_json(self.output / "orchestrator_manifest.json", manifest)
        return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", choices=("A", "B"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--max-calls",
        type=int,
        help="technical smoke limit applied after deterministic call ordering",
    )
    parser.add_argument(
        "--phase",
        choices=("prepare", "discover", "freeze", "classify", "analyze", "all"),
        default="all",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runner = CheckpointRunner(
        design_path=args.design,
        checkpoint=args.checkpoint,
        output=args.output,
        workers=args.workers,
        resume=args.resume,
        max_calls=args.max_calls,
    )
    runner.preflight()
    phases = (
        ("prepare", runner.prepare_inputs),
        ("discover", runner.run_discovery),
        ("freeze", runner.freeze_candidate_inventories),
        ("classify", runner.run_classification),
        ("analyze", runner.analyze),
    )
    if args.phase == "all":
        for _, action in phases:
            action()
    else:
        dict(phases)[args.phase]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
