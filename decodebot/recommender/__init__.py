"""DecodeBot Recommender Engine — careers recommendation package (Wave 3).

This package is deliberately isolated from the rest of the DecodeBot
codebase (FR-233): nothing in the core, rules, or GUI imports it, and no
third-party ML libraries are imported at module scope (FR-234). The dataset
foundation lives in :mod:`decodebot.recommender.corpus`, input normalization
in :mod:`decodebot.recommender.normalization` (W3-M2), and the single
vocabulary TF-IDF pipeline in :mod:`decodebot.recommender.features` (W3-M2).

Public API:
    - Dataset (W3-M1): :class:`CareerProfile`, :class:`SkillSet`,
      :class:`RecommendationResult`, :class:`Corpus`, :func:`load_corpus`,
      :func:`builtin_corpus`, :func:`validate_corpus`, plus the exception
      hierarchy (:class:`RecommenderError`, :class:`CorpusError`,
      :class:`CorpusLoadError`, :class:`CorpusValidationError`).
    - Normalization (W3-M2): :class:`NormalizedSkills`,
      :func:`parse_skills`, :func:`canonical_skill`, :func:`skills_text`,
      :class:`InputError`, :class:`InsufficientSkillsError`.
    - Features (W3-M2): :class:`FeaturePipeline`,
      :func:`build_feature_pipeline`, :func:`profile_text`,
      :func:`is_zero_vector`, :class:`FeatureExtractionError`,
      :class:`EmptyVocabularyError`.

Ranking and configuration integration arrive in W3-M3/W3-M4.
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
from decodebot.recommender.features import (
    EmptyVocabularyError,
    FeatureExtractionError,
    FeaturePipeline,
    build_feature_pipeline,
    is_zero_vector,
    profile_text,
)
from decodebot.recommender.normalization import (
    CANONICAL_ABBREVIATIONS,
    DEFAULT_MIN_SKILLS,
    InputError,
    InsufficientSkillsError,
    NormalizedSkills,
    canonical_skill,
    parse_skills,
    skills_text,
)

__all__ = [
    "BUILTIN_CORPUS_DATA",
    "BUILTIN_CORPUS_SOURCE",
    "CANONICAL_ABBREVIATIONS",
    "CareerProfile",
    "Corpus",
    "CorpusError",
    "CorpusLoadError",
    "CorpusValidationError",
    "DEFAULT_DOMAIN",
    "DEFAULT_MIN_SKILLS",
    "EmptyVocabularyError",
    "FeatureExtractionError",
    "FeaturePipeline",
    "InputError",
    "InsufficientSkillsError",
    "NormalizedSkills",
    "REQUIRED_CSV_COLUMNS",
    "RecommendationResult",
    "RecommenderError",
    "SkillSet",
    "build_feature_pipeline",
    "builtin_corpus",
    "canonical_skill",
    "is_zero_vector",
    "load_corpus",
    "load_csv_corpus",
    "parse_skills",
    "profile_text",
    "skills_text",
    "validate_corpus",
]
