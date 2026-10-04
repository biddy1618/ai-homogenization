"""Full-page recompute of tracker metrics — run LOCALLY (not in CI).

The weekly CI tracker is snippet-level because GitHub runner IPs are blocked from fetching result
pages. This script runs from a normal (residential) machine: it reads the raw SERP URLs we already
saved under ``tracker/data/raw/<date>/``, fetches each actual page, extracts its main text (capped
to ~1000 tokens), re-embeds with the same MiniLM model, and recomputes the three diversity metrics
on FULL PAGE CONTENT. Output goes to a parallel ``tracker/data/runs_fullpage.csv`` — the
snippet-level ``runs.csv`` is left untouched for comparison.

Robustness: fetched pages are cached (re-runs are cheap), any page that fails/blocks/non-HTML falls
back to its snippet, and the per-row ``n_fullpage`` records how many of the N results were truly
full-page (coverage). Re-runs are idempotent per (date, query).

No scraping API needed — uses your machine's IP directly. Deps: beautifulsoup4 + numpy + fastembed.

Usage:
    python tracker/fullpage.py                 # every date under tracker/data/raw/
    python tracker/fullpage.py --date 2026-09-28
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tracker import (  # noqa: E402  (same MiniLM model + metrics as the snippet tracker)
    load_model, embed_texts, mean_pairwise_cosine, vendi_score, mean_marginal_novelty, slugify,
)

RAW = Path("tracker/data/raw")
RUNS = Path("tracker/data/runs.csv")
OUT = Path("tracker/data/runs_fullpage.csv")
CACHE = Path("tracker/data/pagecache")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

FIELDS = ["date", "category", "query", "n_results", "n_fullpage",
          "mean_pairwise_cosine", "vendi", "distinct_ratio", "mean_marginal_novelty"]


def fetch_page_text(url: str, api_key: str | None = None, timeout: int = 20,
                    max_tokens: int = 1000) -> str | None:
    """Capped main-text of a page (cached by TARGET url), or None on failure/non-HTML.

    If ``api_key`` is set, the page is fetched through ScraperAPI (residential/rotating proxies),
    which works from blocked datacenter IPs (VDI / CI runner). The cache is keyed by the target
    url, so a page already fetched directly is reused without spending an API credit."""
    key = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".txt")
    if key.exists():
        return key.read_text(encoding="utf-8") or None
    fetch_url = url
    if api_key:
        fetch_url = "https://api.scraperapi.com/?" + urllib.parse.urlencode(
            {"api_key": api_key, "url": url})
    try:
        req = urllib.request.Request(fetch_url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if "html" not in r.headers.get("Content-Type", "").lower():
                CACHE.mkdir(parents=True, exist_ok=True)
                key.write_text("", encoding="utf-8")  # cache the "not usable" verdict
                return None
            raw = r.read(2_000_000)
    except Exception:  # noqa: BLE001  — transient; don't cache, allow a later retry
        return None
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    node = soup.find("article") or soup.find("main") or soup.body or soup
    text = " ".join(" ".join(node.get_text(" ").split()).split()[:max_tokens])
    CACHE.mkdir(parents=True, exist_ok=True)
    key.write_text(text, encoding="utf-8")
    return text or None


def _existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    if OUT.exists():
        with OUT.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                keys.add((row["date"], row["query"]))
    return keys


def main() -> None:
    ap = argparse.ArgumentParser(description="Full-page recompute of tracker metrics (local)")
    ap.add_argument("--date", default=None, help="Only this run date (default: all under raw/)")
    ap.add_argument("--min-results", type=int, default=3)
    ap.add_argument("--sleep", type=float, default=0.5, help="Seconds between page fetches")
    ap.add_argument("--model-cache", type=Path, default=Path("data/models"))
    ap.add_argument("--provider", choices=["none", "scraperapi"], default="none",
                    help="Route fetches through a scraping API (works from blocked datacenter IPs)")
    ap.add_argument("--key-file", type=Path, default=Path(".secrets/scraper_api_key.txt"))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    api_key = None
    if args.provider == "scraperapi":
        api_key = os.environ.get("SCRAPER_API_KEY")
        if not api_key and args.key_file.exists():
            api_key = args.key_file.read_text(encoding="utf-8").strip()
        if not api_key:
            sys.exit("ERROR: --provider scraperapi needs a key in .secrets/scraper_api_key.txt "
                     "or the SCRAPER_API_KEY env var (free key at https://scraperapi.com/).")

    if not RUNS.exists():
        sys.exit(f"{RUNS} not found")
    snip = list(csv.DictReader(RUNS.open(encoding="utf-8")))
    meta = {(r["date"], slugify(r["query"])): (r["query"], r["category"]) for r in snip}

    dates = [args.date] if args.date else sorted({d.name for d in RAW.iterdir() if d.is_dir()})
    done = set() if args.force else _existing_keys()

    print("Loading MiniLM (ONNX)…", flush=True)
    model = load_model(args.model_cache)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out_new = not OUT.exists()
    writer = csv.DictWriter(OUT.open("a", newline="", encoding="utf-8"), fieldnames=FIELDS)
    if out_new:
        writer.writeheader()

    for date in dates:
        ddir = RAW / date
        if not ddir.is_dir():
            print(f"[{date}] no raw/ dir, skipping", flush=True)
            continue
        files = sorted(ddir.glob("*.json"))
        for i, jf in enumerate(files, 1):
            slug = jf.stem
            query, category = meta.get((date, slug), (slug, "general"))
            if (date, query) in done:
                print(f"[{date} {i}/{len(files)}] skip {query!r} (done)", flush=True)
                continue
            results = json.loads(jf.read_text(encoding="utf-8"))
            texts, positions, n_fp = [], [], 0
            for r in results:
                link = r.get("link", "")
                page = fetch_page_text(link, api_key, timeout=60 if api_key else 20) if link else None
                time.sleep(args.sleep)
                if page and len(page.split()) >= 20:
                    txt, is_fp = page, True
                else:
                    txt, is_fp = f"{r.get('title','')}. {r.get('snippet','')}".strip(), False
                if txt and txt != ".":
                    texts.append(txt)
                    positions.append(r.get("position") or (len(positions) + 1))
                    n_fp += int(is_fp)
            n = len(texts)
            if n < args.min_results:
                print(f"[{date} {i}/{len(files)}] skip {query!r}: only {n} usable", flush=True)
                continue
            v = embed_texts(model, texts)
            vendi = vendi_score(v)
            writer.writerow({
                "date": date, "category": category, "query": query, "n_results": n,
                "n_fullpage": n_fp,
                "mean_pairwise_cosine": round(mean_pairwise_cosine(v), 6),
                "vendi": round(vendi, 4), "distinct_ratio": round(vendi / n, 4),
                "mean_marginal_novelty": round(mean_marginal_novelty(v, positions), 6),
            })
            print(f"[{date} {i}/{len(files)}] {query!r}: n={n} full={n_fp}/{n} "
                  f"vendi={vendi:.2f}", flush=True)

    print(f"\nDone -> {OUT}")


if __name__ == "__main__":
    main()
