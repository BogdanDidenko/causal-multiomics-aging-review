from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import tiktoken
from jsonschema import Draft202012Validator


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode())


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _json_type(value: Any) -> str | None:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if value is None:
        return "null"
    return None


def codex_runtime_schema(value: Any) -> Any:
    """Compile the source schema to the strict subset accepted by Codex CLI."""
    if isinstance(value, dict):
        compiled = {
            key: codex_runtime_schema(item)
            for key, item in value.items()
            if key not in {"uniqueItems", "allOf", "if", "then", "else"}
        }
        if "const" in compiled and "type" not in compiled:
            inferred = _json_type(compiled["const"])
            if inferred:
                compiled["type"] = inferred
        if "enum" in compiled and "type" not in compiled:
            inferred_types = {_json_type(item) for item in compiled["enum"]}
            inferred_types.discard(None)
            if len(inferred_types) == 1:
                compiled["type"] = inferred_types.pop()
        return compiled
    if isinstance(value, list):
        return [codex_runtime_schema(item) for item in value]
    return value


def render_prompt(template: str, substitutions: dict[str, str]) -> str:
    rendered = template
    for name, value in substitutions.items():
        rendered = rendered.replace("{{" + name + "}}", value)
    unresolved = sorted(set(re.findall(r"{{([A-Z0-9_]+)}}", rendered)))
    if unresolved:
        raise ValueError(f"Unresolved prompt placeholders: {unresolved}")
    return rendered


def _tokenizer() -> tiktoken.Encoding:
    return tiktoken.get_encoding("o200k_base")


def token_count(text: str) -> int:
    return len(_tokenizer().encode(text))


def _max_character_end(text: str, start: int, max_tokens: int) -> int:
    low = start + 1
    high = len(text)
    best = low
    while low <= high:
        middle = (low + high) // 2
        if token_count(text[start:middle]) <= max_tokens:
            best = middle
            low = middle + 1
        else:
            high = middle - 1
    return best


def split_text_at_boundaries(text: str, max_tokens: int) -> list[str]:
    if not text:
        return [""]
    if token_count(text) <= max_tokens:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        maximum = _max_character_end(text, start, max_tokens)
        if maximum >= len(text):
            parts.append(text[start:])
            break
        minimum_preferred = start + max(1, (maximum - start) // 2)
        boundary_candidates: list[int] = []
        for pattern in (r"\n\n+", r"(?<=[.!?])\s+", r"\n", r"\s+"):
            positions = [
                match.end()
                for match in re.finditer(pattern, text[start:maximum])
                if start + match.end() >= minimum_preferred
            ]
            if positions:
                boundary_candidates.append(start + positions[-1])
                break
        end = boundary_candidates[0] if boundary_candidates else maximum
        if end <= start:
            end = maximum
        parts.append(text[start:end])
        start = end
    if "".join(parts) != text:
        raise AssertionError("Text split changed canonical content")
    if any(token_count(part) > max_tokens for part in parts):
        raise AssertionError("Token-bounded split exceeded limit")
    return parts


def canonical_sections(record: dict[str, Any]) -> list[dict[str, Any]]:
    sections = []
    for source_order, section in enumerate(record["sections"]):
        sections.append(
            {
                "section_id": str(section["section_id"]),
                "heading": str(section.get("heading", "")),
                "page_numbers": list(section.get("page_numbers", [])),
                "source_order": source_order,
                "text": str(section.get("text", "")),
            }
        )
    return sections


def split_sections_for_tokens(
    sections: list[dict[str, Any]], max_tokens: int
) -> list[dict[str, Any]]:
    derived = []
    for section in sections:
        parts = split_text_at_boundaries(section["text"], max_tokens)
        for index, text in enumerate(parts, start=1):
            item = copy.deepcopy(section)
            item["canonical_section_id"] = section["section_id"]
            item["section_id"] = (
                section["section_id"]
                if len(parts) == 1
                else f"{section['section_id']}::part-{index:03d}"
            )
            item["part_index"] = index
            item["part_count"] = len(parts)
            item["text"] = text
            item["token_count"] = token_count(text)
            derived.append(item)
    return derived


def _json_section_size(section: dict[str, Any]) -> int:
    return len(json.dumps(section, ensure_ascii=False))


def build_open_windows(
    sections: list[dict[str, Any]],
    *,
    max_core_characters: int,
    context_characters: int,
) -> list[dict[str, Any]]:
    core_sections = split_sections_for_tokens(sections, max_tokens=12000)
    windows: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_size = 0
    for section in core_sections:
        size = _json_section_size(section)
        if current and current_size + size > max_core_characters:
            windows.append(current)
            current = []
            current_size = 0
        current.append(section)
        current_size += size
    if current:
        windows.append(current)

    positions = {section["section_id"]: index for index, section in enumerate(core_sections)}
    output = []
    for index, core in enumerate(windows, start=1):
        first = positions[core[0]["section_id"]]
        last = positions[core[-1]["section_id"]]
        before: list[dict[str, Any]] = []
        size = 0
        cursor = first - 1
        while cursor >= 0:
            candidate = core_sections[cursor]
            candidate_size = _json_section_size(candidate)
            if size + candidate_size > context_characters:
                break
            before.insert(0, candidate)
            size += candidate_size
            cursor -= 1
        after: list[dict[str, Any]] = []
        size = 0
        cursor = last + 1
        while cursor < len(core_sections):
            candidate = core_sections[cursor]
            candidate_size = _json_section_size(candidate)
            if size + candidate_size > context_characters:
                break
            after.append(candidate)
            size += candidate_size
            cursor += 1
        output.append(
            {
                "work_unit_id": f"open-window-{index:03d}",
                "core_sections": core,
                "context_sections": before + after,
            }
        )
    return output


def build_dense_batches(
    sections: list[dict[str, Any]],
    *,
    max_chunk_tokens: int,
    max_batch_tokens: int,
) -> list[dict[str, Any]]:
    chunks = split_sections_for_tokens(sections, max_chunk_tokens)
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_tokens = 0
    for chunk in chunks:
        if current and current_tokens + chunk["token_count"] > max_batch_tokens:
            batches.append(current)
            current = []
            current_tokens = 0
        current.append(chunk)
        current_tokens += chunk["token_count"]
    if current:
        batches.append(current)
    return [
        {
            "work_unit_id": f"dense-batch-{index:03d}",
            "core_sections": batch,
            "context_sections": [],
        }
        for index, batch in enumerate(batches, start=1)
    ]


def build_coverage_ledger(
    sections: list[dict[str, Any]],
    open_windows: list[dict[str, Any]],
    dense_batches: list[dict[str, Any]],
) -> dict[str, Any]:
    canonical_ids = [section["section_id"] for section in sections]

    def counts(units: list[dict[str, Any]]) -> dict[str, int]:
        result: dict[str, int] = defaultdict(int)
        for unit in units:
            seen = set()
            for section in unit["core_sections"]:
                seen.add(section.get("canonical_section_id", section["section_id"]))
            for section_id in seen:
                result[section_id] += 1
        return dict(result)

    open_counts = counts(open_windows)
    dense_counts = counts(dense_batches)
    missing_open = sorted(set(canonical_ids) - set(open_counts))
    missing_dense = sorted(set(canonical_ids) - set(dense_counts))
    ledger = {
        "canonical_section_count": len(canonical_ids),
        "canonical_nonempty_section_count": sum(bool(section["text"]) for section in sections),
        "canonical_characters": sum(len(section["text"]) for section in sections),
        "open_work_units": len(open_windows),
        "dense_work_units": len(dense_batches),
        "open_canonical_core_occurrences": open_counts,
        "dense_canonical_core_occurrences": dense_counts,
        "missing_open_sections": missing_open,
        "missing_dense_sections": missing_dense,
        "truncated_section_count": 0,
        "omitted_nonempty_section_count": len(
            [
                section
                for section in sections
                if section["text"]
                and (
                    section["section_id"] in missing_open
                    or section["section_id"] in missing_dense
                )
            ]
        ),
    }
    ledger["coverage_complete"] = (
        not missing_open
        and not missing_dense
        and ledger["truncated_section_count"] == 0
        and ledger["omitted_nonempty_section_count"] == 0
    )
    return ledger


def validate_schema(instance: Any, schema: dict[str, Any]) -> list[str]:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: "
        f"{error.message}"
        for error in errors
    ]


def section_text_index(sections: Iterable[dict[str, Any]]) -> dict[str, str]:
    return {str(section["section_id"]): str(section["text"]) for section in sections}


def validate_discovery_grounding(
    response: dict[str, Any], sections: Iterable[dict[str, Any]]
) -> list[dict[str, str]]:
    index = section_text_index(sections)
    failures = []
    anchors = []
    for candidate in response.get("candidates", []):
        anchors.extend(candidate.get("evidence_anchors", []))
    anchors.extend(response.get("evidence_atoms", []))
    for anchor in anchors:
        section_id = str(anchor.get("section_id", ""))
        quote = str(anchor.get("quote", ""))
        if section_id not in index:
            failures.append(
                {"section_id": section_id, "quote": quote, "reason": "unknown_section_id"}
            )
        elif quote not in index[section_id]:
            failures.append(
                {"section_id": section_id, "quote": quote, "reason": "quote_not_substring"}
            )
    return failures


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(candidate)
    value.pop("candidate_local_id", None)
    for key, item in list(value.items()):
        if isinstance(item, str):
            value[key] = _normalize_text(item)
    anchors = value.get("evidence_anchors", [])
    value["evidence_anchors"] = sorted(
        anchors,
        key=lambda anchor: (
            anchor.get("section_id", ""),
            anchor.get("quote", ""),
            anchor.get("support_role", ""),
        ),
    )
    return value


def freeze_candidates(
    report: dict[str, Any],
    discovery_outputs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nominations: list[dict[str, Any]] = []
    evidence_atoms: list[dict[str, Any]] = []
    for output in discovery_outputs:
        route = output["stage"]
        work_unit = output["work_unit_id"]
        for candidate in output.get("candidates", []):
            nominations.append(
                {
                    "route": route,
                    "work_unit_id": work_unit,
                    "candidate_local_id": candidate["candidate_local_id"],
                    "candidate": candidate,
                    "normalized": normalize_candidate(candidate),
                }
            )
        for atom in output.get("evidence_atoms", []):
            evidence_atoms.append(
                {"route": route, "work_unit_id": work_unit, **atom}
            )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for nomination in nominations:
        grouped[sha256_text(canonical_json(nomination["normalized"]))].append(nomination)

    section_order = {
        section["section_id"]: index
        for index, section in enumerate(canonical_sections(report))
    }

    def earliest(group: list[dict[str, Any]]) -> tuple[int, str]:
        ids = [
            anchor["section_id"]
            for item in group
            for anchor in item["candidate"].get("evidence_anchors", [])
        ]
        return min((section_order.get(section_id, 10**9), section_id) for section_id in ids)

    ordered_groups = sorted(grouped.values(), key=earliest)
    frozen = []
    for index, group in enumerate(ordered_groups, start=1):
        frozen.append(
            {
                "candidate_ref": f"{report['document_id']}::candidate-{index:03d}",
                "report_id": report["record_id"],
                "doi": report["doi"],
                "title": report["title"],
                "candidate": group[0]["normalized"],
                "discovery_routes": sorted({item["route"] for item in group}),
                "source_nominations": [
                    {
                        "route": item["route"],
                        "work_unit_id": item["work_unit_id"],
                        "candidate_local_id": item["candidate_local_id"],
                    }
                    for item in group
                ],
                "exact_duplicate_nomination_count": len(group),
            }
        )
    return frozen, evidence_atoms


def select_stability_candidates(
    candidates: list[dict[str, Any]], *, limit: int, seed: str
) -> list[dict[str, Any]]:
    """Select a reproducible route-balanced subset without reading claim content."""
    if limit <= 0 or len(candidates) <= limit:
        return list(candidates)

    def rank(candidate: dict[str, Any]) -> tuple[str, str]:
        candidate_ref = str(candidate["candidate_ref"])
        return sha256_text(f"{seed}|{candidate_ref}"), candidate_ref

    selected: list[dict[str, Any]] = []
    selected_refs: set[str] = set()
    for route in ("open_claim_discovery", "dense_claim_coverage"):
        route_candidates = [
            candidate
            for candidate in candidates
            if route in candidate.get("discovery_routes", [])
        ]
        if route_candidates and len(selected) < limit:
            chosen = min(route_candidates, key=rank)
            selected.append(chosen)
            selected_refs.add(chosen["candidate_ref"])

    remaining = sorted(
        (
            candidate
            for candidate in candidates
            if candidate["candidate_ref"] not in selected_refs
        ),
        key=rank,
    )
    selected.extend(remaining[: limit - len(selected)])
    return sorted(selected, key=lambda candidate: candidate["candidate_ref"])


def build_evidence_packets(
    report: dict[str, Any],
    candidates: list[dict[str, Any]],
    evidence_atoms: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sections = canonical_sections(report)
    section_by_id = {section["section_id"]: section for section in sections}
    order = {section["section_id"]: index for index, section in enumerate(sections)}
    unique_atoms: dict[tuple[str, str, str], dict[str, Any]] = {}
    for atom in evidence_atoms:
        key = (atom["evidence_type"], atom["section_id"], atom["quote"])
        unique_atoms.setdefault(key, atom)
    atoms = list(unique_atoms.values())
    atom_section_ids = {atom["section_id"] for atom in atoms}
    packets = []
    summaries = [
        {
            "candidate_ref": candidate["candidate_ref"],
            "normalized_claim": candidate["candidate"].get("normalized_claim", ""),
            "exposure_operation": candidate["candidate"].get("exposure_operation", ""),
            "outcome": candidate["candidate"].get("outcome", ""),
        }
        for candidate in candidates
    ]
    for candidate in candidates:
        ids = {
            anchor["section_id"]
            for anchor in candidate["candidate"].get("evidence_anchors", [])
        } | atom_section_ids
        expanded = set(ids)
        for section_id in list(ids):
            position = order.get(section_id)
            if position is None:
                continue
            if position > 0:
                expanded.add(sections[position - 1]["section_id"])
            if position + 1 < len(sections):
                expanded.add(sections[position + 1]["section_id"])
        selected_sections = [
            section_by_id[section_id]
            for section_id in sorted(expanded, key=lambda value: order.get(value, 10**9))
            if section_id in section_by_id
        ]
        packets.append(
            {
                "report_id": report["record_id"],
                "doi": report["doi"],
                "title": report["title"],
                "candidate_ref": candidate["candidate_ref"],
                "candidate": candidate,
                "other_frozen_candidates": [
                    summary
                    for summary in summaries
                    if summary["candidate_ref"] != candidate["candidate_ref"]
                ],
                "evidence_atoms": atoms,
                "canonical_sections": selected_sections,
            }
        )
    return packets


def grounding_anchors_from_claim(record: dict[str, Any]) -> list[dict[str, Any]]:
    anchors = []
    anchors.extend(record.get("evidence_anchors", []))
    field_anchors = record.get("field_anchors", {})
    if isinstance(field_anchors, dict):
        for value in field_anchors.values():
            if isinstance(value, list):
                anchors.extend(value)
    return anchors


def validate_classifier_grounding(
    response: dict[str, Any], packet: dict[str, Any]
) -> list[dict[str, str]]:
    index = section_text_index(packet["canonical_sections"])
    anchors = list(response.get("status_evidence_anchors", []))
    for record in response.get("claim_records", []):
        anchors.extend(grounding_anchors_from_claim(record))
    for proposal in response.get("split_proposals", []):
        anchors.extend(proposal.get("evidence_anchors", []))
    failures = []
    for anchor in anchors:
        section_id = str(anchor.get("section_id", ""))
        quote = str(anchor.get("quote", ""))
        if section_id not in index:
            failures.append(
                {"section_id": section_id, "quote": quote, "reason": "unknown_section_id"}
            )
        elif quote not in index[section_id]:
            failures.append(
                {"section_id": section_id, "quote": quote, "reason": "quote_not_substring"}
            )
    return failures


SET_ARRAYS = {
    "supporting_designs_or_methods",
    "validations_proposed_by_report",
    "duplicate_candidate_refs",
}
ADMIN_FIELDS = {"report_id", "doi", "claim_id", "reviewer_note"}
PROVENANCE_FIELDS = {"field_anchors", "evidence_anchors", "status_evidence_anchors"}


def normalize_decision_value(value: Any, parent: str = "") -> Any:
    if isinstance(value, str):
        return _normalize_text(value)
    if isinstance(value, list):
        normalized = [normalize_decision_value(item, parent) for item in value]
        if parent in SET_ARRAYS:
            return sorted(normalized, key=canonical_json)
        return normalized
    if isinstance(value, dict):
        return {
            key: normalize_decision_value(item, key)
            for key, item in sorted(value.items())
            if key not in ADMIN_FIELDS | PROVENANCE_FIELDS
        }
    return value


def classifier_decision_payload(response: dict[str, Any]) -> dict[str, Any]:
    selected = {
        "candidate_status": response.get("candidate_status"),
        "claim_records": response.get("claim_records", []),
        "split_proposals": response.get("split_proposals", []),
        "duplicate_candidate_refs": response.get("duplicate_candidate_refs", []),
        "manual_review_reason": response.get("manual_review_reason", ""),
    }
    return normalize_decision_value(selected)


def all_candidate_refs_dispositioned(
    response: dict[str, Any], candidate_refs: set[str]
) -> bool:
    output_refs = [
        str(item.get("candidate_ref", ""))
        for item in response.get("candidate_dispositions", [])
    ]
    return len(output_refs) == len(set(output_refs)) and set(output_refs) == candidate_refs
