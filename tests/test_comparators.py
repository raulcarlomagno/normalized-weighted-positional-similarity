import pytest

from nwps import reference_weights
from nwps.comparators import (
    canberra_distance,
    rba_upper,
    rbo_extrapolated,
    rdq_m1,
    rdq_m2,
    reference_weighted_footrule_similarity,
    tau_ap,
    weighted_kendall,
    ws_similarity,
)


def test_comparator_identity_anchors():
    ref = list("ABCDEFG")
    w = reference_weights(len(ref), 3)
    assert ws_similarity(ref, ref) == pytest.approx(1.0)
    assert rdq_m1(ref, ref, k=len(ref)) == pytest.approx(1.0)
    assert rdq_m2(ref, ref, k=len(ref)) == pytest.approx(1.0)
    assert rbo_extrapolated(ref, ref, phi=0.9) == pytest.approx(1.0)
    assert rba_upper(ref, ref, phi=0.9) == pytest.approx(1.0)
    assert tau_ap(ref, ref) == pytest.approx(1.0)
    assert weighted_kendall(ref, ref) == pytest.approx(1.0)
    assert canberra_distance(ref, ref) == pytest.approx(0.0)
    assert reference_weighted_footrule_similarity(ref, ref, w) == pytest.approx(1.0)


def test_correlation_comparator_reverse_anchors():
    ref = list("ABCDEFG")
    rev = ref[::-1]
    assert tau_ap(ref, rev) == pytest.approx(-1.0)
    assert weighted_kendall(ref, rev) == pytest.approx(-1.0)


def test_rbo_a_matches_standard_without_ties():
    from nwps.comparators import rbo_a_extrapolated
    ref = [("A",), ("B",), ("C",), ("D",)]
    pred = [("A",), ("C",), ("B",), ("D",)]
    flat_ref = [x[0] for x in ref]
    flat_pred = [x[0] for x in pred]
    assert rbo_a_extrapolated(ref, pred, phi=0.9) == pytest.approx(
        rbo_extrapolated(flat_ref, flat_pred, phi=0.9)
    )


def test_rbo_a_is_expected_tie_breaking_variant():
    from nwps.comparators import rbo_a_extrapolated
    # With an uncertain top tie, RBO^a(X,X) need not be 1; this is expected
    # under Corsi-Urbano's a-variant semantics.
    blocks = [("A", "B"), ("C",)]
    value = rbo_a_extrapolated(blocks, blocks, phi=0.9)
    assert 0.0 < value < 1.0
