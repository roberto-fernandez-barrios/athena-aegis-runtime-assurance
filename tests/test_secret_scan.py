from scripts.secret_scan import PATTERNS, candidate_files


def detected(value: str) -> bool:
    return any(pattern.search(value) for pattern in PATTERNS)


def test_secret_patterns_cover_api_keys_crns_and_raw_job_ids_without_literals():
    api_key = "XY" + "_" + "a" * 40
    crn = "crn" + ":v1:bluemix:public:quantum-computing:eu-de:a/b:c::"
    raw_job = '{"raw_' + 'job_id":"' + "a1" * 12 + '"}'
    assert detected(api_key)
    assert detected(crn)
    assert detected(raw_job)
    assert not detected('{"job_id":"hmac-sha256:' + "a" * 64 + '"}')


def test_ignored_local_environment_is_not_a_scan_candidate():
    assert all(path.name != ".env" for path in candidate_files())
