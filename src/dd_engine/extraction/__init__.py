"""Tiered, local-first extraction with durable source locators."""

from dd_engine.extraction.models import ExtractionOutcome
from dd_engine.extraction.pipeline import extract_run
from dd_engine.extraction.vision import ingest_vision_review

__all__ = ["ExtractionOutcome", "extract_run", "ingest_vision_review"]
