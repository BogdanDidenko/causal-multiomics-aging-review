#!/usr/bin/env python3
"""Freeze the purposive 12-report v0.3 causal-extraction development sample."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    canonical_sections,
    sha256_file,
    sha256_text,
    write_json,
    write_text,
)
from causal_multiomics_aging_review.evidence_atoms import build_evidence_atom_index

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/v0.3.0"
CORPUS = REPO / "data/full_text_screening/v1.5.3_deterministic_full_text_158/input.jsonl"
ELIGIBILITY = (
    REPO
    / "analysis/full_text_screening/final_eligibility_v1.5.4"
    / "final_eligibility_ledger_158.csv"
)
PRIOR_E0 = REPO / "protocol/causal_extraction/e0_grounding/v0.1.0/sample.json"
PRIOR_CHECKPOINTS = (
    REPO / "protocol/causal_extraction/checkpoints/v0.1.1-rc1/two_sample_design.json"
)
PRIOR_PROFILES = (
    REPO / "analysis/article_design/corpus_grounding_v1.0.0/eligible_graph_profiles_101.jsonl"
)
DEFAULT_OUTPUT = REPO / "data/causal_extraction/v0.3.0_development/inputs"
MAX_ATOM_CHARACTERS = 1000

# Purposive strata were fixed from title, document structure, and previously
# declared development-only graph metadata. These labels are sampling cues,
# never reference answers for causal extraction.
SAMPLE_SPEC = [
    {
        "doi": "10.3389/fendo.2025.1661666",
        "diversity_role": "genetic_instrument_human_disease",
        "anticipated_boundary": "MR with molecular follow-up",
    },
    {
        "doi": "10.1038/s41467-025-59964-z",
        "diversity_role": "population_metabolomic_aging",
        "anticipated_boundary": "observational prediction plus genetic analysis",
    },
    {
        "doi": "10.3390/microorganisms13061379",
        "diversity_role": "assigned_exercise_host_microbiome",
        "anticipated_boundary": "animal intervention with microbiome mediation language",
    },
    {
        "doi": "10.1002/advs.202514269",
        "diversity_role": "microbiota_transfer_cross_system",
        "anticipated_boundary": "donor comparison, transfer, and molecular mechanism",
    },
    {
        "doi": "10.1172/jci.insight.154089",
        "diversity_role": "temporal_cell_perturbation",
        "anticipated_boundary": "time course and targeted rescue",
    },
    {
        "doi": "10.1007/s13238-021-00894-z",
        "diversity_role": "directed_network_with_validation",
        "anticipated_boundary": "regulatory-network inference plus perturbation",
    },
    {
        "doi": "10.7554/elife.71624",
        "diversity_role": "transient_reprogramming_human_cells",
        "anticipated_boundary": "staged intervention with multiple aging readouts",
    },
    {
        "doi": "10.1093/plphys/kiaa034",
        "diversity_role": "plant_leaf_longevity",
        "anticipated_boundary": "plant perturbation and directed pathway model",
    },
    {
        "doi": "10.1016/j.devcel.2023.05.015",
        "diversity_role": "vertebrate_genetic_lifespan",
        "anticipated_boundary": "whole-organism genetic perturbation and lifespan",
    },
    {
        "doi": "10.1186/s40364-023-00458-9",
        "diversity_role": "factorial_genotype_diet_age",
        "anticipated_boundary": "factorial perturbations plus associational cross-omics network",
    },
    {
        "doi": "10.3892/or.2026.9080",
        "diversity_role": "mechanistic_mediation_wording",
        "anticipated_boundary": "pharmacologic and genetic perturbation with mediation wording",
    },
    {
        "doi": "10.1016/j.exger.2025.112815",
        "diversity_role": "assigned_treatment_animal_model",
        "anticipated_boundary": "treatment assignment and multi-omics mechanism",
    },
]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_corpus() -> dict[str, dict[str, Any]]:
    return {str(record["doi"]).casefold(): record for record in _read_jsonl(CORPUS)}


def eligible_report_ids() -> set[str]:
    with ELIGIBILITY.open(newline="", encoding="utf-8") as handle:
        return {
            row["record_id"]
            for row in csv.DictReader(handle)
            if row["final_decision"] == "assessed"
        }


def prior_development_report_ids() -> set[str]:
    e0 = json.loads(PRIOR_E0.read_text(encoding="utf-8"))
    report_ids = {item["report_id"] for item in e0["reports"]}
    checkpoints = json.loads(PRIOR_CHECKPOINTS.read_text(encoding="utf-8"))
    for checkpoint in ("A", "B"):
        report_ids.update(
            item["report_id"] for item in checkpoints["checkpoints"][checkpoint]["reports"]
        )
    return report_ids


def build_sample() -> dict[str, Any]:
    corpus = load_corpus()
    eligible = eligible_report_ids()
    prior = prior_development_report_ids()
    reports = []
    for order, specification in enumerate(SAMPLE_SPEC, start=1):
        doi = specification["doi"].casefold()
        record = corpus.get(doi)
        if record is None:
            raise ValueError(f"Sample DOI is absent from the canonical corpus: {doi}")
        if record["record_id"] not in eligible:
            raise ValueError(f"Sample DOI is not eligible: {doi}")
        if record["record_id"] in prior:
            raise ValueError(f"Sample DOI was used in E0 or checkpoint A/B: {doi}")
        sections = canonical_sections(record)
        atom_index = build_evidence_atom_index(
            record,
            max_atom_characters=MAX_ATOM_CHARACTERS,
        )
        reports.append(
            {
                "sample_order": order,
                "report_id": record["record_id"],
                "document_id": record["document_id"],
                "doi": record["doi"],
                "title": record["title"],
                "diversity_role": specification["diversity_role"],
                "anticipated_boundary": specification["anticipated_boundary"],
                "canonical_section_count": len(sections),
                "canonical_character_count": sum(len(section["text"]) for section in sections),
                "canonical_sections_sha256": sha256_text(canonical_json(record["sections"])),
                "evidence_atom_count": len(atom_index["atoms"]),
                "evidence_atom_index_sha256": sha256_text(canonical_json(atom_index)),
                "evaluation_role": "development_only",
                "prior_e0_or_checkpoint_membership": "none",
            }
        )
    return {
        "sample_id": "causal_extraction_v0.3.0_twelve_report_development_sample",
        "status": "frozen_before_reference_inventory_and_v0.3_model_outputs",
        "freeze_date": "2026-09-02",
        "sampling_method": "purposive_maximum_variation",
        "selection_basis": [
            "causal-design family cue",
            "biological system",
            "aging construct",
            "omics combination",
            "document size and structure",
            "difficult negative or mixed-method boundary",
        ],
        "selection_metadata_warning": (
            "Prior Luna graph profiles were used only as disclosed diversity cues. "
            "They are not reference labels and must not be copied into the inventory."
        ),
        "sampling_frame": {
            "eligible_reports": len(eligible),
            "excluded_prior_e0_or_checkpoint_reports": len(prior & eligible),
            "available_reports_after_exclusion": len(eligible - prior),
            "selected_reports": len(reports),
            "genuinely_sealed": False,
        },
        "atomization": {
            "version": "evidence-atoms-v1",
            "max_atom_characters": MAX_ATOM_CHARACTERS,
            "model_calls": 0,
        },
        "source_files": {
            "canonical_corpus": {
                "path": str(CORPUS.relative_to(REPO)),
                "sha256": sha256_file(CORPUS),
            },
            "eligibility_ledger": {
                "path": str(ELIGIBILITY.relative_to(REPO)),
                "sha256": sha256_file(ELIGIBILITY),
            },
            "prior_graph_profiles": {
                "path": str(PRIOR_PROFILES.relative_to(REPO)),
                "sha256": sha256_file(PRIOR_PROFILES),
                "use": "sampling_diversity_cues_only",
            },
        },
        "reports": reports,
    }


def materialize_inputs(output: Path) -> dict[str, Any]:
    sample = build_sample()
    corpus = load_corpus()
    inventory = []
    for item in sample["reports"]:
        record = corpus[item["doi"].casefold()]
        atom_index = build_evidence_atom_index(
            record,
            max_atom_characters=MAX_ATOM_CHARACTERS,
        )
        report_dir = output / record["document_id"]
        write_json(
            report_dir / "record_metadata.json",
            {key: record.get(key) for key in ("record_id", "document_id", "doi", "title", "year")},
        )
        write_json(report_dir / "evidence_atom_index.json", atom_index)
        write_text(
            report_dir / "canonical_sections.jsonl",
            "".join(
                json.dumps(section, ensure_ascii=False, sort_keys=True) + "\n"
                for section in canonical_sections(record)
            ),
        )
        write_text(
            report_dir / "evidence_atoms.tsv",
            "evidence_atom_id\tsection_id\theading\tdocument_atom_order\traw_text\n"
            + "".join(
                "\t".join(
                    [
                        atom["evidence_atom_id"],
                        atom["section_id"],
                        str(atom["heading"]).replace("\t", " ").replace("\n", " "),
                        str(atom["document_atom_order"]),
                        str(atom["raw_text"]).replace("\t", " ").replace("\n", " "),
                    ]
                )
                + "\n"
                for atom in atom_index["atoms"]
            ),
        )
        inventory.append(
            {
                "report_id": record["record_id"],
                "document_id": record["document_id"],
                "doi": record["doi"],
                "document_sha256": atom_index["document_sha256"],
                "evidence_atom_count": len(atom_index["atoms"]),
                "evidence_atom_index_sha256": sha256_text(canonical_json(atom_index)),
            }
        )
    write_json(output / "source_inventory.json", {"reports": inventory})
    return sample


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write-sample", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    sample = materialize_inputs(args.output.resolve())
    sample_path = SUITE / "sample.json"
    if args.write_sample:
        write_json(sample_path, sample)
    if args.check:
        if not sample_path.is_file():
            raise ValueError(f"Frozen sample is missing: {sample_path}")
        frozen = json.loads(sample_path.read_text(encoding="utf-8"))
        if frozen != sample:
            raise ValueError("Frozen v0.3 development sample is not reproducible")
    print(json.dumps({"reports": len(sample["reports"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
