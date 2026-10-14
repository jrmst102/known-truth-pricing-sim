# Known-truth pricing protocol

Protocol version: 1.1 · Supersedes 1.0 · Date: October 14, 2026 · Author: Jose Mendoza

Approval status: pending author signature
Author signature:
Scientific stages S2–S4 require a signed protocol and a clean committed worktree.

## Authoritative baseline

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


## Amendments

| ID | Protocol v1.0 section | v1.0 text (summary) | v1.1 text (summary) | Reason | Motivating evidence |
|---|---|---|---|---|---|
| A1 | §8, Table 5; chapter Methodology "Limits" | 27 core cells in the tuna environment; one η level per environment with a cross-check | 81 cells: η crossed with every environment | Separates the elasticity effect from the environment effect in every cell rather than in one check | Review of commit `e216e16` |
| A2 | §4, Table 2; §5 | ρξ and the variance split calibrated from residual autocovariances | ρξ = 0.5 and equal split by design; empirical values reported as diagnostics | Empirical autocovariances were replacing a design assumption and varied by environment | Same |
| A3 | §5, Table 4 | Chainwide AR(1) cost series entering the legacy price | Store-week independent cost shifter entering every deployed price once | Instrument relevance must not depend on φ or on promotion timing | Same; audit of `dgm.py:51` and `loop.py:143` |
| A4 | §5 (D_s) | Model stores drawn across all stores | Drawn within price zones; realized share recorded | Balance across zones; auditability | Same |
| A5 | §7 | Reliability: recommended-price regret ≤ 2% in the final 26 cycles and no sign change | Deployed weekly regret ≤ 0.02 and finite negative η̂ in every one of the final 26 cycles; criteria also reported separately; missing estimates fail | Deployed prices are what the retailer experiences; the joint criterion is what the chapter claims | Same |
| A6 | §9.3 | \|η̂\| > 10 counted as failure; previous recommendation carried forward | Extreme estimates and positive slopes retained with flags; legacy fallback only when predictions are unavailable; explicit denominators; smearing retransformation | Discarding extreme estimates hides the failure the chapter studies | Same |
| A7 | §6.1 (M4) | Five-fold cross-fitting, unspecified fold structure | Within-store transformation, store-grouped folds, cluster-robust variance, cross-fitted predictions; coverage withheld until validated | Row-level shuffling with store and serial dependence invalidates nominal coverage | Same |


| A1-window | §3 calibration eligibility | Full tuna calendar span fails 90% UPC coverage | Propose weeks 1–341, 67 zoned stores, unchanged 90% threshold | Retain empirical tuna and the 81-cell grid | Full and window coverage audits; author acceptance pending |

## Implementation corrections (no design change)

- C1: project every deployed price after all adjustments; nearest ties go downward.
- C2: cost enters once for every store through deployment.
- C3: record realized adoption and the assignment vector.
- C4: apply deployment constraints to initial history, with exploration disabled.
- C5: latent sales in core; fixed reference-price capacity and a censored oracle in the extension.
- C6: revenue-weighted fractional regret; cumulative dollar loss and normalized cumulative regret.
- C7: mean valid focal-UPC unit price, including promotions; explicit coverage denominators.
- C8: resolve environments per cell and read every effective configuration setting.

## Operational definitions

The sign convention is beta < 0 for downward-sloping demand; eta_hat = beta * p_bar.
This equals -b_hat * p_bar when b = -beta. Checkpoints are cycles 26, 52, 104,
at absolute weeks 78, 104, 156. Stores missing price zones are excluded.
The committed week_decode.csv Easter dates for 1990–1997 are authoritative.

Every estimator retransforms predicted log demand as exp(y_hat) * S, where
S = mean(exp(training residuals)) (Duan smearing). DML uses out-of-fold
residuals. This constant does not change the ladder argmax.
DML demeans outcome, centered price, and instrument within store over the expanding
training window. Controls and week of year exclude store identifiers and lagged sales.
Five store-grouped folds feed DoubleML partialling-out and store-cluster variance.
New-row nuisances are averaged across folds; store means restore forecast levels.
Cluster variance does not model serial dynamics. Coverage remains withheld until the
200-draw inference test passes and the author sets inference_validated: true.

Censored capacity is 1.5 times expected latent demand at the reference price using
current observed controls, integrated over shocks. The oracle observes controls and
capacity, never realized latent state; all regret uses the same expected-sales mechanism.

Reference arms recommend the oracle or legacy price chainwide and receive the common
cost/manager adjustments. Estimator arms use model recommendations only for assigned
stores; exploration is restricted to those stores. Assignment is shared across arms.
Recommended regret audits recommendations separately from deployed mixture prices.
When predictions are unavailable, model stores use the unprojected legacy base before
the single final projection. Extreme and positive finite estimates remain available.

Reliability requires all final 26 deployed weekly regrets <= 0.02 and a finite negative
eta_hat in every cycle. Missing estimates fail; incomplete horizons cannot qualify.
Report the regret and sign criteria separately. Empty model-store sets have null regret.

## Run sequence and approval

S1 validation uses synthetic fixtures or explicitly labeled mechanical checks of retained
calibrations. S2 diagnostic requires 104 cycles, one replication of each core cell and
five total replications of med/pos/0.5 per environment. S3 requires 100 replications per
core cell. S4 requires the S3 decision and unchanged scientific settings. SeedSequence
children 0, 1, 2, 3 belong to validation, diagnostic, pilot and main respectively.

N_required is the maximum ceil((SD/target)^2) over every core estimator-policy arm for
terminal elasticity error (target 0.02) and normalized cumulative deployed regret
(target 0.0025). Paired regret comparisons use target 0.0025. The explicit computational
floor is 1 and cap is 2000; budget is 150 core hours pending author machine/budget review.
Caps and achieved precision are reported, never silently substituted.

## Pending author acceptance

Author review covers A1–A7, the tuna decision, the sign convention, checkpoints,
unzoned-store exclusion, Easter dates, and S2–S4 compute budget/machine. Implementation
of this document does not constitute a signature. Precision pilot and main experiment
must wait for acceptance of Deliverables 1 and 2.

## Eligibility amendment: tuna window (A1 implementation decision)

The unchanged full-span audit reproduces best coverage approximately 0.836 across 399 weeks
and 66 retained stores. No denominator/join correction was indicated by the audit.
Step 2 selects weeks 1–341 with 67 zoned stores, retaining the 90% UPC threshold.
The focal UPC is 8660000033 with 20,765 rows; the denominator is 67 × 341 = 22,847,
so coverage is 0.908872. Its observed rows end at week 331; missing weeks remain in
the denominator. Competing UPCs also pass coverage; longer screened candidates
failed the competing-index requirement. Selection was based on coverage, not fit.

The candidate search ranks contiguous spans using the full-file retained store set,
then reruns all cleaning rules and store retention within each candidate. This is
not a proof of the global longest window when the retained store set can change.
See `data/calibration/window_evaluation_tna.json` for rejected candidates and
`coverage_audit_tna_window.json` for the adopted-window counts. This proposed
window retains three environments and 81 core cells; author acceptance is pending.
