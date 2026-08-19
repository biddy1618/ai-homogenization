# Next Steps — after the weak-signal result

*Context: five metric families + dynamic semantic topics are done. Strong "AI
homogenized writing" claim is rejected. The only live signal — a small, recent
Sentence-BERT convergence — largely disappears once we control for topic, so it looks
like a topic-mix effect. These steps are ordered to either kill or confirm that weak
signal decisively, and to attack the problem from the data side (per client's steer:
within-topic style, group by tags/categories, add a natural-prose corpus).*

**Two buckets (added 2026-08-20 after brainstorm):**
- **Bucket A — make the current (null) result defensible.** Cheap, reuses existing code,
  aimed at the next client call: close the length caveat (P1), add statistical confidence
  (P3), and segment the population by answer score (client's idea) and author tenure (P2).
- **Bucket B — test a different, more *causal* question.** Bigger effort, to align on with
  the client: does human text drift toward *actual* AI output (P4 anchor), and does it read
  more machine-generated over time (P6 perplexity/burstiness)?

---

## Priority 1 — Length-controlled within-topic similarity (close the main caveat) — ✅ DONE (2026-08-20)
- **What:** Re-run the within-topic similarity test, but on length-controlled embeddings
  (first 100 tokens), not raw full-text.
- **Why:** Our decisive within-topic result used *raw* embeddings. The signal that
  survived length control was the length-controlled one, so strictly we tested the wrong
  variant. This closes the gap.
- **How:** In `topics_bert.py`, embed the 100-token-truncated text (reuse the LC path from
  `semantic_bert.py`), keep the same topic assignments, recompute within-topic cosine.
- **Effort:** Low (one embedding pass + reuse existing code). **Decisive.**
- **Result:** Both corpora — within-topic cosine stays **flat-to-declining** across the
  ChatGPT marker even after length control (CV ~0.354→0.315; Philosophy ~0.40→0.37).
  The within-topic finding is *not* a text-length artifact. New artifacts:
  `6_within_topic_similarity_lc.csv` + `6c_within_topic_similarity_lc.png` per corpus.

## Priority 2 — Segment the population (who is homogenizing?) — Bucket A/B
- **What:** Instead of pooling all answers, split them by a covariate and compare
  homogenization trends between groups. A real AI effect may be concentrated in one group
  and washed out in the pooled view.
- **Axes to split on (same machinery, different grouping key):**
  1. **Answer score / votes — cheap, client-requested (Bucket A).** `score` is already in
     `answers.parquet`. Bucket answers (e.g. low vs high vote, or accepted vs not) and run
     length-controlled BERT similarity over time per bucket. Hypothesis: low-score / low-effort
     answers homogenize post-2022 while high-score expert answers resist — the Samuelson &
     Zeckhauser "weaker preference → more status-quo bias" mechanism from the README.
  2. **Author tenure / experience — cheap proxy (Bucket A).** Tag each answer with how
     experienced its author was *at posting time*, using a proxy we can compute from data we
     already have: the count of that `OwnerUserId`'s prior answers (1st–5th = newcomer,
     50th+ = veteran). No `Users.xml` needed for the proxy (richer version: account age /
     reputation from `Users.xml`). Hypothesis: newcomers lean on AI and converge; veterans
     stay flat. Nothing is dropped — all answers kept, just labelled and compared.
  3. **Topic / tag — medium (needs parsing).** BERTopic clusters we already have (per-cluster
     trend lines), or *real* SE tags which **require new parsing**: answers carry no tags;
     tags live on questions (PostTypeId=1). Extend `parse_posts.py` to capture questions'
     `Tags` + each answer's `ParentId`, then join answer→question to inherit tags.
- **Why:** The most likely place a *real* localized homogenization would show up; score and
  tenure are directly client-motivated and nearly free.
- **Effort:** Score/tenure = low (data on hand); tag = medium (parsing).
- **P2a (score) — ✅ DONE (2026-08-20).** New `src/segment_score.py` (family 7). Splits each
  quarter at its **within-quarter median score** (rank-based, so the split is balanced and free
  of the age confound — older answers accrue more votes) into low/high groups, then runs the
  bias-corrected bootstrap BERT pairwise-cosine (raw + length-controlled) per group per quarter.
  Reuses the embedding cache (runs in ~10 s/corpus, 100% cache hits). New artifacts per corpus:
  `data/7_score_segments.csv`, `plots/7_score_segments.png` (2 panels raw/lc, low=orange vs
  high=blue, shaded 95% CI). **Result: the recent convergence is NOT concentrated in low-score
  answers — it is broad-based across quality tiers.** CV: historically low-score answers were
  *more* homogeneous (boilerplate), but in 2023–2026 the high-score group rises to match/lead,
  both reaching series highs (~0.08). Philosophy: the two groups track each other throughout
  (CIs overlap heavily) and both rise together to series highs in 2023Q3–2026Q1. This argues
  *against* a "low-effort/templated answers" mechanism and is consistent with the family-6
  topic-composition explanation. Does not change the headline (no strong homogenization).
- **P2b (tenure) — blocked on parsing.** `answers.parquet` has **no `OwnerUserId`** (cols:
  id, creation_date, quarter, score, text, token_count). Needs extending `parse_posts.py` to
  capture `OwnerUserId`, then a prior-answer-count proxy. Deferred.

## Priority 3 — Statistical rigor on the signal — ✅ bootstrap DONE (2026-08-20)
- **What:** Bootstrap confidence intervals on the per-quarter BERT metrics + a formal
  change-point / interrupted-time-series test around 2022Q4 and 2023Q4.
- **Why:** We're currently reading curves by eye across 60+ quarters. Need to know if the
  recent uptick is significant or noise, and *when* any break actually occurs.
- **Effort:** Medium.
- **Result (bootstrap, 1000 resamples, 95% CI on the pairwise-cosine metric):** shaded bands
  added to `5_semantic_bert.png` + `*_lo/_hi` columns in `5_semantic_bert.csv`, both corpora.
  Bands are tight (~±0.003). Findings: the recent rise is **statistically real** (recent
  quarters' CIs sit clearly above the 2016–2022 trough, non-overlapping), but its *magnitude*
  differs by corpus — **CV** recent ~0.069–0.073 stays **below** its 2010–11 early-history
  levels (~0.081) → bounded/modest; **Philosophy** recent ~0.13–0.138 **exceeds** early
  history and reaches series highs, corroborated by centroid variance hitting series lows.
  Implemented via the closed-form `(‖Σv‖²−n)/(n(n−1))` identity so bootstrap is ~free compute.
- **Within-topic CI bands (added 2026-08-20):** the decisive within-topic curves (`6b`/`6c`,
  `*_lo/_hi` columns in `6_within_topic_similarity*.csv`) now carry 95% bootstrap bands too —
  red for the overall (unconditioned) line, blue for the topic-controlled line. The
  within-topic band brackets a **flat** line across the ChatGPT marker in both corpora,
  confirming the topic-composition story is not an artifact of eyeballing. Bootstrap uses a
  **bias-corrected (distinct-pairs)** estimator — `(‖Σv‖²−Σcᵢ²)/(n²−Σcᵢ²)` — because the naive
  version inflates the band by ~1/n from duplicate resampled pairs, which is severe for the
  small (~10-answer) within-topic clusters. Same helper now backs the family-5 CIs.
- **Still open:** change-point / ITS test (formal break date); reduce HDBSCAN outliers.
- **Also:** Reduce HDBSCAN outliers (currently ~52–55% unassigned) — lower `min_cluster_size`
  or use `approximate_predict` to assign outliers — so within-topic uses most of the data.

## Priority 4 — Known-AI anchor + encoder robustness — Bucket B
- **What:** (a) **Known-AI anchor** — generate ChatGPT answers to a *sample of the same
  questions*, embed them with the same MiniLM model, and measure whether human answers move
  *toward the AI centroid* over time. This directly tests "are people writing more like the
  bot?", which pairwise similarity alone cannot. (b) **Encoder robustness** — repeat the BERT
  analysis with a *second* sentence encoder (different model family) to confirm the trend
  isn't encoder-specific.
- **Why:** Absolute embedding cosines are inflated by anisotropy/hubness; a known-AI
  reference makes "convergence toward an AI style" a measurable distance rather than an
  assumption, and a second encoder guards against model-specific artifacts.
- **Effort:** Medium. Anchor needs an LLM to generate answers for a sample (API or local);
  second encoder must avoid the Windows/torch issue (prefer another fastembed/ONNX model).

## Priority 5 — A third, more natural-prose corpus on the same topics
- **What:** Add a corpus of natural-language posts covering similar subject matter, to test
  whether the pattern generalizes beyond Stack Exchange's terse, technical style.
- **Candidates:**
  - **Reddit** — r/AskStatistics, r/askphilosophy, r/askscience (natural prose, same topics;
    Pushshift/API access, but note API/licensing constraints).
  - **Other Stack Exchange sites** with more prose — English Language & Usage, Writing,
    Academia — as low-friction drop-ins to the existing pipeline.
- **Why:** Stack Exchange answers are atypically structured; a prose corpus is a stronger test
  of "did everyday writing homogenize." Also gives an independent third replication.
- **Effort:** SE sites = low (pipeline reuse). Reddit = higher (new ingest + licensing).

---

## Priority 6 — AI-likeness content signal (perplexity / burstiness) — Bucket B
- **What:** Measure whether the text itself reads more machine-generated over time, *without*
  generating anything — using a fixed language model (GPT-2) as a ruler.
  - **Perplexity:** how *surprised* the model is by an answer (exp of mean negative
    log-likelihood). Low = predictable/AI-like, high = idiosyncratic/human. Track mean
    perplexity per quarter; a **drop after 2022** = text becoming more model-predictable.
  - **Burstiness:** variance of per-sentence perplexity (or sentence-length variance) *within*
    a text. Humans are bursty (uneven); AI is uniform. **Falling burstiness** = more machine-like.
- **Why:** An *intrinsic*, content-level signal independent of pairwise/embedding similarity —
  different failure mode, complementary evidence. (Basis of detectors like GPTZero.)
- **Effort:** Medium. Needs a small LM; use an **ONNX GPT-2** to avoid the Windows/torch issue.

## New angles (cheap, paper-aligned)
- **Answer-order / anchoring:** within a question, do *later* answers converge toward the
  *first* answer more over time? Directly tests the papers' "number of options → default to
  the existing" mechanism. We have `ParentId` + timestamps. Cheap.
- **Platform impact (not homogenization, but client may value it):** did answer *volume* per
  question drop after ChatGPT (people ask the bot instead)? Cheap — we have counts.
- **Per-quarter sample-size sanity check — dropped:** subsumed by the bootstrap CIs in
  Priority 3 (thin quarters automatically get wide bands); we'll just print `n` per quarter.

---

## Optional / later
- **Per-topic centroid drift:** track whether a topic's *meaning* (centroid vector) moves over
  time, separate from within-topic tightness — detects semantic drift vs convergence.
- **Novelty score (no clustering):** per-answer mean distance to nearest past neighbors — a
  clustering-free check for genuinely new content entering the corpus.
- **Human-vs-AI classifier probe:** train a light probe to distinguish pre- vs post-ChatGPT
  answers within a topic; accuracy above chance = a detectable stylistic shift (even if small).

---

## Recommended sequence
**Bucket A — now, before the next client call (all reuse existing code):**
1. **P1** length-controlled within-topic — cheap, could settle the signal immediately.
2. **P3** bootstrap CIs (+ change-point, outlier fix) — turns "read by eye" into "significant or not".
3. **P2** score buckets + author-tenure buckets — client-requested, nearly free.

**Bucket B — propose to the client, pick a direction together:**
4. **P4** known-AI anchor (drift toward real ChatGPT output) + second encoder.
5. **P6** perplexity / burstiness (intrinsic AI-likeness).
6. **P2 real tags** (parse questions) and **P5** third corpus for external validity.
