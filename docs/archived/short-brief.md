# Homogenization — Short Brief

**Question.** Did ChatGPT (public end of 2022) make online writing more uniform?
Data: five Stack Exchange Q&A sites, quarterly, 2010 to mid-2026.

**Bottom line.** No strong homogenization. What looked like it is two mundane things:
answers got longer, and the mix of topics shifted. Writing *style* is not converging.

---

## The slope *did* change — but on what?
**#8 Significance / ITS.** Segmented regression + Mann-Kendall + bootstrap CIs. Did the
trend line bend upward right after ChatGPT? On the **aggregate** similarity metric, yes —
the slope change is statistically significant in 4 of 5 sites (CV p≈1e-31, Travel p≈4e-7,
Philosophy p≈7e-4, Economics p≈5e-4; only cooking is null, and slightly negative). It
survives even after controlling for answer length. Bootstrap 95% CIs (2026-08-20) also
separate the recent Sentence-BERT rise from the 2016–22 trough. So "something moved" is
real and significant.

The catch: that test measures the *aggregate* — all answers lumped together. A significant
bend there can come from the topic mix shifting, not from writing style. That is exactly
what #10 / #11 / #12 were built to separate out — and they say the bend is topic mix,
not style. Significant ≠ homogenization.

**#9 Cognitive-load test.** Is the similarity rise bigger for hard/technical writing (high
cognitive load) than casual writing (low)? High = **Cross Validated**, **Philosophy**,
**Economics**; low = **Seasoned Advice**, **Travel**. Each corpus centered on its own
pre-ChatGPT mean, then compare the change (levels aren't comparable across sites).
- Rise is widespread, no clean high/low split. Length-controlled deltas: CV +0.0085,
  Philosophy +0.0086, Economics +0.011, Travel (low) also +0.0067; only Seasoned Advice
  flat/negative (−0.0016). A low-load site (Travel) rises more than some high-load ones
  → cognitive load is NOT the mechanism.
- Caveat: only 3-vs-2 corpora — suggestive, not decisive.

**#10 Overall vs within-topic.** Same MK/ITS significance test, two versions of the curve
per corpus: overall (all answers) vs within-topic (topic held constant, family-6 clusters).
- Overall trend significant, within-topic collapses to non-significant — **CV** overall MK
  p≈8e-4 vs within p≈0.28; **Philosophy** p≈5e-3 vs 0.39; **Travel** p≈3e-3 vs 0.38. That
  gap IS the topic-composition signature.
- Honest caveat: the ITS-kink column is noisier than MK — within-topic ITS stays significant
  for CV and Economics even though MK doesn't. Lead with MK + the same-question control (#11);
  don't hide the ITS column.
- Families 8/10 use soft topic clusters (inherit the outlier-drop). Order of rigor:
  10 (soft clusters) < 11 (same literal question) < 12 (AI reference answer).

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
Cognitive load is not the mechanism (#9). Within-topic MK goes non-significant (#10) —
the aggregate rise is topic mix. Both "most direct" tests come back flat almost everywhere.
The two exceptions (Philosophy in one test, Economics in the other) are *different* sites
and don't back each other up — that is what random noise looks like, not a real effect. So
the small similarity rise we saw in earlier measures is topic composition, not people
writing the same way.

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
- Cognitive-load split is 3-vs-2 corpora — suggestive, not decisive.
- #10 uses soft clusters; lead with MK + #11, and don't hide the noisier ITS-kink column.
