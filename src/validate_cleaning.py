"""Validate the text-cleaning step and the parsed corpus.

Three checks:
  1. Residue scan  — across all cleaned answers, how many still contain HTML
     tag / LaTeX math / code-fence residue (should be ~0%).
  2. Length trend  — mean & median tokens per answer per quarter (explains the
     MTLD-up / TTR-down divergence and is a finding in its own right).
  3. Spot check    — print raw-vs-cleaned pairs for a handful of answers that
     contain code and math, so the cleaning can be eyeballed.

Usage:
    python validate_cleaning.py PARQUET POSTS_XML [--samples N]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
from lxml import etree

from text_clean import clean_body

# Residue detectors. Deliberately conservative so we don't flag legitimate prose
# (e.g. a lone "<" in "x < 5" or a "$" price) as leftover markup.
HTML_TAG = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*(?:\s[^>]*)?>")
LATEX = re.compile(r"\$[^$\n]+\$|\\\(|\\\)|\\\[|\\\]|\\begin\{")
CODE_FENCE = re.compile(r"```|&lt;|&gt;|&amp;")


def residue_scan(df: pd.DataFrame) -> None:
    n = len(df)
    text = df["text"]

    html_hits = text.str.contains(HTML_TAG, regex=True)
    latex_hits = text.str.contains(LATEX, regex=True)
    code_hits = text.str.contains(CODE_FENCE, regex=True)

    print("=== 1. RESIDUE SCAN (share of cleaned answers with leftover markup) ===")
    print(f"total answers:        {n:,}")
    print(f"HTML tag residue:     {html_hits.sum():,} ({html_hits.mean():.3%})")
    print(f"LaTeX math residue:   {latex_hits.sum():,} ({latex_hits.mean():.3%})")
    print(f"HTML-entity/fence:    {code_hits.sum():,} ({code_hits.mean():.3%})")

    for label, mask in [("HTML", html_hits), ("LaTeX", latex_hits), ("ENTITY", code_hits)]:
        examples = df.loc[mask, "text"].head(3).tolist()
        if examples:
            print(f"\n  -- sample {label} residue --")
            for ex in examples:
                print(f"    {ex[:160]!r}")
    print()


def length_trend(df: pd.DataFrame) -> None:
    print("=== 2. ANSWER LENGTH TREND (tokens per answer, by quarter) ===")
    g = df.groupby("quarter")["token_count"].agg(["mean", "median", "count"])
    # Show a pre/post-ChatGPT slice.
    show = g.loc[["2018Q1", "2020Q1", "2022Q1", "2022Q4", "2023Q1",
                  "2024Q1", "2025Q1", "2026Q1"]].round(1)
    print(show.to_string())
    print()


def spot_check(posts_xml: Path, n: int) -> None:
    print(f"=== 3. SPOT CHECK — {n} raw-vs-cleaned pairs (answers with code + math) ===")
    found = 0
    context = etree.iterparse(str(posts_xml), events=("end",), tag="row")
    for _, elem in context:
        if elem.get("PostTypeId") == "2":
            raw = elem.get("Body", "")
            if "<code>" in raw and "$" in raw:
                cleaned = clean_body(raw)
                print(f"\n--- answer Id={elem.get('Id')} ({elem.get('CreationDate','')[:10]}) ---")
                print(f"RAW    : {raw[:280].replace(chr(10),' ')!r}")
                print(f"CLEANED: {cleaned[:280]!r}")
                found += 1
                if found >= n:
                    break
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate cleaning and corpus")
    ap.add_argument("parquet", type=Path)
    ap.add_argument("posts_xml", type=Path)
    ap.add_argument("--samples", type=int, default=5)
    args = ap.parse_args()

    df = pd.read_parquet(args.parquet)
    residue_scan(df)
    length_trend(df)
    spot_check(args.posts_xml, args.samples)


if __name__ == "__main__":
    main()
