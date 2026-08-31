# Sealed synthetic ground truth

This directory is reserved for post-analysis scoring. Its contents are fictional,
but they must not be supplied to source registration, extraction, drafting or
red-team reasoning. The normal runtime accepts an explicit data-room directory
and rejects any path containing `planted_issues`.

`issues.json` is the immutable answer key for the deterministic Phase 3 fixture.
The synthetic-room validator may read it only as an explicit sealed-validation
input after generation or analysis.
