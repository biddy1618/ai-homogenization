"""Language-diversity and homogenization metrics.

Primary:
  - MTLD (Measure of Textual Lexical Diversity) — length-robust lexical richness,
    computed per answer then averaged per quarter.
  - Mean pairwise cosine similarity — TF-IDF based; how alike answers are to one
    another within a time window (higher = more homogeneous).

Secondary:
  - TTR (Type-Token Ratio) — simple lexical diversity baseline.

Length-robust surface hardening (independent estimators of lexical diversity):
  - Yule's K / Yule's I — vocabulary concentration / diversity.
  - HD-D — hypergeometric diversity (length-robust successor to TTR).
  - MATTR — moving-average TTR over a fixed sliding window.
"""

from __future__ import annotations

import math
import re
from collections import Counter

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


def yule_k(tokens: list[str]) -> float:
    """Yule's K — vocabulary concentration (higher = more repetitive/homogeneous).

    K = 10^4 * (sum_r r^2 * V_r - N) / N^2, where V_r is the number of types that
    occur exactly r times and N is the token count. Length-robust above ~200 tokens.
    """
    n = len(tokens)
    if n == 0:
        return float("nan")
    freqs = Counter(tokens)
    m2 = sum(r * r for r in freqs.values())
    return 1e4 * (m2 - n) / (n * n)


def yule_i(tokens: list[str]) -> float:
    """Yule's I — vocabulary diversity (higher = more diverse); inverse of K's scale."""
    n = len(tokens)
    if n == 0:
        return float("nan")
    freqs = Counter(tokens)
    m2 = sum(r * r for r in freqs.values())
    denom = m2 - n
    if denom <= 0:
        return float("nan")
    return (n * n) / denom


def hdd(tokens: list[str], sample_size: int = 42) -> float:
    """HD-D — hypergeometric diversity (length-robust successor to TTR).

    Expected type-token ratio for random samples of ``sample_size`` tokens: for each
    type, the probability it appears in the sample contributes 1/sample_size.
    Returns NaN if the text is shorter than ``sample_size``.
    """
    n = len(tokens)
    if n < sample_size:
        return float("nan")
    freqs = Counter(tokens)
    ln_c_all = _ln_choose(n, sample_size)
    total = 0.0
    for f in freqs.values():
        if n - f < sample_size:
            p_absent = 0.0
        else:
            p_absent = math.exp(_ln_choose(n - f, sample_size) - ln_c_all)
        total += (1.0 - p_absent) / sample_size
    return total


def _ln_choose(n: int, k: int) -> float:
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def mattr(tokens: list[str], window: int = 50) -> float:
    """MATTR — moving-average type-token ratio over a sliding ``window`` of tokens.

    Length-comparable because every window is the same size. Falls back to plain TTR
    when the text is shorter than the window.
    """
    n = len(tokens)
    if n == 0:
        return float("nan")
    if n <= window:
        return ttr(tokens)
    ratios = []
    for start in range(n - window + 1):
        w = tokens[start:start + window]
        ratios.append(len(set(w)) / window)
    return float(np.mean(ratios))


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
