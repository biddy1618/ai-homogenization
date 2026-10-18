"""Extract the questions table (title, body, tags) for Stack Exchange sites from their dumps.

The 21 expansion sites were parsed for answers only. Topic controls by tag (and the anchor
test) need each answer's question, so this re-reads ``data/raw/<domain>.20260630.7z`` (fetch
with ``python src/sync_data.py pull raw``) and writes ``data/processed/<key>_questions.parquet``.

    python src/parse_questions.py                 # all expansion sites missing a questions file
    python src/parse_questions.py --only crypto law --delete-7z
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from add_sites import DUMP_TAG, SITES
from parse_posts import parse_posts

ROOT = Path(__file__).resolve().parents[1]


def extract_questions(archive: Path, out: Path) -> int:
    import py7zr

    with tempfile.TemporaryDirectory() as td:
        with py7zr.SevenZipFile(archive, "r") as z:
            z.extract(path=td, targets=["Posts.xml"])
        _, questions = parse_posts(Path(td) / "Posts.xml", want_questions=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    questions.to_parquet(out, index=False)
    return len(questions)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", default=None, help="site keys (default: all expansion sites)")
    ap.add_argument("--force", action="store_true", help="re-parse even if the questions file exists")
    ap.add_argument("--delete-7z", action="store_true", help="remove each dump after a successful parse")
    args = ap.parse_args()

    raw, proc = ROOT / "data" / "raw", ROOT / "data" / "processed"
    for key, domain, *_ in SITES:
        if args.only and key not in args.only:
            continue
        out = proc / f"{key}_questions.parquet"
        if out.exists() and not args.force:
            print(f"{key}: exists, skip")
            continue
        archive = raw / f"{domain}.{DUMP_TAG}.7z"
        if not archive.exists():
            print(f"{key}: MISSING {archive.name} (run: python src/sync_data.py pull raw)")
            continue
        n = extract_questions(archive, out)
        print(f"{key}: {n:,} questions -> {out.name}")
        if args.delete_7z:
            archive.unlink()


if __name__ == "__main__":
    main()
