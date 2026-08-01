from __future__ import annotations

import math
from collections import Counter
from collections.abc import Hashable, Iterable
from typing import Any


def wilson_interval(
    successes: int, total: int, z: float = 1.959963984540054
) -> dict[str, float] | None:
    if total <= 0:
        return None
    proportion = successes / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total + z**2 / (4 * total**2)
        )
        / denominator
    )
    return {"lower": max(0.0, center - margin), "upper": min(1.0, center + margin)}


def confusion_matrix(
    pairs: Iterable[tuple[Hashable, Hashable]],
) -> dict[str, Any]:
    items = list(pairs)
    labels = sorted({value for pair in items for value in pair}, key=str)
    counts = Counter(items)
    return {
        "labels": [str(label) for label in labels],
        "rows_are_gold_columns_are_predicted": [
            [counts[(gold, predicted)] for predicted in labels] for gold in labels
        ],
    }


def categorical_cohen_kappa(
    pairs: Iterable[tuple[Hashable, Hashable]],
) -> float | None:
    items = list(pairs)
    if not items:
        return None
    total = len(items)
    observed = sum(left == right for left, right in items) / total
    left_counts = Counter(left for left, _ in items)
    right_counts = Counter(right for _, right in items)
    expected = sum(
        left_counts[label] * right_counts[label]
        for label in set(left_counts) | set(right_counts)
    ) / total**2
    if expected == 1:
        return 1.0 if observed == 1 else 0.0
    return (observed - expected) / (1 - expected)


def inter_rater_summary(
    rows: list[dict[str, str]], fields: Iterable[str]
) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for field in fields:
        pairs = [
            (row.get(f"expert_1_{field}", ""), row.get(f"expert_2_{field}", ""))
            for row in rows
            if row.get(f"expert_1_{field}", "")
            and row.get(f"expert_2_{field}", "")
        ]
        exact = sum(left == right for left, right in pairs)
        report[field] = {
            "records": len(pairs),
            "exact_agreement": exact / len(pairs) if pairs else None,
            "exact_agreement_wilson_95": (
                wilson_interval(exact, len(pairs)) if pairs else None
            ),
            "cohen_kappa": categorical_cohen_kappa(pairs),
            "confusion_matrix": confusion_matrix(pairs),
        }
    return report
