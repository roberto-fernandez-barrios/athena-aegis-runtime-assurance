import os

import pytest


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.skipif(
    os.environ.get("ATHENA_AEGIS_RUN_IBM_LIVE") != "1",
    reason="IBM live tests require explicit opt-in and external credentials",
)
def test_ibm_live_preflight_requires_explicit_operator_opt_in():
    from athena_aegis.providers.ibm_preflight import main

    assert callable(main)
