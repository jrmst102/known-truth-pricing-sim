# known-truth-pricing-sim
Data and Machine-Learning Foundations for AI-Enhanced Price Optimization

Python 3.11 pilot implementation of [docs/PILOT_SPEC.md](docs/PILOT_SPEC.md).
Scientific protocol approval is pending; see [docs/IMPLEMENTATION_NOTES.md](docs/IMPLEMENTATION_NOTES.md).

## Install

```bash
uv python install 3.11
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e '.[dev,data]'
pre-commit install
```

Alternatively, use Python 3.11's `venv` and `pip install -e '.[dev,data]'`, or
`conda env create -f environment.yml`. Run commands from the repository root.
Dependencies are pinned in [pyproject.toml](pyproject.toml).

## Data

Download data under the [Kilts Center's terms](https://www.chicagobooth.edu/research/kilts/research-data/dominicks).
Do not redistribute movement, demographics or customer-count data. The MIT license covers
code, not the datasets. Existing archives and UPC CSVs in `data/` work directly; new
downloads should go in `data/raw/`. No SAS installation is needed for CSV ZIPs or SAS7BDAT
files. The supplied SAS conversion script is preserved, but is not executed.

Required category files are `wsna`, `upcsna`, `wtna`, `upctna`, `wtti`, `upctti`
as CSV, ZIP (one dataset inside), or SAS7BDAT. Store metadata must contain `store`,
`price_tier`, `zone`; demographics alone does not provide the research pricing zones.
The public codebook's calendar is committed; import its factual store table with:

```bash
curl -L --fail -o /tmp/dominicks-manual.pdf \
	https://www.chicagobooth.edu/-/media/enterprise/centers/kilts/datasets/dominicks-dataset/dominicks-manual-and-codebook_kiltscenter.pdf
python scripts/import_codebook.py --manual /tmp/dominicks-manual.pdf
```

Inspect the generated store/calendar tables before scientific use. Raw data is ignored,
and the pre-commit hook blocks staging raw files even with `git add -f`.

## Three Commands

```bash
python scripts/run_calibration.py --config configs/calibration.yaml --categories sna tna tti
python scripts/run_pilot.py --cells all --n-jobs 8
python scripts/make_report.py --run-id YYYYMMDD-HHMM-COMMIT
```

Calibration writes JSONs, checksums and [data/calibration/calibration_log.md](data/calibration/calibration_log.md).
Invalid category coverage stops that category without relaxing protocol thresholds;
other requested categories are still checked. A blocked tuna calibration prevents real-data
pilot execution. Commit reviewed implementation/configuration/calibration before a real-data
pilot; the pilot refuses a dirty worktree. It also produces its report automatically.

For a quick runnable check that needs no Dominick's data:

```bash
python scripts/run_pilot.py --cells all --synthetic --reps 2 --cycles 2 \
	--estimators M1 M3 --n-jobs 2 --save-data --run-id synthetic-smoke
```

This deliberately shortened run validates plumbing, not statistical acceptance. Omit
`--estimators` to include LightGBM and both DoubleML variants. Full pilot configurations
are expensive: every cycle refits every estimator and cross-fitting learner.

Outputs include estimates/states Parquet, replication shards, runtime and performance CSV,
manifest and decisions JSON, Markdown report and five diagnostic PNGs. `--save-data` also
writes simulated observations, forecasts and realized sales. All latent arrays can be
regenerated from each state's entropy/spawn_key and the frozen calibration/configs.

To resume, rerun the identical pilot command with `--resume --run-id <existing-run-id>`.
Changed code, calibration, settings, environment or worker count are rejected. Choose a
new run ID for a new experiment; existing output directories are never overwritten.

## Validation

```bash
ruff check src scripts tests
pytest -m 'not slow'
pytest tests/test_loop_smoke.py
```

Tests cover ingestion, cleaning, AR variance recovery, elasticity/censoring, oracle bounds,
estimator recovery, MCSEs, parallel checkpoints, saved data, report rendering, CLI resume
and exact scientific replay. CI never reads the movement archives or `data/raw/`.
