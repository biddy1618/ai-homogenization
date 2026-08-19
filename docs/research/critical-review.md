# Critical review of the homogenization findings

*Self-interrogation of the AI-writing-homogenization analysis. Date: 2026-08-12.*
*Corpora: Cross Validated (stats.SE) and Philosophy SE, both refreshed to the
2026-03-31 Stack Exchange dump (data through 2026Q1).*

The purpose of this document is to attack our own results before anyone else does.
It states what we can defend, what we cannot, and what would change our minds.

---

## 1. What the question is (and is not)

**Client question:** did generative AI (ChatGPT, public 2022Q4) make online writing
more *homogeneous* — i.e. more similar to itself — after 2022?

We operationalize "homogeneous" as **reduced diversity among answers within a
quarter**, measured four independent ways:

| Family | Metric | Intuition |
|---|---|---|
| Lexical | TTR, MTLD, Yule's K/I, HD-D, MATTR | vocabulary richness / repetition |
| Surface-semantic | TF-IDF pairwise cosine | word-overlap similarity |
| Semantic (bag-of-words) | LSA (TF-IDF→SVD) pairwise cosine, centroid variance, effective dim | topic/word-cluster similarity |
| Semantic (contextual) | **Sentence-BERT/MiniLM** pairwise cosine, centroid variance, effective dim | order-sensitive *meaning* similarity |

Every metric is computed **raw** and **length-controlled** (each answer truncated to
its first 100 tokens) to separate "text got more similar" from "text got longer."

---

## 2. Headline results (both corpora, to 2026Q1)

| Signal | Cross Validated | Philosophy SE |
|---|---|---|
| Raw TTR | falls (0.73→0.59) | **flat** (~0.58) |
| Length-controlled TTR / MTLD / Yule / HD-D / MATTR | **flat**, no ChatGPT step | **flat**, no ChatGPT step |
| Raw TF-IDF cosine | rises (0.10→0.15) | **flat** (~0.023) |
| Length-controlled TF-IDF / LSA cosine | **flat** (~0.10) | **flat** (~0.08) |
| LDA topic mix (pre/post JSD) | 0.009 (≈identical) | 0.008 (≈identical) |
| **Sentence-BERT cosine (raw)** | falls then **rises 2023–26** | flat then **rises 2023Q4–26** |
| **Sentence-BERT cosine (length-controlled)** | **rises ~0.066→0.084 (2023–26)** | **rises ~0.125→0.151 (2024–26)** |
| Sentence-BERT effective dimensionality | does **not** fall | does **not** fall |

**Two-sentence summary.** The dramatic "homogenization" in the raw surface metrics is
a **length artifact** — answers got longer, and longer text mechanically looks more
similar; it vanishes under length control and does not appear at all in Philosophy
(whose answers were already long). The *only* signal that survives every control is a
**small, recent (2023Q4→2026Q1) convergence in true contextual-embedding similarity**,
which now appears in **both** corpora, lags ChatGPT by ~1 year, and is **not** matched by
a fall in effective dimensionality.

---

## 3. The one live signal, stated precisely

- **Cross Validated:** length-controlled Sentence-BERT pairwise cosine rises from a
  ~2018 low of ~0.063 to ~0.084 by 2024–26 (raw ~0.051→0.070).
- **Philosophy SE:** length-controlled cosine sits ~0.125 through 2022, then climbs to
  ~0.151 across 2023Q4–2026Q1 (raw ~0.110→~0.132). Centroid variance simultaneously
  falls to its **series minimum** in the same window — an independent corroboration
  within the same embedding.
- **Timing:** in both corpora the rise starts ~2023Q4, roughly one year *after*
  ChatGPT's 2022Q4 release. There is **no sharp step at 2022Q4.**

This is what genuinely "moved." Everything below interrogates whether it is real and
whether it can be attributed to AI.

---

## 4. Critical questions (and honest answers)

**Q1. Is the recent uptick just the length artifact again?**
No. It is present in the **length-controlled** series (first 100 tokens of every
answer), which removes the mechanism that produced the surface-metric illusion. In
Philosophy the raw TF-IDF cosine is *flat* (~0.023) while the contextual cosine rises —
so this is not word-overlap or length. **Verdict: not a length artifact.**

**Q2. Could it be a coverage / small-sample artifact?**
This was exactly the trap in our first Philosophy run: the stale dump ended 2024Q1 with
only ~5 post-ChatGPT quarters, and the signal looked like noise. With the refreshed dump
(through 2026Q1, ~14 post-ChatGPT quarters) the rise is sustained across ~10 quarters,
and recent Philosophy volume is *high* (2,000–2,300 answers/quarter, sampled at 800), so
it is **not** a thin-sample effect. In CV the most recent quarters are smaller, which is
a weaker point — but the two corpora fail in opposite directions, and both still show the
rise. **Verdict: not obviously a sampling artifact; stronger in Philosophy than CV.**

**Q3. Is the magnitude actually outside historical variation?**
Only modestly. Philosophy's recent length-controlled peak (~0.151) is above but *close
to* the early-history high (2011Q3 ≈ 0.145). The difference from noise is the
**persistence**: early highs were isolated single quarters, whereas 2023Q4–2026Q1 is a
sustained elevated band. In CV the recent values sit within the 2010–2013 range too.
**Verdict: real but small; we are talking about a few percentage points of cosine, not a
regime change.**

**Q4. Effective dimensionality does not fall — doesn't that contradict "convergence"?**
Yes, partially, and we must disclose it. If answers were truly collapsing onto a few
templates, the effective dimensionality of the embedding cloud should shrink. It does
not (it is flat-to-rising in both corpora). So the picture is "answers are slightly
closer on average" **without** "answers span fewer directions." That is more consistent
with a mild global shift (everyone drifting toward a common register) than with
mode-collapse onto a handful of templates. **Verdict: the metrics disagree; the
convergence is average-pairwise only, not dimensional collapse. Do not claim
template-collapse.**

**Q5. Is pairwise cosine even trustworthy here (anisotropy / hubness)?**
Contextual embeddings are anisotropic — cosine similarities are compressed into a narrow
positive cone, and absolute values are not comparable across corpora (CV ~0.05–0.07 vs
Philosophy ~0.11–0.13 reflects the model/geometry, not "Philosophy is more homogeneous").
We therefore only interpret **within-corpus change over time**, which anisotropy affects
far less. Still, we have not whitened the embeddings or removed hub effects. **Verdict:
trust the *direction* of within-corpus change; distrust absolute levels and
cross-corpus comparisons.**

**Q6. The obvious confound — did the *topics* shift toward AI after 2023?**
This is the most serious alternative explanation. After 2023 both sites saw an influx of
LLM/AI questions (prompting, embeddings, "is the model conscious," etc.). A cluster of
new same-topic answers would raise average pairwise cosine **without any change in
writing style** — convergence of *subject matter*, not of *voice*. Our aggregate 15-topic
LDA JSD is tiny (0.008–0.009), which argues against a large mix shift, but LDA at 15
topics is coarse and would miss an intra-topic AI sub-theme. **We have now run the
decisive test: dynamic within-topic pairwise similarity** (BERTopic on the MiniLM vectors
— UMAP→HDBSCAN clusters, `src/topics_bert.py`, artifacts `6_*`). Holding topic constant,
**within-topic Sentence-BERT cosine is flat-to-declining in both corpora** (CV ~0.30–0.34,
recent values back in the 2010–13 range; Philosophy plateau ~0.37–0.39 since 2014, dipping
to ~0.363 by 2026Q1) — the small recent rise in the *overall* (topic-unconditioned) cosine
does **not** reappear once topic is fixed. The emergent post-2023 topics are ordinary
subject-matter (survival/causal-inference/multilevel models on CV; Bayesian puzzles,
consciousness, indeterminism on Philosophy), **not** an LLM/assistant cluster.
**Verdict: the modest recent convergence is largely a topic-composition effect, not
within-topic style homogenization.** Caveats: HDBSCAN left ~52–55% of answers as outliers
(excluded). The length-control loose end is now **closed** (2026-08-20): re-running the
within-topic test on length-controlled embeddings (first 100 tokens, `6c_*` /
`6_within_topic_similarity_lc.csv`) gives the **same flat-to-declining** within-topic cosine
in both corpora (CV ~0.354→0.315; Philosophy ~0.40→0.37) — the result is not a text-length
artifact.

**Q7. Even if the convergence is real, can we attribute it to ChatGPT?**
Not causally. We have (a) a correlation in time, (b) a plausible ~1-year adoption lag,
and (c) two corpora agreeing. We do **not** have a control platform known to be
AI-free, an instrument for AI exposure, or content-level detection of AI-generated
answers. The ~1-year lag is double-edged: it fits gradual adoption, but it also means
there is **no clean discontinuity** at the intervention, which weakens causal claims and
admits other 2023-onward explanations (moderation changes, traffic decline post-LLM,
community composition shifts). **Verdict: correlational only; "consistent with, not
proof of, AI influence."**

**Q8. Are we p-hacking across many metrics?**
We ran ~10 metric variants × 2 corpora. Most are null; one family (contextual cosine)
is positive. We did **not** pre-register or correct for multiple comparisons, and we
have no per-quarter confidence intervals or a formal change-point test. The
cross-corpus replication is the main guard against a fluke, but the statistics are
descriptive, not inferential. **Verdict: needs bootstrap CIs and a change-point test
before any strong claim.**

**Q9. Could it be the measurement instrument drifting, not the data?**
The embedding model (MiniLM) is fixed and offline, so the *model* is stable. But answer
length distributions, quoting/markdown, code blocks, and cleaning all vary over time and
can nudge embeddings. We control length; we have **not** stress-tested against
code-fraction or quote-fraction changes. **Verdict: low but non-zero risk; worth a
robustness pass.**

---

## 5. What would change our mind (decisive next tests)

1. **Within-topic similarity — DONE (Q6), one variant left.** Dynamic BERTopic within-topic
   cosine is flat-to-declining in both corpora, so the recent rise is mostly topic drift,
   not style homogenization. Remaining: repeat on **length-controlled** embeddings (this run
   used raw) and reduce the ~55% HDBSCAN outliers, to fully close it.
2. **Bootstrap confidence intervals + change-point detection** (Q8): per-quarter CIs and
   a formal break test to see whether 2023Q4 is a real change point.
3. **A near-AI-free control window or platform** (Q7): e.g. a corpus/community with low
   AI adoption, or pre-2020 placebo "interventions," to check specificity.
4. **Held-out embedding model** (Q9): repeat with a second encoder (e.g. e5-small) to
   confirm the trend is not MiniLM-specific.
5. **Third corpus** (English Language & Usage) for a third independent replication.

---

## 6. Bottom line for Mark

- The headline "AI homogenized writing" claim, as usually stated, is **not supported**:
  the big surface-level convergence is an artifact of answers getting longer, and it
  disappears under length control and in a corpus that was already verbose.
- There **is** a small, genuine, length-robust **recent convergence in the *meaning* of
  answers (2023Q4–2026Q1)** that now replicates across two independent communities and is
  corroborated by a second within-embedding metric.
- We **cannot** attribute it to ChatGPT, and the case is now weaker: the timing lags the
  release by ~1 year (no clean step), effective dimensionality does not corroborate
  template-collapse, and — the decisive test — **once topic is held constant the recent
  convergence largely disappears**, so most of the signal is a topic-composition effect
  (what people write about), not homogenization of writing style.
- Honest one-liner: *"Writing did not broadly homogenize. The only surviving signal — a
  small recent rise in semantic similarity — is mostly explained by a shift in topics after
  2023, not by answers being written in a more uniform style; a modest effect worth
  monitoring, not evidence of AI-driven style homogenization."*
