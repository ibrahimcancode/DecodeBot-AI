# samples/ — OCR Recognition Engine fixture images

This directory holds deterministic, locally generated fixture images used by
the Week 4 OCR Recognition Engine (FR-254 acceptance) and its test suite.

| File | Purpose | Provenance |
|---|---|---|
| `sample_text.png` | Bundled fixture image with known, legible text (`DecodeBot AI` + `OCR Engine v3.1`). Used by `python main.py recognize --image "samples/sample_text.png"`. | Generated deterministically with Pillow (no download); black text on a white background, `Consolas`/fallback bitmap font. |

## Usage

```bash
python main.py
> recognize --image "samples/sample_text.png" --psm 6
```

Or via the GUI (`python main.py --gui`) → **Recognition** tab → Browse to this
file → Recognize.

## Notes

- The images are generated locally and committed; nothing is fetched from the
  network (FR-261).
- They are inputs only. The engine never writes to this directory and never
  modifies the originals (FR-261).
- Re-generating `sample_text.png` is intentional and reproducible — see
  `tests` fixtures for the equivalent programmatic generation used by the
  automated suite.
