"""Typed records shared by intake generation and answer ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]


@dataclass(slots=True)
class QuestionCandidate:
    """One ranked question candidate grounded in evidence or an essential context gap."""

    topic_key: str
    round_number: int
    priority: str
    score: int
    exact_question: str
    why_it_matters: str
    decision_potentially_affected: list[str]
    expected_answer_type: str
    blocks_analysis: bool
    invalidate_if_answer_changes_evidence: list[str]
    supporting_evidence: list[JsonObject] = field(default_factory=list)
    structured_gap: JsonObject | None = None

    @property
    def supporting_source_ids(self) -> list[str]:
        """Return stable, de-duplicated source IDs carried by evidence records."""

        source_ids: list[str] = []
        for evidence in self.supporting_evidence:
            raw_ids = evidence.get("source_ids", [])
            if not isinstance(raw_ids, list):
                continue
            for source_id in raw_ids:
                value = str(source_id)
                if value not in source_ids:
                    source_ids.append(value)
        return source_ids

    def as_question(self, question_id: str) -> JsonObject:
        """Serialize the public question schema."""

        return {
            "blocks_analysis": self.blocks_analysis,
            "decision_potentially_affected": self.decision_potentially_affected,
            "exact_question": self.exact_question,
            "expected_answer_type": self.expected_answer_type,
            "invalidate_if_answer_changes_evidence": (self.invalidate_if_answer_changes_evidence),
            "priority": self.priority,
            "question_id": question_id,
            "round_number": self.round_number,
            "structured_gap": self.structured_gap,
            "supporting_evidence": self.supporting_evidence,
            "supporting_source_ids": self.supporting_source_ids,
            "topic_key": self.topic_key,
            "why_it_matters": self.why_it_matters,
        }


@dataclass(frozen=True, slots=True)
class IntakeOutcome:
    """Public result returned by question generation or answer ingestion."""

    action: str
    question_count: int
    reused: bool
    round_number: int
    run_path: Path
    stage_state: str
    unresolved_count: int
