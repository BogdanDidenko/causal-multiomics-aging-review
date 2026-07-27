from causal_multiomics_aging_review.config import load_stage_config
from causal_multiomics_aging_review.gates import gate_answer, route_adjudicated, route_round_a


def active_title_config() -> dict[str, object]:
    return load_stage_config("title_abstract")[1]


def test_round_a_advances_only_when_both_roles_include() -> None:
    config = active_title_config()
    answers = {
        "scope_reviewer": {
            "report_type": "empirical_primary",
            "bio_health_scope": "yes",
            "aging_process_relevance": "yes",
            "multiomics_status": "yes",
        },
        "causal_design_reviewer": {"identification_status": "identified"},
    }
    route, decisions = route_round_a(answers, config)
    assert route == "seek_full_text"
    assert decisions == {
        "scope_reviewer": "include",
        "causal_design_reviewer": "include",
    }


def test_unclear_has_priority_over_exclusion() -> None:
    config = active_title_config()
    answer = {
        "report_type": "nonempirical",
        "bio_health_scope": "yes",
        "aging_process_relevance": "unclear",
        "multiomics_status": "unclear",
    }
    assert gate_answer(
        answer,
        config["roles"]["scope_reviewer"],
        exclude_first=True,
    ) == "exclude"


def test_active_suite_can_prioritize_explicit_exclusion() -> None:
    config = active_title_config()
    config["gate_precedence"] = "exclude_then_unclear"
    answer = {
        "report_type": "nonempirical",
        "bio_health_scope": "yes",
        "aging_process_relevance": "unclear",
        "multiomics_status": "unclear",
        "identification_status": "unclear",
    }
    assert route_adjudicated(answer, config) == ("exclude", "exclude")


def test_adjudicator_routes_failed_causal_design_to_exclusion() -> None:
    config = active_title_config()
    answer = {
        "report_type": "empirical_primary",
        "bio_health_scope": "yes",
        "aging_process_relevance": "yes",
        "multiomics_status": "yes",
        "identification_status": "noncausal",
    }
    assert route_adjudicated(answer, config) == ("exclude", "exclude")


def test_adjudicator_preserves_uncertainty_for_manual_review() -> None:
    config = active_title_config()
    answer = {
        "report_type": "empirical_primary",
        "bio_health_scope": "yes",
        "aging_process_relevance": "yes",
        "multiomics_status": "yes",
        "identification_status": "unclear",
    }
    assert route_adjudicated(answer, config) == ("seek_full_text", "unclear")
