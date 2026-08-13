"""Cosine-similarity ranking, deterministic tie-breaking, Top-N (FR-242-FR-243).

W3-M3 core: given a normalized skill query, the engine projects it into the
fitted corpus vocabulary (FR-241), computes cosine similarity against every
profile vector, applies the optional threshold, breaks ties deterministically
(corpus order, then title — never hash/random order), clamps Top-N to
``1..10`` and the corpus size, and returns ranked
:class:`RecommendationResult` objects. The three FR-244 fallback paths
(cold start, zero-match, partial-match) are delegated to
:mod:`decodebot.recommender.fallbacks`.

Determinism discipline (FR-243, NFR-087):
    - ``scikit-learn``'s ``cosine_similarity`` is a pure function of the two
      matrices, and the fitted pipeline is a pure function of the corpus.
    - Ranking never iterates a ``set`` or relies on ``hash()``; the sort key
      is ``(-score, corpus_index, title)`` with corpus index unique.
    - ``scikit-learn`` is imported lazily via ``importlib.import_module`` so
      importing this module has no heavy side effects (FR-234).

Reference: SPEC.md Part III — Categories S5-S6 (FR-242-FR-244).
"""

import importlib
import logging
from typing import Optional, Sequence

import decodebot.recommender.fallbacks as fallbacks
from decodebot.recommender.corpus import CareerProfile, Corpus, RecommenderError
from decodebot.recommender.features import (
    FeaturePipeline,
    build_feature_pipeline,
    is_zero_vector,
)
from decodebot.recommender.normalization import (
    DEFAULT_MIN_SKILLS,
    InsufficientSkillsError,
    SkillSet,
    parse_skills,
)
from decodebot.recommender.result import (
    RecommendationOutcome,
    RecommendationResult,
    STATUS_OK,
)

logger = logging.getLogger(__name__)

_SKLEARN_PAIRWISE_MODULE = "sklearn.metrics.pairwise"
"""Module providing ``cosine_similarity`` (imported lazily, FR-234)."""

DEFAULT_TOP_N = 3
"""Default number of ranked results (FR-242)."""

MAX_TOP_N = 10
"""Upper bound for the validated Top-N range 1-10 (FR-242)."""


class RankingError(RecommenderError):
    """Base exception for ranking failures (FR-247)."""


def _import_cosine_similarity():
    """Lazily import and return ``sklearn.metrics.pairwise.cosine_similarity``.

    Reference: SPEC.md Part III — FR-242, FR-234.
    """
    module = importlib.import_module(_SKLEARN_PAIRWISE_MODULE)
    return module.cosine_similarity


def clamp_top_n(top_n: Optional[int], corpus_size: int) -> int:
    """Clamp Top-N to the validated ``1..10`` range and the corpus size (FR-242).

    Args:
        top_n: Requested result count (``None`` uses the default 3).
        corpus_size: Number of profiles in the active corpus.

    Returns:
        The effective result count: ``max(1, min(top_n, 10, corpus_size))``.

    Reference: SPEC.md Part III — FR-242 (validated 1-10, clamped to corpus).
    """
    if top_n is None:
        return min(DEFAULT_TOP_N, corpus_size)
    try:
        requested = int(top_n)
    except (TypeError, ValueError):
        logger.warning("Invalid top_n=%r; using default %d.", top_n, DEFAULT_TOP_N)
        requested = DEFAULT_TOP_N
    return max(1, min(requested, MAX_TOP_N, corpus_size))


def _normalize_threshold(threshold: Optional[float]) -> float:
    """Return a usable threshold (``0.0`` disables exclusion, FR-244)."""
    try:
        value = float(threshold)
    except (TypeError, ValueError):
        logger.warning("Invalid threshold=%r; defaulting to 0.0.", threshold)
        return 0.0
    return value if value > 0.0 else 0.0


def _matched_skills(query_skills: SkillSet, profile_skills: SkillSet) -> tuple[str, ...]:
    """Return query skills (canonical) that matched one profile (FR-245).

    Matching is case-insensitive membership of the canonical query skill in
    the profile's skill set, in query order. Deterministic by construction.

    Reference: SPEC.md Part III — FR-245.
    """
    lowered = {skill.lower() for skill in profile_skills}
    return tuple(skill for skill in query_skills if skill in lowered)


def _rank_results(
    entries: Sequence[tuple[int, CareerProfile]],
    scores,
    query_skills: SkillSet,
    top_n: int,
) -> tuple[RecommendationResult, ...]:
    """Rank profiles by cosine score with deterministic tie-breaking (FR-243).

    Args:
        entries: ``(corpus_index, profile)`` pairs to rank.
        scores: Cosine similarity array aligned with the corpus ordering.
        query_skills: The normalized query skills (for matched-skill marking).
        top_n: Effective result count (already clamped).

    Returns:
        Up to ``top_n`` ranked results, highest score first; ties broken by
        corpus order then title (lowercase), never hash order.

    Reference: SPEC.md Part III — FR-242, FR-243.
    """
    ranked: list[tuple[float, int, str, CareerProfile]] = []
    for index, profile in entries:
        ranked.append((float(scores[index]), index, profile.title.lower(), profile))
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))

    results: list[RecommendationResult] = []
    for rank, (_score, _index, _title, profile) in enumerate(ranked[:top_n], start=1):
        results.append(
            RecommendationResult(
                title=profile.title,
                skills=profile.skills,
                description=profile.description,
                similarity=_score,
                matched_skills=_matched_skills(query_skills, profile.skills),
                rank=rank,
            )
        )
    return tuple(results)


def build_recommendation(
    corpus: Corpus,
    raw_skills: object,
    *,
    pipeline: Optional[FeaturePipeline] = None,
    top_n: Optional[int] = DEFAULT_TOP_N,
    min_skills: int = DEFAULT_MIN_SKILLS,
    threshold: Optional[float] = 0.0,
) -> RecommendationOutcome:
    """Rank the corpus against a raw skill query (FR-242-FR-244).

    This is the single engine entry point shared by the CLI (W3-M4) and the
    GUI (W3-M5) — presentation never re-implements ranking logic.

    Args:
        corpus: A validated careers corpus.
        raw_skills: A comma/space-separated skill string or a collection of
            skill strings (may be ``None``/empty → cold-start guidance).
        pipeline: An already-fitted :class:`FeaturePipeline` to reuse (built
            from ``corpus`` when omitted).
        top_n: Number of ranked results (default 3; validated 1-10, clamped to
            corpus size).
        min_skills: Minimum usable unique skills before ranking (default 3).
        threshold: Minimum similarity for inclusion; ``0.0`` (default) disables
            threshold exclusion (FR-244).

    Returns:
        A :class:`RecommendationOutcome` — ``ok`` with ranked results, or
        ``guidance`` / ``zero-match`` / ``partial-match`` with a friendly
        message. Never raises for user-input problems.

    Reference: SPEC.md Part III — Categories S5-S6.
    """
    if raw_skills is None:
        return fallbacks.guidance_outcome(InsufficientSkillsError(min_skills=min_skills, actual=0))

    try:
        normalized = parse_skills(raw_skills, min_skills=min_skills)
    except InsufficientSkillsError as exc:
        return fallbacks.guidance_outcome(exc)

    effective_top_n = clamp_top_n(top_n, len(corpus))

    if pipeline is None:
        pipeline = build_feature_pipeline(corpus)

    query_vector = pipeline.transform(normalized.skills)
    if is_zero_vector(query_vector):
        logger.warning("Zero-match fallback triggered for query %s.", list(normalized.skills))
        return fallbacks.zero_match_outcome()

    scores = _import_cosine_similarity()(query_vector, pipeline.profile_matrix).flatten()

    effective_threshold = _normalize_threshold(threshold)
    if effective_threshold > 0.0:
        included = [
            (index, profile)
            for index, profile in enumerate(corpus)
            if float(scores[index]) >= effective_threshold
        ]
        if not included:
            logger.warning(
                "Threshold fallback: no profiles above %.3f; returning partial match.",
                effective_threshold,
            )
            results = _rank_results(
                list(enumerate(corpus)), scores, normalized.skills, effective_top_n
            )
            return fallbacks.partial_match_outcome(results)
        entries: Sequence[tuple[int, CareerProfile]] = included
    else:
        entries = list(enumerate(corpus))

    results = _rank_results(entries, scores, normalized.skills, effective_top_n)

    logger.info(
        "Ranked %d careers for query %s (top: %s).",
        len(results),
        list(normalized.skills),
        [result.title for result in results],
    )
    return RecommendationOutcome(results=results, status=STATUS_OK, message="")
