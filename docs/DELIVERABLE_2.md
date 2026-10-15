# Deliverable 2: full-horizon diagnostics

Status: **S2 running; Deliverable 2 acceptance pending.** Jose Mendoza accepted
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
