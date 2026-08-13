"""Wave 3, Milestone 1 — recommender corpus foundation tests (FR-236-FR-238).

Covers TC-REC-001 (built-in corpus integrity: >=20 entries across the six
required domains, no case-insensitive duplicate titles), TC-REC-002 (custom
CSV loading: required columns, friendly errors naming the offending columns,
deterministic row order), and TC-REC-003 (corpus validation and the
structured data model: ``CareerProfile``/``SkillSet``/``RecommendationResult``).

Reference: SPEC.md Part III — FR-236, FR-237, FR-238.
"""

import os

import pytest

from decodebot.recommender import (
    BUILTIN_CORPUS_DATA,
    BUILTIN_CORPUS_SOURCE,
    DEFAULT_DOMAIN,
    REQUIRED_CSV_COLUMNS,
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
from decodebot.recommender import corpus as corpus_module

REQUIRED_DOMAINS = (
    "backend",
    "frontend",
    "data/ml",
    "mobile",
    "devops/cloud",
    "cybersecurity",
)
MIN_ENTRIES = 20

VALID_CSV = [
    "title,skills,description,domain",
    '"Backend Developer","Python, FastAPI, SQL, Docker, PostgreSQL","Builds APIs.","backend"',
    '"Data Scientist","Python, SQL, Machine Learning, Statistics","Analyzes data.","data/ml"',
    '"Frontend Developer","HTML, CSS, JavaScript, React, TypeScript, Git","Builds UIs.","frontend"',
]


@pytest.fixture(autouse=True)
def _clear_cache():
    """Isolate the in-memory corpus cache between tests (FR-168 pattern)."""
    corpus_module._CACHE.clear()
    yield
    corpus_module._CACHE.clear()


def _write_csv(tmp_path, lines):
    path = tmp_path / "data.csv"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def _profile(title, skills, description="", domain="general"):
    return CareerProfile(
        title=title,
        skills=SkillSet.from_list(skills.split(",")),
        description=description,
        domain=domain,
    )


class TestBuiltinCorpus:
    """FR-236 / TC-REC-001: the bundled careers corpus."""

    def test_loads_with_expected_minimum_entries(self):
        assert len(builtin_corpus()) >= MIN_ENTRIES

    def test_data_table_has_at_least_twenty_records(self):
        assert len(BUILTIN_CORPUS_DATA) >= MIN_ENTRIES

    def test_covers_all_required_domains(self):
        corpus = builtin_corpus()
        assert set(REQUIRED_DOMAINS).issubset(set(corpus.domains))

    def test_has_no_duplicate_titles_case_insensitive(self):
        corpus = builtin_corpus()
        keys = [profile.title.strip().lower() for profile in corpus]
        assert len(keys) == len(set(keys))

    def test_every_profile_is_fully_populated(self):
        for profile in builtin_corpus():
            assert profile.title.strip()
            assert len(profile.skills) > 0
            assert profile.description.strip()
            assert profile.domain in REQUIRED_DOMAINS

    def test_skill_lists_are_de_duplicated_within_profile(self):
        for profile in builtin_corpus():
            assert len(profile.skills) == len(set(profile.skills))

    def test_is_deterministic_across_calls(self):
        first = [p.title for p in builtin_corpus()]
        second = [p.title for p in builtin_corpus()]
        assert first == second

    def test_returns_corpus_with_builtin_source(self):
        corpus = builtin_corpus()
        assert isinstance(corpus, Corpus)
        assert corpus.source == BUILTIN_CORPUS_SOURCE
        assert corpus.description


class TestLoadCorpusDispatch:
    """FR-236/237: source dispatch and caching."""

    def test_default_source_is_builtin(self):
        corpus = load_corpus()
        assert corpus.source == BUILTIN_CORPUS_SOURCE
        assert len(corpus) >= MIN_ENTRIES

    def test_builtin_is_cached(self):
        first = load_corpus()
        second = load_corpus()
        assert first is second

    def test_builtin_use_cache_false_reloads(self):
        first = load_corpus()
        second = load_corpus(use_cache=False)
        assert first is not second
        assert [p.title for p in first] == [p.title for p in second]

    def test_csv_path_dispatches_to_csv_loader(self, tmp_path):
        path = _write_csv(tmp_path, VALID_CSV)
        corpus = load_corpus(path)
        assert len(corpus) == 3
        assert corpus.source == os.path.abspath(path)

    def test_csv_cache_key_is_normalized_absolute_path(self, tmp_path):
        path = _write_csv(tmp_path, VALID_CSV)
        first = load_corpus(path)
        relative = os.path.relpath(path)
        second = load_corpus(relative)
        assert first is second

    def test_csv_use_cache_false_reloads(self, tmp_path):
        path = _write_csv(tmp_path, VALID_CSV)
        first = load_corpus(path)
        second = load_corpus(path, use_cache=False)
        assert first is not second
        assert [p.title for p in first] == [p.title for p in second]


class TestCsvLoading:
    """FR-237 / TC-REC-002: custom CSV corpora."""

    def test_loads_valid_csv_in_row_order(self, tmp_path):
        path = _write_csv(tmp_path, VALID_CSV)
        corpus = load_csv_corpus(path)
        assert [profile.title for profile in corpus] == [
            "Backend Developer",
            "Data Scientist",
            "Frontend Developer",
        ]

    def test_parses_quoted_skills_cells(self, tmp_path):
        path = _write_csv(
            tmp_path,
            [
                "title,skills,description",
                '"ML Engineer","Python, Machine Learning, SQL","Builds models."',
                '"Backend Developer","Python, FastAPI","Builds APIs."',
            ],
        )
        corpus = load_csv_corpus(path)
        assert list(corpus[0].skills) == ["Python", "Machine Learning", "SQL"]

    def test_optional_domain_column_defaults(self, tmp_path):
        path = _write_csv(
            tmp_path,
            [
                "title,skills,description",
                '"Backend Developer","Python, SQL","Builds APIs."',
                '"Data Scientist","Python, ML","Analyzes data."',
            ],
        )
        assert load_csv_corpus(path)[0].domain == DEFAULT_DOMAIN

    def test_domain_column_is_preserved(self, tmp_path):
        path = _write_csv(tmp_path, VALID_CSV)
        assert load_csv_corpus(path)[1].domain == "data/ml"

    def test_handles_utf8_bom(self, tmp_path):
        path = tmp_path / "data.csv"
        body = "\n".join(VALID_CSV) + "\n"
        path.write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))
        corpus = load_csv_corpus(str(path))
        assert len(corpus) == 3

    def test_skips_blank_lines(self, tmp_path):
        lines = [
            "title,skills,description",
            "",
            '"Backend Developer","Python, SQL","Builds APIs."',
            "",
            '"Data Scientist","Python, ML","Analyzes data."',
        ]
        path = _write_csv(tmp_path, lines)
        assert len(load_csv_corpus(path)) == 2

    def test_missing_column_error_names_every_missing_column(self, tmp_path):
        path = _write_csv(tmp_path, ["title,skills", '"A","Python,SQL"'])
        with pytest.raises(CorpusValidationError) as excinfo:
            load_csv_corpus(path)
        message = str(excinfo.value)
        assert "description" in message
        assert "Required columns" in message

    def test_missing_skills_column_named_explicitly(self, tmp_path):
        path = _write_csv(tmp_path, ["title,description", '"A","Desc."'])
        with pytest.raises(CorpusValidationError) as excinfo:
            load_csv_corpus(path)
        assert "skills" in str(excinfo.value)

    def test_empty_file_raises(self, tmp_path):
        path = tmp_path / "data.csv"
        path.write_bytes(b"")
        with pytest.raises(CorpusValidationError) as excinfo:
            load_csv_corpus(str(path))
        assert "empty" in str(excinfo.value)

    def test_header_only_file_raises(self, tmp_path):
        path = _write_csv(tmp_path, ["title,skills,description"])
        with pytest.raises(CorpusValidationError) as excinfo:
            load_csv_corpus(path)
        assert "no data rows" in str(excinfo.value)

    def test_blank_title_raises_with_row_number(self, tmp_path):
        path = _write_csv(
            tmp_path,
            ["title,skills,description", '" ","Python, SQL","Builds APIs."'],
        )
        with pytest.raises(CorpusValidationError) as excinfo:
            load_csv_corpus(path)
        assert "title is empty" in str(excinfo.value)

    def test_missing_skills_value_raises(self, tmp_path):
        path = _write_csv(
            tmp_path,
            ["title,skills,description", '"Backend Developer","","Builds APIs."'],
        )
        with pytest.raises(CorpusValidationError) as excinfo:
            load_csv_corpus(path)
        assert "no usable skills" in str(excinfo.value)

    def test_skills_with_only_blank_tokens_raise(self, tmp_path):
        path = _write_csv(
            tmp_path,
            ["title,skills,description", '"Backend Developer","  , ,","Builds APIs."'],
        )
        with pytest.raises(CorpusValidationError) as excinfo:
            load_csv_corpus(path)
        assert "no usable skills" in str(excinfo.value)

    def test_case_insensitive_duplicate_titles_raise(self, tmp_path):
        lines = [
            "title,skills,description",
            '"Frontend Developer","HTML, CSS","Builds UIs."',
            '"frontend developer","HTML, JS","Builds interfaces."',
        ]
        path = _write_csv(tmp_path, lines)
        with pytest.raises(CorpusValidationError) as excinfo:
            load_csv_corpus(path)
        assert "Duplicate career title" in str(excinfo.value)

    def test_missing_file_raises_load_error(self, tmp_path):
        with pytest.raises(CorpusLoadError) as excinfo:
            load_csv_corpus(str(tmp_path / "missing.csv"))
        assert "Couldn't find" in str(excinfo.value)

    def test_directory_path_raises_load_error(self, tmp_path):
        with pytest.raises(CorpusLoadError) as excinfo:
            load_csv_corpus(str(tmp_path))
        assert "not a regular file" in str(excinfo.value)

    def test_ragged_row_raises_malformed_csv(self, tmp_path):
        lines = [
            "title,skills,description,domain",
            '"Backend Developer","Python, SQL","Builds APIs.","backend","extra"',
        ]
        path = _write_csv(tmp_path, lines)
        with pytest.raises(CorpusValidationError) as excinfo:
            load_csv_corpus(path)
        assert "malformed CSV" in str(excinfo.value)

    def test_invalid_utf8_raises_load_error(self, tmp_path):
        path = tmp_path / "data.csv"
        path.write_bytes(b"title,skills,description\n\xff\xfe")
        with pytest.raises(CorpusLoadError) as excinfo:
            load_csv_corpus(str(path))
        assert "UTF-8" in str(excinfo.value)


class TestErrorHierarchy:
    """FR-238: structured exception hierarchy for corpus failures."""

    def test_load_errors_are_corpus_errors(self, tmp_path):
        with pytest.raises(CorpusLoadError):
            load_csv_corpus(str(tmp_path / "missing.csv"))

    def test_hierarchy(self):
        assert issubclass(CorpusValidationError, CorpusError)
        assert issubclass(CorpusLoadError, CorpusError)
        assert issubclass(CorpusError, RecommenderError)
        assert issubclass(RecommenderError, Exception)


class TestSkillSet:
    """FR-238: ordered, de-duplicated skills collection."""

    def test_trims_tokens_and_rejects_blanks(self):
        skills = SkillSet.from_list(["  Python ", "SQL", "  ", "", " Docker "])
        assert list(skills) == ["Python", "SQL", "Docker"]

    def test_dedup_exact_keeps_first_occurrence_order(self):
        skills = SkillSet.from_list(["Python", "SQL", "Python", "Java", "SQL"])
        assert list(skills) == ["Python", "SQL", "Java"]

    def test_case_insensitive_normalization_is_deferred(self):
        skills = SkillSet.from_list(["python", "Python"])
        assert list(skills) == ["python", "Python"]

    def test_empty_input_produces_empty_set(self):
        assert len(SkillSet.from_list([])) == 0
        assert len(SkillSet.from_list(["  ", ""])) == 0

    def test_immutable(self):
        skills = SkillSet.from_list(["Python"])
        with pytest.raises(Exception):
            skills.skills = ("SQL",)

    def test_contains_and_len(self):
        skills = SkillSet.from_list(["Python", "SQL"])
        assert "Python" in skills
        assert "Ruby" not in skills
        assert len(skills) == 2


class TestCareerProfile:
    """FR-238: structured profile model."""

    def test_defaults(self):
        profile = _profile("Backend Developer", "Python, SQL")
        assert profile.description == ""
        assert profile.domain == DEFAULT_DOMAIN

    def test_blank_title_rejected(self):
        with pytest.raises(CorpusValidationError):
            _profile("   ", "Python, SQL")

    def test_empty_skills_rejected(self):
        with pytest.raises(CorpusValidationError):
            _profile("Backend Developer", "  ,  ")

    def test_immutable(self):
        profile = _profile("Backend Developer", "Python, SQL")
        with pytest.raises(Exception):
            profile.title = "Changed"


class TestRecommendationResult:
    """FR-238: minimal typed recommendation output (model only)."""

    def test_defaults(self):
        result = corpus_module.RecommendationResult(
            title="Backend Developer", skills=SkillSet.from_list(["Python"])
        )
        assert result.similarity == 0.0
        assert result.matched_skills == ()
        assert result.description == ""

    def test_fields_are_populated(self):
        skills = SkillSet.from_list(["Python", "FastAPI"])
        result = corpus_module.RecommendationResult(
            title="Backend Developer",
            skills=skills,
            description="Builds APIs.",
            similarity=0.87,
            matched_skills=("Python",),
        )
        assert result.title == "Backend Developer"
        assert result.skills is skills
        assert result.similarity == 0.87
        assert result.matched_skills == ("Python",)


class TestValidateCorpus:
    """FR-238 / TC-REC-003: corpus integrity validation."""

    def test_accepts_valid_profiles(self):
        profiles = [
            _profile("Backend Developer", "Python, SQL"),
            _profile("Data Scientist", "Python, ML"),
        ]
        validate_corpus(profiles)

    def test_rejects_fewer_than_two_entries(self):
        with pytest.raises(CorpusValidationError) as excinfo:
            validate_corpus([_profile("Backend Developer", "Python, SQL")])
        assert "at least 2" in str(excinfo.value)

    def test_rejects_empty_corpus(self):
        with pytest.raises(CorpusValidationError):
            validate_corpus([])

    def test_rejects_duplicate_titles(self):
        profiles = [
            _profile("Backend Developer", "Python, SQL"),
            _profile("Backend Developer", "Java, Spring"),
        ]
        with pytest.raises(CorpusValidationError) as excinfo:
            validate_corpus(profiles)
        assert "Duplicate career title" in str(excinfo.value)

    def test_rejects_case_insensitive_duplicates(self):
        profiles = [
            _profile("Frontend Developer", "HTML, CSS"),
            _profile("frontend DEVELOPER", "JavaScript"),
        ]
        with pytest.raises(CorpusValidationError):
            validate_corpus(profiles)

    def test_guards_against_crafted_empty_title(self):
        profile = _profile("Backend Developer", "Python, SQL")
        object.__setattr__(profile, "title", "  ")
        with pytest.raises(CorpusValidationError):
            validate_corpus([profile, _profile("Data Scientist", "Python, ML")])


class TestCorpusContainer:
    """FR-238: Corpus container behavior."""

    def test_len_iter_getitem(self):
        corpus = builtin_corpus()
        assert len(corpus) == len(list(corpus))
        assert isinstance(corpus[0], CareerProfile)
        assert corpus[-1] == list(corpus)[-1]

    def test_domains_sorted_and_unique(self):
        corpus = builtin_corpus()
        domains = list(corpus.domains)
        assert domains == sorted(set(domains))

    def test_describe_reports_metadata(self):
        meta = builtin_corpus().describe()
        assert meta["entries"] == len(builtin_corpus())
        assert set(REQUIRED_DOMAINS).issubset(set(meta["domains"]))
        assert meta["source"] == BUILTIN_CORPUS_SOURCE


class TestW3M1Scope:
    """W3-M1 ships dataset foundation only — no ranking logic yet."""

    def test_ranking_logic_is_not_present(self):
        for name in (
            "recommend",
            "rank",
            "cosine",
            "similarity",
            "tfidf",
            "normalize",
            "result",
        ):
            assert not hasattr(corpus_module, name), (
                f"corpus module exposes '{name}' — W3-M1 must not ship ranking "
                "or normalization logic (deferred to W3-M2/W3-M3)."
            )

    def test_required_columns_constant(self):
        assert REQUIRED_CSV_COLUMNS == ("title", "skills", "description")
