# Did generative AI homogenize online writing?

### A multi-corpus, topic-controlled analysis (2009–2026)

> **Status: DRAFT v0.1 for Mark to mark up.** Prose is deliberately over-explicit so phrasing and
> stance can be edited directly. Framing decisions still open are flagged inline as **[FRAMING]**.
> Every quantitative claim carries a `[fig/CSV]` pointer to the artifact that backs it, so nothing
> here is un-sourced. Numbers are current as of 2026-09-19 (26 Stack Exchange corpora + 3 external
> non-SE corpora, topic control now complete off-SE).

---

## Abstract *(placeholder — write last)*

We test the widely-held intuition that generative AI (ChatGPT, publicly released 2022Q4) has made
online writing more homogeneous. Using per-quarter diversity and similarity metrics on ~29 dated
text corpora (26 Stack Exchange communities spanning high- and low-cognitive-load topics, plus
Hacker News, PubMed oncology abstracts, and arXiv CS abstracts), and a layered battery of controls
(length control, topic control, a known-AI anchor, and interrupted-time-series significance
testing), we find: **the dramatic surface-level convergence is a length artifact; a smaller but
statistically real rise in contextual-embedding similarity survives length control in most corpora;
but this residual rise is largely a shift in _what people write about_ (topic composition), not a
convergence of _how_ they write within a topic.** We therefore find no evidence of broad *stylistic*
homogenization, but clear evidence of *topic-level* homogenization — a narrowing of the topic mix
and the emergence of a shared AI-shaped set of themes. We argue the topic-level effect is the more
consequential one for epistemic diversity, and motivate a live tracker to monitor it going forward.

---

## 1. Motivation

Since late 2022, a common complaint has surfaced: *everything online is starting to sound the same.*
The em-dashes, the "it's not just X — it's Y," the tidy three-part lists. The worry is that as
hundreds of millions of people route their writing through a handful of large language models, the
diversity of human expression — and, more importantly, the diversity of *ideas* — quietly collapses
toward a shared machine mean.

This matters beyond aesthetics. Three stakes in particular:

- **Epistemic diversity.** If the range of answers to a question narrows, so does the pool of ideas
  a reader is exposed to. Homogenization of *content* (not just style) is a narrowing of what gets
  said at all.
- **The integrity of the public record.** Scientific abstracts, legal opinions, and reference sites
  like Stack Overflow are the durable, searchable memory of a field. If that record converges toward
  a model's priors, we lose signal about what humans actually discovered or argued.
- **Search and discovery.** Search engines rank a top-N of results. If those results increasingly
  repeat one another, the marginal information a searcher gains from reading more of them falls —
  the web gets wider but shallower. *(This stake directly motivates the tracker, Workstream C.)*

There is also a prior reason to expect an effect, from behavioural economics. When people face more
options or hold weaker preferences, they default to the status quo and to whatever is placed in
front of them (Samuelson & Zeckhauser's status-quo bias). An always-available, fluent default answer
is exactly the kind of anchor that theory predicts people will converge on.

**The precise question.** "Did AI homogenize writing?" is too coarse to test. We decompose it into
three separable questions, and the paper's contribution is keeping them apart:

1. **Aggregate similarity** — are any two texts from the same period more alike than they used to be?
2. **Within-topic style** — holding the *subject* fixed, do people write it more similarly (the
   "everyone sounds like ChatGPT" claim in its strict form)?
3. **Topic composition** — is the *distribution of subjects* narrowing, so texts look more alike
   simply because everyone now writes about the same things?

A rise in (1) is compatible with (2), (3), or both. Most public commentary implicitly claims (2);
we find the evidence points mainly to (3).

> **[FRAMING]** Mark leans toward the affirmative "AI is driving real, consequential homogenization."
> The data supports that claim at the *topic* level and *rejects* it at the *style* level. The
> introduction can honor the affirmative reading by foregrounding the topic-level finding and the
> epistemic-diversity stakes, without overclaiming a style effect the data doesn't support. The
> tension is a feature: the paper's credibility comes from conceding (2) while establishing (3).

---

## 2. Data

All corpora are **public, dated to the quarter, and run through 2026Q2**, giving ~14 quarters of
post-ChatGPT observation against a long pre-2022 baseline. The ChatGPT marker throughout is **2022Q4**.

### 2.1 Stack Exchange (26 communities)

From the June 2026 Stack Exchange data dump. **14 high-cognitive-load** communities (e.g. Cross
Validated, Philosophy, Economics, Law, Computer Science, Physics) and **12 low-cognitive-load**
communities (e.g. Seasoned Advice, Travel, Bicycles, Gardening, RPG, Board Games). The split lets us
test whether casual writing homogenizes more than expert writing. Five "core" communities (Cross
Validated, Philosophy, Economics, Seasoned Advice, Travel) carry every control; the other 21 carry
the aggregate + significance tests. `[artifacts/sites_manifest.csv]`

### 2.2 External, non-Stack-Exchange corpora (3)

To test whether any finding is an artifact of Stack Exchange's terse, structured Q&A style, we added
three registers from entirely different platforms:

| Corpus | Register | Docs | Span | Unit |
|---|---|---|---|---|
| Hacker News | tech-forum comments | ~39k | 2016Q1–2026Q2 | comments |
| PubMed (oncology) | scientific abstracts | ~34k | 2016Q1–2026Q2 | abstracts |
| arXiv (Computer Science) | scientific abstracts | ~64k | 2016Q1–2026Q2 | abstracts |

All three carry the full pipeline including topic control (added 2026-09). *(Workstream A will
broaden this further — a less-AI-confounded arXiv field such as math or q-bio, SEC EDGAR risk-factor
sections, and CourtListener legal opinions — to diversify the register base.)*

> **[FRAMING]** Decide whether the externals are "robustness checks on an SE result" or a
> "co-equal cross-domain contribution." The latter is a stronger paper if Workstream A lands more
> sources.

---

## 3. Methodology

The design is a **layered battery of controls**, each ruling out one benign explanation for an
apparent rise. Read top-to-bottom, each layer strips away a confound the previous one left standing.

| Layer | Family | What it measures | What it rules out |
|---|---|---|---|
| Surface / lexical | 1–2 | Type-token ratio, MTLD, Yule's K, etc. | Vocabulary-diversity change |
| Length control | 2 | Same metrics on first-100-token windows | **Answers simply got longer** |
| LSA semantic | 3 | TF-IDF→SVD cosine, centroid variance | Coarse topic drift |
| Contextual embedding | 5 | Sentence-BERT (MiniLM) pairwise cosine | — (this is the live signal) |
| Topic control | 6, 10, 11, 13 | Within-topic / same-question / decomposition | **Topic-mix shift vs real style convergence** |
| Significance | 8 | Interrupted time series + Mann-Kendall + bootstrap | Eyeballing noise; wrong break date |
| Known-AI anchor | 12 | Distance from humans to an actual ChatGPT answer | "Similar to each other" ≠ "similar to AI" |

Two methodological commitments deserve emphasis because they are where most naive analyses go wrong:

- **Length control.** Embedding similarity rises mechanically with text length. We recompute every
  headline metric on text truncated to the first 100 tokens. A signal that survives this is not a
  "posts got longer" artifact.
- **Topic control, done four ways.** The crux of the paper. To separate *style* from *subject* we
  (a) cluster with BERTopic and measure *within-topic* similarity over time (family 6); (b) run the
  same test with a Mann-Kendall trend test post-2022 (family 10); (c) use the **same-question**
  gold standard — comparing only answers to the *identical* question, zero clustering, zero dropped
  data (family 11); and (d) decompose the aggregate cosine into within- vs between-topic components
  and track topic diversity directly (family 13, global K-means, no dropped outliers). Agreement
  across four different topic definitions is what makes the topic-composition conclusion robust.

A recurring caveat baked into the method: raw embedding cosines are inflated by **anisotropy**
(embeddings occupy a narrow cone, so everything looks somewhat similar). Where it matters we report
the **mean-centred** ("anisotropy-removed") variant, which repeatedly flattens an apparent
between-topic "convergence."

---

## 4. Results

### 4.1 The dramatic surface rise is a length artifact

Lexical-diversity metrics show a large apparent convergence after 2022 — which **disappears entirely
under length control** and never appears at all in already-verbose corpora like Philosophy. Answers
got *longer*, not more uniform. `[family 1–3; 3 = length-artifact]`

### 4.2 A smaller contextual-embedding rise is real and survives length control

The one signal that does *not* dissolve: Sentence-BERT pairwise similarity rises modestly from
roughly 2023Q4 onward, and the rise survives length control. It is **statistically significant in
18 of 26 Stack Exchange corpora** (20/26 under length control) by interrupted-time-series slope
change, and it replicates in **all three external corpora**: Hacker News (slope-change
+0.00101/qtr, p=4.5e-9 — the cleanest, flat-before/sharp-after), PubMed (+0.00080, p=9e-4), and
arXiv-CS (+0.00105, p=0.0014). `[family 5, 8; artifacts/*/plots/8_its.png]`

Two honesty notes carried from the data: the effect is **broad but modest** (significant partly
because N is huge; magnitudes are small and, for Cross Validated, still below its own 2010–11
early-history levels), and PubMed and arXiv show a **pre-2022 upward trend** — for them the change
is an *acceleration*, not a clean break. `[family 8]`

### 4.3 The residual rise is largely topic composition, not within-topic style

This is the paper's central result. Once the subject is held fixed, the rise mostly evaporates:

- **Stack Exchange:** within-topic (family 6/10) and same-question (family 11) similarity is
  **flat in 4 of 5 core corpora**; the decomposition (family 13) locates the entire rise in
  *between-topic* pairs while within-topic stays flat, and shows **topic diversity shrinking** and
  the **topic mix drifting** after 2022. Philosophy is the lone within-question exception. `[11, 13]`
- **Externals (new, 2026-09):** under BERTopic — the same method as the SE headline — **all three**
  externals show within-topic similarity **flat while the aggregate rises**. Hacker News: overall
  MK-post p=1.2e-4 but within-topic p=0.44 (flat); PubMed: overall p=8e-4, within flat/declining
  (p=0.38); arXiv: overall p=5e-4, within dead flat (p=1.0). A K-means decomposition (family 13)
  initially flagged Hacker News as a within-topic exception (p=0.004), but that **did not survive**
  a second clustering method — a useful reminder that within-topic tests are method-sensitive.
  Every external also shows the tell-tale **emergent LLM-era topics** post-2022Q4
  (`qa_answers_prompt`, `captioning_mllms`, `segmentation_radiomics_dl`, `texttoimage_prompt`).
  `[family 6, 13 on HN/PubMed/arXiv]`

The reading: the rise is real, but it is mostly people **converging on what to write about**, not on
how to write it.

### 4.4 No drift toward actual AI output; cognitive load doesn't explain it

The most literal test — do human answers move *toward an actual ChatGPT answer* to the same question
(family 12)? — is **flat in 4 of 5 corpora** (Economics the lone, noisiest exception). And the rise
is **cognitive-load-independent**: high- and low-cog communities track each other (family 9), so it
isn't a "casual writing homogenizes, expert writing resists" story. The two lone exceptions
(Philosophy in the same-question test, Economics in the anchor test) fall on *different* sites and so
read as noise, not corroboration. `[family 9, 12]`

### 4.5 Summary of evidence

| Claim | Verdict | Backing |
|---|---|---|
| Surface convergence | **Artifact** (length) | families 1–3 |
| Aggregate embedding rise | **Real, modest, broad** | families 5, 8 (18–20/26 + 3/3 externals) |
| Within-topic *style* convergence | **Not supported** | families 6, 10, 11, 13; 4/5 SE + 3/3 externals flat |
| Topic-level homogenization (mix narrows) | **Supported** | family 13 (eff-topics ↓, comp-JSD ↑) + emergent LLM topics |
| Drift toward AI output | **Not supported** | family 12 (4/5 flat) |
| Cognitive-load split | **None** | family 9 |

---

## 5. Real-world consequences *(new section — why this matters in practice)*

The finding is often heard as reassuring ("so writing *didn't* homogenize"). We argue the opposite is
closer to the truth: **the kind of homogenization we _did_ find — topic-level — is the more
consequential one**, and its practical effects are already visible.

- **Narrowing of the idea space, not just the word space.** A flat within-topic style but a
  shrinking, drifting *topic mix* means the concerning change is in *which questions get asked and
  answered at all*. Fewer effective topics is a direct measure of a narrower public conversation —
  arguably worse for collective knowledge than everyone using the same em-dash.
- **The scientific and legal record inherits a model's priors.** Emergent post-2022 topic clusters
  in arXiv (`qa_answers_prompt`, `texttoimage`) and PubMed (`segmentation_radiomics_dl`) show the
  research frontier reorganizing around AI-adjacent themes. Whether that reflects genuine scientific
  progress or a bandwagon is exactly the kind of thing a durable record should let us audit later.
- **Search returns more pages that say less.** If top results increasingly share a topic profile,
  the marginal value of reading result #5 after #1–4 falls. Users do more clicking for less
  information — a measurable degradation of search as a discovery tool (and the basis for the
  proposed tracker).
- **A feedback loop worth naming.** Models are trained on the web; the web is increasingly written
  with model help; topic-level convergence today biases the training data of tomorrow. Even a modest
  topic-narrowing can compound across model generations — a slow ratchet rather than a cliff.
- **Where it is *not* alarming (yet).** We found **no** evidence that individual human voice, within
  a subject, is collapsing, and **no** drift toward literal AI phrasing. The alarmist "everyone
  writes identically now" framing is not supported. The honest message is targeted, not apocalyptic:
  *watch the topic mix, not the prose.*

> **[FRAMING]** This section is where the paper can lean toward impact without overclaiming. Options,
> from most to least cautious: (a) "a subtle but structurally important narrowing worth monitoring";
> (b) "an early-warning sign of epistemic concentration"; (c) "evidence of a self-reinforcing
> homogenization loop." Pick the strongest claim the reader will still find *defensible given §6*.
> Mark to steer tone + which consequence leads.

---

## 6. Criticisms and limitations *(self-critical by design)*

- **Significance ≠ magnitude.** Huge N makes tiny slopes significant; several effects are small in
  absolute terms and, for some corpora, below their own historical highs.
- **Timing ≠ causation.** The clearest bends lag ChatGPT by ~a year and lack a clean 2022Q4 step in
  several corpora; PubMed and arXiv were already trending up pre-2022 (structured-abstract
  standardization is a confound independent of AI).
- **Topic-control fragility.** Within-topic tests depend on how you define a topic: BERTopic discards
  ~50–67% of documents as outliers, and K-means and BERTopic *disagreed* on Hacker News. We treat a
  flat within-topic line as *weak* evidence and lean on the *convergence* of four methods, not any one.
- **Anisotropy.** Raw between-topic "convergence" is largely an embedding-geometry artifact; the
  mean-centred variant flattens it. We report both.
- **Single encoder.** All embedding results use one model family (MiniLM); a second encoder is
  pending. **[open]**
- **Register bias.** Stack Exchange answers are atypically structured; the externals mitigate but
  don't eliminate this.
- **Lone exceptions.** Philosophy (within-question) and Economics (anchor) each show an effect on
  exactly one test; on different sites, so we read them as noise — but they are honestly reported,
  not suppressed.

---

## 7. Conclusion

The popular claim — *generative AI made everyone write the same way* — is **not supported** by a
layered, multi-corpus, topic-controlled analysis. The large surface convergence is a length artifact;
the smaller, real, length-robust embedding rise is **mostly a change in what people write about, not
how**. What we *do* find is **topic-level homogenization**: a measurable narrowing and drift of the
topic mix, and the emergence of a shared, AI-shaped set of themes across forums, science, and
technical writing alike. That is a subtler but arguably more consequential effect for epistemic
diversity than stylistic sameness — and, because it is measurable, it is worth **monitoring in the
open** (motivating the live tracker). The honest headline: *not broad style homogenization, but a
real and structurally important topical convergence — worth watching, not yet worth alarm.*

---

## Appendix A — Claim-to-artifact map

| § | Claim | Artifact(s) |
|---|---|---|
| 4.1 | Surface rise = length artifact | `artifacts/*/plots/1_*`, family 3 outputs |
| 4.2 | Aggregate embedding rise, significant | `artifacts/*/plots/5_semantic_bert.png`, `8_its.png`, `8_significance_all.csv` |
| 4.3 (SE) | Within-topic / same-question flat 4/5 | `11_same_question`, `13_topic_decomposition` |
| 4.3 (ext) | Externals within-topic flat 3/3 | `artifacts/{hackernews,pubmed-oncology,arxiv-cs}/{plots/6b,6c,13_*; data/6_*,13_*}` |
| 4.4 | No AI-anchor drift; no cog-load split | `12_anchor_drift`, `9_cog_load_comparison` |
| 5 | Emergent LLM-era topics | `artifacts/*/data/6_topic_summary.csv`, `6_topics_over_time.csv` |

## Appendix B — Open decisions for Mark

1. **Audience/venue** — CS/comp-social-science workshop vs law-review/policy vs general essay
   (changes tone + which caveats lead). **[FRAMING]**
2. **Externals** — robustness checks vs co-equal contribution (depends on Workstream A). **[FRAMING]**
3. **Consequences framing** — how strong a claim in §5 (options a/b/c above). **[FRAMING]**
4. **Title** — current working title vs a punchier affirmative-but-honest alternative.
