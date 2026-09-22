#!/usr/bin/env python3
"""Create complete annotated Docling inputs for CMACM v1.1.0 development."""

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "analysis/content_model_validation/v1.0.3/input.jsonl"
MODEL = ROOT / "protocol/content_model/v1.1.0"
OUT = ROOT / "analysis/content_model_validation/v1.1.0_development"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomize(markdown: str) -> tuple[list[dict[str, object]], str]:
    atoms = []
    rendered = []
    offset = 0
    for index, match in enumerate(re.finditer(r".*?(?:\n\s*\n|\Z)", markdown, flags=re.DOTALL), 1):
        block = match.group(0)
        if not block:
            continue
        atom_id = f"docatom_{index:05d}"
        atoms.append({"id": atom_id, "start": offset, "end": offset + len(block), "text": block, "sha256": sha256(block.encode())})
        rendered.append(f"[[{atom_id}]]" + block)
        offset += len(block)
    annotated = "".join(rendered)
    restored = re.sub(r"\[\[docatom_[0-9]+\]\]", "", annotated)
    if restored != markdown:
        raise ValueError("Atomization failed to preserve complete Markdown")
    if "".join(atom["text"] for atom in atoms) != markdown:
        raise ValueError("Atom blocks do not cover complete Markdown")
    return atoms, annotated


def main() -> None:
    if OUT.exists():
        raise ValueError(f"Refuse to overwrite CMACM v1.1.0 development package: {OUT}")
    records = []
    for line in SOURCE.open():
        source = json.loads(line)
        markdown = source["sections"][0]["text"]
        atoms, annotated = atomize(markdown)
        record = {key: source[key] for key in ("sample_order", "diversity_role", "record_id", "document_id", "doi", "title", "source", "year", "input_provenance", "size_based_modifications")}
        record.update({"full_markdown": markdown, "document_atoms": atoms, "annotated_full_markdown": annotated})
        records.append(record)
    if len(records) != 15:
        raise ValueError("CMACM development sample must retain all 15 reports")
    OUT.mkdir(parents=True)
    input_path = OUT / "input.jsonl"
    input_path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records))
    sample = {"sample_id": "cmacm_v1_1_0_development_same_15_as_v1_0_3", "reports": [{key: record[key] for key in ("sample_order", "diversity_role", "record_id", "document_id", "doi", "title")} for record in records], "input_size_modifications": False, "purpose": "development only; this sample may not be reused as prospective holdout"}
    sample_path = OUT / "sample.json"
    sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2) + "\n")
    manifest = {"model": "CMACM-v1.1.0", "source_input": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE.read_bytes())}, "input": {"path": str(input_path.relative_to(ROOT)), "sha256": sha256(input_path.read_bytes())}, "sample": {"path": str(sample_path.relative_to(ROOT)), "sha256": sha256(sample_path.read_bytes())}, "schema": {"path": str((MODEL / "atom_classification.schema.json").relative_to(ROOT)), "sha256": sha256((MODEL / "atom_classification.schema.json").read_bytes())}, "prompt": {"path": str((MODEL / "atom_classification_prompt.txt").relative_to(ROOT)), "sha256": sha256((MODEL / "atom_classification_prompt.txt").read_bytes())}, "document_atom_counts": {record["record_id"]: len(record["document_atoms"]) for record in records}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"records": len(records), "atoms": sum(len(record["document_atoms"]) for record in records), "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
