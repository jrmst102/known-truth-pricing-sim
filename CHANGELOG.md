# Changelog

## 1.1.2 - 2026-10-15 (exploratory chapter experiment)

The author replaced the computationally infeasible 81-cell precision-pilot and
main-experiment sequence for this chapter with a six-cell exploratory study.
The amended study crosses the three accepted environments with κ = 0 and +0.05
at η = −1.06 and φ = 0.5, with 30 independent replications per cell, 104 cycles,
and eight arms: M1, M2, and M3 under both policies plus legacy and oracle.
Automatic M3 control-function expansion is disabled. Accepted DML and control-
function diagnostics remain supplementary evidence. The original factorial
design and Monte Carlo precision targets are preserved as future work.

Timing runs are separated from production and must demonstrate that the exact
configuration, including a runtime buffer, fits the remaining worker-hour
budget. Production must retain failures and fallbacks, use fresh seeds, finish
all 180 cell replications, pass saved-run audits, and generate the chapter's two
tables and two figures with replication-level Monte Carlo uncertainty.

The study completed on 2026-10-15: 180/180 replications, six cells, eight arms,
and 104 cycles. All required saved-run checks passed. Measured computation was
14.51 worker-hours; no estimator failure or fallback occurred. The tracked
publication set contains the cycle-level estimates, seed states, manifest,
checks, replication metrics, tables, figures, and chapter text. Larger
store-week, simulated-history, and per-replication checkpoints remain local.

## 1.1.0 - 2026-10-14 (Deliverable 1 accepted)

Corrections and amendments implement SPEC_v1.1.md. 

| ID | Change | Files |
| --- | --- | --- |
| C1 | One deployment function, final ladder projection and downward ties; remove dead exploration helper | dgm.py, oracle.py, loop.py, policies.py |
| C2 | Store-week cost applied once to every deployed price, including model stores | dgm.py, loop.py |
| C3 | Record realized adoption, count and full assignment | rng.py, loop.py, pilot.py |
| C4 | Project history with the same deployment function, cost and sales flag | loop.py |
| C5 | Latent core, fixed reference-price capacity, lognormal censored oracle | dgm.py, oracle.py, loop.py |
| C6 | Expected-dollar, revenue-weighted regret and cumulative loss on all/model stores | oracle.py, loop.py, metrics.py, report.py |
| C7 | Mean reference price, explicit denominators and coverage audits | calibrate.py, clean.py, audit.py, audit_coverage.py, data/calibration/ |
| C8 | Explicit scenario environments and config consumers; replace legacy pilot_cells.yaml | config.py, cli.py, protocol.py, configs/ |
| A1 | 81-cell environment/eta/kappa/phi product; separate extensions and staged seeds | scenarios.yaml, protocol.py, rng.py, cli.py |
| A2 | Design rho=.5/equal split; preserve empirical autocovariance diagnostics | rng.py, calibrate.py, dgm_base.yaml |
| A3 | Independent store-week cost core; switch for chainwide AR(1) extension | rng.py, dgm_base.yaml |
| A4 | Zone-stratified adoption with rounded chain target | rng.py, loop.py |
| A5 | Final-26 deployed-regret and finite-negative-eta joint reliability | metrics.py, dgm_base.yaml |
| A6 | Retain extremes/positive slopes, independent flags, legacy fallback, denominators and Duan smearing | estimators/, loop.py, metrics.py, report.py |
| A7 | Within-store grouped/clustered DML, OOF/fold-averaged prediction, internal first stage; coverage withheld | estimators/dml.py, estimators.yaml, tests/test_dml*.py |

Calibration regeneration (same retained-store samples, pending full metadata audit):

- sna p_bar: 2.89 -> 2.6942881701515216; eta diagnostic -3.159570873246531 -> -2.945603607800617.
- tti p_bar: 0.57 -> 0.5714305254568318; eta diagnostic -3.84815906022416 -> -3.8578167610971525.
- Original benchmark values remain in diagnostics; see BETA_REFERENCE_REVIEW.md.
- The full store table is missing. The committed codebook PDF is corrupted, and
  its public replacement is network-blocked. Audits explicitly label their
  retained-store metadata scope; the original 75-store tuna audit is not certified.
- Preliminary tuna full-span coverage on 66 known stores is 83.576365% (399 weeks).
  A 341-week proposal reaches 91.046832% and passes competing-index cleaning with
  66 stores. It has NOT replaced the calibration, reduced the grid, or changed
  the unchanged 90% threshold. Full metadata and author sample approval are pending.
- The v1.0 failure message's store count was measured before the store-coverage
  filter; errors now print the actual retained-store denominator.

## 0.1.0 - 2026-10-13

Initial implementation of specification v1.0; configs transcribed without changing supplied values.

- The demand slope is negative. OLS, IV, and DoubleML convert a direct price coefficient to elasticity as `coefficient * p_bar`. The spec's M4 negative sign would reverse downward-sloping demand.
- Performance checkpoints 78, 104, 156 are interpreted as absolute weeks (cycles 26, 52, 104), because the loop has only 104 cycles.
- Recommended and deployed regret are percentage points; cumulative regret sums those values.
- Default instrument pass-through 0.20 is provisional until P4 and author approval; P4 explores the supplied grid.
- Cleaning order, competing-price index, cross-fitting splits, decision reliability, and compute-budget ladder cannot be certified against protocol sections that were not provided.
- Stores lacking zones are dropped provisionally, following spec section 14; this requires author confirmation.
- Week dates and store zones can be imported from the public Kilts codebook. Easter indicators use actual Easter dates, not questionable special-event labels in that manual.
- Exact scientific replay excludes wall-clock timings, run IDs, and timestamps, which cannot be deterministic.
