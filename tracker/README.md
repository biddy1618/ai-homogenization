# Homogenization tracker

A forward-looking companion to the retrospective study: every week it measures **how much the
pages behind Google's top results for a question repeat one another**. Low diversity = the web
gives you the same answer many times over; a decline over time = homogenization you can watch live.

**Live dashboard:** https://biddy1618.github.io/ai-homogenization/tracker/dashboard/

## Pipeline (weekly, GitHub Actions)

1. **Collect** — [`tracker.py`](tracker.py): for each of the 100 questions in
   [`queries.txt`](queries.txt), fetch Google's top ~10 organic results via **Serper.dev**, drop video
   results (YouTube, Vimeo, TikTok, …), and save the result list to `data/raw/<date>/<query>.json`.
   One row per query goes to `data/serp_log.csv`; one provenance row per run to `data/_runs_meta.csv`.
2. **Analyse full pages** — [`fullpage.py`](fullpage.py): fetch each result's actual page through
   **ScrapingRobot** (GitHub's datacenter IPs are blocked by many sites), extract the main text
   (first ~1000 words), embed it with **MiniLM** (ONNX), and compute the per-query metrics. Machine strings are stripped first: URLs, DOIs, e-mails, and any single
   "word" longer than 20 tokens (base64, hashes, markup fragments). This removes ~0.5% of tokens and no prose.
   MiniLM reads at most 128 tokens (~90 words) at a time, so each page is
   split into sentences that are packed, whole, into chunks of ≤ 120 tokens (counted with the model's
   own tokenizer); the page vector is the token-weighted mean of its chunk vectors. No sentence is
   cut. The cleaning and chunking live in [`../src/chunk_embed.py`](../src/chunk_embed.py)
   and are shared with the retrospective study. Pages that can't be fetched, aren't HTML (e.g. PDFs),
   or carry < 50 words are **dropped**. Pages are read in Google rank order and **exactly the first 5
   readable pages** are analysed (fetching stops once they are found); a question with fewer than 5
   readable pages is left out that week. Results go to `data/runs_top5.csv`.
3. **Dashboard** — [`dashboard/build.py`](dashboard/build.py) regenerates a self-contained
   `dashboard/index.html` (data embedded), served by GitHub Pages.
4. **Commit** — results + dashboard are committed back to the repo. Git is the datastore.

## Metrics (per query, per run, on the first 5 readable pages)

- **`mean_pairwise_cosine`** — **headline 1, "similarity"**: average cosine similarity between all
  pairs of the 5 pages, the same measure as the retrospective study. Higher = the pages are more alike.
- **`vendi`** — **headline 2, "distinct pages out of 5"**: the effective number of distinct pages,
  `exp(entropy of the eigenvalues of the cosine-similarity matrix / n)`; 5 = all different, 1 = all
  the same. Unlike the average, it shows whether the sameness comes from a few repeated viewpoints.
- **`distinct_ratio`** — `vendi / 5`.
- **`mean_marginal_novelty`** — how much new content each ranked page adds beyond those above it.
- **`n_serp` / `n_results` / `positions`** — results returned, pages analysed (5), and their Google ranks.

**Methodology history.** v1 (2026-10-04 to 2026-10-19): headline "% distinct" = Vendi ÷ however many
pages could be read (3–10), in `data/runs_fullpage.csv`. It fell whenever more pages were read, so runs
were not comparable. v2 (from 2026-10-26): fixed 5 pages and the two headlines above; the v1 runs were
recomputed the same way (pages missing from the cache re-fetched on 2026-10-25). The dashboard shows
v2 only. `data/runs_fullpage.csv` stays in the repo as raw v1 history (`fullpage.py --top-k 0`
reproduces it); it also holds a 2026-10-26 row set from the last scheduled run of the old version.

## Query panel

100 specific, informational questions — 20 each in **health, finance, law, science, tech**. The
first 9 per domain are the original panel (the "core 45", tracked since 2026-10-04, shown as one
line until 2026-10-26); the other 55 were added on 2026-10-26. From then on the dashboard headline is
all questions; the original-45 line is shown only up to 2026-10-26. Commercial ("best X") queries are excluded:
they return shopping/social pages that are neither informational nor scrapable. Never edit or remove
a query; only add, and note the date.

## Secrets & quotas

| Repo secret | Service | Free tier | Weekly use |
|---|---|---|---|
| `SERPER_API_KEY` | Serper.dev (Google results) | 2,500 queries on signup; then pay-as-you-go ($50 / 50k, valid 6 mo) | 100 |
| `SCRAPING_ROBOT_API_KEY` | ScrapingRobot (page fetch) | 5,000 scrapes/month | ~650 (stops at 5 readable pages) |
| `AWS_ACCESS_KEY`, `AWS_SECRET_KEY` (optional) | private S3 bucket | — | ~0.5–0.9 MB: this run's page texts |

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

Both stages are idempotent per `(date, query)`; `--force` recomputes and replaces rows (no duplicates).

## Caveats

- Week-to-week movement per query is still large; read trends only after several months.
- Google's own ranking updates move the metric independently of web content.
- Page texts are never committed (they are other sites' content). They are cached per run date in
  `data/pagecache/<date>/`, so a week never reuses another week's text. With the AWS secrets set
  (ideally a user limited to this bucket), the workflow packs that run's texts into one file,
  `s3://biddy-homogenization/tracker/pages/<date>.jsonl.gz`, and restores only that same date on a
  re-run ([`pagestore.py`](pagestore.py) `pack` / `unpack`). The 2026-10-04 to 2026-10-19 runs are
  stored the same way; the 2026-10-26 texts stayed on the CI runner and are lost.
- Pages for the 2026-10-05 and 2026-10-12 runs were fetched on 2026-10-13, when the tracker moved to
  full-page analysis: those weeks use the URLs Google returned on that date but the page text of
  2026-10-13. From 2026-10-19 on, pages are fetched on the run date.
