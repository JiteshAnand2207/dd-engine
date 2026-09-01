"""Structured analytical record builder shared by Phase 8 and Phase 9."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from dd_engine.analysis.context import AnalysisContext, unit_value
from dd_engine.evidence.models import (
    Calculation,
    Claim,
    Contradiction,
    Evidence,
    Gap,
    Issue,
    JsonObject,
)


@dataclass(frozen=True, slots=True)
class CitationSpec:
    """One exact supporting or contradicting extracted unit."""

    unit: JsonObject
    relationship: str = "supporting"
    exact_text: str | None = None
    exact_value: Any = None


class AnalysisRecords:
    """Create mutually linked claims, citations, calculations, gaps and issues."""

    def __init__(self, context: AnalysisContext, prefix: str) -> None:
        self.context = context
        self.prefix = prefix
        self.claims: list[JsonObject] = []
        self.evidence: list[JsonObject] = []
        self.calculations: list[JsonObject] = []
        self.contradictions: list[JsonObject] = []
        self.gaps: list[JsonObject] = []
        self.issues: list[JsonObject] = []
        self.findings: dict[str, list[JsonObject]] = {}

    def add_calculation(
        self,
        *,
        calculation_id: str,
        description: str,
        inputs: Sequence[tuple[str, JsonObject, float, str | None]],
        expression: str,
        recomputed_value: float,
        reported_value: float | None = None,
        currency: str | None = "EUR",
        units: str = "EUR",
        period: str = "as stated in cited sources",
        decimal_places: int = 2,
        claim_ids: tuple[str, ...] = (),
    ) -> str:
        source_inputs: list[JsonObject] = []
        for input_id, unit, normalized, reported_text in inputs:
            source = self.context.source(str(unit["source_id"]))
            raw = unit_value(unit)
            direct_value: object = raw if isinstance(raw, int | float) else None
            if direct_value is None and isinstance(raw, str):
                try:
                    float(raw.replace(",", ""))
                except ValueError:
                    if reported_text is None:
                        reported_text = raw
                else:
                    direct_value = raw
            source_inputs.append(
                {
                    "currency": currency,
                    "extracted_unit_ids": [unit["unit_id"]],
                    "input_id": input_id,
                    "locator": unit["locator"],
                    "missing": False,
                    "normalized_value": normalized,
                    "period": period,
                    "reported_text": reported_text,
                    "reported_value": direct_value if reported_text is None else None,
                    "sign_convention": "normalized explicitly for the stated formula",
                    "source_checksum": source["sha256"],
                    "source_id": source["source_id"],
                    "source_version_status": source["probable_version_status"],
                    "supersession_acknowledged": (
                        source.get("probable_version_status") == "potentially_superseded"
                    ),
                    "unit": units,
                }
            )
        variance = recomputed_value - reported_value if reported_value is not None else None
        status = "variance_identified" if variance not in {None, 0} else "verified"
        self.calculations.append(
            Calculation(
                run_id=self.context.run_id,
                calculation_id=calculation_id,
                description=description,
                source_inputs=tuple(source_inputs),
                units=units,
                currency=currency,
                normalisation={
                    "currency": f"{currency or 'not applicable'}; no conversion",
                    "period": period,
                    "sign": "inputs retain source sign unless description states otherwise",
                    "units": f"{units}; no scaling",
                },
                formula={"expression": expression, "version": f"{calculation_id.lower()}-v1"},
                result={
                    "reported_value": reported_value,
                    "recomputed_value": recomputed_value,
                    "variance": variance,
                },
                rounding={"decimal_places": decimal_places, "mode": "half_even"},
                independent_recomputation_status=status,
                calculation_method="deterministic",
                claim_ids=claim_ids,
            ).as_record()
        )
        return calculation_id

    def add_finding(
        self,
        *,
        workstream: str,
        issue_id: str,
        conclusion: str,
        source_fact: str,
        analysis: str,
        why_it_matters: str,
        implication: str,
        action: str,
        materiality: str,
        confidence: float,
        supporting: list[CitationSpec],
        counterevidence: list[CitationSpec] | None = None,
        calculation_ids: list[str] | None = None,
        uncertainty: str | None = None,
        transaction_levers: list[str] | None = None,
        opinion_status: str | None = None,
    ) -> JsonObject:
        claim_id = f"CLM-{issue_id}"
        self.claims.append(
            Claim(
                run_id=self.context.run_id,
                claim_id=claim_id,
                statement=conclusion,
                claim_type="inference",
                workstream=workstream,
                materiality=materiality,
                confidence=confidence,
                status="supported",
            ).as_record()
        )
        supporting_ids: list[str] = []
        counter_ids: list[str] = []
        for index, spec in enumerate([*supporting, *(counterevidence or [])], start=1):
            evidence_id = f"EVD-{issue_id}-{index:02d}"
            unit = spec.unit
            source = self.context.source(str(unit["source_id"]))
            raw = unit_value(unit)
            extracted_text = spec.exact_text
            extracted_value = spec.exact_value
            if extracted_text is None and extracted_value is None:
                if isinstance(raw, str):
                    extracted_text = raw
                else:
                    extracted_value = raw
            self.evidence.append(
                Evidence(
                    run_id=self.context.run_id,
                    evidence_id=evidence_id,
                    claim_id=claim_id,
                    source_id=str(source["source_id"]),
                    source_checksum=str(source["sha256"]),
                    exact_locator=dict(unit["locator"]),
                    relationship=spec.relationship,
                    extraction_confidence=float(unit.get("confidence", 0)),
                    source_version_status=str(source["probable_version_status"]),
                    extracted_value=extracted_value,
                    extracted_text=extracted_text,
                    extracted_unit_ids=(str(unit["unit_id"]),),
                    supersession_acknowledged=(
                        source.get("probable_version_status") == "potentially_superseded"
                    ),
                ).as_record()
            )
            (supporting_ids if spec.relationship == "supporting" else counter_ids).append(
                evidence_id
            )
        calculations = tuple(calculation_ids or [])
        self.issues.append(
            Issue(
                run_id=self.context.run_id,
                issue_id=issue_id,
                conclusion=conclusion,
                workstream=workstream,
                supporting_evidence=tuple(supporting_ids),
                counterevidence=tuple(counter_ids),
                calculations=calculations,
                materiality=materiality,
                confidence=confidence,
                transaction_implication=implication,
                recommended_action=action,
                unresolved_question=uncertainty,
                claim_ids=(claim_id,),
            ).as_record()
        )
        finding: JsonObject = {
            "action": action,
            "analysis_conclusion": conclusion,
            "analytical_reasoning": analysis,
            "calculation_ids": list(calculations),
            "claim_ids": [claim_id],
            "confidence": confidence,
            "counterevidence_ids": counter_ids,
            "issue_id": issue_id,
            "materiality": materiality,
            "opinion_status": opinion_status,
            "source_fact": source_fact,
            "supporting_evidence_ids": supporting_ids,
            "transaction_implication": implication,
            "transaction_levers": transaction_levers or [],
            "uncertainty": uncertainty,
            "why_it_matters": why_it_matters,
        }
        self.findings.setdefault(workstream, []).append(finding)
        return finding

    def add_gap(
        self,
        *,
        gap_id: str,
        expected: str,
        absence_evidence: list[str],
        importance: str,
        decisions: list[str],
        action: str,
        source_ids: list[str] | None = None,
        origin: str,
    ) -> None:
        self.gaps.append(
            Gap(
                run_id=self.context.run_id,
                gap_id=gap_id,
                expected_information=expected,
                evidence_that_it_is_missing=tuple(absence_evidence),
                importance=importance,
                affected_decision=tuple(decisions),
                requested_follow_up=action,
                status="open",
                source_ids=tuple(source_ids or []),
                origin=origin,
            ).as_record()
        )

    def add_contradiction(
        self,
        *,
        contradiction_id: str,
        issue_id: str,
        conflicting_values: list[object],
        source_units: list[JsonObject],
        likely_explanations: list[str],
        status: str = "unresolved",
    ) -> None:
        """Retain a source conflict explicitly alongside its supported analytical claim."""

        source_ids = tuple(dict.fromkeys(str(unit["source_id"]) for unit in source_units))
        self.contradictions.append(
            Contradiction(
                run_id=self.context.run_id,
                contradiction_id=contradiction_id,
                conflicting_claims=(f"CLM-{issue_id}",),
                conflicting_values=tuple(conflicting_values),
                source_ids=source_ids,
                likely_explanations=tuple(likely_explanations),
                status=status,
            ).as_record()
        )
