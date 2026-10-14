from ktsim.rng import replication_streams


def test_stage_seed_separation():
    sequences = [
        replication_streams(42, 100, stage)
        for stage in ["validation", "diagnostic", "pilot", "main"]
    ]
    assert len({tuple(ss.generate_state(4)) for group in sequences for ss in group}) == 400
    for index, group in enumerate(sequences):
        assert all(ss.spawn_key[0] == index for ss in group)
