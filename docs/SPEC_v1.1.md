# Implementation Specification v1.1

**Repository:** `jrmst102/known-truth-pricing-sim` · **Baseline commit:** `e216e16` (2026-10-13, "Implement known-truth pricing simulation pilot")
**Supersedes:** `docs/PILOT_SPEC.md` (v1.0) for every item listed here; v1.0 remains in force where this document is silent.
**Companion:** `docs/PROTOCOL_v1.1.md`, to be created from Appendix A of this document and signed off by the author before any scientific run.
**Owner:** Jose Mendoza · **Date:** October 14, 2026 · **Status:** ready for implementation

---

## 0. Why a v1.1 before rerunning

The v1.0 implementation runs end to end, but an audit of commit `e216e16` found that several parts of the code do not implement the methodology as written, and that the methodology itself left choices open that the code resolved silently. Increasing replications now would only measure those inconsistencies more precisely. This specification does three things:

1. Names one authoritative protocol (`docs/PROTOCOL_v1.1.md`) and the baseline settings every config, module, test, and chapter paragraph must agree with.
2. Lists every change as either a **correction** (C) that brings the code into line with Protocol v1.0 and the chapter Methodology, or an **amendment** (A) that changes the design and therefore needs an entry in the protocol's amendments log and in `CHANGELOG.md`. The distinction matters for the chapter: corrections are not reported; amendments are.
3. Fixes the sequence of runs. **Deliverable 1** is the corrected implementation passing the acceptance checks in §10. **Deliverable 2** is the full-horizon diagnostic report. The precision pilot and the main experiment follow and are not started until both deliverables are accepted.

Audit references below use `file:function` and the line numbers of commit `e216e16`.

---

## 1. Authoritative baseline (Protocol v1.1)

The following settings are the baseline for every scientific run. Where a value differs from Protocol v1.0 or from the current code, the "Status" column says so.

| Component | Required specification | Status vs. v1.0 protocol / current code |
|---|---|---|
| Calibration environments | Snack crackers (`sna`), canned tuna (`tna`), bathroom tissue (`tti`), each subject to the documented eligibility audit in §7 | Same as v1.0; `tna` currently blocked |
| Reference price p̄ | **Mean** valid unit price in the retained calibration sample | Code uses the median of non-promotion prices (`calibrate.py:42`) → C7 |
| True elasticity at p̄ | η ∈ {−0.8, −1.06, −2.5}, **crossed with every environment** | v1.0 paired one η level per environment with a cross-check → A1 |
| Endogenous managerial adjustment | κ ∈ {−0.05, 0, +0.05} log-price units per one-SD latent shock | Same |
| Model adoption | φ ∈ {0, 0.5, 1}, assigned once per replication **within price zones**, realized share recorded | Code: unstratified permutation, share not recorded (`rng.py:52`, `loop.py:32`) → C3, A4 |
| Core design | 3 environments × 3 η × 3 κ × 3 φ = **81 scenario cells**, before estimator and policy arms | v1.0: 27 cells in one environment → A1 |
| History and horizon | 52 initial weeks, then 104 pricing cycles; checkpoints at cycles 26, 52, 104 (absolute weeks 78, 104, 156) | Same; checkpoint interpretation confirmed |
| Demand shocks | Latent AR(1) persistence **ρξ = 0.5 by design**; latent-shock and independent-noise variances **each equal to one half of the calibrated residual variance** | v1.0 and code calibrate ρξ and the split from residual autocovariances (`calibrate.py:19–34`) → A2 |
| Feasible prices P | Five-cent ladder inside [0.80 p̄, 1.20 p̄] | Same |
| Core censoring | **Disabled**; observed sales equal latent demand | Code censors always (`loop.py:61–63`) → C5 |
| Exploration | ±0.03 × cycle^(−1/4) in log price, two-point, **model-assigned stores only**, applied before the final projection | Code applies to model stores but never re-projects → C1 |
| Cost shifter | Drawn **independently across stores and weeks**, independent of demand shocks; applied to **all** stores through the common deployment function | Code: one chainwide AR(1) series, applied only through the legacy price (`rng.py:40`, `dgm.py:51`) → A3, C2 |
| Estimators | M1 OLS, M2 GBM, M3 2SLS (with M3_cf stored separately), M4 DML (PLR and PLIV) | Same; M4 inference changes → A7 |
| Policies | Greedy; greedy plus random price shocks; oracle and legacy as reference arms | Same |

Everything in this table is written into `docs/PROTOCOL_v1.1.md` (Appendix A) and mirrored in `configs/`. A test (`tests/test_protocol_consistency.py`, §9) fails if a config value drifts from the protocol table.

---

## 2. Change register

Each change has an ID, a classification, the files it touches, the current behavior found in the audit, the required behavior, and the acceptance check that closes it. Checks are collected in §10.

### C1. Project every deployed price onto the ladder, after every adjustment

- **Files:** `src/ktsim/dgm.py:deployed_log_price` (56–57), `src/ktsim/loop.py` (143–152), `src/ktsim/oracle.py:price_ladder` (4–12), `src/ktsim/policies.py:add_random_price_shock` (dead code, 13–16).
- **Current:** The greedy recommendation is a ladder point, but κ·ξ and δ·u are added afterward and the result is deployed off-ladder. Legacy prices are never projected. The carried-forward initial price p̄ need not be on the ladder.
- **Required:** One deployment function used by every arm:

  `p_st = Π_P { p_base_st × exp(λ z_st + κ v_st + D_s δ_t u_st) }`

  where `p_base_st` is the model recommendation for model-assigned stores and the legacy price otherwise, `Π_P` selects the nearest ladder price and resolves ties **downward**, `z_st` is the cost shifter (A3), `v_st` is the latent demand shock, and `u_st` the two-point exploration draw. Projection is applied **after** all three adjustments, once. Delete `policies.add_random_price_shock` or make `loop.py` call it; no duplicated logic.
- **Check:** every deployed price in `estimates.parquet` and in the history rows is a ladder point (exact float equality against `price_ladder()`); with φ = 0 and δ > 0 the deployed prices are identical to those with δ = 0 under the same seed.

### C2. Apply the cost shifter to all stores, exactly once, through the deployment function

- **Files:** `src/ktsim/dgm.py:legacy_log_price` (51–53), `loop.py:context` (42–52), `loop.py` (143–152).
- **Current:** `pass_through × cost_t` enters the legacy log price only. Model-assigned stores deploy `log(recommendation) + κξ + δu` with no cost term. At φ = 1 the cost instrument has no first stage by construction.
- **Required:** Remove the cost term from `legacy_log_price`; the legacy price is `μ_z + ν_zt + log(1 − d_t)·PROMO_t`. The cost term `λ z_st` enters once, inside the deployment function of C1, for every store. The instrument column exposed to estimators is `z_st` itself (per store-week after A3).
- **Check:** in a non-saturated test case with φ = 1 (an η that keeps the oracle interior, no projection ties), regressing deployed log price on `z_st` gives a coefficient within 10% of λ; the same regression at φ = 0 gives the same coefficient.

### A3. Generate the core cost shifter per store-week

- **Files:** `src/ktsim/rng.py:draw_shocks` (40), `src/ktsim/dgm.py:instruments` (60–70), `configs/dgm_base.yaml`.
- **Current:** one chainwide AR(1) series with `rho 0.80, sd 0.05`, broadcast to all stores.
- **Required:** `cost[s, t] ~ N(0, sd²)` independent across stores and weeks and independent of ω, ε, u. Keep `sd: 0.05`. Keep the chainwide AR(1) generator available under a config switch `cost_shifter.structure: {iid_store_week | chainwide_ar1}` for a later extension; the core uses `iid_store_week`. The other-zone price instrument is retained as an extension-only instrument and is not computed in core runs.
- **Why an amendment:** Protocol v1.0 §5 specified a chainwide AR(1) cost series. The change makes the instrument's first stage a design quantity rather than a function of promotion and zone drift.
- **Check:** `test_dgm.py` asserts zero correlation (|r| < 0.02 on 10⁵ draws) between `cost` and each of ω, ε, u, and between `cost[s, t]` and `cost[s, t−1]`.

### C3 / A4. Assign model adoption within zones and record it

- **Files:** `src/ktsim/rng.py` (52), `src/ktsim/loop.py` (32–33, 189–191), output schema.
- **Current:** uniform random permutation over all stores, first `int(φ × n)` stores become model stores; share truncated; assignment not written to outputs.
- **Required:** stratified assignment: within each zone, draw `round(φ × n_z)` stores at random; if rounding leaves the chainwide share more than one store away from φ, adjust in the largest zone. Draw once per replication and share across arms (unchanged). Write `model_share_realized` and `n_model_stores` to every estimates row, and the full assignment vector to `states.parquet`.
- **Classification:** recording the share is a correction (v1.0 §6.3 required the assignment to be recorded); zone stratification is an amendment (v1.0 drew across all stores).
- **Check:** for φ = 0.5 and the `tti` store set, every zone's realized share is within one store of 0.5 and the chainwide share equals `round(0.5 × n)/n`.

### C4. Apply the same constraints to the initial history

- **Files:** `src/ktsim/loop.py` (74–79).
- **Current:** history prices are `exp(legacy + κξ)` for all stores: no cost term, no projection, no feasible band, and sales are drawn with censoring on.
- **Required:** history weeks use the C1 deployment function with `D_s = 0` for every store (so no exploration), the cost term included, projection applied, and censoring governed by the scenario flag (C5). The pre-history recommendation placeholder becomes `Π_P(p̄)`.
- **Check:** history rows satisfy the same ladder assertion as cycle rows; with censoring off, no history row is flagged censored.

### C5. Make stockouts a separate extension with its own oracle

- **Files:** `src/ktsim/dgm.py:draw_sales` (43–48), `src/ktsim/loop.py:observed` (61–63), `src/ktsim/oracle.py`, `configs/dgm_base.yaml`, `configs/pilot_cells.yaml`.
- **Current:** `censor=True` always; capacity = `1.5 × exp(expected_log_demand)` at the **deployed** price, computed contemporaneously; the oracle ignores censoring.
- **Required:**
  - Scenario flag `sales_process: {latent | censored}`; core cells use `latent` (observed sales equal latent demand).
  - In the `censored` extension, capacity is set **before price selection** as `1.5 × E[q_st | x_st, p̄]`, where the expectation is over the latent shock and noise under the true mechanism at the **reference price** (so `exp(α_s + γ′x_st + (σξ² + σε²)/2)` with b-term zero at p̄). Capacity is fixed while candidate prices are evaluated and does not depend on the deployed price. Document in the module docstring that the expectation uses the current week's observed controls and no shock information.
  - A censored-sales oracle: for each store-week, choose the ladder price maximizing `p × E[min(q_st(p), cap_st)]`, with the expectation over the lognormal shock (ξ + ε) computed in closed form (partial expectation of a lognormal) and verified against Monte Carlo integration in a test. Document that this oracle observes the controls and the capacity, not the realized latent state.
  - Regret in the censored extension uses censored expected revenue for both oracle and deployed prices.
- **Check:** closed-form censored expected revenue matches a 10⁶-draw Monte Carlo estimate within 0.1% on three (p, cap) pairs; in core cells `censored_share` is exactly 0 and the censored oracle is never invoked.

### C6 / A5. Replace the regret calculations with revenue-weighted measures

- **Files:** `src/ktsim/oracle.py:regret` (29–32), `src/ktsim/loop.py` (192–193), `src/ktsim/metrics.py` (94–117).
- **Current:** regret is `100 × (best − achieved)/best` with revenue `p·exp(−b(p−p̄))` that omits α_s, controls, and shocks; averaged with an unweighted mean over all stores; cumulative regret sums per-cycle percentage points; decision reliability is "all final-26 recommended-price regrets ≤ 2.0 pp" with no elasticity condition and no treatment of missing estimates.
- **Required:** for every store-week retain `R_star_st` (expected revenue at the oracle price), `R_dep_st` (expected revenue at the deployed price), and `R_rec_st` (expected revenue at the recommended price), all under the true mechanism with the week's controls and the expectation over shocks (so α_s and γ′x_st are included; the common lognormal factor is included so that the revenue level is right, not just the ratio). Then:
  - Weekly regret_t = Σ_s (R_star_st − R_dep_st) ÷ Σ_s R_star_st
  - Cumulative loss = Σ_t Σ_s (R_star_st − R_dep_st)
  - Normalized cumulative regret = Cumulative loss ÷ Σ_t Σ_s R_star_st
  - The same three quantities on recommended prices (`_rec`), and each of the six on two store sets: all stores and model-assigned stores (`_model`). For φ = 0 the model set is empty and the `_model` columns are null, not zero.
  - Store ratios as **fractions**; convert to percentages only in `report.py`. Never sum weekly ratios and never average store-level ratios without revenue weights.
  - **Decision reliability** (A5): a replication is reliable if, in **every** one of the final 26 cycles, weekly deployed regret on all stores ≤ 0.02 **and** the cycle's `eta_hat` is finite and < 0. Report the two criteria separately as well (`reliable_regret`, `reliable_sign`) and the joint (`reliable`). A missing `eta_hat` fails the sign criterion and therefore the joint criterion.
- **Why an amendment:** Protocol v1.0 §7 defined reliability on recommended-price regret and "no sign change"; v1.1 uses deployed regret and a per-cycle negative-slope condition, and makes the revenue weighting explicit.
- **Check:** a hand-worked three-store, two-week example with unequal store revenues (fixture in `tests/fixtures/regret_example.json`) matches to 1e−12; deploying the oracle price directly with κ = 0, δ = 0, λ = 0 yields regret exactly 0 in every store-week; with κ ≠ 0 the oracle-recommendation arm has non-negative deployed regret and zero recommended regret.

### C7. Reference price and calibration denominators

- **Files:** `src/ktsim/calibrate.py` (42), `src/ktsim/clean.py` (49–69), `data/calibration/`.
- **Current:** p̄ = median of non-promotion unit price. Store coverage denominator = calendar span of the category file; UPC coverage denominator = retained stores × calendar span.
- **Required:** p̄ = mean valid unit price over retained store-weeks of the focal UPC (all weeks, promotion weeks included), as the protocol states. Keep the 90% UPC coverage threshold. Make both denominators explicit in the log: the calendar span used, the week range, the number of retained stores, and the count of focal-UPC rows; add a `coverage_audit.json` per category listing, for the top ten UPCs by volume, the rows present, the expected rows, and the coverage ratio.
- **Check:** `test_clean.py` reproduces the audit numbers on the fixture; `calibration_sna.json` and `calibration_tti.json` regenerate with p̄ equal to the mean (values recorded in `CHANGELOG.md`).

### A2. Shock persistence and variance split by design

- **Files:** `src/ktsim/calibrate.py:residual_components` (19–34), `src/ktsim/rng.py:latent_demand` (56–60), `configs/dgm_base.yaml`, `configs/calibration.yaml`.
- **Current:** ρξ, σξ², σε² estimated from residual autocovariances with clipping and fallbacks; used directly by the mechanism.
- **Required:** calibration still computes and **reports** the residual variance and the empirical autocovariance quantities (they stay in the JSON as `diagnostics`), but the mechanism reads `rho_xi: 0.5` and `xi_share: 0.5` from `configs/dgm_base.yaml`: σξ² = 0.5 × resid_var, σε² = 0.5 × resid_var. The empirical values must not silently replace the design values; a config switch `shock_split: {design | empirical}` exists for a later sensitivity, with `design` the core.
- **Check:** `test_dgm.py` asserts that the simulated ξ has lag-1 autocorrelation 0.5 ± 0.02 and variance 0.5 × resid_var ± 2% on a long series.

### A6. Preserve estimator failures and uncertainty

- **Files:** `src/ktsim/estimators/base.py:finalize` (48–64), `loop.py` (99–137, 187), all four estimator files, `metrics.py` (68–92).
- **Current:** `|eta_hat| > 10` is rejected as a failure (`abs_eta_gt_10`), the estimate is discarded, and the previous recommendation is carried forward; a failed fit still produces regret rows that enter all comparisons without a flag; coverage and bias denominators are converged-only; log predictions are retransformed by `exp()` with no correction.
- **Required:**
  - Replace the rejection with flags. `Estimate` gains four independent boolean fields: `numerical_failure` (exception or non-finite estimate), `predictions_unavailable` (no usable `predict`), `extreme_estimate` (finite and |η̂| > 10), `positive_slope` (finite and η̂ > 0). Finite extreme estimates and positive slopes are **retained** in `eta_hat` and used by the policy.
  - **Fallback rule:** when `predictions_unavailable` is true for a model-assigned store, the base price for that store-week is the **legacy price**, then the common deployment function (C1) applies. Record `fallback_used` per store-week and per cycle. Fallback revenue stays in every policy comparison; the report prints the fallback rate next to each regret figure.
  - **Denominators:** every summary row in `performance.csv` carries `n_total`, `n_estimated` (finite `eta_hat`), and `n_with_interval`. Bias, SE, and RMSE are computed on `n_estimated` and labeled so; coverage on `n_with_interval`; the report prints both counts with the estimate.
  - **Retransformation:** document and implement one rule for all estimators: predicted demand = `exp(ŷ) × S`, where `S` is Duan's smearing factor, the mean of `exp(r̂)` over the training residuals of that fit. Because `S` is a constant multiplier within a fit, the greedy argmax over the ladder is unchanged; forecasts and expected-revenue reporting change. Write the rule in each estimator's docstring and in `docs/PROTOCOL_v1.1.md`.
- **Why an amendment:** Protocol v1.0 §9.3 defined |η̂| > 10 as a failure and prescribed carry-forward; v1.1 retains the estimate and uses a legacy fallback only when no prediction exists.
- **Check:** a planted estimate of −12 is retained with `extreme_estimate = True` and produces a recommendation; a planted `predict = None` produces the legacy base price for model stores and `fallback_used = True`; `performance.csv` rows show `n_estimated ≤ n_total` and `n_with_interval ≤ n_estimated`; the smearing factor equals 1 within 1e−12 when residuals are all zero.

### A7. Dependence-aware DML and withheld coverage claims

- **Files:** `src/ktsim/estimators/dml.py` (15–50), `configs/estimators.yaml`.
- **Current:** `KFold(shuffle=True)` over store-week rows; nuisances re-fit on the full sample for prediction; doubleml asymptotic SEs; PLIV first-stage F obtained by re-running the IV estimator.
- **Required:** a specified procedure, not a fold-splitter swap:
  1. **Within-store transformation first.** Demean `log_q`, `price − p̄`, and (for PLIV) `z` by store over the training window, so store effects are removed before any learner sees the data; drop the store identifier from the nuisance feature set.
  2. **Folds grouped by store.** `GroupKFold` with store as the group, 5 folds, so every week of a store is held out together. Record the fold assignment.
  3. **Training periods.** Nuisance learners use the controls plus week-of-year; no lagged sales; the same expanding window as the other estimators.
  4. **Score.** doubleml `partialling out` for PLR and PLIV, unchanged, on the transformed data.
  5. **Variance.** Cluster-robust by store, through `DoubleMLClusterData` with `cluster_cols = store`. Serial dependence within store is not addressed by this estimator; say so in the docstring.
  6. **Prediction.** Use the cross-fitted nuisance predictions (out-of-fold for training rows; fold-averaged for new rows), not separate full-sample fits.
  7. **First-stage strength** for PLIV is computed from the transformed first stage inside the module, not by re-running M3.
  - **Reporting rule:** until the validation test below passes, M4 rows in `performance.csv` carry `coverage = null` and `coverage_status = "withheld: inference not validated"`. M4 point estimates, bias, Monte Carlo SEs across replications, and policy comparisons are reported normally.
  - **Validation test** (`tests/test_dml_inference.py`, marked `slow`): synthetic panel with store effects, AR(1) latent shock at ρ = 0.5, exogenous price; 200 independent draws; the 95% interval covers the true slope in at least 90% and at most 99% of draws. Passing this test lifts the withholding, by a config flag the author sets, not automatically.
- **Check:** the fold assignment never splits a store across folds; nuisance features contain no store column; `coverage_status` appears on every M4 row of a report generated before the flag is set.

### C8. Configuration hygiene

- **Files:** `configs/*.yaml`, `src/ktsim/cli.py` (120–151, 201), `src/ktsim/loop.py` (24, 31).
- **Current:** `environment: tuna` is not read and the calibration path is hardcoded to `calibration_tna.json`; `rho_m` cannot be set from config; `exploration.delta_levels`, `two_point`, `rho_m_levels`, `phi_levels`, `M3_iv.variants`, `M3_iv.report_first_stage_F`, `M4_dml.nuisance`, `M4_dml.variants` are unread; P1's `policies` list is overridden by δ; the n_sim targets, floor, and cap are function defaults; reliability threshold and window are hardcoded.
- **Required:** every key in `configs/` is read or deleted. Cells name their `environment` explicitly and the CLI resolves `calibration_<env>.json` from it. `rho_m`, `sales_process`, `cost_shifter.structure`, `shock_split`, reliability `tau` and `window`, and the n_sim `targets`, `floor`, and `cap` live in config. Policies are listed per cell; δ is a policy parameter, not a cell factor.
- **Check:** `tests/test_protocol_consistency.py` parses every YAML key and asserts it is referenced in `src/`; a run with `environment: sna` loads `calibration_sna.json`.

---

## 3. Design-grid and run-stage definitions

### 3.1 Scenario cells

`configs/scenarios.yaml` replaces `pilot_cells.yaml` for scientific runs and defines the 81 core cells as the product of `environment ∈ {sna, tna, tti}`, `eta ∈ {low, med, high}`, `kappa ∈ {neg, none, pos}`, `phi ∈ {0, 0.5, 1}`. Arms are the product of estimators `{M1, M2, M3, M4_plr, M4_pliv}` (M3_cf stored alongside M3) and policies `{greedy, greedy_rps}`; `oracle` and `legacy` run as reference arms in every cell at low cost. Extensions (censored sales, weak instrument, invalid other-zone instrument, empirical shock split, chainwide cost series) are separate YAML blocks that vary one factor from a named base cell. If §7 reduces the environments to two, the file carries 54 core cells and the chapter Methodology is amended accordingly.

### 3.2 Stages

| Stage | Purpose | Requirement | Output |
|---|---|---|---|
| S1 Mechanical validation | Prove projection, oracle, regret, fallback, and deterministic replay on small synthetic runs | All tests in §9 pass in CI; §10 checks AC-C1 through AC-C8 pass on the synthetic calibration | CI log; `outputs/validation/<run_id>/` |
| S2 Full-horizon diagnostic run | Exercise every estimator and policy for 104 cycles on the retained environments; examine failure flags, instrument relevance, fallback rates, runtime | One replication per core cell on each retained environment, plus 5 replications of the base cell (med, pos, 0.5) per environment; same seed stream across cells | `outputs/diagnostic/<run_id>/report.md` (**Deliverable 2**) |
| S3 Precision pilot | Estimate across-replication SDs of terminal elasticity error and normalized cumulative regret for every arm in the retained core cells | 100 independent replications per core cell and arm; seeds from a dedicated `SeedSequence` child (`stage: pilot`) | `n_required` decision (§3.3); `outputs/pilot/<run_id>/` |
| S4 Main experiment | Frozen settings, fresh replication seeds (`stage: main`), replication count from S3 | No config change after S3 without a protocol amendment and a new `run_id` | `outputs/main/<run_id>/` |

Runs for different stages never share seed streams: `SeedSequence(master_seed).spawn(4)` yields one child per stage, and each stage spawns its replication streams from its child.

### 3.3 Replication count for S4

`decisions.choose_n_required(perf_pilot)` implements

`N_required = max over cells j and measures m of ceil( (s_jm / τ_m)² )`

with `s_jm` the pilot SD across replications of (a) terminal elasticity error `eta_hat − eta` at cycle 104 and (b) normalized cumulative deployed regret (fraction), and targets `τ_elasticity = 0.02`, `τ_regret = 0.0025` (0.25 percentage points). The maximum runs over every retained core cell and every estimator-policy arm. In addition, for each planned paired comparison (M3 vs M1, M4_pliv vs M1, greedy_rps vs greedy within estimator), compute the SD of the within-replication difference and the implied N for a 0.0025 target on the difference; report these alongside. The function returns `N_required`, the cell and arm that bound it, and, when the compute cap prevents the target, the achieved Monte Carlo SE at the cap, printed as a shortfall in the report. There is no silent floor or cap: `configs/decisions.yaml` holds `targets`, `cap`, and `budget_hours`, and the report prints all three with the decision.

---

## 4. Output schema changes

`estimates.parquet` gains: `model_share_realized`, `n_model_stores`, `fallback_used` (share of model stores on fallback in the cycle), `numerical_failure`, `predictions_unavailable`, `extreme_estimate`, `positive_slope`, `R_star_all`, `R_dep_all`, `R_rec_all`, `R_star_model`, `R_dep_model`, `R_rec_model` (sums over the store set, in dollars), `regret_dep_all`, `regret_rec_all`, `regret_dep_model`, `regret_rec_model` (fractions), `smearing_factor`, `sales_process`, `cost_structure`, `shock_split`. It drops `regret_rec`/`regret_dep` in percentage points.

A new `storeweek.parquet` (optional, `--save-storeweek`) holds the store-week revenue triplets and deployed prices for audit of C6.

`performance.csv` gains `n_total`, `n_estimated`, `n_with_interval`, `coverage_status`, and the stage name. Horizon measures: `cum_loss_all`, `norm_cum_regret_all`, `norm_cum_regret_model`, `reliable`, `reliable_regret`, `reliable_sign`, `fallback_rate`, `extreme_rate`, `positive_slope_rate`.

`states.parquet` gains the model-store assignment vector and the DML fold assignment hash.

---

## 5. Provenance of every scientific run

`manifest.json` already records commit, dirty flag, master seed, effective configs, calibration dict, raw-file checksums, environment, and a fingerprint. Add: `protocol_version` (string, must equal the version line in `docs/PROTOCOL_v1.1.md`), `spec_version`, `stage`, `seed_child_index`, `calibration_ids` (SHA-256 of each `calibration_<env>.json` used), `scenario_file_sha256`, and `figures` (list of generated files). A run refuses to start if `protocol_version` in the manifest template differs from the protocol file's header, or if the worktree is dirty. The existing synthetic reports under `outputs/pilot/synthetic-*` are preserved as development records and labeled as such in `README.md`; they are never cited as results.

---

## 6. Report changes (`src/ktsim/report.py`)

The report prints, in order: header (provenance, protocol version, stage); calibration tables with the coverage audit (§7); for each cell and arm, the elasticity table with `n_estimated/n_total` and `n_with_interval` in the row; the regret table with normalized cumulative regret (all and model stores), fallback rate, extreme-estimate rate, and positive-slope rate; the reliability table with the three columns; forecast MAPE and RMSE; the failure table; runtime; and, for S3 only, the `N_required` decision with its bounding cell and the paired-comparison Ns. Percentages appear only here. M4 coverage prints as "withheld" until A7's flag is set.

---

## 7. Calibration resolution (tuna) and the elasticity flags

**Audit before any sample change.** `scripts/audit_coverage.py --category tna` writes `data/calibration/coverage_audit_tna.json` and a Markdown summary with: the calendar span used as the denominator and whether it equals 399 weeks; the number of retained stores after each rule; for the ten highest-volume UPCs, rows present, expected rows (retained stores × span), coverage, and the count of missing store-weeks by cause (store absent that week in the file, UPC absent while the store is present, dropped by OK = 0, dropped by price/qty rule); any duplicate (upc, store, week) rows; and the date alignment of `week` against `week_decode.csv`. The current 83.6% best coverage must be reproduced from these counts before anything else is changed.

**Decision ladder, applied in order and logged in `CHANGELOG.md` and the protocol amendments table:**

1. If the audit finds a denominator, join, or missing-record error, fix it, regenerate, and re-evaluate at the unchanged 90% threshold.
2. If tuna remains ineligible, evaluate a **shorter, explicitly documented calibration window** (for example, the longest contiguous span in which the best UPC reaches 90% coverage), report the window and its length, and use it only if it retains at least 40 zoned stores and at least 156 weeks.
3. If no defensible sample exists, amend the study to **two environments (54 core cells)**, update the chapter Methodology and the compute plan, and record the reason.
4. **Never** substitute a synthetic tuna calibration in a run described as empirically calibrated. The `--synthetic` path remains available for validation runs only and is labeled in every output.

**Elasticity benchmark flags.** The `beta_reference` failures for crackers (−3.16) and tissue (−3.85) are **review flags, not exclusion criteria**: the observational slope is a descriptive diagnostic, and the imposed η defines the known truth. Change `check_plausibility` so that `beta_reference` produces a `flag` rather than a `FAIL`, keep the reported values unchanged, and open an issue to check units (price per unit vs per bundle), the log base, the promotion coding, and the competing-index construction before any interpretation. The flag and the investigation outcome are printed in the calibration section of every report.

---

## 8. Sequence of deliverables

1. **Deliverable 1, corrected implementation.** All items in §2, §3.1, §4, §5, §6, and §8 implemented; §9 tests green; §10 acceptance checks passed on the synthetic calibration and on the retained real environments; `docs/PROTOCOL_v1.1.md` created from Appendix A and signed; `CHANGELOG.md` entry `1.1.0` listing every C and A item with the files touched.
2. **Deliverable 2, full-horizon diagnostic report** (stage S2) on the retained environments, including the tuna audit outcome and the ladder step taken.
3. Stage S3 precision pilot and its `N_required` decision.
4. Stage S4 main experiment; only then is the Findings section drafted.

---

## 9. Tests (new or changed)

| Test | Proves | Closes |
|---|---|---|
| `test_deployment.py::test_ladder_after_adjustments` | every deployed price (history and cycles) is a ladder point; ties resolve downward | C1, C4 |
| `test_deployment.py::test_exploration_inert_at_phi_zero` | identical deployed prices for δ = 0 and δ = 0.03 at φ = 0 under one seed | C1 |
| `test_deployment.py::test_cost_shifter_relevance` | deployed log price responds to `z_st` with coefficient ≈ λ at φ = 0 and φ = 1 | C2 |
| `test_rng.py::test_cost_shifter_independence` | `cost` uncorrelated with ω, ε, u, and with its own lag | A3 |
| `test_rng.py::test_zone_stratified_assignment` | per-zone shares within one store of φ; share recorded | C3, A4 |
| `test_rng.py::test_design_shock_split` | ξ autocorrelation 0.5 and variance half of residual variance | A2 |
| `test_oracle.py::test_censored_expected_revenue` | closed form vs Monte Carlo within 0.1% | C5 |
| `test_metrics.py::test_revenue_weighted_regret_example` | hand-worked fixture to 1e−12; oracle deployment gives zero regret | C6 |
| `test_metrics.py::test_reliability_joint_criterion` | missing `eta_hat` fails the joint criterion; the two criteria reported separately | A5 |
| `test_estimators.py::test_extreme_and_positive_retained` | −12 retained with flag; +0.3 retained with flag | A6 |
| `test_loop.py::test_legacy_fallback` | `predict = None` → legacy base price for model stores, `fallback_used = True`, revenue counted | A6 |
| `test_estimators.py::test_smearing_factor` | factor = mean(exp(residuals)); equals 1 on zero residuals | A6 |
| `test_dml.py::test_grouped_folds_and_features` | no store split across folds; no store column in nuisance features; cluster SE path used | A7 |
| `test_dml_inference.py` (slow, opt-in) | coverage within [0.90, 0.99] on 200 synthetic draws | A7 validation |
| `test_calibrate.py::test_reference_price_mean` | p̄ equals the mean valid unit price | C7 |
| `test_clean.py::test_coverage_audit_numbers` | audit JSON reproduces fixture counts | §7 |
| `test_protocol_consistency.py` | every YAML key is read; config values equal the protocol baseline table | C8, §1 |
| `test_stages.py::test_stage_seed_separation` | pilot and main replication streams never coincide; stage recorded in manifest | §3.2, §5 |

CI runs everything except the two `slow` tests; the full-horizon smoke test remains in the second CI job.

---

## 10. Acceptance checks for Deliverable 1

| ID | Check | Evidence |
|---|---|---|
| AC-C1 | 100% of deployed prices on the ladder in a 2-replication full-horizon synthetic run across all arms; exploration inert at φ = 0 | `outputs/validation/<run_id>/checks.json` |
| AC-C2 | Cost-shifter coefficient on deployed log price within 10% of λ at φ = 0 and φ = 1 in the non-saturated test case | same |
| AC-C3 | Realized adoption share recorded in every row; zone shares within one store of φ | same |
| AC-C5 | Core run: `censored_share = 0` everywhere; extension run: censored oracle validated against Monte Carlo | same |
| AC-C6 | Hand example reproduced; oracle-deployed regret exactly 0; recommended vs deployed and all vs model columns present and distinct | same; `tests/fixtures/regret_example.json` |
| AC-A6 | Extreme and positive-slope estimates retained with flags; fallback rate reported; denominators printed | report section "Failures and denominators" |
| AC-A7 | M4 rows show `coverage_status = withheld`; grouped folds verified | report; test log |
| AC-C7 | Calibration JSONs regenerated with mean p̄; coverage audits committed for all three categories | `data/calibration/` |
| AC-C8 | No unread config keys; environment resolved from the cell | `test_protocol_consistency.py` |
| AC-P | `docs/PROTOCOL_v1.1.md` exists, version line matches `manifest.protocol_version`; `CHANGELOG.md` 1.1.0 lists every C and A item | repository |

---

## 11. Items the author must confirm before Deliverable 1 is accepted

1. The amendments A1–A7 (grid, shock split, cost shifter structure, zone-stratified adoption, reliability definition, failure handling, DML procedure) are approved for `docs/PROTOCOL_v1.1.md`.
2. The decision ladder in §7 for tuna, including the two-environment fallback and its 54-cell consequence for the chapter.
3. The elasticity-sign convention, closing the pending item in `CHANGELOG.md` 0.1.0: the code regresses `log_q` on `price − p̄` with coefficient β (negative for downward-sloping demand) and reports η̂ = β × p̄; the chapter's "η̂ = −b̂ × p̄" uses b = −β. Both are the same number; the spec adopts the code's convention in all documentation.
4. Checkpoints are cycles 26, 52, and 104 (absolute weeks 78, 104, 156).
5. Stores without a zone remain dropped (Protocol v1.0 §3.2 step 3).
6. Easter dates for 1990–1997 as committed in `week_decode.csv`, overriding the codebook's special-event labels where they conflict.
7. The compute budget and machine for S2–S4.

---

## Appendix A. Content for `docs/PROTOCOL_v1.1.md`

The file carries the header `Protocol version: 1.1 · Supersedes 1.0 · Date · Author`, the baseline table from §1 verbatim, and an amendments table with one row per A item:

| ID | Protocol v1.0 section | v1.0 text (summary) | v1.1 text (summary) | Reason | Motivating evidence |
|---|---|---|---|---|---|
| A1 | §8, Table 5; chapter Methodology "Limits" | 27 core cells in the tuna environment; one η level per environment with a cross-check | 81 cells: η crossed with every environment | Separates the elasticity effect from the environment effect in every cell rather than in one check | Review of commit `e216e16` |
| A2 | §4, Table 2; §5 | ρξ and the variance split calibrated from residual autocovariances | ρξ = 0.5 and equal split by design; empirical values reported as diagnostics | Empirical autocovariances were replacing a design assumption and varied by environment | Same |
| A3 | §5, Table 4 | Chainwide AR(1) cost series entering the legacy price | Store-week independent cost shifter entering every deployed price once | Instrument relevance must not depend on φ or on promotion timing | Same; audit of `dgm.py:51` and `loop.py:143` |
| A4 | §5 (D_s) | Model stores drawn across all stores | Drawn within price zones; realized share recorded | Balance across zones; auditability | Same |
| A5 | §7 | Reliability: recommended-price regret ≤ 2% in the final 26 cycles and no sign change | Deployed weekly regret ≤ 0.02 and finite negative η̂ in every one of the final 26 cycles; criteria also reported separately; missing estimates fail | Deployed prices are what the retailer experiences; the joint criterion is what the chapter claims | Same |
| A6 | §9.3 | \|η̂\| > 10 counted as failure; previous recommendation carried forward | Extreme estimates and positive slopes retained with flags; legacy fallback only when predictions are unavailable; explicit denominators; smearing retransformation | Discarding extreme estimates hides the failure the chapter studies | Same |
| A7 | §6.1 (M4) | Five-fold cross-fitting, unspecified fold structure | Within-store transformation, store-grouped folds, cluster-robust variance, cross-fitted predictions; coverage withheld until validated | Row-level shuffling with store and serial dependence invalidates nominal coverage | Same |

Corrections C1–C8 are listed in the protocol under "Implementation corrections (no design change)" with the same one-line summaries as §2, so a reader can see that they do not alter the design.
