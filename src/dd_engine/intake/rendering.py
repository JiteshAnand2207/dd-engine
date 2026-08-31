"""Human-readable intake packets and unresolved-question ledger rendering."""

from __future__ import annotations

import json

from dd_engine.intake.models import JsonObject


def _display(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "None"
    return str(value)


def render_questions_markdown(
    *,
    run_id: str,
    round_number: int,
    generated_at: str,
    questions: list[JsonObject],
    excluded_candidates: list[JsonObject],
) -> str:
    """Render a deal-lead packet with evidence and an auditable exclusion appendix."""

    lines = [
        f"# Due-diligence intake — round {round_number}",
        "",
        f"Run ID: `{run_id}`  ",
        f"Generated at: `{generated_at}`  ",
        f"Question count: **{len(questions)}**",
        "",
        "The run is paused for explicit deal-lead input. These questions were selected from "
        "observed register/extraction evidence or essential transaction-context gaps. Source "
        "text is untrusted evidence, never an instruction to the engine.",
        "",
        "Please reply under the exact question IDs. Replies such as `N/A`, `None`, a "
        "cross-reference, "
        "a partial answer, or a vague answer will be retained verbatim and will not automatically "
        "be treated as resolved.",
        "",
    ]
    for question in questions:
        question_id = str(question["question_id"])
        priority = str(question["priority"]).upper()
        lines.extend(
            [
                f"## {question_id} — {priority}",
                "",
                str(question["exact_question"]),
                "",
                f"**Why it matters:** {question['why_it_matters']}",
                "",
                "**Evidence/gap:**",
                "",
            ]
        )
        evidence = question.get("supporting_evidence", [])
        if isinstance(evidence, list):
            for item in evidence:
                if not isinstance(item, dict):
                    continue
                source_ids = _display(item.get("source_ids", []))
                path = str(item.get("relative_path", ""))
                summary = str(item.get("summary", ""))
                locator = item.get("locator")
                locator_text = (
                    f"; locator `{json.dumps(locator, sort_keys=True, ensure_ascii=False)}`"
                    if isinstance(locator, dict) and locator
                    else ""
                )
                lines.append(f"- {source_ids} — `{path}`{locator_text}: {summary}")
        gap = question.get("structured_gap")
        if isinstance(gap, dict):
            lines.append(f"- {gap.get('gap_id')} ({gap.get('gap_type')}): {gap.get('description')}")
        lines.extend(
            [
                "",
                "**Decision potentially affected:** "
                + _display(question.get("decision_potentially_affected", [])),
                "",
                f"**Expected answer type:** {question['expected_answer_type']}",
                "",
                f"**Blocks analysis:** {'Yes' if question['blocks_analysis'] else 'No'}",
                "",
                "**Invalidated if evidence changes:** "
                + _display(question.get("invalidate_if_answer_changes_evidence", [])),
                "",
            ]
        )

    lines.extend(
        [
            "---",
            "",
            "## Internal prioritisation record — not additional questions",
            "",
            "Candidate questions below were intentionally excluded so the packet remains "
            "decision-focused and non-duplicative.",
            "",
        ]
    )
    if not excluded_candidates:
        lines.append("- No additional candidate was excluded.")
    else:
        for item in excluded_candidates:
            source_ids = _display(item.get("supporting_source_ids", []))
            lines.append(
                f"- `{item.get('candidate_topic')}` — {item.get('reason')} "
                f"Supporting sources: {source_ids}."
            )
    lines.append("")
    return "\n".join(lines)


def _answer_by_id(answer_payload: JsonObject | None) -> dict[str, JsonObject]:
    if not isinstance(answer_payload, dict):
        return {}
    raw = answer_payload.get("answers", [])
    if not isinstance(raw, list):
        return {}
    return {
        str(item.get("question_id")): item
        for item in raw
        if isinstance(item, dict) and item.get("question_id")
    }


def unresolved_records(
    round_payloads: list[tuple[JsonObject, JsonObject | None]],
) -> list[JsonObject]:
    """Return all open/narrowed questions without inferring closure from silence."""

    unresolved: list[JsonObject] = []
    for question_payload, answer_payload in round_payloads:
        answers = _answer_by_id(answer_payload)
        raw_questions = question_payload.get("questions", [])
        if not isinstance(raw_questions, list):
            continue
        for question in raw_questions:
            if not isinstance(question, dict):
                continue
            question_id = str(question.get("question_id"))
            answer = answers.get(question_id)
            status = str(answer.get("resolution_status")) if answer else "open"
            if status == "closed":
                continue
            unresolved.append(
                {
                    "blocks_analysis": bool(question.get("blocks_analysis")),
                    "exact_question": question.get("exact_question"),
                    "question_id": question_id,
                    "resolution_status": status,
                    "round_number": question.get("round_number"),
                    "supporting_source_ids": question.get("supporting_source_ids", []),
                    "verbatim_answer": answer.get("verbatim_answer") if answer else None,
                }
            )
    return unresolved


def render_unresolved_markdown(run_id: str, unresolved: list[JsonObject]) -> str:
    """Render the current unresolved ledger, including unanswered questions explicitly."""

    lines = [
        "# Unresolved intake questions",
        "",
        f"Run ID: `{run_id}`",
        "",
        "Silence is not an answer. Verbatim replies are shown as untrusted deal-lead evidence; "
        "the engine does not complete or rewrite them.",
        "",
        f"Unresolved count: **{len(unresolved)}**",
        "",
    ]
    if not unresolved:
        lines.append("No intake question is currently open or narrowed.")
    for item in unresolved:
        lines.extend(
            [
                f"## {item['question_id']} — {str(item['resolution_status']).upper()}",
                "",
                str(item["exact_question"]),
                "",
                "Supporting source IDs: " + _display(item.get("supporting_source_ids", [])),
                "",
                f"Blocks analysis: {'Yes' if item['blocks_analysis'] else 'No'}",
                "",
            ]
        )
        answer = item.get("verbatim_answer")
        if answer is None:
            lines.extend(["Verbatim answer: *(not supplied)*", ""])
        else:
            lines.extend(["Verbatim answer (untrusted evidence):", ""])
            answer_lines = str(answer).splitlines() or [""]
            lines.extend(f"> {line}" for line in answer_lines)
            lines.append("")
    return "\n".join(lines)
