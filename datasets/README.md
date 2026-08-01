# datasets/

Notes and (in future phases) bundled dataset files for the DecodeBot ML
Engine. This directory is intentionally minimal in Phase 16.

## Bundled Iris dataset

By default the ML Engine loads the Iris flower benchmark dataset
(150 samples, 4 features, 3 classes) via `sklearn.datasets.load_iris()`:

- Features: sepal length (cm), sepal width (cm), petal length (cm),
  petal width (cm).
- Classes: setosa (50), versicolor (50), virginica (50) — perfectly balanced.
- `load_dataset("iris")` returns a normalized `Dataset` object (FR-164).

## CSV datasets (forward-compatible, FR-165)

An arbitrary CSV can be loaded with:

```python
from decodebot.ml.dataset_loader import load_dataset
dataset = load_dataset("path/to/data.csv", target_column="species")
```

Required format:

- A header row with column names.
- One column designated as the classification target (`target_column`).
- All other (feature) columns must be numeric.
- No missing values unless a missing-value strategy is configured
  (`"error"` / `"drop"` / `"mean_impute"`, FR-170).

Example layout:

```csv
sepal_length,sepal_width,petal_length,petal_width,species
5.1,3.5,1.4,0.2,setosa
4.9,3.0,1.4,0.2,setosa
```
