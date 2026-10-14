# Deliverable 1 implementation and validation

Status: **implementation draft; Deliverable 1 is not accepted**. No scientific
S2, S3 or S4 run was started. The protocol's author approval and deliverable
acceptance lines remain PENDING. Remote CI has been configured but not run here.

## Local evidence

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
| AC-C7 | Mean-price regeneration for sna/tti; three preliminary coverage audits | Full store metadata, tuna resolution and final category audits pending |
| AC-C8 | Configuration consumers, unread-key rejection, environment resolution and baseline checks | Author approval of the final grid pending |
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
stores. **This is a proposal, not the adopted sample.** It does not certify the
original full-metadata audit or authorize two environments. The grid remains 81;
tuna remains blocked. Do not lower the 90% threshold or substitute synthetic tuna.

To close Deliverable 1:

1. Enable the saved public-codebook domain, obtain an intact public codebook and
   restore its full store table; reproduce the original audit using explicit
   denominators and missing-record causes. Re-evaluate any window proposal.
2. Have the author decide tuna/window/two-environment eligibility and confirm
   A1–A7, sign convention, checkpoints, zone exclusion, calendar and compute budget.
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
