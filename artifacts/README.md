# Results (artifacts)

All results here are **whole-text** results: each text is cleaned, split into sentence chunks of
at most 120 model tokens, and its vector is the average of the chunk vectors. Every embedding
result also has an **opening-window** control: exactly the first 120 model tokens of each
text, with shorter texts left out. In CSVs the opening-window columns start with `lc_`.

The delivered results (truncated at 128 tokens, as sent to Mark before 2026-10-15) are no longer
in the tree. Restore them with `git checkout delivered-v1 -- artifacts`; what Mark received is in
`../deliverables/`. The folder registry is [`../src/paths.py`](../src/paths.py).

## Layout

| Folder | Contents |
|---|---|
| [`summary/`](summary/) | Cross-source results. **Start here.** |
| [`se-hcl/<site>/`](se-hcl/) | 14 Stack Exchange sites, high cognitive load |
| [`se-lcl/<site>/`](se-lcl/) | 12 Stack Exchange sites, low cognitive load |
| [`external/<source>/`](external/) | Hacker News, PubMed (oncology), arXiv CS, arXiv Math |
| [`robustness/bge/<source>/`](robustness/bge/) | Same analysis with a second encoder (BGE-small), 9 sources |
| [`robustness/length-k/<source>/`](robustness/length-k/) | Only each text's first K chunks (CV K=3, PubMed K=4) |
| [`robustness/topic-k/<source>/`](robustness/topic-k/) | Family 13 with 25 and 100 topics (`_k25`, `_k100`) |
| [`meta/`](meta/) | `sites_manifest.csv` (site volumes), `anchor_samples.md` (GPT answers used by family 12) |

Each source folder holds a CSV and a PNG per result, with matching names.

## Summary files

| File | What it answers |
|---|---|
| `8_significance_all.{csv,png}` | Did similarity turn upward after ChatGPT (2022Q4)? One row per source and metric, 30 sources |
| `9_cog_load_comparison.{csv,png}` | High- vs low-load trends, centred on each site's pre-ChatGPT mean |
| `9_cog_load_test.{csv,png}`, `9_cog_load_sites.csv` | Formal high vs low test (Fisher, Mann–Whitney, permutation) |
| `10_within_vs_overall.csv` | Overall vs within-topic similarity trend (9 sources, family 6) |
| `11_same_question_all.csv` | Answers to the same question: do they converge? (26 SE) |
| `14_tag_topics_all.csv` | Topic control by Stack Exchange tags (26 SE) |
| `6_encoder_compare.csv` | MiniLM vs BGE-small: same verdict? (9 sources) |

## Families (file prefix)

| # | Family | Sources |
|---|---|---|
| 1, 1a, 1b | Lexical diversity and surface features (no embeddings) | Cross Validated, Philosophy |
| 2 | Length-control sensitivity (no embeddings) | Cross Validated, Philosophy |
| 3 | LSA semantic similarity (no embeddings) | Cross Validated, Philosophy |
| 4 | LDA topics (no embeddings) | Cross Validated, Philosophy |
| 5 | Quarterly embedding similarity (pairwise cosine) | all 30 |
| 6, 6a–6c | BERTopic topics over time; within-topic similarity (drops ~50% of answers as outliers — use for topic labels only) | core 5 + 4 external |
| 7 | High- vs low-score answers | Cross Validated, Philosophy |
| 8 | Interrupted time series at 2022Q4 (`8_its.png` per source) | all 30 |
| 11 | Answers to the same question (21 newer sites: ≤150 questions/quarter) | 26 SE |
| 12 | Drift towards GPT-4o-mini answers (anchor) | core 5 |
| 13 | Topic decomposition with K-means (K=50; diversity also on fixed 100-answer subsamples, `_r` columns) | all 30 |
| 14 | Topic control with Stack Exchange tags (same-tag vs different-tag pairs, tag diversity and drift) | 26 SE |

Core 5 = Cross Validated, Philosophy, Economics, Seasoned Advice, Travel.
