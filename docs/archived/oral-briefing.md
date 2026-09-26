# Homogenization Study — Oral Briefing (story version)

*Client: Mark Nomellini (Kirkland & Ellis). The question we were asked: did generative
AI — ChatGPT, which went public at the end of 2022 — make online writing more the same?*

---

## How to use this document
This is written to be **spoken**, not read. Each chapter is one beat of the story. Read a
chapter out loud, then have your voice assistant ask you the matching questions from the
**Q&A bank** and answer from memory — in your own words, like you're explaining it to a
smart friend who isn't technical. If you can tell the story start to finish and handle the
Q&A, you're ready. Anchor numbers are in **Key numbers**; one-breath definitions are in the
**Glossary**.

The whole thing is built to be *a journey*: we start with a dramatic-looking result, and
each step we take dismantles a little more of it, until we're left with an honest, modest
answer. Tell it that way — as detective work.

---

## The one-breath answer
"No — writing did not broadly homogenize. The dramatic-looking signal turned out to come
from two boring causes: answers simply got longer over the years, and the *topics* people
write about shifted. Once you account for those two things, the 'everyone sounds the same
now' story falls apart."

---

## The 90-second story (say this whole thing out loud)
"We were asked whether AI flattened online writing — made everyone sound alike. To test it
we used public question-and-answer communities on Stack Exchange, where you can read millions
of human answers stretching from 2010 all the way to the middle of 2026 — so we can see well
before ChatGPT and well after. We measured the writing quarter by quarter and looked for a
change around late 2022, when ChatGPT launched.

Our first, simplest measurements screamed 'homogenization' — answers looked less varied and
more alike over time. But that was a trap. Answers also got *longer* over the years, and the
simple measures automatically move when text gets longer. When we made every answer the same
length before measuring, the effect vanished. So the first dramatic signal was really just
'more words,' not 'more similar.'

Then we went deeper, with modern AI language models that read an answer for its meaning. Here
we finally found something real: a small rise in how similar answers are to each other,
starting about a year after ChatGPT. That's the one live hint in the whole study.

So we asked the decisive question: are people writing the *same way*, or just writing about
the *same things*? We sorted answers by topic and measured similarity only *within* each
topic. Within a topic, the similarity was flat — no rise. That means the small overall rise
wasn't style homogenization; it was a shift in the *mix* of topics people discuss. We got the
same answer when we compared answers to the very same question over time — they didn't get
more alike.

To make sure this wasn't a quirk of two communities, we expanded to five — spanning expert,
technical writing and everyday, practical writing — and ran the most direct test of all: for
the same questions, we had ChatGPT itself write answers, then asked whether human answers
drift toward what the AI would say. Across almost every community, they don't. Bottom line: no
strong AI homogenization. A small recent wobble that's mostly about *what* people write, not
*how* — and we can't even pin that on ChatGPT."

---

## The full story — the journey, chapter by chapter

### Chapter 1 — The question, and why it's slippery
"'Did AI make writing more uniform?' sounds simple, but 'uniform' can mean many things —
smaller vocabulary, more copy-paste phrasing, the same ideas, the same topics. So we didn't
pick just one measure; we built a *ladder* of measurements, from crude word-counting at the
bottom to state-of-the-art meaning models at the top. If homogenization were real and strong,
it should light up the whole ladder. Spoiler: it doesn't."

### Chapter 2 — First look: the surface, and the length trap
"At the bottom of the ladder are simple measures — how rich is the vocabulary, how much do
answers overlap in words. Early on, these looked like a smoking gun: diversity falling,
overlap rising, right around the AI era. But we caught the trap. Over these years, answers
steadily got *longer*, and these particular measures move automatically with length — a long
answer looks less diverse and shares more common words no matter who wrote it. So we redid
everything after trimming every answer to the same length. The signal disappeared. We
double-checked at several trim lengths and with four different diversity measures — all flat.
Lesson one: the most dramatic 'homogenization' was a **length illusion**."

### Chapter 3 — Going deeper: meaning, and the first real hint
"Simple word-counting is blind to meaning, so we climbed the ladder to modern sentence
embeddings — AI models that turn a whole answer into a fingerprint of its meaning. This is the
serious test. And here, for the first time, we found something that *survived* the length
correction: a small rise in answer-to-answer similarity, starting about a year after ChatGPT,
showing up in both of our first two communities. We took it seriously. But we stayed skeptical
for three reasons: it was small, it lagged ChatGPT by a year rather than snapping in right at
launch, and a companion measure — whether the 'space' of answers is collapsing — didn't back
it up."

### Chapter 4 — The turning point: is it *style*, or is it *subject*? (the key bottleneck)
"This is the heart of the whole study, so slow down here. A rise in overall similarity has two
completely different possible causes. One: people genuinely started *writing the same way* —
real style homogenization. Two: people started *writing about the same things* — if a
community suddenly gets flooded with questions on a few hot topics, the answers look more
alike on average, even though nobody changed how they write. Same number on the meter, totally
different meaning.

To tell them apart, we grouped answers by topic and measured similarity *only among answers on
the same topic*. If style were converging, within-topic similarity should rise too. It didn't —
it stayed flat, in every community. So the overall rise was mostly a **topic-composition
effect**: the *mix* shifted, not the writing. Put plainly — the structure of what people talk
about drifted a bit, but their actual style did not become more uniform.

Now, the honest bottleneck in this step — say this to Mark, don't hide it. This within-topic
test has two limitations. First, to keep it computable we work from a *sample* — up to about
800 answers per quarter — so the within-topic curve and the overall curve are measured on
slightly different slices; that's *why the two plots don't line up exactly*, and it's expected,
not a bug. Second, the topic-clustering step can't confidently place about half the answers, so
it sets them aside — which means this particular test is run on the cleaner half of the data.
That's a real caveat. It's exactly why we didn't stop here and instead ran two more direct
tests later — the same-question test and the ChatGPT-anchor test — that need *no* clustering at
all. And they agreed."

### Chapter 5 — Pressure-testing: five communities, easy and hard
"Two communities could be a fluke, so we widened to five, and deliberately mixed two kinds:
'hard' communities where answers are expert reasoning — statistics, philosophy, economics — and
'everyday' communities where answers are practical advice — cooking and travel. A popular theory
says AI should flatten the *easy, everyday* writing the most. We found the opposite of a clean
story: the small recent rise showed up in *four of the five*, across both kinds. It wasn't neatly
'hard versus easy.' One community — the cooking one — showed essentially no rise at all. So
whatever the small signal is, it's widespread but uneven, and it doesn't line up with the 'AI
templates the easy stuff' theory."

### Chapter 6 — "But is the trend real?" — the significance check
"Reading wiggly curves by eye is dangerous, so we ran a proper statistical test that asks: did
the trend genuinely *bend* at ChatGPT's release, more than random noise would explain? In the
well-populated communities, yes — the change is statistically real, not eyeballing. The lone
exception was the cooking community, which showed no real change — and, importantly, that's a
*genuine* flat result, not a data-starvation artifact: cooking still has healthy numbers. If
anything, the community we should treat most cautiously is economics, which is our *smallest*
dataset and thins out to just a few dozen answers per quarter at the very end — so its
late-period spikes are noisy. Significance tells us the overall rise is real; it does *not* tell
us it's style rather than topic mix. For that, we needed the direct tests."

### Chapter 7 — The two most direct tests
"These are the cleanest tests, because neither needs topic-clustering.

First, the **same-question test**. On Stack Exchange, many people answer the exact same question.
So we compared answers to the *same* question and asked: over time, did different people's
answers to one question get more alike? For four of the five communities: no. The one exception
was philosophy, where there was a genuine upward drift — we flag it honestly as a single,
isolated hint, not proof.

Second — and this is the one we built this week — the **ChatGPT-anchor test**, the most literal
version of the client's question. For a sample of questions we had ChatGPT *itself* write an
answer, then asked: over the years, do human answers drift toward what the AI would have
written for that same question? We sampled twenty-five human answers per quarter and generated
one AI answer per question. The result: essentially flat in four of five communities — humans
are *not* converging on the AI's output. The one exception here was economics — but notice,
that's a *different* community than the philosophy exception, so the two lone hints don't even
corroborate each other, and economics is our smallest, noisiest dataset. Two isolated,
non-overlapping exceptions is exactly what you'd expect from noise, not a real effect."

### Chapter 8 — Where we landed
"Twelve different measurements, five communities, from crude word-counts to ChatGPT itself as a
yardstick. The strong claim — that AI flattened online writing — is not supported. The dramatic
early signal was a length illusion. The one real, small signal in the deep models mostly
dissolves the moment you separate *what* people write about from *how* they write it. And our
two most direct tests — same question, and 'do they sound like ChatGPT' — come back flat almost
everywhere. So: no strong homogenization; at most a small, recent, topic-driven wobble that we
can't even causally tie to ChatGPT."

---

## Key numbers to anchor on
- **Five communities**, all from the same mid-2026 data snapshot, quarterly from 2010–2026:
  Cross Validated (statistics, ~219k answers), Philosophy (~68k), Economics (~20k, our
  smallest), Seasoned Advice / cooking (~66k), Travel (~80k).
- **ChatGPT marker:** end of 2022 (2022Q4).
- **The length fix:** measure the first ~100 words of every answer (re-checked at several
  lengths — all flat).
- **Topic-mix change (early on):** essentially zero on a 0-to-1 scale — the subject mix barely
  moved at the coarse level.
- **The one live hint:** a small rise in deep-embedding similarity from about late 2023 — small,
  lagging ChatGPT by ~a year, and it *goes flat once you hold topic constant*.
- **Sampling, so you can answer the "why don't the plots match" question:** the embedding
  measurements use up to **800 answers per quarter**; the ChatGPT-anchor test uses **25 answers
  per quarter**. Different tests, different samples — the curves aren't meant to be identical.
- **The clustering caveat:** the within-topic test sets aside about **half** the answers it can't
  confidently assign to a topic.
- **Two direct tests, two lone exceptions that don't agree:** same-question flags *philosophy*;
  ChatGPT-anchor flags *economics*. Different communities → not a consistent signal.

---

## The honest caveats (say these unprompted — it builds trust)
- **Correlation, not causation.** Even the small live signal is only correlational, and the
  ~1-year lag means we can't pin it specifically on ChatGPT.
- **The within-topic test drops ~half the data** (the answers the clustering can't place) and is
  run on a sample — which is exactly why we backed it up with the same-question and anchor tests
  that need no clustering.
- **Economics is thin and noisy** at the end (down to a few dozen answers per quarter), so its
  lone positive in the anchor test deserves a caution flag.
- **Single AI model as the yardstick.** Absolute similarity scores are inflated by quirks of one
  embedding model, so we report *change over time*, not absolute levels; a second model would
  harden it.
- **We're honest about what could still be there:** a genuinely small, topic-specific effect that
  our averages wash out. We're not claiming zero; we're claiming *not strong, and not proven*.

---

## Bottom line for the client (the money line)
"The strong claim — that AI flattened online writing — is not supported. The dramatic signal in
the simple measures is a length illusion. The one genuine hint, a small recent convergence in the
deep models, largely disappears once we separate *what* people write about from *how* they write
it — and our two most direct tests, including using ChatGPT itself as the yardstick, come back
flat in almost every community. So the honest summary is: **no broad homogenization; at most a
small, recent, topic-driven wobble that is not a change in writing style and not provably caused
by ChatGPT.**"

---

## Q&A bank (have the assistant quiz you)
**Q: In one sentence — did AI homogenize writing?**
A: No, not in any strong sense; the headline effect was a length illusion, and the one small real
hint mostly turns out to be a shift in topics, not writing style.

**Q: What's this "length illusion" — explain it to a non-technical person.**
A: Answers got longer over the years. Several of our simple measures move automatically as text
gets longer — long answers look less varied and share more common words — so what looked like
convergence was really just "more words." Trim every answer to the same length and the effect
disappears.

**Q: You found *one* real signal. What was it?**
A: With modern meaning-based AI models, answers got a little more similar starting about a year
after ChatGPT, in both original communities, and it survived the length fix. But it's small, it
lags a year, and it mostly evaporates when we control for topic.

**Q: What does "control for topic" mean and why is it the crux?**
A: If lots of people suddenly ask about the same few subjects, their answers look more alike on
average — not because writing homogenized, but because they're about the same thing. So we
measured similarity *only among answers on the same topic*. That stayed flat, which tells us the
overall rise was a shift in the *mix of topics*, not in style.

**Q: Why don't your two main similarity plots look identical?**
A: They measure different things on different samples. One is overall similarity across up to 800
answers a quarter; the other is similarity *within* each topic, after setting aside the answers
we can't confidently cluster. Different question, different slice — they're not supposed to match.

**Q: What's the ChatGPT-anchor test, in plain words?**
A: For the same questions, we had ChatGPT write its own answer, then checked whether real human
answers drift toward the AI's version over time. In four of five communities they don't — humans
aren't converging on the AI. It's the most literal test of the client's question.

**Q: You mention two exceptions — philosophy and economics. Doesn't that prove something?**
A: They're *different* communities flagged by *different* tests, so they don't back each other up.
And economics is our smallest, noisiest dataset. Two isolated, non-overlapping blips are what you
expect from noise, not a real effect — so we flag them honestly and don't overclaim.

**Q: Five communities — why should I trust that?**
A: They're independent, with different subjects and norms, and we deliberately mixed expert
"hard" communities with everyday "easy" ones. Seeing the same pattern — length illusion, flat
within-topic, flat anchor test — across all of them makes it far less likely to be a quirk of one
dataset.

**Q: Could your method just be missing a real effect?**
A: Possibly a small, topic-specific one our averages smooth over — we're honest about that. But
twelve measurements and five communities all pointing the same way is strong, and our cleanest
tests were designed specifically to catch style convergence if it existed.

**Q: The one line I can repeat to my team?**
A: "No strong AI homogenization. A small recent wobble that's mostly about topic mix, not writing
style, and not provably caused by ChatGPT."

---

## Glossary (say each in one breath, plainly)
- **Homogenization:** everyone's writing becoming more the same.
- **Length illusion / length artifact:** the fake signal that appears just because answers got
  longer; several simple measures move with length on their own.
- **Vocabulary diversity:** how many different words are used; simple, but drops as text gets
  longer, so unreliable alone.
- **Sentence embedding:** a modern AI model that turns a whole answer into a "meaning fingerprint"
  — the serious test of whether answers *mean* more alike.
- **Similarity / cosine:** how alike two fingerprints are; higher = more similar.
- **Topic modeling / clustering:** automatically sorting answers into subject groups so we can ask
  whether *style* changed separately from *subject*.
- **Within-topic similarity:** similarity measured only among answers on the *same* topic — this is
  what separates real style homogenization from a shift in what people write about.
- **Topic-composition effect:** the average looks more similar only because the *mix* of topics
  shifted, not because writing changed.
- **Same-question test:** comparing answers to the exact same question over time — a clean control
  that needs no clustering.
- **ChatGPT-anchor test:** using ChatGPT's own answer as a yardstick and asking whether humans
  drift toward it — the most literal version of the client's question.
- **Significance / trend test:** a statistical check that the trend genuinely bent at ChatGPT's
  release rather than being random noise.
- **Correlation vs causation:** even a real trend around 2022 doesn't prove ChatGPT *caused* it.

---

## Where we can go from here (one-liners)
1. Look *inside* topics one at a time — AI may homogenize some subjects more than others.
2. Add a second, independent AI model as a yardstick, to harden the deep-embedding result.
3. Add a third, more natural-prose source (e.g., Reddit) on the same subjects.
4. Chase the two lone exceptions — philosophy (same-question) and economics (anchor) — to see if
   either survives a closer look or is just noise.
5. Add extra, independent cross-checks (predictability / compression / word-variety) for
   convergent validity.
