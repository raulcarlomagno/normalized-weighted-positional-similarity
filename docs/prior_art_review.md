# Structured Prior-Art Review for NWPS

**Search date:** 2026-09-09  
**Scope:** ranking similarity, ranking distance, ordinal-reference evaluation, top-weighted ranking comparison, ties, partial/nonconjoint rankings, and censoring.

This review is designed to bound claims around **Normalized Weighted Positional Similarity (NWPS)**. It is a structured primary-source review, not a claim that every paper in the ranking-comparison literature has been exhausted.

## Search protocol

Primary-source and author-hosted searches were performed around combinations of:

- `reference ranking similarity`
- `ordered reference list evaluation`
- `top weighted ranking similarity`
- `weighted positional ranking distance`
- `rank deviation metric retrieval`
- `ranking compared to ranking`
- `ties rank biased overlap`
- `right censored ranking footrule`
- `preference ranking offline evaluation`
- `weighted Kendall top ranks`

Inclusion criteria:

1. the work defines or analyzes a ranking-comparison/evaluation measure;
2. at least one of reference directionality, head weighting, positional deviation, incomplete lists, ties, or ordinal preferences is central;
3. the source is a primary paper, author page, official repository, or publisher page whenever available.

## Closest prior work

| Work | Core idea | Overlap with NWPS | Main distinction from NWPS |
|---|---|---|---|
| Sałabun & Urbaniak (2020), **WS** | Asymmetric top-weighted similarity to a reference ranking | Very high: reference directionality, item displacement, head weighting | Fixed `2^-rank` weight shape; linear item-specific normalized displacement; no NWPS `C × F` decomposition or censoring interval |
| Zhou, Moschitti & Class (2026), **RDQ** | Ordered reference list, output-position weights, rank-deviation penalty, ordinal tiers | Very high: ordered reference, omissions, ties, exponential deviation in M2 | RDQ weights produced positions; NWPS anchors mass to reference positions and uses a shared half-life for reference mass and displacement |
| Moffat et al. (2024), **RBA** | Rank-biased alignment between two rankings | High: top-weighted ranking-vs-ranking comparison | Symmetric/alignment-oriented geometric combination of both ranks; NWPS is directional and reference-mass anchored |
| Clarke, Vtyurina & Smucker (2020), **Compatibility/CMP** | Maximum similarity to rankings compatible with weak preferences | High for ordinal/tied reference evaluation | Optimizes similarity over an ideal-set family; NWPS scores identity-specific displacement directly |
| Kumar & Vassilvitskii (2010), **Generalized Footrule/Kendall** | Element weights, position weights, and element distances | High at the weighted-displacement level | Metric-framework objective is more general; NWPS intentionally sacrifices symmetry/metric axioms for directional fidelity semantics |
| Webber, Moffat & Zobel (2010), **RBO** | Top-weighted prefix overlap for indefinite/nonconjoint rankings | High on top weighting and incomplete rankings | Overlap-at-depth rather than reference-item displacement |
| Corsi & Urbano (2024), **tie-aware RBO** | Principled tie semantics for RBO | High on tie treatment | Still prefix-overlap based; NWPS models acceptable reference intervals and expected item credit |
| Jurman et al. (2008/2012), **Canberra ranked-list distance** | Top-sensitive rank-relative displacement | High on top sensitivity and positional disagreement | Symmetric/rank-relative distance rather than reference-priority fidelity |
| Yilmaz, Aslam & Robertson (2008), **tau_AP** | Top-weighted directional AP-style rank correlation | Moderate/high | Pairwise concordance rather than item-specific presence × displacement |
| Vigna (2015), **weighted Kendall** | Weighted Kendall correlation with ties | Moderate/high | Pairwise correlation framework; no missingness/coverage decomposition |
| Fagin, Kumar & Sivakumar (2003), top-k list distances | Distances for top-k and nonconjoint rankings | Foundational overlap | Distance framework rather than NWPS's particular directional similarity semantics |
| Quade & Salama (2006), censored Footrule concordance | Complete/right-censored ranking concordance | Overlap on censoring | Censored correlation/distance setting rather than NWPS itemwise fidelity bounds |
| Aveni, Crippa & Principi (2024), weighted top-difference | Axiomatic top-sensitive ranking distance family | High at general top-weighted distance level | General distance/aggregation framework rather than reference-fidelity factorization |
| Juan et al. (2020), genome-similarity **Ranking Score / Ranking Accuracy** | Reference ranking with tied relation groups, distance outside admissible group borders, explicit random-ranking calibration | High on reference groups/ties, positional deviation, and chance baseline | Domain-specific group-distance construction; not head-persistent reference mass, exponential item credit, or `C × F` decomposition |

## Important conclusions

### 1. Broad novelty claims are not supportable

The following ideas are established and should **not** be claimed as individually novel:

- asymmetric comparison to a reference ranking;
- geometric/exponential head weighting;
- top-sensitive positional disagreement;
- weighted Footrule/Kendall constructions;
- incomplete/nonconjoint ranking comparison;
- tie-aware ranking similarity;
- ordinal-reference evaluation;
- rank-deviation penalties;
- censoring-aware rank comparison.

### 2. RDQ is the most important contemporary comparator

RDQ (August 2026) explicitly evaluates candidate rankings against an **Ordered Reference List** and supports tied tiers. Its M2 penalty is exponential in rank deviation and has application-specific tolerance parameters. It also includes large-scale empirical analysis on 5,000 POI queries and TREC Deep Learning data.

That makes RDQ a mandatory baseline for any publication claim around NWPS.

Primary source:  
X. Zhou, A. Moschitti, D. Class. “Rank-Deviation Quality: A Distance-Aware Metric for Multi-Answer Retrieval and Ranking Evaluation.” arXiv:2608.25318, 2026.  
https://arxiv.org/abs/2608.25318

### 3. RBA narrows the “ranking-vs-ranking” novelty space

Moffat et al. define **Rank-Biased Alignment (RBA)** as a top-weighted ranking-to-ranking measurement. The 2025 `rbstar` toolkit unifies RBA, RBO, RBR, and RBP and includes tie handling.

Primary sources:  
A. Moffat, J. Mackenzie, A. Mallia, M. Petri. “Rank-Biased Quality Measurement for Sets and Rankings.” SIGIR-AP 2024. DOI: 10.1145/3673791.3698405.  
https://jmmackenzie.io/pdf/mmmp24-sigirap.pdf

A. Moffat et al. “A Flexible Resource for Top-Weighted Comparisons Between Sets and Rankings.” SIGIR 2025.  
https://jmmackenzie.io/publication/sigir25-resource/

### 4. The strongest NWPS-specific contribution candidate is the semantics of the factorization

For complete observations:

$$
\operatorname{NWPS} = C \times F,
$$

where:

- $C$ is **weighted reference coverage**;
- $F$ is **conditional positional fidelity** among observed reference mass.

The corresponding loss decomposition is:

$$
1-\operatorname{NWPS}=(1-C)+C(1-F).
$$

This is not merely a restatement of “top weighted ranking similarity”; it gives an operational diagnostic split between **omission** and **reordering** while keeping one scalar fidelity score.

The review did not identify this exact factorization and semantics in the closest measures examined. This is a **bounded finding**, not proof that no equivalent formulation exists elsewhere.

### 5. The shared half-life is distinctive but must be justified

NWPS uses one persistence factor $\rho$ for both:

$$
\frac{w_{i+1}}{w_i}=\rho
$$

and:

$$
\frac{q(d+1)}{q(d)}=\rho.
$$

This yields the persistence-consistency property for downward moves. It also couples head importance and displacement tolerance, so calibration must acknowledge both meanings.

### 6. Censoring is not novel, but the implementation can still be useful

NWPS distinguishes confirmed omission from right-censored observation and supplies lower/upper fidelity bounds. The release includes:

- an inexpensive itemwise relaxation upper bound;
- a tighter **joint-assignment upper bound** for strict rankings.

The latter avoids the incompatibility of assigning multiple unseen items to the same best future rank.


### 7. Domain-specific reference-ranking measures provide another close precedent

Juan et al. (2020) introduced a genome-similarity **Ranking Score (RS)** and
**Ranking Accuracy (RA)**. Their reference ranking groups related individuals
into admissible rank intervals, measures displacement only when a modeled rank
falls outside its reference group, and explicitly compares observed misranking
with the expected misranking of a random ranking. This is a meaningful precedent
for three NWPS ingredients: reference intervals, positional deviation, and chance
calibration. Its objective and mathematical construction are different, but it
further rules out broad claims that those ingredients are new.

Primary source:  
L. Juan et al. “Evaluating individual genome similarity with a topic model.”
*Bioinformatics* 36(18), 4757–4764, 2020. DOI: 10.1093/bioinformatics/btaa583.
https://academic.oup.com/bioinformatics/article/36/18/4757/5861529

## Comparator implementation status in this repository

The release includes reproducible controlled implementations of:

- WS;
- RDQ M1/M2 (strict ORL case);
- RBO extrapolated point estimate;
- RBA score/upper bound for strict rankings;
- RBO^a for complete finite tied rankings at equal total depth;
- a concrete normalized reference-weighted Footrule comparator;
- weighted Kendall through SciPy/Vigna;
- tau_AP;
- Canberra distance;
- NDCG in experiment scripts.

The `reference_weighted_footrule_similarity` comparator is explicitly a **concrete weighted-Footrule instance**, not a claim to reproduce the full Kumar–Vassilvitskii generalized framework.

## Sources

1. P. Diaconis, R. L. Graham. “Spearman’s Footrule as a Measure of Disarray.” JRSS B, 1977. DOI: 10.1111/j.2517-6161.1977.tb01624.x
2. R. Fagin, R. Kumar, D. Sivakumar. “Comparing Top k Lists.” SIAM J. Discrete Math., 2003. DOI: 10.1137/S0895480102412856
3. D. Quade, I. A. Salama. “Concordance of Complete or Right-Censored Rankings Based on Spearman's Footrule.” Communications in Statistics, 2006. DOI: 10.1080/03610920600580091
4. E. Yilmaz, J. A. Aslam, S. Robertson. “A New Rank Correlation Coefficient for Information Retrieval.” SIGIR 2008. DOI: 10.1145/1390334.1390435
5. G. Jurman et al. “Algebraic Stability Indicators for Ranked Lists in Molecular Profiling.” Bioinformatics, 2008. https://academic.oup.com/bioinformatics/article/24/2/258/226884
6. R. Kumar, S. Vassilvitskii. “Generalized Distances Between Rankings.” WWW 2010. DOI: 10.1145/1772690.1772749. https://theory.stanford.edu/~sergei/papers/www10-metrics.pdf
7. W. Webber, A. Moffat, J. Zobel. “A Similarity Measure for Indefinite Rankings.” TOIS, 2010. DOI: 10.1145/1852102.1852106
8. G. Jurman et al. “Algebraic Comparison of Partial Lists in Bioinformatics.” PLOS ONE, 2012. DOI: 10.1371/journal.pone.0036540
9. S. Vigna. “A Weighted Correlation Index for Rankings with Ties.” WWW 2015. DOI: 10.1145/2736277.2741088. https://vigna.di.unimi.it/papers.php
10. W. Sałabun, K. Urbaniak. “A New Coefficient of Rankings Similarity in Decision-Making Problems.” ICCS 2020. DOI: 10.1007/978-3-030-50417-5_47. https://pmc.ncbi.nlm.nih.gov/articles/PMC7302865/
11. C. L. A. Clarke, A. Vtyurina, M. D. Smucker. “Offline Evaluation without Gain.” ICTIR 2020. DOI: 10.1145/3409256.3409816
12. C. L. A. Clarke, M. D. Smucker, A. Vtyurina. “Offline Evaluation by Maximum Similarity to an Ideal Ranking.” CIKM 2020. DOI: 10.1145/3340531.3411915. https://github.com/claclark/Compatibility
13. M. Corsi, J. Urbano. “The Treatment of Ties in Rank-Biased Overlap.” SIGIR 2024. DOI: 10.1145/3626772.3657700. https://arxiv.org/abs/2406.07121
14. A. Aveni, L. Crippa, G. Principi. “On the Weighted Top-Difference Distance: Axioms, Aggregation, and Approximation.” 2024. https://arxiv.org/abs/2403.15198
15. A. Moffat, J. Mackenzie, A. Mallia, M. Petri. “Rank-Biased Quality Measurement for Sets and Rankings.” SIGIR-AP 2024. DOI: 10.1145/3673791.3698405. https://jmmackenzie.io/pdf/mmmp24-sigirap.pdf
16. A. Moffat et al. “A Flexible Resource for Top-Weighted Comparisons Between Sets and Rankings.” SIGIR 2025. https://jmmackenzie.io/publication/sigir25-resource/
17. “Nonparametric Significance Test of the Weighted Similarity Coefficient.” Journal of Computational Science, 2026. https://www.sciencedirect.com/science/article/pii/S1877750326001067
18. X. Zhou, A. Moschitti, D. Class. “Rank-Deviation Quality: A Distance-Aware Metric for Multi-Answer Retrieval and Ranking Evaluation.” 2026. https://arxiv.org/abs/2608.25318
19. L. Juan et al. “Evaluating individual genome similarity with a topic model.” Bioinformatics, 2020. DOI: 10.1093/bioinformatics/btaa583. https://academic.oup.com/bioinformatics/article/36/18/4757/5861529
