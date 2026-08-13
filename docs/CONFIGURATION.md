# Configuration Guide

DecodeBot AI supports an optional `config.json` file at the project root.

## Available Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `bot_name` | str | `"DecodeBot"` | Display name used in banner and prompts |
| `enable_colors` | bool | `true` | Toggle ANSI color output |
| `debug_mode` | bool | `false` | Enable verbose console diagnostics |
| `developer_mode` | bool | `false` | Unlock hidden developer commands |
| `log_level` | str | `"INFO"` | Minimum log level (DEBUG, INFO, WARNING, ERROR) |
| `log_dir` | str | `"logs"` | Directory for log files |
| `history_size` | int | `100` | Max conversation history entries |
| `enable_time_aware_greeting` | bool | `false` | Add time-of-day to greetings |
| `enable_emoji_greeting` | bool | `false` | Recognize emoji greetings |
| `plain_mode` | bool | `false` | Disable non-ASCII characters |
| `enable_animations` | bool | `true` | Toggle typewriter/thinking animations |
| `reduced_motion` | bool | `false` | Reduce animation motion |
| `typewriter_speed` | float | `0.015` | Seconds between typewriter characters |

## Machine Learning Keys (FR-226)

All ML settings flow through the shared config with per-key validation and
default fallback; an invalid ML key never prevents startup.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `ml_dataset` | str | `"iris"` | Dataset source: `"iris"` or a CSV path |
| `ml_target_column` | str \| null | `null` | Target column (required for CSV datasets) |
| `ml_test_size` | float | `0.2` | Fraction held out for testing |
| `ml_random_state` | int | `42` | Reproducibility seed |
| `knn_k` | int | `5` | Neighbor count for KNN |
| `classifier_type` | str | `"knn"` | `knn`, `decision_tree`, `logistic_regression`, `svm`, `random_forest` |
| `scaler_type` | str | `"standard"` | `standard`, `minmax`, `none` |
| `ml_missing_value_strategy` | str | `"error"` | `error`, `drop`, `mean_impute` |
| `models_dir` | str | `"models/"` | Directory for saved model files |
| `ml_outputs_dir` | str | `"outputs/"` | Directory for generated visualizations |
| `ml_log_level` | str | `"INFO"` | Minimum ML log level (inherits `log_level` by default) |

## Recommender Keys (FR-235)

All recommender settings flow through the shared config with per-key
validation and default fallback; a single invalid recommender key never
prevents startup (FR-094, FR-247).

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `recommender_corpus` | str | `"builtin"` | `"builtin"` uses the bundled careers corpus; a CSV file path uses the custom corpus (FR-236/237) |
| `recommender_top_n` | int | `3` | Number of ranked results to return; valid `1-10`, clamped to corpus size (FR-242) |
| `recommender_min_skills` | int | `3` | Minimum usable skills required before ranking; below this the engine returns guidance (FR-244) |
| `recommender_threshold` | float | `0.0` | Optional minimum similarity for inclusion; `0.0` disables threshold exclusion (FR-244) |
| `recommender_random_state` | int | `42` | Reproducibility seed for any future shuffling/vectorizer options (FR-243) |

The `recommend` command reads `--skills` (comma- or space-separated) and
honors `plain_mode` (`config.json`) or the `--plain` command-line flag
(`FR-133`).

## Example

```json
{
    "bot_name": "MyBot",
    "enable_colors": true,
    "debug_mode": true
}
```

If `config.json` is absent or malformed, the application uses built-in defaults without crashing.
