# Homogenization Metrics: Comparison & Recommendation
## Deliverable II — Which Metrics to Use?

---

## Quick Summary

| Metric | Measures | Text Length Robust? | Compute Cost | Best For |
|--------|----------|:-------------------:|:------------:|---------|
| **TTR** | Vocabulary diversity | ❌ Breaks on different lengths | Trivial | Fixed-length comparisons only |
| **MTLD** | Sequential lexical diversity | ✅ Yes (>100 tokens) | Trivial | Long texts (articles, reviews) |
| **Yule's K** | Vocabulary concentration | ✅ Yes (>200 tokens) | Trivial | Any text length, robust baseline |
| **Cosine Similarity** (embeddings) | Semantic similarity between texts | ✅ Yes | Heavy (GPU) | Meaning-level homogeneity |
| **Centroid Distance** | Spread of texts in embedding space | ✅ Yes | Heavy (GPU) | Group-level diversity |
| **JSD** (Jensen-Shannon Divergence) | Distribution shift between time periods | ✅ Yes | Moderate | Detecting change over time |
| **Perplexity** | How "predictable" text is | ⚠️ Varies | Heavy (LLM) | Detecting AI-generated text patterns |

---

## The Problem with TTR

TTR is what Mark mentioned, but it has a fatal flaw: **it systematically decreases as text gets longer**. A 50-word tweet and a 500-word review will have wildly different TTRs regardless of homogeneity.

**Use MTLD or Yule's K instead** — they solve this problem.

TTR is still fine if you:
- Compare texts of the **same length** (truncate to fixed window)
- Use it as one signal among several
- Report it because the audience expects it (it's the most well-known metric)

---

## Recommended Metric Stack

### Tier 1 — Always Compute (primary evidence)

| Metric | Why | Implementation |
|--------|-----|----------------|
| **MTLD** | Length-robust lexical diversity, easy to compute | `lexicalrichness` Python package |
| **Pairwise Cosine Similarity** | Semantic homogeneity (what de Rooij used) | `sentence-transformers` → cosine |
| **JSD between time periods** | Detects distributional shift pre/post ChatGPT | `scipy.spatial.distance.jensenshannon` |

### Tier 2 — Robustness Checks (supporting evidence)

| Metric | Why | Implementation |
|--------|-----|----------------|
| **Yule's K** | Most text-length-robust classical metric | Simple formula, manual implementation |
| **Embedding Variance** | How spread out a group's texts are | `np.var()` on embedding matrix |
| **TTR** (fixed-window) | Expected by audience, easy to explain | Truncate to N tokens, compute |

### Tier 3 — Stretch (if time allows)

| Metric | Why |
|--------|-----|
| Perplexity (GPT-2 based) | Detects "AI-like" predictability in text |
| Sentence length variance | Structural homogenization (AI writes uniform-length sentences) |

---

## Metrics by Data Source Type

| Data Source | Typical Text Length | Recommended Metrics |
|-------------|-------------------|-------------------|
| Tweets / YouTube comments | 10-50 words | Cosine similarity, embedding variance (too short for lexical metrics) |
| Amazon / Yelp reviews | 50-200 words | MTLD + cosine similarity + TTR (fixed window) |
| Stack Overflow answers | 100-1000 words | MTLD + Yule's K + cosine similarity + JSD |
| PubMed abstracts | 150-350 words | MTLD + cosine similarity + JSD |
| Reddit posts | 100-500 words | MTLD + cosine similarity |
| arXiv abstracts | 100-300 words | MTLD + cosine similarity + JSD |

---

## How to Compute "Homogeneity Score" for a Time Period

1. **Lexical approach (MTLD/Yule's K):**
   - Compute MTLD per text in a time-window (e.g., Q1 2022)
   - Average across all texts → lower average = more homogeneous writing
   - Track this average over time → downward trend = increasing homogenization

2. **Semantic approach (Cosine Similarity):**
   - Embed all texts in a time-window using `all-MiniLM-L6-v2` or similar
   - Compute average pairwise cosine similarity within the group
   - Higher average = texts are more semantically similar = more homogeneous
   - Track over time → upward trend = increasing homogenization

3. **Distributional approach (JSD):**
   - Build word/n-gram frequency distribution for period A (pre-ChatGPT) and period B (post)
   - Compute JSD between the two distributions
   - Higher JSD = bigger shift. Compare JSD(2021→2022) vs JSD(2022→2023) — if the post-ChatGPT shift is larger, that's evidence of AI-driven change

---

## Cost Estimate for Computing at Scale

| Metric | 1M texts | 10M texts | Bottleneck |
|--------|----------|-----------|------------|
| MTLD | ~5 min | ~50 min | CPU only, trivial |
| Yule's K | ~2 min | ~20 min | CPU only, trivial |
| TTR | ~1 min | ~10 min | CPU only, trivial |
| Cosine similarity (pairwise) | ~2 hrs (GPU) | Infeasible for full pairwise | Sampling needed |
| Cosine similarity (sampled) | ~30 min | ~3 hrs | GPU for embeddings |
| JSD | ~5 min | ~30 min | CPU only |

**Note:** For cosine similarity at scale, you DON'T compute all pairs (N² problem). Instead:
- Sample 1000-5000 texts per time-period-topic bucket
- Compute pairwise within sampled groups
- Or: compute centroid, then average distance to centroid (O(N) not O(N²))

---

## For the Mark Discussion

**Bottom line recommendation:**
> Use **MTLD + Pairwise Cosine Similarity** as the two primary metrics. MTLD captures surface-level lexical homogenization. Cosine similarity captures deeper semantic convergence. If they both show the same trend, the evidence is strong. If they diverge, that's analytically interesting (surface diversity maintained but meaning converging, or vice versa).
>
> Add TTR as a secondary metric because it's widely known and easy to explain in a paper, but note its text-length limitation. Use JSD to formally test for distributional shifts between time periods.

See `research/METRICS-RESEARCH.md` for the full detailed comparison of all 16 metrics.
