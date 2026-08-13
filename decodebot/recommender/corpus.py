"""Career corpus foundation for the DecodeBot Recommender Engine (FR-236-FR-238).

This module provides the structured data model (``CareerProfile``,
``SkillSet``, ``Corpus``, and the minimal ``RecommendationResult``), the
built-in careers corpus, CSV corpus loading, and corpus validation. It is the
entire W3-M1 dataset foundation: no ranking, TF-IDF, or recommendation logic
lives here (those arrive in W3-M2/W3-M3).

Only the Python standard library is used (``csv``, ``dataclasses``, ``os``,
``logging``); no ML library is imported at module scope (FR-233, FR-234).

Provenance of the built-in corpus:
    ``BUILTIN_CORPUS_DATA`` is a synthetic/curated educational dataset
    authored specifically for DecodeBot AI by this project's maintainers. It
    is not sourced from, derived from, or copied from any external dataset,
    website, or commercial corpus, and makes no claim of real-world
    employment data. It is intended solely as a deterministic, offline,
    demoable baseline for the content-based recommender (FR-236). It is
    licensed under the same MIT license as the rest of the project.

Reference: SPEC.md Part III — Categories S1-S2.
"""

import csv
import logging
import os
from dataclasses import dataclass
from typing import Iterable, Sequence

logger = logging.getLogger(__name__)

BUILTIN_CORPUS_SOURCE = "builtin"
"""Source identifier of the bundled careers corpus (FR-236)."""

DEFAULT_DOMAIN = "general"
"""Domain assigned to CSV rows when the optional ``domain`` column is absent."""

REQUIRED_CSV_COLUMNS: tuple[str, ...] = ("title", "skills", "description")
"""Required CSV corpus columns (FR-237)."""

_MIN_CORPUS_ENTRIES = 2
"""Minimum corpus entry count enforced by validation (FR-238)."""


class RecommenderError(Exception):
    """Base exception for all recommender-engine failures (FR-247)."""


class CorpusError(RecommenderError):
    """Base exception for corpus loading and validation failures (FR-238)."""


class CorpusLoadError(CorpusError):
    """Raised when a corpus source cannot be located or parsed (FR-237)."""


class CorpusValidationError(CorpusError):
    """Raised when a corpus fails integrity validation (FR-238)."""


@dataclass(frozen=True)
class SkillSet:
    """Ordered, de-duplicated collection of skill names (FR-238).

    Attributes:
        skills: Skill names in first-seen order, each trimmed, with exact
            duplicates removed. Blank tokens are rejected (never stored).

    Reference: SPEC.md Part III — Category S2 (``SkillSet``).
    """

    skills: tuple[str, ...]

    @classmethod
    def from_list(cls, items: Iterable[str]) -> "SkillSet":
        """Build a SkillSet from raw skill tokens (W3-M1 normalization).

        Each token is trimmed; tokens that become empty are rejected, and
        exact duplicate tokens are removed while preserving the first-seen
        order. Case folding is intentionally deferred to the W3-M2
        normalization stage.

        Args:
            items: Raw skill tokens (e.g. from splitting a CSV ``skills``
                cell on commas).

        Returns:
            A frozen ``SkillSet`` containing the usable, unique skills.
        """
        seen: set[str] = set()
        ordered: list[str] = []
        for item in items:
            name = item.strip()
            if not name:
                continue
            if name in seen:
                continue
            seen.add(name)
            ordered.append(name)
        return cls(tuple(ordered))

    def __iter__(self):
        return iter(self.skills)

    def __len__(self) -> int:
        return len(self.skills)

    def __contains__(self, item: object) -> bool:
        return item in self.skills


@dataclass(frozen=True)
class CareerProfile:
    """A single career/tech-stack profile (FR-236, FR-238).

    Attributes:
        title: Career role name; must be non-empty after trimming.
        skills: Non-empty ``SkillSet`` of the profile's usable skills.
        description: Short human-readable profile description (may be empty).
        domain: Broad technology domain (e.g. ``"backend"``); defaults to
            ``DEFAULT_DOMAIN`` when not provided.

    Raises:
        CorpusValidationError: If the title is blank or the skills set is
            empty.

    Reference: SPEC.md Part III — Category S2 (``CareerProfile``).
    """

    title: str
    skills: SkillSet
    description: str = ""
    domain: str = DEFAULT_DOMAIN

    def __post_init__(self) -> None:
        title = self.title.strip()
        if not title:
            raise CorpusValidationError("Career profile title must not be empty.")
        if len(self.skills) == 0:
            raise CorpusValidationError(f"Career profile '{title}' must have at least one skill.")
        domain = self.domain.strip() or DEFAULT_DOMAIN
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "domain", domain)


@dataclass(frozen=True)
class RecommendationResult:
    """Structured recommendation output (FR-238, FR-245).

    W3-M1 defines the minimal data model only; ranking behavior and rendering
    helpers are finalized in W3-M3/W3-M4. The fields below mirror the typed
    surface required by ``FR-238``.

    Attributes:
        title: Career role title.
        skills: The matched profile's skills.
        description: The matched profile's description.
        similarity: Cosine similarity of this result (populated by ranking).
        matched_skills: Skills of the query that matched this profile.

    Reference: SPEC.md Part III — Category S2 / S7 (``RecommendationResult``).
    """

    title: str
    skills: SkillSet
    description: str = ""
    similarity: float = 0.0
    matched_skills: tuple[str, ...] = ()


@dataclass(frozen=True)
class Corpus:
    """Validated collection of career profiles (FR-236-FR-238).

    Attributes:
        profiles: The corpus entries in deterministic (file or authoring)
            order.
        source: Source identifier — ``"builtin"`` or an absolute CSV path.
        description: Human-readable corpus summary.

    Reference: SPEC.md Part III — Category S2.
    """

    profiles: tuple[CareerProfile, ...]
    source: str = BUILTIN_CORPUS_SOURCE
    description: str = ""

    @property
    def domains(self) -> tuple[str, ...]:
        """Return the distinct profile domains in sorted order."""
        return tuple(sorted({profile.domain for profile in self.profiles}))

    def describe(self) -> dict[str, object]:
        """Return corpus metadata for logging and inspection (FR-236)."""
        return {
            "entries": len(self.profiles),
            "domains": list(self.domains),
            "source": self.source,
        }

    def __len__(self) -> int:
        return len(self.profiles)

    def __iter__(self):
        return iter(self.profiles)

    def __getitem__(self, index):
        return self.profiles[index]


BUILTIN_CORPUS_DATA: tuple[tuple[str, str, str, str], ...] = (
    # Domain: data/ml
    (
        "Data Scientist",
        "Python, SQL, Machine Learning, Pandas, Scikit-learn, Statistics",
        "Analyzes data to drive business decisions.",
        "data/ml",
    ),
    (
        "Machine Learning Engineer",
        "Python, Machine Learning, TensorFlow, PyTorch, Deep Learning, Kubernetes",
        "Designs, trains, and deploys machine learning models in production.",
        "data/ml",
    ),
    (
        "Data Analyst",
        "SQL, Excel, Tableau, Power BI, Python, Data Visualization",
        "Turns raw data into actionable insights and dashboards.",
        "data/ml",
    ),
    (
        "Data Engineer",
        "Python, SQL, Spark, Airflow, AWS, Snowflake",
        "Builds and maintains scalable data pipelines and warehouses.",
        "data/ml",
    ),
    (
        "NLP Engineer",
        "Python, Natural Language Processing, Transformers, PyTorch, Machine Learning",
        "Builds language models and conversational AI systems.",
        "data/ml",
    ),
    # Domain: backend
    (
        "Backend Developer",
        "Python, FastAPI, SQL, REST API, Docker, PostgreSQL",
        "Builds server-side logic, APIs, and data services.",
        "backend",
    ),
    (
        "Java Backend Engineer",
        "Java, Spring Boot, SQL, REST API, Microservices, Kafka",
        "Designs enterprise services and APIs on the JVM.",
        "backend",
    ),
    (
        "Node.js Backend Developer",
        "JavaScript, Node.js, Express, SQL, MongoDB, REST API",
        "Builds fast, event-driven server applications.",
        "backend",
    ),
    (
        "Go Backend Engineer",
        "Go, gRPC, PostgreSQL, Docker, Kubernetes, REST API",
        "Builds high-concurrency, distributed backend services.",
        "backend",
    ),
    (
        "API Engineer",
        "REST API, JSON, SQL, Authentication, Docker, OpenAPI",
        "Designs and secures public and internal APIs.",
        "backend",
    ),
    # Domain: frontend
    (
        "Frontend Developer",
        "HTML, CSS, JavaScript, React, TypeScript, Git",
        "Builds responsive user interfaces for the web.",
        "frontend",
    ),
    (
        "React Developer",
        "React, TypeScript, JavaScript, HTML, CSS, Redux",
        "Builds component-driven single-page applications.",
        "frontend",
    ),
    (
        "Vue.js Developer",
        "Vue, JavaScript, TypeScript, HTML, CSS, Pinia",
        "Crafts progressive, maintainable web interfaces.",
        "frontend",
    ),
    (
        "Full-Stack Developer",
        "HTML, CSS, JavaScript, React, Node.js, SQL, REST API",
        "Builds complete web applications across the frontend and backend.",
        "frontend",
    ),
    # Domain: mobile
    (
        "iOS Developer",
        "Swift, iOS, Xcode, UIKit, Core Data, REST API",
        "Builds native iOS applications with Swift.",
        "mobile",
    ),
    (
        "Android Developer",
        "Kotlin, Android, Jetpack Compose, REST API, Firebase, Gradle",
        "Builds native Android applications.",
        "mobile",
    ),
    (
        "Flutter Developer",
        "Dart, Flutter, REST API, Firebase, SQLite, Git",
        "Builds cross-platform mobile apps from a single codebase.",
        "mobile",
    ),
    # Domain: devops/cloud
    (
        "DevOps Engineer",
        "Docker, Kubernetes, Terraform, CI/CD, Jenkins, AWS",
        "Automates infrastructure and software delivery pipelines.",
        "devops/cloud",
    ),
    (
        "Site Reliability Engineer",
        "Kubernetes, Prometheus, Grafana, Linux, Python, Incident Response",
        "Keeps large-scale systems reliable, observable, and available.",
        "devops/cloud",
    ),
    (
        "Cloud Solutions Architect",
        "AWS, Azure, Google Cloud, Terraform, Kubernetes, Networking",
        "Designs cloud infrastructure and migration strategies.",
        "devops/cloud",
    ),
    (
        "Platform Engineer",
        "AWS, Terraform, CI/CD, Linux, Docker, Python",
        "Builds and secures shared cloud platform services.",
        "devops/cloud",
    ),
    # Domain: cybersecurity
    (
        "Cybersecurity Analyst",
        "Network Security, SIEM, Incident Response, Firewalls, Kali Linux, Security Audit",
        "Monitors and defends systems against cyber threats.",
        "cybersecurity",
    ),
    (
        "Penetration Tester",
        "Penetration Testing, OWASP, Kali Linux, Network Security, Ethical Hacking, Burp Suite",
        "Finds and exploits vulnerabilities to harden systems.",
        "cybersecurity",
    ),
    (
        "Security Engineer",
        "Network Security, Cryptography, Identity Management, Cloud Security, Python",
        "Designs and enforces enterprise security controls.",
        "cybersecurity",
    ),
)

_BUILTIN_CORPUS_DESCRIPTION = (
    "Built-in curated careers corpus: 24 profiles across 6 domains "
    "(synthetic/curated educational data, see module docstring)."
)

_CACHE: dict[str, Corpus] = {}
"""In-memory corpus cache keyed by source identifier (mirrors ML FR-168)."""


def builtin_corpus() -> Corpus:
    """Build and validate the bundled careers corpus (FR-236).

    Returns:
        A validated ``Corpus`` with at least 20 profiles spanning the six
        required domains (TC-REC-001).

    Raises:
        CorpusValidationError: If the curated data ever violates the FR-238
            rules (authoring-time guard).

    Reference: SPEC.md Part III — FR-236.
    """
    profiles = [
        CareerProfile(
            title=record[0],
            skills=SkillSet.from_list(record[1].split(",")),
            description=record[2],
            domain=record[3],
        )
        for record in BUILTIN_CORPUS_DATA
    ]
    validate_corpus(profiles)
    return Corpus(
        profiles=tuple(profiles),
        source=BUILTIN_CORPUS_SOURCE,
        description=_BUILTIN_CORPUS_DESCRIPTION,
    )


def load_corpus(
    source: str = BUILTIN_CORPUS_SOURCE,
    *,
    use_cache: bool = True,
) -> Corpus:
    """Load the active corpus from the builtin source or a CSV path (FR-236/237).

    Args:
        source: ``"builtin"`` for the bundled corpus, or a path to a CSV
            corpus file.
        use_cache: When True (default) and the source was already loaded this
            session, return the cached ``Corpus`` without re-reading it. Pass
            False to force a fresh load.

    Returns:
        A validated ``Corpus`` in deterministic row/authoring order.

    Raises:
        CorpusLoadError: If a CSV source does not exist, is not a regular
            file, or cannot be parsed/decoded.
        CorpusValidationError: If the CSV source violates the corpus rules.

    Reference: SPEC.md Part III — FR-236, FR-237.
    """
    key = source if source == BUILTIN_CORPUS_SOURCE else os.path.abspath(source)
    if use_cache and key in _CACHE:
        logger.info("Returning cached corpus for source %r.", source)
        return _CACHE[key]

    if source == BUILTIN_CORPUS_SOURCE:
        corpus = builtin_corpus()
    else:
        corpus = load_csv_corpus(source)

    if use_cache:
        _CACHE[key] = corpus
    logger.info("Corpus loaded: %s", corpus.describe())
    return corpus


def load_csv_corpus(path: str) -> Corpus:
    """Load a custom career corpus from a CSV file (FR-237).

    Required columns: ``title``, ``skills``, ``description``. The optional
    ``domain`` column, when present, sets each profile's domain; otherwise
    ``DEFAULT_DOMAIN`` is used (a deterministic default, never fabricated
    career data). Rows are validated with the same rules as the built-in
    corpus (FR-238) and kept in file order.

    Args:
        path: Path to the CSV corpus file.

    Returns:
        A validated ``Corpus`` sourced from the CSV file.

    Raises:
        CorpusLoadError: If the file does not exist, is not a regular file,
            or cannot be decoded as UTF-8 / parsed as CSV.
        CorpusValidationError: If the file is empty, lacks required columns,
            or contains rows that violate the FR-238 rules.

    Reference: SPEC.md Part III — FR-237, FR-238.
    """
    if not os.path.exists(path):
        raise CorpusLoadError(
            f"Couldn't find the corpus file '{path}' — check the path and try again."
        )
    if not os.path.isfile(path):
        raise CorpusLoadError(
            f"'{path}' is not a regular file — provide a path to a CSV corpus file."
        )

    try:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
    except UnicodeDecodeError as exc:
        raise CorpusLoadError(
            f"Couldn't read '{path}' — the file is not valid UTF-8 text."
        ) from exc
    except OSError as exc:
        raise CorpusLoadError(f"Couldn't open the corpus file '{path}': {exc}") from exc
    except csv.Error as exc:
        raise CorpusLoadError(f"Couldn't parse '{path}' as CSV: {exc}") from exc

    if not rows:
        raise CorpusValidationError(f"The corpus file '{os.path.basename(path)}' is empty.")

    header = [cell.strip() for cell in rows[0]]
    missing = [column for column in REQUIRED_CSV_COLUMNS if column not in header]
    if missing:
        raise CorpusValidationError(
            "Missing required column(s) in CSV corpus: "
            + ", ".join(missing)
            + ". Required columns: "
            + ", ".join(REQUIRED_CSV_COLUMNS)
            + "."
        )
    header_index = {name: index for index, name in enumerate(header)}

    data_rows = rows[1:]
    if not data_rows:
        raise CorpusValidationError(
            f"The corpus file '{os.path.basename(path)}' contains no data rows."
        )

    profiles: list[CareerProfile] = []
    for row_number, row in enumerate(data_rows, start=2):
        if not row:
            continue
        if len(row) != len(header):
            raise CorpusValidationError(
                f"Row {row_number} has {len(row)} column(s) but the header has "
                f"{len(header)} — malformed CSV."
            )
        title = row[header_index["title"]].strip()
        if not title:
            raise CorpusValidationError(f"Row {row_number}: career title is empty.")
        skills = SkillSet.from_list(row[header_index["skills"]].split(","))
        if len(skills) == 0:
            raise CorpusValidationError(
                f"Row {row_number}: profile '{title}' has no usable skills."
            )
        description = row[header_index["description"]].strip()
        if "domain" in header_index:
            domain = row[header_index["domain"]].strip() or DEFAULT_DOMAIN
        else:
            domain = DEFAULT_DOMAIN
        profiles.append(
            CareerProfile(
                title=title,
                skills=skills,
                description=description,
                domain=domain,
            )
        )

    validate_corpus(profiles)
    corpus = Corpus(
        profiles=tuple(profiles),
        source=os.path.abspath(path),
        description=(f"CSV corpus from '{os.path.basename(path)}': {len(profiles)} profiles."),
    )
    logger.info("CSV corpus loaded from %r (%d profiles).", path, len(profiles))
    return corpus


def validate_corpus(profiles: Sequence[CareerProfile]) -> None:
    """Validate a corpus against the FR-238 rules.

    Checks that the corpus has at least two entries, every entry has a
    non-empty title and a non-empty skills list, and no two entries share a
    title (case-insensitive, whitespace-insensitive).

    Args:
        profiles: The corpus entries to validate.

    Raises:
        CorpusValidationError: With an actionable message listing every rule
            violation found.

    Reference: SPEC.md Part III — FR-238 (TC-REC-003).
    """
    errors: list[str] = []

    if len(profiles) < _MIN_CORPUS_ENTRIES:
        errors.append(
            f"Corpus must contain at least {_MIN_CORPUS_ENTRIES} entries; "
            f"found {len(profiles)}."
        )

    for index, profile in enumerate(profiles, start=1):
        if not profile.title.strip():
            errors.append(f"Entry {index}: career title is empty.")
        if len(profile.skills) == 0:
            errors.append(f"Entry {index}: profile '{profile.title}' has no skills.")

    seen: dict[str, str] = {}
    for profile in profiles:
        key = profile.title.strip().lower()
        if key in seen:
            errors.append(
                f"Duplicate career title '{profile.title}' "
                f"(case-insensitive match of '{seen[key]}')."
            )
        else:
            seen[key] = profile.title

    if errors:
        logger.error("Corpus validation failed: %s", "; ".join(errors))
        raise CorpusValidationError("; ".join(errors))
    logger.info("Corpus validated: %d profiles, no duplicates.", len(profiles))
