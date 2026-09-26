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
one file per query), so the time series is versioned in git — no database needed. Built to
run weekly on a GitHub-hosted runner against the SerpAPI free tier (250 searches/month).

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

    used = 0
    for i, (category, query) in enumerate(queries, 1):
        try:
            results = fetch_serp(query, api_key, args.num, args.gl, args.hl,
                                 args.engine, args.device, args.location)
            used += 1
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{len(queries)}] SKIP {query!r}: {e}", flush=True)
            continue

        texts, positions = [], []
        for r in results:
            text = f"{r['title']}. {r['snippet']}".strip()
            if text and text != ".":
                texts.append(text)
                positions.append(r["position"] or (len(positions) + 1))

        n = len(texts)
        if n < args.min_results:
            print(f"[{i}/{len(queries)}] SKIP {query!r}: only {n} usable results", flush=True)
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
        print(f"[{i}/{len(queries)}] {query!r}: n={n} cos={row['mean_pairwise_cosine']:.3f} "
              f"vendi={vendi:.2f} novelty={row['mean_marginal_novelty']:.3f}", flush=True)
        time.sleep(args.sleep)

    print(f"\nDone → {combined} (+ per-query CSVs in {args.out_dir}). "
          f"Used ~{used} SerpAPI searches (free tier = 250/month).")


if __name__ == "__main__":
    main()
