from __future__ import annotations

import math
from collections.abc import Hashable, Iterable, Sequence
from itertools import islice
from typing import TypeVar

from .types import NWPSResult

T = TypeVar("T", bound=Hashable)
_LN2 = math.log(2.0)


def _validate_half_life(half_life: float) -> float:
    if isinstance(half_life, bool) or not isinstance(half_life, (int, float)):
        raise ValueError("half_life must be a finite positive number")
    h = float(half_life)
    if not math.isfinite(h) or h <= 0.0:
        raise ValueError("half_life must be a finite positive number")
    return h


def _log_rho(half_life: float) -> float:
    return -_LN2 / half_life


def _rho(half_life: float) -> float:
    # Underflow to zero for extremely small half-lives is mathematically safe.
    return math.exp(_log_rho(half_life))


def _weight0(k: int, log_rho: float) -> float:
    """First normalized geometric weight, stable even when rho ~= 1."""
    numerator = -math.expm1(log_rho)
    denominator = -math.expm1(k * log_rho)
    if denominator == 0.0:
        # Only reachable after extreme floating-point collapse; use the limit.
        return 1.0 / k
    return numerator / denominator


def reference_weights(k: int, half_life: float) -> tuple[float, ...]:
    """Return normalized geometric reference weights."""
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer")
    h = _validate_half_life(half_life)
    log_rho = _log_rho(h)
    rho = math.exp(log_rho)
    w = _weight0(k, log_rho)
    out = []
    for _ in range(k):
        out.append(w)
        w *= rho
    # Normalize one final time to remove accumulated recurrence error.
    total = math.fsum(out)
    return tuple(x / total for x in out)


def positional_credit(displacement: int | float, half_life: float) -> float:
    """Exponential positional credit rho**displacement."""
    if displacement < 0:
        raise ValueError("displacement must be non-negative")
    h = _validate_half_life(half_life)
    return math.exp(_log_rho(h) * float(displacement))


def _strict_reference(
    reference: Iterable[T],
    k: int | None,
) -> tuple[tuple[T, ...], int]:
    if k is not None:
        if isinstance(k, bool) or not isinstance(k, int) or k < 1:
            raise ValueError("k must be a positive integer or None")
        ref = tuple(islice(reference, k))
        if len(ref) != k:
            raise ValueError("reference contains fewer than k items")
    else:
        ref = tuple(reference)
        k = len(ref)
        if k == 0:
            raise ValueError("reference must contain at least one item")
    if len(set(ref)) != k:
        raise ValueError("reference contains duplicate identifiers")
    return ref, k


def _prediction_positions(predicted: Iterable[T]) -> tuple[tuple[T, ...], dict[T, int]]:
    pred = tuple(predicted)
    if len(set(pred)) != len(pred):
        raise ValueError("predicted contains duplicate identifiers")
    return pred, {item: index for index, item in enumerate(pred)}


def _tight_censor_upper_strict(
    unseen: Sequence[tuple[int, float]],
    *,
    observed_depth: int,
    reference_depth: int,
    log_rho: float,
) -> float:
    """Jointly attainable upper contribution for unseen strict items.

    This solves a maximum-weight assignment between unseen reference items and
    future distinct output ranks. The candidate future positions
    ``m .. max(k-1, m+n-1)`` (zero-based) are sufficient: they include every
    reference target rank that lies beyond the censoring boundary and at least
    ``n`` future positions. Positions farther right are dominated for all items.

    SciPy is imported lazily so core point-valued NWPS remains lightweight.
    """
    if not unseen:
        return 0.0
    try:
        import numpy as np
        from scipy.optimize import linear_sum_assignment
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "tight censoring bounds require numpy and scipy"
        ) from exc

    n = len(unseen)
    first = observed_depth
    last = max(reference_depth - 1, observed_depth + n - 1)
    future_positions = list(range(first, last + 1))

    utility = np.empty((n, len(future_positions)), dtype=float)
    for row, (ref_pos, weight) in enumerate(unseen):
        for col, pred_pos in enumerate(future_positions):
            utility[row, col] = weight * math.exp(
                log_rho * abs(ref_pos - pred_pos)
            )

    rows, cols = linear_sum_assignment(-utility)
    return float(utility[rows, cols].sum())


def nwps(
    reference: Iterable[T],
    predicted: Iterable[T],
    *,
    half_life: float,
    k: int | None = None,
    prediction_complete: bool = True,
    censoring_upper: str = "itemwise",
) -> NWPSResult:
    """Compute NWPS for strict rankings.

    Parameters
    ----------
    reference:
        Privileged strict reference ranking.
    predicted:
        All observed predicted items. The prediction is not truncated at ``k``.
    half_life:
        Positive rank half-life ``h``.
    k:
        Number of reference items in scope. Defaults to the full reference.
    prediction_complete:
        If False, the observed prediction is interpreted as a right-censored
        prefix and an interval is returned.
    censoring_upper:
        ``"itemwise"`` (default) uses the dependency-free independent-item
        relaxation. ``"tight"`` solves a joint-assignment upper bound for
        unseen items and requires NumPy/SciPy.

    Returns
    -------
    NWPSResult
        Stable result object. Point estimates have equal lower/upper bounds.
    """
    h = _validate_half_life(half_life)
    ref, k = _strict_reference(reference, k)
    pred, position = _prediction_positions(predicted)

    if censoring_upper not in {"tight", "itemwise"}:
        raise ValueError("censoring_upper must be 'tight' or 'itemwise'")

    log_rho = _log_rho(h)
    rho = math.exp(log_rho)
    weight = _weight0(k, log_rho)

    contributions: list[float] = []
    coverage_weights: list[float] = []
    unseen: list[tuple[int, float]] = []
    itemwise_upper_extra: list[float] = []
    m = len(pred)

    for i, item in enumerate(ref):
        j = position.get(item)
        if j is not None:
            credit = math.exp(log_rho * abs(i - j))
            contributions.append(weight * credit)
            coverage_weights.append(weight)
        elif not prediction_complete:
            unseen.append((i, weight))
            min_disp = max(0, m - i)
            itemwise_upper_extra.append(weight * math.exp(log_rho * min_disp))
        weight *= rho

    lower = math.fsum(contributions)
    coverage = math.fsum(coverage_weights)
    positional = lower / coverage if coverage > 0.0 else 0.0

    if prediction_complete:
        return NWPSResult(
            lower_bound=lower,
            upper_bound=lower,
            weighted_coverage_observed=coverage,
            conditional_positional_fidelity_observed=positional,
            half_life=h,
            reference_depth=k,
            observed_prediction_depth=m,
            is_censored=False,
            upper_bound_method="point",
        )

    if censoring_upper == "itemwise":
        extra = math.fsum(itemwise_upper_extra)
        method = "itemwise-relaxation"
    else:
        extra = _tight_censor_upper_strict(
            unseen,
            observed_depth=m,
            reference_depth=k,
            log_rho=log_rho,
        )
        method = "joint-assignment"

    upper = min(1.0, lower + extra)
    return NWPSResult(
        lower_bound=lower,
        upper_bound=upper,
        weighted_coverage_observed=coverage,
        conditional_positional_fidelity_observed=positional,
        half_life=h,
        reference_depth=k,
        observed_prediction_depth=m,
        is_censored=True,
        upper_bound_method=method,
    )
