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


class SourcePathError(DDEngineError):
    """Raised when an explicit source-room path is missing or unsafe."""


class InventoryError(DDEngineError):
    """Raised when a source room cannot be inventoried safely."""


class ArchiveSafetyError(InventoryError):
    """Raised when archive metadata cannot be inspected safely."""


class ExtractionError(DDEngineError):
    """Raised when extraction cannot safely produce its required artifacts."""


class SourceIntegrityError(ExtractionError):
    """Raised when a registered source cannot be resolved with its recorded hash."""


class IntakeError(DDEngineError):
    """Raised when intake cannot safely generate or ingest its human packet."""


class EvidenceError(DDEngineError):
    """Raised when the evidence foundation cannot be built or trusted."""
