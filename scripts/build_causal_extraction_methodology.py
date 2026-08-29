#!/usr/bin/env python3
"""Build and validate the frozen causal-extraction methodology package."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SUITE_VERSION = "0.1.0-rc1"
PACKAGE = REPO_ROOT / f"protocol/causal_extraction/prompt_suite/v{SUITE_VERSION}"
CODEBOOK = REPO_ROOT / "protocol/causal_extraction/v0.2.0/codebook.md"
CLAIM_SCHEMA = (
    REPO_ROOT / "protocol/causal_extraction/v0.2.0/claim_record.schema.json"
)
MANIFEST = PACKAGE / "artifact_manifest.json"
FREEZE = PACKAGE / "freeze.json"
CHECKPOINT = PACKAGE / "checkpoint_inventory.json"
PILOT_REPORTS = (
    REPO_ROOT / "analysis/causal_extraction/codebook_pilot_v0.1.0/reports_15.csv"
)
ELIGIBILITY_LEDGER = (
    REPO_ROOT
    / "analysis/full_text_screening/final_eligibility_v1.5.4"
    / "final_eligibility_ledger_158.csv"
)

PROMPT_PLACEHOLDERS = {
    "prompts/open_claim_discovery.txt": {
        "REPORT_ID",
        "DOCUMENT_SHA256",
        "WORK_UNIT_ID",
        "CORE_SECTION_IDS_JSON",
        "CONTEXT_SECTION_IDS_JSON",
        "CANONICAL_SECTIONS_JSON",
    },
    "prompts/dense_claim_coverage.txt": {
        "REPORT_ID",
        "DOCUMENT_SHA256",
        "WORK_UNIT_ID",
        "CORE_SECTION_IDS_JSON",
        "CONTEXT_SECTION_IDS_JSON",
        "CANONICAL_SECTIONS_JSON",
    },
    "prompts/fixed_candidate_classifier.txt": {
        "REPORT_ID",
        "CANDIDATE_REF",
        "PROVISIONAL_CLAIM_ID",
        "FROZEN_CANDIDATE_JSON",
        "EVIDENCE_PACKET_JSON",
        "CODEBOOK_TEXT",
    },
    "prompts/final_claim_adjudicator.txt": {
        "REPORT_ID",
        "CANDIDATE_INVENTORY_SHA256",
        "FROZEN_CANDIDATES_JSON",
        "FIVE_RUN_OUTPUTS_JSON",
        "CANONICAL_EVIDENCE_JSON",
        "CODEBOOK_TEXT",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_text(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n"


def evidence_anchor_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["section_id", "quote", "support_role"],
        "properties": {
            "section_id": {"type": "string", "minLength": 1},
            "quote": {"type": "string", "minLength": 1},
            "support_role": {
                "type": "string",
                "enum": [
                    "author_claim",
                    "current_report_attribution",
                    "design_or_method",
                    "variation_or_assignment",
                    "contrast",
                    "assumption",
                    "diagnostic",
                    "result",
                    "omics_role",
                    "validation",
                    "limitation",
                    "source_adequacy",
                ],
            },
        },
    }


def candidate_schema() -> dict[str, Any]:
    fields = [
        "normalized_claim",
        "exposure_or_intervention",
        "exposure_operation",
        "comparator",
        "outcome",
        "population_or_model",
        "biological_system",
        "time_horizon",
        "split_note",
    ]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "candidate_local_id",
            "current_report_attribution",
            *fields,
            "candidate_kind",
            "result_signal",
            "evidence_anchors",
        ],
        "properties": {
            "candidate_local_id": {
                "type": "string",
                "pattern": "^candidate_[0-9]{3}$",
            },
            "current_report_attribution": {
                "type": "string",
                "enum": ["yes", "no", "unclear"],
            },
            **{field: {"type": "string"} for field in fields},
            "candidate_kind": {
                "type": "string",
                "enum": [
                    "effect",
                    "mechanism",
                    "directed_hypothesis",
                    "mediation",
                    "prioritization",
                ]
                + (["association_link"] if SUITE_VERSION == "0.1.0-rc1" else [])
                + ["unclear"],
            },
            "result_signal": {
                "type": "string",
                "enum": [
                    "supports",
                    "does_not_support",
                    "null",
                    "mixed",
                    "conflicting",
                    "not_reported",
                    "unclear",
                ],
            },
            "evidence_anchors": {
                "type": "array",
                "minItems": 1,
                "items": evidence_anchor_schema(),
            },
        },
    }


def evidence_atom_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "atom_local_id",
            "evidence_type",
            "candidate_local_ids",
            "section_id",
            "quote",
        ],
        "properties": {
            "atom_local_id": {
                "type": "string",
                "pattern": "^atom_[0-9]{3}$",
            },
            "evidence_type": {
                "type": "string",
                "enum": [
                    "design_or_method",
                    "variation_source",
                    "assignment",
                    "contrast",
                    "assumption",
                    "diagnostic",
                    "result",
                    "omics_role",
                    "validation",
                    "limitation",
                    "source_adequacy",
                ],
            },
            "candidate_local_ids": {
                "type": "array",
                "uniqueItems": True,
                "items": {
                    "type": "string",
                    "pattern": "^candidate_[0-9]{3}$",
                },
            },
            "section_id": {"type": "string", "minLength": 1},
            "quote": {"type": "string", "minLength": 1},
        },
    }


def discovery_schema(stage: str) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"{stage} output v{SUITE_VERSION}",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "report_id",
            "document_sha256",
            "stage",
            "work_unit_id",
            "core_section_ids",
            "context_section_ids",
            "candidates",
            "evidence_atoms",
            "coverage_note",
        ],
        "properties": {
            "report_id": {"type": "string", "minLength": 1},
            "document_sha256": {
                "type": "string",
                "pattern": "^[a-f0-9]{64}$",
            },
            "stage": {"const": stage},
            "work_unit_id": {"type": "string", "minLength": 1},
            "core_section_ids": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "context_section_ids": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "candidates": {"type": "array", "items": candidate_schema()},
            "evidence_atoms": {"type": "array", "items": evidence_atom_schema()},
            "coverage_note": {"type": "string"},
        },
    }


def embedded_claim_defs() -> dict[str, Any]:
    base = json.loads(CLAIM_SCHEMA.read_text())
    claim_record = {
        key: copy.deepcopy(value)
        for key, value in base.items()
        if key not in {"$schema", "$id", "$defs", "title"}
    }
    defs = copy.deepcopy(base.get("$defs", {}))
    defs["claim_record"] = claim_record
    defs["candidate_nomination"] = candidate_schema()
    defs["evidence_anchor"] = evidence_anchor_schema()
    return defs


def fixed_classifier_schema() -> dict[str, Any]:
    statuses = [
        "valid_single_claim",
        "split_required",
        "duplicate_or_overlapping",
        "background_or_cited_work",
        "no_current_report_empirical_result",
        "context_only",
        "insufficient_source",
    ]
    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"Fixed candidate classifier output v{SUITE_VERSION}",
        "type": "object",
        "additionalProperties": False,
        "$defs": embedded_claim_defs(),
        "required": [
            "report_id",
            "candidate_ref",
            "candidate_status",
            "status_evidence_anchors",
            "claim_records",
            "split_proposals",
            "duplicate_candidate_refs",
            "manual_review_reason",
            "reviewer_note",
        ],
        "properties": {
            "report_id": {"type": "string", "minLength": 1},
            "candidate_ref": {"type": "string", "minLength": 1},
            "candidate_status": {"type": "string", "enum": statuses},
            "status_evidence_anchors": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/evidence_anchor"},
            },
            "claim_records": {
                "type": "array",
                "maxItems": 1,
                "items": {"$ref": "#/$defs/claim_record"},
            },
            "split_proposals": {
                "type": "array",
                "items": {"$ref": "#/$defs/candidate_nomination"},
            },
            "duplicate_candidate_refs": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "manual_review_reason": {"type": "string"},
            "reviewer_note": {"type": "string"},
        },
        "allOf": [
            {
                "if": {
                    "properties": {
                        "candidate_status": {"const": "valid_single_claim"}
                    }
                },
                "then": {
                    "properties": {
                        "claim_records": {"minItems": 1, "maxItems": 1},
                        "split_proposals": {"maxItems": 0},
                        "duplicate_candidate_refs": {"maxItems": 0},
                    }
                },
            },
            {
                "if": {
                    "properties": {"candidate_status": {"const": "split_required"}}
                },
                "then": {
                    "properties": {
                        "claim_records": {"maxItems": 0},
                        "split_proposals": {"minItems": 2},
                        "duplicate_candidate_refs": {"maxItems": 0},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "candidate_status": {"const": "duplicate_or_overlapping"}
                    }
                },
                "then": {
                    "properties": {
                        "claim_records": {"maxItems": 0},
                        "split_proposals": {"maxItems": 0},
                        "duplicate_candidate_refs": {"minItems": 1},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "candidate_status": {
                            "enum": [
                                "background_or_cited_work",
                                "no_current_report_empirical_result",
                                "context_only",
                                "insufficient_source",
                            ]
                        }
                    }
                },
                "then": {
                    "properties": {
                        "claim_records": {"maxItems": 0},
                        "split_proposals": {"maxItems": 0},
                        "duplicate_candidate_refs": {"maxItems": 0},
                    }
                },
            },
        ],
    }
    return schema


def candidate_disposition_schema() -> dict[str, Any]:
    accepted = ["accepted_claim", "split_into_claims", "merged_into_claim"]
    excluded = [
        "excluded_background",
        "excluded_no_current_result",
        "excluded_context_only",
        "manual_review_insufficient_source",
    ]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "candidate_ref",
            "disposition",
            "final_claim_ids",
            "evidence_anchors",
            "reason",
        ],
        "properties": {
            "candidate_ref": {"type": "string", "minLength": 1},
            "disposition": {"type": "string", "enum": accepted + excluded},
            "final_claim_ids": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "evidence_anchors": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/evidence_anchor"},
            },
            "reason": {"type": "string", "minLength": 1},
        },
        "allOf": [
            {
                "if": {"properties": {"disposition": {"enum": accepted}}},
                "then": {"properties": {"final_claim_ids": {"minItems": 1}}},
            },
            {
                "if": {"properties": {"disposition": {"enum": excluded}}},
                "then": {"properties": {"final_claim_ids": {"maxItems": 0}}},
            },
        ],
    }


def adjudicator_schema() -> dict[str, Any]:
    defs = embedded_claim_defs()
    defs["candidate_disposition"] = candidate_disposition_schema()
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"Final claim adjudicator output v{SUITE_VERSION}",
        "type": "object",
        "additionalProperties": False,
        "$defs": defs,
        "required": [
            "report_id",
            "candidate_inventory_sha256",
            "candidate_dispositions",
            "final_claim_records",
            "manual_review_items",
            "adjudication_note",
        ],
        "properties": {
            "report_id": {"type": "string", "minLength": 1},
            "candidate_inventory_sha256": {
                "type": "string",
                "pattern": "^[a-f0-9]{64}$",
            },
            "candidate_dispositions": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/candidate_disposition"},
            },
            "final_claim_records": {
                "type": "array",
                "items": {"$ref": "#/$defs/claim_record"},
            },
            "manual_review_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["candidate_refs", "reason"],
                    "properties": {
                        "candidate_refs": {
                            "type": "array",
                            "minItems": 1,
                            "uniqueItems": True,
                            "items": {"type": "string", "minLength": 1},
                        },
                        "reason": {"type": "string", "minLength": 1},
                    },
                },
            },
            "adjudication_note": {"type": "string"},
        },
    }


def generated_schemas() -> dict[Path, dict[str, Any]]:
    schema_dir = PACKAGE / "schemas"
    return {
        schema_dir / "open_claim_discovery.schema.json": discovery_schema(
            "open_claim_discovery"
        ),
        schema_dir / "dense_claim_coverage.schema.json": discovery_schema(
            "dense_claim_coverage"
        ),
        schema_dir / "fixed_candidate_classifier.schema.json": (
            fixed_classifier_schema()
        ),
        schema_dir / "final_claim_adjudicator.schema.json": adjudicator_schema(),
    }


def prompt_metadata(path: Path) -> dict[str, Any]:
    text = path.read_text()
    prompt_id = re.search(r"^PROMPT_ID:\s*(.+)$", text, re.MULTILINE)
    version = re.search(r"^PROMPT_VERSION:\s*(.+)$", text, re.MULTILINE)
    if not prompt_id or not version:
        raise ValueError(f"Missing prompt metadata in {path}")
    return {
        "prompt_id": prompt_id.group(1).strip(),
        "prompt_version": version.group(1).strip(),
        "path": str(path.relative_to(REPO_ROOT)),
        "sha256": sha256(path),
        "placeholders": sorted(set(re.findall(r"{{([A-Z0-9_]+)}}", text))),
    }


def build_checkpoint_inventory() -> dict[str, Any]:
    with PILOT_REPORTS.open(newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    reports = []
    for index, row in enumerate(source_rows, start=1):
        document = REPO_ROOT / row["docling_markdown_path"]
        reports.append(
            {
                "checkpoint_order": index,
                "report_id": f"doi:{row['doi']}",
                "doi": row["doi"],
                "title": row["title"],
                "design_diversity_role": row["design_diversity_role"],
                "canonical_docling_path": row["docling_markdown_path"],
                "canonical_docling_sha256": sha256(document),
                "canonical_docling_bytes": document.stat().st_size,
            }
        )
    return {
        "checkpoint_id": f"causal_extraction_v{SUITE_VERSION}_checkpoint_15",
        "purpose": "instrument_development_and_technical_stability_checkpoint",
        "report_count": len(reports),
        "selected_before_suite_terra_outputs": True,
        "prior_human_codebook_annotations_exist": True,
        "independent_accuracy_set": False,
        "reuse_limit": (
            "Results may guide a new prompt-suite version but cannot be used as "
            "an unbiased accuracy estimate. A revised version requires a "
            "disjoint checkpoint set."
        ),
        "selection_source": {
            "path": str(PILOT_REPORTS.relative_to(REPO_ROOT)),
            "sha256": sha256(PILOT_REPORTS),
        },
        "eligibility_ledger": {
            "path": str(ELIGIBILITY_LEDGER.relative_to(REPO_ROOT)),
            "sha256": sha256(ELIGIBILITY_LEDGER),
            "eligible_report_count": 101,
        },
        "reports": reports,
    }


def artifact_entries() -> list[dict[str, Any]]:
    excluded = {MANIFEST.resolve(), FREEZE.resolve()}
    entries = []
    for path in sorted(PACKAGE.rglob("*")):
        if not path.is_file() or path.resolve() in excluded:
            continue
        entries.append(
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    return entries


def git_parent() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()


def build_manifest() -> dict[str, Any]:
    runtime = json.loads((PACKAGE / "runtime.json").read_text())
    return {
        "suite_id": runtime["suite_id"],
        "suite_version": runtime["suite_version"],
        "status": runtime["status"],
        "manifest_date": "2026-08-29",
        "codebook": {
            "version": "0.2.0",
            "path": str(CODEBOOK.relative_to(REPO_ROOT)),
            "sha256": sha256(CODEBOOK),
        },
        "claim_record_schema": {
            "path": str(CLAIM_SCHEMA.relative_to(REPO_ROOT)),
            "sha256": sha256(CLAIM_SCHEMA),
        },
        "prompts": [
            prompt_metadata(PACKAGE / relative)
            for relative in sorted(PROMPT_PLACEHOLDERS)
        ],
        "artifacts": artifact_entries(),
    }


def build_freeze(manifest_hash: str) -> dict[str, Any]:
    return {
        "suite_id": "causal_multiomics_aging.causal_extraction",
        "suite_version": SUITE_VERSION,
        "freeze_date": "2026-08-29",
        "status": "frozen_before_first_terra_checkpoint",
        "parent_git_revision": git_parent(),
        "freeze_revision": "the Git commit containing this file",
        "artifact_manifest_path": str(MANIFEST.relative_to(REPO_ROOT)),
        "artifact_manifest_sha256": manifest_hash,
        "model_calls_before_freeze": 0,
        "first_checkpoint_report_count": 15,
        "approval_note": (
            "Instrument-development release candidate approved for the first "
            "preselected Terra checkpoint. Any prompt or schema change creates "
            "a new version and requires a disjoint checkpoint set."
        ),
    }


def validate_package() -> list[str]:
    errors: list[str] = []
    for path, schema in generated_schemas().items():
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # pragma: no cover - exact library text varies
            errors.append(f"Invalid generated schema {path}: {exc}")
            continue
        if not path.exists():
            errors.append(f"Missing generated schema: {path}")
        elif path.read_text() != json_text(schema):
            errors.append(f"Generated schema is stale: {path}")

    for relative, expected in PROMPT_PLACEHOLDERS.items():
        path = PACKAGE / relative
        if not path.exists():
            errors.append(f"Missing prompt: {path}")
            continue
        actual = set(re.findall(r"{{([A-Z0-9_]+)}}", path.read_text()))
        if actual != expected:
            errors.append(
                f"Placeholder mismatch for {relative}: expected {sorted(expected)}, "
                f"found {sorted(actual)}"
            )

    expected_checkpoint = build_checkpoint_inventory()
    if not CHECKPOINT.exists():
        errors.append(f"Missing checkpoint inventory: {CHECKPOINT}")
    elif CHECKPOINT.read_text() != json_text(expected_checkpoint):
        errors.append("Checkpoint inventory is stale")
    elif len(expected_checkpoint["reports"]) != 15:
        errors.append("Checkpoint inventory must contain 15 reports")

    try:
        runtime = json.loads((PACKAGE / "runtime.json").read_text())
        coverage = json.loads((PACKAGE / "coverage_contract.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid runtime or coverage config: {exc}")
    else:
        if runtime.get("model") != "gpt-5.6-terra":
            errors.append("Runtime model must be gpt-5.6-terra")
        if runtime.get("reasoning_effort") != "medium":
            errors.append("Runtime reasoning effort must be medium")
        classifier = runtime.get("stages", {}).get("fixed_candidate_classifier", {})
        if classifier.get("repeats") != 5:
            errors.append("Fixed candidate classification must use five repeats")
        if runtime.get("generation", {}).get("technical_retry_limit") != 1:
            errors.append("Technical retry limit must equal one")
        assertions = coverage.get("pre_classification_assertions", {})
        for key in (
            "canonical_section_coverage_ratio",
            "open_core_coverage_ratio",
            "dense_core_coverage_ratio",
        ):
            if assertions.get(key) != 1.0:
                errors.append(f"Coverage assertion {key} must equal 1.0")

    expected_manifest = build_manifest()
    if not MANIFEST.exists():
        errors.append(f"Missing manifest: {MANIFEST}")
    elif MANIFEST.read_text() != json_text(expected_manifest):
        errors.append("Artifact manifest is stale")

    if not FREEZE.exists():
        errors.append(f"Missing freeze record: {FREEZE}")
    elif MANIFEST.exists():
        try:
            freeze = json.loads(FREEZE.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid freeze record: {exc}")
        else:
            if freeze.get("artifact_manifest_sha256") != sha256(MANIFEST):
                errors.append("Freeze record does not match artifact manifest hash")
            if freeze.get("model_calls_before_freeze") != 0:
                errors.append("Pre-run freeze must record zero prior model calls")
    return errors


def write_package() -> None:
    (PACKAGE / "schemas").mkdir(parents=True, exist_ok=True)
    for path, schema in generated_schemas().items():
        path.write_text(json_text(schema))
    CHECKPOINT.write_text(json_text(build_checkpoint_inventory()))
    MANIFEST.write_text(json_text(build_manifest()))
    FREEZE.write_text(json_text(build_freeze(sha256(MANIFEST))))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--suite-version", default="0.1.0-rc1")
    return parser.parse_args()


def configure_suite(version: str) -> None:
    global SUITE_VERSION, PACKAGE, MANIFEST, FREEZE, CHECKPOINT
    SUITE_VERSION = version.removeprefix("v")
    PACKAGE = REPO_ROOT / f"protocol/causal_extraction/prompt_suite/v{SUITE_VERSION}"
    MANIFEST = PACKAGE / "artifact_manifest.json"
    FREEZE = PACKAGE / "freeze.json"
    CHECKPOINT = PACKAGE / "checkpoint_inventory.json"


def main() -> int:
    args = parse_args()
    configure_suite(args.suite_version)
    if args.write:
        write_package()
    errors = validate_package()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Causal-extraction methodology package is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
