"""Execution-only resume: verify original scientific inputs; preserve their manifest."""
import argparse
import hashlib
import json
import logging
import subprocess
from pathlib import Path

import pandas as pd

from ktsim.config import Calibration, CellConfig, DGMConfig
from ktsim.io import sha256, week_table
from ktsim.pilot import atomic_json, run_pilot
from ktsim.protocol import validate_protocol
from ktsim.report import environment, make_report

ROOT = Path('/workspace/known-truth-pricing-sim')
OUTPUT = ROOT / 'outputs/diagnostic/s2-diagnostic-20261014'


def prepare():
    manifest = json.loads((OUTPUT / 'manifest.json').read_text())
    if subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip():
        raise ValueError('Scientific resume requires a clean checkout')
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() != manifest['commit']:
        raise ValueError('Original commit changed')
    if environment() != manifest['environment']:
        raise ValueError('Original software/hardware environment changed')
    frozen = {k: v for k, v in manifest.items() if k not in ('fingerprint', 'execution_history')}
    frozen['figures'] = []
    # asdict originally serialized numeric store keys; restore their types for
    # the exact original sort_keys fingerprint, rather than string sorting.
    frozen['dgm'] = dict(frozen['dgm'])
    frozen['dgm']['store_zones'] = {int(k): v for k, v in frozen['dgm']['store_zones'].items()}
    frozen['calibration'] = {env: dict(cal) for env, cal in frozen['calibration'].items()}
    for cal in frozen['calibration'].values():
        for field in ('alpha_s', 'mu_z'):
            cal[field] = {int(k): v for k, v in cal[field].items()}
    digest = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    if digest != manifest['fingerprint']:
        raise ValueError('Original manifest fingerprint is invalid')
    for group in ('config_checksums', 'source_checksums'):
        for path, expected in manifest[group].items():
            if sha256(path) != expected:
                raise ValueError(f'Changed frozen input: {path}')
    # Raw movement archives are not read by S2. Verify every simulation input;
    # retain the original raw-archive provenance without rebuilding calibration.
    for path, expected in manifest['checksums'].items():
        if path.startswith('data/calibration/') or path == 'data/fixtures/week_decode.csv':
            if sha256(path) != expected:
                raise ValueError(f'Changed simulation input: {path}')
    checks = json.loads(Path('data/calibration/checks.json').read_text())
    if checks != manifest['calibration_checks']:
        raise ValueError('Calibration checks changed')
    calibrations = {}
    for env, expected in manifest['calibration'].items():
        path = Path(f'data/calibration/calibration_{env}.json')
        if json.loads(path.read_text()) != expected:
            raise ValueError(f'Calibration changed: {env}')
        audit = json.loads(Path(f'data/calibration/coverage_audit_{env}.json').read_text())
        window = Path(f'data/calibration/coverage_audit_{env}_window.json')
        if window.exists():
            audit['calibration_window_audit'] = json.loads(window.read_text())
        if audit != manifest['coverage_audits'][env]:
            raise ValueError(f'Coverage audit changed: {env}')
        calibrations[env] = Calibration.load(path)
    validate_protocol(manifest, scientific=True, stage='diagnostic')
    assert manifest['stage'] == 'diagnostic' and not manifest['synthetic'] and not manifest['dirty']
    dgm_raw = dict(manifest['dgm'])
    dgm_raw['store_zones'] = {int(k): v for k, v in dgm_raw['store_zones'].items()}
    dgm = DGMConfig(**dgm_raw)
    dgm.calendar = week_table(Path('data/fixtures/week_decode.csv'))
    cells = [CellConfig(**cell) for cell in manifest['cells']]
    states = pd.read_parquet(OUTPUT / 'states.parquet')
    for key in states.loc[states.status.eq('finished'), 'key']:
        for path in (OUTPUT/'replications'/f'{key}.parquet', OUTPUT/'replications'/f'{key}.state.json', OUTPUT/'storeweek'/f'{key}.parquet'):
            if not path.exists():
                raise ValueError(f'Missing completed checkpoint: {path}')
    assert sum(c.reps for c in cells) == 96 and dgm.cycles == 104
    print(f'Frozen inputs verified; {states.status.eq("finished").sum()}/96 complete; resume with 4 workers', flush=True)
    return manifest, cells, calibrations, dgm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    manifest, cells, calibrations, dgm = prepare()
    if args.check_only:
        return
    run_pilot(cells, calibrations, dgm, manifest['estimators'], manifest['master_seed'],
              OUTPUT, manifest, n_jobs=4, resume=True,
              save_data=manifest['save_data'], save_storeweek=manifest['save_storeweek'])
    # Execution history is derived provenance, like report figure paths. Preserve
    # the original fingerprint and scientific inputs, including initial n_jobs=2.
    saved = json.loads((OUTPUT / 'manifest.json').read_text())
    saved['execution_history'] = json.loads((OUTPUT / 'execution_history.json').read_text())
    atomic_json(saved, OUTPUT / 'manifest.json')
    print('Report:', make_report(OUTPUT), flush=True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    main()
