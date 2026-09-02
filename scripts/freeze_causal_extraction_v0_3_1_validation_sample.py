#!/usr/bin/env python3
"""Freeze the disjoint 15-report validation sample for v0.3.1."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_analysis_inventory import (
    build_compact_report_packet,
    packet_atom_ids,
)
from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    canonical_sections,
    render_prompt,
    sha256_file,
    sha256_text,
    token_count,
    write_json,
    write_text,
)
from causal_multiomics_aging_review.evidence_atoms import build_evidence_atom_index

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/validation/v0.3.1-independent-15-v1.0.0"
CORPUS = REPO / "data/full_text_screening/v1.5.3_deterministic_full_text_158/input.jsonl"
ELIGIBILITY = (
    REPO
    / "analysis/full_text_screening/final_eligibility_v1.5.4"
    / "final_eligibility_ledger_158.csv"
)
SEARCH_FRAME = REPO / "data/screening/v1.1.2_full_corpus/input.csv"
EXTERNAL_ROOT = REPO / "data/causal_extraction/v0.3.1_independent_validation/external"
EXTERNAL_RECORDS = EXTERNAL_ROOT / "external_records.jsonl"
EXTERNAL_MANIFEST = EXTERNAL_ROOT / "manifest.json"
OUTPUT = REPO / "data/causal_extraction/v0.3.1_independent_validation/inputs"
ANNOTATION_OUTPUT = (
    REPO / "data/causal_extraction/v0.3.1_independent_validation/independent_inventories"
)
MAX_ATOM_CHARACTERS = 1000
CONTEXT_WINDOW = 131_072
MAX_RENDERED_PROMPT_TOKENS = 110_000
FREEZE_DATE = "2026-09-03"

PRIOR_SAMPLES = (
    REPO / "protocol/causal_extraction/e0_grounding/v0.1.0/sample.json",
    REPO / "protocol/causal_extraction/checkpoints/v0.1.1-rc1/two_sample_design.json",
    REPO / "protocol/causal_extraction/v0.3.0/sample.json",
)

SAMPLE_SPEC = [
    {
        "doi": "10.14336/ad.2026.0356",
        "source_frame": "eligible_101",
        "diversity_role": "multi_target_mendelian_randomization_aging",
        "anticipated_boundary": "MR screens, colocalization, and target prioritization",
    },
    {
        "doi": "10.1097/md.0000000000047376",
        "source_frame": "eligible_101",
        "diversity_role": "smr_colocalization_human_disease",
        "anticipated_boundary": "SMR identification versus standalone colocalization",
    },
    {
        "doi": "10.1038/s41467-024-52967-2",
        "source_frame": "eligible_101",
        "diversity_role": "centenarian_loss_of_function_variation",
        "anticipated_boundary": "natural genetic variation versus associational depletion",
    },
    {
        "doi": "10.1002/advs.202502249",
        "source_frame": "eligible_101",
        "diversity_role": "multi_stage_human_mouse_perturbation",
        "anticipated_boundary": "omics nomination followed by genetic and pharmacologic tests",
    },
    {
        "doi": "10.1038/s41586-025-09873-4",
        "source_frame": "eligible_101",
        "diversity_role": "cross_system_aged_immunity_intervention",
        "anticipated_boundary": "assigned treatment, cross-tissue outcomes, and validation",
    },
    {
        "doi": "10.1172/jci.insight.174007",
        "source_frame": "eligible_101",
        "diversity_role": "targeted_bmal1_restoration_lifespan",
        "anticipated_boundary": "muscle-specific genetic restoration with systemic aging outcomes",
    },
    {
        "doi": "10.1038/s42255-026-01515-x",
        "source_frame": "eligible_101",
        "diversity_role": "redox_rhythm_aging_perturbation",
        "anticipated_boundary": "temporal language versus assigned perturbation",
    },
    {
        "doi": "10.1080/15548627.2025.2561073",
        "source_frame": "eligible_101",
        "diversity_role": "pharmacologic_and_genetic_mitophagy",
        "anticipated_boundary": "compound treatment and pathway-specific perturbations",
    },
    {
        "doi": "10.3390/plants14152388",
        "source_frame": "eligible_101",
        "diversity_role": "plant_nitrogen_leaf_senescence",
        "anticipated_boundary": (
            "environmental intervention with transcriptome-metabolome integration"
        ),
    },
    {
        "doi": "10.1038/s41438-020-00420-y",
        "source_frame": "eligible_101",
        "diversity_role": "plant_mirna_network_and_validation",
        "anticipated_boundary": "directed regulatory wording versus empirical perturbation",
    },
    {
        "doi": "10.21037/tcr-2026-1-0264",
        "source_frame": "eligible_101",
        "diversity_role": "prediction_only_boundary",
        "anticipated_boundary": "machine learning and enrichment without a causal design",
    },
    {
        "doi": "10.1093/geroni/igaf122.3850",
        "source_frame": "eligible_101",
        "diversity_role": "thin_conference_intervention_report",
        "anticipated_boundary": "short report with multi-omics screening and drug treatment",
    },
    {
        "doi": "10.1111/acel.70279",
        "source_frame": "targeted_search_frame_challenge",
        "diversity_role": "formal_mediation_positive_challenge",
        "anticipated_boundary": "formal mediation across genomic and epigenomic measures",
    },
    {
        "doi": "10.1186/s13040-025-00432-1",
        "source_frame": "targeted_search_frame_challenge",
        "diversity_role": "formal_mediation_multiomics_boundary",
        "anticipated_boundary": "genetics, behavior, and imaging versus molecular multi-omics",
    },
    {
        "doi": "10.1093/geroni/igad104.2477",
        "source_frame": "targeted_search_frame_challenge",
        "diversity_role": "bayesian_network_future_work_boundary",
        "anticipated_boundary": "formal directed method versus future or preliminary analysis",
    },
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def eligible_report_ids() -> set[str]:
    with ELIGIBILITY.open(newline="", encoding="utf-8") as handle:
        return {
            row["record_id"]
            for row in csv.DictReader(handle)
            if row["final_decision"] == "assessed"
        }


def search_frame_dois() -> set[str]:
    with SEARCH_FRAME.open(newline="", encoding="utf-8") as handle:
        return {
            str(row.get("doi", "")).casefold()
            for row in csv.DictReader(handle)
            if str(row.get("doi", "")).strip()
        }


def prior_report_ids_and_dois() -> tuple[set[str], set[str]]:
    report_ids: set[str] = set()
    dois: set[str] = set()
    for path in PRIOR_SAMPLES:
        value = json.loads(path.read_text(encoding="utf-8"))
        if "checkpoints" in value:
            reports = [
                report
                for checkpoint in value["checkpoints"].values()
                for report in checkpoint["reports"]
            ]
        else:
            reports = value.get("reports", [])
        for report in reports:
            if report.get("report_id"):
                report_ids.add(str(report["report_id"]))
            if report.get("doi"):
                dois.add(str(report["doi"]).casefold())
    return report_ids, dois


def load_records() -> tuple[dict[str, dict[str, Any]], set[str]]:
    canonical = read_jsonl(CORPUS)
    external = read_jsonl(EXTERNAL_RECORDS)
    canonical_dois = {
        str(record.get("doi", "")).casefold() for record in canonical if record.get("doi")
    }
    all_records = canonical + external
    by_doi = {str(record["doi"]).casefold(): record for record in all_records}
    if len(by_doi) != len(all_records):
        raise ValueError("Duplicate DOI across canonical and external validation records")
    return by_doi, canonical_dois


def build_sample() -> dict[str, Any]:
    if not EXTERNAL_MANIFEST.is_file() or not EXTERNAL_RECORDS.is_file():
        raise FileNotFoundError("Prepare deterministic external validation records first")
    records, canonical_dois = load_records()
    eligible = eligible_report_ids()
    broader_search = search_frame_dois()
    prior_ids, prior_dois = prior_report_ids_and_dois()
    selected = []
    for order, specification in enumerate(SAMPLE_SPEC, start=1):
        doi = specification["doi"].casefold()
        record = records.get(doi)
        if record is None:
            raise ValueError(f"Validation DOI has no deterministic record: {doi}")
        if record["record_id"] in prior_ids or doi in prior_dois:
            raise ValueError(f"Validation DOI appeared in prior causal development: {doi}")
        source_frame = specification["source_frame"]
        if source_frame == "eligible_101":
            if doi not in canonical_dois or record["record_id"] not in eligible:
                raise ValueError(f"Corpus validation DOI is not eligible: {doi}")
        elif source_frame == "targeted_search_frame_challenge":
            if doi not in broader_search:
                raise ValueError(f"External challenge is absent from search frame: {doi}")
            if doi in canonical_dois:
                raise ValueError(
                    f"External challenge unexpectedly appears in canonical corpus: {doi}"
                )
        else:
            raise ValueError(f"Unknown source frame: {source_frame}")

        sections = canonical_sections(record)
        atom_index = build_evidence_atom_index(record, max_atom_characters=MAX_ATOM_CHARACTERS)
        selected.append(
            {
                "sample_order": order,
                "report_id": record["record_id"],
                "document_id": record["document_id"],
                "doi": record["doi"],
                "title": record["title"],
                "source_frame": source_frame,
                "diversity_role": specification["diversity_role"],
                "anticipated_boundary": specification["anticipated_boundary"],
                "canonical_section_count": len(sections),
                "canonical_character_count": sum(len(section["text"]) for section in sections),
                "canonical_sections_sha256": sha256_text(canonical_json(record["sections"])),
                "evidence_atom_count": len(atom_index["atoms"]),
                "evidence_atom_index_sha256": sha256_text(canonical_json(atom_index)),
                "prior_causal_extraction_membership": "none",
            }
        )
    return {
        "sample_id": "v0.3.1_independent_validation_15_v1.0.0",
        "status": "frozen_before_independent_inventory_outputs",
        "freeze_date": FREEZE_DATE,
        "sampling_method": "purposive_maximum_variation_with_targeted_challenges",
        "sample_size": len(selected),
        "composition": {
            "disjoint_full_text_eligible_reports": sum(
                item["source_frame"] == "eligible_101" for item in selected
            ),
            "targeted_search_frame_challenges": sum(
                item["source_frame"] == "targeted_search_frame_challenge" for item in selected
            ),
        },
        "independence": {
            "disjoint_from_e0": True,
            "disjoint_from_v0_1_checkpoints": True,
            "disjoint_from_v0_3_development": True,
            "expert_gold": False,
            "reviewers": ["codex", "claude_opus_4_8"],
        },
        "selection_information_allowed": [
            "title",
            "abstract",
            "document length",
            "full-text eligibility status",
            "prior graph labels as non-reference diversity cues",
        ],
        "atomization": {
            "version": "evidence-atoms-v1",
            "max_atom_characters": MAX_ATOM_CHARACTERS,
        },
        "source_files": {
            "canonical_corpus": {
                "path": relative(CORPUS),
                "sha256": sha256_file(CORPUS),
            },
            "eligibility_ledger": {
                "path": relative(ELIGIBILITY),
                "sha256": sha256_file(ELIGIBILITY),
            },
            "search_frame": {
                "path": relative(SEARCH_FRAME),
                "sha256": sha256_file(SEARCH_FRAME),
            },
            "external_manifest": {
                "path": relative(EXTERNAL_MANIFEST),
                "sha256": sha256_file(EXTERNAL_MANIFEST),
            },
        },
        "reports": selected,
    }


def materialize_inputs(sample: dict[str, Any]) -> None:
    records, _ = load_records()
    inventory = []
    for item in sample["reports"]:
        record = records[item["doi"].casefold()]
        atom_index = build_evidence_atom_index(record, max_atom_characters=MAX_ATOM_CHARACTERS)
        report_dir = OUTPUT / record["document_id"]
        write_json(
            report_dir / "record_metadata.json",
            {
                key: record.get(key)
                for key in ("record_id", "document_id", "doi", "title", "year", "source")
            },
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
                "source_frame": item["source_frame"],
                "document_sha256": atom_index["document_sha256"],
                "evidence_atom_count": len(atom_index["atoms"]),
                "evidence_atom_index_sha256": sha256_text(canonical_json(atom_index)),
            }
        )
    write_json(OUTPUT / "source_inventory.json", {"reports": inventory})


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": relative(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def build_packaging_audit(sample: dict[str, Any]) -> dict[str, Any]:
    task = (SUITE / "annotation_task.txt").read_text(encoding="utf-8")
    manual = (SUITE / "annotation_manual.md").read_text(encoding="utf-8")
    codebook = (REPO / "protocol/causal_extraction/v0.3.1/codebook.md").read_text(encoding="utf-8")
    reports = []
    for item in sample["reports"]:
        atom_index = json.loads(
            (OUTPUT / item["document_id"] / "evidence_atom_index.json").read_text(encoding="utf-8")
        )
        packet = build_compact_report_packet(atom_index)
        source_ids = [atom["evidence_atom_id"] for atom in atom_index["atoms"]]
        serialized_ids = packet_atom_ids(packet)
        if serialized_ids != source_ids:
            raise ValueError(f"Evidence packet coverage mismatch: {item['doi']}")
        reviewer_tokens = {}
        for reviewer_id in ("codex", "claude_opus_4_8"):
            rendered = render_prompt(
                task,
                {
                    "REVIEWER_ID": reviewer_id,
                    "REPORT_ID": item["report_id"],
                    "ANNOTATION_MANUAL": manual,
                    "CODEBOOK": codebook,
                    "REPORT_PACKET": packet,
                },
            )
            reviewer_tokens[reviewer_id] = token_count(rendered)
            if reviewer_tokens[reviewer_id] > MAX_RENDERED_PROMPT_TOKENS:
                raise ValueError(
                    f"Rendered annotation exceeds limit for {item['doi']}: "
                    f"{reviewer_tokens[reviewer_id]}"
                )
        reports.append(
            {
                "sample_order": item["sample_order"],
                "report_id": item["report_id"],
                "document_id": item["document_id"],
                "doi": item["doi"],
                "atom_count": len(source_ids),
                "serialized_atom_count": len(serialized_ids),
                "atom_order_exact": serialized_ids == source_ids,
                "packet_sha256": sha256_text(packet),
                "rendered_prompt_tokens": reviewer_tokens,
            }
        )
    return {
        "packaging_version": "independent_inventory_all_evidence_atoms_compact_v1",
        "report_count": len(reports),
        "coverage_complete": all(item["atom_order_exact"] for item in reports),
        "omitted_report_atom_count": 0,
        "model_selected_content": False,
        "graph_selected_content": False,
        "context_window": CONTEXT_WINDOW,
        "max_rendered_prompt_tokens": MAX_RENDERED_PROMPT_TOKENS,
        "observed_max_rendered_prompt_tokens": max(
            max(item["rendered_prompt_tokens"].values()) for item in reports
        ),
        "reports": reports,
    }


def build_manifest(sample: dict[str, Any]) -> dict[str, Any]:
    protocol_files = [
        SUITE / "sampling_protocol.md",
        SUITE / "annotation_manual.md",
        SUITE / "annotation_task.txt",
        SUITE / "reference_inventory.schema.json",
        SUITE / "runtime.json",
        SUITE / "sample.json",
        SUITE / "phase1_packaging_audit.json",
        REPO / "protocol/causal_extraction/v0.3.1/codebook.md",
        REPO / "protocol/causal_extraction/v0.3.1/prompt.txt",
        REPO / "protocol/causal_extraction/v0.3.1/candidate_classification.schema.json",
        REPO / "protocol/causal_extraction/v0.3.1/runtime.json",
        Path(__file__),
        REPO / "scripts/prepare_causal_validation_external_reports.py",
        REPO / "scripts/run_independent_causal_inventory.py",
        REPO / "src/causal_multiomics_aging_review/causal_analysis_inventory.py",
        REPO / "tests/test_independent_causal_inventory.py",
        REPO / "tests/test_causal_extraction_v0_3_1_validation_sample.py",
    ]
    source_files = [
        CORPUS,
        ELIGIBILITY,
        SEARCH_FRAME,
        EXTERNAL_RECORDS,
        EXTERNAL_MANIFEST,
        OUTPUT / "source_inventory.json",
    ]
    evidence_files = [
        OUTPUT / item["document_id"] / "evidence_atom_index.json" for item in sample["reports"]
    ]
    return {
        "manifest_version": "1.0.0",
        "validation_id": sample["sample_id"],
        "protocol_artifacts": [file_record(path) for path in protocol_files],
        "source_artifacts": [file_record(path) for path in source_files],
        "evidence_atom_indices": [file_record(path) for path in evidence_files],
    }


def independent_output_count() -> int:
    if not ANNOTATION_OUTPUT.exists():
        return 0
    return sum(1 for path in ANNOTATION_OUTPUT.rglob("normalized.json") if path.is_file())


def write_freeze() -> None:
    if independent_output_count():
        raise ValueError("Refusing to freeze after independent annotations exist")
    sample = build_sample()
    write_json(SUITE / "sample.json", sample)
    materialize_inputs(sample)
    write_json(SUITE / "phase1_packaging_audit.json", build_packaging_audit(sample))
    manifest = build_manifest(sample)
    write_json(SUITE / "phase1_artifact_manifest.json", manifest)
    write_json(
        SUITE / "phase1_freeze.json",
        {
            "freeze_version": "1.0.0",
            "status": "frozen_before_independent_inventory_outputs",
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "artifact_manifest_sha256": sha256_file(SUITE / "phase1_artifact_manifest.json"),
            "independent_output_count_at_freeze": 0,
            "inherits_v0_3_1_without_modification": True,
            "expert_gold_standard": False,
        },
    )


def check_freeze() -> None:
    sample = build_sample()
    if json.loads((SUITE / "sample.json").read_text(encoding="utf-8")) != sample:
        raise ValueError("Frozen validation sample is stale")
    materialize_inputs(sample)
    packaging_audit = build_packaging_audit(sample)
    if (
        json.loads((SUITE / "phase1_packaging_audit.json").read_text(encoding="utf-8"))
        != packaging_audit
    ):
        raise ValueError("Validation packaging audit is stale")
    manifest = build_manifest(sample)
    if (
        json.loads((SUITE / "phase1_artifact_manifest.json").read_text(encoding="utf-8"))
        != manifest
    ):
        raise ValueError("Validation artifact manifest is stale")
    freeze = json.loads((SUITE / "phase1_freeze.json").read_text(encoding="utf-8"))
    if freeze["artifact_manifest_sha256"] != sha256_file(SUITE / "phase1_artifact_manifest.json"):
        raise ValueError("Validation freeze does not match its manifest")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("Choose exactly one of --write or --check")
    if args.write:
        write_freeze()
    else:
        check_freeze()
    print(json.dumps({"sample_reports": len(SAMPLE_SPEC), "status": "verified"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
