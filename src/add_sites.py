"""Batch-add Stack Exchange sites and run family-5 (Sentence-BERT) on each.

Mark's ask: replicate the aggregate-similarity metric (family 5) across ~20 sites,
balanced 10 high- vs 10 low-cognitive-load. We already have 5 (stats, philosophy,
economics / cooking, travel); this driver adds the rest.

Per site, each stage is skipped if its output already exists (resumable):
  1. download  data/raw/<domain>.20260630.7z         (archive.org, curl, resumable)
  2. extract   Posts.xml (py7zr, single member) -> parse -> data/processed/<key>_answers.parquet
               (Posts.xml is deleted after parsing; the .7z is kept for cheap re-parse)
  3. family 5  semantic_bert.compute_quarterly (bootstrap CIs) ->
               artifacts/se-{hcl,lcl}/<slug>/5_semantic_bert.{csv,png} (see paths.py)

The MiniLM model is provisioned once and reused across all sites. A manifest row per
site (answers, quarters, span, recent volume) is written to artifacts/meta/sites_manifest.csv.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from parse_posts import parse_posts
from semantic_bert import EMBED_MODES, embedding_setup, load_model, compute_quarterly, plot_metrics
from embed_cache import load_cache, save_cache
from paths import meta_dir, source_dir

DUMP_BASE = ("https://archive.org/download/stackexchange_20260630/"
             "stackexchange_20260630")
DUMP_TAG = "20260630"

# (key, domain, slug, corpus display name, cognitive load)
# key -> data/processed/<key>_answers.parquet + embedding-cache tag
# slug -> artifacts/<slug>/
# Volume-weighted picks (mid/large, healthy post-2022 activity). Family 5 samples <=800
# answers/quarter, so big sites cost no more compute than small ones — only download/parse.
# Ordered mid-first so we bank reliable sites quickly, then the large ones. A volume gate
# (see main) auto-skips coffee-like thin sites so they don't add noise.
SITES: list[tuple[str, str, str, str, str]] = [
    # --- low cognitive load (everyday / practical / hobby / culture) ---
    ("bicycles", "bicycles.stackexchange.com", "bicycles", "Bicycles", "low"),
    ("gardening", "gardening.stackexchange.com", "gardening", "Gardening", "low"),
    ("rpg", "rpg.stackexchange.com", "rpg", "Role-playing Games", "low"),
    ("boardgames", "boardgames.stackexchange.com", "boardgames", "Board Games", "low"),
    ("money", "money.stackexchange.com", "money", "Personal Finance & Money", "low"),
    ("photo", "photo.stackexchange.com", "photo", "Photography", "low"),
    ("workplace", "workplace.stackexchange.com", "workplace", "The Workplace", "low"),
    ("diy", "diy.stackexchange.com", "diy", "Home Improvement", "low"),
    ("scifi", "scifi.stackexchange.com", "scifi", "Science Fiction & Fantasy", "low"),
    ("gaming", "gaming.stackexchange.com", "gaming", "Arqade (Gaming)", "low"),
    # --- high cognitive load (technical / expert) ---
    ("crypto", "crypto.stackexchange.com", "crypto", "Cryptography", "high"),
    ("law", "law.stackexchange.com", "law", "Law", "high"),
    ("history", "history.stackexchange.com", "history", "History", "high"),
    ("cs", "cs.stackexchange.com", "cs", "Computer Science", "high"),
    ("biology", "biology.stackexchange.com", "biology", "Biology", "high"),
    ("astronomy", "astronomy.stackexchange.com", "astronomy", "Astronomy", "high"),
    ("chemistry", "chemistry.stackexchange.com", "chemistry", "Chemistry", "high"),
    ("electronics", "electronics.stackexchange.com", "electronics", "Electrical Engineering", "high"),
    ("physics", "physics.stackexchange.com", "physics", "Physics", "high"),
    ("softwareengineering", "softwareengineering.stackexchange.com", "softwareengineering", "Software Engineering", "high"),
    ("english", "english.stackexchange.com", "english", "English Language & Usage", "high"),
]


def download(domain: str, raw_dir: Path) -> Path:
    """Download <domain>.7z from archive.org (resumable) unless already present."""
    out = raw_dir / f"{domain}.{DUMP_TAG}.7z"
    if out.exists() and out.stat().st_size > 0:
        print(f"  [download] cached {out.name} ({out.stat().st_size/1e6:.1f} MB)")
        return out
    raw_dir.mkdir(parents=True, exist_ok=True)
    url = f"{DUMP_BASE}/{domain}.7z"
    print(f"  [download] {url}")
    # -C - resumes a partial file; -L follows the archive.org redirect.
    cmd = ["curl.exe" if sys.platform == "win32" else "curl", "-L", "-C", "-", "--fail", "--retry", "3",
           "--max-time", "5400", "-o", str(out), url]
    subprocess.run(cmd, check=True)
    print(f"  [download] got {out.name} ({out.stat().st_size/1e6:.1f} MB)")
    return out


def ensure_parquet(archive: Path, parquet: Path) -> None:
    """Extract Posts.xml from the .7z, parse to answers parquet, drop Posts.xml."""
    if parquet.exists():
        print(f"  [parse] cached {parquet.name}")
        return
    import py7zr
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        print(f"  [parse] extracting Posts.xml from {archive.name} ...")
        with py7zr.SevenZipFile(archive, "r") as z:
            z.extract(path=str(tmp), targets=["Posts.xml"])
        posts = tmp / "Posts.xml"
        if not posts.exists():
            raise FileNotFoundError(f"Posts.xml not found inside {archive}")
        df, _ = parse_posts(posts)
    parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet, index=False)
    print(f"  [parse] wrote {len(df):,} answers -> {parquet.name}")


def recent_volume(df: pd.DataFrame, n_recent: int = 6) -> dict:
    """Coverage stats used by the volume gate: recent median quarterly answer count."""
    vc = df["quarter"].value_counts()
    quarters = sorted(vc.index)
    recent = [int(vc[q]) for q in quarters[-n_recent:]]
    return {
        "n_answers": len(df),
        "first_quarter": quarters[0] if quarters else "",
        "last_quarter": quarters[-1] if quarters else "",
        "recent_median_vol": float(pd.Series(recent).median()) if recent else 0.0,
    }


def run_family5(df: pd.DataFrame, model, key: str, slug: str, corpus: str,
                base: Path, sample: int, bootstrap: int, mode: str = "legacy") -> pd.DataFrame:
    """Family-5 semantic-BERT metrics for one corpus; returns the per-quarter frame."""
    out = source_dir(slug, base / "artifacts")
    if mode != "whole":  # 128-token results are only kept in git tag delivered-v1
        out = out / "legacy"
    csv = out / "5_semantic_bert.csv"
    plot = out / "5_semantic_bert.png"
    if csv.exists():
        print(f"  [family5] cached {csv.relative_to(base)}")
        return pd.read_csv(csv)

    emb = embedding_setup(model, mode, base / "data" / "embeddings", f"{key}_answers")
    raw_path, lc_path = emb.raw_path, emb.lc_path
    raw_cache, lc_cache = load_cache(raw_path), load_cache(lc_path)

    result = compute_quarterly(df, model, sample=sample, n_boot=bootstrap,
                               raw_cache=raw_cache, lc_cache=lc_cache, emb=emb)
    save_cache(raw_path, raw_cache)
    save_cache(lc_path, lc_cache)

    csv.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(csv, index=False)
    plot_metrics(result, plot, corpus, emb=emb)
    print(f"  [family5] wrote {csv.relative_to(base)} ({len(result)} quarters)")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Batch-add SE sites + run family 5")
    ap.add_argument("--base", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--only", nargs="*", default=None,
                    help="Restrict to these site keys (default: all)")
    ap.add_argument("--sample", type=int, default=800)
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--keep-7z", action="store_true", default=True)
    ap.add_argument("--min-recent-vol", type=float, default=40.0,
                    help="Skip family 5 if recent median quarterly volume is below this. "
                         "40 sits well above family-5's 30-answer/quarter floor and excludes "
                         "coffee-like noise (~8/qtr) without dropping healthy sites (e.g. gardening ~92)")
    ap.add_argument("--min-last-quarter", default="2026Q1",
                    help="Skip family 5 if the site has no data at/after this quarter "
                         "(aligns endpoint with existing corpora, which reach 2026Q2)")
    ap.add_argument("--embed", choices=EMBED_MODES, default="legacy",
                    help="whole = whole-text chunked embeddings -> artifacts/se-*/<slug>/")
    args = ap.parse_args()

    base = args.base
    raw_dir = base / "data" / "raw"
    proc_dir = base / "data" / "processed"
    sites = [s for s in SITES if args.only is None or s[0] in args.only]
    print(f"Processing {len(sites)} site(s): {', '.join(s[0] for s in sites)}")

    # Prefetch downloads on a background worker (network-bound) so they overlap the
    # main thread's parse+embed (CPU-bound). One worker keeps us off archive.org's
    # throttle while still racing ahead of compute. Sites with a cached parquet need
    # no download and are skipped here.
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dl")
    dl_futures: dict[str, Future] = {}
    for key, domain, slug, corpus, cog in sites:
        if not (proc_dir / f"{key}_answers.parquet").exists():
            dl_futures[key] = pool.submit(download, domain, raw_dir)

    model = load_model(base / "data" / "models")
    manifest_rows: list[dict] = []

    for key, domain, slug, corpus, cog in sites:
        print(f"\n=== {corpus} ({domain}, {cog}-cog) ===")
        parquet = proc_dir / f"{key}_answers.parquet"
        try:
            if not parquet.exists():
                fut = dl_futures.get(key)
                archive = fut.result() if fut is not None else download(domain, raw_dir)
                ensure_parquet(archive, parquet)
            df = pd.read_parquet(parquet)
            cov = recent_volume(df)
            row = {"key": key, "domain": domain, "slug": slug, "corpus": corpus,
                   "cog_load": cog, **cov}

            thin = (cov["recent_median_vol"] < args.min_recent_vol
                    or cov["last_quarter"] < args.min_last_quarter)
            if thin:
                row["status"] = "thin-skip"
                print(f"  [gate] SKIP family 5 — thin (recent median {cov['recent_median_vol']:.0f}"
                      f"/qtr, last {cov['last_quarter']}); parquet kept for reference")
                manifest_rows.append(row)
                continue

            result = run_family5(df, model, key, slug, corpus, base,
                                 args.sample, args.bootstrap, args.embed)
            row["status"] = "ok"
            row["n_quarters"] = len(result)
            row["recent_median_sample"] = (result.tail(6)["n_sample"].median()
                                           if "n_sample" in result else float("nan"))
            manifest_rows.append(row)
        except Exception as exc:  # keep the batch going if one site fails
            print(f"  !! FAILED {key}: {exc}", file=sys.stderr)
            manifest_rows.append({"key": key, "domain": domain, "slug": slug,
                                  "corpus": corpus, "cog_load": cog, "status": "error",
                                  "error": str(exc)})

    pool.shutdown(wait=True)
    man = pd.DataFrame(manifest_rows)
    if args.embed != "legacy":
        print(man.to_string(index=False))
        return
    man_path = meta_dir(base / "artifacts") / "sites_manifest.csv"
    if man_path.exists():
        prev = pd.read_csv(man_path)
        man = pd.concat([prev[~prev["key"].isin(man["key"])], man], ignore_index=True)
    man.to_csv(man_path, index=False)
    print(f"\nManifest -> {man_path}")
    with pd.option_context("display.width", 160, "display.max_columns", 20):
        print(man.to_string(index=False))


if __name__ == "__main__":
    main()
