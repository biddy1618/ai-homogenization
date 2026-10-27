"""Per-run page-text store for the tracker (texts are other sites' content: never committed).

Each run date has its own cache directory, ``tracker/data/pagecache/<date>/<sha1(url)>.txt``, so a
week only ever reuses page text fetched for that same week (a cross-week cache keyed by URL would
freeze page content at its first fetch). For safe keeping, a date is packed into one gzipped JSONL
file, ``tracker/data/pages/<date>.jsonl.gz`` (one ``{"url_sha1", "text"}`` line per page; an empty
text marks a non-HTML page), which CI stores in the private bucket at
``s3://biddy-homogenization/tracker/pages/<date>.jsonl.gz``.

    python tracker/pagestore.py pack   --date 2026-10-26   # pagecache/<date>/ -> pages/<date>.jsonl.gz
    python tracker/pagestore.py unpack --date 2026-10-26   # pages/<date>.jsonl.gz -> pagecache/<date>/
    python tracker/pagestore.py migrate                    # one-off: old flat cache -> per-date dirs
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
from pathlib import Path

CACHE = Path("tracker/data/pagecache")
PAGES = Path("tracker/data/pages")
RAW = Path("tracker/data/raw")


def cache_dir(date: str) -> Path:
    return CACHE / date


def url_key(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()


def pack(date: str) -> Path:
    src = cache_dir(date)
    files = sorted(src.glob("*.txt")) if src.is_dir() else []
    if not files:
        raise SystemExit(f"nothing to pack: {src} is empty")
    PAGES.mkdir(parents=True, exist_ok=True)
    out = PAGES / f"{date}.jsonl.gz"
    with gzip.open(out, "wt", encoding="utf-8") as f:
        for p in files:
            f.write(json.dumps({"url_sha1": p.stem, "text": p.read_text(encoding="utf-8")},
                               ensure_ascii=False) + "\n")
    print(f"packed {len(files)} pages -> {out} ({out.stat().st_size / 1e6:.2f} MB)")
    return out


def unpack(date: str) -> int:
    src = PAGES / f"{date}.jsonl.gz"
    if not src.exists():
        print(f"no {src}; starting {date} with an empty cache")
        return 0
    dst = cache_dir(date)
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(src, "rt", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            (dst / f"{d['url_sha1']}.txt").write_text(d["text"], encoding="utf-8")
            n += 1
    print(f"unpacked {n} pages -> {dst}")
    return n


def migrate() -> None:
    """Copy each flat ``pagecache/<sha1>.txt`` into every date whose results link to that URL, then
    remove the flat files. Reproduces exactly what earlier runs read (they shared one cache)."""
    flat = {p.stem: p for p in CACHE.glob("*.txt")}
    used = set()
    for ddir in sorted(d for d in RAW.iterdir() if d.is_dir()):
        n = 0
        for jf in ddir.glob("*.json"):
            for r in json.loads(jf.read_text(encoding="utf-8")):
                k = url_key(r.get("link", ""))
                if k in flat:
                    cache_dir(ddir.name).mkdir(parents=True, exist_ok=True)
                    shutil.copy2(flat[k], cache_dir(ddir.name) / flat[k].name)
                    used.add(k)
                    n += 1
        print(f"{ddir.name}: {n} pages")
    for p in flat.values():
        p.unlink()
    print(f"migrated {len(used)} of {len(flat)} flat files; {len(flat) - len(used)} unreferenced dropped")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("action", choices=["pack", "unpack", "migrate"])
    ap.add_argument("--date")
    a = ap.parse_args()
    if a.action == "migrate":
        migrate()
    elif not a.date:
        ap.error("--date is required")
    else:
        (pack if a.action == "pack" else unpack)(a.date)


if __name__ == "__main__":
    main()
