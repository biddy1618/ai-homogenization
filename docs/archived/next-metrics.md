# Next Metrics — Roadmap

*What we have measured, what it showed, and which metrics to add next.*
Companion to [`metrics-recommendation.md`](metrics-recommendation.md) (generic catalog) and
[`next-steps.md`](../research/next-steps.md) (forward roadmap after the BERTopic within-topic
result); see [`critical-review.md`](../research/critical-review.md) for the self-critique.
This document is empirically grounded in the Cross Validated results to date.

---

## Where we are

Corpus: Cross Validated (stats.stackexchange) answers, 219k answers, 63 quarters (2010Q3–2026Q1).
Every metric is computed **raw** and **length-controlled** (first 100 tokens) per quarter,
with the ChatGPT release (2022Q4) marked.

| Family | Metric | Implemented in | Raw trend | Length-controlled trend |
|--------|--------|----------------|-----------|--------------------------|
| Surface / lexical | MTLD | `src/metrics.py`, `src/pipeline.py` | flat / slight recovery | flat |
| Surface / lexical | TTR | `src/metrics.py`, `src/pipeline.py` | falls (length-driven) | flat |
| Surface / semantic | Pairwise cosine (TF-IDF) | `src/pipeline.py` | rises | flat |
| Semantic | Pairwise cosine (LSA embeddings) | `src/semantic.py` | rises 0.096→0.146 | flat ~0.10 |
| Semantic | Centroid variance (LSA) | `src/semantic.py` | falls 0.903→0.853 | flat ~0.90 |
| Semantic | Effective dimensionality (LSA) | `src/semantic.py` | mild decline | ~flat |
| **Semantic (true)** | **Pairwise cosine (Sentence-BERT/MiniLM)** | `src/semantic_bert.py` | **falls 0.082→0.052 (2010–21), then rises to ~0.070 (2023–26)** | **same shape, survives length control** |
| **Semantic (true), Philosophy** | **Pairwise cosine (Sentence-BERT/MiniLM)** | `src/semantic_bert.py` | **flat ~0.11–0.13 (2011–22), then rises to ~0.13–0.135 (2023Q4–26)** | **flat ~0.125, rises to ~0.151 (2024–26), survives length control** |
| Content | LDA topic entropy | `src/topics.py` | ~flat (3.72→3.63 bits) | n/a |
| Content | Pre/post-ChatGPT topic JSD | `src/topics.py` | 0.0091 (≈ identical) | n/a |

**Headline finding:** every raw surface/LSA "homogenization" signal disappears once
length is held constant. Answers got longer over time; longer text mechanically lowers
TTR and raises TF-IDF/LSA cosine. Topic mix barely moved (JSD 0.009). The apparent
homogenization is a **length artifact** — not evidence of AI-driven convergence.

**True-embedding update (Sentence-BERT/MiniLM):** the order-sensitive embedding test
*falsifies the LSA rise* — real semantic cosine actually declines 2010–2021 (the opposite
of homogenization), confirming the LSA trend was a bag-of-words/length artifact. It does,
however, reveal a **small, genuine convergence in 2023–2026** that survives length control
(raw ~0.054→0.070; length-controlled ~0.066→0.082). Caveats: it lags ChatGPT by ~1 year
(no sharp 2022Q4 step), stays within the 2010–13 historical range, is *not* corroborated by
effective dimensionality (which rises = more spread), and recent quarters have smaller
samples. Net: strong homogenization is rejected; a modest recent signal is worth tracking,
not overclaiming. **Follow-up (within-topic, `src/topics_bert.py`):** holding topic constant
via dynamic BERTopic clusters, within-topic cosine is flat-to-declining in both corpora — so
most of this 2023–26 rise is a topic-composition effect (post-2023 subject matter), not
within-topic style homogenization. See `critical-review.md` §Q6.

---

## Sensitivity work already done

- **Length-control window sweep** (`src/lc_sensitivity.py`): cosine stays flat at
  windows of 50/100/150/200 tokens — the null result is not an artifact of the window choice.

---

## Metrics to add next (prioritized)

### Tier 1 — Definitive semantic confirmation
1. **Sentence-BERT pairwise cosine + centroid variance. — DONE** (`src/semantic_bert.py`).
   `all-MiniLM-L6-v2` via ONNX Runtime (`fastembed`, no PyTorch — sidesteps the Windows
   MAX_PATH failure that blocked `sentence-transformers`). HuggingFace is proxy-blocked,
   so the model is pulled from the Qdrant Google-Cloud-Storage mirror and loaded via
   `specific_model_path`. Result: LSA rise falsified; small genuine 2023–26 convergence
   that survives length control (see headline update above).
   - **Caveat reported:** embedding similarity is subject to anisotropy/hubness; we report
     **relative change over time**, and note the cosine uptick is not confirmed by
     effective dimensionality.

2. **Within-topic semantic similarity. — DONE** (`src/topics_bert.py`, dynamic BERTopic on
   the MiniLM vectors; artifacts `6_*`). Condition the semantic metrics on topic to separate
   *topic drift* from *style homogenization*. Result: within-topic Sentence-BERT cosine is
   **flat-to-declining** in both corpora (CV ~0.30–0.34; Philosophy ~0.37–0.39, dipping to
   ~0.363 by 2026Q1), while the topic-unconditioned cosine shows the small recent rise — so
   the 2023–26 convergence is **largely a topic-composition effect, not within-topic style
   homogenization**. Caveats: raw (not length-controlled) embeddings; ~52–55% HDBSCAN
   outliers excluded. Remaining: length-controlled within-topic re-run.

### Tier 2 — Length-robust surface hardening
3. **Yule's K / Yule's I** — vocabulary concentration, robust above ~200 tokens.
4. **HD-D** — hypergeometric diversity, the length-robust successor to TTR.
5. **MATTR** — moving-average TTR (windowed), directly comparable across lengths.

   If these three track MTLD (i.e. also flat length-controlled), the "no lexical
   homogenization" claim is airtight from three independent estimators.

### Tier 3 — Information-theoretic / structural (stretch)
6. **GPT-2 perplexity** — detects "AI-like" predictability; falling perplexity
   post-ChatGPT would be positive evidence of AI-style text.
7. **Sentence-length variance** — structural uniformity (AI tends to write
   even-length sentences).
8. **Character/word n-gram entropy** — distributional compression over time.

---

## Second data source (replicated)

- **Philosophy Stack Exchange** — high-cognitive-effort prose, different domain
  (originally 52k answers to 2024Q1; refreshed dump: 66,551 answers, 2011Q2–2026Q1).
  Same pipeline (surface + length-robust + LSA
  semantic + LDA topics) run end-to-end.
  - **Result: the null result replicates.** No homogenization in any metric, and
    — critically — even the *raw* length-sensitive metrics are flat here, because
    Philosophy answers were already long (~270 tokens) from the start, so there was
    no length trend to manufacture a spurious signal. Pre/post-ChatGPT topic JSD =
    0.0086 (≈ identical). This is strong corroboration that the Cross Validated
    "homogenization" tracked its rising answer length, not AI.
  - Artifacts: `artifacts/philosophy/` (Cross Validated outputs live in
    `artifacts/cross-validated/`).
  - **Update (refreshed 2026-03-31 dump, 66,551 answers to 2026Q1):** surface,
    lexical, LSA and topic metrics remain flat, but the *true* Sentence-BERT
    pairwise cosine now shows a **modest recent convergence (2023Q4–2026Q1)**
    that survives length control and is corroborated by falling centroid
    variance — echoing Cross Validated. The earlier Philosophy “flat/no signal”
    was a coverage artifact of the stale 2024Q1 dump. See
    `docs/research/critical-review.md` for the full self-critique.
  - (English Language & Usage is a planned further replication.)

---

## One-line summary for Mark

> Across lexical, length-robust, LSA-semantic and topic metrics, the headline
> homogenization signal is explained by answers getting longer — it vanishes under length
> control, topic content is essentially unchanged (JSD ≈ 0.009), and it does not replicate
> in a second corpus (Philosophy SE). The decisive true-embedding test (Sentence-BERT/MiniLM)
> confirms the LSA rise was an artifact, but surfaces a small, genuine semantic convergence
> in 2023–2026 that survives length control — modest, lagging ChatGPT by ~1 year, within the
> historical range, and not corroborated by effective dimensionality. Bottom line: strong
> AI homogenization is not supported; a small recent signal is worth continued tracking.

