# Homogenization Study — Oral Briefing (for voice-assistant practice)

*Client: Mark Nomellini (Kirkland & Ellis). Question: did generative AI (ChatGPT,
public Nov 2022 / "2022Q4") homogenize online writing?*

---

## How to use this document
Read a section aloud, then have your voice assistant ask you the questions in the
**Q&A bank** and answer from memory. The goal is to *explain*, not recite. If you can
say the "90-second summary" and handle the Q&A bank cleanly, you're ready. Numbers to
memorize are in **Key numbers**. Plain-language definitions are in the **Glossary** —
practice saying those in one breath.

---

## The 20-second pitch
"We tested whether AI made online writing more uniform, using two large Q&A communities
— Cross Validated for statistics and Philosophy Stack Exchange — from 2010 to early 2026.
We measured writing with five families of metrics, from simple vocabulary richness up to
modern sentence embeddings. The big headline 'AI homogenized writing' claim does not hold
up: almost everything is flat once you account for the fact that answers simply got longer.
There's a small, recent convergence signal in the deep-embedding metric, but when we
controlled for *topic*, even that mostly disappears. So: no strong homogenization; at most
a weak, unproven hint."

---

## The 90-second summary
"We built two corpora: Cross Validated, about 219,000 answers, and Philosophy, about 66,500
answers, both quarterly to the first quarter of 2026. For each quarter we measured writing
several ways and looked for a change around ChatGPT's release.

First, surface metrics — vocabulary diversity and word-overlap similarity. The raw numbers
looked like homogenization, but that was an artifact: answers got longer over time, and
length mechanically distorts those metrics. When we hold length constant — truncate every
answer to its first hundred tokens — the trend goes flat. We confirmed that with four
independent diversity estimators and by re-checking at several truncation lengths.

Second, meaning-based metrics. Bag-of-words semantic similarity, called LSA, was also flat
under length control. Topic modeling with LDA showed the mix of topics barely changed —
divergence near zero.

Third, the sophisticated test: true contextual embeddings, Sentence-BERT. Here we found the
only live signal — a small rise in answer-to-answer similarity starting late 2023, which
survived length control and appeared in both corpora. But it lags ChatGPT by about a year,
it's small, and one of our three embedding metrics — effective dimensionality — did not
corroborate it.

So we ran the decisive test: dynamic semantic topic modeling with BERTopic, then measured
similarity *within* each topic. Result: within-topic similarity is flat in both corpora. That
means the small recent uptick was largely a change in *what people write about*, not in *how*
they write. Bottom line: the strong claim is rejected, and the weak signal is probably a
topic-mix effect, not real style homogenization."

---

## Key numbers to memorize
- **Two corpora.** Cross Validated: ~219,000 answers, 63 quarters, 2010Q3–2026Q1. Philosophy:
  ~66,551 answers, 60 quarters, 2011Q2–2026Q1.
- **ChatGPT marker:** 2022Q4 (public release, Nov 2022).
- **Length control:** first **100 tokens** per answer (re-checked at 50/100/150/200 — all flat).
- **Topic-mix change (LDA JSD):** ~**0.008–0.009** on a 0–1 scale — essentially identical
  pre/post. (0 = identical, 1 = completely different topics.)
- **BERT signal (the one live hint):** length-controlled similarity rises from ~late 2023;
  Philosophy length-controlled cosine ~0.125 (2022Q4) → ~0.151 (2024–26); the recent peak
  barely exceeds a pre-ChatGPT high (2011Q3 ≈ 0.145). Small.
- **Effective dimensionality:** ~**85 out of 384**, flat — no dimensional collapse.
- **BERTopic:** CV 84 topics, Philosophy 71 topics. **Within-topic similarity flat** in both.

---

## The five/six methods, in plain words
1. **Surface / lexical metrics** — how rich the vocabulary is (TTR, MTLD, Yule's K/I, HD-D,
   MATTR) and how much answers overlap in words (TF-IDF cosine). "Does the writing look
   simpler or more copy-paste?"
2. **Length-control sensitivity** — the same checks at several truncation lengths, to prove
   our conclusions aren't an artifact of the cutoff we chose.
3. **LSA (bag-of-words meaning)** — project answers into a latent semantic space and see if
   they cluster tighter. "Are they converging in gist?" — but still word-order-blind.
4. **LDA topic modeling** — a statistical model that splits the corpus into topics and tracks
   their proportions over time. "Did the subject mix shift after ChatGPT?"
5. **Sentence-BERT embeddings** — true contextual, order-sensitive vectors; the modern test of
   semantic convergence. "Do answers *mean* more alike, accounting for phrasing?"
6. **BERTopic (dynamic semantic topics)** — cluster the BERT vectors into data-driven topics
   that can *emerge* over time, then measure similarity *within* each topic. "Is any convergence
   real style, or just a change in what people write about?"

---

## Findings, family by family (say these out loud)
- **Surface:** The dramatic-looking homogenization is a **length artifact**. Answers got longer;
  longer text mechanically lowers vocabulary ratios and raises word-overlap similarity. Hold
  length constant → flat, no ChatGPT step. Four independent diversity estimators agree.
- **Length-control sensitivity:** Flat at 50, 100, 150, and 200 tokens, in both corpora. The
  conclusion is not sensitive to our cutoff.
- **LSA:** Raw similarity rises, but that's the same length effect (LSA is built on TF-IDF).
  Length-controlled → flat. No semantic convergence at the bag-of-words level.
- **LDA topics:** Topic mix barely moved (JSD ~0.008). Entropy flat. No major subject shift —
  but this model is coarse (15 fixed topics), so we didn't fully trust the "no drift" result.
- **Sentence-BERT:** The **only** live signal — a small, recent (late-2023 on) rise that survives
  length control and replicates across both corpora. Caveats: ~1-year lag after ChatGPT (no sharp
  2022Q4 step), small magnitude, and effective dimensionality does **not** corroborate it.
- **BERTopic + within-topic:** Emergent topics are **field evolution, not AI** (Cross Validated:
  survival analysis, causal inference, multilevel models — rising since ~2019; Philosophy: Bayesian
  puzzles, consciousness/neuroscience; only a small, flat Turing/robots cluster). And crucially,
  **within-topic similarity is flat** in both corpora. So the BERT uptick was largely a
  **topic-composition effect** — more same-topic pairs — not answers becoming stylistically uniform.

---

## The critical caveats (be honest with the client)
- **Correlation, not causation.** Even the weak signal is only correlational; the ~1-year lag
  means we cannot pin it on ChatGPT specifically.
- **The within-topic test used raw (full-text) embeddings, not the length-controlled variant.**
  So we've shown the *raw* uptick is mostly topic-mix; a length-controlled within-topic run is
  still needed to fully close it.
- **~52–55% of answers were clustering outliers** (excluded from within-topic). A tuning pass to
  capture more documents is warranted.
- **No confidence intervals or change-point test yet** — we're reading curves by eye across 60+
  quarters, which risks over-reading noise.
- **Single encoder.** Absolute embedding cosines are inflated by anisotropy/hubness; we report
  *relative* change, and a second encoder would harden the finding.

---

## Bottom line for the client (the money line)
"The strong claim — that AI flattened online writing — is not supported. The dramatic signal in
simple metrics is a length artifact. The one genuine hint, a small recent convergence in deep
embeddings, largely disappears once we control for what people are writing about. So the honest
summary is: **no homogenization; at most a small, recent uptick that is probably a shift in topic
mix, not a change in writing style — and not causally tied to ChatGPT.**"

---

## Anticipated client questions — Q&A bank (core practice)
**Q: In one sentence, did AI homogenize writing?**
A: No — not in any strong sense; the headline effect is a length artifact, and the only real hint
is small, recent, and probably just a shift in topics.

**Q: Why do you keep saying "length artifact"? Explain it simply.**
A: Answers got longer over the years. Several of our metrics mechanically move as text gets longer
— longer answers look less lexically diverse and share more common words — so the apparent
convergence was really just "more words," not "more similar." When we cut every answer to the same
length, the effect vanishes.

**Q: Then what is the one signal you did find?**
A: Using modern sentence embeddings, answer-to-answer similarity rose a little starting in late
2023, in both communities, and it held up under length control. But it's small, it lags ChatGPT by
about a year, and a shape metric (effective dimensionality) didn't back it up.

**Q: So is that ChatGPT's fingerprint?**
A: We can't say that. It's correlational, the timing is off by a year, and when we controlled for
topic it mostly went away — pointing to a change in subject matter rather than writing style.

**Q: What does "controlling for topic" mean, and why did it matter?**
A: If people suddenly ask more questions on one narrow subject, answers look more similar on average
— not because the writing homogenized, but because they're about the same thing. We clustered
answers into topics and measured similarity only *within* each topic. That within-topic similarity
stayed flat, so the average rise was mostly a topic-mix effect.

**Q: Two different sites — why should I trust that?**
A: They're independent communities with different subject matter and norms. Finding the same
pattern in both — the same length artifact, the same flat within-topic result — makes it much less
likely to be a quirk of one dataset.

**Q: Could your method just be missing it?**
A: Possible, and we're honest about the gaps: single encoder, no confidence intervals yet, and the
within-topic test hasn't been run in the length-controlled version. Those are our next steps. But
five independent metric families pointing the same way is strong.

**Q: What's the strongest evidence *for* some homogenization?**
A: The small, length-robust, recent rise in Sentence-BERT similarity that appears in both corpora
and is echoed by the centroid-variance metric hitting a series low. We take it seriously — we just
don't overclaim it.

**Q: What's the strongest evidence *against*?**
A: Effective dimensionality is flat — the answer space isn't collapsing — and within-topic
similarity is flat. Real "everything sounds the same" homogenization should show up in both, and it
doesn't.

**Q: What would change your mind / what's next?**
A: A length-controlled within-topic test, per-topic trends (AI may homogenize some topics more than
others), confidence intervals and a change-point test, a second encoder, and a third, more
natural-prose data source. If within-topic similarity rose in the length-controlled version with
tight confidence intervals, that would be real.

**Q: Bottom line I can repeat to my team?**
A: "No strong AI homogenization. A small recent uptick that's likely about topic mix, not writing
style, and not provably caused by ChatGPT."

---

## Glossary (say each in plain language)
- **TTR (type-token ratio):** unique words ÷ total words. Simple diversity, but drops as text gets
  longer — unreliable alone.
- **MTLD:** a length-robust vocabulary-diversity score. The honest diversity number.
- **Yule's K/I, HD-D, MATTR:** other length-robust diversity estimators; used to cross-check MTLD.
- **TF-IDF cosine:** how much two answers overlap in weighted word usage; higher = more alike.
- **LSA:** latent semantic analysis — compress word-overlap into a meaning space; still word-order-blind.
- **LDA:** a probabilistic topic model; each document is a mix of topics, each topic a bag of words.
- **JSD (Jensen-Shannon divergence):** distance between two distributions, 0 to 1; we used it to
  compare the topic mix before vs after ChatGPT (~0 = unchanged).
- **Sentence-BERT / MiniLM:** a small BERT model that turns a whole answer into one vector capturing
  meaning and word order. "MiniLM" = the specific model; same vectors throughout.
- **Pairwise cosine:** average similarity between answer vectors in a quarter; higher = more homogeneous.
- **Centroid variance:** average spread of answers around their center; lower = more homogeneous.
- **Effective dimensionality:** the effective number of independent directions the answers vary
  along (out of 384); low = collapsed/homogeneous. Ours is ~85 and flat.
- **BERTopic:** clusters BERT vectors into data-driven topics (via UMAP + HDBSCAN) that can emerge
  over time — the semantic, dynamic upgrade over LDA.
- **Within-topic similarity:** similarity measured only among answers on the *same* topic; it
  separates real style homogenization from a shift in subject matter.

---

## Next steps (one-liners — full detail in next-steps.md)
1. Length-controlled within-topic similarity (close the main caveat).
2. Per-tag / per-topic homogenization trends (AI may homogenize some topics more) — needs question
   tags joined to answers.
3. Reduce clustering outliers; add confidence intervals + a change-point test.
4. Second encoder + a known-AI-text anchor for calibration.
5. A third, more natural-prose data source (e.g., Reddit askscience/askphilosophy) on the same topics.
