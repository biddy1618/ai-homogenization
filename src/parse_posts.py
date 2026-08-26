"""Stream-parse a Stack Exchange ``Posts.xml`` dump into tidy tables.

The dump is large, so we use ``lxml.etree.iterparse`` and free each element after
reading it (constant memory). We keep **answers** (``PostTypeId == 2``) since they carry
the substantive prose we want to measure. Optionally (``--questions-output``) we also emit
a **questions** table (``PostTypeId == 1``) with the title + body, which the anchor test
(family 12) uses as prompts to generate a known-AI answer per question.

Output (answers): one row per answer:
    id, parent_id, creation_date, quarter, score, text, token_count

Output (questions, optional): one row per question:
    id, creation_date, quarter, score, title, text, tags, answer_count

``parent_id`` is the question id the answer belongs to; it lets us group answers by
their shared question for the same-question topic control (family 11) and join answers to
their question text for the anchor test (family 12).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from lxml import etree
from tqdm import tqdm

from text_clean import clean_body

ANSWER_POST_TYPE = "2"
QUESTION_POST_TYPE = "1"


def _quarter(iso_date: str) -> str:
    """Map an ISO timestamp (e.g. 2023-04-17T...) to a quarter label 2023Q2."""
    year = iso_date[:4]
    month = int(iso_date[5:7])
    return f"{year}Q{(month - 1) // 3 + 1}"


def parse_posts(posts_xml: Path, min_chars: int = 1,
                want_questions: bool = False) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Parse answers (and optionally questions) from ``Posts.xml`` in a single pass."""
    rows: list[dict] = []
    q_rows: list[dict] = []

    context = etree.iterparse(str(posts_xml), events=("end",), tag="row")
    for _, elem in tqdm(context, desc="Parsing posts", unit="row"):
        ptype = elem.get("PostTypeId")
        if ptype == ANSWER_POST_TYPE:
            body = elem.get("Body", "")
            text = clean_body(body)
            if len(text) >= min_chars:
                creation = elem.get("CreationDate", "")
                rows.append(
                    {
                        "id": int(elem.get("Id")),
                        "parent_id": int(elem.get("ParentId", 0) or 0),
                        "creation_date": creation,
                        "quarter": _quarter(creation),
                        "score": int(elem.get("Score", 0)),
                        "text": text,
                        "token_count": len(text.split()),
                    }
                )
        elif want_questions and ptype == QUESTION_POST_TYPE:
            body = clean_body(elem.get("Body", ""))
            title = (elem.get("Title", "") or "").strip()
            if title or len(body) >= min_chars:
                creation = elem.get("CreationDate", "")
                q_rows.append(
                    {
                        "id": int(elem.get("Id")),
                        "creation_date": creation,
                        "quarter": _quarter(creation),
                        "score": int(elem.get("Score", 0)),
                        "title": title,
                        "text": body,
                        "tags": elem.get("Tags", "") or "",
                        "answer_count": int(elem.get("AnswerCount", 0) or 0),
                    }
                )
        # Free memory: clear the element and its now-processed siblings.
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    questions = pd.DataFrame(q_rows) if want_questions else None
    return pd.DataFrame(rows), questions


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse Posts.xml into answers.parquet")
    ap.add_argument("posts_xml", type=Path, help="Path to extracted Posts.xml")
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("data/processed/answers.parquet"),
        help="Output Parquet path (answers)",
    )
    ap.add_argument(
        "-q",
        "--questions-output",
        type=Path,
        default=None,
        help="If set, also parse questions (title+body) to this Parquet path (for the anchor test)",
    )
    args = ap.parse_args()

    df, questions = parse_posts(args.posts_xml, want_questions=args.questions_output is not None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.output, index=False)
    print(f"Wrote {len(df):,} answers -> {args.output}")
    print(df["quarter"].value_counts().sort_index().to_string())

    if questions is not None:
        args.questions_output.parent.mkdir(parents=True, exist_ok=True)
        questions.to_parquet(args.questions_output, index=False)
        print(f"Wrote {len(questions):,} questions -> {args.questions_output}")


if __name__ == "__main__":
    main()
