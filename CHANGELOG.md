# Changelog

## 1.1.0 - 2026-10-14

Implementation of `docs/SPEC_v1.1.md`; protocol prepared for author sign-off.
Scientific diagnostics, precision pilot and main experiment remain gated.

Corrections:

- C1 (`dgm.py`, `oracle.py`, `policies.py`, `loop.py`): one final nearest-ladder
  projection, downward midpoint ties, exploration restricted to model stores.
- C2 (`dgm.py`, `loop.py`): cost pass-through once for every store.
- C3 (`rng.py`, `loop.py`, `pilot.py`): realized adoption counts/shares and assignment vectors.
- C4 (`loop.py`): constrained history, cost included, no history exploration.
- C5 (`dgm.py`, `oracle.py`, `loop.py`): latent core sales; pre-price reference capacity
  and closed-form censored oracle/revenue for the separate extension.
- C6 (`oracle.py`, `loop.py`, `metrics.py`, `report.py`): revenue-weighted fractions,
  cumulative dollar loss, normalized regret, recommended/deployed and all/model sets.
- C7 (`clean.py`, `coverage.py`, `calibrate.py`, audit scripts, `data/calibration/`):
  mean reference prices: sna **2.6942881701515216**, tti **0.5714305254568318**,
  tna **0.7931355646520587**. Full coverage audits and empirical shock diagnostics.
- C8 (`config.py`, `cli.py`, `configs/`, consistency tests): environment-specific
  calibration and explicit mechanism, reliability, policy and precision settings.

Amendments, pending author protocol acceptance:

- A1 (`scenarios.yaml`, `cli.py`, protocol): 81 crossed core cells. Tuna step 1
  reproduced 83.6% best coverage over 399 weeks (66 retained stores; the old error
  message's 75 was the count before coverage filtering). No denominator/join error
  found. Step 2 selects weeks 1–341, 67 stores, unchanged 90% UPC threshold, with
  eligible competing UPCs. Window-selection limits and rejected candidates are recorded.
- A2 (`rng.py`, `calibrate.py`, `dgm_base.yaml`): rho_xi=0.5, equal variance split by
  design; empirical sensitivity remains explicit.
- A3 (`rng.py`, `dgm.py`, config): independent store-week cost; chainwide AR(1) extension.
- A4 (`rng.py`, `loop.py`): within-zone assignment with balanced chainwide rounding.
- A5 (`metrics.py`, config): reliability requires deployed regret <=0.02 and finite
  negative elasticity in all final 26 cycles; separate criteria reported.
- A6 (`estimators/`, `loop.py`, `metrics.py`): retain finite extreme/positive estimates,
  per-store legacy fallback when predictions fail, explicit denominators, Duan smearing.
- A7 (`estimators/dml.py`, inference tests): within-store transformation, store folds,
  cluster variance, fold-based forecasts, internal first-stage strength; coverage withheld.

`pilot.py`, `cli.py`, `decisions.py`, `report.py` implement four isolated stage streams,
provenance, frozen S3-to-S4 settings, configured precision targets and paired comparisons.
The sign convention is beta*p_bar (equivalently -b*p_bar); checkpoints are cycles
26/52/104. These resolve the corresponding 0.1.0 interpretation items in the draft
protocol; signature remains the author's action. Historical elasticity diagnostics
are preserved alongside recalibrated values and an open local interpretation issue.

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