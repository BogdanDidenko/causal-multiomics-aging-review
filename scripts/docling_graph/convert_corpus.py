#!/usr/bin/env python3
"""Convert the frozen corpus once with a reusable no-OCR Docling converter."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "protocol/full_text/docling_graph_v1.0.0.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def latest_by_document(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        latest[str(row["document_id"])] = row
    return latest


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def make_converter() -> Any:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options = PdfPipelineOptions()
    options.do_ocr = False
    options.do_table_structure = True
    options.table_structure_options.mode = TableFormerMode.ACCURATE
    options.table_structure_options.do_cell_matching = True
    options.generate_page_images = False
    options.generate_picture_images = False
    options.do_picture_description = False
    options.do_formula_enrichment = False
    options.generate_parsed_pages = True
    options.heading_hierarchy_options.enabled = True
    options.heading_hierarchy_options.use_bookmarks = True
    options.heading_hierarchy_options.use_numbering = True
    options.heading_hierarchy_options.use_style = True
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


def existing_export(output_root: Path, document_id: str) -> tuple[Path, Path] | None:
    roots = sorted(
        (output_root / "artifacts" / document_id).glob("*/docling/document.json"),
        reverse=True,
    )
    for document_json in roots:
        markdown = document_json.with_name("document.md")
        if markdown.is_file():
            return document_json, markdown
    return None


def write_summary(
    output_root: Path, corpus_rows: list[dict[str, str]], manifest_path: Path
) -> dict[str, Any]:
    attempts = read_jsonl(manifest_path)
    latest = latest_by_document(attempts)
    success = sum(row.get("status") == "success" for row in latest.values())
    failed = sum(row.get("status") == "failed" for row in latest.values())
    insufficient = sum(
        row.get("failure_route") == "insufficient_full_text" for row in latest.values()
    )
    technical_failures = failed - insufficient
    resolved = success + insufficient
    summary = {
        "schema_version": "1.0.0",
        "status": "complete" if resolved == len(corpus_rows) else "in_progress",
        "corpus_documents": len(corpus_rows),
        "documents_converted": success,
        "documents_insufficient_full_text": insufficient,
        "documents_failed": technical_failures,
        "documents_pending": len(corpus_rows) - len(latest),
        "attempt_count": len(attempts),
        "ocr_enabled": False,
        "manifest": str(manifest_path.relative_to(REPO)),
    }
    (output_root / "conversion_summary.json").write_text(
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
    args = parser.parse_args()

    config = json.loads(args.config.resolve().read_text(encoding="utf-8"))
    output_root = (REPO / config["runtime"]["output_root"]).resolve()
    corpus_rows = read_csv(output_root / "corpus_manifest.csv")
    all_corpus_rows = list(corpus_rows)
    selected_dois = {doi.casefold() for doi in args.doi}
    if selected_dois:
        corpus_rows = [row for row in corpus_rows if row["doi"].casefold() in selected_dois]
    if args.limit is not None:
        corpus_rows = corpus_rows[: args.limit]

    converted_dir = output_root / "converted"
    converted_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / "conversion_manifest.jsonl"
    latest = latest_by_document(read_jsonl(manifest_path))
    converter = None

    for index, row in enumerate(corpus_rows, start=1):
        document_id = row["document_id"]
        document_json = converted_dir / f"{document_id}.docling.json"
        markdown = converted_dir / f"{document_id}.md"
        previous = latest.get(document_id)
        if (
            not args.no_resume
            and previous
            and previous.get("status") == "success"
            and previous.get("source_sha256") == row["source_sha256"]
            and document_json.is_file()
            and markdown.is_file()
        ):
            print(f"[{index}/{len(corpus_rows)}] resume {row['doi']}", flush=True)
            continue

        started = time.time()
        attempt: dict[str, Any] = {
            "document_id": document_id,
            "doi": row["doi"],
            "source_path": row["source_path"],
            "source_sha256": row["source_sha256"],
            "ocr_enabled": False,
            "started_at_unix": started,
        }
        try:
            reusable = existing_export(output_root, document_id)
            if reusable and config["conversion"]["reuse_existing_docling_graph_exports"]:
                shutil.copyfile(reusable[0], document_json)
                shutil.copyfile(reusable[1], markdown)
                conversion_source = "reused_docling_graph_export"
            else:
                if converter is None:
                    converter = make_converter()
                result = converter.convert(REPO / row["source_path"])
                result.document.save_as_json(document_json)
                markdown.write_text(result.document.export_to_markdown(), encoding="utf-8")
                conversion_source = "reusable_no_ocr_converter"
            if document_json.stat().st_size < 1000 or markdown.stat().st_size < 1000:
                raise ValueError("Converted document is unexpectedly small")
            attempt.update(
                {
                    "status": "success",
                    "conversion_source": conversion_source,
                    "elapsed_seconds": time.time() - started,
                    "docling_json_path": str(document_json.relative_to(REPO)),
                    "docling_json_sha256": sha256_file(document_json),
                    "markdown_path": str(markdown.relative_to(REPO)),
                    "markdown_sha256": sha256_file(markdown),
                    "markdown_characters": len(markdown.read_text(encoding="utf-8")),
                }
            )
        except Exception as exc:
            failure_route = (
                "insufficient_full_text"
                if isinstance(exc, ValueError)
                and str(exc) == "Converted document is unexpectedly small"
                else "conversion_failed"
            )
            attempt.update(
                {
                    "status": "failed",
                    "failure_route": failure_route,
                    "elapsed_seconds": time.time() - started,
                    "error_type": type(exc).__name__,
                    "error": repr(exc),
                }
            )
        append_jsonl(manifest_path, attempt)
        latest[document_id] = attempt
        print(json.dumps(attempt, ensure_ascii=False, sort_keys=True), flush=True)

    summary = write_summary(output_root, all_corpus_rows, manifest_path)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
