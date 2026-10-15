#!/bin/bash
set -u
cd /workspace/known-truth-pricing-sim || exit 1
export XDG_CACHE_HOME=/workspace/.cache
export MPLCONFIGDIR=/workspace/.cache/matplotlib
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export PYTHONUNBUFFERED=1
export PATH=/workspace/known-truth-pricing-sim/.venv/bin:$PATH
printf '\nResuming original S2 inputs with four workers; completed checkpoints retained.\n'
timeout --signal=TERM --kill-after=60s 106255s .venv/bin/python /workspace/onboarding-artifacts/s2-diagnostic-20261014/resume_four_workers.py
run_status=$?
printf '%s\n' "$run_status" > /workspace/onboarding-artifacts/s2-diagnostic-20261014/four-worker-exit-code.txt
date -u +%FT%TZ > /workspace/onboarding-artifacts/s2-diagnostic-20261014/four-worker-finished-at.txt
exit "$run_status"
