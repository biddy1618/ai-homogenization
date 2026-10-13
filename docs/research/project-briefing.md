# Project Briefing — AI Homogenization Study

> **Purpose of this document.** A single, self-contained briefing on the whole project, written
> so it can be read cold (e.g. by an assistant seeded with only this file) and used to answer
> questions in conversation. It covers *what we did, why, what we found, the paper, the tracker,
> current status, open questions,* a **glossary**, and an **anticipated Q&A bank**. For the paper
> itself see [paper/main.tex](../../paper/main.tex); for the live tracker see
> [tracker/README.md](../../tracker/README.md). Last updated 2026-10-13.

> **Status 2026-10-13 — results under re-check.** The embedding model (MiniLM) turned out to read only
> the first 128 tokens (~100 words) of each text, so every embedding-based finding below (families
> 5–13) describes how answers *open*, not whole answers. All of it is being re-run on whole text;
> the findings below are the delivered baseline and may change. Wording of the aggregate result is
> also being softened ("the long decline turned upward", not "rose"). See
> [status.md](../status.md) → *Current state* for progress and open framing questions.

---

## 1. TL;DR (30 seconds)

We tested the popular worry that generative AI (ChatGPT, public 2022Q4) made online writing
**homogeneous** — "everything sounds the same now." Using per-quarter text-similarity metrics on
30 dated corpora (26 Stack Exchange communities + Hacker News + PubMed oncology + arXiv CS + arXiv
mathematics) and a
layered battery of statistical controls, the honest finding is:

- The **dramatic surface convergence is a length artifact** — answers got *longer*, not more uniform.
- A **smaller, real rise in deep semantic similarity** survives that control in most corpora.
- But it is **largely a shift in _what_ people write about (topic composition), not _how_ they write
  within a topic.** Within-topic style stays flat once you hold the subject fixed.
- So: **no broad *style* homogenization, but real *topic-level* homogenization** (the mix of topics
  narrows and drifts toward a shared, AI-shaped set of themes). We argue the topic-level effect is
  the more consequential one for epistemic diversity — and worth **monitoring live** (the tracker).

**One-liner for Mark:** *"Writing didn't broadly homogenize in style; the real, measurable
convergence is in the topics people cover — a narrowing of the conversation, not the prose."*

---

## 2. The question and why it matters

**Client:** Mark Nomellini (litigation partner, Kirkland & Ellis). He's interested in whether AI is
measurably homogenizing human output, with an eye to the societal / epistemic stakes.

**Why it matters (three stakes):**
1. **Epistemic diversity** — if the range of answers narrows, so does the pool of ideas people see.
2. **Integrity of the durable record** — science, law, and reference sites are society's searchable
   memory; if they converge toward a model's priors, we lose signal about what humans actually found.
3. **Search & discovery** — if the top results increasingly repeat each other, the web gets wider but
   shallower (this stake directly motivates the tracker).

**The precise question, split three ways** (keeping these apart is the whole contribution):
1. **Aggregate similarity** — are any two texts from the same period more alike than before?
2. **Within-topic style** — holding the subject fixed, do people write it more similarly? (the strict
   "everyone sounds like ChatGPT" claim)
3. **Topic composition** — is the *distribution of subjects* narrowing, so texts look alike simply
   because everyone now writes about the same things?

A rise in (1) can come from (2), (3), or both. Public commentary assumes (2); we find mostly (3).

---

## 3. Data

All corpora are **public, dated to the quarter, and run through 2026Q2** — a long pre-2022 baseline
plus ~14 post-ChatGPT quarters. The ChatGPT marker is **2022Q4**.

- **26 Stack Exchange communities** — 14 high-cognitive-load (Cross Validated, Philosophy, Economics,
  Law, Physics, …) + 12 low-cognitive-load (Seasoned Advice, Travel, Bicycles, RPG, …). Five "core"
  communities carry every control; the other 21 carry the aggregate + significance tests.
- **4 external, non-Stack-Exchange corpora** (added to prove it's not an SE artifact):
  Hacker News comments (~39k), PubMed oncology abstracts (~34k), arXiv CS abstracts (~64k), arXiv
  mathematics abstracts (~69k).

*(Workstream A could broaden this further — SEC EDGAR risk factors, CourtListener legal opinions.)*

---

## 4. Method — a layered battery of controls

The design strips away one benign explanation at a time. Each layer answers "could the apparent
rise just be X?"

| Layer | What it measures | Rules out |
|---|---|---|
| Surface / lexical (families 1–2) | vocabulary diversity (TTR, MTLD, …) | — |
| **Length control** (family 2) | metrics on first-100-token windows | **"answers just got longer"** |
| LSA semantic (family 3) | TF-IDF→SVD cosine | coarse topic drift |
| Contextual embedding (family 5) | Sentence-BERT (MiniLM) pairwise cosine | (this is the live signal) |
| **Topic control** (families 6, 10, 11, 13) | within-topic / same-question / decomposition | **topic-mix vs real style convergence** |
| Significance (family 8) | interrupted time series + Mann-Kendall + bootstrap | eyeballing noise; wrong break date |
| Known-AI anchor (family 12) | distance from humans to an actual ChatGPT answer | "similar to each other" ≠ "similar to AI" |

**Two commitments that matter most:**
- **Length control** — embedding similarity rises mechanically with length; we recompute every
  headline metric on 100-token-truncated text. A signal that survives is not a length artifact.
- **Topic control, done four ways** — BERTopic within-topic (6), Mann-Kendall on the post-period (10),
  the **same-question** gold standard (11, compares only answers to the *identical* question, zero
  clustering), and a within-vs-between decomposition (13). Agreement across four topic definitions is
  what makes the "it's topic composition" conclusion robust.

A recurring caveat: raw embedding cosines are inflated by **anisotropy** (vectors sit in a narrow
cone, so everything looks a bit similar). Where it matters we report the **mean-centred**
(anisotropy-removed) variant, which repeatedly flattens an apparent between-topic "convergence."

---

## 5. Findings

1. **Surface rise = length artifact.** Big lexical convergence after 2022 vanishes under length
   control and never appears in already-verbose corpora (Philosophy).
2. **A real, modest embedding rise** from ~2023Q4 survives length control; significant in **18/26 SE
   corpora** (20/26 length-controlled) and **all 4 externals** (Hacker News cleanest; PubMed & arXiv
   accelerate a pre-existing trend).
3. **It's largely topic composition, not style.** Once the subject is held fixed, within-topic
   similarity is **flat in 4/5 core SE corpora** and — the key new result — **flat in all 4 externals
   under BERTopic**. Meanwhile topic diversity shrinks and the topic mix drifts (family 13), and
   emergent LLM-era topics appear post-2022 (`qa_answers_prompt`, `captioning_mllms`,
   `segmentation_radiomics_dl`).
4. **No drift toward actual AI output** (family 12): flat in 4/5. **No cognitive-load split** (family
   9): high- and low-cog communities track together.
5. **Honest exceptions, reported not hidden:** Philosophy (within-question) and Economics (anchor)
   each show an effect on exactly one test, on *different* sites → read as noise. Hacker News looked
   like a within-topic exception under K-means but **did not survive** a second clustering method
   (BERTopic) — a reminder that within-topic tests are method-sensitive.

**The stance we hold (important for framing).** The within-topic tests are a fragile arbiter (coarse
clusters; BERTopic discards ~⅔ of docs as outliers; "holding topic constant" can absorb real
convergence into the topic boundary). A flat within-topic line does **not** mean "no homogenization";
it *localizes* it. Topic-level homogenization (aggregate rise + shrinking effective topic count +
drifting mix + emergent AI topics) **is** homogenization — arguably the more consequential kind. We
do **not** conclude "no homogenization"; we conclude it's **mostly topical, not stylistic.**

---

## 6. The paper

The paper: [paper/main.tex](../../paper/main.tex) (LaTeX, compiled to `paper/main.pdf`; open framing
decisions are the orange boxes). The earlier markdown draft v0.1 is archived. Structure:
1. **Motivation** — the worry, the stakes, the behavioural-economics prior (status-quo bias), the
   three separable questions.
2. **Data** — 26 SE + 4 externals.
3. **Methodology** — the layered-controls design; what each layer rules out.
4. **Results** — surface=artifact; aggregate rise real; mostly topic composition; no AI-anchor drift;
   no cog-load split.
5. **Real-world consequences** — idea-space narrowing, the record inheriting model priors, shallower
   search, a training-data feedback loop; with an honest "not alarming yet" hedge.
6. **Criticisms / limitations** — significance≠magnitude, timing≠causation, topic-control fragility,
   anisotropy, single encoder, register bias, the lone exceptions.
7. **Conclusion** — not broad style homogenization; a real, structurally important topical convergence
   worth monitoring.

Open framing decisions (orange boxes in the paper): audience/venue; externals as robustness vs
co-equal contribution; how strong a claim to make in the consequences section.

---

## 7. The tracker (forward-looking companion)

A live, open tool that measures **how redundant Google's top results are** for a fixed panel of
queries, tracked over time. Retrospective study = the past; tracker = the future. Full detail in
[tracker/README.md](../../tracker/README.md). In one line: **weekly GitHub Action → Serper.dev
Google top-10 → each result's full page via ScrapingRobot → whole-page embeddings → "% distinct"
(Vendi ÷ pages analysed) → commit results + dashboard.** Snippets are no longer used (they
overstated homogeneity). Latest run (2026-10-12): on average 36.7% of a question's top pages are
effectively distinct; law and science questions are the most repetitive, tech the least. Most
repetitive single questions (~23–25% distinct): two-factor authentication, adult sleep needs,
hurricane formation, probate. The series is only a few weeks old — no trend yet.

---

## 8. Current status (2026-10-13)

- **Research:** 13 metric families on 26 SE corpora + 4 externals. **Whole-text re-run of the
  embedding families in progress** (see the banner at the top and `status.md`).
- **Paper:** LaTeX version (`paper/main.tex`); methodology and numbers will be updated after the re-run.
- **Tracker:** v0.5, full-page only, live on GitHub Actions with a dashboard; Google results via
  Serper.dev from 2026-10-19 (SerpAPI before).
- **Meetings:** last call 2026-09-14 (Mark) opened two workstreams — the paper and the tracker.

---

## 9. Open questions / decisions

- **Paper:** venue/audience; how affirmative to be about consequences; externals' role.
- **Tracker:** whether to freeze or grow the query panel; how to annotate Google ranking-algorithm
  changes; when the series is long enough to read trends.
- **More data (Workstream A):** SEC EDGAR, CourtListener. A true "low-AI control" corpus is an open
  framing question (see `status.md`).
- **Leftovers:** second encoder (guard against model-specific artifacts); the Philosophy
  within-question exception; reduce BERTopic outliers.

---

## 10. Glossary (plain-language)

- **Cosine similarity** — how alike two text embeddings are, 0 (unrelated) to 1 (identical).
- **Embedding / Sentence-BERT / MiniLM** — a model that turns text into a vector so similar meanings
  sit close together. MiniLM is the small, fast one we use (via ONNX, no PyTorch).
- **Aggregate vs within-topic similarity** — aggregate = any two texts in a quarter; within-topic =
  only texts about the same subject. The gap between them tells style apart from topic.
- **Topic composition** — the *mix* of subjects people write about. If it narrows, texts look alike
  without anyone changing their style.
- **BERTopic** — clusters texts into topics using embeddings; used to define "same topic."
- **Same-question control** — the strictest topic control: compare only answers to the *identical*
  question (no clustering, nothing discarded).
- **Vendi score** — the "effective number of distinct items" in a set = exp(entropy of the similarity
  matrix's eigenvalues). 1 = all identical; N = all different. The tracker's headline metric.
- **Marginal novelty** — how much new information each ranked result adds beyond the ones above it;
  low = you stop learning as you scroll.
- **Anisotropy** — embeddings occupy a narrow cone, so *everything* looks somewhat similar; inflates
  raw cosines. Mean-centring removes it.
- **Interrupted time series (ITS) / segmented regression** — fits a trend before and after a marker
  (2022Q4) and tests whether the slope *changes*.
- **Mann-Kendall (MK)** — a non-parametric test for a monotonic trend; we use "MK-post" = is there an
  upward trend *after* ChatGPT?
- **Length control** — recomputing metrics on truncated text so "longer answers" can't fake a rise.
- **Effective topic count** — exp(entropy of cluster sizes); drops when the conversation narrows.

---

## 11. Anticipated Q&A (practice bank)

**Q: In one sentence, what did you find?**
A: The dramatic "everyone writes the same now" effect is mostly a length artifact; a smaller real
convergence exists but is driven by people writing about the *same topics*, not in the *same style*.

**Q: So AI did *not* homogenize writing?**
A: Not in *style* — within a topic, people write about as differently as before. But it *did*
homogenize *topics*: the mix of subjects narrows and drifts toward AI-shaped themes. That's real
homogenization, just at a different level.

**Q: Isn't a "topic effect" less important than a "style effect"?**
A: Arguably the opposite. A narrower set of topics means a narrower range of *ideas* in the public
record — worse for epistemic diversity than everyone using the same em-dash.

**Q: How do you know it's not just that answers got longer?**
A: We recompute every metric on the first 100 tokens. The surface effect disappears; only the deeper
semantic one survives, and even that is mostly topical.

**Q: Could this just be coincidence / correlation, not ChatGPT?**
A: We're careful here — timing isn't causation. Several corpora lack a clean 2022Q4 step and lag by
~a year; PubMed/arXiv were already trending. We report significance *and* these caveats.

**Q: Why should we trust the embeddings? Don't they make everything look similar?**
A: That's anisotropy, and yes — so we also report an anisotropy-removed version, which flattens the
apparent "topics converging" signal, showing part of it was a geometry artifact.

**Q: What is the tracker and does it run by itself?**
A: It's a weekly GitHub Action that measures how repetitive Google's top results are and saves the
numbers into the repo. Yes — it runs on a schedule with no server; if handed to Mark it keeps running
as long as the repo has a Serper.dev key and a ScrapingRobot key. (See tracker/README.md.)

**Q: What's the single most striking early tracker result?**
A: For many plain informational questions only about a quarter of the top pages are effectively
distinct (e.g. "how does two-factor authentication work", "how much sleep do adults need"). It is
early: a few weekly runs, no trend yet.

**Q: What would change your conclusion?**
A: A second encoder disagreeing; the whole-text re-run losing the rise; a tracker trend showing
top results converging over time; or a control corpus with little AI use showing the same change
(we do not have a clean control yet — see the open framing questions in `status.md`).
