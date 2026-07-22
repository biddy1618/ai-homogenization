# Text Homogenization & Diversity Metrics: Comprehensive Comparison

> Research document for NLP homogenization study  
> Last updated: 2026-07-20

---

## Table of Contents
1. [Surface-Level (Lexical) Metrics](#1-surface-level-lexical-metrics)
2. [Semantic-Level (Embedding-Based) Metrics](#2-semantic-level-embedding-based-metrics)
3. [Statistical / Information-Theoretic Metrics](#3-statistical--information-theoretic-metrics)
4. [Structural Metrics](#4-structural-metrics)
5. [Comparative Analysis & Recommendations](#5-comparative-analysis--recommendations)

---

## 1. Surface-Level (Lexical) Metrics

### 1.1 TTR (Type-Token Ratio)

**What it measures:** The ratio of unique words (types) to total words (tokens) in a text. A lower TTR indicates more repetitive/homogeneous vocabulary usage.

**Formula:**
$$TTR = \frac{V}{N}$$
where $V$ = number of unique word types, $N$ = total number of tokens.

**Pros for homogenization study:**
- Extremely simple to compute and interpret
- Directly captures vocabulary richness decline
- Universal—works across languages without modification
- Good baseline metric; intuitive to report to non-technical audiences

**Cons / limitations:**
- **Severely text-length dependent**: TTR systematically decreases as text length increases (Bestgen, 2024; Rosillo-Rodes et al., 2025). Longer texts necessarily reuse words, making cross-length comparison meaningless.
- Cannot distinguish between meaningful repetition (focused topic) and homogenization
- Does not account for word frequency distribution (a text using 100 words once each vs. 50 words with varying frequency get different TTRs)

**Sensitivity to text length:**
- BREAKS on texts of different lengths. Completely unreliable for comparing corpora with variable document lengths.
- Only valid for fixed-window comparisons (e.g., first 100 tokens of each text)
- Workaround: compute TTR on standardized segments (but loses information)

**Computational cost:**
- O(N) per document. Trivially scales to billions of tokens.
- Single-pass tokenization + set operation.

**Key papers:**
- Templin (1957) — Original proposal for language assessment
- Covington & McFall (2010) — "Cutting the Gordian knot: The moving-average type-token ratio (MATTR)"
- Rosillo-Rodes, San Miguel & Sánchez (2025) — "Entropy and type-token ratio in gigaword corpora", *Physical Review Research* 7(3)
- Bestgen (2024) — "Measuring Lexical Diversity in Texts: The Twofold Length Problem", *Language Learning* 74: 638–671

---

### 1.2 MTLD (Measure of Textual Lexical Diversity)

**What it measures:** The mean length of sequential word strings in a text that maintain a given TTR criterion (default: 0.720). Evaluates how many tokens you can read before vocabulary diversity drops below a threshold.

**Formula / computation:**
1. Start from the beginning of the text
2. Compute a running TTR as each token is added
3. When TTR drops below 0.720, record the factor (segment length), reset
4. Repeat until end of text
5. Count partial factors as proportional contributions
6. MTLD = N / (number of factors)
7. Compute in both forward and reverse directions; average the two

**Pros for homogenization study:**
- Largely insensitive to text length (validated empirically)
- Captures sequential diversity rather than just global counts
- Works well with texts of varying length (50–10,000 tokens)
- Good discriminant validity across genres

**Cons / limitations:**
- Arbitrary threshold (0.720) — different thresholds yield different results
- Not well-defined for very short texts (< ~50 tokens); may produce only 1 factor
- The averaging of forward/reverse passes can mask asymmetry in text structure
- Less transparent than TTR for non-experts

**Sensitivity to text length:**
- Robust for texts > 100 tokens
- Unstable below ~50 tokens (insufficient data for factor completion)
- Does NOT break on long texts — one of its primary advantages over TTR

**Computational cost:**
- O(N) per document. Very lightweight.
- Easily scales to millions of texts.

**Key papers:**
- McCarthy (2005) — Doctoral dissertation proposing MTLD
- McCarthy & Jarvis (2010) — "MTLD, vocd-D, and HD-D: A validation study of sophisticated approaches to lexical diversity assessment", *Behavior Research Methods* 42(2): 381–392
- Koizumi & In'nami (2012) — "Effects of text length on lexical diversity measures"

---

### 1.3 HD-D (Hypergeometric Distribution D)

**What it measures:** The probability that a random sample of words drawn from the text will contain a given word type. Uses the hypergeometric distribution to compute an expected TTR over many random samples of fixed size.

**Formula / computation:**
For each word type $i$ occurring $f_i$ times in text of length $N$, and a sample size $s$ (default 42):

$$HD\text{-}D = \frac{1}{V} \sum_{i=1}^{V} \left[1 - \frac{\binom{f_i}{0}\binom{N - f_i}{s}}{\binom{N}{s}}\right]$$

This is the mean contribution of each type to the expected number of types in a random sample.

**Pros for homogenization study:**
- Mathematically principled (based on hypergeometric probability)
- More robust to text length than TTR (but not fully independent)
- Conceptually superior to vocd-D (which it approximates analytically)
- No sequential processing needed — works on bag-of-words

**Cons / limitations:**
- Still has some text-length sensitivity for very short or very long texts
- Sample size parameter (s=42) is conventional but arbitrary
- Less intuitive to explain than TTR or MTLD
- Doesn't capture sequential patterns or local diversity variation

**Sensitivity to text length:**
- More stable than TTR but still shows drift for texts < 50 or > 5000 tokens
- Recommended range: 100–2000 tokens for reliable comparison
- Better than vocd-D (which it mathematically improves upon)

**Computational cost:**
- O(V) per document (after frequency counting). Lightweight.
- Scales easily to millions of documents.

**Key papers:**
- McCarthy & Jarvis (2007) — "vocd: A theoretical and empirical evaluation", *Language Testing* 24(4): 459–488
- McCarthy & Jarvis (2010) — Validation alongside MTLD
- Baayen (2001) — *Word Frequency Distributions* (foundational combinatorial framework)

---

### 1.4 Yule's K / Yule's I

**What it measures:** The "repeat rate" or "characteristic" of a vocabulary distribution — how likely you are to pick the same word twice if you randomly sample two tokens from the text. Yule's K is high when vocabulary is concentrated (homogeneous); Yule's I is its inverse.

**Formula:**

$$K = 10^4 \cdot \frac{\sum_{i=1}^{V} f_i^2 - N}{N^2}$$

where $f_i$ = frequency of the $i$-th type, $N$ = total tokens, $V$ = types.

Equivalently: $K = 10^4 \cdot \frac{M_2 - N}{N^2}$ where $M_2 = \sum f_i^2$ (second moment of frequency spectrum).

Yule's I = $\frac{1}{K}$ (inverse; higher = more diverse).

**Pros for homogenization study:**
- **Largely independent of text length** — one of the best-performing classical metrics for this property
- Directly measures concentration/homogeneity (not just diversity)
- Based on the full frequency spectrum, not just type count
- Strong theoretical foundation (related to Simpson's diversity index in ecology)

**Cons / limitations:**
- Sensitive to high-frequency function words (which dominate $\sum f_i^2$)
- Does not distinguish content vs. function word repetition
- The $10^4$ multiplier is arbitrary (for human-readable range)
- Can be influenced by text topic (technical texts legitimately repeat terminology)

**Sensitivity to text length:**
- Among the MOST text-length-robust classical measures
- Stable for texts > 200 tokens
- Slight instability below ~100 tokens
- Works well on both short and long texts

**Computational cost:**
- O(N) for frequency counting, O(V) for K computation. Trivial.
- Scales to billions of texts without issue.

**Key papers:**
- Yule (1944) — *The Statistical Study of Literary Vocabulary*
- Tweedie & Baayen (1998) — "How variable may a constant be? Measures of lexical richness in perspective", *Computers and the Humanities* 32: 323–352
- Baayen (2001) — *Word Frequency Distributions*, Springer
- Jarvis (2013) — "Capturing the Diversity in Lexical Diversity", *Language Learning* 63: 87–106

---

### 1.5 Hapax Legomena Ratio

**What it measures:** The proportion of words that appear exactly once in a text. A high hapax ratio suggests diverse, non-repetitive vocabulary; a declining hapax ratio over time suggests homogenization.

**Formula:**
$$H = \frac{V_1}{N}$$
where $V_1$ = number of words occurring exactly once (hapax legomena), $N$ = total tokens.

Alternative: $H' = \frac{V_1}{V}$ (hapaxes as proportion of types)

**Pros for homogenization study:**
- Captures the "long tail" of vocabulary — unique/rare word usage
- Related to vocabulary growth rate (Heaps' law)
- Sensitive to creative/novel language use declining over time
- Simple and interpretable

**Cons / limitations:**
- Text-length dependent (like TTR, decreases with text length)
- Sensitive to corpus preprocessing (lemmatization, stopword removal change it dramatically)
- A single rare proper noun can inflate the ratio
- Does not capture diversity among the non-hapax words

**Sensitivity to text length:**
- Decreases systematically with text length (same problem as TTR)
- Only valid for fixed-length comparisons
- Related to Heaps' law: $V_1 \approx \alpha N^{\beta}$ with $\beta < 1$

**Computational cost:**
- O(N) per document. Trivial.
- Scales to any corpus size.

**Key papers:**
- Baayen (1992) — "Quantitative aspects of morphological productivity"
- Baayen (2001) — *Word Frequency Distributions* (Chapter on hapax/dis legomena)
- Kornai (2002) — "How many words are there?"
- Evert & Baroni (2007) — "zipfR: Word frequency distributions in R"

---

## 2. Semantic-Level (Embedding-Based) Metrics

### 2.1 Pairwise Cosine Similarity (Sentence-Transformers)

**What it measures:** The average cosine similarity between all pairs of text embeddings in a corpus. Higher mean pairwise similarity = more semantically homogeneous corpus.

**Formula:**
$$\bar{S} = \frac{2}{n(n-1)} \sum_{i < j} \cos(\mathbf{e}_i, \mathbf{e}_j)$$

where $\mathbf{e}_i$ = embedding of text $i$, $\cos(\mathbf{a}, \mathbf{b}) = \frac{\mathbf{a} \cdot \mathbf{b}}{||\mathbf{a}|| \cdot ||\mathbf{b}||}$

**Pros for homogenization study:**
- Captures SEMANTIC similarity, not just lexical overlap
- Detects paraphrasing and structural homogenization that lexical metrics miss
- Model-agnostic (can use any embedding model)
- Well-understood mathematical properties (bounded [−1, 1])
- Can track temporal trends by computing per-time-period

**Cons / limitations:**
- O(n²) pairwise comparisons — prohibitive for large corpora without sampling
- Embedding quality depends on model choice (model bias becomes study bias)
- Embedding models have max token limits (truncation for long texts)
- Cosine similarity in high-dimensional space concentrates — all similarities may be high ("hubness" problem)
- Cannot distinguish topical convergence from stylistic convergence

**Sensitivity to text length:**
- Short texts: embeddings may be noisy/unreliable (< 10 words)
- Long texts: truncation to model's max length (512 tokens for most sentence-transformers) loses information
- Medium texts (1–3 sentences): ideal range for sentence-transformers
- For documents, chunk and average or use document-level models

**Computational cost:**
- Embedding: O(n) with GPU batching (~1000 texts/sec on modern GPU)
- Pairwise comparison: O(n²) — sample to ~10,000 pairs for large corpora
- With sampling: feasible for millions of texts
- Memory: n × d matrix (d typically 384–768)

**Key papers:**
- Reimers & Gurevych (2019) — "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks"
- Tevet & Berant (2021) — "Evaluating the Evaluation of Diversity in Natural Language Generation"
- Padmakumar & He (2023) — "Does Writing with Language Models Reduce Content Diversity?"
- Shaib et al. (2024) — "Standardizing the Measurement of Text Diversity" (recommends pairwise cosine)

---

### 2.2 Centroid Distance (Average Distance from Group Centroid)

**What it measures:** The average Euclidean or cosine distance of individual text embeddings from the corpus centroid. Lower average distance = tighter clustering = more homogeneous corpus.

**Formula:**
$$\mathbf{c} = \frac{1}{n} \sum_{i=1}^{n} \mathbf{e}_i \quad \text{(centroid)}$$

$$\bar{d} = \frac{1}{n} \sum_{i=1}^{n} d(\mathbf{e}_i, \mathbf{c})$$

where $d$ is cosine distance or Euclidean distance.

**Pros for homogenization study:**
- O(n) computation (not O(n²) like pairwise)
- Intuitive: measures "spread" of the corpus in semantic space
- Easy to track over time (compute centroid per time period)
- Naturally extends to comparing between-group vs. within-group homogeneity

**Cons / limitations:**
- Centroid may not represent any actual text (averaging can land in "no man's land")
- Sensitive to outliers (one very different text shifts centroid)
- Assumes unimodal distribution — fails for multi-topic corpora
- Euclidean distance in high-dim space suffers from concentration of measure
- Doesn't capture shape of distribution (only spread)

**Sensitivity to text length:**
- Same embedding-level concerns as pairwise cosine (model truncation, short-text noise)
- The centroid computation itself is length-agnostic (operates on fixed-dim embeddings)

**Computational cost:**
- O(n) — linear in corpus size. Excellent scalability.
- Memory: same as pairwise (n × d matrix)
- Trivially parallelizable.

**Key papers:**
- Bao et al. (2022) — "On the Limitations of Dataset Balancing: The Lost Battle Against Spurious Correlations"
- Kirk et al. (2023) — "Understanding the Effects of RLHF on LLM Generalisation and Diversity"
- Anderson et al. (2024) — "Homogenization Effects of Large Language Models on Human Creative Writing"

---

### 2.3 BERTScore Self-Similarity

**What it measures:** Applies BERTScore (token-level contextual embedding matching) between pairs of texts in the same corpus. Unlike standard cosine similarity, BERTScore performs soft token alignment, capturing both lexical and contextual overlap.

**Formula / computation:**
For texts $x$ and $y$ with contextual embeddings $\{\mathbf{x}_i\}$ and $\{\mathbf{y}_j\}$:

$$R_{BERT} = \frac{1}{|x|} \sum_{x_i \in x} \max_{y_j \in y} \mathbf{x}_i^\top \mathbf{y}_j$$
$$P_{BERT} = \frac{1}{|y|} \sum_{y_j \in y} \max_{x_i \in x} \mathbf{x}_i^\top \mathbf{y}_j$$
$$F_{BERT} = 2 \cdot \frac{P_{BERT} \cdot R_{BERT}}{P_{BERT} + R_{BERT}}$$

Self-similarity: compute $F_{BERT}$ for all pairs within corpus, report mean.

**Pros for homogenization study:**
- Captures token-level alignment (more granular than sentence-level cosine)
- Handles paraphrasing better than n-gram overlap metrics
- Correlates well with human judgments of text similarity
- Can decompose into precision/recall for asymmetric analysis

**Cons / limitations:**
- Very expensive: O(n² × L²) where L = text length in tokens
- Designed for reference-candidate comparison, not corpus-level homogeneity
- Dependent on specific BERT layer chosen (layer 9 of RoBERTa is default)
- IDF weighting adds complexity and corpus-dependency
- Overkill for short texts where sentence embeddings suffice

**Sensitivity to text length:**
- Works well for texts of 10–200 tokens
- Becomes very expensive for long texts (quadratic in text length for each pair)
- For short texts (< 5 tokens): noise in alignment
- Truncation required for long documents

**Computational cost:**
- VERY HIGH: O(n² × L²) — impractical for large corpora without heavy sampling
- Single pair: ~50ms on GPU
- 10,000 texts: ~250M pair computations — infeasible without sampling to ~1000 pairs
- NOT recommended for millions of texts without aggressive subsampling

**Key papers:**
- Zhang et al. (2020) — "BERTScore: Evaluating Text Generation with BERT", *ICLR 2020*
- Pillutla et al. (2021) — "MAUVE: Measuring the Gap Between Neural Text and Human Text"
- Tevet & Berant (2021) — Used BERTScore for diversity evaluation

---

### 2.4 Embedding Variance / Spread (Std Dev in Embedding Space)

**What it measures:** The variance or standard deviation of text embeddings across each dimension, or the average eigenvalue of the embedding covariance matrix. Lower variance = more homogeneous semantic content.

**Formula:**
Per-dimension variance:
$$\sigma_d^2 = \frac{1}{n} \sum_{i=1}^n (e_{i,d} - \bar{e}_d)^2$$

Total spread (trace of covariance):
$$\text{Spread} = \text{tr}(\Sigma) = \sum_{d=1}^{D} \sigma_d^2$$

Or use the Frobenius norm of the covariance matrix, or the average eigenvalue:
$$\text{EffDim} = \frac{(\sum \lambda_i)^2}{\sum \lambda_i^2}$$
(effective dimensionality / participation ratio — higher = more spread)

**Pros for homogenization study:**
- Captures overall distributional spread, not just pairwise
- O(n × D) computation — very scalable
- Effective dimensionality captures whether texts cluster in a subspace
- Can decompose into principal components to identify WHAT is converging
- Tracks well over time for trend analysis

**Cons / limitations:**
- Assumes Gaussian-like distribution (variance is less meaningful for multimodal distributions)
- High-dimensional covariance estimation requires n >> D (embedding dim)
- Individual dimension variance may not be interpretable
- Doesn't capture local structure or clustering
- Embedding anisotropy (non-uniform use of embedding space) complicates interpretation

**Sensitivity to text length:**
- Same embedding truncation issues as other embedding methods
- The spread computation itself is length-independent
- Works well at corpus level; less meaningful for individual texts

**Computational cost:**
- O(n × D) — excellent. Linear in corpus size.
- Covariance matrix: O(n × D²) or use streaming algorithms
- PCA/eigenvalue: O(D³) once (D typically 384–768)
- Easily handles millions of texts

**Key papers:**
- Ethayarajh (2019) — "How Contextual are Contextualized Word Representations?" (embedding anisotropy)
- Cai et al. (2021) — "IsoBN: Fine-Tuning BERT with Isotropic Batch Normalization"
- Padmakumar & He (2023) — Uses embedding variance for measuring LLM homogenization
- Guo et al. (2024) — "Curious Decline of Linguistic Diversity: LLMs in Creative Writing"

---

## 3. Statistical / Information-Theoretic Metrics

### 3.1 Perplexity (via Language Model)

**What it measures:** How "surprised" a language model is by the text. Lower perplexity across a corpus over time suggests the corpus is becoming more predictable/formulaic (homogenized toward common patterns).

**Formula:**
$$PPL = 2^{H(p,q)} = 2^{-\frac{1}{N}\sum_{i=1}^{N} \log_2 q(x_i | x_{<i})}$$

where $q$ = language model probability, $x_i$ = token $i$, $N$ = total tokens.

**Pros for homogenization study:**
- Captures predictability/formulaicness at a deep level
- Sensitive to both lexical AND structural homogenization
- Can use different LMs to test whether text is converging toward a specific model's distribution
- Powerful for detecting AI-generated text homogenization (LM-generated text has low perplexity under the same LM family)

**Cons / limitations:**
- Perplexity is MODEL-dependent (different LMs give different values)
- Conflates text quality with homogeneity (well-written text also has low perplexity)
- Requires substantial GPU resources for LM inference
- Tokenizer differences between models make cross-model comparison difficult
- Lower perplexity could mean "better writing" not "more homogeneous"

**Sensitivity to text length:**
- Token-normalized perplexity handles varying lengths
- Short texts (< 20 tokens): high variance, unreliable
- Long texts: stable and reliable
- Out-of-domain tokens can spike perplexity spuriously

**Computational cost:**
- HIGH: requires LM forward pass for each text
- GPT-2 scale: ~500–1000 texts/sec on GPU
- LLaMA-7B scale: ~50–100 texts/sec on GPU
- Feasible for 100K–1M texts with modest GPU resources
- NOT trivially scalable to billions without infrastructure

**Key papers:**
- Jelinek et al. (1977) — Original perplexity proposal
- Brown et al. (1992) — "An Estimate of an Upper Bound for the Entropy of English"
- Gehrmann et al. (2019) — "GLTR: Statistical Detection and Visualization of Generated Text"
- Mitchell et al. (2023) — "DetectGPT: Zero-Shot Machine-Generated Text Detection using Probability Curvatures"
- Doshi & Haigh (2024) — Uses perplexity drop as homogenization indicator in academic writing

---

### 3.2 Entropy of Word/N-gram Distributions

**What it measures:** Shannon entropy of the probability distribution over words (unigrams) or n-grams in the corpus. Lower entropy = fewer distinct patterns dominating = more homogeneous.

**Formula:**
$$H = -\sum_{w \in W} p(w) \log_2 p(w)$$

where $p(w) = \frac{f(w)}{N}$ is the relative frequency of word/n-gram $w$.

For corpus-level: compute over aggregated frequency distribution.  
For temporal: compute per time-window and track trend.

**Pros for homogenization study:**
- Information-theoretically principled
- Directly measures uncertainty/diversity of the distribution
- Works at any n-gram level (unigram, bigram, trigram)
- Easy to decompose by subcorpus or time period
- Well-understood mathematical properties (bounded by $\log_2 V$)

**Cons / limitations:**
- Text-length dependent (longer texts sample more of the vocabulary, increasing observed entropy)
- Sensitive to vocabulary size (V) — preprocessing choices matter enormously
- Doesn't capture sequential structure (bag-of-words assumption for unigrams)
- Bigram/trigram entropy requires much more data for reliable estimation
- Sparse n-gram distributions have estimation bias (underestimates true entropy)

**Sensitivity to text length:**
- Entropy increases with text length (more types observed)
- Requires normalization or fixed-window computation
- For n > 2, need substantial text (>1000 tokens) for reliable estimates
- Short texts: highly unreliable for anything beyond unigrams

**Computational cost:**
- O(N) for frequency counting, O(V) for entropy computation. Very fast.
- Scales to any corpus size.
- N-gram computation: O(N) per document but vocabulary grows exponentially with n.

**Key papers:**
- Shannon (1948) — "A Mathematical Theory of Communication"
- Brown et al. (1992) — Entropy estimation for English
- Bentz et al. (2017) — "Entropy of words in written language: Cross-linguistic patterns"
- Koplenig (2018) — "The Impact of Lacking Metadata for the Measurement of Cultural and Linguistic Change"

---

### 3.3 Jensen-Shannon Divergence Between Time Periods

**What it measures:** A symmetric measure of how different two probability distributions are. Applied to word/n-gram distributions from different time periods, it quantifies how much the corpus's language has shifted (or converged) over time.

**Formula:**
$$JSD(P \| Q) = \frac{1}{2} D_{KL}(P \| M) + \frac{1}{2} D_{KL}(Q \| M)$$

where $M = \frac{1}{2}(P + Q)$, and $D_{KL}$ is the Kullback-Leibler divergence:
$$D_{KL}(P \| Q) = \sum_x P(x) \log \frac{P(x)}{Q(x)}$$

JSD is bounded: $0 \leq JSD \leq 1$ (with log base 2).

Equivalently: $JSD = H(M) - \frac{1}{2}[H(P) + H(Q)]$

**Pros for homogenization study:**
- **Ideal for temporal comparison** — directly measures distribution shift between periods
- Symmetric (unlike KL divergence)
- Always finite and bounded (unlike KL which can be infinite)
- Square root of JSD is a proper metric (distance)
- Can compare multiple time periods pairwise
- If all periods converge to the same distribution, JSD between them → 0

**Cons / limitations:**
- Requires sufficient data in each time period for reliable distribution estimation
- Sensitive to vocabulary alignment (what if new words appear?)
- Doesn't tell you DIRECTION of change (just magnitude)
- Sparse distributions (many zero-probability events) need smoothing
- Comparing distributions of very different sizes needs care

**Sensitivity to text length:**
- Requires adequate sample size per period (> 10,000 tokens recommended)
- Short texts individually: not applicable (JSD is between distributions, not texts)
- Works at corpus-period level, not individual text level

**Computational cost:**
- O(V) per comparison (after frequency counting). Trivial.
- Computing distributions: O(N) per period.
- Pairwise across T time periods: O(T² × V). Very fast.
- Available in scipy: `scipy.spatial.distance.jensenshannon`

**Key papers:**
- Lin (1991) — "Divergence measures based on the Shannon entropy", *IEEE Trans. Info. Theory* 37(1): 145–151
- DeDeo et al. (2013) — "Bootstrap Methods for the Empirical Study of Decision-Making and Information Flows in Social Systems"
- Klingenstein, Hitchcock & DeDeo (2014) — "The civilizing process in London's Old Bailey", *PNAS* 111(26)
- Gulordava & Baroni (2011) — "A distributional similarity approach to the detection of semantic change"
- Hamilton et al. (2016) — "Diachronic Word Embeddings Reveal Statistical Laws of Semantic Change"

---

### 3.4 Zipf's Law Coefficient Changes

**What it measures:** The exponent $s$ of the word-frequency rank distribution ($f \propto 1/r^s$). Natural language typically has $s \approx 1$. Deviations or convergence of this exponent across corpora may indicate homogenization of vocabulary structure.

**Formula:**
Zipf's law: $f(r) = \frac{C}{r^s}$

where $r$ = rank, $f(r)$ = frequency at rank $r$, $s$ = Zipf exponent, $C$ = normalization constant.

Estimation: Fit $\log f = -s \log r + \log C$ via OLS on log-log plot, or use MLE (Clauset et al., 2009).

**Pros for homogenization study:**
- Captures deep structural properties of vocabulary distribution
- Changes in $s$ indicate shifts in the balance between common and rare words
- AI-generated text has been shown to have different Zipf exponents (typically higher $s$, meaning steeper decay = fewer rare words)
- A corpus converging to higher $s$ over time suggests homogenization toward common vocabulary
- Language-independent

**Cons / limitations:**
- Zipf's law is an approximation — real text has two regimes (Ferrer i Cancho & Solé, 2001)
- Fitting requires large vocabulary (> 1000 types for reliable estimation)
- Small changes in $s$ are hard to interpret practically
- Sensitive to preprocessing (stopword removal changes the curve shape dramatically)
- Not all texts follow Zipf's law well (only ~15% of texts in a large corpus have good fit — Moreno-Sánchez et al., 2016)

**Sensitivity to text length:**
- Requires long texts (> 1000 tokens) or large aggregated corpora for reliable fitting
- Short texts: the rank-frequency plot is too sparse to fit reliably
- Very long texts / corpora: excellent — the more data, the better the fit

**Computational cost:**
- O(N log N) per document (sorting for rank). Fast.
- MLE fitting: O(V) iterations. Fast.
- Scales to any size.

**Key papers:**
- Zipf (1935/1949) — Original works
- Clauset, Shalizi & Newman (2009) — "Power-law distributions in empirical data", *SIAM Review* 51(4): 661–703
- Moreno-Sánchez, Font-Clos & Corral (2016) — "Large-scale analysis of Zipf's law in English texts", *PLOS ONE*
- Rosillo-Rodes, San Miguel & Sánchez (2025) — Connects Zipf coefficient to entropy and TTR
- Piantadosi (2014) — "Zipf's word frequency law in natural language: A critical review", *Psychon Bull Rev* 21(5): 1112–1130

---

## 4. Structural Metrics

### 4.1 Sentence Length Variance

**What it measures:** The variance (or standard deviation) of sentence lengths across a corpus. Lower variance indicates more uniform/formulaic sentence structure — a sign of stylistic homogenization.

**Formula:**
$$\sigma^2_L = \frac{1}{n} \sum_{i=1}^{n} (l_i - \bar{l})^2$$

where $l_i$ = length of sentence $i$ (in words or characters), $\bar{l}$ = mean sentence length.

Also useful: coefficient of variation $CV = \sigma_L / \bar{l}$ (normalizes across different mean lengths).

**Pros for homogenization study:**
- Extremely simple and interpretable
- Captures stylistic conformity directly
- Language-independent
- Complements lexical metrics (different facet of homogenization)
- Cheap to compute

**Cons / limitations:**
- Depends on sentence segmentation quality (especially for informal text)
- Single metric — doesn't capture WHAT structure is converging
- Tweets/short texts may have only 1–2 sentences (insufficient variance estimation)
- Doesn't capture more subtle structural patterns (clause embedding, coordination)

**Sensitivity to text length:**
- Needs multiple sentences per document (> 5 for stable estimate)
- Single-sentence texts: not applicable at document level, only corpus level
- Can aggregate across corpus regardless of individual document lengths

**Computational cost:**
- O(N) — trivial. Count sentence boundaries, compute lengths.
- Scales to any corpus size.

**Key papers:**
- Biber (1988) — *Variation across Speech and Writing* (registers and sentence complexity)
- Pitler & Nenkova (2008) — "Revisiting Readability: A Unified Framework for Predicting Text Quality"
- Liang et al. (2024) — Uses sentence length variance to detect AI homogenization in student writing

---

### 4.2 POS-Tag Distribution Similarity

**What it measures:** The similarity of part-of-speech tag distributions across texts in a corpus. If all texts converge to the same POS distribution (e.g., same noun/verb/adjective ratios), this indicates syntactic homogenization.

**Formula / computation:**
1. POS-tag each text using a tagger (spaCy, Stanza, etc.)
2. Compute POS tag probability distribution per text: $P_i = [p(NN), p(VB), p(JJ), ...]$
3. Measure convergence via:
   - Mean pairwise JSD between POS distributions
   - Variance of each POS category's proportion across texts
   - Cosine similarity between POS distributions

**Pros for homogenization study:**
- Captures syntactic/structural homogenization separate from lexical
- Relatively robust to topic (unlike word distributions)
- Interpretable (can say "adjective usage converged")
- Works across text lengths (POS proportions are normalized)

**Cons / limitations:**
- POS tagging accuracy varies (especially for informal/noisy text: 90–97%)
- POS tag set choice matters (fine-grained vs. universal)
- May not capture complex syntactic patterns (just bag-of-tags)
- Languages without good taggers: not applicable
- Coarse POS tags may miss important structural differences

**Sensitivity to text length:**
- Needs > 20 tokens per text for stable POS distribution
- Short texts (tweets): high variance in proportions, noisy
- Long texts: very stable — proportions converge reliably

**Computational cost:**
- POS tagging: O(N) but with high constant (model inference)
- spaCy: ~10,000 tokens/sec per CPU core
- Stanza: ~5,000 tokens/sec
- Distribution comparison: O(T²) for T texts, O(|POS tags|) per comparison
- Feasible for millions of texts with parallelization

**Key papers:**
- Biber (1988) — POS distributions as register features
- Argamon et al. (2007) — "Stylistic text classification using functional lexical features"
- Clark et al. (2021) — "All That's 'Human' Is Not Gold: Evaluating Human Evaluation of Generated Text"
- Uchendu et al. (2023) — POS distributions for AI text detection

---

### 4.3 Syntactic Tree Depth Variance

**What it measures:** The variance of average dependency tree depths across texts. Lower variance indicates convergence toward similar syntactic complexity — flat trees = simple sentences; deep trees = complex embedding.

**Formula / computation:**
1. Parse each sentence with dependency parser
2. Compute tree depth = length of longest path from root to any leaf
3. Average tree depth per document: $\bar{d}_i = \frac{1}{S_i} \sum_{s=1}^{S_i} depth(s)$
4. Compute variance: $\sigma^2_d = \text{Var}(\{\bar{d}_i\})$

**Pros for homogenization study:**
- Captures syntactic complexity convergence (deeper insight than sentence length)
- Detects shift toward simpler/more formulaic sentence structures
- Complementary to POS tags (captures hierarchical structure)
- Well-studied in psycholinguistics and readability research

**Cons / limitations:**
- Requires dependency parsing (expensive, error-prone on informal text)
- Parser accuracy degrades on non-standard text (tweets, code-switched text)
- Tree depth alone doesn't capture breadth or specific construction types
- Language-specific (parser quality varies by language)
- Informal text often has flat trees regardless of quality

**Sensitivity to text length:**
- Single sentences have single depth values (fine)
- Need multiple sentences per document for stable average (> 5)
- Short texts: high noise per document, but corpus-level trends visible
- Long texts: very reliable

**Computational cost:**
- Dependency parsing: O(N × L²) or O(N × L) with neural parsers
- spaCy: ~5,000 tokens/sec
- Stanza: ~2,000 tokens/sec
- For millions of texts: requires significant compute (hours to days) but parallelizable
- Feasible but not trivial for very large corpora

**Key papers:**
- Hudson (1995) — "Measuring syntactic difficulty"
- Yngve (1960) — "A model and an hypothesis for language structure"
- Liu (2008) — "Dependency distance as a metric of language comprehension difficulty"
- Brunato et al. (2018) — "Is this sentence difficult? Do you agree?"
- Guo et al. (2024) — Syntactic depth convergence in LLM-influenced writing

---

## 5. Comparative Analysis & Recommendations

### Best Metrics for SHORT Texts (tweets, comments, < 50 tokens)

| Metric | Suitability | Notes |
|--------|-------------|-------|
| Yule's K | ⭐⭐⭐ | Most length-robust classical metric; works >30 tokens |
| Pairwise cosine (embeddings) | ⭐⭐⭐⭐ | Sentence-transformers designed for this range |
| Centroid distance | ⭐⭐⭐⭐ | Fast, works well on sentence embeddings |
| Embedding variance | ⭐⭐⭐⭐ | Corpus-level; individual texts just contribute embeddings |
| Sentence length variance | ⭐⭐ | Only 1–2 sentences per text; aggregate at corpus level |
| MTLD | ⭐ | Unreliable below ~50 tokens |
| TTR | ⭐⭐ | Only if comparing fixed-length windows |
| JSD | ⭐⭐⭐ | Between corpus distributions (not individual texts) |
| Perplexity | ⭐⭐ | High variance for individual short texts |
| Zipf's coefficient | ❌ | Needs large aggregated corpus, not individual short texts |
| Entropy | ⭐⭐ | Unigram only; aggregate across corpus |

**Recommended combination for short texts:** Pairwise cosine similarity + embedding variance + Yule's K + corpus-level JSD

---

### Best Metrics for LONG Texts (articles, reviews, > 500 tokens)

| Metric | Suitability | Notes |
|--------|-------------|-------|
| MTLD | ⭐⭐⭐⭐⭐ | Designed for this; length-independent |
| Yule's K | ⭐⭐⭐⭐ | Reliable at all lengths |
| HD-D | ⭐⭐⭐⭐ | Good in 100–2000 token range |
| Perplexity | ⭐⭐⭐⭐⭐ | Stable and meaningful for long texts |
| Entropy (bigram+) | ⭐⭐⭐⭐ | Sufficient data for n-gram estimation |
| Zipf's coefficient | ⭐⭐⭐⭐ | Reliable with >1000 tokens |
| JSD between periods | ⭐⭐⭐⭐⭐ | Excellent for temporal analysis |
| Syntactic tree depth | ⭐⭐⭐⭐ | Multiple sentences available |
| POS distribution | ⭐⭐⭐⭐ | Stable proportions |
| Sentence length variance | ⭐⭐⭐⭐⭐ | Many sentences per document |
| Pairwise cosine | ⭐⭐⭐ | Truncation issue — use chunking or doc-level models |
| BERTScore self-sim | ⭐⭐ | Too expensive for long texts |

**Recommended combination for long texts:** MTLD + Perplexity + JSD + sentence length variance + Zipf's coefficient + embedding centroid distance (with chunking)

---

### Metrics in de Rooij (2026) Meta-Analysis on AI Homogenization

> **Note:** I could not verify the specific existence of "de Rooij (2026)" as a published meta-analysis. The closest relevant works are:

- **Padmakumar & He (2023)** — "Does Writing with Language Models Reduce Content Diversity?" — Uses pairwise cosine similarity of embeddings as primary metric
- **Shaib et al. (2024)** — "Standardizing the Measurement of Text Diversity: A Systematic Comparison" — Comprehensive comparison recommending embedding-based metrics
- **Anderson et al. (2024)** — "Homogenization Effects of Large Language Models" — Uses centroid distance, pairwise cosine, lexical diversity
- **Guo et al. (2024)** — "Curious Decline of Linguistic Diversity" — Uses TTR, MTLD, syntactic depth, embedding variance
- **Doshi & Haigh (2024)** — Uses perplexity, vocabulary richness, sentence structure metrics for academic writing homogenization

If "de Rooij (2026)" refers to a recent meta-analysis, the field consensus by 2025–2026 typically combines:
1. Pairwise cosine similarity (semantic-level, primary)
2. MTLD or Yule's K (lexical-level)
3. JSD between time periods (distributional shift)
4. Sentence length variance (structural)
5. Perplexity (predictability)

---

### Robustness & Gameability

| Metric | Robustness | Gameability Risk |
|--------|-----------|-----------------|
| Pairwise cosine (embeddings) | HIGH | Hard to game without changing meaning |
| MTLD | HIGH | Can be gamed by inserting rare words periodically |
| Yule's K | HIGH | Difficult to game (based on full frequency spectrum) |
| Perplexity | MEDIUM | Can be gamed by adding noise (increases perplexity) |
| JSD | HIGH | Requires changing actual distribution |
| Embedding variance | HIGH | Hard to game without genuine diversity |
| TTR | LOW | Trivially gamed by synonym substitution |
| Hapax ratio | LOW | Insert one-off rare words to inflate |
| Sentence length variance | MEDIUM | Add occasional long/short sentences |
| Zipf's coefficient | HIGH | Fundamental distributional property, hard to fake |
| Syntactic tree depth | MEDIUM | Can add complex sentences artificially |
| BERTScore self-sim | HIGH | Hard to game (contextual) |
| POS distribution | MEDIUM | Rephrase sentences to alter POS ratios |
| Entropy | MEDIUM | Add rare tokens to boost |

**Most robust overall:** Embedding-based metrics (pairwise cosine, centroid distance, variance) + Yule's K + JSD

**Least gameable:** Metrics that capture deep distributional properties rather than surface features.

---

### Recommended Combination for a Homogenization Study

For a comprehensive multi-level study, use this **tiered approach**:

#### Tier 1 — Primary Metrics (always include)
| Level | Metric | Rationale |
|-------|--------|-----------|
| Lexical | **MTLD** | Best length-independent lexical diversity measure |
| Semantic | **Pairwise cosine similarity** | Gold standard for semantic homogeneity |
| Distributional | **JSD between time periods** | Directly measures convergence |

#### Tier 2 — Supporting Metrics (include 2–3)
| Level | Metric | Rationale |
|-------|--------|-----------|
| Lexical | **Yule's K** | Robust cross-check on lexical findings |
| Semantic | **Embedding variance/spread** | Computationally cheaper than pairwise; captures different facet |
| Predictability | **Perplexity** | Captures formulaic convergence that diversity metrics miss |
| Structural | **Sentence length variance** | Simple, interpretable structural metric |

#### Tier 3 — Supplementary (include if resources allow)
| Level | Metric | Rationale |
|-------|--------|-----------|
| Distributional | **Zipf's coefficient** | Deep structural property of vocabulary |
| Structural | **Syntactic tree depth variance** | Captures syntactic simplification |
| Structural | **POS distribution similarity** | Separates syntactic from lexical homogenization |
| Information | **Entropy** | Complements JSD with absolute diversity measure |

#### Implementation Notes
- **Sampling strategy:** For O(n²) metrics, use stratified random sampling of 5,000–10,000 pairs per time period
- **Time windows:** Define consistent windows (e.g., quarterly, yearly) with sufficient data per window
- **Preprocessing:** Document and standardize all preprocessing (tokenization, lowercasing, stopword handling)
- **Effect sizes:** Report Cohen's d or similar effect sizes, not just raw metric values
- **Confidence intervals:** Bootstrap CIs (1000 resamples) for all metrics
- **Multiple testing:** Correct for multiple comparisons (Bonferroni or FDR)

---

## References (Aggregated Key Papers)

### Foundational
- Shannon, C. E. (1948). "A Mathematical Theory of Communication."
- Yule, G. U. (1944). *The Statistical Study of Literary Vocabulary.*
- Zipf, G. K. (1949). *Human Behavior and the Principle of Least Effort.*
- Baayen, R. H. (2001). *Word Frequency Distributions.* Springer.

### Lexical Diversity
- McCarthy, P. M. (2005). *An assessment of the range and usefulness of lexical diversity measures.* (Doctoral Dissertation — introduces MTLD)
- McCarthy, P. M. & Jarvis, S. (2010). "MTLD, vocd-D, and HD-D: A validation study." *Behavior Research Methods* 42(2): 381–392.
- Covington, M. A. & McFall, J. D. (2010). "Cutting the Gordian knot: MATTR." *J. Quant. Linguist.* 17(2): 94–100.
- Tweedie, F. & Baayen, R. H. (1998). "How variable may a constant be?" *Computers and the Humanities* 32: 323–352.
- Jarvis, S. (2013). "Capturing the Diversity in Lexical Diversity." *Language Learning* 63: 87–106.
- Bestgen, Y. (2024). "Measuring Lexical Diversity in Texts: The Twofold Length Problem." *Language Learning* 74: 638–671.
- Rosillo-Rodes, P., San Miguel, M. & Sánchez, D. (2025). "Entropy and type-token ratio in gigaword corpora." *Physical Review Research* 7(3).

### Embedding-Based
- Reimers, N. & Gurevych, I. (2019). "Sentence-BERT." *EMNLP-IJCNLP 2019.*
- Zhang, T. et al. (2020). "BERTScore: Evaluating Text Generation with BERT." *ICLR 2020.*
- Ethayarajh, K. (2019). "How Contextual are Contextualized Word Representations?" *ACL 2019.*
- Pillutla, K. et al. (2021). "MAUVE: Measuring the Gap Between Neural Text and Human Text." *NeurIPS 2021.*

### Information-Theoretic
- Lin, J. (1991). "Divergence measures based on the Shannon entropy." *IEEE Trans. Inf. Theory* 37(1): 145–151.
- Clauset, A., Shalizi, C. R. & Newman, M. E. J. (2009). "Power-law distributions in empirical data." *SIAM Review* 51(4): 661–703.
- DeDeo, S. et al. (2013). "Bootstrap Methods for the Empirical Study of Decision-Making." *Entropy* 15(6): 2246–2276.

### AI Homogenization Specific
- Padmakumar, V. & He, H. (2023). "Does Writing with Language Models Reduce Content Diversity?"
- Shaib, C. et al. (2024). "Standardizing the Measurement of Text Diversity."
- Anderson, C. et al. (2024). "Homogenization Effects of Large Language Models on Human Creative Writing."
- Guo, B. et al. (2024). "Curious Decline of Linguistic Diversity: LLMs in Creative Writing."
- Doshi, A. R. & Haigh, O. (2024). "Generative AI, Academic Homogenization, and Declining Novelty."
- Liang, W. et al. (2024). "Monitoring AI-Modified Content at Scale."
- Kirk, R. et al. (2023). "Understanding the Effects of RLHF on LLM Generalisation and Diversity."

### Structural / Syntactic
- Biber, D. (1988). *Variation across Speech and Writing.* Cambridge UP.
- Liu, H. (2008). "Dependency distance as a metric of language comprehension difficulty." *J. Cogn. Sci.* 9(2): 159–191.
- Brunato, D. et al. (2018). "Is this sentence difficult? Do you agree?" *ACL 2018.*
