from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_checked_in_delivery_manifest_passes() -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "validate_delivery_manifest.py"),
            "--manifest",
            str(root / "DELIVERY_MANIFEST.md"),
            "--json",
        ],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
