# Project Status — AI Homogenization

*Running "what's done / current state / open threads" tracker. Newest state at top.*
*Last updated: 2026-08-12.*

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
| 5 | Sentence-BERT/MiniLM (cosine, centroid var, eff. dim) | `semantic_bert.py` | ✅ done | Small **length-robust convergence 2023Q4–2026Q1** (the one live signal) |
| 6 | Dynamic BERTopic + **within-topic** similarity | `topics_bert.py` | ✅ done | Within-topic cosine **flat-to-declining** → signal is mostly topic-composition |

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

- **P1** Length-controlled within-topic similarity (this run used raw embeddings) — closes the
  main caveat, cheap, decisive.
- **P2** Per-tag / per-topic trends — NOTE: needs a parsing change (answers carry no tags; must
  parse questions' `Tags` + join on `ParentId`).
- **P3** Bootstrap CIs + change-point test; reduce the ~52–55% HDBSCAN outliers.
- **P4** Second encoder + known-AI anchor. **P5** Third natural-prose corpus.

## Pending action items (from meetings.md)

- Check whether companies object to data usage for research.
- Review papers for data-sharing / referencing best practices.
