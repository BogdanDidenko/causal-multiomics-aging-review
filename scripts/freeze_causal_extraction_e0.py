#!/usr/bin/env python3
"""Freeze the deterministic six-report E0 grounding experiment."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    canonical_sections,
    render_prompt,
    sha256_file,
    sha256_text,
    token_count,
    write_json,
)
from causal_multiomics_aging_review.evidence_atoms import (
    build_evidence_atom_index,
    build_evidence_atom_windows,
    evidence_packet,
    table_density,
)

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol/causal_extraction/e0_grounding/v0.1.0"
CORPUS = REPO / "data/full_text_screening/v1.5.3_deterministic_full_text_158/input.jsonl"
ELIGIBILITY = (
    REPO
    / "analysis/full_text_screening/final_eligibility_v1.5.4"
    / "final_eligibility_ledger_158.csv"
)
CHECKPOINT_DESIGN = (
    REPO / "protocol/causal_extraction/checkpoints/v0.1.1-rc1" / "two_sample_design.json"
)
GRAPH_PROFILES = (
    REPO / "analysis/article_design/corpus_grounding_v1.0.0" / "eligible_graph_profiles_101.jsonl"
)
GRAPH_AGENT_MANIFEST = (
    REPO / "analysis/article_design/corpus_grounding_v1.0.0" / "agent_manifest.json"
)
SEED = "20260829-e0-grounding-development-v1"
PACKAGING_CANDIDATES = [
    {
        "candidate_id": "char_only_48k",
        "max_core_characters": 48000,
        "context_characters_per_side": 4000,
        "max_core_atoms": None,
        "max_context_atoms_per_side": None,
    },
    {
        "candidate_id": "char_only_32k",
        "max_core_characters": 32000,
        "context_characters_per_side": 2000,
        "max_core_atoms": None,
        "max_context_atoms_per_side": None,
    },
    {
        "candidate_id": "bounded_30k_300_atoms",
        "max_core_characters": 30000,
        "context_characters_per_side": 2000,
        "max_core_atoms": 300,
        "max_context_atoms_per_side": 30,
    },
    {
        "candidate_id": "bounded_26k_250_atoms",
        "max_core_characters": 26000,
        "context_characters_per_side": 1500,
        "max_core_atoms": 250,
        "max_context_atoms_per_side": 20,
    },
    {
        "candidate_id": "bounded_24k_250_atoms",
        "max_core_characters": 24000,
        "context_characters_per_side": 1500,
        "max_core_atoms": 250,
        "max_context_atoms_per_side": 20,
    },
    {
        "candidate_id": "bounded_22k_220_atoms",
        "max_core_characters": 22000,
        "context_characters_per_side": 1000,
        "max_core_atoms": 220,
        "max_context_atoms_per_side": 15,
    },
]

# One underlying study should not occupy two development slots.
SUPERSEDED_REPORT_VERSIONS = {
    "10.21203/rs.3.rs-1264931/v1": "10.26508/lsa.202201492",
    "10.1101/2025.10.29.685384": "10.1002/advs.202521633",
    "10.1101/2025.06.19.660635": "10.1161/circresaha.125.327427",
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def load_corpus() -> dict[str, dict[str, Any]]:
    return {record["record_id"]: record for record in _read_jsonl(CORPUS)}


def eligible_report_ids() -> set[str]:
    with ELIGIBILITY.open(newline="", encoding="utf-8") as handle:
        return {
            row["record_id"]
            for row in csv.DictReader(handle)
            if row["final_decision"] == "assessed"
        }


def checkpoint_membership() -> dict[str, str]:
    design = json.loads(CHECKPOINT_DESIGN.read_text(encoding="utf-8"))
    return {
        report["report_id"]: checkpoint
        for checkpoint in ("A", "B")
        for report in design["checkpoints"][checkpoint]["reports"]
    }


def exposure_audit() -> dict[str, Any]:
    eligible = eligible_report_ids()
    graph_profiles = _read_jsonl(GRAPH_PROFILES)
    graph_ids = {profile["record_id"] for profile in graph_profiles}
    checkpoints = checkpoint_membership()
    if len(eligible) != 101:
        raise ValueError(f"Expected 101 eligible reports, found {len(eligible)}")
    if graph_ids != eligible:
        raise ValueError(
            "Graph-profile exposure does not match eligible corpus: "
            f"missing={len(eligible - graph_ids)}, extra={len(graph_ids - eligible)}"
        )
    outside_checkpoints = eligible - checkpoints.keys()
    return {
        "audit_id": "causal_extraction_e0_prior_exposure_audit",
        "audit_date": "2026-08-29",
        "eligible_reports": len(eligible),
        "reports_with_prior_luna_graph_profile": len(graph_ids),
        "reports_in_checkpoint_a": sum(value == "A" for value in checkpoints.values()),
        "reports_in_checkpoint_b": sum(value == "B" for value in checkpoints.values()),
        "reports_outside_checkpoints_a_b": len(outside_checkpoints),
        "genuinely_sealed_internal_reports": 0,
        "interpretation": (
            "All eligible reports had model-generated Luna Light graph profiles, and "
            "four article-design agents reviewed all 101 profiles. Reports outside "
            "checkpoints A and B remain usable for development, but none may be "
            "represented as an untouched sealed evaluation set."
        ),
        "future_sealed_requirement": (
            "Acquire an external or temporal report sample after the replacement "
            "instrument, runtime, code, and acceptance thresholds are frozen."
        ),
        "sources": {
            "graph_profiles": {
                "path": str(GRAPH_PROFILES.relative_to(REPO)),
                "sha256": sha256_file(GRAPH_PROFILES),
            },
            "graph_agent_manifest": {
                "path": str(GRAPH_AGENT_MANIFEST.relative_to(REPO)),
                "sha256": sha256_file(GRAPH_AGENT_MANIFEST),
            },
            "checkpoint_design": {
                "path": str(CHECKPOINT_DESIGN.relative_to(REPO)),
                "sha256": sha256_file(CHECKPOINT_DESIGN),
            },
        },
    }


def _tie_break(label: str, report_id: str) -> str:
    return hashlib.sha256(f"{SEED}|{label}|{report_id}".encode()).hexdigest()


def build_sample() -> dict[str, Any]:
    corpus = load_corpus()
    eligible = eligible_report_ids()
    checkpoints = checkpoint_membership()
    superseded = set(SUPERSEDED_REPORT_VERSIONS)
    pool = [
        corpus[report_id]
        for report_id in eligible
        if report_id not in checkpoints
        and str(corpus[report_id]["doi"]).casefold() not in superseded
    ]
    pool.sort(
        key=lambda record: (
            sum(len(section["text"]) for section in canonical_sections(record)),
            _tie_break("size", record["record_id"]),
        )
    )
    if len(pool) < 6:
        raise ValueError("E0 development pool is too small")

    strata: dict[int, list[dict[str, Any]]] = {1: [], 2: [], 3: []}
    for position, record in enumerate(pool):
        tercile = min(3, (position * 3) // len(pool) + 1)
        sections = canonical_sections(record)
        strata[tercile].append(
            {
                "report_id": record["record_id"],
                "document_id": record["document_id"],
                "doi": record["doi"],
                "title": record["title"],
                "document_size_tercile": tercile,
                "canonical_section_count": len(sections),
                "canonical_section_characters": sum(len(section["text"]) for section in sections),
                "table_density": table_density(record),
                "canonical_sections_sha256": sha256_text(canonical_json(record["sections"])),
                "prior_luna_graph_profile": True,
                "prior_checkpoint": "none",
                "evaluation_role": "development_only",
            }
        )

    selected: list[dict[str, Any]] = []
    for tercile, records in strata.items():
        low = min(
            records,
            key=lambda item: (
                item["table_density"],
                _tie_break(f"tercile-{tercile}-low", item["report_id"]),
            ),
        )
        remaining = [item for item in records if item["report_id"] != low["report_id"]]
        high = min(
            remaining,
            key=lambda item: (
                -item["table_density"],
                _tie_break(f"tercile-{tercile}-high", item["report_id"]),
            ),
        )
        selected.extend(
            [
                {**low, "table_density_role": "low_within_tercile"},
                {**high, "table_density_role": "high_within_tercile"},
            ]
        )

    return {
        "sample_id": "causal_extraction_e0_six_report_development_sample",
        "status": "frozen_development_sample",
        "freeze_date": "2026-08-29",
        "seed": SEED,
        "sampling_frame": {
            "eligible_reports": len(eligible),
            "excluded_checkpoint_a_or_b": len(checkpoints),
            "excluded_superseded_report_versions": len(
                [
                    record
                    for record in corpus.values()
                    if record["record_id"] in eligible
                    and str(record["doi"]).casefold() in superseded
                    and record["record_id"] not in checkpoints
                ]
            ),
            "development_pool": len(pool),
            "genuinely_sealed": False,
        },
        "selection_rule": (
            "Sort by canonical character count and seeded hash; assign size "
            "terciles; choose one minimum-density and one maximum-density report "
            "per tercile with seeded hash tie breaks."
        ),
        "superseded_report_versions": SUPERSEDED_REPORT_VERSIONS,
        "reports": [
            {**report, "sample_order": order} for order, report in enumerate(selected, start=1)
        ],
    }


def build_packaging_calibration() -> dict[str, Any]:
    runtime = json.loads((SUITE / "runtime.json").read_text(encoding="utf-8"))
    sample = json.loads((SUITE / "sample.json").read_text(encoding="utf-8"))
    corpus = load_corpus()
    template = (SUITE / "prompts/inventory_template.txt").read_text(encoding="utf-8")
    grounding_contracts = {
        arm: (SUITE / config["grounding_contract"]).read_text(encoding="utf-8")
        for arm, config in runtime["arms"].items()
    }
    indexes = {
        item["report_id"]: build_evidence_atom_index(
            corpus[item["report_id"]],
            max_atom_characters=runtime["atomization"]["max_atom_characters"],
        )
        for item in sample["reports"]
    }
    results = []
    for candidate in PACKAGING_CANDIDATES:
        prompt_tokens: list[int] = []
        work_units = 0
        for item in sample["reports"]:
            index = indexes[item["report_id"]]
            windows = build_evidence_atom_windows(
                index,
                max_core_characters=candidate["max_core_characters"],
                context_characters_per_side=candidate["context_characters_per_side"],
                max_core_atoms=candidate["max_core_atoms"],
                max_context_atoms_per_side=candidate["max_context_atoms_per_side"],
            )
            work_units += len(windows)
            for window in windows:
                packet = evidence_packet(index, window)
                included_sections = {
                    *window["core_section_ids"],
                    *window["context_section_ids"],
                }
                substitutions = {
                    "REPORT_TITLE": item["title"],
                    "SECTION_INDEX_JSON": json.dumps(
                        [
                            {
                                "section_id": section["section_id"],
                                "heading": section["heading"],
                                "page_numbers": section["page_numbers"],
                            }
                            for section in index["sections"]
                            if section["section_id"] in included_sections
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
                    "EVIDENCE_ATOMS_JSON": json.dumps(
                        packet, ensure_ascii=False, separators=(",", ":")
                    ),
                }
                for _arm, contract in grounding_contracts.items():
                    prompt = render_prompt(
                        template,
                        {**substitutions, "GROUNDING_CONTRACT": contract},
                    )
                    prompt_tokens.append(token_count(prompt))
        ordered = sorted(prompt_tokens)
        result = {
            **candidate,
            "report_count": len(sample["reports"]),
            "work_unit_count": work_units,
            "planned_calls": (work_units * len(runtime["arms"]) * runtime["repeats_per_arm"]),
            "rendered_prompt_count": len(prompt_tokens),
            "minimum_rendered_prompt_tokens": min(prompt_tokens),
            "mean_rendered_prompt_tokens": sum(prompt_tokens) / len(prompt_tokens),
            "p95_rendered_prompt_tokens": ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)],
            "maximum_rendered_prompt_tokens": max(prompt_tokens),
            "passes_frozen_prompt_token_limit": max(prompt_tokens)
            <= runtime["packaging"]["maximum_rendered_prompt_tokens"],
        }
        results.append(result)
    passing = [item for item in results if item["passes_frozen_prompt_token_limit"]]
    selected = min(
        passing,
        key=lambda item: (
            item["planned_calls"],
            item["maximum_rendered_prompt_tokens"],
            item["candidate_id"],
        ),
    )
    runtime_fields = {
        key: runtime["packaging"][key]
        for key in (
            "max_core_characters",
            "context_characters_per_side",
            "max_core_atoms",
            "max_context_atoms_per_side",
        )
    }
    selected_fields = {key: selected[key] for key in runtime_fields}
    if runtime_fields != selected_fields:
        raise ValueError("Frozen runtime does not match packaging calibration selection")
    return {
        "calibration_id": "e0_pre_model_deterministic_packaging_calibration",
        "date": "2026-08-29",
        "model_calls": 0,
        "tokenizer": "o200k_base",
        "sample_id": sample["sample_id"],
        "selection_rule": (
            "Among candidates below the frozen 23,000-token input limit, minimize "
            "planned calls; break ties by lower maximum prompt tokens, then ID."
        ),
        "selected_candidate_id": selected["candidate_id"],
        "candidates": results,
    }


def artifact_manifest() -> dict[str, Any]:
    paths = [
        SUITE / "protocol.md",
        SUITE / "run_artifact_contract.md",
        SUITE / "semantic_audit_codebook.md",
        SUITE / "runtime.json",
        SUITE / "sample.json",
        SUITE / "contamination_audit.json",
        SUITE / "packaging_calibration.json",
        SUITE / "prompts/inventory_template.txt",
        SUITE / "prompts/grounding_evidence_atom_id.txt",
        SUITE / "prompts/grounding_verbatim_quote.txt",
        SUITE / "schemas/inventory_evidence_atom_id.schema.json",
        SUITE / "schemas/inventory_verbatim_quote.schema.json",
        REPO / "src/causal_multiomics_aging_review/evidence_atoms.py",
        REPO / "src/causal_multiomics_aging_review/causal_extraction.py",
        REPO / "src/causal_multiomics_aging_review/llm.py",
        REPO / "scripts/freeze_causal_extraction_e0.py",
        REPO / "scripts/run_causal_extraction_e0.py",
        REPO / "scripts/summarize_causal_extraction_e0.py",
        REPO / "tests/test_causal_extraction_e0.py",
    ]
    missing = [str(path.relative_to(REPO)) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"E0 freeze artifacts are missing: {missing}")
    return {
        "manifest_id": "causal_extraction_e0_grounding_v0.1.0",
        "freeze_date": "2026-08-29",
        "artifacts": [
            {
                "path": str(path.relative_to(REPO)),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in paths
        ],
        "source_data": [
            {
                "path": str(path.relative_to(REPO)),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in (
                CORPUS,
                ELIGIBILITY,
                CHECKPOINT_DESIGN,
                GRAPH_PROFILES,
                GRAPH_AGENT_MANIFEST,
            )
        ],
    }


def write_freeze() -> None:
    write_json(SUITE / "contamination_audit.json", exposure_audit())
    write_json(SUITE / "sample.json", build_sample())
    write_json(SUITE / "packaging_calibration.json", build_packaging_calibration())
    manifest = artifact_manifest()
    write_json(SUITE / "artifact_manifest.json", manifest)
    write_json(
        SUITE / "freeze.json",
        {
            "experiment_id": "causal_extraction_e0_grounding",
            "version": "0.1.0",
            "status": "frozen_before_any_e0_terra_output",
            "freeze_date": "2026-08-29",
            "freeze_revision": "the Git commit containing this file",
            "model_calls_before_freeze": 0,
            "artifact_manifest_path": str((SUITE / "artifact_manifest.json").relative_to(REPO)),
            "artifact_manifest_sha256": sha256_file(SUITE / "artifact_manifest.json"),
            "scientific_output_allowed": False,
            "maximum_pre_human_verdict": ("technical_pass_pending_human_semantic_audit"),
        },
    )


def main() -> int:
    write_freeze()
    print(f"wrote frozen E0 package under {SUITE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
