# Implementation Status

The CLI, calibration, mechanism, all estimator variants, retraining, checkpoint/resume,
Monte Carlo summaries, decisions, diagnostics and report generation are implemented.
This is an exploratory implementation of the supplied specification, not a signed-off
implementation of the referenced Pilot Protocol, which was not included in the repository.

## Scientific Approval Required

- Provide Pilot Protocol v1.0, particularly cleaning rules (section 3.2), the auxiliary
  regression and fallback rules (section 4), decision reliability (section 7), the
  n_sim rule and compute ladder (section 9), and report section order (section 10).
- Confirm the spec's elasticity sign conflict. This implementation uses a negative
  direct price slope times p_bar for OLS, IV and DoubleML.
- Confirm that performance checkpoints 78, 104 and 156 are absolute weeks, not cycles.
- Confirm dropping stores with no zone. The public manual provides 79 zoned stores;
  demographics and customer counts do not replace the zone table.
- Confirm the provisional 0.20 instrument pass-through before P4 approval, the
  150 core-hour budget, and the eventual pilot machine.
- Confirm actual Easter dates rather than erroneous special-event labels in some
  codebook rows. The committed table retains the original labels and separately
  derives Easter and the four pre-Easter weeks.

## Explicit Provisional Interpretations

Cleaning removes invalid OK/price/quantity/sales rows, unknown UPCs and unzoned stores,
checks store coverage against the full observed calendar span, checks UPC coverage
against retained stores times that span, selects the largest-sales eligible UPC,
substitutes if its zero-sales share is too large, then removes zero sales before logs.
It refuses duplicate observations and incomplete competing-price weeks.
The competitor index is an equal-weight mean of other eligible UPCs' demeaned log unit
prices by week. The exact protocol definition is still needed.

Calibration residual autocovariances use calendar-adjacent pairs within store, weighted
by valid pair counts. rho is cov(2)/cov(1); stationary latent variance is cov(1)/rho,
clipped to the configured share of residual variance. Nonpositive cov(1) assigns zero
latent variance and the lower rho bound. This fallback needs protocol confirmation.
Price dispersion additionally records profit_mean and resid_sd so plausibility checks
can be regenerated without raw data. Those two nested fields extend the spec schema.
Failed plausibility checks are logged and never silently repaired.

P1 pairs delta=0 with greedy and delta=0.03 with greedy_rps. M3_cf is stored separately
and is not a fifth estimator in the protocol sense. Its forecast excludes the
unobserved control-function residual. DoubleML predictions use full-sample outcome and
treatment nuisance fits plus the orthogonal price slope. Cross-fitting uses deterministic
row-wise folds; the protocol must confirm whether to group by store or week instead.
No estimator receives latent shocks or the truth.

Decision reliability currently means all of the final 26 recommended-price regrets
are at most 2 percentage points. Horizon statistics are computed first by replication,
then summarized across replications; repeated cycles are not treated as independent draws.
Compute projection assumes 27 cells with P1's measured arm mix, and does not apply an
unknown compute ladder. Missing final-week results or qualifying instrument strengths
produce missing decisions, not made-up choices. Required n_sim above the cap is flagged.

## Reproducibility And Acceptance

Real-data pilot runs require a clean worktree. Synthetic overrides are explicitly labeled
and permitted on a dirty worktree. Manifests contain code/config/calibration hashes,
effective settings, package versions, hardware and master seed. Resume rejects changed
inputs. Replication shards and states are written atomically; unfinished shards are rerun
from their saved seed. Scientific values reproduce exactly; seconds, timestamps and
run IDs are execution metadata and cannot reproduce byte-for-byte.

CI uses only generated observations and the synthetic calibration. The calendar is a
public factual decode table, not movement data. The two-replication short smoke test
checks correctness, not AC1 statistical acceptance. A full-horizon slow check and
additional all-learner checks exercise the same loop. AC1-AC6 require a full, committed
pilot on an approved calibration and machine. AC7 remains blocked if a supplied category
has no UPC satisfying the unchanged coverage thresholds. AC8 checks deterministic
scientific replay, excluding wall-clock metadata.

Full protocol conformity, the compute ladder, author sign-off, and the full real-data
P0-P5 experiment remain pending. No scientific acceptance or production result is implied
by the sample synthetic report.