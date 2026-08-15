# Architecture

DecodeBot AI is split into two engines that share nothing at runtime.

```
                     ┌────────────────────────────┐
                     │   Presentation Layer       │
                     │  CLI (core/loop.py)        │
                     │  GUI (gui/app_gui.py)      │
                     │  Web (streamlit_app.py)    │
                     └──────────────┬─────────────┘
                                    │
                     ┌──────────────▼─────────────┐
                     │   Application Layer        │
                     │  core/dispatcher.py        │
                     │  core/responder.py         │
                     └──────────────┬─────────────┘
                                    │
                     ┌──────────────▼─────────────┐
                     │   Domain Layer             │
                     │  core/rule_engine.py       │
                     │  core/session.py           │
                     └──────────────┬─────────────┘
                                    │
                     ┌──────────────▼─────────────┐
                     │   Infrastructure Layer     │
                     │  config, logger, stats,    │
                     │  history, plugins          │
                     └──────────────┬─────────────┘
                                    │
                     ┌──────────────▼─────────────┐
                     │   ML Engine (isolated)     │
                     │  decodebot/ml/*            │
                     │  (lazy bridge via          │
                     │   ml/app_ml.py)            │
                     └────────────────────────────┘
```

## Chatbot Engine (Week 1)

- **Presentation adapters** (`core/loop.py`, `gui/app_gui.py`,
  `streamlit_app.py`) never contain conversational logic; they only route
  input to the dispatcher / engine bridges and render responses.
- **Dispatcher** (`core/dispatcher.py`) maps an `Intent` to a handler. ML
  intents are routed to the ML bridge lazily — the `decodebot.ml` import
  happens inside the ML command branch, so startup stays dependency-free
  (FR-232).
- **Rule engine** (`core/rule_engine.py`) normalizes input and classifies it
  into an `Intent` entirely by deterministic rules.
- **Session state** (`core/session.py`) holds history, stats, personalization,
  and the ML pipeline cache (`ml_state`).
- **Plugins** (`plugins/`) are auto-discovered modules extending the rule set.

## ML Engine (Week 2)

The ML Engine is a supervised classification pipeline confined to
`decodebot/ml/` (FR-229). Each module has one responsibility:

| Module | Responsibility |
|--------|----------------|
| `dataset.py` | `Dataset` dataclass, class counts, balance ratio, stats |
| `dataset_loader.py` | Iris/CSV loading, validation, explore report |
| `dataset_validator.py` | NaN/single-class/integrity validation |
| `preprocessor.py` | Scaling (standard/minmax/none), encoding, split, report |
| `trainer.py` | Classifier training + `tune_k` (elbow method) |
| `predictor.py` | Batch/single-sample prediction + probabilities |
| `evaluator.py` | Accuracy, confusion matrix, precision/recall/F1, mirage warning |
| `model_manager.py` | joblib save/load, metadata model cards, `compare`, listing |
| `visualization.py` | File-based PNG plots (Agg backend, headless) |
| `app_ml.py` | The single lazy bridge + standalone CLI entry point |

Dependency flow is one-way: `app_ml.py` → modules above → `dataset.py`. The
Chatbot Engine only ever reaches `app_ml.py`, lazily, never importing any ML
library at startup.

## Data flow (train → predict)

```
load_dataset() → validate() → preprocess_and_split()
                                   │  scaler fit on X_train only
                                   ▼
Trainer.train(X_train, y_train) ──► model ──► evaluate(model, X_test, y_test)
                                   │              │
                                   ▼              ▼
                            save_model()   EvaluationReport
                                   │        (matrix + macro-F1)
                                   ▼
                         models/<name>.joblib + <name>.json
```

Prediction goes through the same trained pipeline: raw feature values are
scaled with the train-fitted scaler, then classified; the canonical Iris
sample `[5.1, 3.5, 1.4, 0.2]` always classifies as `setosa`.
