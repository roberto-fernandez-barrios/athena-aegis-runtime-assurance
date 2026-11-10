"""Campaign B design constants (freeze candidate; author decisions of 2026-10-06).

Values reused unchanged from Campaign A are imported from the frozen A operator
projection so that the workload-context projection, fixed support, shots,
layout, transpiler seed set and calibration semantics cannot drift.
"""

from __future__ import annotations

from athena_aegis.confirmatory.context_projection import (  # noqa: F401  (re-exported, unchanged)
    BACKEND_ID,
    DATASET_DIGEST,
    FEATURES,
    FIXED_INITIAL_LAYOUT,
    FIXED_NATIVE_ROUTE,
    FIXED_PHYSICAL_QUBITS,
    INSTANCE_ALIAS,
    PRIMARY_OPTIMIZATION_LEVEL,
    PROJECTION_DEFINITION,
    PROJECTION_DEFINITION_DIGEST,
    RUNTIME_OPTIONS,
    RUNTIME_PRIMITIVE,
    SEMANTIC_HASH,
    SHOTS,
    STRATUM_FIELDS,
    TRANSPILE_SEEDS,
    WORKLOAD_ID,
)

CAMPAIGN_ID = "paper-2.5b-campaign-b"
INTENDED_PREREG_TAG = "paper25b-prereg-v1"
CAMPAIGN_A_FREEZE_TAG = "paper25-prereg-v1"

# --- availability gate (derived from Campaign A operational metadata, Section H)
GATE_MAX_PENDING_JOBS = 5
GATE_REQUIRED_STATUS_MESSAGE = "active"

# --- polling cadence (author decision 7)
DISCOVERY_INTERVAL_SECONDS = 1800
GATED_REPOLL_INTERVAL_SECONDS = 300
CONFIRMATION_INTERVAL_SECONDS = 600

# --- provider-aware waiting (author decision 8, 14)
JOB_STATUS_POLL_SCHEDULE = ((60.0, 2.0), (600.0, 10.0), (float("inf"), 30.0))  # (elapsed upper bound, poll interval)
CONTEXT_REPOLL_SECONDS = 60.0
WINDOW_WALL_CLOCK_CAP_SECONDS = 24 * 3600.0
PROVIDER_TERMINAL_STATES = ("DONE", "ERROR", "CANCELLED")
PROVIDER_WAITING_STATES = ("INITIALIZING", "QUEUED")

# --- physical design (author decision 5)
CALIBRATION_UNITS = 39
PRIMARY_PROBES = 6
VERIFICATION_PROBES = 2
BOOTSTRAP_WINDOW_JOBS = CALIBRATION_UNITS + VERIFICATION_PROBES  # 41
TRANSITION_WINDOW_JOBS = PRIMARY_PROBES + CALIBRATION_UNITS + VERIFICATION_PROBES  # 47
TARGET_USABLE_TRANSITION_WINDOWS = 10
TARGET_ACCEPTED_WINDOWS = 1 + TARGET_USABLE_TRANSITION_WINDOWS  # bootstrap + 10
MAX_CANDIDATE_EPOCHS = 16
BASE_JOBS = BOOTSTRAP_WINDOW_JOBS + TARGET_USABLE_TRANSITION_WINDOWS * TRANSITION_WINDOW_JOBS  # 511
MAX_ACQUISITION_RERUNS_PER_WINDOW = 1

# --- budget (author decision 15)
# bootstrap 41 + 16 candidate blocks x 47 + 16 reruns = 809 -> 810 (author closure 1, 2026-10-07)
HARD_MAX_JOBS = 810
HARD_MAX_QPU_SECONDS = 2430.0
ESTIMATED_QPU_SECONDS_PER_JOB = 3.0
PROVIDER_OBSERVED_QPU_SECONDS_PER_JOB = 2.0

# --- stopping (author decision 13, 17)
CALENDAR_CAP_DAYS = 90
NO_GATE_OPEN_OPPORTUNITY_DAYS = 30

# --- endpoint (author decision 2)
SERVICE_DEADLINE_SECONDS = 1800.0
MIN_RETAINED_RESULT_PROBES = 5
MAX_FALLBACK_PROBES = 1

# --- calibration rule (unchanged from A)
CALIBRATION_ALPHA = 0.05
NONCONFORMITY_SCORE_ID = "relative_frobenius_error_vs_exact_statevector_reference"
NONCONFORMITY_SCORE_DEFINITION = (
    "nonconformity(unit) = relative Frobenius error of the post-processed fidelity-kernel "
    "matrix against the exact IEEE-754 float64 statevector fidelity matrix of the frozen "
    "three-sample workload; greater is worse; calibration reference = the 39 scores of the "
    "accepted epoch; p=(1+count(cal>=s))/40; reject at p<=0.05."
)

# --- statistics (author decision 3)
PRIMARY_NULL_PI = 0.5
PRIMARY_ALPHA = 0.05
PRIMARY_REJECTION_MINIMUM_SUCCESSES = 9

# --- kill criteria (author decision 17)
KC_B3_UNBOUND_FATAL_FRACTION = 0.20
KC_B3_MINIMUM_TERMINAL_UNITS = 50

# --- randomization (author decision 11)
RANDOMIZATION_SEED_PHRASE = "ATHENA-AEGIS|Campaign-B|paper25b-prereg-v1|2026-10-06|PID2024-155693NB-C43"

POLICY_P2 = "P2-global-calibrated"
POLICY_P4 = "P4-context-oos-abstention"
POLICY_P5 = "P5-recovery-enforcement"

SERVED_SOURCE_HELD = "held_physical_result"
SERVED_SOURCE_FALLBACK = "classical_fallback"

UNIT_STATE_BOUND = "BOUND_SEALED"
UNIT_STATE_UNBOUND = "UNBOUND_AUDIT_ONLY"
UNIT_STATE_EXECUTION_FAILURE = "EXECUTION_FAILURE"
UNIT_STATE_CANCELLED_BY_RUNNER = "CANCELLED_BY_RUNNER"
UNIT_STATE_SUBMIT_FAILED = "SUBMIT_FAILED"
UNIT_STATE_NOT_SUBMITTED = "NOT_SUBMITTED"
UNIT_STATE_POST_WINDOW = "POST_WINDOW_TERMINAL_RESULT"
UNIT_STATE_PRE_PROVIDER_ERROR = "PRE_PROVIDER_IMPLEMENTATION_ERROR"  # AMENDMENT_002: local failure before the provider adapter was invoked; fatal, never rerun, never a submitted job
POST_WINDOW_CLASSIFICATION = "post_window_terminal_result"
POST_WINDOW_EXCLUSIONS = ("calibration", "P2/P4/P5 endpoints", "reference creation or repair", "window usability", "terminal reason")
