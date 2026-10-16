"""One-off: import legacy data/embeddings/*.npz caches into data/embeddings/embeddings.duckdb.

Each file becomes cache key = file stem. After import, every cache is read back and compared
to the .npz (same ids, max |diff| below float32 rounding). With --delete, verified .npz files
are removed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from embed_cache import _read_db, write_vectors  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", type=Path, default=ROOT / "data" / "embeddings")
    ap.add_argument("--delete", action="store_true", help="remove .npz files that verify")
    args = ap.parse_args()

    bad = []
    files = sorted(args.dir.glob("*.npz"))
    for n, f in enumerate(files, 1):
        d = np.load(f)
        ids, vecs = d["ids"], d["vecs"]
        added = write_vectors(f, ids, vecs)
        got = _read_db(f)
        order = np.argsort(ids)
        ok = (got is not None and np.array_equal(got[0], ids[order])
              and float(np.abs(got[1] - vecs[order]).max()) < 1e-6)
        print(f"[{n}/{len(files)}] {f.stem}: {len(ids)} vecs, +{added} new, {'ok' if ok else 'MISMATCH'}",
              flush=True)
        if not ok:
            bad.append(f.name)
        elif args.delete:
            d.close()
            f.unlink()
    if bad:
        sys.exit(f"mismatches: {bad}")
    print("all caches verified")


if __name__ == "__main__":
    main()
