"""Cold-start, zero-match, and partial-match fallback outcomes (FR-244).

FR-244 guarantees a friendly result for any input. The ranking engine
(:mod:`decodebot.recommender.ranker`) delegates all three failure-to-rank
paths to this module:

1. **Cold start / guidance** — fewer than ``recommender_min_skills`` usable
   skills (or none) → a friendly guidance outcome listing example skills.
   Never an error stack.
2. **Zero-match** — every query token falls outside the fitted vocabulary,
   so all similarities are zero → a ``zero-match`` outcome with a helpful
   message.
3. **Partial-match** — threshold exclusion empties the result list → the
   best available profiles are returned under a clearly labeled
   ``partial-match`` status.

Each constructor returns a structured :class:`RecommendationOutcome` (from
:mod:`decodebot.recommender.result`) so the CLI and GUI render one shape and
never duplicate fallback logic (FR-145, FR-245).

Reference: SPEC.md Part III — Category S6 (FR-244).
"""

from decodebot.recommender.result import (
    RecommendationOutcome,
    RecommendationResult,
    STATUS_GUIDANCE,
    STATUS_PARTIAL_MATCH,
    STATUS_ZERO_MATCH,
)

EXAMPLE_SKILLS: tuple[str, ...] = ("Python", "SQL", "Machine Learning")
"""Example skills shown in cold-start guidance messages (FR-244)."""

GUIDANCE_MESSAGE = (
    "I couldn't make a recommendation from those skills. Please provide at "
    "least {min_skills} usable skills, separated by commas — for example: "
    "{examples}."
)

ZERO_MATCH_MESSAGE = (
    "None of your skills matched the careers catalog vocabulary, so I can't "
    "score a match. Try more common skills such as Python, SQL, or Machine "
    "Learning."
)

PARTIAL_MATCH_MESSAGE = (
    "No careers met the configured match threshold, so I'm showing the "
    "closest available careers instead (partial match)."
)


def guidance_outcome(error: Exception) -> RecommendationOutcome:
    """Build a friendly guidance outcome for cold-start input (FR-244).

    Args:
        error: The underlying input validation exception (used for context).

    Returns:
        A ``guidance`` outcome with no results and a friendly message listing
        example skills.

    Reference: SPEC.md Part III — FR-244 (cold start).
    """
    message = GUIDANCE_MESSAGE.format(
        min_skills=getattr(error, "min_skills", 3),
        examples=", ".join(EXAMPLE_SKILLS),
    )
    return RecommendationOutcome(
        results=(),
        status=STATUS_GUIDANCE,
        message=message,
    )


def zero_match_outcome() -> RecommendationOutcome:
    """Build a ``zero-match`` outcome (FR-244, FR-241).

    Returns:
        An outcome with no results and a helpful message explaining that the
        query fell entirely outside the fitted vocabulary.

    Reference: SPEC.md Part III — FR-244 (zero-match).
    """
    return RecommendationOutcome(
        results=(),
        status=STATUS_ZERO_MATCH,
        message=ZERO_MATCH_MESSAGE,
    )


def partial_match_outcome(
    results: tuple[RecommendationResult, ...],
) -> RecommendationOutcome:
    """Label the best available profiles as a partial match (FR-244).

    Args:
        results: The best-ranked profiles (threshold ignored) to return.

    Returns:
        A ``partial-match`` outcome carrying ``results`` and a message that
        clearly labels them as a partial match.

    Reference: SPEC.md Part III — FR-244 (threshold fallback).
    """
    return RecommendationOutcome(
        results=results,
        status=STATUS_PARTIAL_MATCH,
        message=PARTIAL_MATCH_MESSAGE,
    )
