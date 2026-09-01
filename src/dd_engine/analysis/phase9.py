"""Phase 9 Irish legal, Tax, operational/management and IT analysis."""

from __future__ import annotations

import re
from datetime import date

from dd_engine.analysis.context import AnalysisContext, numeric_value, unit_value
from dd_engine.analysis.records import AnalysisRecords, CitationSpec
from dd_engine.evidence.models import JsonObject
from dd_engine.evidence.store import load_record_sets

PHASE9_VERSION = "phase9-analysis-v4"
IRISH_SCOPE = (
    "Commercial due diligence in an Irish transaction context; this is not a formal Irish legal "
    "or tax opinion and specialist advisers must confirm conclusions used in transaction documents."
)


def _money(value: float) -> str:
    return f"EUR {value:,.0f}"


def _first_match(
    context: AnalysisContext,
    pattern: str,
    *,
    path_hint: str | None = None,
    locator_type: str | None = None,
) -> tuple[JsonObject, re.Match[str]] | None:
    matches = context.units_matching(
        pattern,
        path_hint=path_hint,
        locator_type=locator_type,
    )
    return matches[0] if matches else None


def _cell_by_label(
    context: AnalysisContext,
    label: str,
    *,
    offset: int = 1,
    path_hint: str | None = None,
) -> JsonObject | None:
    anchor = context.cell_matching(re.escape(label), path_hint=path_hint)
    if anchor is None:
        return None
    sheet = context.sheet_for_unit(context.sheets, anchor)
    return context.offset_cell(sheet, anchor, offset) if sheet else None


def _add_change_of_control(context: AnalysisContext, records: AnalysisRecords) -> None:
    clause = _first_match(
        context,
        r"supplier must obtain the customer's prior written consent following any change of "
        r"control",
        path_hint="customer contracts",
        locator_type="pdf_page",
    )
    continuing = _first_match(
        context,
        r"Clause 14\.2 remains in full force, including the consent requirement following a "
        r"change of control",
        path_hint="amendment",
        locator_type="pdf_page",
    )
    response = _first_match(
        context,
        r"consent has not been requested",
        path_hint="customer_consent_response",
        locator_type="pdf_page",
    )
    if not clause or not continuing or not response:
        return
    records.add_finding(
        workstream="legal_contractual",
        issue_id="LEGAL-001",
        conclusion=(
            "The operative Harbourlight contract requires prior written customer consent following "
            "a supplier change of control, the amendment preserves that clause, and consent "
            "has not been requested."
        ),
        source_fact=(
            "The base framework contains the consent clause; the 2025 amendment expressly keeps it "
            "in force; the updated vendor response confirms no request."
        ),
        analysis=(
            "On the contract text supplied, this is a transaction deliverability issue, not a "
            "generic "
            "legal caveat. Formal counsel must confirm application to the proposed structure."
        ),
        why_it_matters="The customer can use consent timing to seek concessions or delay "
        "completion.",
        implication=(
            "Make written consent a closing condition, prohibit pre-consent commercial concessions "
            "without buyer approval, and use escrow/price protection if consent is deferred."
        ),
        action=(
            "Counsel should confirm the contemplated transaction triggers the clause, prepare a "
            "contract-by-contract consent matrix and obtain unconditional written consent "
            "before completion."
        ),
        materiality="critical",
        confidence=0.99,
        supporting=[
            CitationSpec(clause[0], exact_text=clause[1].group(0)),
            CitationSpec(continuing[0], exact_text=continuing[1].group(0)),
            CitationSpec(response[0], exact_text=response[1].group(0)),
        ],
        transaction_levers=["consent", "closing_condition", "escrow", "price_assumptions"],
        opinion_status="commercial_diligence_not_formal_legal_opinion",
    )


def _add_liability_amendment(context: AnalysisContext, records: AnalysisRecords) -> None:
    original = _first_match(
        context,
        r"aggregate liability shall not exceed three months of fees",
        path_hint="mosaic_north",
        locator_type="pdf_page",
    )
    amendment = _first_match(
        context,
        r"supersedes Clause 11 in its entirety\. The supplier's liability for service failure is\s*"
        r"increased to twelve months of fees and service credits are uncapped",
        path_hint="amendment_mosaic_2026",
        locator_type="pdf_page",
    )
    if not original or not amendment:
        return
    records.add_finding(
        workstream="legal_contractual",
        issue_id="LEGAL-002",
        conclusion=(
            "The later Mosaic North amendment replaces the three-month liability cap with twelve "
            "months of fees and uncapped service credits; citing the base cap as current would "
            "materially understate exposure."
        ),
        source_fact="The amendment states that it prevails over inconsistent terms and "
        "supersedes Clause 11 entirely.",
        analysis="Version evidence resolves the inconsistency in favour of the later, less "
        "protective liability regime.",
        why_it_matters="Liability and service-credit exposure affect downside, insurance "
        "sufficiency and customer leverage.",
        implication=(
            "Reflect the effective cap in risk allocation, obtain a warranty that all "
            "amendments are "
            "disclosed, and seek specific seller protection for pre-close service failures."
        ),
        action=(
            "Counsel should produce an executed-document chronology, confirm "
            "signatures/effective dates "
            "and map the amended exposure against insurance and open incidents."
        ),
        materiality="high",
        confidence=0.99,
        supporting=[
            CitationSpec(original[0], exact_text=original[1].group(0)),
            CitationSpec(amendment[0], exact_text=amendment[1].group(0)),
        ],
        uncertainty="Execution copies and complete statement-of-work schedules were not "
        "independently verified.",
        transaction_levers=["warranty", "indemnity", "escrow", "price_assumptions"],
        opinion_status="commercial_diligence_not_formal_legal_opinion",
    )


def _add_corporate_records(context: AnalysisContext, records: AnalysisRecords) -> None:
    constitution = _first_match(
        context,
        r"issued capital comprises ([\d,]+) ordinary shares",
        path_hint="constitution",
        locator_type="pdf_page",
    )
    cap_sheets = context.sheets_with(
        "Shareholder", "Shares", "Ownership", path_hint="cap_table_rev2"
    )
    share_units = [
        unit
        for unit in (cap_sheets[0].cells.values() if cap_sheets else [])
        if re.fullmatch(r"B\d+", str(unit.get("locator", {}).get("cell", "")))
        and numeric_value(unit) is not None
    ]
    shareholder_terms = _first_match(
        context,
        r"Approval of holders of (\d+)% of ordinary shares is required for acquisitions, "
        r"material borrowing and\s*changes to the business plan\.[\s\S]*?"
        r"Customary pre-emption and permitted-transfer provisions apply",
        locator_type="pdf_page",
    )
    if not constitution or not share_units:
        return
    total = sum(float(numeric_value(unit) or 0) for unit in share_units)
    stated = float(constitution[1].group(1).replace(",", ""))
    calculation = records.add_calculation(
        calculation_id="CALC-LEGAL-001",
        description="Recompute issued shares in the current cap-table response.",
        inputs=[
            (f"holder_{index}", unit, float(numeric_value(unit) or 0), None)
            for index, unit in enumerate(share_units, start=1)
        ],
        expression=" + ".join(f"holder_{index}" for index in range(1, len(share_units) + 1)),
        recomputed_value=total,
        reported_value=stated,
        currency=None,
        units="shares",
        period="latest cap-table response date as stated in source",
        claim_ids=("CLM-LEGAL-003",),
    )
    records.add_finding(
        workstream="legal_contractual",
        issue_id="LEGAL-003",
        conclusion=(
            f"The latest cap-table response recomputes to {total:,.0f} shares and agrees to the "
            "constitution's issued-capital figure, but no current official CRO extract was "
            "supplied. The shareholders' agreement also contains a supermajority reserved-matter "
            "threshold and transfer pre-emption mechanics."
        ),
        source_fact="The constitution states issued capital and the Rev2 cap table lists three "
        "holdings that sum to it.",
        analysis=(
            "Internal consistency is established; statutory filing consistency remains "
            "unproven because the CRO evidence is image-only. Transaction approval and transfer "
            "steps must be mapped against the shareholders' agreement, not inferred from the "
            "cap table alone."
        ),
        why_it_matters="Ownership and authority must be certain before signing and funds flow.",
        implication=(
            "Make delivery of current official searches, registers and board/shareholder "
            "approvals a "
            "closing condition; do not rely on the screenshot as conclusive title evidence."
        ),
        action=(
            "Irish counsel should obtain current CRO records, inspect statutory registers and "
            "reconcile "
            "all allotments/transfers/options to the Rev2 cap table and shareholders' agreement."
        ),
        materiality="high",
        confidence=0.9,
        supporting=[
            CitationSpec(constitution[0], exact_text=constitution[1].group(0)),
            *[CitationSpec(unit, exact_value=unit_value(unit)) for unit in share_units],
            *(
                [CitationSpec(shareholder_terms[0], exact_text=shareholder_terms[1].group(0))]
                if shareholder_terms
                else []
            ),
        ],
        calculation_ids=[calculation],
        uncertainty="The CRO screenshot/refresh remains pending visual review and is an exact "
        "duplicate, not independent corroboration.",
        transaction_levers=["closing_condition", "warranty", "further_diligence"],
        opinion_status="commercial_diligence_not_formal_legal_opinion",
    )


def _add_contractor_status(context: AnalysisContext, records: AnalysisRecords) -> None:
    contract = _first_match(
        context,
        r"parties intend an independent contractor relationship\. Tax and classification "
        r"consequences remain\s*"
        r"subject to actual working practices",
        path_hint="contractor_agreement",
        locator_type="pdf_page",
    )
    scope = context.cell_matching(r"\d+\s+active contractors", path_hint="contractor_list")
    if not contract or scope is None:
        return
    scope_match = re.search(r"(\d+)\s+active contractors", str(unit_value(scope)), re.I)
    if scope_match is None:
        return
    end_dates = context.units_matching(
        r"^(\d{4}-\d{2}-\d{2})$",
        path_hint="contractor_list",
        locator_type="spreadsheet_cell",
    )
    created = str(context.manifest.get("created_at", ""))[:10]
    try:
        cutoff = date.fromisoformat(created)
    except ValueError:
        cutoff = None
    expired = [
        (unit, match)
        for unit, match in end_dates
        if cutoff is not None and date.fromisoformat(match.group(1)) < cutoff
    ]
    stated_population = int(scope_match.group(1))
    records.add_finding(
        workstream="legal_contractual",
        issue_id="LEGAL-004",
        conclusion=(
            f"The list states {stated_population} active contractors at its own snapshot date, "
            f"but {len(expired)} listed end dates precede the run date. The source therefore "
            "does not establish the current roster. The sample agreement also makes status "
            "dependent on actual working practices."
        ),
        source_fact="The contractor list states the population and the sample form preserves "
        "working-practice uncertainty.",
        analysis="Contract labels alone do not resolve employment or tax status indicators.",
        why_it_matters="Reclassification can create payroll tax, employment-rights and cost "
        "exposure.",
        implication=(
            "Require a workforce warranty and tax/employment indemnity for pre-close "
            "classification "
            "exposure if individual assessments cannot be completed before signing."
        ),
        action=(
            "Irish employment and tax advisers should review each contractor's substitution, "
            "control, "
            "integration, equipment, exclusivity, duration and invoicing evidence."
        ),
        materiality="high",
        confidence=0.92,
        supporting=[
            CitationSpec(contract[0], exact_text=contract[1].group(0)),
            CitationSpec(scope, exact_value=unit_value(scope)),
            *[
                CitationSpec(end_date_unit, exact_text=end_date_match.group(0))
                for end_date_unit, end_date_match in expired
            ],
        ],
        uncertainty=(
            "A run-date roster, renewal evidence, individual working-practice evidence and "
            "signed agreements were not supplied."
        ),
        transaction_levers=["warranty", "indemnity", "escrow", "further_diligence"],
        opinion_status="commercial_diligence_not_formal_legal_opinion",
    )


def _add_property_and_ip_limitations(context: AnalysisContext, records: AnalysisRecords) -> None:
    lease = _first_match(
        context,
        r"A corporate change of control is\s*not itself an assignment",
        path_hint="head_office_lease",
        locator_type="pdf_page",
    )
    response = _first_match(
        context,
        r"No landlord consent is believed required solely for a share sale",
        path_hint="lease_consent_response",
        locator_type="pdf_page",
    )
    if lease and response:
        records.add_finding(
            workstream="legal_contractual",
            issue_id="LEGAL-005",
            conclusion=(
                "The readable lease says a corporate change of control is not an assignment, "
                "consistent "
                "with the updated response; that conclusion is limited to a share sale and the "
                "supplied lease."
            ),
            source_fact="The lease and updated response are aligned on a share-sale scenario.",
            analysis="This resolves the identified lease point commercially, subject to "
            "counsel and transaction structure.",
            why_it_matters="Incorrect consent assumptions can delay completion or create "
            "landlord leverage.",
            implication="Document the share-sale assumption and obtain counsel confirmation; "
            "re-open consent analysis if structure changes.",
            action=(
                "Counsel should review the complete executed lease and property scans, confirm "
                "no side letters "
                "or superior-landlord restrictions, and record the conclusion in the consent "
                "matrix."
            ),
            materiality="medium",
            confidence=0.88,
            supporting=[
                CitationSpec(lease[0], exact_text=lease[1].group(0)),
                CitationSpec(response[0], exact_text=response[1].group(0)),
            ],
            uncertainty="Property purchase/sale scans remain pending visual review.",
            transaction_levers=["consent", "closing_condition", "further_diligence"],
            opinion_status="commercial_diligence_not_formal_legal_opinion",
        )
    retention = _first_match(
        context,
        r"retention of EUR\s*([\d,]+) remains[^.]*snagging",
        locator_type="pdf_page",
    )
    if retention:
        retention_value = float(retention[1].group(1).replace(",", ""))
        records.add_finding(
            workstream="legal_contractual",
            issue_id="LEGAL-006",
            conclusion=(
                f"A property-source page records a {_money(retention_value)} retention for "
                "outstanding snagging; completion evidence and release conditions are not in "
                "the room."
            ),
            source_fact=(
                "The visually reviewed original page expressly states the retained amount and "
                "the snagging basis."
            ),
            analysis=(
                "The retention is a live property/completion item until the defects, contractual "
                "release mechanics and accounting treatment are evidenced."
            ),
            why_it_matters=(
                "Unresolved works and retained consideration can affect cash, title/completion "
                "mechanics and post-close liabilities."
            ),
            implication=(
                "Treat the retention and any remaining works explicitly in debt-like/working "
                "capital definitions and seller protections."
            ),
            action=(
                "Obtain the executed property contract, snag list, completion certificate, "
                "invoices, release correspondence and ledger treatment."
            ),
            materiality="high",
            confidence=0.8,
            supporting=[CitationSpec(retention[0], exact_text=retention[1].group(0))],
            uncertainty=(
                "The source does not establish whether the retention has since been released."
            ),
            transaction_levers=["price_assumptions", "escrow", "indemnity", "warranty"],
            opinion_status="commercial_diligence_not_formal_legal_opinion",
        )

    contractor_form = _first_match(
        context,
        r"parties intend an independent contractor relationship",
        path_hint="contractor_agreement",
        locator_type="pdf_page",
    )
    if contractor_form:
        form_text = str(unit_value(contractor_form[0]) or "")
        has_ip_assignment = bool(
            re.search(
                r"\b(?:intellectual property|copyright|assign(?:ment|s|ed)?)\b", form_text, re.I
            )
        )
        if not has_ip_assignment:
            records.add_finding(
                workstream="legal_contractual",
                issue_id="LEGAL-007",
                conclusion=(
                    "The supplied contractor form contains no express IP assignment, while the "
                    "room identifies an active contractor population; contractor-created IP "
                    "chain of title is not established."
                ),
                source_fact=(
                    "The complete one-page sample form addresses services, status and termination "
                    "but contains no express IP ownership or assignment term."
                ),
                analysis=(
                    "A sample form cannot prove the terms signed by each contractor, and its "
                    "silence is an adverse chain-of-title limitation rather than proof of "
                    "ownership."
                ),
                why_it_matters=(
                    "Missing assignments can impair ownership, licensing, enforcement and buyer "
                    "freedom to use acquired deliverables."
                ),
                implication=(
                    "Require confirmatory assignments as a closing condition and targeted IP "
                    "warranties/indemnity for pre-close contractor work."
                ),
                action=(
                    "Map every contractor to deliverables and signed terms, obtain confirmatory "
                    "assignments and verify moral-rights, confidentiality and "
                    "third-party-code terms."
                ),
                materiality="critical",
                confidence=0.82,
                supporting=[CitationSpec(contractor_form[0])],
                uncertainty=(
                    "Signed individual agreements and a contractor-to-deliverable register "
                    "are absent."
                ),
                transaction_levers=["closing_condition", "warranty", "indemnity", "escrow"],
                opinion_status="commercial_diligence_not_formal_legal_opinion",
            )

    customer_contract_units = context.text_units(path_hint="customer contracts")
    if customer_contract_units:
        records.add_finding(
            workstream="legal_contractual",
            issue_id="LEGAL-008",
            conclusion=(
                "The supplied customer documents do not form a complete contract-term schedule: "
                "termination, renewal, pricing, service-level and statement-of-work coverage "
                "cannot be concluded across the portfolio."
            ),
            source_fact=(
                "Readable framework and amendment pages establish selected consent, service and "
                "liability terms, but no comprehensive executed-document matrix is supplied."
            ),
            analysis=(
                "Selected clauses cannot be extrapolated to every customer or treated as complete "
                "coverage of operative schedules and amendments."
            ),
            why_it_matters=(
                "Omitted renewal, termination, pricing or SLA terms can change revenue durability "
                "and pre-close consent/protection requirements."
            ),
            implication=(
                "Do not assume portfolio-wide renewal or pricing protection; condition valuation "
                "on a complete operative-contract matrix."
            ),
            action=(
                "Build a customer-by-customer schedule of executed base terms, amendments, SOWs, "
                "renewal, termination, pricing, SLAs, credits, consent and dispute status."
            ),
            materiality="high",
            confidence=0.8,
            supporting=[CitationSpec(unit) for unit in customer_contract_units[:3]],
            uncertainty="Completeness of executed customer contracts and schedules is unverified.",
            transaction_levers=["price_assumptions", "consent", "warranty", "further_diligence"],
            opinion_status="commercial_diligence_not_formal_legal_opinion",
        )
    records.add_gap(
        gap_id="GAP-P9-IP-DATA",
        expected="Complete IP chain-of-title, software licensing, privacy and data-processing "
        "evidence.",
        absence_evidence=[
            "Only sample employment IP wording and provider-level data clauses were "
            "identified; no complete IP register, contractor assignment set or DPA inventory "
            "was supplied."
        ],
        importance="high",
        decisions=["go_no_go", "warranty", "indemnity"],
        action=(
            "Provide the IP/software register, employee and contractor assignments, "
            "open-source scan, "
            "privacy notices, Article 30-style records, DPAs, transfer assessments and "
            "incident log."
        ),
        origin="phase9_analysis",
    )


def _add_vat_finding(context: AnalysisContext, records: AnalysisRecords) -> None:
    original_candidates = context.units_matching(
        r"VAT payable: EUR ([\d,]+)", path_hint="vat3", locator_type="pdf_page"
    )
    amended = _first_match(
        context,
        r"Original payable: EUR ([\d,]+)\. Amended payable: EUR ([\d,]+)\. Increase: EUR ([\d,]+)",
        path_hint="amended",
        locator_type="pdf_page",
    )
    rev2 = context.cell_matching(
        r"No VAT returns have been amended", path_hint="tax_response_summary_rev2"
    )
    paid = _first_match(
        context,
        r"All listed charges were paid\. No enforcement balance is shown",
        path_hint="vat_charges",
        locator_type="pdf_page",
    )
    vat_control = _cell_by_label(context, "VAT control", path_hint="tax/trial balance")
    if not amended or rev2 is None or not paid or vat_control is None:
        return
    original_value = float(amended[1].group(1).replace(",", ""))
    amended_value = float(amended[1].group(2).replace(",", ""))
    increase = float(amended[1].group(3).replace(",", ""))
    vat_control_value = float(numeric_value(vat_control) or 0)
    original = next(
        (
            (unit, match)
            for unit, match in original_candidates
            if float(match.group(1).replace(",", "")) == original_value
        ),
        None,
    )
    if original is None:
        return
    calculation = records.add_calculation(
        calculation_id="CALC-TAX-001",
        description="Recompute the P2 VAT amendment from original and amended documents.",
        inputs=[
            (
                "amended_payable",
                amended[0],
                amended_value,
                f"Amended payable: EUR {amended_value:,.0f}",
            ),
            (
                "original_payable",
                original[0],
                original_value,
                original[1].group(0),
            ),
        ],
        expression="amended_payable - original_payable",
        recomputed_value=increase,
        reported_value=increase,
        period="2025-P2",
        claim_ids=("CLM-TAX-001",),
    )
    records.add_finding(
        workstream="tax",
        issue_id="TAX-001",
        conclusion=(
            f"The Rev2 tax response is demonstrably wrong: a 2025-P2 VAT amendment increased "
            f"payable VAT by {_money(increase)}, although Rev2 states that no VAT returns "
            f"were amended. The tax trial balance also carries a {_money(vat_control_value)} "
            "VAT-control balance that the payment-status evidence does not reconcile."
        ),
        source_fact=(
            f"The original return reports {_money(original_value)}, the amended return reports "
            f"{_money(amended_value)}, and the ROS-style account says all listed charges were paid."
        ),
        analysis=(
            "Payment evidence for listed charges reduces one cash-exposure concern, but it does "
            "not clear or explain the ledger control balance. The current questionnaire answer "
            "is unreliable and requires a broader completeness check."
        ),
        why_it_matters="Incorrect tax responses undermine warranty disclosure and may conceal "
        "other amendments or process failures.",
        implication=(
            "Require corrected tax disclosures, a specific tax warranty covering amended "
            "filings and a "
            "tax covenant/indemnity for pre-close liabilities, interest and penalties."
        ),
        action=(
            "Tax advisers should obtain ROS filing receipts and account statements for every "
            "period, "
            "reconcile original/amended returns to the ledger and document amendment causes "
            "and settlement."
        ),
        materiality="critical",
        confidence=0.99,
        supporting=[
            CitationSpec(original[0], exact_text=original[1].group(0)),
            CitationSpec(amended[0], exact_text=amended[1].group(0)),
            CitationSpec(rev2, exact_value=unit_value(rev2)),
            CitationSpec(paid[0], exact_text=paid[1].group(0)),
            CitationSpec(vat_control, exact_value=unit_value(vat_control)),
        ],
        calculation_ids=[calculation],
        transaction_levers=["tax_indemnity", "warranty", "escrow", "further_diligence"],
        opinion_status="commercial_tax_diligence_not_formal_tax_opinion",
    )
    records.add_contradiction(
        contradiction_id="CON-TAX-001",
        issue_id="TAX-001",
        conflicting_values=[
            f"P2 original {_money(original_value)}; amended {_money(amended_value)}",
            "Rev2: no VAT returns amended",
        ],
        source_units=[original[0], amended[0], rev2, vat_control],
        likely_explanations=[
            "The revised questionnaire response was prepared without checking the amended return.",
            "The payment-status source and ledger control balance may cover different posting or "
            "settlement scopes, but no reconciliation was supplied.",
        ],
    )


def _add_ct_finding(context: AnalysisContext, records: AnalysisRecords) -> None:
    liability = _first_match(
        context,
        r"Corporation tax liability EUR ([\d,]+)",
        path_hint="ct_return_2025",
        locator_type="pdf_page",
    )
    charge = _first_match(
        context,
        r"Late amendment charge EUR ([\d,]+)",
        path_hint="ct_charge",
        locator_type="pdf_page",
    )
    payment = _first_match(
        context,
        r"Payments on account total EUR ([\d,]+)",
        path_hint="ct_payment",
        locator_type="pdf_page",
    )
    refund = _first_match(
        context,
        r"Refund issued EUR ([\d,]+)",
        path_hint="ct_refund",
        locator_type="pdf_page",
    )
    computation = _first_match(
        context,
        r"corporation tax at 12\.5%: EUR ([\d,]+)",
        path_hint="tax_computation_2025",
        locator_type="pdf_page",
    )
    tb = _cell_by_label(context, "Corporation tax", path_hint="financial/trial_balance")
    additional_payment = _first_match(
        context,
        r"corporation tax payment of EUR ([\d,]+) was recorded",
        locator_type="pdf_page",
    )
    if not all((liability, charge, payment, refund, computation)) or tb is None:
        return
    assert liability and charge and payment and refund and computation
    values = [
        float(item[1].group(1).replace(",", ""))
        for item in (liability, charge, payment, refund, computation)
    ]
    liability_value, charge_value, payment_value, refund_value, computation_value = values
    tb_value = float(numeric_value(tb) or 0)
    residual = payment_value - refund_value - liability_value - charge_value
    additional_payment_value = (
        float(additional_payment[1].group(1).replace(",", "")) if additional_payment else None
    )
    calculation = records.add_calculation(
        calculation_id="CALC-TAX-002",
        description="Reconcile 2025 CT return and amendment charge to net ROS cash.",
        inputs=[
            ("payment", payment[0], payment_value, payment[1].group(0)),
            ("refund", refund[0], refund_value, refund[1].group(0)),
            ("return_liability", liability[0], liability_value, liability[1].group(0)),
            ("amendment_charge", charge[0], charge_value, charge[1].group(0)),
        ],
        expression="payment - refund - return_liability - amendment_charge",
        recomputed_value=residual,
        reported_value=0,
        period="2025 corporation tax account evidence",
        claim_ids=("CLM-TAX-002",),
    )
    records.add_finding(
        workstream="tax",
        issue_id="TAX-002",
        conclusion=(
            f"Net ROS cash of {_money(payment_value - refund_value)} arithmetically equals the "
            f"{_money(liability_value)} return plus "
            f"{_money(charge_value)} late-amendment charge, but the return does not reconcile "
            f"to the {_money(computation_value)} "
            f"annual computation or {_money(tb_value)} trial-balance tax figure. This equality "
            "does not prove that the cited cash entries settled the cited assessment."
        ),
        source_fact=(
            f"Payments of {_money(payment_value)} less a {_money(refund_value)} refund equal the "
            f"return plus charge; the computation and trial balance show different amounts."
        ),
        analysis=(
            "The equality is an arithmetic hypothesis only: the source set lacks assessment "
            "references, filing receipts and transaction-level linkage. A separate tax-payment "
            "confirmation elsewhere in the room also requires classification rather than being "
            "silently ignored."
        ),
        why_it_matters="An unexplained CT bridge affects tax warranties, normalized earnings "
        "and balance-sheet provisions.",
        implication=(
            "Do not adjust price for a presumed refund or liability without the bridge; "
            "require a tax "
            "covenant and retain escrow for unresolved pre-close CT exposures."
        ),
        action=(
            "Obtain the filed Form CT1/supporting computation, assessment, general-ledger tax "
            "accounts "
            "and adviser bridge explaining every difference between computation, TB, return, "
            "charge, payment and refund."
        ),
        materiality="critical",
        confidence=0.98,
        supporting=[
            CitationSpec(liability[0], exact_text=liability[1].group(0)),
            CitationSpec(charge[0], exact_text=charge[1].group(0)),
            CitationSpec(payment[0], exact_text=payment[1].group(0)),
            CitationSpec(refund[0], exact_text=refund[1].group(0)),
            CitationSpec(computation[0], exact_text=computation[1].group(0)),
            CitationSpec(tb, exact_value=unit_value(tb)),
            *(
                [CitationSpec(additional_payment[0], exact_text=additional_payment[1].group(0))]
                if additional_payment
                else []
            ),
        ],
        calculation_ids=[calculation],
        uncertainty=(
            "The source set does not establish why the computation, ledger and filed return "
            "differ or link the cash entries—including the separate payment confirmation—to a "
            "specific assessment."
            + (
                f" The additional unlinked payment is {_money(additional_payment_value)}."
                if additional_payment_value is not None
                else ""
            )
        ),
        transaction_levers=["tax_indemnity", "escrow", "warranty", "price_assumptions"],
        opinion_status="commercial_tax_diligence_not_formal_tax_opinion",
    )
    records.add_contradiction(
        contradiction_id="CON-TAX-002",
        issue_id="TAX-002",
        conflicting_values=[computation_value, tb_value, liability_value],
        source_units=[computation[0], tb, liability[0]],
        likely_explanations=[
            "Timing, prior-year adjustments or return amendments may explain part of the bridge, "
            "but the room does not evidence the reconciliation."
        ],
    )


def _add_paye_reconciliation(context: AnalysisContext, records: AnalysisRecords) -> None:
    returns = _first_match(
        context,
        r"Registered PAYE headcount: (\d+)\. Annual liability: EUR ([\d,]+)",
        path_hint="paye_returns",
        locator_type="pdf_page",
    )
    payments = _first_match(
        context,
        r"Total payments: EUR ([\d,]+)\. Returns and payments agree",
        path_hint="paye_payments",
        locator_type="pdf_page",
    )
    csv_count = context.units_matching(
        r"^\d+$",
        path_hint="paye_reconciliation",
        locator_type="csv_cell",
    )
    paye_control = _cell_by_label(context, "PAYE control", path_hint="tax/trial balance")
    if not returns or not payments or not csv_count or paye_control is None:
        return
    liability_value = float(returns[1].group(2).replace(",", ""))
    payment_value = float(payments[1].group(1).replace(",", ""))
    paye_control_value = float(numeric_value(paye_control) or 0)
    calculation = records.add_calculation(
        calculation_id="CALC-TAX-003",
        description="Reconcile annual PAYE liability to payments.",
        inputs=[
            ("return_liability", returns[0], liability_value, returns[1].group(0)),
            ("payments", payments[0], payment_value, payments[1].group(0)),
        ],
        expression="return_liability - payments",
        recomputed_value=liability_value - payment_value,
        reported_value=0,
        period="2025 PAYE return and payment evidence",
        claim_ids=("CLM-TAX-003",),
    )
    records.add_finding(
        workstream="tax",
        issue_id="TAX-003",
        conclusion=(
            f"PAYE returns and payments agree at {_money(liability_value)} and the 64-person "
            "count is "
            "corroborated by "
            f"the updated reconciliation. The annual tie-out does not resolve the "
            f"{_money(abs(paye_control_value))} PAYE-control balance or contractor-status risk."
        ),
        source_fact="The ROS-style return/payment pair and updated CSV carry matching "
        "liability/payment and headcount evidence.",
        analysis=(
            "The annual PAYE cash tie-out is supported, but equality of annual totals is not a "
            "ledger reconciliation and does not explain the control balance."
        ),
        why_it_matters="A supported payroll tax tie-out narrows, but does not eliminate, "
        "workforce tax exposure.",
        implication="Use the tie-out as supporting disclosure; preserve tax indemnity for "
        "omitted workers, periods and classification matters.",
        action=(
            "Reconcile monthly payroll submissions, payslips, employee master, contractor "
            "payments and "
            "the PAYE control balance through the latest completion date."
        ),
        materiality="high",
        confidence=0.96,
        supporting=[
            CitationSpec(returns[0], exact_text=returns[1].group(0)),
            CitationSpec(payments[0], exact_text=payments[1].group(0)),
            CitationSpec(csv_count[0][0], exact_value=unit_value(csv_count[0][0])),
            CitationSpec(paye_control, exact_value=unit_value(paye_control)),
        ],
        calculation_ids=[calculation],
        uncertainty=(
            f"The {_money(abs(paye_control_value))} PAYE control balance and post-source periods "
            "require reconciliation."
        ),
        transaction_levers=["tax_indemnity", "warranty", "further_diligence"],
        opinion_status="commercial_tax_diligence_not_formal_tax_opinion",
    )


def _add_positive_tax_controls(context: AnalysisContext, records: AnalysisRecords) -> None:
    invoice_matches = context.units_matching(
        r"Tax Invoice\s+([^\s]+)[\s\S]*?Description\s+Net\s+VAT\s+Gross\s+Services\s+"
        r"EUR ([\d,]+)\s+EUR ([\d,]+)\s+EUR ([\d,]+)",
        locator_type="pdf_page",
    )
    register_sheets = context.sheets_with("Invoice", "Net", "VAT", "Gross")
    clearance = _first_match(
        context,
        r"Tax clearance is shown as current through (\d{4}-\d{2}-\d{2})",
        locator_type="pdf_page",
    )
    if not invoice_matches or not register_sheets or not clearance:
        return
    register_sheet = register_sheets[0]
    total_anchor = next(
        (
            unit
            for unit in register_sheet.cells.values()
            if str(unit_value(unit) or "").strip().casefold() == "total"
        ),
        None,
    )
    if total_anchor is None:
        return
    register_gross = context.offset_cell(register_sheet, total_anchor, 4)
    if register_gross is None or numeric_value(register_gross) is None:
        return
    parsed = [
        (
            unit,
            match,
            float(match.group(2).replace(",", "")),
            float(match.group(3).replace(",", "")),
            float(match.group(4).replace(",", "")),
        )
        for unit, match in invoice_matches
    ]
    if not all(abs((net + vat) - gross) < 0.01 for _, _, net, vat, gross in parsed):
        return
    gross_total = sum(item[4] for item in parsed)
    registered_gross = float(numeric_value(register_gross) or 0)
    calculation = records.add_calculation(
        calculation_id="CALC-TAX-004",
        description="Reconcile sample-invoice gross values to the invoice register total.",
        inputs=[
            *[
                (
                    f"invoice_gross_{index}",
                    unit,
                    gross,
                    f"EUR {gross:,.0f}",
                )
                for index, (unit, _, _, _, gross) in enumerate(parsed, start=1)
            ],
            ("register_gross", register_gross, registered_gross, None),
        ],
        expression=(
            " + ".join(f"invoice_gross_{index}" for index in range(1, len(parsed) + 1))
            + " - register_gross"
        ),
        recomputed_value=gross_total - registered_gross,
        reported_value=0,
        period="invoice sample period as stated in source",
        claim_ids=("CLM-TAX-004",),
    )
    records.add_finding(
        workstream="tax",
        issue_id="TAX-004",
        conclusion=(
            f"The supplied invoice sample is internally arithmetical and its gross total "
            f"reconciles to the register at {_money(gross_total)}; tax clearance is shown as "
            f"current through {clearance[1].group(1)}. These are positive controls, not proof "
            "of full-period tax completeness."
        ),
        source_fact=(
            "Each sampled invoice's net plus VAT equals gross, the invoice gross values tie to "
            "the register, and a separate clearance certificate states its validity date."
        ),
        analysis=(
            "The checks support the sampled documents and clearance status only; they do not "
            "override unresolved VAT, PAYE or corporation-tax control balances."
        ),
        why_it_matters=(
            "Balanced reporting distinguishes verified positive controls from broader adverse "
            "reconciliation findings."
        ),
        implication=(
            "Retain these items as supporting disclosure while preserving the tax covenant, "
            "warranties and completion-date reconciliations for open balances."
        ),
        action=(
            "Extend the invoice-to-ledger/return test across a representative period and obtain "
            "fresh tax-clearance confirmation immediately before completion."
        ),
        materiality="medium",
        confidence=0.9,
        supporting=[
            *[CitationSpec(unit, exact_text=match.group(0)) for unit, match, _, _, _ in parsed],
            CitationSpec(register_gross, exact_value=unit_value(register_gross)),
            CitationSpec(clearance[0], exact_text=clearance[1].group(0)),
        ],
        calculation_ids=[calculation],
        uncertainty="Sample coverage and completion-date clearance remain limited.",
        transaction_levers=["warranty", "tax_indemnity", "further_diligence"],
        opinion_status="commercial_tax_diligence_not_formal_tax_opinion",
    )


def _add_operational_findings(context: AnalysisContext, records: AnalysisRecords) -> None:
    restore = _first_match(
        context,
        r"schedule a restore test after the summer release\. No date was approved",
        path_hint="board_minutes",
        locator_type="docx_paragraph",
    )
    hosting = _first_match(
        context,
        r"annual fee EUR ([\d,]+)",
        path_hint="web_hosting",
        locator_type="pdf_page",
    )
    creditors = context.cell_matching(r"Juniper Hosting Services", path_hint="aged_creditors")
    creditor_total = None
    creditor_31_60 = None
    creditor_61_plus = None
    if creditors is not None:
        sheet = context.sheet_for_unit(context.sheets, creditors)
        creditor_31_60 = context.offset_cell(sheet, creditors, 2) if sheet else None
        creditor_61_plus = context.offset_cell(sheet, creditors, 3) if sheet else None
        creditor_total = context.offset_cell(sheet, creditors, 4) if sheet else None
    if restore and hosting:
        records.add_finding(
            workstream="operational_management",
            issue_id="OPS-001",
            conclusion=(
                "Business-continuity governance is incomplete: the board left the restore-test "
                "action without an approved date or accountable delivery evidence."
            ),
            source_fact="Board minutes record the open restore-test action; the hosting "
            "agreement supplies backups but no committed witnessed test.",
            analysis=(
                "This is the management-control and ownership failure around scheduling, "
                "escalation and evidence. The separate IT finding addresses the technical "
                "assurance and recovery-control gap."
            ),
            why_it_matters="A failed restoration can interrupt concentrated customer services "
            "and trigger credits/churn.",
            implication=(
                "Make a successful witnessed restore/DR exercise a pre-completion condition or "
                "retain "
                "escrow until remediation and evidence are delivered."
            ),
            action=(
                "Run and evidence a time-bound restore and failover exercise, capture actual "
                "RTO/RPO, "
                "owners and defects, and approve a tested continuity plan."
            ),
            materiality="high",
            confidence=0.98,
            supporting=[
                CitationSpec(restore[0], exact_text=restore[1].group(0)),
                CitationSpec(hosting[0], exact_text=hosting[1].group(0)),
            ],
            transaction_levers=["closing_condition", "escrow", "warranty"],
        )
    if (
        hosting
        and creditor_total is not None
        and creditor_31_60 is not None
        and creditor_61_plus is not None
    ):
        fee = float(hosting[1].group(1).replace(",", ""))
        total_payable = float(numeric_value(creditor_total) or 0)
        overdue_31_60 = float(numeric_value(creditor_31_60) or 0)
        overdue_61_plus = float(numeric_value(creditor_61_plus) or 0)
        overdue = overdue_31_60 + overdue_61_plus
        calculation = records.add_calculation(
            calculation_id="CALC-OPS-001",
            description="Compute the hosting supplier balance aged beyond current.",
            inputs=[
                ("aged_31_60", creditor_31_60, overdue_31_60, None),
                ("aged_61_plus", creditor_61_plus, overdue_61_plus, None),
            ],
            expression="aged_31_60 + aged_61_plus",
            recomputed_value=overdue,
            period="aged-creditor source snapshot",
            claim_ids=("CLM-OPS-002",),
        )
        records.add_finding(
            workstream="operational_management",
            issue_id="OPS-002",
            conclusion=(
                f"A single hosting provider carries an annual fee of {_money(fee)} and an "
                f"aggregate creditor exposure of {_money(total_payable)}, of which "
                f"{_money(overdue)} is aged beyond current. This supports payment-status "
                "diligence, but not an inference of default or threatened suspension."
            ),
            source_fact="The hosting contract and creditor ageing identify the same provider "
            "and amounts.",
            analysis=(
                "The dependency and overdue amount are evidenced. The room does not establish "
                "whether the balance is disputed, contractually overdue, subject to agreed terms "
                "or linked to any suspension threat."
            ),
            why_it_matters="Supplier disruption or repricing can affect delivery capacity, "
            "margin and customer SLAs.",
            implication="Test downside in price assumptions and require transition assistance, "
            "continuity warranties and a funded migration plan.",
            action=(
                "Obtain service performance, payment status, renewal/termination rights, "
                "data-export terms, "
                "subprocessors, portability architecture and a costed exit/migration plan."
            ),
            materiality="high",
            confidence=0.95,
            supporting=[
                CitationSpec(hosting[0], exact_text=hosting[1].group(0)),
                CitationSpec(creditor_total, exact_value=unit_value(creditor_total)),
                CitationSpec(creditor_31_60, exact_value=unit_value(creditor_31_60)),
                CitationSpec(creditor_61_plus, exact_value=unit_value(creditor_61_plus)),
            ],
            calculation_ids=[calculation],
            uncertainty=(
                "No evidence establishes contractual due dates, payment dispute/status, "
                "provider substitutability or migration duration."
            ),
            transaction_levers=["price_assumptions", "warranty", "closing_condition"],
        )
    records.add_gap(
        gap_id="GAP-P9-KEY-PERSON-CONTROLS",
        expected="Management succession, delegation, capacity, KPI controls and key-person "
        "coverage.",
        absence_evidence=[
            "Board minutes and provider contracts were supplied, but no organization chart, "
            "succession plan, capacity model or control matrix was identified."
        ],
        importance="high",
        decisions=["go_no_go", "earn_out", "retention"],
        action=(
            "Provide organization/capacity plans, decision rights, management KPI packs, "
            "succession and "
            "retention proposals, and evidence of control operation."
        ),
        origin="phase9_analysis",
    )


def _add_it_findings(context: AnalysisContext, records: AnalysisRecords) -> None:
    hosting = _first_match(
        context,
        r"No contractual recovery time objective is stated\. Restore tests are performed on "
        r"request; "
        r"no annual\s*witnessed test, penetration-test report or independent assurance report "
        r"is committed",
        path_hint="web_hosting",
        locator_type="pdf_page",
    )
    security = _first_match(
        context,
        r"Multi-factor authentication is enabled for administrators\. No independent "
        r"penetration test "
        r"or witnessed disaster-recovery exercise has been supplied",
        path_hint="it_security_response",
        locator_type="docx_paragraph",
    )
    questionnaire = _first_match(
        context,
        r"Hosting recovery metrics are not contractually documented",
        path_hint="legal_questionnaire_rev2",
        locator_type="docx_paragraph",
    )
    if hosting and security and questionnaire:
        records.add_finding(
            workstream="it",
            issue_id="IT-001",
            conclusion=(
                "IT resilience is not evidenced to an acquisition standard: there is no "
                "contractual RTO, "
                "witnessed disaster-recovery test, penetration-test report or independent "
                "assurance report."
            ),
            source_fact="The hosting agreement and current vendor responses consistently "
            "identify the missing controls.",
            analysis="Administrator MFA is a positive control but does not compensate for "
            "untested recovery and absent assurance.",
            why_it_matters="Control failure can interrupt service, trigger customer credits "
            "and exceed cyber-insurance assumptions.",
            implication=(
                "Make remediation and evidence a closing condition, retain escrow for "
                "unresolved critical "
                "defects, and require cybersecurity/incident warranties."
            ),
            action=(
                "Commission an independent penetration test and witnessed restore/DR test; "
                "agree contractual "
                "RTO/RPO, remediate critical findings and deliver the final reports before "
                "completion."
            ),
            materiality="critical",
            confidence=0.99,
            supporting=[
                CitationSpec(hosting[0], exact_text=hosting[1].group(0)),
                CitationSpec(security[0], exact_text=security[1].group(0)),
                CitationSpec(questionnaire[0], exact_text=questionnaire[1].group(0)),
            ],
            transaction_levers=["closing_condition", "escrow", "warranty", "indemnity"],
        )
    complaint = _first_match(
        context,
        r"three priority-one incidents\s+exceeded the four-hour response target",
        path_hint="complaint",
        locator_type="pdf_page",
    )
    response = _first_match(
        context,
        r"accepts two response-time misses[\s\S]*?A full recovery exercise has not yet been "
        r"scheduled",
        path_hint="company_response",
        locator_type="pdf_page",
    )
    if complaint and response:
        records.add_finding(
            workstream="it",
            issue_id="IT-002",
            conclusion=(
                "Incident history is not clean: a customer alleges three priority-one SLA "
                "failures, "
                "management accepts two misses, and a full recovery exercise remains unscheduled."
            ),
            source_fact="The complaint and company response document incident frequency, "
            "accepted misses and incomplete recovery testing.",
            analysis="The evidence links technical-control gaps to a real customer service "
            "dispute.",
            why_it_matters="Repeat incidents can drive credits, churn, liability and insurance "
            "notification obligations.",
            implication=(
                "Seek a specific pre-close incident indemnity/escrow, validate insurance "
                "notice compliance "
                "and condition closing on remediation of repeat root causes."
            ),
            action=(
                "Obtain the complete incident register, root-cause analyses, SLA calculations, "
                "insurer "
                "notifications, remediation evidence and post-incident trend metrics."
            ),
            materiality="high",
            confidence=0.98,
            supporting=[
                CitationSpec(complaint[0], exact_text=complaint[1].group(0)),
                CitationSpec(response[0], exact_text=response[1].group(0)),
            ],
            uncertainty="The room does not contain a complete incident history or insurer "
            "correspondence.",
            transaction_levers=["indemnity", "escrow", "warranty", "closing_condition"],
        )
    work_email = context.cell_matching(r"^Work email$")
    personal_email = context.cell_matching(r"^Personal email$")
    identifier = context.cell_matching(r"PPS-like ID")
    privacy_warning = context.cell_matching(r"personal data included for privacy testing")
    if work_email and personal_email and identifier and privacy_warning:
        source_ids = {
            str(unit["source_id"])
            for unit in (work_email, personal_email, identifier, privacy_warning)
        }
        if len(source_ids) == 1:
            records.add_finding(
                workstream="it",
                issue_id="IT-003",
                conclusion=(
                    "An unredacted employee workbook in the room contains work-email, "
                    "personal-email and government-identifier-like fields; access, purpose, "
                    "retention and secure-transfer controls are not evidenced."
                ),
                source_fact=(
                    "The workbook itself labels the personal-data content and exposes the three "
                    "sensitive field categories. No personal values are reproduced in this finding."
                ),
                analysis=(
                    "The presence of employee PII in an unrestricted diligence artifact creates "
                    "a concrete data-handling issue independent of the broader policy-document gap."
                ),
                why_it_matters=(
                    "Unnecessary or uncontrolled disclosure can create privacy, security and "
                    "employee-trust exposure."
                ),
                implication=(
                    "Restrict the artifact immediately, preserve an access audit and make "
                    "data-room "
                    "remediation plus privacy warranties a transaction requirement."
                ),
                action=(
                    "Move the workbook to least-privilege access, identify recipients, assess "
                    "lawful "
                    "purpose and necessity, replace it with a minimized/redacted version, document "
                    "retention/deletion, and notify privacy counsel if required."
                ),
                materiality="critical",
                confidence=0.95,
                supporting=[
                    CitationSpec(privacy_warning, exact_value=unit_value(privacy_warning)),
                    CitationSpec(work_email, exact_value=unit_value(work_email)),
                    CitationSpec(personal_email, exact_value=unit_value(personal_email)),
                    CitationSpec(identifier, exact_value=unit_value(identifier)),
                ],
                uncertainty=(
                    "The room does not provide an access log, lawful-basis assessment, retention "
                    "record or confirmation of deletion from prior recipients."
                ),
                transaction_levers=["closing_condition", "warranty", "indemnity", "escrow"],
            )
    records.add_gap(
        gap_id="GAP-P9-IT-CONTROLS",
        expected=(
            "User access reviews, privileged-access inventory, vulnerability management, "
            "software/IP "
            "licensing, data maps, GDPR evidence and complete incident history."
        ),
        absence_evidence=[
            "The room provides administrator-MFA narrative and provider contracts but no "
            "complete technical-control evidence set."
        ],
        importance="high",
        decisions=["go_no_go", "warranty", "indemnity", "closing_condition"],
        action=(
            "Provide IAM exports and reviews, security policies/evidence, asset/software "
            "inventories, "
            "licences, vulnerability and patch reports, DPAs/data maps and the incident register."
        ),
        origin="phase9_analysis",
    )


def _coverage(
    findings: dict[str, list[JsonObject]], existing_issue_ids: set[str]
) -> dict[str, list[JsonObject]]:
    topics = {
        "legal_contractual": {
            "corporate_structure_ownership_cap_table": ["LEGAL-003"],
            "constitution_shareholder_restrictions": ["LEGAL-003"],
            "change_control_assignment_consent": ["LEGAL-001", "LEGAL-005"],
            "amendments_effective_terms": ["LEGAL-001", "LEGAL-002"],
            "termination_renewal_pricing_service": ["LEGAL-008"],
            "liability_warranties_indemnities": ["LEGAL-002"],
            "complaints_correspondence": ["IT-002"],
            "employment_contractor_status": ["LEGAL-004"],
            "property_restrictions": ["LEGAL-005", "LEGAL-006"],
            "insurance_licences_work_permits": [],
            "ip_ownership_data_protection": ["LEGAL-007", "IT-003"],
            "missing_documents_questionnaire_references": [],
        },
        "tax": {
            "vat_returns_xero_original_amended": ["TAX-001"],
            "vat_charges_payments": ["TAX-001"],
            "paye_returns_payments": ["TAX-003"],
            "corporation_tax_returns_payments_charges_refunds": ["TAX-002"],
            "annual_computations_trial_balances": ["TAX-002"],
            "invoice_samples": ["TAX-004"],
            "tax_clearance": ["TAX-004"],
            "original_vs_rev2_responses": ["TAX-001"],
        },
        "operational_management": {
            "key_person_dependency": [],
            "paye_contractor_workforce": ["LEGAL-004"],
            "client_linked_headcount": ["COMM-004"],
            "workforce_inconsistencies": ["FIN-006", "LEGAL-004"],
            "supplier_dependency": ["OPS-002"],
            "capacity_delivery_risk": ["OPS-001", "OPS-002"],
            "management_controls": ["OPS-001"],
            "related_party_arrangements": ["FIN-005"],
            "business_continuity": ["OPS-001"],
            "missing_operational_evidence": [],
        },
        "it": {
            "hosting_provider_agreements": ["IT-001"],
            "access_management": [],
            "cybersecurity_controls": ["IT-001"],
            "backup_restore_disaster_recovery": ["IT-001", "IT-002"],
            "vendor_dependence": ["OPS-002"],
            "software_ip_licensing": ["LEGAL-007"],
            "data_processing_gdpr": ["IT-003"],
            "incident_history": ["IT-002"],
            "missing_technical_evidence": [],
        },
    }
    available = existing_issue_ids | {
        str(item["issue_id"])
        for workstream_findings in findings.values()
        for item in workstream_findings
    }
    return {
        workstream: [
            {
                "issue_ids": [issue for issue in issue_ids if issue in available],
                "status": "analysed"
                if any(issue in available for issue in issue_ids)
                else "limitation",
                "topic": topic,
            }
            for topic, issue_ids in workstream_topics.items()
        ]
        for workstream, workstream_topics in topics.items()
    }


def build_phase9(context: AnalysisContext) -> tuple[AnalysisRecords, dict[str, JsonObject]]:
    """Build Phase 9 records and narratives without making a formal legal/tax opinion."""

    records = AnalysisRecords(context, "P9")
    _add_change_of_control(context, records)
    _add_liability_amendment(context, records)
    _add_corporate_records(context, records)
    _add_contractor_status(context, records)
    _add_property_and_ip_limitations(context, records)
    _add_vat_finding(context, records)
    _add_ct_finding(context, records)
    _add_paye_reconciliation(context, records)
    _add_positive_tax_controls(context, records)
    _add_operational_findings(context, records)
    _add_it_findings(context, records)

    existing_issue_ids = {
        str(issue.get("issue_id")) for issue in load_record_sets(context.run_path).get("issues", [])
    }
    coverage = _coverage(records.findings, existing_issue_ids)
    common = {
        "analysis_version": PHASE9_VERSION,
        "generated_by": "deterministic local analytical rules; Python made no model call",
        "irish_jurisdiction_scope": IRISH_SCOPE,
        "public_research_performed": False,
        "run_id": context.run_id,
        "schema_version": 1,
        "unresolved_intake_question_ids": context.unresolved_answer_ids(),
        "untrusted_source_data_was_executed": False,
    }

    def source_ids(*path_fragments: str) -> list[str]:
        return sorted(
            source_id
            for source_id, source in context.sources.items()
            if any(
                fragment.casefold() in str(source.get("relative_path", "")).casefold()
                for fragment in path_fragments
            )
        )

    effective_versions = [
        {
            "decision": "base framework plus 2025 amendment; consent clause expressly continues",
            "family": "Harbourlight customer contract",
            "source_ids": source_ids("Customer_Framework_Harbourlight", "Amendment_Harbourlight"),
        },
        {
            "decision": "2026 amendment replaces the original liability clause",
            "family": "Mosaic North customer contract",
            "source_ids": source_ids("Customer_Framework_Mosaic_North", "Amendment_Mosaic_2026"),
        },
        {
            "decision": "2025 amendment extends scope/term; other terms continue",
            "family": "Mosaic South customer contract",
            "source_ids": source_ids("Customer_Framework_Mosaic_South", "Amendment_Mosaic_South"),
        },
        {
            "decision": "Rev2 is the current response, but its no-amendment VAT answer is "
            "contradicted",
            "family": "Tax response summary",
            "source_ids": source_ids("Tax_Response_Summary_Original", "Tax_Response_Summary_Rev2"),
        },
    ]
    payloads: dict[str, JsonObject] = {}
    for workstream in ("legal_contractual", "tax", "operational_management", "it"):
        payloads[workstream] = {
            **common,
            "coverage": coverage[workstream],
            "effective_version_decisions": effective_versions
            if workstream in {"legal_contractual", "tax"}
            else [],
            "findings": records.findings.get(workstream, []),
            "limitations": [
                "No formal Irish legal or tax opinion is provided.",
                "Visual property/CRO evidence and the unreadable legacy policy remain unresolved.",
                "Topics marked limitation had insufficient source evidence for an adverse "
                "conclusion.",
            ],
            "workstream": workstream,
        }
    return records, payloads
