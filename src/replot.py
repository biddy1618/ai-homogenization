"""Redraw plots from saved CSVs (no embedding, no recomputation).

    python src/replot.py            # families 5, 13 (incl. topic-k), 14 for all sources

Families 8 and 9 redraw by re-running their scripts (``significance.py --all``,
``cog_load_compare.py``, ``cog_load_test.py``), which only read CSVs.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from paths import ALL_SOURCES, LABEL, bge_dir, source_dir, topic_k_dir
from semantic_bert import plot_metrics
from topic_decomposition import plot_decomposition

WHOLE = SimpleNamespace(mode="whole", raw_label="whole text",
                        lc_label="opening window (first 120 model tokens)")


def main() -> None:
    n = 0
    for folder, label, _ in ALL_SOURCES:
        d = source_dir(folder)
        plot_metrics(pd.read_csv(d / "data" / "5_semantic_bert.csv"), d / "5_semantic_bert.png", label, WHOLE)
        n += 1
        b = bge_dir(folder)
        if (b / "data" / "5_semantic_bert.csv").exists():
            plot_metrics(pd.read_csv(b / "data" / "5_semantic_bert.csv"), b / "5_semantic_bert.png", label,
                         WHOLE, encoder="bge-small")
            n += 1
        for dd, suf in ((d, ""), (topic_k_dir(folder), "_k25"), (topic_k_dir(folder), "_k100")):
            f = dd / "data" / f"13_topic_decomposition{suf}.csv"
            if f.exists():
                title = label + (f" (K={suf[2:]})" if suf else "")
                plot_decomposition(pd.read_csv(f), dd / f"13_topic_decomposition{suf}.png", title,
                                   pd.read_csv(dd / "data" / f"13_decomposition_significance{suf}.csv"))
                n += 1
    subprocess.run([sys.executable, str(Path(__file__).with_name("tag_topics.py")), "--all",
                    "--replot"], check=True)
    print(f"redrew {n} plots + family 14")


if __name__ == "__main__":
    main()
