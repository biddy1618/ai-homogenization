"""Dynamic *semantic* topic modeling (BERTopic on cached MiniLM embeddings).

Unlike ``topics.py`` (LDA, bag-of-words, fixed 15 topics fit once on the whole
corpus), this discovers topics bottom-up from the contextual embeddings:

    embed (MiniLM, reused) -> UMAP (reduce) -> HDBSCAN (cluster) -> c-TF-IDF (label)

Because topics are density clusters in a fixed shared embedding space, a genuinely
new theme (e.g. post-2022 LLM/prompting questions) forms its OWN cluster instead of
being smeared across pre-defined topics — so topic *emergence* is visible.

Two questions answered:
  1. Emergence / drift  -> each topic's share per quarter (6a). Topics ranked both by
     size and by post-minus-pre-ChatGPT share increase (which topics grew).
  2. Confound test      -> within-topic pairwise cosine over time vs the unconditioned
     (overall) pairwise cosine (6b). If the recent BERT convergence is just a topic-mix
     shift, the OVERALL line rises while the WITHIN-TOPIC line stays flat.

Embeddings are the SAME all-MiniLM-L6-v2 vectors used by ``semantic_bert.py`` (one
model, no torch — provisioned via the GCS mirror). BERTopic is fed precomputed
embeddings, so it never needs a sentence-transformers/torch backend.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from metrics import tokenize
from semantic import spread_metrics, bootstrap_pairwise_samples
from semantic_bert import load_model, embed_texts
from embed_cache import load_cache, save_cache, cached_embed

CHATGPT_QUARTER = "2022Q4"


def sample_corpus(df: pd.DataFrame, sample: int, min_answers: int, seed: int) -> pd.DataFrame:
    """Per-quarter sample so every quarter is represented for the time axis."""
    rng = np.random.default_rng(seed)
    parts = []
    for _, group in sorted(df.groupby("quarter")):
        if len(group) < min_answers:
            continue
        if len(group) > sample:
            group = group.iloc[rng.choice(len(group), size=sample, replace=False)]
        parts.append(group)
    return pd.concat(parts).reset_index(drop=True)


def fit_topics(texts: list[str], embeddings: np.ndarray, min_cluster_size: int, seed: int):
    """Cluster embeddings into data-driven topics; return the model and assignments."""
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0,
                      metric="cosine", random_state=seed)
    # "leaf" yields many fine-grained clusters instead of a few giant ones ("eom").
    hdbscan_model = HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean",
                            cluster_selection_method="leaf", prediction_data=True)
    # Strip stopwords so c-TF-IDF labels are content words, not "the of to is".
    vectorizer_model = CountVectorizer(stop_words="english", min_df=5, max_df=0.5)
    topic_model = BERTopic(umap_model=umap_model, hdbscan_model=hdbscan_model,
                           vectorizer_model=vectorizer_model,
                           calculate_probabilities=False, verbose=True)
    topics, _ = topic_model.fit_transform(texts, embeddings=embeddings)
    return topic_model, np.asarray(topics)


def topic_shares(quarters: np.ndarray, topics: np.ndarray) -> pd.DataFrame:
    """Per-quarter share of each topic (outliers, topic -1, excluded)."""
    d = pd.DataFrame({"quarter": quarters, "topic": topics})
    d = d[d["topic"] != -1]
    counts = d.groupby(["quarter", "topic"]).size().rename("count").reset_index()
    totals = d.groupby("quarter").size().rename("total")
    counts = counts.merge(totals, on="quarter")
    counts["share"] = counts["count"] / counts["total"]
    return counts


def topic_summary(shares: pd.DataFrame, labels: dict[int, str], sizes: dict[int, int]
                  ) -> pd.DataFrame:
    """Pre/post-ChatGPT mean share per topic + the growth delta (emergence signal)."""
    rows = []
    for topic, g in shares.groupby("topic"):
        pre = g.loc[g["quarter"] < CHATGPT_QUARTER, "share"]
        post = g.loc[g["quarter"] >= CHATGPT_QUARTER, "share"]
        pre_share = float(pre.mean()) if len(pre) else 0.0
        post_share = float(post.mean()) if len(post) else 0.0
        rows.append({"topic": topic, "size": sizes.get(topic, 0),
                     "pre_share": pre_share, "post_share": post_share,
                     "delta": post_share - pre_share, "top_words": labels.get(topic, "")})
    return pd.DataFrame(rows).sort_values("delta", ascending=False).reset_index(drop=True)


def within_topic_similarity(quarters: np.ndarray, topics: np.ndarray, emb: np.ndarray,
                            n_boot: int = 0, ci: float = 0.95, rng=None) -> pd.DataFrame:
    """Overall vs topic-conditioned pairwise cosine per quarter (the confound test).

    With ``n_boot`` > 0, also returns percentile-bootstrap CIs: the overall line resamples
    the quarter's answers; the within-topic line resamples *within each topic* (stratified)
    and recombines with the same size weights.
    """
    alpha = 1.0 - ci
    records = []
    for quarter in sorted(set(quarters)):
        qidx = np.where(quarters == quarter)[0]
        overall = spread_metrics(emb[qidx])["pairwise_cosine"]
        num, den = 0.0, 0
        boot_overall = bootstrap_pairwise_samples(emb[qidx], n_boot, rng) if n_boot else None
        boot_num = np.zeros(n_boot) if n_boot else None
        boot_den = 0
        for t in set(topics[qidx]):
            if t == -1:
                continue
            tidx = qidx[topics[qidx] == t]
            if len(tidx) < 2:
                continue
            pc = spread_metrics(emb[tidx])["pairwise_cosine"]
            num += pc * len(tidx)
            den += len(tidx)
            if n_boot:
                s = bootstrap_pairwise_samples(emb[tidx], n_boot, rng)
                if s is not None:
                    s = np.where(np.isfinite(s), s, pc)   # degenerate replicates -> point est
                    boot_num += s * len(tidx)
                    boot_den += len(tidx)
        within = num / den if den else float("nan")
        rec = {"quarter": quarter, "n": len(qidx),
               "overall_cosine": overall, "within_topic_cosine": within}
        if n_boot:
            if boot_overall is not None:
                rec["overall_cosine_lo"] = float(np.nanpercentile(boot_overall, 100 * alpha / 2))
                rec["overall_cosine_hi"] = float(np.nanpercentile(boot_overall, 100 * (1 - alpha / 2)))
            else:
                rec["overall_cosine_lo"] = rec["overall_cosine_hi"] = float("nan")
            if boot_den:
                bw = boot_num / boot_den
                rec["within_topic_cosine_lo"] = float(np.nanpercentile(bw, 100 * alpha / 2))
                rec["within_topic_cosine_hi"] = float(np.nanpercentile(bw, 100 * (1 - alpha / 2)))
            else:
                rec["within_topic_cosine_lo"] = rec["within_topic_cosine_hi"] = float("nan")
        records.append(rec)
    return pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)


def _series(shares: pd.DataFrame, quarters: list[str], topic: int) -> list[float]:
    s = shares[shares["topic"] == topic].set_index("quarter")["share"]
    return [float(s.get(q, 0.0)) for q in quarters]


def plot_topics_over_time(shares: pd.DataFrame, summary: pd.DataFrame, labels: dict[int, str],
                          output: Path, top_k: int, corpus: str) -> None:
    quarters = sorted(shares["quarter"].unique())
    x = list(range(len(quarters)))
    marker_x = quarters.index(CHATGPT_QUARTER) if CHATGPT_QUARTER in quarters else None

    largest = summary.sort_values("size", ascending=False).head(top_k)["topic"].tolist()
    emergent = summary.sort_values("delta", ascending=False).head(top_k)["topic"].tolist()

    fig, axes = plt.subplots(2, 1, figsize=(14, 11), sharex=True)
    for ax, topics_sel, title in [
        (axes[0], largest, f"Largest {top_k} topics"),
        (axes[1], emergent, f"Top {top_k} emergent topics (largest post-minus-pre share gain)"),
    ]:
        for t in topics_sel:
            ax.plot(x, _series(shares, quarters, t), marker="o", ms=2,
                    label=f"[{t}] {labels.get(t, '')[:40]}")
        ax.set_ylabel("share of quarter")
        ax.set_title(title, fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=6, loc="upper left", ncol=2)
        if marker_x is not None:
            ax.axvline(marker_x, color="black", linestyle="--", alpha=0.7)
    if marker_x is not None:
        axes[0].text(marker_x, axes[0].get_ylim()[1], " ChatGPT (2022Q4)", va="top", fontsize=8)

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(quarters, rotation=90, fontsize=6)
    axes[-1].set_xlabel("Quarter")
    fig.suptitle(f"{corpus} — semantic topics over time (BERTopic / MiniLM)", fontsize=13)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    print(f"Saved figure -> {output}")


def plot_within_topic(wts: pd.DataFrame, output: Path, corpus: str, note: str = "",
                      footnote: str = "") -> None:
    quarters = wts["quarter"].tolist()
    x = list(range(len(quarters)))
    marker_x = quarters.index(CHATGPT_QUARTER) if CHATGPT_QUARTER in quarters else None

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(x, wts["overall_cosine"], marker="o", ms=3, color="tab:red",
            label="overall pairwise cosine (unconditioned)")
    ax.plot(x, wts["within_topic_cosine"], marker="o", ms=3, color="tab:blue",
            label="within-topic pairwise cosine (topic-controlled)")
    if "overall_cosine_lo" in wts.columns:
        ax.fill_between(x, wts["overall_cosine_lo"], wts["overall_cosine_hi"],
                        color="tab:red", alpha=0.2)
    if "within_topic_cosine_lo" in wts.columns:
        ax.fill_between(x, wts["within_topic_cosine_lo"], wts["within_topic_cosine_hi"],
                        color="tab:blue", alpha=0.2)
    ax.set_ylabel("mean pairwise cosine\n(higher = more homogeneous)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="best")
    if marker_x is not None:
        ax.axvline(marker_x, color="black", linestyle="--", alpha=0.7)
        ax.text(marker_x, ax.get_ylim()[1], " ChatGPT (2022Q4)", va="top", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(quarters, rotation=90, fontsize=6)
    ax.set_xlabel("Quarter")
    fig.suptitle(f"{corpus} \u2014 Real style change, or just a shift in topics? "
                 f"(within-topic vs overall){note}", fontsize=13)
    if footnote:
        fig.text(0.5, -0.01, footnote, ha="center", va="top", fontsize=8,
                 color="dimgray", wrap=True)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    print(f"Saved figure -> {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Dynamic semantic topic modeling (BERTopic)")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("--data-dir", type=Path, required=True, help="Folder for output CSVs")
    ap.add_argument("--plots-dir", type=Path, required=True, help="Folder for output PNGs")
    ap.add_argument("--cache-dir", type=Path, default=Path("data/models"))
    ap.add_argument("--sample", type=int, default=800, help="Max answers per quarter")
    ap.add_argument("--min-cluster-size", type=int, default=150)
    ap.add_argument("--lc-window", type=int, default=100, help="Length-control token window")
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--corpus", default="Cross Validated")
    ap.add_argument("--emb-cache-dir", type=Path, default=Path("data/embeddings"),
                    help="Folder for the persistent id-keyed embedding cache")
    ap.add_argument("--no-emb-cache", action="store_true", help="Bypass the embedding cache")
    ap.add_argument("--bootstrap", type=int, default=1000,
                    help="Bootstrap resamples for within-topic/overall CIs (0 = off)")
    ap.add_argument("--ci", type=float, default=0.95, help="Confidence level for the CIs")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df = pd.read_parquet(args.input)
    sampled = sample_corpus(df, args.sample, min_answers=30, seed=args.seed)
    ids = sampled["id"].tolist()
    texts = sampled["text"].tolist()
    quarters = sampled["quarter"].to_numpy()
    print(f"Embedding {len(texts):,} answers ({len(set(quarters))} quarters)...")

    if args.no_emb_cache:
        raw_cache = lc_cache = None
    else:
        tag = args.input.stem
        raw_path = args.emb_cache_dir / f"{tag}_minilm_raw.npz"
        lc_path = args.emb_cache_dir / f"{tag}_minilm_lc{args.lc_window}.npz"
        raw_cache, lc_cache = load_cache(raw_path), load_cache(lc_path)

    model = load_model(args.cache_dir)
    emb = cached_embed(model, ids, texts, embed_texts, raw_cache)

    print(f"Clustering (min_cluster_size={args.min_cluster_size})...")
    topic_model, topics = fit_topics(texts, emb, args.min_cluster_size, args.seed)

    info = topic_model.get_topic_info()
    n_topics = int((info["Topic"] != -1).sum())
    n_outlier = int((topics == -1).sum())
    print(f"Found {n_topics} topics; {n_outlier:,}/{len(topics):,} answers are outliers.")

    labels = {int(r.Topic): r.Name for r in info.itertuples()}
    sizes = {int(r.Topic): int(r.Count) for r in info.itertuples()}

    shares = topic_shares(quarters, topics)
    summary = topic_summary(shares, labels, sizes)
    boot_rng = np.random.default_rng(args.seed + 1)
    wts = within_topic_similarity(quarters, topics, emb,
                                  n_boot=args.bootstrap, ci=args.ci, rng=boot_rng)

    args.data_dir.mkdir(parents=True, exist_ok=True)
    shares.to_csv(args.data_dir / "6_topics_over_time.csv", index=False)
    summary.to_csv(args.data_dir / "6_topic_summary.csv", index=False)
    wts.to_csv(args.data_dir / "6_within_topic_similarity.csv", index=False)
    print(f"Wrote CSVs -> {args.data_dir}")
    print("\nTop 10 emergent topics (post - pre ChatGPT share gain):")
    print(summary.head(10).to_string(index=False))

    wt_foot = (f"Random sample of up to {args.sample} answers/quarter; {n_topics} data-driven "
               f"topics via HDBSCAN. {n_outlier:,}/{len(topics):,} "
               f"({100 * n_outlier / len(topics):.0f}%) are topic-outliers, excluded from the "
               "within-topic line. Flat within-topic while overall rises = a topic-mix shift, "
               "not style homogenization.")
    plot_topics_over_time(shares, summary, labels,
                          args.plots_dir / "6a_topics_over_time.png", args.top_k, args.corpus)
    plot_within_topic(wts, args.plots_dir / "6b_within_topic_similarity.png", args.corpus,
                      footnote=wt_foot)

    # P1: length-controlled within-topic — same topic assignments, but embeddings of the
    # first lc_window tokens (answers shorter than the window are excluded, matching the
    # length-control convention in semantic_bert.py). Closes the raw-embedding caveat.
    tokenized = [tokenize(t) for t in texts]
    lc_mask = np.array([len(tk) >= args.lc_window for tk in tokenized])
    if int(lc_mask.sum()) >= 2:
        lc_ids = [i for i, tk in zip(ids, tokenized) if len(tk) >= args.lc_window]
        lc_texts = [" ".join(tk[:args.lc_window]) for tk in tokenized if len(tk) >= args.lc_window]
        print(f"Length-controlled within-topic on {int(lc_mask.sum()):,} answers "
              f"(>= {args.lc_window} tokens)...")
        emb_lc = cached_embed(model, lc_ids, lc_texts, embed_texts, lc_cache)
        wts_lc = within_topic_similarity(quarters[lc_mask], topics[lc_mask], emb_lc,
                                         n_boot=args.bootstrap, ci=args.ci, rng=boot_rng)
        wts_lc.to_csv(args.data_dir / "6_within_topic_similarity_lc.csv", index=False)
        print(f"Wrote CSV -> {args.data_dir / '6_within_topic_similarity_lc.csv'}")
        plot_within_topic(wts_lc, args.plots_dir / "6c_within_topic_similarity_lc.png",
                          args.corpus, note=" \u2014 length-controlled (first 100 tokens)",
                          footnote=wt_foot)
    else:
        print("Not enough answers >= lc-window tokens for length-controlled within-topic.")

    if not args.no_emb_cache:
        save_cache(raw_path, raw_cache)
        save_cache(lc_path, lc_cache)
        print(f"Embedding cache -> {args.emb_cache_dir} "
              f"({len(raw_cache):,} raw / {len(lc_cache):,} lc vectors)")


if __name__ == "__main__":
    main()
