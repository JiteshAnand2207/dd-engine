"""Stable package and run-contract constants."""

from enum import StrEnum

RUN_DIRECTORY_NAMES = (
    "checkpoints",
    "logs",
    "source_register",
    "extracts",
    "intake",
    "evidence",
    "workstreams",
    "red_team",
    "outputs",
)

STAGE_ORDER = ("register", "extract", "intake", "analyse", "report", "validate")


class StageState(StrEnum):
    """All valid persistent states for a pipeline stage."""

    NOT_STARTED = "not_started"
    RUNNING = "running"
    AWAITING_INPUT = "awaiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    INVALIDATED = "invalidated"


VALID_STAGE_STATES = tuple(state.value for state in StageState)
