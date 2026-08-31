from __future__ import annotations

import json
from pathlib import Path

from dd_engine.artifacts import append_json_line


def test_jsonl_events_are_valid_and_appended_without_rewriting(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "events.jsonl"
    first_event = {"event": "run_created", "run_id": "run-1", "sequence": 1}
    second_event = {"event": "stage_started", "run_id": "run-1", "sequence": 2}

    append_json_line(log_path, first_event)
    original_bytes = log_path.read_bytes()
    append_json_line(log_path, second_event)

    final_bytes = log_path.read_bytes()
    records = [json.loads(line) for line in final_bytes.decode().splitlines()]
    assert final_bytes.startswith(original_bytes)
    assert records == [first_event, second_event]
