# Data Sources Research: AI Homogenization Study

## High-Cognitive-Load Platforms — Structured Assessment

---

## 1. Stack Overflow (stackoverflow.com)

| Field | Details |
|-------|---------|
| **Data Access** | ✅ **Public API** (Stack Exchange API v2.3) + **Full Data Dump** on Internet Archive |
| **Rate Limits** | 10,000 requests/day with API key; 30 req/sec IP hard cap; `backoff` field may require waiting; no more than 1 semantically identical request/min |
| **Time Coverage** | Data dump goes back to **2008** (site launch). Full history available. Excellent pre-2022 coverage. |
| **Volume** | ~23M questions, ~35M answers on SO alone |
| **Text Length** | Medium-long (questions: 100-500 words; answers: 50-2000+ words) |
| **Topic Segmentation** | Yes — tags system (80,000+ tags). Filter by tag via API. |
| **Scraping Difficulty** | **1** (data dump is a direct download; API is very permissive) |
| **ToS / Legal** | CC BY-SA 4.0 license. Requires attribution. Data dump explicitly provided for reuse. API has [Terms of Use](https://stackexchange.com/legal/api-terms-of-use). |

**Best approach:** Download the **data dump** from https://archive.org/details/stackexchange (92.3 GB total, all sites). It's XML files with Posts, Users, Comments, Votes, Tags, PostHistory. Filter by `CreationDate` for temporal analysis.

---

## 2. Stack Exchange Network (math, physics, stats, etc.)

| Field | Details |
|-------|---------|
| **Data Access** | Same as Stack Overflow — **API v2.3** (pass `site=math`, `site=physics`, etc.) + **Data Dump** (each site is a separate archive) |
| **Rate Limits** | Same as SO: 10,000/day with key, shared across all SE sites per IP |
| **Time Coverage** | Varies by site: Math (2010), Physics (2010), Stats (2010), etc. All have pre-2022 data. |
| **Volume** | Math SE: ~1.5M questions; Physics: ~200K; Cross Validated: ~180K |
| **Text Length** | Medium-long. Math/Physics tend toward longer, more detailed answers with LaTeX. |
| **Topic Segmentation** | Yes — each site is already a topic. Tags within each site provide sub-segmentation. |
| **Scraping Difficulty** | **1** (data dump — just download the specific site's .7z archive) |
| **ToS / Legal** | CC BY-SA 4.0. Same attribution requirements as SO. |

**Best approach:** Same data dump. Each site (e.g., `math.stackexchange.com.7z`, `stats.stackexchange.com.7z`) is a separate file.

---

## 3. PubMed Abstracts (pubmed.ncbi.nlm.nih.gov)

| Field | Details |
|-------|---------|
| **Data Access** | ✅ **E-utilities API** (ESearch, EFetch) + **FTP bulk download** (annual baseline + daily updates in XML) + **Kaggle** |
| **Rate Limits** | 3 req/sec without API key; **10 req/sec with API key** (free NCBI account). Weekday large jobs should be off-peak (9PM-5AM ET). |
| **Time Coverage** | Back to **1966** (MEDLINE) and some records from the 1800s. Excellent historical depth. |
| **Volume** | **36+ million** citation records |
| **Text Length** | Short-medium (abstracts: 150-350 words typically) |
| **Topic Segmentation** | Yes — **MeSH terms** (Medical Subject Headings) provide hierarchical categorization. Filter by journal, publication type, date, etc. |
| **Scraping Difficulty** | **1** (official FTP bulk data at ftp.ncbi.nlm.nih.gov/pubmed/baseline/) |
| **ToS / Legal** | Abstracts may be copyrighted by publishers. NLM provides data freely but notes: "persons reproducing, redistributing, or making commercial use... are expected to adhere to copyright holder terms." Fair use for research likely applies. Non-commercial research is standard use. |

**Best approach:** FTP baseline download (XML, released annually). Use E-utilities API for targeted queries. Get an API key from NCBI account settings.

---

## 4. arXiv Paper Abstracts (arxiv.org)

| Field | Details |
|-------|---------|
| **Data Access** | ✅ **arXiv API** (Atom/XML, query-based) + **Bulk access via AWS S3** (full text PDFs/TeX) + **Kaggle dataset** (metadata JSON) + **OAI-PMH** for metadata harvesting |
| **Rate Limits** | API: no official published rate limit but requests should be "reasonable" (a few per second). Bulk data via S3 has no rate limit (pay for bandwidth). Must follow [API Terms of Use](https://info.arxiv.org/help/api/tou.html). |
| **Time Coverage** | Back to **1991** (arXiv's founding). Complete historical archive. |
| **Volume** | **2.4+ million** papers |
| **Text Length** | Short-medium for abstracts (100-300 words). Full papers available via S3. |
| **Topic Segmentation** | Yes — **category taxonomy** (physics, math, cs, q-bio, etc. with sub-categories like cs.AI, math.AG). |
| **Scraping Difficulty** | **1** (Kaggle dataset for metadata is instant; API is straightforward; S3 for full text) |
| **ToS / Legal** | Open access. Licenses vary per paper (CC BY, CC BY-SA, CC BY-NC-SA, arXiv license). Metadata is freely reusable. Must acknowledge arXiv. Not all full texts are CC-licensed — check individual paper licenses. |

**Best approach:** Use the **Kaggle arXiv dataset** (Cornell University) for all metadata/abstracts — it's a single JSON file. For targeted queries, use the arXiv API (`export.arxiv.org/api/query`).

---

## 5. Math Stack Exchange (math.stackexchange.com)

| Field | Details |
|-------|---------|
| **Data Access** | Same as #2 — API v2.3 (`site=math`) + data dump |
| **Rate Limits** | Same as SE network |
| **Time Coverage** | **2010–present**. Good pre-2022 coverage. |
| **Volume** | ~1.5M questions, ~2M+ answers |
| **Text Length** | Medium-long. Heavy LaTeX/MathJax usage. Answers often 200-1000+ words. |
| **Topic Segmentation** | Tags: algebra, calculus, real-analysis, linear-algebra, probability, etc. (~1500 tags) |
| **Scraping Difficulty** | **1** |
| **ToS / Legal** | CC BY-SA 4.0 |

**Note:** Already covered in data dump from #2. Separate 7z archive.

---

## 6. Cross Validated / Stats SE (stats.stackexchange.com)

| Field | Details |
|-------|---------|
| **Data Access** | Same as #2 — API v2.3 (`site=stats`) + data dump |
| **Rate Limits** | Same as SE network |
| **Time Coverage** | **2010–present** |
| **Volume** | ~180K questions, ~200K+ answers |
| **Text Length** | Long. Detailed statistical explanations. Avg answer likely 300-1500 words. |
| **Topic Segmentation** | Tags: machine-learning, regression, probability, bayesian, neural-networks, etc. |
| **Scraping Difficulty** | **1** |
| **ToS / Legal** | CC BY-SA 4.0 |

**Particularly valuable:** This community has many ML/statistics experts. Content pre/post ChatGPT would show if AI-written statistical explanations differ from human expert ones.

---

## 7. LessWrong (lesswrong.com)

| Field | Details |
|-------|---------|
| **Data Access** | ✅ **GraphQL API** (undocumented but functional at `lesswrong.com/graphql`). GraphiQL explorer available. Also accessible via **GreaterWrong** mirror. No official data dump. |
| **Rate Limits** | No published rate limits. The GraphQL API is public but undocumented — moderate request rates recommended (1-2/sec). |
| **Time Coverage** | **2006–present** (original Overcoming Bias era content + LW 1.0 from 2009 + LW 2.0 from 2017). Excellent pre-2022 data. |
| **Volume** | ~15,000-20,000 posts + hundreds of thousands of comments |
| **Text Length** | **Long** (blog posts: 1000-10,000+ words; comments: 50-2000 words). One of the longest-form platforms in this study. |
| **Topic Segmentation** | Tags/wiki system: AI safety, rationality, epistemology, decision theory, forecasting, etc. |
| **Scraping Difficulty** | **2** (GraphQL API works but is undocumented; need to reverse-engineer schema) |
| **ToS / Legal** | Posts are author-owned. No explicit blanket license for scraping. However, content is publicly accessible and commonly used in NLP research. Check individual post licenses. |

**Best approach:** Use the GraphQL API. Key queries: `posts(input: {...})` and `comments(input: {...})`. Can filter by date, karma, tags. Schema explorable at `lesswrong.com/graphiql`.

---

## 8. Hacker News Comments (news.ycombinator.com)

| Field | Details |
|-------|---------|
| **Data Access** | ✅ **Official Firebase API** (real-time, item-by-item) + **BigQuery dataset** (Google Cloud, full history) + various third-party dumps |
| **Rate Limits** | Firebase API: **No rate limit** (officially stated). However, it's item-by-item access (one HTTP call per item), so bulk fetching is slow by design. BigQuery has no such limitation. |
| **Time Coverage** | Back to **2006** (HN launch, item #1). Complete history. |
| **Volume** | **40+ million items** (stories + comments). Max item ID currently ~42M. |
| **Text Length** | Short-medium (comments: 20-500 words typically; many are concise technical opinions) |
| **Topic Segmentation** | Limited — only "story", "comment", "job", "poll" types. No tags. Stories can be filtered by "Ask HN", "Show HN". Topic inference must be done from title/content. |
| **Scraping Difficulty** | **1** (official API with no rate limits; BigQuery for bulk analysis) |
| **ToS / Legal** | API is officially provided. Data is public. HN's guidelines don't restrict data use for research. BigQuery dataset is maintained by Google. |

**Best approach:** Use **Google BigQuery** (`bigquery-public-data.hacker_news`). Full dataset, SQL-queryable, free tier available. Firebase API is too slow for bulk collection (one item at a time, would take weeks for full corpus).

---

## 9. GitHub Issues / Discussions

| Field | Details |
|-------|---------|
| **Data Access** | ✅ **REST API** + **GraphQL API**. Also: **GH Archive** (BigQuery, all public events) and **GHTorrent** (historical dump). |
| **Rate Limits** | REST: 5,000 req/hr authenticated (PAT), 60/hr unauthenticated. Secondary limits: 100 concurrent, 900 points/min. GraphQL: 5,000 points/hr. |
| **Time Coverage** | GitHub launched **2008**. GH Archive has events from 2011+. Issues/discussions from any public repo are accessible. |
| **Volume** | Billions of events. Hundreds of millions of issues/comments across all public repos. |
| **Text Length** | Variable — issue bodies: 50-2000 words; comments: 20-500 words. Technical discussions can be very long. |
| **Topic Segmentation** | By repository (language, topic tags), by label on issues, by repo topics. GH Archive allows filtering by event type, repo, date. |
| **Scraping Difficulty** | **2** (API is well-documented but rate limits make large-scale collection slow; GH Archive/BigQuery is the better path for bulk) |
| **ToS / Legal** | GitHub ToS: API usage for research is generally permitted. Content licenses vary by repo. Public data is... public. GH Archive is explicitly for research. Avoid violating any repo's specific license regarding derived works. |

**Best approach:** Use **GH Archive on BigQuery** (`githubarchive.day.*` tables) for bulk event data. For targeted repositories, use GraphQL API. For NLP research, consider filtering to high-quality repos (e.g., top-starred repos in specific languages).

---

## 10. Quora (Technical Topics)

| Field | Details |
|-------|---------|
| **Data Access** | ❌ **No public API** (deprecated in 2018). No data dump. Must scrape or use limited historical datasets (Quora Question Pairs on Kaggle). |
| **Rate Limits** | Aggressive anti-bot: requires login for most content, uses JavaScript rendering, CAPTCHAs, IP bans. |
| **Time Coverage** | **2009–present**. Content exists pre-2022 but access is difficult. |
| **Volume** | 300M+ questions claimed, but accessibility is severely limited |
| **Text Length** | Medium-long (answers: 200-2000+ words; question descriptions: 20-200 words) |
| **Topic Segmentation** | Yes — topic/space system. Users tag questions with topics. |
| **Scraping Difficulty** | **5** (login wall, heavy JavaScript, anti-bot measures, no API, legally hostile to scraping) |
| **ToS / Legal** | ⚠️ **Explicitly prohibits scraping.** ToS states content may not be copied, reproduced, or scraped. They have sent cease-and-desist letters. High legal risk. |

**Best approach:** **Avoid for this study.** The risk/reward is poor. If Quora data is needed, look for existing academic datasets (Quora Question Pairs, Quora Insincere Questions on Kaggle — but these are limited). Consider replacing with another platform.

---

## Summary Comparison Matrix

| Platform | Access Method | Difficulty | Pre-2022 | Volume | Text Length | Topic Filter | Legal Risk |
|----------|--------------|:----------:|:--------:|--------|:-----------:|:------------:|:----------:|
| Stack Overflow | Data dump + API | 1 | ✅ | 58M+ posts | Med-Long | ✅ Tags | Low |
| SE Network | Data dump + API | 1 | ✅ | Varies | Med-Long | ✅ Tags+Sites | Low |
| PubMed | FTP + E-utilities | 1 | ✅ | 36M+ | Short-Med | ✅ MeSH | Low |
| arXiv | Kaggle + API + S3 | 1 | ✅ | 2.4M+ | Short-Med | ✅ Categories | Low |
| Math SE | Data dump + API | 1 | ✅ | 3.5M+ | Med-Long | ✅ Tags | Low |
| Cross Validated | Data dump + API | 1 | ✅ | 380K+ | Long | ✅ Tags | Low |
| LessWrong | GraphQL API | 2 | ✅ | 20K+ posts | Long | ✅ Tags | Medium |
| Hacker News | BigQuery + API | 1 | ✅ | 40M+ items | Short-Med | ❌ Limited | Low |
| GitHub Issues | GH Archive + API | 2 | ✅ | 100M+ | Variable | ✅ Repo/Label | Low |
| Quora | Scraping only | 5 | ⚠️ | 300M+ claimed | Med-Long | ✅ Topics | **High** |

---

## Recommendations

### Tier 1 — Use Immediately (data dumps available, trivial access)
1. **Stack Exchange data dump** (covers SO, Math, Stats, Physics — platforms 1, 2, 5, 6)
2. **PubMed FTP baseline**
3. **arXiv Kaggle dataset**
4. **Hacker News BigQuery**

### Tier 2 — Requires API Work (but well-documented and legal)
5. **GitHub via GH Archive/BigQuery**
6. **LessWrong via GraphQL**

### Tier 3 — Avoid or Replace
7. **Quora** — Replace with another platform (e.g., Reddit's r/AskScience, r/MachineLearning, or Wikipedia Talk pages)

---

## Suggested Quora Replacement Candidates
- **Reddit (r/AskScience, r/MachineLearning, r/statistics)** — Pushshift archive, good API
- **Wikipedia Talk Pages** — Full dump available
- **Semantic Scholar** — API available, 200M+ papers
- **PhilPapers** — Philosophy academia, some API access
