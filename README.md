# AI Homogenization Research Project

## Overview
Research project measuring the **homogenizing effect of AI on online written output**. The goal is to determine whether AI adoption has increased textual homogeneity over time, comparing high-cognitive-load platforms (technical, domain-expert content) vs. low-cognitive-load platforms (casual, everyday writing).

**Client:** Mark Nomellini (Kirkland & Ellis, US law firm)  
**Commitment:** ~10 hrs/week, hourly  
**Timezone:** CST (client works ~6PM-2AM)  
**Start:** July 14, 2026  

---

## Current Phase: Platform & Metrics Research

### Mark's Priorities (from July 14 meeting)
1. **Identify 20 platforms** — 10 high-cognitive-load + 10 low-cognitive-load, assessed for scrapeability
2. **Determine best homogenization metrics** — TTR, cosine similarity, or others?
3. **Test case** — pick one platform, run TTR + cosine similarity on sample data
4. **(Lower priority)** Google search results dashboard — daily homogenization tracking

---

## Methodology

### Data Sources
| Source | Type | Access Method |
|--------|------|---------------|
| Amazon Reviews | Product reviews across categories | Public datasets / API / scraping |
| Stack Exchange | Q&A posts (technical topics) | Stack Exchange Data Dump (free, quarterly) |
| Reddit (stretch) | Community discussions | Pushshift / API |

### Key Metrics
- **Type-Token Ratio (TTR)** — lexical diversity measure (unique words / total words)
- **Cosine similarity** between text embeddings (semantic homogeneity)
- **Pairwise semantic distance** across posts in a category/timeframe
- Additional: vocabulary richness, sentence structure variance, stylistic markers

### Analytical Approach
- **Differences-in-Differences (DiD)** — compare pre/post ChatGPT release (Nov 2022) across treatment/control groups
  - Treatment: categories likely affected by AI (e.g., technical writing, code answers)
  - Control: categories less likely AI-affected (e.g., personal experience reviews)
- **Regression analysis** — model homogenization as function of time, topic complexity, AI adoption proxies
- **Time series** — track diversity metrics over time to identify structural breaks

---

## Project Structure

```
project-ai-homogenization/
├── README.md
├── papers/                    # Reference papers
├── data/                      # Raw and processed datasets
│   ├── raw/
│   ├── processed/
│   └── interim/
├── notebooks/                 # Exploratory analysis
├── src/                       # Production code
│   ├── collection/            # Web scraping & data gathering
│   ├── processing/            # Data cleaning & preparation
│   ├── metrics/               # Homogenization measures
│   └── analysis/              # Regression & statistical models
├── reports/                   # Figures, tables, write-ups
└── requirements.txt
```

---

## Papers Summary

### Paper 1: "Does Generative AI Make Us Think Alike?" (de Rooij & Biskjaer, 2026)
**Direct relevance: ★★★★★**

A systematic review and **meta-analysis of 19 studies (61 effect sizes)** on homogenization in human-AI co-creation.

**Key Findings:**
- **Small but significant homogenization effect** (Cohen's d = 0.334, 95% CI [.094, .574])
- Effect is **task-sensitive**: strongest in semantically constrained ideation tasks (d = 0.70) vs. divergent thinking (d = 0.12)
- Homogenization **persists after AI use ends** (d = 0.414) — not just during co-creation
- Effect **extends to real-world contexts** (quasi-experiments d = 0.303), not just lab settings
- No publication bias detected
- Individual creativity may improve while collective diversity decreases — the "leveling up + narrowing" paradox

**Relevance to Our Work:**
- Validates the core hypothesis that AI increases homogeneity
- Provides methodological precedent (pairwise cosine distances between embeddings)
- Shows homogenization is **task-constraint sensitive** — stronger in semantically constrained tasks (ideation) than open-ended ones (divergent thinking)
- ⚠️ NOTE: "task constraints" ≠ "number of options" — de Rooij's moderator is about semantic framing tightness, NOT about how many choices are available
- Temporal persistence finding supports our pre/post ChatGPT DiD approach

**Metrics they used:** Pairwise cosine distances between transformer-based sentence embeddings, expert ratings of semantic diversity

---

### Paper 2: "Status Quo Bias in Decision Making" (Samuelson & Zeckhauser, 1988)
**Relevance: ★★★☆☆ (theoretical framing)**

Classic behavioral economics paper demonstrating that people disproportionately stick with default/existing options.

**Key Findings:**
- Decision makers exhibit significant status quo bias across many contexts
- Bias increases with number of alternatives (more options → more status quo adherence)
- Bias decreases with strength of preference
- Explained by: loss aversion, sunk cost, cognitive effort minimization, uncertainty avoidance

**Relevance to Our Work:**
- Core hypothesis: **more options → stronger status quo bias** — this is a testable mechanism for AI homogenization
- AI generates many candidate outputs/suggestions → users face high option count → status quo bias increases → they accept AI's default output rather than crafting their own
- This is a DISTINCT mechanism from de Rooij's "task constraints" finding — both may contribute to homogenization but through different pathways
- Could test empirically: do domains with more AI-generated answer options (e.g., Stack Overflow where many AI answers compete) show stronger homogenization?
- Weaker individual preference → stronger bias: less-expert writers more susceptible to defaulting to AI output

---

## Key Connections Between Papers & This Project

### Two Distinct Mechanisms → Same Outcome (Homogenization)

| Mechanism | Source | How It Drives Homogenization |
|-----------|--------|-----------------------------|
| **Task constraints** | de Rooij (2026) | Semantically constrained tasks amplify AI's convergent pull — tighter framing = less room to deviate from AI suggestions |
| **Number of options** | Samuelson & Zeckhauser (1988) | More available options → stronger status quo bias → people default to AI's output rather than exploring alternatives |

⚠️ **These are NOT the same thing.** Task constraints ≈ "how tightly the problem is framed." Number of options ≈ "how many alternatives are available." Both independently predict more homogenization, but through different cognitive pathways.

### Implications for Our Research Design

| Finding | Application |
|---------|-------------|
| de Rooij: Real-world quasi-experiments show effect | Our observational approach (Amazon/SE + DiD) is valid |
| de Rooij: Cosine similarity of embeddings as metric | Use same approach at scale on our data |
| de Rooij: Effect persists after AI use ends | Longitudinal analysis is warranted |
| S&Z: More options → more bias | Test whether domains with MORE available AI answers show stronger homogenization |
| S&Z: Weaker preference → more bias | Less-expert writers (casual reviewers vs. domain experts) may show bigger effect |

### Open Question (for discussion with Mark)
Can we operationalize "number of options" in observational data? Possible proxies:
- Stack Exchange: number of competing answers per question (more answers = more options for future writers to default to)
- Amazon: number of existing reviews on a product (more reviews = more "templates" available as status quo)
- Both: availability of AI tools that generate multiple candidate outputs

---

## Timeline & Milestones

### Phase 1: Data Collection (Weeks 1-3)
- [ ] Set up Stack Exchange data pipeline (data dump is ~100GB, well-structured XML)
- [ ] Build Amazon reviews scraper/dataset accessor
- [ ] Define category taxonomy (technical complexity levels)
- [ ] Establish pre/post ChatGPT time boundaries

### Phase 2: Data Preparation (Weeks 2-4)
- [ ] Clean and structure text data
- [ ] Compute text embeddings (sentence-transformers)
- [ ] Calculate TTR and other diversity metrics per category/timeframe
- [ ] Build analysis-ready panel dataset

### Phase 3: Analysis (Weeks 3-6)
- [ ] Exploratory visualization of metrics over time
- [ ] DiD regression implementation
- [ ] Robustness checks (placebo tests, alternative metrics)
- [ ] Report preparation

---

## Technical Notes

### Stack Exchange Data
- **Best source:** [Stack Exchange Data Dump](https://archive.org/details/stackexchange) — CC-BY-SA licensed, quarterly releases
- XML format with Posts, Users, Comments, Tags tables
- Can identify "complexity" via tags (e.g., `machine-learning` vs. `html`)
- Post creation dates allow clean pre/post segmentation

### Amazon Reviews
- **Amazon Review Dataset** (McAuley et al.) — academic dataset up to 2023
- Alternative: scrape recent reviews with category metadata
- Product categories as natural treatment/control groups

### Key Python Libraries
- `sentence-transformers` — text embeddings for cosine similarity
- `nltk` / `spacy` — TTR and linguistic features
- `statsmodels` / `linearmodels` — DiD regression
- `beautifulsoup4` / `scrapy` — web scraping
- `pandas`, `numpy`, `matplotlib`, `seaborn`
