"""Run family 12 (GPT anchor) over every Stack Exchange site.

    python src/run_anchor.py --generate-only            # Mac: generate GPT answers only
    python src/run_anchor.py --analyse                  # this PC: embed + analyse cached answers
    python src/run_anchor.py --generate-only --only economics travel

Extra arguments after ``--`` go to anchor_test.py (e.g. ``-- --concurrency 32``).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from paths import CORPORA, answers_parquet, questions_parquet, source_dir, summary_dir


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--generate-only", action="store_true")
    mode.add_argument("--analyse", action="store_true")
    mode.add_argument("--summarize", action="store_true",
                      help="only build artifacts/summary/data/12_anchor_all.csv from per-site results")
    ap.add_argument("--only", nargs="*", default=None, help="site folders (default: all 26)")
    ap.add_argument("rest", nargs=argparse.REMAINDER, help="-- extra args for anchor_test.py")
    args = ap.parse_args()
    extra = [a for a in args.rest if a != "--"]
    if args.summarize:
        summarize()
        return

    script = Path(__file__).with_name("anchor_test.py")
    for folder, label, _ in CORPORA:
        if args.only and folder not in args.only:
            continue
        cmd = [sys.executable, str(script), "-i", str(answers_parquet(folder)),
               "-Q", str(questions_parquet(folder)), "--corpus", label,
               "--out-dir", str(source_dir(folder))]
        cmd += ["--generate-only"] if args.generate_only else ["--no-generate"]
        print(f"\n=== {label} ===", flush=True)
        subprocess.run(cmd + extra, check=False)
    if args.analyse:
        summarize()


def summarize() -> None:
    """All sites' family-12 significance rows -> one table + high/low counts."""
    import pandas as pd

    rows = []
    for folder, label, cog in CORPORA:
        f = source_dir(folder) / "data" / "12_anchor_significance.csv"
        if f.exists():
            rows.append(pd.read_csv(f).assign(corpus=label, cog_load=cog))
    if not rows:
        print("no family-12 results yet")
        return
    out = pd.concat(rows, ignore_index=True)
    dest = summary_dir() / "data" / "12_anchor_all.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest, index=False)
    for m in ("ai_match_cosine", "lc_ai_match_cosine", "pull", "lc_pull"):
        d = out[out["metric"] == m]
        parts = []
        for cog in ("high", "low"):
            s = d[d["cog_load"] == cog]
            up = int(((s["slope_change"] > 0) & (s["slope_change_p"] < 0.05)).sum())
            dn = int(((s["slope_change"] < 0) & (s["slope_change_p"] < 0.05)).sum())
            parts.append(f"{cog} {up} up / {dn} down of {len(s)}")
        print(f"{m:<20} " + " | ".join(parts))
    print(f"Wrote -> {dest}")


if __name__ == "__main__":
    main()
