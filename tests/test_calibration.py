import itertools

import pytest

from nwps import half_life_from_retention, nwps, positional_credit


def test_half_life_calibration_targets_declared_retention():
    for d, r in [(1, 0.5), (2, 0.8), (5, 0.7), (10, 0.9)]:
        h = half_life_from_retention(d, r)
        assert positional_credit(d, h) == pytest.approx(r, rel=1e-12)


def test_same_h_controls_reference_and_displacement_persistence():
    h = 3.0
    rho = 2 ** (-1 / h)
    from nwps import reference_weights
    w = reference_weights(20, h)
    assert w[1] / w[0] == pytest.approx(rho)
    assert positional_credit(2, h) / positional_credit(1, h) == pytest.approx(rho)
