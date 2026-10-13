# Homogenization Tracker — Implementation, Operations & Handover

> **Purpose.** The complete, self-contained reference for the live tracker: what it is, how it works,
> where the data lives, what it costs, how it sustains itself, **what it takes to transfer to Mark
> (and whether it would run on its own)**, the technical details, the phased roadmap, and the open
> questions. Written to be read cold. Companion to [project-briefing.md](project-briefing.md) and the
> code under [`../../tracker/`](../../tracker). Last updated 2026-09-26.

---

## 1. What it is and why

A forward-looking companion to the retrospective homogenization study. For a **fixed panel of search
queries**, it fetches Google's top-N results on a schedule and scores **how much those results repeat
one another**. Low diversity = the web says the same thing many ways; a decline over time =
homogenization you can watch happen, live and in public.

The retrospective paper measures the *past* (2009–2026 archives). The tracker measures the *future*
(from launch forward), and because the data is committed to a public repo, the trend is **auditable
by anyone**.

---

## 2. How it works (architecture)

```
GitHub Actions (weekly cron)
        │
        ▼
  tracker/tracker.py
        │   1. read query panel (tracker/queries.txt)
        │   2. SerpAPI  → top-N Google organic results (title + snippet)   [1 credit / query]
        │   3. MiniLM (ONNX) embeds each result's text
        │   4. compute 3 diversity metrics per query
        │   5. append rows + save raw SERP + write provenance
        ▼
  commit results back to the repo  (git = the datastore)
        │
        ▼
  (future) GitHub Pages / Streamlit dashboard reads the committed CSVs
```

No server, no database, no always-on process. Compute is the free GitHub-hosted runner; storage is
the git repo; presentation (future) is a static page. Total cost on the current design: **$0**.

---

## 3. The metrics (what each number means)

For each query, the N result texts (title + snippet) are embedded and reduced to three numbers:

- **`mean_pairwise_cosine`** — average similarity between all pairs of results. Higher = more
  redundant. Raw redundancy.
- **`vendi`** — the **effective number of distinct results** = exp(Shannon entropy of the eigenvalues
  of the cosine Gram matrix). Ranges 1 (all identical) to N (all different). **The headline metric** —
  interpretable as "out of N results, how many genuinely different answers are there?"
- **`mean_marginal_novelty`** — average new information each ranked result adds beyond the ones above
  it (1 − max cosine to any higher-ranked result). Low = you stop learning as you scroll down.
- **`distinct_ratio`** — `vendi / n_results`, a 0–1 normalization for comparing across queries with
  different N.

**First-run illustration (2026-09-26):** definitional tech queries are the most homogeneous
(`what is two factor authentication` Vendi 1.93, `what is a vpn` 1.96, `what is retrieval augmented
generation` 1.95 — ~2 distinct pages of 8); open questions are the most diverse (`how does inflation
affect the economy` 7.30, `how to start investing` 6.35).

---

## 4. Data layout (where it saves)

Everything lives under [`tracker/data/`](../../tracker/data), committed to `main`:

| Path | Contents |
|---|---|
| `runs.csv` | one row per query per run (the combined time series) |
| `<query-slug>.csv` | per-query time series (one file per query) |
| `raw/<date>/<query-slug>.json` | the raw top-N SERP (`position, title, link, domain, snippet`) |
| `_runs_meta.csv` | one provenance row per run (params, model, code SHA, counts) |

**Columns in `runs.csv`:** `date, category, query, n_results, mean_pairwise_cosine, vendi,
distinct_ratio, mean_marginal_novelty`.

**Why raw JSON matters:** it lets us (a) recompute metrics if the method changes and (b) gives phase 3
the result URLs to fetch. **Why provenance matters:** if we ever change the model, panel, or params,
the change is annotated in the data itself, so trends can't be silently corrupted.

---

## 5. Cost and quota

- **SerpAPI free tier:** 250 searches/month; 1 query = 1 credit (regardless of result count); only
  successful searches count; resets monthly.
- **Current panel:** 45 queries. Weekly → **~195–225 searches/month**, inside the free tier with
  headroom for occasional manual runs.
- **Embedding / compute:** free (MiniLM on CPU, on the GitHub-hosted runner).
- **Storage:** free (CSV/JSON in the repo).
- **Month-to-date usage (Sept 2026):** ~49 / 250.

---

## 6. Current progress

- **Phase 1 — MVP (done):** snippet-level tracker, 3 metrics, weekly workflow, first runner test green
  (the runner reached SerpAPI fine — only *page* fetches will be blocked later).
- **Phase 2 — production hardening (done, v0.2):**
  - pinned SERP inputs (`--location "United States" --device desktop --num 10`) so the origin can't
    drift;
  - pinned dependency versions (`numpy==2.5.1`, `fastembed==0.8.0`, `onnxruntime==1.28.0`) so
    embeddings stay numerically identical;
  - **raw-SERP capture** + **per-run provenance** (`_runs_meta.csv`);
  - **idempotency** — re-runs skip already-recorded `(date, query)` pairs before spending a credit
    (`--force` to override);
  - **panel expanded 18 → 45 queries** across 12 categories.
- First full 45-query snapshot committed for 2026-09-26.

---

## 7. Roadmap (future steps)

- **Phase 3 — full-page extraction.** Replace snippets with each result's actual page text (capped at
  ~1000 tokens, matching the study's length-control convention). **Critical constraint:** direct
  fetches from a GitHub runner are largely **blocked** (shared Azure IPs → Cloudflare/403; many pages
  are JS-rendered), so this must route through a **scraping API**. Options priced today: ScraperAPI
  (1,000 free credits/mo), ScrapingBee (Hobby $19/mo → 75k credits; 1 credit plain / 5 with JS),
  ScrapingRobot (flat, non-expiring). Design: swappable `fetch_page()` provider, **degrade to snippet
  on failure**, fetch only top-K, no-JS by default, dedupe URLs. Cost math: 45×top-10 weekly ≈ 780
  fetches/mo (or ~390 at top-5).
- **Phase 4 — dashboard.** Static GitHub Pages (or Streamlit) over the committed CSVs: per-query and
  per-category trends with a "since when" marker.
- **Phase 5 — analysis & write-up.** Interpret the accumulated series; connect to the paper's
  consequences section (shallower search / epistemic narrowing).

Nice-to-haves: annotate major Google ranking-update dates (a confounder); domain-level analysis using
the captured `domain` field; expand/rotate the panel deliberately (with provenance).

---

## 8. Sustainability — does it run on its own?

**Yes.** It's a scheduled GitHub Action (`.github/workflows/tracker.yml`, cron **Mondays 06:17 UTC**)
plus manual trigger (`workflow_dispatch`). Each run installs pinned deps, downloads the MiniLM model,
runs the panel, and commits results using the built-in `GITHUB_TOKEN`. No server to keep alive, no
human in the loop.

**What could stop it (and the mitigation):**
- **SerpAPI key missing/expired** → the run fails loudly (GitHub emails on failure). Fix: refresh the
  `SERP_API_KEY` secret.
- **Free quota exhausted** → SerpAPI returns an error; queries skip and the run logs it. Mitigation:
  the panel is sized to stay under 250/mo.
- **A dependency breaks** → prevented by pinned versions; unpin only deliberately (and the provenance
  records the change).
- **90 days of no repo activity** → GitHub disables scheduled workflows on inactive repos; a single
  manual run (or any commit) re-enables them.
- **Google/SerpAPI SERP-format change** → SerpAPI absorbs most of this; if the shape changes, the
  parser may need a tweak.

---

## 9. Transfer to Mark — handover checklist

If the project is handed to Mark and he wants it to keep running under his control:

1. **Repository** — transfer ownership, or he forks it. Actions must be **enabled** on his copy.
2. **SerpAPI key** — Mark creates his **own free SerpAPI account** and gets a key (250/mo, no card).
3. **Secret** — he adds it as a repository secret named **`SERP_API_KEY`** (Settings → Secrets and
   variables → Actions). This is the only credential the runner needs.
4. **Permissions** — the workflow already sets `permissions: contents: write`, so the built-in token
   commits results; nothing else to configure.
5. **First run** — trigger once via Actions → *homogenization-tracker* → Run workflow, to confirm
   green; thereafter the weekly cron carries it.
6. **(Only if editing workflows)** — pushing changes to `.github/workflows/*` requires a Personal
   Access Token with the **`workflow`** scope (a gotcha we hit; not needed just to *run* it).

**Would it run on its own after transfer?** Yes — with his `SERP_API_KEY` set, it self-runs weekly and
commits data at **$0/month**. He needs to do nothing week-to-week. The only ongoing "cost" is the free
SerpAPI account staying active. Phase 3 (full-page) would add a scraping-API key and possibly a small
monthly fee (≈$19 if he wants JS rendering at scale); phases 1–2 stay free.

---

## 10. Technical details

- **Language/runtime:** Python 3.12; standalone script (`tracker/tracker.py`), no dependency on the
  study's analysis stack. Only `numpy` + `fastembed` (+ its `onnxruntime`) are needed.
- **Model:** `sentence-transformers/all-MiniLM-L6-v2` via **fastembed/ONNX** (no PyTorch → installs
  cleanly on Windows and Linux runners). Provisioned from a GCS mirror and cached.
- **HTTP:** stdlib `urllib` with exponential backoff on 429/503 (no `requests` dependency).
- **SerpAPI params sent:** `engine=google, q, num=10, gl=us, hl=en, google_domain=google.com,
  device=desktop, location="United States"`. The User-Agent header is only on *our* call to SerpAPI;
  the Google-facing proxy/UA is managed by SerpAPI.
- **Reproducibility:** pinned deps + pinned inputs + per-run provenance (model, params, `code_sha`).
- **Idempotency:** `(date, query)` keys are read from `runs.csv` and skipped before any fetch;
  `--force` overrides (note: `--force` *appends*, so use it only for fresh dates, not to overwrite).
- **Key handling:** reads `SERPAPI_KEY` env first (CI secret), then falls back to
  `.secrets/serp_api_key.txt` (gitignored) for local runs. The key is never printed or committed.

---

## 11. Runbook (common tasks)

- **Run locally:**
  ```powershell
  $env:SERPAPI_KEY = "<key>"   # or put it in .secrets/serp_api_key.txt
  python tracker/tracker.py --location "United States"
  ```
- **Cheap test (2 credits):** `python tracker/tracker.py --limit 2`
- **Trigger the runner:** GitHub → Actions → *homogenization-tracker* → Run workflow (owner/admin
  only; the `baitud_cat` read account cannot dispatch).
- **Add/change queries:** edit `tracker/queries.txt` (`category | query`); keep the panel frozen once
  a series is meaningful, and record the change (provenance + a commit).
- **Read the data:** open `tracker/data/runs.csv`, or the per-query file; provenance in `_runs_meta.csv`.

---

## 12. Open technical questions

- **Snippet vs full-page:** snippets conflate real page homogenization with Google's snippet
  generation; phase 3 (full-page) is the stronger signal but needs a scraping API.
- **Provider choice for phase 3:** ScraperAPI (free tier) vs ScrapingBee ($19) vs ScrapingRobot; or
  consolidate SERP+page-fetch onto one vendor (ScrapingBee/ScraperAPI both offer a Google endpoint).
- **Panel governance:** freeze at 45, or grow to ~50 and rotate categories? Frozen = comparable;
  growing = richer.
- **Confounders:** Google ranking-algorithm updates move the metric independently — annotate them.
- **Baseline:** the tracker is forward-only (Google doesn't serve historical SERPs); the retrospective
  study is the historical arm.
- **Dashboard tech:** static GitHub Pages (simplest) vs Streamlit (interactive but sleeps when idle).
