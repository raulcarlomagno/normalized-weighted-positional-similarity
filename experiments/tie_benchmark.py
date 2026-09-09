from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nwps import nwps_tied  # noqa: E402
from nwps.comparators import rbo_a_extrapolated  # noqa: E402

H = 3.0
PHI = 2 ** (-1 / H)

CASES = {
    "same_reference_tie": (
        [("A",), ("B", "C"), ("D",)],
        [("A",), ("B", "C"), ("D",)],
    ),
    "reference_tie_resolved_BC": (
        [("A",), ("B", "C"), ("D",)],
        [("A",), ("B",), ("C",), ("D",)],
    ),
    "reference_tie_resolved_CB": (
        [("A",), ("B", "C"), ("D",)],
        [("A",), ("C",), ("B",), ("D",)],
    ),
    "prediction_top_tie_against_strict": (
        [("A",), ("B",), ("C",), ("D",)],
        [("A", "B"), ("C",), ("D",)],
    ),
    "misplaced_reference_tie": (
        [("A",), ("B", "C"), ("D",)],
        [("B", "C"), ("A",), ("D",)],
    ),
}


def main():
    rows = []
    for name, (ref, pred) in CASES.items():
        nw = nwps_tied(ref, pred, half_life=H)
        rows.append({
            "case": name,
            "NWPS_tied": nw.score,
            "RBO_a": rbo_a_extrapolated(ref, pred, phi=PHI),
            "note": "RBO^a treats ties as uncertainty; NWPS reference ties encode indifference.",
        })
    path = ROOT / "results" / "tie_benchmark.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(path)


if __name__ == "__main__":
    main()
