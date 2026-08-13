"""DecodeBot Recommender Engine — careers recommendation package (Wave 3).

This package is deliberately isolated from the rest of the DecodeBot
codebase (FR-233): nothing in the core, rules, or GUI imports it, and no
third-party ML libraries are imported at module scope (FR-234). The dataset
foundation lives in :mod:`decodebot.recommender.corpus` and provides the
built-in careers corpus plus custom CSV loading.

Public API (W3-M1):
    - :class:`CareerProfile` — a single career profile.
    - :class:`SkillSet` — an ordered, de-duplicated skills collection.
    - :class:`RecommendationResult` — typed recommendation output (model only).
    - :func:`load_corpus` — load the builtin or a CSV corpus.
    - :func:`builtin_corpus` — load the bundled careers corpus.
    - Exception hierarchy: :class:`RecommenderError`, :class:`CorpusError`,
      :class:`CorpusLoadError`, :class:`CorpusValidationError`.

Ranking, normalization, and configuration integration arrive in W3-M2/W3-M4.
"""

from decodebot.recommender.corpus import (
    DEFAULT_DOMAIN,
    REQUIRED_CSV_COLUMNS,
    BUILTIN_CORPUS_DATA,
    BUILTIN_CORPUS_SOURCE,
    CareerProfile,
    Corpus,
    CorpusError,
    CorpusLoadError,
    CorpusValidationError,
    RecommendationResult,
    RecommenderError,
    SkillSet,
    builtin_corpus,
    load_corpus,
    load_csv_corpus,
    validate_corpus,
)

__all__ = [
    "BUILTIN_CORPUS_DATA",
    "BUILTIN_CORPUS_SOURCE",
    "CareerProfile",
    "Corpus",
    "CorpusError",
    "CorpusLoadError",
    "CorpusValidationError",
    "DEFAULT_DOMAIN",
    "REQUIRED_CSV_COLUMNS",
    "RecommendationResult",
    "RecommenderError",
    "SkillSet",
    "builtin_corpus",
    "load_corpus",
    "load_csv_corpus",
    "validate_corpus",
]
