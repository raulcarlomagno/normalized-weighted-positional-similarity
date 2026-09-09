import math
from itertools import permutations

import pytest

from nwps import nwps, reference_weights, uniform_permutation_baseline


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
def test_exhaustive_permutations_bounds_and_identity(n):
    ref = tuple(range(n))
    values = []
    for pred in permutations(ref):
        res = nwps(ref, pred, half_life=2.75)
        assert res.score is not None
        assert -1e-12 <= res.score <= 1.0 + 1e-12
        values.append(res.score)
        if pred == ref:
            assert res.score == pytest.approx(1.0)
        else:
            assert res.score < 1.0
    assert max(values) == pytest.approx(1.0)


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6, 7])
def test_random_baseline_matches_exhaustive_average(n):
    ref = tuple(range(n))
    vals = [nwps(ref, p, half_life=3).score for p in permutations(ref)]
    empirical = math.fsum(v for v in vals if v is not None) / len(vals)
    analytic = uniform_permutation_baseline(n, 3)
    assert empirical == pytest.approx(analytic, abs=1e-12)


def test_head_weight_converges_to_nonzero_limit():
    h = 3
    rho = 2 ** (-1 / h)
    target = 1 - rho
    for k in [100, 1_000, 10_000]:
        top = reference_weights(k, h)[0]
        assert abs(top - target) < 0.01
