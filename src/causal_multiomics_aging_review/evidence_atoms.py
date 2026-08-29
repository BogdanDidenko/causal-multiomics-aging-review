from __future__ import annotations

import copy
import re
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from causal_multiomics_aging_review.causal_extraction import (
    canonical_json,
    canonical_sections,
    sha256_text,
)

ATOMIZATION_VERSION = "evidence-atoms-v1"
EVIDENCE_FIELDS = ("method_evidence", "result_evidence")
_PARAGRAPH_BOUNDARY = re.compile(r"\n{2,}")
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")
_TABLE_HEADING = re.compile(r"\b(table|supplementary table)\b", re.IGNORECASE)


def _trim_span(text: str, start: int, end: int) -> tuple[int, int] | None:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return (start, end) if start < end else None


def _boundary_spans(
    text: str, start: int, end: int, boundary: re.Pattern[str]
) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    cursor = start
    for match in boundary.finditer(text, start, end):
        trimmed = _trim_span(text, cursor, match.start())
        if trimmed is not None:
            spans.append(trimmed)
        cursor = match.end()
    trimmed = _trim_span(text, cursor, end)
    if trimmed is not None:
        spans.append(trimmed)
    return spans


def _is_table_like(text: str, start: int, end: int, heading: str) -> bool:
    if _TABLE_HEADING.search(heading):
        return True
    lines = text[start:end].splitlines()
    if not lines:
        return False
    table_lines = sum(
        line.count("|") >= 2
        or line.count("\t") >= 2
        or bool(re.match(r"^\s*Table\s+[A-Z0-9]", line, re.IGNORECASE))
        for line in lines
    )
    return table_lines >= max(1, len(lines) // 3)


def _split_long_span(text: str, start: int, end: int, max_characters: int) -> list[tuple[int, int]]:
    if end - start <= max_characters:
        return [(start, end)]
    spans: list[tuple[int, int]] = []
    cursor = start
    while end - cursor > max_characters:
        maximum = cursor + max_characters
        minimum = cursor + max_characters // 2
        window = text[minimum:maximum]
        split = None
        for pattern in (r"\n+", r"(?<=[;:,.!?])\s+", r"\s+"):
            matches = list(re.finditer(pattern, window))
            if matches:
                split = minimum + matches[-1].end()
                break
        split = split or maximum
        trimmed = _trim_span(text, cursor, split)
        if trimmed is not None:
            spans.append(trimmed)
        cursor = split
    trimmed = _trim_span(text, cursor, end)
    if trimmed is not None:
        spans.append(trimmed)
    return spans


def section_atom_spans(
    text: str,
    *,
    heading: str = "",
    max_characters: int = 1000,
) -> list[tuple[int, int, str]]:
    """Return deterministic non-overlapping raw spans for one canonical section."""

    if max_characters < 100:
        raise ValueError("max_characters must be at least 100")
    paragraphs = _boundary_spans(text, 0, len(text), _PARAGRAPH_BOUNDARY)
    atoms: list[tuple[int, int, str]] = []
    for paragraph_start, paragraph_end in paragraphs:
        table_like = _is_table_like(text, paragraph_start, paragraph_end, heading)
        if table_like:
            units = _boundary_spans(text, paragraph_start, paragraph_end, re.compile(r"\n+"))
            atom_type = "table_row"
        else:
            units = _boundary_spans(text, paragraph_start, paragraph_end, _SENTENCE_BOUNDARY)
            atom_type = "prose"

        for unit_start, unit_end in units:
            for atom_start, atom_end in _split_long_span(
                text, unit_start, unit_end, max_characters
            ):
                atoms.append((atom_start, atom_end, atom_type))

    _validate_span_coverage(text, atoms)
    return atoms


def _validate_span_coverage(text: str, spans: Iterable[tuple[int, int, str]]) -> None:
    covered = bytearray(len(text))
    previous_end = 0
    for start, end, _ in spans:
        if not 0 <= start < end <= len(text):
            raise ValueError(f"Invalid evidence span: {start}:{end}")
        if start < previous_end:
            raise ValueError(f"Overlapping evidence span: {start}:{end}")
        if any(covered[start:end]):
            raise ValueError(f"Duplicate evidence coverage: {start}:{end}")
        covered[start:end] = b"\x01" * (end - start)
        previous_end = end
    uncovered = [
        position
        for position, character in enumerate(text)
        if not character.isspace() and not covered[position]
    ]
    if uncovered:
        raise ValueError(f"Evidence atoms omit non-whitespace character {uncovered[0]}")


def build_evidence_atom_index(
    record: dict[str, Any], *, max_atom_characters: int = 1000
) -> dict[str, Any]:
    sections = canonical_sections(record)
    document_sha256 = sha256_text(canonical_json(record["sections"]))
    atoms: list[dict[str, Any]] = []
    section_records: list[dict[str, Any]] = []
    document_atom_order = 0
    for section in sections:
        text = section["text"]
        section_sha256 = sha256_text(text)
        spans = section_atom_spans(
            text,
            heading=section["heading"],
            max_characters=max_atom_characters,
        )
        section_records.append(
            {
                "section_id": section["section_id"],
                "heading": section["heading"],
                "page_numbers": section["page_numbers"],
                "source_order": section["source_order"],
                "character_count": len(text),
                "section_sha256": section_sha256,
                "atom_count": len(spans),
            }
        )
        for section_atom_order, (start, end, atom_type) in enumerate(spans, start=1):
            raw_text = text[start:end]
            atom_sha256 = sha256_text(raw_text)
            locator = canonical_json(
                {
                    "document_sha256": document_sha256,
                    "section_id": section["section_id"],
                    "start": start,
                    "end": end,
                    "atom_sha256": atom_sha256,
                    "atomization_version": ATOMIZATION_VERSION,
                }
            )
            document_atom_order += 1
            atoms.append(
                {
                    "evidence_atom_id": f"ea_{sha256_text(locator)[:24]}",
                    "section_id": section["section_id"],
                    "section_sha256": section_sha256,
                    "heading": section["heading"],
                    "page_numbers": section["page_numbers"],
                    "source_order": section["source_order"],
                    "section_atom_order": section_atom_order,
                    "document_atom_order": document_atom_order,
                    "raw_start": start,
                    "raw_end": end,
                    "offset_unit": "unicode_codepoint",
                    "atom_type": atom_type,
                    "raw_text": raw_text,
                    "atom_sha256": atom_sha256,
                }
            )
    atom_ids = [atom["evidence_atom_id"] for atom in atoms]
    if len(atom_ids) != len(set(atom_ids)):
        raise ValueError("Evidence atom IDs are not unique")
    return {
        "atomization_version": ATOMIZATION_VERSION,
        "report_id": record["record_id"],
        "document_id": record["document_id"],
        "doi": record["doi"],
        "title": record["title"],
        "document_sha256": document_sha256,
        "offset_unit": "unicode_codepoint",
        "max_atom_characters": max_atom_characters,
        "sections": section_records,
        "atoms": atoms,
        "coverage": {
            "canonical_section_count": len(sections),
            "canonical_character_count": sum(len(section["text"]) for section in sections),
            "nonempty_section_count": sum(bool(section["text"].strip()) for section in sections),
            "atom_count": len(atoms),
            "non_whitespace_coverage": 1.0,
            "overlap_count": 0,
        },
    }


def build_evidence_atom_windows(
    atom_index: dict[str, Any],
    *,
    max_core_characters: int = 48000,
    context_characters_per_side: int = 4000,
    max_core_atoms: int | None = None,
    max_context_atoms_per_side: int | None = None,
) -> list[dict[str, Any]]:
    if (
        max_core_characters <= 0
        or context_characters_per_side < 0
        or (max_core_atoms is not None and max_core_atoms <= 0)
        or (max_context_atoms_per_side is not None and max_context_atoms_per_side < 0)
    ):
        raise ValueError("Window character limits must be non-negative")
    atoms = atom_index["atoms"]
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_characters = 0
    for atom in atoms:
        characters = len(atom["raw_text"])
        if current and (
            current_characters + characters > max_core_characters
            or (max_core_atoms is not None and len(current) >= max_core_atoms)
        ):
            groups.append(current)
            current = []
            current_characters = 0
        current.append(atom)
        current_characters += characters
    if current:
        groups.append(current)

    atom_position = {atom["evidence_atom_id"]: position for position, atom in enumerate(atoms)}
    windows: list[dict[str, Any]] = []
    for window_order, core_atoms in enumerate(groups, start=1):
        first = atom_position[core_atoms[0]["evidence_atom_id"]]
        last = atom_position[core_atoms[-1]["evidence_atom_id"]]
        before: list[dict[str, Any]] = []
        characters = 0
        cursor = first - 1
        while cursor >= 0:
            if max_context_atoms_per_side is not None and len(before) >= max_context_atoms_per_side:
                break
            atom = atoms[cursor]
            if characters + len(atom["raw_text"]) > context_characters_per_side:
                break
            before.insert(0, atom)
            characters += len(atom["raw_text"])
            cursor -= 1
        after: list[dict[str, Any]] = []
        characters = 0
        cursor = last + 1
        while cursor < len(atoms):
            if max_context_atoms_per_side is not None and len(after) >= max_context_atoms_per_side:
                break
            atom = atoms[cursor]
            if characters + len(atom["raw_text"]) > context_characters_per_side:
                break
            after.append(atom)
            characters += len(atom["raw_text"])
            cursor += 1

        core_atom_ids = [atom["evidence_atom_id"] for atom in core_atoms]
        context_atom_ids = [atom["evidence_atom_id"] for atom in before + after]

        def ordered_section_ids(items: list[dict[str, Any]]) -> list[str]:
            return list(dict.fromkeys(str(atom["section_id"]) for atom in items))

        windows.append(
            {
                "work_unit_id": f"analysis-window-{window_order:03d}",
                "core_section_ids": ordered_section_ids(core_atoms),
                "context_section_ids": ordered_section_ids(before + after),
                "core_atom_ids": core_atom_ids,
                "context_atom_ids": context_atom_ids,
                "core_character_count": sum(len(atom["raw_text"]) for atom in core_atoms),
                "context_character_count": sum(len(atom["raw_text"]) for atom in before + after),
                "core_atom_count": len(core_atoms),
                "context_atom_count": len(before + after),
            }
        )

    core_atom_occurrences: dict[str, int] = defaultdict(int)
    for window in windows:
        for atom_id in window["core_atom_ids"]:
            core_atom_occurrences[atom_id] += 1
    missing = sorted(set(atom["evidence_atom_id"] for atom in atoms) - core_atom_occurrences.keys())
    repeated = sorted(atom_id for atom_id, count in core_atom_occurrences.items() if count != 1)
    if missing or repeated:
        raise ValueError(
            f"Invalid atom-window coverage: missing={len(missing)}, repeated={len(repeated)}"
        )
    return windows


def evidence_packet(atom_index: dict[str, Any], window: dict[str, Any]) -> list[dict[str, Any]]:
    core_ids = set(window["core_atom_ids"])
    context_ids = set(window["context_atom_ids"])
    packet = []
    for atom in atom_index["atoms"]:
        atom_id = atom["evidence_atom_id"]
        if atom_id not in core_ids and atom_id not in context_ids:
            continue
        packet.append(
            {
                "evidence_atom_id": atom_id,
                "section_id": atom["section_id"],
                "evidence_scope": "core" if atom_id in core_ids else "context",
                "text": atom["raw_text"],
            }
        )
    return packet


def _analysis_evidence(response: dict[str, Any]) -> Iterable[tuple[str, Any]]:
    for analysis_index, analysis in enumerate(response.get("analyses", [])):
        for field in EVIDENCE_FIELDS:
            for anchor_index, anchor in enumerate(analysis.get(field, [])):
                yield f"analyses[{analysis_index}].{field}[{anchor_index}]", anchor


def validate_atom_grounding(
    response: dict[str, Any],
    packet: Iterable[dict[str, Any]],
    *,
    core_atom_ids: set[str] | None = None,
) -> list[dict[str, str]]:
    packet_items = list(packet)
    valid_ids = {str(atom["evidence_atom_id"]) for atom in packet_items}
    required_core_ids = (
        set(core_atom_ids)
        if core_atom_ids is not None
        else {
            str(atom["evidence_atom_id"])
            for atom in packet_items
            if atom.get("evidence_scope") == "core"
        }
    )
    failures: list[dict[str, str]] = []
    for path, atom_id in _analysis_evidence(response):
        value = str(atom_id)
        if value not in valid_ids:
            failures.append({"path": path, "evidence_atom_id": value, "reason": "unknown_atom_id"})
    for analysis_index, analysis in enumerate(response.get("analyses", [])):
        analysis_ids = {
            str(atom_id) for field in EVIDENCE_FIELDS for atom_id in analysis.get(field, [])
        }
        if not analysis_ids:
            failures.append(
                {
                    "path": f"analyses[{analysis_index}]",
                    "evidence_atom_id": "",
                    "reason": "analysis_without_evidence",
                }
            )
        elif not analysis_ids.intersection(required_core_ids):
            failures.append(
                {
                    "path": f"analyses[{analysis_index}]",
                    "evidence_atom_id": "",
                    "reason": "analysis_without_core_evidence",
                }
            )
    return failures


def validate_quote_grounding(
    response: dict[str, Any],
    packet: Iterable[dict[str, Any]],
    *,
    core_atom_ids: set[str] | None = None,
) -> list[dict[str, str]]:
    packet_items = list(packet)
    section_atoms: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for atom in packet_items:
        section_atoms[str(atom["section_id"])].append(atom)
    required_core_ids = (
        set(core_atom_ids)
        if core_atom_ids is not None
        else {
            str(atom["evidence_atom_id"])
            for atom in packet_items
            if atom.get("evidence_scope") == "core"
        }
    )
    failures: list[dict[str, str]] = []
    matched_ids_by_analysis: dict[int, set[str]] = defaultdict(set)
    for path, anchor in _analysis_evidence(response):
        analysis_index = int(path.split("[", 1)[1].split("]", 1)[0])
        section_id = str(anchor.get("section_id", ""))
        quote = str(anchor.get("quote", ""))
        matching_atoms = [
            atom
            for atom in section_atoms.get(section_id, [])
            if quote and quote in str(atom["text"])
        ]
        if section_id not in section_atoms:
            reason = "unknown_section_id"
        elif not matching_atoms:
            reason = "quote_not_substring_of_supplied_atom"
        else:
            matched_ids_by_analysis[analysis_index].update(
                str(atom["evidence_atom_id"]) for atom in matching_atoms
            )
            continue
        failures.append({"path": path, "section_id": section_id, "quote": quote, "reason": reason})
    for analysis_index, analysis in enumerate(response.get("analyses", [])):
        if not any(analysis.get(field) for field in EVIDENCE_FIELDS):
            failures.append(
                {
                    "path": f"analyses[{analysis_index}]",
                    "section_id": "",
                    "quote": "",
                    "reason": "analysis_without_evidence",
                }
            )
        elif not matched_ids_by_analysis[analysis_index].intersection(required_core_ids):
            failures.append(
                {
                    "path": f"analyses[{analysis_index}]",
                    "section_id": "",
                    "quote": "",
                    "reason": "analysis_without_core_evidence",
                }
            )
    return failures


def resolve_atom_grounding(response: dict[str, Any], atom_index: dict[str, Any]) -> dict[str, Any]:
    resolved = copy.deepcopy(response)
    atom_by_id = {atom["evidence_atom_id"]: atom for atom in atom_index["atoms"]}
    for analysis in resolved.get("analyses", []):
        for field in EVIDENCE_FIELDS:
            resolved_field = []
            for atom_id in analysis.get(field, []):
                atom = atom_by_id[atom_id]
                resolved_field.append(
                    {
                        "evidence_atom_id": atom_id,
                        "section_id": atom["section_id"],
                        "section_sha256": atom["section_sha256"],
                        "raw_start": atom["raw_start"],
                        "raw_end": atom["raw_end"],
                        "offset_unit": atom["offset_unit"],
                        "quote": atom["raw_text"],
                        "quote_sha256": atom["atom_sha256"],
                    }
                )
            analysis[f"{field}_resolved"] = resolved_field
    return resolved


def resolve_quote_grounding(
    response: dict[str, Any],
    atom_index: dict[str, Any],
    *,
    allowed_atom_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Resolve exact model quotes to deterministic source atoms and raw offsets."""

    resolved = copy.deepcopy(response)
    atoms = [
        atom
        for atom in atom_index["atoms"]
        if allowed_atom_ids is None or atom["evidence_atom_id"] in allowed_atom_ids
    ]
    for analysis in resolved.get("analyses", []):
        for field in EVIDENCE_FIELDS:
            resolved_field = []
            for anchor in analysis.get(field, []):
                section_id = str(anchor["section_id"])
                quote = str(anchor["quote"])
                matches = [
                    atom
                    for atom in atoms
                    if atom["section_id"] == section_id and quote in atom["raw_text"]
                ]
                if not matches:
                    raise ValueError(f"Quote does not resolve to an allowed atom: {section_id!r}")
                selected = min(matches, key=lambda atom: atom["document_atom_order"])
                atom_offset = selected["raw_text"].index(quote)
                resolved_field.append(
                    {
                        "evidence_atom_id": selected["evidence_atom_id"],
                        "section_id": section_id,
                        "section_sha256": selected["section_sha256"],
                        "raw_start": selected["raw_start"] + atom_offset,
                        "raw_end": selected["raw_start"] + atom_offset + len(quote),
                        "offset_unit": selected["offset_unit"],
                        "quote": quote,
                        "quote_sha256": sha256_text(quote),
                        "matching_atom_count": len(matches),
                    }
                )
            analysis[f"{field}_resolved"] = resolved_field
    return resolved


def table_density(record: dict[str, Any]) -> float:
    total = 0
    table_like = 0
    for section in canonical_sections(record):
        text = section["text"]
        total += len(text)
        for line in text.splitlines() or [text]:
            if (
                line.count("|") >= 2
                or line.count("\t") >= 2
                or bool(re.match(r"^\s*Table\s+[A-Z0-9]", line, re.IGNORECASE))
                or _TABLE_HEADING.search(section["heading"])
            ):
                table_like += len(line)
    return table_like / total if total else 0.0
