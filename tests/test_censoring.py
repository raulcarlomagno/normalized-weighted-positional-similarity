from itertools import permutations

import pytest

from nwps import nwps


def test_tight_bound_no_looser_than_itemwise():
    ref = list("ABCDEFG")
    observed = list("AB")
    tight = nwps(ref, observed, half_life=2.5, prediction_complete=False, censoring_upper="tight")
    loose = nwps(ref, observed, half_life=2.5, prediction_complete=False, censoring_upper="itemwise")
    assert tight.lower_bound == pytest.approx(loose.lower_bound)
    assert tight.upper_bound <= loose.upper_bound + 1e-12


def test_tight_bound_contains_all_small_strict_completions():
    ref = list("ABCD")
    observed = ["A"]
    bound = nwps(ref, observed, half_life=2, prediction_complete=False, censoring_upper="tight")
    unseen = ["B", "C", "D"]
    for tail in permutations(unseen):
        full = observed + list(tail)
        score = nwps(ref, full, half_life=2).score
        assert score is not None
        assert bound.lower_bound - 1e-12 <= score <= bound.upper_bound + 1e-12


def test_itemwise_is_documented_relaxation():
    ref = list("ABCDEFGH")
    observed = ["A"]
    loose = nwps(ref, observed, half_life=3, prediction_complete=False, censoring_upper="itemwise")
    tight = nwps(ref, observed, half_life=3, prediction_complete=False, censoring_upper="tight")
    assert loose.upper_bound >= tight.upper_bound
    assert loose.upper_bound_method == "itemwise-relaxation"
    assert tight.upper_bound_method == "joint-assignment"
