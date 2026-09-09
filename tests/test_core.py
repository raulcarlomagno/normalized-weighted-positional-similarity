import math

import pytest

from nwps import (
    NWPSResult,
    half_life_from_retention,
    nwps,
    nwps_skill,
    positional_credit,
    reference_weights,
    skill_minimum,
    uniform_permutation_baseline,
)


def test_identity_and_disjointness():
    ref = list("ABCDE")
    exact = nwps(ref, ref, half_life=3)
    disjoint = nwps(ref, list("VWXYZ"), half_life=3)
    assert isinstance(exact, NWPSResult)
    assert exact.score == pytest.approx(1.0)
    assert exact.lower_bound == exact.upper_bound
    assert exact.weighted_coverage_observed == pytest.approx(1.0)
    assert exact.conditional_positional_fidelity_observed == pytest.approx(1.0)
    assert disjoint.score == pytest.approx(0.0)
    assert disjoint.weighted_coverage_observed == pytest.approx(0.0)


def test_decomposition():
    ref = list("ABCDE")
    pred = list("XBCDE")
    res = nwps(ref, pred, half_life=3)
    c = res.weighted_coverage_observed
    f = res.conditional_positional_fidelity_observed
    assert res.score == pytest.approx(c * f)
    assert 1.0 - res.score == pytest.approx((1.0 - c) + c * (1.0 - f))


def test_one_step_credit_independent_of_k():
    h = 4.5
    expected = 2 ** (-1 / h)
    assert positional_credit(1, h) == pytest.approx(expected)
    for k in [2, 10, 100, 10_000]:
        w = reference_weights(k, h)
        assert math.fsum(w) == pytest.approx(1.0, abs=1e-12)


def test_extreme_half_lives_are_numerically_stable():
    for h in [1e-12, 1e-6, 1.0, 1e6, 1e12, 1e100, 1e300]:
        w = reference_weights(13, h)
        assert all(math.isfinite(x) and x >= 0 for x in w)
        assert math.fsum(w) == pytest.approx(1.0, abs=1e-12)
        res = nwps(list(range(13)), list(range(13)), half_life=h)
        assert res.score == pytest.approx(1.0, abs=1e-12)


def test_semantic_half_life_roundtrip():
    h = half_life_from_retention(2, 0.8)
    assert positional_credit(2, h) == pytest.approx(0.8)


def test_uniform_random_baseline_and_skill():
    b = uniform_permutation_baseline(5, 3)
    assert 0 < b < 1
    assert nwps_skill(1.0, b) == pytest.approx(1.0)
    assert nwps_skill(b, b) == pytest.approx(0.0)
    assert nwps_skill(0.0, b) == pytest.approx(skill_minimum(b))
    assert skill_minimum(b) < 0


def test_censored_result_has_stable_shape():
    ref = list("ABCDE")
    point = nwps(ref, list("ABCDE"), half_life=3)
    cens = nwps(ref, list("AB"), half_life=3, prediction_complete=False)
    assert isinstance(point, NWPSResult)
    assert isinstance(cens, NWPSResult)
    assert point.score is not None
    assert cens.score is None
    assert cens.is_censored
    assert cens.lower_bound <= cens.upper_bound <= 1.0
