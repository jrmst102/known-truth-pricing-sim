# Known-Truth Pricing Simulation

This project provides the Python simulation implementation for the book chapter
*Data and Machine-Learning Foundations for AI-Enhanced Price Optimization: From
Prediction to Prescription and Decision Reliability*, by Dr. Jose Mendoza,
Clinical Associate Professor at New York University.

The pilot supports the chapter's work on evaluating machine-learning methods for
price optimization using reproducible, known-truth simulations calibrated with
Dominick's data. V1.1 is described in the
[implementation specification](docs/SPEC_v1.1.md) and
[protocol](docs/PROTOCOL_v1.1.md). The protocol is prepared for author signature;
implementation does not imply scientific approval.

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

## Calibrate and audit

```bash
python scripts/audit_coverage.py --category tna
python scripts/run_calibration.py --config configs/calibration.yaml --categories sna tna tti
```

Coverage audits record the calendar denominator, retained stores, top UPCs, best
coverage across all UPCs, missing-row causes, duplicates and calendar alignment.
Tuna's full 399-week sample fails the unchanged 90% UPC rule. The documented
weeks 1–341 calibration window retains 67 zoned stores and eligible competitors;
`data/calibration/calibration_windows.json` controls that window. Its focal rows
end at week 331, with missing weeks still counted in the denominator. This proposed
step-2 resolution awaits protocol acceptance; all 81 core cells remain configured.
`python scripts/evaluate_calibration_window.py --category tna` reproduces the search.

Calibration uses the mean valid focal-UPC unit price including promotion weeks.
Empirical shock persistence and variance decomposition remain diagnostics; core
simulations impose persistence 0.5 and an equal variance split. Observational
elasticity benchmarks are review flags; see the [open review record](docs/issues/elasticity-benchmark.md).

## Run V1.1

A small synthetic mechanical check:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/run_pilot.py \
  --stage validation --cells sna:med:pos:0.5 --synthetic --reps 2 --cycles 2 \
  --estimators M1 M3 --save-data --save-storeweek --run-id synthetic-v11-smoke
python scripts/check_validation.py outputs/validation/synthetic-v11-smoke
```

Omit the cycle/estimator overrides for a full-horizon check. The default scenario
file crosses three environments, three elasticities, three managerial adjustments,
and three adoption shares. Every cell runs greedy and greedy-RPS policies plus
separate oracle and legacy reference arms. `M3_cf` is stored alongside M3.
Named extensions (`censored`, `weak_instrument`, `other_zone`, `empirical`,
`chainwide`) each vary one factor from a documented base cell.

The four stages have separate seed streams and output directories:

| Stage | Replications | Output |
| --- | --- | --- |
| `validation` (S1) | configurable mechanical checks | `outputs/validation/` |
| `diagnostic` (S2) | 1 per core cell; 5 total for med/pos/0.5 per environment | `outputs/diagnostic/` |
| `pilot` (S3) | 100 per core cell | `outputs/pilot/` |
| `main` (S4) | S3 precision decision | `outputs/main/` |

After author signature and committing reviewed code/configuration/calibration:

```bash
python scripts/run_pilot.py --stage diagnostic --cells all --n-jobs 8
```

S3/S4 additionally require `Deliverables 1 and 2 accepted: yes` in the signed
protocol. S4 reads `stages.main.decision_file` in `configs/scenarios.yaml`; it
rejects changes to scientific settings or source code since S3. Replication
streams are fresh for each stage. Targets, floor, cap and budget are explicit in
`configs/decisions.yaml`; only S3 reports an N-required decision and paired Ns.
No scientific stage has been executed or approved by implementing this version.

The manifest freezes effective configs, calibration hashes, raw checksums, code,
protocol version, stage, seed child, environment and generated figures. Scientific
runs require a clean worktree. Validation allows development changes and records
them. `--synthetic` is limited to validation and appears in output provenance.
Existing `outputs/pilot/synthetic-*` reports are **development records**, preserved
for reference and never cited as empirical or scientific results.

Outputs include estimates, assignment/fold states, per-replication metrics,
performance summaries, runtime, report, figures and decisions. `--save-data`
retains history and cycle observations; `--save-storeweek` retains deployed prices,
per-store fallback flags and the expected-revenue triplets. All regret ratios in
data files are fractions, with percentages used only when rendering reports.
M4 coverage stays withheld until the author enables the validated-inference flag.

Resume with exactly the same command plus `--resume --run-id <existing-run-id>`.
Input changes are rejected; existing runs are never overwritten. To re-render:

```bash
python scripts/make_report.py --output-root outputs/validation --run-id synthetic-v11-smoke
```

## Validate

```bash
ruff check src scripts tests
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 pytest -m 'not slow'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 pytest tests/test_loop_smoke.py
# Optional, 200 independent panels; does not automatically lift coverage withholding:
KTSIM_VALIDATE_INFERENCE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  pytest tests/test_dml_inference.py
```

CI runs standard tests and a separate full-horizon job using synthetic fixtures.
Tests cover deployment and exploration, cost independence, zone assignment,
closed-form censored revenue, weighted regret, failure/fallback denominators,
smearing, grouped DML, calibration audits, stage seeds, resume and exact replay.
See [implementation notes](docs/IMPLEMENTATION_NOTES.md) for acceptance evidence.
