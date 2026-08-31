"""Deterministic, read-only source-room inventory."""

from dd_engine.inventory.models import RegisterLimits, RegistrationOutcome
from dd_engine.inventory.register import register_room

__all__ = ["RegisterLimits", "RegistrationOutcome", "register_room"]
