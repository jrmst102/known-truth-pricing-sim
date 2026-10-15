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

## Development validation

From the repository root, use a fresh run ID for a small synthetic check:

```bash
python scripts/run_pilot.py --stage validation --synthetic \
  --cells sna:med:pos:phi=0.5 --reps 2 --cycles 2 --estimators M1 M3 \
  --n-jobs 2 --save-data --save-storeweek --run-id v11-smoke
```

Synthetic fixtures can be used only for validation; they never replace a blocked
empirical calibration. The environment tag names the scenario whose mechanics
are exercised, not a claim that synthetic results use that environment's data.

Run reproducible mechanical acceptance across all estimators and policies,
three adoption settings, two replications, and 104 cycles:

```bash
python scripts/validate_v11.py --run-id v11-acceptance --n-jobs 2
```

This uses small nuisance learners for mechanical validation and records the
actual parameters. It is not the S2 diagnostic or a statistical acceptance study.
Results, report, manifest and checks are under `outputs/validation/<run-id>/`.
Both validation commands use the same saved-run checker. For a short run, use
`python scripts/check_validation.py <run-directory>`; add `--full-horizon` to
require the complete 104-cycle, two-replication, all-arm adoption matrix.
Use `--check-only` to recheck already-generated acceptance artifacts; `--resume`
requires identical source, calibration, configuration, environment and worker count.

`--save-data` writes simulated histories, forecasts and realized sales.
`--save-storeweek` writes per-store prices, assignments, fallback flags and true
expected revenue triplets to `storeweek.parquet`. Ratios are stored as fractions;
percentages are a report presentation choice. Model-store measures are null
when phi is zero. Failures remain in policy comparisons, with fallback rates.

The historical `outputs/pilot/synthetic-smoke` and `synthetic-demo` reports are
**v1.0 development records**, preserved for provenance. They are not scientific
results and must not be cited as such.

## Calibration and staged runs

Audit eligibility before proposing any sample change:

```bash
python scripts/audit_coverage.py --category tna --search-window
python scripts/run_calibration.py --config configs/calibration.yaml --categories sna tna tti
```

Recalibration reads approved selections from
`<data-dir>/calibration/calibration_windows.json`, or an explicit `--windows` file.
Tuna uses the approved inclusive range 1–341 without changing the 90% threshold.
The full-span audit is preserved in `coverage_audit_tna.json`; the applied-window
audit is written to `coverage_audit_tna_window.json`. Calibration diagnostics and
checksums record the selected window and its configuration hash. A category
without a window selection keeps its full sample. Invalid/too-short windows fail
before calibration outputs are changed; selected windows must retain at least 40 stores.
The observed focal-UPC range (currently weeks 1–331 for tuna) is separate from the
approved 341-week denominator, which includes missing boundary weeks.

The first command needs the full public zoned-store table, normally imported to
`data/raw/stores.csv`. Audit results identify the metadata source and scope.
The checked-in preliminary audits used the previously retained store table;
they do not certify the original full-metadata tuna sample. A search result alone
never changes the selected window; author approval is recorded separately. Keep
the 90% threshold.
Benchmark observational elasticities are review flags, not exclusion criteria;
see [the investigation draft](docs/BETA_REFERENCE_REVIEW.md).

After the required author acceptance, stages use `configs/scenarios.yaml`:

```bash
python scripts/run_pilot.py --stage diagnostic --cells all --n-jobs 2 --run-id s2-diagnostic
python scripts/run_pilot.py --stage pilot --cells all --n-jobs 2 --run-id s3-precision
python scripts/run_pilot.py --stage main --cells all --decision outputs/pilot/s3-precision/decisions.json \
  --n-jobs 2 --run-id s4-main
```

The core has 81 cells; the two-environment 54-cell alternative requires author
approval and a protocol/chapter amendment. Named extensions vary one factor from
a base cell, for example `--extension censored` during validation. No extension
is silently mixed into the core. Stage seeds are separate; cells within a stage
share replication streams. The diagnostic's five extra base replications use
new streams, separate from its first base replication.

The precision decision reports per-cell/arm SDs, the bounding measure, planned
paired comparisons, targets, explicit floor/cap, achieved precision at the cap,
and projected runtime against the budget. It appears only for the pilot stage.

## Validate

```bash
ruff check src scripts tests
pytest -m 'not slow' --ignore=tests/test_loop_smoke.py
pytest tests/test_loop_smoke.py
RUN_DML_INFERENCE=1 pytest tests/test_dml_inference.py
```

The last command explicitly runs 200 independent draws for each DML variant.
Passing never changes `M4_dml.inference_validated`: author opt-in is separate.
CI runs the unit and full-horizon smoke jobs with synthetic data; it never reads
movement archives or `data/raw/`.
