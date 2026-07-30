# PLAN.md — DecodeBot AI Implementation Plan

> **Companion document to SPEC.md.** This file translates the specification into a strict, ordered, dependency-safe build sequence for an AI coding agent (OpenCode) to execute. It introduces **zero new requirements** — every task below cites the exact FR/NFR/Test ID it implements or verifies in SPEC.md. If any instruction here appears to conflict with SPEC.md, **SPEC.md is authoritative** and this plan must be corrected to match it, never the reverse.

---

## How To Use This Plan

1. Read SPEC.md in full before starting. Do not implement from memory of this plan alone.
2. Execute phases **in order** (Phase 0 ? Phase 15). Each phase has hard dependencies on the one before it — do not skip ahead.
3. After finishing each phase, run its listed test IDs before moving to the next phase. A phase is not "done" until its Definition of Done checklist is fully checked.
4. **Phase 1 (Core Compliance MVP) is the single most important phase.** It alone must satisfy 100% of the DecodeLabs Internship Compliance Matrix in SPEC.md. Every later phase must be implemented such that it **never** weakens or overrides Phase 1 behavior (see FR-121 — core rules are protected).
5. Never introduce a machine learning, deep learning, NLP, or LLM library at any phase, for any reason (FR-009, NFR-016, CON-01). If a task seems to require one, stop and re-read the relevant SPEC.md requirement — the rule-based solution is always achievable with the Python standard library.
6. Commit after each phase with a message referencing the phase name and FR range covered (e.g., eat: Phase 3 - session state, history, statistics (FR-064–FR-079)).

---

## Non-Negotiable Guardrails (Recap)

These apply across **every** phase, without exception:

- ? No spacy, 
ltk, 	ransformers, 	orch, 	ensorflow, langchain, asa, or any OpenAI/Gemini/LLM API client, ever (FR-009).
- ? No network sockets opened by default (NFR-008).
- ? No eval()/exec()/os.system() with user-controlled string content (NFR-006, NFR-007).
- ? No silent except: pass — every catch logs (Coding Standards ? Error Handling).
- ? No feature may cause the loop to crash or hang on any input (FR-050, NFR-020).
- ? Every module uses type hints and docstrings (Coding Standards).
- ? Every new intent/rule is traceable to an FR ID via an inline comment.
- ? Only Python standard library at runtime; pytest is dev/test-only (CON-03, NFR-016).

---

## Definition of Ready (Before Phase 0)

- [ ] SPEC.md has been read in full.
- [ ] Python 3.9+ is available in the build environment.
- [ ] pytest is installed as a dev dependency only.
- [ ] Git repository is initialized.

---

## Build Order Overview

| Phase | Name | FR Range | Key New Files | Gate to Proceed |
|---|---|---|---|---|
| 0 | Repository Bootstrap | — (NFR-052) | Skeleton, configs, license | Structure matches SPEC.md Folder Structure |
| 1 | **Core Compliance MVP** | FR-001–FR-053 | main.py, core/* (minimal), utils/normalization.py, ules/greetings.py, ules/exit.py, ules/unknown.py | 100% of Compliance Matrix passes |
| 2 | Command Layer | FR-054–FR-063 | ules/help_about_version.py, core/responder.py | help/bout/ersion fully functional |
| 3 | Session, History & Statistics | FR-064–FR-079 | core/history.py, core/stats.py | history/stats commands correct |
| 4 | Personalization | FR-080–FR-087 | ules/personalization.py | Name capture/interpolation verified |
| 5 | Configuration System | FR-088–FR-095 | core/config.py, config.json, docs/CONFIGURATION.md | Malformed config never crashes app |
| 6 | Logging, Debug & Dev Mode | FR-096–FR-103 | core/logger.py | Rotating logs verified; no sensitive data |
| 7 | Error Handling & Resilience | FR-104–FR-111 | Loop-level try/except + circuit breaker | Fuzz test: 0 crashes across 1,000 inputs |
| 8 | Hidden Commands & Easter Eggs | FR-112–FR-117 | ules/easter_eggs.py, docs/HIDDEN_COMMANDS.md | Hidden commands work, absent from help |
| 9 | Plugin/Extensible Rule Engine | FR-118–FR-125 | core/rule_engine.py (full), plugins/README.md, docs/PLUGIN_GUIDE.md | New plugin loads without core changes |
| 10 | CLI Polish & Accessibility | FR-126–FR-133, FR-049 | utils/terminal.py, utils/levenshtein.py, utils/formatting.py (final) | All CLI Specification screens match exactly |
| 11 | Full Test Suite Completion | — (Testing Specification) | Remaining files in 	ests/ | 105+ tests pass, =90% coverage on core//ules/ |
| 12 | Documentation & GitHub Packaging | — (GitHub Standards) | README.md, CONTRIBUTING.md, CHANGELOG.md, docs/ARCHITECTURE.md | GitHub Standards checklist complete |
| 13 | Final Compliance & Acceptance Sign-off | All | — | Every box in Acceptance Criteria checked |
| 14 | Terminal Animation Layer | FR-134–FR-143 | core/animation.py, 	ests/test_animations.py | All TC-ANIM-* pass; Ctrl+C still responsive during animation |
| 15 | Optional Tkinter GUI Layer | FR-144–FR-163 | gui/*.py, 	ests/test_gui.py, docs/GUI_GUIDE.md | All TC-GUI-* pass; Compliance Matrix still 100% via default CLI launch |


## Phase 0 — Repository Bootstrap

**Goal:** Establish the exact repository skeleton defined in SPEC.md ? Folder Structure, with zero functional code yet.

**Files to create:**
`
decodebot-ai/
+-- main.py                 (empty stub with TODO, no logic yet)
+-- decodebot/__init__.py   (define __version__ = "0.1.0")
+-- decodebot/core/__init__.py
+-- decodebot/rules/__init__.py
+-- decodebot/plugins/README.md
+-- decodebot/utils/__init__.py
+-- tests/__init__.py
+-- docs/ (empty, populated in later phases)
+-- logs/.gitkeep
+-- requirements.txt        (empty — no runtime deps)
+-- requirements-dev.txt     (pytest)
+-- pyproject.toml           (black/ruff config, line-length=100)
+-- .gitignore               (logs/, __pycache__/, .pytest_cache/, *.pyc)
+-- README.md                (placeholder, filled in Phase 12)
+-- CONTRIBUTING.md          (placeholder, filled in Phase 12)
+-- CHANGELOG.md             (Unreleased section only)
+-- LICENSE                  (MIT, full text)
`

**Implements:** Groundwork for NFR-052 (one-command setup), NFR-016 (dependency minimalism).

**Definition of Done:**
- [ ] Folder tree matches SPEC.md ? Folder Structure exactly.
- [ ] pip install -r requirements-dev.txt && pytest runs (even with zero tests) without error.
- [ ] equirements.txt contains no packages.
- [ ] LICENSE file is the full MIT license text.

---

## Phase 1 — Core Compliance MVP (Highest Priority)

**Goal:** Implement the smallest possible working chatbot that satisfies **100% of the DecodeLabs Internship Compliance Matrix** in SPEC.md. This phase is the actual internship deliverable; everything after it is enhancement layered on top without ever weakening this behavior.

**Preconditions:** Phase 0 complete.

**Files to create:**
- decodebot/core/intents.py — Intent enum: at minimum GREETING, EXIT, HELP, ABOUT, VERSION, UNKNOWN, EMPTY_INPUT, NUMERIC_INPUT, SYMBOLS_ONLY.
- decodebot/utils/normalization.py — implements the **Input Normalization Algorithm** from SPEC.md ? Algorithms (FR-013–FR-024).
- decodebot/rules/greetings.py — GREETING_PATTERNS, GREETING_RESPONSES (FR-026–FR-029, FR-033).
- decodebot/rules/exit.py — EXIT_PATTERNS, EXIT_RESPONSES, negation exclusion list (FR-036–FR-039, FR-042, FR-044).
- decodebot/rules/unknown.py — fallback response pool (FR-046–FR-047); fuzzy suggestion (FR-049) may be stubbed here and completed in Phase 10.
- decodebot/core/rule_engine.py (minimal version) — implements the **Intent Matching Algorithm**; hardcoded imports of the three rule modules above only (full plugin discovery deferred to Phase 9).
- decodebot/core/dispatcher.py — the explicit if/elif/else chain required by FR-006 and the internship rubric, routing GREETING / EXIT / HELP (stub) / UNKNOWN / default else.
- decodebot/core/io_handler.py — injectable get_input() / print_response() wrappers (FR-011, FR-012, FR-022).
- decodebot/core/session.py (minimal) — bare SessionState dataclass holding only history: list for now (expanded in Phase 3).
- decodebot/core/loop.py — implements the **Conversation Loop Algorithm** while True structure (FR-004, FR-005), calling into the dispatcher; exit on Intent.EXIT only for now (interrupt/EOF handling wired here but deepened in Phase 7).
- decodebot/core/app.py — un() bootstrap function called by main.py.
- main.py — final: if __name__ == "__main__": app.run() (FR-001, FR-002).
- 	ests/test_compliance.py — the 8 mandatory checks (TC-CORE-001– 08).
- 	ests/test_greetings.py, 	ests/test_exit.py, 	ests/test_unknown.py — TC-GREET-001– 10, TC-EXIT-001– 10, TC-UNK-001– 08.
- 	ests/test_normalization.py — covers TC-U-001– 09.
- 	ests/test_no_prohibited_imports.py — static scan gate (FR-009, TC-A-002).

**Implements:** FR-001–FR-053 (Categories A, B, C, D, E in full).

**Verifies:** All rows of the **DecodeLabs Internship Compliance Matrix**, plus TC-CORE-001– 08, TC-GREET-001– 10, TC-EXIT-001– 10, TC-UNK-001– 08, TC-U-001– 20.

**Definition of Done:**
- [ ] python main.py runs, accepts input, loops on a while statement, uses explicit if/elif/else.
- [ ] All 8 Compliance Matrix rows pass their mapped tests.
- [ ] 	ests/test_no_prohibited_imports.py passes (zero prohibited imports anywhere in the tree).
- [ ] Program never crashes on empty, numeric, symbol-only, or gibberish input.
- [ ] Word-boundary safety verified ("history" ? greeting; "quitter" ? exit).
- [ ] **Stop and fully verify this phase before proceeding — it is the graded deliverable.**


## Phase 2 — Command Layer (Help / About / Version)

**Preconditions:** Phase 1 complete and verified.

**Files to create/modify:**
- decodebot/rules/help_about_version.py — COMMANDS registry single source of truth (FR-058), aliases (FR-059).
- decodebot/core/responder.py — response selection logic factored out of the dispatcher (get_response() from the **Response Selection Algorithm**).
- Modify decodebot/core/dispatcher.py to route HELP, ABOUT, VERSION through the new COMMANDS registry.
- 	ests/test_help_about_version.py — covers TC-I-003.

**Implements:** FR-054–FR-063.

**Definition of Done:**
- [ ] help output is generated dynamically from COMMANDS, not hardcoded text.
- [ ] ersion output matches decodebot.__version__ exactly (single source of truth, FR-056).
- [ ] All documented aliases (?, info, , --version) route identically to their canonical command.

---

## Phase 3 — Session State, History & Statistics

**Preconditions:** Phase 2 complete.

**Files to create/modify:**
- Expand decodebot/core/session.py to the full SessionState dataclass (FR-064): turn-numbered history, intent counts, timestamps, flags.
- decodebot/core/history.py — bounded FIFO buffer (FR-025, FR-067), history command rendering incl. pagination (FR-068).
- decodebot/core/stats.py — message count, per-intent frequency, duration (monotonic clock), longest/shortest message, avg. response time (FR-072–FR-079).
- Add history, stats, eset entries to the COMMANDS registry from Phase 2.
- 	ests/test_session_history_stats.py — covers TC-U-022, TC-U-023, TC-I-004, TC-I-005, TC-E-011– 15.

**Implements:** FR-064–FR-079 (also FR-061–FR-063 command wiring).

**Definition of Done:**
- [ ] History buffer evicts oldest entry at exactly 100 entries (FR-067).
- [ ] stats and history both correctly report "empty/zero" states gracefully (TC-E-012, TC-E-013).
- [ ] eset clears history and stats counters to their initial state (FR-063, FR-077).
- [ ] Session duration uses 	ime.monotonic(), not wall-clock time.

---

## Phase 4 — Personalization

**Preconditions:** Phase 3 complete.

**Files to create/modify:**
- decodebot/rules/personalization.py — name extraction patterns (FR-032), set name/call me command (FR-081), orget my name (FR-085), sanitization (FR-080, FR-086).
- Modify decodebot/core/responder.py — interpolate_personalization() (FR-082), ensuring no literal "{name}"/"None" leaks when unset (FR-082 edge case).
- Modify decodebot/rules/greetings.py response pool to include name-aware variants.
- 	ests/test_personalization.py — covers TC-U-024, TC-U-025, TC-U-029, TC-U-030, TC-I-002.

**Implements:** FR-080–FR-087.

**Definition of Done:**
- [ ] "my name is Sara" sets the name and future greetings can include it.
- [ ] Invalid-character-only names are rejected with a clarifying prompt (FR-086, TC-E-014).
- [ ] eset and orget my name both correctly clear the stored name (FR-084, FR-085).

---

## Phase 5 — Configuration System

**Preconditions:** Phase 4 complete.

**Files to create/modify:**
- decodebot/core/config.py — loader with per-key validation and default fallback (FR-088, FR-094); supports ot_name, enable_colors, debug_mode, developer_mode, log_dir, plain_mode, feature flags (enable_time_aware_greeting, emoji-greeting toggle).
- config.json — shipped example with documented default values.
- docs/CONFIGURATION.md — every key documented (FR-095).
- decodebot/rules/help_about_version.py ? add settings command wiring (FR-093), session-scoped toggle only (not persisted unless explicitly saved).
- 	ests/test_config.py — covers TC-U-026, TC-U-027, TC-U-028, TC-N-001, TC-I-006, TC-I-009, TC-I-010.

**Implements:** FR-088–FR-095.

**Definition of Done:**
- [ ] Deleting config.json still allows a normal run using built-in defaults.
- [ ] Malformed JSON is caught, logged as WARNING, defaults used — app never crashes on bad config.
- [ ] A single bad key does not invalidate the rest of a valid config file.
- [ ] Every config key appears in docs/CONFIGURATION.md.


## Phase 6 — Logging, Debug & Developer Mode

**Preconditions:** Phase 5 complete (depends on config for level/toggles).

**Files to create/modify:**
- decodebot/core/logger.py — rotating file handler (FR-096, FR-098), configurable level (FR-097), console/file separation (FR-100).
- Modify decodebot/core/dispatcher.py/esponder.py — add [DEBUG] console diagnostics when debug_mode is on (FR-091).
- Modify decodebot/core/dispatcher.py — add hidden dumpstate / listplugins commands gated by developer_mode (FR-092, FR-102, FR-125 — listplugins fully wired in Phase 9).
- 	ests/test_logging.py — covers TC-I-011, TC-I-012, TC-I-013.

**Implements:** FR-096–FR-103.

**Definition of Done:**
- [ ] logs/decodebot.log contains startup and shutdown entries after any session.
- [ ] No sensitive data ever appears in logs (there is none by design — verify no accidental logging of full config dumps containing anything beyond documented, non-sensitive keys).
- [ ] Log rotation triggers at 1MB with 3 backups retained.
- [ ] debug_mode affects console only; log file verbosity is controlled independently.

---

## Phase 7 — Error Handling & Resilience

**Preconditions:** Phase 6 complete.

**Files to modify:**
- decodebot/core/loop.py — wrap the full iteration body per the **Error Recovery Algorithm**: KeyboardInterrupt (FR-104), EOFError (FR-105), generic exception safety net (FR-106), consecutive-error circuit breaker (FR-107).
- decodebot/core/config.py — ensure config load failures cannot crash startup (FR-108, already partially covered in Phase 5 — confirm here).
- decodebot/core/rule_engine.py — isolate individual rule/plugin load failures (FR-109) — full effect realized in Phase 9, stub the isolation mechanism now.
- decodebot/core/io_handler.py — catch broken-pipe/output failures gracefully (FR-110).
- Audit all user-facing strings for tone consistency, no raw tracebacks exposed (FR-111).
- 	ests/test_error_handling.py — covers TC-ERR-001– 10, TC-N-006, TC-A-008 (1,000-iteration fuzz harness).

**Implements:** FR-104–FR-111.

**Definition of Done:**
- [ ] Ctrl+C and Ctrl+D both exit cleanly with code   and a graceful message.
- [ ] A forced exception mid-session is caught, logged with traceback, and the session continues.
- [ ] 5 consecutive forced exceptions trip the circuit breaker and exit with code 1.
- [ ] 1,000-iteration fuzz test produces zero unhandled exceptions.
- [ ] No console string contains "Traceback" or a raw Python exception class name.

---

## Phase 8 — Hidden Commands & Easter Eggs

**Preconditions:** Phase 7 complete.

**Files to create:**
- decodebot/rules/easter_eggs.py — joke pool (FR-113), self-awareness gag (FR-114), hidden phrase trigger (FR-115), registered in a separate hidden-command registry (FR-112) not exposed via help.
- docs/HIDDEN_COMMANDS.md — full internal documentation of every hidden command (FR-117).
- Modify decodebot/core/stats.py — aggregate easter-egg hits under a single Intent.EASTER_EGG counter if FR-116 is implemented.
- 	ests/test_easter_eggs.py — covers TC-M-005.

**Implements:** FR-112–FR-117.

**Definition of Done:**
- [ ] None of the hidden commands appear in help output.
- [ ] Every hidden command is documented in docs/HIDDEN_COMMANDS.md.
- [ ] Hidden commands do not collide with any public command or alias.

---

## Phase 9 — Plugin / Extensible Rule Engine

**Preconditions:** Phase 8 complete. This phase upgrades core/rule_engine.py from Phase 1's hardcoded imports to full auto-discovery — **without changing any Phase 1 core behavior**.

**Files to create/modify:**
- decodebot/core/rule_engine.py — full plugin discovery from decodebot/rules/ and decodebot/plugins/ (FR-118); enforce the plugin interface contract (PATTERNS, INTENT, RESPONSES, priority) (FR-119); priority/conflict resolution (FR-120); protect the 8 mandatory core intents from override (FR-121 — critical, re-verify Compliance Matrix still passes after this change); new-intent registration API egister_intent() (FR-122); documented sandbox constraints (FR-123).
- decodebot/plugins/README.md and docs/PLUGIN_GUIDE.md — contributor-facing documentation (FR-123).
- 	ests/test_plugin_template.py — example plugin + isolated unit test template (FR-124).
- Complete listplugins developer command from Phase 6 (FR-125).
- 	ests/test_rule_engine.py — covers TC-I-007, TC-I-008, TC-N-010, TC-R-002, TC-R-006.

**Implements:** FR-118–FR-125.

**Definition of Done:**
- [ ] **Re-run the full Compliance Matrix test suite from Phase 1 — it must still pass 100%** after this refactor.
- [ ] A new, valid plugin file dropped into plugins/ is auto-discovered with zero core code changes.
- [ ] A deliberately broken plugin file is isolated (logged, skipped) without affecting core functionality.
- [ ] A plugin attempting to override EXIT patterns to empty does not disable real exit behavior.
- [ ] Duplicate intent registration fails fast with a clear startup error.


## Phase 10 — CLI Polish & Accessibility

**Preconditions:** Phase 9 complete.

**Files to create/modify:**
- decodebot/utils/terminal.py — cross-platform clear-screen (FR-060), terminal width detection with 80-column fallback (FR-131).
- decodebot/utils/levenshtein.py — pure-Python edit distance (FR-049's **Fuzzy Command Suggestion Algorithm**); wire into decodebot/rules/unknown.py (FR-048, FR-049).
- decodebot/utils/formatting.py (finalized) — banner (FR-126), consistent prefixes (FR-127), blank-line spacing (FR-128), ANSI colors with auto-fallback (FR-090, FR-129), exit-screen framing (FR-130), echo suppression (FR-132), --plain mode (FR-133).
- Modify main.py/core/app.py — add --plain CLI flag parsing (stdlib rgparse only).
- 	ests/test_cli_formatting.py — covers TC-A-011, TC-U-014– 17, TC-M-002.

**Implements:** FR-126–FR-133, FR-048, FR-049.

**Definition of Done:**
- [ ] Every screen (Welcome, Help, About, Stats, Settings, Exit) visually matches SPEC.md ? CLI Specification exactly.
- [ ] --plain mode produces zero ANSI codes and zero box-drawing characters.
- [ ] Fuzzy suggestion correctly proposes "help" for "hepl"/"halp" and returns no suggestion for inputs with edit distance > 2.
- [ ] Escalating fallback triggers after exactly 3 consecutive UNKNOWN classifications.

---

## Phase 11 — Full Test Suite Completion

**Preconditions:** Phases 0–10 complete. Every feature exists; this phase closes remaining test gaps and confirms totals.

**Tasks:**
- Fill any remaining test files from SPEC.md ? Testing Specification not yet fully covered by earlier phases: Regression (TC-R-001– 10), Manual/Exploratory checklist (TC-M-001– 10, executed manually and logged), Acceptance (TC-A-001– 15), remaining Negative (TC-N-002– 05,  07– 09) and Edge Case tests (TC-E-001– 10).
- Run full coverage report; add tests until core/ and ules/ reach =90% line coverage (NFR-034).
- Confirm total test count = 105 and full suite runtime < 30 seconds (NFR-036).
- Confirm zero flaky tests across 10 consecutive runs (NFR-037).

**Definition of Done:**
- [ ] All 105+ test cases listed in SPEC.md exist and pass.
- [ ] 	ests/test_compliance.py still passes (final regression check).
- [ ] Coverage report confirms =90% on core/ and ules/.
- [ ] CI matrix passes on Python 3.9–3.13 (FR-003, NFR-026).

---

## Phase 12 — Documentation & GitHub Packaging

**Preconditions:** Phase 11 complete.

**Files to finalize:**
- README.md — full 11-section structure from SPEC.md ? GitHub Standards.
- CONTRIBUTING.md, CHANGELOG.md (v1.0.0 entry), LICENSE (confirm final).
- docs/ARCHITECTURE.md — expand on SPEC.md ? Architecture diagrams for contributor onboarding.
- Badges (Python version, license, build status, coverage, "100% Rule-Based").
- Terminal recording/screenshot of a live session (greeting ? help ? stats ? exit).

**Definition of Done:**
- [ ] Every GitHub Standards checklist item in SPEC.md is satisfied.
- [ ] A reviewer can go from git clone to a working demo in under 5 minutes using only the README (TC-A-004).
- [ ] docs/ contains all four required documents, each cross-linked from the README.

---

## Phase 13 — Final Compliance & Acceptance Sign-off

**Preconditions:** Phases 0–12 complete.

**Tasks:**
- Re-run the **entire** Compliance Matrix from SPEC.md end-to-end one final time.
- Walk the **entire** Acceptance Criteria checklist from SPEC.md and check every box.
- Verify NFR benchmarks: startup time (NFR-003), idle memory (NFR-043), idle CPU (NFR-045), response latency (NFR-001, NFR-002, NFR-047).
- Confirm __version__ matches the latest CHANGELOG.md entry and the Git release tag (NFR-048, NFR-049).
- Confirm zero prohibited imports one final time (	ests/test_no_prohibited_imports.py).

**Definition of Done (Release Gate):**
- [ ] Every row of the Compliance Matrix: ?
- [ ] Every box of the Acceptance Criteria section: ?
- [ ] All NFR benchmarks met.
- [ ] Tagged Git release 1.0.0 created matching __version__ and CHANGELOG.md.
- [ ] **DecodeBot AI v1.0.0 is ready to submit and to publish.**


## Phase 14 — Terminal Animation Layer

**Preconditions:** Phase 13 complete (v1.0.0 core is done and compliant). This phase and Phase 15 constitute the v1.1 release.

**Files to create:**
- decodebot/core/animation.py — typewriter printing (FR-134), thinking indicator (FR-135), animated banner (FR-136), animated clear transition (FR-137), injectable clock for testability (FR-143).
- Modify decodebot/core/config.py — add enable_animations, educed_motion, 	yping_speed_cps, 	hinking_frame_ms keys (FR-138, FR-140).
- Modify decodebot/core/loop.py — ensure animation calls respect the 100ms interrupt-responsiveness budget (FR-141) and never write frame-by-frame output to logs (FR-142).
- Modify decodebot/utils/terminal.py — TTY detection for auto-disable (FR-139).
- 	ests/test_animations.py — TC-ANIM-001– 08.

**Implements:** FR-134–FR-143.

**Definition of Done:**
- [ ] All animation effects are toggleable via enable_animations and auto-disable on non-TTY output.
- [ ] Ctrl+C remains responsive within 100ms during any animation.
- [ ] educed_motion shows static equivalents, not just "off".
- [ ] **Re-run the full Compliance Matrix — it must still pass 100%** (animations must never alter classification or block input).
- [ ] Log file contains one entry per response, never per animation frame.

---

## Phase 15 — Optional Tkinter GUI Layer

**Preconditions:** Phase 14 complete.

**Files to create:**
- decodebot/gui/__init__.py
- decodebot/gui/app_gui.py — window bootstrap, --gui flag handling, headless fallback (FR-144, FR-160).
- decodebot/gui/widgets.py — chat bubble, entry field, send button (FR-146–FR-148).
- decodebot/gui/animations.py — typing indicator, fade-in, using Tkinter.after() only (FR-149, FR-150).
- decodebot/gui/theme.py — shared color palette with CLI (FR-151, FR-152).
- docs/GUI_GUIDE.md — layout, theming, accessibility documentation (NFR-065).
- 	ests/test_gui.py — TC-GUI-001– 12.
- Modify decodebot/core/dispatcher.py/ule_engine.py — confirm zero changes needed; if any GUI-specific branching creeps in here, refactor it out immediately (FR-145 is non-negotiable).
- Modify 	ests/test_no_prohibited_imports.py — extend the scan to reject non-stdlib GUI imports (FR-163).

**Implements:** FR-144–FR-163.

**Definition of Done:**
- [ ] python main.py --gui launches a working window; python main.py (no flag) is completely unaffected.
- [ ] GUI calls the identical classify_intent()/get_response() functions as the CLI — zero duplicated rule logic (FR-145, verified by TC-GUI-003).
- [ ] All CLI commands work identically inside the GUI (FR-153).
- [ ] Headless environments fall back to CLI with a logged warning instead of crashing (FR-160).
- [ ] **Re-run the full Compliance Matrix one final time — it must still pass 100% via the default CLI launch** (FR-161).
- [ ] Zero non-stdlib GUI dependencies present (FR-163).
- [ ] docs/GUI_GUIDE.md is complete.


---

## Master File Creation Sequence (Flat, Dependency-Ordered)

> For an agent that prefers a single linear checklist instead of phase-by-phase framing, this is the same plan flattened into strict build order. Each item notes its phase in parentheses.

1. .gitignore, LICENSE, pyproject.toml, equirements.txt, equirements-dev.txt (P0)
2. decodebot/__init__.py (__version__) (P0)
3. decodebot/core/__init__.py, decodebot/rules/__init__.py, decodebot/utils/__init__.py (P0)
4. decodebot/utils/normalization.py (P1)
5. decodebot/core/intents.py (P1)
6. decodebot/rules/greetings.py (P1)
7. decodebot/rules/exit.py (P1)
8. decodebot/rules/unknown.py (P1, fuzzy suggestion stubbed)
9. decodebot/core/rule_engine.py — minimal, hardcoded imports (P1)
10. decodebot/core/io_handler.py (P1)
11. decodebot/core/session.py — minimal (P1)
12. decodebot/core/dispatcher.py (P1)
13. decodebot/core/loop.py — basic loop, exit-only termination (P1)
14. decodebot/core/app.py (P1)
15. main.py (P1)
16. 	ests/test_compliance.py, 	est_greetings.py, 	est_exit.py, 	est_unknown.py, 	est_normalization.py, 	est_no_prohibited_imports.py (P1)
17. **? GATE: full Compliance Matrix must pass before continuing.**
18. decodebot/rules/help_about_version.py (P2)
19. decodebot/core/responder.py (P2)
20. 	ests/test_help_about_version.py (P2)
21. Expand decodebot/core/session.py to full SessionState (P3)
22. decodebot/core/history.py (P3)
23. decodebot/core/stats.py (P3)
24. 	ests/test_session_history_stats.py (P3)
25. decodebot/rules/personalization.py (P4)
26. 	ests/test_personalization.py (P4)
27. decodebot/core/config.py, config.json, docs/CONFIGURATION.md (P5)
28. 	ests/test_config.py (P5)
29. decodebot/core/logger.py (P6)
30. 	ests/test_logging.py (P6)
31. Harden decodebot/core/loop.py with full error handling + circuit breaker (P7)
32. 	ests/test_error_handling.py (P7)
33. decodebot/rules/easter_eggs.py, docs/HIDDEN_COMMANDS.md (P8)
34. 	ests/test_easter_eggs.py (P8)
35. Upgrade decodebot/core/rule_engine.py to full plugin discovery (P9)
36. decodebot/plugins/README.md, docs/PLUGIN_GUIDE.md (P9)
37. 	ests/test_plugin_template.py, 	ests/test_rule_engine.py (P9)
38. **? GATE: re-run full Compliance Matrix — must still pass 100%.**
39. decodebot/utils/terminal.py, decodebot/utils/levenshtein.py (P10)
40. Finalize decodebot/utils/formatting.py (P10)
41. 	ests/test_cli_formatting.py (P10)
42. Fill remaining tests to reach 105+ total, =90% coverage (P11)
43. README.md, CONTRIBUTING.md, CHANGELOG.md, docs/ARCHITECTURE.md (P12)
44. Final full-suite run + Acceptance Criteria + NFR benchmark verification (P13)
45. Tag 1.0.0 release.

---

## Continuous Verification Checklist (Runs After *Every* Phase, Not Just Once)

- [ ] python main.py still launches without error.
- [ ] All 8 Compliance Matrix rows still pass.
- [ ] 	ests/test_no_prohibited_imports.py still passes.
- [ ] No new console output contains a raw traceback or exception class name.
- [ ] No new file exceeds ~400 lines (NFR-012).
- [ ] No new function exceeds a cyclomatic complexity of 10 (NFR-014).
- [ ] All new public functions/classes have type hints and docstrings.
- [ ] GUI module presence never affects default (non---gui) CLI behavior.
- [ ] No animation effect can block Ctrl+C responsiveness beyond 100ms.

---

## Traceability Appendix — Phase ? Requirement ? Test Quick Reference

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

---

*End of PLAN.md. This document must be re-validated against SPEC.md after any future specification change — if SPEC.md is revised, re-derive the affected phase(s) of this plan before resuming implementation.*
