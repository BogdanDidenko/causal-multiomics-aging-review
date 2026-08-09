#!/usr/bin/env python3
"""Run the frozen full-text corpus through Docling Graph with resume support."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "protocol/full_text/docling_graph_v1.0.0.json"
SERVER_SCRIPT = REPO / "scripts/docling_graph/codex_openai_compat_server.py"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_template(dotted_path: str) -> type[Any]:
    module_name, class_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_attempts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def latest_by_document(attempts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for attempt in attempts:
        latest[str(attempt["document_id"])] = attempt
    return latest


def belongs_to_shard(document_id: str, shard_count: int, shard_index: int) -> bool:
    """Assign a document to one stable, non-overlapping execution shard."""
    return int(document_id.rsplit("_", 1)[-1], 16) % shard_count == shard_index


def wait_for_server(base_url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    health_url = base_url.rstrip("/").removesuffix("/v1") + "/health"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.25)
    raise TimeoutError(f"Codex adapter did not become ready: {health_url}")


def start_server(config: dict[str, Any], output_root: Path) -> subprocess.Popen[str]:
    runtime = config["runtime"]
    model = config["model"]
    base_url = str(runtime["base_url"])
    port = int(base_url.rstrip("/").rsplit(":", 1)[1].split("/", 1)[0])
    command = [
        sys.executable,
        str(SERVER_SCRIPT),
        "--port",
        str(port),
        "--model",
        str(model["codex_cli_model"]),
        "--reasoning-effort",
        str(model["reasoning_effort"]),
        "--timeout",
        str(runtime["timeout_seconds"]),
        "--audit-dir",
        str(output_root / "audit"),
        "--quiet",
    ]
    log_path = output_root / "codex_adapter.log"
    log_handle = log_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=REPO,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    process._docling_log_handle = log_handle  # type: ignore[attr-defined]
    try:
        wait_for_server(base_url)
    except Exception:
        process.terminate()
        process.wait(timeout=10)
        log_handle.close()
        raise
    return process


def stop_server(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    handle = getattr(process, "_docling_log_handle", None)
    if handle:
        handle.close()


def find_export(document_output: Path, filename: str) -> Path | None:
    matches = sorted(document_output.rglob(filename))
    return matches[0] if matches else None


def make_pipeline_config(
    config: dict[str, Any],
    source: Path,
    output_dir: Path,
    template: type[Any],
    extraction_contract: str,
) -> dict[str, Any]:
    graph = config["docling_graph"]
    return {
        "source": str(source),
        "template": template,
        "backend": graph["backend"],
        "inference": graph["inference"],
        "provider_override": graph["provider"],
        "model_override": config["model"]["codex_cli_model"],
        "processing_mode": graph["processing_mode"],
        "extraction_contract": extraction_contract,
        "llm_input_format": graph["llm_input_format"],
        "use_chunking": graph["use_chunking"],
        "chunk_max_tokens": graph["chunk_max_tokens"],
        "dense_skeleton_batch_tokens": graph["dense_skeleton_batch_tokens"],
        "dense_fill_nodes_cap": graph["dense_fill_nodes_cap"],
        "dense_fill_context": graph["dense_fill_context"],
        "dense_dedupe": graph["dense_dedupe"],
        "parallel_workers": graph["parallel_workers"],
        "gleaning_enabled": graph["gleaning_enabled"],
        "provenance": graph["provenance"],
        "structured_output": graph["structured_output"],
        "structured_sparse_check": graph["structured_sparse_check"],
        "llm_overrides": graph["llm_overrides"],
        "dump_to_disk": True,
        "debug": True,
        "export_format": "csv",
        "export_docling": True,
        "export_docling_json": graph["export_docling_json"],
        "export_markdown": graph["export_markdown"],
        "export_doclang": graph["export_doclang"],
        "output_dir": str(output_dir),
    }


def append_attempt(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def is_context_overflow(exc: Exception) -> bool:
    message = repr(exc).casefold()
    return any(
        marker in message
        for marker in (
            "context window",
            "context length",
            "input too long",
            "token limit",
            "too many tokens",
            "exceeds the model",
        )
    )


def write_summary(
    output_root: Path,
    corpus_rows: list[dict[str, str]],
    attempts_path: Path,
    config_path: Path,
    template_path: Path,
    config: dict[str, Any],
) -> dict[str, Any]:
    attempts = read_attempts(attempts_path)
    latest = latest_by_document(attempts)
    counts = Counter(row.get("status", "missing") for row in latest.values())
    resolved = counts["success"] + counts["insufficient_full_text"]
    summary = {
        "schema_version": "1.0.0",
        "status": "complete" if resolved == len(corpus_rows) else "in_progress",
        "corpus_documents": len(corpus_rows),
        "documents_attempted": len(latest),
        "documents_succeeded": counts["success"],
        "documents_insufficient_full_text": counts["insufficient_full_text"],
        "documents_failed": counts["failed"],
        "documents_pending": len(corpus_rows) - len(latest),
        "attempt_count": len(attempts),
        "model": config["model"]["codex_cli_model"],
        "reasoning_effort": config["model"]["reasoning_effort"],
        "runtime": {
            "python": platform.python_version(),
            "codex_cli": subprocess.run(
                ["codex", "--version"], capture_output=True, text=True, check=True
            ).stdout.strip(),
            "docling_graph": importlib.metadata.version("docling-graph"),
            "docling": importlib.metadata.version("docling"),
            "docling_core": importlib.metadata.version("docling-core"),
            "litellm": importlib.metadata.version("litellm"),
        },
        "config_sha256": sha256_file(config_path),
        "template_sha256": sha256_file(template_path),
        "attempt_manifest": str(attempts_path.relative_to(REPO)),
    }
    (output_root / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--doi", action="append", default=[])
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--external-server", action="store_true")
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    args = parser.parse_args()

    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_root = (REPO / config["runtime"]["output_root"]).resolve()
    corpus_path = output_root / "corpus_manifest.csv"
    if not corpus_path.exists():
        raise FileNotFoundError(
            f"Missing {corpus_path}; run scripts/docling_graph/build_corpus_manifest.py first"
        )
    corpus_rows = read_manifest(corpus_path)
    all_corpus_rows = list(corpus_rows)
    selected_dois = {doi.casefold() for doi in args.doi}
    if selected_dois:
        corpus_rows = [row for row in corpus_rows if row["doi"].casefold() in selected_dois]
        missing = selected_dois - {row["doi"].casefold() for row in corpus_rows}
        if missing:
            raise ValueError(f"DOIs not found in corpus: {sorted(missing)}")
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise ValueError("Require shard_count >= 1 and 0 <= shard_index < shard_count")
    if args.shard_count > 1:
        corpus_rows = [
            row
            for row in corpus_rows
            if belongs_to_shard(row["document_id"], args.shard_count, args.shard_index)
        ]
    if args.limit is not None:
        corpus_rows = corpus_rows[: args.limit]

    conversion_manifest_path = output_root / "conversion_manifest.jsonl"
    conversions = latest_by_document(read_attempts(conversion_manifest_path))
    missing_conversions = [
        row["doi"] for row in corpus_rows if row["document_id"] not in conversions
    ]
    if missing_conversions:
        raise RuntimeError(
            "Missing canonical Docling conversion attempts for: "
            f"{missing_conversions[:10]}; run convert_corpus.py first"
        )
    broken_successes = [
        row["doi"]
        for row in corpus_rows
        if conversions[row["document_id"]].get("status") == "success"
        and not (REPO / str(conversions[row["document_id"]].get("docling_json_path", ""))).is_file()
    ]
    if broken_successes:
        raise RuntimeError(
            "Canonical Docling files are missing for successful conversions: "
            f"{broken_successes[:10]}"
        )

    attempts_path = output_root / "run_manifest.jsonl"
    latest = latest_by_document(read_attempts(attempts_path))
    template_path = REPO / "scripts/docling_graph/templates/causal_multiomics_aging.py"
    config_hash = sha256_file(config_path)
    template_hash = sha256_file(template_path)
    template = load_template(config["docling_graph"]["template"])
    os.environ["CUSTOM_LLM_BASE_URL"] = str(config["runtime"]["base_url"])
    os.environ["CUSTOM_LLM_API_KEY"] = "local-codex-cli"

    server: subprocess.Popen[str] | None = None
    if args.external_server:
        wait_for_server(str(config["runtime"]["base_url"]))
    else:
        server = start_server(config, output_root)

    from docling_graph import run_pipeline

    max_retries = int(config["runtime"]["max_retries"])
    try:
        for index, row in enumerate(corpus_rows, start=1):
            document_id_value = row["document_id"]
            previous = latest.get(document_id_value)
            conversion = conversions[document_id_value]
            if conversion.get("status") != "success":
                failure_route = str(conversion.get("failure_route", "conversion_failed"))
                run_status = (
                    "insufficient_full_text"
                    if failure_route == "insufficient_full_text"
                    else "failed"
                )
                if not previous or previous.get("status") != run_status:
                    attempt = {
                        "document_id": document_id_value,
                        "doi": row["doi"],
                        "source_path": row["source_path"],
                        "source_sha256": row["source_sha256"],
                        "status": run_status,
                        "config_sha256": config_hash,
                        "template_sha256": template_hash,
                        "reason": failure_route,
                        "conversion_error_type": conversion.get("error_type"),
                        "conversion_error": conversion.get("error"),
                    }
                    append_attempt(attempts_path, attempt)
                    latest[document_id_value] = attempt
                print(
                    f"[{index}/{len(corpus_rows)}] {run_status} {row['doi']}",
                    flush=True,
                )
                continue
            if (
                not args.no_resume
                and previous
                and previous.get("status") == "success"
                and previous.get("source_sha256") == row["source_sha256"]
                and (REPO / str(previous["graph_path"])).is_file()
            ):
                print(f"[{index}/{len(corpus_rows)}] resume {row['doi']}", flush=True)
                continue

            source = REPO / str(conversion["docling_json_path"])
            document_output = output_root / "artifacts" / document_id_value
            active_contract = str(config["docling_graph"]["extraction_contract"])
            for retry in range(max_retries + 1):
                started = time.time()
                attempt: dict[str, Any] = {
                    "document_id": document_id_value,
                    "doi": row["doi"],
                    "source_path": row["source_path"],
                    "source_sha256": row["source_sha256"],
                    "graph_input_path": conversion["docling_json_path"],
                    "graph_input_sha256": conversion["docling_json_sha256"],
                    "model": config["model"]["codex_cli_model"],
                    "reasoning_effort": config["model"]["reasoning_effort"],
                    "config_sha256": config_hash,
                    "template_sha256": template_hash,
                    "extraction_contract": active_contract,
                    "retry_index": retry,
                    "started_at_unix": started,
                }
                print(
                    f"[{index}/{len(corpus_rows)}] extract {row['doi']} retry={retry}",
                    flush=True,
                )
                try:
                    context = run_pipeline(
                        make_pipeline_config(
                            config, source, document_output, template, active_contract
                        )
                    )
                    graph_path = find_export(document_output, "graph.json")
                    provenance_path = find_export(document_output, "provenance.json")
                    if graph_path is None or provenance_path is None:
                        raise RuntimeError(
                            "Docling Graph did not export graph.json and provenance.json"
                        )
                    graph = context.knowledge_graph
                    attempt.update(
                        {
                            "status": "success",
                            "elapsed_seconds": time.time() - started,
                            "graph_nodes": graph.number_of_nodes(),
                            "graph_edges": graph.number_of_edges(),
                            "extracted_models": len(context.extracted_models or []),
                            "graph_path": str(graph_path.relative_to(REPO)),
                            "graph_sha256": sha256_file(graph_path),
                            "provenance_path": str(provenance_path.relative_to(REPO)),
                            "provenance_sha256": sha256_file(provenance_path),
                        }
                    )
                    append_attempt(attempts_path, attempt)
                    latest[document_id_value] = attempt
                    break
                except Exception as exc:
                    attempt.update(
                        {
                            "status": "failed",
                            "elapsed_seconds": time.time() - started,
                            "error_type": type(exc).__name__,
                            "error": repr(exc),
                        }
                    )
                    append_attempt(attempts_path, attempt)
                    latest[document_id_value] = attempt
                    if retry >= max_retries:
                        print(f"failed {row['doi']}: {exc!r}", file=sys.stderr, flush=True)
                    elif is_context_overflow(exc):
                        active_contract = str(
                            config["docling_graph"]["fallback_contract_on_context_overflow"]
                        )
        summary = write_summary(
            output_root,
            all_corpus_rows,
            attempts_path,
            config_path,
            template_path,
            config,
        )
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0 if summary["documents_failed"] == 0 else 1
    finally:
        stop_server(server)


if __name__ == "__main__":
    raise SystemExit(main())
