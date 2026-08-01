# Changelog

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
