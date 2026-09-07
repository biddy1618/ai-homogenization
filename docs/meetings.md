# Meeting Log — Mark Nomellini

Running log of client meetings, newest entry first.

---

## 2026-09-07 (live call with Mark — held)

Screen-shared the 26-corpus expansion with the family-8 significance forest plot and the family-9
cognitive-load comparison. Mark wants the plots + methodology emailed to review.

### What I showed
- **26 Stack Exchange corpora** now (up from 5), each gated for sufficient recent volume and
  aligned time range (all end 2026Q2). Noted SE is trending *less* active over time, so I kept
  only sites with enough posts/quarter. External sources (arXiv, Reddit) not yet in — downloading
  + volume/timeframe vetting takes time.
- **Family 8 forest plot** — per-site post-ChatGPT slope change in semantic pairwise cosine;
  blue = high cognitive load, orange = low; filled marker = statistically significant.
- **Family 9** — high vs low cognitive-load bucket means: both rise slightly, indistinguishable.

### Mark's takeaways
- Most sites show a significant upward slope-change (answers getting more alike after ChatGPT).
- **No** high- vs low-cognitive-load difference — indistinguishable.

### ⚠️ Correction for the follow-up material
On the call I eyeballed "5 sites don't show a significant increase," so Mark concluded **21/26**
significant. The actual count from `artifacts/8_significance_all.csv` is **18/26 significant (raw)**
— i.e. **8 do not**: Seasoned Advice, Gardening, Board Games, Personal Finance & Money, Photography,
Physics, Astronomy, English L&U. Under length control it's **20/26**. Use the correct numbers in the
methodology notes. (Reminders to include: significance ≠ magnitude — effects are small ~0.001–0.003
cosine/qtr; and the topic-composition caveat from families 6/10/11 still stands.)

### Action items

| # | Owner | Item | Status |
|---|-------|------|--------|
| 1 | Dauren | **Email Mark the plots** (to Gmail), as self-explanatory as possible | ✅ Done — sent zipped bundle 2026-09-07 |
| 2 | Dauren | **Send methodology notes** with the plots — use the correct 18/26 count | ✅ Done (2026-09-07) |
| 3 | Dauren | **List which sources are high vs low cognitive load** (for Mark) | ✅ Done — in the notes (2026-09-07) |
| 4 | Dauren | **Try arXiv** as the next data source (high-cog scientific papers) — Mark endorsed | Next (tentatively Fri) |
| 5 | Dauren | Check if companies object to data usage for research | Pending (carried) |
| 6 | Dauren | Review papers for data-sharing / referencing best practices | Pending (carried) |

### Deliverable sent (2026-09-07)
- Emailed Mark's Gmail a **zipped bundle**: 26 family-5 similarity-trend plots + 26 family-8
  per-site slope plots (split high/low cognitive load), the significance forest, and the
  cognitive-load comparison, plus plain-English methodology notes (how-to-read + high/low list).
- Framing softened per Dauren to an affirmative stance: **"ChatGPT may be driving a real,
  topic-level homogenization"** (topical/subject-matter, not a uniform writing style), keeping the
  "timing, not proof" and "significant ≠ big" caveats. Correct **18/26 raw (20/26 length-controlled)**
  count used. Committed + pushed (`be1d7cb`, reframed in `c110328`).


### Steer
- Stack Exchange breadth is essentially exhausted; next is **external corpora**, starting with
  **arXiv** (easiest high-cog after SE — they publish paper dumps). Mark reviews the emailed plots
  + notes, then comes back with questions.

---

## 2026-08-29 (live call with Mark — held)

*Reconstructed from memory (no transcript/recording).* Set the breadth sprint that led to the
26-corpus expansion.

### What we agreed
- **Expand family 5 to ~20 corpora total** — **10 high** + **10 low** cognitive load — to test the
  homogenization signal at breadth. (This drove the 20-site expansion; now **26 total**.)
- **If time: investigate how topic drift occurs** — characterize *how* the topic mix shifts over
  time, not just detect that it does.
- **Explain the family-5 increase.** The topic controls (families 6/10) and the same-question
  control (family 11) did **not** show a within-topic rise — but that alone does **not** prove the
  aggregate rise is *caused* by topic drift; it remains a hypothesis. Dig deeper to positively
  attribute the mechanism.
- **Mark's emphasis (key framing):** AI may homogenize **which topics** people write about
  (across/between topics) **without** homogenizing **style within a topic** — and that is exactly
  our signal: aggregate/among-answer cosine rises while within-question cosine stays flat → a
  topic-composition effect, not within-topic style convergence. This is the reading to carry forward.

### Action items

| # | Owner | Item | Status |
|---|-------|------|--------|
| 1 | Dauren | Run **family 5 on ~20 corpora** (10 high + 10 low cog) | ✅ Done (26 total, 2026-09-07) |
| 2 | Dauren | **Significance + cognitive-load** plots across all sites (families 8/9) | ✅ Done (2026-09-07) |
| 3 | Dauren | If time: **investigate the topic-drift mechanism** (e.g. family 13 within/between decomposition) | Open |
| 4 | Dauren | **Explain the family-5 increase** — positively attribute (topic-composition vs other), not just infer | Open |

### Steer / reading to carry forward
"AI homogenizes topics, not within-topic style" is the working interpretation — supported by
within-question being flat while the aggregate rises. Keep hedging: the topic-drift mechanism is a
**hypothesis** until positively shown (family 13 is the intended tool).

---

## 2026-08-26 (interim work — pre-call)

Work done on our side since the Aug-20 call, ahead of the Aug-26/27 call. No client contact.

### Progress on the action items
- **Item 1 (more sites) — done.** Added Economics, Seasoned Advice, Travel → **5 corpora**.
- **Item 2 (significance) — done.** ITS/segmented regression + Mann-Kendall + bootstrap (family 8).
- **Item 3 (cognitive load) — done.** High vs low compare (family 9): the rise is **widespread**
  (4/5 sites, incl. low-cog Travel) — no clean high/low split.
- **New topic controls.** Overall-vs-within MK-post (family 10) and the gold-standard
  **same-question** control (family 11, `ParentId`, zero dropped outliers): within-topic rise is
  **ns in 4/5 corpora** → the aggregate rise is **topic-composition**, not style homogenization.
  **Philosophy** is the lone exception (within-question up-trend) — flagged to probe, not claim.

### Decision — next sequence
1. **GPT-generated-answer anchor test (item 4) first** — generate AI answers for the same
   questions, measure whether human answers drift toward the AI centroid over time.
2. **Then** an orthogonal-metrics pass (predictability/perplexity, compression, n-gram diversity,
   Vendi) for convergent validity — see `docs/research/homogenization-metrics-literature.md`.

### Reminder to self
Re-hedge with Mark: metrics **indicate**, and the aggregate rise now looks like a topic-mix effect
— don't let "homogenization confirmed" get ahead of the evidence.

---

## 2026-08-20 (live call with Mark — held)

The confirmed Wednesday 9 PM (Mark's time) call happened — Aug 19 Mark's time / Aug 20 mine.
Walked Mark through the interim Bucket A analysis; he zeroed in on the semantic pairwise-cosine
result and set the direction for the next sprint.

### What I showed
- **Surface/lexical** (answer count, avg length, TF-IDF, lexical diversity) — still "opposite of
  expected": no surface homogenization.
- **Semantic pairwise cosine + centroid variance** — upward trend = *indication* of
  homogenization, on **both** Cross Validated and Philosophy SE.
- **Bootstrap 95% CIs** — trend is not statistical noise. Flagged the caveat myself: the y-axis is
  zoomed (0.05–0.10), so the magnitude is small — don't overstate.
- **Length control** (first 100 tokens) — results unchanged.
- **Topic-share over time** — no single topic dominating (only a minor "hazard" bump).
- **Within-topic vs overall cosine** — convergence is **across** topics, not within → a
  topic-composition effect.
- **Score split** — high- and low-score answers homogenize similarly (not a low-effort artifact).

### My framing (kept consistent)
Metrics **indicate** homogenization but do **not prove** it; still checking whether it's an
artifact / some other cause. Mark leaned more affirmative ("this is showing homogenization as we
hypothesized") — worth re-hedging next time so the claim doesn't get ahead of the evidence.

### Action items

| # | Owner | Item | Status |
|---|-------|------|--------|
| 1 | Dauren | Run the semantic pairwise-cosine analysis on **2+ more sites** (beyond CV + Philosophy) | ✅ Done (5 corpora) |
| 2 | Dauren | Add a **statistical-significance** test for the increase, across all sites | ✅ Done (family 8) |
| 3 | Dauren | **Bucket sources into high vs low cognitive load** and compare the degree of homogenization | ✅ Done (family 9) |
| 4 | Dauren | **Older-GPT generated-text comparison** (generate replies w/ early GPT, check similarity) — my idea, Mark endorsed | Next (up now) |
| 5 | Dauren | Pursue other hypotheses at discretion, but prioritize 1–4 | Ongoing |
| 6 | Dauren | Check if companies object to data usage for research | Pending (carried) |
| 7 | Dauren | Review papers for data-sharing / referencing best practices | Pending (carried) |

### Candidate sources (raised on the call)
- **Low cognitive load:** Twitter, Reddit, Yelp, TripAdvisor, Goodreads book reviews, movie reviews.
- **High cognitive load:** Stack Exchange network (CV + Philosophy done; more SE sites available).

### Decisions / steer
- **Primary metric going forward:** semantic pairwise cosine similarity across distinct answer
  pairs (MiniLM embeddings).
- Headline Mark wants: **expand breadth** (more sites) + **add rigor** (significance) + the
  **high- vs low-cognitive-load** comparison.

### Next call
- **Aug 26 (Mark's time) / Aug 27 (mine), ~9 PM Mark's time.**

---

## 2026-08-20 (reschedule + interim work)

Monday call didn't happen (timezone back-and-forth). Rescheduled and **confirmed for
Wednesday 9 PM Mark's time**. Doing extra analysis on our side in the meantime.

- **Next call:** Google Meet, **Wed 9 PM Mark's time** (confirmed).
- **New hypotheses raised to Mark (to investigate before the call):** group answers by
  **score/votes** — do low-scored answers homogenize differently than high-scored ones? — plus
  a couple of related segmentation tests.
- **Plan (from brainstorm, see `docs/research/next-steps.md`):**
  - *Bucket A (defensible, cheap, before the call):* P1 length-controlled within-topic;
    P3 bootstrap CIs; P2 segment by score + author tenure.
  - *Bucket B (bigger, to align on with Mark):* known-AI anchor, perplexity/burstiness,
    per-tag parsing, third corpus.

---

## 2026-08-16 (async update — no live meeting)

Tried to meet Thu; Mark was stuck in transit, so we agreed to a Monday call and I sent an
email update in the meantime.

- **Next call:** Google Meet, **Mon 9 PM Mark's time (7 AM mine)** — offered to push to 6 AM.
- **Sent:** short email + 2 plots (Sentence-BERT semantic similarity over time for **Cross
  Validated** and **Philosophy SE**, ChatGPT launch marked) + repo link.
- **Framing:** "semantic *similarity* trends" (softened from "homogenization"); trends point to
  answers becoming more similar over time; flagged one nuance to discuss on Monday. Asked Mark
  to form his own read from the plots first.
- **Held back for the call:** the within-topic plot (the topic-composition caveat).

### Monday agenda (sent)

- New data source — Philosophy SE — homogenization-trend plots
- Semantic metrics applied to both sources — what they tell us
- Topic drift — is there any within-source topic drift

---

## 2026-08-12 (async — analysis + repo delivery)

- Pushed the full analysis to `github.com/biddy1618/ai-homogenization` (main): dynamic BERTopic
  + within-topic confound test, semantic (LSA + Sentence-BERT) metrics, artifacts reorganized
  per corpus, docs added (status, oral-briefing, next-steps), week-1 docs archived, plot-title
  fixes. Nothing outstanding to send.

---

## 2026-07-22

### Action Items

| # | Owner | Item | Status |
|---|-------|------|--------|
| 1 | Dauren | Send three Stack Exchange prototype candidates to Mark | ✅ Done (07/22) |
| 2 | Mark | Review three candidates and email Dauren feedback | ✅ Done — picked Cross Validated |
| 3 | Dauren | Set up GitHub repository with research files and scripts for Mark | ✅ Done |
| 4 | Dauren | Check if companies will object to data usage for research | Pending |
| 5 | Dauren | Review papers for data sharing and referencing best practices | Pending |
| 6 | Dauren | Build Cross Validated prototype (download dump, parse, analyze) | **Next** |

### Key Decisions

- **Primary platform**: Stack Exchange (available data dumps)
- **Approach**: Start simple (TTR + cosine similarity), sophisticate later
- **Content scope**: Start with articles/posts first, then incorporate comments
- **Temporal framing**: Measure trends over time, with pre-ChatGPT baseline for comparison

### Data Sources

**High expertise**: Stack Overflow, Stack Exchange network, Hacker News, academic journals (PubMed data dumps available)  
**Low expertise**: Amazon reviews, YouTube comments, general review platforms  
**Dropped**: Quora (crawling challenges, no data dumps)

### Metrics (Agreed)

- **First iteration**: Type-token ratio (TTR) + cosine similarity
- **Later**: Centroid distance, divergence, perplexity
- Simple heuristics first → sophisticated embeddings later

### Platform Categorization

- Categorize by posting difficulty and required domain expertise
- High cognitive load = significant domain knowledge required
- Comments vary by platform (Stack Exchange comments are substantive vs YouTube which are low-content)

### Research Context

- Internet homogenization affects Google search utility and academic research quality
- Homogenization trends should be visible in post data if properly measured

---

## 2026-07-14 (kickoff)

### Questions to Ask Mark

1. What's the target publication venue / format? (Academic journal, working paper, report?)
2. Amazon reviews — does he have a preferred dataset already, or do I source from scratch?
3. Stack Exchange — any specific communities prioritized (Stack Overflow vs. others)?
4. "Technical/complex areas" — how does he define complexity? By topic? By required expertise?
5. Pre/post cutoff date — strictly Nov 30, 2022 (ChatGPT release) or flexible?
6. Reddit scope — when would we bring this in? What subreddits?
7. Does he want raw code deliverables, or packaged notebooks/reports?
8. Collaboration tools — GitHub? Shared drive? How to share interim results?
9. How much latitude on the analytics approach? (e.g., can I propose additional measures beyond TTR?)
10. Any IRB or ethical review considerations given this is academic research?

### Initial Technical Approach Proposed

1. **Stack Exchange Data Dump** as primary clean dataset (freely available, well-structured, clear timestamps)
2. **Sentence embeddings** (via sentence-transformers) to compute pairwise/centroid cosine similarity within topic-timeframe buckets
3. **Type-Token Ratio** as complementary lexical diversity metric
4. **Differences-in-Differences**: pre/post ChatGPT × high-complexity/low-complexity topics
5. **Robustness**: alternative cutoff dates, placebo tests with pre-period fake cutoffs, multiple embedding models

### Key Distinction Mark Raised

- **de Rooij's "task constraints"** = how semantically constrained the task is (tight problem framing → more homogenization)
- **Samuelson & Zeckhauser's "number of options"** = more available alternatives → stronger status quo bias
- These are **different mechanisms** — both predict homogenization but through different cognitive pathways
- de Rooij does NOT test "number of options" — this is a gap our research could address

### Open Questions Raised

- Can we operationalize "number of options" in our observational data?
  - SE: # of competing answers per question? # of AI-generated candidate responses?
  - Amazon: # of existing reviews (templates people might default to)?
- Is Mark's thesis that the *status quo bias mechanism* (number of options) explains homogenization BETTER or ADDITIONALLY to task constraints?
- Would this be a novel contribution — testing S&Z's "number of options" hypothesis in the AI-generated content domain?
