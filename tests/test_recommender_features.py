"""Wave 3, Milestone 2 — input normalization & TF-IDF feature tests.

Covers TC-REC-004 (skill normalization equivalence) and TC-REC-005 (single
fitted TF-IDF vocabulary invariant), plus the W3-M2 normalization and feature
contracts: whitespace/case normalization, empty-value removal,
case-insensitive deduplication, deterministic ordering, the three-skill
minimum, canonical abbreviation mapping, profile-text construction, one
shared fitted vocabulary, user transform without refitting, feature
determinism, unknown-skill/zero-vector behavior, empty-vocabulary handling,
no module-scope fitting, and isolation from chatbot startup.

Reference: SPEC.md Part III — FR-239 (engine-level parsing), FR-240, FR-241.
"""

import os
import subprocess
import sys

import pytest

from decodebot.recommender import (
    BUILTIN_CORPUS_SOURCE,
    DEFAULT_MIN_SKILLS,
    EmptyVocabularyError,
    FeatureExtractionError,
    InputError,
    InsufficientSkillsError,
    NormalizedSkills,
    SkillSet,
    build_feature_pipeline,
    builtin_corpus,
    canonical_skill,
    is_zero_vector,
    load_corpus,
    parse_skills,
    profile_text,
    skills_text,
)
from decodebot.recommender import corpus as corpus_module
from decodebot.recommender import features as features_module

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CANONICAL_QUERY = "Python, SQL, Machine Learning"


@pytest.fixture(autouse=True)
def _clear_cache():
    """Isolate the in-memory corpus cache between tests (FR-168 pattern)."""
    corpus_module._CACHE.clear()
    yield
    corpus_module._CACHE.clear()


def _run_subprocess(script):
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=60,
    )


class TestWhitespaceNormalization:
    def test_trims_leading_and_trailing_whitespace(self):
        result = parse_skills("  Python ,  SQL ,  Machine Learning  ")
        assert list(result.skills) == ["python", "sql", "machine learning"]

    def test_internal_whitespace_collapsed(self):
        result = parse_skills("Python, SQL,   Machine    Learning")
        assert list(result.skills) == ["python", "sql", "machine learning"]

    def test_whitespace_only_input_is_insufficient(self):
        with pytest.raises(InsufficientSkillsError):
            parse_skills("    ,   ")


class TestCaseNormalization:
    def test_upper_and_mixed_case_fold_to_lowercase(self):
        result = parse_skills("PYTHON, sQl, MaChInE LeArNiNg")
        assert list(result.skills) == ["python", "sql", "machine learning"]

    def test_canonical_skill_lowercases(self):
        assert canonical_skill("Docker") == "docker"


class TestEmptyValueRemoval:
    def test_empty_values_dropped(self):
        result = parse_skills("Python, , SQL,   , Machine Learning")
        assert list(result.skills) == ["python", "sql", "machine learning"]

    def test_symbol_only_tokens_dropped(self):
        result = parse_skills("Python, ###, @@@, SQL, ML")
        assert list(result.skills) == ["python", "sql", "machine learning"]

    def test_trailing_punctuation_stripped(self):
        result = parse_skills("Python!!, SQL., Machine Learning!")
        assert list(result.skills) == ["python", "sql", "machine learning"]

    def test_canonican_skill_empty_for_blank(self):
        assert canonical_skill("   ") == ""
        assert canonical_skill("###") == ""


class TestDeduplication:
    def test_case_insensitive_dedup(self):
        result = parse_skills("Python, python, PYTHON, SQL, Java")
        assert list(result.skills) == ["python", "sql", "java"]

    def test_canonical_abbreviation_dedup(self):
        result = parse_skills("Python, SQL, ML, Machine Learning")
        assert list(result.skills) == ["python", "sql", "machine learning"]

    def test_first_seen_order_preserved(self):
        result = parse_skills("SQL, Python, Java, Python, sql")
        assert list(result.skills) == ["sql", "python", "java"]


class TestDeterministicOrdering:
    def test_repeated_parsing_is_identical(self):
        first = parse_skills(CANONICAL_QUERY)
        second = parse_skills(CANONICAL_QUERY)
        assert first == second
        assert list(first.skills) == list(second.skills)
        assert first.labels == second.labels

    def test_different_casing_produces_same_canonical_order(self):
        a = parse_skills("Python, SQL, Machine Learning")
        b = parse_skills("python,sql,machine learning")
        assert list(a.skills) == list(b.skills)


class TestMinimumSkills:
    def test_fewer_than_three_raises(self):
        with pytest.raises(InsufficientSkillsError) as excinfo:
            parse_skills("Python, SQL")
        assert excinfo.value.actual == 2
        assert excinfo.value.min_skills == DEFAULT_MIN_SKILLS
        assert "3" in str(excinfo.value)

    def test_single_skill_raises(self):
        with pytest.raises(InsufficientSkillsError):
            parse_skills("Python")

    def test_empty_input_raises(self):
        with pytest.raises(InsufficientSkillsError):
            parse_skills("")

    def test_exactly_three_valid_skills_succeeds(self):
        result = parse_skills("Python, SQL, Docker")
        assert list(result.skills) == ["python", "sql", "docker"]
        assert len(result.skills) == 3

    def test_insufficient_skill_error_is_input_error(self):
        assert issubclass(InsufficientSkillsError, InputError)
        assert issubclass(InputError, Exception)

    def test_min_skills_override(self):
        with pytest.raises(InsufficientSkillsError):
            parse_skills("Python, SQL", min_skills=5)


class TestAbbreviationMapping:
    def test_ml_maps_to_machine_learning(self):
        result = parse_skills("Python, SQL, ML")
        assert list(result.skills) == ["python", "sql", "machine learning"]

    def test_ml_query_equals_full_phrase_query(self):
        a = parse_skills("Python, SQL, ML")
        b = parse_skills("Python, SQL, Machine Learning")
        assert list(a.skills) == list(b.skills)

    def test_nlp_and_k8s_mapped(self):
        result = parse_skills("Python, NLP, K8s, SQL")
        assert "natural language processing" in result.skills
        assert "kubernetes" in result.skills


class TestInputFormsAndLabels:
    def test_collection_input(self):
        result = parse_skills(["Python", "SQL", "Machine Learning"])
        assert list(result.skills) == ["python", "sql", "machine learning"]

    def test_collection_input_preserves_phrases(self):
        result = parse_skills(["Python", "Machine Learning", "SQL"])
        assert list(result.skills) == ["python", "machine learning", "sql"]

    def test_skillset_input(self):
        skills = SkillSet(("Python", "SQL", "ML"))
        result = parse_skills(skills)
        assert list(result.skills) == ["python", "sql", "machine learning"]

    def test_display_labels_preserve_first_seen_casing(self):
        result = parse_skills("Python, SQL, Machine Learning")
        assert result.labels == ("Python", "SQL", "Machine Learning")

    def test_labels_align_with_skills(self):
        result = parse_skills("Machine Learning, python, ML, SQL")
        assert result.labels == ("Machine Learning", "python", "SQL")
        assert list(result.skills) == ["machine learning", "python", "sql"]

    def test_collection_label_preserved(self):
        result = parse_skills(["Docker", "Kubernetes", "Terraform"])
        assert result.labels == ("Docker", "Kubernetes", "Terraform")

    def test_raw_input_recorded_for_strings(self):
        result = parse_skills(CANONICAL_QUERY)
        assert result.raw == CANONICAL_QUERY

    def test_unicode_skill_preserved(self):
        result = parse_skills(["Python", "Café", "SQL"])
        assert "café" in result.skills


class TestCommaSpaceEquivalence:
    def test_feature_level_equivalence(self):
        corpus = builtin_corpus()
        pipeline = build_feature_pipeline(corpus)
        comma = parse_skills("Python, SQL, Machine Learning")
        space = parse_skills("python sql machine learning")
        comma_vec = pipeline.transform(comma.skills)
        space_vec = pipeline.transform(space.skills)
        assert comma_vec.shape == space_vec.shape
        diff = comma_vec - space_vec
        assert diff.nnz == 0

    def test_comma_spacing_equivalence(self):
        a = parse_skills("Python, SQL, machine learning")
        b = parse_skills("python,sql,machine learning")
        assert list(a.skills) == list(b.skills)


class TestProfileText:
    def test_combines_skills_and_description(self):
        corpus = builtin_corpus()
        profile = corpus[0]
        text = profile_text(profile)
        for token in profile.skills.skills:
            assert token in text
        assert profile.description in text

    def test_deterministic(self):
        corpus = builtin_corpus()
        profile = corpus[0]
        assert profile_text(profile) == profile_text(profile)

    def test_field_order_skills_then_description(self):
        corpus = builtin_corpus()
        profile = corpus[0]
        text = profile_text(profile)
        assert text.startswith(profile.skills.skills[0])
        assert text.endswith(profile.description)


class TestSingleFittedVocabulary:
    def test_shared_vocabulary_dimensionality(self):
        corpus = builtin_corpus()
        pipeline = build_feature_pipeline(corpus)
        query = pipeline.transform(parse_skills(CANONICAL_QUERY).skills)
        assert query.shape[1] == pipeline.vocabulary_size
        assert pipeline.profile_matrix.shape[1] == pipeline.vocabulary_size
        assert pipeline.profile_matrix.shape[0] == len(corpus)

    def test_transform_never_refits(self):
        corpus = builtin_corpus()
        pipeline = build_feature_pipeline(corpus)
        first = pipeline.transform(parse_skills(CANONICAL_QUERY).skills)
        second = pipeline.transform(parse_skills("Docker, Kubernetes, Terraform").skills)
        assert first.shape == second.shape
        assert first.shape[1] == pipeline.vocabulary_size

    def test_feature_names_are_stable_and_sorted(self):
        corpus = builtin_corpus()
        pipeline = build_feature_pipeline(corpus)
        names = list(pipeline.feature_names)
        assert names == sorted(names)
        assert len(names) == pipeline.vocabulary_size


class TestFeatureDeterminism:
    def test_two_pipelines_identical(self):
        corpus = builtin_corpus()
        first = build_feature_pipeline(corpus)
        second = build_feature_pipeline(corpus)
        assert first.feature_names == second.feature_names
        assert first.profile_matrix.toarray().tolist() == second.profile_matrix.toarray().tolist()
        assert first.vocabulary_size == second.vocabulary_size

    def test_transforms_identical_for_same_input(self):
        corpus = builtin_corpus()
        pipeline = build_feature_pipeline(corpus)
        skills = parse_skills(CANONICAL_QUERY).skills
        assert (pipeline.transform(skills) - pipeline.transform(skills)).nnz == 0

    def test_max_features_bound(self):
        corpus = builtin_corpus()
        pipeline = build_feature_pipeline(corpus, max_features=50)
        assert pipeline.vocabulary_size == pipeline.profile_matrix.shape[1]
        assert pipeline.vocabulary_size <= 50
        assert len(pipeline.feature_names) == pipeline.vocabulary_size


class TestUnknownSkillBehavior:
    def test_completely_unknown_skills_zero_vector(self):
        corpus = builtin_corpus()
        pipeline = build_feature_pipeline(corpus)
        query = pipeline.transform(parse_skills("Qwzx, Kvlm, Zjmt").skills)
        assert query.shape[1] == pipeline.vocabulary_size
        assert query.nnz == 0
        assert is_zero_vector(query)

    def test_partially_known_skills_nonzero(self):
        corpus = builtin_corpus()
        pipeline = build_feature_pipeline(corpus)
        query = pipeline.transform(parse_skills("python, Qwzx, Kvlm").skills)
        assert query.shape[1] == pipeline.vocabulary_size
        assert query.nnz > 0
        assert not is_zero_vector(query)

    def test_known_skills_have_nonzero_weight(self):
        corpus = builtin_corpus()
        pipeline = build_feature_pipeline(corpus)
        query = pipeline.transform(parse_skills(CANONICAL_QUERY).skills)
        assert query.nnz > 0

    def test_is_zero_vector_none(self):
        assert is_zero_vector(None)


class TestEmptyVocabulary:
    def test_empty_corpus_raises(self):
        from decodebot.recommender.corpus import Corpus

        with pytest.raises(FeatureExtractionError):
            build_feature_pipeline(Corpus(profiles=()))

    def test_symbol_only_corpus_raises_empty_vocabulary(self, tmp_path):
        path = tmp_path / "empty_vocab.csv"
        path.write_text(
            "title,skills,description\n" '"Alpha","###",""\n' '"Beta","@@@",""\n',
            encoding="utf-8",
        )
        corpus = load_corpus(str(path))
        with pytest.raises(EmptyVocabularyError):
            build_feature_pipeline(corpus)

    def test_empty_vocabulary_is_feature_error(self):
        assert issubclass(EmptyVocabularyError, FeatureExtractionError)


class TestNoModuleScopeFitting:
    def test_import_does_not_load_sklearn(self):
        script = (
            "import sys\n"
            "import decodebot.recommender.features\n"
            "import decodebot.recommender.normalization\n"
            "import decodebot.recommender\n"
            "if 'sklearn' in sys.modules:\n"
            "    print('SKLEARN-PRESENT')\n"
            "    sys.exit(1)\n"
            "if 'numpy' in sys.modules:\n"
            "    print('NUMPY-PRESENT')\n"
            "    sys.exit(1)\n"
            "corpus_mod = sys.modules['decodebot.recommender.corpus']\n"
            "if not hasattr(corpus_mod, '_CACHE'):\n"
            "    print('NO-CACHE')\n"
            "    sys.exit(1)\n"
            "if corpus_mod._CACHE:\n"
            "    print('CACHE-NOT-EMPTY')\n"
            "    sys.exit(1)\n"
            "print('OK')\n"
        )
        result = _run_subprocess(script)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout

    def test_no_pipeline_singleton_at_module_scope(self):
        for name in ("pipeline", "vectorizer", "_pipeline"):
            assert not hasattr(features_module, name)

    def test_no_corpus_auto_load(self):
        assert corpus_module._CACHE == {}


class TestIsolationFromChatbotStartup:
    def test_chatbot_startup_does_not_import_recommender(self):
        script = (
            "import sys\n"
            "import decodebot.core.app\n"
            "for m in sys.modules:\n"
            "    if m == 'decodebot.recommender' "
            "or m.startswith('decodebot.recommender.'):\n"
            "        print('IMPORTED:' + m)\n"
            "        sys.exit(1)\n"
            "print('OK')\n"
        )
        result = _run_subprocess(script)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout


class TestW3M1Regression:
    def test_builtin_corpus_still_loads(self):
        corpus = builtin_corpus()
        assert len(corpus) >= 20
        assert corpus.source == BUILTIN_CORPUS_SOURCE

    def test_load_corpus_cache_still_works(self):
        first = load_corpus()
        second = load_corpus()
        assert first is second

    def test_skills_text_joins_with_spaces(self):
        skills = SkillSet(("python", "sql", "machine learning"))
        assert skills_text(skills) == "python sql machine learning"

    def test_normalized_skills_is_structured(self):
        result = parse_skills(CANONICAL_QUERY)
        assert isinstance(result, NormalizedSkills)
        assert isinstance(result.skills, SkillSet)
        assert result.labels == ("Python", "SQL", "Machine Learning")
