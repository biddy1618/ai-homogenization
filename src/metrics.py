"""Language-diversity and homogenization metrics.

Primary:
  - MTLD (Measure of Textual Lexical Diversity) — length-robust lexical richness,
    computed per answer then averaged per quarter.
  - Mean pairwise cosine similarity — TF-IDF based; how alike answers are to one
    another within a time window (higher = more homogeneous).

Secondary:
  - TTR (Type-Token Ratio) — simple lexical diversity baseline.
"""

from __future__ import annotations

import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_TOKEN = re.compile(r"[a-z]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def ttr(tokens: list[str]) -> float:
    if not tokens:
        return float("nan")
    return len(set(tokens)) / len(tokens)


def _mtld_pass(tokens: list[str], threshold: float) -> float:
    factors = 0.0
    factor_len = 0
    types: set[str] = set()
    count = 0
    for tok in tokens:
        count += 1
        types.add(tok)
        if len(types) / count <= threshold:
            factors += 1
            factor_len += count
            types = set()
            count = 0
    if count > 0:
        partial = (1 - len(types) / count) / (1 - threshold)
        factors += partial
        factor_len += count
    if factors == 0:
        return float("nan")
    return factor_len / factors


def mtld(tokens: list[str], threshold: float = 0.72, min_tokens: int = 50) -> float:
    """Bidirectional MTLD. Returns NaN for texts shorter than ``min_tokens``."""
    if len(tokens) < min_tokens:
        return float("nan")
    forward = _mtld_pass(tokens, threshold)
    backward = _mtld_pass(list(reversed(tokens)), threshold)
    return float(np.nanmean([forward, backward]))


def mean_pairwise_cosine(
    texts: list[str], max_features: int = 5000, seed: int = 42, sample: int | None = None
) -> float:
    """Mean off-diagonal TF-IDF cosine similarity across a set of texts."""
    if sample is not None and len(texts) > sample:
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(texts), size=sample, replace=False)
        texts = [texts[i] for i in idx]
    if len(texts) < 2:
        return float("nan")

    tfidf = TfidfVectorizer(max_features=max_features, stop_words="english")
    matrix = tfidf.fit_transform(texts)
    sim = cosine_similarity(matrix)
    # Mean of the upper triangle (exclude the diagonal of 1.0s).
    iu = np.triu_indices_from(sim, k=1)
    return float(sim[iu].mean())
