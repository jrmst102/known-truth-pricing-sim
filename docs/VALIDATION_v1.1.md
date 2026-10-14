# Deliverable 1 implementation and validation

Status: **implementation draft; Deliverable 1 is not accepted**. No scientific
S2, S3 or S4 run was started. The protocol's author approval and deliverable
acceptance lines remain PENDING. Remote CI has been configured but not run here.

## Author decisions recorded — 2026-10-14

The author has approved A1–A7 and the tuna calibration window (weeks 1–341),
and retained the 150-hour budget and 2,000-replication cap. This resolves those
research-design decisions; it does not accept Deliverable 1 or enable M4 coverage.
The merged calibration records report 67 stores; the preliminary evidence below
used 66. Reconcile the technical records and validate merged `main` before acceptance.

## Post-merge fixes and verification — 2026-10-14

The three confirmed merge problems are corrected:

- The dirty-worktree test explicitly invokes the diagnostic stage with simulated
  Git state and forbids configuration/simulation calls. It no longer depends on
  missing calibration data or starts an 81-cell validation. CLI integration tests
  have timeouts; the unit workflow is limited to 15 minutes.
- `check_validation.py` and `validate_v11.py` now share the current-schema checker.
  It checks complete planned results, ladder/history/store-week records, revenue
  balances, adoption, state/fold hashes and coverage policy. Regression tests
  reject corrupted artifacts and prevent short runs from passing full-horizon
  acceptance. The full-horizon gate also checks both replications and all arms
  across the three adoption settings.
- Recalibration loads the explicitly selected window configuration, filters before
  cleaning, and uses the selected calendar span as the denominator even when
  boundary weeks have no observations. The full eligibility audit is preserved;
  a separate window audit and configuration hash explain the actual calibration.

Verification on the fixed working tree:

- **61 unit tests passed**, two opt-in slow inference cases deselected, with the
  loop-smoke file run separately. **All four loop-smoke tests passed**. These are
  65 distinct local passing cases. The DML estimators were not modified; their
  200-draw inference studies were not repeated for these merge fixes.
- Ruff, whitespace checks and Git hooks passed.
- The shared checker passed against the existing full synthetic 104-cycle,
  two-replication, 14-arm artifacts, and against the retained empirical smoke
  artifacts. This is artifact revalidation, not a new scientific simulation.
- Actual-archive tuna recalibration in a temporary output directory reproduced
  **67 stores, 20,765 observations, p_bar 0.7931355646520587**. Fitted coefficients
  agree with the committed calibration to floating-point precision (differences
  below 1e-12). The full audit is weeks 1–399; the selected audit is weeks 1–341;
  observed focal-UPC weeks remain 1–331. The failure entry was cleared only after
  the selected calibration succeeded. Committed calibration values were preserved.
- The shorter window retains store 45, explaining **66 full-span versus 67 window
  stores** for the supplied retained-store metadata. This reconciles the counts;
  it does not certify that the missing full public metadata has been reconstructed.

Evidence is in `/workspace/onboarding-artifacts/merge-fixes-{unit,smoke}.xml`,
`merge-fixes-targeted.log`, `merge-fixes-full-artifact-check.log`,
`merge-fixes-empirical-artifact-check.log`, and `merge-fixes-tuna-recalibration.log`.
Remote CI for these fixes has not yet been confirmed. Author research approvals
remain recorded above; final protocol/Deliverable 1 acceptance is still pending.

## Local evidence (before merge)

- Standard suite: **53 passed**, three slow cases deselected.
- Full-horizon loop suite: **4 passed** (three overlap the standard suite).
- Opt-in DML inference: **2 passed**, 200 independent draws per variant, each
  satisfying the required 90–99% interval coverage criterion. The author-controlled
  inference_validated flag remains false. Across these suites, 56 unique cases ran.
- Ruff and both pre-commit hooks passed. Matplotlib/pyparsing deprecation warnings
  remain dependency warnings, not failed checks.
- Full synthetic validation: three adoption settings (0, .5, 1), two replications,
  104 cycles, **14 arms**, **8,736 estimate rows**, **69,888 cycle store-week rows**.
  Small 10-tree learners exercise mechanics; this is not a precision or diagnostic run.
- All history and cycle prices were on the ladder. Core censoring was exactly zero.
  Exploration was inert at phi=0. Expected revenue sums balanced against store-week
  records. Cost pass-through coefficient was **0.1995680631**, target **0.20**.
- Model assignments, recorded adoption counts and DML fold hashes were verified.
  Positive estimates were retained with flags (2,276 rows); numerical failures: zero.
  Planted unit tests separately exercise extreme estimates and missing predictions.
- Cracker/tissue empirical smoke: one replication per environment, two cycles,
  all 14 arms. History/cycle ladder checks, zero core censoring and revenue sums passed.
  These short runs do **not** replace retained-environment full acceptance.
- The censored extension completed a separate two-cycle synthetic run. Its oracle's
  closed form passed million-draw Monte Carlo comparisons on three price/cap pairs.

Evidence in this machine is under `/workspace/onboarding-artifacts/`:

- `v11-validation/v11-full-synthetic/{checks.json,manifest.json,report.md,estimates.parquet,storeweek.parquet}`
- `v11-validation/v11-retained-final/` and `v11-validation/v11-censored/`
- `v11-unit-results.xml`, `v11-tests-final.log`, `v11-loop-smoke.log`,
  `v11-dml-inference.log`, `v11-hooks.log`, `v11-artifact-checks.log`

The long synthetic run started during implementation; its manifest records the
source/configuration hashes used at startup. Subsequent CLI/report/audit changes
were covered by the final tests and refreshed report. A new CI run exercises the
current checkout from scratch. Do not describe this as a published scientific run.

An initial acceptance-harness assertion incorrectly expected zero deployed oracle
regret while cost pass-through was active. It was corrected to test direct oracle
deployment with kappa, exploration and pass-through all zero. The saved artifacts
were rechecked successfully; no prices or result rows were altered.

## Acceptance register

| Check | Local evidence | Remaining limitation |
| --- | --- | --- |
| AC-C1/C4 | Full synthetic history/cycle ladder checks; tie and phi-zero tests | Retained empirical full acceptance pending |
| AC-C2 | Non-saturated coefficient within 10% at both adoption extremes | Scientific first-stage diagnostics await S2 |
| AC-C3/A4 | Zone assignment unit test on tissue store set; assignments/counts saved | Full metadata eligibility review pending |
| AC-C5 | Core zero censoring; MC-validated censored expectation and extension smoke | Extension is not a scientific result |
| AC-C6/A5 | Three-store fixture, revenue balances, direct oracle zero loss, joint reliability tests | Retained empirical full acceptance pending |
| AC-A6 | Extreme/positive retention, legacy fallback, smearing and denominator tests | No performance acceptance claim from two reps |
| AC-A7 | Store folds/features/cluster path; coverage withheld; 200-draw checks passed | Author opt-in required to publish M4 coverage |
| AC-C7 | Mean-price regeneration for sna/tti; three preliminary coverage audits | Full store metadata and final category audits pending; window approved |
| AC-C8 | Configuration consumers, unread-key rejection, environment resolution and baseline checks | Three-environment grid approved; implementation validation pending |
| AC-P | Protocol version/baseline, amendments and changelog prepared | Author signature and acceptance pending |

## Eligibility and author decisions

The full public store table used by the original calibration is absent. The
committed PDF is corrupted (the nominal 10,165,552-byte PDF became an 18 MB file
with invalid compressed objects). Both pypdf and pdftotext failed to read it.
The public replacement request was rejected by the network proxy with CONNECT
403. The necessary `www.chicagobooth.edu` addition was saved in environment
settings; it has not been confirmed active. No restricted movement data needs
to be downloaded.

Preliminary audits explicitly identify the retained-store table as their source.
On 66 known tuna stores, full-span coverage is 83.576365% over 399 weeks. The
first 344-week candidate failed competing-index eligibility; the search now
checks that too. A 341-week candidate passes cleaning at 91.046832%, with 66
stores. **The author has since approved weeks 1–341.** The merged calibration
uses 67 stores and requires reconciliation with this preliminary evidence.
Approval does not certify the original full-metadata audit or authorize two
environments. The grid remains 81; scientific use awaits acceptance. Do not lower
the 90% threshold or substitute synthetic tuna.

To close Deliverable 1:

1. Enable the saved public-codebook domain, obtain an intact public codebook and
   restore its full store table; reproduce the original audit using explicit
   denominators and missing-record causes. Validate the approved 341-week window.
2. Apply the approved A1–A7, tuna window and compute limits. Complete final protocol
   review of sign convention, checkpoints, zone exclusion, calendar and machine.
3. Finish acceptance on the agreed retained empirical environments, run current
   CI, review the implementation/calibration changes, and record author acceptance.
4. Only then run S2 diagnostics. S3 requires accepted S2; S4 requires an approved
   precision decision and unchanged settings. Nothing here signs on the author's behalf.

The other-zone-price block is an extension, not proof of instrument invalidity:
its exclusion properties depend on the common-demand setting and the chosen
price construction. The core uses only the independent cost instrument. Any
scientific claim of invalidity needs an explicit, author-reviewed extension design.

The benchmark-slope investigation is an [issue draft](BETA_REFERENCE_REVIEW.md);
no external issue or message has been posted. Original diagnostic values remain
visible beside mean-reference-price values in calibration reports.
