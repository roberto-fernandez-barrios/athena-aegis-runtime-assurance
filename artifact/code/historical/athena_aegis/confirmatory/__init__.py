"""Confirmatory design utilities; importing this package never submits a job."""

from .randomization import assignment_digest, generate_assignments

__all__ = ["assignment_digest", "generate_assignments"]
