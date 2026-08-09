"""Docling Graph schema for causal multi-omics studies of aging.

The graph is an evidence index, not an eligibility decision. Entity identities
must be document-derived so Docling Graph can ground them back to source text.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def edge(label: str, **kwargs: Any) -> Any:
    """Declare a graph relationship using Docling Graph field metadata."""
    if "default" not in kwargs and "default_factory" not in kwargs:
        kwargs["default"] = ...
    return Field(json_schema_extra={"edge_label": label}, **kwargs)


class OmicsLayerType(str, Enum):
    GENOMICS = "genomics"
    EPIGENOMICS = "epigenomics"
    TRANSCRIPTOMICS = "transcriptomics"
    PROTEOMICS = "proteomics"
    METABOLOMICS = "metabolomics"
    LIPIDOMICS = "lipidomics"
    MICROBIOMICS = "microbiomics"
    METAGENOMICS = "metagenomics"
    OTHER_MOLECULAR_OMICS = "other_molecular_omics"


class DesignFamily(str, Enum):
    GENETIC_INSTRUMENT = "genetic_instrument"
    RANDOMIZED_INTERVENTION = "randomized_intervention"
    NONRANDOMIZED_INTERVENTION = "nonrandomized_intervention"
    QUASI_EXPERIMENT = "quasi_experiment"
    DIRECT_PERTURBATION = "direct_perturbation"
    TEMPORAL_IDENTIFICATION = "temporal_identification"
    FORMAL_MEDIATION = "formal_mediation"
    DAG_SCM = "dag_scm"
    SEM = "sem"
    BAYESIAN_NETWORK = "bayesian_network"
    CAUSAL_DISCOVERY_ALGORITHM = "causal_discovery_algorithm"
    OTHER_FORMAL_CAUSAL_DESIGN = "other_formal_causal_design"


class IdentificationStatus(str, Enum):
    IDENTIFIED = "identified"
    HYPOTHESIS_ONLY = "hypothesis_only"
    ASSOCIATION_ONLY = "association_only"
    UNCLEAR = "unclear"


class EvidenceAnchor(BaseModel):
    """Shortest exact source quotation supporting the parent extraction."""

    model_config = ConfigDict(is_entity=False, extra="forbid")

    quote: str = Field(
        description="A short verbatim quotation from the current report; never paraphrase."
    )
    section_heading: str = Field(
        default="",
        description="Nearest printed section heading, or an empty string if unavailable.",
    )


class OmicsLayer(BaseModel):
    """A molecular omics layer analyzed in the current report."""

    model_config = ConfigDict(
        is_entity=True,
        graph_id_fields=["reported_name", "assay_or_data_source"],
        extra="forbid",
    )

    reported_name: str = Field(
        description="Verbatim layer or assay name used in the report, such as RNA-seq."
    )
    normalized_layer: OmicsLayerType
    assay_or_data_source: str = Field(
        description="Named assay, cohort, QTL resource, or dataset from the report."
    )
    cohort_or_system: str = ""
    origin: str = Field(
        description=(
            "One of measured_in_report, external_dataset_analyzed, context_only, or unclear."
        )
    )
    analytic_role: str = Field(description="How this layer participates in the reported analysis.")
    evidence: EvidenceAnchor


class AgingConstruct(BaseModel):
    """An aging process, trajectory, longevity phenotype, or intervention target."""

    model_config = ConfigDict(is_entity=True, graph_id_fields=["reported_name"], extra="forbid")

    reported_name: str = Field(description="Verbatim aging-related construct or phenotype.")
    role: str = Field(
        description=(
            "One of aging_outcome_or_trajectory, longevity_or_healthspan, aging_mechanism, "
            "aging_intervention_target, age_context_only, or unclear."
        )
    )
    evidence: EvidenceAnchor


class CausalAssumption(BaseModel):
    """A design assumption nested within one causal analysis."""

    model_config = ConfigDict(is_entity=False, extra="forbid")

    name: str = Field(
        description="Assumption name as stated or conventionally named in the report."
    )
    analysis_name: str = Field(description="Verbatim method or analysis name to which it applies.")
    status: str = Field(description="One of addressed, not_reported, violated, or unclear.")
    assessment: str = ""
    evidence: EvidenceAnchor


class DiagnosticOrSensitivity(BaseModel):
    """A diagnostic or sensitivity check nested within one causal analysis."""

    model_config = ConfigDict(is_entity=False, extra="forbid")

    name: str
    analysis_name: str = Field(description="Verbatim method or analysis name being checked.")
    result_or_role: str
    evidence: EvidenceAnchor


class ValidationEvidence(BaseModel):
    """Validation evidence nested within one causal analysis."""

    model_config = ConfigDict(is_entity=False, extra="forbid")

    reported_name: str = Field(description="Verbatim validation experiment or analysis name.")
    analysis_name: str = Field(description="Verbatim causal analysis name being validated.")
    validation_type: str = Field(
        description=(
            "One of replication, colocalization, orthogonal_perturbation, "
            "independent_cohort, negative_control, triangulation, or other."
        )
    )
    independence: str = Field(
        description="One of independent, partially_independent, not_independent, or unclear."
    )
    alignment: str = Field(
        description=(
            "One of same_causal_link, related_mechanism_only, general_plausibility, or unclear."
        )
    )
    what_it_validates: str
    evidence: EvidenceAnchor


class CausalAnalysis(BaseModel):
    """A formal causal-effect or directed-hypothesis analysis in the current report."""

    model_config = ConfigDict(
        is_entity=True, graph_id_fields=["method_name", "target_claim"], extra="forbid"
    )

    method_name: str = Field(
        description="Verbatim name of the method or experimental design in the report."
    )
    design_family: DesignFamily
    design_role: str = Field(
        description=(
            "One of primary_identification, supporting_identification, validation_only, "
            "mentioned_only, or unclear."
        )
    )
    identification_status: IdentificationStatus
    target_claim: str = Field(
        description="Concise claim using only entities and direction stated in the report."
    )
    population_or_model: str = ""
    exposure_or_intervention: str = ""
    comparator: str = ""
    outcome: str = ""
    time_horizon: str = ""
    estimand_or_contrast: str = ""
    evidence: EvidenceAnchor
    assumptions: list[CausalAssumption] = Field(default_factory=list)
    diagnostics: list[DiagnosticOrSensitivity] = Field(default_factory=list)
    validations: list[ValidationEvidence] = Field(default_factory=list)


class CausalMultiomicsAgingPaper(BaseModel):
    """Evidence index for the current full report; empty lists are valid.

    Exclude cited-study claims, background wording, feature importance, WGCNA,
    pseudotime, colocalization alone, and undirected networks from causal analyses.
    """

    model_config = ConfigDict(is_entity=True, graph_id_fields=["title"], extra="forbid")

    title: str = Field(description="Exact report title from the document.")
    doi: str = Field(default="", description="DOI printed in the report, if present.")
    report_type: str = Field(
        description=(
            "One of empirical_primary, review_editorial, protocol, methods_only, "
            "resource, or unclear."
        )
    )
    biological_or_health_scope: str = Field(description="One of yes, no, or unclear.")
    full_text_sufficient: str = Field(description="One of yes, no, or unclear.")
    aging_constructs: list[AgingConstruct] = edge(
        "INVESTIGATES_AGING_CONSTRUCT", default_factory=list
    )
    omics_layers: list[OmicsLayer] = edge("USES_OMICS_LAYER", default_factory=list)
    causal_analyses: list[CausalAnalysis] = edge("REPORTS_CAUSAL_ANALYSIS", default_factory=list)
    limitations: list[str] = Field(
        default_factory=list,
        description="Verbatim or closely normalized limitations stated by the authors.",
    )
