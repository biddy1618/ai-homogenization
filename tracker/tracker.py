"""Homogenization tracker (MVP) — how redundant are Google's top-N results?

For each query in a panel, fetch the top-N Google results via SerpAPI, embed the result
texts (title + snippet) with the same MiniLM/ONNX model this repo uses elsewhere, and
compute three diversity metrics per query per run:

  * mean_pairwise_cosine  — raw redundancy of the result set (higher = more alike).
  * vendi                 — effective number of "distinct" results: exp(Shannon entropy
                            of the eigenvalues of the cosine Gram matrix); range [1, n].
  * mean_marginal_novelty — average "new information" each ranked result adds beyond the
                            higher-ranked ones (1 - max cosine to any result above it);
                            lower = you stop learning sooner as you read down the page.

Rows are appended to committed CSVs under ``tracker/data/`` (a combined ``runs.csv`` plus
one file per query); the raw top-N SERP is saved under ``tracker/data/raw/<date>/`` and a
per-run provenance row to ``_runs_meta.csv``. The time series is versioned in git — no
database needed. Re-runs are idempotent per (date, query). Built to run weekly on a
GitHub-hosted runner against the SerpAPI free tier (250 searches/month).

Setup: set the ``SERPAPI_KEY`` environment variable (a GitHub Actions secret in CI). Free
key at https://serpapi.com/ .

Usage:
    python tracker/tracker.py --queries tracker/queries.txt --out-dir tracker/data
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
TRACKER_VERSION = "0.3"

# Video result types are dropped: their pages carry no article text to full-page-scrape, so
# they only add noise to the diversity metric. (Social/forum results are kept — they're real
# text answers; they just fall back to snippet when full-page extraction is thin.)
BLOCKLIST = {
    "youtube.com", "youtu.be", "m.youtube.com", "vimeo.com", "dailymotion.com", "tiktok.com",
}

# Same model + GCS mirror as src/semantic_bert.py, inlined so the tracker stays a lean,
# standalone tool (CI needs only numpy + fastembed, not the full analysis stack).
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
GCS_URL = (
    "https://storage.googleapis.com/qdrant-fastembed/"
    "sentence-transformers-all-MiniLM-L6-v2.tar.gz"
)


def load_model(cache_dir: Path):
    from fastembed import TextEmbedding
    from fastembed.text.onnx_embedding import OnnxTextEmbedding

    cache_dir.mkdir(parents=True, exist_ok=True)
    model_dir = OnnxTextEmbedding.retrieve_model_gcs(
        MODEL_NAME, GCS_URL, str(cache_dir), deprecated_tar_struct=True
    )
    return TextEmbedding(MODEL_NAME, specific_model_path=str(model_dir))


def embed_texts(model, texts: list[str], batch_size: int = 256) -> np.ndarray:
    """Embed and L2-normalize a list of texts into an (n, dim) array."""
    vecs = np.asarray(list(model.embed(texts, batch_size=batch_size)), dtype=np.float64)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


# --------------------------------------------------------------------------- panel I/O
def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "query"


def _blocked(url: str) -> bool:
    """True if the result's domain is a non-article type (video/social) we skip."""
    host = urllib.parse.urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return any(host == d or host.endswith("." + d) for d in BLOCKLIST)


def read_queries(path: Path) -> list[tuple[str, str]]:
    """Parse the panel file. Lines are 'category | query'; '#' comments and blanks skipped."""
    out: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            cat, q = line.split("|", 1)
            out.append((cat.strip() or "general", q.strip()))
        else:
            out.append(("general", line))
    return out


# --------------------------------------------------------------------------- SerpAPI
def fetch_serp(query: str, api_key: str, num: int, gl: str, hl: str,
               engine: str = "google", device: str = "desktop", location: str | None = None,
               retries: int = 4, timeout: int = 60) -> list[dict]:
    """Return organic results (position/title/snippet/link) for one query via SerpAPI."""
    params = {
        "engine": engine, "q": query, "api_key": api_key,
        "num": num, "gl": gl, "hl": hl, "google_domain": "google.com",
        "device": device,
    }
    if location:
        params["location"] = location
    url = f"{SERPAPI_ENDPOINT}?{urllib.parse.urlencode(params)}"
    backoff, last = 3.0, None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ai-homogenization-tracker/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read())
            if "error" in data:
                raise RuntimeError(f"SerpAPI error: {data['error']}")
            results = data.get("organic_results", []) or []
            return [
                {
                    "position": item.get("position"),
                    "title": item.get("title", "") or "",
                    "snippet": item.get("snippet", "") or "",
                    "link": item.get("link", "") or "",
                }
                for item in results
            ]
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 503):  # rate limit / throttle — back off and retry
                time.sleep(max(backoff, 15.0) * (attempt + 1))
                backoff *= 2
            else:
                raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(backoff)
            backoff *= 2
    raise RuntimeError(f"SerpAPI GET failed after {retries} tries: {query!r} ({last})")


# --------------------------------------------------------------------------- metrics
def mean_pairwise_cosine(v: np.ndarray) -> float:
    """Mean cosine over distinct pairs of L2-normalized rows (closed form)."""
    n = len(v)
    if n < 2:
        return float("nan")
    s = v.sum(axis=0)
    return float((s @ s - n) / (n * (n - 1)))


def vendi_score(v: np.ndarray) -> float:
    """Effective number of distinct items = exp(Shannon entropy of eigenvalues of K/n)."""
    n = len(v)
    if n < 2:
        return float(n)
    k = (v @ v.T) / n
    w = np.clip(np.linalg.eigvalsh(k).real, 0.0, None)
    total = w.sum()
    if total <= 0:
        return float("nan")
    w = w / total
    nz = w[w > 1e-12]
    return float(np.exp(-np.sum(nz * np.log(nz))))


def mean_marginal_novelty(v: np.ndarray, positions: list[int]) -> float:
    """Average (1 - max cosine to any higher-ranked result), over results 2..n by rank."""
    n = len(v)
    if n < 2:
        return float("nan")
    vv = v[np.argsort(positions)]
    novelties = [1.0 - float(np.max(vv[:k] @ vv[k])) for k in range(1, n)]
    return float(np.mean(novelties)) if novelties else float("nan")


# --------------------------------------------------------------------------- driver
FIELDNAMES = ["date", "category", "query", "n_results",
              "mean_pairwise_cosine", "vendi", "distinct_ratio", "mean_marginal_novelty"]


def _append_row(path: Path, row: dict) -> None:
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if is_new:
            w.writeheader()
        w.writerow(row)


def _existing_keys(combined: Path) -> set[tuple[str, str]]:
    """(date, query) pairs already recorded, so re-runs are idempotent."""
    keys: set[tuple[str, str]] = set()
    if combined.exists():
        with combined.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                keys.add((row["date"], row["query"]))
    return keys


def _save_raw(out_dir: Path, run_date: str, query: str, results: list[dict]) -> None:
    """Persist the raw top-N SERP so metrics can be recomputed and phase-3 has the URLs."""
    raw_dir = out_dir / "raw" / run_date
    raw_dir.mkdir(parents=True, exist_ok=True)
    payload = [
        {"position": r["position"], "title": r["title"], "link": r["link"],
         "domain": urllib.parse.urlparse(r["link"]).netloc, "snippet": r["snippet"]}
        for r in results
    ]
    (raw_dir / f"{slugify(query)}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _code_sha() -> str:
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


META_FIELDS = ["run_date", "run_ts_utc", "tracker_version", "model", "engine", "num",
               "gl", "hl", "device", "location", "n_queries", "n_ok", "n_skipped", "code_sha"]


def _write_meta(out_dir: Path, run_date: str, args, n_queries: int, n_ok: int, n_skipped: int) -> None:
    """One provenance row per run, so any methodology change is annotated in the data."""
    path = out_dir / "_runs_meta.csv"
    row = {
        "run_date": run_date,
        "run_ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tracker_version": TRACKER_VERSION, "model": MODEL_NAME, "engine": args.engine,
        "num": args.num, "gl": args.gl, "hl": args.hl, "device": args.device,
        "location": args.location or "", "n_queries": n_queries, "n_ok": n_ok,
        "n_skipped": n_skipped, "code_sha": _code_sha(),
    }
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=META_FIELDS)
        if is_new:
            w.writeheader()
        w.writerow(row)


def main() -> None:
    ap = argparse.ArgumentParser(description="Homogenization tracker (MVP)")
    ap.add_argument("--queries", type=Path, default=Path("tracker/queries.txt"))
    ap.add_argument("--out-dir", type=Path, default=Path("tracker/data"))
    ap.add_argument("--num", type=int, default=10, help="Top-N results per query")
    ap.add_argument("--gl", default="us", help="Google country code")
    ap.add_argument("--hl", default="en", help="Google UI language")
    ap.add_argument("--engine", default="google")
    ap.add_argument("--device", default="desktop", choices=["desktop", "mobile", "tablet"],
                    help="Pin the device profile so the series stays comparable over time")
    ap.add_argument("--location", default=None,
                    help="Pin the search origin (e.g. 'United States') for comparable results")
    ap.add_argument("--model-cache", type=Path, default=Path("data/models"))
    ap.add_argument("--date", default=None, help="Run date YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--min-results", type=int, default=3, help="Skip queries with fewer usable results")
    ap.add_argument("--key-file", type=Path, default=Path(".secrets/serp_api_key.txt"),
                    help="Fallback file holding the SerpAPI key when SERPAPI_KEY is unset")
    ap.add_argument("--limit", type=int, default=0, help="Process only the first N queries (0 = all)")
    ap.add_argument("--force", action="store_true", help="Re-record queries already saved for this date")
    ap.add_argument("--sleep", type=float, default=1.0, help="Seconds between queries (throughput guard)")
    args = ap.parse_args()

    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key and args.key_file.exists():
        api_key = args.key_file.read_text(encoding="utf-8").strip()
    if not api_key:
        sys.exit("ERROR: set SERPAPI_KEY or put the key in .secrets/serp_api_key.txt "
                 "(free key at https://serpapi.com/ — 250 searches/month).")

    queries = read_queries(args.queries)
    if not queries:
        sys.exit(f"No queries found in {args.queries}")
    if args.limit > 0:
        queries = queries[:args.limit]
    run_date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print("Loading MiniLM (ONNX)…", flush=True)
    model = load_model(args.model_cache)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    combined = args.out_dir / "runs.csv"
    done = set() if args.force else _existing_keys(combined)

    used = n_ok = n_skipped = 0
    for i, (category, query) in enumerate(queries, 1):
        if (run_date, query) in done:  # idempotent: skip before spending a credit
            print(f"[{i}/{len(queries)}] skip {query!r}: already recorded for {run_date}", flush=True)
            n_skipped += 1
            continue
        try:
            results = fetch_serp(query, api_key, args.num, args.gl, args.hl,
                                 args.engine, args.device, args.location)
            used += 1
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{len(queries)}] SKIP {query!r}: {e}", flush=True)
            n_skipped += 1
            continue

        results = [r for r in results if not _blocked(r.get("link", ""))]
        _save_raw(args.out_dir, run_date, query, results)
        texts, positions = [], []
        for r in results:
            text = f"{r['title']}. {r['snippet']}".strip()
            if text and text != ".":
                texts.append(text)
                positions.append(r["position"] or (len(positions) + 1))

        n = len(texts)
        if n < args.min_results:
            print(f"[{i}/{len(queries)}] SKIP {query!r}: only {n} usable results", flush=True)
            n_skipped += 1
            continue

        v = embed_texts(model, texts)
        vendi = vendi_score(v)
        row = {
            "date": run_date, "category": category, "query": query, "n_results": n,
            "mean_pairwise_cosine": round(mean_pairwise_cosine(v), 6),
            "vendi": round(vendi, 4),
            "distinct_ratio": round(vendi / n, 4),
            "mean_marginal_novelty": round(mean_marginal_novelty(v, positions), 6),
        }
        _append_row(combined, row)
        _append_row(args.out_dir / f"{slugify(query)}.csv", row)
        n_ok += 1
        print(f"[{i}/{len(queries)}] {query!r}: n={n} cos={row['mean_pairwise_cosine']:.3f} "
              f"vendi={vendi:.2f} novelty={row['mean_marginal_novelty']:.3f}", flush=True)
        time.sleep(args.sleep)

    _write_meta(args.out_dir, run_date, args, len(queries), n_ok, n_skipped)
    print(f"\nDone → {combined} (+ per-query CSVs, raw/, _runs_meta.csv in {args.out_dir}). "
          f"Recorded {n_ok}, skipped {n_skipped}. Used ~{used} SerpAPI searches (free tier = 250/month).")


if __name__ == "__main__":
    main()
