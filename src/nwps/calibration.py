from __future__ import annotations

import math
from collections.abc import Iterable

from .core import _log_rho, _validate_half_life, reference_weights


def half_life_from_retention(displacement: float, retained_credit: float) -> float:
    if not math.isfinite(float(displacement)) or displacement <= 0:
        raise ValueError("displacement must be a finite positive number")
    if not math.isfinite(float(retained_credit)) or not 0.0 < retained_credit < 1.0:
        raise ValueError("retained_credit must be a finite number in (0, 1)")
    return -float(displacement) * math.log(2.0) / math.log(float(retained_credit))


def uniform_permutation_baseline(k: int, half_life: float) -> float:
    """Expected NWPS for a uniformly random complete permutation."""
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer")
    h = _validate_half_life(half_life)
    log_rho = _log_rho(h)
    weights = reference_weights(k, h)

    # O(k^2) is intentionally explicit and numerically robust. Calibration
    # baselines are typically computed once per (k, h), not per query.
    expected = []
    for i in range(k):
        avg_credit = math.fsum(
            math.exp(log_rho * abs(i - j)) for j in range(k)
        ) / k
        expected.append(weights[i] * avg_credit)
    return math.fsum(expected)


def nwps_skill(score: float, null_expectation: float) -> float:
    if not math.isfinite(float(score)) or not -1e-12 <= score <= 1.0 + 1e-12:
        raise ValueError("score must be a finite number in [0, 1] up to floating-point tolerance")
    score = min(1.0, max(0.0, float(score)))
    if (
        not math.isfinite(float(null_expectation))
        or not 0.0 <= null_expectation < 1.0
    ):
        raise ValueError("null_expectation must be a finite number in [0, 1)")
    return (score - float(null_expectation)) / (1.0 - float(null_expectation))


def skill_minimum(null_expectation: float) -> float:
    if not 0.0 <= null_expectation < 1.0:
        raise ValueError("null_expectation must be in [0, 1)")
    return -null_expectation / (1.0 - null_expectation)
