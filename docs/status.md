# Project Status — AI Homogenization

*Running "what's done / current state / open threads" tracker. Newest state at top.*
*Last updated: 2026-08-27 (anchor test done; pre Aug-27 call with Mark).*

---

## One-liner

Measuring whether generative AI (ChatGPT, public 2022Q4) made online writing more
homogeneous. Method: per-quarter diversity metrics on Stack Exchange answers, five metric
families, raw **and** length-controlled, replicated across two corpora.

## Corpora (5, from the latest SE dump `20260630`, data through 2026Q2)

| Corpus | Cog-load | Answers | Parquet |
|---|---|---|---|
| Cross Validated (stats.SE) | high | ~219k | `data/processed/answers.parquet` |
| Philosophy SE | high | ~68k | `data/processed/philosophy_answers.parquet` |
| Economics SE | high | ~20k | `data/processed/economics_answers.parquet` |
| Seasoned Advice (cooking) | low | ~66k | `data/processed/cooking_answers.parquet` |
| Travel SE | low | ~80k | `data/processed/travel_answers.parquet` |

ChatGPT marker: 2022Q4. All parquets now carry `parent_id` (enables family 11). `data/` is
gitignored; committed outputs live in `artifacts/<corpus>/{data,plots}/` (+ consolidated `artifacts/*_all.csv`).

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
| 8 | **Significance / ITS** (segmented regression + Mann-Kendall + bootstrap) | `significance.py` | ✅ done | Post-ChatGPT rise is a significant **slope-change** in well-powered corpora — but see families 6/10/11 (`8_significance`, `8_its`) |
| 9 | High- vs low-**cognitive-load** comparison | `cog_load_compare.py` | ✅ done | Rise is **widespread (4/5 sites)**, NOT a clean high/low split (low-cog Travel also rises) — no cog-load explanation (`9_cog_load_comparison`) |
| 10 | Overall vs within-topic **MK-post** test | `within_vs_overall.py` | ✅ done | Within-topic MK-post **ns in all 5** while aggregate rises → topic-composition (`10_within_vs_overall`) |
| 11 | **Same-question** topic control (`ParentId`) — gold standard | `same_question.py` | ✅ done | Field-standard control, **zero dropped outliers**: 4/5 corpora show **no** within-question rise → composition; **Philosophy** is the lone exception (within-Q MK-post p=0.0002) (`11_same_question`) |
| 12 | **GPT-anchor** drift (do humans drift toward ChatGPT's own answer?) — client item 4 | `anchor_test.py` | ✅ done | Most literal test of the client's question. Sampled 25 human answers/qtr vs 1 gpt-4o-mini answer/question. Human-vs-AI cosine **flat in 4/5** (CV slightly *down*, Philosophy/Seasoned Advice/Travel MK-post ns); **Economics** is the lone rise (MK-post τ+0.43 p=0.027) — smallest/noisiest site. The two lone exceptions (Philosophy in #11, Economics in #12) are *different* sites → noise, not corroboration (`12_anchor_drift`) |

## Headline finding (current)

- The "AI homogenized writing" claim is **not supported**. The big surface convergence is a
  length artifact (answers got longer); it vanishes under length control and never appears in
  Philosophy (already verbose).
- The **only** surviving signal — a small recent (2023Q4→2026Q2) rise in contextual-embedding
  similarity — **largely disappears once topic is held constant** (families 6/10, and now the
  gold-standard **same-question** control family 11). So most of it is a shift in *what people
  write about* after 2023, not homogenization of *style*. Replicated across **5 corpora**.
- The **ITS slope-change** (family 8) is statistically significant in 4/5 sites — but that is on
  the *aggregate* metric; the direct topic-held-constant tests (6/10/11/12) attribute the bend to
  topic mix, not style. Significant ≠ homogenization.
- The **GPT-anchor test** (family 12, the most literal version of the client's question) is
  **flat in 4/5**; only Economics (smallest/noisiest) rises. The two lone exceptions
  (Philosophy in #11, Economics in #12) fall on *different* sites and don't corroborate → noise.
- Honest one-liner for the client: *"Writing did not broadly homogenize; the small recent
  uptick is mostly a topic-mix effect, not AI-driven style convergence — worth monitoring, not
  a finding to claim."*

## Deliverables / docs

**Current (main tree):**
- `docs/status.md` — this running status tracker.
- `docs/research/critical-review.md` — self-critique of the findings (updated with the within-topic result).
- `docs/research/next-steps.md` — forward roadmap (P1–P5).
- `docs/research/oral-briefing.md` — voice-assistant practice script (pitch, Q&A bank, glossary).
- `docs/research/short-brief.md` — dense one-pager: today's two direct tests (#11, #12) + the ITS caveat + big picture.
- `docs/research/homogenization-metrics-literature.md` — how the field measures homogenization + the 4 orthogonal metrics to add (perplexity/compression/n-gram/Vendi), after the anchor test.
- `docs/meetings.md` — client meeting log + action items.

**Archived (`docs/archived/`, see its `INDEX.md`):** Week-1 platform research
(`platforms-assessment.md`, `data-sources-{high,low}-cog.md`, `prototype-candidates.md`),
metric background (`metrics.md`, `metrics-recommendation.md`), the superseded
`next-metrics.md`, and `workplan.md`.

## Open threads / next actions (see next-steps.md for detail)

*Client items 1–3 from the 2026-08-20 call are now **done**; the agreed next sequence is the
GPT-generated-answer anchor test (item 4), then the orthogonal-metrics research.*

- **[done] Expand to 2+ more sites** — added Economics, Seasoned Advice, Travel (5 corpora total).
- **[done] High- vs low-cognitive-load comparison** — family 9: rise is widespread, no clean split.
- **[done] Statistical significance** — family 8 ITS/Mann-Kendall + bootstrap; plus families 10/11
  showing the aggregate rise is topic-composition once topic is held constant.
- **[done — client item 4] GPT-generated-answer anchor test** — family 12: generated gpt-4o-mini
  answers per question, measured whether human answers drift toward the AI answer over time.
  Flat in 4/5 (Economics lone rise, smallest/noisiest); does not corroborate the Philosophy #11
  exception. Most literal test of the client's question → no drift toward the AI.
- **[NEXT] Orthogonal-metrics research (the 4 points)** — predictability (distilgpt2-ONNX /
  n-gram perplexity), compression ratio, n-gram diversity, Vendi Score; for convergent validity.
  See `docs/research/homogenization-metrics-literature.md`.
- **Deferred:** P2b tenure (needs `OwnerUserId` parsing); per-tag trends (needs `Tags` parsing);
  reduce HDBSCAN outliers; second encoder; probe the Philosophy within-question exception.

## Pending action items (from meetings.md)

- Check whether companies object to data usage for research.
- Review papers for data-sharing / referencing best practices.
