from __future__ import annotations

import math
from collections.abc import Hashable, Iterable, Sequence
from typing import TypeVar

from .core import _log_rho, _rho, _validate_half_life, reference_weights
from .types import NWPSResult

T = TypeVar("T", bound=Hashable)
RankBlock = tuple[T, ...]


def _materialize_blocks(blocks: Iterable[Iterable[T]], *, name: str) -> tuple[RankBlock[T], ...]:
    out: list[RankBlock[T]] = []
    seen: set[T] = set()
    for raw in blocks:
        block = tuple(raw)
        if not block:
            raise ValueError(f"{name} contains an empty tie block")
        if len(set(block)) != len(block):
            raise ValueError(f"{name} contains duplicates inside a tie block")
        overlap = seen.intersection(block)
        if overlap:
            raise ValueError(f"{name} contains duplicate identifiers across blocks")
        seen.update(block)
        out.append(block)
    if not out:
        raise ValueError(f"{name} must contain at least one tie block")
    return tuple(out)


def _block_spans(blocks: Sequence[RankBlock[T]]) -> tuple[dict[T, tuple[int, int]], int]:
    spans: dict[T, tuple[int, int]] = {}
    start = 0
    for block in blocks:
        end = start + len(block) - 1
        for item in block:
            spans[item] = (start, end)
        start = end + 1
    return spans, start


def _distance_to_interval(position: int, interval: tuple[int, int]) -> int:
    a, b = interval
    if position < a:
        return a - position
    if position > b:
        return position - b
    return 0


def _expected_tie_credit(
    pred_interval: tuple[int, int],
    ref_interval: tuple[int, int],
    log_rho: float,
) -> float:
    c, d = pred_interval
    vals = [
        math.exp(log_rho * _distance_to_interval(rank, ref_interval))
        for rank in range(c, d + 1)
    ]
    return math.fsum(vals) / len(vals)


def nwps_tied(
    reference_blocks: Iterable[Iterable[T]],
    predicted_blocks: Iterable[Iterable[T]],
    *,
    half_life: float,
    prediction_complete: bool = True,
    censoring_upper: str = "itemwise",
) -> NWPSResult:
    """Compute tie-aware NWPS for ordered tie blocks.

    Reference ties mean indifference: each item in a reference block receives
    the block's total positional mass divided equally. Prediction ties mean
    uncertainty: each item receives expected positional credit under uniform
    resolution among the positions occupied by its prediction block.

    The current tie-aware censoring upper bound is an itemwise relaxation.
    Strict rankings can use the tighter joint-assignment bound in ``nwps``.
    """
    h = _validate_half_life(half_life)
    if censoring_upper != "itemwise":
        raise ValueError("tie-aware censoring currently supports only 'itemwise'")

    ref_blocks = _materialize_blocks(reference_blocks, name="reference")
    pred_blocks = _materialize_blocks(predicted_blocks, name="predicted")
    ref_spans, k = _block_spans(ref_blocks)
    pred_spans, m = _block_spans(pred_blocks)

    base_weights = reference_weights(k, h)
    item_weights: dict[T, float] = {}
    cursor = 0
    for block in ref_blocks:
        mass = math.fsum(base_weights[cursor : cursor + len(block)])
        each = mass / len(block)
        for item in block:
            item_weights[item] = each
        cursor += len(block)

    log_rho = _log_rho(h)
    contributions: list[float] = []
    coverage_parts: list[float] = []
    upper_extra: list[float] = []

    for item, ref_interval in ref_spans.items():
        weight = item_weights[item]
        pred_interval = pred_spans.get(item)
        if pred_interval is not None:
            credit = _expected_tie_credit(pred_interval, ref_interval, log_rho)
            contributions.append(weight * credit)
            coverage_parts.append(weight)
        elif not prediction_complete:
            _, ref_end = ref_interval
            min_disp = max(0, m - ref_end)
            upper_extra.append(weight * math.exp(log_rho * min_disp))

    lower = math.fsum(contributions)
    coverage = math.fsum(coverage_parts)
    positional = lower / coverage if coverage > 0.0 else 0.0

    if prediction_complete:
        upper = lower
        method = "point"
    else:
        upper = min(1.0, lower + math.fsum(upper_extra))
        method = "itemwise-relaxation"

    return NWPSResult(
        lower_bound=lower,
        upper_bound=upper,
        weighted_coverage_observed=coverage,
        conditional_positional_fidelity_observed=positional,
        half_life=h,
        reference_depth=k,
        observed_prediction_depth=m,
        is_censored=not prediction_complete,
        upper_bound_method=method,
    )
