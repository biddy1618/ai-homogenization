# Stack Exchange Prototype Candidates

> **Decision (07/22):** Mark selected **Cross Validated** as the starting platform. Prototype work begins here, with Philosophy SE and arXiv as follow-up validation.

Three Stack Exchange sites recommended for the homogenization measurement prototype. All are included in the quarterly SE data dump (XML format, CC BY-SA 4.0, available at archive.org). No crawling required — dumps include Posts, Comments, Users, PostHistory, Tags, Votes.

Latest dump: **March 2026** (91.7 GiB total network; individual sites are separate .7z files ranging from ~50MB to ~500MB for these candidates).

---

## Candidate 1: Cross Validated (stats.stackexchange.com)

**Why this site:**
- **Directly in the AI/ML domain** — questions about statistical methods, machine learning, regression, Bayesian inference. If ChatGPT is homogenizing expert discourse, this community is ground zero.
- Answers require deep statistical expertise (high cognitive load)
- Text-heavy explanations with some formulas — the prose portions are rich for lexical/semantic analysis
- Pre-ChatGPT baseline is robust: active since 2010 with steady growth

**Stats:**
| Metric | Value |
|--------|-------|
| Questions | 220,000 |
| Answers | 220,000 |
| Users | 436,000 |
| Current activity | 3.5 questions/day |
| Site age | 16 years (founded 2010) |
| Estimated dump size | ~400-500 MB compressed |

**Prototype approach:**
- Filter to top tags: `machine-learning`, `regression`, `bayesian`, `neural-networks`, `classification`
- Compare answer text TTR/cosine-similarity quarterly: 2018-2022 (baseline) vs 2023-2026 (post-ChatGPT)
- Hypothesis: Answer lexical diversity drops and pairwise cosine similarity increases after Nov 2022

**Strengths:** Most directly relevant to AI homogenization thesis; large volume; long history  
**Risks:** Some LaTeX/formulas in answers may need stripping; answers can be short

---

## Candidate 2: English Language & Usage (english.stackexchange.com)

**Why this site:**
- **Meta-signal**: A community *about language* whose members' own writing may be getting homogenized. If people writing about English start writing more uniformly, that's strong evidence.
- Purely text-based answers (no code, minimal formulas)
- High cognitive load: linguists, etymologists, serious enthusiasts explaining word origins, usage rules, style
- Answers tend to be longer, more discursive — ideal for TTR and semantic analysis

**Stats:**
| Metric | Value |
|--------|-------|
| Questions | 133,000 |
| Answers | 301,000 |
| Users | 766,000 |
| Current activity | 1.4 questions/day |
| Site age | ~16 years (founded 2010) |
| Estimated dump size | ~300-400 MB compressed |

**Prototype approach:**
- Analyze all answer bodies (already pure text/prose)
- Compute monthly TTR (using MTLD for length robustness) and pairwise cosine similarity
- Track vocabulary richness trends: are answers using fewer unique words over time?
- Hypothesis: Writing about English becomes less linguistically diverse post-ChatGPT

**Strengths:** Cleanest text signal (no code/formulas); high answer count; strong "irony factor" for publication  
**Risks:** Site activity declining (1.4 q/day) — may reflect less new content to analyze post-2023; older answers may dominate

---

## Candidate 3: Philosophy Stack Exchange (philosophy.stackexchange.com)

**Why this site:**
- **Maximally opinion-driven, argumentative text** — philosophy answers reflect individual reasoning styles, which should be highly diverse pre-AI
- Requires genuine philosophical expertise (knowledge of traditions, logical reasoning)
- Currently the highest activity rate of the three (5.6 questions/day) — suggests ongoing engagement including post-ChatGPT
- Purely discursive text: no code, no formulas, no data tables

**Stats:**
| Metric | Value |
|--------|-------|
| Questions | 26,000 |
| Answers | 68,000 |
| Users | 98,000 |
| Current activity | 5.6 questions/day |
| Site age | 15 years (founded 2011) |
| Estimated dump size | ~80-120 MB compressed |

**Prototype approach:**
- Small enough to process entirely on a laptop — fastest path to results
- Compare semantic diversity of answers: pre-ChatGPT philosophical arguments should span many "styles" (analytic, continental, pragmatist, etc.)
- Measure whether post-ChatGPT answers converge toward a single "helpful AI assistant" style
- Hypothesis: Pairwise cosine similarity increases sharply; centroid distance decreases

**Strengths:** Smallest dataset (fastest prototype); highest signal-to-noise for style diversity; currently very active  
**Risks:** Smaller volume means less statistical power; niche topic may limit generalizability

---

## Recommendation

**Start with Cross Validated** (Mark's pick) — directly AI/ML adjacent, large volume, 16-year history. Then validate on Philosophy SE (smaller, max style diversity) and arXiv (long-form academic writing).

## Data Access

All three sites are in the same data dump archive:
- **Download**: https://archive.org/details/stackexchange (March 2026 release)
- **Individual files**: `stats.stackexchange.com.7z`, `english.stackexchange.com.7z`, `philosophy.stackexchange.com.7z`
- **Format**: XML files (Posts.xml, Comments.xml, Users.xml, etc.)
- **License**: CC BY-SA 4.0 (requires attribution to Stack Exchange and original authors)
- **Schema docs**: https://meta.stackexchange.com/questions/2677

## Legal Note (Action Item)

Need to verify: CC BY-SA 4.0 allows research use with attribution. Should confirm that using aggregated/anonymized statistics (not reproducing individual posts) for academic research does not create issues. The data dump is explicitly provided for reuse under CC BY-SA 4.0.
