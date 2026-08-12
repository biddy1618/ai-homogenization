"""Topic modeling and topic-diversity drift over time (LDA).

Tests whether the *mix of topics* on Cross Validated changed after ChatGPT —
a potential confound for the homogenization metrics. We fit an LDA topic model
on a global sample, then per quarter measure:

  - topic_entropy   Shannon entropy (bits) of the quarter's aggregate topic mix;
                    lower = topics narrowed (less diverse content)
  - doc_entropy     mean per-answer topic entropy (how topically mixed answers are)
  - t0..t{K-1}      aggregate proportion of each topic that quarter

We also report the Jensen-Shannon divergence between the pre- and post-ChatGPT
aggregate topic distributions (magnitude of the topic shift).

Output: ``artifacts/topic_metrics.csv`` and ``artifacts/topic_trends.png``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from tqdm import tqdm

CHATGPT_QUARTER = "2022Q4"


def build_model(texts: list[str], n_topics: int = 15, seed: int = 42
                ) -> tuple[CountVectorizer, LatentDirichletAllocation]:
    cv = CountVectorizer(stop_words="english", max_features=10000, min_df=5, max_df=0.5)
    X = cv.fit_transform(texts)
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=seed,
                                    learning_method="online", batch_size=2048, max_iter=10)
    lda.fit(X)
    return cv, lda


def topic_dist(cv: CountVectorizer, lda: LatentDirichletAllocation, texts: list[str]) -> np.ndarray:
    return lda.transform(cv.transform(texts))


def entropy_bits(p: np.ndarray) -> float:
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def jensen_shannon(p: np.ndarray, q: np.ndarray) -> float:
    m = 0.5 * (p + q)
    return float(0.5 * _kl(p, m) + 0.5 * _kl(q, m))


def _kl(p: np.ndarray, q: np.ndarray) -> float:
    mask = p > 0
    return float(np.sum(p[mask] * np.log2(p[mask] / q[mask])))


def top_words(cv: CountVectorizer, lda: LatentDirichletAllocation, n: int = 8) -> list[str]:
    vocab = np.array(cv.get_feature_names_out())
    return [", ".join(vocab[comp.argsort()[::-1][:n]]) for comp in lda.components_]


def compute_quarterly(df: pd.DataFrame, n_topics: int = 15, sample: int = 800,
                      min_answers: int = 30, fit_sample: int = 30000, seed: int = 42):
    rng = np.random.default_rng(seed)
    fit_idx = rng.choice(len(df), size=min(fit_sample, len(df)), replace=False)
    cv, lda = build_model(df["text"].iloc[fit_idx].tolist(), n_topics=n_topics, seed=seed)

    records: list[dict] = []
    weights: list[tuple[str, int, np.ndarray]] = []
    for quarter, group in tqdm(sorted(df.groupby("quarter")), desc="Quarters"):
        volume = len(group)
        if volume < min_answers:
            continue
        if volume > sample:
            group = group.iloc[rng.choice(volume, size=sample, replace=False)]

        td = topic_dist(cv, lda, group["text"].tolist())
        mean_td = td.mean(axis=0)
        rec = {"quarter": quarter, "volume": volume, "n_sample": len(group),
               "topic_entropy": entropy_bits(mean_td),
               "doc_entropy": float(np.mean([entropy_bits(r) for r in td]))}
        rec.update({f"t{i}": float(mean_td[i]) for i in range(n_topics)})
        records.append(rec)
        weights.append((quarter, len(group), mean_td))

    result = pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)
    return result, cv, lda, weights


def prepost_jsd(weights, n_topics: int) -> float:
    pre = np.zeros(n_topics)
    post = np.zeros(n_topics)
    pre_n = post_n = 0
    for quarter, n, td in weights:
        if quarter < CHATGPT_QUARTER:
            pre += n * td
            pre_n += n
        else:
            post += n * td
            post_n += n
    if pre_n == 0 or post_n == 0:
        return float("nan")
    return jensen_shannon(pre / pre_n, post / post_n)


def plot_metrics(df: pd.DataFrame, n_topics: int, output: Path, corpus: str = "Cross Validated") -> None:
    quarters = df["quarter"].tolist()
    x = list(range(len(quarters)))
    marker_x = quarters.index(CHATGPT_QUARTER) if CHATGPT_QUARTER in quarters else None

    fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)

    axes[0].plot(x, df["topic_entropy"], marker="o", ms=3, color="tab:purple",
                 label="aggregate topic entropy")
    axes[0].plot(x, df["doc_entropy"], marker="o", ms=3, color="tab:gray",
                 label="mean per-answer topic entropy")
    axes[0].axhline(np.log2(n_topics), color="black", linestyle=":", alpha=0.5,
                    label=f"max ({np.log2(n_topics):.2f} bits)")
    axes[0].set_ylabel("Topic diversity (bits)", fontsize=9)
    axes[0].legend(fontsize=7, loc="best")

    topic_cols = [f"t{i}" for i in range(n_topics)]
    axes[1].stackplot(x, *[df[c] for c in topic_cols],
                      labels=[f"T{i}" for i in range(n_topics)])
    axes[1].set_ylabel("Topic proportion", fontsize=9)
    axes[1].set_ylim(0, 1)
    axes[1].legend(fontsize=6, ncol=n_topics, loc="lower center", bbox_to_anchor=(0.5, 1.0))

    for ax in axes:
        ax.grid(True, alpha=0.3)
        if marker_x is not None:
            ax.axvline(marker_x, color="black", linestyle="--", alpha=0.7)
    if marker_x is not None:
        axes[0].text(marker_x, axes[0].get_ylim()[1], " ChatGPT (2022Q4)", va="top", fontsize=8)

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(quarters, rotation=90, fontsize=6)
    axes[-1].set_xlabel("Quarter")
    fig.suptitle(f"{corpus} — topic diversity and drift over time (LDA)", fontsize=13)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    print(f"Saved figure -> {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="LDA topic diversity over time")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("-o", "--output", type=Path, default=Path("artifacts/topic_metrics.csv"))
    ap.add_argument("--plot", type=Path, default=Path("artifacts/topic_trends.png"))
    ap.add_argument("--n-topics", type=int, default=15)
    ap.add_argument("--sample", type=int, default=800)
    ap.add_argument("--corpus", default="Cross Validated")
    args = ap.parse_args()

    df = pd.read_parquet(args.input)
    result, cv, lda, weights = compute_quarterly(df, n_topics=args.n_topics, sample=args.sample)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"Wrote {len(result)} quarters -> {args.output}")

    print("\nTopics (top words):")
    for i, words in enumerate(top_words(cv, lda)):
        print(f"  T{i:2d}: {words}")

    jsd = prepost_jsd(weights, args.n_topics)
    print(f"\nPre vs post-ChatGPT topic-distribution JSD: {jsd:.4f} (0=identical, 1=disjoint)")
    print(result[["quarter", "topic_entropy", "doc_entropy"]].to_string(index=False))

    plot_metrics(result, args.n_topics, args.plot, corpus=args.corpus)


if __name__ == "__main__":
    main()
