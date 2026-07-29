#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCREENING = ROOT / "protocol" / "screening"
SUITE_PATH = SCREENING / "configs" / "prompt_suite_v0.91.0.json"
OUTPUT = SCREENING / "prompt_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def add_artifact(
    artifacts: list[dict[str, str]],
    stage: str,
    role: str,
    config: dict[str, str],
) -> None:
    prompt_path = SCREENING / config["prompt"]
    schema_path = SCREENING / config["schema"]
    prompt = prompt_path.read_text(encoding="utf-8")
    prompt_id = re.search(r"^PROMPT_ID:\s*(.+)$", prompt, re.M)
    version = re.search(r"^PROMPT_VERSION:\s*(.+)$", prompt, re.M)
    if not prompt_id or not version:
        raise ValueError(f"Missing prompt ID/version in {prompt_path}")
    artifacts.append(
        {
            "prompt_id": prompt_id.group(1).strip(),
            "version": version.group(1).strip(),
            "stage": stage,
            "role": role,
            "prompt_path": str(prompt_path.relative_to(SCREENING)),
            "prompt_sha256": sha256(prompt_path),
            "schema_path": str(schema_path.relative_to(SCREENING)),
            "schema_sha256": sha256(schema_path),
        }
    )


def main() -> None:
    suite = load(SUITE_PATH)
    artifacts: list[dict[str, str]] = []
    for stage in ("title_abstract", "full_text"):
        stage_config = suite["stages"][stage]
        if "section_selector" in stage_config:
            add_artifact(
                artifacts,
                stage,
                "section_selector",
                stage_config["section_selector"],
            )
        for role, config in stage_config["roles"].items():
            add_artifact(artifacts, stage, role, config)
            if config.get("verification_prompt"):
                add_artifact(
                    artifacts,
                    stage,
                    f"{role}_contract_verifier",
                    {
                        "prompt": config["verification_prompt"],
                        "schema": config["schema"],
                    },
                )
        add_artifact(artifacts, stage, "adjudicator", stage_config["adjudication"])
    manifest = {
        "manifest_version": "1.0.0",
        "active_suite": f"{suite['suite_id']}@{suite['suite_version']}",
        "suite_config": {
            "path": str(SUITE_PATH.relative_to(SCREENING)),
            "sha256": sha256(SUITE_PATH),
        },
        "approval_status": "rejected_title_abstract_v0.91.0_sealed_v6",
        "approval_date": date.today().isoformat(),
        "benchmark_version": "sealed_v6_v0.51.0",
        "created_date": date.today().isoformat(),
        "change_note": (
            "Title/abstract v0.91.0 preserves the v0.77.0 scope contract and "
            "replaces two compound causal judgments with short atomic "
            "contracts. Separate GPT 5.6 Terra Medium reviewers assess report "
            "completion, genetic-instrument designs, assigned interventions, "
            "molecular perturbations, directed or mediation models, "
            "directional action language, and explicit effect or causal-link "
            "language. Python performs only fixed three-valued OR aggregation "
            "and the existing logical consistency rules. Stability still "
            "requires 100% exact agreement for every tracked categorical "
            "family signal, both aggregate signals, identification status, "
            "and PRISMA route; no metric or exclusion short-circuit was "
            "relaxed. The v0.79.0 refinement fixes general class boundaries "
            "found by the first atomic focus run: genetic-instrument methods "
            "are not directed models, drug prioritization without a contrast "
            "is not an intervention, background causal wording is not a "
            "current result, ordinary causal-relationship inflections count, "
            "and variance-contribution wording is not an action verb. "
            "v0.80.0 makes the two directional lexical families disjoint: "
            "a positive action/mechanism signal has precedence, so the "
            "effect/causal-noun fallback is recorded as not assessed and is "
            "not sent to the model. This is a logical routing rule and "
            "reduces stochastic calls without changing the aggregate "
            "directional criterion. v0.81.0 removes route-irrelevant "
            "title-stage subtyping between assigned interventions and direct "
            "molecular perturbations. Both now feed one atomic "
            "manipulation-design signal; full text retains responsibility "
            "for the detailed design-family profile. "
            "After separate-agent focus runs showed new one-off drift in "
            "otherwise unchanged specialists, v0.82.0 retains the same "
            "atomic fields but evaluates them in one causal-signals Terra "
            "call per record. This reduces the independent stochastic call "
            "surface while preserving criterion-level JSON and Python-only "
            "logical aggregation. v0.83.0 removes route-irrelevant "
            "title-stage subtyping of directional action versus effect "
            "phrases. One binary high-sensitivity language specialist now "
            "retains any explicit X-to-Y causal, mechanistic, or effect "
            "wording; current-report attribution and evidence strength are "
            "deferred to full text. v0.84.0 clarifies three general boundary "
            "classes exposed by the full development run: any literal "
            "current analysis of lifespan is aging-relevant even when it is "
            "secondary; treated or induced validation models count as "
            "manipulation when results validate those models; and changes in "
            "algorithmic prediction/classification performance are not "
            "biological directional language. v0.85.0 converts the "
            "directional-language check into an ordered syntax-presence "
            "contract covering active, passive, compact, effect, and role "
            "constructions, with stop-on-first-match behavior. It also "
            "forbids inferring an engineered manipulation from a disease "
            "model name or genotype label without explicit record text. "
            "v0.86.0 makes relative-clause passive constructions explicit "
            "positives and excludes purpose/infinitive prevention wording "
            "that has no named biological agent. "
            "v0.87.0 moves the literal current-result lifespan check ahead "
            "of disease-prognosis interpretation and treats spaced and "
            "hyphenated X-mediated-Y constructions identically. "
            "v0.88.0 adds a mandatory Terra Medium contract-verification pass "
            "after the three specialist drafts. Canonical production fields "
            "are verified before routing, while draft_round_a and a separate "
            "raw-reviewer agreement metric preserve direct visibility into "
            "single-call stochastic drift. Python only splits the verified "
            "atomic fields and applies existing logical consistency rules. "
            "v0.89.0 replaces the compound verifier with three separate "
            "self-contained scope, causal-design, and directional-language "
            "contract-verification passes. Each second pass sees only its "
            "matching specialist draft and the same narrow atomic contract. "
            "v0.90.0 adds an ordered literal check for X with causal role(s) "
            "in a named outcome while retaining the negative boundary for "
            "causal-role fragments that omit the outcome. "
            "v0.91.0 makes applied genomic structural equation modeling, "
            "including genomic SEM, an explicit directed-model positive "
            "without requiring a separate mediation estimate. "
            "The candidate was frozen at commit 1dd685d before the one-time "
            "sealed v6 run. Sealed v6 retained identical final routes but "
            "failed strict stability with 0.84 all-tracked and 0.96 decisive "
            "agreement, so v0.91.0 is rejected and v6 is not calibration "
            "data. "
            "Full-text prompts remain v0.1.0 and unvalidated."
        ),
        "artifacts": artifacts,
    }
    OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
