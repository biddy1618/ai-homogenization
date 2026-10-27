# Project Status — AI Homogenization

*Running "what's done / current state / open threads" tracker. Newest state at top.*

## Current state (2026-10-27; tracker v2 live ? see rows T2/T3 below)

**Analysis complete; paper v0.2 sent to Mark (meeting Wed 2026-10-21).** All 30 sources (26 SE: 14 high-
and 12 low-cognitive-load; 4 external) are embedded on whole text (sentence chunks of <=120 tokens,
averaged); a second encoder (BGE-small, pinned as release `bge-small-v1`) covers all 30. Families in the
analysis: 5/8 (similarity trend, all 30), 9 (high vs low load), 13 (K-means topics, all 30), 14 (tags,
26 SE), 11 (same question, 26 SE), 12 (GPT anchor, 26 SE, 154k gpt-4o-mini answers generated on the Mac).
Exploratory families 1-4, 6, 7, 10 are in `artifacts/exploratory/`. Results map: `artifacts/README.md`;
summary plots: `artifacts/summary/`; paper: `paper/main.tex` (compile with TinyTeX pdflatex + bibtex).

**Findings:** (1) answer-to-answer similarity turns up after ChatGPT: 15/26 SE + 4/4 external significant;
robust with BGE in expert and academic corpora, encoder-dependent in everyday ones; (2) stronger in
high-load communities (MiniLM 11/14 vs 4/12, BGE 9/14 vs 2/12); (3) the change is mainly in what is
asked and discussed: subject mix shifts 24/26 (tags), same-tag answers converge 18/26, same-question
answers only 6/26; (4) no movement towards GPT's own answers (pull 2 up / 6 down). Data: S3
`biddy-homogenization` via `src/sync_data.py` (raw, processed, embeddings 11.2 GB, anchor). The CAT
network blocks api.openai.com: GPT generation runs on the Mac.

**Next (agreed 2026-10-25; Mark approved open-ended work):** tracker first, then paper.
- *Tracker v2:* keep the 4 existing snapshots (artifacts) but recompute them on a fixed page count;
  from the next Monday add ~100 queries, the paper's similarity measure (mean pairwise cosine) as a
  headline alongside Vendi, and a source-mix panel; mark the provider switch.
- *Paper:* placebo break dates; test the explanation (question volume / question change on high- vs
  low-load sites); an objective measure of cognitive load instead of our own labels; condense after
  Mark's feedback.
- *Later ideas:* ChatGPT-vs-Google tracker, low-load external corpus, "number of ideas" measure,
  preprint. Meeting log: `docs/meetings.md` (2026-10-25).

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
| 7–8 | Claims ledger + conclusions review; paper v0.2; reply to Mark (next meeting Thu 2026-10-22) | **paper v0.2 drafted (2026-10-19)**: `paper/main.tex` rewritten around four questions (more alike? 5/8; where stronger? 9; what changed? 13/14/11; like the model? 12), whole-text method and 128-token disclosure, robustness table, updated limitations, exploratory families 1–4/6/7 in an appendix; 7 fresh figures from `artifacts/summary/`; compiles with TinyTeX (`tools/TinyTeX/bin/windows/pdflatex` + `bibtex`; tectonic needs network). Reply to Mark sent by Dauren |
| 12 | **GPT anchor redesign (2026-10-18)**: 100 answers/qtr, 3 gpt-4o-mini answers per question averaged, baseline = GPT answers to other same-tag questions in the same quarter (`pull`), all 26 SE (~425k generations, ~$100) | **done (2026-10-19)** on all 26 SE (154,517 GPT answers; Economics 3 draws, others 1 — draws agree at cosine 0.92). **Largely null.** Similarity to GPT's answer for the same question rises on 8/26 (all survive BH; 2 fall); at fixed length (first 120 tokens of both) 5 up / 3 down; **pull** (question-specific GPT-likeness) 2 up / 6 down, none after BH. So humans do not broadly move towards GPT's answer to their question. The fixed-length rises are mostly low-load sites (Travel, Home Improvement, Photography, Seasoned Advice) — opposite to family 9's high-load pattern. Caveat: gpt-4o-mini is a fixed proxy for the ChatGPT models people used. Summary: `artifacts/summary/12_anchor_summary.png`. Generation runs on the Mac (CAT network blocks api.openai.com): `run_anchor.py --generate-only` → `sync_data.py push anchor`; here `pull anchor` → `run_anchor.py --analyse` |
| 6c | **Topic control strengthened (2026-10-16/17)** — families 13 (all 30), 14 tags (26 SE, new: `tag_topics.py`; questions re-parsed via `parse_questions.py`), 11 same-question (26 SE; 21 new sites sample ≤150 questions/qtr) | **done**. Topic **mix shifts** almost everywhere (K-means JSD 25/30; tag JSD 24/26). Topic **diversity** falls 27/30 by K-means (fixed 100-answer subsamples; same at K=25/100) but only 13/26 by tags. **Same-subject convergence**: K-means within-topic 16/30 (high 11/14, low 3/12); same-tag 18/26 (high 9/14, low 9/12). **Same question**: 6/26 (4 after BH: History, Biology, English, Board Games) while overall similarity on the same answers rises 18/26. Reading: holding the exact question fixed, answers do *not* broadly converge; the rise is in *what* is discussed (subject mix, and question mix within subjects). K-means topics live in the embedding space, so they can mistake writing convergence for topic narrowing — tags are the cleaner SE control. Family 6 (BERTopic) drops ~50% of answers as outliers → demoted to topic labels only. Family 13's anisotropy panel (mean-centred cosine) is not interpretable (centred vectors sum to zero) — drop from the paper. Families 1–4 and 7 demoted (appendix / one line). **Plots simplified (2026-10-18):** opening window shown only in family 8 (agrees with whole text 26/30; the 4 differences are opening-only significant — so length does not drive the result; family-9 effect-size difference is borderline on the opening window, p=0.06 — disclose); family 13 = 3 panels (same-topic vs all pairs, effective topics, JSD vs pre-ChatGPT mix, with an explanatory footnote); family 14 without opening-window / share-of-pairs lines; `src/replot.py` redraws from CSVs. Travel shows a COVID jump at 2020Q2 in all tag panels — a confounder to mention |
| 6d | **Second encoder on all 30 (2026-10-20)**: BGE-small on the 21 remaining SE sites (`robustness/bge/`), `encoder_compare.py` now covers all sources + family 9 per encoder | **done**. Same verdict 21/30 (opening window 20/30), series correlation median 0.66. High load 11/14 agree (9 significant with both); external 4/4; low load 6/12 (BGE: 2 up*, 3 down* ? Seasoned Advice, Bicycles, Home Improvement). Family 9 with BGE stronger: 9/14 vs 2/12 (Fisher p=0.019), scaled median 0.11 vs -0.02 (MWU p=0.002). Reading: the rise is robust in expert/academic writing, encoder-dependent in everyday communities. Paper updated (abstract, 4.1, 4.2, robustness, limitation, discussion, conclusion; pending box removed) |
| T2 | **Tracker v2 (2026-10-25, live from the 2026-10-26 run)** | Fixed page count: first 5 readable pages in Google rank order (`fullpage.py --top-k 5`, fetching stops at 5; `runs_top5.csv`; v1 `runs_fullpage.csv` kept as archive). Headlines: mean pairwise cosine (the paper's measure) + Vendi as distinct pages out of 5. Panel 45 -> 100 questions (20/domain; original 45 = continuous 'core' line). New dashboard panels: similarity over time (core + all, per domain, provider/panel markers), distinct pages over time, by domain, source mix (top-10 domains grouped), by question, v1 archive. Historic runs recomputed (167 pages re-fetched on 2026-10-25). Result: on the 27 questions present in all 4 runs similarity still rises 0.72 -> 0.80 (Vendi 2.24 -> 1.89), most of it at the SerpAPI -> Serper switch, so the page-count artefact is gone but the provider confound remains. Page texts kept in private S3 `tracker/pagecache/` (workflow syncs if AWS secrets are set). 'Other sites' is 45-70% of results: refine source groups later |
| T3 | **Tracker follow-ups agreed 2026-10-27 (to do next chat)** | 2026-10-26 run complete (100 searched, 98 scored; core 45 similarity 0.788 -> 0.786 week on week on the same provider, so the 10/19 jump was mostly the provider switch). Decisions: (1) legend: line-style entries; 'All questions' light-grey dashed, distinct from the white 'Original 45'; (2) add domain lines to the distinct-pages (Vendi) chart + caption 'axis zoomed; full scale 1-5'; (3) REMOVE the v1 archive section from the dashboard (Vendi is already headline 2); keep runs_fullpage.csv in the repo as raw history and say so in the README (it also has a 2026-10-26 row from the old-version scheduled run); (4) keep page texts privately per week: one gz JSONL per run date in s3://biddy-homogenization/tracker/pages/<date>.jsonl.gz, restore only the same date (never reuse earlier weeks' texts: the cache is keyed by URL, so cross-week reuse would freeze content); ~0.9 MB/week compressed, ~135 MB over 3 years; replace the current cross-week pagecache sync in tracker.yml; Dauren then adds AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY repo secrets (ideally a bucket-only IAM user); (5) refine source groups ('Other sites' 45-70%). Scheduled runs actually start ~13:00 UTC Mondays, not 06:17; the gh login on the VDI cannot dispatch workflows (trigger from the Actions tab) |
| T | **Tracker note (2026-10-19)** | Headline "% distinct" fell 0.44 → 0.42 → 0.37 → 0.31 over 4 snapshots. Not yet a trend: (1) % distinct = Vendi / pages falls ~0.04 per extra page, and pages/query rose 5.8 → 7.0 (~40% of the drop); (2) 10/19 was the first Serper.dev run (v0.5; earlier SerpAPI) — more Reddit/Wikipedia/Mayo Clinic results; (3) week-to-week domain overlap only 14–23%; (4) pairwise cosine (page-count-independent) did rise 0.70 → 0.78 (10/19 p=0.002 holding pages fixed). Possible fix, not done (user's call): headline on a fixed 5 pages/query. Read trends only after 8–10 weekly points from one provider |

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
