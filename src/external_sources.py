"""Ingest EXTERNAL (non-Stack-Exchange) corpora into the same answers.parquet schema.

Each external source is harvested into one row per document with the columns the rest of
the pipeline expects (``semantic_bert.py`` / ``significance.py`` only read ``id`` / ``text`` /
``quarter``; the others mirror the SE parquets):

    id, creation_date, quarter, score, text, token_count [, parent_id]

Sources (all reachable from this machine; Reddit + HuggingFace are proxy-blocked):
  * ``hn``     Hacker News comments via the Algolia search API (fast, date-filterable,
               no auth). ``parent_id`` = the story id (a natural topic grouping).
  * ``pubmed`` PubMed abstracts via NCBI E-utilities (esearch + efetch). Scoped to one
               MeSH field so it reads like a single "community" of scientific writing.
  * ``arxiv``  arXiv abstracts via OAI-PMH (the search API's submittedDate range predicate times
               out and it rate-limits hard). We window by OAI datestamp per quarter and keep only
               papers actually CREATED that quarter, using arXiv's true <created> date.

We sample REPRESENTATIVELY across each quarter (not just newest N) so the per-quarter
pairwise-cosine is not biased toward one week. Family 5 later downsamples to <=800/quarter.

Usage (per source):
  python src/external_sources.py hn     --start 2016Q1 --end 2026Q2 --target 900
  python src/external_sources.py pubmed --start 2016Q1 --end 2026Q2 --target 900
  python src/external_sources.py arxiv  --start 2016Q1 --end 2026Q2 --target 500 --cat cs
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from text_clean import clean_body

USER_AGENT = "ai-homogenization-research/1.0 (academic; contact via repo)"


# --------------------------------------------------------------------------- helpers
def quarter_of(dt: datetime) -> str:
    return f"{dt.year}Q{(dt.month - 1) // 3 + 1}"


def quarter_bounds(q: str) -> tuple[datetime, datetime]:
    """Return [start, end) UTC datetimes for a 'YYYYQn' label."""
    year = int(q[:4])
    qn = int(q[5])
    start_month = (qn - 1) * 3 + 1
    start = datetime(year, start_month, 1, tzinfo=timezone.utc)
    if qn == 4:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, start_month + 3, 1, tzinfo=timezone.utc)
    return start, end


def quarters_range(start_q: str, end_q: str) -> list[str]:
    out, cur = [], start_q
    while cur <= end_q:
        out.append(cur)
        y, n = int(cur[:4]), int(cur[5])
        n += 1
        if n > 4:
            y, n = y + 1, 1
        cur = f"{y}Q{n}"
    return out


def http_get(url: str, timeout: int = 60, retries: int = 5) -> bytes:
    """GET with exponential backoff; honors Retry-After on 429/503 (rate limit / flow control)."""
    backoff = 3.0
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            retry_after = e.headers.get("Retry-After") if e.headers else None
            if e.code in (429, 503):
                wait = float(retry_after) if retry_after and retry_after.isdigit() else max(backoff, 20.0) * (attempt + 1)
                print(f"    {e.code}; backing off {wait:.0f}s", flush=True)
                time.sleep(wait)
                backoff *= 2
            elif 500 <= e.code < 600:
                time.sleep(backoff)
                backoff *= 2
            else:
                raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(backoff)
            backoff *= 2
    raise RuntimeError(f"GET failed after {retries} tries: {url} ({last})")


def write_parquet(rows: list[dict], out: Path, extra_cols: list[str]) -> None:
    cols = ["id", "creation_date", "quarter", "score", "text", "token_count"] + extra_cols
    df = pd.DataFrame(rows)[cols].drop_duplicates(subset="id").reset_index(drop=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"\nWrote {len(df):,} docs -> {out}")
    print(df["quarter"].value_counts().sort_index().to_string())


def make_row(doc_id: int, dt: datetime, text: str, score: int = 0,
             parent_id: int = 0) -> dict | None:
    text = clean_body(text)
    if len(text) < 20:
        return None
    return {
        "id": int(doc_id),
        "creation_date": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "quarter": quarter_of(dt),
        "score": int(score),
        "text": text,
        "token_count": len(text.split()),
        "parent_id": int(parent_id),
    }


# --------------------------------------------------------------------------- Hacker News
HN_URL = "https://hn.algolia.com/api/v1/search_by_date"


def harvest_hn(quarters: list[str], target: int, windows: int = 20,
               per_window: int = 100, min_tokens: int = 20) -> list[dict]:
    """Sample HN comments across each quarter via evenly-spaced time windows."""
    rows: list[dict] = []
    for q in quarters:
        start, end = quarter_bounds(q)
        span = (end - start).total_seconds()
        seen: set[int] = set()
        kept = 0
        for w in range(windows):
            if kept >= target:
                break
            w_start = int(start.timestamp() + span * w / windows)
            w_end = int(start.timestamp() + span * (w + 1) / windows)
            params = {
                "tags": "comment",
                "numericFilters": f"created_at_i>={w_start},created_at_i<{w_end}",
                "hitsPerPage": per_window,
                "page": 0,
            }
            url = f"{HN_URL}?{urllib.parse.urlencode(params)}"
            data = json.loads(http_get(url, timeout=30))
            for h in data.get("hits", []):
                oid = int(h["objectID"])
                if oid in seen:
                    continue
                seen.add(oid)
                dt = datetime.fromtimestamp(int(h["created_at_i"]), tz=timezone.utc)
                row = make_row(oid, dt, h.get("comment_text") or "",
                               score=0, parent_id=int(h.get("story_id") or 0))
                if row is None or row["token_count"] < min_tokens:
                    continue
                rows.append(row)
                kept += 1
            time.sleep(0.15)
        print(f"  {q}: {kept:>4} comments", flush=True)
    return rows


# --------------------------------------------------------------------------- PubMed
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _pubmed_esearch(term: str, mindate: str, maxdate: str, retmax: int,
                    retstart: int = 0) -> tuple[int, list[str]]:
    params = {
        "db": "pubmed", "term": term, "datetype": "pdat",
        "mindate": mindate, "maxdate": maxdate, "sort": "pub_date",
        "retmax": retmax, "retstart": retstart, "retmode": "json",
    }
    url = f"{EUTILS}/esearch.fcgi?{urllib.parse.urlencode(params)}"
    d = json.loads(http_get(url, timeout=45))["esearchresult"]
    return int(d.get("count", 0)), d.get("idlist", [])


def _pubmed_efetch(pmids: list[str]) -> list[dict]:
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
    url = f"{EUTILS}/efetch.fcgi?{urllib.parse.urlencode(params)}"
    root = ET.fromstring(http_get(url, timeout=90))
    out = []
    for art in root.findall(".//PubmedArticle"):
        pmid_el = art.find(".//MedlineCitation/PMID")
        if pmid_el is None:
            continue
        abstract = " ".join(
            "".join(a.itertext()) for a in art.findall(".//Abstract/AbstractText")
        ).strip()
        if not abstract:
            continue
        dt = _pubmed_date(art)
        out.append({"pmid": int(pmid_el.text), "abstract": abstract, "dt": dt})
    return out


def _pubmed_date(art: ET.Element) -> datetime | None:
    ad = art.find(".//Article/ArticleDate")
    node = ad if ad is not None else art.find(".//JournalIssue/PubDate")
    if node is None:
        return None
    y = node.findtext("Year")
    if not y:
        return None
    month_txt = node.findtext("Month") or "1"
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
              "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
    m = months.get(month_txt[:3].lower(), None)
    if m is None:
        m = int(month_txt) if month_txt.isdigit() else 1
    d = node.findtext("Day")
    try:
        return datetime(int(y), m, int(d) if d and d.isdigit() else 1, tzinfo=timezone.utc)
    except ValueError:
        return None


def harvest_pubmed(term: str, quarters: list[str], target: int,
                   subwindows: int = 9, batch: int = 200) -> list[dict]:
    """Sample PubMed abstracts across each quarter via date sub-windows (avoids the
    esearch retstart<=9998 cap and spreads the sample across the 3 months)."""
    rows: list[dict] = []
    for q in quarters:
        start, end = quarter_bounds(q)
        total, _ = _pubmed_esearch(term, start.strftime("%Y/%m/%d"),
                                   (end).strftime("%Y/%m/%d"), retmax=0)
        pmids: list[str] = []
        span = (end - start).total_seconds()
        per_sub = max(1, target // subwindows)
        for s in range(subwindows):
            s_start = start.timestamp() + span * s / subwindows
            s_end = start.timestamp() + span * (s + 1) / subwindows
            d0 = datetime.fromtimestamp(s_start, tz=timezone.utc).strftime("%Y/%m/%d")
            d1 = datetime.fromtimestamp(s_end, tz=timezone.utc).strftime("%Y/%m/%d")
            _, ids = _pubmed_esearch(term, d0, d1, retmax=per_sub)
            pmids.extend(ids)
            time.sleep(0.34)
        pmids = list(dict.fromkeys(pmids))[:target]
        kept = 0
        for i in range(0, len(pmids), batch):
            for rec in _pubmed_efetch(pmids[i:i + batch]):
                dt = rec["dt"] or start
                if not (start <= dt < end):
                    dt = start  # keep it in the queried quarter
                row = make_row(rec["pmid"], dt, rec["abstract"], score=0, parent_id=0)
                if row is not None:
                    row["quarter"] = q  # esearch pdat already bounded it
                    rows.append(row)
                    kept += 1
            time.sleep(0.34)
        print(f"  {q}: pool={total:>6}  fetched={kept:>4}", flush=True)
    return rows


# --------------------------------------------------------------------------- arXiv
# The API's submittedDate RANGE predicate times out and the API rate-limits hard (429);
# OAI-PMH is the gentle, reliable path. We window by OAI datestamp per quarter and keep only
# records actually CREATED in that quarter (new submissions), reading arXiv's true <created> date.
OAI_URL = "https://export.arxiv.org/oai2"
_OAI = "{http://www.openarchives.org/OAI/2.0/}"
_ARX = "{http://arxiv.org/OAI/arXiv/}"


def harvest_arxiv(cat: str, quarters: list[str], target: int, page_delay: float = 3.0,
                  max_pages: int = 20) -> list[dict]:
    """OAI-PMH harvest. ``cat`` is the OAI set (e.g. 'cs'); if it names a subcategory
    (e.g. 'cs.CL') we keep only records whose PRIMARY category matches."""
    set_spec = cat.split(".")[0]
    subcat = cat if "." in cat else None
    rows: list[dict] = []
    for q in quarters:
        start, end = quarter_bounds(q)
        d_from = start.strftime("%Y-%m-%d")
        d_until = (end - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        url = (f"{OAI_URL}?verb=ListRecords&metadataPrefix=arXiv&set={set_spec}"
               f"&from={d_from}&until={d_until}")
        kept, pages = 0, 0
        while pages < max_pages:
            root = ET.fromstring(http_get(url, timeout=90))
            lr = root.find(f"{_OAI}ListRecords")
            if lr is None:
                break
            for rec in lr.findall(f"{_OAI}record"):
                meta = rec.find(f"{_OAI}metadata")
                if meta is None:
                    continue  # deleted record
                arx = meta.find(f"{_ARX}arXiv")
                if arx is None:
                    continue
                created = arx.findtext(f"{_ARX}created") or ""
                try:
                    dt = datetime.strptime(created, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                if quarter_of(dt) != q:
                    continue  # re-stamped older paper, not a new submission this quarter
                cats = (arx.findtext(f"{_ARX}categories") or "").split()
                if subcat and (not cats or cats[0] != subcat):
                    continue
                num = re.sub(r"\D", "", (arx.findtext(f"{_ARX}id") or "").rsplit("/", 1)[-1])[:15] or "0"
                row = make_row(int(num), dt, arx.findtext(f"{_ARX}abstract") or "", score=0, parent_id=0)
                if row is not None:
                    rows.append(row)
                    kept += 1
            pages += 1
            if kept >= target:
                break
            token_el = lr.find(f"{_OAI}resumptionToken")
            token = (token_el.text or "").strip() if token_el is not None else ""
            if not token:
                break
            url = f"{OAI_URL}?verb=ListRecords&resumptionToken={urllib.parse.quote(token)}"
            time.sleep(page_delay)
        print(f"  {q}: {kept:>4} papers ({pages} page(s))", flush=True)
        time.sleep(page_delay)
    return rows


# --------------------------------------------------------------------------- CLI
def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest external corpora into answers.parquet")
    ap.add_argument("source", choices=["hn", "pubmed", "arxiv"])
    ap.add_argument("--start", default="2016Q1")
    ap.add_argument("--end", default="2026Q2")
    ap.add_argument("--target", type=int, default=900)
    ap.add_argument("-o", "--output", type=Path, default=None)
    ap.add_argument("--term", default="Neoplasms[Mesh] AND hasabstract",
                    help="pubmed: MeSH-scoped query defining the corpus")
    ap.add_argument("--cat", default="cs", help="arxiv: OAI set (e.g. 'cs'); 'cs.CL' also filters primary category")
    args = ap.parse_args()

    quarters = quarters_range(args.start, args.end)
    print(f"Harvesting {args.source} across {len(quarters)} quarters "
          f"{args.start}..{args.end} (target {args.target}/quarter)")

    if args.source == "hn":
        rows = harvest_hn(quarters, args.target)
        out = args.output or Path("data/processed/hackernews_answers.parquet")
    elif args.source == "pubmed":
        rows = harvest_pubmed(args.term, quarters, args.target)
        out = args.output or Path("data/processed/pubmed_onco_answers.parquet")
    else:
        rows = harvest_arxiv(args.cat, quarters, args.target)
        slug = args.cat.replace(".", "_").lower()
        out = args.output or Path(f"data/processed/arxiv_{slug}_answers.parquet")

    if not rows:
        print("No rows harvested.", file=sys.stderr)
        sys.exit(1)
    write_parquet(rows, out, extra_cols=["parent_id"])


if __name__ == "__main__":
    main()
