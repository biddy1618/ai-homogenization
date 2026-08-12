"""Compute per-quarter homogenization metrics from the parsed answers table.

For each quarter we sample up to ``--sample`` answers and compute both raw and
length-controlled metrics:
  - raw MTLD / TTR / pairwise cosine (on full answer text)
  - length-controlled MTLD / TTR / pairwise cosine (each answer truncated to the
    first ``--lc-window`` tokens, so length can't bias the result)
  - mean answer length (tokens) and true posting volume for the quarter

Output: ``artifacts/quarterly_metrics.csv``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from metrics import hdd, mattr, mean_pairwise_cosine, mtld, ttr, tokenize, yule_i, yule_k


def compute_quarterly(
    df: pd.DataFrame,
    sample: int = 1000,
    min_answers: int = 30,
    lc_window: int = 100,
    seed: int = 42,
) -> pd.DataFrame:
    records: list[dict] = []
    rng = np.random.default_rng(seed)

    for quarter, group in tqdm(sorted(df.groupby("quarter")), desc="Quarters"):
        volume = len(group)  # true posting volume, before sampling
        if volume < min_answers:
            continue

        if volume > sample:
            group = group.iloc[rng.choice(volume, size=sample, replace=False)]

        texts = group["text"].tolist()
        tokenized = [tokenize(t) for t in texts]

        # Raw (length-uncontrolled) metrics.
        mtld_vals = [mtld(tk) for tk in tokenized]
        ttr_vals = [ttr(tk) for tk in tokenized]
        yule_k_vals = [yule_k(tk) for tk in tokenized]
        yule_i_vals = [yule_i(tk) for tk in tokenized]
        hdd_vals = [hdd(tk) for tk in tokenized]
        mattr_vals = [mattr(tk) for tk in tokenized]

        # Length-controlled: keep answers with >= lc_window tokens and truncate
        # each to exactly lc_window, so every answer contributes the same amount
        # of text. This removes the mechanical length bias from TTR and cosine.
        lc_tokens = [tk[:lc_window] for tk in tokenized if len(tk) >= lc_window]
        lc_ttr_vals = [ttr(tk) for tk in lc_tokens]
        lc_mtld_vals = [mtld(tk, min_tokens=lc_window) for tk in lc_tokens]
        lc_yule_k_vals = [yule_k(tk) for tk in lc_tokens]
        lc_yule_i_vals = [yule_i(tk) for tk in lc_tokens]
        lc_hdd_vals = [hdd(tk) for tk in lc_tokens]
        lc_mattr_vals = [mattr(tk) for tk in lc_tokens]
        lc_texts = [" ".join(tk) for tk in lc_tokens]

        records.append(
            {
                "quarter": quarter,
                "volume": volume,
                "n_sample": len(group),
                "n_lc": len(lc_tokens),
                "mean_len": float(np.mean([len(tk) for tk in tokenized])),
                "mean_mtld": float(np.nanmean(mtld_vals)),
                "mean_ttr": float(np.nanmean(ttr_vals)),
                "mean_yule_k": float(np.nanmean(yule_k_vals)),
                "mean_yule_i": float(np.nanmean(yule_i_vals)),
                "mean_hdd": float(np.nanmean(hdd_vals)),
                "mean_mattr": float(np.nanmean(mattr_vals)),
                "mean_pairwise_cosine": mean_pairwise_cosine(texts, seed=seed),
                "lc_mtld": float(np.nanmean(lc_mtld_vals)) if lc_mtld_vals else float("nan"),
                "lc_ttr": float(np.nanmean(lc_ttr_vals)) if lc_ttr_vals else float("nan"),
                "lc_yule_k": float(np.nanmean(lc_yule_k_vals)) if lc_yule_k_vals else float("nan"),
                "lc_yule_i": float(np.nanmean(lc_yule_i_vals)) if lc_yule_i_vals else float("nan"),
                "lc_hdd": float(np.nanmean(lc_hdd_vals)) if lc_hdd_vals else float("nan"),
                "lc_mattr": float(np.nanmean(lc_mattr_vals)) if lc_mattr_vals else float("nan"),
                "lc_pairwise_cosine": (
                    mean_pairwise_cosine(lc_texts, seed=seed)
                    if len(lc_texts) >= 2
                    else float("nan")
                ),
            }
        )

    return pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute per-quarter metrics")
    ap.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("data/processed/answers.parquet"),
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("artifacts/quarterly_metrics.csv"),
    )
    ap.add_argument("--sample", type=int, default=1000, help="Answers per quarter")
    ap.add_argument("--lc-window", type=int, default=100, help="Length-control token window")
    args = ap.parse_args()

    df = pd.read_parquet(args.input)
    result = compute_quarterly(df, sample=args.sample, lc_window=args.lc_window)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"Wrote {len(result)} quarters -> {args.output}")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
