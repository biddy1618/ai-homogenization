# AI & online writing — does the pattern hold *outside* Stack Exchange?

Prepared for: Mark Nomellini · Prepared by: Dauren · 2026-09-14

## The one-line highlight

**Yes — the ChatGPT-era rise in "sameness" shows up on three completely different platforms too.**
We took the same method we ran on Stack Exchange and pointed it at **academic papers (arXiv &
PubMed)** and **tech-forum comments (Hacker News)**. In all three, answers/abstracts became
**significantly more similar to each other after ChatGPT (2022 Q4)**, and the effect **survives**
our "answers just got longer" control. Hacker News is the cleanest case — flat for years, then a
clear turn upward right after ChatGPT.

## What's new since the 26-community update

We moved beyond Stack Exchange to **three external sources** (all public, all running to mid-2026):

| Source | What it is | Size | Time span |
|---|---|---|---|
| **Hacker News** | tech-forum comments | ~39,000 comments | 2016 → mid-2026 |
| **PubMed (oncology)** | cancer-research paper abstracts | ~34,000 abstracts | 2016 → mid-2026 |
| **arXiv (Computer Science)** | CS paper abstracts | ~64,000 abstracts | 2016 → mid-2026 |

## What each one shows

- **Hacker News — the cleanest signal.** Similarity was **flat before ChatGPT**, then rises
  sharply after. Statistically strong and it holds up under the length control. This is the
  textbook "before/after" shape.
- **PubMed (cancer abstracts).** A **significant rise that accelerates** after ChatGPT — but note
  these abstracts were **already** slowly converging beforehand (journals standardized structured
  abstracts, lots of non-native-English authors using templates). So ChatGPT **sped up** an
  existing trend rather than starting one.
- **arXiv (CS papers).** Same story as PubMed — **already converging fast, then the rate roughly
  doubles** after ChatGPT. Worth flagging that CS is the *most* AI-saturated field (it's literally
  where LLM research is published), so some of this is a flood of similar AI/LLM papers.

## The honest caveats (same as before)

- **This is the "aggregate" rise only.** On Stack Exchange, when we controlled for **topic**, most
  of the rise turned out to be a shift in *what* people write about, not *how* they write. **We
  have not yet run that topic control on these three external sources** — so read this as "the
  overall similarity went up," not yet "people write in the same style."
- **Significant ≠ big.** These are large datasets, so even small changes register as
  statistically real. The effect sizes are modest.
- **Timing, not proof.** The rise lines up with ChatGPT (~1 year after), but we haven't proven
  ChatGPT *caused* it.

## How to read the two charts per source

Each folder (`hacker-news`, `pubmed-oncology`, `arxiv-computer-science`) has two charts:

- **`similarity-trend.png`** — "are answers getting more alike?" The dashed vertical line is
  ChatGPT (2022 Q4). **Top panel is the main one: higher = more alike.** Red = raw, orange =
  length-controlled (first 100 words only, to rule out "longer text looks more similar"). Shaded
  band = confidence range.
- **`slope-break.png`** — the statistical version: we fit a trend line **before** ChatGPT (blue)
  and **after** (red), and the yellow box reports the **slope change** and its p-value
  (p < 0.05 = statistically real). Top = raw, bottom = length-controlled.

## What's next

- **Topic control on these three sources** — re-run the "is it style or subject matter?" check
  (like we did for Stack Exchange) so we can say whether it's people writing in the same *style*
  or just about the same *topics*.
- **A few more external sources** — to broaden the picture beyond tech/science. Good candidates:
  a less "AI-heavy" arXiv field (e.g. math) as a control, plus **legal opinions** (CourtListener)
  and **SEC company filings** (10-K risk sections are famously boilerplate).
- **The paper** — I'll draft an outline (motivation → methodology → results → criticisms) for you
  to react to; send over any framing ideas whenever.
- **The Google tracker** — start scoping the live/open-source tool that measures homogenization
  across top Google search results (info-gain across the top results, randomized queries per topic).

*Plan: pin these down over the weekend and start executing next week.*
