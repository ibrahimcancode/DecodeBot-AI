# DecodeBot AI GUI Guide

This guide covers the Tkinter graphical interface of DecodeBot AI. Launch it
with:

```console
python main.py --gui
```

If no display is available, DecodeBot falls back to CLI mode with a notice
instead of crashing (FR-227).

## Tabs

The window opens with a notebook of tabs:

- **Chat** — the conversational agent. Type a command (e.g. `help`,
  `predict --features ...`, `recommend --skills ...`) and press Enter or click
  **Send**. The reply appears in the transcript and is recorded in the session
  exactly as it would be in the terminal (FR-201).
- **Machine Learning** — buttons that run the identical CLI ML commands:
  Train, Evaluate, Compare, Tune-K, Explore, List Models. The **Classify** form
  collects four numeric feature values and routes them through the same
  validation and prediction path as the `predict` CLI command (FR-224, FR-225).
- **Career Recommender** — a skills field plus a **Recommend** button. The tab
  calls the identical engine function as the CLI `recommend` command, so the
  ranked list shown in the window is the same one you get in the terminal
  (FR-246).

## Career Recommender tab

1. Type your skills as a comma-separated list, e.g.
   `Python, SQL, Machine Learning`.
2. Click **Recommend** (or press Enter in the skills field).
3. The boxed top-3 list is rendered below, one row per role with match
   percentage and matched skills.

Rules:

- An empty skills field shows an inline validation message and leaves the app
  responsive; it never crashes the window (FR-246).
- The output honors the same `plain_mode` setting as the CLI: with
  `plain_mode: true` in your config (or `--plain` when launching), the rows are
  printed without box-drawing characters.
- Configuration keys such as `recommender_top_n`, `recommender_min_skills`, and
  `recommender_corpus` apply to the GUI exactly as they do to the CLI. See
  `docs/CONFIGURATION.md`.

## Close

Closing the window prints a session summary (messages exchanged and duration)
into the transcript, says goodbye, and exits after a short delay (FR-227).
