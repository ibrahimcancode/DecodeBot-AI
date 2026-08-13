"""DecodeBot Recommender Engine — careers recommendation package (Wave 3).

This package is deliberately isolated from the rest of the DecodeBot
codebase (FR-233): nothing in the core, rules, or GUI imports it, and no
third-party ML libraries are imported at module scope (FR-234). The dataset
foundation lives in :mod:`decodebot.recommender.corpus`, input normalization
in :mod:`decodebot.recommender.normalization` (W3-M2), the single vocabulary
TF-IDF pipeline in :mod:`decodebot.recommender.features` (W3-M2), the result
model in :mod:`decodebot.recommender.result`, the deterministic cosine
ranking in :mod:`decodebot.recommender.ranker` (W3-M3), and the FR-244
fallbacks in :mod:`decodebot.recommender.fallbacks` (W3-M3).

Public API:
    - Dataset (W3-M1): :class:`CareerProfile`, :class:`SkillSet`,
      :class:`Corpus`, :func:`load_corpus`, :func:`builtin_corpus`,
      :func:`validate_corpus`, plus the exception hierarchy
      (:class:`RecommenderError`, :class:`CorpusError`,
      :class:`CorpusLoadError`, :class:`CorpusValidationError`).
    - Normalization (W3-M2): :class:`NormalizedSkills`, :func:`parse_skills`,
      :func:`canonical_skill`, :func:`skills_text`, :class:`InputError`,
      :class:`InsufficientSkillsError`.
    - Features (W3-M2): :class:`FeaturePipeline`, :func:`build_feature_pipeline`,
      :func:`profile_text`, :func:`is_zero_vector`,
      :class:`FeatureExtractionError`, :class:`EmptyVocabularyError`.
    - Results (W3-M3): :class:`RecommendationResult`,
      :class:`RecommendationOutcome`, status constants, and the pure
      rendering helpers :func:`similarity_percent`,
      :func:`matched_skills_text`.
    - Ranking (W3-M3): :func:`build_recommendation`, :func:`clamp_top_n`,
      :class:`RankingError`, and the FR-244 fallback constructors
      (:func:`guidance_outcome`, :func:`zero_match_outcome`,
      :func:`partial_match_outcome`).

Configuration and CLI/GUI wiring arrive in W3-M4/W3-M5.
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
    RecommenderError,
    SkillSet,
    builtin_corpus,
    load_corpus,
    load_csv_corpus,
    validate_corpus,
)
from decodebot.recommender.fallbacks import (
    EXAMPLE_SKILLS,
    guidance_outcome,
    partial_match_outcome,
    zero_match_outcome,
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
from decodebot.recommender.ranker import (
    DEFAULT_TOP_N,
    MAX_TOP_N,
    RankingError,
    build_recommendation,
    clamp_top_n,
)
from decodebot.recommender.result import (
    STATUS_GUIDANCE,
    STATUS_OK,
    STATUS_PARTIAL_MATCH,
    STATUS_ZERO_MATCH,
    RecommendationOutcome,
    RecommendationResult,
    matched_skills_text,
    similarity_percent,
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
    "DEFAULT_TOP_N",
    "EXAMPLE_SKILLS",
    "EmptyVocabularyError",
    "FeatureExtractionError",
    "FeaturePipeline",
    "InputError",
    "InsufficientSkillsError",
    "MAX_TOP_N",
    "NormalizedSkills",
    "REQUIRED_CSV_COLUMNS",
    "RankingError",
    "RecommendationOutcome",
    "RecommendationResult",
    "RecommenderError",
    "STATUS_GUIDANCE",
    "STATUS_OK",
    "STATUS_PARTIAL_MATCH",
    "STATUS_ZERO_MATCH",
    "SkillSet",
    "build_feature_pipeline",
    "build_recommendation",
    "builtin_corpus",
    "canonical_skill",
    "clamp_top_n",
    "guidance_outcome",
    "is_zero_vector",
    "load_corpus",
    "load_csv_corpus",
    "matched_skills_text",
    "parse_skills",
    "partial_match_outcome",
    "profile_text",
    "similarity_percent",
    "skills_text",
    "validate_corpus",
    "zero_match_outcome",
]
