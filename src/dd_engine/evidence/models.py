"""Typed Phase 7 claim, evidence, calculation and issue records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, cast

JsonObject = dict[str, Any]

CLAIM_TYPES = frozenset({"fact", "calculation", "inference", "recommendation", "limitation"})
WORKSTREAMS = frozenset(
    {
        "financial",
        "commercial",
        "legal_contractual",
        "operational_management",
        "it",
        "tax",
        "cross_workstream",
    }
)
MATERIALITY_LEVELS = frozenset({"immaterial", "low", "medium", "high", "critical"})
MATERIAL_CLAIM_LEVELS = frozenset({"high", "critical"})
CLAIM_STATUSES = frozenset({"draft", "supported", "contradicted", "unresolved", "withdrawn"})
EVIDENCE_RELATIONSHIPS = frozenset({"supporting", "contradicting"})
CONTRADICTION_STATUSES = frozenset({"resolved", "unresolved"})
GAP_STATUSES = frozenset({"open", "narrowed", "resolved", "accepted_limitation"})
CALCULATION_METHODS = frozenset({"deterministic", "model_assisted"})
RECOMPUTATION_STATUSES = frozenset(
    {
        "verified",
        "variance_identified",
        "failed",
        "not_performed",
        "blocked_missing_inputs",
        "not_applicable_model_assisted",
    }
)


class _Record:
    """Serialize a frozen dataclass without hiding null or empty audit fields."""

    def as_record(self) -> JsonObject:
        return cast(JsonObject, asdict(cast(Any, self)))


@dataclass(frozen=True, slots=True)
class Claim(_Record):
    """One analytical statement whose support can be checked independently."""

    run_id: str
    claim_id: str
    statement: str
    claim_type: str
    workstream: str
    materiality: str
    confidence: float
    status: str
    required_independent_sources: int = 1


@dataclass(frozen=True, slots=True)
class Evidence(_Record):
    """One source-bound citation that supports or contradicts exactly one claim."""

    run_id: str
    evidence_id: str
    claim_id: str
    source_id: str
    source_checksum: str
    exact_locator: JsonObject
    relationship: str
    extraction_confidence: float
    source_version_status: str
    extracted_value: Any = None
    extracted_text: str | None = None
    extracted_unit_ids: tuple[str, ...] = ()
    supersession_acknowledged: bool = False


@dataclass(frozen=True, slots=True)
class Calculation(_Record):
    """A reported-versus-recomputed calculation with explicit normalization."""

    run_id: str
    calculation_id: str
    description: str
    source_inputs: tuple[JsonObject, ...]
    units: str | None
    currency: str | None
    normalisation: JsonObject
    formula: JsonObject
    result: JsonObject
    rounding: JsonObject
    independent_recomputation_status: str
    calculation_method: str
    claim_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Contradiction(_Record):
    """A conflict retained until its evidence-backed resolution is explicit."""

    run_id: str
    contradiction_id: str
    conflicting_claims: tuple[str, ...]
    conflicting_values: tuple[Any, ...]
    source_ids: tuple[str, ...]
    likely_explanations: tuple[str, ...]
    status: str
    intake_question_id: str | None = None


@dataclass(frozen=True, slots=True)
class Gap(_Record):
    """Expected information that is absent, incomplete or unresolved."""

    run_id: str
    gap_id: str
    expected_information: str
    evidence_that_it_is_missing: tuple[str, ...]
    importance: str
    affected_decision: tuple[str, ...]
    requested_follow_up: str
    status: str
    intake_question_id: str | None = None
    source_ids: tuple[str, ...] = ()
    answer_provenance: JsonObject | None = None
    origin: str = "analytical"


@dataclass(frozen=True, slots=True)
class Issue(_Record):
    """A decision-oriented conclusion linked only through structured records."""

    run_id: str
    issue_id: str
    conclusion: str
    workstream: str
    supporting_evidence: tuple[str, ...]
    counterevidence: tuple[str, ...]
    calculations: tuple[str, ...]
    materiality: str
    confidence: float
    transaction_implication: str
    recommended_action: str
    unresolved_question: str | None = None
    status: str = "open"
    claim_ids: tuple[str, ...] = field(default_factory=tuple)
