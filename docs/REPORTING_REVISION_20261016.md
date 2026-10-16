# Exploratory reporting revision, October 16, 2026

This revision finalizes the exploratory chapter's outcome definitions and incorporates paired comparisons from the completed six-cell experiment. It does not rerun simulations or change the experimental design.

## Changes

- Standardize common-grid horizon RMSE as the square root of mean squared weekly RMSE. Publication Table 1 already used this definition; `performance.csv` now agrees.
- Treat reference-arm terminal elasticity error, estimated-sign outcomes, and joint decision reliability as not applicable. Reference truth placeholders are not estimated coefficients. Set reference estimated/interval counts to zero and report regret-only reliability separately.
- Add Table 3 with 48 within-cell paired contrasts, each using 30 replications: six fitted-model arms versus legacy, plus IV versus OLS under each policy. Differences and MCSEs are in percentage points, with treatment minus comparator as the direction.
- Explain the constrained oracle benchmark separately from the oracle-recommendation arm with deployment adjustments. Label both in Figure 2 and express regret levels as percentages.
- Clarify the GBM local ±1% contrast, forecast targets, reliability threshold/window, and MCSE interpretation. Incorporate the paired results and limitations into the chapter.
- Add a `report` command that regenerates derived outputs using saved estimates and the saved audit. The existing `analyze` command still performs the full audit. Preserve the original production manifest; record reporting provenance in a separate JSON file.

## Verification

- Four focused regression tests passed, covering RMSE pooling, reference applicability, within-replication paired MCSE, incomplete-pair rejection, and the existing hand-calculated MCSE example.
- All 48 paired contrasts and MCSEs were independently recomputed from the preserved original replication metrics and matched.
- All 36 model common-grid RMSE summaries and MCSEs agreed between the publication table definitions and `performance.csv`.
- Table 1, all prior model-arm Table 2 outcomes, and all arms' regret and revenue-loss summaries were unchanged to numerical tolerance.
- Git blob hashes confirmed that estimates, states, manifest, saved checks, failures, and runtime records were unchanged. Generated output hashes were checked, and both figures were visually reviewed.

Verification used Python 3.12.14 with NumPy 2.3.5, pandas 2.2.3, PyArrow 19.0.1, and pytest 8.3.5. The reporting metadata records the actual runtime versions. The full simulation suite and simulation-based validation were not rerun; production remains associated with its original recorded environment and audit. This reporting-only verification does not supersede the supported Python 3.11 simulation environment or authorize M4 coverage claims.
