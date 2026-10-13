from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from ktsim.loop import run_replication
from ktsim.metrics import performance
from ktsim.rng import draw_shocks, replication_streams


def atomic_parquet(frame, path):
    path = Path(path)
    temporary = path.with_suffix(".tmp.parquet")
    frame.to_parquet(temporary, index=False)
    os.replace(temporary, path)


def atomic_json(data, path):
    path = Path(path)
    temporary = path.with_suffix(".tmp.json")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    os.replace(temporary, path)


def now():
    return datetime.now(timezone.utc).isoformat()


def worker(cell, rep, ss, cal, dgm, est_cfg, output, save_data, key):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info("Start %s replication %s", cell.label, rep)
    shocks = draw_shocks(ss, cal.n_stores, dgm.history_weeks + dgm.cycles, cal, dgm)
    result = run_replication(cell, rep, shocks, cal, dgm, est_cfg, save_data=save_data)
    simulated = result.attrs.pop("simulated_data")
    result["run_id"] = output.name
    if save_data:
        frames = [pd.DataFrame(frame).assign(arm=arm, cell=cell.label, rep=rep, run_id=output.name)
                  for arm, frame in simulated.items()]
        atomic_parquet(pd.concat(frames, ignore_index=True), output / "simulated" / f"{key}.parquet")
    atomic_parquet(result, output / "replications" / f"{key}.parquet")
    logging.info("Finish %s replication %s; %.2f seconds", cell.label, rep, result.seconds.sum())
    return key


def run_pilot(cells, cal, dgm, est_cfg, master_seed, output, manifest, n_jobs=1,
              resume=False, save_data=False):
    output = Path(output)
    if n_jobs < 1:
        raise ValueError("n_jobs must be positive")
    if output.exists() and not resume:
        raise FileExistsError(f"Run already exists: {output}; use --resume")
    if resume and not (output / "manifest.json").exists():
        raise FileNotFoundError("Resume requires an existing manifest.json")
    output.mkdir(parents=True, exist_ok=True)
    (output / "replications").mkdir(exist_ok=True)
    (output / "simulated").mkdir(exist_ok=True)
    manifest_path = output / "manifest.json"
    if resume:
        previous = json.loads(manifest_path.read_text())
        if previous["fingerprint"] != manifest["fingerprint"]:
            raise ValueError("Resume inputs differ from stored calibration/config/commit/environment")
    else:
        atomic_json(manifest, manifest_path)
    state_path = output / "states.parquet"
    states = pd.read_parquet(state_path).to_dict("records") if state_path.exists() else []
    lookup = {row["key"]: row for row in states}
    streams = replication_streams(master_seed, max(cell.reps for cell in cells))
    pending = []
    for cell_index, cell in enumerate(cells):
        for rep in range(cell.reps):
            key = f"cell{cell_index:02d}-rep{rep:04d}"
            path = output / "replications" / f"{key}.parquet"
            if key in lookup and lookup[key]["status"] == "finished" and path.exists():
                continue
            ss = streams[rep]
            state = dict(key=key, run_id=output.name, cell=cell.label, rep=rep, entropy=ss.entropy,
                         spawn_key=json.dumps(ss.spawn_key), started_at=now(), finished_at=None,
                         status="running")
            lookup[key] = state
            pending.append((cell, rep, ss, key))
    atomic_parquet(pd.DataFrame(lookup.values()), state_path)
    completed = Parallel(n_jobs=n_jobs, return_as="generator_unordered")(
        delayed(worker)(cell, rep, ss, cal, dgm, est_cfg, output, save_data, key)
        for cell, rep, ss, key in pending)
    for key in completed:
        lookup[key]["status"] = "finished"
        lookup[key]["finished_at"] = now()
        atomic_parquet(pd.DataFrame(lookup.values()), state_path)
    frames = [pd.read_parquet(output / "replications" / f"{key}.parquet") for key in lookup]
    estimates = pd.concat(frames, ignore_index=True).sort_values(["cell", "rep", "arm", "cycle"])
    atomic_parquet(estimates, output / "estimates.parquet")
    performance(estimates).to_csv(output / "performance.csv", index=False)
    runtime = estimates.groupby(["run_id", "cell", "rep", "arm"], as_index=False).seconds.sum()
    runtime.to_csv(output / "runtime.csv", index=False)
    return output


def replay_state(state, cell, cal, dgm, est_cfg):
    spawn_key = state["spawn_key"]
    if isinstance(spawn_key, str):
        spawn_key = json.loads(spawn_key)
    ss = np.random.SeedSequence(int(state["entropy"]), spawn_key=tuple(spawn_key))
    shocks = draw_shocks(ss, cal.n_stores, dgm.history_weeks + dgm.cycles, cal, dgm)
    result = run_replication(cell, int(state["rep"]), shocks, cal, dgm, est_cfg)
    result.attrs.clear()
    result["run_id"] = state["run_id"]
    return result