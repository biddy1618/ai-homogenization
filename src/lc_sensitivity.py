"""Sensitivity check: does the length-controlled homogeneity result depend on
the chosen token window?

For each quarter we sample answers, truncate every answer with >= W tokens to
exactly W tokens, and recompute length-controlled pairwise cosine, TTR and MTLD
for several windows W. If the cosine curves stay flat across windows, the
"apparent homogenization is a length artifact" conclusion is robust.

Output: ``artifacts/lc_sensitivity.csv`` and ``artifacts/lc_sensitivity.png``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from metrics import mean_pairwise_cosine, mtld, ttr, tokenize

CHATGPT_QUARTER = "2022Q4"
WINDOWS = [50, 100, 150, 200]


def compute(
    df: pd.DataFrame,
    windows: list[int],
    sample: int = 1000,
    min_answers: int = 30,
    seed: int = 42,
) -> pd.DataFrame:
    records: list[dict] = []
    rng = np.random.default_rng(seed)

    for quarter, group in tqdm(sorted(df.groupby("quarter")), desc="Quarters"):
        volume = len(group)
        if volume < min_answers:
            continue
        if volume > sample:
            group = group.iloc[rng.choice(volume, size=sample, replace=False)]

        tokenized = [tokenize(t) for t in group["text"].tolist()]

        row: dict = {"quarter": quarter, "volume": volume}
        for w in windows:
            lc = [tk[:w] for tk in tokenized if len(tk) >= w]
            row[f"n_{w}"] = len(lc)
            if len(lc) >= 2:
                texts = [" ".join(tk) for tk in lc]
                row[f"cos_{w}"] = mean_pairwise_cosine(texts, seed=seed)
                row[f"ttr_{w}"] = float(np.mean([ttr(tk) for tk in lc]))
                row[f"mtld_{w}"] = float(
                    np.nanmean([mtld(tk, min_tokens=w) for tk in lc])
                )
            else:
                row[f"cos_{w}"] = float("nan")
                row[f"ttr_{w}"] = float("nan")
                row[f"mtld_{w}"] = float("nan")
        records.append(row)

    return pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)


def plot(df: pd.DataFrame, windows: list[int], output: Path) -> None:
    quarters = df["quarter"].tolist()
    x = list(range(len(quarters)))
    marker_x = quarters.index(CHATGPT_QUARTER) if CHATGPT_QUARTER in quarters else None

    fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)
    metrics = [
        ("cos", "Length-controlled pairwise cosine"),
        ("ttr", "Length-controlled TTR"),
        ("mtld", "Length-controlled MTLD"),
    ]
    cmap = plt.get_cmap("viridis")
    for ax, (prefix, label) in zip(axes, metrics):
        for i, w in enumerate(windows):
            ax.plot(
                x, df[f"{prefix}_{w}"], marker="o", ms=3,
                color=cmap(i / max(1, len(windows) - 1)), label=f"{w} tok",
            )
        ax.set_ylabel(label, fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, title="window", ncol=len(windows))
        if marker_x is not None:
            ax.axvline(marker_x, color="black", linestyle="--", alpha=0.7)

    if marker_x is not None:
        axes[0].text(marker_x, axes[0].get_ylim()[1], " ChatGPT (2022Q4)", va="top", fontsize=8)

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(quarters, rotation=90, fontsize=6)
    axes[-1].set_xlabel("Quarter")
    fig.suptitle("Length-control sensitivity across token windows", fontsize=13)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    print(f"Saved figure -> {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="LC window sensitivity check")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("-o", "--output", type=Path, default=Path("artifacts/lc_sensitivity.csv"))
    ap.add_argument("--plot", type=Path, default=Path("artifacts/lc_sensitivity.png"))
    ap.add_argument("--sample", type=int, default=1000)
    args = ap.parse_args()

    df = pd.read_parquet(args.input)
    result = compute(df, WINDOWS, sample=args.sample)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"Wrote {len(result)} quarters -> {args.output}")

    cos_cols = [f"cos_{w}" for w in WINDOWS]
    print(result[["quarter", *cos_cols]].to_string(index=False))

    plot(result, WINDOWS, args.plot)


if __name__ == "__main__":
    main()
