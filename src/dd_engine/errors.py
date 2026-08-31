"""Application-specific exception hierarchy for dd-engine."""


class DDEngineError(Exception):
    """Base class for expected dd-engine application errors."""


class ConfigError(DDEngineError):
    """Raised when engine configuration is missing or unsafe."""


class ArtifactError(DDEngineError):
    """Raised when a run artifact is unsafe or invalid."""


class RunError(DDEngineError):
    """Raised when a run cannot be created, read or trusted."""


class StageTransitionError(RunError):
    """Raised for an unsafe or invalid stage transition."""


class ArtifactValidationError(StageTransitionError):
    """Raised when completion artifacts do not pass validation."""
