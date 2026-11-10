"""Campaign B (paper25b): a new prospective campaign, independent of Campaign A.

Importing this package never submits a provider job and never writes under the
sealed Campaign A namespace ``artifacts/confirmatory/campaign/``.  Every writer
in this package passes through :func:`athena_aegis.campaign_b.immutability.guard_write_path`.
"""

from athena_aegis.campaign_b.constants import CAMPAIGN_ID, INTENDED_PREREG_TAG

__all__ = ["CAMPAIGN_ID", "INTENDED_PREREG_TAG"]
