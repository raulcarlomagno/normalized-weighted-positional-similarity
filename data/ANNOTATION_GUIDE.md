# Reference-Fidelity Judgment Protocol

This file defines the annotation protocol for `human_judgment_template.jsonl`.
The template contains **no synthetic preference labels**: `preferred`, severity,
confidence, and assessor fields are intentionally empty so that external
validation cannot be confused with generated ground truth.

## Task

For each record, inspect the reference ranking and candidates A and B. Answer:

> Which candidate ranking better preserves the reference ranking?

Use `preferred = "A"`, `"B"`, or `"TIE"`.

The judgment should reflect **reference fidelity**, not generic retrieval utility.
Consider both:

1. whether high-priority reference items remain present; and
2. how far present reference items move from their intended positions.

If the reference explicitly includes a tie block in a future tie-aware dataset,
permutations inside that tie should be treated as equivalent.

## Additional fields

- `confidence_1_to_5`: confidence in the pairwise preference.
- `severity_a_1_to_5`: severity of A's deviation from the reference.
- `severity_b_1_to_5`: severity of B's deviation from the reference.
- `assessor_id`: anonymized assessor identifier.
- `notes`: optional rationale.

## Blinding recommendation

Do not show assessors NWPS or comparator scores during annotation. Metric values
should be computed only after judgments are frozen.

## Data split recommendation

Assign judgments by reference/query to disjoint development and test partitions.
Calibrate the half-life only on development data. Freeze it before computing
held-out test results.
