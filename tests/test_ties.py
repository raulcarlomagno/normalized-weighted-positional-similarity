import pytest

from nwps import nwps_tied


def test_reference_tie_internal_swap_is_free():
    ref = [("A",), ("B", "C"), ("D",)]
    p1 = [("A",), ("B",), ("C",), ("D",)]
    p2 = [("A",), ("C",), ("B",), ("D",)]
    s1 = nwps_tied(ref, p1, half_life=3).score
    s2 = nwps_tied(ref, p2, half_life=3).score
    assert s1 == pytest.approx(1.0)
    assert s2 == pytest.approx(1.0)


def test_prediction_tie_against_strict_reference_is_partial_credit():
    ref = [("A",), ("B",), ("C",)]
    pred = [("A", "B"), ("C",)]
    score = nwps_tied(ref, pred, half_life=3).score
    assert score is not None
    assert 0.0 < score < 1.0


def test_identical_tie_blocks_are_exact():
    blocks = [("A",), ("B", "C"), ("D", "E", "F")]
    res = nwps_tied(blocks, blocks, half_life=2)
    assert res.score == pytest.approx(1.0)
    assert res.weighted_coverage_observed == pytest.approx(1.0)


def test_tied_censoring_interval():
    ref = [("A",), ("B", "C"), ("D",)]
    pred = [("A",)]
    res = nwps_tied(ref, pred, half_life=3, prediction_complete=False)
    assert res.is_censored
    assert res.lower_bound <= res.upper_bound <= 1.0


def test_singleton_blocks_match_strict_nwps():
    from nwps import nwps
    ref = list("ABCDE")
    pred = list("ACBED")
    strict = nwps(ref, pred, half_life=3).score
    tied = nwps_tied([(x,) for x in ref], [(x,) for x in pred], half_life=3).score
    assert strict == pytest.approx(tied)
