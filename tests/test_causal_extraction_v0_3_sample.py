import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUITE = REPO / "protocol" / "causal_extraction" / "v0.3.0"
SPEC = importlib.util.spec_from_file_location(
    "freeze_causal_extraction_v0_3_sample",
    REPO / "scripts" / "freeze_causal_extraction_v0_3_sample.py",
)
assert SPEC is not None and SPEC.loader is not None
FREEZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FREEZER)


def test_frozen_sample_is_reproducible_and_disjoint() -> None:
    frozen = json.loads((SUITE / "sample.json").read_text(encoding="utf-8"))

    assert frozen == FREEZER.build_sample()
    assert len(frozen["reports"]) == 12
    assert frozen["sampling_frame"]["eligible_reports"] == 101
    assert frozen["sampling_frame"]["genuinely_sealed"] is False
    report_ids = {item["report_id"] for item in frozen["reports"]}
    assert report_ids.isdisjoint(FREEZER.prior_development_report_ids())
    assert len({item["diversity_role"] for item in frozen["reports"]}) == 12


def test_v0_3_remains_inactive_before_reference_freeze() -> None:
    lifecycle = json.loads((SUITE / "lifecycle.json").read_text(encoding="utf-8"))

    assert lifecycle["lifecycle_status"] == "development_sample_pending_reference_inventory"
    assert lifecycle["active"] is False
    assert lifecycle["production_approved"] is False
    assert lifecycle["sample_frozen"] is True
    assert lifecycle["codebook_frozen"] is False
    assert lifecycle["model_runs_allowed"] is False
