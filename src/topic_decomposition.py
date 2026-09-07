"""#13 — decompose the family-5 aggregate similarity into within-topic + between-topic.

The story so far: aggregate answer-to-answer similarity (family 5) rises after ChatGPT,
but every *within-topic* control (families 6/10/11/12) is flat. That logically forces the
rise to live at the *topic* level rather than in writing style. This script measures that
directly and positively, instead of by elimination.

For each quarter we sample answers (cache-backed MiniLM vectors), assign every answer a
*stable* topic via a single global K-means (so topics mean the same thing across time and
there are no dropped outliers), then split the mean pairwise cosine into:

  overall = p_within * within_cosine + p_between * between_cosine

Because there are many topics, almost all *pairs* are cross-topic, so ``between_cosine``
dominates ``overall``. We also report:

* ``eff_topics``  — effective number of topics = exp(Shannon entropy of the topic mix).
  A drop after ChatGPT = topic diversity shrinking (topic-level homogenization).
* ``comp_jsd``    — Jensen-Shannon divergence of the quarter's topic mix vs the pooled
  pre-ChatGPT mix. A rise = the *composition* of topics drifting.
* ``between_centroid_cosine`` — mean mutual cosine of the topic centroids. A rise = topics
  moving closer together in meaning space.
* ``mc_*``        — the same overall/between cosine after removing each quarter's mean
  vector (anisotropy control). If ``between_cosine`` rises but ``mc_between_cosine`` goes
  flat, the "topics converging" signal was just a growing global common direction
  (an embedding artifact), not genuine relative convergence.

All pairwise quantities use the closed-form ``(||sum v||^2 - n) / (n(n-1))`` identity, so
each quarter is O(n*d) with no n-by-n matrix. Runs entirely on cached embeddings (offline).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from sklearn.cluster import KMeans

from semantic_bert import load_model, embed_texts
from embed_cache import load_cache, save_cache, cached_embed
from significance import _q_ord, analyze_metric

CHATGPT_QUARTER = "2022Q4"

# Series we run the interrupted-time-series / Mann-Kendall significance test on.
SIG_METRICS = (
    "overall_cosine", "within_cosine", "between_cosine",
    "eff_topics", "comp_jsd", "between_centroid_cosine", "mc_between_cosine",
)


def sample_quarters(df: pd.DataFrame, sample: int, min_answers: int, seed: int):
    """Mirror family-5 sampling (same RNG order) so ids overlap the embedding cache."""
    rng = np.random.default_rng(seed)
    ids, texts, quarters = [], [], []
    for quarter, group in sorted(df.groupby("quarter")):
        volume = len(group)
        if volume < min_answers:
            continue
        if volume > sample:
            group = group.iloc[rng.choice(volume, size=sample, replace=False)]
        ids.extend(int(i) for i in group["id"].tolist())
        texts.extend(group["text"].tolist())
        quarters.extend([quarter] * len(group))
    return ids, texts, np.asarray(quarters)


def _pairwise_pieces(V: np.ndarray, labels: np.ndarray, K: int) -> dict:
    """Within/between mean pairwise cosine for one quarter, via closed-form sums."""
    n = len(V)
    if n < 2:
        return {}
    St = np.zeros((K, V.shape[1]))
    np.add.at(St, labels, V)                       # per-topic sum vectors
    nt = np.bincount(labels, minlength=K).astype(float)
    sst = np.einsum("kd,kd->k", St, St)            # ||S_t||^2 per topic
    S = V.sum(0)
    ss = float(S @ S)

    within_sum = float((sst - nt).sum())           # sum_t (||S_t||^2 - n_t)
    within_count = float((nt * (nt - 1)).sum())
    between_sum = ss - float(sst.sum())
    between_count = n * (n - 1) - within_count

    overall = (ss - n) / (n * (n - 1))
    within = within_sum / within_count if within_count > 0 else float("nan")
    between = between_sum / between_count if between_count > 0 else float("nan")
    return {
        "overall_cosine": overall,
        "within_cosine": within,
        "between_cosine": between,
        "p_within": within_count / (n * (n - 1)),
        "_nt": nt,
        "_St": St,
        "_sst": sst,
    }


def decompose_quarter(V: np.ndarray, labels: np.ndarray, K: int) -> dict:
    n = len(V)
    rec: dict = {"n": n}
    base = _pairwise_pieces(V, labels, K)
    if not base:
        return rec
    nt, St, sst = base.pop("_nt"), base.pop("_St"), base.pop("_sst")
    rec.update(base)

    present = nt > 0
    T = int(present.sum())
    rec["n_topics"] = T

    # topic-diversity: effective number of topics = exp(entropy of the mix)
    p = nt[present] / n
    entropy = float(-(p * np.log(p)).sum())
    rec["topic_entropy"] = entropy
    rec["eff_topics"] = float(np.exp(entropy))
    rec["_prop"] = nt / n                            # full-K proportion vector (for JSD)

    # between-topic geometry: mutual cosine of the (unit) topic centroids
    if T > 1:
        C = St[present] / np.sqrt(sst[present])[:, None]
        Sc = C.sum(0)
        rec["between_centroid_cosine"] = float((Sc @ Sc - T) / (T * (T - 1)))
    else:
        rec["between_centroid_cosine"] = float("nan")

    # anisotropy control: remove the quarter mean direction, recompute
    mu = V.mean(0)
    Vc = V - mu
    nn = np.linalg.norm(Vc, axis=1)
    keep = nn > 1e-8
    if keep.sum() >= 2:
        Vc = Vc[keep] / nn[keep][:, None]
        mc = _pairwise_pieces(Vc, labels[keep], K)
        rec["mc_overall_cosine"] = mc.get("overall_cosine", float("nan"))
        rec["mc_between_cosine"] = mc.get("between_cosine", float("nan"))
    else:
        rec["mc_overall_cosine"] = rec["mc_between_cosine"] = float("nan")
    return rec


def compute(df: pd.DataFrame, model, sample: int, K: int, min_answers: int, seed: int,
            raw_cache: dict | None) -> pd.DataFrame:
    ids, texts, quarters = sample_quarters(df, sample, min_answers, seed)
    print(f"Sampled {len(ids):,} answers across {len(set(quarters))} quarters; "
          f"embedding (cache-backed)...")
    V = cached_embed(model, ids, texts, embed_texts, raw_cache)

    print(f"Global K-means into K={K} stable topics...")
    labels = KMeans(n_clusters=K, random_state=seed, n_init=4).fit_predict(V)

    pre_mask = np.array([_q_ord(q) < _q_ord(CHATGPT_QUARTER) for q in quarters])
    records, props = [], {}
    for quarter in sorted(set(quarters)):
        m = quarters == quarter
        rec = decompose_quarter(V[m], labels[m], K)
        rec["quarter"] = quarter
        rec["n_sample"] = int(m.sum())
        props[quarter] = rec.pop("_prop", None)
        records.append(rec)

    # composition drift: JSD of each quarter's topic mix vs the pooled pre-ChatGPT mix
    pre_props = [decompose_quarter(V[pre_mask], labels[pre_mask], K).get("_prop")]
    pre_prop = _pairwise_pieces(V[pre_mask], labels[pre_mask], K)
    base_counts = np.bincount(labels[pre_mask], minlength=K).astype(float)
    base_dist = base_counts / base_counts.sum()
    for rec in records:
        q = rec["quarter"]
        pr = props.get(q)
        if pr is not None:
            rec["comp_jsd"] = float(jensenshannon(pr, base_dist, base=2) ** 2)
        else:
            rec["comp_jsd"] = float("nan")

    out = pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)
    cols = ["quarter", "n", "n_sample", "n_topics", "p_within", "overall_cosine",
            "within_cosine", "between_cosine", "mc_overall_cosine", "mc_between_cosine",
            "between_centroid_cosine", "eff_topics", "topic_entropy", "comp_jsd"]
    return out[[c for c in cols if c in out.columns]]


def run_significance(df: pd.DataFrame, corpus: str, break_quarter: str,
                     hac_lags: int = 4) -> pd.DataFrame:
    d = df.copy()
    d["_t"] = d["quarter"].map(_q_ord)
    t_break = _q_ord(break_quarter)
    rows = []
    for metric in SIG_METRICS:
        if metric not in d.columns or d[metric].notna().sum() < 8:
            continue
        row, _ = analyze_metric(d, metric, t_break, hac_lags)
        row["corpus"] = corpus
        rows.append(row)
    cols = ["corpus", "metric", "n_quarters", "pre_slope", "slope_change",
            "slope_change_p", "post_slope", "mk_tau_post", "mk_p_post",
            "prepost_diff", "prepost_p"]
    out = pd.DataFrame(rows)
    return out[[c for c in cols if c in out.columns]]


def plot_decomposition(df: pd.DataFrame, output: Path, corpus: str) -> None:
    quarters = df["quarter"].tolist()
    x = list(range(len(quarters)))
    mx = quarters.index(CHATGPT_QUARTER) if CHATGPT_QUARTER in quarters else None

    fig, axes = plt.subplots(4, 1, figsize=(13, 15), sharex=True)

    # Panel A — the decomposition
    ax = axes[0]
    ax.plot(x, df["overall_cosine"], marker="o", ms=3, color="black", label="overall (all pairs)")
    ax.plot(x, df["between_cosine"], marker="o", ms=3, color="tab:red",
            label="between different topics")
    ax.plot(x, df["within_cosine"], marker="o", ms=3, color="tab:blue",
            label="within the same topic")
    ax.set_ylabel("mean pairwise cosine\n(higher = more alike)", fontsize=9)
    ax.set_title("Where does the rise live? Overall similarity splits into within-topic vs "
                 "between-topic", fontsize=10, color="dimgray", loc="left", pad=6)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="best")

    # Panel B — topic diversity
    ax = axes[1]
    ax.plot(x, df["eff_topics"], marker="o", ms=3, color="tab:green")
    ax.set_ylabel("effective # of topics\n(lower = less diverse)", fontsize=9)
    ax.set_title("Topic diversity over time (a drop after ChatGPT = topics homogenising)",
                 fontsize=10, color="dimgray", loc="left", pad=6)
    ax.grid(True, alpha=0.3)

    # Panel C — composition drift
    ax = axes[2]
    ax.plot(x, df["comp_jsd"], marker="o", ms=3, color="tab:purple")
    ax.set_ylabel("JSD vs pre-ChatGPT mix\n(higher = mix has drifted)", fontsize=9)
    ax.set_title("Topic-composition drift: how far each quarter's topic mix is from the "
                 "pre-ChatGPT baseline", fontsize=10, color="dimgray", loc="left", pad=6)
    ax.grid(True, alpha=0.3)

    # Panel D — genuine convergence vs global drift (anisotropy control)
    ax = axes[3]
    ax.plot(x, df["between_cosine"], marker="o", ms=3, color="tab:red",
            label="between-topic (raw)")
    ax.plot(x, df["mc_between_cosine"], marker="o", ms=3, color="tab:orange", linestyle="--",
            label="between-topic (mean-centred = anisotropy removed)")
    ax.set_ylabel("between-topic cosine", fontsize=9)
    ax.set_title("Are topics genuinely converging, or is it a growing global direction? "
                 "If the dashed line stays flat, the raw rise was an artifact.",
                 fontsize=10, color="dimgray", loc="left", pad=6)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="best")

    for ax in axes:
        if mx is not None:
            ax.axvline(mx, color="black", linestyle="--", alpha=0.7)
    if mx is not None:
        axes[0].text(mx, axes[0].get_ylim()[1], " ChatGPT (2022Q4)", va="top", fontsize=8)

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(quarters, rotation=90, fontsize=6)
    axes[-1].set_xlabel("Quarter")

    n_med = int(df["n_sample"].median())
    n_top = int(df["n_topics"].max())
    foot = (f"Up to {int(df['n_sample'].max())} answers/quarter (median {n_med}); every answer "
            f"assigned one of K={n_top} global K-means topics (stable across time, no dropped "
            "outliers). Overall = within-topic + between-topic pairs combined.")
    fig.text(0.5, 0.005, foot, ha="center", va="bottom", fontsize=8, color="dimgray", wrap=True)
    fig.suptitle(f"{corpus} \u2014 Is AI homogenising topics, or writing style within a topic? "
                 "(decomposition #13)", fontsize=13, fontweight="bold", y=0.997)
    fig.tight_layout(rect=(0, 0.02, 1, 0.985))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    print(f"Plot -> {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Within-topic vs between-topic decomposition (#13)")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("--out-dir", type=Path, default=Path("artifacts/cross-validated"))
    ap.add_argument("--corpus", default="Cross Validated")
    ap.add_argument("--sample", type=int, default=800)
    ap.add_argument("--k", type=int, default=50, help="Number of global K-means topics")
    ap.add_argument("--min-answers", type=int, default=30)
    ap.add_argument("--break-quarter", default=CHATGPT_QUARTER)
    ap.add_argument("--cache-dir", type=Path, default=Path("data/models"))
    ap.add_argument("--emb-cache-dir", type=Path, default=Path("data/embeddings"))
    ap.add_argument("--no-emb-cache", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    model = load_model(args.cache_dir)
    df = pd.read_parquet(args.input)

    if args.no_emb_cache:
        raw_cache = None
    else:
        raw_path = args.emb_cache_dir / f"{args.input.stem}_minilm_raw.npz"
        raw_cache = load_cache(raw_path)

    result = compute(df, model, sample=args.sample, K=args.k,
                     min_answers=args.min_answers, seed=args.seed, raw_cache=raw_cache)

    if not args.no_emb_cache:
        save_cache(raw_path, raw_cache)
        print(f"Embedding cache -> {raw_path} ({len(raw_cache):,} vectors)")

    data_dir = args.out_dir / "data"
    plot_dir = args.out_dir / "plots"
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / "13_topic_decomposition.csv"
    result.to_csv(csv_path, index=False)
    print(f"Wrote {len(result)} quarters -> {csv_path}")

    sig = run_significance(result, args.corpus, args.break_quarter)
    sig_path = data_dir / "13_decomposition_significance.csv"
    sig.to_csv(sig_path, index=False)
    print(f"\n=== significance (break {args.break_quarter}) ===")
    with pd.option_context("display.width", 160, "display.max_columns", 20):
        print(sig.to_string(index=False))

    plot_decomposition(result, plot_dir / "13_topic_decomposition.png", args.corpus)


if __name__ == "__main__":
    main()
