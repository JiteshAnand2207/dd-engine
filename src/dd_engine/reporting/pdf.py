"""Deterministic in-process two-page A4 renderer for the IC brief."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
from reportlab.pdfbase.pdfmetrics import stringWidth  # type: ignore[import-untyped]
from reportlab.pdfgen.canvas import Canvas  # type: ignore[import-untyped]

from dd_engine.errors import ReportError
from dd_engine.evidence.models import JsonObject

PAGE_WIDTH: float = float(A4[0])
PAGE_HEIGHT: float = float(A4[1])
A4_SIZE = (PAGE_WIDTH, PAGE_HEIGHT)
LEFT = 38.0
RIGHT = 38.0
TOP = 38.0
BOTTOM = 38.0
CONTENT_WIDTH = PAGE_WIDTH - LEFT - RIGHT
BODY_FONT_SIZE = 8.4
BODY_LEADING = 10.2
SMALL_FONT_SIZE = 7.8
SMALL_LEADING = 9.4
FOOTER_FONT_SIZE = 7.5
TEXT_COLOUR = colors.HexColor("#20252B")


@dataclass(frozen=True, slots=True)
class PageLayout:
    """Recorded layout guardrails for one rendered page."""

    bottom_y: float
    line_count: int
    page_number: int


def _plain(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().replace("\u2011", "-")


def _objects(value: object) -> list[JsonObject]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _wrap(text: str, *, font: str, size: float, width: float) -> list[str]:
    words = _plain(text).split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if stringWidth(candidate, font, size) <= width:
            current = candidate
            continue
        lines.append(current)
        current = word
    lines.append(current)
    return lines


def _guard(y: float, leading: float) -> None:
    if y - leading < BOTTOM + 13:
        raise ReportError(
            "IC brief content exceeds its deterministic page frame; shorten content rather than "
            "clip it or reduce text below the readable font threshold"
        )


def _draw_lines(
    canvas: Canvas,
    lines: list[str],
    *,
    y: float,
    font: str = "Helvetica",
    size: float = BODY_FONT_SIZE,
    leading: float = BODY_LEADING,
    x: float = LEFT,
    colour: colors.Color | None = None,
) -> tuple[float, int]:
    canvas.setFillColor(colour or TEXT_COLOUR)
    canvas.setFont(font, size)
    for line in lines:
        _guard(y, leading)
        canvas.drawString(x, y, line)
        y -= leading
    return y, len(lines)


def _draw_paragraph(
    canvas: Canvas,
    text: object,
    *,
    y: float,
    size: float = BODY_FONT_SIZE,
    leading: float = BODY_LEADING,
    font: str = "Helvetica",
    x: float = LEFT,
    width: float = CONTENT_WIDTH,
) -> tuple[float, int]:
    return _draw_lines(
        canvas,
        _wrap(_plain(text), font=font, size=size, width=width),
        y=y,
        font=font,
        size=size,
        leading=leading,
        x=x,
    )


def _draw_heading(canvas: Canvas, title: str, *, y: float) -> tuple[float, int]:
    y -= 3
    _guard(y, 14)
    canvas.setFillColor(colors.HexColor("#0B4F6C"))
    canvas.setFont("Helvetica-Bold", 10.4)
    canvas.drawString(LEFT, y, title)
    y -= 13.5
    canvas.setStrokeColor(colors.HexColor("#B7CBD4"))
    canvas.setLineWidth(0.6)
    canvas.line(LEFT, y + 5.5, PAGE_WIDTH - RIGHT, y + 5.5)
    return y, 1


def _draw_bullets(
    canvas: Canvas,
    values: list[str],
    *,
    y: float,
    size: float = BODY_FONT_SIZE,
    leading: float = BODY_LEADING,
) -> tuple[float, int]:
    line_count = 0
    for value in values:
        wrapped = _wrap(value, font="Helvetica", size=size, width=CONTENT_WIDTH - 13)
        _guard(y, leading)
        canvas.setFillColor(colors.HexColor("#0B4F6C"))
        canvas.setFont("Helvetica-Bold", size)
        canvas.drawString(LEFT, y, "-")
        y, used = _draw_lines(
            canvas,
            wrapped,
            y=y,
            font="Helvetica",
            size=size,
            leading=leading,
            x=LEFT + 11,
        )
        line_count += used
        y -= 1.5
    return y, line_count


def _page_header(canvas: Canvas, run_id: str, page_number: int) -> float:
    canvas.setFillColor(colors.HexColor("#0B4F6C"))
    canvas.setFont("Helvetica-Bold", 15.2)
    canvas.drawString(LEFT, PAGE_HEIGHT - TOP, "Investment Committee brief")
    canvas.setFont("Helvetica", 8.2)
    canvas.setFillColor(colors.HexColor("#505A63"))
    canvas.drawRightString(PAGE_WIDTH - RIGHT, PAGE_HEIGHT - TOP + 1, "CONFIDENTIAL - SYNTHETIC")
    canvas.setStrokeColor(colors.HexColor("#0B4F6C"))
    canvas.setLineWidth(1.1)
    canvas.line(LEFT, PAGE_HEIGHT - TOP - 8, PAGE_WIDTH - RIGHT, PAGE_HEIGHT - TOP - 8)
    canvas.setFont("Helvetica", FOOTER_FONT_SIZE)
    canvas.setFillColor(colors.HexColor("#505A63"))
    canvas.drawString(LEFT, 23, f"Run {run_id}")
    canvas.drawRightString(PAGE_WIDTH - RIGHT, 23, f"Page {page_number} of 2")
    return float(PAGE_HEIGHT - TOP - 24)


def _draw_recommendation(canvas: Canvas, content: JsonObject, *, y: float) -> tuple[float, int]:
    recommendation = _plain(content.get("recommendation"))
    lines = _wrap(recommendation, font="Helvetica-Bold", size=9.0, width=CONTENT_WIDTH - 18)
    height = len(lines) * 11.0 + 15
    if y - height < BOTTOM + 13:
        raise ReportError("IC brief recommendation box would overflow")
    canvas.setFillColor(colors.HexColor("#EAF3F6"))
    canvas.roundRect(LEFT, y - height + 5, CONTENT_WIDTH, height, 4, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#0B4F6C"))
    canvas.setFont("Helvetica-Bold", 8.1)
    canvas.drawString(LEFT + 9, y - 7, "IC VIEW")
    y, count = _draw_lines(
        canvas,
        lines,
        y=y - 18,
        font="Helvetica-Bold",
        size=9.0,
        leading=11.0,
        x=LEFT + 9,
        colour=colors.HexColor("#15323F"),
    )
    return y - 4, count


def _page_one(canvas: Canvas, content: JsonObject) -> PageLayout:
    y = _page_header(canvas, str(content["run_id"]), 1)
    lines = 0
    y, used = _draw_recommendation(canvas, content, y=y)
    lines += used
    y, used = _draw_heading(canvas, "Transaction and thesis", y=y)
    lines += used
    y, used = _draw_paragraph(canvas, f"Transaction: {_plain(content.get('transaction'))}", y=y)
    lines += used
    y, used = _draw_paragraph(canvas, f"Thesis: {_plain(content.get('thesis'))}", y=y - 2)
    lines += used
    y, used = _draw_heading(canvas, "Headline financial reconciliation", y=y - 2)
    lines += used
    for item in _objects(content.get("headline")):
        citations = " ".join(_strings(item.get("citations")))
        text = f"{item.get('issue_id')}: {_plain(item.get('text'))} {citations}"
        y, used = _draw_bullets(
            canvas, [text], y=y, size=SMALL_FONT_SIZE, leading=SMALL_LEADING
        )
        lines += used
    y, used = _draw_heading(canvas, "Most material findings", y=y - 1)
    lines += used
    for item in _objects(content.get("material_findings")):
        citations = " ".join(_strings(item.get("citations")))
        text = (
            f"{item.get('issue_id')} / {item.get('workstream')}: "
            f"{_plain(item.get('text'))} {citations}"
        )
        y, used = _draw_bullets(
            canvas, [text], y=y, size=SMALL_FONT_SIZE, leading=SMALL_LEADING
        )
        lines += used
    return PageLayout(bottom_y=y, line_count=lines, page_number=1)


def _page_two(canvas: Canvas, content: JsonObject) -> PageLayout:
    y = _page_header(canvas, str(content["run_id"]), 2)
    lines = 0
    sections = (
        ("Go/no-go conditions", _strings(content.get("conditions"))),
        ("Price/structure protections", _strings(content.get("price_protections"))),
        ("Critical unanswered questions", _strings(content.get("unanswered"))),
        ("Immediate next actions", _strings(content.get("actions"))),
    )
    for title, values in sections:
        y, used = _draw_heading(canvas, title, y=y)
        lines += used
        y, used = _draw_bullets(canvas, values, y=y)
        lines += used
        y -= 1
    return PageLayout(bottom_y=y, line_count=lines, page_number=2)


def render_ic_brief_pdf(path: Path, content: JsonObject) -> tuple[PageLayout, PageLayout]:
    """Write exactly two deterministic A4 pages or fail before clipping content."""

    path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(
        str(path),
        pagesize=A4_SIZE,
        pageCompression=1,
        invariant=1,
    )
    run_id = str(content["run_id"])
    canvas.setTitle("Investment Committee brief")
    canvas.setAuthor("dd-engine")
    canvas.setSubject("Two-page acquisition due-diligence decision brief")
    canvas.setKeywords(f"dd-engine run_id {run_id}")
    page_one = _page_one(canvas, content)
    canvas.showPage()
    page_two = _page_two(canvas, content)
    canvas.showPage()
    canvas.save()
    return page_one, page_two
