# Project Status — AI Homogenization

*Running "what's done / current state / open threads" tracker. Newest state at top.*
*Last updated: 2026-08-21 (after the 2026-08-20 client call).*

---

## One-liner

Measuring whether generative AI (ChatGPT, public 2022Q4) made online writing more
homogeneous. Method: per-quarter diversity metrics on Stack Exchange answers, five metric
families, raw **and** length-controlled, replicated across two corpora.

## Corpora (both from the 2026-03-31 SE dump, data through 2026Q1)

| Corpus | Answers | Quarters | Parquet |
|---|---|---|---|
| Cross Validated (stats.SE) | ~219k | 63 (2010Q3–2026Q1) | `data/processed/answers.parquet` |
| Philosophy SE | 66,551 | 60 (2011Q2–2026Q1) | `data/processed/philosophy_answers.parquet` |

ChatGPT marker: 2022Q4. `data/` is gitignored; committed outputs live in `artifacts/<corpus>/{data,plots}/`.

## Metric families — status

| # | Family | Code | Status | Result (both corpora unless noted) |
|---|---|---|---|---|
| 1 | Lexical / surface (TTR, MTLD, Yule, HD-D, MATTR) | `metrics.py`, `pipeline.py` | ✅ done | Length-controlled: **flat**, no ChatGPT step |
| 2 | Length-control window sweep | `lc_sensitivity.py` | ✅ done | Null is robust to 50/100/150/200-token windows |
| 3 | LSA semantic (TF-IDF→SVD cosine, centroid var, eff. dim) | `semantic.py` | ✅ done | Raw rise is a **length artifact**; flat under length control |
| 4 | LDA topics + pre/post JSD | `topics.py` | ✅ done | JSD ≈ 0.008–0.009 (topic mix ≈ unchanged) |
| 5 | Sentence-BERT/MiniLM (cosine, centroid var, eff. dim) | `semantic_bert.py` | ✅ done | Small **length-robust convergence 2023Q4–2026Q1** (the one live signal); **bootstrap 95% CIs** (2026-08-20): recent rise CI-separated from the 2016–22 trough — CV stays below early-history, Philosophy reaches series highs |
| 6 | Dynamic BERTopic + **within-topic** similarity | `topics_bert.py` | ✅ done | Within-topic cosine **flat-to-declining** → signal is mostly topic-composition; holds under length control (`6c`, 2026-08-20); 95% bootstrap CI bands added, within-topic band brackets a flat line (2026-08-20) |
| 7 | Homogenization by **answer score** (within-quarter median split) | `segment_score.py` | ✅ done | Recent uptick is **broad-based across quality tiers**, NOT concentrated in low-score answers — argues against a low-effort/templated mechanism (`7_score_segments`, 2026-08-20) |

## Headline finding (current)

- The "AI homogenized writing" claim is **not supported**. The big surface convergence is a
  length artifact (answers got longer); it vanishes under length control and never appears in
  Philosophy (already verbose).
- The **only** surviving signal — a small recent (2023Q4→2026Q1) rise in contextual-embedding
  similarity — **largely disappears once topic is held constant** (family 6). So most of it is
  a shift in *what people write about* after 2023, not homogenization of *style*.
- Honest one-liner for the client: *"Writing did not broadly homogenize; the small recent
  uptick is mostly a topic-mix effect, not AI-driven style convergence — worth monitoring, not
  a finding to claim."*

## Deliverables / docs

**Current (main tree):**
- `docs/status.md` — this running status tracker.
- `docs/research/critical-review.md` — self-critique of the findings (updated with the within-topic result).
- `docs/research/next-steps.md` — forward roadmap (P1–P5).
- `docs/research/oral-briefing.md` — voice-assistant practice script (pitch, Q&A bank, glossary).
- `docs/meetings.md` — client meeting log + action items.

**Archived (`docs/archived/`, see its `INDEX.md`):** Week-1 platform research
(`platforms-assessment.md`, `data-sources-{high,low}-cog.md`, `prototype-candidates.md`),
metric background (`metrics.md`, `metrics-recommendation.md`), the superseded
`next-metrics.md`, and `workplan.md`.

## Open threads / next actions (see next-steps.md for detail)

*Post 2026-08-20 client call — Mark's steer: broaden the site coverage, add significance, and
compare homogenization by cognitive load. Client-agreed priorities first, then leftovers.*

- **[client] Expand to 2+ more sites** — repeat the semantic pairwise-cosine analysis beyond
  Cross Validated + Philosophy (P5; more Stack Exchange sites are low-friction drop-ins).
- **[client] High- vs low-cognitive-load comparison** — bucket sources (high: Stack Exchange;
  low: Twitter / Reddit / Yelp / TripAdvisor / Goodreads / movie reviews) and compare the degree
  of homogenization between buckets. NEW cross-corpus framing, and Mark's headline ask.
- **[client] Statistical significance of the increase** — per-site significance + a formal
  change-point / interrupted-time-series test around 2022Q4/2023Q4 (P3; bootstrap CIs already done).
- **[client] Older-GPT generated-text comparison** — greenlit: generate replies with an early GPT
  and measure similarity / drift toward the AI centroid (P4 known-AI anchor).
- **Done (Bucket A, pre-call):** P1 length-controlled within-topic (flat), P2a score segmentation
  (broad-based across tiers), P3 bootstrap CIs (families 5/6/7).
- **Still open / deferred:** P2b tenure (blocked — `answers.parquet` lacks `OwnerUserId`); per-tag
  trends (needs `Tags`+`ParentId` parsing); reduce ~52–55% HDBSCAN outliers; second encoder (P4b);
  perplexity / burstiness (P6).

## Pending action items (from meetings.md)

- Check whether companies object to data usage for research.
- Review papers for data-sharing / referencing best practices.
