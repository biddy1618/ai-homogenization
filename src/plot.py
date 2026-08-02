"""Plot per-quarter homogenization metrics with the ChatGPT-release marker.

Reads ``quarterly_metrics.csv`` and produces a stacked time-series figure with
raw vs length-controlled diversity/homogeneity, plus answer length and posting
volume. A vertical line marks 2022 Q4 (ChatGPT public release, Nov 2022).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

CHATGPT_QUARTER = "2022Q4"


def plot_metrics(df: pd.DataFrame, output: Path) -> None:
    quarters = df["quarter"].tolist()
    x = list(range(len(quarters)))

    fig, axes = plt.subplots(5, 1, figsize=(13, 15), sharex=True)

    marker_x = quarters.index(CHATGPT_QUARTER) if CHATGPT_QUARTER in quarters else None

    # Panel 0-2: raw vs length-controlled, one metric each.
    overlays = [
        ("mean_mtld", "lc_mtld", "MTLD (lexical diversity)", "tab:blue", "tab:cyan"),
        ("mean_ttr", "lc_ttr", "TTR (lexical diversity)", "tab:green", "tab:olive"),
        ("mean_pairwise_cosine", "lc_pairwise_cosine",
         "Answer-to-answer similarity\n(TF-IDF cosine)", "tab:red", "tab:orange"),
    ]
    for ax, (raw, lc, label, c_raw, c_lc) in zip(axes, overlays):
        ax.plot(x, df[raw], marker="o", ms=3, color=c_raw, label="raw")
        ax.plot(x, df[lc], marker="o", ms=3, color=c_lc, label="length-controlled (100 tok)")
        ax.set_ylabel(label, fontsize=9)
        ax.legend(fontsize=7, loc="best")

    # Panel 3: mean answer length (the confounder).
    axes[3].plot(x, df["mean_len"], marker="o", ms=3, color="tab:purple")
    axes[3].set_ylabel("Mean tokens / answer", fontsize=9)

    # Panel 4: true posting volume per quarter.
    axes[4].plot(x, df["volume"], marker="o", ms=3, color="tab:brown")
    axes[4].set_ylabel("Answers / quarter", fontsize=9)

    for ax in axes:
        ax.grid(True, alpha=0.3)
        if marker_x is not None:
            ax.axvline(marker_x, color="black", linestyle="--", alpha=0.7)

    if marker_x is not None:
        axes[0].text(
            marker_x, axes[0].get_ylim()[1], " ChatGPT (2022Q4)",
            va="top", fontsize=8,
        )

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(quarters, rotation=90, fontsize=6)
    axes[-1].set_xlabel("Quarter")
    fig.suptitle("Cross Validated — answer language over time (raw vs length-controlled)", fontsize=13)
    fig.tight_layout()

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    print(f"Saved figure -> {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Plot quarterly metrics")
    ap.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("artifacts/quarterly_metrics.csv"),
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("artifacts/homogenization_trends.png"),
    )
    args = ap.parse_args()

    df = pd.read_csv(args.input).sort_values("quarter").reset_index(drop=True)
    plot_metrics(df, args.output)


if __name__ == "__main__":
    main()
