"""Where results live: one registry of the 30 sources and the artifacts/ layout.

    artifacts/
      summary/                 cross-source results (families 8, 9, 10, encoder comparison)
      se-hcl/<site>/           Stack Exchange, high cognitive load (14) - CSV + PNG side by side
      se-lcl/<site>/           Stack Exchange, low cognitive load (12)
      external/<source>/       non-SE corpora (4)
      robustness/bge/<source>/       second encoder (BGE-small)
      robustness/length-k/<source>/  first-K-chunks length check
      meta/                    site manifest, anchor samples

Per-source files are whole-text results (families 5-13; the opening-window control is the
``lc_*`` columns). Families 1-4 (lexical/LSA/LDA, no embeddings) exist for Cross Validated and
Philosophy. The delivered 128-token results are in git tag ``delivered-v1``.
"""
from __future__ import annotations

from pathlib import Path

ARTIFACTS = Path("artifacts")

# (folder, display label, group); group is "high" / "low" (SE cognitive load) or "external"
SE_HIGH = [
    ("cross-validated", "Cross Validated"), ("philosophy", "Philosophy"),
    ("economics", "Economics"), ("crypto", "Cryptography"), ("law", "Law"),
    ("history", "History"), ("cs", "Computer Science"), ("biology", "Biology"),
    ("astronomy", "Astronomy"), ("chemistry", "Chemistry"),
    ("electronics", "Electrical Engineering"), ("physics", "Physics"),
    ("softwareengineering", "Software Engineering"), ("english", "English Language & Usage"),
]
SE_LOW = [
    ("seasoned-advice", "Seasoned Advice"), ("travel", "Travel"), ("bicycles", "Bicycles"),
    ("gardening", "Gardening"), ("rpg", "Role-playing Games"), ("boardgames", "Board Games"),
    ("money", "Personal Finance & Money"), ("photo", "Photography"),
    ("workplace", "The Workplace"), ("diy", "Home Improvement"),
    ("scifi", "Science Fiction & Fantasy"), ("gaming", "Arqade (Gaming)"),
]
EXTERNAL = [
    ("hackernews", "Hacker News"), ("pubmed-oncology", "PubMed (Oncology)"),
    ("arxiv-cs", "arXiv (CS)"), ("arxiv-math", "arXiv (Math)"),
]
CORPORA = [(f, l, "high") for f, l in SE_HIGH] + [(f, l, "low") for f, l in SE_LOW]
EXTERNALS = [(f, l, "external") for f, l in EXTERNAL]
ALL_SOURCES = CORPORA + EXTERNALS
CORE = ["cross-validated", "philosophy", "economics", "seasoned-advice", "travel"]

GROUP_DIR = {"high": "se-hcl", "low": "se-lcl", "external": "external"}
_GROUP = {f: g for f, _, g in ALL_SOURCES}
LABEL = {f: l for f, l, _ in ALL_SOURCES}
# data/processed/<stem>.parquet where the stem is not "<folder>_answers"
_INPUT_STEM = {"cross-validated": "answers", "seasoned-advice": "cooking_answers",
               "pubmed-oncology": "pubmed_onco_answers", "arxiv-cs": "arxiv_cs_answers",
               "arxiv-math": "arxiv_math_answers"}


def answers_parquet(folder: str, processed: Path = Path("data/processed")) -> Path:
    return processed / f"{_INPUT_STEM.get(folder, folder + '_answers')}.parquet"


def questions_parquet(folder: str, processed: Path = Path("data/processed")) -> Path:
    stem = answers_parquet(folder, processed).stem
    return processed / f"{'questions' if stem == 'answers' else stem.replace('_answers', '_questions')}.parquet"


def source_dir(folder: str, root: Path = ARTIFACTS) -> Path:
    """Main (whole-text, MiniLM) results for one source; CSVs live in its ``data/`` subfolder."""
    return root / GROUP_DIR[_GROUP[folder]] / folder


def data_dir(d: Path) -> Path:
    """CSV subfolder of any results folder (plots stay in the folder itself)."""
    return d / "data"


def bge_dir(folder: str, root: Path = ARTIFACTS) -> Path:
    return root / "robustness" / "bge" / folder


def length_k_dir(folder: str, root: Path = ARTIFACTS) -> Path:
    return root / "robustness" / "length-k" / folder


def topic_k_dir(folder: str, root: Path = ARTIFACTS) -> Path:
    return root / "robustness" / "topic-k" / folder


def summary_dir(root: Path = ARTIFACTS) -> Path:
    return root / "summary"


def meta_dir(root: Path = ARTIFACTS) -> Path:
    return root / "meta"
