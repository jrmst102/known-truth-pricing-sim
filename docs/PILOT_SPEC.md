# Pilot Implementation Specification

**Repository:** `known-truth-pricing-sim` (working name)
**Scope:** the pilot defined in *Pilot Protocol v1.0* (October 13, 2026) for the known-truth simulation in Chapter 1, *Data and Machine-Learning Foundations for AI-Enhanced Price Optimization*.
**Spec version:** 1.0 · **Owner:** Jose Mendoza · **Status:** ready for implementation

This document tells a developer what to build so that the pilot runs exactly as the protocol describes. The protocol is the authority on *what* and *why*; this specification is the authority on *how*. Section numbers in brackets, such as [P §9.1], point to the protocol.

---

## 1. Goals and non-goals

**Goals**

1. Run the six pilot cells P0–P5 [P §8, Table 5] and the three-category calibration [P §4] from a single command each.
2. Produce the four dataset classes of Morris et al. (2019, Table 5): estimates, states, performance, and (regenerable) simulated data [P §10].
3. Generate the pilot report (`report.md`) automatically, including the `n_sim` decision, the instrument pass-through decision, the compute projection, and the failure rates [P §9, §10].
4. Make every number reproducible from a commit hash, a master seed, and the raw Dominick's files.

**Non-goals**

- Running the full 27-cell design (a later milestone reuses this code without change to the protocol-governed parts).
- Any plotting beyond the diagnostic figures listed in §9.
- Any use of the Dominick's data in CI (CI runs on a synthetic fixture only).

---

## 2. Repository layout

```
known-truth-pricing-sim/
├── README.md                     # install, data download, three commands
├── LICENSE                       # MIT for code; data terms are the Kilts Center's
├── CITATION.cff
├── CHANGELOG.md                  # amendments mirror P §12
├── pyproject.toml                # package `ktsim`, pinned dependencies
├── environment.yml               # conda alternative
├── configs/
│   ├── dgm_base.yaml             # all constants of P Table 4 and P §5
│   ├── estimators.yaml           # hyperparameters of M1–M4 (P §6.1)
│   ├── pilot_cells.yaml          # P Table 5, one block per cell
│   └── calibration.yaml          # cleaning thresholds and plausibility ranges (P §3.2, Table 3)
├── data/
│   ├── raw/                      # Dominick's CSVs; git-ignored; checksums recorded
│   ├── fixtures/                 # synthetic calibration fixture used by tests and CI
│   └── calibration/              # committed outputs: calibration_<cat>.json, calibration_log.md
├── src/ktsim/
│   ├── __init__.py
│   ├── io.py                     # load movement/UPC/store files, decode weeks
│   ├── clean.py                  # P §3.2 rules, in order
│   ├── calibrate.py              # P §4 auxiliary regression and Table 2 quantities
│   ├── rng.py                    # seed sequence, per-replication shock arrays
│   ├── dgm.py                    # P §5: demand, legacy prices, instruments, censoring
│   ├── oracle.py                 # oracle price and regret (P §6.2)
│   ├── policies.py               # greedy, greedy + random price shocks
│   ├── estimators/
│   │   ├── base.py               # Estimator protocol: fit(df) -> Estimate
│   │   ├── ols.py                # M1
│   │   ├── gbm.py                # M2
│   │   ├── iv.py                 # M3 (2SLS and control function)
│   │   └── dml.py                # M4 (PLR and PLIV)
│   ├── loop.py                   # P §6.3 retraining loop
│   ├── metrics.py                # performance measures and Monte Carlo SEs (P §7)
│   ├── pilot.py                  # cell runner, parallelism, dataset writers
│   ├── decisions.py              # n_sim, pass-through choice, compute ladder (P §9)
│   └── report.py                 # report.md generator (P §10)
├── scripts/
│   ├── run_calibration.py
│   ├── run_pilot.py
│   └── make_report.py
├── tests/
│   ├── test_clean.py
│   ├── test_calibrate.py
│   ├── test_dgm.py
│   ├── test_oracle.py
│   ├── test_estimators_known_properties.py
│   ├── test_metrics.py
│   └── test_loop_smoke.py
├── outputs/                      # git-ignored except report.md and performance.csv per run
│   └── pilot/<run_id>/
└── .github/workflows/ci.yml
```

`run_id` is `YYYYMMDD-HHMM-<short-commit-hash>`.

---

## 3. Environment

- Python 3.11. Pin exact versions in `pyproject.toml` and record them in the report.
- Core: `numpy`, `pandas`, `pyarrow`, `scipy`, `statsmodels`, `linearmodels` (IV2SLS), `lightgbm`, `doubleml`, `scikit-learn`, `pyyaml`, `joblib`, `matplotlib`.
- Random numbers: `numpy.random.Generator` with `PCG64`, seeded through `numpy.random.SeedSequence` [P §8].
- Hardware is recorded by `report.py` (CPU model, cores, RAM) because the compute projection [P §9.2] is machine-specific.

---

## 4. Data acquisition

1. Download from the Kilts Center Dominick's page (login and acceptance of terms required): `wsna.csv`, `upcsna.csv`, `wtna.csv`, `upctna.csv`, `wtti.csv`, `upctti.csv`, and the store file with store number, price tier, and zone. Place them in `data/raw/`.
2. `scripts/run_calibration.py` refuses to run if any file is missing and prints the expected names.
3. `io.load_movement(path)` reads the CSV with the truncated `price` and `profit` columns (the `_hex` columns are ignored). Column names are lower-cased: `upc, store, week, move, price, qty, profit, sale, ok`.
4. `io.week_table()` returns the week-to-date decode for weeks 1–400 from a committed CSV transcribed from the manual (`data/fixtures/week_decode.csv`), with a `special_event` column and a derived `lent` flag (four weeks preceding Easter week, Easter dates committed for 1990–1997).
5. SHA-256 of each raw file is written to `data/calibration/calibration_log.md`. Raw files are git-ignored.

---

## 5. Configuration schema

### 5.1 `configs/dgm_base.yaml` (values from P Table 4 and §5)

```yaml
feasible_band: {lower: 0.80, upper: 1.20}   # multiples of p_bar
ladder_step: 0.05                            # dollars
cross_price_coef: 0.20
comp_index: {rho: 0.80}                      # sd from calibration (sigma_comp)
cost_shifter: {rho: 0.80, sd: 0.05}
zone_drift: {rho: 0.90}                      # variance from calibration (sigma_nu2)
kappa_levels: {none: 0.0, pos: 0.05, neg: -0.05}   # log-price move per one-SD shock
exploration: {delta_levels: [0.0, 0.03], decay_power: -0.25, two_point: true}
censoring: {multiplier: 1.5}
history_weeks: 52
cycles: 104
rho_m_levels: [0.0, 0.5]
eta_levels: {low: -0.8, med: -1.06, high: -2.5}
phi_levels: [0.0, 0.5, 1.0]
```

### 5.2 `configs/estimators.yaml`

```yaml
M1_ols: {robust_se: HC1}
M2_gbm: {n_estimators: 500, learning_rate: 0.05, num_leaves: 31, min_child_samples: 20,
         fd_step: 0.01, fd_window_weeks: 4}
M3_iv:  {instrument: cost_shifter, variants: [tsls, control_function], report_first_stage_F: true}
M4_dml: {n_folds: 5, nuisance: lightgbm, nuisance_params: {n_estimators: 500, learning_rate: 0.05, num_leaves: 31, min_child_samples: 20},
         variants: [plr_controls, pliv_cost_shifter]}
```

### 5.3 `configs/pilot_cells.yaml` (P Table 5)

```yaml
master_seed: 20261013
environment: tuna
cells:
  P0: {eta: med, kappa: none, phi: 0.0, delta: 0.0, reps: 20,
       estimators: [M1, M2, M3, M4_plr, M4_pliv], policies: [greedy, oracle]}
  P1: {eta: med, kappa: pos, phi: 0.5, delta: [0.0, 0.03], reps: 100,
       estimators: [M1, M2, M3, M4_plr, M4_pliv], policies: [greedy, greedy_rps]}
  P2: {eta: low,  kappa: pos, phi: 0.5, delta: 0.0, reps: 20, estimators: [M1, M3], policies: [greedy]}
  P3: {eta: high, kappa: pos, phi: 0.5, delta: 0.0, reps: 20, estimators: [M1, M3], policies: [greedy]}
  P4: {eta: med, kappa: pos, phi: 0.0, delta: 0.0, reps: 20, estimators: [M3], policies: [legacy],
       pass_through_grid: [0.05, 0.10, 0.20, 0.50, 1.00]}
  P5: {eta: med, kappa: none, phi: 0.0, delta: 0.0, reps: 5, data_only: true,
       censoring_multipliers: [1.25, 1.5, 2.0]}
```

`estimators: [M1, M2, M3, M4_plr, M4_pliv]` counts as four estimators in the protocol's sense (M4 has two variants). `greedy_rps` is greedy plus random price shocks. `oracle` is the known-truth policy used only for the regret-equals-zero check.

### 5.4 `configs/calibration.yaml` (P §3.2 and Table 3)

```yaml
store_coverage_min: 0.80
store_coverage_fallback: 0.70
upc_coverage_min: 0.90
zero_share_max: 0.10
harmonics: 2
rho_xi_bounds: [0.20, 0.90]
xi_share_max: 0.90
plausibility:
  retained_stores_min: 40
  promo_freq: [0.05, 0.40]
  promo_depth: [0.05, 0.40]
  resid_sd: [0.20, 1.00]
  profit_mean: [10, 45]
  beta_reference: [-2.59, -0.79]
```

---

## 6. Module contracts

All DataFrames are `pandas`; long format; one row per store-week unless stated. Functions must be pure (no hidden state) except for the RNG objects passed in explicitly.

### 6.1 `clean.py`

```python
def clean_category(movement: pd.DataFrame, upc: pd.DataFrame, stores: pd.DataFrame,
                   cfg: CalibrationConfig) -> CleanResult
```
Applies P §3.2 steps 1–7 in order. `CleanResult` holds the cleaned store-week frame for the focal UPC, the chosen `focal_upc`, the retained `store_ids`, the `zero_share`, a `substituted_focal: bool`, and a `log: list[str]` with one line per rule and its row counts.

### 6.2 `calibrate.py`

```python
def calibrate(clean: CleanResult, cfg: CalibrationConfig) -> Calibration
def check_plausibility(cal: Calibration, cfg: CalibrationConfig) -> list[Check]
```
`Calibration` is a dataclass serialized to `data/calibration/calibration_<cat>.json` with exactly the fields of P Table 2: `alpha_s: dict[int, float]`, `season: {g: [..], h: [..]}`, `holiday: dict[str, float]`, `promo_effect`, `rho_xi`, `sigma_xi2`, `sigma_eps2`, `p_bar`, `mu_z: dict[int, float]`, `sigma_nu2`, `pi_promo`, `promo_depth: {mean, sd}`, `sigma_comp`, `unit_cost`, `price_dispersion: {sd_log_price, n_distinct}`, `beta_reference`, plus `n_stores`, `n_store_weeks`, `zero_share`, `focal_upc`, `weeks: [first, last]`.
The auxiliary regression is OLS with store fixed effects (`statsmodels`), as in P §4. Autocovariances are computed within store on the residual series, averaged across stores weighted by series length.

### 6.3 `rng.py`

```python
def replication_streams(master_seed: int, n_reps: int) -> list[np.random.SeedSequence]
def draw_shocks(ss: np.random.SeedSequence, n_stores: int, n_weeks: int, cal: Calibration, dgm: DGMConfig) -> ShockArrays
```
`ShockArrays` contains every random input a replication consumes, pre-generated: `omega[s, t]`, `eps[s, t]`, `u[s, t]` (±1), `cost[t]`, `nu[z, t]`, `promo[t]` (Bernoulli), `promo_depth[t]`, `comp_index[t]`, `common_shock[t]`, `model_store_assignment[s]` (drawn for the largest φ and truncated for smaller φ so that φ = 0.5 stores are a subset of φ = 1 stores). The state (`ss.entropy`, `spawn_key`) is written to `states.parquet` before the replication starts [P §8]. Arms within a replication share one `ShockArrays` [P §6.3 step 4].

### 6.4 `dgm.py`

```python
def expected_log_demand(cal, dgm, x: pd.DataFrame, price: np.ndarray, eta: float) -> np.ndarray   # alpha_s + gamma'x - b(p - p_bar)
def draw_sales(cal, dgm, x, price, eta, xi, eps, censor: bool) -> np.ndarray
def legacy_log_price(cal, dgm, t, zone, cost_t, nu_zt, promo_t, depth_t) -> np.ndarray
def deployed_log_price(rec_log_price, legacy_log_price, D_s, kappa_scaled, xi_st, delta_t, u_st) -> np.ndarray
def instruments(cal, dgm, t, legacy_log_price_all_stores, zone) -> dict[str, np.ndarray]  # cost_shifter, other_zone_price
def kappa_scaled(level: float, sigma_xi: float) -> float   # level / sigma_xi
```
`b = abs(eta) / cal.p_bar`. `ξ` is AR(1) with innovation variance `sigma_xi2 * (1 - rho_xi**2)`; when `rho_m > 0`, replace a share `rho_m` of the variance with `common_shock[t]`. Censoring: `min(q, 1.5 * exp(expected_log_demand))` with the multiplier from config.

### 6.5 `oracle.py`

```python
def oracle_price(cal, dgm, eta) -> float          # argmax over the ladder of p * exp(-b (p - p_bar))
def regret(p_rec: np.ndarray, p_star: float, b: float, p_bar: float) -> np.ndarray   # P §6.2 formula
```
Both must agree with a brute-force grid in `test_oracle.py`. Record `oracle_at_bound: {"ceiling","floor","interior"}` per cell.

### 6.6 `estimators/`

```python
class Estimate(TypedDict):
    eta_hat: float; ci_low: float | None; ci_high: float | None
    first_stage_F: float | None; converged: bool; failure_reason: str | None
    predict: Callable[[pd.DataFrame, np.ndarray], np.ndarray]   # expected demand at given prices and controls

class Estimator(Protocol):
    name: str
    def fit(self, df: pd.DataFrame, cal: Calibration, cfg: dict) -> Estimate: ...
```
Inputs available in `df`: `store, t, log_q, price, p_bar, promo, holiday_*, sin_k, cos_k, log_comp_index, zone, cost_shifter, other_zone_price`. Estimators never receive `xi`, `eps`, `D_s`, or `eta`.

- **M1** (`ols.py`): `log_q ~ (price - p_bar) + controls + C(store)`, HC1 SEs; `eta_hat = -b_hat * p_bar`; CI from the coefficient CI.
- **M2** (`gbm.py`): LightGBM regressor on `price, controls, week_of_year, store (categorical)`; `eta_hat` = mean over store-weeks in the last `fd_window_weeks` of `(f(1.01 * p_bar) - f(0.99 * p_bar)) / (ln 1.01 - ln 0.99)`, where `f` is the predicted log demand at the store-week's controls; no CI.
- **M3** (`iv.py`): `linearmodels.IV2SLS` with `price - p_bar` endogenous, `cost_shifter` instrument, controls and store dummies exogenous; `first_stage_F` from the first-stage diagnostic; control-function variant: first-stage OLS residual appended to the M1 design. In the pilot, the reported M3 is the 2SLS; the control-function variant is stored under `M3_cf` for comparison.
- **M4** (`dml.py`): `doubleml.DoubleMLPLR` (controls-only) and `DoubleMLPLIV` (cost shifter), `n_folds = 5`, LightGBM learners with the M2 hyperparameters; `eta_hat = -theta_hat * p_bar`; CI from DoubleML.

Failure codes [P §9.3]: `nonconvergence`, `nonfinite`, `abs_eta_gt_10`. A sign flip is a flag, not a failure.

### 6.7 `policies.py`

```python
def greedy_price(est: Estimate, x_t: pd.DataFrame, ladder: np.ndarray) -> np.ndarray   # per store: argmax p * q_hat(p | x)
def add_random_price_shock(log_price: np.ndarray, delta: float, t: int, u_t: np.ndarray, decay_power: float) -> np.ndarray
```
For M1, M3, M4 the predicted demand is the fitted semi-log model at the store's controls; for M2 it is the model prediction. `t` in the decay is the cycle index starting at 1 in week 53.

### 6.8 `loop.py`

```python
def run_replication(cell: CellConfig, rep: int, shocks: ShockArrays, cal: Calibration,
                    dgm: DGMConfig, est_cfg: dict) -> pd.DataFrame
```
Returns the estimates rows for every arm and cycle (schema in §7.1). Procedure is P §6.3 verbatim: 52 legacy weeks, then 104 cycles of refit, recommend, deploy, draw, append. On a failed fit, carry the previous recommendation forward and record the failure. Forecasts: at the end of week t−1, predict week t sales for all stores at the deployed price of week t; store `forecast` and `realized`.

Runtime: wrap each arm's cycle loop in a timer; write `seconds` per arm per replication.

### 6.9 `metrics.py`

```python
def performance(estimates: pd.DataFrame, truth: dict) -> pd.DataFrame
```
Computes, per cell × arm, at cycles 78, 104, and 156: bias, empirical SE, RMSE, coverage (where CI exists), share of sign flips, failure share; per cell × arm over the horizon: mean per-period regret on recommended and deployed prices, cumulative regret (percentage points), decision reliability (τ = 0.02, K = 26), MAPE and RMSE of one-week-ahead forecasts, trailing-26-week SD of deployed log price at cycle 156. Every row carries a Monte Carlo SE using the Morris et al. (2019, Table 6) formulas, implemented in `mcse_bias`, `mcse_empse`, `mcse_mse`, `mcse_coverage`, `mcse_mean`. `test_metrics.py` checks each against a hand-computed example.

### 6.10 `decisions.py`

```python
def choose_n_sim(perf_P1: pd.DataFrame, bias_target=0.02, regret_target_pp=0.25, floor=500, cap=2000) -> NSimDecision
def choose_pass_through(perf_P4: pd.DataFrame) -> PassThroughDecision     # median F in [8,12] -> weak; >= 50 -> strong
def compute_projection(runtime: pd.DataFrame, n_sim: int, budget_hours=150.0) -> ComputePlan  # applies the ladder of P §9.2
def censoring_multiplier(summary_P5) -> float                               # closest to 5% censored store-weeks
```
Each returns a dataclass with the inputs that produced the decision so the report can print them.

### 6.11 `report.py`

Builds `outputs/pilot/<run_id>/report.md` with the sections in P §10, in that order, plus a header with commit hash, package versions, hardware, master seed, and the SHA-256 of each raw file. Tables are Markdown; numbers are printed to the precision justified by their Monte Carlo SE (bias to 3 decimals, coverage to 2, regret to 2 decimals in percentage points).

---

## 7. Output schemas

### 7.1 `estimates.parquet` (one row per cell × rep × arm × cycle)

| Column | Type | Notes |
|---|---|---|
| run_id, cell, rep, arm | str/int | arm = `<estimator>:<policy>` |
| cycle | int | 1–104 (week = cycle + 52) |
| eta_true, p_star, oracle_at_bound | float/str | per cell |
| eta_hat, ci_low, ci_high | float | NaN when failed or no CI |
| first_stage_F | float | M3, M4_pliv only |
| converged, failure_reason, sign_flip | bool/str/bool | |
| p_rec, p_dep_mean | float | recommended price; mean deployed price over model stores |
| regret_rec, regret_dep | float | P §6.2 |
| forecast_mape, forecast_rmse | float | one-week-ahead, all stores |
| price_sd_26 | float | trailing SD of deployed log price |
| seconds | float | wall-clock for the cycle |

### 7.2 `states.parquet`
`run_id, cell, rep, entropy, spawn_key, started_at, finished_at, status`.

### 7.3 `performance.csv`
`run_id, cell, arm, cycle_or_horizon, measure, estimate, mcse, n_reps`.

### 7.4 `calibration_<cat>.json` and `calibration_log.md`
As in §6.2; the log records every cleaning rule's row counts, every plausibility check with its result and fallback, and the raw-file checksums.

---

## 8. Command-line interface

```bash
# Calibration for all three categories (requires data/raw/)
python scripts/run_calibration.py --config configs/calibration.yaml --categories sna tna tti

# One pilot cell, or all; parallel across replications only
python scripts/run_pilot.py --cells P0 --n-jobs 8
python scripts/run_pilot.py --cells all --n-jobs 8

# Report (reads outputs/pilot/<run_id>/ and data/calibration/)
python scripts/make_report.py --run-id 20261020-0930-ab12cd3
```

`run_pilot.py` refuses to start if the working tree is dirty, so that every run maps to a commit. It writes `states.parquet` incrementally and resumes from the last finished replication if interrupted.

---

## 9. Diagnostic figures (pilot only)

Saved as PNG under `outputs/pilot/<run_id>/figures/`: (a) P0 distribution of `eta_hat` by estimator with the true value marked; (b) P1 trajectories of `eta_hat` over cycles, median and 10th–90th percentiles by arm; (c) P1 trailing price SD over cycles by policy; (d) P4 first-stage F by pass-through value; (e) P1 forecast MAPE against elasticity bias, one point per arm. These support the pilot report only; chapter figures are produced later from the full design.

---

## 10. Tests and continuous integration

| Test | What it proves | Fixture |
|---|---|---|
| `test_clean.py` | Each P §3.2 rule drops exactly the rows planted in the fixture; focal UPC selection and substitution | `data/fixtures/movement_small.csv` with planted OK = 0 rows, zero-price rows, a low-coverage store, a discontinued UPC |
| `test_calibrate.py` | `rho_xi`, `sigma_xi2`, `sigma_eps2` recovered within tolerance from a series with known AR(1) + noise; clipping and fallback paths | generated in-test |
| `test_dgm.py` | Elasticity at `p_bar` equals `eta` by finite difference; κ scaling moves log price by 0.05 per SD; censoring never exceeds demand; common shock share equals `rho_m` | generated |
| `test_oracle.py` | Oracle price equals brute-force argmax; regret is 0 at `p_star`, positive elsewhere; bound classification for η = −0.8, −1.06, −2.5 | generated |
| `test_estimators_known_properties.py` | With κ = 0 and exogenous prices on 2,000 store-weeks, M1 and M3 recover `eta` within 2 SEs; M3 first-stage F > 50 at pass-through 1.0 | generated |
| `test_metrics.py` | Each MCSE formula against a hand-computed example from Morris et al. (2019, Table 6) | in-test |
| `test_loop_smoke.py` | Two replications of P0 run end to end on the synthetic calibration fixture in under 5 minutes; output schemas validate | `data/fixtures/calibration_synthetic.json` |

`ci.yml` runs on push and pull request: `ruff`, `pytest -m "not slow"`, then `test_loop_smoke.py`. CI never touches `data/raw/`. A `pre-commit` hook blocks any file under `data/raw/` from being staged.

---

## 11. Acceptance criteria (maps to P Table 1)

| ID | Criterion | Verified by |
|---|---|---|
| AC1 | P0: bias of M1, M3, M4_plr within 2 MCSE of 0; coverage ≥ .80; oracle regret = 0; zero failures | `report.md`, section "P0 correctness" |
| AC2 | `n_sim` printed with the SDs that produced it and the rule in P §9.1 | `report.md`, "P1 decision" |
| AC3 | Two pass-through values chosen with median F in [8, 12] and ≥ 50 | `report.md`, "P4 instrument" |
| AC4 | Oracle at ceiling in P2, floor in P3, interior in P0/P1, every cycle | `report.md`, "Bound cells" |
| AC5 | Compute projection and, if needed, the ladder step applied, printed with inputs | `report.md`, "Compute plan" |
| AC6 | Failure rates by arm; any arm > 5% flagged | `report.md`, "Failures" |
| AC7 | Three calibration JSONs and a log with every Table 3 check | `data/calibration/` |
| AC8 | Rerunning any single replication from its stored state reproduces its estimates rows exactly | `tests/test_loop_smoke.py::test_replay` |

---

## 12. Milestones and issues

| Milestone | Issues | Done when |
|---|---|---|
| M0 Scaffold | repo layout, `pyproject`, CI skeleton, fixtures | CI green on an empty smoke test |
| M1 Data and calibration | `io`, `clean`, `calibrate`, plausibility checks, calibration log | AC7 |
| M2 Mechanism and oracle | `rng`, `dgm`, `oracle`, tests | `test_dgm`, `test_oracle` pass |
| M3 Estimators | M1–M4 with the `Estimator` contract, known-property test | `test_estimators_known_properties` passes |
| M4 Loop and policies | `policies`, `loop`, forecasts, timing, resume | `test_loop_smoke` passes |
| M5 Metrics and decisions | `metrics`, `decisions`, `report` | `test_metrics` passes; report renders on smoke output |
| M6 Pilot run | P0–P5 on the author's machine | AC1–AC6 |
| M7 Sign-off | protocol amendments (if any) logged in `CHANGELOG.md` and P §12; `n_sim`, pass-through, multiplier, and failure rules copied into the chapter Methodology | Author approval |

Each issue references the protocol section it implements. Pull requests that change anything under `configs/` require a `CHANGELOG.md` entry, because those files are the protocol's parameters.

---

## 13. Conventions

- Prices in dollars; log prices natural logs; regret in percentage points; elasticities negative for downward-sloping demand.
- `t` counts weeks from 1 (history) to 156; `cycle = t - 52` for t > 52.
- Store identifiers are the Dominick's `store` numbers; zones are the store-file zone codes.
- No function reads a config file; configs are parsed once in `scripts/` and passed down as dataclasses.
- Logging via `logging` at INFO; one line per replication start and finish with the elapsed time.

---

## 14. Open items for the author before M1

1. Confirm the store file name and zone column as distributed, and whether stores without a zone are to be dropped (P §3.2 step 3) or assigned the "no zone" tier.
2. Confirm Easter dates for 1990–1997 for the Lent indicator (committed in `week_decode.csv`).
3. Confirm the cross-price coefficient (+0.2) and competing-index persistence (0.8), which are design constants rather than calibrated values.
4. Confirm the 150 core-hour budget and the machine on which the pilot will run.
