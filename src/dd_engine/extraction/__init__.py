"""Tiered, local-first extraction with durable source locators."""

from dd_engine.extraction.models import ExtractionOutcome
from dd_engine.extraction.pipeline import extract_run

__all__ = ["ExtractionOutcome", "extract_run"]
