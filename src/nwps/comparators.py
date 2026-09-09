from __future__ import annotations

import math
from collections.abc import Hashable, Iterable, Sequence
from itertools import permutations, product
from typing import TypeVar

T = TypeVar("T", bound=Hashable)


def _strict_positions(reference: Sequence[T], predicted: Sequence[T]) -> dict[T, int]:
    if len(set(reference)) != len(reference):
        raise ValueError("reference contains duplicate identifiers")
    if len(set(predicted)) != len(predicted):
        raise ValueError("predicted contains duplicate identifiers")
    return {item: i for i, item in enumerate(predicted)}


def ws_similarity(reference: Sequence[T], predicted: Sequence[T]) -> float:
    """Sałabun-Urbaniak WS coefficient for complete conjoint strict rankings.

    The reference ranking supplies x_i; the prediction supplies y_i. Formula:
        1 - sum 2^{-x_i} |x_i-y_i| / max(|x_i-1|, |x_i-n|)
    with one-based ranks.
    """
    if len(reference) != len(predicted) or set(reference) != set(predicted):
        raise ValueError("WS comparator requires complete conjoint rankings")
    n = len(reference)
    if n == 0:
        raise ValueError("rankings must be non-empty")
    if n == 1:
        return 1.0
    pos = _strict_positions(reference, predicted)
    loss = 0.0
    for i0, item in enumerate(reference):
        x = i0 + 1
        y = pos[item] + 1
        denom = max(abs(x - 1), abs(x - n))
        loss += (2.0 ** (-x)) * abs(x - y) / denom
    return 1.0 - loss


def rdq_m1(
    reference: Sequence[T],
    predicted: Sequence[T],
    *,
    k: int | None = None,
    output_weights: Sequence[float] | None = None,
) -> float:
    """RDQ M1 for a strict ordered reference list.

    This is a faithful implementation of the strict-tier case of Zhou,
    Moschitti & Class (2026). Duplicated predicted items earn credit only at
    their first occurrence, matching the paper.
    """
    if not reference:
        raise ValueError("reference must be non-empty")
    if len(set(reference)) != len(reference):
        raise ValueError("reference must be strict for this comparator")
    if k is None:
        k = len(predicted)
    k = min(k, len(predicted))
    n_ref = len(reference)
    ref_rank = {item: i + 1 for i, item in enumerate(reference)}
    if output_weights is None:
        output_weights = [1.0] * max(k, min(k, n_ref))
    if len(output_weights) < k:
        raise ValueError("output_weights shorter than k")
    denom_n = min(k, n_ref)
    denom = math.fsum(output_weights[:denom_n])
    if denom <= 0:
        raise ValueError("output weights must yield positive normalization")

    seen: set[T] = set()
    num = 0.0
    for i0, item in enumerate(predicted[:k]):
        if item in seen:
            continue
        seen.add(item)
        gamma = ref_rank.get(item)
        if gamma is None:
            continue
        expected = i0 + 1
        penalty = min(1.0, expected / gamma)
        num += output_weights[i0] * penalty
    return num / denom


def rdq_m2(
    reference: Sequence[T],
    predicted: Sequence[T],
    *,
    alpha: float = 1.0,
    lam: float = 0.2,
    k: int | None = None,
    output_weights: Sequence[float] | None = None,
) -> float:
    """RDQ M2 for a strict ordered reference list.

    Penalty:
      exp(-d / (sqrt(|R|) * alpha * (1 + lam*(gamma-1))))
    where d is the difference between the expected ORL rank at output position
    and the item's ORL rank. For a strict ORL, expected rank equals output
    position, continuing beyond |R|.
    """
    if alpha <= 0 or lam < 0:
        raise ValueError("alpha must be positive and lam non-negative")
    if not reference:
        raise ValueError("reference must be non-empty")
    if len(set(reference)) != len(reference):
        raise ValueError("reference must be strict for this comparator")
    if k is None:
        k = len(predicted)
    k = min(k, len(predicted))
    n_ref = len(reference)
    ref_rank = {item: i + 1 for i, item in enumerate(reference)}
    if output_weights is None:
        output_weights = [1.0] * max(k, min(k, n_ref))
    if len(output_weights) < k:
        raise ValueError("output_weights shorter than k")
    denom_n = min(k, n_ref)
    denom = math.fsum(output_weights[:denom_n])
    if denom <= 0:
        raise ValueError("output weights must yield positive normalization")

    seen: set[T] = set()
    num = 0.0
    root_n = math.sqrt(n_ref)
    for i0, item in enumerate(predicted[:k]):
        if item in seen:
            continue
        seen.add(item)
        gamma = ref_rank.get(item)
        if gamma is None:
            continue
        expected = i0 + 1
        d = abs(expected - gamma)
        scale = root_n * alpha * (1.0 + lam * (gamma - 1))
        penalty = math.exp(-d / scale)
        num += output_weights[i0] * penalty
    return num / denom


def rdq_vertical_weights(k: int) -> tuple[float, ...]:
    """Default vertical-layout weights reported by Zhou et al. (2026)."""
    prefix = [
        1.0,
        0.9,
        0.8,
        0.8,
        0.7,
        0.6,
        0.5,
        0.5,
        0.4,
        0.4,
        0.4,
        0.3,
        0.3,
        0.2,
        0.2,
        0.2,
    ]
    if k <= len(prefix):
        return tuple(prefix[:k])
    return tuple(prefix + [0.1] * (k - len(prefix)))


def rbo_extrapolated(reference: Sequence[T], predicted: Sequence[T], phi: float = 0.9) -> float:
    """Finite equal-depth extrapolated RBO point estimate.

    For depth k = max(len(reference), len(predicted)), this uses the common
    extrapolated form:
      (1-phi) * sum_{d=1}^k A_d phi^{d-1} + A_k phi^k,
    where A_d is prefix overlap proportion. For rankings shorter than k, their
    full observed set is retained at deeper d.
    """
    if not 0.0 < phi < 1.0:
        raise ValueError("phi must be in (0, 1)")
    if len(set(reference)) != len(reference) or len(set(predicted)) != len(predicted):
        raise ValueError("RBO comparator expects strict rankings")
    k = max(len(reference), len(predicted))
    if k == 0:
        raise ValueError("rankings must be non-empty")
    seen_r: set[T] = set()
    seen_p: set[T] = set()
    terms = []
    a_k = 0.0
    for d in range(1, k + 1):
        if d <= len(reference):
            seen_r.add(reference[d - 1])
        if d <= len(predicted):
            seen_p.add(predicted[d - 1])
        overlap = len(seen_r.intersection(seen_p))
        a_d = overlap / d
        a_k = a_d
        terms.append((1.0 - phi) * a_d * (phi ** (d - 1)))
    return math.fsum(terms) + a_k * (phi ** k)


def rba_score(reference: Sequence[T], predicted: Sequence[T], phi: float = 0.9) -> float:
    """Rank-Biased Alignment lower score for strict rankings.

    Formula from Moffat et al. (2024):
      (1-phi)/phi * sum_{e in intersection}
      phi^(rank_R(e)/2 + rank_P(e)/2)
    with one-based ranks.
    """
    if not 0.0 < phi < 1.0:
        raise ValueError("phi must be in (0, 1)")
    pos_r = {x: i + 1 for i, x in enumerate(reference)}
    pos_p = {x: i + 1 for i, x in enumerate(predicted)}
    common = pos_r.keys() & pos_p.keys()
    return ((1.0 - phi) / phi) * math.fsum(
        phi ** ((pos_r[x] + pos_p[x]) / 2.0) for x in common
    )


def rba_upper(reference: Sequence[T], predicted: Sequence[T], phi: float = 0.9) -> float:
    """RBA upper bound for strict finite rankings.

    This implements the group-free augmentation described by Moffat et al.:
    missing items are appended to the opposite ranking in source-priority order,
    then an infinite agreement residual phi^|union| is added.
    """
    if not 0.0 < phi < 1.0:
        raise ValueError("phi must be in (0, 1)")
    if len(set(reference)) != len(reference) or len(set(predicted)) != len(predicted):
        raise ValueError("RBA comparator expects strict rankings")
    ref_set = set(reference)
    pred_set = set(predicted)
    aug_r = list(reference) + [x for x in predicted if x not in ref_set]
    aug_p = list(predicted) + [x for x in reference if x not in pred_set]
    union_n = len(set(aug_r) | set(aug_p))
    return min(1.0, rba_score(aug_r, aug_p, phi=phi) + phi ** union_n)


def tau_ap(reference: Sequence[T], predicted: Sequence[T]) -> float:
    """Directional AP correlation tau_AP for complete conjoint strict rankings.

    Traverses the predicted ranking from top to bottom; for each item at
    predicted position i, counts items above it that are also above it in the
    reference. This is the Yilmaz-Aslam-Robertson construction with reference
    ranking supplying the desired pairwise order.
    """
    if len(reference) != len(predicted) or set(reference) != set(predicted):
        raise ValueError("tau_AP requires complete conjoint rankings")
    n = len(reference)
    if n < 2:
        return 1.0
    ref_pos = {x: i for i, x in enumerate(reference)}
    parts = []
    for i in range(1, n):
        item = predicted[i]
        concordant = sum(
            1 for above in predicted[:i] if ref_pos[above] < ref_pos[item]
        )
        parts.append(concordant / i)
    return (2.0 / (n - 1)) * math.fsum(parts) - 1.0


def weighted_kendall(reference: Sequence[T], predicted: Sequence[T]) -> float:
    """Vigna/SciPy additive hyperbolic weighted Kendall with reference ranks."""
    if len(reference) != len(predicted) or set(reference) != set(predicted):
        raise ValueError("weighted Kendall requires complete conjoint rankings")
    try:
        import numpy as np
        from scipy.stats import weightedtau
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("weighted Kendall comparator requires numpy/scipy") from exc
    pos = {x: i for i, x in enumerate(predicted)}
    x = np.arange(len(reference), dtype=float)
    y = np.array([pos[item] for item in reference], dtype=float)
    rank = np.arange(len(reference), dtype=int)
    return float(weightedtau(x, y, rank=rank, additive=True).statistic)


def canberra_distance(reference: Sequence[T], predicted: Sequence[T]) -> float:
    """Canberra distance on complete conjoint permutations (one-based ranks)."""
    if len(reference) != len(predicted) or set(reference) != set(predicted):
        raise ValueError("Canberra comparator requires complete conjoint rankings")
    pos = {x: i + 1 for i, x in enumerate(predicted)}
    return math.fsum(
        abs((i + 1) - pos[item]) / ((i + 1) + pos[item])
        for i, item in enumerate(reference)
    )


def spearman_footrule(reference: Sequence[T], predicted: Sequence[T]) -> float:
    """Classical Spearman Footrule distance on complete conjoint rankings."""
    if len(reference) != len(predicted) or set(reference) != set(predicted):
        raise ValueError("Footrule comparator requires complete conjoint rankings")
    pos = {x: i for i, x in enumerate(predicted)}
    return float(sum(abs(i - pos[item]) for i, item in enumerate(reference)))


def reference_weighted_footrule_similarity(
    reference: Sequence[T],
    predicted: Sequence[T],
    weights: Sequence[float],
) -> float:
    """A concrete element-weighted Footrule comparator normalized to [0, 1].

    The distance is sum_i w_i |i - pi(item_i)|. The denominator is the exact
    maximum assignment cost for the supplied nonnegative reference-element
    weights, computed via the Hungarian algorithm. This is a comparator in the
    generalized/weighted Footrule family, not a reimplementation of the full
    Kumar-Vassilvitskii framework with arbitrary position/element distances.
    """
    if len(reference) != len(predicted) or set(reference) != set(predicted):
        raise ValueError("weighted Footrule requires complete conjoint rankings")
    n = len(reference)
    if len(weights) != n or any(w < 0 for w in weights):
        raise ValueError("weights must be nonnegative and match ranking length")
    if n <= 1:
        return 1.0
    try:
        import numpy as np
        from scipy.optimize import linear_sum_assignment
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("weighted Footrule comparator requires numpy/scipy") from exc

    pos = {x: i for i, x in enumerate(predicted)}
    observed = math.fsum(weights[i] * abs(i - pos[item]) for i, item in enumerate(reference))
    cost = np.array(
        [[weights[i] * abs(i - j) for j in range(n)] for i in range(n)],
        dtype=float,
    )
    rows, cols = linear_sum_assignment(-cost)
    worst = float(cost[rows, cols].sum())
    if worst == 0.0:
        return 1.0
    return 1.0 - observed / worst


def _linear_extensions(blocks: Sequence[Sequence[T]], max_extensions: int = 200_000) -> list[tuple[T, ...]]:
    counts = [math.factorial(len(b)) for b in blocks]
    total = math.prod(counts)
    if total > max_extensions:
        raise ValueError(
            f"too many tie resolutions ({total}); increase max_extensions only for small benchmarks"
        )
    block_perms = [list(permutations(block)) for block in blocks]
    out: list[tuple[T, ...]] = []
    for combo in product(*block_perms):
        flat: list[T] = []
        for p in combo:
            flat.extend(p)
        out.append(tuple(flat))
    return out


def expected_rbo_over_ties(
    reference_blocks: Sequence[Sequence[T]],
    predicted_blocks: Sequence[Sequence[T]],
    *,
    phi: float = 0.9,
    max_extensions: int = 200_000,
) -> float:
    """Exact expected standard RBO over all tie linearizations for small cases.

    This is a controlled-benchmark helper, not claimed to be the closed-form
    Corsi-Urbano tie-aware RBO implementation. It provides a transparent exact
    expectation over all linear extensions and is useful for verifying that tie
    handling is not an artifact of arbitrary deterministic tie breaking.
    """
    refs = _linear_extensions(reference_blocks, max_extensions=max_extensions)
    preds = _linear_extensions(predicted_blocks, max_extensions=max_extensions)
    return math.fsum(
        rbo_extrapolated(r, p, phi=phi) for r in refs for p in preds
    ) / (len(refs) * len(preds))


def rbo_a_extrapolated(
    reference_blocks: Sequence[Sequence[T]],
    predicted_blocks: Sequence[Sequence[T]],
    *,
    phi: float = 0.9,
) -> float:
    """Corsi-Urbano RBO^a for complete finite tied rankings of equal depth.

    RBO^a interprets ties as uncertainty and equals expected bare RBO over all
    random tie breakings, but computes that expectation deterministically.
    This implementation uses their item contribution c_{e|d} and agreement
    A_d^a = (1/d) sum_e c_{e,R|d} c_{e,P|d}, followed by the standard finite
    extrapolated RBO point estimate. It is intended for complete finite
    controlled comparisons where both rankings span the same total depth.
    """
    if not 0.0 < phi < 1.0:
        raise ValueError("phi must be in (0, 1)")

    def spans(blocks: Sequence[Sequence[T]]):
        mapping = {}
        seen = set()
        start = 1
        for block in blocks:
            block = tuple(block)
            if not block:
                raise ValueError("tie blocks must be non-empty")
            if len(set(block)) != len(block) or seen.intersection(block):
                raise ValueError("duplicate identifiers in tie blocks")
            end = start + len(block) - 1
            for item in block:
                mapping[item] = (start, end)
            seen.update(block)
            start = end + 1
        return mapping, start - 1

    sr, nr = spans(reference_blocks)
    sp, np_ = spans(predicted_blocks)
    if nr != np_:
        raise ValueError("this RBO^a comparator requires equal total depth")
    k = nr
    if k == 0:
        raise ValueError("rankings must be non-empty")
    universe = set(sr) | set(sp)

    def c(interval: tuple[int, int] | None, d: int) -> float:
        if interval is None:
            return 0.0
        t, b = interval
        if d < t:
            return 0.0
        if b <= d:
            return 1.0
        return (d - t + 1) / (b - t + 1)

    terms = []
    a_k = 0.0
    for d in range(1, k + 1):
        agreement = math.fsum(c(sr.get(e), d) * c(sp.get(e), d) for e in universe) / d
        a_k = agreement
        terms.append((1.0 - phi) * agreement * (phi ** (d - 1)))
    return math.fsum(terms) + a_k * (phi ** k)
