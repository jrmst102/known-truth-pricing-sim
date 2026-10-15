# Exploratory known-truth pricing experiment

## Methodology

The completed study is a six-cell exploratory Monte Carlo experiment calibrated to snack crackers, canned tuna, and bathroom tissue. The cells cross those environments with κ = 0 and +0.05 while fixing the true reference-price elasticity at −1.06 and model adoption at 0.5. Each cell contains 30 independent replications, 52 initial-history weeks, and 104 pricing cycles. The eight arms are M1 OLS, M2 GBM, and M3 2SLS under greedy and greedy-with-exploration pricing, plus legacy and direct-oracle references. GBM uses the accepted 500-tree configuration. DML and the M3 control-function variant are retained only as supplementary Deliverable 2 evidence.

Within a replication, all arms use the same initial history and exogenous draws. Each method-policy arm then maintains its own evolving data history. Production seeds are distinct from diagnostic and timing seeds. Failures remain in the dataset and deploy legacy fallback prices when predictions are unavailable. Monte Carlo standard errors use independent replication-level quantities. Policy-difference uncertainty uses the 30 paired exploration-minus-greedy differences for the same replication seeds. Common-grid forecast RMSE evaluates predictions over the feasible price ladder and is reported separately from error at deployed prices.

The originally planned 81-cell precision pilot and main experiment are deferred because measured computation exceeded the retained budget. The present 30-replication design provides exploratory evidence with uncertainty; it does not claim the original Monte Carlo precision targets.

## Findings

### Calibration and implementation checks

All six cells contain 30 completed replications and eight arms over 104 cycles. The saved-run audit acceptance record is `{"AC-A6": true, "AC-A7": null, "AC-C1": true, "AC-C2": true, "AC-C3": true, "AC-C5": true, "AC-C6": true, "run_complete": true}`. It verifies constrained cycle prices, uncensored core demand, adoption assignments, revenue identities, and direct-oracle zero regret. The run used commit `161b1f8c2d7e2fac281f9f7e2665e85f4d6ef665` and calibration identifiers recorded in the manifest.

Each retained calibration contains 67 stores. The reference prices differ sharply across categories (snack crackers: 67 stores, p̄=2.694; canned tuna: 67 stores, p̄=0.793; bathroom tissue: 67 stores, p̄=0.571), so revenue loss and demand-scale forecast RMSE should be compared within environment. The failure record contains 0 rows: no estimator failure or fallback occurred in the 149,760 saved arm-cycle records, and the empty file retains the required schema.

### Elasticity recovery and prediction accuracy

Table 1 reports terminal elasticity bias and RMSE, common-grid and deployed-price forecast RMSE, positive-slope frequency, failures, and fallbacks for every environment, endogeneity condition, estimator, and policy. Figure 1 shows full elasticity trajectories against the known value −1.06. All uncertainty is calculated across 30 independent replications rather than repeated weeks.

Without endogeneity, M1 recovered the elasticity most closely on average across environments. Positive endogeneity produced severe positive bias and frequent sign reversals for M1, while M3 was materially more stable. M2 had larger terminal dispersion than M1 under κ=0 and remained variable under κ=+0.05. Averaged across environments and the two policies, the numerical summaries were: κ=+0.00 M1: bias -0.010, RMSE 0.079, positive-slope frequency 0.0%; κ=+0.00 M2: bias -0.944, RMSE 2.070, positive-slope frequency 6.7%; κ=+0.00 M3: bias 0.451, RMSE 0.897, positive-slope frequency 23.7%; κ=+0.05 M1: bias 1.377, RMSE 1.385, positive-slope frequency 93.8%; κ=+0.05 M2: bias 0.314, RMSE 1.929, positive-slope frequency 31.9%; κ=+0.05 M3: bias 0.348, RMSE 0.705, positive-slope frequency 19.7%. Common-grid RMSE and deployed-price RMSE are kept in separate columns because a policy's deployed-price errors reflect its endogenous price path.

### Pricing losses and exploration

Table 2 reports normalized cumulative deployed regret, cumulative revenue loss, decision reliability, and paired exploration-minus-greedy differences. Figure 2 shows cumulative normalized deployed regret over all 104 cycles. Lower regret is better; a negative paired difference favors exploration. The lowest mean model-arm regret in each cell was: snack crackers, κ=+0.00: M1 greedy (0.005); snack crackers, κ=+0.05: M3 greedy_rps (0.012); canned tuna, κ=+0.00: M1 greedy (0.008); canned tuna, κ=+0.05: M3 greedy_rps (0.015); bathroom tissue, κ=+0.00: M1 greedy_rps (0.004); bathroom tissue, κ=+0.05: M3 greedy_rps (0.008).

Exploration effects were small relative to total regret: the 18 estimator-cell paired mean changes ranged from -0.000277 to 0.000233 in normalized cumulative regret. Exploration tended to reduce regret for M3 and in the endogenous cells, but it was not uniformly beneficial. The paired Monte Carlo standard errors in Table 2, rather than unpaired policy-arm errors, govern those comparisons.

### Differences across calibrated environments

Results are kept separate by environment and κ in both tables and figures. The best no-endogeneity arm was M1 in all three environments. Under κ=+0.05, M3 with exploration had the lowest mean regret in all three, but decision reliability varied: snack crackers 86.7%, canned tuna 26.7%, bathroom tissue 83.3%. Forecast RMSE levels were largest for bathroom tissue and smallest for snack crackers, consistent with different calibrated demand scales; the within-environment estimator comparisons are the interpretable ones.

## Discussion

The experiment compares estimation, prediction, and pricing outcomes under one moderate elasticity, one adoption share, two endogeneity conditions, and a two-year pricing horizon. The paired design gives a direct estimate of the incremental effect of exploration for each estimator while holding the replication's exogenous draws fixed. Common-grid prediction error supports comparisons of predictive recovery across the feasible decision set; deployed-price error describes the endogenous data path actually generated by each policy.

## Limitations

The evidence is exploratory. Thirty replications quantify Monte Carlo uncertainty but do not satisfy the original precision targets. The study does not identify behavior at elasticities −0.8 or −2.5, adoption shares 0 or 1, negative endogeneity, alternative horizons, censored demand, or the full 81-cell interaction structure. DML confidence-interval coverage remains withheld. Repeated store-weeks are not counted as independent replications.

## Reproducibility appendix

The production manifest, configuration hashes, calibration identifiers, seed states, replication checkpoints, failure records, execution history, and audit results are stored with the run at `outputs/exploratory/six-cell-20261015`. Timing artifacts are separate under `outputs/timing/exploratory-six-cell`. Deliverable 1 and 2 acceptance dates, the cloud-to-local transfer, and checkpoint verification remain in `docs/DELIVERABLE_2.md` and are excluded from the substantive Findings.

The reproducible chapter outputs are `table1_estimation_prediction.csv`, `table2_pricing_performance.csv`, `figure1_elasticity_trajectories.png`, and `figure2_cumulative_regret.png`.
