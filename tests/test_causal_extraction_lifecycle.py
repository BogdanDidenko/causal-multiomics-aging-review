import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_DIR = ROOT / "protocol" / "causal_extraction" / "v0.2.0"


def test_v0_2_is_explicitly_rejected_and_inactive() -> None:
    lifecycle = json.loads((LEGACY_DIR / "lifecycle.json").read_text())

    assert lifecycle["lifecycle_status"] == "legacy_rejected"
    assert lifecycle["active"] is False
    assert lifecycle["production_approved"] is False
    assert lifecycle["semantic_content_frozen"] is True


def test_v0_2_frozen_files_match_recorded_hashes() -> None:
    lifecycle = json.loads((LEGACY_DIR / "lifecycle.json").read_text())

    for filename, expected_hash in lifecycle["original_sha256"].items():
        actual_hash = hashlib.sha256((LEGACY_DIR / filename).read_bytes()).hexdigest()
        assert actual_hash == expected_hash
