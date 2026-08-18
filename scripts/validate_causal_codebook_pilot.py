#!/usr/bin/env python3
"""Validate the claim-level causal codebook development pilot."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PILOT_DIR = (
    REPO_ROOT / "analysis/causal_extraction/codebook_pilot_v0.1.0"
)
DEFAULT_SCHEMA = (
    REPO_ROOT / "protocol/causal_extraction/v0.1.0/claim_record.schema.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-dir", type=Path, default=DEFAULT_PILOT_DIR)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    return parser.parse_args()


def load_claims(path: Path) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            claims.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
    return claims


def expected_level(claim: dict[str, Any]) -> int | str:
    assessment = claim["reviewer_identification_assessment"]
    formal_basis = claim["formal_basis_present"]
    qualifying_validation = any(
        item["qualifies_for_level4"] == "yes" for item in claim["validations"]
    )

    if assessment == "no_identification":
        return 1
    if assessment == "formal_hypothesis_only":
        return 2
    if assessment == "effect_claim_not_assessable":
        return 2 if formal_basis == "yes" else 1
    if assessment == "effect_assessable":
        return 4 if qualifying_validation else 3
    return "manual_review"


def anchor_references(claim: dict[str, Any]) -> set[str]:
    references: set[str] = set()
    for judgment in claim["assumption_judgments"]:
        references.update(judgment["evidence_anchor_ids"])
    for diagnostic in claim["diagnostics"]:
        references.update(diagnostic["evidence_anchor_ids"])
    for validation in claim["validations"]:
        references.update(validation["evidence_anchor_ids"])
    return references


def main() -> int:
    args = parse_args()
    pilot_dir = args.pilot_dir.resolve()
    schema_path = args.schema.resolve()
    claims = load_claims(pilot_dir / "claims.jsonl")
    schema = json.loads(schema_path.read_text())
    validator = Draft202012Validator(schema)
    errors: list[str] = []

    report_rows = list(csv.DictReader((pilot_dir / "reports_15.csv").open()))
    report_dois = {row["doi"].lower() for row in report_rows}
    claim_dois = {claim["doi"].lower() for claim in claims}
    if len(report_rows) != 15 or len(report_dois) != 15:
        errors.append(
            f"reports_15.csv must contain 15 unique reports; found "
            f"{len(report_rows)} rows and {len(report_dois)} unique DOIs"
        )
    if claim_dois != report_dois:
        errors.append(
            f"claim/report DOI mismatch: claims-only={sorted(claim_dois-report_dois)}, "
            f"reports-only={sorted(report_dois-claim_dois)}"
        )

    claim_ids: set[str] = set()
    document_cache: dict[Path, str] = {}
    for claim in claims:
        claim_id = claim.get("claim_id", "<missing>")
        for error in validator.iter_errors(claim):
            location = ".".join(str(part) for part in error.absolute_path)
            errors.append(f"{claim_id}: schema {location}: {error.message}")

        if claim_id in claim_ids:
            errors.append(f"duplicate claim_id: {claim_id}")
        claim_ids.add(claim_id)

        derived = expected_level(claim)
        if claim.get("candidate_level") != derived:
            errors.append(
                f"{claim_id}: candidate_level={claim.get('candidate_level')} but "
                f"deterministic mapping gives {derived}"
            )

        anchors = claim.get("evidence_anchors", [])
        anchor_ids = [anchor.get("anchor_id") for anchor in anchors]
        if len(anchor_ids) != len(set(anchor_ids)):
            errors.append(f"{claim_id}: duplicate evidence anchor IDs")
        missing_refs = anchor_references(claim) - set(anchor_ids)
        if missing_refs:
            errors.append(
                f"{claim_id}: unknown evidence anchor references {sorted(missing_refs)}"
            )

        for anchor in anchors:
            relative_path = Path(anchor["document_path"])
            document_path = (REPO_ROOT / relative_path).resolve()
            try:
                document_path.relative_to(REPO_ROOT)
            except ValueError:
                errors.append(
                    f"{claim_id}/{anchor['anchor_id']}: document is outside repository"
                )
                continue
            if not document_path.is_file():
                errors.append(
                    f"{claim_id}/{anchor['anchor_id']}: missing {relative_path}"
                )
                continue
            text = document_cache.setdefault(document_path, document_path.read_text())
            if anchor["quote"] not in text:
                errors.append(
                    f"{claim_id}/{anchor['anchor_id']}: quote is not an exact substring"
                )

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    level_counts: dict[str, int] = {}
    for claim in claims:
        key = str(claim["candidate_level"])
        level_counts[key] = level_counts.get(key, 0) + 1
    print("PASS")
    print(f"reports={len(report_dois)} claims={len(claims)}")
    print(f"levels={json.dumps(level_counts, sort_keys=True)}")
    print("schema_errors=0 grounding_errors=0 mapping_errors=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
