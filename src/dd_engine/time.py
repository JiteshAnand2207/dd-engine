"""UTC timestamp helpers kept in one place for consistent artifacts."""

from datetime import UTC, datetime


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp with a ``Z`` suffix."""

    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
