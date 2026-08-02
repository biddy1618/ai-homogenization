# Meeting Log — Mark Nomellini

Running log of client meetings, newest entry first.

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
