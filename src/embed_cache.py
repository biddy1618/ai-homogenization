"""Persistent, id-keyed cache for MiniLM embeddings, stored in one DuckDB file.

Embedding is the expensive step (CPU ONNX); the vectors are deterministic per text,
so we cache them by answer ``id`` and reuse them across runs and scripts. The first
request for an id embeds and stores it; later requests hit the cache.

Storage: ``<dir>/embeddings.duckdb`` (gitignored; synced via ``src/sync_data.py``), table
``embeddings(cache, id, dim, vec BLOB)``; ``vec`` holds the raw little-endian float32 bytes
(DuckDB's float compression inflates near-random embedding values by ~35%, BLOB does not).
Callers still pass the legacy per-cache path (``data/embeddings/<stem>.npz``); its stem is the
``cache`` key. Vectors are stored as float32 and returned as float64: measured effect on mean
pairwise cosine is ~1e-11, far below reported precision. A legacy ``.npz`` that is not yet in
the database is still read.

Typical use (load once, reuse across a loop, save once):

    cache = load_cache(path)
    for ...:
        emb = cached_embed(model, ids, texts, embed_texts, cache)
    save_cache(path, cache)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

DB_NAME = "embeddings.duckdb"


def _connect(path: Path, read_only: bool = False):
    import duckdb

    db = path.parent / DB_NAME
    if read_only and not db.exists():
        return None
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db), read_only=read_only)
    if not read_only:
        con.execute("CREATE TABLE IF NOT EXISTS embeddings ("
                    "cache VARCHAR NOT NULL, id BIGINT NOT NULL, dim SMALLINT NOT NULL, "
                    "vec BLOB NOT NULL, PRIMARY KEY (cache, id))")
    return con


def _read_db(path: Path) -> tuple[np.ndarray, np.ndarray] | None:
    con = _connect(path, read_only=True)
    if con is None:
        return None
    try:
        if not con.execute("SELECT count(*) FROM information_schema.tables "
                           "WHERE table_name = 'embeddings'").fetchone()[0]:
            return None
        tbl = con.execute("SELECT id, dim, vec FROM embeddings WHERE cache = ? ORDER BY id",
                          [path.stem]).to_arrow_table()
    finally:
        con.close()
    if tbl.num_rows == 0:
        return None
    ids = tbl.column("id").to_numpy()
    dim = int(tbl.column("dim")[0].as_py())
    flat = np.frombuffer(b"".join(tbl.column("vec").to_pylist()), dtype="<f4")
    return ids, flat.reshape(len(ids), dim).astype(np.float64)


def write_vectors(path: Path, ids: np.ndarray, vecs: np.ndarray) -> int:
    """Insert ``ids``/``vecs`` under cache key ``path.stem``, skipping ids already stored."""
    import pyarrow as pa

    if len(ids) == 0:
        return 0
    vecs = np.ascontiguousarray(vecs, dtype="<f4")
    tbl = pa.table({"id": pa.array(np.asarray(ids, dtype=np.int64)),
                    "vec": pa.array([r.tobytes() for r in vecs], pa.binary())})
    con = _connect(path)
    try:
        con.register("incoming", tbl)
        before = con.execute("SELECT count(*) FROM embeddings WHERE cache = ?", [path.stem]).fetchone()[0]
        con.execute("INSERT INTO embeddings SELECT ?, i.id, ?, i.vec FROM incoming i "
                    "ANTI JOIN (SELECT id FROM embeddings WHERE cache = ?) e ON e.id = i.id",
                    [path.stem, vecs.shape[1], path.stem])
        after = con.execute("SELECT count(*) FROM embeddings WHERE cache = ?", [path.stem]).fetchone()[0]
    finally:
        con.close()
    return after - before


def load_cache(path: Path) -> dict[int, np.ndarray]:
    """Load the id -> vector cache keyed by ``path.stem`` (empty dict if none yet)."""
    got = _read_db(path)
    if got is None and path.exists():
        d = np.load(path)
        got = d["ids"], d["vecs"]
    if got is None:
        return {}
    return {int(i): v for i, v in zip(*got)}


def save_cache(path: Path, cache: dict[int, np.ndarray]) -> None:
    """Persist new cache entries to the DuckDB store (existing ids are left unchanged)."""
    if not cache:
        return
    ids = np.fromiter(cache.keys(), dtype=np.int64, count=len(cache))
    write_vectors(path, ids, np.vstack([cache[int(i)] for i in ids]))


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
