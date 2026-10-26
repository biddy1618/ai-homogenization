# Meeting Log — Mark Nomellini

Running log of client meetings, newest entry first.

---

## 2026-10-25 (live call with Mark — held, ~18 min)

Recording: tl;dv transcript "AI Project – update". Mark had not yet read paper v0.2.

### What I showed / said
- **Paper v0.2** (sent 2026-10-19): after the whole-text fix, the rise in similarity is clearly
  stronger in high-cognitive-load communities. Mark: "extremely interesting". Paper is 13 pages, PDF.
- **Tracker:** the latest drop is not apples-to-apples: the switch from SerpAPI to Serper.dev
  returned more pages per query, and "% distinct" falls with page count. Mark agreed it can't be
  compared with earlier points.

### Decisions
- **More queries approved**, even if it costs ~$1/month later ("that's okay, let's do that").
- **Open-ended work approved:** Mark is fine with me setting the direction — more tracker plots,
  testing other scores, mirroring the paper's similarity measure on the tracker so the two can be
  compared, and testing my own hypotheses for the paper ("I like that idea").

### Action items

| # | Owner | Item | Status |
|---|-------|------|--------|
| 1 | Dauren | Email Mark a summary of the call, incl. the two additions (tracker plots/metrics, paper hypotheses) | Open |
| 2 | Dauren | Calendar invite: same time next week | Open |
| 3 | Dauren | Tracker: comparable weeks (fixed page count), more queries, paper's similarity measure, new plots | Open |
| 4 | Mark | Read paper v0.2 and send feedback | Open (Mark) |

---

## 2026-10-15 (live call with Mark + Emmett — held, 07:00, 50 min)

Mark joined from the car, and his connection dropped around 26:00–29:10. **New participant: Emmett
Nomellini** (Mark's son, sophomore in economics at the University of Michigan). He'll be on the
email chain and review the drafts.
Recording/notes: tl;dv meeting `6ad03383ea34c80013a98639`.

### What I showed / said
- **Told Mark about the 128-token issue.** The embedding model only read the first ~80–90 words of
  each text, so the embedding results need redoing on whole text, and that's in progress. Mark
  accepted it: "go ahead and do that tweaking of the data" before the next meeting. **No
  whole-text numbers were shared.**
- For Emmett, Mark restated the big picture: is human output homogenizing because of AI, and more
  so on **high-cognitive-load** sites, where AI saves more work?
- Screen-shared the Cross Validated similarity trend and the slope-change idea (decline before
  ChatGPT, rise after), and listed the data sources (Stack Exchange, arXiv CS/math, Hacker News,
  Philosophy, …).
- **Demoed the tracker proof of concept:** weekly Monday run, Google top 10 → filter → full pages
  → embeddings → similarity. Mark: "I really like where you're going with that." He likes that it
  all goes through Google, since that's what most people use.

### Corrections to send with the follow-up email
- **"High cognitive load is stronger."** I said this on the call. On whole text it is partly
  supported: 11 of 14 high-load sites vs 4 of 12 low-load sites have a significant slope change
  (delivered results: 11 of 14 vs 7 of 12). But the average changes are close (Δ similarity
  +0.0070 high vs +0.0052 low), and the delivered family-9 conclusion was "no clean split".
  Needs a proper whole-text family-9 read before we claim it.
- **"A text = the question plus its top answer."** Wrong. Each text is a single **answer** (all
  answers, not just the top one), sampled up to 800 per quarter.
- **Tracker numbers:** it has **45 queries** (5 domains × 9) and **3 snapshots**, not "28–30
  queries" or "four weeks". Search now goes through Serper.dev, not SerpAPI.
- **Emmett's question exposed a gap:** every external source (HN, PubMed, arXiv) is high load, so
  **low load is Stack Exchange only.** A non-SE low-load source would strengthen the high- vs
  low-load comparison.

### New ideas discussed
- **Homogenization of *ideas*** (from an academic friend): count the number of distinct ideas in a
  text. The hypothesis is that AI stays tightly on-topic while humans wander across sub-points.
  **Mark's condition: it must be an objective, quantitative measure**, otherwise "it's a Rorschach
  test". Look for papers that quantify the number of ideas or claims in a text.
- **Does Google fight AI content?** Mark wonders what Google does to filter AI-generated pages
  (possible context for the tracker). I speculated about an internal AI-content index, like
  Instagram/Threads labels. Unverified.
- **Dashboard visual:** Mark (half-joking) suggested a row of stormtroopers at the "most
  homogenized" end of the scale.
- Mark asked about week-to-week movement in the tracker. **Too early to say:** 3 points, and the
  apparent drop is likely noise.

### Action items

| # | Owner | Item | Status |
|---|-------|------|--------|
| 1 | Mark | **Start an email chain** with Dauren + Emmett | Open (Mark) |
| 2 | Dauren | **Reply with the paper draft link** (say it's stale: numbers pending the whole-text re-run) **and the tracker link** | Open |
| 3 | Dauren | **Finish the whole-text re-run** before the next meeting | In progress |
| 4 | Dauren | **Research quantitative "number of ideas" measures** (papers, objective metrics) | Open |
| 5 | Emmett | Review the drafts (paper + tracker) and send ideas | Open (Emmett) |
| 6 | Dauren | (Optional) Look into how Google handles AI-generated content in ranking | Open |

**Next meeting:** tentatively the same time next week (Thu 2026-10-22, ~07:00 Almaty).

### Not covered (carry into the email or next call)
From the prep notes:
- the whole-text headline: 15 of 26 Stack Exchange sites (was 18), externals hold, PubMed
  stronger;
- that "topic, not style" is provisional until the topic controls finish;
- the weaker old length control (~128 vs ~100 tokens).

Open questions for Mark: the headline wording ("long decline turned upward"), the control-corpus
question, the timeline for the paper rewrite, and which tracker domains and cadence he wants.

---

## 2026-09-14 (live call with Mark — held, 07:00)

Status update on the three external (non-Stack-Exchange) sources.
Recording/notes: <https://tldv.io/app/meetings/6aa755071fda0f00134fc840>

### What I showed / findings
- **Homogenization signal replicates across all three external platforms** — PubMed cancer
  abstracts, arXiv Computer Science, and Hacker News comments — matching the Stack Exchange
  pattern. Abstract similarity **accelerates significantly after the ChatGPT launch**.
- Analysis is on the **abstract portion only** (not full papers) for PubMed/arXiv; HN uses
  comment text.
- Both **scientific terminology and stylistic patterns** trend the same way.
- Consistent with the 26 SE corpora shown on 2026-09-07.

### New direction — two workstreams opened
1. **Academic paper.** Mark wants a paper drafted covering **motivation → methodology → results
   → criticisms (self-critical analysis)**. Mark will review the data and send ideas for the paper.
2. **Homogenization tracker (new product idea).** A live/ongoing tool that measures homogenization
   on **key websites**, likely **daily or weekly** depending on workload:
   - Measure via **information-gain scores across the top search results** for a query.
   - Use **randomized, domain-specific queries** to sample homogenization over time.
   - **Google top search results** proposed as the primary measurement source.
   - Ideally **open source** so the trend is publicly verifiable.
   - Context for *why Google*: search favours optimized/keyword-rich (often AI-generated)
     content, crowding out original human perspectives, and Google increasingly synthesizes
     sources into one standard answer — all plausibly diversity-reducing.

### Action items

| # | Owner | Item | Status |
|---|-------|------|--------|
| 1 | Dauren | **Email the homogenization results** (3 externals) to Mark for review | Open |
| 2 | Dauren | **Add more external data sources** beyond the current three (HN/PubMed/arXiv) | Open |
| 3 | Dauren | **Develop a paper outline** — motivation, methodology, results, criticisms | Open |
| 4 | Dauren | **Brainstorm the homogenization-tracker implementation** for key websites | Open |
| 5 | Dauren | **Propose solutions for computing homogenization metrics across Google search results** | Open |
| 6 | Mark | **Review the data + send Dauren ideas** for paper development | Open (Mark) |

### Side discussion (context, not action)
AI safety/goals (models lack goals unless given; guardrails limit dangerous behaviour; an
internet-connected agent *could* attempt attacks if tasked), benchmark chatter (Chinese models
reportedly leading recent benchmarks), and the AI-investment-bubble risk. No deliverable.

### Note to self
The three externals ran **families 5 + 8 only** (aggregate similarity + ITS significance). **No
topic control** (families 6/10/11/13) has been run off Stack Exchange yet — so when emailing
results (item 1), keep the same honest hedge: this is the *aggregate* rise; the within-topic /
topic-composition question is still untested on the externals.

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
