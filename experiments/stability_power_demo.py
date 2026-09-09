from __future__ import annotations

import csv
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau, ttest_rel
from sklearn.metrics import ndcg_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nwps import nwps  # noqa: E402
from nwps.comparators import (  # noqa: E402
    rba_upper,
    rbo_extrapolated,
    rdq_m2,
    rdq_vertical_weights,
)

SEED = 20260909
H = 3.0
PHI = 2 ** (-1 / H)
K = 15
N_QUERIES = 800

SYSTEMS = {
    "S0_near_exact": dict(swap=0.04, move=0.02, omit=0.01),
    "S1_mild": dict(swap=0.08, move=0.04, omit=0.02),
    "S2_moderate": dict(swap=0.15, move=0.08, omit=0.04),
    "S3_order_drift": dict(swap=0.25, move=0.16, omit=0.02),
    "S4_coverage_drift": dict(swap=0.08, move=0.04, omit=0.12),
    "S5_severe": dict(swap=0.30, move=0.22, omit=0.15),
}


def apply_system(ref, profile, rng):
    p = list(ref)
    # independent opportunities make per-query severity variable
    for i in range(K - 1):
        if rng.random() < profile["swap"] / 3:
            p[i], p[i + 1] = p[i + 1], p[i]
    if rng.random() < profile["move"] * 2:
        i = rng.randrange(K)
        j = rng.randrange(K)
        item = p.pop(i)
        p.insert(j, item)
    for i in range(K):
        if rng.random() < profile["omit"]:
            p[i] = ("D", rng.randrange(10**12), i)
    return p


def ndcg_linear(ref, pred):
    rel = {item: K - i for i, item in enumerate(ref)}
    universe = list(ref) + [x for x in pred if x not in rel]
    pos = {x: i for i, x in enumerate(pred)}
    y_true = np.array([[float(rel.get(x, 0)) for x in universe]])
    y_score = np.array([[float(len(pred) - pos[x]) if x in pos else -1.0 for x in universe]])
    return float(ndcg_score(y_true, y_score, k=K))


def system_order(means):
    return sorted(means, key=means.get, reverse=True)


def tau_between_orders(a, b):
    pa = {s: i for i, s in enumerate(a)}
    pb = {s: i for i, s in enumerate(b)}
    x = [pa[s] for s in SYSTEMS]
    y = [pb[s] for s in SYSTEMS]
    return float(kendalltau(x, y).statistic)


def main():
    rng = random.Random(SEED)
    metrics = ["NWPS", "RDQ", "RBO", "RBA", "NDCG"]
    values = {metric: {s: [] for s in SYSTEMS} for metric in metrics}

    for q in range(N_QUERIES):
        ref = [(q, i) for i in range(K)]
        for system, profile in SYSTEMS.items():
            pred = apply_system(ref, profile, rng)
            values["NWPS"][system].append(nwps(ref, pred, half_life=H).score)
            values["RDQ"][system].append(rdq_m2(ref, pred, alpha=1.0, lam=0.2, k=K, output_weights=rdq_vertical_weights(K)))
            values["RBO"][system].append(rbo_extrapolated(ref, pred, phi=PHI))
            values["RBA"][system].append(rba_upper(ref, pred, phi=PHI))
            values["NDCG"][system].append(ndcg_linear(ref, pred))

    rows = []
    full_orders = {}
    for metric in metrics:
        means = {s: float(np.mean(values[metric][s])) for s in SYSTEMS}
        full_orders[metric] = system_order(means)
        for s in SYSTEMS:
            rows.append({"metric": metric, "system": s, "mean": means[s], "rank": full_orders[metric].index(s) + 1})

    out_means = ROOT / "results" / "synthetic_system_means.csv"
    with out_means.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    np_rng = np.random.default_rng(SEED)
    stability = []
    for metric in metrics:
        full = full_orders[metric]
        for n in [25, 50, 100, 200, 400]:
            taus = []
            for _ in range(250):
                idx = np_rng.choice(N_QUERIES, size=n, replace=False)
                means = {s: float(np.mean(np.asarray(values[metric][s])[idx])) for s in SYSTEMS}
                taus.append(tau_between_orders(system_order(means), full))
            stability.append({
                "metric": metric,
                "n_queries": n,
                "mean_kendall_tau_vs_full": float(np.mean(taus)),
                "p10": float(np.quantile(taus, 0.10)),
                "p90": float(np.quantile(taus, 0.90)),
            })

    out_stab = ROOT / "results" / "synthetic_stability.csv"
    with out_stab.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(stability[0]))
        w.writeheader(); w.writerows(stability)

    # Empirical rejection-rate power proxy under paired t-tests on repeated
    # query subsamples. This is synthetic meta-evaluation, not a substitute for
    # real test-collection power analysis.
    power = []
    systems = list(SYSTEMS)
    for metric in metrics:
        for n in [50, 100, 200]:
            rejects = []
            for a_i in range(len(systems)):
                for b_i in range(a_i + 1, len(systems)):
                    a, b = systems[a_i], systems[b_i]
                    hit = 0
                    for _ in range(120):
                        idx = np_rng.choice(N_QUERIES, size=n, replace=False)
                        va = np.asarray(values[metric][a])[idx]
                        vb = np.asarray(values[metric][b])[idx]
                        p = ttest_rel(va, vb).pvalue
                        hit += bool(p < 0.05)
                    rejects.append(hit / 120)
            power.append({
                "metric": metric,
                "n_queries": n,
                "median_pairwise_rejection_rate": float(np.median(rejects)),
                "mean_pairwise_rejection_rate": float(np.mean(rejects)),
            })

    out_power = ROOT / "results" / "synthetic_power.csv"
    with out_power.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(power[0]))
        w.writeheader(); w.writerows(power)

    summary = {
        "status": "synthetic system-ranking stability and power demonstration; not external validation",
        "seed": SEED,
        "n_queries": N_QUERIES,
        "systems": SYSTEMS,
        "full_system_orders": full_orders,
        "power_test": "paired t-test rejection rate at alpha=0.05 over repeated subsamples",
    }
    (ROOT / "results" / "synthetic_stability_power_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(8.5, 5.2))
    ax = fig.add_subplot(111)
    for metric in metrics:
        pts = [x for x in stability if x["metric"] == metric]
        ax.plot([x["n_queries"] for x in pts], [x["mean_kendall_tau_vs_full"] for x in pts], marker="o", label=metric)
    ax.set_xlabel("Number of sampled queries")
    ax.set_ylabel("Mean Kendall tau vs full-query system ordering")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("Synthetic system-ranking stability")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "images" / "synthetic_system_stability.png", dpi=180)
    plt.close(fig)

    print(out_means)
    print(out_stab)
    print(out_power)


if __name__ == "__main__":
    main()
