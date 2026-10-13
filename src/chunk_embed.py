"""Whole-text embeddings for a short-context encoder, via sentence-aware chunking.

The fastembed MiniLM tokenizer truncates every input at 128 tokens (~90-100 words), silently
dropping the rest. To represent a whole text we:

0. strip machine strings: URLs, DOIs, e-mails, and any single "word" longer than
   ``MAX_WORD_TOKENS`` tokens (base64, hashes, markup/PDF fragments; real words never get there);
1. split it into sentences;
2. count each sentence's tokens with a non-truncating copy of the model's tokenizer;
3. pack whole sentences, in order, into chunks of at most ``budget`` content tokens (a sentence
   longer than the budget is split into overlapping word windows);
4. optionally repeat the last ``overlap`` sentence(s) of a chunk at the start of the next;
5. embed every chunk, then average the chunk vectors weighted by token count and L2-normalise.

Shared by the retrospective study (src/) and the live tracker (tracker/fullpage.py). numpy only.
"""
from __future__ import annotations

import re

import numpy as np

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
# 128-token model limit minus [CLS]/[SEP], with slack for tokenisation drift when sentences are joined.
DEFAULT_BUDGET = 120
MAX_WORD_TOKENS = 20

# Trailing sentence punctuation is left in place so sentence boundaries survive.
_TAIL = r"\S*?(?=[.,;:!?)\]]*(?:\s|$))"
_URL = re.compile(r"(?:https?://|www\.)" + _TAIL, re.I)
_DOI = re.compile(r"\b(?:doi:\s*)?10\.\d{4,9}/" + _TAIL, re.I)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# A word of <= MAX_WORD_TOKENS chars can't exceed MAX_WORD_TOKENS tokens, so only longer ones are counted.
_LONG = re.compile(r"\S{%d,}" % (MAX_WORD_TOKENS + 1))
_SPACES = re.compile(r"[ \t]{2,}")


def clean_text(tok, text: str, max_word_tokens: int = MAX_WORD_TOKENS) -> str:
    """Remove URLs, DOIs, e-mails and over-long single 'words'; prose is left untouched."""
    text = _EMAIL.sub(" ", _DOI.sub(" ", _URL.sub(" ", text)))
    text = _LONG.sub(lambda m: " " if _ntok(tok, [m.group()])[0] > max_word_tokens else m.group(), text)
    return _SPACES.sub(" ", text).strip()


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text) if s and s.strip()]


def opening_window(tok, text: str, n: int = DEFAULT_BUDGET, clean: bool = True) -> str | None:
    """The first ``n`` model tokens of the (cleaned) text, or None if it is shorter than ``n``."""
    if clean:
        text = clean_text(tok, text)
    enc = tok.encode(text, add_special_tokens=False)
    if len(enc.ids) < n:
        return None
    return text[: enc.offsets[n - 1][1]]


def counting_tokenizer(model):
    """A copy of the model's tokenizer with truncation off, used only for counting tokens."""
    from tokenizers import Tokenizer

    tok = Tokenizer.from_str(model.model.tokenizer.to_str())
    tok.no_truncation()
    tok.no_padding()
    return tok


def _ntok(tok, texts: list[str]) -> list[int]:
    return [len(e.ids) for e in tok.encode_batch(texts, add_special_tokens=False)] if texts else []


def _split_long(tok, sentence: str, budget: int, overlap_words: int) -> list[tuple[str, int]]:
    """Overlapping word windows for a single sentence that exceeds the budget."""
    words = sentence.split()
    sizes = _ntok(tok, words)
    pieces, start = [], 0
    while start < len(words):
        end, used = start, 0
        while end < len(words) and (used + sizes[end] <= budget or end == start):
            used += sizes[end]
            end += 1
        pieces.append((" ".join(words[start:end]), used))
        if end >= len(words):
            break
        start = max(end - overlap_words, start + 1)
    return pieces


def chunk_text(tok, text: str, budget: int = DEFAULT_BUDGET, overlap: int = 0,
               overlap_words: int = 10) -> list[tuple[str, int]]:
    """Pack a text into (chunk_text, n_tokens) pieces of at most ``budget`` content tokens."""
    units: list[tuple[str, int]] = []
    sents = split_sentences(text)
    for s, n in zip(sents, _ntok(tok, sents)):
        units.extend(_split_long(tok, s, budget, overlap_words) if n > budget else [(s, n)])

    chunks, cur, used = [], [], 0
    for s, n in units:
        if cur and used + n > budget:
            chunks.append((" ".join(x for x, _ in cur), used))
            cur = cur[-overlap:] if overlap else []
            used = sum(m for _, m in cur)
            if used + n > budget:  # carried overlap + next unit won't fit: drop the carry
                cur, used = [], 0
        cur.append((s, n))
        used += n
    if cur:
        chunks.append((" ".join(x for x, _ in cur), used))
    return chunks


def embed_documents(model, texts: list[str], embed_fn, budget: int = DEFAULT_BUDGET,
                    overlap: int = 0, tok=None, clean: bool = True) -> np.ndarray:
    """One L2-normalised vector per text = token-weighted mean of its chunk embeddings.

    ``embed_fn(model, list_of_str) -> (n, dim)`` is the caller's normalising embedder.
    """
    tok = tok or counting_tokenizer(model)
    flat, owner, weight = [], [], []
    for i, t in enumerate(texts):
        if clean:
            t = clean_text(tok, t) or t
        for c, n in chunk_text(tok, t, budget, overlap) or [(t, 1)]:
            flat.append(c)
            owner.append(i)
            weight.append(max(n, 1))
    cv = embed_fn(model, flat)
    out = np.zeros((len(texts), cv.shape[1]))
    np.add.at(out, np.array(owner), cv * np.array(weight, dtype=float)[:, None])
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return out / norms
