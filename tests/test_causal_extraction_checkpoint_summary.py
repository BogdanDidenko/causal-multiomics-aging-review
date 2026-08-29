import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/summarize_causal_extraction_checkpoints.py"
SPEC = importlib.util.spec_from_file_location("checkpoint_summary", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
SUMMARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUMMARY)


def test_empty_derived_outputs_are_not_level_agreement() -> None:
    outputs = [[], [], [], [], []]
    assert SUMMARY.exact(outputs) is True
    assert SUMMARY.repeated_nonempty_exact(outputs) is False


def test_nonempty_derived_outputs_can_be_exact() -> None:
    output = [{"causal_evidence_level": 3}]
    outputs = [output, output, output, output, output]
    assert SUMMARY.repeated_nonempty_exact(outputs) is True


def test_zero_denominator_is_not_reported_as_zero_agreement() -> None:
    metric = SUMMARY.observed_rate(0, 0)
    assert metric["proportion"] is None
    assert SUMMARY.metric_cell(metric) == "not estimable (0 candidates)"


def test_corrected_checkpoint_report_withdraws_vacuous_level_agreement() -> None:
    path = REPO / "analysis/causal_extraction/checkpoints/v0.1.1-rc1" / "two_sample_stability.json"
    report = json.loads(path.read_text())
    checkpoint_a, checkpoint_b = report["checkpoints"]
    assert checkpoint_a["five_run_derived_level_exact"]["total"] == 0
    assert checkpoint_a["five_run_derived_level_exact"]["proportion"] is None
    assert checkpoint_b["five_run_derived_level_exact"]["total"] == 1
    assert checkpoint_b["five_run_derived_level_exact"]["successes"] == 0
    assert report["correction"]["scientific_synthesis_permission"] == "rejected"
