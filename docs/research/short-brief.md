# Homogenization — Short Brief

**Question.** Did ChatGPT (public end of 2022) make online writing more uniform?
Data: five Stack Exchange Q&A sites, quarterly, 2010 to mid-2026.

**Bottom line.** No strong homogenization. What looked like it is two mundane things:
answers got longer, and the mix of topics shifted. Writing *style* is not converging.

---

## The slope *did* change — but on what?
We also ran an interrupted time-series test: did the trend line bend upward right after
ChatGPT? On the **aggregate** similarity metric, yes — the slope change is statistically
significant in 4 of 5 sites (CV p≈1e-31, Travel p≈4e-7, Philosophy p≈7e-4, Economics
p≈5e-4; only cooking is null, and slightly negative). It survives even after controlling
for answer length. So "something moved" is real and significant.

The catch: that test measures the *aggregate* — all answers lumped together. A significant
bend there can come from the topic mix shifting, not from writing style. That is exactly
what the two tests below were built to separate out — and they say the bend is topic mix,
not style. Significant ≠ homogenization.

## What we did today
Two direct tests. Neither needs topic-guessing, so neither can be blamed on our
clustering choices. Both ask "are answers converging?" — one against other humans, one
against ChatGPT itself.

**1. Same-question test (#11).** Compare answers written to the *identical* question over
time. If people are writing more alike, these should get more similar.
- Flat in 4 of 5 sites. Only **Philosophy** rises.
- Separately, "any two answers this quarter" similarity *did* rise in CV, Philosophy, and
  Travel — but the same-question line stayed flat. That means the rise is the topic mix
  shifting, not style. (Clear topic-mix in **CV** and **Travel**; **Philosophy** is a real
  exception; **Economics** too noisy; **cooking** no rise at all.)

**2. ChatGPT-anchor test (#12).** Generate ChatGPT's own answer to each question, then ask:
do human answers drift toward it over the years? This is the most literal version of the
client's question.
- Sampled 25 human answers/quarter, 1 GPT answer/question.
- Flat in 4 of 5 sites. Only **Economics** rises — and Economics is our smallest, noisiest
  site.

---

## What it means
Both "most direct" tests come back flat almost everywhere. The two exceptions
(Philosophy in one test, Economics in the other) are *different* sites and don't back each
other up — that is what random noise looks like, not a real effect. So the small similarity
rise we saw in earlier measures is topic composition, not people writing the same way.

**Per site, quick read:**
- **Cross Validated** — overall rise = topic mix; same-question flat. No style convergence.
- **Travel** — same as CV. No style convergence.
- **Philosophy** — the one genuine same-question rise; isolated, not confirmed by the anchor test.
- **Economics** — the one genuine anchor rise; smallest/noisiest site, not confirmed elsewhere.
- **Seasoned Advice (cooking)** — no rise anywhere.

---

## Say-it-out-loud version
"Across five communities and our most direct tests — including using ChatGPT itself as the
yardstick — human answers are not drifting toward each other or toward the AI. The apparent
convergence is longer answers plus shifting topics, not a change in writing style."

## Caveats to state plainly
- Correlational only; the signal lags ChatGPT by ~a year, so we can't pin it on ChatGPT.
- Economics is thin (a few dozen answers/quarter recently) — treat its lone rise with caution.
- One embedding model, so we report *change over time*, not absolute similarity levels.
