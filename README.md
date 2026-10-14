# Known-Truth Pricing Simulation

This project provides the Python pilot implementation for the book chapter
*Data and Machine-Learning Foundations for AI-Enhanced Price Optimization: From
Prediction to Prescription and Decision Reliability*, by Dr. Jose Mendoza,
Clinical Associate Professor at New York University.

The pilot supports the chapter's work on evaluating machine-learning methods for
price optimization using reproducible, known-truth simulations calibrated with
Dominick's data. Its implementation and protocol are described in the
[pilot specification](PILOT_SPEC.md).

The software is provided under the [MIT License](LICENSE). This license applies
to the code, not to the data; see the [Data section](#data) for the applicable
data terms.

## Set up

The project uses Python 3.11. From the repository root, create an environment
and install the package and development/data dependencies:

```bash
uv python install 3.11
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e '.[dev,data]'
pre-commit install
```

You can also use Python's built-in `venv` with `pip install -e '.[dev,data]'`,
or create a Conda environment with `conda env create -f environment.yml`.
Dependency versions are pinned in [pyproject.toml](pyproject.toml).

## Data

Download Dominick's data in accordance with the
[Kilts Center's terms](https://www.chicagobooth.edu/research/kilts/research-data/dominicks).
Do not redistribute movement, demographics, or customer-count data. The MIT
License covers this project's code only; the datasets remain subject to their
own terms.

Existing archives and UPC CSV files in `data/` can be used directly. Put new
downloads in `data/raw/`. SAS does not need to be installed to use CSV ZIP
archives or SAS7BDAT files. The supplied SAS conversion script is retained for
reference and is not run by the project.

Calibration requires the `wsna`, `upcsna`, `wtna`, `upctna`, `wtti`, and
`upctti` category files. Each can be a CSV, a ZIP containing one dataset, or a
SAS7BDAT file. The store metadata must include `store`, `price_tier`, and
`zone`; demographic data alone does not provide the research pricing zones.

The public codebook calendar is committed to the repository. To import its
factual store table, download the codebook and run:

```bash
curl -L --fail -o /tmp/dominicks-manual.pdf \
  https://www.chicagobooth.edu/-/media/enterprise/centers/kilts/datasets/dominicks-dataset/dominicks-manual-and-codebook_kiltscenter.pdf
python scripts/import_codebook.py --manual /tmp/dominicks-manual.pdf
```

Review the generated store and calendar tables before using them in scientific
analyses. Raw data is ignored by Git, and the pre-commit hook blocks staging raw
files, including with `git add -f`.

## Run the pilot

Run calibration, the pilot, and report generation from the repository root:

```bash
python scripts/run_calibration.py --config configs/calibration.yaml --categories sna tna tti
python scripts/run_pilot.py --cells all --n-jobs 8
python scripts/make_report.py --run-id YYYYMMDD-HHMM-COMMIT
```

Calibration results, checksums, and the run log are written under
`data/calibration/`. If a category does not meet the protocol's coverage
requirements, that category is stopped without relaxing the thresholds; other
requested categories are still checked. A blocked tuna calibration prevents a
real-data pilot from running.

Before starting a real-data pilot, commit the reviewed implementation,
configuration, and calibration results. The pilot refuses to run from a dirty
worktree and generates its report automatically.

For a quick run that does not need Dominick's data:

```bash
python scripts/run_pilot.py --cells all --synthetic --reps 2 --cycles 2 \
  --estimators M1 M3 --n-jobs 2 --save-data --run-id synthetic-smoke
```

This shortened synthetic run checks that the pipeline works; it does not test
statistical acceptance. Omit `--estimators` to include LightGBM and both
DoubleML variants. Full pilot configurations can take substantially longer,
since each cycle refits every estimator and cross-fitting learner.

The pilot writes estimate and state Parquet files, replication shards, runtime
and performance CSV files, a manifest, a decisions JSON file, a Markdown
report, and five diagnostic plots. With `--save-data`, it also saves simulated
observations, forecasts, and realized sales. The latent arrays can be
regenerated from each state's `entropy` and `spawn_key`, together with the
frozen calibration and configuration.

To resume a run, repeat the same pilot command with `--resume` and the existing
run ID:

```bash
python scripts/run_pilot.py --cells all --n-jobs 8 --resume \
  --run-id <existing-run-id>
```

The resume check rejects changes to code, calibration, settings, environment,
or worker count. Use a new run ID for a new experiment; existing output
directories are never overwritten.

## Validate

Run the linter and the standard test suite with:

```bash
ruff check src scripts tests
pytest -m 'not slow'
pytest tests/test_loop_smoke.py
```

Tests cover data ingestion and cleaning, calibration, elasticity and censoring,
oracle bounds, estimator recovery, Monte Carlo standard errors, parallel
checkpoints, saved data, report generation, CLI resume, and reproducible
scientific replay. CI uses synthetic fixtures and does not read movement
archives or `data/raw/`.
