"""Provider adapters isolate cloud- and simulator-specific APIs."""

from athena_aegis.providers.base import (
    BackendSummary,
    CountsResult,
    ProviderAdapter,
    ProviderJobHandle,
    SubmissionRequest,
)
from athena_aegis.providers.selection import (
    BackendSelection,
    PILOT_BACKEND_SELECTION_RULE,
    select_pilot_backend,
)

__all__ = [
    "BackendSelection",
    "BackendSummary",
    "CountsResult",
    "PILOT_BACKEND_SELECTION_RULE",
    "ProviderAdapter",
    "ProviderJobHandle",
    "SubmissionRequest",
    "select_pilot_backend",
]
