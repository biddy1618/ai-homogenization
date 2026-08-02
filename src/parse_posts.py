"""Stream-parse a Stack Exchange ``Posts.xml`` dump into a tidy answers table.

The dump is large, so we use ``lxml.etree.iterparse`` and free each element after
reading it (constant memory). We keep **answers** only (``PostTypeId == 2``) since
they carry the substantive prose we want to measure.

Output: a Parquet file with one row per answer:
    id, creation_date, quarter, score, text, token_count
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from lxml import etree
from tqdm import tqdm

from text_clean import clean_body

ANSWER_POST_TYPE = "2"


def _quarter(iso_date: str) -> str:
    """Map an ISO timestamp (e.g. 2023-04-17T...) to a quarter label 2023Q2."""
    year = iso_date[:4]
    month = int(iso_date[5:7])
    return f"{year}Q{(month - 1) // 3 + 1}"


def parse_posts(posts_xml: Path, min_chars: int = 1) -> pd.DataFrame:
    rows: list[dict] = []

    context = etree.iterparse(str(posts_xml), events=("end",), tag="row")
    for _, elem in tqdm(context, desc="Parsing answers", unit="row"):
        if elem.get("PostTypeId") == ANSWER_POST_TYPE:
            body = elem.get("Body", "")
            text = clean_body(body)
            if len(text) >= min_chars:
                creation = elem.get("CreationDate", "")
                rows.append(
                    {
                        "id": int(elem.get("Id")),
                        "creation_date": creation,
                        "quarter": _quarter(creation),
                        "score": int(elem.get("Score", 0)),
                        "text": text,
                        "token_count": len(text.split()),
                    }
                )
        # Free memory: clear the element and its now-processed siblings.
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse Posts.xml into answers.parquet")
    ap.add_argument("posts_xml", type=Path, help="Path to extracted Posts.xml")
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("data/processed/answers.parquet"),
        help="Output Parquet path",
    )
    args = ap.parse_args()

    df = parse_posts(args.posts_xml)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.output, index=False)
    print(f"Wrote {len(df):,} answers -> {args.output}")
    print(df["quarter"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
