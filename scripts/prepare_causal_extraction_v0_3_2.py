#!/usr/bin/env python3
"""Prepare the inherited inputs for the v0.3.2 role-contract ablation."""

from __future__ import annotations

import copy
from pathlib import Path

from causal_multiomics_aging_review.causal_extraction import (
    read_json,
    sha256_file,
    write_json,
)

REPO = Path(__file__).resolve().parents[1]
PARENT_SUITE = REPO / "protocol/causal_extraction/v0.3.1"
PARENT_OUTPUT = REPO / "data/causal_extraction/v0.3.1_development/terra_5repeat"
SUITE = REPO / "protocol/causal_extraction/v0.3.2"


def main() -> None:
    sample = read_json(PARENT_SUITE / "sample.json")
    scaffold = read_json(PARENT_SUITE / "candidate_scaffold.json")
    inherited_sample = copy.deepcopy(sample)
    inherited_sample["sample_id"] = (
        "causal_extraction_v0.3.2_inherited_twelve_report_development_sample"
    )
    inherited_sample["status"] = "inherited_unchanged_from_frozen_v0.3.1"
    inherited_sample["parent_sample"] = {
        "path": "protocol/causal_extraction/v0.3.1/sample.json",
        "sample_id": sample["sample_id"],
    }
    write_json(SUITE / "sample.json", inherited_sample)
    write_json(SUITE / "candidate_scaffold.json", scaffold)

    selected_reports = []
    total_selected = 0
    for report in scaffold["reports"]:
        repeat_paths = [
            PARENT_OUTPUT
            / "calls"
            / report["document_id"]
            / f"repeat-{repeat:02d}"
            / "normalized.json"
            for repeat in range(1, 6)
        ]
        if not all(path.is_file() for path in repeat_paths):
            raise ValueError(f"Incomplete v0.3.1 output for {report['document_id']}")
        outputs = [read_json(path) for path in repeat_paths]
        maps = [
            {item["candidate_id"]: item for item in output["candidates"]}
            for output in outputs
        ]
        selected_ids = []
        for candidate in report["candidates"]:
            candidate_id = candidate["candidate_id"]
            qualifications = [mapping[candidate_id]["qualification"] for mapping in maps]
            if len(set(qualifications)) != 1:
                raise ValueError(
                    f"Non-unanimous parent qualification for {candidate_id}: "
                    f"{qualifications}"
                )
            if qualifications[0] == "include":
                selected_ids.append(candidate_id)
        total_selected += len(selected_ids)
        selected_reports.append(
            {
                "sample_order": report["sample_order"],
                "report_id": report["report_id"],
                "document_id": report["document_id"],
                "doi": report["doi"],
                "eligible_candidate_ids": selected_ids,
                "parent_normalized_sha256": [
                    sha256_file(path) for path in repeat_paths
                ],
            }
        )
    write_json(
        SUITE / "eligible_candidate_set.json",
        {
            "set_version": "0.3.2",
            "status": "frozen_input_pending_suite_freeze",
            "source": "v0.3.1 five_repeat_unanimous_qualification",
            "selection_rule": "include only when all five v0.3.1 runs returned include",
            "majority_vote_used": False,
            "report_count": len(selected_reports),
            "eligible_candidate_count": total_selected,
            "reports": selected_reports,
        },
    )
    print(
        f"prepared {total_selected} unanimously eligible candidates across "
        f"{len(selected_reports)} reports"
    )


if __name__ == "__main__":
    main()
