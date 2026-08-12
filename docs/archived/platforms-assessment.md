# Platform Assessment: AI Homogenization Study
## Deliverable I — 20 Data Sources Evaluated

---

## Framing Question: Is "Cognitive Load" the Right Metric?

Before the table — Mark asked: is "cognitive load" the right way to categorize platforms?

**Options considered:**
| Term | Definition | Pros | Cons |
|------|-----------|------|------|
| Cognitive load | Mental effort required to process/produce content | Intuitive, well-known concept | Vague — a tweet can be cognitively demanding if the topic is hard |
| Semantic complexity | Richness/depth of meaning in the text | Aligns with de Rooij's "task constraints" | Academic jargon |
| Domain expertise required | How much specialized knowledge you need to write | Operationalizable — could proxy with vocabulary/jargon density | Some "expert" writing is simple |
| Technical depth | How specialized/technical the subject matter is | Easy to label platforms | Excludes non-STEM complexity (legal, philosophy) |

**Recommendation:** Use **"domain expertise required"** as the primary dimension. It's:
- Operationalizable (measurable via vocabulary complexity, jargon density)
- Aligns with the hypothesis (experts may resist AI defaults more → less homogenization)
- Connects to S&Z's "strength of preference" (experts have stronger preferences → less status quo bias)

Could refine later to: "expertise threshold" — the minimum domain knowledge needed to contribute meaningfully.

---

## HIGH DOMAIN-EXPERTISE PLATFORMS (Top 10)

| # | Platform | Access | Difficulty | Pre-2022 | Volume | Text Length | Legal Risk | Verdict |
|---|----------|--------|:----------:|:--------:|--------|:-----------:|:----------:|---------|
| 1 | Stack Overflow | Data dump (free) | 1 | ✅ | 58M posts | Med-Long | Low | ✅ USE |
| 2 | Stack Exchange (Math, Stats, Physics) | Data dump (free) | 1 | ✅ | 5M+ posts | Med-Long | Low | ✅ USE |
| 3 | PubMed Abstracts | FTP bulk download (free) | 1 | ✅ | 36M records | Short-Med | Low | ✅ USE |
| 4 | arXiv Abstracts | Kaggle dataset (free) | 1 | ✅ | 2.4M papers | Short-Med | Low | ✅ USE |
| 5 | Cross Validated (Stats SE) | Data dump (free) | 1 | ✅ | 380K posts | Long | Low | ✅ USE |
| 6 | Hacker News | BigQuery (free tier) | 1 | ✅ | 40M items | Short-Med | Low | ✅ USE |
| 7 | GitHub Issues | GH Archive / BigQuery | 2 | ✅ | 100M+ | Variable | Low | ✅ USE |
| 8 | LessWrong | GraphQL API (undocumented) | 2 | ✅ | 20K posts | Long | Medium | ⚠️ MAYBE |
| 9 | Wikipedia Talk Pages | Wikimedia dumps (free) | 1 | ✅ | Millions | Med-Long | Low | ✅ USE |
| 10 | Quora | Scraping only | 5 | ⚠️ | 300M claimed | Med-Long | **High** | ❌ AVOID |

### Notes:
- **Stack Exchange data dump covers #1, #2, #5** in a single 92GB download (CC BY-SA 4.0)
- **Quora** has no API, aggressive anti-bot, and explicitly prohibits scraping. Replace with **Wikipedia Talk Pages** (free dumps, CC license, expert discussions)
- **PubMed + arXiv** are gold for "high-expertise" — peer-reviewed science with clear timestamps
- **Hacker News + GitHub** — tech industry practitioners; different from academic expertise

---

## LOW DOMAIN-EXPERTISE PLATFORMS (Top 10)

| # | Platform | Access | Difficulty | Pre-2022 | Volume | Text Length | Legal Risk | Verdict |
|---|----------|--------|:----------:|:--------:|--------|:-----------:|:----------:|---------|
| 1 | Reddit (casual subs) | Pushshift dumps + API | 2 | ✅ | Billions | Med | Low | ✅ USE |
| 2 | YouTube Comments | YouTube API v3 (free) | 2 | ✅ | Billions | Short | Low | ✅ USE |
| 3 | Amazon Reviews | McAuley dataset (free) | 1 | ✅ | 233M reviews | Med | Low | ✅ USE |
| 4 | Yelp Reviews | Yelp Open Dataset (free) | 1 | ✅ | 7M reviews | Med-Long | Low | ✅ USE |
| 5 | IMDb Reviews | Stanford dataset + scrape | 3 | ✅ | 50K (dataset) | Long | Medium | ⚠️ MAYBE |
| 6 | App Store / Google Play | Python scraping libraries | 3 | ✅ | Millions | Short | Medium | ⚠️ MAYBE |
| 7 | Goodreads | UCSD Book Graph dataset | 1 | ✅ | 15M reviews | Long | Low | ✅ USE |
| 8 | X / Twitter | Paid API ($0.005/tweet) | 4 | ✅ | 500M+/day | Short | Low | 💰 COSTLY |
| 9 | TripAdvisor | Scraping only | 4 | ✅ | 1B+ reviews | Med-Long | High | ❌ AVOID |
| 10 | Trustpilot | Scraping only | 4 | ✅ | 300M reviews | Med | High | ❌ AVOID |

### Notes:
- **Reddit + YouTube + Amazon + Yelp** are the easy wins — free, massive, well-structured
- **Twitter/X** costs ~$500 for 100K tweets, $5K for 1M. Good data but budget-dependent.
- **TripAdvisor & Trustpilot** — Cloudflare-protected, explicitly anti-scraping, no datasets. Skip them.
- **Goodreads** (UCSD dataset) is great for long-form casual writing — book reviews are one of the least likely to be AI-generated pre-2023

---

## Recommended Pairings (High vs. Low Expertise)

For the DiD design, you want matched pairs where the **same type of content** exists on both a high-expertise and low-expertise platform:

| Domain | High Expertise | Low Expertise | Comparison |
|--------|---------------|---------------|------------|
| Tech/Programming | Stack Overflow answers | Reddit r/learnprogramming | Expert vs. beginner explanations |
| Science | PubMed abstracts | Reddit r/explainlikeimfive | Peer-reviewed vs. casual explanations |
| Product opinions | Hacker News (tech products) | Amazon reviews | Expert tech opinions vs. casual reviews |
| Writing/narrative | arXiv abstracts | Goodreads reviews | Formal academic vs. casual book reviews |
| Q&A format | Cross Validated (stats) | Yahoo Answers / Reddit r/nostupidquestions | Expert Q&A vs. casual Q&A |

---

## Top Recommendation for Test Case (Deliverable III)

**Stack Overflow** — because:
1. Free, instant download (single .7z file from data dump)
2. Perfect timestamps for pre/post ChatGPT split
3. Tags give natural topic segmentation (python, javascript, machine-learning, etc.)
4. Known to be heavily affected by AI (SO even banned AI-generated answers in Dec 2022)
5. High-expertise content → maximum expected effect per de Rooij
6. Well-structured XML → fast to parse and analyze
