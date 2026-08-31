# Fictional Phase 3 synthetic data room

This directory contains the deterministic diligence fixture for **Larkspur
Transit Analytics Limited**, an entirely fictional Irish private company. No
real client room, company profile, person, registration identifier or copied
financial figure was used.

## Layout and counting

- `data_room/`: exactly 90 visible files under Financial, Legal and Tax.
- `data_room/Legal/Updated_Responses.zip`: exactly 10 file members.
- `room_manifest.json`: hashes, sizes, classifications, versions and quirks for
  all 100 logical documents.
- `canonical_dataset.json`: the coherent structured baseline from which all
  documents are generated.
- `planted_issues/`: sealed post-analysis ground truth, never a runtime input.

The visible folder counts are 27 Financial, 33 Legal and 30 Tax. Including the
ZIP members, logical counts are 27 Financial, 43 Legal and 30 Tax.

## Reproduction

From the repository root:

```text
python scripts/generate_synthetic_room.py --output synthetic/data_room --metadata-root synthetic --issues synthetic/planted_issues/issues.json --seed 314159
python scripts/validate_synthetic_room.py --room synthetic/data_room --manifest synthetic/room_manifest.json --canonical synthetic/canonical_dataset.json --issues synthetic/planted_issues/issues.json --seed 314159 --check-determinism
```

The generator uses multiple document layouts and writes valid PDF, DOCX, XLSX,
CSV, JPG and PNG artifacts. Deliberate exceptions (one CSV/XLSX extension
mismatch and one damaged PDF) are identified by the manifest and enforced by
the validator. Scanned PDFs contain raster page images only.
