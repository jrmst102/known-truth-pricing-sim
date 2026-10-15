# Changelog

## 1.1.1 - 2026-10-15 (reduced S2 diagnostic scope)

Jose Mendoza explicitly requested that Deliverable 2 finish within one to two
hours after the original 96-replication diagnostic was observed to require about
210 worker-hours, above the retained 150-worker-hour budget. The broad run was
stopped with 14 completed SNA replications preserved. The replacement diagnostic
retains those full-horizon results and adds one representative base cell for each
of TNA and TTI, with all 14 arms and unchanged learners, for 52 cycles. The report
must label this reduced scope and cannot claim 81-cell or full-horizon cross-
environment coverage. S3 and S4 remain blocked pending review and explicit
acceptance of the reduced Deliverable 2.

Jose Mendoza accepted the completed reduced Deliverable 2 on 2026-10-15. The
acceptance includes its stated limitations and makes S3 eligible for a new scope
and compute decision; it does not authorize S4 or M4 coverage reporting.

## 1.1.0 - 2026-10-14 (Deliverable 1 accepted)

Corrections and amendments implement SPEC_v1.1.md. Jose Mendoza confirmed all CI
jobs passed, explicitly accepted Deliverable 1 and authorized Deliverable 2 (S2)
on 2026-10-14. This records author acceptance; it does not claim additional locally
reproduced metadata evidence. The validation history below predates acceptance.
S3/S4 remain gated by Deliverable 2 acceptance and the precision decision.

Author decisions: A1–A7 approved; tuna window weeks 1–341 approved at the unchanged
90% coverage threshold; compute limits retained at 150 hours and a 2,000-replication
cap. M4 inference reporting remains withheld. S2 uses the current cloud machine,
two workers and unchanged scientific settings; see docs/PROTOCOL_v1.1.md.

Post-merge fixes:

- The dirty-worktree test explicitly targets the diagnostic stage with controlled
  Git state and fails if it reaches configuration or simulation. CLI integration
  tests have timeouts; the unit CI job has a 15-minute bound.
- Both saved-run validation commands share the current manifest/state/store-week
  checker. It verifies artifact completeness, revenue balances, assignments and
  fold hashes; missing artifacts and shortened runs cannot pass full acceptance.
- Recalibration reads `calibration_windows.json` (or `--windows`), applies approved
  bounds before cleaning, preserves the full-span audit, and records a separate
  selected-window audit and configuration hash. Denominators include missing
  boundary weeks. Actual-archive reproduction matches the saved tuna sample:
  67 stores, 20,765 observations, p_bar 0.7931355646520587; fitted coefficients agree
  to floating-point precision. Store 45 passes coverage in the shorter window,
  explaining 67 window stores versus 66 over the full span. No coverage threshold
  was changed and no scientific stage was started.

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

Additional changes: v1.1 protocol draft, output schemas and stage provenance;
S3 precision decision over all cells/arms with paired differences and explicit
compute limits; optional store-week audits; scientific-stage acceptance gates;
new tests and reproducible full-horizon synthetic acceptance runner. CI has
separate unit and full-horizon smoke jobs. Existing synthetic pilot records are
preserved as development records.

Calibration regeneration (same retained-store samples, pending full metadata audit):

- sna p_bar: 2.89 -> 2.6942881701515216; eta diagnostic -3.159570873246531 -> -2.945603607800617.
- tti p_bar: 0.57 -> 0.5714305254568318; eta diagnostic -3.84815906022416 -> -3.8578167610971525.
- Original benchmark values remain in diagnostics; see BETA_REFERENCE_REVIEW.md.
- The full store table is missing. The committed codebook PDF is corrupted and
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

Pending author approval (not amendments to the missing Pilot Protocol):

- The demand slope is negative. OLS, IV and DoubleML convert a direct price coefficient to elasticity as `coefficient * p_bar`. The spec's M4 negative sign would reverse downward-sloping demand.
- Performance checkpoints 78, 104, 156 are interpreted as absolute weeks (cycles 26, 52, 104), because the loop has only 104 cycles.
- Recommended and deployed regret are percentage points; cumulative regret sums those values.
- Default instrument pass-through 0.20 is provisional until P4 and author approval; P4 explores the supplied grid.
- Cleaning order, competing-price index, cross-fitting splits, decision reliability, and compute-budget ladder cannot be certified against protocol sections that were not provided.
- Stores lacking zones are dropped provisionally, following spec section 14; this requires author confirmation.
- Week dates and store zones can be imported from the public Kilts codebook. Easter indicators use actual Easter dates, not questionable special-event labels in that manual.
- Exact scientific replay excludes wall-clock timings, run IDs and timestamps, which cannot be deterministic.
