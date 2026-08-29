from causal_multiomics_aging_review.causal_extraction import sha256_text
from causal_multiomics_aging_review.evidence_atoms import (
    build_evidence_atom_index,
    build_evidence_atom_windows,
    evidence_packet,
    resolve_atom_grounding,
    resolve_quote_grounding,
    section_atom_spans,
    table_density,
    validate_atom_grounding,
    validate_quote_grounding,
)


def record() -> dict:
    return {
        "record_id": "doi:10.1000/evidence",
        "document_id": "doi_evidence",
        "doi": "10.1000/evidence",
        "title": "Evidence test",
        "sections": [
            {
                "section_id": "chunk:0000",
                "heading": "Methods",
                "page_numbers": [1],
                "text": "Cells received CRISPRi. Target engagement was verified.",
            },
            {
                "section_id": "chunk:0001",
                "heading": "Results",
                "page_numbers": [2],
                "text": "Knockdown reduced senescence by 20%. β = −0.20.\n\nNo toxicity occurred.",
            },
        ],
    }


def test_atom_offsets_resolve_exact_unicode_text() -> None:
    index = build_evidence_atom_index(record(), max_atom_characters=100)
    source = {section["section_id"]: section["text"] for section in record()["sections"]}
    for atom in index["atoms"]:
        text = source[atom["section_id"]]
        assert text[atom["raw_start"] : atom["raw_end"]] == atom["raw_text"]
        assert sha256_text(atom["raw_text"]) == atom["atom_sha256"]
    assert index["coverage"]["non_whitespace_coverage"] == 1.0


def test_atomization_is_deterministic_and_content_bound() -> None:
    first = build_evidence_atom_index(record(), max_atom_characters=100)
    second = build_evidence_atom_index(record(), max_atom_characters=100)
    assert first == second

    changed = record()
    changed["sections"][0]["text"] += " Additional diagnostic."
    third = build_evidence_atom_index(changed, max_atom_characters=100)
    assert third["document_sha256"] != first["document_sha256"]
    assert {atom["evidence_atom_id"] for atom in third["atoms"]} != {
        atom["evidence_atom_id"] for atom in first["atoms"]
    }


def test_long_sections_are_split_without_omitting_non_whitespace() -> None:
    text = " ".join(["A long scientific statement with evidence."] * 30)
    spans = section_atom_spans(text, max_characters=120)
    assert len(spans) > 1
    assert all(end - start <= 120 for start, end, _ in spans)
    covered = set()
    for start, end, _ in spans:
        covered.update(range(start, end))
    assert all(character.isspace() or index in covered for index, character in enumerate(text))


def test_each_atom_is_core_in_exactly_one_window() -> None:
    index = build_evidence_atom_index(record(), max_atom_characters=100)
    windows = build_evidence_atom_windows(
        index,
        max_core_characters=60,
        context_characters_per_side=100,
        max_core_atoms=2,
        max_context_atoms_per_side=1,
    )
    core_ids = [atom_id for window in windows for atom_id in window["core_atom_ids"]]
    expected = [atom["evidence_atom_id"] for atom in index["atoms"]]
    assert sorted(core_ids) == sorted(expected)
    assert len(core_ids) == len(set(core_ids))
    assert all(window["core_character_count"] <= 60 for window in windows)
    assert all(window["core_atom_count"] <= 2 for window in windows)
    assert all(window["context_atom_count"] <= 2 for window in windows)


def test_atom_id_grounding_resolves_source_quotes() -> None:
    index = build_evidence_atom_index(record(), max_atom_characters=100)
    window = build_evidence_atom_windows(index)[0]
    packet = evidence_packet(index, window)
    method_id = packet[0]["evidence_atom_id"]
    response = {
        "analyses": [
            {
                "method_evidence": [method_id],
                "result_evidence": [],
            }
        ]
    }
    assert validate_atom_grounding(response, packet) == []
    resolved = resolve_atom_grounding(response, index)
    anchor = resolved["analyses"][0]["method_evidence_resolved"][0]
    assert anchor["quote"] == packet[0]["text"]
    assert anchor["quote_sha256"] == sha256_text(anchor["quote"])


def test_unknown_atom_id_and_paraphrased_quote_fail() -> None:
    index = build_evidence_atom_index(record(), max_atom_characters=100)
    packet = evidence_packet(index, build_evidence_atom_windows(index)[0])
    id_response = {"analyses": [{"method_evidence": ["ea_unknown"], "result_evidence": []}]}
    assert validate_atom_grounding(id_response, packet)[0]["reason"] == "unknown_atom_id"

    quote_response = {
        "analyses": [
            {
                "method_evidence": [
                    {
                        "section_id": packet[0]["section_id"],
                        "quote": "The cells were treated with CRISPR interference.",
                    }
                ],
                "result_evidence": [],
            }
        ]
    }
    assert (
        validate_quote_grounding(quote_response, packet)[0]["reason"]
        == "quote_not_substring_of_supplied_atom"
    )


def test_context_only_evidence_fails_core_requirement() -> None:
    index = build_evidence_atom_index(record(), max_atom_characters=100)
    atoms = index["atoms"]
    packet = [
        {
            "evidence_atom_id": atom["evidence_atom_id"],
            "section_id": atom["section_id"],
            "evidence_scope": "core" if position == 0 else "context",
            "text": atom["raw_text"],
        }
        for position, atom in enumerate(atoms)
    ]
    context = packet[-1]

    id_response = {
        "analyses": [{"method_evidence": [context["evidence_atom_id"]], "result_evidence": []}]
    }
    assert validate_atom_grounding(id_response, packet)[0]["reason"] == (
        "analysis_without_core_evidence"
    )

    quote_response = {
        "analyses": [
            {
                "method_evidence": [
                    {"section_id": context["section_id"], "quote": context["text"]}
                ],
                "result_evidence": [],
            }
        ]
    }
    assert validate_quote_grounding(quote_response, packet)[0]["reason"] == (
        "analysis_without_core_evidence"
    )


def test_quote_grounding_resolves_raw_subspan() -> None:
    index = build_evidence_atom_index(record(), max_atom_characters=100)
    packet = evidence_packet(index, build_evidence_atom_windows(index)[0])
    quote = "CRISPRi"
    response = {
        "analyses": [
            {
                "method_evidence": [{"section_id": packet[0]["section_id"], "quote": quote}],
                "result_evidence": [],
            }
        ]
    }
    resolved = resolve_quote_grounding(
        response,
        index,
        allowed_atom_ids={atom["evidence_atom_id"] for atom in packet},
    )
    anchor = resolved["analyses"][0]["method_evidence_resolved"][0]
    source = record()["sections"][0]["text"]
    assert source[anchor["raw_start"] : anchor["raw_end"]] == quote
    assert anchor["matching_atom_count"] == 1


def test_table_density_uses_raw_table_like_lines() -> None:
    source = record()
    source["sections"][0]["heading"] = "Table 1"
    source["sections"][0]["text"] = "Outcome | Effect | P\nAge | -0.2 | 0.01"
    assert table_density(source) > 0
