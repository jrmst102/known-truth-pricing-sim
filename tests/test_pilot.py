import pandas as pd
import pytest

from ktsim.config import CellConfig
from ktsim.pilot import replay_state, run_pilot
from ktsim.report import make_report


def test_checkpoint_resume_report_and_replay(tmp_path, cal, dgm):
    dgm.cycles = 2
    cells = [CellConfig("P0", -1.06, 0., 0., 0., 2, ["M1"], ["greedy", "oracle"])]
    manifest = dict(fingerprint="test", commit="test", master_seed=42, synthetic=True)
    output = tmp_path / "run"
    run_pilot(cells, cal, dgm, {"M1_ols": {}}, 42, output, manifest, n_jobs=2, save_data=True)
    first = pd.read_parquet(output / "estimates.parquet")
    states = pd.read_parquet(output / "states.parquet")
    assert states.status.eq("finished").all()
    run_pilot(cells, cal, dgm, {"M1_ols": {}}, 42, output, manifest, resume=True, save_data=True)
    pd.testing.assert_frame_equal(first, pd.read_parquet(output / "estimates.parquet"))
    replay = replay_state(states.iloc[0].to_dict(), cells[0], cal, dgm, {"M1_ols": {}})
    original = first[first.rep.eq(states.rep.iloc[0])].sort_values(["arm", "cycle"])
    pd.testing.assert_frame_equal(original.drop(columns="seconds").reset_index(drop=True),
                                  replay.drop(columns="seconds").sort_values(["arm", "cycle"])
                                  .reset_index(drop=True), check_exact=True)
    path = make_report(output)
    assert "Synthetic fixture" in path.read_text()
    assert (output / "figures/p0_elasticity.png").exists()
    assert len(list((output / "simulated").glob("*.parquet"))) == 2
    with pytest.raises(ValueError, match="Resume inputs differ"):
        run_pilot(cells, cal, dgm, {"M1_ols": {}}, 42, output, dict(fingerprint="changed"), resume=True)