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

from paths import CORPORA, answers_parquet, questions_parquet, source_dir


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--generate-only", action="store_true")
    mode.add_argument("--analyse", action="store_true")
    ap.add_argument("--only", nargs="*", default=None, help="site folders (default: all 26)")
    ap.add_argument("rest", nargs=argparse.REMAINDER, help="-- extra args for anchor_test.py")
    args = ap.parse_args()
    extra = [a for a in args.rest if a != "--"]

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


if __name__ == "__main__":
    main()
