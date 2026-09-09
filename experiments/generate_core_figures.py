from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nwps import (  # noqa: E402
    half_life_from_retention,
    nwps,
    nwps_skill,
    nwps_tied,
    positional_credit,
    reference_weights,
    uniform_permutation_baseline,
)

IMG = ROOT / "images"
IMG.mkdir(exist_ok=True)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(IMG / name, dpi=180)
    plt.close(fig)


def main():
    # Reference mass profiles.
    k = 20
    fig = plt.figure(figsize=(8, 4.8)); ax = fig.add_subplot(111)
    for h in [1.0, 3.0, 5.0, 10.0]:
        ax.plot(np.arange(1, k + 1), reference_weights(k, h), marker="o", label=f"h={h:g}")
    ax.set_xlabel("Reference rank"); ax.set_ylabel("Normalized reference mass")
    ax.set_title("NWPS reference-mass profiles"); ax.legend()
    save(fig, "reference_mass_profiles.png")

    # Positional credit.
    d = np.arange(0, 21)
    fig = plt.figure(figsize=(8, 4.8)); ax = fig.add_subplot(111)
    for h in [1.0, 3.0, 5.0, 10.0]:
        ax.plot(d, [positional_credit(int(x), h) for x in d], marker="o", label=f"h={h:g}")
    ax.set_xlabel("Absolute displacement"); ax.set_ylabel("Positional credit")
    ax.set_ylim(-0.03, 1.03); ax.set_title("NWPS positional credit"); ax.legend()
    save(fig, "positional_credit_profiles.png")

    # Decomposition.
    ref = list("ABCDEFGHIJKLM"); h = 3.0
    cases = {
        "Perfect": ref,
        "Reverse": ref[::-1],
        "Top omission": ["X", *ref[1:]],
        "Tail omission": [*ref[:-1], "X"],
        "Interleaved": list("AMBLCKDJEIFHG"),
    }
    labels, scores, cov, fidel = [], [], [], []
    for name, pred in cases.items():
        r = nwps(ref, pred, half_life=h)
        labels.append(name); scores.append(r.score); cov.append(r.weighted_coverage_observed); fidel.append(r.conditional_positional_fidelity_observed)
    x = np.arange(len(labels)); width = 0.25
    fig = plt.figure(figsize=(9, 5)); ax = fig.add_subplot(111)
    ax.bar(x - width, scores, width, label="NWPS")
    ax.bar(x, cov, width, label="Weighted coverage")
    ax.bar(x + width, fidel, width, label="Conditional positional fidelity")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylim(-0.03, 1.03); ax.set_title("NWPS diagnostic decomposition (h=3)"); ax.legend()
    save(fig, "coverage_position_decomposition_h3.png")

    # Tie behavior.
    tie_cases = {
        "Reference tie\nresolved BC": ([("A",), ("B", "C"), ("D",)], [("A",), ("B",), ("C",), ("D",)]),
        "Reference tie\nresolved CB": ([("A",), ("B", "C"), ("D",)], [("A",), ("C",), ("B",), ("D",)]),
        "Prediction top tie\nstrict reference": ([("A",), ("B",), ("C",), ("D",)], [("A", "B"), ("C",), ("D",)]),
        "Misplaced\nreference tie": ([("A",), ("B", "C"), ("D",)], [("B", "C"), ("A",), ("D",)]),
    }
    vals = [nwps_tied(r, p, half_life=h).score for r, p in tie_cases.values()]
    fig = plt.figure(figsize=(8, 4.8)); ax = fig.add_subplot(111)
    ax.bar(list(tie_cases), vals); ax.set_ylim(0, 1.05); ax.set_ylabel("NWPS")
    ax.set_title("Tie-aware NWPS behavior (h=3)")
    save(fig, "tie_aware_behavior_h3.png")

    # Censor bounds: strict rank-1 unseen after m.
    ref = list(range(13)); lower, upper_tight, upper_item = [], [], []
    ms = list(range(1, 13))
    for m in ms:
        obs = list(range(1, m + 1))  # rank-1 item 0 unseen, observed other items
        t = nwps(ref, obs, half_life=h, prediction_complete=False, censoring_upper="tight")
        i = nwps(ref, obs, half_life=h, prediction_complete=False, censoring_upper="itemwise")
        lower.append(t.lower_bound); upper_tight.append(t.upper_bound); upper_item.append(i.upper_bound)
    fig = plt.figure(figsize=(8, 4.8)); ax = fig.add_subplot(111)
    ax.plot(ms, lower, marker="o", label="Lower bound")
    ax.plot(ms, upper_tight, marker="o", label="Joint-assignment upper")
    ax.plot(ms, upper_item, linestyle="--", label="Itemwise relaxation upper")
    ax.set_xlabel("Observed prediction depth m"); ax.set_ylabel("NWPS bound")
    ax.set_ylim(-0.03, 1.03); ax.set_title("Censoring bounds contract with observation depth"); ax.legend()
    save(fig, "censoring_bound_rank1_h3.png")

    # Half-life semantic calibration.
    disps = np.arange(1, 11)
    fig = plt.figure(figsize=(8, 4.8)); ax = fig.add_subplot(111)
    for retention in [0.9, 0.8, 0.7, 0.5]:
        hs = [half_life_from_retention(float(d), retention) for d in disps]
        ax.plot(disps, hs, marker="o", label=f"retained={retention:.1f}")
    ax.set_xlabel("Declared displacement"); ax.set_ylabel("Equivalent half-life h")
    ax.set_title("Semantic half-life calibration"); ax.legend()
    save(fig, "half_life_semantic_calibration.png")

    # Half-life sensitivity.
    ref = list("ABCDEFGHIJKLM")
    preds = {
        "Reverse": ref[::-1],
        "Top-2 swap": [ref[1], ref[0], *ref[2:]],
        "Top omission": ["X", *ref[1:]],
        "Interleaved": list("AMBLCKDJEIFHG"),
    }
    hs = np.linspace(0.75, 10, 80)
    fig = plt.figure(figsize=(8, 4.8)); ax = fig.add_subplot(111)
    for name, pred in preds.items():
        ax.plot(hs, [nwps(ref, pred, half_life=float(x)).score for x in hs], label=name)
    ax.set_xlabel("Rank half-life h"); ax.set_ylabel("NWPS"); ax.set_ylim(-0.03, 1.03)
    ax.set_title("NWPS half-life sensitivity"); ax.legend()
    save(fig, "half_life_sensitivity.png")

    # Raw vs skill.
    b = uniform_permutation_baseline(len(ref), h)
    names = list(cases); raw = [nwps(ref, cases[n], half_life=h).score for n in names]
    skill = [nwps_skill(s, b) for s in raw]
    x = np.arange(len(names)); width = 0.38
    fig = plt.figure(figsize=(9, 5)); ax = fig.add_subplot(111)
    ax.bar(x - width / 2, raw, width, label="Raw NWPS")
    ax.bar(x + width / 2, skill, width, label="NWPS Skill")
    ax.axhline(0, linestyle="--"); ax.set_xticks(x); ax.set_xticklabels(names, rotation=25, ha="right")
    ax.set_title("Raw fidelity and chance-adjusted reporting (h=3)"); ax.legend()
    save(fig, "raw_vs_chance_adjusted_h3.png")

    # Calibration baselines over k.
    ks = np.arange(2, 101); reverse, random_b, omit_top = [], [], []
    for kk in ks:
        rr = list(range(int(kk)))
        reverse.append(nwps(rr, rr[::-1], half_life=h).score)
        random_b.append(uniform_permutation_baseline(int(kk), h))
        omit_top.append(nwps(rr, [("x", kk), *rr[1:]], half_life=h).score)
    fig = plt.figure(figsize=(8, 4.8)); ax = fig.add_subplot(111)
    ax.plot(ks, np.ones_like(ks), label="Perfect")
    ax.plot(ks, random_b, label="Expected random permutation")
    ax.plot(ks, reverse, label="Reverse")
    ax.plot(ks, omit_top, label="Only rank-1 omitted")
    ax.plot(ks, np.zeros_like(ks), label="Confirmed disjoint")
    ax.set_xlabel("Reference depth k"); ax.set_ylabel("NWPS"); ax.set_ylim(-0.03, 1.03)
    ax.set_title("NWPS calibration baselines (h=3)"); ax.legend()
    save(fig, "calibration_baselines_h3.png")

    print(f"Generated core figures in {IMG}")


if __name__ == "__main__":
    main()
