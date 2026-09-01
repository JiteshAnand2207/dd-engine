#!/usr/bin/env python3
"""Generate the complete deterministic fictional Phase 3 data room."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from synthetic_formats import (  # noqa: E402
    SYNTHETIC_LABEL,
    FormulaCell,
    SheetSpec,
    bytes_from_writer,
    write_corrupt_pdf,
    write_cro_screenshot,
    write_csv_bytes_with_xlsx_extension,
    write_docx,
    write_image_only_pdf,
    write_phone_photo,
    write_stable_zip,
    write_text_pdf,
    write_xlsx,
)

from dd_engine.source_paths import (  # noqa: E402
    EMPTY_DIRECTORY_MARKER,
    EMPTY_DIRECTORY_MARKER_CONTENT,
)

DEFAULT_SEED = 314159
DATASET_ID = "SYN-LARKSPUR-2026-314159"
GENERATOR_VERSION = "3.0.0"
TOP_LEVELS = ("Financial", "Legal", "Tax")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_canonical_dataset(seed: int) -> dict[str, Any]:
    """Return the coherent baseline used by every generated document."""

    years = [
        (2020, 6_200_000, 3_720_000, 720_000, 310_000, 82_000, 328_000, 41),
        (2021, 7_180_000, 4_379_800, 910_000, 345_000, 91_000, 379_200, 45),
        (2022, 8_350_000, 5_177_000, 1_120_000, 382_000, 106_000, 505_600, 50),
        (2023, 9_620_000, 6_060_600, 1_350_000, 425_000, 128_000, 621_600, 55),
        (2024, 11_400_000, 7_410_000, 1_720_000, 470_000, 152_000, 824_400, 60),
        (2025, 13_100_000, 8_646_000, 2_080_000, 515_000, 171_000, 1_045_800, 64),
    ]
    financial_years = []
    for (
        year,
        revenue,
        gross_profit,
        ebitda,
        depreciation,
        interest,
        profit_after_tax,
        headcount,
    ) in years:
        ebit = ebitda - depreciation
        profit_before_tax = ebit - interest
        tax = profit_before_tax - profit_after_tax
        financial_years.append(
            {
                "year": year,
                "revenue": revenue,
                "cost_of_sales": revenue - gross_profit,
                "gross_profit": gross_profit,
                "operating_expenses_before_da": gross_profit - ebitda,
                "ebitda": ebitda,
                "depreciation_amortisation": depreciation,
                "ebit": ebit,
                "net_interest": interest,
                "profit_before_tax": profit_before_tax,
                "corporation_tax": tax,
                "profit_after_tax": profit_after_tax,
                "average_headcount": headcount,
            }
        )

    customers = [
        {
            "code": "HBL",
            "legal_name": "Harbourlight Stores Limited",
            "trading_name": "Harbourlight",
            "group_id": "GRP-HBL",
            "group_name": "Harbourlight Mutual Group",
            "revenue_2025": 3_100_000,
            "revenue_2026_ytd": 1_900_000,
            "debtor_balance": 410_000,
            "terms_days": 45,
        },
        {
            "code": "GCH",
            "legal_name": "Glencree Health Systems Limited",
            "trading_name": "Glencree Health",
            "group_id": "GRP-GCH",
            "group_name": "Glencree Health Systems",
            "revenue_2025": 2_600_000,
            "revenue_2026_ytd": 1_550_000,
            "debtor_balance": 320_000,
            "terms_days": 30,
        },
        {
            "code": "MNR",
            "legal_name": "Mosaic North Retail Limited",
            "trading_name": "Mosaic North",
            "group_id": "GRP-MOSAIC",
            "group_name": "Mosaic Arc Group",
            "revenue_2025": 2_000_000,
            "revenue_2026_ytd": 1_250_000,
            "debtor_balance": 230_000,
            "terms_days": 30,
        },
        {
            "code": "MST",
            "legal_name": "Mosaic South Trading Limited",
            "trading_name": "Mosaic South",
            "group_id": "GRP-MOSAIC",
            "group_name": "Mosaic Arc Group",
            "revenue_2025": 1_700_000,
            "revenue_2026_ytd": 1_100_000,
            "debtor_balance": 210_000,
            "terms_days": 30,
        },
        {
            "code": "RMF",
            "legal_name": "Rowanmere Foods Limited",
            "trading_name": "Rowanmere",
            "group_id": "GRP-RMF",
            "group_name": "Rowanmere Foods",
            "revenue_2025": 1_600_000,
            "revenue_2026_ytd": 900_000,
            "debtor_balance": 160_000,
            "terms_days": 30,
        },
        {
            "code": "CFL",
            "legal_name": "Copper Finch Logistics Limited",
            "trading_name": "Copper Finch",
            "group_id": "GRP-CFL",
            "group_name": "Copper Finch Logistics",
            "revenue_2025": 1_200_000,
            "revenue_2026_ytd": 550_000,
            "debtor_balance": 90_000,
            "terms_days": 60,
        },
        {
            "code": "OTH",
            "legal_name": "Other fictional customers",
            "trading_name": "Other",
            "group_id": "GRP-OTHER",
            "group_name": "Other",
            "revenue_2025": 900_000,
            "revenue_2026_ytd": 400_000,
            "debtor_balance": 60_000,
            "terms_days": 30,
        },
    ]

    first_names = [
        "Nessa",
        "Ciar",
        "Orla",
        "Tomas",
        "Maeve",
        "Ronan",
        "Eimear",
        "Dara",
        "Sive",
        "Oisin",
        "Una",
        "Fiach",
        "Ailbhe",
        "Cormac",
        "Liadan",
        "Senan",
    ]
    surnames = ["Brannock", "Mollen", "Fenwick", "Tallis", "Reddan", "Kearlen"]
    client_codes = (
        ["HBL"] * 18
        + ["GCH"] * 13
        + ["MNR"] * 9
        + ["MST"] * 7
        + ["RMF"] * 8
        + ["CFL"] * 4
        + ["INT"] * 5
    )
    employees = []
    for index in range(64):
        first = first_names[index % len(first_names)]
        surname = surnames[(index // len(first_names)) % len(surnames)]
        suffix = index // (len(first_names) * len(surnames))
        display_surname = f"{surname}{suffix + 1}" if suffix else surname
        slug = f"{first}.{display_surname}".lower()
        employees.append(
            {
                "employee_id": f"EMP-{index + 1:03d}",
                "name": f"{first} {display_surname}",
                "department": ("Delivery", "Engineering", "Operations", "Commercial")[index % 4],
                "client_code": client_codes[index],
                "annual_salary": 46_000 + (index % 11) * 2_750,
                "start_date": f"20{18 + index % 8:02d}-{1 + index % 12:02d}-{1 + index % 27:02d}",
                "work_email": f"{slug}@larkspur.invalid",
                "personal_email": f"{slug}@personal.invalid",
                "synthetic_pps_like_id": f"SYN{index + 1:06d}{chr(65 + index % 26)}",
            }
        )
    contractors = [
        {
            "contractor_id": f"CTR-{index + 1:03d}",
            "name": f"{first_names[(index + 3) % len(first_names)]} Advisory {index + 1}",
            "client_code": ("HBL", "GCH", "MNR", "MST", "RMF", "CFL")[index % 6],
            "monthly_fee": 6_500 + index * 250,
            "end_date": f"2026-{7 + index % 5:02d}-{15 + index % 10:02d}",
        }
        for index in range(12)
    ]

    return {
        "schema_version": 1,
        "dataset_id": DATASET_ID,
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "as_of_date": "2026-06-30",
        "provenance": {
            "classification": "entirely fictional synthetic fixture",
            "real_source_material_used": False,
            "external_research_used": False,
            "notice": SYNTHETIC_LABEL,
        },
        "company": {
            "legal_name": "Larkspur Transit Analytics Limited",
            "registration_id": "IE-SYN-748291",
            "vat_id": "IE-SYN-VAT-912345",
            "incorporated": "2017-02-14",
            "registered_address": "14 Alder Quay, Kilnmore Business Park, Dublin D99 SYN4",
            "business": "Route optimisation and fleet analytics software",
            "directors": ["Nessa Brannock", "Ciar Mollen", "Orla Fenwick"],
            "shareholders": [
                {"name": "Nessa Brannock", "ordinary_shares": 520_000, "ownership": 0.52},
                {"name": "Ciar Mollen", "ordinary_shares": 280_000, "ownership": 0.28},
                {
                    "name": "Alder Quay Ventures (Synthetic) LP",
                    "ordinary_shares": 200_000,
                    "ownership": 0.20,
                },
            ],
            "governance": {"board_meetings_per_year": 6, "reserved_matters_threshold": 0.75},
        },
        "financial_years": financial_years,
        "management_accounts": {
            "period_end": "2026-06-30",
            "revenue": 7_650_000,
            "cost_of_sales": 2_601_000,
            "gross_profit": 5_049_000,
            "baseline_ebitda": 1_230_000,
            "reported_adjusted_ebitda": 1_410_000,
            "transformation_adjustment": 180_000,
        },
        "customers": customers,
        "working_capital": {
            "trade_debtors": 1_480_000,
            "other_debtors": 95_000,
            "prepayments": 185_000,
            "trade_creditors": 930_000,
            "correct_net_working_capital": 830_000,
        },
        "creditors": [
            {"supplier": "Juniper Hosting Services Limited", "balance": 265_000, "days": 42},
            {"supplier": "Northmere HR Services Limited", "balance": 105_000, "days": 31},
            {"supplier": "Fleetcraft Leasing Limited", "balance": 180_000, "days": 55},
            {"supplier": "Other fictional suppliers", "balance": 380_000, "days": 28},
        ],
        "debt": {
            "loans": [
                {
                    "lender": "Fictional Atlantic Bank",
                    "facility": "Term loan",
                    "balance": 1_450_000,
                    "rate": 0.0575,
                    "maturity": "2029-03-31",
                },
                {
                    "lender": "Synthetic Enterprise Finance",
                    "facility": "Innovation loan",
                    "balance": 360_000,
                    "rate": 0.0425,
                    "maturity": "2028-11-30",
                },
            ],
            "hp_agreements": [
                {
                    "provider": "Fleetcraft Leasing Limited",
                    "asset": "18 service vehicles",
                    "balance": 215_000,
                    "maturity": "2028-06-30",
                },
                {
                    "provider": "Quayside Equipment Finance",
                    "asset": "Server and test equipment",
                    "balance": 75_000,
                    "maturity": "2027-09-30",
                },
            ],
            "director_current_account": 120_000,
        },
        "fixed_assets": [
            {
                "class": "Computer equipment",
                "cost": 1_280_000,
                "accumulated_depreciation": 720_000,
                "nbv": 560_000,
            },
            {
                "class": "Motor vehicles",
                "cost": 1_050_000,
                "accumulated_depreciation": 540_000,
                "nbv": 510_000,
            },
            {
                "class": "Leasehold improvements",
                "cost": 540_000,
                "accumulated_depreciation": 210_000,
                "nbv": 330_000,
            },
            {
                "class": "Test equipment",
                "cost": 330_000,
                "accumulated_depreciation": 180_000,
                "nbv": 150_000,
            },
        ],
        "disposals": [
            {
                "asset": "Five route-survey vehicles",
                "proceeds": 148_000,
                "nbv": 121_000,
                "profit": 27_000,
            },
            {"asset": "Legacy server rack", "proceeds": 38_000, "nbv": 45_000, "profit": -7_000},
        ],
        "employees": employees,
        "contractors": contractors,
        "properties": [
            {
                "address": "14 Alder Quay, Kilnmore Business Park, Dublin D99 SYN4",
                "tenure": "leasehold",
                "annual_rent": 310_000,
                "expiry": "2031-12-31",
            },
            {
                "address": "Unit 6, Bracken Loop, Cork C99 SYN8",
                "tenure": "sold",
                "sale_date": "2024-10-15",
                "proceeds": 820_000,
            },
        ],
        "insurance": [
            {"type": "Employers and public liability", "limit": 10_000_000, "expiry": "2027-02-28"},
            {"type": "Cyber liability", "limit": 2_000_000, "expiry": "2027-02-28"},
            {"type": "Fleet", "vehicles": 18, "expiry": "2027-01-31"},
        ],
        "licences": [
            {
                "name": "Synthetic road-data processing registration",
                "id": "SYN-LIC-44218",
                "expiry": "2027-05-31",
            }
        ],
        "providers": [
            {
                "name": "Juniper Hosting Services Limited",
                "service": "Managed hosting",
                "annual_fee": 420_000,
                "notice_days": 90,
            },
            {
                "name": "Northmere HR Services Limited",
                "service": "Payroll and HR support",
                "annual_fee": 96_000,
                "notice_days": 60,
            },
        ],
        "related_parties": [
            {
                "party": "Nessa Brannock",
                "relationship": "Director",
                "transaction": "Current account",
                "balance": 120_000,
            },
            {
                "party": "Alder Quay Properties (Synthetic) Limited",
                "relationship": "Shareholder affiliate",
                "transaction": "Temporary office licence",
                "annual_value": 36_000,
            },
        ],
        "tax": {
            "vat_periods": [
                {
                    "period": "2025-P1",
                    "output_vat": 438_000,
                    "input_vat": 272_000,
                    "payable": 166_000,
                },
                {
                    "period": "2025-P2",
                    "output_vat": 455_000,
                    "input_vat": 281_000,
                    "payable": 174_000,
                    "amended_payable": 182_000,
                },
                {
                    "period": "2025-P3",
                    "output_vat": 472_000,
                    "input_vat": 293_000,
                    "payable": 179_000,
                },
                {
                    "period": "2025-P4",
                    "output_vat": 498_000,
                    "input_vat": 306_000,
                    "payable": 192_000,
                },
            ],
            "paye": {
                "registered_headcount": 64,
                "annual_liability_2025": 1_584_000,
                "paid_2025": 1_584_000,
            },
            "corporation_tax": {
                "period": "2025",
                "return_liability": 389_200,
                "payments": 420_000,
                "charge": 12_500,
                "refund": 18_300,
            },
            "tax_clearance_expiry": "2027-04-30",
        },
        "pipeline": [
            {
                "opportunity": "Harbourlight route expansion",
                "stage": "Contracting",
                "probability": 0.85,
                "annual_value": 1_250_000,
            },
            {
                "opportunity": "Bracken County mobility",
                "stage": "Proposal",
                "probability": 0.55,
                "annual_value": 920_000,
            },
            {
                "opportunity": "Mosaic Arc renewals",
                "stage": "Verbal",
                "probability": 0.70,
                "annual_value": 1_100_000,
            },
            {
                "opportunity": "Copper Finch optimisation",
                "stage": "Discovery",
                "probability": 0.30,
                "annual_value": 680_000,
            },
        ],
        "forecasts": [
            {"year": 2026, "revenue": 15_900_000, "gross_profit": 10_494_000, "ebitda": 2_760_000},
            {"year": 2027, "revenue": 18_100_000, "gross_profit": 12_126_000, "ebitda": 3_350_000},
            {"year": 2028, "revenue": 20_300_000, "gross_profit": 13_804_000, "ebitda": 3_980_000},
        ],
    }


@dataclass(slots=True)
class ArtifactRecord:
    path: str
    workstream: str
    family: str
    declared_format: str
    visible: bool = True
    container: str | None = None
    member_path: str | None = None
    quirks: list[str] = field(default_factory=list)
    expected_readability: str = "readable"
    supersedes: str | None = None


class RoomBuilder:
    def __init__(self, room: Path, data: dict[str, Any], seed: int) -> None:
        self.room = room
        self.data = data
        self.seed = seed
        self.records: list[ArtifactRecord] = []

    def record(
        self,
        relative: str,
        workstream: str,
        family: str,
        *,
        quirks: Sequence[str] = (),
        expected_readability: str = "readable",
        supersedes: str | None = None,
    ) -> Path:
        suffix = Path(relative).suffix.lower().lstrip(".")
        self.records.append(
            ArtifactRecord(
                path=relative,
                workstream=workstream,
                family=family,
                declared_format=suffix,
                quirks=list(quirks),
                expected_readability=expected_readability,
                supersedes=supersedes,
            )
        )
        return self.room / relative

    def text_pdf(
        self,
        relative: str,
        workstream: str,
        family: str,
        *,
        title: str,
        subtitle: str,
        sections: Sequence[tuple[str, Sequence[str]]],
        table: Sequence[Sequence[Any]] | None = None,
        template: str = "navy",
        quirks: Sequence[str] = (),
        supersedes: str | None = None,
    ) -> None:
        path = self.record(relative, workstream, family, quirks=quirks, supersedes=supersedes)
        write_text_pdf(
            path,
            title=title,
            subtitle=subtitle,
            sections=sections,
            table=table,
            template=template,
            metadata=(
                ("Company", self.data["company"]["legal_name"]),
                ("Dataset", DATASET_ID),
                ("Status", "Synthetic"),
            ),
        )

    def workbook(
        self,
        relative: str,
        workstream: str,
        family: str,
        sheets: Sequence[SheetSpec],
        *,
        quirks: Sequence[str] = (),
        supersedes: str | None = None,
    ) -> None:
        path = self.record(relative, workstream, family, quirks=quirks, supersedes=supersedes)
        write_xlsx(path, sheets)

    def generate_financial(self) -> None:
        company = self.data["company"]["legal_name"]
        templates = ("slate", "green", "navy", "slate", "green", "navy")
        for index, year in enumerate(self.data["financial_years"]):
            balance_assets = 2_500_000 + (year["year"] - 2020) * 520_000
            balance_liabilities = 1_250_000 + (year["year"] - 2020) * 260_000
            self.text_pdf(
                f"Financial/Statutory Accounts/Statutory_Accounts_{year['year']}.pdf",
                "financial",
                "statutory_accounts",
                title=f"Abridged Statutory Accounts {year['year']}",
                subtitle=f"{company} | year ended 31 December {year['year']}",
                template=templates[index],
                sections=(
                    (
                        "Directors' statement",
                        (
                            f"The directors present the fictional statutory accounts for {year['year']}. These accounts form part of dataset {DATASET_ID}.",
                        ),
                    ),
                    (
                        "Profit and loss account",
                        (
                            f"Revenue EUR {year['revenue']:,}; gross profit EUR {year['gross_profit']:,}; EBITDA EUR {year['ebitda']:,}; profit after tax EUR {year['profit_after_tax']:,}.",
                        ),
                    ),
                    (
                        "Balance sheet",
                        (
                            f"Total assets EUR {balance_assets:,}; total liabilities EUR {balance_liabilities:,}; shareholders' funds EUR {balance_assets - balance_liabilities:,}. The balance sheet balances.",
                        ),
                    ),
                    (
                        "Notes",
                        (
                            "Revenue arises from fleet analytics subscriptions and implementation services. Accounting policies are consistently applied except where expressly stated.",
                        ),
                    ),
                ),
                table=(
                    ("Metric", str(year["year"]), "Prior-year comparative"),
                    ("Revenue", f"EUR {year['revenue']:,}", "see prior filing"),
                    ("Gross profit", f"EUR {year['gross_profit']:,}", "see prior filing"),
                    ("EBITDA", f"EUR {year['ebitda']:,}", "management measure"),
                    ("Profit after tax", f"EUR {year['profit_after_tax']:,}", "statutory"),
                    ("Average headcount", year["average_headcount"], "employees"),
                ),
            )

        management = self.data["management_accounts"]
        mgmt_sections = (
            (
                "Executive summary",
                (
                    f"Revenue for the six months ended 30 June 2026 was EUR {management['revenue']:,} and gross profit was EUR {management['gross_profit']:,}.",
                    f"Reported adjusted EBITDA: EUR {management['reported_adjusted_ebitda']:,}. Baseline ledger EBITDA before the transformation adjustment was EUR {management['baseline_ebitda']:,}.",
                ),
            ),
            (
                "Adjusting items",
                (
                    f"A transformation adjustment of EUR {management['transformation_adjustment']:,} was added back. Supporting invoices and an approved restructuring plan were not included in this room.",
                ),
            ),
            (
                "Outlook",
                (
                    "Management expects second-half revenue conversion to depend on the Harbourlight expansion and Mosaic renewals. Forecasts are not guarantees.",
                ),
            ),
        )
        self.text_pdf(
            "Financial/Management_Accounts_2026_YTD.pdf",
            "financial",
            "management_accounts",
            title="Management Accounts - June 2026 YTD",
            subtitle=f"{company} | final management pack",
            sections=mgmt_sections,
            table=(
                ("Metric", "EUR"),
                ("Revenue", f"{management['revenue']:,}"),
                ("Gross profit", f"{management['gross_profit']:,}"),
                ("Reported adjusted EBITDA", f"{management['reported_adjusted_ebitda']:,}"),
            ),
            template="navy",
            quirks=("near_duplicate_final", "ebitda_contradiction"),
            supersedes="Financial/Management_Accounts_2026_YTD_DRAFT.pdf",
        )
        self.text_pdf(
            "Financial/Management_Accounts_2026_YTD_DRAFT.pdf",
            "financial",
            "management_accounts_version",
            title="Management Accounts - June 2026 YTD",
            subtitle=f"{company} | DRAFT v0.8 - superseded",
            sections=(
                (
                    "Executive summary",
                    (
                        f"Draft revenue EUR {management['revenue']:,}; draft gross profit EUR {management['gross_profit']:,}; draft adjusted EBITDA EUR {management['reported_adjusted_ebitda'] - 25_000:,}.",
                    ),
                ),
                (
                    "Status",
                    (
                        "Superseded by the final management pack. Do not rely on this draft for closing adjustments.",
                    ),
                ),
            ),
            table=(
                ("Metric", "Draft EUR"),
                ("Revenue", f"{management['revenue']:,}"),
                ("Adjusted EBITDA", f"{management['reported_adjusted_ebitda'] - 25_000:,}"),
            ),
            template="navy",
            quirks=("near_duplicate", "superseded_version"),
        )

        year = self.data["financial_years"][-1]
        tb_rows = [
            [f"Trial Balance 2025 | {SYNTHETIC_LABEL}"],
            ["Dataset", DATASET_ID, "Currency", "EUR"],
            ["Account", "Description", "Debit", "Credit"],
            ["1000", "Cash", 960_000, 0],
            ["1100", "Trade debtors", 1_480_000, 0],
            ["1200", "Other debtors and prepayments", 280_000, 0],
            ["1500", "Fixed assets NBV", 1_550_000, 0],
            ["2000", "Trade creditors", 0, 930_000],
            ["2100", "Loans and HP", 0, 2_100_000],
            ["3000", "Shareholders' funds", 0, 1_240_000],
            ["4000", "Revenue", 0, year["revenue"]],
            ["5000", "Cost of sales", year["cost_of_sales"], 0],
            ["6000", "Operating expenses before D&A", year["operating_expenses_before_da"], 0],
            ["6100", "Depreciation and amortisation", year["depreciation_amortisation"], 0],
            ["7000", "Interest", year["net_interest"], 0],
            ["8000", "Corporation tax", year["corporation_tax"], 0],
            ["9999", "Retained earnings movement", 0, year["profit_after_tax"]],
        ]
        self.workbook(
            "Financial/Trial_Balance_2025.xlsx",
            "financial",
            "trial_balance",
            (SheetSpec("Trial Balance", tb_rows, currency_columns=frozenset({3, 4})),),
        )

        debtor_rows = [
            [f"Aged Debtors | {SYNTHETIC_LABEL}"],
            ["As of", "2026-06-30"],
            ["Customer", "Current", "31-60", "61-90", "90+", "Total"],
        ]
        for index, customer in enumerate(self.data["customers"]):
            total = customer["debtor_balance"]
            current = int(total * (0.65 if index != 0 else 0.40))
            d31 = int(total * 0.20)
            d61 = int(total * 0.10)
            d90 = total - current - d31 - d61
            debtor_rows.append([customer["legal_name"], current, d31, d61, d90, total])
        debtor_rows.append(
            [
                "Total trade debtors",
                FormulaCell("SUM(B4:B10)", 962_000),
                FormulaCell("SUM(C4:C10)", 296_000),
                FormulaCell("SUM(D4:D10)", 148_000),
                FormulaCell("SUM(E4:E10)", 74_000),
                FormulaCell("SUM(F4:F10)", 1_480_000, style=8),
            ]
        )
        self.workbook(
            "Financial/Aged_Debtors.xlsx",
            "financial",
            "aged_debtors",
            (SheetSpec("Aged Debtors", debtor_rows, currency_columns=frozenset({2, 3, 4, 5, 6})),),
        )

        creditor_rows = [
            [f"Aged Creditors | {SYNTHETIC_LABEL}"],
            ["As of", "2026-06-30"],
            ["Supplier", "Current", "31-60", "61+", "Total"],
        ]
        for creditor in self.data["creditors"]:
            total = creditor["balance"]
            creditor_rows.append(
                [
                    creditor["supplier"],
                    int(total * 0.65),
                    int(total * 0.25),
                    total - int(total * 0.65) - int(total * 0.25),
                    total,
                ]
            )
        creditor_rows.append(
            [
                "Total trade creditors",
                FormulaCell("SUM(B4:B7)", 604_500),
                FormulaCell("SUM(C4:C7)", 232_500),
                FormulaCell("SUM(D4:D7)", 93_000),
                FormulaCell("SUM(E4:E7)", 930_000, style=8),
            ]
        )
        self.workbook(
            "Financial/Aged_Creditors.xlsx",
            "financial",
            "aged_creditors",
            (SheetSpec("Aged Creditors", creditor_rows, currency_columns=frozenset({2, 3, 4, 5})),),
        )

        wc = self.data["working_capital"]
        self.workbook(
            "Financial/Other_Debtors_and_Prepayments.xlsx",
            "financial",
            "other_debtors",
            (
                SheetSpec(
                    "Schedule",
                    [
                        [f"Other Debtors and Prepayments | {SYNTHETIC_LABEL}"],
                        ["As of", "2026-06-30"],
                        ["Category", "Amount", "Support"],
                        ["Other debtors", wc["other_debtors"], "deposit and staff advances"],
                        ["Prepayments", wc["prepayments"], "insurance and hosting"],
                        [
                            "Total",
                            FormulaCell("SUM(B4:B5)", 280_000, style=8),
                            "ties to trial balance",
                        ],
                    ],
                    currency_columns=frozenset({2}),
                ),
            ),
        )
        fixed_rows = [
            [f"Fixed Asset Register | {SYNTHETIC_LABEL}"],
            ["As of", "2025-12-31"],
            ["Class", "Cost", "Accumulated depreciation", "NBV"],
        ]
        for asset in self.data["fixed_assets"]:
            fixed_rows.append(
                [asset["class"], asset["cost"], asset["accumulated_depreciation"], asset["nbv"]]
            )
        fixed_rows.append(
            [
                "Total",
                FormulaCell("SUM(B4:B7)", 3_200_000, style=8),
                FormulaCell("SUM(C4:C7)", 1_650_000, style=8),
                FormulaCell("SUM(D4:D7)", 1_550_000, style=8),
            ]
        )
        self.workbook(
            "Financial/Fixed_Asset_Register.xlsx",
            "financial",
            "fixed_assets",
            (SheetSpec("Register", fixed_rows, currency_columns=frozenset({2, 3, 4})),),
        )

        working_rows = [
            [f"Working Capital Calculation | {SYNTHETIC_LABEL}"],
            ["As of", "2026-06-30", "Units", "EUR"],
            ["Component", "Amount", "Treatment", "Note"],
            ["Trade debtors", wc["trade_debtors"], "+", "Aged debtors"],
            ["Other debtors", wc["other_debtors"], "+", "Schedule"],
            ["Trade creditors", -wc["trade_creditors"], "+", "Aged creditors"],
            ["Cash", 0, "excluded", "not working capital"],
            ["Prepayments", wc["prepayments"], "+", "Hidden row omitted by formula"],
            [
                "Calculated net working capital",
                FormulaCell("SUM(B5:B7)", -835_000, style=8),
                "formula",
                "Formula incorrectly excludes rows 4 and 8",
            ],
            [
                "Correct net working capital",
                wc["correct_net_working_capital"],
                "control",
                "Expected baseline",
            ],
        ]
        hidden_input = SheetSpec(
            "Assumptions",
            [
                [f"Assumptions | {SYNTHETIC_LABEL}"],
                ["Dataset", DATASET_ID],
                ["Parameter", "Value"],
                ["Target NWC", wc["correct_net_working_capital"]],
            ],
            hidden=True,
            currency_columns=frozenset({2}),
        )
        self.workbook(
            "Financial/Working_Capital_Calculation.xlsx",
            "financial",
            "working_capital",
            (
                SheetSpec(
                    "Calculation",
                    working_rows,
                    hidden_rows=frozenset({8}),
                    currency_columns=frozenset({2}),
                    warning_cells=frozenset({"B9"}),
                ),
                hidden_input,
            ),
            quirks=(
                "hidden_sheet",
                "hidden_row",
                "incorrect_formula_range",
                "non_tying_spreadsheet",
            ),
        )

        revenue_rows = [
            [f"Revenue by Customer | {SYNTHETIC_LABEL}"],
            ["Years", "FY2025", "2026 YTD", "Group reference"],
            ["Customer", "FY2025 revenue", "2026 YTD revenue", "Group ID", "Group name"],
        ]
        for customer in self.data["customers"]:
            revenue_rows.append(
                [
                    customer["legal_name"],
                    customer["revenue_2025"],
                    customer["revenue_2026_ytd"],
                    customer["group_id"],
                    customer["group_name"],
                ]
            )
        revenue_rows.append(
            [
                "Total",
                FormulaCell("SUM(B4:B10)", 13_100_000, style=8),
                FormulaCell("SUM(C4:C10)", 7_650_000, style=8),
                "",
                "",
            ]
        )
        self.workbook(
            "Financial/Revenue_by_Customer.xlsx",
            "financial",
            "revenue_by_customer",
            (SheetSpec("Revenue", revenue_rows, currency_columns=frozenset({2, 3})),),
            quirks=("customer_alias_evidence",),
        )

        allocations: dict[str, int] = {}
        for employee in self.data["employees"]:
            allocations[employee["client_code"]] = allocations.get(employee["client_code"], 0) + 1
        paye_rows = [
            [f"PAYE Headcount by Client | {SYNTHETIC_LABEL}"],
            ["As of", "2026-06-30"],
            ["Client code", "PAYE headcount", "Basis"],
        ]
        paye_rows.extend(
            [[code, value, "Payroll allocation"] for code, value in allocations.items()]
        )
        paye_rows.append(
            [
                "Total PAYE headcount",
                FormulaCell(f"SUM(B4:B{3 + len(allocations)})", 64, style=9),
                "64 employees per PAYE return",
            ]
        )
        self.workbook(
            "Financial/PAYE_Headcount_by_Client.xlsx",
            "financial",
            "paye_headcount",
            (SheetSpec("PAYE", paye_rows, integer_columns=frozenset({2})),),
            quirks=("workforce_mismatch_evidence",),
        )

        contractor_alloc = {"HBL": 2, "GCH": 2, "MNR": 2, "MST": 1, "RMF": 2, "CFL": 1}
        contractor_rows = [
            [f"Contractor Headcount by Client | {SYNTHETIC_LABEL}"],
            ["As of", "2026-06-30"],
            ["Client code", "Contractor headcount", "Note"],
        ]
        contractor_rows.extend(
            [[code, count, "Active allocation"] for code, count in contractor_alloc.items()]
        )
        contractor_rows.append(
            [
                "Total",
                FormulaCell("SUM(B4:B9)", 10, style=9),
                "10 contractors allocated; legal list contains 12 active contractors",
            ]
        )
        self.workbook(
            "Financial/Contractor_Headcount_by_Client.xlsx",
            "financial",
            "contractor_headcount",
            (SheetSpec("Contractors", contractor_rows, integer_columns=frozenset({2})),),
            quirks=("workforce_mismatch_evidence",),
        )

        loan_rows = [
            [f"Loan Summary | {SYNTHETIC_LABEL}"],
            ["As of", "2026-06-30"],
            ["Lender", "Facility", "Balance", "Rate", "Maturity", "Scope note"],
        ]
        for loan in self.data["debt"]["loans"]:
            loan_rows.append(
                [
                    loan["lender"],
                    loan["facility"],
                    loan["balance"],
                    loan["rate"],
                    loan["maturity"],
                    "Loan schedule only",
                ]
            )
        loan_rows.append(
            [
                "Total loans",
                "",
                FormulaCell("SUM(C4:C5)", 1_810_000, style=8),
                "",
                "",
                "HP agreements are excluded; director balances are not debt per management",
            ]
        )
        loan_path = "Financial/Loan_Summary.xlsx"
        self.workbook(
            loan_path,
            "financial",
            "loan_summary",
            (
                SheetSpec(
                    "Loans",
                    loan_rows,
                    currency_columns=frozenset({3}),
                    percent_columns=frozenset({4}),
                ),
            ),
            quirks=("omitted_debt_scope",),
        )
        duplicate_path = self.record(
            "Financial/Loan_Summary_for_Bank.xlsx",
            "financial",
            "controlled_duplicate",
            quirks=("exact_duplicate_different_name",),
        )
        shutil.copyfile(self.room / loan_path, duplicate_path)

        hp_rows = [
            [f"HP Summary | {SYNTHETIC_LABEL}"],
            ["As of", "2026-06-30"],
            ["Provider", "Asset", "Balance", "Maturity"],
        ]
        for hp in self.data["debt"]["hp_agreements"]:
            hp_rows.append([hp["provider"], hp["asset"], hp["balance"], hp["maturity"]])
        hp_rows.append(
            [
                "Total HP exposure",
                "",
                FormulaCell("SUM(C4:C5)", 290_000, style=8),
                "Debt-like exposure",
            ]
        )
        self.workbook(
            "Financial/HP_Summary.xlsx",
            "financial",
            "hp_summary",
            (SheetSpec("HP", hp_rows, currency_columns=frozenset({3})),),
            quirks=("omitted_debt_evidence",),
        )

        disposal_rows = [
            [f"Profit on Disposal Schedule | {SYNTHETIC_LABEL}"],
            ["Year", "2025"],
            ["Asset", "Proceeds", "NBV", "Profit/(loss)"],
        ]
        for disposal in self.data["disposals"]:
            disposal_rows.append(
                [disposal["asset"], disposal["proceeds"], disposal["nbv"], disposal["profit"]]
            )
        disposal_rows.append(
            [
                "Total",
                FormulaCell("SUM(B4:B5)", 186_000, style=8),
                FormulaCell("SUM(C4:C5)", 166_000, style=8),
                FormulaCell("SUM(D4:D5)", 20_000, style=8),
            ]
        )
        self.workbook(
            "Financial/Profit_on_Disposal.xlsx",
            "financial",
            "profit_on_disposal",
            (SheetSpec("Disposals", disposal_rows, currency_columns=frozenset({2, 3, 4})),),
        )

        pipeline_rows = [
            [f"Revenue Pipeline | {SYNTHETIC_LABEL}"],
            ["Snapshot", "2026-06-30"],
            ["Opportunity", "Stage", "Probability", "Annual value", "Weighted value"],
        ]
        for item in self.data["pipeline"]:
            weighted = int(item["probability"] * item["annual_value"])
            pipeline_rows.append(
                [
                    item["opportunity"],
                    item["stage"],
                    item["probability"],
                    item["annual_value"],
                    weighted,
                ]
            )
        pipeline_rows.append(
            [
                "Total",
                "",
                "",
                FormulaCell("SUM(D4:D7)", 3_950_000, style=8),
                FormulaCell("SUM(E4:E7)", 2_580_000, style=8),
            ]
        )
        self.workbook(
            "Financial/Revenue_Pipeline.xlsx",
            "financial",
            "revenue_pipeline",
            (
                SheetSpec(
                    "Pipeline",
                    pipeline_rows,
                    percent_columns=frozenset({3}),
                    currency_columns=frozenset({4, 5}),
                ),
            ),
        )

        request_rows = [
            [f"Financial Information Request | {SYNTHETIC_LABEL}"],
            ["Status", "Vendor responses as of 2026-07-15"],
            ["Request ID", "Request", "Vendor answer", "Owner"],
            ["F-01", "Monthly management accounts", "N/A - only YTD pack prepared", "Finance"],
            [
                "F-02",
                "EBITDA adjustment support",
                "EUR 180,000 transformation adjustment; support to follow",
                "CFO",
            ],
            [
                "F-03",
                "Debt and debt-like schedule",
                "See loan summary; HP handled by operations",
                "Finance",
            ],
            ["F-04", "Property obligations", "see legal 2.1", "Legal"],
            ["F-05", "Customer concentration", "None", "Commercial"],
            ["F-06", "Tax audits", "N/A", "Tax"],
            ["F-07", "Related-party balances", "See Word note", "CFO"],
            ["F-08", "IT recovery costs", "None", "IT"],
            ["F-09", "Forecast methodology", "Pipeline probability weighting", "Commercial"],
            ["F-10", "Working-capital target", "see legal 2.1", "Finance"],
        ]
        self.workbook(
            "Financial/Financial_Request_List.xlsx",
            "financial",
            "financial_request_list",
            (
                SheetSpec(
                    "Request List", request_rows, warning_cells=frozenset({"C5", "C7", "C13"})
                ),
            ),
            quirks=("n_a_answers", "missing_reference", "ambiguous_see_legal_2_1"),
        )

        related_path = self.record(
            "Financial/Related_Party_Transactions.docx", "financial", "related_party_transactions"
        )
        write_docx(
            related_path,
            title="Related-Party Transactions",
            subtitle=f"{company} | summary for diligence",
            metadata=(
                ("Date", "30 June 2026"),
                ("Prepared by", "Finance"),
                ("Dataset", DATASET_ID),
            ),
            sections=(
                (
                    "Scope",
                    (
                        "This short note summarises declared transactions with directors, shareholders and their affiliates.",
                    ),
                ),
                (
                    "Observation",
                    (
                        "The director current account of EUR 120,000 is repayable on demand but is excluded from the loan summary because management does not classify it as debt.",
                    ),
                ),
            ),
            tables=(
                (
                    ("Party", "Relationship", "Transaction", "Balance/value"),
                    tuple(
                        (
                            item["party"],
                            item["relationship"],
                            item["transaction"],
                            f"EUR {item['balance'] if 'balance' in item else item['annual_value']:,}",
                        )
                        for item in self.data["related_parties"]
                    ),
                ),
            ),
        )

        photo1 = self.record(
            "Financial/Loan Letters/Phone_Photo_Term_Loan.jpg",
            "financial",
            "loan_letter_photo",
            quirks=("phone_photo", "rotation", "perspective", "noise"),
        )
        write_phone_photo(
            photo1,
            bank_name="Fictional Atlantic Bank",
            reference="SYN-FAB-20491",
            amount=1_450_000,
            text=(
                "We confirm the outstanding term loan made available to Larkspur Transit Analytics Limited.",
                "A transaction resulting in a change of control is a review event under the facility letter.",
            ),
            seed=self.seed + 11,
            angle=-3.2,
        )
        photo2 = self.record(
            "Financial/Loan Letters/Phone_Photo_Innovation_Loan.jpg",
            "financial",
            "loan_letter_photo",
            quirks=("phone_photo", "rotation", "perspective", "noise"),
        )
        write_phone_photo(
            photo2,
            bank_name="Synthetic Enterprise Finance",
            reference="SYN-SEF-88310",
            amount=360_000,
            text=(
                "This letter confirms the innovation loan balance and repayment profile.",
                "Quarterly repayments continue through November 2028.",
            ),
            seed=self.seed + 12,
            angle=4.1,
        )
        scan = self.record(
            "Financial/Loan Letters/Scanned_Loan_and_HP_Pack.pdf",
            "financial",
            "loan_hp_scan",
            quirks=("image_only_pdf", "raster_scan"),
        )
        write_image_only_pdf(
            scan,
            title="Loan and HP Security Pack",
            page_lines=(
                (
                    "Fictional Atlantic Bank security schedule.",
                    "Fixed and floating charge over synthetic company assets.",
                    f"Term loan balance EUR {self.data['debt']['loans'][0]['balance']:,}.",
                ),
                (
                    "Fleetcraft hire-purchase schedule.",
                    "Eighteen service vehicles remain subject to title retention.",
                    "Outstanding HP balance EUR 215,000.",
                ),
                (
                    "Quayside equipment finance annex.",
                    "Server and test equipment outstanding balance EUR 75,000.",
                ),
            ),
            seed=self.seed + 20,
        )

    def generate_legal(self) -> None:
        company = self.data["company"]["legal_name"]
        questionnaire = self.record(
            "Legal/Legal_Questionnaire_Completed.docx",
            "legal",
            "legal_questionnaire",
            quirks=("original_answers", "missing_reference"),
        )
        write_docx(
            questionnaire,
            title="Legal Due-Diligence Questionnaire",
            subtitle=f"Completed vendor responses for {company}",
            metadata=(
                ("Version", "Original"),
                ("Response date", "15 July 2026"),
                ("Dataset", DATASET_ID),
            ),
            sections=(
                (
                    "Corporate",
                    (
                        "The company is an Irish private company limited by shares. A CRO-style screenshot is supplied instead of a certified extract.",
                    ),
                ),
                (
                    "Contracts",
                    (
                        "Material customer agreements and amendments are in the Customer Contracts folder. Property detail: see legal 2.1; no folder bearing that reference is populated.",
                    ),
                ),
                (
                    "Information technology",
                    (
                        "Backups are performed by the hosting provider. No independent penetration test report is available and no witnessed disaster-recovery test has been completed.",
                    ),
                ),
            ),
            tables=(
                (
                    ("Question", "Vendor answer"),
                    (
                        (
                            "Any litigation or disputes?",
                            "One customer complaint; correspondence supplied.",
                        ),
                        ("Any change-of-control consents?", "None noted by management."),
                        ("Work permits complete?", "See Work Permits folder."),
                        ("Material IT incidents?", "None reported."),
                    ),
                ),
            ),
        )

        cap_rows = [
            [f"Statutory Register and Cap Table | {SYNTHETIC_LABEL}"],
            ["As of", "2026-06-30", "Total shares", 1_000_000],
            ["Shareholder", "Ordinary shares", "Ownership", "Synthetic identifier"],
        ]
        for shareholder in self.data["company"]["shareholders"]:
            cap_rows.append(
                [
                    shareholder["name"],
                    shareholder["ordinary_shares"],
                    shareholder["ownership"],
                    f"SYN-SH-{len(cap_rows) - 2:03d}",
                ]
            )
        cap_rows.append(
            [
                "Total",
                FormulaCell("SUM(B4:B6)", 1_000_000, style=9),
                FormulaCell("SUM(C4:C6)", 1.0, style=9),
                "",
            ]
        )
        self.workbook(
            "Legal/Corporate/Statutory_Register_and_Cap_Table.xlsx",
            "legal",
            "statutory_register",
            (
                SheetSpec(
                    "Cap Table",
                    cap_rows,
                    integer_columns=frozenset({2}),
                    percent_columns=frozenset({3}),
                ),
            ),
        )

        self.text_pdf(
            "Legal/Corporate/Shareholders_Agreement.pdf",
            "legal",
            "shareholders_agreement",
            title="Shareholders' Agreement",
            subtitle=f"{company} | executed fictional agreement",
            sections=(
                (
                    "Parties",
                    (
                        "Nessa Brannock, Ciar Mollen, Alder Quay Ventures (Synthetic) LP and the Company.",
                    ),
                ),
                (
                    "Reserved matters",
                    (
                        "Approval of holders of 75% of ordinary shares is required for acquisitions, material borrowing and changes to the business plan.",
                    ),
                ),
                (
                    "Transfers",
                    (
                        "Customary pre-emption and permitted-transfer provisions apply. This agreement is governed by the laws of Ireland.",
                    ),
                ),
            ),
            template="slate",
        )
        self.text_pdf(
            "Legal/Corporate/Constitution.pdf",
            "legal",
            "constitution",
            title="Constitution",
            subtitle=f"{company} | private company limited by shares",
            sections=(
                (
                    "Objects and capacity",
                    (
                        "The company has full and unlimited capacity to carry on business, subject to applicable Irish law.",
                    ),
                ),
                (
                    "Share capital",
                    (
                        "The issued capital comprises 1,000,000 ordinary shares with one vote per share.",
                    ),
                ),
                (
                    "Directors",
                    (
                        "The board may exercise all powers not reserved to members. Quorum is two directors.",
                    ),
                ),
            ),
            template="green",
        )

        redacted_rows = [
            [f"Employee Master - Redacted | {SYNTHETIC_LABEL}"],
            ["Scope", "61 records supplied; three payroll records omitted pending HR review"],
            ["Employee ID", "Name", "Department", "Client", "Salary", "Start date"],
        ]
        for employee in self.data["employees"][:61]:
            redacted_rows.append(
                [
                    employee["employee_id"],
                    "REDACTED",
                    employee["department"],
                    employee["client_code"],
                    employee["annual_salary"],
                    employee["start_date"],
                ]
            )
        self.workbook(
            "Legal/Employment/Employee_Master_Redacted.xlsx",
            "legal",
            "employee_master",
            (SheetSpec("Employees", redacted_rows, currency_columns=frozenset({5})),),
            quirks=("workforce_mismatch_evidence", "redacted_data"),
        )
        contractor_rows = [
            [f"Contractor List | {SYNTHETIC_LABEL}"],
            ["Scope", "12 active contractors at 30 June 2026"],
            ["Contractor ID", "Name", "Client", "Monthly fee", "End date"],
        ]
        for contractor in self.data["contractors"]:
            contractor_rows.append(
                [
                    contractor["contractor_id"],
                    contractor["name"],
                    contractor["client_code"],
                    contractor["monthly_fee"],
                    contractor["end_date"],
                ]
            )
        self.workbook(
            "Legal/Employment/Contractor_List.xlsx",
            "legal",
            "contractor_list",
            (SheetSpec("Contractors", contractor_rows, currency_columns=frozenset({4})),),
            quirks=("workforce_mismatch_evidence",),
        )
        self.text_pdf(
            "Legal/Employment/Employment_Contract_Sample.pdf",
            "legal",
            "employment_contract",
            title="Sample Employment Contract",
            subtitle=f"{company} | fictional standard form",
            sections=(
                (
                    "Appointment",
                    (
                        "The employee is appointed as a delivery analyst in Ireland with a six-month probation period.",
                    ),
                ),
                (
                    "Compensation",
                    (
                        "Salary is payable monthly subject to PAYE, PRSI and other statutory deductions.",
                    ),
                ),
                (
                    "Confidentiality and IP",
                    (
                        "Work product created in the course of employment belongs to the Company, subject to applicable law.",
                    ),
                ),
            ),
            template="slate",
        )
        self.text_pdf(
            "Legal/Employment/Contractor_Agreement_Sample.pdf",
            "legal",
            "contractor_agreement",
            title="Sample Independent Contractor Agreement",
            subtitle=f"{company} | fictional standard form",
            sections=(
                (
                    "Services",
                    (
                        "The contractor provides scoped analytics services and controls the manner of performance, subject to deliverable standards.",
                    ),
                ),
                (
                    "Status",
                    (
                        "The parties intend an independent contractor relationship. Tax and classification consequences remain subject to actual working practices.",
                    ),
                ),
                ("Termination", ("Either party may terminate on 30 days' notice.",)),
            ),
            template="green",
        )
        self.text_pdf(
            "Legal/Employment/Payslip_Sample.pdf",
            "legal",
            "payslip",
            title="Sample Payslip",
            subtitle=f"{company} | June 2026 | employee data redacted",
            sections=(
                (
                    "Pay details",
                    (
                        "Employee: REDACTED. Gross pay EUR 5,250; PAYE EUR 1,080; PRSI EUR 210; USC EUR 168; net pay EUR 3,792.",
                    ),
                ),
                ("Notice", (SYNTHETIC_LABEL,)),
            ),
            table=(
                ("Item", "Amount"),
                ("Gross pay", "EUR 5,250"),
                ("PAYE", "EUR 1,080"),
                ("PRSI", "EUR 210"),
                ("USC", "EUR 168"),
                ("Net pay", "EUR 3,792"),
            ),
            template="navy",
        )

        contracts = [
            (
                "Harbourlight",
                "Harbourlight Stores Limited",
                "Harbourlight Mutual Group",
                "The supplier must obtain the customer's prior written consent following any change of control of the supplier.",
                "Liability is capped at twelve months of fees.",
            ),
            (
                "Mosaic_North",
                "Mosaic North Retail Limited",
                "Mosaic Arc Group",
                "Assignment is permitted within the Mosaic Arc Group.",
                "The supplier's aggregate liability shall not exceed three months of fees.",
            ),
            (
                "Mosaic_South",
                "Mosaic South Trading Limited",
                "Mosaic Arc Group",
                "Mosaic South Trading Limited confirms it is controlled by Mosaic Arc Group.",
                "Liability is capped at six months of fees.",
            ),
        ]
        for slug, customer, group, control, liability in contracts:
            self.text_pdf(
                f"Legal/Customer Contracts/Customer_Framework_{slug}.pdf",
                "legal",
                "customer_framework",
                title=f"Customer Framework Agreement - {slug.replace('_', ' ')}",
                subtitle=f"Between {company} and {customer}",
                sections=(
                    ("Parties and group", (f"Customer: {customer}. Corporate group: {group}.",)),
                    (
                        "Services",
                        (
                            "The supplier provides route-optimisation software, implementation and support services under annual statements of work.",
                        ),
                    ),
                    ("Control and assignment", (control,)),
                    ("Liability", (liability,)),
                ),
                template="slate",
                quirks=("customer_group_relationship",)
                if "Mosaic" in slug
                else ("change_of_control_clause",),
            )
        self.text_pdf(
            "Legal/Customer Contracts/Amendment_Harbourlight_2025.pdf",
            "legal",
            "contract_amendment",
            title="Amendment No. 1 - Harbourlight",
            subtitle="Effective 1 January 2025",
            sections=(
                (
                    "Commercial extension",
                    (
                        "The subscription term is extended to 31 December 2027 and annual fees increase by 4% each January.",
                    ),
                ),
                (
                    "Continuing effect",
                    (
                        "Clause 14.2 remains in full force, including the consent requirement following a change of control.",
                    ),
                ),
            ),
            template="green",
            quirks=("change_of_control_confirmation",),
        )
        self.text_pdf(
            "Legal/Customer Contracts/Amendment_Mosaic_2026.pdf",
            "legal",
            "contract_amendment",
            title="Amendment No. 2 - Mosaic North",
            subtitle="Signed 18 February 2026 | later operative version",
            sections=(
                (
                    "Priority",
                    (
                        "This amendment is later in date and prevails over inconsistent terms in the original framework.",
                    ),
                ),
                (
                    "Replacement liability clause",
                    (
                        "This amendment supersedes Clause 11 in its entirety. The supplier's liability for service failure is increased to twelve months of fees and service credits are uncapped.",
                    ),
                ),
            ),
            template="navy",
            quirks=("later_amendment", "supersedes_favourable_terms"),
            supersedes="Legal/Customer Contracts/Customer_Framework_Mosaic_North.pdf",
        )
        self.text_pdf(
            "Legal/Customer Contracts/Amendment_Mosaic_South_2025.pdf",
            "legal",
            "contract_amendment",
            title="Amendment No. 1 - Mosaic South",
            subtitle="Signed 30 September 2025",
            sections=(
                ("Scope", ("Adds two depots and extends the service term by eighteen months.",)),
                ("Other terms", ("All other terms remain unchanged.",)),
            ),
            template="green",
        )
        self.text_pdf(
            "Legal/Dispute/Client_Complaint_Letter.pdf",
            "legal",
            "client_dispute",
            title="Client Complaint",
            subtitle="Glencree Health Systems Limited | 4 May 2026",
            sections=(
                (
                    "Complaint",
                    (
                        "Glencree alleges three priority-one incidents exceeded the four-hour response target and seeks EUR 85,000 in service credits.",
                    ),
                ),
                (
                    "Requested response",
                    (
                        "Please provide a remediation plan and confirm whether recovery procedures were exercised.",
                    ),
                ),
            ),
            template="slate",
        )
        self.text_pdf(
            "Legal/Dispute/Company_Response.pdf",
            "legal",
            "client_dispute_response",
            title="Response to Client Complaint",
            subtitle=f"{company} | 12 May 2026",
            sections=(
                (
                    "Position",
                    (
                        "The company accepts two response-time misses but disputes the calculation of credits. It offers EUR 24,000 without admission of liability.",
                    ),
                ),
                (
                    "Remediation",
                    (
                        "Monitoring thresholds were adjusted. A full recovery exercise has not yet been scheduled.",
                    ),
                ),
            ),
            template="navy",
        )

        purchase_scan = self.record(
            "Legal/Property/Property_Purchase_Contract_Scanned.pdf",
            "legal",
            "property_purchase",
            quirks=("image_only_pdf", "large_scanned_contract"),
        )
        write_image_only_pdf(
            purchase_scan,
            title="Historic Property Purchase Contract",
            page_lines=(
                (
                    "Vendor: Alder Quay Holdings (Synthetic) Limited.",
                    "Purchaser: Larkspur Transit Analytics Limited.",
                    "Consideration EUR 690,000.",
                ),
                (
                    "The property is fictional Unit 6, Bracken Loop, Cork C99 SYN8.",
                    "Completion occurred on 12 March 2019.",
                ),
                ("Standard synthetic title warranties and planning provisions apply.",),
            ),
            seed=self.seed + 40,
        )
        sale_scan = self.record(
            "Legal/Property/Property_Sale_Contract_Scanned.pdf",
            "legal",
            "property_sale",
            quirks=("image_only_pdf", "large_scanned_contract"),
        )
        write_image_only_pdf(
            sale_scan,
            title="Property Sale Contract",
            page_lines=(
                (
                    "Vendor: Larkspur Transit Analytics Limited.",
                    "Purchaser: Rowan Loop Estates (Synthetic) Limited.",
                    "Consideration EUR 820,000.",
                ),
                (
                    "Completion date 15 October 2024.",
                    "Vacant possession was promised at completion.",
                ),
                ("A retention of EUR 45,000 remains for fictional snagging items.",),
            ),
            seed=self.seed + 50,
        )
        self.text_pdf(
            "Legal/Property/Head_Office_Lease.pdf",
            "legal",
            "lease",
            title="Head Office Lease",
            subtitle="14 Alder Quay, Kilnmore Business Park, Dublin D99 SYN4",
            sections=(
                (
                    "Term",
                    (
                        "The term runs from 1 January 2022 to 31 December 2031 at annual rent EUR 310,000.",
                    ),
                ),
                (
                    "Assignment and control",
                    (
                        "Assignment requires landlord consent, not to be unreasonably withheld. A corporate change of control is not itself an assignment.",
                    ),
                ),
                (
                    "Break",
                    (
                        "The tenant may break on 31 December 2028 on nine months' notice and payment of all rent.",
                    ),
                ),
            ),
            template="slate",
        )

        self.text_pdf(
            "Legal/Insurance/Employers_and_Public_Liability_Certificate.pdf",
            "legal",
            "insurance_certificate",
            title="Employers and Public Liability Certificate",
            subtitle="Policy SYN-EPL-77190 | expires 28 February 2027",
            sections=(
                ("Insured", (company,)),
                (
                    "Limits",
                    (
                        "Employers liability EUR 13,000,000; public liability EUR 10,000,000 per occurrence.",
                    ),
                ),
                ("Notice", (SYNTHETIC_LABEL,)),
            ),
            template="green",
        )
        self.text_pdf(
            "Legal/Insurance/Cyber_Insurance_Certificate.pdf",
            "legal",
            "insurance_certificate",
            title="Cyber Insurance Certificate",
            subtitle="Policy SYN-CYB-44018 | expires 28 February 2027",
            sections=(
                ("Insured", (company,)),
                ("Limit", ("Aggregate limit EUR 2,000,000; retention EUR 75,000.",)),
                (
                    "Conditions",
                    (
                        "Coverage is subject to multi-factor authentication declarations and incident notification within 72 hours.",
                    ),
                ),
            ),
            template="navy",
        )
        self.text_pdf(
            "Legal/Insurance/Fleet_Insurance_Schedule.pdf",
            "legal",
            "fleet_insurance",
            title="Fleet Insurance Schedule",
            subtitle="Policy SYN-FLT-10288 | 18 vehicles",
            sections=(
                (
                    "Schedule",
                    (
                        "Eighteen fictional service vehicles are insured for business use in Ireland through 31 January 2027.",
                    ),
                ),
                (
                    "Finance interests",
                    (
                        "Fleetcraft Leasing Limited is noted as interested party for financed vehicles.",
                    ),
                ),
            ),
            template="green",
        )
        self.text_pdf(
            "Legal/Licences/Trade_Licence_and_Registration.pdf",
            "legal",
            "trade_licence",
            title="Road-Data Processing Registration",
            subtitle="Synthetic registration SYN-LIC-44218",
            sections=(
                ("Holder", (company,)),
                (
                    "Scope",
                    (
                        "Registration covers processing of fictional fleet telematics for route optimisation.",
                    ),
                ),
                ("Expiry", ("31 May 2027. This is not a real statutory licence.",)),
            ),
            template="slate",
        )
        self.text_pdf(
            "Legal/Operational Providers/HR_Provider_Agreement.pdf",
            "legal",
            "hr_provider_agreement",
            title="Managed HR and Payroll Agreement",
            subtitle="Northmere HR Services Limited | effective 1 July 2024",
            sections=(
                (
                    "Services",
                    (
                        "Payroll processing, HR helpline and template policy maintenance for annual fee EUR 96,000.",
                    ),
                ),
                (
                    "Data",
                    (
                        "Personal data is processed in Ireland. The supplier must notify incidents without undue delay.",
                    ),
                ),
                (
                    "Termination",
                    ("Either party may terminate on 60 days' notice after the initial term.",),
                ),
            ),
            template="green",
        )
        self.text_pdf(
            "Legal/Operational Providers/Web_Hosting_Agreement.pdf",
            "legal",
            "web_hosting_agreement",
            title="Managed Hosting Agreement",
            subtitle="Juniper Hosting Services Limited | effective 1 April 2023",
            sections=(
                (
                    "Services",
                    ("Managed hosting, monitoring and daily backups for annual fee EUR 420,000.",),
                ),
                (
                    "Service levels",
                    (
                        "Monthly availability target is 99.5%. Service credits are the sole contractual remedy.",
                    ),
                ),
                (
                    "Recovery and security",
                    (
                        "No contractual recovery time objective is stated. Restore tests are performed on request; no annual witnessed test, penetration-test report or independent assurance report is committed.",
                    ),
                ),
            ),
            template="navy",
            quirks=("weak_it_recovery_evidence",),
        )

        board = self.record("Legal/Governance/Board_Minutes.docx", "legal", "board_minutes")
        write_docx(
            board,
            title="Minutes of a Meeting of the Board",
            subtitle=company,
            metadata=(
                ("Date", "24 June 2026"),
                ("Location", "Alder Quay"),
                ("Dataset", DATASET_ID),
            ),
            sections=(
                (
                    "Attendance",
                    (
                        "Nessa Brannock, Ciar Mollen and Orla Fenwick attended. Quorum was confirmed.",
                    ),
                ),
                (
                    "Trading",
                    (
                        "The board reviewed June management accounts and the transformation adjustment. Further support was requested before year end.",
                    ),
                ),
                (
                    "Financing",
                    (
                        "The board noted the term loan and innovation loan. HP agreements were not included in the finance paper.",
                    ),
                ),
                (
                    "IT resilience",
                    (
                        "Management will schedule a restore test after the summer release. No date was approved.",
                    ),
                ),
            ),
            tables=(
                (
                    ("Resolution", "Outcome"),
                    (
                        ("Approve 2026 forecast", "Approved"),
                        ("Obtain EBITDA-adjustment support", "Action open"),
                        ("Schedule recovery test", "Action open"),
                    ),
                ),
            ),
        )
        screenshot = self.record(
            "Legal/Corporate/CRO_Search_Screenshot.png",
            "legal",
            "cro_screenshot",
            quirks=("screenshot_instead_of_extract",),
        )
        write_cro_screenshot(
            screenshot, company=company, registration_id=self.data["company"]["registration_id"]
        )

        self.text_pdf(
            "Legal/Work Permits/Registration.pdf",
            "legal",
            "work_permit",
            title="Synthetic Work Permit Acknowledgement",
            subtitle="Employee reference EMP-044 | fictional",
            sections=(
                (
                    "Acknowledgement",
                    (
                        "A fictional employment-permit renewal was received on 3 March 2026 and is valid through 28 February 2028.",
                    ),
                ),
                ("Privacy", ("Personal identifiers are redacted in this visible-room copy.",)),
            ),
            template="green",
            quirks=("same_basename_different_directory",),
        )
        self.text_pdf(
            "Legal/Business Registration/Registration.pdf",
            "legal",
            "business_registration",
            title="Business Name Registration",
            subtitle="Larkspur RouteWorks | synthetic trading name",
            sections=(
                (
                    "Registration",
                    (
                        "Larkspur RouteWorks is a fictional business name of Larkspur Transit Analytics Limited.",
                    ),
                ),
                ("Identifier", ("Synthetic registration BN-SYN-50812.",)),
            ),
            template="slate",
            quirks=("same_basename_different_directory",),
        )
        self.text_pdf(
            "Legal/Corporate/Tax_Payment_Confirmation.pdf",
            "legal",
            "wrong_folder_tax_document",
            title="ROS-Style Tax Payment Confirmation",
            subtitle="Corporation tax payment | filed in the wrong folder",
            sections=(
                (
                    "Payment",
                    (
                        "A fictional corporation tax payment of EUR 210,000 was recorded on 23 September 2025.",
                    ),
                ),
                (
                    "Classification",
                    ("This tax document is deliberately placed under Legal/Corporate.",),
                ),
            ),
            template="green",
            quirks=("wrong_folder_document",),
        )
        corrupt = self.record(
            "Legal/Legacy/Unreadable_Policy_Archive.pdf",
            "legal",
            "legacy_policy",
            quirks=("partially_corrupted", "unreadable_file"),
            expected_readability="unreadable",
        )
        write_corrupt_pdf(corrupt)

        # Preserve the intentional empty folder in Git without creating a source artifact.
        empty_directory = self.room / "Legal/Legal 2.1"
        empty_directory.mkdir(parents=True, exist_ok=True)
        (empty_directory / EMPTY_DIRECTORY_MARKER).write_bytes(EMPTY_DIRECTORY_MARKER_CONTENT)

        zip_members: dict[str, bytes] = {}
        zip_members["Updated Responses/Legal_Questionnaire_Rev2.docx"] = bytes_from_writer(
            write_docx,
            ".docx",
            title="Legal Questionnaire - Rev2",
            subtitle=f"Updated answers for {company}",
            metadata=(("Version", "Rev2"), ("Date", "29 July 2026")),
            sections=(
                (
                    "Updates",
                    (
                        "The customer consent review remains in progress. Hosting recovery metrics are not contractually documented.",
                    ),
                ),
            ),
            tables=(
                (
                    ("Question", "Rev2 answer"),
                    (
                        ("Change-of-control consents", "Under legal review"),
                        ("Penetration testing", "No report available"),
                    ),
                ),
            ),
        )
        unredacted_rows = [
            [f"Employee Master - Unredacted | {SYNTHETIC_LABEL}"],
            ["Warning", "Synthetic personal data included for privacy testing"],
            [
                "Employee ID",
                "Name",
                "Department",
                "Work email",
                "Personal email",
                "Synthetic PPS-like ID",
            ],
        ]
        for employee in self.data["employees"]:
            unredacted_rows.append(
                [
                    employee["employee_id"],
                    employee["name"],
                    employee["department"],
                    employee["work_email"],
                    employee["personal_email"],
                    employee["synthetic_pps_like_id"],
                ]
            )
        zip_members["Updated Responses/Employee_Master_Unredacted.xlsx"] = bytes_from_writer(
            write_xlsx, ".xlsx", (SheetSpec("Employees", unredacted_rows),)
        )
        cap_rev2 = [
            [f"Cap Table Rev2 | {SYNTHETIC_LABEL}"],
            ["As of", "2026-07-29"],
            ["Shareholder", "Shares", "Ownership"],
        ]
        for shareholder in self.data["company"]["shareholders"]:
            cap_rev2.append(
                [shareholder["name"], shareholder["ordinary_shares"], shareholder["ownership"]]
            )
        zip_members["Updated Responses/Cap_Table_Rev2.xlsx"] = bytes_from_writer(
            write_xlsx,
            ".xlsx",
            (
                SheetSpec(
                    "Cap Table",
                    cap_rev2,
                    integer_columns=frozenset({2}),
                    percent_columns=frozenset({3}),
                ),
            ),
        )
        zip_members["Updated Responses/Customer_Consent_Response.pdf"] = bytes_from_writer(
            write_text_pdf,
            ".pdf",
            title="Customer Consent Response",
            subtitle="Updated vendor response",
            sections=(
                (
                    "Status",
                    (
                        "Harbourlight consent has not been requested. Management believed the transaction would not trigger the clause.",
                    ),
                ),
            ),
            template="navy",
            metadata=(("Dataset", DATASET_ID),),
        )
        zip_members["Updated Responses/Lease_Consent_Response.pdf"] = bytes_from_writer(
            write_text_pdf,
            ".pdf",
            title="Lease Consent Response",
            subtitle="Updated vendor response",
            sections=(
                ("Status", ("No landlord consent is believed required solely for a share sale.",)),
            ),
            template="green",
            metadata=(("Dataset", DATASET_ID),),
        )
        zip_members["Updated Responses/Insurance_Response.pdf"] = bytes_from_writer(
            write_text_pdf,
            ".pdf",
            title="Insurance Response",
            subtitle="Updated vendor response",
            sections=(
                ("Status", ("Certificates have been supplied. Cyber limit is EUR 2,000,000.",)),
            ),
            template="slate",
            metadata=(("Dataset", DATASET_ID),),
        )
        zip_members["Updated Responses/IT_Security_Response.docx"] = bytes_from_writer(
            write_docx,
            ".docx",
            title="IT Security Response",
            subtitle="Updated response",
            metadata=(("Date", "29 July 2026"), ("Dataset", DATASET_ID)),
            sections=(
                (
                    "Controls",
                    (
                        "Multi-factor authentication is enabled for administrators. No independent penetration test or witnessed disaster-recovery exercise has been supplied.",
                    ),
                ),
            ),
        )
        zip_members["Updated Responses/PAYE_Reconciliation.csv"] = (
            f"notice,employee_count,period\n{SYNTHETIC_LABEL},64,2026-06\n"
        ).encode()
        zip_members["Updated Responses/CRO_Search_Refresh.png"] = bytes_from_writer(
            write_cro_screenshot,
            ".png",
            company=company,
            registration_id=self.data["company"]["registration_id"],
        )
        zip_members["Updated Responses/Director_Declaration.pdf"] = bytes_from_writer(
            write_text_pdf,
            ".pdf",
            title="Director Declaration",
            subtitle="Synthetic signed response",
            sections=(
                (
                    "Declaration",
                    (
                        "The director declares that the response archive is complete to the best of her knowledge, subject to stated exceptions.",
                    ),
                ),
            ),
            template="navy",
            metadata=(("Dataset", DATASET_ID),),
        )
        zip_relative = "Legal/Updated_Responses.zip"
        zip_path = self.record(
            zip_relative,
            "legal",
            "updated_responses_archive",
            quirks=("archive_with_updated_versions", "contains_unredacted_employee_list"),
        )
        write_stable_zip(zip_path, zip_members)
        for member_name in sorted(zip_members):
            suffix = Path(member_name).suffix.lower().lstrip(".")
            member_quirks: list[str] = ["zip_member"]
            if "Unredacted" in member_name:
                member_quirks.extend(["synthetic_unredacted_personal_data", "privacy_exposure"])
            if "Rev2" in member_name:
                member_quirks.append("updated_version")
            self.records.append(
                ArtifactRecord(
                    path=f"{zip_relative}!{member_name}",
                    workstream="legal",
                    family="updated_response_member",
                    declared_format=suffix,
                    visible=False,
                    container=zip_relative,
                    member_path=member_name,
                    quirks=member_quirks,
                )
            )

    def generate_tax(self) -> None:
        vat_periods = self.data["tax"]["vat_periods"]
        for index, item in enumerate(vat_periods):
            self.text_pdf(
                f"Tax/VAT/VAT3_{item['period'].replace('-', '_')}.pdf",
                "tax",
                "vat3_return",
                title=f"VAT3-Style Return {item['period']}",
                subtitle="ROS-style fictional VAT return",
                sections=(
                    (
                        "Return",
                        (
                            f"Output VAT: EUR {item['output_vat']:,}. Input VAT: EUR {item['input_vat']:,}. VAT payable: EUR {item['payable']:,}.",
                        ),
                    ),
                    ("Declaration", (SYNTHETIC_LABEL,)),
                ),
                table=(
                    ("Field", "Amount"),
                    ("T1 Output VAT", f"EUR {item['output_vat']:,}"),
                    ("T2 Input VAT", f"EUR {item['input_vat']:,}"),
                    ("Net payable", f"EUR {item['payable']:,}"),
                ),
                template=("green", "slate", "navy", "green")[index],
            )
            self.text_pdf(
                f"Tax/VAT/Xero_VAT_Summary_{item['period'].replace('-', '_')}.pdf",
                "tax",
                "xero_vat_summary",
                title=f"Xero-Style VAT Summary {item['period']}",
                subtitle="Fictional accounting-system summary",
                sections=(
                    (
                        "Summary",
                        (
                            f"Sales tax EUR {item['output_vat']:,}; purchase tax EUR {item['input_vat']:,}; amount due EUR {item['payable']:,}.",
                        ),
                    ),
                    (
                        "Reconciliation",
                        ("The original return agrees to this summary before any later amendment.",),
                    ),
                ),
                template=("slate", "navy", "green", "slate")[index],
            )
        amended = vat_periods[1]
        self.text_pdf(
            "Tax/VAT/VAT3_2025_P2_AMENDED.pdf",
            "tax",
            "amended_vat_return",
            title="VAT3-Style Return 2025-P2 - AMENDED",
            subtitle="Amended on 19 August 2025",
            sections=(
                (
                    "Amendment",
                    (
                        f"Original payable: EUR {amended['payable']:,}. Amended payable: EUR {amended['amended_payable']:,}. Increase: EUR {amended['amended_payable'] - amended['payable']:,}.",
                    ),
                ),
                (
                    "Reason",
                    ("A late supplier credit note was reclassified after the original filing.",),
                ),
            ),
            template="navy",
            quirks=("amended_tax_document", "original_and_amended"),
            supersedes="Tax/VAT/VAT3_2025_P2.pdf",
        )

        self.text_pdf(
            "Tax/ROS Screens/VAT_Charges_and_Payments.pdf",
            "tax",
            "vat_charges_payments",
            title="ROS-Style VAT Charges and Payments",
            subtitle="Account view through 30 June 2026",
            sections=(
                (
                    "Charges",
                    (
                        "2025-P1 EUR 166,000; 2025-P2 original EUR 174,000; amendment EUR 8,000; 2025-P3 EUR 179,000; 2025-P4 EUR 192,000.",
                    ),
                ),
                ("Payments", ("All listed charges were paid. No enforcement balance is shown.",)),
            ),
            template="green",
        )
        paye = self.data["tax"]["paye"]
        self.text_pdf(
            "Tax/ROS Screens/PAYE_Returns.pdf",
            "tax",
            "paye_returns",
            title="ROS-Style PAYE Returns",
            subtitle="Employer account 2025",
            sections=(
                (
                    "Returns",
                    (
                        f"Registered PAYE headcount: {paye['registered_headcount']}. Annual liability: EUR {paye['annual_liability_2025']:,}.",
                    ),
                ),
                ("Status", ("Twelve monthly submissions recorded.",)),
            ),
            template="slate",
            quirks=("workforce_mismatch_evidence",),
        )
        self.text_pdf(
            "Tax/ROS Screens/PAYE_Payments.pdf",
            "tax",
            "paye_payments",
            title="ROS-Style PAYE Payments",
            subtitle="Employer account 2025",
            sections=(
                (
                    "Payments",
                    (
                        f"Total payments: EUR {paye['paid_2025']:,}. Returns and payments agree for the year.",
                    ),
                ),
            ),
            template="green",
        )
        ct = self.data["tax"]["corporation_tax"]
        self.text_pdf(
            "Tax/ROS Screens/CT_Return_2025.pdf",
            "tax",
            "ct_return",
            title="Corporation Tax Return 2025",
            subtitle="ROS-style fictional return",
            sections=(
                (
                    "Assessment",
                    (
                        f"Corporation tax liability EUR {ct['return_liability']:,} for period {ct['period']}.",
                    ),
                ),
            ),
            template="navy",
        )
        self.text_pdf(
            "Tax/ROS Screens/CT_Payment.pdf",
            "tax",
            "ct_payment",
            title="Corporation Tax Payment",
            subtitle="ROS-style account entry",
            sections=(("Payment", (f"Payments on account total EUR {ct['payments']:,}.",)),),
            template="green",
        )
        self.text_pdf(
            "Tax/ROS Screens/CT_Charge.pdf",
            "tax",
            "ct_charge",
            title="Corporation Tax Charge",
            subtitle="ROS-style account entry",
            sections=(("Charge", (f"Late amendment charge EUR {ct['charge']:,}.",)),),
            template="slate",
        )
        self.text_pdf(
            "Tax/ROS Screens/CT_Refund.pdf",
            "tax",
            "ct_refund",
            title="Corporation Tax Refund",
            subtitle="ROS-style account entry",
            sections=(("Refund", (f"Refund issued EUR {ct['refund']:,}.",)),),
            template="green",
        )

        for year in (2023, 2024, 2025):
            fy = next(item for item in self.data["financial_years"] if item["year"] == year)
            adjusted = fy["profit_before_tax"] + (35_000 if year == 2025 else 22_000)
            tax = int(adjusted * 0.125)
            self.text_pdf(
                f"Tax/Computations/Tax_Computation_{year}.pdf",
                "tax",
                "tax_computation",
                title=f"Corporation Tax Computation {year}",
                subtitle="Fictional Irish-company computation",
                sections=(
                    (
                        "Trading result",
                        (
                            f"Profit before tax per accounts EUR {fy['profit_before_tax']:,}. Tax adjustments EUR {adjusted - fy['profit_before_tax']:,}. Taxable trading profit EUR {adjusted:,}.",
                        ),
                    ),
                    (
                        "Tax",
                        (
                            f"Illustrative corporation tax at 12.5%: EUR {tax:,}. This fixture is not tax advice.",
                        ),
                    ),
                ),
                template=("slate", "green", "navy")[(year - 2023) % 3],
            )
        self.text_pdf(
            "Tax/Registration/ROS_Registration_Details.pdf",
            "tax",
            "ros_registration",
            title="ROS-Style Registration Details",
            subtitle="Synthetic taxpayer profile",
            sections=(
                (
                    "Registrations",
                    (
                        f"VAT identifier {self.data['company']['vat_id']}; PAYE employer reference SYN-PAYE-52019; corporation tax reference SYN-CT-748291.",
                    ),
                ),
                ("Contact", ("Electronic correspondence address tax@larkspur.invalid.",)),
            ),
            template="slate",
        )
        self.text_pdf(
            "Tax/Registration/Tax_Clearance_Certificate.pdf",
            "tax",
            "tax_clearance",
            title="Tax Clearance Certificate",
            subtitle="Synthetic certificate - not valid for use",
            sections=(
                (
                    "Status",
                    (
                        f"Tax clearance is shown as current through {self.data['tax']['tax_clearance_expiry']}.",
                    ),
                ),
                ("Notice", (SYNTHETIC_LABEL,)),
            ),
            template="green",
        )

        csv_path = self.record(
            "Tax/Trial Balance/Trial_Balance_2024.xlsx",
            "tax",
            "tax_trial_balance",
            quirks=("csv_bytes_xlsx_extension", "extension_mismatch"),
        )
        write_csv_bytes_with_xlsx_extension(
            csv_path,
            (
                (f"{SYNTHETIC_LABEL}", ""),
                ("Account", "Debit", "Credit"),
                ("Revenue", 0, 11_400_000),
                ("Costs", 9_680_000, 0),
                ("Tax", 273_000, 0),
            ),
        )
        tax_tb_rows = [
            [f"Tax Trial Balance 2025 | {SYNTHETIC_LABEL}"],
            ["Period", "2025"],
            ["Account", "Debit", "Credit"],
            ["Corporation tax expense", 0, self.data["financial_years"][-1]["corporation_tax"]],
            ["Corporation tax paid", self.data["tax"]["corporation_tax"]["payments"], 0],
            ["VAT control", 182_000, 0],
            ["PAYE control", 0, 132_000],
        ]
        self.workbook(
            "Tax/Trial Balance/Trial_Balance_2025.xlsx",
            "tax",
            "tax_trial_balance",
            (SheetSpec("Tax TB", tax_tb_rows, currency_columns=frozenset({2, 3})),),
        )
        invoices = [
            ("INV-SYN-2401", "Harbourlight Stores Limited", 118_000, 27_140),
            ("INV-SYN-2402", "Mosaic North Retail Limited", 96_000, 22_080),
            ("INV-SYN-2403", "Glencree Health Systems Limited", 142_000, 32_660),
            ("INV-SYN-2404", "Mosaic South Trading Limited", 84_000, 19_320),
        ]
        for number, customer, net, vat in invoices:
            self.text_pdf(
                f"Tax/Invoice Samples/{number}.pdf",
                "tax",
                "invoice_sample",
                title=f"Tax Invoice {number}",
                subtitle=f"Supplier: {self.data['company']['legal_name']}",
                sections=(
                    ("Bill to", (customer,)),
                    ("Services", ("Fleet analytics subscription and implementation services.",)),
                ),
                table=(
                    ("Description", "Net", "VAT", "Gross"),
                    ("Services", f"EUR {net:,}", f"EUR {vat:,}", f"EUR {net + vat:,}"),
                ),
                template="navy",
            )
        invoice_rows = [
            [f"Invoice Sample Register | {SYNTHETIC_LABEL}"],
            ["Period", "2025 sample"],
            ["Invoice", "Customer", "Net", "VAT", "Gross"],
        ]
        for number, customer, net, vat in invoices:
            invoice_rows.append([number, customer, net, vat, net + vat])
        invoice_rows.append(
            [
                "Total",
                "",
                FormulaCell("SUM(C4:C7)", 440_000, style=8),
                FormulaCell("SUM(D4:D7)", 101_200, style=8),
                FormulaCell("SUM(E4:E7)", 541_200, style=8),
            ]
        )
        self.workbook(
            "Tax/Invoice Samples/Invoice_Register.xlsx",
            "tax",
            "invoice_register",
            (SheetSpec("Register", invoice_rows, currency_columns=frozenset({3, 4, 5})),),
        )

        original = [
            [f"Tax Response Summary | {SYNTHETIC_LABEL}"],
            ["Version", "Original", "Date", "2026-07-15"],
            ["Question", "Answer", "Owner", "Status"],
            ["Are all VAT returns filed?", "Yes", "Tax", "Complete"],
            ["Have any VAT returns been amended?", "Yes - 2025-P2", "Tax", "Complete"],
            ["Any open PAYE liabilities?", "None", "Payroll", "Complete"],
            ["Tax clearance current?", "Yes", "Tax", "Complete"],
        ]
        rev2 = [
            [f"Tax Response Summary Rev2 | {SYNTHETIC_LABEL}"],
            ["Version", "Rev2", "Date", "2026-07-29"],
            ["Question", "Answer", "Owner", "Status"],
            ["Are all VAT returns filed?", "Yes", "Tax", "Complete"],
            [
                "Have any VAT returns been amended?",
                "No VAT returns have been amended",
                "CFO",
                "Complete",
            ],
            ["Any open PAYE liabilities?", "None", "Payroll", "Complete"],
            ["Tax clearance current?", "Yes", "Tax", "Complete"],
        ]
        self.workbook(
            "Tax/Tax_Response_Summary_Original.xlsx",
            "tax",
            "tax_response_summary",
            (SheetSpec("Responses", original),),
            quirks=("original_answers", "versioned_answers"),
        )
        self.workbook(
            "Tax/Tax_Response_Summary_Rev2.xlsx",
            "tax",
            "tax_response_summary",
            (SheetSpec("Responses", rev2, warning_cells=frozenset({"B5"})),),
            quirks=("rev2_answers", "superseded_version", "tax_response_inconsistency"),
            supersedes="Tax/Tax_Response_Summary_Original.xlsx",
        )

    def finalize_manifest(self, metadata_root: Path, issues_path: Path) -> dict[str, Any]:
        visible_records = [record for record in self.records if record.visible]
        member_records = [record for record in self.records if not record.visible]
        if len(visible_records) != 90:
            raise RuntimeError(
                f"generator composition error: expected 90 visible records, got {len(visible_records)}"
            )
        if len(member_records) != 10:
            raise RuntimeError(
                f"generator composition error: expected 10 archive members, got {len(member_records)}"
            )
        entries = []
        for record in self.records:
            item = asdict(record)
            if record.visible:
                path = self.room / record.path
                item["sha256"] = sha256_file(path)
                item["size_bytes"] = path.stat().st_size
            else:
                container_path = self.room / str(record.container)
                with zipfile.ZipFile(container_path) as archive:
                    payload = archive.read(str(record.member_path))
                item["sha256"] = sha256_bytes(payload)
                item["size_bytes"] = len(payload)
            entries.append(item)

        visible_counts = {
            name.lower(): sum(
                record.visible and record.path.startswith(f"{name}/") for record in self.records
            )
            for name in TOP_LEVELS
        }
        logical_counts = {
            name.lower(): sum(record.workstream == name.lower() for record in self.records)
            for name in TOP_LEVELS
        }
        format_counts: dict[str, int] = {}
        for record in self.records:
            format_counts[record.declared_format] = format_counts.get(record.declared_format, 0) + 1
        manifest = {
            "schema_version": 1,
            "dataset_id": DATASET_ID,
            "generator_version": GENERATOR_VERSION,
            "seed": self.seed,
            "generated_at": "2026-08-31T09:00:00Z",
            "provenance": {
                "entirely_fictional": True,
                "real_source_material_used": False,
                "external_research_used": False,
                "notice": SYNTHETIC_LABEL,
            },
            "counts": {
                "visible_files": len(visible_records),
                "zip_containers": sum(
                    record.visible and record.declared_format == "zip" for record in self.records
                ),
                "zip_members": len(member_records),
                "logical_documents": len(self.records),
                "visible_by_folder": visible_counts,
                "logical_by_workstream": logical_counts,
                "logical_by_format": dict(sorted(format_counts.items())),
            },
            "required_empty_folders": ["Legal/Legal 2.1"],
            "canonical_dataset": {
                "path": "canonical_dataset.json",
                "sha256": sha256_file(metadata_root / "canonical_dataset.json"),
            },
            "sealed_issue_config": {
                "path": "planted_issues/issues.json",
                "sha256": sha256_file(issues_path),
                "issue_count": 10,
            },
            "intentional_contradictions": [f"PI-{index:03d}" for index in range(1, 11)],
            "entries": entries,
        }
        stable_json(metadata_root / "room_manifest.json", manifest)
        return manifest


def _prepare_output(output: Path) -> None:
    resolved = output.resolve(strict=False)
    if resolved == Path(resolved.anchor) or resolved == Path.cwd().resolve():
        raise RuntimeError(f"refusing unsafe output path: {resolved}")
    if resolved.exists():
        unexpected = {path.name for path in resolved.iterdir()} - set(TOP_LEVELS)
        if unexpected:
            raise RuntimeError(
                f"refusing to replace output containing unexpected top-level items: {sorted(unexpected)}"
            )
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def generate(output: Path, metadata_root: Path, issues_path: Path, seed: int) -> dict[str, Any]:
    if seed != DEFAULT_SEED:
        raise RuntimeError(f"Phase 3 fixture currently locks seed {DEFAULT_SEED}")
    issues = json.loads(issues_path.read_text(encoding="utf-8"))
    if issues.get("issue_count") != 10 or len(issues.get("issues", [])) != 10:
        raise RuntimeError("sealed issue configuration must contain exactly 10 issues")
    _prepare_output(output)
    metadata_root.mkdir(parents=True, exist_ok=True)
    data = build_canonical_dataset(seed)
    stable_json(metadata_root / "canonical_dataset.json", data)
    builder = RoomBuilder(output.resolve(), data, seed)
    builder.generate_financial()
    builder.generate_legal()
    builder.generate_tax()
    manifest = builder.finalize_manifest(metadata_root.resolve(), issues_path.resolve())
    return manifest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("synthetic/data_room"),
        help="explicit room output directory",
    )
    parser.add_argument(
        "--metadata-root",
        type=Path,
        default=Path("synthetic"),
        help="directory for canonical dataset and manifest",
    )
    parser.add_argument(
        "--issues",
        type=Path,
        default=Path("synthetic/planted_issues/issues.json"),
        help="sealed issue configuration",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = generate(args.output, args.metadata_root, args.issues, args.seed)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"generation failed: {exc}", file=sys.stderr)
        return 1
    counts = manifest["counts"]
    print(
        f"Generated {counts['visible_files']} visible files and {counts['logical_documents']} logical documents"
    )
    print(f"Manifest: {(args.metadata_root / 'room_manifest.json').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
