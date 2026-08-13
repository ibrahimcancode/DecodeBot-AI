# PLAN.md — DecodeBot AI Implementation Plan

> **Companion document to `SPEC.md` (v3.0.0).** This file translates the specification into a strict, ordered, dependency-safe build sequence for an AI coding agent (OpenCode) to execute. It introduces **zero new requirements** — every task below cites the exact FR/NFR/Test ID it implements or verifies in `SPEC.md`. If any instruction here appears to conflict with `SPEC.md`, **`SPEC.md` is authoritative** and this plan must be corrected to match it, never the reverse.
>
> **This plan now covers five linked phase groups:**
> - **Phases 0–13 — Chatbot Engine (Week 1, unchanged).** 100% rule-based conversational agent.
> - **Phases 14–15 — GUI & Animation Layer (unchanged).** Optional Tkinter GUI and terminal animation effects, both reusing the Week 1 rule engine unchanged.
> - **Phases 16–24 — Machine Learning Engine (Week 2, new).** A new, isolated `decodebot/ml/` module implementing supervised classification, per the official DecodeLabs Week 2 brief. **Only Phases 16–24 are permitted to use `scikit-learn`/`pandas`/`numpy`/`matplotlib`/`joblib`.** Phases 0–15 remain strictly stdlib-only.
> - **Wave 3 — Content-Based Tech Stack Recommendation Engine (Week 3, PLANNED).** A new, isolated `decodebot/recommender/` package implementing content-based career/tech-stack recommendation (`FR-233`–`FR-248`, `NFR-086`–`NFR-090`, `NFR-096`). It reuses the Week 2 ML dependency scope (`FR-229`) inside `decodebot/recommender/` **only** — never in `decodebot/core/`, `decodebot/rules/`, or `decodebot/gui/`.
> - **Wave 4 — OCR Image/Text Recognition Engine (Week 4, PLANNED and OPTIONAL-EXTENSION).** A new, isolated `decodebot/recognition/` package implementing local OCR via OpenCV + `pytesseract` (`FR-249`–`FR-262`, `NFR-091`–`NFR-095`, `NFR-097`). **Optional:** the project remains complete and gradeable without it; `opencv-python-headless` and `pytesseract` are optional dependencies installed only for this engine.
>
> If you are resuming an already-built Week 1 project, **skip directly to Phase 16** — Phases 0–15 describe already-completed work and are retained here only for full-history traceability. Do not re-run or redo them; verify their Definition of Done checklists still hold (nothing should have regressed), then proceed to Phase 16. If Phases 16–24 are already complete, begin at **Wave 3 (W3-M1)**; Wave 4 (W4-M1) is optional and may be skipped entirely.

---

## How To Use This Plan

1. Read `SPEC.md` in full before starting. Do not implement from memory of this plan alone.
2. Execute phases **in order** (Phase 0 → Phase 24 → Wave 3 → Wave 4). Each phase/milestone has hard dependencies on the one before it — do not skip ahead. If Phases 0–15 are already complete (an existing Week 1 + GUI/Animation build), begin at Phase 16. If Phases 16–24 are complete, begin at **W3-M1**. Wave 4 is optional and may be skipped entirely.
3. After finishing each phase, run its listed test IDs before moving to the next phase. A phase is not "done" until its Definition of Done checklist is fully checked.
4. **Phase 1 (Core Compliance MVP) is the single most important phase.** It alone must satisfy 100% of the DecodeLabs Internship Compliance Matrix in `SPEC.md`. Every later phase must be implemented such that it **never** weakens or overrides Phase 1 behavior (see `FR-121` — core rules are protected).
5. **Phases 0–15 (Chatbot Engine, GUI, Animation):** never introduce a machine learning, deep learning, NLP, or LLM library, for any reason (`FR-009`, `NFR-016`, `CON-01`). **Phases 16–24 (ML Engine):** `scikit-learn`, `pandas`, `numpy`, `matplotlib`, and `joblib` are explicitly required and permitted, but **only** inside `decodebot/ml/` (`FR-229`) — never inside `decodebot/core/`, `decodebot/rules/`, or `decodebot/gui/`. **Wave 3 (Recommender):** reuses the same ML libraries **only** inside `decodebot/recommender/` (`FR-233`) — never inside `decodebot/core/`, `decodebot/rules/`, or `decodebot/gui/`. **Wave 4 (OCR):** `opencv-python-headless` and `pytesseract` are **optional** and permitted **only** inside `decodebot/recognition/` (`FR-249`, `FR-250`).
6. Commit after each phase with a message referencing the phase name and FR range covered (e.g., `feat: Phase 3 - session state, history, statistics (FR-064–FR-079)`).

---

## Non-Negotiable Guardrails (Recap)

These apply across **every** phase, without exception:

- ❌ No `spacy`, `nltk`, `transformers`, `torch`, `tensorflow`, `langchain`, `rasa`, or any OpenAI/Gemini/LLM API client, ever (`FR-009`).
- ❌ No network sockets opened by default (`NFR-008`).
- ❌ No `eval()`/`exec()`/`os.system()` with user-controlled string content (`NFR-006`, `NFR-007`).
- ❌ No silent `except: pass` — every catch logs (`Coding Standards → Error Handling`).
- ❌ No feature may cause the loop to crash or hang on any input (`FR-050`, `NFR-020`).
- ✅ Every module uses type hints and docstrings (`Coding Standards`).
- ✅ Every new intent/rule is traceable to an FR ID via an inline comment.
- ✅ Only Python standard library at runtime; `pytest` is dev/test-only (`CON-03`, `NFR-016`).

---

## Definition of Ready (Before Phase 0)

- [ ] `SPEC.md` has been read in full.
- [ ] Python 3.9+ is available in the build environment.
- [ ] `pytest` is installed as a dev dependency only.
- [ ] Git repository is initialized.

---

## Build Order Overview

| Phase | Name | FR Range | Key New Files | Gate to Proceed |
|---|---|---|---|---|
| 0 | Repository Bootstrap | — (NFR-052) | Skeleton, configs, license | Structure matches `SPEC.md` Folder Structure |
| 1 | **Core Compliance MVP** | FR-001–FR-053 | `main.py`, `core/*` (minimal), `utils/normalization.py`, `rules/greetings.py`, `rules/exit.py`, `rules/unknown.py` | 100% of Compliance Matrix passes |
| 2 | Command Layer | FR-054–FR-063 | `rules/help_about_version.py`, `core/responder.py` | `help`/`about`/`version` fully functional |
| 3 | Session, History & Statistics | FR-064–FR-079 | `core/history.py`, `core/stats.py` | `history`/`stats` commands correct |
| 4 | Personalization | FR-080–FR-087 | `rules/personalization.py` | Name capture/interpolation verified |
| 5 | Configuration System | FR-088–FR-095 | `core/config.py`, `config.json`, `docs/CONFIGURATION.md` | Malformed config never crashes app |
| 6 | Logging, Debug & Dev Mode | FR-096–FR-103 | `core/logger.py` | Rotating logs verified; no sensitive data |
| 7 | Error Handling & Resilience | FR-104–FR-111 | Loop-level try/except + circuit breaker | Fuzz test: 0 crashes across 1,000 inputs |
| 8 | Hidden Commands & Easter Eggs | FR-112–FR-117 | `rules/easter_eggs.py`, `docs/HIDDEN_COMMANDS.md` | Hidden commands work, absent from `help` |
| 9 | Plugin/Extensible Rule Engine | FR-118–FR-125 | `core/rule_engine.py` (full), `plugins/README.md`, `docs/PLUGIN_GUIDE.md` | New plugin loads without core changes |
| 10 | CLI Polish & Accessibility | FR-126–FR-133, FR-049 | `utils/terminal.py`, `utils/levenshtein.py`, `utils/formatting.py` (final) | All CLI Specification screens match exactly |
| 11 | Full Test Suite Completion | — (Testing Specification) | Remaining files in `tests/` | 105+ tests pass, ≥90% coverage on `core/`/`rules/` |
| 12 | Documentation & GitHub Packaging | — (GitHub Standards) | `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/ARCHITECTURE.md` | GitHub Standards checklist complete |
| 13 | Final Compliance & Acceptance Sign-off | All | — | Every box in Acceptance Criteria checked |
| 14 | Terminal Animation Layer | FR-134–FR-143 | `core/animation.py`, `tests/test_animations.py` | All TC-ANIM-* pass; Ctrl+C still responsive during animation |
| 15 | Optional Tkinter GUI Layer | FR-144–FR-163 | `gui/*.py`, `tests/test_gui.py`, `docs/GUI_GUIDE.md` | All TC-GUI-* pass; Week 1 Compliance Matrix still 100% via default CLI launch |
| 16 | ML Foundation — Dataset Loader & Validator | FR-164–FR-172 | `ml/dataset.py`, `ml/dataset_loader.py`, `ml/dataset_validator.py` | Iris loads correctly; malformed CSVs rejected cleanly |
| 17 | ML Preprocessing & Train/Test Split | FR-173–FR-186 | `ml/preprocessor.py` | Scaling verified (fit-on-train-only); stratified 80/20 split verified |
| 18 | ML Model Training | FR-187–FR-195 | `ml/trainer.py` | KNN trains correctly; K-tuning and multi-classifier support work |
| 19 | ML Prediction & Evaluation | FR-196–FR-209 | `ml/predictor.py`, `ml/evaluator.py` | Confusion matrix + precision/recall/F1 correct; "accuracy mirage" warning verified |
| 20 | ML Persistence, Comparison & Visualization | FR-210–FR-221 | `ml/model_manager.py`, `ml/visualization.py` | Save/load round-trips; `compare` table correct; plots saved headlessly |
| 21 | ML CLI/GUI Integration, Config, Logging, Error Handling | FR-222–FR-232 | `ml/app_ml.py`, config/logging/dispatcher updates | ML commands in `help`; zero ML imports outside `ml/`; chatbot startup unaffected |
| 22 | ML Full Test Suite Completion | — (ML Testing Strategy) | Remaining `tests/test_*` ML files | 80+ ML tests pass; ≥90% coverage on `decodebot/ml/` |
| 23 | ML Documentation & GitHub Packaging | — (GitHub Standards, Week 2) | `docs/ML_GUIDE.md`, README updates | Week 2 GitHub Standards checklist complete |
| 24 | Final Week 2 Compliance & Acceptance Sign-off | All (Part II) | — | Every box in Week 2 Acceptance Criteria checked; Week 1 Compliance Matrix re-verified unaffected |
| W3-M1 | Recommender Package & Dataset Foundation | FR-233, FR-236–FR-238 | `recommender/__init__.py`, `recommender/corpus.py`, `tests/test_wave3_isolation.py`, `tests/test_recommender_corpus.py` | Corpus loads (≥20 entries, ≥6 domains); isolation gate green |
| W3-M2 | Input & Feature Extraction | FR-239–FR-241 | `recommender/normalization.py`, `recommender/features.py`, `tests/test_recommender_features.py` | Normalization equivalence + shared-vocabulary TF-IDF verified |
| W3-M3 | Ranking Engine & Fallbacks | FR-242–FR-244 | `recommender/ranker.py`, `recommender/fallbacks.py`, `tests/test_recommender_ranker.py` | Cosine Top-N correct; cold-start/zero-match/partial-match handled |
| W3-M4 | CLI Integration | FR-235, FR-239, FR-245, FR-247 | `recommender/app_recommender.py`, `recommender/result.py`, COMMANDS/dispatcher/config wiring, `tests/test_recommender_cli.py` | `recommend` in `help`; boxed output works; fuzz-green; startup < 300ms |
| W3-M5 | GUI Career Recommender Tab | FR-246 | `gui/recommender_panel.py`, `gui/app_gui.py` update, `tests/test_gui_recommender.py` | GUI tab calls identical engine function as the CLI |
| W3-M6 | Test Suite Completion | FR-248 (TC-REC-*) | Remaining `tests/test_recommender*.py` | All TC-REC-* pass; ≥90% coverage on `decodebot/recommender/` |
| W3-M7 | Documentation & Final Wave 3 Sign-off | All Wave 3 (NFR-086–090, NFR-096) | `docs/RECOMMENDER_GUIDE.md`, README/CHANGELOG updates | Wave 3 Acceptance Criteria checked; Weeks 1–2 matrices unaffected |
| W4-M1 | Recognition Package & Image Ingestion | FR-249, FR-252 | `recognition/__init__.py`, `recognition/ingestor.py`, `recognition/result.py`, `tests/test_wave4_isolation.py`, `samples/`, `requirements-ocr.txt` | Ingestion bounds work; isolation gate green |
| W4-M2 | Preprocessing Pipeline | FR-253 | `recognition/preprocess.py`, `tests/test_recognition_preprocess.py` | Grayscale/blur/deskew/threshold verified headless |
| W4-M3 | Tesseract OCR Engine | FR-254–FR-255 | `recognition/ocr_engine.py`, `tests/test_recognition_ocr.py` | Fixture image extracts expected words; missing-dep handled |
| W4-M4 | Confidence Filtering & Output | FR-256–FR-258 | `recognition/filter.py`, finalize `recognition/result.py`, `tests/test_recognition_filter.py`, `tests/test_recognition_output.py` | 80% threshold + statuses + `--save` no-overwrite verified |
| W4-M5 | CLI & GUI Integration | FR-251, FR-259–FR-260 | `recognition/app_recognition.py`, `gui/recognition_panel.py`, COMMANDS/dispatcher/config wiring, `docs/CONFIGURATION.md` update, `tests/test_recognition_cli.py`, `tests/test_gui_recognition.py` | `recognize` in `help`; CLI/GUI parity; startup < 300ms |
| W4-M6 | Testing, Documentation & Final Sign-off | FR-261–FR-262 (TC-OCR-*), NFR-091–095, NFR-097 | Remaining `tests/test_recognition*.py`, `docs/OCR_GUIDE.md`, README/CHANGELOG updates | All TC-OCR-* pass; privacy + isolation green; Wave 4 Acceptance Criteria checked |


---

## Phase 0 — Repository Bootstrap

**Goal:** Establish the exact repository skeleton defined in `SPEC.md → Folder Structure`, with zero functional code yet.

**Files to create:**
```
decodebot-ai/
├── main.py                 (empty stub with TODO, no logic yet)
├── decodebot/__init__.py   (define __version__ = "0.1.0")
├── decodebot/core/__init__.py
├── decodebot/rules/__init__.py
├── decodebot/plugins/README.md
├── decodebot/utils/__init__.py
├── tests/__init__.py
├── docs/ (empty, populated in later phases)
├── logs/.gitkeep
├── requirements.txt        (empty — no runtime deps)
├── requirements-dev.txt     (pytest)
├── pyproject.toml           (black/ruff config, line-length=100)
├── .gitignore               (logs/, __pycache__/, .pytest_cache/, *.pyc)
├── README.md                (placeholder, filled in Phase 12)
├── CONTRIBUTING.md          (placeholder, filled in Phase 12)
├── CHANGELOG.md             (Unreleased section only)
└── LICENSE                  (MIT, full text)
```

**Implements:** Groundwork for `NFR-052` (one-command setup), `NFR-016` (dependency minimalism).

**Definition of Done:**
- [ ] Folder tree matches `SPEC.md → Folder Structure` exactly.
- [ ] `pip install -r requirements-dev.txt && pytest` runs (even with zero tests) without error.
- [ ] `requirements.txt` contains no packages.
- [ ] `LICENSE` file is the full MIT license text.

---

## Phase 1 — Core Compliance MVP (Highest Priority)

**Goal:** Implement the smallest possible working chatbot that satisfies **100% of the DecodeLabs Internship Compliance Matrix** in `SPEC.md`. This phase is the actual internship deliverable; everything after it is enhancement layered on top without ever weakening this behavior.

**Preconditions:** Phase 0 complete.

**Files to create:**
- `decodebot/core/intents.py` — `Intent` enum: at minimum `GREETING`, `EXIT`, `HELP`, `ABOUT`, `VERSION`, `UNKNOWN`, `EMPTY_INPUT`, `NUMERIC_INPUT`, `SYMBOLS_ONLY`.
- `decodebot/utils/normalization.py` — implements the **Input Normalization Algorithm** from `SPEC.md → Algorithms` (`FR-013`–`FR-024`).
- `decodebot/rules/greetings.py` — `GREETING_PATTERNS`, `GREETING_RESPONSES` (`FR-026`–`FR-029`, `FR-033`).
- `decodebot/rules/exit.py` — `EXIT_PATTERNS`, `EXIT_RESPONSES`, negation exclusion list (`FR-036`–`FR-039`, `FR-042`, `FR-044`).
- `decodebot/rules/unknown.py` — fallback response pool (`FR-046`–`FR-047`); fuzzy suggestion (`FR-049`) may be stubbed here and completed in Phase 10.
- `decodebot/core/rule_engine.py` (minimal version) — implements the **Intent Matching Algorithm**; hardcoded imports of the three rule modules above only (full plugin discovery deferred to Phase 9).
- `decodebot/core/dispatcher.py` — the explicit `if`/`elif`/`else` chain required by `FR-006` and the internship rubric, routing `GREETING` / `EXIT` / `HELP` (stub) / `UNKNOWN` / default `else`.
- `decodebot/core/io_handler.py` — injectable `get_input()` / `print_response()` wrappers (`FR-011`, `FR-012`, `FR-022`).
- `decodebot/core/session.py` (minimal) — bare `SessionState` dataclass holding only `history: list` for now (expanded in Phase 3).
- `decodebot/core/loop.py` — implements the **Conversation Loop Algorithm** `while True` structure (`FR-004`, `FR-005`), calling into the dispatcher; exit on `Intent.EXIT` only for now (interrupt/EOF handling wired here but deepened in Phase 7).
- `decodebot/core/app.py` — `run()` bootstrap function called by `main.py`.
- `main.py` — final: `if __name__ == "__main__": app.run()` (`FR-001`, `FR-002`).
- `tests/test_compliance.py` — the 8 mandatory checks (`TC-CORE-001`–`008`).
- `tests/test_greetings.py`, `tests/test_exit.py`, `tests/test_unknown.py` — `TC-GREET-001`–`010`, `TC-EXIT-001`–`010`, `TC-UNK-001`–`008`.
- `tests/test_normalization.py` — covers `TC-U-001`–`009`.
- `tests/test_no_prohibited_imports.py` — static scan gate (`FR-009`, `TC-A-002`).

**Implements:** `FR-001`–`FR-053` (Categories A, B, C, D, E in full).

**Verifies:** All rows of the **DecodeLabs Internship Compliance Matrix**, plus `TC-CORE-001`–`008`, `TC-GREET-001`–`010`, `TC-EXIT-001`–`010`, `TC-UNK-001`–`008`, `TC-U-001`–`020`.

**Definition of Done:**
- [ ] `python main.py` runs, accepts input, loops on a `while` statement, uses explicit `if`/`elif`/`else`.
- [ ] All 8 Compliance Matrix rows pass their mapped tests.
- [ ] `tests/test_no_prohibited_imports.py` passes (zero prohibited imports anywhere in the tree).
- [ ] Program never crashes on empty, numeric, symbol-only, or gibberish input.
- [ ] Word-boundary safety verified (`"history"` ≠ greeting; `"quitter"` ≠ exit).
- [ ] **Stop and fully verify this phase before proceeding — it is the graded deliverable.**

---

## Phase 2 — Command Layer (Help / About / Version)

**Preconditions:** Phase 1 complete and verified.

**Files to create/modify:**
- `decodebot/rules/help_about_version.py` — `COMMANDS` registry single source of truth (`FR-058`), aliases (`FR-059`).
- `decodebot/core/responder.py` — response selection logic factored out of the dispatcher (`get_response()` from the **Response Selection Algorithm**).
- Modify `decodebot/core/dispatcher.py` to route `HELP`, `ABOUT`, `VERSION` through the new `COMMANDS` registry.
- `tests/test_help_about_version.py` — covers `TC-I-003`.

**Implements:** `FR-054`–`FR-063`.

**Definition of Done:**
- [ ] `help` output is generated dynamically from `COMMANDS`, not hardcoded text.
- [ ] `version` output matches `decodebot.__version__` exactly (single source of truth, `FR-056`).
- [ ] All documented aliases (`?`, `info`, `v`, `--version`) route identically to their canonical command.

---

## Phase 3 — Session State, History & Statistics

**Preconditions:** Phase 2 complete.

**Files to create/modify:**
- Expand `decodebot/core/session.py` to the full `SessionState` dataclass (`FR-064`): turn-numbered history, intent counts, timestamps, flags.
- `decodebot/core/history.py` — bounded FIFO buffer (`FR-025`, `FR-067`), `history` command rendering incl. pagination (`FR-068`).
- `decodebot/core/stats.py` — message count, per-intent frequency, duration (monotonic clock), longest/shortest message, avg. response time (`FR-072`–`FR-079`).
- Add `history`, `stats`, `reset` entries to the `COMMANDS` registry from Phase 2.
- `tests/test_session_history_stats.py` — covers `TC-U-022`, `TC-U-023`, `TC-I-004`, `TC-I-005`, `TC-E-011`–`015`.

**Implements:** `FR-064`–`FR-079` (also `FR-061`–`FR-063` command wiring).

**Definition of Done:**
- [ ] History buffer evicts oldest entry at exactly 100 entries (`FR-067`).
- [ ] `stats` and `history` both correctly report "empty/zero" states gracefully (`TC-E-012`, `TC-E-013`).
- [ ] `reset` clears history and stats counters to their initial state (`FR-063`, `FR-077`).
- [ ] Session duration uses `time.monotonic()`, not wall-clock time.

---

## Phase 4 — Personalization

**Preconditions:** Phase 3 complete.

**Files to create/modify:**
- `decodebot/rules/personalization.py` — name extraction patterns (`FR-032`), `set name`/`call me` command (`FR-081`), `forget my name` (`FR-085`), sanitization (`FR-080`, `FR-086`).
- Modify `decodebot/core/responder.py` — `interpolate_personalization()` (`FR-082`), ensuring no literal `"{name}"`/`"None"` leaks when unset (`FR-082` edge case).
- Modify `decodebot/rules/greetings.py` response pool to include name-aware variants.
- `tests/test_personalization.py` — covers `TC-U-024`, `TC-U-025`, `TC-U-029`, `TC-U-030`, `TC-I-002`.

**Implements:** `FR-080`–`FR-087`.

**Definition of Done:**
- [ ] `"my name is Sara"` sets the name and future greetings can include it.
- [ ] Invalid-character-only names are rejected with a clarifying prompt (`FR-086`, `TC-E-014`).
- [ ] `reset` and `forget my name` both correctly clear the stored name (`FR-084`, `FR-085`).

---

## Phase 5 — Configuration System

**Preconditions:** Phase 4 complete.

**Files to create/modify:**
- `decodebot/core/config.py` — loader with per-key validation and default fallback (`FR-088`, `FR-094`); supports `bot_name`, `enable_colors`, `debug_mode`, `developer_mode`, `log_dir`, `plain_mode`, feature flags (`enable_time_aware_greeting`, emoji-greeting toggle).
- `config.json` — shipped example with documented default values.
- `docs/CONFIGURATION.md` — every key documented (`FR-095`).
- `decodebot/rules/help_about_version.py` → add `settings` command wiring (`FR-093`), session-scoped toggle only (not persisted unless explicitly saved).
- `tests/test_config.py` — covers `TC-U-026`, `TC-U-027`, `TC-U-028`, `TC-N-001`, `TC-I-006`, `TC-I-009`, `TC-I-010`.

**Implements:** `FR-088`–`FR-095`.

**Definition of Done:**
- [ ] Deleting `config.json` still allows a normal run using built-in defaults.
- [ ] Malformed JSON is caught, logged as `WARNING`, defaults used — app never crashes on bad config.
- [ ] A single bad key does not invalidate the rest of a valid config file.
- [ ] Every config key appears in `docs/CONFIGURATION.md`.

---

## Phase 6 — Logging, Debug & Developer Mode

**Preconditions:** Phase 5 complete (depends on config for level/toggles).

**Files to create/modify:**
- `decodebot/core/logger.py` — rotating file handler (`FR-096`, `FR-098`), configurable level (`FR-097`), console/file separation (`FR-100`).
- Modify `decodebot/core/dispatcher.py`/`responder.py` — add `[DEBUG]` console diagnostics when `debug_mode` is on (`FR-091`).
- Modify `decodebot/core/dispatcher.py` — add hidden `dumpstate` / `listplugins` commands gated by `developer_mode` (`FR-092`, `FR-102`, `FR-125` — `listplugins` fully wired in Phase 9).
- `tests/test_logging.py` — covers `TC-I-011`, `TC-I-012`, `TC-I-013`.

**Implements:** `FR-096`–`FR-103`.

**Definition of Done:**
- [ ] `logs/decodebot.log` contains startup and shutdown entries after any session.
- [ ] No sensitive data ever appears in logs (there is none by design — verify no accidental logging of full config dumps containing anything beyond documented, non-sensitive keys).
- [ ] Log rotation triggers at 1MB with 3 backups retained.
- [ ] `debug_mode` affects console only; log file verbosity is controlled independently.

---

## Phase 7 — Error Handling & Resilience

**Preconditions:** Phase 6 complete.

**Files to modify:**
- `decodebot/core/loop.py` — wrap the full iteration body per the **Error Recovery Algorithm**: `KeyboardInterrupt` (`FR-104`), `EOFError` (`FR-105`), generic exception safety net (`FR-106`), consecutive-error circuit breaker (`FR-107`).
- `decodebot/core/config.py` — ensure config load failures cannot crash startup (`FR-108`, already partially covered in Phase 5 — confirm here).
- `decodebot/core/rule_engine.py` — isolate individual rule/plugin load failures (`FR-109`) — full effect realized in Phase 9, stub the isolation mechanism now.
- `decodebot/core/io_handler.py` — catch broken-pipe/output failures gracefully (`FR-110`).
- Audit all user-facing strings for tone consistency, no raw tracebacks exposed (`FR-111`).
- `tests/test_error_handling.py` — covers `TC-ERR-001`–`010`, `TC-N-006`, `TC-A-008` (1,000-iteration fuzz harness).

**Implements:** `FR-104`–`FR-111`.

**Definition of Done:**
- [ ] `Ctrl+C` and `Ctrl+D` both exit cleanly with code `0` and a graceful message.
- [ ] A forced exception mid-session is caught, logged with traceback, and the session continues.
- [ ] 5 consecutive forced exceptions trip the circuit breaker and exit with code `1`.
- [ ] 1,000-iteration fuzz test produces zero unhandled exceptions.
- [ ] No console string contains "Traceback" or a raw Python exception class name.

---

## Phase 8 — Hidden Commands & Easter Eggs

**Preconditions:** Phase 7 complete.

**Files to create:**
- `decodebot/rules/easter_eggs.py` — joke pool (`FR-113`), self-awareness gag (`FR-114`), hidden phrase trigger (`FR-115`), registered in a separate hidden-command registry (`FR-112`) not exposed via `help`.
- `docs/HIDDEN_COMMANDS.md` — full internal documentation of every hidden command (`FR-117`).
- Modify `decodebot/core/stats.py` — aggregate easter-egg hits under a single `Intent.EASTER_EGG` counter if `FR-116` is implemented.
- `tests/test_easter_eggs.py` — covers `TC-M-005`.

**Implements:** `FR-112`–`FR-117`.

**Definition of Done:**
- [ ] None of the hidden commands appear in `help` output.
- [ ] Every hidden command is documented in `docs/HIDDEN_COMMANDS.md`.
- [ ] Hidden commands do not collide with any public command or alias.

---

## Phase 9 — Plugin / Extensible Rule Engine

**Preconditions:** Phase 8 complete. This phase upgrades `core/rule_engine.py` from Phase 1's hardcoded imports to full auto-discovery — **without changing any Phase 1 core behavior**.

**Files to create/modify:**
- `decodebot/core/rule_engine.py` — full plugin discovery from `decodebot/rules/` and `decodebot/plugins/` (`FR-118`); enforce the plugin interface contract (`PATTERNS`, `INTENT`, `RESPONSES`, `priority`) (`FR-119`); priority/conflict resolution (`FR-120`); protect the 8 mandatory core intents from override (`FR-121` — critical, re-verify Compliance Matrix still passes after this change); new-intent registration API `register_intent()` (`FR-122`); documented sandbox constraints (`FR-123`).
- `decodebot/plugins/README.md` and `docs/PLUGIN_GUIDE.md` — contributor-facing documentation (`FR-123`).
- `tests/test_plugin_template.py` — example plugin + isolated unit test template (`FR-124`).
- Complete `listplugins` developer command from Phase 6 (`FR-125`).
- `tests/test_rule_engine.py` — covers `TC-I-007`, `TC-I-008`, `TC-N-010`, `TC-R-002`, `TC-R-006`.

**Implements:** `FR-118`–`FR-125`.

**Definition of Done:**
- [ ] **Re-run the full Compliance Matrix test suite from Phase 1 — it must still pass 100%** after this refactor.
- [ ] A new, valid plugin file dropped into `plugins/` is auto-discovered with zero core code changes.
- [ ] A deliberately broken plugin file is isolated (logged, skipped) without affecting core functionality.
- [ ] A plugin attempting to override `EXIT` patterns to empty does not disable real exit behavior.
- [ ] Duplicate intent registration fails fast with a clear startup error.

---

## Phase 10 — CLI Polish & Accessibility

**Preconditions:** Phase 9 complete.

**Files to create/modify:**
- `decodebot/utils/terminal.py` — cross-platform clear-screen (`FR-060`), terminal width detection with 80-column fallback (`FR-131`).
- `decodebot/utils/levenshtein.py` — pure-Python edit distance (`FR-049`'s **Fuzzy Command Suggestion Algorithm**); wire into `decodebot/rules/unknown.py` (`FR-048`, `FR-049`).
- `decodebot/utils/formatting.py` (finalized) — banner (`FR-126`), consistent prefixes (`FR-127`), blank-line spacing (`FR-128`), ANSI colors with auto-fallback (`FR-090`, `FR-129`), exit-screen framing (`FR-130`), echo suppression (`FR-132`), `--plain` mode (`FR-133`).
- Modify `main.py`/`core/app.py` — add `--plain` CLI flag parsing (stdlib `argparse` only).
- `tests/test_cli_formatting.py` — covers `TC-A-011`, `TC-U-014`–`017`, `TC-M-002`.

**Implements:** `FR-126`–`FR-133`, `FR-048`, `FR-049`.

**Definition of Done:**
- [ ] Every screen (Welcome, Help, About, Stats, Settings, Exit) visually matches `SPEC.md → CLI Specification` exactly.
- [ ] `--plain` mode produces zero ANSI codes and zero box-drawing characters.
- [ ] Fuzzy suggestion correctly proposes `"help"` for `"hepl"`/`"halp"` and returns no suggestion for inputs with edit distance > 2.
- [ ] Escalating fallback triggers after exactly 3 consecutive `UNKNOWN` classifications.

---

## Phase 11 — Full Test Suite Completion

**Preconditions:** Phases 0–10 complete. Every feature exists; this phase closes remaining test gaps and confirms totals.

**Tasks:**
- Fill any remaining test files from `SPEC.md → Testing Specification` not yet fully covered by earlier phases: Regression (`TC-R-001`–`010`), Manual/Exploratory checklist (`TC-M-001`–`010`, executed manually and logged), Acceptance (`TC-A-001`–`015`), remaining Negative (`TC-N-002`–`005`, `007`–`009`) and Edge Case tests (`TC-E-001`–`010`).
- Run full coverage report; add tests until `core/` and `rules/` reach ≥90% line coverage (`NFR-034`).
- Confirm total test count ≥ 105 and full suite runtime < 30 seconds (`NFR-036`).
- Confirm zero flaky tests across 10 consecutive runs (`NFR-037`).

**Definition of Done:**
- [ ] All 105+ test cases listed in `SPEC.md` exist and pass.
- [ ] `tests/test_compliance.py` still passes (final regression check).
- [ ] Coverage report confirms ≥90% on `core/` and `rules/`.
- [ ] CI matrix passes on Python 3.9–3.13 (`FR-003`, `NFR-026`).

---

## Phase 12 — Documentation & GitHub Packaging

**Preconditions:** Phase 11 complete.

**Files to finalize:**
- `README.md` — full 11-section structure from `SPEC.md → GitHub Standards`.
- `CONTRIBUTING.md`, `CHANGELOG.md` (v1.0.0 entry), `LICENSE` (confirm final).
- `docs/ARCHITECTURE.md` — expand on `SPEC.md → Architecture` diagrams for contributor onboarding.
- Badges (Python version, license, build status, coverage, "100% Rule-Based").
- Terminal recording/screenshot of a live session (greeting → help → stats → exit).

**Definition of Done:**
- [ ] Every GitHub Standards checklist item in `SPEC.md` is satisfied.
- [ ] A reviewer can go from `git clone` to a working demo in under 5 minutes using only the README (`TC-A-004`).
- [ ] `docs/` contains all four required documents, each cross-linked from the README.

---

## Phase 13 — Final Compliance & Acceptance Sign-off

**Preconditions:** Phases 0–12 complete.

**Tasks:**
- Re-run the **entire** Compliance Matrix from `SPEC.md` end-to-end one final time.
- Walk the **entire** Acceptance Criteria checklist from `SPEC.md` and check every box.
- Verify NFR benchmarks: startup time (`NFR-003`), idle memory (`NFR-043`), idle CPU (`NFR-045`), response latency (`NFR-001`, `NFR-002`, `NFR-047`).
- Confirm `__version__` matches the latest `CHANGELOG.md` entry and the Git release tag (`NFR-048`, `NFR-049`).
- Confirm zero prohibited imports one final time (`tests/test_no_prohibited_imports.py`).

**Definition of Done (Release Gate):**
- [ ] Every row of the Compliance Matrix: ✅
- [ ] Every box of the Acceptance Criteria section: ✅
- [ ] All NFR benchmarks met.
- [ ] Tagged Git release `v1.0.0` created matching `__version__` and `CHANGELOG.md`.
- [ ] **DecodeBot AI v1.0.0 is ready to submit and to publish.**


---

---

## Phase 14 — Terminal Animation Layer

**Preconditions:** Phase 13 complete (v1.0.0 core is done and compliant). This phase and Phase 15 constitute the v1.1 release.

**Files to create:**
- `decodebot/core/animation.py` — typewriter printing (`FR-134`), thinking indicator (`FR-135`), animated banner (`FR-136`), animated clear transition (`FR-137`), injectable clock for testability (`FR-143`).
- Modify `decodebot/core/config.py` — add `enable_animations`, `reduced_motion`, `typing_speed_cps`, `thinking_frame_ms` keys (`FR-138`, `FR-140`).
- Modify `decodebot/core/loop.py` — ensure animation calls respect the 100ms interrupt-responsiveness budget (`FR-141`) and never write frame-by-frame output to logs (`FR-142`).
- Modify `decodebot/utils/terminal.py` — TTY detection for auto-disable (`FR-139`).
- `tests/test_animations.py` — `TC-ANIM-001`–`008`.

**Implements:** `FR-134`–`FR-143`.

**Definition of Done:**
- [ ] All animation effects are toggleable via `enable_animations` and auto-disable on non-TTY output.
- [ ] `Ctrl+C` remains responsive within 100ms during any animation.
- [ ] `reduced_motion` shows static equivalents, not just "off".
- [ ] **Re-run the full Week 1 Compliance Matrix — it must still pass 100%** (animations must never alter classification or block input).
- [ ] Log file contains one entry per response, never per animation frame.

---

## Phase 15 — Optional Tkinter GUI Layer

**Preconditions:** Phase 14 complete.

**Files to create:**
- `decodebot/gui/__init__.py`
- `decodebot/gui/app_gui.py` — window bootstrap, `--gui` flag handling, headless fallback (`FR-144`, `FR-160`).
- `decodebot/gui/widgets.py` — chat bubble, entry field, send button (`FR-146`–`FR-148`).
- `decodebot/gui/animations.py` — typing indicator, fade-in, using `Tkinter.after()` only (`FR-149`, `FR-150`).
- `decodebot/gui/theme.py` — shared color palette with CLI (`FR-151`, `FR-152`).
- `docs/GUI_GUIDE.md` — layout, theming, accessibility documentation (`NFR-065`).
- `tests/test_gui.py` — `TC-GUI-001`–`012`.
- Modify `decodebot/core/dispatcher.py`/`rule_engine.py` — confirm zero changes needed; if any GUI-specific branching creeps in here, refactor it out immediately (`FR-145` is non-negotiable).
- Modify `tests/test_no_prohibited_imports.py` — extend the scan to reject non-stdlib GUI imports (`FR-163`).

**Implements:** `FR-144`–`FR-163`.

**Definition of Done:**
- [ ] `python main.py --gui` launches a working window; `python main.py` (no flag) is completely unaffected.
- [ ] GUI calls the identical `classify_intent()`/`get_response()` functions as the CLI — zero duplicated rule logic (`FR-145`, verified by `TC-GUI-003`).
- [ ] All CLI commands work identically inside the GUI (`FR-153`).
- [ ] Headless environments fall back to CLI with a logged warning instead of crashing (`FR-160`).
- [ ] **Re-run the full Week 1 Compliance Matrix one final time — it must still pass 100% via the default CLI launch** (`FR-161`).
- [ ] Zero non-stdlib GUI dependencies present (`FR-163`).
- [ ] `docs/GUI_GUIDE.md` is complete.
- [ ] **v1.1.0 milestone reached.** Everything above this line (Phases 0–15) represents the pre-Week-2 baseline. If you are starting fresh from an existing project, this is where you resume: proceed to Phase 16.

---

## Phase 16 — Machine Learning Foundation: Dataset Loader & Validator

**Preconditions:** Phase 15 complete (v1.1.0 baseline verified). This phase begins the v2.0.0 Week 2 release. **From this phase forward, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, and `joblib` are permitted — but only inside `decodebot/ml/`.**

**Files to create:**
- `decodebot/ml/__init__.py`
- `decodebot/ml/dataset.py` — the `Dataset` dataclass shared by all ML modules.
- `decodebot/ml/dataset_loader.py` — Iris loading via `sklearn.datasets.load_iris()`, CSV loading via `pandas` (`FR-164`–`FR-166`, `FR-168`).
- `decodebot/ml/dataset_validator.py` — missing-value/class-count/sample-count validation (`FR-169`–`FR-170`).
- Update `requirements.txt` with the clearly-labeled ML dependency section (`FR-230`).
- `datasets/README.md` — notes on the bundled Iris dataset and future CSV format.
- `tests/test_dataset_loader.py`, `tests/test_dataset_validator.py`, `tests/test_ml_isolation.py` (start this test now — it must remain green through every subsequent phase).
- `tests/test_ml_compliance.py` — scaffold the 8-row Week 2 compliance gate; rows 1 (dataset loading) should already be passable after this phase.

**Implements:** `FR-164`–`FR-172` (Category R1).

**Verifies:** `TC-ML-001`–`010`.

**Definition of Done:**
- [ ] `load_dataset("iris")` returns 150 samples, 4 features, 3 classes matching the official brief's benchmark.
- [ ] Class balance reporting works (Iris reports as perfectly balanced, 1.0 ratio).
- [ ] Malformed/missing datasets are caught and produce friendly errors, never a crash.
- [ ] `tests/test_ml_isolation.py` passes: **zero** `sklearn`/`pandas`/`numpy` imports exist anywhere outside `decodebot/ml/` at this point in the build.
- [ ] Re-run the Week 1 Compliance Matrix — still 100% (new ML files must not have touched chatbot code).

**Suggested Commit Message:** `feat: Phase 16 - ML dataset loader & validator (FR-164-FR-172)`

---

## Phase 17 — Machine Learning Preprocessing & Train/Test Split

**Preconditions:** Phase 16 complete.

**Files to create:**
- `decodebot/ml/preprocessor.py` — `StandardScaler`/`MinMaxScaler` support, fit-on-train-only discipline, shuffling, `LabelEncoder` for CSV targets, `sklearn.pipeline.Pipeline` composition (`FR-173`–`FR-181`).
- Extend `decodebot/ml/preprocessor.py` — `train_test_split` with stratification and configurable `test_size`/`random_state` (`FR-182`–`FR-186`).
- `tests/test_preprocessor.py` — covers scaling correctness, fit-on-train-only (data leakage regression test, `FR-184`), stratification, reproducibility.

**Implements:** `FR-173`–`FR-186` (Categories R2, R3).

**Verifies:** `TC-ML-011`–`028`.

**Definition of Done:**
- [ ] Post-scaling features have mean ≈ 0, variance ≈ 1 on the training set.
- [ ] A dedicated regression test proves the scaler is fit **only** on `X_train`, never on `X_test` or the full dataset.
- [ ] 80/20 stratified split verified on Iris: 120 train / 30 test, proportional class representation.
- [ ] Same `random_state` produces bit-identical splits across repeated runs.
- [ ] `tests/test_ml_isolation.py` still passes.

**Suggested Commit Message:** `feat: Phase 17 - ML preprocessing & train/test split (FR-173-FR-186)`

---

## Phase 18 — Machine Learning Model Training

**Preconditions:** Phase 17 complete.

**Files to create:**
- `decodebot/ml/trainer.py` — `KNeighborsClassifier` baseline (`FR-187`–`FR-189`), configurable K (`FR-188`), K-tuning elbow method (`FR-190`), multi-classifier support (Decision Tree, Logistic Regression, SVM, Random Forest) behind one interface (`FR-191`), training time tracking (`FR-192`), error handling (`FR-193`), reproducibility hook (`FR-195`).
- Wire the `train` command scaffold (full CLI wiring completes in Phase 21) (`FR-194`).
- `tests/test_trainer.py` — covers KNN fit correctness, K-tuning, classifier-swap, invalid-K handling.

**Implements:** `FR-187`–`FR-195` (Category R4).

**Verifies:** `TC-ML-029`–`038`.

**Definition of Done:**
- [ ] `KNeighborsClassifier(n_neighbors=5)` trains successfully on the Iris training set, matching the brief's exact workflow.
- [ ] K-tuning across a range (default 1–20) correctly identifies the lowest-error K.
- [ ] Swapping `classifier_type` to `"decision_tree"` (etc.) works through the identical `train()` interface.
- [ ] Invalid hyperparameters (K ≤ 0, K > training set size) produce friendly errors, never a crash.
- [ ] Two consecutive trainings with the same `random_state`/data produce identical trained model parameters.

**Suggested Commit Message:** `feat: Phase 18 - ML model training, KNN + multi-classifier support (FR-187-FR-195)`

---

## Phase 19 — Machine Learning Prediction & Evaluation

**Preconditions:** Phase 18 complete.

**Files to create:**
- `decodebot/ml/predictor.py` — batch prediction (`FR-196`), single-sample prediction (`FR-197`), probability output (`FR-198`), "no trained model" guard (`FR-199`), output formatting (`FR-200`).
- `decodebot/ml/evaluator.py` — accuracy (`FR-201`), confusion matrix (`FR-202`), precision/recall/F1 (`FR-203`), "accuracy mirage" warning (`FR-204`), `EvaluationReport` object (`FR-205`), cross-validation (`FR-207`), determinism (`FR-208`), baseline comparison (`FR-209`).
- Wire the `evaluate` command scaffold (`FR-206`; full CLI wiring completes in Phase 21).
- `tests/test_predictor.py`, `tests/test_evaluator.py` — covers all of the above, including the imbalance-warning trigger test.

**Implements:** `FR-196`–`FR-209` (Categories R5, R6).

**Verifies:** `TC-ML-039`–`058`.

**Definition of Done:**
- [ ] Batch prediction on the Iris test set returns correct-length, valid-class output.
- [ ] Single-sample prediction correctly classifies the canonical Iris example `[5.1, 3.5, 1.4, 0.2]` as `"setosa"`.
- [ ] Confusion matrix, precision, recall, and F1 are all computed and reported — **never accuracy alone** (`NFR-080`).
- [ ] A synthetic imbalanced dataset triggers the "accuracy mirage" warning; Iris (balanced) does not.
- [ ] **Week 2 Compliance Matrix rows 5, 6, and 7 now pass** (`tests/test_ml_compliance.py`).

**Suggested Commit Message:** `feat: Phase 19 - ML prediction & evaluation (FR-196-FR-209)`

---

## Phase 20 — Machine Learning Persistence, Comparison & Visualization

**Preconditions:** Phase 19 complete.

**Files to create:**
- `decodebot/ml/model_manager.py` — save/load via `joblib` (`FR-210`–`FR-211`), security boundary on model loading (`FR-212`), metadata recording (`FR-213`), `models` listing command scaffold (`FR-214`), `compare` utility (`FR-215`), best-model auto-selection (`FR-216`).
- `decodebot/ml/visualization.py` — confusion matrix heatmap (`FR-217`), K-tuning elbow curve (`FR-218`), before/after scaling plot (`FR-219`), model comparison bar chart (`FR-220`), non-blocking file-based rendering (`FR-221`).
- `models/.gitkeep`, `outputs/.gitkeep`.
- `tests/test_model_manager.py`, `tests/test_visualization.py`.

**Implements:** `FR-210`–`FR-221` (Categories R7, R8).

**Verifies:** `TC-ML-059`–`070+` (persistence/comparison/visualization subset).

**Definition of Done:**
- [ ] A trained model saves to `models/` and reloads with identical prediction behavior.
- [ ] Model loading from outside `models/` is blocked by default (`FR-212`), with an explicit opt-in flag required.
- [ ] `compare` trains/evaluates multiple classifiers on the identical split and reports a correct side-by-side table.
- [ ] Confusion matrix heatmap and K-tuning curve save correctly to `outputs/`, including in a headless (no-display) test environment.
- [ ] No visualization call ever opens a blocking window from the CLI path.

**Suggested Commit Message:** `feat: Phase 20 - ML model persistence, comparison & visualization (FR-210-FR-221)`

---

## Phase 21 — Machine Learning CLI/GUI Integration, Configuration, Logging & Error Handling

**Preconditions:** Phase 20 complete. This phase wires everything built in Phases 16–20 into the existing Chatbot Engine's dispatcher, config, and logging systems — **without modifying any Week 1 chatbot behavior.**

**Files to create/modify:**
- `decodebot/ml/app_ml.py` — thin bootstrap registering `train`, `predict`, `evaluate`, `explore`, `models`, `compare`, `tune-k` into the existing `COMMANDS` registry (`FR-222`).
- Modify `decodebot/core/dispatcher.py` — route ML commands to `app_ml.py` handlers; add a static-analysis-friendly boundary comment confirming no chat-text ever reaches a `scikit-learn` model (`FR-223`).
- If the GUI (Phase 15) was built: `decodebot/gui/ml_panel.py` — new "Machine Learning" tab calling the identical `app_ml.py` functions as the CLI (`FR-224`), plus the interactive `predict` form (`FR-225`).
- Modify `decodebot/core/config.py` — add the 8 ML config keys from `FR-226`.
- Modify `decodebot/core/logger.py` usage in `decodebot/ml/*.py` — `decodebot.ml` logger tag (`FR-227`).
- Ensure every ML error path routes through the friendly-message pattern (`FR-228`).
- Confirm `tests/test_ml_isolation.py` still passes with the new dispatcher wiring (`FR-229`).
- Confirm lazy imports: `decodebot/ml/*.py` modules are only imported when an ML command first runs, not at `main.py` startup (`FR-232`).
- Confirm the ML Engine works fully via `python main.py --plain` with zero GUI dependency (`FR-231`).
- `docs/CONFIGURATION.md` — extended with the 8 new ML keys.
- `tests/test_ml_compliance.py` — complete all remaining rows now that CLI wiring exists.

**Implements:** `FR-222`–`FR-232` (Category R9).

**Verifies:** Remaining `TC-ML-059`–`070+`; full `tests/test_ml_compliance.py` (all 8 rows).

**Definition of Done:**
- [x] `help` output lists all ML commands, clearly grouped, alongside the existing Chatbot commands.
- [x] **Re-run the full Week 1 Compliance Matrix — it must still pass 100%** (this is the highest-risk phase for accidental chatbot regression, since it touches `dispatcher.py`).
- [x] `python main.py` (chatbot-only session, no ML command invoked) still starts in under 300ms (`NFR-075`), confirming lazy ML imports work.
- [x] `tests/test_ml_isolation.py` passes with the dispatcher changes included.
- [x] **All 8 rows of the Week 2 Compliance Matrix now pass.**
- [x] If GUI was built: the ML panel's "Train"/"Classify" buttons call the identical functions as their CLI equivalents.

**Suggested Commit Message:** `feat: Phase 21 - ML CLI/GUI integration, config, logging, error handling (FR-222-FR-232)`

---

## Phase 22 — Machine Learning Full Test Suite Completion

**Preconditions:** Phase 21 complete. Every ML feature exists; this phase closes remaining test gaps.

**Tasks:**
- Fill any remaining test files from the ML Testing Strategy not yet fully covered: Regression (8), Manual/Exploratory checklist (6, executed manually and logged), Acceptance (10), remaining Negative and Edge Case tests.
- Run full coverage report on `decodebot/ml/`; add tests until ≥ 90% line coverage is reached (`NFR-076`).
- Confirm total new ML test count ≥ 80, combined project test total ≥ 205 (`NFR-036`-style runtime budget still respected).
- Confirm `tests/test_ml_isolation.py` and the Week 1 Compliance Matrix both remain green.

**Definition of Done:**
- [x] All 80+ ML test cases exist and pass.
- [x] `tests/test_ml_compliance.py` (8/8) and `tests/test_compliance.py` (Week 1, 8/8) both pass in the same test run.
- [x] Coverage report confirms ≥90% on `decodebot/ml/`.
- [x] Combined test suite (Week 1 + GUI/Animation + Week 2) runs in a reasonable CI time budget.

**Suggested Commit Message:** `test: Phase 22 - complete ML test suite, 80+ cases, isolation verified`

---

## Phase 23 — Machine Learning Documentation & GitHub Packaging

**Preconditions:** Phase 22 complete.

**Files to finalize:**
- `docs/ML_GUIDE.md` — pipeline explanation, configuration reference, CLI/GUI usage walkthrough.
- `README.md` — add the "Machine Learning Engine" section, dataset attribution, `scikit-learn`/"Supervised Learning" badges, updated `requirements.txt` explanation (Chatbot vs. ML dependency split).
- `CHANGELOG.md` — add the `v2.0.0` entry: "Added: Machine Learning Data Classification Engine (Week 2). Preserved: 100% rule-based Chatbot Engine (Week 1), unchanged."
- Screenshot/GIF of a `train` → `evaluate` session (and the GUI ML panel + predict form, if built).

**Definition of Done:**
- [x] Every Week 2 GitHub Standards checklist item in `SPEC.md` Part II is satisfied.
- [x] A reviewer can go from `git clone` to a working `train`/`evaluate` demo using only the README.
- [x] `docs/ML_GUIDE.md` is complete and cross-linked from the README.

**Suggested Commit Message:** `docs: Phase 23 - ML documentation & GitHub packaging (Week 2)`

---

## Phase 24 — Final Week 2 Compliance & Acceptance Sign-off

**Preconditions:** Phases 16–23 complete.

**Tasks:**
- Re-run the **entire** Week 2 Compliance Matrix from `SPEC.md` end-to-end one final time.
- Re-run the **entire** Week 1 Compliance Matrix one final time — confirm zero regression across the whole Week 2 build.
- Walk the **entire** Week 2 Acceptance Criteria checklist from `SPEC.md` and check every box.
- Verify Week 2 NFR benchmarks: training time (`NFR-066`), prediction latency (`NFR-067`), full pipeline time (`NFR-068`), chatbot startup time unaffected (`NFR-075`).
- Confirm `tests/test_ml_isolation.py` passes one final time.
- Confirm `__version__` reflects `2.0.0` and `CHANGELOG.md` matches.

**Definition of Done (Release Gate):**
- [x] Every row of the Week 1 Compliance Matrix: ✅ (unchanged, re-verified)
- [x] Every row of the Week 2 Compliance Matrix: ✅
- [x] Every box of the Week 1 and Week 2 Acceptance Criteria sections: ✅
- [x] All Part I and Part II NFR benchmarks met.
- [ ] Tagged Git release `v2.0.0` created matching `__version__` and `CHANGELOG.md`. (pending: git tag + push — requires explicit approval)
- [x] **DecodeBot AI v2.0.0 (Chatbot Engine + Machine Learning Engine) is ready to submit and to publish.**

**Suggested Commit Message:** `release: v2.0.0 - Week 2 Machine Learning Engine complete, Week 1 preserved`

---

## Wave 3 (Week 3) — Content-Based Tech Stack Recommendation Engine (PLANNED)

> **Status: PLANNED.** This Wave must NOT be started until (a) Phases 16–24 (Week 2) are complete and verified, and (b) the user explicitly approves starting Wave 3. It implements `SPEC.md → Part III` (`FR-233`–`FR-248`, `NFR-086`–`NFR-090`, `NFR-096`). **Only `decodebot/recommender/` may import the ML libraries** (`scikit-learn`/`pandas`/`numpy`), lazily, per `FR-233`. Every milestone ends with a **mandatory stop for user approval**.
>
> **Non-negotiable gates for every Wave 3 milestone:** `tests/test_wave3_isolation.py` passes; `python main.py` (chatbot-only) starts in < 300ms; Week 1 and Week 2 Compliance Matrices still pass 100%.

---

### W3-M1 — Recommender Package & Dataset Foundation

- **Scope:** Create the isolated `decodebot/recommender/` package skeleton, the built-in careers corpus, CSV corpus support, validation, and the `CareerProfile`/`SkillSet`/`RecommendationResult` data model. No ranking logic yet.
- **Files to create/modify:** `decodebot/recommender/__init__.py`, `decodebot/recommender/corpus.py` (built-in corpus + CSV loading + validation + data model), `tests/test_wave3_isolation.py` (isolation gate — must stay green through every Wave 3 milestone), `tests/test_recommender_corpus.py`. No changes to existing engine code.
- **Implements (Requirements satisfied):** `FR-233`, `FR-236`, `FR-237`, `FR-238`.
- **Verifies (Tests required):** `TC-REC-001`, `TC-REC-002`, `TC-REC-003`.
- **Manual verification:** `python main.py` launches normally; the built-in corpus loads via a small REPL check; a deliberately malformed CSV is rejected with a friendly error.
- **Documentation updates:** none required this milestone (config keys land in W3-M4).
- **Performance / isolation checks:** `tests/test_wave3_isolation.py` green (zero `decodebot.recommender` imports in `core/`/`rules/`/`gui/`, zero eager ML-library imports); chatbot-only startup < 300ms.
- **Exit criteria:** all TC-REC-001–003 pass; corpus integrity verified (≥ 20 entries, ≥ 6 domains, no duplicate titles); malformed CSV → friendly error, never a crash.
- **One scoped commit:** `feat: W3-M1 - recommender package & corpus foundation (FR-233, FR-236-FR-238)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** before starting W3-M2.

---

### W3-M2 — Input & Feature Extraction

- **Scope:** Engine-level skill parsing/normalization and TF-IDF vectorization of corpus + query under a single fitted vocabulary. (CLI command registration completes in W3-M4.)
- **Files to create/modify:** `decodebot/recommender/normalization.py`, `decodebot/recommender/features.py`, `tests/test_recommender_features.py`.
- **Implements (Requirements satisfied):** `FR-239` (engine-level skill parsing; CLI registration completes in W3-M4), `FR-240`, `FR-241`.
- **Verifies (Tests required):** `TC-REC-004`, `TC-REC-005`.
- **Manual verification:** unit-level check that `"Python, SQL, machine learning"` and `"python,sql,machine learning"` tokenize identically; transformed query dimensionality equals the profile matrix dimensionality.
- **Documentation updates:** none.
- **Performance / isolation checks:** vectorization latency < 100ms on the built-in corpus (NFR-086 checkpoint); isolation gate still green.
- **Exit criteria:** normalization equivalence and shared-vocabulary TF-IDF tests pass.
- **One scoped commit:** `feat: W3-M2 - skill normalization & TF-IDF feature extraction (FR-239-FR-241)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** before starting W3-M3.

---

### W3-M3 — Ranking Engine & Fallbacks

- **Scope:** Cosine-similarity ranking, deterministic tie-breaking, Top-N default 3 (validated 1–10, clamped to corpus size), and cold-start / zero-match / partial-match fallback handling.
- **Files to create/modify:** `decodebot/recommender/ranker.py`, `decodebot/recommender/fallbacks.py`, finalize `decodebot/recommender/result.py`, `tests/test_recommender_ranker.py`.
- **Implements (Requirements satisfied):** `FR-242`, `FR-243`, `FR-244`.
- **Verifies (Tests required):** `TC-REC-006`, `TC-REC-007`, `TC-REC-008`, `TC-REC-009`.
- **Manual verification:** canonical query `"Python, SQL, Machine Learning"` returns exactly 3 ranked results, highest-similarity first; a repeated run is identical; < 3 skills → guidance; out-of-vocabulary query → zero-match status.
- **Documentation updates:** none.
- **Performance / isolation checks:** NFR-086 latency checkpoint (< 100ms); NFR-087 determinism verified; isolation gate green.
- **Exit criteria:** all ranker/fallback tests pass.
- **One scoped commit:** `feat: W3-M3 - cosine ranking, Top-N & fallback handling (FR-242-FR-244)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** before starting W3-M4.

---

### W3-M4 — CLI Integration

- **Scope:** Register `recommend` in the `COMMANDS` registry (`FR-058`), wire it into the dispatcher, add the `FR-235` config keys, add the `decodebot.recommender` logger tag, and render structured boxed CLI output honoring `--plain` (`FR-133`).
- **Files to create/modify:** `decodebot/recommender/app_recommender.py` (thin bootstrap), modify `decodebot/rules/help_about_version.py` (COMMANDS entry), modify `decodebot/core/dispatcher.py` (route `recommend`), modify `decodebot/core/config.py` (`FR-235` keys), extend `docs/CONFIGURATION.md`, `tests/test_recommender_cli.py`.
- **Implements (Requirements satisfied):** `FR-235`, `FR-239` (CLI registration), `FR-245`, `FR-247`.
- **Verifies (Tests required):** `TC-REC-010`, `TC-REC-011`, `TC-REC-012`.
- **Manual verification:** `python main.py recommend --skills "Python, SQL, Machine Learning"` prints a boxed top-3; `--plain` prints plain output; `help` lists `recommend`; missing `--skills` shows a friendly usage message.
- **Documentation updates:** `docs/CONFIGURATION.md` extended with the five recommender keys and valid ranges.
- **Performance / isolation checks:** lazy imports verified — chatbot-only startup < 300ms (NFR-090); `tests/test_wave3_isolation.py` and `tests/test_ml_isolation.py` both green; 1,000-iteration fuzz on malformed `recommend` invocations → zero unhandled exceptions (FR-247).
- **Exit criteria:** TC-REC-010/011/012 pass; `recommend` appears in `help`; fuzz-green.
- **One scoped commit:** `feat: W3-M4 - recommend CLI, config, logging & error handling (FR-235, FR-239, FR-245, FR-247)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** before starting W3-M5.

---

### W3-M5 — GUI Career Recommender Tab

- **Scope:** Add the Tkinter "Career Recommender" tab calling the identical engine function as the CLI.
- **Files to create/modify:** `decodebot/gui/recommender_panel.py`, modify `decodebot/gui/app_gui.py` (tab registration), `tests/test_gui_recommender.py` (headless-safe, mirroring `test_gui.py` patterns).
- **Implements (Requirements satisfied):** `FR-246`.
- **Verifies (Tests required):** `TC-REC-010` (GUI-parity half).
- **Manual verification:** `python main.py --gui` → Career Recommender tab → enter `Python, SQL, Machine Learning` → click "Recommend" → same top-3 as the CLI; empty entry → inline validation, GUI stays responsive.
- **Documentation updates:** `docs/GUI_GUIDE.md` extended with the new tab.
- **Performance / isolation checks:** GUI module presence never affects default (non-`--gui`) CLI behavior; isolation gate green.
- **Exit criteria:** GUI parity test passes; tab renders the same results as the CLI.
- **One scoped commit:** `feat: W3-M5 - Career Recommender GUI tab (FR-246)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** before starting W3-M6.

---

### W3-M6 — Test Suite Completion

- **Scope:** Close remaining TC-REC-* gaps; reach ≥ 90% line coverage on `decodebot/recommender/` (NFR-089); add any missing negative/edge/fuzz cases.
- **Files to create/modify:** remaining `tests/test_recommender*.py` files.
- **Implements (Requirements satisfied):** `FR-248`.
- **Verifies (Tests required):** full `TC-REC-001`–`012` suite; `NFR-089` coverage target.
- **Manual verification:** full test suite (Weeks 1 + 2 + Wave 3) runs green; coverage report confirms ≥ 90% on `decodebot/recommender/`.
- **Documentation updates:** none.
- **Performance / isolation checks:** full isolation + startup re-verification; Week 1 and Week 2 Compliance Matrices still pass 100%.
- **Exit criteria:** all TC-REC-* pass; coverage ≥ 90%; zero regressions.
- **One scoped commit:** `test: W3-M6 - complete recommender test suite (FR-248)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** before starting W3-M7.

---

### W3-M7 — Documentation & Final Wave 3 Sign-off

- **Scope:** `docs/RECOMMENDER_GUIDE.md`, README section + badge, CHANGELOG v3.0.0 entry, and a full walk of the Part III Acceptance Criteria.
- **Files to create/modify:** `docs/RECOMMENDER_GUIDE.md`, modify `README.md`, `CHANGELOG.md`.
- **Implements (Requirements satisfied):** `NFR-096`; `FR-248` acceptance gate.
- **Verifies (Tests required):** Part III Acceptance Criteria (all boxes).
- **Manual verification:** a reviewer can run `recommend --skills "Python, SQL, Machine Learning"` from the README alone.
- **Documentation updates:** `docs/RECOMMENDER_GUIDE.md`, README, CHANGELOG (`v3.0.0` entry).
- **Performance / isolation checks:** final re-verification of isolation + startup + Weeks 1–2 compliance.
- **Exit criteria:** Part III Acceptance Criteria checked; docs complete; **Wave 3 milestone reached (v3.0.0)**.
- **One scoped commit:** `docs: W3-M7 - recommender guide, README, CHANGELOG (Wave 3 complete)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** — either to proceed to the optional Wave 4 or to tag the v3.0.0 release.

---

## Wave 4 (Week 4) — OCR Image/Text Recognition Engine (OPTIONAL EXTENSION, PLANNED)

> **Status: PLANNED and OPTIONAL-EXTENSION.** This Wave is **optional** and must NOT be started until (a) Wave 3 is complete and approved, and (b) the user explicitly approves starting Wave 4. It implements `SPEC.md → Part IV` (`FR-249`–`FR-262`, `NFR-091`–`NFR-095`, `NFR-097`). **`opencv-python-headless` and `pytesseract` are optional dependencies** permitted **only** inside `decodebot/recognition/` (`FR-249`, `FR-250`); Tesseract is an external binary invoked via `pytesseract`. Every milestone ends with a **mandatory stop for user approval**.
>
> **Non-negotiable gates for every Wave 4 milestone:** `tests/test_wave4_isolation.py` passes; `python main.py` (chatbot-only) starts in < 300ms with OCR deps installed-but-unused; Weeks 1–3 Compliance Matrices still pass 100%. CI must never require OpenCV or Tesseract installed (all such paths tested via mocks).

---

### W4-M1 — Recognition Package & Image Ingestion

- **Scope:** Create the isolated `decodebot/recognition/` package skeleton, the ingestion module (formats, existence, file-size and dimension bounds), the `RecognitionResult` scaffold, the `samples/` fixture image, and the optional-dependency manifest.
- **Files to create/modify:** `decodebot/recognition/__init__.py`, `decodebot/recognition/ingestor.py`, `decodebot/recognition/result.py` (scaffold), `tests/test_wave4_isolation.py` (isolation gate — must stay green through every Wave 4 milestone), `tests/test_recognition_ingestion.py`, `samples/README.md`, `samples/sample_text.png` (fixture), `requirements-ocr.txt` (documented; **not** installed in the base venv).
- **Implements (Requirements satisfied):** `FR-249`, `FR-252` (config keys `FR-251` wire in W4-M5).
- **Verifies (Tests required):** `TC-OCR-001`, `TC-OCR-002`.
- **Manual verification:** chatbot runs with neither OpenCV nor pytesseract installed; missing file, > 10MB file, and over-dimension image each produce a friendly error.
- **Documentation updates:** `requirements-ocr.txt` + README optional-dependency note.
- **Performance / isolation checks:** `tests/test_wave4_isolation.py` green (zero `cv2`/`pytesseract`/`decodebot.recognition` imports outside the allowed scope); chatbot-only startup < 300ms with OCR deps absent.
- **Exit criteria:** TC-OCR-001/002 pass; ingestion bounds verified.
- **One scoped commit:** `feat: W4-M1 - recognition package & image ingestion (FR-249, FR-252)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** before starting W4-M2.

---

### W4-M2 — Preprocessing Pipeline

- **Scope:** Grayscale → Gaussian blur → deskew → adaptive thresholding, each stage a separate, headless-safe, testable function.
- **Files to create/modify:** `decodebot/recognition/preprocess.py`, `tests/test_recognition_preprocess.py`.
- **Implements (Requirements satisfied):** `FR-253`.
- **Verifies (Tests required):** `TC-OCR-003`, `TC-OCR-004`.
- **Manual verification:** run the pipeline on the fixture image; deskew corrects a synthetic 3°-skewed image to within ~0.5°; blank image yields `no_text` without crashing.
- **Documentation updates:** none.
- **Performance / isolation checks:** pipeline completes < 1s on the fixture (NFR-093 checkpoint); isolation gate green.
- **Exit criteria:** TC-OCR-003/004 pass.
- **One scoped commit:** `feat: W4-M2 - OCR preprocessing pipeline (FR-253)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** before starting W4-M3.

---

### W4-M3 — Tesseract OCR Engine

- **Scope:** `pytesseract.image_to_data` wrapper supporting PSM modes 3/6/7/11 (default 6), per-word data collection, and friendly missing-dependency/binary handling.
- **Files to create/modify:** `decodebot/recognition/ocr_engine.py`, finalize `requirements-ocr.txt`, `tests/test_recognition_ocr.py` (mocked tesseract; real fixture used when Tesseract is available).
- **Implements (Requirements satisfied):** `FR-254`, `FR-255`.
- **Verifies (Tests required):** `TC-OCR-005`, `TC-OCR-010`.
- **Manual verification:** fixture image yields expected words with per-word confidence; simulated missing dependency/binary → friendly message, no crash.
- **Documentation updates:** README / `requirements-ocr.txt` install instructions.
- **Performance / isolation checks:** OCR latency checkpoint; isolation gate green.
- **Exit criteria:** TC-OCR-005/010 pass.
- **One scoped commit:** `feat: W4-M3 - Tesseract OCR engine, PSM modes, graceful degradation (FR-254-FR-255)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** before starting W4-M4.

---

### W4-M4 — Confidence Filtering & Output

- **Scope:** Default 80% confidence threshold filtering, low-confidence routing, the four recognition statuses, the finalized structured `RecognitionResult`, and `--save` output with no-overwrite protection.
- **Files to create/modify:** `decodebot/recognition/filter.py`, finalize `decodebot/recognition/result.py`, `tests/test_recognition_filter.py`, `tests/test_recognition_output.py`.
- **Implements (Requirements satisfied):** `FR-256`, `FR-257`, `FR-258` (engine-level; CLI `--save` wiring completes in W4-M5).
- **Verifies (Tests required):** `TC-OCR-006`, `TC-OCR-007`, `TC-OCR-008`.
- **Manual verification:** a fixture with a low-confidence word routes that word to `low_confidence_words`; each status demonstrated; `--save` refuses to overwrite an existing file.
- **Documentation updates:** none.
- **Performance / isolation checks:** no-overwrite behavior verified; isolation gate green.
- **Exit criteria:** TC-OCR-006/007/008 pass.
- **One scoped commit:** `feat: W4-M4 - confidence filtering & recognition output (FR-256-FR-258)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** before starting W4-M5.

---

### W4-M5 — CLI & GUI Integration

- **Scope:** Register `recognize` in `COMMANDS`, wire the dispatcher, add the `FR-251` config keys, add the `decodebot.recognition` logger tag, render boxed CLI output honoring `--plain`, and add the GUI "Recognition" tab.
- **Files to create/modify:** `decodebot/recognition/app_recognition.py`, modify `decodebot/rules/help_about_version.py`, `decodebot/core/dispatcher.py`, `decodebot/core/config.py`, `decodebot/gui/recognition_panel.py`, `decodebot/gui/app_gui.py`, extend `docs/CONFIGURATION.md`, `tests/test_recognition_cli.py`, `tests/test_gui_recognition.py`.
- **Implements (Requirements satisfied):** `FR-251`, `FR-259`, `FR-260`.
- **Verifies (Tests required):** `TC-OCR-009`, `TC-OCR-012`.
- **Manual verification:** `python main.py recognize --image "samples/sample_text.png" --psm 6` → `accepted` status + text; GUI tab matches; missing `--image` → friendly usage message.
- **Documentation updates:** `docs/CONFIGURATION.md` extended with the seven recognition keys and valid ranges.
- **Performance / isolation checks:** lazy imports verified — chatbot-only startup < 300ms with OCR deps installed but unused (`FR-250`); `tests/test_wave4_isolation.py` green; Weeks 1–3 matrices unaffected.
- **Exit criteria:** TC-OCR-009/012 pass; `recognize` appears in `help`.
- **One scoped commit:** `feat: W4-M5 - recognize CLI & GUI, config, logging (FR-251, FR-259-FR-260)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** before starting W4-M6.

---

### W4-M6 — Testing, Documentation & Final Wave 4 Sign-off

- **Scope:** Complete the TC-OCR-* suite, reach ≥ 90% coverage on `decodebot/recognition/` (NFR-094), run the privacy static scan, write `docs/OCR_GUIDE.md`, update README/CHANGELOG, and walk the Part IV Acceptance Criteria.
- **Files to create/modify:** remaining `tests/test_recognition*.py`, `docs/OCR_GUIDE.md`, modify `README.md`, `CHANGELOG.md`.
- **Implements (Requirements satisfied):** `FR-261`, `FR-262`; `NFR-091`–`NFR-095`, `NFR-097`.
- **Verifies (Tests required):** full `TC-OCR-001`–`012` suite; Part IV Acceptance Criteria (all boxes).
- **Manual verification:** full suite (Weeks 1–4) runs green; privacy scan clean; a reviewer can run the `recognize` demo from the README alone.
- **Documentation updates:** `docs/OCR_GUIDE.md`, README, CHANGELOG (`v3.1.0` entry).
- **Performance / isolation checks:** final isolation + startup re-verification; all compliance matrices (Weeks 1–3) still pass.
- **Exit criteria:** all TC-OCR-* pass; coverage ≥ 90%; privacy gate green; Part IV Acceptance Criteria checked; **Wave 4 milestone reached (v3.1.0, optional)**.
- **One scoped commit:** `docs: W4-M6 - OCR guide, README, CHANGELOG (Wave 4 complete)`
- **Mandatory stop:** After exit criteria are met, **stop and await user approval** — either to tag the v3.1.0 release or to conclude.

---

## Master File Creation Sequence (Flat, Dependency-Ordered)

> For an agent that prefers a single linear checklist instead of phase-by-phase framing, this is the same plan flattened into strict build order. Each item notes its phase in parentheses.

1. `.gitignore`, `LICENSE`, `pyproject.toml`, `requirements.txt`, `requirements-dev.txt` (P0)
2. `decodebot/__init__.py` (`__version__`) (P0)
3. `decodebot/core/__init__.py`, `decodebot/rules/__init__.py`, `decodebot/utils/__init__.py` (P0)
4. `decodebot/utils/normalization.py` (P1)
5. `decodebot/core/intents.py` (P1)
6. `decodebot/rules/greetings.py` (P1)
7. `decodebot/rules/exit.py` (P1)
8. `decodebot/rules/unknown.py` (P1, fuzzy suggestion stubbed)
9. `decodebot/core/rule_engine.py` — minimal, hardcoded imports (P1)
10. `decodebot/core/io_handler.py` (P1)
11. `decodebot/core/session.py` — minimal (P1)
12. `decodebot/core/dispatcher.py` (P1)
13. `decodebot/core/loop.py` — basic loop, exit-only termination (P1)
14. `decodebot/core/app.py` (P1)
15. `main.py` (P1)
16. `tests/test_compliance.py`, `test_greetings.py`, `test_exit.py`, `test_unknown.py`, `test_normalization.py`, `test_no_prohibited_imports.py` (P1)
17. **⛔ GATE: full Compliance Matrix must pass before continuing.**
18. `decodebot/rules/help_about_version.py` (P2)
19. `decodebot/core/responder.py` (P2)
20. `tests/test_help_about_version.py` (P2)
21. Expand `decodebot/core/session.py` to full `SessionState` (P3)
22. `decodebot/core/history.py` (P3)
23. `decodebot/core/stats.py` (P3)
24. `tests/test_session_history_stats.py` (P3)
25. `decodebot/rules/personalization.py` (P4)
26. `tests/test_personalization.py` (P4)
27. `decodebot/core/config.py`, `config.json`, `docs/CONFIGURATION.md` (P5)
28. `tests/test_config.py` (P5)
29. `decodebot/core/logger.py` (P6)
30. `tests/test_logging.py` (P6)
31. Harden `decodebot/core/loop.py` with full error handling + circuit breaker (P7)
32. `tests/test_error_handling.py` (P7)
33. `decodebot/rules/easter_eggs.py`, `docs/HIDDEN_COMMANDS.md` (P8)
34. `tests/test_easter_eggs.py` (P8)
35. Upgrade `decodebot/core/rule_engine.py` to full plugin discovery (P9)
36. `decodebot/plugins/README.md`, `docs/PLUGIN_GUIDE.md` (P9)
37. `tests/test_plugin_template.py`, `tests/test_rule_engine.py` (P9)
38. **⛔ GATE: re-run full Compliance Matrix — must still pass 100%.**
39. `decodebot/utils/terminal.py`, `decodebot/utils/levenshtein.py` (P10)
40. Finalize `decodebot/utils/formatting.py` (P10)
41. `tests/test_cli_formatting.py` (P10)
42. Fill remaining tests to reach 105+ total, ≥90% coverage (P11)
43. `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/ARCHITECTURE.md` (P12)
44. Final full-suite run + Acceptance Criteria + NFR benchmark verification (P13)
45. Tag `v1.0.0` release.
46. **⛔ MILESTONE: v1.0.0 core chatbot complete.**
47. `decodebot/core/animation.py` (P14)
48. `tests/test_animations.py` (P14)
49. `decodebot/gui/__init__.py`, `app_gui.py`, `widgets.py`, `animations.py`, `theme.py` (P15)
50. `docs/GUI_GUIDE.md`, `tests/test_gui.py` (P15)
51. **⛔ GATE: re-run Week 1 Compliance Matrix — must still pass 100%. Tag `v1.1.0` release.**
52. `decodebot/ml/__init__.py`, `dataset.py`, `dataset_loader.py`, `dataset_validator.py` (P16)
53. Update `requirements.txt` (ML section), `datasets/README.md`, `tests/test_dataset_loader.py`, `test_dataset_validator.py`, `test_ml_isolation.py` (P16)
54. `decodebot/ml/preprocessor.py`, `tests/test_preprocessor.py` (P17)
55. `decodebot/ml/trainer.py`, `tests/test_trainer.py` (P18)
56. `decodebot/ml/predictor.py`, `evaluator.py`, `tests/test_predictor.py`, `test_evaluator.py` (P19)
57. `decodebot/ml/model_manager.py`, `visualization.py`, `tests/test_model_manager.py`, `test_visualization.py` (P20)
58. `decodebot/ml/app_ml.py`, dispatcher/config/logger wiring, GUI ML panel (if built), `docs/CONFIGURATION.md` update (P21)
59. **⛔ GATE: re-run Week 1 Compliance Matrix AND `tests/test_ml_isolation.py` — both must pass 100%.**
60. Fill remaining ML tests to reach 80+ total, ≥90% coverage on `decodebot/ml/` (P22)
61. `docs/ML_GUIDE.md`, README/CHANGELOG updates (P23)
62. Final full-suite run (Week 1 + Week 2) + both Acceptance Criteria checklists + all NFR benchmarks (P24)
63. Tag `v2.0.0` release.
64. `decodebot/recommender/__init__.py`, `corpus.py`, `tests/test_wave3_isolation.py`, `test_recommender_corpus.py` (W3-M1)
65. `decodebot/recommender/normalization.py`, `features.py`, `tests/test_recommender_features.py` (W3-M2)
66. `decodebot/recommender/ranker.py`, `fallbacks.py`, `result.py`, `tests/test_recommender_ranker.py` (W3-M3)
67. `decodebot/recommender/app_recommender.py`, COMMANDS/dispatcher/config wiring, `docs/CONFIGURATION.md` update, `tests/test_recommender_cli.py` (W3-M4)
68. **⛔ GATE: `tests/test_wave3_isolation.py` + `tests/test_ml_isolation.py` + startup check; re-run Week 1 & Week 2 Compliance Matrices — all must still pass.**
69. `decodebot/gui/recommender_panel.py`, `gui/app_gui.py` update, `tests/test_gui_recommender.py` (W3-M5)
70. Remaining `tests/test_recommender*.py` → full TC-REC suite, ≥90% coverage on `decodebot/recommender/` (W3-M6)
71. `docs/RECOMMENDER_GUIDE.md`, README/CHANGELOG updates, Part III Acceptance Criteria walk (W3-M7)
72. **⛔ MILESTONE: Wave 3 complete. Tag `v3.0.0` release (await approval). Wave 4 is OPTIONAL.**
73. `decodebot/recognition/__init__.py`, `ingestor.py`, `result.py`, `tests/test_wave4_isolation.py`, `test_recognition_ingestion.py`, `samples/`, `requirements-ocr.txt` (W4-M1)
74. `decodebot/recognition/preprocess.py`, `tests/test_recognition_preprocess.py` (W4-M2)
75. `decodebot/recognition/ocr_engine.py`, `tests/test_recognition_ocr.py` (W4-M3)
76. `decodebot/recognition/filter.py`, `tests/test_recognition_filter.py`, `test_recognition_output.py` (W4-M4)
77. `decodebot/recognition/app_recognition.py`, COMMANDS/dispatcher/config wiring, `gui/recognition_panel.py`, `gui/app_gui.py` update, `docs/CONFIGURATION.md` update, `tests/test_recognition_cli.py`, `test_gui_recognition.py` (W4-M5)
78. **⛔ GATE: `tests/test_wave4_isolation.py` + privacy static scan + startup check; re-run Weeks 1–3 Compliance Matrices — all must still pass.**
79. Remaining `tests/test_recognition*.py` → full TC-OCR suite, ≥90% coverage on `decodebot/recognition/` (W4-M6)
80. `docs/OCR_GUIDE.md`, README/CHANGELOG updates, Part IV Acceptance Criteria walk (W4-M6)
81. **⛔ MILESTONE: Wave 4 complete (optional). Tag `v3.1.0` release (await approval).**

---

## Continuous Verification Checklist (Runs After *Every* Phase, Not Just Once)

### Applies to every phase (0–24)
- [ ] `python main.py` still launches without error.
- [ ] All 8 Week 1 Compliance Matrix rows still pass.
- [ ] `tests/test_no_prohibited_imports.py` still passes.
- [ ] No new console output contains a raw traceback or exception class name.
- [ ] No new file exceeds ~400 lines (`NFR-012`).
- [ ] No new function exceeds a cyclomatic complexity of 10 (`NFR-014`).
- [ ] All new public functions/classes have type hints and docstrings.

### Additional checks starting Phase 14 (GUI/Animation)
- [ ] GUI module presence never affects default (non-`--gui`) CLI behavior.
- [ ] No animation effect can block `Ctrl+C` responsiveness beyond 100ms.

### Additional checks starting Phase 16 (Machine Learning Engine)
- [ ] `tests/test_ml_isolation.py` still passes — zero `sklearn`/`pandas`/`numpy`/`matplotlib`/`joblib` imports outside `decodebot/ml/`.
- [ ] All 8 Week 2 Compliance Matrix rows still pass (once Phase 21 is reached and onward).
- [ ] Chatbot-only startup time (`python main.py`, no ML command invoked) remains under 300ms even with ML dependencies installed.
- [ ] No chat-text input is ever passed into a `scikit-learn` model's `predict()` method (`FR-223`).

### Additional checks starting Wave 3 (Recommender Engine)
- [ ] `tests/test_wave3_isolation.py` still passes — zero `decodebot.recommender` imports in `decodebot/core/`, `decodebot/rules/`, `decodebot/gui/`, and no eager ML-library import at chatbot startup.
- [ ] `recommend` produces identical ranked output across repeated runs (`NFR-087`).
- [ ] Chatbot-only startup time remains < 300ms with recommender dependencies installed but unused (`NFR-090`).
- [ ] No new recommender file exceeds ~400 lines (`NFR-012`); no function exceeds cyclomatic complexity 10 (`NFR-014`).

### Additional checks starting Wave 4 (Recognition Engine)
- [ ] `tests/test_wave4_isolation.py` still passes — zero `cv2`/`pytesseract`/`decodebot.recognition` imports outside the allowed scope.
- [ ] OCR runs entirely locally — zero network sockets opened (`NFR-092`).
- [ ] Chatbot-only startup time remains < 300ms with OCR dependencies installed but unused (`FR-250`).
- [ ] Saved recognition output never overwrites an existing file unless `rec_overwrite=true`.
- [ ] No new recognition file exceeds ~400 lines (`NFR-012`); no function exceeds cyclomatic complexity 10 (`NFR-014`).

---

## Traceability Appendix — Phase → Requirement → Test Quick Reference

| Phase | FR Range | Related NFRs | Test ID Ranges |
|---|---|---|---|
| 0 | — | NFR-016, NFR-052 | — |
| 1 | FR-001–FR-053 | NFR-001–005, NFR-020–023 | TC-CORE-001–008, TC-GREET-001–010, TC-EXIT-001–010, TC-UNK-001–008, TC-U-001–020 |
| 2 | FR-054–FR-063 | NFR-048–049 | TC-I-003 |
| 3 | FR-064–FR-079 | NFR-004, NFR-019 | TC-U-022–023, TC-I-004–005, TC-I-014, TC-E-011–015 |
| 4 | FR-080–FR-087 | — | TC-U-024–025, TC-U-029–030, TC-I-002 |
| 5 | FR-088–FR-095 | NFR-021 | TC-U-026–028, TC-N-001, TC-I-006, TC-I-009–010 |
| 6 | FR-096–FR-103 | NFR-038–039 | TC-I-011–013 |
| 7 | FR-104–FR-111 | NFR-020, NFR-023 | TC-ERR-001–010, TC-N-006, TC-A-008 |
| 8 | FR-112–FR-117 | — | TC-M-005 |
| 9 | FR-118–FR-125 | NFR-017–018, NFR-050–051 | TC-I-007–008, TC-N-010, TC-R-002, TC-R-006 |
| 10 | FR-126–FR-133, FR-048–049 | NFR-027–029 | TC-A-011, TC-U-014–017, TC-M-002 |
| 11 | — (all) | NFR-034, NFR-036–037 | Full 105+ test suite |
| 12 | — | NFR-030–033 | TC-A-004, TC-A-013 |
| 13 | — (all) | All benchmarked NFRs | TC-A-001–015 |
| 14 | FR-134–FR-143 | NFR-055–056 | TC-ANIM-001–008 |
| 15 | FR-144–FR-163 | NFR-057–065 | TC-GUI-001–012 |
| 16 | FR-164–FR-172 | NFR-072 | TC-ML-001–010 |
| 17 | FR-173–FR-186 | NFR-082 | TC-ML-011–028 |
| 18 | FR-187–FR-195 | NFR-066, NFR-069, NFR-081 | TC-ML-029–038 |
| 19 | FR-196–FR-209 | NFR-067, NFR-080 | TC-ML-039–058 |
| 20 | FR-210–FR-221 | NFR-071, NFR-085, NFR-084 | TC-ML-059–070+ |
| 21 | FR-222–FR-232 | NFR-072–075, NFR-083 | Full ML compliance gate (8/8) |
| 22 | — (all Part II) | NFR-076–077 | 80+ ML test suite |
| 23 | — | NFR-079 | Week 2 GitHub Standards checklist |
| 24 | — (all Part II) | All Part II NFRs | Week 2 Acceptance Criteria (all boxes) |
| W3-M1 | FR-233, FR-236–238 | NFR-088 | TC-REC-001–003 |
| W3-M2 | FR-239–241 | NFR-086 | TC-REC-004–005 |
| W3-M3 | FR-242–244 | NFR-086, NFR-087 | TC-REC-006–009 |
| W3-M4 | FR-235, FR-239, FR-245, FR-247 | NFR-090 | TC-REC-010–012 |
| W3-M5 | FR-246 | NFR-088 | TC-REC-010 (GUI parity) |
| W3-M6 | FR-248 | NFR-089 | Full TC-REC suite |
| W3-M7 | All Wave 3 | NFR-096 | Part III Acceptance Criteria (all boxes) |
| W4-M1 | FR-249, FR-252 | NFR-091, NFR-093 | TC-OCR-001–002 |
| W4-M2 | FR-253 | NFR-093 | TC-OCR-003–004 |
| W4-M3 | FR-254–255 | NFR-095 | TC-OCR-005, TC-OCR-010 |
| W4-M4 | FR-256–258 | — | TC-OCR-006–008 |
| W4-M5 | FR-251, FR-259–260 | NFR-092, NFR-097 | TC-OCR-009, TC-OCR-012 |
| W4-M6 | FR-261–262 | NFR-091–095, NFR-097 | Full TC-OCR suite; Part IV Acceptance Criteria (all boxes) |

---

## Version History of This Plan

| Version | Phases | Description |
|---|---|---|
| v1.0.0 | 0–13 | Initial Week 1 rule-based Chatbot Engine implementation plan |
| v1.1.0 | 14–15 | Added Terminal Animation Layer and Optional Tkinter GUI Layer |
| v2.0.0 | 16–24 | Added Machine Learning Data Classification Engine (Week 2), fully isolated in `decodebot/ml/`. Phases 0–15 unchanged and fully preserved. |
| **v3.0.0** | **W3-M1–W3-M7 (+ Phases 0–24 preserved)** | **Added Content-Based Tech Stack Recommendation Engine (Week 3, PLANNED) in isolated `decodebot/recommender/`, plus the optional OCR Image/Text Recognition Engine (Week 4, PLANNED and OPTIONAL-EXTENSION) in isolated `decodebot/recognition/`. Phases 0–24 unchanged and fully preserved.** |

---

*End of PLAN.md. This document must be re-validated against `SPEC.md` after any future specification change — if `SPEC.md` is revised, re-derive the affected phase(s) of this plan before resuming implementation. Phases 0–15 represent completed, preserved work; Phases 16–24 represent the Week 2 Machine Learning Engine build sequence; Wave 3 (W3-M1–W3-M7) and Wave 4 (W4-M1–W4-M6, optional) represent the planned Week 3 and Week 4 build sequences.*
