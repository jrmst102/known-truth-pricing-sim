# Continue Deliverable 2 in VS Code

Cloud execution was stopped at the author's request on October 15, 2026,
11:12 a.m. Eastern. No cloud scientific workers remain active. All 14 finished
replications were preserved and verified byte-for-byte. The four interrupted
replications will be recomputed from their original seeds; no completed
replication needs repeating. There are 96 planned replications in total.

This folder is a self-contained project snapshot plus checkpoints. It contains
no raw Dominick's movement archives. Source/configuration/calibration files are
included, so a separate Git clone is not required to continue this run.
Original simulation commit: 8f04ebb0cc3cc33e554dce5c93d9b6acfbefe588.
Project snapshot: main at 8041fa5ae80eca6f7ff16f13b9985256cfc346cf.

## 1. Open the project

Extract the ZIP, then use VS Code's File > Open Folder to open `s2-local`.
Open Terminal > New Terminal. Run commands from that folder.

Install uv if it is not installed:
https://docs.astral.sh/uv/getting-started/installation/

Then install the exact Python version and verify the handoff (these commands
work in PowerShell, macOS terminals and Linux terminals):

```sh
uv python install 3.11.17
uv run --python 3.11.17 --extra dev --extra data python resume_local.py --check-only
```

uv creates the local environment and installs dependencies from pyproject.toml.
The check should report `14/96 complete` and approximately `116.745` remaining
worker-hours. Python and numerical-package versions must match the original run.
If a package cannot load, resolve that prerequisite before starting the run.
For example, macOS LightGBM installations may need the OpenMP runtime (`libomp`).
VS Code can use the resulting `.venv` via Python: Select Interpreter.

## 2. Resume

Use four workers on a computer with at least four available CPU cores:

```sh
uv run --python 3.11.17 --extra dev --extra data python resume_local.py --workers 4
```

Use `--workers 2` instead on a smaller computer. The launcher limits numerical
libraries to one thread per worker. Keep the computer awake and the terminal
open while it runs. To stop intentionally, press Ctrl+C once and wait for the
launcher to finish stopping its child processes and recording execution history.
Resume later with the same command. Only fully finished replications are reused.

The launcher verifies original scientific-source/configuration/calibration hashes,
coverage records, the manifest fingerprint and transferred checkpoint hashes.
It permits changed hardware and records each local attempt separately; it does
not rewrite the original scientific fingerprint or pretend the new machine was
the original one. Editable ktsim package-version metadata can differ; numerical
packages must match and ktsim source hashes must remain identical. Historical
local paths inside the cloud execution logs are provenance, not local commands.

The original manifest retains the initial `n_jobs=2` setting. Actual later worker
counts are in the adjacent `execution_history.json`; successful completion adds
that history to the generated report's manifest.

## 3. Monitor and review

The VS Code terminal logs replication starts and finishes. Checkpoints are in:

`outputs/diagnostic/s2-diagnostic-20261014/replications/`

The report will be generated at:

`outputs/diagnostic/s2-diagnostic-20261014/report.md`

The launcher retains the 150-worker-hour budget, subtracting cloud and recorded
local execution time, including interrupted attempts. On four workers the
remaining cloud handoff budget permits approximately 29.19 elapsed hours of local
execution. It may stop before all replications finish; this is an incomplete run,
not accepted Deliverable 2. Do not silently increase the budget or change learners.
A different/faster local CPU may change the observed runtime.

Hard termination, power loss or closing VS Code may leave a local attempt marked
running. Before restarting, ensure no old local worker processes remain and record
the stopped attempt/time used; the launcher refuses to overlap an unclosed attempt.
Normal Ctrl+C and budget stops update this history automatically.

Deliverable 2 remains pending author review of the completed diagnostic report.
Do not start the precision pilot or main experiment yet.
