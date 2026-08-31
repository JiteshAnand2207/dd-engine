from dd_engine.errors import (
    ArtifactError,
    ArtifactValidationError,
    ConfigError,
    DDEngineError,
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
