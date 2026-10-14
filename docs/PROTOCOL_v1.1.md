# Known-Truth Pricing Protocol

Protocol version: 1.1 · Supersedes 1.0 · Date: 2026-10-14 · Author: Jose Mendoza
Author approval: PENDING
Deliverable 1 acceptance: PENDING
Deliverable 2 acceptance: PENDING

This is an implementation draft for author review. Scientific stages are blocked
until the author records approval here. Synthetic validation is permitted.
The complete implementation requirements are in [SPEC_v1.1.md](SPEC_v1.1.md).
Where silent, [PILOT_SPEC.md](../PILOT_SPEC.md) remains in force.

## Baseline

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

## Amendments (pending author approval)

| ID | Protocol v1.0 section | v1.0 text (summary) | v1.1 text (summary) | Reason | Motivating evidence |
|---|---|---|---|---|---|
| A1 | §8, Table 5; chapter Methodology "Limits" | 27 core cells in the tuna environment; one η level per environment with a cross-check | 81 cells: η crossed with every environment | Separates the elasticity effect from the environment effect in every cell rather than in one check | Review of commit `e216e16` |
| A2 | §4, Table 2; §5 | ρξ and the variance split calibrated from residual autocovariances | ρξ = 0.5 and equal split by design; empirical values reported as diagnostics | Empirical autocovariances were replacing a design assumption and varied by environment | Same |
| A3 | §5, Table 4 | Chainwide AR(1) cost series entering the legacy price | Store-week independent cost shifter entering every deployed price once | Instrument relevance must not depend on φ or on promotion timing | Same; audit of `dgm.py:51` and `loop.py:143` |
| A4 | §5 (D_s) | Model stores drawn across all stores | Drawn within price zones; realized share recorded | Balance across zones; auditability | Same |
| A5 | §7 | Reliability: recommended-price regret ≤ 2% in the final 26 cycles and no sign change | Deployed weekly regret ≤ 0.02 and finite negative η̂ in every one of the final 26 cycles; criteria also reported separately; missing estimates fail | Deployed prices are what the retailer experiences; the joint criterion is what the chapter claims | Same |
| A6 | §9.3 | \|η̂\| > 10 counted as failure; previous recommendation carried forward | Extreme estimates and positive slopes retained with flags; legacy fallback only when predictions are unavailable; explicit denominators; smearing retransformation | Discarding extreme estimates hides the failure the chapter studies | Same |
| A7 | §6.1 (M4) | Five-fold cross-fitting, unspecified fold structure | Within-store transformation, store-grouped folds, cluster-robust variance, cross-fitted predictions; coverage withheld until validated | Row-level shuffling with store and serial dependence invalidates nominal coverage | Same |

## Implementation corrections (no design change)

- C1. Project every deployed price onto the ladder, after every adjustment
- C2. Apply the cost shifter to all stores, exactly once, through the deployment function
- C3 / A4. Assign model adoption within zones and record it
- C4. Apply the same constraints to the initial history
- C5. Make stockouts a separate extension with its own oracle
- C6 / A5. Replace the regret calculations with revenue-weighted measures
- C7. Reference price and calibration denominators
- C8. Configuration hygiene

## Operational definitions

- Eta is beta * p_bar, where beta is the coefficient of price - p_bar in log demand.
- Checkpoints: cycles 26, 52, 104, absolute weeks 78, 104, 156.
- Every arm and initial history uses final projection with downward ties.
- Capacity uses current observed controls and reference price, without realized shocks.
- Regret fractions use expected-dollar revenue sums, including store effects, controls,
  and the lognormal expectation. Model-only quantities are null at phi = 0.
- Reliable means deployed weekly regret <= 0.02 AND finite negative eta in every one
  of the final 26 cycles. Missing estimates fail; short runs have null reliability.
- Every estimator retransforms log predictions using Duan's factor, mean(exp(training
  residuals)); DML uses out-of-fold residuals. Greedy prices use the same factor.
- M4 first demeans outcome, treatment and instrument by store, uses five store-grouped
  folds and DoubleMLClusterData. No separate temporal/HAC dependence model is fitted.
  Training predictions are out of fold; new predictions average the fold learners.
  Coverage is withheld until 200-draw inference validation and explicit author opt-in.
- Stage streams are the four children of the master SeedSequence, ordered validation,
  diagnostic, pilot, main. Cells share the same replication streams within a stage.
- S2: one replication per core cell plus five additional base-cell replications.
  S3: 100 replications per cell. S4 uses the accepted S3 decision, fresh seeds and
  frozen scientific settings. No S2/S3/S4 run is authorized by this implementation draft.
- Tuna: audit at the unchanged 90% threshold first; investigate denominator or join
  errors before proposing a window. A window needs >=40 zoned stores and >=156 weeks.
  If no defensible window exists, propose two environments (54 cells), with author
  approval and chapter amendment. No synthetic substitute for empirical calibration.
- Benchmark elasticity slopes are descriptive review flags, not exclusion criteria.
  Units, log base, promotions and competitor construction remain under investigation.
- Stores without a price zone stay excluded. The committed calendar uses factual
  Easter dates for 1990–1997 rather than conflicting codebook special-event labels.
- Outputs from synthetic-smoke and synthetic-demo are development records, never findings.

## Pending author decisions

Approve A1–A7; approve the tuna sample decision; confirm sign convention, checkpoint
interpretation, zoned-store restriction and calendar; approve the S2–S4 machine and
compute budget (configured draft: 150 hours, cap 2000 replications, no positive floor).
The author must record their own name/date with approval. Implementation does not sign
on the author's behalf.
