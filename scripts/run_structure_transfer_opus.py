#!/usr/bin/env python3
"""Retry the frozen Opus inventory procedure on a disjoint six-report subset."""

from __future__ import annotations

import concurrent.futures
import json
from datetime import datetime, timezone
from pathlib import Path

from causal_multiomics_aging_review.causal_analysis_inventory import (
    normalize_reference_inventory,
    validate_reference_inventory_semantics,
)
from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    read_json,
    sha256_file,
    sha256_text,
    validate_schema,
    write_json,
    write_text,
)
from causal_multiomics_aging_review.llm import ProviderError
from causal_multiomics_aging_review.runtime_schema import inline_local_json_schema
from run_independent_causal_inventory import complete_claude_json


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "protocol/causal_extraction/validation/v0.3.1-independent-15-v1.0.0"
OLD = ROOT / "data/causal_extraction/v0.3.1_independent_validation/independent_inventories"
INPUTS = ROOT / "data/causal_extraction/v0.3.1_independent_validation/inputs"
OUT = ROOT / "data/article_design/structure_transfer_six_v1.0.0/opus"
SELECTED = (
    "doi_9bd21f903f00005b",
    "doi_fc55eaf97b778a04",
    "doi_6b523b6e6aa043ca",
    "doi_2b6595596a732fb9",
    "doi_ef6b9bff3b03d476",
    "doi_ec4e8c88344d7790",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_one(document_id: str, schema: dict, source_schema: dict, config: dict) -> dict:
    source_dir = OLD / "claude_opus_4_8/calls" / document_id
    output_dir = OUT / "calls" / document_id
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = source_dir / "rendered_prompt.txt"
    prompt = prompt_path.read_text()
    atom_index = read_json(INPUTS / document_id / "evidence_atom_index.json")
    metadata = read_json(INPUTS / document_id / "record_metadata.json")
    write_text(output_dir / "rendered_prompt.txt", prompt)
    write_json(
        output_dir / "request.json",
        {
            "procedure": "exact_frozen_prompt_retry_after_historical_429",
            "reviewer_id": "claude_opus_4_8",
            "document_id": document_id,
            "report_id": metadata["record_id"],
            "doi": metadata["doi"],
            "model": config["model"],
            "effort": config["effort"],
            "prompt_source": str(prompt_path.relative_to(ROOT)),
            "prompt_sha256": sha256_text(prompt),
            "source_atom_count": len(atom_index["atoms"]),
            "source_atom_index_sha256": sha256_text(canonical_json(atom_index)),
            "input_size_modifications": False,
        },
    )
    failures = []
    for attempt in (1, 2):
        started = now()
        try:
            parsed, raw = complete_claude_json(prompt=prompt, schema=schema, config=config)
            write_json(output_dir / f"raw_response_attempt_{attempt}.json", raw)
            write_json(output_dir / f"parsed_attempt_{attempt}.json", parsed)
            schema_errors = validate_schema(parsed, source_schema)
            semantic_errors = (
                validate_reference_inventory_semantics(
                    parsed,
                    expected_reviewer_id="claude_opus_4_8",
                    expected_report_id=metadata["record_id"],
                    atom_index=atom_index,
                )
                if not schema_errors
                else []
            )
            errors = schema_errors + semantic_errors
            if errors:
                failure = {
                    "attempt": attempt,
                    "kind": "validation_error",
                    "errors": errors,
                    "started_at": started,
                    "finished_at": now(),
                }
                failures.append(failure)
                write_json(output_dir / f"failure_attempt_{attempt}.json", failure)
                continue
            normalized = normalize_reference_inventory(parsed, atom_index)
            write_json(output_dir / "normalized.json", normalized)
            validation = {
                "valid": True,
                "attempt": attempt,
                "prompt_sha256": sha256_text(prompt),
                "normalized_sha256": sha256_text(canonical_json(normalized)),
                "started_at": started,
                "finished_at": now(),
            }
            write_json(output_dir / "validation.json", validation)
            return {
                "document_id": document_id,
                "doi": metadata["doi"],
                "status": "valid",
                "attempts": attempt,
                "qualifying_analysis_count": len(normalized["qualifying_analyses"]),
                "boundary_candidate_count": len(normalized["excluded_boundary_candidates"]),
            }
        except ProviderError as error:
            failure = {
                "attempt": attempt,
                "kind": "provider_error",
                "message": str(error),
                "raw_response": error.raw_response,
                "started_at": started,
                "finished_at": now(),
            }
            failures.append(failure)
            write_json(output_dir / f"failure_attempt_{attempt}.json", failure)
    write_json(output_dir / "validation.json", {"valid": False, "failures": failures})
    return {"document_id": document_id, "doi": metadata["doi"], "status": "failed", "attempts": 2}


def main() -> None:
    if OUT.exists():
        raise ValueError(f"Refuse to overwrite nonempty transfer output: {OUT}")
    runtime = read_json(SUITE / "runtime.json")
    config = runtime["reviewers"]["claude_opus_4_8"]
    source_schema = read_json(SUITE / runtime["schema"])
    schema = inline_local_json_schema(source_schema)
    OUT.mkdir(parents=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda document_id: run_one(document_id, schema, source_schema, config),
                SELECTED,
            )
        )
    write_json(
        OUT / "completion.json",
        {
            "status": "complete" if all(row["status"] == "valid" for row in results) else "complete_with_failures",
            "selected_reports": len(SELECTED),
            "valid_reports": sum(row["status"] == "valid" for row in results),
            "results": results,
            "inherited_schema": str((SUITE / runtime["schema"]).relative_to(ROOT)),
            "inherited_schema_sha256": sha256_file(SUITE / runtime["schema"]),
            "finished_at": now(),
        },
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    raise SystemExit(0 if all(row["status"] == "valid" for row in results) else 1)


if __name__ == "__main__":
    main()
