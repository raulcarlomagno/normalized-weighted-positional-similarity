"""Normalized Weighted Positional Similarity (NWPS)."""

from .calibration import (
    half_life_from_retention,
    nwps_skill,
    skill_minimum,
    uniform_permutation_baseline,
)
from .core import nwps, positional_credit, reference_weights
from .ties import nwps_tied
from .types import NWPSResult

__all__ = [
    "NWPSResult",
    "half_life_from_retention",
    "nwps",
    "nwps_skill",
    "nwps_tied",
    "positional_credit",
    "reference_weights",
    "skill_minimum",
    "uniform_permutation_baseline",
]

__version__ = "0.1.0"

# Research comparators live in ``nwps.comparators`` and are intentionally not
# imported into the top-level namespace.
