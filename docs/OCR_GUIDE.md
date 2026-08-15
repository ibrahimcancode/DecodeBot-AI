# DecodeBot AI — OCR Image/Text Recognition Engine Guide

The **OCR Image/Text Recognition Engine** (Week 4, optional) provides local, offline image preprocessing and text extraction capabilities in an isolated package (`decodebot/recognition/`).

---

## 1. Overview & Architecture

The recognition engine is built with strict architectural boundaries (FR-249):
- **Isolated Package:** All OCR logic lives in `decodebot/recognition/`.
- **Zero Heavy Startup:** OpenCV (`cv2`), `pytesseract`, and `numpy` are imported only lazily inside the recognition package. Merely running `python main.py` or `python main.py --gui` never loads OCR dependencies or touches system binaries (FR-250).
- **Graceful Degradation:** If optional dependencies or the Tesseract binary are missing, `recognize` displays a friendly, actionable install message and returns to the session — it never crashes or prints a traceback (FR-255).
- **Local-Only Privacy:** Processing is 100% offline. Zero network calls, telemetry, or external API calls (FR-261).

---

## 2. Installation

### Python Optional Dependencies

To use OCR features, install the optional dependencies:

```bash
pip install -r requirements-ocr.txt
```

This installs `opencv-python-headless`, `pytesseract`, and `numpy`.

### Tesseract OCR System Binary

Tesseract must be installed on your system PATH:

- **Windows:** Download and run the Tesseract installer from [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki). Ensure `C:\Program Files\Tesseract-OCR` (or equivalent) is added to your PATH environment variable.
- **Linux (Ubuntu/Debian):** `sudo apt-get install tesseract-ocr`
- **macOS:** `brew install tesseract`

Verify installation in your terminal:

```bash
tesseract --version
```

---

## 3. Ingestion & Preprocessing Pipeline

### Image Ingestion (FR-252)

- **Supported Formats:** PNG, JPEG (`.png`, `.jpg`, `.jpeg`).
- **File Size Bound:** Checked before decoding against `rec_max_file_mb` (default 10 MB). Oversized files are rejected before full load to prevent memory exhaustion.
- **Dimension Bound:** Longest edge checked after decoding against `rec_max_dimension` (default 4096 pixels).

### Preprocessing Pipeline (FR-253)

Before passing the image to Tesseract, the image undergoes sequential preprocessing to maximize OCR accuracy:
1. **Grayscale:** Conversion to a single-channel grayscale image.
2. **Gaussian Blur:** 5x5 Gaussian kernel for noise reduction.
3. **Deskew:** Automatic orientation detection and rotation correction (applied when estimated skew exceeds ~0.5°).
4. **Adaptive Thresholding:** Gaussian adaptive thresholding producing a crisp binary (0/255) image.

---

## 4. Tesseract OCR & PSM Modes (FR-254)

Text extraction uses `pytesseract.image_to_data(...)` on the preprocessed image. Per-word text, confidence scores, and bounding boxes are collected.

Supported Page Segmentation Modes (PSM):
- `3`: Fully automatic page segmentation (without OSD).
- `6`: Assume a single uniform block of text (default `rec_psm`).
- `7`: Treat the image as a single text line.
- `11`: Sparse text — find as much text as possible in no particular order.

---

## 5. Confidence Filtering & Recognition Statuses (FR-256, FR-257)

- **Confidence Threshold:** Words with confidence below `rec_confidence_threshold` (default `0.80` / 80%) are filtered out of the main extracted text and routed to `low_confidence_words`.
- **Recognition Statuses:** Every run returns exactly one status:
  - `accepted`: At least one word met or exceeded the confidence threshold.
  - `low_confidence`: Words were detected, but all fell below the confidence threshold.
  - `no_text`: No words/text were detected in the image.
  - `error`: Missing file, unsupported format, size limit violation, or missing dependency.

---

## 6. CLI Usage (`recognize`) (FR-258, FR-259)

The `recognize` command is registered in the CLI command registry.

### Basic Invocation

```bash
python main.py recognize --image "samples/sample_text.png"
```

### Specifying PSM and Saving Output

```bash
python main.py recognize --image "samples/sample_text.png" --psm 6 --save
```

- `--psm <3|6|7|11>`: Override the default PSM mode.
- `--save`: Save extracted text to `rec_output_dir` (default `outputs/`). Existing files are not overwritten unless `rec_overwrite` is set to `true`.
- `--plain`: Render plain-text output without ANSI or box-drawing characters.

---

## 7. GUI Usage (Recognition Tab) (FR-260)

Launch the Tkinter GUI:

```bash
python main.py --gui
```

1. Switch to the **Recognition** tab.
2. Click **Browse** or type an image file path (e.g. `samples/sample_text.png`).
3. Click **Recognize**.
4. The recognition status, bounding box count, confidence summary, and extracted text will be displayed in the preview pane.

---

## 8. Configuration Reference (FR-251)

Settings in `config.json`:

| Key | Type | Default | Valid Range / Description |
|-----|------|---------|---------------------------|
| `rec_image_path` | str | `""` | Default image path when omitted from command |
| `rec_psm` | int | `6` | PSM mode (`3`, `6`, `7`, `11`) |
| `rec_confidence_threshold` | float | `0.80` | Minimum confidence score (`0.0`–`1.0`) |
| `rec_max_dimension` | int | `4096` | Maximum allowed image dimension in pixels |
| `rec_max_file_mb` | float/int | `10` | Maximum allowed file size in MB |
| `rec_output_dir` | str | `"outputs/"` | Directory for saved OCR text files |
| `rec_overwrite` | bool | `false` | Allow overwriting existing saved OCR text files |

---

## 9. Verification & Testing (FR-262)

Run the Wave 4 OCR test suite:

```bash
python -m pytest tests/test_recognition*.py tests/test_gui_recognition.py tests/test_wave4_isolation.py -q
```

Coverage measurement:

```bash
python -m coverage run -m pytest tests/test_recognition*.py tests/test_gui_recognition.py tests/test_wave4_isolation.py -q
python -m coverage report --include="decodebot/recognition/*"
```
