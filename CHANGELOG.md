# Changelog

## [3.1.0] - 2026-08-15

> **Release note:** Added (Optional): OCR Image/Text Recognition Engine
> (Week 4). Preserved: Chatbot Engine (Week 1), ML Engine (Week 2),
> Recommender Engine (Week 3) — all unchanged and unaffected.

### Added
- OCR Recognition Engine (Week 4) — isolated `decodebot/recognition/` package
- `recognize` command wired into the shared `COMMANDS` registry with its own "OCR / Recognition" help section
- Image ingestion supporting PNG and JPEG, enforcing file size (`rec_max_file_mb`) and dimension (`rec_max_dimension`) limits
- Preprocessing pipeline: grayscale conversion, 5x5 Gaussian blur, auto-deskew (>0.5° skew correction), and Gaussian adaptive thresholding
- Tesseract OCR integration with PSM modes (`3`, `6`, `7`, `11`) via `pytesseract.image_to_data`
- Confidence filtering (80% default threshold) and structured `RecognitionResult` outputs (`accepted`, `low_confidence`, `no_text`, `error`)
- `--save` flag writing extracted text to output directory without overwriting unless `rec_overwrite: true`
- GUI **Recognition** tab calling the identical engine function as the CLI
- Recognition config keys (`rec_image_path`, `rec_psm`, `rec_confidence_threshold`, `rec_max_dimension`, `rec_max_file_mb`, `rec_output_dir`, `rec_overwrite`)
- Friendly missing-dependency handling for OpenCV, pytesseract, and Tesseract binary (FR-255)
- Privacy verification confirming zero network I/O or telemetry (FR-261)
- Recognition isolation gate (`tests/test_wave4_isolation.py`), lazy imports, and startup preservation (FR-249, FR-250)
- Full `TC-OCR-001`–`012` suite with 98% line coverage on `decodebot/recognition/` (target ≥ 90%)
- `docs/OCR_GUIDE.md` and extended `docs/CONFIGURATION.md`

### Changed
- `__version__` bumped to 3.1.0
- README and GUI guide updated with OCR documentation

## [3.0.0] - 2026-08-13

> **Release note:** Added: Content-Based Tech Stack Recommendation Engine
> (Week 3). Preserved: 100% rule-based Chatbot Engine (Week 1) and the
> isolated Machine Learning Engine (Week 2), both unchanged and unaffected.

### Added
- Recommender Engine (Week 3) — isolated `decodebot/recommender/` package
- `recommend` command wired into the shared `COMMANDS` registry with its own
  "Recommendations" help section
- Built-in careers corpus (≥ 20 profiles, ≥ 6 domains) + custom CSV corpus
  loading with validation
- Skill normalization: tokenization, canonical abbreviations, case-insensitive
  de-duplication, three-skill minimum
- Single fitted TF-IDF vocabulary shared by queries and profiles
- Cosine-similarity ranking, Top-N default 3 (validated 1–10), deterministic
  tie-breaking by corpus order then title
- Guidance / zero-match / partial-match fallbacks with structured outcomes
- Boxed CLI output with `--plain` / `plain_mode` support (zero box/ANSI chars)
- GUI **Career Recommender** tab calling the identical engine function as the CLI
- Recommender config keys (`recommender_corpus`, `recommender_top_n`,
  `recommender_min_skills`, `recommender_threshold`, `recommender_random_state`)
- `decodebot.recommender` logger tag for corpus loads, queries, and ranking summaries
- Recommender isolation gate (`tests/test_wave3_isolation.py`), lazy imports,
  and startup preservation (FR-233, FR-234)
- Full `TC-REC-001`–`012` suite with 100% line coverage on
  `decodebot/recommender/` (target ≥ 90%)
- `docs/RECOMMENDER_GUIDE.md` and extended `docs/CONFIGURATION.md`

### Changed
- `__version__` bumped to 3.0.0
- README documents the recommender with an example transcript
- Help text groups recommend commands under a "Recommendations" section

## [Unreleased]

### Changed
- Repository housekeeping for the public portfolio release:
  - Renamed `SPEC.md.md` → `SPEC.md` and `PLAN.md.md` → `PLAN.md` (documentation links updated).
  - Added `[project]` packaging metadata and a `decodebot` console entry point (`pip install -e .`); the ML dependencies remain optional (`[ml]` extra), preserving the stdlib-only chatbot core.
  - Added GitHub Actions CI (`pytest`, `ruff`, `black`).
  - Added `python -m decodebot` as an alternative to `python main.py`.

## [2.0.0] - 2026-08-02

> **Release note:** Added: Machine Learning Data Classification Engine (Week 2).
> Preserved: 100% rule-based Chatbot Engine (Week 1), unchanged.

### Added
- ML Engine (Week 2) — isolated `decodebot/ml/` package
- Dataset loading for Iris + CSV with validation and explore reports
- Preprocessing: scaling (standard/minmax/none), label encoding, shuffled stratified train/test split
- Classifiers: KNN, decision tree, logistic regression, SVM, random forest behind one `Trainer`
- Batch and single-sample prediction with per-class probabilities
- Evaluation reports: confusion matrix, precision, recall, macro-F1, cross-validation, dummy baseline
- Model persistence (`models/`) with metadata sidecars and path-security boundary
- Classifier comparison on the identical split and best-model saving
- File-based visualizations (confusion heatmap, K-tuning elbow, scaling comparison, model comparison bar)
- ML commands wired into the command registry: `train`, `predict`, `evaluate`, `explore`, `models`, `compare`, `tune-k`
- GUI Machine Learning tab with interactive predict form (`python main.py --gui`)
- Standalone ML entry point: `python -m decodebot.ml.app_ml`
- ML config keys (`ml_dataset`, `knn_k`, `classifier_type`, `scaler_type`, ...) with per-key validation
- ML logging hierarchy (`decodebot.ml.*`) with `ml_log_level`
- ML dependency isolation gate (FR-229), lazy startup gate (FR-232), friendly error handling (FR-228)
- 8-row Week 2 compliance matrix all green
- 500+ tests total

### Changed
- `__version__` bumped to 2.0.0
- Help text groups ML commands under a "Machine Learning" section
- About text reflects the rule-based core + isolated ML Engine
- `config.json` includes ML defaults
- Fixed a pre-existing GUI bug where `_append_text` referenced an out-of-scope `tk`

## [1.0.0] - 2026-07-30

### Added
- Core conversation loop with input normalization
- Greeting detection (15+ patterns, 8+ response variants)
- Exit detection (10+ patterns, negation-safe)
- Unknown input fallback with escalation and fuzzy suggestions
- Help, About, Version commands with aliases
- Session history (bounded to 100 turns)
- Runtime statistics (message count, duration, intent breakdown)
- Personalization (set/forget name)
- Hidden easter eggs and commands
- Plugin auto-discovery system
- Config file support (JSON) with fallback to defaults
- Rotating file logging with configurable log levels
- Error handling (KeyboardInterrupt, EOFError, circuit breaker)
- CLI animations (typewriter effect, thinking indicator)
- Levenshtein-based fuzzy command suggestions
- Cross-platform terminal utilities (clear screen, width detection)
- Comprehensive test suite (219+ tests)
