# Meeting Log — Mark Nomellini

Running log of client meetings, newest entry first.

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
| 1 | Dauren | Run the semantic pairwise-cosine analysis on **2+ more sites** (beyond CV + Philosophy) | Next |
| 2 | Dauren | Add a **statistical-significance** test for the increase, across all sites | Next |
| 3 | Dauren | **Bucket sources into high vs low cognitive load** and compare the degree of homogenization | Next |
| 4 | Dauren | **Older-GPT generated-text comparison** (generate replies w/ early GPT, check similarity) — my idea, Mark endorsed | Next |
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
