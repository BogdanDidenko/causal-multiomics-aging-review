import pytest

from causal_multiomics_aging_review.validation import (
    categorical_cohen_kappa,
    confusion_matrix,
    inter_rater_summary,
    wilson_interval,
)


def test_wilson_interval_is_bounded() -> None:
    interval = wilson_interval(98, 100)
    assert interval is not None
    assert 0 < interval["lower"] < 0.98 < interval["upper"] <= 1


def test_confusion_matrix_uses_gold_rows() -> None:
    matrix = confusion_matrix([("include", "include"), ("exclude", "include")])
    assert matrix["labels"] == ["exclude", "include"]
    assert matrix["rows_are_gold_columns_are_predicted"] == [[0, 1], [0, 1]]


def test_categorical_kappa_perfect_agreement() -> None:
    assert categorical_cohen_kappa([("yes", "yes"), ("no", "no")]) == 1.0


def test_inter_rater_summary_ignores_unfinished_rows() -> None:
    rows = [
        {"expert_1_route": "include", "expert_2_route": "include"},
        {"expert_1_route": "exclude", "expert_2_route": ""},
    ]
    report = inter_rater_summary(rows, ["route"])
    assert report["route"]["records"] == 1
    assert report["route"]["exact_agreement"] == 1.0
    assert report["route"]["cohen_kappa"] == pytest.approx(1.0)
