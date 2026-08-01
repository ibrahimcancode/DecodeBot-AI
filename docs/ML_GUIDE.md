# ML Engine Guide

DecodeBot AI v2.0.0 ships an optional **Machine Learning Engine** that trains
and evaluates scikit-learn classifiers on the Iris benchmark dataset (or a
CSV of your choice). It is fully isolated from the rule-based chat brain and
never loaded at chatbot startup.

> **Dataset attribution:** The Iris dataset (Fisher, R.A., 1936) is distributed
> via `sklearn.datasets.load_iris()` and cited per standard dataset-citation
> practice. See [README](../README.md) and the SPEC References section.

## Quick Start

```bash
pip install -r requirements.txt   # scikit-learn, numpy, pandas, joblib, matplotlib
python main.py                    # CLI — try: train, predict, evaluate
```

Or run the ML Engine standalone (no GUI/animation layers):

```bash
python -m decodebot.ml.app_ml explore
python -m decodebot.ml.app_ml train
python -m decodebot.ml.app_ml predict 5.1 3.5 1.4 0.2
python -m decodebot.ml.app_ml compare
python -m decodebot.ml.app_ml tune-k
```

## Commands

| Command | What it does |
|---------|--------------|
| `train` | Train the configured classifier, evaluate it, and save it to `models/` |
| `predict 5.1,3.5,1.4,0.2` | Classify 4 feature values (Iris) and show probabilities |
| `evaluate` | Full report: accuracy, confusion matrix, precision, recall, macro-F1 |
| `explore` | Dataset summary: shape, features, classes, balance, statistics |
| `models` | List saved models with metadata |
| `compare` | Train KNN, decision tree, and logistic regression on the identical split |
| `tune-k` | Scan K values (elbow method) and report the best K |

## Configuration

All ML behavior is configurable via `config.json` (see
[docs/CONFIGURATION.md](CONFIGURATION.md) for the full key table):

- `ml_dataset`: `"iris"` or a CSV path (with `ml_target_column`)
- `classifier_type`: `knn` (default), `decision_tree`, `logistic_regression`, `svm`, `random_forest`
- `knn_k`: neighbor count (default 5)
- `scaler_type`: `standard` (default), `minmax`, `none`
- `ml_test_size`: held-out fraction (default 0.2)
- `ml_random_state`: reproducibility seed (default 42)
- `models_dir` / `ml_outputs_dir`: output locations (defaults `models/`, `outputs/`)
- `ml_log_level`: ML logging level (inherits `log_level` by default)

## Graphical Interface

Run `python main.py --gui` and open the **Machine Learning** tab. Buttons run
the identical functions as the CLI (FR-224); the predict form classifies four
feature values you type into the entry fields (FR-225).

## Guarantees

- **FR-223:** raw chat input never reaches a scikit-learn `predict` call —
  feature values are parsed into exactly 4 numbers first.
- **FR-229:** `scikit-learn`/`pandas`/`numpy`/`matplotlib`/`joblib` are used
  only inside `decodebot/ml/` and its dedicated tests.
- **FR-232:** chatbot startup never imports the ML dependencies (lazy bridge).
- **NFR-080:** evaluation never relies on accuracy alone — every report
  includes a confusion matrix and macro-F1.
