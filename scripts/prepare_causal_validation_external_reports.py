#!/usr/bin/env python3
"""Build deterministic Docling records for external causal-validation challenges."""

from __future__ import annotations

import hashlib
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from docling.document_converter import DocumentConverter
from docling_graph.core.extractors.document_chunker import DocumentChunker

from scripts.docling_graph.convert_corpus import jats_xml_to_markdown

REPO = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO / "data/full_text/causal_validation_v0.3.1_external"
OUTPUT_ROOT = REPO / "data/causal_extraction/v0.3.1_independent_validation/external"
CHUNK_MAX_TOKENS = 1024

REPORTS = [
    {
        "doi": "10.1111/acel.70279",
        "pmcid": "PMC12686565",
        "year": "2025",
        "source_path": SOURCE_ROOT / "PMC12686565.xml",
        "sampling_role": "formal_mediation_positive_challenge",
    },
    {
        "doi": "10.1186/s13040-025-00432-1",
        "pmcid": "PMC11931790",
        "year": "2025",
        "source_path": SOURCE_ROOT / "PMC11931790.xml",
        "sampling_role": "formal_mediation_multiomics_boundary",
    },
    {
        "doi": "10.1093/geroni/igad104.2477",
        "pmcid": "PMC10738687",
        "year": "2023",
        "source_path": SOURCE_ROOT / "PMC10738687.xml",
        "sampling_role": "bayesian_network_future_work_boundary",
    },
]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def document_id(doi: str) -> str:
    return f"doi_{sha256_bytes(doi.casefold().encode('utf-8'))[:16]}"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def element_text(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def xml_metadata(path: Path) -> tuple[str, str]:
    root = ET.parse(path).getroot()
    title = next(
        (element_text(node) for node in root.iter() if local_name(node.tag) == "article-title"),
        path.stem,
    )
    abstract = next(
        (element_text(node) for node in root.iter() if local_name(node.tag) == "abstract"),
        "",
    )
    return title, abstract


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_report(
    specification: dict[str, Any], converter: DocumentConverter
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_path = Path(specification["source_path"])
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    doi = str(specification["doi"]).casefold()
    doc_id = document_id(doi)
    title, abstract = xml_metadata(source_path)
    source_markdown = jats_xml_to_markdown(source_path)

    with tempfile.TemporaryDirectory(prefix="causal-validation-docling-") as directory:
        intermediary = Path(directory) / f"{doc_id}.md"
        intermediary.write_text(source_markdown, encoding="utf-8")
        document = converter.convert(intermediary).document

    converted_dir = OUTPUT_ROOT / "converted"
    converted_dir.mkdir(parents=True, exist_ok=True)
    document_json_path = converted_dir / f"{doc_id}.docling.json"
    document_markdown_path = converted_dir / f"{doc_id}.md"
    document.save_as_json(document_json_path)
    document_markdown_path.write_text(document.export_to_markdown(), encoding="utf-8")

    chunker = DocumentChunker(chunk_max_tokens=CHUNK_MAX_TOKENS)
    chunks, chunk_stats = chunker.chunk_document_with_stats(document)
    sections = []
    chunk_records = []
    for order, text in enumerate(chunks):
        text_hash = sha256_bytes(text.encode("utf-8"))[:16]
        section_id = f"chunk:{order:04d}"
        sections.append(
            {
                "section_id": section_id,
                "heading": title,
                "text": text,
                "text_hash": text_hash,
                "page_numbers": [],
            }
        )
        chunk_records.append(
            {
                "chunk_id": order,
                "headings": [title],
                "token_count": chunk_stats["chunk_tokens"][order],
                "text_hash": text_hash,
                "char_length": len(text),
                "text": text,
            }
        )
    chunks_path = OUTPUT_ROOT / "chunks" / f"{doc_id}.json"
    write_json(chunks_path, chunk_records)

    record = {
        "record_id": f"doi:{doi}",
        "document_id": doc_id,
        "doi": doi,
        "source": "external_validation_challenge",
        "year": specification["year"],
        "title": title,
        "abstract": abstract,
        "sections": sections,
        "input_provenance": {
            "source_frame": "v1.1.2_broader_search_frame_outside_final_101",
            "pmcid": specification["pmcid"],
            "source_path": str(source_path.relative_to(REPO)),
            "source_sha256": sha256_file(source_path),
            "source_conversion": "deterministic_jats_markdown_then_docling_hybrid_chunker",
            "chunk_max_tokens": CHUNK_MAX_TOKENS,
            "sampling_role": specification["sampling_role"],
        },
    }
    audit = {
        "record_id": record["record_id"],
        "document_id": doc_id,
        "doi": doi,
        "title": title,
        "source_path": str(source_path.relative_to(REPO)),
        "source_sha256": sha256_file(source_path),
        "source_markdown_sha256": sha256_bytes(source_markdown.encode("utf-8")),
        "docling_json_path": str(document_json_path.relative_to(REPO)),
        "docling_json_sha256": sha256_file(document_json_path),
        "docling_markdown_path": str(document_markdown_path.relative_to(REPO)),
        "docling_markdown_sha256": sha256_file(document_markdown_path),
        "chunks_path": str(chunks_path.relative_to(REPO)),
        "chunks_sha256": sha256_file(chunks_path),
        "chunk_count": len(chunks),
        "canonical_character_count": sum(len(section["text"]) for section in sections),
        "chunk_stats": chunk_stats,
        "sampling_role": specification["sampling_role"],
    }
    return record, audit


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    converter = DocumentConverter()
    records = []
    audits = []
    for specification in REPORTS:
        record, audit = build_report(specification, converter)
        records.append(record)
        audits.append(audit)
    records.sort(key=lambda item: item["record_id"])
    audits.sort(key=lambda item: item["record_id"])

    records_path = OUTPUT_ROOT / "external_records.jsonl"
    records_path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records
        ),
        encoding="utf-8",
    )
    manifest = {
        "status": "frozen_deterministic_external_validation_input",
        "records": len(records),
        "conversion": "JATS XML -> deterministic Markdown -> Docling -> HybridChunker",
        "chunk_max_tokens": CHUNK_MAX_TOKENS,
        "external_records_path": str(records_path.relative_to(REPO)),
        "external_records_sha256": sha256_file(records_path),
        "reports": audits,
    }
    write_json(OUTPUT_ROOT / "manifest.json", manifest)
    print(json.dumps({"records": len(records), "output": str(OUTPUT_ROOT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
