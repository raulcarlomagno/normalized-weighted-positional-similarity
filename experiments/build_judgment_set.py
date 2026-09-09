from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20260909


def perturb(reference, rng):
    p = list(reference)
    ops = []
    for _ in range(rng.randint(1, 3)):
        op = rng.choice(["adjacent_swap", "move", "omit", "block_rotate"])
        if op == "adjacent_swap":
            i = rng.randrange(len(p) - 1)
            p[i], p[i + 1] = p[i + 1], p[i]
            ops.append({"type": op, "rank": i + 1})
        elif op == "move":
            i, j = rng.sample(range(len(p)), 2)
            item = p.pop(i)
            p.insert(j, item)
            ops.append({"type": op, "from": i + 1, "to": j + 1})
        elif op == "omit":
            i = rng.randrange(len(p))
            old = p[i]
            p[i] = f"D{rng.randrange(10**9)}"
            ops.append({"type": op, "rank": i + 1, "item": old})
        else:
            start = rng.randrange(0, len(p) - 2)
            width = rng.randint(2, min(5, len(p) - start))
            block = p[start:start + width]
            p[start:start + width] = block[1:] + block[:1]
            ops.append({"type": op, "start": start + 1, "width": width})
    return p, ops


def main():
    rng = random.Random(SEED)
    records = []
    for idx in range(200):
        reference = [f"Q{idx:03d}_R{i+1}" for i in range(12)]
        a, ops_a = perturb(reference, rng)
        b, ops_b = perturb(reference, rng)
        records.append({
            "judgment_id": f"J{idx+1:04d}",
            "reference": reference,
            "candidate_a": a,
            "candidate_b": b,
            "generation_metadata": {"candidate_a": ops_a, "candidate_b": ops_b},
            "question": "Which candidate ranking better preserves the reference ranking?",
            "preferred": None,
            "confidence_1_to_5": None,
            "severity_a_1_to_5": None,
            "severity_b_1_to_5": None,
            "assessor_id": None,
            "notes": None,
        })

    out = ROOT / "data" / "human_judgment_template.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(out)


if __name__ == "__main__":
    main()
