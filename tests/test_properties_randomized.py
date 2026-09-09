"""Deterministic randomized property sweeps.

These tests provide property-based coverage without depending on a third-party
property-testing package. The seed is fixed so failures are reproducible.
"""

import random

from nwps import nwps, nwps_tied


def test_randomized_strict_properties():
    rng = random.Random(20260909)
    for _ in range(2_000):
        n = rng.randint(1, 30)
        ref = list(range(n))
        pred = ref[:]
        rng.shuffle(pred)
        # Randomly replace some items with distractors.
        for i in range(n):
            if rng.random() < 0.15:
                pred[i] = ("x", _, i)
        # Keep unique items after replacement.
        assert len(set(pred)) == len(pred)
        h = 10 ** rng.uniform(-1.0, 1.5)
        res = nwps(ref, pred, half_life=h)
        assert res.score is not None
        assert -1e-12 <= res.score <= 1 + 1e-12
        assert 0 <= res.weighted_coverage_observed <= 1 + 1e-12
        assert 0 <= res.conditional_positional_fidelity_observed <= 1 + 1e-12
        assert abs(res.score - res.weighted_coverage_observed * res.conditional_positional_fidelity_observed) < 1e-10


def test_randomized_tie_invariance_inside_reference_blocks():
    rng = random.Random(17)
    for _ in range(300):
        # Three blocks with random sizes, unique integer IDs.
        sizes = [rng.randint(1, 4) for _ in range(3)]
        items = iter(range(sum(sizes)))
        ref = [tuple(next(items) for _ in range(s)) for s in sizes]
        p1 = []
        p2 = []
        for block in ref:
            a = list(block)
            b = list(block)
            rng.shuffle(a)
            rng.shuffle(b)
            p1.extend((x,) for x in a)
            p2.extend((x,) for x in b)
        s1 = nwps_tied(ref, p1, half_life=2.5).score
        s2 = nwps_tied(ref, p2, half_life=2.5).score
        assert s1 is not None and s2 is not None
        assert abs(s1 - 1.0) < 1e-12
        assert abs(s2 - 1.0) < 1e-12
