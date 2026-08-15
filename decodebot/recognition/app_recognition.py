"""Week 4 OCR Recognition Engine — CLI/GUI wiring and engine entry (FR-249-FR-260).

This module is the single bridge between the Chatbot Engine and the isolated
recognition package, mirroring ``decodebot/recommender/app_recommender.py``
(FR-249, FR-233 precedent):

- :func:`recognize_image` is the identical engine function the CLI and the GUI
  call (FR-260) — it runs ingest → preprocess → OCR → filter → result and
  degrades gracefully on every failure path (FR-255).
- :func:`handle_recognize` is the chat-command handler invoked by the
  dispatcher for ``recognize`` (FR-259).
- :func:`render_result` renders the boxed summary + text, honoring
  ``plain_mode``/``--plain`` (FR-133, FR-258).
- :func:`recognize_to_text` is the thin string entry the GUI tab uses.
- :func:`main` is the standalone CLI entry for
  ``python main.py recognize --image X --psm 6`` (FR-259).

Isolation (FR-249, FR-250 — enforced by ``tests/test_wave4_isolation.py``):
this module lives inside ``decodebot/recognition/`` and never imports
``cv2``/``pytesseract``/``numpy`` at module scope, and lazily imports
``decodebot.core`` infrastructure only inside the functions that need it, so
importing the recognition package at chatbot startup has no side effects.

Reference: SPEC.md Part IV — Categories T7-T8 (FR-249, FR-251, FR-259-FR-262).
"""

import os
import shlex
import time
from dataclasses import dataclass, replace
from typing import Optional

from decodebot.recognition.filter import build_result, error_result
from decodebot.recognition.errors import (
    RecognitionError,
    UnsupportedPsmError,
)
from decodebot.recognition.ingestor import DEFAULT_MAX_DIMENSION, DEFAULT_MAX_FILE_MB, ingest_image
from decodebot.recognition.ocr_engine import DEFAULT_PSM, run_ocr, validate_psm
from decodebot.recognition.preprocess import preprocess_image
from decodebot.recognition.result import (
    DEFAULT_OUTPUT_DIR,
    RecognitionResult,
    save_text_output,
    format_confidence,
    confidence_range_text,
)

RECOGNIZE_USAGE = (
    "recognize --image <path> [--psm 3|6|7|11] [--save]\n"
    "  --image  Local PNG/JPEG image to read (required).\n"
    "  --psm    Page-segmentation mode: 3, 6 (default), 7 or 11.\n"
    "  --save   Also save the extracted text to the output directory."
)
"""Help text for missing/invalid ``recognize`` arguments (FR-259)."""

_RECOGNITION_LOGGER = "decodebot.recognition"


@dataclass(frozen=True)
class RecognizeArgs:
    """Resolved CLI/chat arguments for a ``recognize`` run."""

    image_path: Optional[str]
    psm: int
    confidence_threshold: float
    save: bool
    output_dir: str
    overwrite: bool


def _resolve_psm(requested_psm, config: dict) -> int:
    """Resolve a PSM to a supported value, falling back to 6 with a warning.

    Honors the FR-251 edge case: ``rec_psm = 0`` (or any unsupported value)
    falls back to the default PSM (6) and logs a warning.
    """
    import logging

    resolved = requested_psm if requested_psm is not None else config.get("rec_psm", DEFAULT_PSM)
    try:
        return validate_psm(resolved)
    except UnsupportedPsmError:
        logging.getLogger(_RECOGNITION_LOGGER).warning(
            "Unsupported PSM %r; falling back to default %d.", resolved, DEFAULT_PSM
        )
        return DEFAULT_PSM


def parse_recognize_args(raw_input: str, config: Optional[dict] = None) -> RecognizeArgs:
    """Parse ``recognize --image X --psm N --save`` from chat/CLI text.

    Args:
        raw_input: The full raw command line, e.g.
            ``recognize --image samples/sample_text.png --psm 6 --save``.
        config: The application config (for defaults); loaded if omitted.

    Returns:
        A :class:`RecognizeArgs`. When ``--image`` is missing the
        ``image_path`` is ``None`` so the caller can surface the usage message
        (FR-259 edge case).

    Reference: SPEC.md Part IV — FR-251, FR-259.
    """
    if config is None:
        from decodebot.core.config import load_config

        config = load_config()
    tokens = shlex.split(raw_input) if raw_input else []
    if tokens and tokens[0] == "recognize":
        tokens = tokens[1:]
    image_path = None
    psm = None
    save = False
    index = 0
    positional = []
    while index < len(tokens):
        token = tokens[index]
        if token == "--image" and index + 1 < len(tokens):
            image_path = tokens[index + 1]
            index += 2
        elif token.startswith("--image="):
            image_path = token.split("=", 1)[1]
            index += 1
        elif token == "--psm" and index + 1 < len(tokens):
            psm = tokens[index + 1]
            index += 2
        elif token.startswith("--psm="):
            psm = token.split("=", 1)[1]
            index += 1
        elif token == "--save":
            save = True
            index += 1
        elif token.startswith("--"):
            index += 1  # ignore unknown flags
        else:
            positional.append(token)
            index += 1
    if image_path is None and positional:
        image_path = positional[0]
    resolved_psm = _resolve_psm(psm, config)
    threshold = float(config.get("rec_confidence_threshold", 0.80))
    output_dir = config.get("rec_output_dir", DEFAULT_OUTPUT_DIR)
    overwrite = bool(config.get("rec_overwrite", False))
    return RecognizeArgs(
        image_path=image_path,
        psm=resolved_psm,
        confidence_threshold=threshold,
        save=save,
        output_dir=output_dir,
        overwrite=overwrite,
    )


def recognize_image(
    image_path: Optional[str],
    psm: int = DEFAULT_PSM,
    confidence_threshold: float = 0.80,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    overwrite: bool = False,
    save: bool = False,
    config: Optional[dict] = None,
) -> RecognitionResult:
    """Run the full OCR pipeline and return a structured result (FR-258, FR-260).

    This is the single engine entry point shared by the CLI, the chat command
    and the GUI tab. It orchestrates ingest → preprocess → OCR → filter,
    optionally writes the extracted text, and never raises — every failure
    path is captured as an ``error``-status :class:`RecognitionResult`
    (FR-255, FR-257). All heavy imports are lazy, so calling this with no
    dependencies installed degrades gracefully.

    Args:
        image_path: The local image to read (required).
        psm: The page-segmentation mode (3/6/7/11, default 6).
        confidence_threshold: Min accepted per-word confidence (default 0.80).
        output_dir: Output directory for ``--save`` (default ``outputs/``).
        overwrite: Allow overwriting an existing saved file.
        save: Whether to persist the extracted text.
        config: The active config (for size/dimension bounds); loaded if
            omitted.

    Returns:
        A frozen :class:`RecognitionResult`. The ``error`` status covers a
        missing image, oversized image, missing OCR deps, missing Tesseract
        binary, or an OCR runtime failure — always with a friendly message.

    Reference: SPEC.md Part IV — FR-252-FR-258, FR-260.
    """
    if config is None:
        from decodebot.core.config import load_config

        config = load_config()
    start = time.perf_counter()
    image_path_str = image_path or ""
    try:
        validated_psm = validate_psm(psm)
    except UnsupportedPsmError as exc:
        return error_result(str(exc), image_path=image_path_str, psm=DEFAULT_PSM)

    try:
        ingested = ingest_image(
            image_path,
            max_file_mb=config.get("rec_max_file_mb", DEFAULT_MAX_FILE_MB),
            max_dimension=config.get("rec_max_dimension", DEFAULT_MAX_DIMENSION),
        )
        binary, metadata = preprocess_image(ingested.image)
        ocr_output = run_ocr(binary, psm=validated_psm)
        duration_ms = (time.perf_counter() - start) * 1000.0
        result = build_result(
            ocr_output.words,
            full_text=ocr_output.full_text,
            image_path=str(ingested.path),
            psm=validated_psm,
            confidence_threshold=float(confidence_threshold),
            duration_ms=duration_ms,
            deskew_applied=metadata["deskew_applied"],
            detected_angle=metadata["detected_angle"],
            processed_image=binary,
        )
        if save:
            saved = save_text_output(
                result.text,
                ingested.path,
                output_dir=output_dir,
                overwrite=overwrite,
            )
            result = replace(result, saved_to=saved)
        return result
    except RecognitionError as exc:
        duration_ms = (time.perf_counter() - start) * 1000.0
        return error_result(
            str(exc), image_path=image_path_str, psm=validated_psm, duration_ms=duration_ms
        )


def render_result(result: RecognitionResult, plain: bool = False) -> str:
    """Render a result for the terminal — boxed summary + text (FR-258, FR-133).

    Args:
        result: The structured recognition result.
        plain: When True (or when ``plain_mode`` is set), emit plain ASCII with
            zero box-drawing / ANSI characters (FR-133).

    Returns:
        The rendered multi-line string.

    Reference: SPEC.md Part IV — FR-258, FR-133.
    """
    from decodebot.utils.formatting import box_text

    lines = []
    if result.is_error:
        lines.append(result.message or "Recognition failed.")
    else:
        lines.append(f"Status: {result.render_status()}")
        lines.append(f"Words: {result.word_count} | Characters: {result.character_count}")
        lines.append(
            f"Confidence: {format_confidence(result.overall_confidence)} "
            f"(range {confidence_range_text(result.words)})"
        )
        if result.deskew_applied:
            lines.append(f"Deskew: applied ({result.detected_angle:.2f}\u00b0)")
        lines.append("")
        lines.append(result.text if result.text else "(no accepted text)")
    if result.image_path:
        lines.append("")
        lines.append(f"Source: {os.path.basename(result.image_path)}")
    if result.saved_to:
        lines.append(f"Saved to: {os.path.basename(result.saved_to)}")
    if plain:
        return "\n".join(lines)
    title = "Error" if result.is_error else "Recognition"
    return box_text(lines, title=title)


def handle_recognize(config: dict, raw_input: str) -> str:
    """Chat-command handler for ``recognize`` (FR-259).

    Args:
        config: The active application config (incl. ``plain_mode`` and the
            FR-251 recognition keys).
        raw_input: The full raw command line typed by the user.

    Returns:
        The rendered recognition result (boxed or plain). When ``--image``
        is missing, a friendly usage message is returned and the session
        continues (FR-259 edge case).

    Reference: SPEC.md Part IV — FR-259.
    """
    args = parse_recognize_args(raw_input, config)
    if not args.image_path:
        return RECOGNIZE_USAGE
    result = recognize_image(
        args.image_path,
        psm=args.psm,
        confidence_threshold=args.confidence_threshold,
        output_dir=args.output_dir,
        overwrite=args.overwrite,
        save=args.save,
        config=config,
    )
    return render_result(result, plain=bool(config.get("plain_mode", False)))


def recognize_to_text(
    image_path: str,
    psm: Optional[int] = None,
    plain_mode: bool = False,
    save: bool = False,
    config: Optional[dict] = None,
) -> str:
    """String-only entry used by the GUI Recognition tab (FR-260).

    Args:
        image_path: The local image to recognize.
        psm: Optional PSM override (else config/``6``).
        plain_mode: Strip box-drawing characters from the output.
        save: Persist the extracted text.
        config: The active config.

    Returns:
        The rendered recognition result.

    Reference: SPEC.md Part IV — FR-260.
    """
    if config is None:
        from decodebot.core.config import load_config

        config = load_config()
    resolved_psm = _resolve_psm(psm, config)
    result = recognize_image(
        image_path,
        psm=resolved_psm,
        confidence_threshold=float(config.get("rec_confidence_threshold", 0.80)),
        output_dir=config.get("rec_output_dir", DEFAULT_OUTPUT_DIR),
        overwrite=bool(config.get("rec_overwrite", False)),
        save=save,
        config=config,
    )
    return render_result(result, plain=plain_mode)


def main(argv: Optional[list] = None) -> int:
    """Standalone CLI entry — ``python main.py recognize ...`` (FR-259).

    Args:
        argv: ``sys.argv``. ``argv[0]`` may be the program name; ``argv[1]``
            may be the ``recognize`` command word.

    Returns:
        ``0`` on a completed run (including friendly errors), ``2`` for a
        usage error with no image supplied.

    Reference: SPEC.md Part IV — FR-259.
    """
    import sys

    args = list(sys.argv[1:] if argv is None else argv[1:])
    if args and args[0] == "recognize":
        args = args[1:]
    parsed = parse_recognize_args(" ".join(args))
    if not parsed.image_path:
        print(RECOGNIZE_USAGE)
        return 2
    result = recognize_image(
        parsed.image_path,
        psm=parsed.psm,
        confidence_threshold=parsed.confidence_threshold,
        output_dir=parsed.output_dir,
        overwrite=parsed.overwrite,
        save=parsed.save,
    )
    print(render_result(result, plain=bool(parsed.overwrite)))
    return 0
