# Project Status — AI Homogenization

*Running "what's done / current state / open threads" tracker. Newest state at top.*

## Current state (2026-10-16)

**Whole-text replication done (Steps 0–6); paper update next.** The MiniLM embedding model reads only the first 128 tokens
(~100 words) of each text, so every delivered embedding result (families 5–13) describes how answers
*open*. Families 1–4 are unaffected. All embedding families were re-run on whole text (cleaned
of URLs/machine strings, split into sentence chunks, chunk vectors averaged), with an exact
opening-window control (first 120 model tokens). **Artifacts layout (2026-10-16):** `artifacts/`
holds whole-text results only — `summary/`, `se-hcl/<site>/`, `se-lcl/<site>/`, `external/<source>/`,
`robustness/{bge,length-k}/`, `meta/` (map: `artifacts/README.md`; registry: `src/paths.py`). The
delivered 128-token results were removed from the tree; they are in git tag `delivered-v1`
(`git checkout delivered-v1 -- artifacts`), and what Mark received is in `deliverables/`.

| Step | What | State |
|---|---|---|
| 0–1 | Shared chunked embedding (`src/chunk_embed.py`), `--embed whole` in every script | done |
| 2 | Decision gate: families 5 + 8, core 5 + 4 externals | **done — passed**: change holds wherever it was significant; whole text stronger in CV, Econ, Philosophy, PubMed (partly length: up-to-K check) |
| 3 | Families 5 + 8 on the other 21 SE sites, 26-site summary, cognitive load (9) | **done**: 15/26 significant on whole text (opening window 19/26; delivered 18/26); 24/26 move up; high-load 11/14 vs low-load 4/12 (needs a proper family-9 read) |
| 4 | Topic controls: same-question (11), decomposition (13), BERTopic (6), within vs overall (10) | **done**: same-question 0/5 converge; topic narrowing 8/9; within-topic rises 8/9 on whole text but only Philosophy/Economics/Travel under the opening window |
| 5 | Score segments (7), GPT anchor (12, cached GPT answers only) | **done** (outputs not yet committed): both score tiers rise; anchor Economics positive, Seasoned Advice borderline, 3 null |
| 5b | Local DuckDB store: runs, sampled answers, embeddings keyed by model/variant/text hash, metrics (one gitignored file; imports existing caches) | **embeddings done (2026-10-15)**: all 116 `.npz` caches → `data/embeddings/embeddings.duckdb` (float32 BLOB, 6.0 GB vs 11.6 GB; Economics family 5 reproduces to ≤5e-8). Same `embed_cache` API, no script changes. Runs/samples/metrics tables not built yet |
| 5c | Data sharing with the Mac: private S3 `s3://biddy-homogenization` (us-west-2) via `src/sync_data.py` (`push` / `pull` / `status`, targets `raw` and `embeddings`; keys in `.secrets/`) | **done**: 26 June-2026 dumps (5.7 GB) + embeddings DB uploaded and verified; local copies of dumps removed; unused March/undated dumps and `Posts.xml` extracts deleted. Run `pull raw` before re-parsing a site |
| 6 | Second encoder (BGE-small) on core 5 + externals | **done (2026-10-16)**: `semantic_bert.py --encoder bge-small` (same 120-token chunking; only the encoder changes) → `artifacts/robustness/bge/<source>/`; comparison `artifacts/summary/6_encoder_compare.csv` (`src/encoder_compare.py`). Verdict agrees 6/9 whole text, 7/9 opening window. Holds with both encoders: CV, Economics, HN, arXiv Math, arXiv CS, PubMed (all p<0.001, both metrics); Philosophy opening window. **Does not hold with BGE**: Travel (MiniLM up*, BGE flat/down), Philosophy whole text (up, p=0.17), Seasoned Advice (MiniLM flat, BGE down*). BGE similarity *levels* are much higher (~0.67 vs ~0.16), so compare slope changes, not levels |
| 6b | Family 9 formal test (high vs low load, 26 SE sites; `src/cog_load_test.py` → `artifacts/summary/9_cog_load_{test,sites}.csv`) + tracker check | **done (2026-10-16)**. Whole text: high-load turns up more — significant 11/14 vs 4/12 (Fisher p=0.026, same after BH), median slope change in pre-SD units 0.20 vs 0.09 (Mann–Whitney p=0.010, permutation p=0.010); holds controlling for site answer length (p=0.026). Opening window: more high-load sites significant (13/14 vs 6/12, p=0.021) but effect sizes similar (p=0.06–0.15). Delivered results: no clear split (p=0.06–0.25), as reported. Tracker already uses whole-page chunking; recompute from the page cache is identical. **Plots (2026-10-16):** `artifacts/summary/8_significance_all.png` now covers all 30 sources (`significance.py --all`; SE 15/26, external 4/4); `9_cog_load_test.png` (per-site dot/box plot with the tests); per-source `8_its.png` (main and BGE) relabelled "whole text" / "opening window" |
| 7–8 | Claims ledger + conclusions review; paper v0.2; reply to Mark (next meeting Thu 2026-10-22) | |

### To discuss (framing; decide before the paper rewrite)
1. **Wording of the aggregate result — agreed: "the long decline turned upward", not "rose".** The
   test is a change in slope at 2022Q4. Of the 18/26 significant sites, 16 were *declining* before
   ChatGPT; 11 show a significant upward trend after it; 9 have a significantly higher post-ChatGPT
   average. Corrected for testing 26 sites (Benjamini–Hochberg), 17/26 remain significant.
2. **arXiv mathematics as a "low-AI control" — dropped as a control.** It shows the same turn-upward
   as the AI-heavy fields, "low-AI" was never defined, and a field whose subject isn't AI can still
   use AI to write. Keep it as a 4th external corpus. Open: is any defensible control corpus
   possible, or do we drop the control framing altogether?
3. **"Topic composition, not style" needs re-testing.** The committed family-10 summary
   (`artifacts/10_within_vs_overall.csv`) was generated from an older family-6 run and did not
   reproduce. Regenerated from the committed inputs: Cross Validated's within-topic similarity does
   rise after ChatGPT (Mann–Kendall p=0.016, was 0.28), and the within-topic slope also turns upward
   in Philosophy, Travel and Hacker News. Externals now included; their paper values reproduce
   exactly. Step 4 (whole text) decides how this claim is worded.
4. **Paper methodology** must disclose the 128-token window and describe the whole-text method.

**Docs map:** [research/project-briefing.md](research/project-briefing.md) (entry point),
[../paper/main.tex](../paper/main.tex) (the paper), [../tracker/README.md](../tracker/README.md)
(tracker), [meetings.md](meetings.md). The markdown paper draft and the old tracker plan are in
[archived/](archived/INDEX.md).

---

*Below: state as of 2026-09-26 (delivered, opening-window results). Superseded where the Current
state block above says so.*
*Last updated: 2026-09-26 (topic control now run on all 3 externals — within-topic **flat** under
BERTopic, matching SE; paper DRAFT v0.1 written; live tracker built and running weekly on GitHub
Actions, first 45-query snapshot committed).*
*Prev: 2026-09-14 (3 external corpora landed — HN, PubMed, arXiv-CS; Mark opened two new
workstreams: an academic paper and a live homogenization tracker over Google search results).*

---

## One-liner

Measuring whether generative AI (ChatGPT, public 2022Q4) made online writing more
homogeneous. Method: per-quarter diversity/similarity metrics with a layered battery of
controls (length, topic, significance, a known-AI anchor) — **13 metric families**, replicated
across **26 Stack Exchange communities + 3 external non-SE corpora** (Hacker News, PubMed
oncology, arXiv CS). Honest headline: **not broad *style* homogenization, but real *topic-level*
homogenization** — the rise is mostly in *what* people write about, not *how*.

## Corpora (26, from the latest SE dump `20260630`, data through 2026Q2)

**Core 5** (full family 1–12 analysis; parquets carry `parent_id`):

| Corpus | Cog-load | Answers | Parquet |
|---|---|---|---|
| Cross Validated (stats.SE) | high | ~219k | `data/processed/answers.parquet` |
| Philosophy SE | high | ~68k | `data/processed/philosophy_answers.parquet` |
| Economics SE | high | ~20k | `data/processed/economics_answers.parquet` |
| Seasoned Advice (cooking) | low | ~66k | `data/processed/cooking_answers.parquet` |
| Travel SE | low | ~80k | `data/processed/travel_answers.parquet` |

**+21 expansion sites** (2026-09-07, via `add_sites.py`; families 5 + 8/9 only): **high-cog** —
Cryptography, Law, History, Computer Science, Biology, Astronomy, Chemistry, Electrical
Engineering, Physics, Software Engineering, English L&U; **low-cog** — Bicycles, Gardening, RPG,
Board Games, Personal Finance & Money, Photography, The Workplace, Home Improvement, Sci-Fi &
Fantasy, Arqade (Gaming). Volume+timeframe gated (all end 2026Q2, recent median ≥40/qtr); manifest
in `artifacts/meta/sites_manifest.csv`. **26 corpora total: 14 high-cog + 12 low-cog.**

ChatGPT marker: 2022Q4. All core parquets carry `parent_id` (enables family 11). `data/` is
gitignored; committed outputs live in `artifacts/` (layout in the Current state block above).

**+4 external, non-SE corpora** (HN, PubMed, arXiv-CS on 2026-09-13; arXiv mathematics on
2026-10-13; via `external_sources.py`; families 5, 6, 8, 13):

| Corpus | Cog-load | Docs | Timeframe | Unit | Harvester |
|---|---|---|---|---|---|
| Hacker News | high | ~39k | 2016Q1–2026Q2 (42q) | comments | Algolia `search_by_date` |
| PubMed (oncology) | high | ~34k | 2016Q1–2026Q2 (42q) | abstracts | eutils esearch/efetch |
| arXiv (Computer Science) | high | ~64k | 2016Q1–2026Q2 (42q) | abstracts | OAI-PMH `set=cs` |

All three **replicate the significant post-ChatGPT aggregate rise** and it **survives length
control**: HN slope-change +0.00101/qtr (p=4.5e-9), PubMed +0.00080 (p=9e-4), arXiv-CS +0.00105
(p=0.0014). **HN is the cleanest** (flat before, sharp rise after); PubMed and arXiv-CS both had a
significant *pre-trend* (the change is an acceleration, not a clean break). ✅ **Topic control now
run on all 3 externals (2026-09-26)** — families 6 (BERTopic) + 13 (decomposition): within-topic is
**flat** under BERTopic in all three (HN's K-means within-topic bump did **not** survive BERTopic), so
the rise is **topic-composition**, matching SE. Committed `d4e626f` (harvest) + `23b7a8d` (topic control).

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
| 8 | **Significance / ITS** (segmented regression + Mann-Kendall + bootstrap) | `significance.py` | ✅ done | `--all` mode runs all **26 corpora** → `8_significance_all.csv` + forest summary (`8_significance_all.png`) + per-corpus ITS plots (`8_its`). **18/26 show a significant post-ChatGPT slope-increase** (20/26 under length control) — but see families 6/10/11: significant ≠ *style* homogenization (it's topic-level) |
| 9 | High- vs low-**cognitive-load** comparison | `cog_load_compare.py` | ✅ done | Now across all **26 corpora** with a readable high/low **bucket-mean ±1SE** plot (faint per-site lines behind). High- and low-cog tracks **overlap** → cognitive load does not explain the rise; confirms "no clean split" at scale (`9_cog_load_comparison`) |
| 10 | Overall vs within-topic **MK-post** test | `within_vs_overall.py` | ✅ done | Within-topic MK-post **ns in all 5** while aggregate rises → topic-composition (`10_within_vs_overall`) |
| 11 | **Same-question** topic control (`ParentId`) — gold standard | `same_question.py` | ✅ done | Field-standard control, **zero dropped outliers**: 4/5 corpora show **no** within-question rise → composition; **Philosophy** is the lone exception (within-Q MK-post p=0.0002) (`11_same_question`) |
| 12 | **GPT-anchor** drift (do humans drift toward ChatGPT's own answer?) — client item 4 | `anchor_test.py` | ✅ done | Most literal test of the client's question. Sampled 25 human answers/qtr vs 1 gpt-4o-mini answer/question. Human-vs-AI cosine **flat in 4/5** (CV slightly *down*, Philosophy/Seasoned Advice/Travel MK-post ns); **Economics** is the lone rise (MK-post τ+0.43 p=0.027) — smallest/noisiest site. The two lone exceptions (Philosophy in #11, Economics in #12) are *different* sites → noise, not corroboration (`12_anchor_drift`) |
| 13 | **Within- vs between-topic decomposition** (global K-means, K=50, no dropped outliers) | `topic_decomposition.py` | ✅ done (core 5) | Positively locates the rise: it lives in **between-topic** pairs (≈ overall); **within-topic is weak/flat**. **Effective # of topics drops** + **composition JSD rises** after ChatGPT → topic-level homogenization. The between-topic "convergence" is mostly **anisotropy** (mean-centred `mc_between` line flat) (`13_topic_decomposition`) |

## Headline finding (current)

- **We do not conclude "no homogenization."** The strong popular claim — that AI homogenized
  *writing style* ("everyone sounds like ChatGPT") — is **not supported**; but there **is** real
  **topic-level** homogenization (see below). The big surface convergence is a length artifact
  (answers got longer); it vanishes under length control and never appears in Philosophy (already
  verbose).
- The surviving signal — a small recent (2023Q4→2026Q2) rise in contextual-embedding
  similarity — **largely disappears once topic is held constant** (families 6/10, the
  gold-standard **same-question** control family 11, and the decomposition family 13). So most of
  it is a shift in *what people write about* after 2023, not homogenization of *style*. Replicated
  across the **core 5 SE corpora** and, via topic control (families 6 + 13), **all 3 external
  corpora** (within-topic flat under BERTopic in HN/PubMed/arXiv).
- **Positively confirmed (family 13, core 5):** decomposing the aggregate cosine, the rise lives in
  **between-topic** pairs while **within-topic is flat**, and **topic diversity shrinks** +
  **composition drifts** after ChatGPT. So the mechanism is topic-level (what people write about),
  matching Mark's "AI homogenises *topics*, not within-topic *style*" framing — though the
  "topics converging" piece is mostly an embedding-anisotropy artifact.
- The **ITS slope-change** (family 8) is now significant in **18/26 sites** (20/26 under length
  control) — a broad, modest, cognitive-load-independent rise — but that is on the *aggregate*
  metric; the direct topic-held-constant tests (6/10/11/12, on the core 5) attribute the bend to
  topic mix, not style. Significant ≠ *style* homogenization.
- The **GPT-anchor test** (family 12, the most literal version of the client's question) is
  **flat in 4/5**; only Economics (smallest/noisiest) rises. The two lone exceptions
  (Philosophy in #11, Economics in #12) fall on *different* sites and don't corroborate → noise.
- Honest one-liner for the client: *"No broad **style** homogenization, but real **topic-level**
  homogenization — the convergence is mostly in *what* people write about, not *how*. A real (if
  subtler) effect worth monitoring, not a null result."* (Matches `project-briefing.md` and
  `paper-draft.md`; we do **not** claim "no homogenization.")

## Deliverables / docs

**Current (main tree):**
- `docs/status.md` — this running status tracker.
- `docs/research/project-briefing.md` — **whole-project anchor** (what/why/findings/paper/tracker + glossary + Q&A bank); read-cold reference.
- `paper/main.tex` (+ `main.pdf`) — the paper (LaTeX).
- `tracker/README.md` — the live tracker (pipeline, metrics, secrets, caveats).
- `docs/meetings.md` — client meeting log + action items.

**Archived (`docs/archived/`, see its `INDEX.md`):** the markdown paper draft v0.1, the old tracker
plan, critical review, next-steps, short/oral briefings, metrics literature, and Week-1 platform
research.

## Open threads / next actions (as of 2026-09-26)

*Client items 1–3 from the 2026-08-20 call are now **done**; the agreed next sequence is the
GPT-generated-answer anchor test (item 4), then the orthogonal-metrics research.*

- **[done] Expand to 2+ more sites** — added Economics, Seasoned Advice, Travel (5 corpora).
- **[done — 2026-09-07] Scale to 26 corpora** — `add_sites.py` batch added 21 more SE sites
  (family 5), volume+timeframe gated, parallel download/compute; then ran families 8 & 9 across
  all 26. Note: the topic-held-constant controls (6/10/11/12) still cover only the core 5.
- **[done] High- vs low-cognitive-load comparison** — family 9, now all 26 corpora with a
  readable bucket-mean plot: high/low tracks overlap, no cog-load split.
- **[done] Statistical significance** — family 8 ITS/Mann-Kendall + bootstrap, now `--all` over
  26 (18/26 significant) + summary/ITS plots; families 10/11 attribute the rise to topic-mix.
- **[done — client item 4] GPT-generated-answer anchor test** — family 12: generated gpt-4o-mini
  answers per question, measured whether human answers drift toward the AI answer over time.
  Flat in 4/5 (Economics lone rise, smallest/noisiest); does not corroborate the Philosophy #11
  exception. Most literal test of the client's question → no drift toward the AI.
- **[done — 2026-09-13] External corpora (HN, PubMed, arXiv-CS)** — 3 non-SE sources landed via
  `external_sources.py`, families 5 + 8. All replicate the significant aggregate post-ChatGPT rise
  (survives length control); HN cleanest, PubMed/arXiv accelerate a pre-trend.
- **[NEXT — client, 2026-09-14] Add MORE external sources** beyond the three (broaden the
  replication; candidates from the reachability probe / prior platform research).
- **[done — 2026-09-26] Topic control on the externals** — families 6 (BERTopic) + 13
  (decomposition) run on HN/PubMed/arXiv. Within-topic **flat** under BERTopic in all three →
  topic-composition, matching SE (HN's K-means within-topic bump did not survive BERTopic).
  Committed `23b7a8d`.
- **[in progress — workstream B] Academic paper** — now LaTeX (`paper/main.tex`); markdown draft v0.1 archived:
  motivation → data → methodology → results → real-world consequences → criticisms → conclusion.
  Awaiting Mark's framing input.
- **[in progress — workstream C] Homogenization tracker** — v0.5 live: weekly GitHub Action →
  Serper.dev Google top-10 (SerpAPI through 2026-10-12) → full pages via ScrapingRobot → whole-page
  embeddings → "% distinct" → results + dashboard committed. Snippets dropped. See `tracker/README.md`.
- **[NEXT] Orthogonal-metrics research (the 4 points)** — predictability (distilgpt2-ONNX /
  n-gram perplexity), compression ratio, n-gram diversity, Vendi Score; for convergent validity.
  See `docs/archived/homogenization-metrics-literature.md`.
- **Deferred:** extend family 13 decomposition from the core 5 to all 26; P2b tenure (needs
  `OwnerUserId` parsing); per-tag trends (needs `Tags` parsing); reduce HDBSCAN outliers; second
  encoder; probe the Philosophy within-question exception.

## Pending action items (from meetings.md)

*From the 2026-09-14 call:*
- **[open] Email the external results** (HN + PubMed + arXiv-CS) to Mark for review.
- **[open] Add more external data sources** beyond the current three (Workstream A).
- **[done — 2026-09-26] Develop a paper outline** — went further: full DRAFT v0.1 (`paper-draft.md`).
- **[done — 2026-09-26] Brainstorm the homogenization-tracker implementation** — built + running
  (`tracker/`, `tracker/README.md`).
- **[done — 2026-09-26] Propose how to compute homogenization metrics across Google top results** —
  implemented: Vendi score + mean pairwise cosine + marginal novelty over the top-N SERP.
- **[open — Mark] Mark reviews the data + sends ideas** for paper development.

*From the 2026-09-07 call (all done):*
- **[done] Emailed Mark the 26-corpus plots + methodology notes** (correct 18/26 raw / 20/26 LC).
- **[done] Listed high- vs low-cognitive-load sources** in the notes.
- **[done — 2026-09-13] Tried arXiv** — landed via OAI-PMH (plus HN + PubMed).

*Carried:*
- Check whether companies object to data usage for research.
- Review papers for data-sharing / referencing best practices.
