"""Skill-token normalization and canonical abbreviation mapping (FR-240).

W3-M2 engine-level input parsing: a user-supplied skill string or skill
collection is parsed, trimmed, case-folded, de-duplicated, and mapped to
canonical forms before any feature extraction happens. This module uses only
the Python standard library — no ML library is imported at module scope
(FR-233, FR-234), and no presentation/CLI formatting lives here (the
friendly-message rendering is a W3-M4 CLI concern).

Normalization guarantees (FR-240):
    - Leading/trailing whitespace is trimmed and internal whitespace runs
      collapsed.
    - Empty and symbol-only tokens are dropped, never crash.
    - Trailing punctuation (``, . ; : ! ?``) is stripped so ``"Python,"`` and
      ``"python"`` normalize identically.
    - Matching is case-insensitive: tokens are folded to lowercase.
    - Common abbreviations map to canonical forms (e.g. ``"ml"`` →
      ``"machine learning"``).
    - Duplicates are removed case-insensitively while preserving the
      first-seen ordering, so results stay deterministic (FR-243).
    - Comma-separated and space-separated lists tokenize equivalently at the
      feature level (the joined canonical text reaches the vectorizer the
      same way either way).

Reference: SPEC.md Part III — Category S3 (FR-240).
"""

import logging
import re
from dataclasses import dataclass
from typing import Iterable

from decodebot.recommender.corpus import RecommenderError, SkillSet

logger = logging.getLogger(__name__)

DEFAULT_MIN_SKILLS = 3
"""Default minimum usable skill count required before ranking (FR-244)."""

_TRAILING_PUNCTUATION_RE = re.compile(r"[.,;:!?]+$")
"""Trailing punctuation stripped from a raw skill token (FR-240)."""

CANONICAL_ABBREVIATIONS: dict[str, str] = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "mlops": "machine learning operations",
    "js": "javascript",
    "ts": "typescript",
    "k8s": "kubernetes",
}
"""Case-folded abbreviation -> canonical skill form (FR-240).

Only unambiguous, single-token abbreviations are mapped. Anything not in this
table is preserved verbatim so real skills (``"Python"``, ``"C++"``) are never
rewritten.
"""


class InputError(RecommenderError):
    """Base exception for skill-input validation failures (FR-240)."""


class InsufficientSkillsError(InputError):
    """Raised when a skill input yields fewer than the minimum unique skills.

    Attributes:
        min_skills: The configured minimum (default ``DEFAULT_MIN_SKILLS``).
        actual: Number of usable unique skills actually parsed.

    Reference: SPEC.md Part III — FR-240, FR-244 (cold start).
    """

    def __init__(self, min_skills: int, actual: int):
        self.min_skills = min_skills
        self.actual = actual
        super().__init__(
            f"At least {min_skills} usable skills are required for a career "
            f"recommendation; only {actual} usable unique skill(s) were provided. "
            "Try listing skills separated by commas, e.g. "
            '"Python, SQL, Machine Learning".'
        )


@dataclass(frozen=True)
class NormalizedSkills:
    """Structured result of skill-input parsing (FR-240).

    Attributes:
        skills: Canonical (lowercased, abbreviation-expanded) unique skills
            in deterministic first-seen order, ready for comparison and
            vectorization.
        labels: Display labels aligned with ``skills`` — the cleaned original
            casing of each skill's first occurrence, preserved for friendly
            presentation layers.
        raw: The original raw input string when the input was a string.

    Reference: SPEC.md Part III — Category S3.
    """

    skills: SkillSet
    labels: tuple[str, ...]
    raw: str = ""


def _clean_token(token: str) -> str:
    """Trim whitespace and strip trailing punctuation from one token."""
    value = " ".join(token.split())
    value = value.strip()
    value = _TRAILING_PUNCTUATION_RE.sub("", value)
    return value


def canonical_skill(token: str) -> str:
    """Normalize one raw skill token to its canonical matching form (FR-240).

    Args:
        token: A single raw skill token, e.g. ``"  ML, "``.

    Returns:
        The canonical form (lowercased, whitespace-collapsed, trailing
        punctuation stripped, abbreviation expanded), or ``""`` when the
        token carries no usable skill content (blank or symbol-only).

    Reference: SPEC.md Part III — FR-240.
    """
    value = _clean_token(token)
    if not value:
        return ""
    if not any(character.isalnum() for character in value):
        return ""
    value = value.lower()
    return CANONICAL_ABBREVIATIONS.get(value, value)


def _split_item(item: str) -> list[str]:
    """Split one raw item into candidate skill tokens (FR-240).

    Comma-separated items are split on commas (any surrounding whitespace is
    trimmed later). An item without a comma is treated as a single skill token
    so multi-word phrases such as ``"Machine Learning"`` survive intact.
    """
    text = item.strip()
    if not text:
        return []
    if "," in text:
        return [part.strip() for part in text.split(",")]
    return [text]


def _tokenize(raw: str | Iterable[str]) -> list[str]:
    """Expand a skill input into candidate raw tokens (FR-240).

    A plain string is tokenized on commas when present, otherwise on
    whitespace (space-separated lists). A collection (list/tuple/``SkillSet``)
    treats each element as one skill; comma-split items inside an element are
    still honoured so ``["Python", "SQL, ML"]`` parses like a CSV cell.
    """
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        if "," in text:
            return [part.strip() for part in text.split(",")]
        return text.split()
    tokens: list[str] = []
    for item in raw:
        tokens.extend(_split_item(str(item)))
    return tokens


def parse_skills(
    raw: str | Iterable[str],
    min_skills: int = DEFAULT_MIN_SKILLS,
) -> NormalizedSkills:
    """Parse and normalize a skill input into usable canonical skills (FR-240).

    Args:
        raw: A comma-separated or space-separated skill string, or a
            collection of skill strings.
        min_skills: Minimum number of usable unique skills required. Defaults
            to ``DEFAULT_MIN_SKILLS`` (3); below this an
            :class:`InsufficientSkillsError` is raised (FR-244 cold start).

    Returns:
        A :class:`NormalizedSkills` with canonical skills and display labels
        in deterministic first-seen order.

    Raises:
        InsufficientSkillsError: If fewer than ``min_skills`` usable unique
            skills survive normalization.

    Reference: SPEC.md Part III — FR-240, FR-244.
    """
    seen: dict[str, str] = {}
    skills: list[str] = []
    labels: list[str] = []

    for token in _tokenize(raw):
        canonical = canonical_skill(token)
        if not canonical:
            continue
        if canonical in seen:
            continue
        seen[canonical] = token
        skills.append(canonical)
        labels.append(_clean_token(token))

    if len(skills) < min_skills:
        logger.warning(
            "Skill input produced %d usable unique skill(s); minimum is %d.",
            len(skills),
            min_skills,
        )
        raise InsufficientSkillsError(min_skills=min_skills, actual=len(skills))

    normalized = NormalizedSkills(
        skills=SkillSet(tuple(skills)),
        labels=tuple(labels),
        raw=raw if isinstance(raw, str) else "",
    )
    logger.info("Normalized %d usable skills: %s.", len(skills), skills)
    return normalized


def skills_text(skills: SkillSet) -> str:
    """Render a canonical skill set as the query text for TF-IDF (FR-241).

    Canonical skills are joined with single spaces; multi-word skills remain
    intact so the shared vectorizer's word analyzer sees exactly the same
    tokens as a space-separated equivalent input.

    Args:
        skills: A normalized skill set (e.g. from :func:`parse_skills`).

    Returns:
        A deterministic whitespace-joined text representation.

    Reference: SPEC.md Part III — FR-240, FR-241.
    """
    return " ".join(skills.skills)
