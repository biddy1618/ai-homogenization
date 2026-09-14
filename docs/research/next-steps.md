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
     - **✅ Effectively addressed via family 11 (2026-08-26).** We added `ParentId` to
       `parse_posts.py` and built the **same-question** control (`same_question.py`): the
       strongest possible "same topic" grouping (identical question), no clustering, **zero
       dropped outliers**. Within-question similarity is **flat/ns in 4/5 corpora** →
       topic-composition. Full `Tags` parsing is now optional (only for per-tag breakdowns).
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
  - **✅ ITS done (2026-08-26)** — `significance.py` (family 8): segmented regression +
    Mann-Kendall + bootstrap around 2022Q4. Also drove families 10/11 (MK-post on the
    within-topic / within-question metric), which is where the topic-composition call comes from.

## Priority 4 — Known-AI anchor + encoder robustness — Bucket B — ▶ NEXT UP (2026-08-26)
**This is the "GPT-generated-answer test" to run next**, before the orthogonal-metrics pass.
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

## Priority 5 — More sites + high/low-cognitive-load comparison — ✅ DONE (2026-08-26)
**Result:** added Economics (high-cog), Seasoned Advice + Travel (low-cog) → **5 corpora**
(family 9, `cog_load_compare.py`). The recent rise is **widespread across cog-load tiers**
(low-cog Travel rises too) — no clean high/low split, and once topic is held constant
(families 10/11) the within-topic rise is ns in 4/5. Below is the original scope for reference.
- **Client's headline ask (2026-08-20):** run the semantic pairwise-cosine analysis on **2+ more
  sites** beyond Cross Validated + Philosophy, then **bucket sources into high vs low cognitive
  load** and compare the *degree* of homogenization between the two buckets.
  - **High cognitive load:** Stack Exchange network (CV + Philosophy done; more SE sites are
    low-friction drop-ins — English Language & Usage, Writing, Academia).
  - **Low cognitive load:** Twitter, Reddit, Yelp, TripAdvisor, Goodreads book reviews, movie
    reviews (see `docs/archived/data-sources-low-cog.md`).
  - **Deliverable framing:** does low-cog casual writing homogenize *more* than high-cog expert
    writing? That contrast is the story Mark wants, on top of the per-site significance test (P3).
- **What (original):** Add a corpus of natural-language posts covering similar subject matter, to
  test whether the pattern generalizes beyond Stack Exchange's terse, technical style.
- **Why:** Stack Exchange answers are atypically structured; a prose corpus is a stronger test
  of "did everyday writing homogenize." Also gives independent replication + the cog-load contrast.
- **Effort:** SE sites = low (pipeline reuse). Reddit / review sites = higher (new ingest + licensing).

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
- **Now folded into the orthogonal-metrics pass** — see
  `docs/research/homogenization-metrics-literature.md` (perplexity/compression/n-gram/Vendi).
  Runs **after** the P4 GPT-answer anchor test.

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
**Done (as of 2026-08-26):** P1 length-controlled within-topic (flat) · P2a score segments
(broad-based) · P3 bootstrap CIs **+ ITS/Mann-Kendall** (family 8) · P5 more sites +
cognitive-load compare (family 9, 5 corpora) · topic controls families 10/11 (**same-question**
gold standard) → aggregate rise is **topic-composition** in 4/5 corpora.

**Done (2026-09-13):** first **external, non-SE** corpora — Hacker News, PubMed (oncology),
arXiv (CS), families 5 + 8. All three replicate the significant aggregate post-ChatGPT rise
(survives length control); HN cleanest, PubMed/arXiv accelerate a pre-trend. Topic control not
yet run off-SE.

**Next, in order (post 2026-09-14 call with Mark):**
1. **Email the external results to Mark** for review (item 1) — done via `deliverables/2026-09-14-mark`.
2. **Topic control on the externals** — run families 6/10/11 (or 13) on HN/PubMed/arXiv so the
   within-topic vs topic-composition question is answered off Stack Exchange *before* the paper
   claims replication. (Keeps the honest hedge; not a Mark item but a prerequisite.)
3. **Add more external data sources** beyond the three (item 2) — see **Workstream A** below.
4. **Paper** (item 3) — motivation → methodology → results → criticisms — see **Workstream B** below.
5. **Homogenization tracker** (items 4–5) — Google-search info-gain tool — see **Workstream C** below.
6. **Orthogonal-metrics pass** (the 4 points: predictability/perplexity, compression, n-gram
   diversity, Vendi) for convergent validity — see `homogenization-metrics-literature.md`.
7. **Leftovers:** probe the Philosophy within-question exception; P2b tenure + real `Tags`
   parsing; reduce HDBSCAN outliers; second encoder.

---

## Workstream A — More external data sources (2026-09-14 — Mark)

**Goal:** broaden the replication beyond the current three (Hacker News, PubMed-oncology,
arXiv-CS) so the paper rests on a diverse, cross-domain base rather than three tech/science
platforms. Same pipeline throughout: harvest → drop-in `answers.parquet` schema (`id`,
`creation_date`, `quarter`, `score`, `text`, `token_count`, `parent_id`) → family 5 + 8, then the
topic control. Vet per-quarter volume + coverage-to-2026Q2 **before** any bulk pull (standing rule).

### Reachability (from the 2026-09-13 probe — recheck before use)
- **Reachable now:** arXiv (API + OAI-PMH), Hacker News (Algolia + Firebase), PubMed eutils,
  archive.org, Kaggle homepage (dataset *download* still needs a token).
- **Blocked:** Reddit JSON (403 — needs a registered OAuth app), Hugging Face (403).

### Tier 1 — trivial (reuse an existing harvester, ~an hour each)
- **More arXiv fields** via the same OAI-PMH `set=`: **math**, **q-bio**, **physics**, **econ**,
  **stat**. Crucial value: these are **less LLM-confounded than CS**, so they test whether the
  arXiv rise is "papers *about* AI" vs a general writing effect. A low-AI field (e.g. math) that
  *still* rises would be strong evidence; one that stays flat would localize the CS signal.
- **More PubMed branches** via the same eutils `term=`: **cardiology**, **neurology**, a
  **general-medicine** slice, or an all-fields sample. Tests whether the oncology pre-trend
  (structured-abstract standardization) generalizes or is field-specific.

### Tier 2 — new ingest, high value (a day or so each)
- **Legal opinions — CourtListener API** (`courtlistener.com/api/rest`). High-cog, dated, runs to
  present, and **directly relevant to Mark** (judicial writing). Good homogenization candidate
  (citation/boilerplate conventions). Check auth + rate limits.
- **SEC filings — EDGAR** (`sec.gov` full-text + submissions API). 10-K **risk-factor** sections
  are famously templated/boilerplate → a strong homogenization signal, dated, free, no auth.
  Corporate-prose counterpoint to academic/forum text.
- **Wikipedia** — talk-page comments or article revision diffs (dumps + API). Collaborative prose,
  huge, dated; a different register again.
- **GitHub** — commit messages or PR/issue text via the API (auth'd). Developer prose, dated;
  a fourth register, though noisy.

### Tier 3 — blocked / awkward (only if specifically wanted)
- **Reddit** — richest low-cog prose but needs an OAuth app (live JSON is 403); alternative is an
  archive.org / academic-torrent Pushshift dump (older vintage, may not reach 2026Q2).
- **Product/review datasets** (Amazon/Yelp/Goodreads) — mostly **stop ~2023**, so they can't reach
  2026Q2 and can't show the post-ChatGPT tail; excluded for now.

**Suggested pick for the next batch:** 1 less-confounded arXiv field (**math** or **q-bio**) +
**SEC EDGAR risk factors** + **CourtListener** — gives a low-AI science control, a corporate-
boilerplate case, and a legal case Mark will care about, all with clean dated coverage to 2026Q2.

---

## Workstream B — The paper (2026-09-14 — Mark)

**Goal:** a self-contained paper: **motivation → methodology → results → criticisms**. Mark will
review the data and send framing ideas; the outline should be ready for him to react to. Most
figures already exist — the paper is mostly assembly + honest narrative, not new computation.

### Working title
*"Did generative AI homogenize online writing? A multi-corpus, topic-controlled analysis
(2009–2026)."*

### Proposed section outline
1. **Motivation / introduction.** The public worry ("everything sounds like ChatGPT"); why it
   matters (epistemic diversity, search, legal/scientific record); the behavioural-economics prior
   from the README (more options → default to the existing; weaker preferences → status-quo bias).
   State the precise question: *aggregate* similarity vs *within-topic* style vs *topic composition*.
2. **Data.** The 26 Stack Exchange communities + the external sources (HN, PubMed, arXiv, and the
   Workstream-A additions). Table of size/timespan/cog-load/register. Public, dated, to 2026Q2.
3. **Methodology.** The metric families as a layered design: surface/lexical (length artifact) →
   LSA → contextual embeddings (Sentence-BERT) → **length control** (first-100-token) → **topic
   controls** (BERTopic within-topic 6, MK-post 10, **same-question** 11, decomposition 13) →
   **significance** (ITS/segmented regression + Mann-Kendall + bootstrap, family 8) → the **GPT
   anchor** test (family 12). Emphasize *what each control rules out.*
4. **Results.** (a) The surface rise is a **length artifact**. (b) A small **contextual-embedding**
   rise is real and significant in most corpora (18/26 SE + all 3 externals), survives length
   control. (c) But it is **largely topic-composition**: within-topic / same-question similarity is
   flat once topic is held constant (SE); topic diversity shrinks + mix drifts (family 13). (d) The
   **anchor test** finds no drift toward actual AI output in 4/5. (e) Cognitive load doesn't split it.
5. **Criticisms / limitations (self-critical).** Anisotropy/hubness inflating cosines;
   significance ≠ magnitude (huge-N tight CIs); timing ≠ causation (~1yr lag, no clean 2022Q4 step
   in several); pre-trends (PubMed/arXiv were already converging); topic control **not yet run on
   the externals**; single encoder; ~50% HDBSCAN outliers in family 6; SE's atypical structured
   style; the Philosophy (within-Q) and Economics (anchor) lone exceptions.
6. **Conclusion.** Honest headline: *no broad style homogenization; a real but modest, largely
   topical convergence — worth monitoring (motivates the tracker), not a settled finding.*

### To decide with Mark
- **Audience/venue:** academic (e.g. a CS/computational-social-science workshop or arXiv preprint)
  vs a **law-review / policy** angle vs a general-audience essay. Changes tone + which caveats lead.
- **Framing tension:** Mark leans to the affirmative "AI may drive real topic-level homogenization";
  the data supports *topic-level*, not *style*. The paper must hold both without overclaiming.
- **Scope:** SE-only + externals as robustness, or externals as a co-equal contribution.

### Immediate next action
Draft the **outline as a doc** (`docs/research/paper-outline.md`) with the section skeleton +
which existing figure/CSV backs each claim, for Mark to mark up. (Create on request.)

---

## Workstream C — Homogenization tracker over Google search (2026-09-14 — Mark)

A live/ongoing, ideally **open-source** tool that measures homogenization on **key websites** over
time so trends are publicly verifiable — the forward-looking companion to the retrospective study.

### Core idea
For a given query, pull the **top N Google results**, and score how much the set **repeats itself**
vs adds new information. Low marginal information gain across results = homogeneous. Track per
domain over time (daily/weekly) to get a homogenization time series with a clear "since when."

### Metric options (evaluate 2–3 for convergent validity, reuse our machinery)
- **Embedding redundancy:** mean pairwise cosine of the N result texts (our family-5 metric).
- **Marginal novelty / information gain:** rank results, measure how much each *new* result adds
  beyond those above it (embedding distance to the running set, or KL/entropy of new n-grams).
- **Vendi Score:** effective number of "distinct" results = exp(Shannon entropy of the similarity
  matrix eigenvalues) — one clean diversity number per query (see the metrics-literature doc).
- **Compression ratio / n-gram overlap:** cheap, model-free baselines.

### Data-fetch options (the hard/legal part — decide first)
- **SerpAPI / Serper.dev / Zenserp** (paid, ToS-clean, reliable) — fastest MVP.
- **Google Programmable Search / Custom Search JSON API** (official, quota-limited, not identical
  to organic top results).
- **Direct scraping** — brittle + against Google ToS; avoid for an open, reputable tool.
- Consider also measuring **Google's AI Overview / synthesized answer** vs the organic results
  (Mark's point that Google increasingly collapses sources into one answer).

### Query design
Curated **randomized, domain-specific query sets** per vertical (e.g. health, finance, legal,
cooking, travel) so the signal is comparable to our cog-load buckets; rotate queries to avoid
personalization/caching bias; log locale + timestamp.

### MVP → v1
1. **MVP:** 1 provider (SerpAPI), ~50 queries across 3 domains, fetch top-10, compute pairwise
   cosine + Vendi, store JSONL, one matplotlib time-series. Prove the signal moves.
2. **v1:** scheduled runs (cron/GitHub Actions), a small DB, a public dashboard + open-source repo
   so anyone can reproduce; add the AI-Overview-vs-organic comparison.

### Open questions to resolve with Mark
Provider + budget; legality/ToS stance for an open tool; which metric(s) to headline; domain +
query list; cadence vs cost; hosting for the public dashboard; how to separate "results are
similar because the *topic* is narrow" from "results are similar because content *homogenized*"
(the same topic-vs-style caveat as the main study — bake the control in from day one).
