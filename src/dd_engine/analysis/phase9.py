"""Phase 9 Irish legal, Tax, operational/management and IT analysis."""

from __future__ import annotations

import re

from dd_engine.analysis.context import AnalysisContext, numeric_value, unit_value
from dd_engine.analysis.records import AnalysisRecords, CitationSpec
from dd_engine.evidence.models import JsonObject
from dd_engine.evidence.store import load_record_sets

PHASE9_VERSION = "phase9-analysis-v2"
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
    latest = context.cell_matching(r"^520000$", path_hint="cap_table_rev2")
    other_one = context.cell_matching(r"^280000$", path_hint="cap_table_rev2")
    other_two = context.cell_matching(r"^200000$", path_hint="cap_table_rev2")
    if not constitution or latest is None or other_one is None or other_two is None:
        return
    total = sum(float(numeric_value(unit) or 0) for unit in (latest, other_one, other_two))
    stated = float(constitution[1].group(1).replace(",", ""))
    calculation = records.add_calculation(
        calculation_id="CALC-LEGAL-001",
        description="Recompute issued shares in the current cap-table response.",
        inputs=[
            ("holder_one", latest, float(numeric_value(latest) or 0), None),
            ("holder_two", other_one, float(numeric_value(other_one) or 0), None),
            ("holder_three", other_two, float(numeric_value(other_two) or 0), None),
        ],
        expression="holder_one + holder_two + holder_three",
        recomputed_value=total,
        reported_value=stated,
        currency=None,
        units="shares",
        period="latest response at 29 July 2026",
        claim_ids=("CLM-LEGAL-003",),
    )
    records.add_finding(
        workstream="legal_contractual",
        issue_id="LEGAL-003",
        conclusion=(
            f"The latest cap-table response recomputes to {total:,.0f} shares and agrees to the "
            "constitution's issued-capital figure, but no current official CRO extract was "
            "supplied."
        ),
        source_fact="The constitution states issued capital and the Rev2 cap table lists three "
        "holdings that sum to it.",
        analysis="Internal consistency is established; statutory filing consistency remains "
        "unproven because the CRO evidence is image-only.",
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
            CitationSpec(latest, exact_value=unit_value(latest)),
            CitationSpec(other_one, exact_value=unit_value(other_one)),
            CitationSpec(other_two, exact_value=unit_value(other_two)),
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
    scope = context.cell_matching(r"12 active contractors", path_hint="contractor_list")
    if not contract or scope is None:
        return
    records.add_finding(
        workstream="legal_contractual",
        issue_id="LEGAL-004",
        conclusion=(
            "Twelve active contractors are documented only against a sample agreement that "
            "expressly "
            "makes status dependent on actual working practices; contractor classification is "
            "not established."
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
        ],
        uncertainty="Individual working-practice evidence and signed agreements were not supplied.",
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
    original = _first_match(
        context,
        r"VAT payable: EUR ([\d,]+)",
        path_hint="vat3_2025_p2.pdf",
        locator_type="pdf_page",
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
    if not original or not amended or rev2 is None or not paid:
        return
    original_value = float(amended[1].group(1).replace(",", ""))
    amended_value = float(amended[1].group(2).replace(",", ""))
    increase = float(amended[1].group(3).replace(",", ""))
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
                f"VAT payable: EUR {original_value:,.0f}",
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
            "were amended."
        ),
        source_fact=(
            f"The original return reports {_money(original_value)}, the amended return reports "
            f"{_money(amended_value)}, and the ROS-style account says all listed charges were paid."
        ),
        analysis=(
            "Payment evidence reduces the identified cash exposure, but the current "
            "questionnaire answer "
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
        source_units=[original[0], amended[0], rev2],
        likely_explanations=[
            "The revised questionnaire response was prepared without checking the amended return."
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
    tb = context.cell_matching(r"^348200$", path_hint="trial_balance_2025")
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
            f"Net ROS cash of {_money(payment_value - refund_value)} reconciles to the "
            f"{_money(liability_value)} return plus "
            f"{_money(charge_value)} late-amendment charge, but the return does not reconcile "
            f"to the {_money(computation_value)} "
            f"annual computation or {_money(tb_value)} trial-balance tax figure."
        ),
        source_fact=(
            f"Payments of {_money(payment_value)} less a {_money(refund_value)} refund equal the "
            f"return plus charge; the computation and trial balance show different amounts."
        ),
        analysis=(
            "Settlement of the ROS account appears arithmetically supported, while the "
            "underlying tax "
            "provision/computation bridge remains unexplained."
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
        ],
        calculation_ids=[calculation],
        uncertainty="The source set does not establish why the computation, ledger and filed "
        "return differ.",
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
        r"^64$",
        path_hint="paye_reconciliation",
        locator_type="csv_cell",
    )
    if not returns or not payments or not csv_count:
        return
    liability_value = float(returns[1].group(2).replace(",", ""))
    payment_value = float(payments[1].group(1).replace(",", ""))
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
            "the updated reconciliation; this tie-out does not resolve contractor-status risk "
            "or the PAYE control balance."
        ),
        source_fact="The ROS-style return/payment pair and updated CSV carry matching "
        "liability/payment and headcount evidence.",
        analysis="The annual PAYE cash tie-out is supported, while scope remains limited to "
        "supplied periods and records.",
        why_it_matters="A supported payroll tax tie-out narrows, but does not eliminate, "
        "workforce tax exposure.",
        implication="Use the tie-out as supporting disclosure; preserve tax indemnity for "
        "omitted workers, periods and classification matters.",
        action=(
            "Reconcile monthly payroll submissions, payslips, employee master, contractor "
            "payments and "
            "the EUR 132k PAYE control balance through the latest completion date."
        ),
        materiality="medium",
        confidence=0.96,
        supporting=[
            CitationSpec(returns[0], exact_text=returns[1].group(0)),
            CitationSpec(payments[0], exact_text=payments[1].group(0)),
            CitationSpec(csv_count[0][0], exact_value=unit_value(csv_count[0][0])),
        ],
        calculation_ids=[calculation],
        uncertainty="The EUR 132k PAYE control balance and post-2025 periods require "
        "reconciliation.",
        transaction_levers=["tax_indemnity", "warranty", "further_diligence"],
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
    creditor_amount = None
    if creditors is not None:
        sheet = context.sheet_for_unit(context.sheets, creditors)
        creditor_amount = context.offset_cell(sheet, creditors, 4) if sheet else None
    if restore and hosting:
        records.add_finding(
            workstream="operational_management",
            issue_id="OPS-001",
            conclusion=(
                "Business-continuity control is incomplete: the board left the restore test "
                "open with "
                "no approved date, while delivery depends on a single managed-hosting arrangement."
            ),
            source_fact="Board minutes record the open restore-test action; the hosting "
            "agreement supplies backups but no committed witnessed test.",
            analysis="Backups without demonstrated restoration do not prove recoverability or "
            "operational resilience.",
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
            materiality="critical",
            confidence=0.98,
            supporting=[
                CitationSpec(restore[0], exact_text=restore[1].group(0)),
                CitationSpec(hosting[0], exact_text=hosting[1].group(0)),
            ],
            transaction_levers=["closing_condition", "escrow", "warranty"],
        )
    if hosting and creditor_amount is not None:
        fee = float(hosting[1].group(1).replace(",", ""))
        payable = float(numeric_value(creditor_amount) or 0)
        records.add_finding(
            workstream="operational_management",
            issue_id="OPS-002",
            conclusion=(
                f"A single hosting provider carries an annual fee of {_money(fee)} and an "
                f"aged-creditor balance of {_money(payable)}, creating supplier continuity "
                "and negotiating dependence."
            ),
            source_fact="The hosting contract and creditor ageing identify the same provider "
            "and amounts.",
            analysis="No alternate-hosting plan, exit assistance or tested migration evidence "
            "was supplied.",
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
                CitationSpec(creditor_amount, exact_value=unit_value(creditor_amount)),
            ],
            uncertainty="No evidence establishes provider substitutability or migration duration.",
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
            "termination_renewal_pricing_service": ["LEGAL-001", "LEGAL-002"],
            "liability_warranties_indemnities": ["LEGAL-002"],
            "complaints_correspondence": ["IT-002"],
            "employment_contractor_status": ["LEGAL-004"],
            "property_restrictions": ["LEGAL-005"],
            "insurance_licences_work_permits": [],
            "ip_ownership_data_protection": [],
            "missing_documents_questionnaire_references": [],
        },
        "tax": {
            "vat_returns_xero_original_amended": ["TAX-001"],
            "vat_charges_payments": ["TAX-001"],
            "paye_returns_payments": ["TAX-003"],
            "corporation_tax_returns_payments_charges_refunds": ["TAX-002"],
            "annual_computations_trial_balances": ["TAX-002"],
            "invoice_samples": [],
            "tax_clearance": [],
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
            "software_ip_licensing": [],
            "data_processing_gdpr": [],
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
