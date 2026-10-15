# Deliverable 2: full-horizon diagnostics

Status: **Deliverable 2 accepted by Jose Mendoza on 2026-10-15.** Jose Mendoza accepted
Deliverable 1 and authorized S2 in chat on 2026-10-14. On 2026-10-15 he explicitly
requested increasing the run from two workers to four. No S3 or S4 run is authorized.

## Frozen scientific design

- Run ID: `s2-diagnostic-20261014`.
- Simulation commit: `8f04ebb0cc3cc33e554dce5c93d9b6acfbefe588`.
- Three retained empirical environments; 81 core cells and five additional base
  replications per environment: 96 cell replications in total.
- Every replication uses 52 history weeks, 104 cycles and all 14 arms. Scientific
  configurations, calibrations and stage-specific seeds are unchanged.
- M4 coverage remains withheld. Deliverable 2 needs the completed diagnostic report
  and author review before the precision pilot can begin.

## Execution history

The initial two-worker attempt started on 2026-10-14 at 18:54:33 Eastern. It was
stopped on 2026-10-15 for the author-requested four-worker restart. Four workers
logged replication starts at approximately 10:53 Eastern on 2026-10-15.

At restart, all **14 completed replications** and their state/store-week audits
were preserved byte-for-byte and backed up. The two incomplete replications
restart from their original seeds because only finished replications are
checkpointed. This is not a change to the planned replication count.

The existing Python runner supports a different worker count on resume. A local
execution-only launcher verified the original commit, software/hardware,
manifest fingerprint, source/configuration/calibration hashes, coverage audits
and completed checkpoints before calling that runner with `n_jobs=4`. No tracked
scientific source was changed. The existing checkpoint/replay regression passed,
including resuming with a changed worker count.

The frozen manifest retains `n_jobs=2` as its original launch setting. The adjacent
`execution_history.json` records the subsequent four-worker attempt; the report
launcher includes that history in the final manifest on successful completion.
The simulation commit remains the original commit even after documentation merges.

## Reduced-scope decision — 2026-10-15

At 12:54 p.m. Eastern, after live inspection showed four healthy workers spending
about 71% of measured runtime in M4 and projected total work of roughly 210
worker-hours, Jose Mendoza requested reducing the diagnostic scope so it would
finish within one to two hours. The local broad-run attempt stopped cleanly with
14 completed SNA full-horizon replications preserved and no new partial result
treated as complete.

The replacement diagnostic retains those 14 SNA replications and adds one
representative `med, pos, phi=0.5` cell for TNA and TTI. Both new cells retain all
14 arms, the original diagnostic seed, calibrations and 500-tree learner settings,
but run for 52 cycles. The final report must keep the two evidence sets separate
and explicitly state that the reduced scope does not diagnose all 81 cells or a
104-cycle horizon in TNA and TTI.

Both replacement cells finished successfully on 2026-10-15 at approximately
2:07 p.m. Eastern. The report is under
`outputs/diagnostic/s2-reduced-20261015/report.md`. The author subsequently stated:
“Deliverable 2 is accepted.” This acceptance applies to the documented reduced
scope and its limitations. It does not authorize S4 or validate M4 coverage.

Machine: Intel Xeon Platinum 8573C, four CPU equivalents, 32 GiB cgroup memory;
one numerical-library thread per worker. The 150-hour budget and 2,000-replication
cap remain unchanged. Conservative worker-slot accounting includes interrupted
work: the first attempt consumed at most 31.93887841 worker-hours, leaving a
106,255-second (approximately 29.515-hour) wall-time limit for four workers.
This replaces the initial 75-hour two-worker timeout. Completion within that
budget is not assured; a budget stop leaves an incomplete diagnostic, not an
accepted deliverable.

## Local artifacts

Outputs are under `outputs/diagnostic/s2-diagnostic-20261014/`:

- `manifest.json`: original scientific provenance and frozen inputs.
- `states.parquet`, `replications/`, `storeweek/`: checkpointed results and audits.
- `execution_history.json`: worker-count change and budget accounting.
- `report.md`: generated only after successful completion.

Execution controls and the checkpoint backup are under
`/workspace/onboarding-artifacts/s2-diagnostic-20261014/`:

- `run.log`: combined log from both execution attempts.
- `checkpoint-before-four-workers/`: snapshot before restart.
- `preserved-checkpoint-hashes.json`: hashes verified after restart.
- `resume_four_workers.py`, `run-four-workers.sh`: local execution launchers.
- `four-worker-launcher.json`, `four-worker-budget.json`: process/budget records.
- `four-worker-exit-code.txt`: created when the four-worker attempt exits;
  the older `exit_code.txt` describes the intentionally stopped two-worker attempt.

The execution-only Python launcher SHA256 is
`c5031675dbc24aaf4fa044adb57fa510ab04c91a3c2bd8aa9d2b3f2d542051ba`.
Checkpoints, logs, movement archives and machine-specific launchers are local
artifacts, not Git-tracked project files. A Git clone does not transfer them.

A move to Codespaces requires transferring the checkpoints and execution history,
validating the frozen scientific inputs and recording the changed environment.
The normal CLI resume check rejects changed hardware/worker settings; do not
bypass it by rewriting the original fingerprint. Stop the current execution
before starting a replacement to avoid duplicate computation.

## Local handoff — 2026-10-15

The author requested stopping the cloud run to continue locally in VS Code.
All cloud scientific workers were stopped at 11:12 a.m. Eastern. Fourteen
completed replications and their audits remain preserved; the four interrupted
replications will restart from their original seeds. No local scientific run was
started by the cloud handoff process.

The cloud attempts used at most 33.25511136 worker-hours under conservative
worker-slot accounting, leaving approximately 116.74488864 worker-hours of the
unchanged 150-hour budget. Local execution must retain that accounting.

A self-contained transfer bundle is prepared at
`/workspace/exports/s2-local-transfer.zip`. It includes a source snapshot,
calibrations, completed checkpoints, execution history, original cloud logs,
`README_LOCAL.md`, and a portable `resume_local.py` launcher. No raw movement
archives or virtual environment are included. The launcher validates original
scientific inputs, permits and records hardware changes, enforces numerical
package versions, and preserves the original manifest/fingerprint. It records
local attempts and stops child workers on the remaining-budget timeout or Ctrl+C.
The normal `scripts/run_pilot.py --resume` command is not the migration launcher.

The bundle's preflight was verified against the transferred checkpoints; checks
accept hardware changes and reject changed dependency versions, scientific
configurations and corrupted checkpoints. Deliverable 2 still needs completion
and author review before S3 can start.
