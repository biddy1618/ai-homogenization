"""Homogenization tracker — stage 2: diversity metrics on FULL PAGE content.

Reads the result lists saved by stage 1 (``tracker/data/raw/<date>/*.json``), fetches each result's
actual page through a scraping API (ScrapingRobot by default in CI — datacenter IPs such as GitHub
runners and VDIs are blocked by many sites), extracts the main text (capped at ~1000 tokens),
embeds it with MiniLM, and computes the per-query diversity metrics into
``tracker/data/runs_fullpage.csv``.

Fixed page count (methodology v2, from 2026-10-26; historic runs recomputed): for each query the
pages are read in Google rank order and exactly the first ``--top-k`` (default 5) readable pages are
analysed; fetching stops once they are found, and a query with fewer readable pages is skipped that
week. This keeps every metric comparable across weeks. Output: ``runs_top5.csv``. ``--top-k 0``
reproduces methodology v1 (all readable pages, ``runs_fullpage.csv``, kept as an archive).

A page that can't be fetched or yields too little text is DROPPED (no snippet substitution).
``n_serp`` = results returned, ``n_results`` = pages analysed, ``positions`` = their Google ranks.
Pages are cached locally (re-runs are cheap). Re-running a date replaces its rows (no duplicates).

Usage:
    python tracker/fullpage.py --provider scrapingrobot                 # every date under raw/
    python tracker/fullpage.py --provider scrapingrobot --date 2026-10-26
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from tracker import (  # noqa: E402  (same MiniLM model + metrics as the snippet tracker)
    load_model, embed_texts, mean_pairwise_cosine, vendi_score, mean_marginal_novelty, slugify,
)
from chunk_embed import counting_tokenizer, embed_documents  # noqa: E402  (shared with the study)

RAW = Path("tracker/data/raw")
SERP_LOG = Path("tracker/data/serp_log.csv")
LEGACY_OUT = Path("tracker/data/runs_fullpage.csv")   # methodology v1 (all readable pages)
CACHE = Path("tracker/data/pagecache")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

FIELDS = ["date", "category", "query", "n_serp", "n_results",
          "mean_pairwise_cosine", "vendi", "distinct_ratio", "mean_marginal_novelty"]
FIELDS_V2 = FIELDS + ["positions"]


def _get_html(url: str, provider: str, api_key: str | None, timeout: int) -> bytes | None:
    """Raw HTML bytes for ``url`` via the provider. None = failure (retry); b'' = non-HTML."""
    if provider == "scrapingrobot":
        body = json.dumps({"url": url, "render": False}).encode()
        req = urllib.request.Request("https://api.scrapingrobot.com/?token=" + api_key,
                                     data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        d = json.loads(raw)
        if d.get("status") != "SUCCESS":
            return None
        return (d.get("result") or "").encode("utf-8", "ignore")
    fetch_url = url
    if provider == "scraperapi":
        fetch_url = "https://api.scraperapi.com/?" + urllib.parse.urlencode({"api_key": api_key, "url": url})
    req = urllib.request.Request(fetch_url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if "html" not in r.headers.get("Content-Type", "").lower():
            return b""  # non-HTML (PDF, etc.)
        return r.read(2_000_000)


def fetch_page_text(url: str, provider: str = "none", api_key: str | None = None,
                    timeout: int = 20, max_tokens: int = 1000, cache_only: bool = False) -> str | None:
    """Capped main-text of a page (cached by TARGET url), or None on failure/non-HTML.

    ``provider`` routes the fetch: 'none' (direct, only works from an unblocked IP), 'scraperapi'
    (GET-wrapped proxy), or 'scrapingrobot' (POST + gzip JSON). The cache is keyed by the target
    url, so a page already fetched is reused without spending a credit."""
    key = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".txt")
    if key.exists():
        text = key.read_text(encoding="utf-8")
        return None if text.startswith("%PDF-") else (text or None)
    if cache_only:
        return None
    try:
        raw = _get_html(url, provider, api_key, timeout)
    except Exception:  # noqa: BLE001  — transient; don't cache, allow a later retry
        return None
    if raw is None:
        return None
    if raw.lstrip()[:5] == b"%PDF-":  # scraping APIs can return PDF bytes as the 'HTML' result
        raw = b""
    if raw == b"":  # non-HTML — cache the "not usable" verdict
        CACHE.mkdir(parents=True, exist_ok=True)
        key.write_text("", encoding="utf-8")
        return None
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    node = soup.find("article") or soup.find("main") or soup.body or soup
    text = " ".join(" ".join(node.get_text(" ").split()).split()[:max_tokens])
    CACHE.mkdir(parents=True, exist_ok=True)
    key.write_text(text, encoding="utf-8")
    return text or None


def _read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_rows(path: Path, rows: list[dict], fields: list[str]) -> None:
    """Rewrite the whole file sorted by date, category, query (one row per date and query)."""
    rows = sorted(rows, key=lambda r: (r["date"], r["category"], r["query"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def main() -> None:
    ap = argparse.ArgumentParser(description="Full-page tracker metrics (fixed top-K pages per query)")
    ap.add_argument("--date", default=None, help="Only this run date (default: all under raw/)")
    ap.add_argument("--top-k", type=int, default=5,
                    help="Analyse the first K readable pages in rank order; fewer = skip the query "
                         "(0 = all readable pages, methodology v1)")
    ap.add_argument("--min-results", type=int, default=3, help="Only with --top-k 0")
    ap.add_argument("--min-words", type=int, default=50, help="Pages with less text are dropped")
    ap.add_argument("--sleep", type=float, default=0.5, help="Seconds between page fetches")
    ap.add_argument("--model-cache", type=Path, default=Path("data/models"))
    ap.add_argument("--provider", choices=["none", "scraperapi", "scrapingrobot"], default="none",
                    help="Route fetches through a scraping API (works from blocked datacenter IPs)")
    ap.add_argument("--key-file", type=Path, default=None, help="Override the provider's default key file")
    ap.add_argument("--out", type=Path, default=None,
                    help="Output CSV (default runs_top<K>.csv, or runs_fullpage.csv for --top-k 0)")
    ap.add_argument("--force", action="store_true", help="Recompute (date, query) rows already present")
    ap.add_argument("--cache-only", action="store_true",
                    help="Recompute from cached pages only (no fetching, no API credits)")
    args = ap.parse_args()
    out = args.out or (LEGACY_OUT if args.top_k == 0 else Path(f"tracker/data/runs_top{args.top_k}.csv"))
    fields = FIELDS if args.top_k == 0 else FIELDS_V2
    need = args.min_results if args.top_k == 0 else args.top_k

    api_key = None
    if args.provider != "none":
        env = {"scraperapi": "SCRAPER_API_KEY", "scrapingrobot": "SCRAPING_ROBOT_API_KEY"}[args.provider]
        default_file = {"scraperapi": ".secrets/scraper_api_key.txt",
                        "scrapingrobot": ".secrets/scraping_robot_api_key.txt"}[args.provider]
        kf = args.key_file or Path(default_file)
        api_key = os.environ.get(env) or (kf.read_text(encoding="utf-8").strip() if kf.exists() else None)
        if not api_key:
            sys.exit(f"ERROR: --provider {args.provider} needs the {env} env var or {default_file}.")

    if not SERP_LOG.exists():
        sys.exit(f"{SERP_LOG} not found ? run tracker/tracker.py first")
    log = list(csv.DictReader(SERP_LOG.open(encoding="utf-8")))
    meta = {(r["date"], slugify(r["query"])): (r["query"], r["category"]) for r in log}

    dates = [args.date] if args.date else sorted({d.name for d in RAW.iterdir() if d.is_dir()})
    rows = _read_rows(out)
    done = set() if args.force else {(r["date"], r["query"]) for r in rows}

    print("Loading MiniLM (ONNX)?", flush=True)
    model = load_model(args.model_cache)
    tok = counting_tokenizer(model)
    fetched = 0

    for date in dates:
        ddir = RAW / date
        if not ddir.is_dir():
            print(f"[{date}] no raw/ dir, skipping", flush=True)
            continue
        new_rows = []
        files = sorted(ddir.glob("*.json"))
        for i, jf in enumerate(files, 1):
            slug = jf.stem
            query, category = meta.get((date, slug), (slug, "general"))
            if (date, query) in done:
                print(f"[{date} {i}/{len(files)}] skip {query!r} (done)", flush=True)
                continue
            results = json.loads(jf.read_text(encoding="utf-8"))
            results = sorted(results, key=lambda r: r.get("position") or 999)
            texts, positions = [], []
            for r in results:
                if args.top_k and len(texts) >= args.top_k:
                    break
                link = r.get("link", "")
                cached = (CACHE / (hashlib.sha1(link.encode()).hexdigest() + ".txt")).exists()
                page = fetch_page_text(link, args.provider, api_key,
                                       timeout=90 if api_key else 20,
                                       cache_only=args.cache_only) if link else None
                if link and not cached and not args.cache_only:
                    fetched += 1
                    time.sleep(args.sleep)
                if page and len(page.split()) >= args.min_words:
                    texts.append(page)
                    positions.append(r.get("position") or (len(positions) + 1))
            n = len(texts)
            if n < need:
                print(f"[{date} {i}/{len(files)}] skip {query!r}: only {n}/{len(results)} readable pages",
                      flush=True)
                continue
            v = embed_documents(model, texts, embed_texts, tok=tok)
            vendi = vendi_score(v)
            new_rows.append({
                "date": date, "category": category, "query": query,
                "n_serp": len(results), "n_results": n,
                "mean_pairwise_cosine": round(mean_pairwise_cosine(v), 6),
                "vendi": round(vendi, 4), "distinct_ratio": round(vendi / n, 4),
                "mean_marginal_novelty": round(mean_marginal_novelty(v, positions), 6),
                "positions": ";".join(str(p) for p in positions),
            })
            print(f"[{date} {i}/{len(files)}] {query!r}: pages={n}/{len(results)} "
                  f"cos={mean_pairwise_cosine(v):.3f} vendi={vendi:.2f}", flush=True)
        if new_rows:
            replaced = {(r["date"], r["query"]) for r in new_rows}
            rows = [r for r in rows if (r["date"], r["query"]) not in replaced] + new_rows
            _write_rows(out, rows, fields)

    print(f"\nDone -> {out} ({fetched} new page fetches)")


if __name__ == "__main__":
    main()
