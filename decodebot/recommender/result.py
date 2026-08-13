"""Recommendation result data model and rendering helpers (FR-238, FR-245).

Finalized in W3-M3: :class:`RecommendationResult` gains ranking fields (``rank``)
and outcome helpers, and :class:`RecommendationOutcome` carries the FR-244
status for the whole recommendation response (``ok``, ``guidance``,
``zero-match``, ``partial-match``). The pure formatting helpers here
(``similarity_percent``, ``matched_skills_text``) are shared by the CLI
(FR-245) and the GUI (FR-246) so presentation never re-implements engine
logic — only these data-shaped helpers, not box drawing, which stays in
``decodebot/utils/formatting.py``.

This module depends only on the Python standard library at runtime; the
``SkillSet`` type used in field annotations is imported under
``TYPE_CHECKING`` so there is no import cycle with ``corpus.py`` (which
re-exports :class:`RecommendationResult` for the W3-M1 public API).

Reference: SPEC.md Part III — Categories S2 (FR-238), S5-S6 (FR-242-FR-244),
S7 (FR-245).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:  # pragma: no cover - annotation-only import
    from decodebot.recommender.corpus import SkillSet

STATUS_OK = "ok"
STATUS_GUIDANCE = "guidance"
STATUS_ZERO_MATCH = "zero-match"
STATUS_PARTIAL_MATCH = "partial-match"
"""FR-244 outcome statuses carried by :class:`RecommendationOutcome`."""


@dataclass(frozen=True)
class RecommendationResult:
    """One ranked career recommendation (FR-238, FR-242, FR-245).

    Attributes:
        title: Career role title (matches the corpus profile).
        skills: The matched profile's full skill set.
        description: The matched profile's description.
        similarity: Cosine similarity of this result vs the query (0.0-1.0).
        matched_skills: Query skills (canonical form) that matched this
            profile's skills.
        rank: 1-based rank within the outcome's result list.

    Reference: SPEC.md Part III — Category S2 / S7.
    """

    title: str
    skills: SkillSet
    description: str = ""
    similarity: float = 0.0
    matched_skills: tuple[str, ...] = ()
    rank: int = 0

    def similarity_percent(self) -> int:
        """Render similarity as a whole-number percentage for display (FR-245)."""
        return similarity_percent(self.similarity)

    def matched_skills_text(self) -> str:
        """Render matched skills as a comma-joined string for display (FR-245)."""
        return matched_skills_text(self.matched_skills)


@dataclass(frozen=True)
class RecommendationOutcome:
    """A complete recommendation response with an FR-244 status.

    Attributes:
        results: Ranked :class:`RecommendationResult` objects in display
            order (empty for ``guidance`` and ``zero-match`` outcomes).
        status: One of :data:`STATUS_OK`, :data:`STATUS_GUIDANCE`,
            :data:`STATUS_ZERO_MATCH`, :data:`STATUS_PARTIAL_MATCH`.
        message: A friendly, user-facing message explaining the outcome
            (always present for non-``ok`` statuses).

    Reference: SPEC.md Part III — Category S6 (FR-244).
    """

    results: Tuple[RecommendationResult, ...]
    status: str = STATUS_OK
    message: str = ""

    @property
    def has_results(self) -> bool:
        """True when the outcome carries at least one ranked result."""
        return len(self.results) > 0


def similarity_percent(similarity: float) -> int:
    """Convert a cosine similarity to a rounded whole-number percent (FR-245).

    Args:
        similarity: A similarity score in the range 0.0-1.0.

    Returns:
        The rounded percentage (e.g. ``0.873`` → ``87``).

    Reference: SPEC.md Part III — FR-245.
    """
    return int(round(float(similarity) * 100))


def matched_skills_text(matched_skills: tuple[str, ...]) -> str:
    """Join matched skills into a display string (FR-245).

    Args:
        matched_skills: Ordered matched skill labels.

    Returns:
        A comma-and-space joined string (``""`` when empty).

    Reference: SPEC.md Part III — FR-245.
    """
    return ", ".join(matched_skills)
