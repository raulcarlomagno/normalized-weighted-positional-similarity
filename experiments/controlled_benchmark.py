from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import ndcg_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nwps import nwps, reference_weights  # noqa: E402
from nwps.comparators import (  # noqa: E402
    canberra_distance,
    rba_upper,
    rbo_extrapolated,
    rdq_m2,
    rdq_vertical_weights,
    reference_weighted_footrule_similarity,
    tau_ap,
    weighted_kendall,
    ws_similarity,
)

H = 3.0
RHO = 2 ** (-1 / H)
REF = list("ABCDEFGHIJKLM")
N = len(REF)


def independent_oracle(reference, predicted):
    """Synthetic reference-fidelity oracle used only for controlled meta-evaluation.

    It intentionally differs from NWPS: logarithmic head weights and a
    hyperbolic positional kernel 1/(1+d). It is *not* human ground truth.
    """
    raw_w = np.array([1.0 / math.log2(i + 2) for i in range(len(reference))])
    w = raw_w / raw_w.sum()
    pos = {x: j for j, x in enumerate(predicted)}
    return float(sum(
        w[i] * (1.0 / (1.0 + abs(i - pos[item])))
        for i, item in enumerate(reference)
        if item in pos
    ))


def ndcg_linear(reference, predicted):
    relevance = {item: len(reference) - i for i, item in enumerate(reference)}
    universe = list(reference) + [x for x in predicted if x not in reference]
    pos = {x: i for i, x in enumerate(predicted)}
    y_true = np.array([[float(relevance.get(x, 0.0)) for x in universe]])
    y_score = np.array([[float(len(predicted) - pos[x]) if x in pos else -1.0 for x in universe]])
    return float(ndcg_score(y_true, y_score, k=len(reference)))


def make_scenarios():
    r = REF
    out = {"perfect": r.copy(), "reverse": r[::-1]}
    # Adjacent swaps across depth.
    for i in range(N - 1):
        p = r.copy()
        p[i], p[i + 1] = p[i + 1], p[i]
        out[f"swap_{i+1}_{i+2}"] = p
    # Move selected reference items to selected depths.
    for src, dst in [(0, 3), (0, 6), (0, 12), (1, 8), (3, 10), (10, 1)]:
        p = r.copy()
        item = p.pop(src)
        p.insert(dst, item)
        out[f"move_{src+1}_to_{dst+1}"] = p
    # Block rotations/rearrangements.
    out["interleaved"] = list("AMBLCKDJEIFHG")
    out["top5_to_bottom"] = r[5:] + r[:5]
    out["pairwise_swaps"] = [r[i + 1] if i % 2 == 0 and i + 1 < N else r[i - 1] if i % 2 else r[i] for i in range(N)]
    # Omissions with distractors.
    for i in [0, 1, 4, 8, 12]:
        p = r.copy()
        p[i] = f"X{i}"
        out[f"omit_{i+1}"] = p
    # Deterministic random permutations.
    rng = np.random.default_rng(20260909)
    for i in range(12):
        p = r.copy()
        rng.shuffle(p)
        out[f"random_{i+1:02d}"] = p
    return out


def safe(fn, *args, **kwargs):
    try:
        return float(fn(*args, **kwargs))
    except ValueError:
        return math.nan


def main():
    scenarios = make_scenarios()
    weights = reference_weights(N, H)
    rows = []
    for name, pred in scenarios.items():
        res = nwps(REF, pred, half_life=H)
        row = {
            "scenario": name,
            "oracle_synthetic": independent_oracle(REF, pred),
            "NWPS": res.score,
            "NWPS_C": res.weighted_coverage_observed,
            "NWPS_F": res.conditional_positional_fidelity_observed,
            "RDQ_M2_a1": rdq_m2(REF, pred, alpha=1.0, lam=0.2, k=N, output_weights=rdq_vertical_weights(N)),
            "RDQ_M2_a4": rdq_m2(REF, pred, alpha=4.0, lam=0.2, k=N, output_weights=rdq_vertical_weights(N)),
            "RBO": rbo_extrapolated(REF, pred, phi=RHO),
            "RBA_upper": rba_upper(REF, pred, phi=RHO),
            "NDCG_linear": ndcg_linear(REF, pred),
            "WS": safe(ws_similarity, REF, pred),
            "WeightedFootruleSim": safe(reference_weighted_footrule_similarity, REF, pred, weights),
            "WeightedKendall": safe(weighted_kendall, REF, pred),
            "tau_AP": safe(tau_ap, REF, pred),
            "CanberraDistance": safe(canberra_distance, REF, pred),
        }
        rows.append(row)

    out_csv = ROOT / "results" / "controlled_benchmark.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    oracle = np.array([r["oracle_synthetic"] for r in rows])
    metric_names = [
        "NWPS", "RDQ_M2_a1", "RDQ_M2_a4", "RBO", "RBA_upper", "NDCG_linear",
        "WS", "WeightedFootruleSim", "WeightedKendall", "tau_AP", "CanberraDistance",
    ]
    meta = []
    for metric in metric_names:
        values = np.array([r[metric] for r in rows], dtype=float)
        mask = np.isfinite(values)
        direction = -1.0 if metric == "CanberraDistance" else 1.0
        corr = spearmanr(oracle[mask], direction * values[mask]).statistic
        meta.append({
            "metric": metric,
            "n_scenarios": int(mask.sum()),
            "spearman_vs_synthetic_oracle": float(corr),
            "direction": "lower-is-better" if metric == "CanberraDistance" else "higher-is-better",
        })

    out_meta = ROOT / "results" / "controlled_meta_evaluation.csv"
    with out_meta.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(meta[0]))
        writer.writeheader()
        writer.writerows(meta)

    summary = {
        "half_life": H,
        "rbo_rba_phi": RHO,
        "n_scenarios": len(rows),
        "warning": "Synthetic controlled benchmark only; oracle is not human ground truth.",
        "top_correlations": sorted(meta, key=lambda x: x["spearman_vs_synthetic_oracle"], reverse=True),
    }
    (ROOT / "results" / "controlled_benchmark_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    # Figure of meta-correlations.
    import matplotlib.pyplot as plt
    ordered = sorted(meta, key=lambda x: x["spearman_vs_synthetic_oracle"])
    fig = plt.figure(figsize=(9, 5.8))
    ax = fig.add_subplot(111)
    ax.barh([x["metric"] for x in ordered], [x["spearman_vs_synthetic_oracle"] for x in ordered])
    ax.set_xlabel("Spearman correlation with independent synthetic fidelity oracle")
    ax.set_xlim(-1.05, 1.05)
    ax.set_title("Controlled meta-evaluation (synthetic; not external validation)")
    fig.tight_layout()
    fig.savefig(ROOT / "images" / "controlled_metric_correlations.png", dpi=180)
    plt.close(fig)

    print(out_csv)
    print(out_meta)


if __name__ == "__main__":
    main()
