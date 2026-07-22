# Week 1 Work Plan (July 19-25, 2026)
## Budget: 10 hours

---

## Deliverables (mapped to Mark's email)

### Deliverable I: Platform Assessment (4 hours)
**Mark's ask:** 10 high-cognitive-load sources + 10 low-cognitive-load sources, evaluated for scrapeability.

| Task | Hours |
|------|-------|
| Research & list 10 high-cognitive platforms | 1.5 |
| Research & list 10 low-cognitive platforms | 1.5 |
| Evaluate scrapeability of each (access method, rate limits, ToS, data format) | 1.0 |

**Output:** Table with 20 platforms rated on: cognitive load level, data volume, time coverage, access method, scraping difficulty (1-5), data format, notes.

**Also address Mark's question:** Is "cognitive load" the right framing? Or should it be "semantic complexity," "domain expertise required," "technical depth"?

#### Candidate Platforms (starting point to research)

**High Cognitive Load** (requires domain expertise, complex reasoning):
1. Stack Overflow / Stack Exchange network
2. PubMed / biomedical abstracts
3. arXiv (paper abstracts)
4. Math Stack Exchange
5. Cross Validated (stats SE)
6. LessWrong / AI Alignment Forum
7. Hacker News (comments)
8. GitHub Issues / Discussions
9. Wikipedia Talk Pages
10. Quora (technical topics)

**Low Cognitive Load** (casual, everyday language):
1. X / Twitter
2. Reddit (casual subreddits: r/askreddit, r/showerthoughts)
3. Amazon product reviews
4. Yelp reviews
5. TripAdvisor reviews
6. YouTube comments
7. Goodreads reviews
8. App Store / Google Play reviews
9. IMDb reviews
10. Facebook public posts / groups

#### Evaluation Criteria Per Platform
- [ ] Public API available? Rate limits?
- [ ] Public dataset/dump exists?
- [ ] Scraping feasible? (anti-bot measures, legal/ToS risk)
- [ ] Time coverage (how far back does data go? Pre-2022?)
- [ ] Volume (enough posts per time period for statistical power?)
- [ ] Text length (short tweets vs. long essays — affects metric choice)
- [ ] Can we segment by topic/category?

---

### Deliverable II: Homogenization Metrics Research (3 hours)
**Mark's ask:** Best metrics for measuring homogenization? TTR + Cosine Similarity? Others?

| Task | Hours |
|------|-------|
| Research literature on text homogenization metrics | 1.5 |
| Write up pros/cons/applicability for each metric | 1.0 |
| Recommendation on which metrics for which data types | 0.5 |

**Output:** Write-up comparing metrics with recommendation.

#### Metrics to Research:

| Metric | What it measures | Level |
|--------|-----------------|-------|
| **TTR (Type-Token Ratio)** | Lexical diversity within a text | Surface |
| **MTLD (Measure of Textual Lexical Diversity)** | TTR that's robust to text length | Surface |
| **Cosine Similarity (embeddings)** | Semantic similarity between texts | Deep |
| **Pairwise centroid distance** | How spread out a group's texts are in embedding space | Deep |
| **Jaccard similarity** | Word overlap between texts | Surface |
| **Perplexity / entropy** | How predictable the text is | Statistical |
| **Stylometric variance** | Diversity in sentence length, punctuation, structure | Structural |
| **BERTScore self-similarity** | Neural-based similarity within a corpus | Deep |

#### Key Questions to Answer:
- Does TTR work for short texts (tweets) vs. long texts (articles)?
- Does cosine similarity require same-length texts?
- What embedding model is best for this use case?
- How do you aggregate pairwise similarities into a single "homogeneity score" per time period?
- Are there established benchmarks or thresholds?

---

### Deliverable III: Test Case Prototype (2 hours)
**Mark's ask:** Pick one source, compute TTR + cosine similarity on a sample.

| Task | Hours |
|------|-------|
| Select best test platform (likely Stack Overflow or Amazon reviews) | 0.25 |
| Pull small sample (~1000 posts, pre/post split) | 0.75 |
| Compute TTR + cosine similarity | 0.75 |
| Visualize results (time series or pre/post comparison) | 0.25 |

**Output:** Quick notebook/script showing metrics on real data with a basic chart.

**Best candidate for test:** Stack Overflow (data dump is free, well-structured, clear timestamps, high-cognitive).

---

### Deliverable IV: Google Search Dashboard Concept (1 hour)
**Mark's ask:** (Lower priority) How would you assess homogenization in top Google results? Daily updates? Historical?

| Task | Hours |
|------|-------|
| Write up architecture/approach | 0.5 |
| Research Google scraping feasibility & historical options | 0.5 |

**Output:** Short write-up covering:
- Technical approach (daily scrape → compute metrics → display on dashboard)
- Search result access options (SerpAPI, custom scraper, Google Cache)
- Historical data: Wayback Machine / Common Crawl / cached results
- Dashboard tech (simple static site? Streamlit? Observable?)
- Define what "queries" to track (static set of questions across domains)

---

## Suggested Work Order

```
Day 1 (Sat/Sun): Deliverable I — Platform research (4 hrs)
Day 2 (Mon/Tue): Deliverable II — Metrics research (3 hrs)  
Day 3 (Wed/Thu): Deliverable III — Test prototype (2 hrs)
Day 4 (Fri):     Deliverable IV — Dashboard concept (1 hr)
```

---

## What to Send Mark After This Week

A single document/email with:
1. Platform comparison table (20 sources with ratings)
2. Metrics comparison (pros/cons, recommendation)
3. Test results on one platform (chart + numbers)
4. Dashboard concept (half-page)
5. Recommended next steps + which platforms to align on

Then schedule a call to review and pick the final sources.
