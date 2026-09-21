#!/usr/bin/env python3
"""Freeze an unseen full-text sample for CMACM prospective validation."""

import csv
import hashlib
import json
import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "v1.0.3"
MODEL = ROOT / f"protocol/content_model/{VERSION}"
MASTER = ROOT / "analysis/review_synthesis/master_corpus_v1.0.0/eligible_report_ledger_376.csv"
FULL_INPUT = ROOT / "data/full_text_screening/v1.6.0_full_markdown296/input/input.jsonl"
OUT = ROOT / f"analysis/content_model_validation/{VERSION}"

SAMPLE = (
    ("10.18632/aging.102822", "growth_hormone_knockout_mouse_multiomics"),
    ("10.31857/s0026898424020065", "gene_knockout_drosophila_lifespan"),
    ("10.15252/embr.202152606", "overexpression_mitochondrial_mutant_longevity"),
    ("10.1038/s43856-025-00942-3", "assigned_intervention_middle_aged_mouse"),
    ("10.1038/s41514-025-00318-w", "human_exercise_intervention_proteomic_aging"),
    ("10.1038/s41591-019-0504-5", "microbiota_transfer_progeroid_mouse"),
    ("10.1101/680462", "placebo_controlled_human_randomized_trial"),
    ("10.3389/fnut.2026.1750030", "randomized_crossover_human_multiomics"),
    ("10.1007/s11357-025-01794-4", "microbiome_protein_mr_mediation"),
    ("10.1038/s43587-021-00159-8", "human_aging_mr_protein_target"),
    ("10.1093/ehjcvp/pvae038", "drug_target_genetics_proteomics_mr"),
    ("10.1111/acel.70065", "mr_cohort_cell_validation"),
    ("10.64898/2026.07.05.26356402", "formal_causal_inference_aging_biomarkers"),
    ("10.3389/fnagi.2023.1241412", "causality_network_longevity_neurodegeneration"),
    ("10.3390/ijms26094389", "plant_senescence_genetic_variation"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def previous_sample_dois() -> set[str]:
    seen: set[str] = set()
    for path in (ROOT / "protocol/causal_extraction").rglob("sample.json"):
        payload = json.loads(path.read_text())
        for report in payload.get("reports", []):
            doi = report.get("doi")
            if doi:
                seen.add(doi.lower())
    for path in (ROOT / "analysis/causal_extraction").rglob("reports_15.csv"):
        for row in csv.DictReader(path.open()):
            if row.get("doi"):
                seen.add(row["doi"].lower())
    return seen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=VERSION)
    args = parser.parse_args()
    model = ROOT / f"protocol/content_model/{args.version}"
    out = ROOT / f"analysis/content_model_validation/{args.version}"
    if out.exists():
        raise ValueError(f"Refuse to overwrite frozen CMACM validation package: {out}")
    prior = previous_sample_dois() | {"10.1002/advs.202411015"}
    requested = {doi for doi, _ in SAMPLE}
    overlap = requested & prior
    if overlap:
        raise ValueError(f"CMACM sample overlaps prior test material: {sorted(overlap)}")

    master = {row["doi"].lower(): row for row in csv.DictReader(MASTER.open())}
    inputs = {row["doi"].lower(): row for row in map(json.loads, FULL_INPUT.open())}
    records = []
    for index, (doi, role) in enumerate(SAMPLE, 1):
        master_row = master[doi]
        if master_row["source_cohort"] != "stable_layer_pair_extension":
            raise ValueError(f"Not from the new extension: {doi}")
        if master_row["provisional_canonical_report"] != "true":
            raise ValueError(f"Not canonical after version linkage: {doi}")
        source = inputs[doi]
        full_markdown = source["sections"][0]["text"]
        records.append(
            {
                "sample_order": index,
                "diversity_role": role,
                "record_id": source["record_id"],
                "document_id": source["document_id"],
                "doi": doi,
                "title": source["title"],
                "source": source["source"],
                "year": source["year"],
                "sections": [{"section_id": "chunk:0000", "heading": "Complete Docling Markdown", "text": full_markdown}],
                "input_provenance": source["input_provenance"],
                "size_based_modifications": False,
            }
        )
    assert len(records) == 15
    assert len({record["doi"] for record in records}) == 15

    out.mkdir(parents=True)
    input_path = out / "input.jsonl"
    input_path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records))
    sample_path = out / "sample.json"
    sample_path.write_text(
        json.dumps(
            {
                "sample_id": "cmacm_v1_0_0_unseen_15",
                "reports": [
                    {
                        key: record[key]
                        for key in ("sample_order", "diversity_role", "record_id", "document_id", "doi", "title")
                    }
                    for record in records
                ],
                "prior_test_doi_count": len(prior),
                "prior_test_overlap": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    manifest = {
        "model": "CMACM-" + args.version,
        "input": {"path": str(input_path.relative_to(ROOT)), "sha256": sha256(input_path)},
        "sample": {"path": str(sample_path.relative_to(ROOT)), "sha256": sha256(sample_path)},
        "schema": {"path": str((model / "foundation_extraction.schema.json").relative_to(ROOT)), "sha256": sha256(model / "foundation_extraction.schema.json")},
        "prompt": {"path": str((model / "foundation_extraction_prompt.txt").relative_to(ROOT)), "sha256": sha256(model / "foundation_extraction_prompt.txt")},
        "source_master": {"path": str(MASTER.relative_to(ROOT)), "sha256": sha256(MASTER)},
        "source_full_input": {"path": str(FULL_INPUT.relative_to(ROOT)), "sha256": sha256(FULL_INPUT)},
        "input_size_modifications": False,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"records": len(records), "output": str(out), "prior_overlap": sorted(overlap)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
