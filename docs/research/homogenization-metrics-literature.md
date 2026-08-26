# How Homogenization Is Measured (NLP methods reading)

*Reference note (2026-08-26). Why: our headline metric is aggregate BERT pairwise
cosine, which is the most ambiguous single number in the literature. This records how
others measure homogenization/diversity and the orthogonal metrics we plan to add.*
*Sequencing: this methods work comes **after** the GPT-generated-answer anchor test
(meeting item #4). It is the "add convergent, mostly embedding-free metrics" follow-up.*

## Key point that validates our current approach

Padmakumar & He (ICLR 2024) define **homogenization exactly as our family-11 does** —
an item's *"average pairwise similarity to all other items written on the same topic."*
So our same-question control is the field-standard operationalization. But the rigorous
methods papers never rely on embedding cosine alone; they triangulate across families,
several needing **no embeddings**.

## Metric families used in the literature

| Family | Metric(s) | Captures | Embeddings? |
|---|---|---|---|
| Similarity / homogenization | within-topic pairwise **ROUGE-L** + **BERTScore** | authors converging | ROUGE no / BERTScore yes |
| Lexical diversity | distinct-n, unique-n-gram fraction, self-BLEU, 5-gram head-mass | repetition (order-sensitive) | no |
| Information-theoretic | **GPT-2 perplexity**, **compression ratio** (gzip/LZMA/zlib) | predictability / redundancy | no |
| Corpus diversity | **Vendi Score**, key-point clustering | effective # of distinct items | either |
| Distributional | **MAUVE**, n-gram / POS-n-gram divergence (χ²) | distribution collapsing to a mode | no |
| Syntactic | dependency-tree height, POS-n-gram diversity | structural templating | no |

**References:** Padmakumar & He, *Does Writing with Language Models Reduce Content
Diversity?* ([arxiv 2309.05196](https://arxiv.org/abs/2309.05196)); Friedman & Dieng, *The
Vendi Score* ([2210.02410](https://arxiv.org/abs/2210.02410)); Tevet & Berant, *Evaluating
the Evaluation of Diversity in NLG* ([2004.02990](https://arxiv.org/abs/2004.02990)) — auto
metrics correlate only moderately with humans, hence triangulate. Observational
AI-homogenization studies (Doshi & Hauser, *Science Advances* 2024; Anderson et al., CHI
2024) mostly use embedding cosine like us.

## The GPT-2 / perplexity idea (predictability)

Run text through a **fixed** language model and measure perplexity / per-token
cross-entropy; lower = more predictable = more template-like. Padmakumar report GPT-2
perplexity **25.1 (human-only) → 22.1 (GPT-3) → 20.3 (InstructGPT)** and higher
compressibility with AI — so "text got more predictable" is a published homogenization
signal. Attractive for us: **no embeddings** (sidesteps anisotropy/"what does cosine
mean"), absolute and interpretable, and a different axis than semantic similarity.
Confounds (observational): length- and topic-sensitive (length-control + condition on
tag), fluency ≠ homogenization, and pasted-AI text lowers perplexity mechanically.
Tooling: torch is blocked on Windows (MAX_PATH) → use **distilgpt2 ONNX** under
onnxruntime, or the model-free fallback (**compression ratio** / a frozen pre-2020
**KenLM n-gram** cross-entropy).

## Planned additions (the 4 points) — after the anchor test

1. **Predictability over time** — distilgpt2-ONNX perplexity *or* frozen n-gram-LM
   cross-entropy, length-controlled, per quarter. Most orthogonal; the exact idea above.
2. **Compression ratio** (gzip/LZMA) per quarter — model-free redundancy, ~free, published.
3. **n-gram diversity / self-repetition** (distinct-2/3/4, 5-gram head-mass) — order-sensitive
   lexical signal we lack (our TTR family is bag-of-words).
4. **Vendi Score** on cached embeddings — principled "effective # of distinct answers".

**Payoff = convergent validity.** The current story (no strong homogenization; aggregate
rise ≈ topic composition) gets much stronger if predictability / compression / n-gram
diversity *also* show no post-ChatGPT break — and if one *does*, that is a real new lead.
