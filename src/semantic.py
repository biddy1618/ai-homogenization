"""Semantic homogenization metrics via LSA embeddings.

We fit a shared latent-semantic space (TF-IDF -> TruncatedSVD) on a global
sample of answers, then embed each quarter's answers into that space and measure
how tightly they cluster:

  - pairwise_cosine    mean cosine similarity between answers (higher = homogeneous)
  - centroid_variance  mean squared distance to the quarter centroid = 1 - ||mean||^2
                       (the "semantic centroid variance"; lower = homogeneous)
  - eff_dim            participation ratio of the embedding covariance (higher = spread)

Each is computed on full text (raw) and on the first ``--lc-window`` tokens
(length-controlled), mirroring the surface-metric pipeline.

LSA is a dependency-light stand-in for sentence embeddings; the embedding
backend (``fit_space`` / ``embed``) can be swapped for Sentence-BERT later.

Output: ``artifacts/semantic_metrics.csv`` and ``artifacts/semantic_trends.png``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm

from metrics import tokenize

CHATGPT_QUARTER = "2022Q4"


def fit_space(texts: list[str], n_components: int = 200, max_features: int = 20000,
              seed: int = 42) -> tuple[TfidfVectorizer, TruncatedSVD]:
    vec = TfidfVectorizer(max_features=max_features, stop_words="english",
                          sublinear_tf=True, min_df=2)
    X = vec.fit_transform(texts)
    n_components = min(n_components, X.shape[1] - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=seed)
    svd.fit(X)
    return vec, svd


def embed(vec: TfidfVectorizer, svd: TruncatedSVD, texts: list[str]) -> np.ndarray:
    z = svd.transform(vec.transform(texts))
    norms = np.linalg.norm(z, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return z / norms


def spread_metrics(v: np.ndarray) -> dict:
    n = len(v)
    if n < 2:
        return {"pairwise_cosine": float("nan"), "centroid_variance": float("nan"),
                "eff_dim": float("nan")}
    s = v.sum(axis=0)
    ss = float(s @ s)
    pairwise = (ss - n) / (n * (n - 1))          # mean of off-diagonal cosine
    centroid_variance = 1.0 - ss / (n * n)        # mean ||v_i - centroid||^2
    sv = np.linalg.svd(v - v.mean(axis=0), compute_uv=False)
    lam = sv ** 2
    eff_dim = float(lam.sum() ** 2 / np.sum(lam ** 2)) if lam.sum() > 0 else float("nan")
    return {"pairwise_cosine": pairwise, "centroid_variance": centroid_variance,
            "eff_dim": eff_dim}


def compute_quarterly(df: pd.DataFrame, sample: int = 800, lc_window: int = 100,
                      min_answers: int = 30, fit_sample: int = 30000,
                      seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    fit_idx = rng.choice(len(df), size=min(fit_sample, len(df)), replace=False)
    vec, svd = fit_space(df["text"].iloc[fit_idx].tolist(), seed=seed)

    records: list[dict] = []
    for quarter, group in tqdm(sorted(df.groupby("quarter")), desc="Quarters"):
        volume = len(group)
        if volume < min_answers:
            continue
        if volume > sample:
            group = group.iloc[rng.choice(volume, size=sample, replace=False)]

        texts = group["text"].tolist()
        raw = spread_metrics(embed(vec, svd, texts))

        tokenized = [tokenize(t) for t in texts]
        lc_texts = [" ".join(tk[:lc_window]) for tk in tokenized if len(tk) >= lc_window]
        lc = spread_metrics(embed(vec, svd, lc_texts)) if len(lc_texts) >= 2 else {
            "pairwise_cosine": float("nan"), "centroid_variance": float("nan"),
            "eff_dim": float("nan")}

        rec = {"quarter": quarter, "volume": volume, "n_sample": len(group),
               "n_lc": len(lc_texts)}
        rec.update({f"sem_{k}": v for k, v in raw.items()})
        rec.update({f"lc_sem_{k}": v for k, v in lc.items()})
        records.append(rec)

    return pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)


def plot_metrics(df: pd.DataFrame, output: Path, corpus: str = "Cross Validated") -> None:
    quarters = df["quarter"].tolist()
    x = list(range(len(quarters)))
    marker_x = quarters.index(CHATGPT_QUARTER) if CHATGPT_QUARTER in quarters else None

    panels = [
        ("sem_pairwise_cosine", "lc_sem_pairwise_cosine",
         "Semantic pairwise cosine\n(higher = homogeneous)", "tab:red", "tab:orange"),
        ("sem_centroid_variance", "lc_sem_centroid_variance",
         "Semantic centroid variance\n(lower = homogeneous)", "tab:blue", "tab:cyan"),
        ("sem_eff_dim", "lc_sem_eff_dim",
         "Effective dimensionality\n(higher = spread)", "tab:green", "tab:olive"),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)
    for ax, (raw, lc, label, c_raw, c_lc) in zip(axes, panels):
        ax.plot(x, df[raw], marker="o", ms=3, color=c_raw, label="raw")
        ax.plot(x, df[lc], marker="o", ms=3, color=c_lc, label="length-controlled (100 tok)")
        ax.set_ylabel(label, fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, loc="best")
        if marker_x is not None:
            ax.axvline(marker_x, color="black", linestyle="--", alpha=0.7)
    if marker_x is not None:
        axes[0].text(marker_x, axes[0].get_ylim()[1], " ChatGPT (2022Q4)", va="top", fontsize=8)

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(quarters, rotation=90, fontsize=6)
    axes[-1].set_xlabel("Quarter")
    fig.suptitle(f"{corpus} — semantic homogenization (LSA embeddings)", fontsize=13)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    print(f"Saved figure -> {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Semantic homogenization metrics (LSA)")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("-o", "--output", type=Path, default=Path("artifacts/semantic_metrics.csv"))
    ap.add_argument("--plot", type=Path, default=Path("artifacts/semantic_trends.png"))
    ap.add_argument("--sample", type=int, default=800)
    ap.add_argument("--lc-window", type=int, default=100)
    ap.add_argument("--corpus", default="Cross Validated")
    args = ap.parse_args()

    df = pd.read_parquet(args.input)
    result = compute_quarterly(df, sample=args.sample, lc_window=args.lc_window)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"Wrote {len(result)} quarters -> {args.output}")
    print(result.to_string(index=False))
    plot_metrics(result, args.plot, corpus=args.corpus)


if __name__ == "__main__":
    main()
