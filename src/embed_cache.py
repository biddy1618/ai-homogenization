"""Persistent, id-keyed cache for MiniLM embeddings.

Embedding is the expensive step (CPU ONNX); the vectors are deterministic per text,
so we cache them by answer ``id`` under ``data/embeddings/`` (gitignored) and reuse
them across runs and scripts. The first request for an id embeds and stores it; later
requests hit the cache. Vectors are stored as ``.npz`` (``ids`` int64, ``vecs`` float64
L2-normalized), so a reloaded vector is bit-identical to a fresh embed and metrics
reproduce exactly.

Typical use (load once, reuse across a loop, save once):

    cache = load_cache(path)
    for ...:
        emb = cached_embed(model, ids, texts, embed_texts, cache)
    save_cache(path, cache)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def load_cache(path: Path) -> dict[int, np.ndarray]:
    """Load an id -> vector cache from ``path`` (empty dict if it does not exist yet)."""
    if path.exists():
        d = np.load(path)
        return {int(i): v for i, v in zip(d["ids"], d["vecs"])}
    return {}


def save_cache(path: Path, cache: dict[int, np.ndarray]) -> None:
    """Persist the cache atomically (write to a temp file, then replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ids = np.fromiter(cache.keys(), dtype=np.int64, count=len(cache))
    vecs = np.vstack([cache[int(i)] for i in ids]) if len(ids) else np.empty((0, 0))
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez(tmp, ids=ids, vecs=vecs)
    tmp.replace(path)


def cached_embed(model, ids, texts, embed_fn, cache: dict[int, np.ndarray] | None) -> np.ndarray:
    """Return embeddings for ``texts`` (aligned to ``ids``), embedding only cache misses.

    ``cache`` is mutated in place with any newly embedded vectors. Pass ``cache=None`` to
    bypass the cache entirely (embed everything).
    """
    if cache is None:
        return embed_fn(model, list(texts))
    ids = [int(i) for i in ids]
    missing = [(i, t) for i, t in zip(ids, texts) if i not in cache]
    if missing:
        vecs = embed_fn(model, [t for _, t in missing])
        for (i, _), v in zip(missing, vecs):
            cache[i] = v
    return np.vstack([cache[i] for i in ids])
