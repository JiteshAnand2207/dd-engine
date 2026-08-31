"""Dynamic intake candidate generation from registered and extracted observations."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from dd_engine.intake.models import JsonObject, QuestionCandidate
from dd_engine.intake.observations import (
    ObservationIndex,
    source_evidence,
    unit_evidence,
    unit_text,
)

ROUND_LIMITS = {1: 12, 2: 15}
_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2}
_MISSING_REFERENCE = re.compile(r"\bsee\s+([a-z][a-z0-9_-]*\s+\d+(?:\.\d+)*)", re.I)
_COMPANY_NAME = re.compile(
    r"\b([A-Z][A-Za-z&'-]+(?:\s+[A-Z][A-Za-z&'-]+){0,4}\s+"
    r"(?:Limited|Ltd|PLC))\b"
)


def _gap(gap_id: str, gap_type: str, description: str) -> JsonObject:
    return {"description": description, "gap_id": gap_id, "gap_type": gap_type}


def _source_labels(index: ObservationIndex, source_ids: list[str]) -> str:
    labels: list[str] = []
    for source_id in source_ids:
        source = index.sources_by_id.get(source_id, {})
        labels.append(f"{source_id} ({source.get('relative_path', 'unknown path')})")
    return "; ".join(labels)


def _context_candidates(round_number: int) -> list[QuestionCandidate]:
    if round_number != 1:
        return []
    invalidates = ["intake_round_2", "analyse", "report", "validate"]
    return [
        QuestionCandidate(
            topic_key="transaction-perimeter",
            round_number=1,
            priority="critical",
            score=95,
            exact_question=(
                "What legal entities, businesses, assets and liabilities are inside and "
                "outside the proposed transaction perimeter, and is the contemplated deal "
                "a share purchase, asset purchase or another structure?"
            ),
            why_it_matters=(
                "The room identifies the target evidence but not the buyer's agreed perimeter; "
                "scope and transaction form determine which liabilities and consents matter."
            ),
            decision_potentially_affected=["scope", "go_no_go", "transaction_structure"],
            expected_answer_type=(
                "structured list of included/excluded perimeter items and deal form"
            ),
            blocks_analysis=True,
            invalidate_if_answer_changes_evidence=invalidates,
            structured_gap=_gap(
                "GAP-R1-TRANSACTION-PERIMETER",
                "essential_transaction_context",
                "No deal-lead transaction perimeter is stored in the room or run artifacts.",
            ),
        ),
        QuestionCandidate(
            topic_key="price-structure-assumptions",
            round_number=1,
            priority="critical",
            score=94,
            exact_question=(
                "What headline price or valuation reference should the diligence test, and "
                "what cash, debt, debt-like, working-capital, earn-out, rollover or other "
                "consideration assumptions are currently proposed? Please distinguish fixed "
                "terms from open negotiating positions."
            ),
            why_it_matters=(
                "Material findings cannot be translated into price or structure implications "
                "without the committee's assumptions, and the engine must not invent a valuation."
            ),
            decision_potentially_affected=["price", "transaction_structure", "negotiating_terms"],
            expected_answer_type=(
                "currency amounts plus a structured description of consideration mechanics"
            ),
            blocks_analysis=True,
            invalidate_if_answer_changes_evidence=invalidates,
            structured_gap=_gap(
                "GAP-R1-PRICE-STRUCTURE",
                "essential_transaction_context",
                "No committee price or consideration mechanics are stored in the "
                "observed evidence.",
            ),
        ),
        QuestionCandidate(
            topic_key="investment-thesis",
            round_number=1,
            priority="high",
            score=80,
            exact_question=(
                "What is the investment thesis, which value drivers must be proven, and which "
                "specific findings would be deal-breakers or require a price or structure change?"
            ),
            why_it_matters=(
                "The room cannot reveal the committee's thesis or risk appetite; these are "
                "needed to prioritize material contradictions without a generic diligence script."
            ),
            decision_potentially_affected=["go_no_go", "price", "diligence_priority"],
            expected_answer_type="short thesis, ranked value drivers and explicit deal-breakers",
            blocks_analysis=True,
            invalidate_if_answer_changes_evidence=invalidates,
            structured_gap=_gap(
                "GAP-R1-INVESTMENT-THESIS",
                "essential_transaction_context",
                "No deal-lead investment thesis or deal-breaker criteria are stored in the run.",
            ),
        ),
        QuestionCandidate(
            topic_key="scope-materiality",
            round_number=1,
            priority="high",
            score=76,
            exact_question=(
                "What diligence cut-off date, materiality thresholds, forecast horizon and "
                "scope exclusions should apply, including any topics already covered by "
                "another adviser?"
            ),
            why_it_matters=(
                "A defined cut-off and materiality lens prevents low-value questions and makes "
                "omissions, stale evidence and out-of-scope matters explicit."
            ),
            decision_potentially_affected=["scope", "diligence_priority", "go_no_go"],
            expected_answer_type="dates, monetary/qualitative thresholds and scoped exclusions",
            blocks_analysis=False,
            invalidate_if_answer_changes_evidence=invalidates,
            structured_gap=_gap(
                "GAP-R1-SCOPE-MATERIALITY",
                "essential_transaction_context",
                "No deal-specific cut-off, materiality threshold or scope exclusion is stored.",
            ),
        ),
    ]


def _unreadable_candidate(index: ObservationIndex, round_number: int) -> QuestionCandidate | None:
    adverse = [
        source
        for source_id, source in index.sources_by_id.items()
        if index.extraction_sources_by_id[source_id].get("status") == "failed"
    ]
    if not adverse:
        return None
    evidence = [
        source_evidence(
            source,
            "Extraction failed: "
            + str(index.extraction_sources_by_id[str(source["source_id"])].get("failure_reason")),
        )
        for source in adverse
    ]
    labels = _source_labels(index, [str(item["source_id"]) for item in adverse])
    return QuestionCandidate(
        topic_key="critical-unreadable-sources",
        round_number=round_number,
        priority="critical",
        score=100,
        exact_question=(
            f"The following registered source could not be read: {labels}. What does each "
            "document cover, is it current or operative, and can you provide a readable original "
            "or replacement?"
        ),
        why_it_matters=(
            "An unreadable source can conceal a material obligation; its relevance must be "
            "established before analysis can rely on the room as complete."
        ),
        decision_potentially_affected=["scope", "go_no_go", "transaction_structure"],
        expected_answer_type=(
            "document purpose/status plus readable replacement or explicit unavailability"
        ),
        blocks_analysis=True,
        invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
        supporting_evidence=evidence,
        structured_gap=_gap(
            "GAP-UNREADABLE-SOURCES",
            "critical_unreadable_source",
            f"{len(adverse)} registered source(s) failed extraction.",
        ),
    )


def _missing_reference_candidate(
    index: ObservationIndex, round_number: int
) -> QuestionCandidate | None:
    matches: list[tuple[JsonObject, str]] = []
    empty_names = {path.lower().replace("\\", "/") for path in index.empty_directories}
    known_paths = [str(source.get("relative_path", "")).lower() for source in index.sources]
    for unit in index.units:
        for match in _MISSING_REFERENCE.finditer(unit_text(unit)):
            reference = " ".join(match.group(1).split())
            normalized = reference.lower()
            explicitly_empty = any(
                item.endswith("/" + normalized) or item == normalized for item in empty_names
            )
            path_missing = not any(normalized.replace(" ", "_") in path for path in known_paths)
            if explicitly_empty or path_missing:
                matches.append((unit, reference))
    if not matches:
        return None
    references = sorted({reference for _, reference in matches})
    evidence = [
        unit_evidence(unit, f"References missing location '{reference}'.")
        for unit, reference in matches[:8]
    ]
    return QuestionCandidate(
        topic_key="missing-cross-referenced-documents",
        round_number=round_number,
        priority="critical",
        score=93,
        exact_question=(
            "Room responses refer to "
            + ", ".join(references)
            + ", but the corresponding location is absent or empty. Which documents were meant, "
            "and can you provide them or confirm explicitly that they do not exist?"
        ),
        why_it_matters=(
            "A broken document reference is not evidence of the underlying matter and may hide "
            "property, contract, debt or other material support."
        ),
        decision_potentially_affected=["scope", "go_no_go", "price", "transaction_structure"],
        expected_answer_type=(
            "document list with source paths/files, or an explicit non-existence statement"
        ),
        blocks_analysis=True,
        invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
        supporting_evidence=evidence,
        structured_gap=_gap(
            "GAP-MISSING-CROSS-REFERENCE",
            "missing_referenced_document",
            "Extracted answers point to a location with no registered document.",
        ),
    )


def _matching_units(
    index: ObservationIndex,
    pattern: re.Pattern[str],
    *,
    workstreams: set[str] | None = None,
) -> list[JsonObject]:
    matches: list[JsonObject] = []
    for unit in index.units:
        source = index.sources_by_id.get(str(unit.get("source_id")), {})
        if workstreams is not None and str(source.get("likely_workstream")) not in workstreams:
            continue
        if pattern.search(unit_text(unit)):
            matches.append(unit)
    return matches


def _unsupported_financial_candidate(
    index: ObservationIndex, round_number: int
) -> QuestionCandidate | None:
    pattern = re.compile(
        r"support\s+to\s+follow|supporting\s+.{0,100}\s+not\s+"
        r"(?:included|provided|available)",
        re.I | re.S,
    )
    matches = _matching_units(index, pattern, workstreams={"financial"})
    if not matches:
        return None
    return QuestionCandidate(
        topic_key="unsupported-financial-adjustments",
        round_number=round_number,
        priority="critical",
        score=92,
        exact_question=(
            "The observed financial evidence includes a material adjustment whose support is "
            "stated to be absent or still to follow. What is the amount and rationale, which "
            "costs are non-recurring, and where are the invoices, approvals and "
            "implementation plan?"
        ),
        why_it_matters=(
            "An unsupported adjustment can change the supportable earnings base and therefore "
            "the committee's price and go/no-go assessment."
        ),
        decision_potentially_affected=["price", "go_no_go", "earnings_quality"],
        expected_answer_type="amount-by-item bridge plus supporting source files",
        blocks_analysis=True,
        invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
        supporting_evidence=[unit_evidence(unit) for unit in matches[:6]],
        structured_gap=_gap(
            "GAP-UNSUPPORTED-FINANCIAL-ADJUSTMENT",
            "unsupported_figure",
            "A source asserts an adjustment but also says its supporting evidence is absent.",
        ),
    )


def _calculation_warning_candidate(
    index: ObservationIndex, round_number: int
) -> QuestionCandidate | None:
    pattern = re.compile(
        r"formula\s+(?:incorrect|wrong)|does\s+not\s+tie|doesn't\s+tie|"
        r"not\s+reconciled|unreconciled|mismatch",
        re.I,
    )
    matches = _matching_units(index, pattern, workstreams={"financial", "tax"})
    if not matches:
        return None
    return QuestionCandidate(
        topic_key="explicit-calculation-contradiction",
        round_number=round_number,
        priority="critical",
        score=91,
        exact_question=(
            "A source explicitly flags an incorrect, non-tying or unreconciled calculation. "
            "What is the correct treatment and amount, who approved it, and can you provide the "
            "controlled replacement schedule without overwriting the submitted source?"
        ),
        why_it_matters=(
            "A source-labelled calculation error may directly change working capital, debt, tax "
            "or earnings adjustments; the engine will preserve the original and any "
            "correction separately."
        ),
        decision_potentially_affected=["price", "working_capital_mechanism", "go_no_go"],
        expected_answer_type="corrected amount/method, approver and replacement source reference",
        blocks_analysis=True,
        invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
        supporting_evidence=[unit_evidence(unit) for unit in matches[:6]],
        structured_gap=_gap(
            "GAP-EXPLICIT-CALCULATION-CONTRADICTION",
            "financial_contradiction",
            "Extracted evidence explicitly describes a submitted calculation as incorrect "
            "or non-tying.",
        ),
    )


def _debt_candidate(index: ObservationIndex, round_number: int) -> QuestionCandidate | None:
    debt_sources = {
        str(source.get("source_id"))
        for source in index.sources
        if source.get("likely_document_class") == "debt_document"
    }
    pending = [task for task in index.vision_tasks if str(task.get("source_id")) in debt_sources]
    exclusion_pattern = re.compile(
        r"(?:debt|loan|hp|director\s+(?:current\s+)?account).{0,120}"
        r"(?:excluded|not\s+included|not\s+debt)|"
        r"(?:excluded|not\s+included).{0,120}(?:debt|loan|hp)",
        re.I | re.S,
    )
    excluded = _matching_units(index, exclusion_pattern, workstreams={"financial"})
    if not pending and not excluded:
        return None
    evidence = [unit_evidence(unit) for unit in excluded[:5]]
    pending_ids: list[str] = []
    for task in pending:
        source_id = str(task.get("source_id"))
        if source_id not in pending_ids:
            pending_ids.append(source_id)
    evidence.extend(
        source_evidence(
            index.sources_by_id[source_id],
            "Debt/HP source remains pending local vision review.",
        )
        for source_id in pending_ids
    )
    return QuestionCandidate(
        topic_key="debt-hp-completeness",
        round_number=round_number,
        priority="critical",
        score=96,
        exact_question=(
            "The room contains debt/HP documents still pending visual review and evidence that "
            "some HP or director balances may be excluded from loan summaries. Please provide a "
            "complete lender-by-lender debt and debt-like schedule, including HP, related-party "
            "balances, security, covenants, repayment dates and change-of-control requirements, "
            "and identify the controlling source for each balance."
        ),
        why_it_matters=(
            "Debt completeness affects net-debt treatment, equity value, consent requirements "
            "and transaction structure; a management classification alone is not source proof."
        ),
        decision_potentially_affected=["price", "net_debt", "transaction_structure", "go_no_go"],
        expected_answer_type="lender-level schedule with balances, terms and source references",
        blocks_analysis=True,
        invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
        supporting_evidence=evidence,
        structured_gap=_gap(
            "GAP-DEBT-HP-COMPLETENESS",
            "debt_or_hp_gap",
            "Debt evidence is partly visual-only and submitted schedules state exclusions.",
        ),
    )


def _tax_candidate(index: ObservationIndex, round_number: int) -> QuestionCandidate | None:
    pattern = re.compile(r"\bamended\b|late\s+amendment|late\s+filing|late\s+payment", re.I)
    matches = _matching_units(index, pattern, workstreams={"tax", "legal_contractual"})
    tax_family_sources: list[str] = []
    for family in index.version_families:
        raw_ids = family.get("source_ids", [])
        if not isinstance(raw_ids, list):
            continue
        ids = [str(item) for item in raw_ids]
        if any(index.sources_by_id.get(item, {}).get("likely_workstream") == "tax" for item in ids):
            tax_family_sources.extend(item for item in ids if item not in tax_family_sources)
    if not matches and not tax_family_sources:
        return None
    evidence = [unit_evidence(unit) for unit in matches[:5]]
    evidenced = {source_id for item in evidence for source_id in item["source_ids"]}
    evidence.extend(
        source_evidence(index.sources_by_id[source_id], "Member of a candidate tax version family.")
        for source_id in tax_family_sources
        if source_id not in evidenced
    )
    return QuestionCandidate(
        topic_key="tax-amendment-status",
        round_number=round_number,
        priority="high",
        score=86,
        exact_question=(
            "The observed tax evidence includes amended/versioned returns or a late amendment "
            "entry. Which return is the filed controlling version, what caused each amendment, "
            "and have all resulting charges, interest and payments been fully settled?"
        ),
        why_it_matters=(
            "Unresolved amended filings can change tax liabilities, warranties/indemnities and "
            "the transaction's price or escrow structure."
        ),
        decision_potentially_affected=["price", "tax_indemnity", "escrow", "go_no_go"],
        expected_answer_type="period-by-period filed status, reason and payment evidence",
        blocks_analysis=False,
        invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
        supporting_evidence=evidence,
        structured_gap=_gap(
            "GAP-TAX-AMENDMENT-STATUS",
            "tax_inconsistency",
            "Versioned/amended tax evidence does not itself establish filing and settlement "
            "status.",
        ),
    )


def _consent_candidate(index: ObservationIndex, round_number: int) -> QuestionCandidate | None:
    pattern = re.compile(
        r"consent\s+(?:has\s+)?not\s+been\s+requested|"
        r"consent\s+review\s+remains\s+in\s+progress|"
        r"change[-\s]of[-\s]control.{0,100}(?:consent|required)",
        re.I | re.S,
    )
    matches = _matching_units(index, pattern, workstreams={"commercial", "legal_contractual"})
    if not matches:
        return None
    return QuestionCandidate(
        topic_key="contract-consents",
        round_number=round_number,
        priority="critical",
        score=90,
        exact_question=(
            "The room states that at least one customer-consent review is outstanding or a "
            "consent has not been requested. Which contracts, amendments, leases, debt documents "
            "or licences require notice or consent for the contemplated transaction, what is the "
            "legal/commercial basis, and what is the owner and timetable for obtaining "
            "each consent?"
        ),
        why_it_matters=(
            "Unobtained transaction consents can affect deliverability, closing conditions, "
            "customer retention and negotiating leverage."
        ),
        decision_potentially_affected=["go_no_go", "transaction_structure", "closing_conditions"],
        expected_answer_type="contract-by-contract consent matrix with clause/source and status",
        blocks_analysis=True,
        invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
        supporting_evidence=[unit_evidence(unit) for unit in matches[:6]],
        structured_gap=_gap(
            "GAP-CONTRACT-CONSENTS",
            "contract_consent_gap",
            "Extracted vendor evidence says a material consent review is incomplete or "
            "not requested.",
        ),
    )


def _company_group_candidate(index: ObservationIndex) -> QuestionCandidate | None:
    by_root: dict[str, dict[str, list[JsonObject]]] = defaultdict(lambda: defaultdict(list))
    for unit in index.units:
        text = unit_text(unit)
        for match in _COMPANY_NAME.finditer(text):
            name = " ".join(match.group(1).split())
            root = name.split()[0].casefold()
            by_root[root][name].append(unit)
    groups = [names for names in by_root.values() if len(names) >= 2]
    if not groups:
        return None
    names = sorted({name for group in groups for name in group})
    evidence: list[JsonObject] = []
    for group in groups:
        for units in group.values():
            evidence.append(unit_evidence(units[0]))
    return QuestionCandidate(
        topic_key="customer-group-identities",
        round_number=2,
        priority="critical",
        score=94,
        exact_question=(
            "Observed customer names may represent related entities: "
            + ", ".join(names[:10])
            + ". Which names share a parent or common control, what is the ultimate group, and "
            "should exposure and revenue concentration be aggregated?"
        ),
        why_it_matters=(
            "Separate trading names can understate true customer-group concentration and change "
            "retention, pricing and go/no-go conclusions."
        ),
        decision_potentially_affected=["go_no_go", "price", "customer_concentration"],
        expected_answer_type="alias-to-ultimate-parent mapping with ownership/supporting sources",
        blocks_analysis=True,
        invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
        supporting_evidence=evidence[:10],
        structured_gap=_gap(
            "GAP-CUSTOMER-GROUP-IDENTITIES",
            "customer_identity_gap",
            "Multiple observed customer names share a distinctive root but ownership is "
            "not evidenced.",
        ),
    )


def _workforce_candidate(index: ObservationIndex) -> QuestionCandidate | None:
    matches = _matching_units(
        index,
        re.compile(r"(?:headcount|employees?|contractors?).{0,80}\b\d{1,4}\b", re.I | re.S),
        workstreams={"operational_management", "tax"},
    )
    values: set[str] = set()
    for unit in matches:
        values.update(re.findall(r"\b\d{1,4}\b", unit_text(unit)))
    if len(values) < 2:
        return None
    return QuestionCandidate(
        topic_key="workforce-count-reconciliation",
        round_number=2,
        priority="high",
        score=88,
        exact_question=(
            "The extracted workforce/PAYE evidence contains different stated employee or "
            "contractor counts. Please reconcile the population by cut-off date, employment "
            "status, legal entity and client allocation, and identify the authoritative roster."
        ),
        why_it_matters=(
            "Workforce discrepancies affect payroll, tax, contractor classification, customer "
            "delivery dependence and normalized cost conclusions."
        ),
        decision_potentially_affected=["price", "go_no_go", "workforce_liabilities"],
        expected_answer_type=(
            "reconciliation table by population/date/entity with source references"
        ),
        blocks_analysis=False,
        invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
        supporting_evidence=[unit_evidence(unit) for unit in matches[:8]],
        structured_gap=_gap(
            "GAP-WORKFORCE-COUNT-RECONCILIATION",
            "workforce_discrepancy",
            "Distinct numeric workforce counts appear in observed records.",
        ),
    )


def _contract_version_candidate(index: ObservationIndex) -> QuestionCandidate | None:
    evidence: list[JsonObject] = []
    families: list[str] = []
    for family in index.version_families:
        raw_ids = family.get("source_ids", [])
        if not isinstance(raw_ids, list):
            continue
        ids = [str(item) for item in raw_ids]
        if not any(
            index.sources_by_id.get(item, {}).get("likely_document_class")
            == "contract_or_agreement"
            for item in ids
        ):
            continue
        families.append(str(family.get("version_family")))
        evidence.extend(
            source_evidence(
                index.sources_by_id[source_id],
                "Candidate agreement/amendment family; registrar status is not authoritative.",
            )
            for source_id in ids
        )
    if not evidence:
        return None
    return QuestionCandidate(
        topic_key="contract-amendment-control",
        round_number=2,
        priority="critical",
        score=92,
        exact_question=(
            "The register links original agreements and amendments in candidate version families "
            + ", ".join(families)
            + ". For each family, which documents are executed and operative, are any side "
            "letters or later amendments missing, and which provisions control consent, liability, "
            "termination and pricing?"
        ),
        why_it_matters=(
            "The register deliberately does not choose an authoritative version; applying a stale "
            "contract can reverse consent, liability and commercial conclusions."
        ),
        decision_potentially_affected=["go_no_go", "transaction_structure", "price"],
        expected_answer_type="executed-document/version matrix with missing amendments identified",
        blocks_analysis=True,
        invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
        supporting_evidence=evidence,
        structured_gap=_gap(
            "GAP-CONTRACT-AMENDMENT-CONTROL",
            "contract_version_gap",
            "Agreement supersession is candidate-only and not established as source truth.",
        ),
    )


def _property_vision_candidate(index: ObservationIndex) -> QuestionCandidate | None:
    source_ids: list[str] = []
    for task in index.vision_tasks:
        source_id = str(task.get("source_id"))
        source = index.sources_by_id.get(source_id, {})
        path = str(source.get("relative_path", "")).lower()
        if any(token in path for token in ("property", "lease", "title")) and (
            source_id not in source_ids
        ):
            source_ids.append(source_id)
    if not source_ids:
        return None
    return QuestionCandidate(
        topic_key="property-document-coverage",
        round_number=2,
        priority="high",
        score=84,
        exact_question=(
            "Material property documents remain image-only pending vision review: "
            + _source_labels(index, source_ids)
            + ". Which properties are owned, sold or leased, which are in the transaction "
            "perimeter, and can you provide searchable executed copies plus any "
            "lender/landlord consents?"
        ),
        why_it_matters=(
            "Property title, disposal history, lease obligations and consents may affect deal "
            "perimeter, closing conditions and liabilities."
        ),
        decision_potentially_affected=["scope", "transaction_structure", "closing_conditions"],
        expected_answer_type=(
            "property schedule plus executed/searchable documents and consent status"
        ),
        blocks_analysis=False,
        invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
        supporting_evidence=[
            source_evidence(
                index.sources_by_id[source_id], "Image-only source pending vision review."
            )
            for source_id in source_ids
        ],
        structured_gap=_gap(
            "GAP-PROPERTY-DOCUMENT-COVERAGE",
            "critical_unreadable_area",
            "Property source content is not yet deterministically readable.",
        ),
    )


def _answer_followups(
    round_one_questions: list[JsonObject], round_one_answers: list[JsonObject]
) -> tuple[list[QuestionCandidate], list[JsonObject]]:
    by_id = {str(item.get("question_id")): item for item in round_one_answers}
    candidates: list[QuestionCandidate] = []
    excluded: list[JsonObject] = []
    for question in round_one_questions:
        question_id = str(question.get("question_id"))
        answer = by_id.get(question_id)
        if answer is None or answer.get("verbatim_answer") is None:
            excluded.append(
                {
                    "candidate_topic": f"followup-{question_id}",
                    "reason": (
                        "Round-one question remains unanswered and is carried in "
                        "unresolved_questions.md; "
                        "it is not repeated verbatim."
                    ),
                    "supporting_source_ids": question.get("supporting_source_ids", []),
                }
            )
            continue
        if answer.get("resolution_status") == "closed":
            excluded.append(
                {
                    "candidate_topic": f"followup-{question_id}",
                    "reason": (
                        "Round-one answer is closed; asking again would duplicate known "
                        "information."
                    ),
                    "supporting_source_ids": question.get("supporting_source_ids", []),
                }
            )
            continue
        normalized = answer.get("normalised_interpretation")
        answer_kind = normalized.get("kind") if isinstance(normalized, dict) else "ambiguous"
        if answer_kind == "cross_reference":
            exact = (
                f"Your answer to {question_id} cross-referenced another location but did not "
                "resolve the underlying point. Which exact registered source ID/path and locator "
                "contains the answer, and what fact should the analysis rely on?"
            )
        else:
            exact = (
                f"Your answer to {question_id} remains ambiguous or partial. Please state the "
                "precise facts needed as "
                f"{question.get('expected_answer_type', 'a structured answer')}, "
                "identify what is still unknown, and cite the supporting source."
            )
        evidence = question.get("supporting_evidence", [])
        original_gap = question.get("structured_gap")
        original_gap_type = (
            str(original_gap.get("gap_type"))
            if isinstance(original_gap, dict)
            else "ambiguous_deal_lead_answer"
        )
        candidates.append(
            QuestionCandidate(
                topic_key=f"followup-{question_id}",
                round_number=2,
                priority=str(question.get("priority", "high")),
                score=97 if question.get("blocks_analysis") else 82,
                exact_question=exact,
                why_it_matters=(
                    f"The explicit deal-lead response to {question_id} is evidence, but its "
                    "unresolved ambiguity cannot be silently completed by the engine."
                ),
                decision_potentially_affected=[
                    str(item) for item in question.get("decision_potentially_affected", [])
                ],
                expected_answer_type=str(question.get("expected_answer_type", "structured answer")),
                blocks_analysis=bool(question.get("blocks_analysis")),
                invalidate_if_answer_changes_evidence=["analyse", "report", "validate"],
                supporting_evidence=(
                    [dict(item) for item in evidence if isinstance(item, dict)]
                    if isinstance(evidence, list)
                    else []
                ),
                structured_gap=_gap(
                    f"GAP-R2-ANSWER-{question_id}",
                    (
                        "essential_transaction_context"
                        if original_gap_type == "essential_transaction_context"
                        else "ambiguous_deal_lead_answer"
                    ),
                    f"The answer to {question_id} is {answer.get('resolution_status')}.",
                ),
            )
        )
    return candidates, excluded


def _round_one_candidates(
    index: ObservationIndex,
) -> tuple[list[QuestionCandidate], list[JsonObject]]:
    candidates = _context_candidates(1)
    for candidate in (
        _unreadable_candidate(index, 1),
        _debt_candidate(index, 1),
        _missing_reference_candidate(index, 1),
        _unsupported_financial_candidate(index, 1),
        _calculation_warning_candidate(index, 1),
        _consent_candidate(index, 1),
        _tax_candidate(index, 1),
    ):
        if candidate is not None:
            candidates.append(candidate)

    excluded: list[JsonObject] = []
    non_debt_vision = [
        task
        for task in index.vision_tasks
        if index.sources_by_id.get(str(task.get("source_id")), {}).get("likely_document_class")
        != "debt_document"
    ]
    if non_debt_vision:
        excluded.append(
            {
                "candidate_topic": "non-debt-vision-queue",
                "reason": (
                    "Deferred to round two: these visual sources are not yet shown to change the "
                    "early price/structure decision and remain visible in needs_vision.json."
                ),
                "supporting_source_ids": sorted(
                    {str(task.get("source_id")) for task in non_debt_vision}
                ),
            }
        )
    generic_non_answers = _matching_units(index, re.compile(r"^\s*(?:n/?a|none|unknown)\s*$", re.I))
    if generic_non_answers:
        excluded.append(
            {
                "candidate_topic": "generic-questionnaire-non-answers",
                "reason": (
                    "Excluded from round one as a bulk administrative request; only non-answers "
                    "linked to a material observed matter are promoted."
                ),
                "supporting_source_ids": sorted(
                    {str(unit.get("source_id")) for unit in generic_non_answers}
                ),
            }
        )
    return candidates, excluded


def _round_two_candidates(
    index: ObservationIndex,
    round_one_questions: list[JsonObject],
    round_one_answers: list[JsonObject],
) -> tuple[list[QuestionCandidate], list[JsonObject]]:
    candidates, excluded = _answer_followups(round_one_questions, round_one_answers)
    for candidate in (
        _company_group_candidate(index),
        _contract_version_candidate(index),
        _workforce_candidate(index),
        _property_vision_candidate(index),
        _debt_candidate(index, 2),
        _missing_reference_candidate(index, 2),
        _tax_candidate(index, 2),
        _consent_candidate(index, 2),
        _unsupported_financial_candidate(index, 2),
        _calculation_warning_candidate(index, 2),
        _unreadable_candidate(index, 2),
    ):
        if candidate is not None:
            candidates.append(candidate)

    prior_topics = {str(item.get("topic_key")) for item in round_one_questions}
    filtered: list[QuestionCandidate] = []
    for candidate in candidates:
        if candidate.topic_key in prior_topics:
            excluded.append(
                {
                    "candidate_topic": candidate.topic_key,
                    "reason": (
                        "Already asked in round one; it remains in unresolved_questions.md and is "
                        "not duplicated without a narrowing answer."
                    ),
                    "supporting_source_ids": candidate.supporting_source_ids,
                }
            )
            continue
        filtered.append(candidate)
    return filtered, excluded


def _merge_evidence(target: QuestionCandidate, duplicate: QuestionCandidate) -> None:
    seen = {
        (
            tuple(str(item) for item in evidence.get("source_ids", [])),
            tuple(str(item) for item in evidence.get("unit_ids", [])),
            str(evidence.get("summary", "")),
        )
        for evidence in target.supporting_evidence
    }
    for evidence in duplicate.supporting_evidence:
        key = (
            tuple(str(item) for item in evidence.get("source_ids", [])),
            tuple(str(item) for item in evidence.get("unit_ids", [])),
            str(evidence.get("summary", "")),
        )
        if key not in seen:
            target.supporting_evidence.append(evidence)
            seen.add(key)


def select_questions(
    candidates: list[QuestionCandidate],
    excluded: list[JsonObject],
    *,
    round_number: int,
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Suppress duplicates, rank by materiality and enforce the round limit."""

    unique: dict[str, QuestionCandidate] = {}
    question_texts: dict[str, str] = {}
    for candidate in candidates:
        normalized_text = " ".join(candidate.exact_question.casefold().split())
        if candidate.topic_key in unique:
            _merge_evidence(unique[candidate.topic_key], candidate)
            excluded.append(
                {
                    "candidate_topic": candidate.topic_key,
                    "reason": "Duplicate topic merged into the higher-priority supported question.",
                    "supporting_source_ids": candidate.supporting_source_ids,
                }
            )
            continue
        if normalized_text in question_texts:
            excluded.append(
                {
                    "candidate_topic": candidate.topic_key,
                    "reason": (
                        "Duplicate wording suppressed in favour of "
                        f"{question_texts[normalized_text]}."
                    ),
                    "supporting_source_ids": candidate.supporting_source_ids,
                }
            )
            continue
        unique[candidate.topic_key] = candidate
        question_texts[normalized_text] = candidate.topic_key

    ranked = sorted(
        unique.values(),
        key=lambda item: (
            -item.score,
            _PRIORITY_ORDER.get(item.priority, 99),
            item.topic_key,
        ),
    )
    limit = ROUND_LIMITS[round_number]
    selected = ranked[:limit]
    for candidate in ranked[limit:]:
        excluded.append(
            {
                "candidate_topic": candidate.topic_key,
                "reason": (
                    f"Excluded by round-{round_number} prioritisation limit of {limit}; lower "
                    "materiality than the selected candidates."
                ),
                "supporting_source_ids": candidate.supporting_source_ids,
            }
        )
    prefix = f"INT-R{round_number}"
    questions = [
        candidate.as_question(f"{prefix}-{number:03d}")
        for number, candidate in enumerate(selected, start=1)
    ]
    return questions, excluded


def generate_candidates(
    index: ObservationIndex,
    *,
    round_number: int,
    round_one_questions: list[JsonObject] | None = None,
    round_one_answers: list[JsonObject] | None = None,
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Generate and prioritize one round from actual observations and prior answers."""

    if round_number == 1:
        candidates, excluded = _round_one_candidates(index)
    else:
        candidates, excluded = _round_two_candidates(
            index,
            round_one_questions or [],
            round_one_answers or [],
        )
    return select_questions(candidates, excluded, round_number=round_number)


def question_support_is_valid(question: JsonObject) -> bool:
    """Return whether a question has source evidence or an essential structured gap."""

    source_ids = question.get("supporting_source_ids")
    if isinstance(source_ids, list) and any(str(item) for item in source_ids):
        return True
    gap = question.get("structured_gap")
    return isinstance(gap, dict) and gap.get("gap_type") == "essential_transaction_context"


def question_fingerprint(question: JsonObject) -> tuple[Any, ...]:
    """Expose a stable semantic fingerprint for regression tests and audits."""

    return (
        question.get("topic_key"),
        " ".join(str(question.get("exact_question", "")).casefold().split()),
        tuple(str(item) for item in question.get("supporting_source_ids", [])),
    )
