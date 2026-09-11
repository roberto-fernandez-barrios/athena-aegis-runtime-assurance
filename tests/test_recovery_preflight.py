from experiments.run_recovery_preflight import build


def test_all_recovery_state_transitions_have_verified_envelopes():
    payload = build()
    records = {record["requested_action"]: record for record in payload["records"]}
    assert set(records) == {"HOLD", "RERUN", "RECALIBRATE", "FALLBACK", "ROLLBACK", "BLOCK"}
    assert not records["HOLD"]["served"]
    assert not records["BLOCK"]["served"]
    for action in ("RERUN", "RECALIBRATE", "FALLBACK", "ROLLBACK"):
        assert records[action]["served"]
        assert records[action]["recovery_attempted"]
        assert records[action]["envelope"]["envelope_digest"]
