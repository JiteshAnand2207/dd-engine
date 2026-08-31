from dd_engine.errors import (
    ArchiveSafetyError,
    ArtifactError,
    ArtifactValidationError,
    ConfigError,
    DDEngineError,
    InventoryError,
    RunError,
    SourcePathError,
    StageTransitionError,
)


def test_application_errors_share_a_clear_hierarchy() -> None:
    assert issubclass(ConfigError, DDEngineError)
    assert issubclass(ArtifactError, DDEngineError)
    assert issubclass(RunError, DDEngineError)
    assert issubclass(StageTransitionError, RunError)
    assert issubclass(ArtifactValidationError, StageTransitionError)
    assert issubclass(SourcePathError, DDEngineError)
    assert issubclass(InventoryError, DDEngineError)
    assert issubclass(ArchiveSafetyError, InventoryError)
