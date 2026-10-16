# Exploratory known-truth pricing experiment

## Methodology

The completed study is a six-cell exploratory Monte Carlo experiment calibrated to snack crackers, canned tuna, and bathroom tissue. It crosses these environments with κ = 0 and 0.05, holding the true reference-price elasticity at −1.06 and model adoption at 0.5. Each cell contains 30 independent replications, 52 initial-history weeks, and 104 pricing cycles. Each calibrated environment contains 67 stores. The eight arms are M1 OLS, M2 GBM, and M3 IV (2SLS), each under greedy and greedy-with-exploration pricing, plus legacy and an oracle-recommendation reference. GBM uses the accepted 500-tree configuration. DML and the M3 control-function variant remain supplementary diagnostic evidence and are not part of this experiment.

Within a cell and replication, arms share initial history and exogenous draws, then maintain their own evolving data histories. Production seeds differ from diagnostic and timing seeds. Failures remain in the dataset, with legacy fallback prices used when predictions are unavailable. The original 81-cell precision pilot and main experiment are deferred; this reduced study does not claim their precision targets or factorial coverage.

### Outcome definitions and uncertainty

**Elasticity recovery.** Terminal error is the final-cycle estimate minus −1.06. Bias is its mean across replications; terminal elasticity RMSE is the square root of mean squared terminal error across replications. For GBM, the reported elasticity is a local finite contrast in predicted log demand between prices 1% below and 1% above the reference price, divided by the corresponding log-price difference and averaged over recent observed contexts. It is a local response summary, not a globally constant GBM coefficient. Positive-slope frequency is the share of cycles with an estimate strictly above zero; a zero estimate does not count as positive but also does not meet the negative-sign reliability criterion. Legacy and oracle reference arms do not estimate elasticity, so recovery, estimated-sign outcomes, and joint decision reliability are not applicable to them.

**Forecast accuracy.** Common-grid RMSE evaluates predicted demand against known expected demand at every feasible ladder price using common current observable contexts across arms. Deployed-price RMSE evaluates predictions against realized sales at the prices actually deployed and therefore reflects both the policy's price path and realized demand noise. Within each replication, horizon RMSE is the square root of the mean of the 104 squared weekly RMSE values. Weekly evaluation sets are equally sized. The tables then report the mean and Monte Carlo standard error (MCSE) of these replication-level horizon RMSEs. This definition is used in both Table 1 and `performance.csv`; it is not the arithmetic mean of weekly RMSEs. Demand-scale RMSE levels should be compared within a calibrated environment.

**Pricing performance.** For each replication, normalized cumulative deployed regret is total expected revenue loss relative to the constrained oracle divided by total constrained-oracle expected revenue, summed over all stores and 104 cycles. Thus, it is revenue weighted rather than an unweighted average of weekly regret ratios. Cumulative revenue loss is the numerator of this ratio. CSV regret levels are fractions; the chapter and Figure 2 express levels as percentages and paired regret differences as percentage points. Lower regret is better.

**Reliability.** Model decision reliability is the fraction of replications in which every one of the final 26 cycles has deployed regret at most 2% and a finite, strictly negative estimated elasticity. Regret-only reliability omits the estimated-sign requirement and is reported separately for all arms, including references. Neither measure is an elasticity confidence-interval coverage rate.

**Oracle references.** The constrained oracle benchmark chooses the feasible ladder price maximizing known expected revenue and defines the regret denominator and zero-regret baseline. The simulated oracle-recommendation arm passes its optimal recommendation through the implementation's deployment adjustments, including cost pass-through and the managerial component. Its deployed prices can therefore depart from the optimum and incur positive regret. The saved direct-oracle zero-regret check is a separate controlled validation condition, not evidence that the adjusted oracle arm must have zero deployed regret in every production cell.

**Monte Carlo uncertainty and pairing.** MCSEs are calculated from independent replication-level outcomes, not from repeated store-weeks. A paired comparison subtracts the comparator's outcome from the treatment's outcome within the same cell and replication, then reports the mean difference and its sample standard deviation divided by √30. This applies to exploration versus greedy pricing, fitted-model arms versus legacy, and IV versus OLS under the same pricing policy. A negative paired regret difference favors the first-named arm. Figures show mean ± one MCSE, not 95% confidence intervals. Terminal elasticity RMSE uses a delta-method MCSE. All comparisons are exploratory; no multiple-comparison-adjusted significance claims are made.

## Findings

### Completed runs and implementation checks

All six cells completed 30 replications with eight arms and 104 pricing cycles, yielding 149,760 arm-cycle records. The saved mechanical audit passed all applicable checks, including feasible ladder prices, uncensored core demand, adoption assignments, and revenue identities. No numerical failure or fallback was recorded. These checks support implementation integrity; they do not establish estimator accuracy or economic superiority.

### Elasticity recovery and prediction

Table 1 reports recovery and prediction outcomes separately for each environment, endogeneity condition, estimator, and policy. Figure 1 shows the estimated trajectories against the known reference-price elasticity. Under κ = 0, greedy OLS terminal biases were approximately −0.006, −0.012, and −0.013 for snack crackers, canned tuna, and bathroom tissue, with RMSEs of 0.062, 0.100, and 0.075. OLS therefore recovered the reference elasticity closely in these exogenous cells.

Under κ = 0.05, greedy OLS terminal biases increased to approximately 1.344, 1.241, and 1.549, respectively. Mean terminal estimates consequently became positive despite the negative known elasticity. Corresponding IV biases were approximately 0.254, 0.452, and 0.338. IV substantially reduced OLS bias in these cells, but it did not eliminate it.

GBM's reported local contrast was zero at the terminal cycle in all 30 canned-tuna replications under both endogeneity conditions and both pricing policies. Its terminal bias and RMSE there were consequently 1.06. This result is consistent with locally flat tree predictions over the narrow ±1% interval. It does not establish that GBM learned no price response elsewhere on the feasible ladder.

Prediction accuracy and pricing performance did not yield interchangeable conclusions. For endogenous canned tuna, common-grid RMSE under greedy pricing was 21.016 for OLS and 21.064 for IV, while IV reduced normalized cumulative regret relative to OLS by approximately 0.363 percentage points. These numerically similar RMSE means do not establish formal predictive equivalence. They show why forecast accuracy and decision outcomes must be reported separately.

### Pricing performance and verified paired comparisons

Table 2 reports regret, revenue loss, joint model decision reliability, and regret-only reliability. Table 3 reports all 48 within-cell paired contrasts: six model arms versus legacy and IV versus OLS under each of the two policies in each cell. The selected comparisons below summarize the principal findings; each uses 30 paired replications.

| Environment | κ | Paired contrast | Mean regret difference (percentage points) | Paired MCSE (percentage points) |
|---|---:|---|---:|---:|
| Snack crackers | 0.00 | OLS: greedy minus Legacy | -0.2361 | 0.0202 |
| Canned tuna | 0.00 | OLS: greedy minus Legacy | -0.2820 | 0.0432 |
| Bathroom tissue | 0.00 | OLS: greedy minus Legacy | -0.1697 | 0.0255 |
| Snack crackers | 0.05 | IV: greedy minus OLS: greedy | -0.3977 | 0.0617 |
| Canned tuna | 0.05 | IV: greedy minus OLS: greedy | -0.3628 | 0.0630 |
| Bathroom tissue | 0.05 | IV: greedy minus OLS: greedy | -0.2529 | 0.0439 |
| Snack crackers | 0.05 | IV: exploration minus Legacy | +0.4013 | 0.0633 |
| Canned tuna | 0.05 | IV: exploration minus Legacy | +0.3764 | 0.0664 |
| Bathroom tissue | 0.05 | IV: exploration minus Legacy | +0.1994 | 0.0462 |

Without endogeneity, greedy OLS reduced mean regret relative to legacy in all three environments. Under endogeneity, greedy IV reduced mean regret relative to greedy OLS in every environment. Nevertheless, every fitted-model arm had higher mean regret than legacy in each endogenous cell. IV with exploration had the lowest mean regret among the fitted-model arms there, but this within-model ranking does not make it the best available pricing policy overall.

| Environment, κ = 0.05 | OLS greedy regret (%) | IV exploration regret (%) | Legacy regret (%) | IV exploration joint reliability (%) |
|---|---:|---:|---:|---:|
| Snack crackers | 1.610 | 1.209 | 0.808 | 86.7 |
| Canned tuna | 1.887 | 1.521 | 1.144 | 26.7 |
| Bathroom tissue | 1.099 | 0.844 | 0.645 | 83.3 |

Joint model reliability varied substantially across environments even for the lowest-regret fitted-model arm. The separate regret-only column in Table 2 permits pricing-threshold comparisons with reference policies without treating their stored truth placeholders as estimated elasticities.

### Exploration and environmental variation

Across the 18 estimator-cell comparisons, mean exploration-minus-greedy regret differences ranged from -0.0277 to +0.0233 percentage points. Exploration reduced mean regret in all six IV cells and all nine endogenous estimator-cell comparisons, but it was not uniformly beneficial across the experiment. These effects were small relative to the regret levels. Their precision is given by the paired MCSEs in Table 2; small magnitude should not be confused with an absence of statistical precision.

Results remain stratified by environment and κ. Differences in demand scales, price ladders, and calibration parameters make within-environment comparisons the interpretable basis for estimator and policy assessment. The canned-tuna local GBM result and variation in IV reliability also caution against treating a cross-environment average as a universal ranking.

## Discussion

The exploratory evidence separates three objectives: recovering the known reference-price elasticity, predicting demand, and choosing prices with low revenue loss. OLS performed well in the exogenous cells but became strongly biased under endogeneity. IV improved both elasticity recovery and regret relative to OLS under endogeneity, yet legacy pricing retained lower mean regret than all fitted-model arms in those cells. A more accurate estimator relative to another fitted method therefore did not, in this design, guarantee improvement over the operational reference policy. Exploration produced modest, condition-dependent changes over the 104-cycle horizon.

## Limitations

These conclusions apply to three calibrations, one reference elasticity, one adoption share, two endogeneity conditions, and the specified learner and policy settings. Thirty replications permit MCSE reporting but do not establish the originally planned precision targets or a general estimator ranking. The experiment does not cover other elasticities, adoption shares, negative endogeneity, alternative horizons, censored demand, or the full 81-cell interaction structure. GBM's local contrast is sensitive to the chosen price interval. Observed zero failures, or empirical reliability of 0% or 100%, do not establish corresponding population probabilities, even when a plug-in MCSE is zero. DML inference and M4 confidence-interval coverage remain withheld pending separate validation. No confirmatory hypothesis-testing or generalization beyond this design is claimed.

## Reproducibility appendix

Production used commit `161b1f8c2d7e2fac281f9f7e2665e85f4d6ef665`. The original manifest, configurations, calibration identifiers, seeds, checkpoints, runtime records, and saved mechanical audit remain under `outputs/exploratory/six-cell-20261015`. The audit acceptance record is `{"AC-A6": true, "AC-A7": null, "AC-C1": true, "AC-C2": true, "AC-C3": true, "AC-C5": true, "AC-C6": true, "run_complete": true}`. The direct-oracle validation has the restricted interpretation described above. Timing artifacts remain separate under `outputs/timing/exploratory-six-cell`.

Reporting revisions regenerate derived summaries and figures from saved estimates without rerunning simulations. `reporting_revision.json` records the source checksums, reporting-source hashes, environment, and output hashes. Original production and analysis provenance remains in the manifest. Run `PYTHONPATH=src python scripts/run_exploratory.py report` to regenerate reporting from the saved artifacts; this command reuses the saved audit and does not rerun simulation-based validation. The `analyze` command additionally performs the full audit in the project's supported environment.

Publication files are `table1_estimation_prediction.csv`, `table2_pricing_performance.csv`, `table3_paired_comparisons.csv`, `figure1_elasticity_trajectories.png`, `figure2_cumulative_regret.png`, and `replication_metrics.parquet`. In Figure 1, the dashed horizontal line is the true reference elasticity. In Figure 2, the dotted zero line is the constrained oracle benchmark and the separately labeled oracle-recommendation curve includes deployment adjustments. Shaded bands show one MCSE across replications. CSV blanks in reference-arm recovery and joint-reliability fields mean not applicable.
