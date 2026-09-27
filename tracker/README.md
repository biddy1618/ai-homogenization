# Homogenization tracker (MVP)

A forward-looking companion to the retrospective study: it measures **how much Google's
top-N results for a query repeat one another**, and tracks that over time. Low diversity =
the web says the same thing many ways; a drop over time = homogenization you can watch live.

## What it does

For each query in [`queries.txt`](queries.txt):

1. Fetch the top-N Google organic results via **SerpAPI** (title + snippet).
2. Embed the result texts with **MiniLM** (ONNX, same model as the main study).
3. Compute three per-query diversity metrics:
   - **`mean_pairwise_cosine`** — raw redundancy of the result set (higher = more alike).
   - **`vendi`** — effective number of *distinct* results (1 … N); the headline number.
   - **`mean_marginal_novelty`** — how much new info each ranked result adds beyond the
     ones above it (lower = you stop learning sooner as you scroll).
4. Append one row per query to committed CSVs in [`data/`](data) — a combined `runs.csv`
   plus one file per query. The raw top-N SERP is saved under `data/raw/<date>/` and a
   per-run provenance row to `data/_runs_meta.csv`. **Git is the datastore; no database
   needed.** Re-runs are idempotent per `(date, query)` (pass `--force` to overwrite).

## Run it locally

```powershell
$env:SERPAPI_KEY = "<your-free-key>"          # get one at https://serpapi.com/
python tracker/tracker.py --queries tracker/queries.txt --out-dir tracker/data
```

Only `numpy` + `fastembed` are required (`pip install numpy fastembed`).

## Automation

[`.github/workflows/tracker.yml`](../.github/workflows/tracker.yml) runs it **weekly** on a
GitHub-hosted runner, rebuilds the dashboard, and commits the new rows. Add your key as a
repository secret named `SERP_API_KEY` (Settings → Secrets and variables → Actions).

## Dashboard

[`dashboard/build.py`](dashboard/build.py) generates a self-contained
[`dashboard/index.html`](dashboard/index.html) from `data/runs.csv` — the data is embedded, so it
renders on GitHub Pages *and* by simply opening the file (no server needed). Rebuild locally with
`python tracker/dashboard/build.py`. To publish it, enable **GitHub Pages** (Settings → Pages →
deploy from `main`); it will be served at `…/tracker/dashboard/`.

## Cost / quota

~45 queries × weekly ≈ **195–225 searches/month** — inside the SerpAPI **free tier**
(250/mo), with headroom for manual runs. One query = one search credit, regardless of how
many results come back.

## Notes / next steps

- MVP scores **snippets**; a v1 upgrade fetches each result's full page text for richer
  embeddings (doesn't cost SerpAPI credits, but some sites block bots).
- Keep the query panel **frozen** once tracking starts so the series stays comparable.
- Dashboard (GitHub Pages / Streamlit) reads the committed CSVs — to be added.
- Google's own ranking changes move the metric independently; log major update dates as
  annotations when interpreting trends.
