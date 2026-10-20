# Results (artifacts)

All results here are **whole-text** results: each text is cleaned, split into sentence chunks of
at most 120 model tokens, and its vector is the average of the chunk vectors. Every embedding
result also has an **opening-window** control: exactly the first 120 model tokens of each
text, with shorter texts left out. In CSVs the opening-window columns start with `lc_`. It is
**plotted only in family 8** (length check: same verdict as whole text in 26/30 sources; the 4
that differ are significant only on the opening window); other plots show whole text only.
Redraw any plot from its CSV with `python src/replot.py`.

The delivered results (truncated at 128 tokens, as sent to Mark before 2026-10-15) are no longer
in the tree. Restore them with `git checkout delivered-v1 -- artifacts`; what Mark received is in
`../deliverables/`. The folder registry is [`../src/paths.py`](../src/paths.py).

## Layout

| Folder | Contents |
|---|---|
| [`summary/`](summary/) | Cross-source results. **Start here.** |
| [`se-hcl/<site>/`](se-hcl/) | 14 Stack Exchange sites, high cognitive load |
| [`se-lcl/<site>/`](se-lcl/) | 12 Stack Exchange sites, low cognitive load |
| [`external/<source>/`](external/) | Hacker News, PubMed (oncology), arXiv CS, arXiv Math (families 5, 8, 13 only: no questions or tags) |
| [`robustness/bge/<source>/`](robustness/bge/) | Same analysis with a second encoder (BGE-small), all 30 sources |
| [`robustness/length-k/<source>/`](robustness/length-k/) | Only each text's first K chunks (CV K=3, PubMed K=4) |
| [`robustness/topic-k/<source>/`](robustness/topic-k/) | Family 13 with 25 and 100 topics (`_k25`, `_k100`) |
| [`exploratory/`](exploratory/) | Earlier exploration, not part of the main analysis: families 1?4, 6, 7, 10 |
| [`meta/`](meta/) | `sites_manifest.csv` (site volumes), `anchor_samples.md` (GPT answers used by the first family-12 version) |

Each results folder holds its plots (PNG) directly and its tables in a `data/` subfolder, with
matching names (`5_semantic_bert.png` ? `data/5_semantic_bert.csv`).

## Summary files

| File | What it answers |
|---|---|
| `8_significance_all.{csv,png}` | Did similarity turn upward after ChatGPT (2022Q4)? One row per source and metric, 30 sources |
| `9_cog_load_comparison.{csv,png}` | High- vs low-load trends, centred on each site's pre-ChatGPT mean |
| `9_cog_load_test.{csv,png}`, `9_cog_load_sites.csv` | Formal high vs low test (Fisher, Mann?Whitney, permutation) |
| `11_same_question_all.csv`, `11_same_question_summary.png` | Answers to the same question: do they converge? (26 SE) |
| `12_anchor_all.csv`, `12_anchor_summary.png` | Do human answers move towards GPT's answer to their question? (26 SE) |
| `13_topic_summary.png` | K-means topics: same-topic convergence, topic diversity, topic-mix drift (30 sources) |
| `14_tag_topics_all.csv`, `14_tag_summary.png` | The same with Stack Exchange tags as topics (26 SE) |
| `6_encoder_compare.csv` | MiniLM vs BGE-small: same verdict? (30 sources; also family 9 per encoder, printed by `encoder_compare.py`) |

The `*_summary.png` plots show one row per site and one column per measure: the post-ChatGPT
slope change, filled = p<0.05 (`python src/summary_plots.py`).

## Families in the analysis (file prefix)

| # | Family | Sources |
|---|---|---|
| 5 | Quarterly embedding similarity (pairwise cosine) | all 30 |
| 8 | Interrupted time series at 2022Q4 (`8_its.png` per source) | all 30 |
| 9 | High vs low cognitive load (summary only) | 26 SE |
| 11 | Answers to the same question (21 newer sites: ?150 questions/quarter) | 26 SE |
| 12 | GPT anchor: similarity to gpt-4o-mini's answer to the same question; `pull` = question-specific part; `lc_*` = first 120 tokens of both | 26 SE |
| 13 | Topic decomposition with K-means (K=50; diversity and drift on fixed 100-answer samples, `_r` columns) | all 30 |
| 14 | Topic control with Stack Exchange tags (same-tag pairs, tag diversity and drift) | 26 SE |

Core 5 = Cross Validated, Philosophy, Economics, Seasoned Advice, Travel.

## Exploratory (`exploratory/`)

| # | Family | Sources | Why it is not in the main analysis |
|---|---|---|---|
| 1, 1a, 1b | Lexical diversity and surface features (no embeddings) | CV, Philosophy | Rises only because of length |
| 2 | Length-control window sweep | CV, Philosophy | Supports family 1?3 only |
| 3 | LSA semantic similarity (no embeddings) | CV, Philosophy | Replaced by embeddings (family 5) |
| 4 | LDA topics (no embeddings) | CV, Philosophy | Replaced by families 13 and 14 |
| 6, 6a?6c | BERTopic topics; within-topic similarity | core 5 + 4 external | Drops ~50% of answers as outliers; keep for topic labels |
| 7 | High- vs low-score answers | CV, Philosophy | Two sites only; both tiers rise |
| 10 | Overall vs within-topic trend (summary of family 6) | 9 sources | Depends on family 6 |
