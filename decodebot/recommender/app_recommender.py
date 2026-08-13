"""Thin CLI bootstrap for the ``recommend`` command (FR-235, FR-239, FR-245, FR-247).

This module is the single bridge between the Chatbot Engine dispatcher and the
Recommender Engine. It is deliberately thin: it parses the ``--skills``
argument, reads the FR-235 config keys, calls the single engine entry point
:func:`decodebot.recommender.ranker.build_recommendation`, and renders the
structured :class:`RecommendationOutcome` as boxed text — or plain ASCII when
``plain_mode`` / ``--plain`` is active (FR-133, FR-245). It never re-computes
ranking logic (FR-245): the output derives exclusively from the structured
``RecommendationResult`` objects.

Isolation constraints honored here (FR-233, FR-234 — enforced by
``tests/test_wave3_isolation.py``):
    - Files inside ``decodebot.recommender`` may not import ``decodebot.core``
      or ``decodebot.ml`` at any scope. The dispatcher therefore passes the
      config dict and raw input line in as plain arguments; this module does
      no session/config/logger wiring of its own.
    - No ML library is imported at module scope; the engine's lazy imports
      are the only path to scikit-learn (FR-234).

Reference: SPEC.md Part III — Categories S7 (FR-245) and S9 (FR-247).
"""

import logging
import re

from decodebot.recommender.corpus import RecommenderError, load_corpus
from decodebot.recommender.normalization import DEFAULT_MIN_SKILLS
from decodebot.recommender.ranker import DEFAULT_TOP_N, build_recommendation
from decodebot.recommender.result import RecommendationOutcome, STATUS_OK
from decodebot.utils.formatting import box_text

logger = logging.getLogger(__name__)

USAGE_MESSAGE = (
    "To get career recommendations, use: recommend --skills " '"Python, SQL, Machine Learning"'
)
"""Friendly usage guidance when ``--skills`` is missing (FR-239, FR-244)."""

_SKILLS_ARG_RE = re.compile(r"--skills\s*=?\s*")
"""Matches the ``--skills`` (or ``--skills=``) flag and trailing spaces."""

_BOX_TITLE = "Career Recommendations"
"""Box title for the ranked recommendations screen (FR-245)."""


def _extract_skills_arg(raw: str | None) -> str | None:
    """Extract the ``--skills`` value from a raw command line (FR-239).

    Accepts ``--skills "a, b, c"`` (double/single-quoted), ``--skills=a, b, c``
    and unquoted ``--skills a, b, c``. Returns ``None`` when the flag is
    absent or empty so the caller can prompt instead of recommending nothing.

    Reference: SPEC.md Part III — FR-239.
    """
    if not raw:
        return None
    match = _SKILLS_ARG_RE.search(raw)
    if match is None:
        return None
    rest = raw[match.end() :].strip()
    if not rest:
        return None
    if rest[0] in ('"', "'"):
        quote = rest[0]
        end = rest.find(quote, 1)
        value = rest[1:end] if end != -1 else rest[1:]
    else:
        value = rest
    value = value.strip()
    return value or None


def _load_active_corpus(source: str | None):
    """Load the configured corpus source via the cached loader (FR-235/FR-236).

    Reference: SPEC.md Part III — FR-235, FR-236, FR-237.
    """
    return load_corpus(source or "builtin")


def render_outcome(outcome: RecommendationOutcome, *, plain: bool = False) -> str:
    """Render a recommendation outcome for the terminal (FR-245, FR-133).

    Args:
        outcome: The structured outcome from the ranking engine.
        plain: When True, produce plain ASCII output with zero box-drawing
            characters (``--plain`` / ``plain_mode``, FR-133).

    Returns:
        The rendered multi-line text. For ``ok`` outcomes this is the ranked
        list (rank, title, similarity %, matched skills); for the FR-244
        fallback statuses it is the friendly message.

    Reference: SPEC.md Part III — FR-245, FR-133.
    """
    if outcome.status != STATUS_OK:
        lines = [outcome.message] if outcome.message else [outcome.status]
        if plain:
            return "\n".join(lines)
        return box_text(lines, title="Recommendation")

    lines = [
        (
            f"{result.rank}. {result.title} - {result.similarity_percent()}% "
            f"- matched: {result.matched_skills_text() or '-'}"
        )
        for result in outcome.results
    ]
    if plain:
        return "\n".join(lines)
    return box_text(lines, title=_BOX_TITLE)


def handle_recommend(config: dict, raw_input: str) -> str:
    """Handle a ``recommend`` invocation from the dispatcher (FR-239, FR-245).

    Args:
        config: The active application config (from the session or on-disk
            defaults) containing the FR-235 keys and ``plain_mode``.
        raw_input: The full raw command line typed by the user (used to
            extract ``--skills``).

    Returns:
        The rendered recommendation text. Never raises for user-input or
        corpus problems: every failure path logs and returns a friendly
        message so the session continues (FR-247).

    Reference: SPEC.md Part III — Categories S7-S9.
    """
    cfg = config or {}
    skills_arg = _extract_skills_arg(raw_input)
    if skills_arg is None:
        return USAGE_MESSAGE

    try:
        corpus = _load_active_corpus(cfg.get("recommender_corpus", "builtin"))
        outcome = build_recommendation(
            corpus,
            skills_arg,
            top_n=cfg.get("recommender_top_n", DEFAULT_TOP_N),
            min_skills=cfg.get("recommender_min_skills", DEFAULT_MIN_SKILLS),
            threshold=cfg.get("recommender_threshold", 0.0),
        )
    except RecommenderError as exc:
        logger.error("Recommend command failed: %s", exc)
        return f"Recommendation error: {exc}"

    logger.info(
        "Recommend command produced status %s with %d result(s).",
        outcome.status,
        len(outcome.results),
    )
    return render_outcome(outcome, plain=bool(cfg.get("plain_mode", False)))
