# NWPS — Normalized Weighted Positional Similarity

**Research Release v0.1.0**

NWPS is a directional metric for **fidelity to a privileged reference ranking**.
It is designed for cases where the evaluator cares about:

- specific reference-item identities;
- stronger importance for the reference head;
- positional displacement;
- omission of important reference items;
- declared ties;
- incomplete observation of the produced ranking.

The full mathematical specification is in [`nwps_report.md`](nwps_report.md).
A structured prior-art review is in [`docs/prior_art_review.md`](docs/prior_art_review.md).

## Core definition

Let `h > 0` be the **rank half-life** and define

\[
\rho=2^{-1/h}.
\]

For reference depth \(k\), normalized reference weights are

\[
w_i=
\frac{(1-\rho)\rho^{i-1}}{1-\rho^k}.
\]

For a retrieved reference item at reference rank \(i\) and predicted rank \(j\),

\[
q_i=\rho^{|i-j|}.
\]

A confirmed missing reference item receives

\[
q_i=0.
\]

Then

\[
\boxed{
NWPS(R,P;h)=\sum_{i=1}^{k}w_iq_i
}
\]

with

\[
0\le NWPS\le1.
\]

- `1` — exact reference fidelity.
- `0` — confirmed absence of all evaluated reference mass.

## Diagnostic decomposition

Define weighted reference coverage

\[
C=\sum_{i:r_i\in P}w_i
\]

and conditional positional fidelity

\[
F=
\frac{\sum_{i:r_i\in P}w_iq_i}{C}
\]

when \(C>0\), with \(F=0\) when \(C=0\).

Then

\[
\boxed{NWPS=C\,F}
\]

and

\[
1-NWPS=(1-C)+C(1-F).
\]

That factorization is the main diagnostic interpretation of NWPS:

- `1 - C` measures **weighted omission loss**;
- `C(1 - F)` measures **positional loss among retained reference mass**.

## Why a rank half-life?

The half-life has an operational meaning:

> a displacement of `h` rank positions retains half of positional credit.

It also controls the geometric decay of reference importance. Base NWPS deliberately
uses a **single persistence scale** for both effects:

\[
\frac{w_{i+1}}{w_i}
=
\frac{q(d+1)}{q(d)}
=
\rho.
\]

This coupling is a modeling assumption and should be calibrated or sensitivity-tested.

### Semantic calibration

If a task says that displacement \(d\) should retain fraction \(r\), then

\[
\boxed{
h=-\frac{d\ln2}{\ln r}.}
\]

```python
from nwps import half_life_from_retention

h = half_life_from_retention(
    displacement=2,
    retained_credit=0.80,
)
# approximately 6.21
```

## Stable result API

All evaluators return the same `NWPSResult` type.

```python
from nwps import nwps

result = nwps(
    reference=list("ABCDE"),
    predicted=list("ACBED"),
    half_life=3,
)

print(result.score)
print(result.weighted_coverage_observed)
print(result.conditional_positional_fidelity_observed)
```

For complete observations, `lower_bound == upper_bound` and `result.score` is a
float. For right-censored observations, `result.score is None` and the result
contains a fidelity interval.

## Right censoring

NWPS distinguishes:

- **confirmed omission** — item is known not to be returned;
- **right censoring** — only a prefix of the produced ranking is observable.

```python
result = nwps(
    reference=list("ABCDE"),
    predicted=list("AB"),
    half_life=3,
    prediction_complete=False,
)

print(result.lower_bound, result.upper_bound)
print(result.upper_bound_method)
# itemwise-relaxation
```

The default censoring bound is the dependency-free **itemwise relaxation**.
For strict rankings a tighter joint-assignment bound is available explicitly:

```python
nwps(
    reference,
    observed_prefix,
    half_life=3,
    prediction_complete=False,
    censoring_upper="tight",
)
```

The tight option assigns unseen reference items to distinct future ranks and
requires NumPy/SciPy (`pip install nwps[tight]`).

## Tie-aware API

Reference ties mean **indifference** among the positions in the block.
Prediction ties mean **uncertainty** over the resolved rank.

```python
from nwps import nwps_tied

reference = [
    ("A",),
    ("B", "C"),
    ("D",),
]

predicted = [
    ("A",),
    ("C",),
    ("B",),
    ("D",),
]

result = nwps_tied(
    reference,
    predicted,
    half_life=3,
)

assert result.score == 1.0
```

The tie block `{B, C}` carries the reference mass of its occupied positions,
shared equally between its items. A prediction tie receives expected positional
credit over its possible ranks.

## Chance calibration

Raw NWPS is a direct fidelity score, not a chance-corrected statistic.
For a declared null expectation \(B\), the optional reporting transform is

\[
\boxed{
NWPS_{skill}=\frac{NWPS-B}{1-B}.
}
\]

```python
from nwps import uniform_permutation_baseline, nwps_skill

b = uniform_permutation_baseline(k=13, half_life=3)
skill = nwps_skill(score=0.75, null_expectation=b)
```

Properties:

- perfect fidelity maps to `1`;
- the null expectation maps to `0`;
- below-null scores are negative;
- the minimum is `-B / (1 - B)`, not necessarily `-1`.

For multiple queries with different structures, calibrate the null per query or
state the aggregation rule explicitly.

## Intended use cases

NWPS is intended for **reference-fidelity diagnosis**, including:

- reranker regression testing;
- teacher–student ranking distillation;
- canonical expert rankings;
- retrieval-drift monitoring;
- curated RAG retrieval suites;
- ranking stability analysis against a trusted baseline.

It is not intended as a universal replacement for NDCG, Recall@K, MRR, RBO,
RBA, WS, RDQ, Spearman, Kendall, or generalized ranking distances.

## Closest comparators

The release explicitly treats the following as mandatory prior art / baselines:

- **WS** — asymmetric top-weighted reference similarity;
- **RDQ** — ordered-reference retrieval/ranking evaluation with deviation penalties;
- **RBA** — top-weighted ranking-to-ranking alignment;
- **Compatibility/CMP** — preference/weak-order evaluation by maximum similarity;
- **generalized/weighted Footrule**;
- **RBO** and **tie-aware RBO**;
- **Canberra** ranked-list distance;
- **weighted Kendall**;
- **tau_AP**.

See [`docs/prior_art_review.md`](docs/prior_art_review.md) for the novelty boundary.

## Controlled benchmark

Run:

```bash
PYTHONPATH=src python experiments/controlled_benchmark.py
```

The benchmark contains 40 controlled perturbations and an **independent synthetic
fidelity oracle** using logarithmic head weights and hyperbolic positional credit.
It is not human ground truth.

Spearman correlation with that synthetic oracle:

| Metric | Correlation |
|---|---:|
| Canberra distance (sign reversed) | 0.994 |
| NWPS | 0.985 |
| Reference-weighted Footrule similarity | 0.982 |
| RBO | 0.978 |
| Weighted Kendall | 0.977 |
| RDQ M2, alpha=1 | 0.972 |
| WS | 0.955 |
| tau_AP | 0.936 |
| RBA upper | 0.930 |
| RDQ M2, alpha=4 | 0.890 |
| NDCG with synthetic linear grades | 0.845 |

The result is intentionally non-promotional: NWPS does not dominate every
comparator in this synthetic test.

Full outputs are in [`results/`](results/README.md).

## Tie comparison

The controlled tie benchmark includes Corsi–Urbano `RBO^a`.
For a reference tie `{B,C}`, NWPS assigns full fidelity to either strict ordering
`B,C` or `C,B` because the tie encodes **reference indifference**. `RBO^a`
interprets ties as rank uncertainty and therefore has different self-similarity
semantics. The difference is documented rather than hidden.

## Half-life calibration demo

`experiments/calibration_demo.py` demonstrates development-set calibration and
held-out evaluation using a synthetic oracle that is structurally different from
NWPS.

Current deterministic run:

- selected `h`: **3.0561**;
- dev Spearman: **0.8752**;
- held-out test Spearman: **0.8766**;
- held-out pairwise accuracy: **0.8605**.

These values verify the calibration pipeline only. They are **not external validation**.

## System-ranking stability and power demo

`experiments/stability_power_demo.py` generates 800 synthetic queries and six
systems with different regression profiles.

At 100 sampled queries, mean Kendall agreement with each metric's full-query
system ordering is:

| Metric | Mean tau |
|---|---:|
| RBA | 0.962 |
| RDQ | 0.961 |
| NDCG | 0.952 |
| RBO | 0.938 |
| NWPS | 0.937 |

Mean pairwise rejection rate at 100 queries in the synthetic paired-test power
proxy is:

| Metric | Mean rejection rate |
|---|---:|
| RDQ | 0.904 |
| NWPS | 0.897 |
| RBO | 0.852 |
| NDCG | 0.796 |
| RBA | 0.791 |

Again, the purpose is reproducible meta-evaluation machinery, not a claim of
superiority.

## Human/expert judgment set

The repository contains:

- [`data/human_judgment_template.jsonl`](data/human_judgment_template.jsonl) — 200 generated pairwise ranking cases;
- [`data/ANNOTATION_GUIDE.md`](data/ANNOTATION_GUIDE.md) — blinded annotation instructions.

The preference and severity fields are deliberately empty. No synthetic labels
are presented as human judgments.

## Tests

```bash
PYTHONPATH=src pytest
```

The release includes:

- exact identity/disjointness checks;
- numerical-extreme half-life tests;
- exhaustive permutation checks through `n=7` for random-baseline equality;
- exhaustive small censoring-bound verification;
- tie invariance checks;
- comparator anchor tests;
- 2,000 deterministic randomized strict-ranking property sweeps;
- 300 randomized tie-block invariance sweeps.

Current result:

```text
35 passed
```

## Reproduce all generated results

```bash
make test
make figures
make experiments
```

or:

```bash
make all
```

## Repository layout

```text
.
├── README.md
├── nwps_report.md
├── pyproject.toml
├── CITATION.cff
├── LICENSE
├── Makefile
├── docs/
│   └── prior_art_review.md
├── src/nwps/
│   ├── __init__.py
│   ├── calibration.py
│   ├── comparators.py
│   ├── core.py
│   ├── ties.py
│   ├── types.py
│   └── py.typed
├── tests/
├── experiments/
├── data/
├── results/
└── images/
```

## License

NWPS is licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE).

SPDX identifier: `Apache-2.0`.

## Research status

The mathematical definition, reference implementation, tests, controlled
benchmarks, calibration pipeline, tie handling, censoring bounds, and structured
prior-art review are included in this release.

What is **not** claimed:

- external human validation;
- superiority over RDQ, RBA, WS, RBO, or weighted distance families;
- universal optimality of the half-life;
- mathematical metric axioms such as symmetry or triangle inequality;
- proof that no mathematically equivalent formulation exists anywhere in the literature.

Those boundaries are deliberate.
