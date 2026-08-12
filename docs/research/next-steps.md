# Next Steps — after the weak-signal result

*Context: five metric families + dynamic semantic topics are done. Strong "AI
homogenized writing" claim is rejected. The only live signal — a small, recent
Sentence-BERT convergence — largely disappears once we control for topic, so it looks
like a topic-mix effect. These steps are ordered to either kill or confirm that weak
signal decisively, and to attack the problem from the data side (per client's steer:
within-topic style, group by tags/categories, add a natural-prose corpus).*

---

## Priority 1 — Length-controlled within-topic similarity (close the main caveat)
- **What:** Re-run the within-topic similarity test, but on length-controlled embeddings
  (first 100 tokens), not raw full-text.
- **Why:** Our decisive within-topic result used *raw* embeddings. The signal that
  survived length control was the length-controlled one, so strictly we tested the wrong
  variant. This closes the gap.
- **How:** In `topics_bert.py`, embed the 100-token-truncated text (reuse the LC path from
  `semantic_bert.py`), keep the same topic assignments, recompute within-topic cosine.
- **Effort:** Low (one embedding pass + reuse existing code). **Decisive.**

## Priority 2 — Per-tag / per-topic homogenization trends
- **What:** Compute the *full* homogenization pipeline **within each topic/tag** over time,
  not just pooled. Hypothesis: LLMs may homogenize some topics (e.g., how-to/code) far more
  than others (e.g., open-ended philosophy), which pooling would wash out.
- **Two ways to define the group:**
  1. **BERTopic clusters** (already have them) — per-cluster trend lines.
  2. **Real Stack Exchange tags** (richer, human-defined) — **requires new parsing**: our
     answers table has NO tags. Tags live on *questions* (PostTypeId=1). Must extend
     `parse_posts.py` to also capture questions' `Tags` + each answer's `ParentId`, then
     join answer→question to inherit tags. Then group by tag (e.g., "bayesian",
     "ethics") and run per-tag length-controlled BERT similarity over time.
- **Why:** This is the most likely place a *real* localized homogenization would show up,
  and it's directly client-motivated.
- **Effort:** Medium. Parsing change is straightforward (ParentId + Tags already in the XML).

## Priority 3 — Statistical rigor on the signal
- **What:** Bootstrap confidence intervals on the per-quarter BERT metrics + a formal
  change-point / interrupted-time-series test around 2022Q4 and 2023Q4.
- **Why:** We're currently reading curves by eye across 60+ quarters. Need to know if the
  recent uptick is significant or noise, and *when* any break actually occurs.
- **Effort:** Medium.
- **Also:** Reduce HDBSCAN outliers (currently ~52–55% unassigned) — lower `min_cluster_size`
  or use `approximate_predict` to assign outliers — so within-topic uses most of the data.

## Priority 4 — Encoder robustness + known-AI anchor
- **What:** (a) Repeat the BERT analysis with a *second* sentence encoder (different model
  family) to confirm the trend isn't encoder-specific. (b) Embed a sample of *known* ChatGPT
  answers and see where they land relative to the human clusters over time — a calibration
  anchor.
- **Why:** Absolute embedding cosines are inflated by anisotropy/hubness; a second encoder
  and a known-AI reference make "convergence toward an AI style" testable rather than assumed.
- **Effort:** Medium (second encoder must also avoid the Windows/torch issue — prefer another
  fastembed/ONNX model).

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

## Optional / later
- **Per-topic centroid drift:** track whether a topic's *meaning* (centroid vector) moves over
  time, separate from within-topic tightness — detects semantic drift vs convergence.
- **Novelty score (no clustering):** per-answer mean distance to nearest past neighbors — a
  clustering-free check for genuinely new content entering the corpus.
- **Human-vs-AI classifier probe:** train a light probe to distinguish pre- vs post-ChatGPT
  answers within a topic; accuracy above chance = a detectable stylistic shift (even if small).

---

## Recommended sequence for the next session
1. **P1** (length-controlled within-topic) — cheap, could settle the signal immediately.
2. **P3 outlier fix + CIs** — so P1's numbers are trustworthy.
3. **P2 real tags** (parse questions) — the client's per-topic hypothesis, highest-value.
4. Then P4/P5 for external validity if the signal survives P1–P3.
