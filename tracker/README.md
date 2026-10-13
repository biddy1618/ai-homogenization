# Homogenization tracker

A forward-looking companion to the retrospective study: every week it measures **how much the
pages behind Google's top results for a question repeat one another**. Low diversity = the web
gives you the same answer many times over; a decline over time = homogenization you can watch live.

**Live dashboard:** https://biddy1618.github.io/ai-homogenization/tracker/dashboard/

## Pipeline (weekly, GitHub Actions)

1. **Collect** — [`tracker.py`](tracker.py): for each of the 45 questions in
   [`queries.txt`](queries.txt), fetch Google's top ~10 organic results via **Serper.dev**, drop video
   results (YouTube, Vimeo, TikTok, …), and save the result list to `data/raw/<date>/<query>.json`.
   One row per query goes to `data/serp_log.csv`; one provenance row per run to `data/_runs_meta.csv`.
2. **Analyse full pages** — [`fullpage.py`](fullpage.py): fetch each result's actual page through
   **ScrapingRobot** (GitHub's datacenter IPs are blocked by many sites), extract the main text
   (first ~1000 words), embed it with **MiniLM** (ONNX), and compute the per-query metrics into
   `data/runs_fullpage.csv`. Machine strings are stripped first: URLs, DOIs, e-mails, and any single
   "word" longer than 20 tokens (base64, hashes, markup fragments). This removes ~0.5% of tokens and no prose.
   MiniLM reads at most 128 tokens (~90 words) at a time, so each page is
   split into sentences that are packed, whole, into chunks of ≤ 120 tokens (counted with the model's
   own tokenizer); the page vector is the token-weighted mean of its chunk vectors. No sentence is
   cut. The cleaning and chunking live in [`../src/chunk_embed.py`](../src/chunk_embed.py)
   and are shared with the retrospective study. Pages that can't be fetched, aren't HTML (e.g. PDFs),
   or carry < 50 words are **dropped**; a query needs ≥ 3 analysable pages to be scored.
3. **Dashboard** — [`dashboard/build.py`](dashboard/build.py) regenerates a self-contained
   `dashboard/index.html` (data embedded), served by GitHub Pages.
4. **Commit** — results + dashboard are committed back to the repo. Git is the datastore.

## Metrics (per query, per run)

- **`distinct_ratio`** — **the headline** (shown as "% distinct" on the dashboard): `vendi / n_results`,
  the share of analysed pages that are effectively distinct. Normalising by page count keeps weeks
  comparable when fewer pages could be fetched.
- **`vendi`** — the *effective number of distinct pages* among the analysed results,
  `exp(entropy of the eigenvalues of the cosine-similarity matrix)`. Ranges from 1 (all pages say
  the same thing) to N (all different).
- **`mean_pairwise_cosine`** — average similarity between all page pairs.
- **`mean_marginal_novelty`** — how much new content each ranked page adds beyond those above it.
- **`n_serp` / `n_results`** — results returned vs. pages actually analysed (coverage).

## Query panel

45 specific, informational questions — 9 each in **health, finance, law, science, tech**. Commercial
("best X") queries were excluded: they return shopping/social pages that are neither informational
nor scrapable. Keep the panel **frozen** so the series stays comparable.

## Secrets & quotas

| Repo secret | Service | Free tier | Weekly use |
|---|---|---|---|
| `SERPER_API_KEY` | Serper.dev (Google results) | 2,500 queries on signup; then pay-as-you-go ($50 / 50k, valid 6 mo) | 45 |
| `SCRAPING_ROBOT_API_KEY` | ScrapingRobot (page fetch) | 5,000 scrapes/month | ~330 |

SerpAPI is still supported (`--provider serpapi`, secret `SERP_API_KEY`, mapped to the same-named
env var); runs through 2026-10-12 used SerpAPI. The provider is recorded per run in
`data/_runs_meta.csv` (`engine` column). If every search request fails (bad key, no credits),
`tracker.py` exits with an error so the workflow run fails visibly instead of recording nothing.

GitHub Actions minutes are free and unlimited on this public repo.

## Run locally

```powershell
python tracker/tracker.py --location "United States"          # key from .secrets/serper_dev_api_key.txt
python tracker/fullpage.py --provider scrapingrobot           # key from .secrets/scraping_robot_api_key.txt
python tracker/dashboard/build.py
```

Both stages are idempotent per `(date, query)`; pass `--force` to redo.

## Caveats

- Week-to-week movement per query is still large; read trends only after several months.
- Google's own ranking updates move the metric independently of web content.
- The page cache (`data/pagecache/`) is local scratch and not committed.
- Pages for the 2026-10-05 and 2026-10-12 runs were fetched on 2026-10-13, when the tracker moved to
  full-page analysis: those weeks use the URLs Google returned on that date but the page text of
  2026-10-13. From 2026-10-19 on, pages are fetched on the run date.
