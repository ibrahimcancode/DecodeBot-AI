# DecodeBot AI

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Chatbot Engine](https://img.shields.io/badge/Chatbot%20Engine-100%25%20Rule--Based-4c1)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-orange)
![Supervised Learning](https://img.shields.io/badge/Supervised%20Learning-KNN%20%7C%20Decision%20Tree%20%7C%20SVM%20%7C%20LogReg%20%7C%20RandomForest-brightgreen)
![Recommender Engine](https://img.shields.io/badge/Recommender-Content--Based%20%7C%20TF--IDF%20%7C%20Cosine-blueviolet)
![OCR Engine](https://img.shields.io/badge/OCR-OpenCV%20%7C%20Tesseract-green)

> The **100% Rule-Based** badge describes the *Chatbot Engine only* (Week 1) — the
> conversational agent is pure deterministic rules with zero NLP/ML. The optional
> **Machine Learning Engine** (Week 2), **Recommendation Engine** (Week 3), and
> **OCR Recognition Engine** (Week 4) are separate, isolated packages.

A rule-based conversational agent built in pure Python — the chat brain is 100% rule-based (no NLP, no LLMs, no external APIs), with optional, fully isolated scikit-learn engines for the Week 2 training project (classification, prediction, evaluation), the Week 3 recommender (content-based career matching), and the Week 4 OCR engine (image text extraction).

## Why Rule-Based?

Rule-based AI is transparent, predictable, and fully auditable. Every response can be traced to a specific pattern and handler. There's no black box, no statistical uncertainty, and no external API calls. The ML Engine lives in its own package (`decodebot/ml/`) and is never loaded at chatbot startup, so the fast, dependency-free CLI stays the default experience.

## Project Structure

```
decodebot-ai/
├── main.py                     # Entry point (python main.py [--gui])
├── config.json                 # Configuration (chatbot + ML defaults)
├── requirements.txt            # Production deps (split: chatbot core / ML)
├── pyproject.toml              # Packaging + lint/test tool config
│
├── decodebot/                  # Main application source
│   ├── core/                   # Chatbot engine (config, dispatcher, loop, ...)
│   ├── rules/                  # Rule modules (greetings, exit, help, ...)
│   ├── utils/                  # Animations, normalization, formatting, ...
│   ├── gui/                    # Tkinter GUI + ML + Career Recommender + Recognition tabs
│   ├── ml/                     # Isolated ML Engine (train/predict/evaluate)
│   ├── recommender/            # Isolated Recommender Engine (recommend)
│   ├── recognition/            # Isolated OCR Recognition Engine (recognize)
│   └── plugins/                # Optional user-provided rule plugins
│
├── models/                     # Trained models + metadata model cards
├── outputs/                    # Generated plots & saved OCR text files
├── datasets/                   # Dataset notes / future CSV datasets
├── docs/                       # ARCHITECTURE, ML_GUIDE, RECOMMENDER_GUIDE, OCR_GUIDE, ...
└── tests/                      # 1000+ unit, integration, compliance, isolation tests
```

## Features

- Greeting, exit, and fallback handling with varied response pools
- Help, About, Version commands with aliases
- Session conversation history (bounded to 100 turns)
- Runtime statistics (message count, duration, intent breakdown)
- Personalization (set/forget your name)
- Hidden easter eggs and commands
- Configurable settings (bot name, colors, debug mode, animations)
- Rotating file logging with configurable levels
- Plugin auto-discovery system for extending rules
- CLI animations (typewriter effect, thinking indicator)
- Fuzzy command suggestion via Levenshtein distance
- **ML Engine (Week 2):** `train`, `predict`, `evaluate`, `explore`, `models`, `compare`, `tune-k` commands
- Iris dataset loading + CSV support with validation
- Scikit-learn classifiers (KNN, decision tree, logistic regression, SVM, random forest)
- Preprocessing with scaling, train/test split, and reproducibility seeds
- Model persistence (`models/`), classifier comparison, and K tuning
- Evaluation reports with confusion matrix, precision, recall, and macro-F1
- GUI Machine Learning tab with an interactive predict form
- Full ML dependency isolation (FR-229) and lazy startup (FR-232)
- **Recommender Engine (Week 3):** `recommend` command for content-based career matching
- Skill normalization with canonical abbreviations (`ml` → `machine learning`)
- Single fitted TF-IDF vocabulary shared by queries and profiles
- Cosine-similarity ranking with deterministic Top-N (default 3) tie-breaking
- Cold-start / zero-match / partial-match fallbacks, never a crash
- GUI Career Recommender tab calling the identical engine function as the CLI
- **OCR Engine (Week 4):** `recognize` command for image text extraction
- PNG and JPEG image ingestion with size (10MB) and dimension (4096px) limits
- Preprocessing pipeline: grayscale, 5x5 Gaussian blur, auto-deskew (>0.5°), adaptive thresholding
- Tesseract OCR integration with PSM modes (`3`, `6`, `7`, `11`)
- Confidence filtering (default 80%) with structured status (`accepted`, `low_confidence`, `no_text`, `error`)
- GUI Recognition tab with file browser and inline preview
- Full OCR dependency isolation (FR-249) and local privacy guarantee (FR-261)

## Installation

```bash
git clone <repo-url>
cd decodebot-ai
python main.py
```

Chatbot core: only Python 3.12+ (no third-party dependencies required).

The **Machine Learning Engine** uses 5 optional dependencies listed in
`requirements.txt`, which is clearly split into a "Chatbot Engine (stdlib
only)" section and a "Machine Learning Engine" section (FR-230). Install them
only if you want ML features:

```bash
pip install -r requirements.txt
```

## Usage

```
$ python main.py

+==========================================+
|         D E C O D E B O T   A I         |
|   Rule-Based Conversational Agent        |
|              v3.0.0                      |
+==========================================+

Type 'help' to see what I can do.

You: hello
Bot: Hey there! What's on your mind?

You: recommend --skills "Python, SQL, Machine Learning"
Bot: 1. Machine Learning Engineer - 61% - matched: python, machine learning
     2. Data Scientist - 41% - matched: python, sql, machine learning
     3. NLP Engineer - 32% - matched: python, machine learning

You: train
Bot: Dataset: iris (150 samples, 4 features)
     Training set: 120 | Test set: 30
     Model trained in 4ms. Classifier: knn(k=5) | ...
     Test accuracy: 0.967 | Macro F1: 0.965
     Saved model to models/knn_iris.joblib

You: predict 5.1,3.5,1.4,0.2
Bot: Prediction: setosa
     Probabilities: setosa: 1.000, versicolor: 0.000, virginica: 0.000

You: bye
Bot: Goodbye! Thanks for chatting!
```

A GUI with Machine Learning and Career Recommender tabs is available via
`python main.py --gui`.

## Machine Learning Engine

The ML Engine is a supervised classification pipeline built on `scikit-learn`,
`numpy`, `pandas`, `joblib`, and `matplotlib` — all used **only inside
`decodebot/ml/`** (FR-229) and never imported at chatbot startup (FR-232).

**Dataset.** The benchmark dataset is the classic **Iris dataset** (Fisher,
R.A., 1936; distributed via `sklearn.datasets.load_iris()`), used with
attribution per standard dataset-citation practice. CSV datasets are also
supported (configure `ml_dataset` + `ml_target_column` in `config.json`).

**Pipeline.** Load → validate → preprocess (standard/minmax scaling, stratified
shuffled 80/20 split, fit-on-train-only to prevent leakage) → train (KNN,
decision tree, logistic regression, SVM, or random forest) → evaluate →
persist to `models/` with a companion metadata model card.

### Try it

```bash
pip install -r requirements.txt          # installs the 5 optional ML deps

python -m decodebot.ml.app_ml explore    # dataset understanding report
python -m decodebot.ml.app_ml train      # train + save a model
python -m decodebot.ml.app_ml predict 5.1,3.5,1.4,0.2
python -m decodebot.ml.app_ml evaluate   # confusion matrix + precision/recall/F1
python -m decodebot.ml.app_ml compare    # identical-split classifier comparison
python -m decodebot.ml.app_ml tune-k     # elbow-method K search
```

Or chat directly in the CLI (`train`, `predict 5.1,3.5,1.4,0.2`, `evaluate`,
...) and use the GUI's **Machine Learning** tab for a point-and-click predict
form.

### Example session transcript

```
$ python main.py
> train
Dataset: iris (150 samples, 4 features)
Training set: 120 | Test set: 30
Model trained in 3ms. Classifier: knn(k=5) | Samples: 120 | Features: 4 | Classes: [0, 1, 2]
Test accuracy: 0.933 | Macro F1: 0.933
Saved model to models/knn_iris.joblib

> evaluate
========================================
 Evaluation Report
----------------------------------------
 Accuracy: 0.9333
 Confusion Matrix (rows = actual, cols = predicted)
            0 1 2
setosa      10 0 0
versicolor  0 10 0
virginica   0 2 8
...
 Macro average: precision 0.944 | recall 0.933 | F1 0.933
========================================

> predict 6.3,3.3,6.0,2.5
Prediction: virginica
Probabilities: setosa: 0.000, versicolor: 0.000, virginica: 1.000
```

Each committed model in `models/` carries a companion metadata `.json` that
doubles as a lightweight **model card** — classifier type, hyperparameters,
training date, dataset, and test accuracy.

See [docs/ML_GUIDE.md](docs/ML_GUIDE.md) for the full pipeline explanation,
configuration reference, and CLI/GUI usage walkthrough.

## Content-Based Tech Stack Recommendation Engine

Wave 3 adds a content-based career recommender in an isolated package,
`decodebot/recommender/` (FR-233). Type the skills you've learned and get the
top career matches ranked by cosine similarity against the bundled careers
catalog (≥ 20 profiles across 6 domains), with match percentage and matched
skills. scikit-learn is imported **only lazily**, inside this package, so the
fast chatbot CLI and ML Engine are completely unaffected (FR-234).

**Pipeline.** Normalize skills (`ml` → `machine learning`, case/whitespace
fold, de-dup) → fit **one** TF-IDF vocabulary on the corpus → project the query
through that same vocabulary → cosine rank with deterministic tie-breaking →
structured outcome (ranked list, or a friendly guidance / zero-match /
partial-match fallback — never a crash).

### Try it

```bash
python main.py          # then type the command below in the REPL
> recommend --skills "Python, SQL, Machine Learning"
```

Or use the GUI's **Career Recommender** tab (`python main.py --gui`) — it calls
the identical engine function as the CLI (FR-246).

### Example session transcript

```
$ python main.py
> recommend --skills "Python, SQL, Machine Learning"
┌───────────────────────────────────────────────────────┐
│ Career Recommendations                                │
├───────────────────────────────────────────────────────┤
│ 1. Machine Learning Engineer - 61% - matched: python, machine learning
│ 2. Data Scientist - 41% - matched: python, sql, machine learning
│ 3. NLP Engineer - 32% - matched: python, machine learning
└───────────────────────────────────────────────────────┘
```

- **Deterministic:** identical input → byte-identical output, every run.
- **Custom corpora:** set `recommender_corpus` in `config.json` to a CSV path
  (`title,skills,description[,domain]`) to recommend against your own roles.
- **Plain output:** run with `--plain` (or set `plain_mode: true`) for
  zero box/ANSI characters.

See [docs/RECOMMENDER_GUIDE.md](docs/RECOMMENDER_GUIDE.md) for the full engine
explanation, configuration reference, and behavior guarantees.

## OCR Image/Text Recognition Engine (Week 4, Optional)

Wave 4 adds an offline OCR image/text recognition engine in an isolated package,
`decodebot/recognition/` (FR-249). Extract text from PNG/JPEG documents with
automated image preprocessing (grayscale, Gaussian blur, auto-deskew, adaptive
thresholding), configurable PSM modes (`3`, `6`, `7`, `11`), 80% confidence
filtering, and structured result statuses (`accepted`, `low_confidence`,
`no_text`, `error`).

### Try it

```bash
python main.py recognize --image "samples/sample_text.png" --psm 6
```

Or use the GUI's **Recognition** tab (`python main.py --gui`) — it calls the
identical engine function as the CLI (FR-260).

See [docs/OCR_GUIDE.md](docs/OCR_GUIDE.md) for full details.

## Architecture

DecodeBot uses a clean layered architecture:

- **Presentation Layer:** CLI REPL loop (`core/loop.py`) and Tkinter GUI (`gui/app_gui.py`)
- **Application Layer:** Intent dispatcher + response selector (`core/dispatcher.py`, `core/responder.py`)
- **Domain Layer:** Rule engine + session state (`core/rule_engine.py`, `core/session.py`)
- **Infrastructure Layer:** Config, logging, stats, history (`core/config.py`, `core/logger.py`, `core/stats.py`, `core/history.py`)
- **ML Engine (isolated):** `ml/` package — dataset loading, preprocessing, training, prediction, evaluation, persistence, visualization (`ml/app_ml.py` is the single lazy bridge)
- **Recommender Engine (isolated):** `recommender/` package — corpus, normalization, TF-IDF features, cosine ranking, fallbacks (`recommender/app_recommender.py` is the single lazy bridge)
- **Recognition Engine (isolated):** `recognition/` package — ingestion, preprocessing, Tesseract OCR, confidence filtering, result formatting (`recognition/app_recognition.py` is the single lazy bridge)

See `docs/ARCHITECTURE.md`, `docs/ML_GUIDE.md`, `docs/RECOMMENDER_GUIDE.md`, `docs/OCR_GUIDE.md`, and `SPEC.md` for full details.

## Testing

```bash
python -m pytest
```

The test suite includes:
- 8 mandatory compliance gate tests (Week 2 matrix)
- 1000+ unit, integration, regression, and edge-case tests
- ML dependency isolation gate (FR-229) and lazy-startup gate (FR-232)
- Recommender isolation gate (FR-233, `tests/test_wave3_isolation.py`)
- Recognition isolation gate (FR-249, `tests/test_wave4_isolation.py`)
- Full `TC-OCR-001`–`012` OCR suite with 98% line coverage on `decodebot/recognition/`
- Plugin interface, animation, and error-handling tests

## Documentation

- [Configuration](docs/CONFIGURATION.md)
- [ML Guide](docs/ML_GUIDE.md)
- [Recommender Guide](docs/RECOMMENDER_GUIDE.md)
- [OCR Guide](docs/OCR_GUIDE.md)
- [GUI Guide](docs/GUI_GUIDE.md)
- [Plugin Guide](docs/PLUGIN_GUIDE.md)
- [Hidden Commands](docs/HIDDEN_COMMANDS.md)
- [Full Specification](SPEC.md)

## License

MIT
