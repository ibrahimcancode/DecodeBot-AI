# DecodeBot AI — Content-Based Tech Stack Recommendation Engine

> Wave 3 (Week 3) deliverable. Implements `SPEC.md → Part III`
> (`FR-233`–`FR-248`, `NFR-086`–`NFR-090`, `NFR-096`).
> A reviewer can run `recommend --skills "Python, SQL, Machine Learning"` in the
> CLI or GUI and get a ranked career match list.

## What it is

A content-based career / tech-stack recommender. You type the skills you've
learned, and DecodeBot ranks every career profile in its catalog by cosine
similarity between your skill text and the profile text (skills + description),
returning the top matches with a match percentage and the matched skills.

It is a **single-command engine** (`recommend`) wired into the existing
Chatbot Engine dispatcher, and it ships as a fully isolated package:
`decodebot/recommender/`. Nothing outside the permitted wiring files
(`main.py`, `dispatcher.py`, `app_gui.py`, `app.py`) may import it, and it
never imports the Chatbot Engine core or the ML Engine (FR-233). It uses
scikit-learn only lazily, inside the functions that need it, so chatbot-only
startup is unaffected (FR-234, NFR-088, NFR-090).

## Quick start

Run the REPL and type the command (quotes are optional; comma- or
space-separated skills both work):

```
$ python main.py

You: recommend --skills "Python, SQL, Machine Learning"
Bot: ┌───────────────────────────────────────────────────────────────┐
     │ Career Recommendations                                       │
     ├───────────────────────────────────────────────────────────────┤
     │ 1. Machine Learning Engineer - 61% - matched: python, machine learning
     │ 2. Data Scientist - 41% - matched: python, sql, machine learning
     │ 3. NLP Engineer - 32% - matched: python, machine learning
     └───────────────────────────────────────────────────────────────┘
```

The GUI has an equivalent **Career Recommender** tab (`python main.py --gui`)
that calls the identical engine function (FR-246).

## Pipeline

1. **Input & normalization** (`normalization.py`) — the `--skills` argument is
   tokenized (commas or whitespace), canonicalized (lowercase, trailing
   punctuation stripped, abbreviations like `ml` → `machine learning`,
   `k8s` → `kubernetes`), and de-duplicated case-insensitively while keeping
   first-seen order. Fewer than `recommender_min_skills` (default 3) usable
   skills produces a friendly guidance message, never a crash (FR-240, FR-244).
2. **Corpus** (`corpus.py`) — a built-in careers catalog (≥ 20 profiles across
   ≥ 6 domains: backend, frontend, data/ml, mobile, devops/cloud,
   cybersecurity). Custom CSV corpora load through `load_csv_corpus()` with
   validation (required `title,skills,description` columns, no duplicate
   titles, no empty entries) and friendly errors (FR-236, FR-237, FR-238).
3. **Features** (`features.py`) — exactly **one** TF-IDF vectorizer is fitted
   on the corpus (skills + description text per profile). Every user query is
   projected through that same fitted vocabulary, so query and profile
   dimensionality always match and no corpus text leaks into the query
   representation (FR-241).
4. **Ranking** (`ranker.py`) — cosine similarity between the query vector and
   each profile row; results are sorted by similarity (highest first), then by
   corpus order, then by title — never by hash/set order, so output is
   bit-identical across runs (FR-242, FR-243, NFR-087). Top-N defaults to 3,
   is validated to 1–10, and is clamped to the corpus size.
5. **Fallbacks** (`fallbacks.py`, `result.py`) — the engine always returns a
   structured `RecommendationOutcome`, never an error stack:
   - **Guidance** — fewer than `recommender_min_skills` skills (cold start).
   - **Zero-match** — every query token falls outside the fitted vocabulary.
   - **Partial-match** — a configured threshold (`recommender_threshold`) would
     exclude every profile; the closest careers are returned, clearly labeled.
6. **Presentation** (`app_recommender.py`) — the single thin bridge from the
   dispatcher. It parses `--skills`, reads the FR-235 config keys, calls the
   engine, and renders the structured outcome as a boxed screen (or plain
   ASCII rows under `plain_mode` / `--plain`, FR-133, FR-245).

## Configuration (FR-235)

All keys are optional — sensible defaults apply. See `docs/CONFIGURATION.md`
for the full reference.

| Key | Default | Meaning |
| --- | --- | --- |
| `recommender_corpus` | `"builtin"` | `builtin` or a path to a CSV corpus file. |
| `recommender_top_n` | `3` | Number of ranked results (validated 1–10). |
| `recommender_min_skills` | `3` | Minimum usable skills before guidance. |
| `recommender_threshold` | `0.0` | Minimum similarity to keep a result; `0.0` disables exclusion. |
| `recommender_random_state` | `42` | Reproducibility seed for the pipeline. |

## Command-line flags

- `python main.py --plain` — runs the whole session in plain mode (no box
  drawing / ANSI characters anywhere, including `recommend` output).
- `python main.py --gui` — opens the GUI; the **Career Recommender** tab uses
  the same engine and honors `plain_mode`.

## Behavior guarantees

- **Deterministic** — same query, same corpus → identical ranked output every
  run (NFR-087).
- **Never crashes** — malformed arguments, missing `--skills`, bad CSV paths,
  and out-of-vocabulary queries all route to friendly messages while the
  session keeps running (FR-247); a 1,000-iteration fuzz test asserts zero
  unhandled exceptions.
- **Honest partial matches** — if a threshold would empty the list, results are
  returned under a clear "partial match" label rather than silently dropping
  everything.
- **Fast** — ranking latency is ~2 ms on the built-in corpus (target < 100 ms,
  NFR-086); chatbot-only startup stays well under 300 ms (NFR-090).

## Isolation & testing

- **Isolation (FR-233, NFR-088):** `tests/test_wave3_isolation.py` statically
  scans every `.py` file: no engine file may import `decodebot.recommender`
  (only the four wiring files), and no recommender file may import
  `decodebot.ml`/`decodebot.core` or any ML library at module scope (lazy
  imports only). Importing the recommender pulls zero heavy modules and loads
  no corpus.
- **Test suite (FR-248, NFR-089):** the full `TC-REC-001`–`012` set plus
  unit/regression/fuzz tests, with **100% line coverage** on
  `decodebot/recommender/` (target ≥ 90%). Week 1 and Week 2 compliance
  matrices still pass 100%.

Run the suite:

```bash
python -m pytest
```

## Source layout

```
decodebot/recommender/
├── __init__.py            # public API exports
├── corpus.py              # built-in + custom CSV corpus, validation
├── normalization.py       # skill parsing / canonicalization (FR-240)
├── features.py            # single fitted TF-IDF pipeline (FR-241)
├── ranker.py              # cosine ranking, Top-N, threshold (FR-242-244)
├── result.py              # RecommendationResult / RecommendationOutcome
├── fallbacks.py           # guidance / zero-match / partial-match outcomes
└── app_recommender.py     # thin CLI bridge (FR-235, FR-239, FR-245, FR-247)
```
