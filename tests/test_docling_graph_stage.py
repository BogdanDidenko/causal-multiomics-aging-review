from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = REPO / "scripts/docling_graph" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_corpus_has_98_unique_source_hashed_documents() -> None:
    module = load_script("build_corpus_manifest.py")
    config = REPO / "protocol/full_text/docling_graph_v1.0.0.json"
    _, rows = module.build_rows(config)
    assert len(rows) == 98
    assert len({row["doi"] for row in rows}) == 98
    assert len({row["document_id"] for row in rows}) == 98
    assert {row["source_format"] for row in rows} == {"pdf", "html", "xml"}
    assert all(len(row["source_sha256"]) == 64 for row in rows)


def test_codex_adapter_preserves_roles_and_extracts_json_schema() -> None:
    module = load_script("codex_openai_compat_server.py")
    payload = {
        "messages": [
            {"role": "system", "content": "Extract facts."},
            {"role": "user", "content": "Paper text."},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "result", "schema": {"type": "object"}},
        },
    }
    prompt = module.messages_to_prompt(payload["messages"])
    assert "<SYSTEM>" in prompt
    assert "<USER>" in prompt
    assert module.response_schema(payload) == {"type": "object"}
    assert module.request_hash(payload) == module.request_hash(json.loads(json.dumps(payload)))


def test_codex_schema_normalizer_requires_every_object_property() -> None:
    module = load_script("codex_openai_compat_server.py")
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "details": {
                "type": "object",
                "properties": {"note": {"type": "string", "default": ""}},
            },
        },
        "required": ["name"],
    }
    normalized = module.normalize_codex_schema(schema)
    assert normalized["required"] == ["name", "details"]
    assert normalized["additionalProperties"] is False
    assert normalized["properties"]["details"]["required"] == ["note"]
    assert "default" not in normalized["properties"]["details"]["properties"]["note"]


def test_docling_graph_config_locks_luna_light_and_no_decision_role() -> None:
    config = json.loads(
        (REPO / "protocol/full_text/docling_graph_v1.0.0.json").read_text(encoding="utf-8")
    )
    assert config["model"]["codex_cli_model"] == "gpt-5.6-luna"
    assert config["model"]["reasoning_effort"] == "low"
    assert "no eligibility" in config["model"]["purpose"]
    assert config["docling_graph"]["provenance"] == "detailed"
    assert config["docling_graph"]["parallel_workers"] == 1
    assert config["docling_graph"]["extraction_contract"] == "direct"
    assert config["docling_graph"]["fallback_contract_on_context_overflow"] == "dense"
    assert config["docling_graph"]["gleaning_enabled"] is False
    assert config["docling_graph"]["structured_sparse_check"] is False
    assert config["conversion"]["pdf_ocr"] is False
    assert config["corpus"]["expected_retrieval_candidates"] == 98
    assert config["corpus"]["expected_sufficient_full_texts_after_conversion"] == 97
    assert config["corpus"]["full_text_sufficiency_gate"]["model_input_allowed"] is False


def test_execution_shards_are_stable_and_non_overlapping() -> None:
    module = load_script("run_corpus.py")
    document_ids = [f"doi_{value:016x}" for value in range(30)]
    shards = [
        {doc for doc in document_ids if module.belongs_to_shard(doc, 3, index)}
        for index in range(3)
    ]
    assert set.union(*shards) == set(document_ids)
    assert not (shards[0] & shards[1] or shards[0] & shards[2] or shards[1] & shards[2])


def test_graph_quote_normalization_handles_markup_not_content_changes() -> None:
    module = load_script("audit_graph_outputs.py")
    source = "Cochran *Q* test\nwas used for heterogeneity."
    assert module.normalized_text("Cochran Q test was used") in module.normalized_text(source)
    assert module.normalized_text("Egger test was used") not in module.normalized_text(source)
