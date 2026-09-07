# AI & online writing — notes to go with the charts

Prepared for: Mark Nomellini · Prepared by: Dauren · 2026-09-07

## The question
Did ChatGPT (released **2022 Q4**) make people's online writing more alike — are answers converging
on a single "AI voice"?

## What we measured (one paragraph)
We took public Stack Exchange answers from **26 communities** (~1M answers). Each answer is turned into
a numeric "meaning fingerprint," which lets us score how similar any two answers are (roughly 0 = unrelated,
1 = identical in meaning). If AI is homogenizing writing, that average similarity should climb after
2022 Q4. We track it quarter by quarter for every community — and, importantly, run controls so a rise
can't be explained by something boring (answers getting **longer** over time, or people just switching
**topics**).

## The two buckets
We split the 26 communities by how much expertise/reasoning a typical answer needs ("cognitive load"):

- **High cognitive load (14):** Cross Validated (statistics), Philosophy, Economics, Cryptography, Law,
  History, Computer Science, Biology, Astronomy, Chemistry, Electrical Engineering, Physics,
  Software Engineering, English Language & Usage.
- **Low cognitive load (12):** Seasoned Advice (cooking), Travel, Bicycles, Gardening,
  Role-playing Games, Board Games, Personal Finance & Money, Photography, The Workplace,
  Home Improvement, Science Fiction & Fantasy, Arqade (Gaming).

## The headline
**No strong evidence that AI homogenized *how* people write.** Similarity does rise modestly after
ChatGPT in most communities, but once we hold the **topic** constant that rise largely disappears. The
signal is mostly a shift in **what** people write about, not **how**.

---

## How to read the charts

### 1) Per-community similarity trends — folder `family5-similarity-trends\`
One chart per community (these are the ones you were most interested in). The dashed vertical line marks
**ChatGPT (2022 Q4)** — left of it is "before," right is "after." Three stacked panels:

- **Top — "are answers becoming more alike?"** This is the main panel. **Higher = more alike.** Two
  lines: **raw** (red) and **length-controlled** (orange — uses only the first 100 words of each answer,
  to rule out the "longer text looks more similar" effect). A rise to the right of the dashed line is the
  thing everyone's asking about.
- **Middle — centroid variance.** The same question from another angle; here **lower = more alike.**
- **Bottom — effective dimensionality.** How spread-out the answers are; **higher = more varied.**
- Shaded bands = confidence range (how sure we are of each point).

Across both buckets the pattern is similar: a long flat/declining stretch, then a **modest uptick in the
last ~2–3 years.**

### 2) The summary chart — `01_significance_by_site_26corpora.png`
Every community on one chart, showing its after-ChatGPT change. Dots to the **right of the "0" line** got
more alike. **Filled dot = statistically real; hollow dot = could be noise.**

- **18 of 26** communities rose significantly (**20 of 26** after the length control).
- So **8 communities did *not* show a significant rise** (more than the ~5 I eyeballed on the call):
  **Physics, Astronomy, English Language & Usage** (high); **Seasoned Advice, Gardening, Board Games,
  Personal Finance & Money, Photography** (low). Seasoned Advice is the only one that actually drifts
  slightly **down.**

### 3) High vs low cognitive load — `02_cognitive_load_comparison.png`
The two buckets, each starting from its own pre-ChatGPT baseline. They **basically overlap** — so
cognitive load doesn't decide the effect, and the "AI flattens the easy content most" theory isn't
supported.

### 4) Per-site trend with the slope break — folder `family8-significance-trends\`
One chart per community (all 26), the statistical companion to the family-5 charts. Same grey dots
(quarterly similarity), but here we **fit a straight trend line before ChatGPT (blue) and after (red)**
and test whether the slope genuinely changed at the 2022 Q4 line. Two panels: **raw** (top) and
**length-controlled, first 100 words** (bottom). The yellow box reports the **slope change after ChatGPT**
and its p-value (p < 0.05 = statistically real, not noise).

- A **blue line sloping down, then a red line sloping up** (like Cross Validated) is the classic pattern:
  similarity was drifting *down* for a decade, then ticks *up* after ChatGPT.
- The 8 non-significant communities above are the ones where that red-line change is small or uncertain.

Takeaway: this is where the "18 of 26 rose significantly" number on the summary chart comes from — one
site at a time, with the before/after slopes drawn in.

---

## Two honest caveats
- **Significant ≠ big.** Large communities have very tight error bars, so even tiny changes register as
  "statistically significant." The actual effect sizes here are small.
- **Timing, not proof.** The uptick lines up with ChatGPT (~1 year after), but we haven't proven ChatGPT
  *caused* it.

## What's next
**arXiv** (academic papers) as the first non–Stack-Exchange, high-cognitive-load source — I'll vet its
volume and time span first, like we did for the others.
