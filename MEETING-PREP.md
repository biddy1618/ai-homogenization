# Meeting Prep: Mark Nomellini — July 14, 2026

## Questions to Ask Mark
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

## Key Talking Points

### What I Bring
- Strong Python data engineering + analysis pipeline experience
- NLP/embedding-based text analysis (directly relevant to homogeneity measurement)
- Experience with causal inference methods (DiD)
- Can own the full stack: scraping → processing → analysis → reporting

### Initial Technical Approach I'd Propose
1. **Stack Exchange Data Dump** as primary clean dataset (freely available, well-structured, clear timestamps)
2. **Sentence embeddings** (via sentence-transformers) to compute pairwise/centroid cosine similarity within topic-timeframe buckets
3. **Type-Token Ratio** as complementary lexical diversity metric
4. **Differences-in-Differences**: pre/post ChatGPT × high-complexity/low-complexity topics
5. **Robustness**: alternative cutoff dates, placebo tests with pre-period fake cutoffs, multiple embedding models

### What the Literature Supports (from papers)
- de Rooij & Biskjaer (2026): Meta-analysis confirms d=0.334 homogenization effect, stronger in constrained/technical tasks
- This directly supports Mark's hypothesis about technical areas being more affected
- Their methodology (embedding cosine distances) is exactly what we'd replicate at scale on observational data
- Quasi-experimental studies already show effects in real-world writing (not just lab) — validates our approach

## Key Distinction Mark Raised
- **de Rooij's "task constraints"** = how semantically constrained the task is (tight problem framing → more homogenization)
- **Samuelson & Zeckhauser's "number of options"** = more available alternatives → stronger status quo bias
- These are **different mechanisms** — both predict homogenization but through different cognitive pathways
- de Rooij does NOT test "number of options" — this is a gap our research could address

## Questions This Raises
- Can we operationalize "number of options" in our observational data?
  - SE: # of competing answers per question? # of AI-generated candidate responses?
  - Amazon: # of existing reviews (templates people might default to)?
- Is Mark's thesis that the *status quo bias mechanism* (number of options) explains homogenization BETTER or ADDITIONALLY to task constraints?
- Would this be a novel contribution — testing S&Z's "number of options" hypothesis in the AI-generated content domain?
