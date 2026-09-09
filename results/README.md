# Experimental Results

All results in this directory are **synthetic or controlled** unless explicitly stated otherwise. They are included to verify behavior, exercise calibration and meta-evaluation pipelines, and compare response functions. They are **not external empirical validation**.

## Files

- `controlled_benchmark.csv` — scenario-level scores for NWPS and comparators.
- `controlled_meta_evaluation.csv` — Spearman correlation with an independent synthetic fidelity oracle.
- `controlled_benchmark_summary.json` — metadata for the controlled benchmark.
- `tie_benchmark.csv` — tie-aware NWPS vs Corsi–Urbano RBO^a on small controlled cases.
- `calibration_demo.json` — development-set half-life calibration and held-out synthetic evaluation.
- `synthetic_system_means.csv` — mean scores for six synthetic systems over 800 synthetic queries.
- `synthetic_stability.csv` — system-ordering stability under query subsampling.
- `synthetic_power.csv` — empirical paired-test rejection-rate proxy under repeated subsampling.
- `synthetic_stability_power_summary.json` — generation and test metadata.

## Controlled benchmark caution

The synthetic oracle deliberately uses a different form from NWPS: logarithmic reference weights and hyperbolic positional credit. It is a pipeline stress test, not human ground truth. The benchmark is intentionally non-promotional: several comparators equal or exceed NWPS on some synthetic summaries.

## External validation

The repository includes `data/human_judgment_template.jsonl` and `data/ANNOTATION_GUIDE.md` to collect blinded external judgments. Those label fields are empty. No human results are claimed until real annotations are collected and frozen.
