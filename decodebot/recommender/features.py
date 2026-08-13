"""Single-vocabulary TF-IDF feature extraction (FR-241).

W3-M2 feature layer: exactly one :class:`sklearn.feature_extraction.text.TfidfVectorizer`
is fitted on the career corpus (each profile's combined skills + description
text), and user queries are transformed with that same fitted vocabulary —
never a separate query vectorizer (FR-241).

Design constraints honored here:

- FR-241: one fitted vocabulary; query and profile dimensionality always
  match; no corpus text leaks into the query representation.
- FR-233/FR-234: no ML library is imported at module scope. ``scikit-learn``
  (and ``numpy`` for dense-vector checks) are loaded lazily via
  ``importlib.import_module`` only inside the functions that need them, so
  importing this module has zero heavy side effects and chatbot-only startup
  never touches the recommender.
- Determinism (FR-243): fitting is a pure function of the corpus; feature
  names come from the vectorizer's stable sorted vocabulary.
- Error containment (FR-247): an empty corpus or an empty fitted vocabulary
  raises a structured :class:`FeatureExtractionError` subclass that the
  presentation layers translate into friendly messages.

Reference: SPEC.md Part III — Category S4 (FR-241).
"""

import importlib
import logging
from dataclasses import dataclass
from typing import Optional

from decodebot.recommender.corpus import CareerProfile, Corpus, RecommenderError
from decodebot.recommender.normalization import SkillSet, skills_text

logger = logging.getLogger(__name__)

_SKLEARN_TEXT_MODULE = "sklearn.feature_extraction.text"
"""Module that provides ``TfidfVectorizer`` (imported lazily)."""

_NUMPY_MODULE = "numpy"
"""Module used only for dense zero-vector checks (imported lazily)."""


class FeatureExtractionError(RecommenderError):
    """Base exception for TF-IDF vectorization failures (FR-241, FR-247)."""


class EmptyVocabularyError(FeatureExtractionError):
    """Raised when fitting the corpus produces an empty vocabulary.

    An empty vocabulary means no career profile contributes any usable word
    token, so no query can ever match; the recommender reports it as a
    controlled, friendly error rather than crashing (FR-241, FR-247).
    """


@dataclass(eq=False)
class FeaturePipeline:
    """Encapsulated fitted TF-IDF feature space over one corpus (FR-241).

    Attributes:
        corpus: The corpus the pipeline was fitted on.
        vectorizer: The single fitted ``TfidfVectorizer`` (the shared
            vocabulary).
        profile_matrix: Document-term matrix for the corpus profiles in
            corpus order (sparse matrix from scikit-learn).
        feature_names: Deterministic sorted vocabulary of fitted feature
            names.

    Reference: SPEC.md Part III — Category S4.
    """

    corpus: Corpus
    vectorizer: object
    profile_matrix: object
    feature_names: tuple[str, ...] = ()

    @property
    def vocabulary_size(self) -> int:
        """Number of features in the shared fitted vocabulary (FR-241)."""
        return len(self.feature_names)

    def transform(self, skills: SkillSet) -> object:
        """Transform a normalized skill set with the already-fitted vectorizer.

        The user query is projected into the corpus vocabulary using the very
        vectorizer fitted on the career corpus (FR-241). No refit ever happens
        on the query; unknown tokens simply map to zero-weight dimensions.

        Args:
            skills: A normalized skill set (see
                :func:`decodebot.recommender.normalization.parse_skills`).

        Returns:
            A one-row sparse query vector with ``vocabulary_size`` columns.

        Reference: SPEC.md Part III — FR-241.
        """
        text = skills_text(skills)
        return self.vectorizer.transform([text])


def _import_vectorizer() -> object:
    """Lazily import and return the TfidfVectorizer class (FR-234)."""
    module = importlib.import_module(_SKLEARN_TEXT_MODULE)
    return module.TfidfVectorizer


def profile_text(profile: CareerProfile) -> str:
    """Build the deterministic profile text vectorized for one career (FR-241).

    The text is the profile's combined skills + description, joined in a fixed
    order with single spaces. Each field contributes its real content exactly
    once — text is never repeated to invent undocumented feature weights.

    Args:
        profile: The career profile to render.

    Returns:
        A deterministic whitespace-joined text representation.

    Reference: SPEC.md Part III — FR-241.
    """
    skills_part = " ".join(profile.skills.skills)
    if profile.description:
        return f"{skills_part} {profile.description}"
    return skills_part


def build_feature_pipeline(
    corpus: Corpus,
    *,
    max_features: Optional[int] = None,
) -> FeaturePipeline:
    """Fit exactly one TF-IDF vectorizer on the career corpus (FR-241).

    Args:
        corpus: A validated careers corpus.
        max_features: Optional cap on the vocabulary size (configurable
            max-feature bound). ``None`` (default) uses the full vocabulary.

    Returns:
        A :class:`FeaturePipeline` holding the single fitted vectorizer, the
        corpus document-term matrix, and the deterministic feature names.

    Raises:
        FeatureExtractionError: If the corpus is empty.
        EmptyVocabularyError: If the corpus yields no word tokens at all.

    Reference: SPEC.md Part III — FR-241.
    """
    if len(corpus) == 0:
        raise FeatureExtractionError(
            "Cannot build features from an empty corpus — load a corpus first."
        )

    TfidfVectorizer = _import_vectorizer()
    vectorizer = TfidfVectorizer(lowercase=True, max_features=max_features)
    texts = [profile_text(profile) for profile in corpus]

    try:
        profile_matrix = vectorizer.fit_transform(texts)
    except ValueError as exc:
        logger.error("TF-IDF fitting failed on the corpus: %s", exc)
        raise EmptyVocabularyError(
            "The careers corpus produced no word features (empty vocabulary) "
            "\u2014 check that profiles contain real skill words."
        ) from exc

    feature_names = tuple(vectorizer.get_feature_names_out())
    if not feature_names:
        logger.error("TF-IDF fitting produced an empty vocabulary.")
        raise EmptyVocabularyError(
            "The careers corpus produced an empty TF-IDF vocabulary; " "no skills could be matched."
        )

    logger.info(
        "Fitted shared TF-IDF vocabulary of %d features over %d profiles.",
        len(feature_names),
        len(corpus),
    )
    return FeaturePipeline(
        corpus=corpus,
        vectorizer=vectorizer,
        profile_matrix=profile_matrix,
        feature_names=feature_names,
    )


def is_zero_vector(vector: object) -> bool:
    """Return True when a query vector carries no term weights (FR-241/FR-244).

    A zero vector means every query token fell outside the fitted vocabulary
    (unknown skills); the ranking layer turns this into the zero-match status
    rather than returning misleading results (FR-244).

    Args:
        vector: A transformed query vector (scipy sparse or dense array).

    Returns:
        True if the vector is None or contains only zero entries.

    Reference: SPEC.md Part III — FR-241, FR-244.
    """
    if vector is None:
        return True
    nnz = getattr(vector, "nnz", None)
    if nnz is not None:
        return nnz == 0
    numpy = importlib.import_module(_NUMPY_MODULE)
    return not bool(numpy.any(numpy.asarray(vector)))
