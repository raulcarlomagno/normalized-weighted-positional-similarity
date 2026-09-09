from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nwps import nwps  # noqa: E402

SEED = 20260909
N = 15
REF = tuple(range(N))


def oracle_score(pred):
    """Independent synthetic proxy: log head weights + hyperbolic displacement."""
    raw = np.array([1 / math.log2(i + 2) for i in range(N)])
    w = raw / raw.sum()
    pos = {x: j for j, x in enumerate(pred)}
    return float(sum(
        w[i] / (1 + abs(i - pos[item]))
        for i, item in enumerate(REF)
        if item in pos
    ))


def perturb(rng: random.Random):
    p = list(REF)
    # 1-4 random structural operations.
    for _ in range(rng.randint(1, 4)):
        op = rng.choice(["swap", "move", "omit"])
        if op == "swap":
            i = rng.randrange(N - 1)
            p[i], p[i + 1] = p[i + 1], p[i]
        elif op == "move":
            i, j = rng.sample(range(N), 2)
            item = p.pop(i)
            p.insert(j, item)
        else:
            i = rng.randrange(N)
            p[i] = ("x", rng.randrange(10**9), i)
    return tuple(p)


def pairwise_accuracy(y_true, y_pred, pairs):
    good = 0
    used = 0
    for a, b in pairs:
        dt = y_true[a] - y_true[b]
        dp = y_pred[a] - y_pred[b]
        if abs(dt) < 1e-12:
            continue
        good += (dt > 0) == (dp > 0)
        used += 1
    return good / used if used else float("nan")


def main():
    rng = random.Random(SEED)
    candidates = [perturb(rng) for _ in range(1200)]
    oracle = np.array([oracle_score(p) for p in candidates])
    indices = list(range(len(candidates)))
    rng.shuffle(indices)
    train = indices[:720]
    dev = indices[720:960]
    test = indices[960:]

    grid = np.geomspace(0.5, 12.0, 80)
    dev_scores = []
    all_by_h = {}
    for h in grid:
        vals = np.array([nwps(REF, p, half_life=float(h)).score for p in candidates], dtype=float)
        all_by_h[float(h)] = vals
        corr = spearmanr(oracle[dev], vals[dev]).statistic
        dev_scores.append(float(corr))
    best_idx = int(np.nanargmax(dev_scores))
    best_h = float(grid[best_idx])
    pred = all_by_h[best_h]

    pair_rng = random.Random(SEED + 1)
    test_pairs = [tuple(pair_rng.sample(test, 2)) for _ in range(3000)]
    result = {
        "status": "synthetic calibration pipeline demonstration; not external validation",
        "seed": SEED,
        "n_candidates": len(candidates),
        "split_sizes": {"train": len(train), "dev": len(dev), "test": len(test)},
        "calibration_objective": "maximize Spearman correlation with an independent synthetic fidelity oracle on dev",
        "selected_half_life": best_h,
        "dev_spearman": float(spearmanr(oracle[dev], pred[dev]).statistic),
        "test_spearman": float(spearmanr(oracle[test], pred[test]).statistic),
        "test_pairwise_accuracy": float(pairwise_accuracy(oracle, pred, test_pairs)),
        "oracle": "logarithmic reference weights with hyperbolic positional credit; distinct from NWPS",
    }
    path = ROOT / "results" / "calibration_demo.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # Save the calibration curve.
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(8, 4.8))
    ax = fig.add_subplot(111)
    ax.plot(grid, dev_scores)
    ax.axvline(best_h, linestyle="--", label=f"selected h={best_h:.3f}")
    ax.set_xscale("log")
    ax.set_xlabel("Rank half-life h")
    ax.set_ylabel("Dev Spearman vs synthetic oracle")
    ax.set_title("Calibration pipeline demonstration")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "images" / "calibration_dev_curve.png", dpi=180)
    plt.close(fig)
    print(path)


if __name__ == "__main__":
    main()
