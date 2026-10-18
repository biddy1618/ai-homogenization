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

from semantic_bert import EMBED_MODES, embedding_setup, load_model, embed_texts
from embed_cache import load_cache, save_cache, cached_embed
from paths import source_dir
from significance import _q_ord, analyze_metric

CHATGPT_QUARTER = "2022Q4"
# Diversity and drift depend on how many answers a quarter has (fewer answers -> fewer topics
# seen). Post-ChatGPT volumes fell on several sites, so both are also measured on a fixed-size
# random subsample per quarter, averaged over draws ("rarefaction").
RARE_SIZE = 100
RARE_DRAWS = 50

# Series we run the interrupted-time-series / Mann-Kendall significance test on.
SIG_METRICS = (
    "overall_cosine", "within_cosine", "between_cosine",
    "eff_topics", "comp_jsd", "eff_topics_r", "comp_jsd_r",
    "between_centroid_cosine", "mc_between_cosine",
)


def rarefied_diversity(labels: np.ndarray, K: int, base_dist: np.ndarray, rng,
                       size: int = RARE_SIZE, draws: int = RARE_DRAWS) -> tuple[float, float]:
    """Mean effective number of topics and mean JSD vs ``base_dist`` over random subsamples of
    ``size`` labels (NaN if the quarter has fewer)."""
    if len(labels) < size:
        return float("nan"), float("nan")
    effs, jsds = [], []
    for _ in range(draws):
        sub = labels[rng.choice(len(labels), size=size, replace=False)]
        p = np.bincount(sub, minlength=K) / size
        nz = p[p > 0]
        effs.append(float(np.exp(-(nz * np.log(nz)).sum())))
        jsds.append(float(jensenshannon(p, base_dist, base=2) ** 2))
    return float(np.mean(effs)), float(np.mean(jsds))


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
            raw_cache: dict | None, embed_fn=embed_texts) -> pd.DataFrame:
    ids, texts, quarters = sample_quarters(df, sample, min_answers, seed)
    print(f"Sampled {len(ids):,} answers across {len(set(quarters))} quarters; "
          f"embedding (cache-backed)...")
    V = cached_embed(model, ids, texts, embed_fn, raw_cache)

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
    rare_rng = np.random.default_rng(seed)
    for rec in records:
        q = rec["quarter"]
        pr = props.get(q)
        if pr is not None:
            rec["comp_jsd"] = float(jensenshannon(pr, base_dist, base=2) ** 2)
        else:
            rec["comp_jsd"] = float("nan")
        rec["eff_topics_r"], rec["comp_jsd_r"] = rarefied_diversity(
            labels[quarters == q], K, base_dist, rare_rng)

    out = pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)
    cols = ["quarter", "n", "n_sample", "n_topics", "p_within", "overall_cosine",
            "within_cosine", "between_cosine", "mc_overall_cosine", "mc_between_cosine",
            "between_centroid_cosine", "eff_topics", "topic_entropy", "comp_jsd",
            "eff_topics_r", "comp_jsd_r"]
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


def plot_decomposition(df: pd.DataFrame, output: Path, corpus: str,
                       sig: pd.DataFrame | None = None) -> None:
    """Three panels: same-topic vs overall similarity, topic diversity, topic-mix drift."""
    quarters = df["quarter"].tolist()
    x = list(range(len(quarters)))
    mx = quarters.index(CHATGPT_QUARTER) if CHATGPT_QUARTER in quarters else None
    s = sig.set_index("metric") if sig is not None and len(sig) else None

    def lab(name, m):
        if s is None or m not in s.index:
            return name
        r = s.loc[m]
        return f"{name}  (slope change {r['slope_change']:+.4f}/qtr, p={r['slope_change_p']:.2g})"

    fig, axes = plt.subplots(3, 1, figsize=(13, 12), sharex=True)

    ax = axes[0]
    ax.plot(x, df["overall_cosine"], marker="o", ms=3, color="black",
            label=lab("all answer pairs", "overall_cosine"))
    ax.plot(x, df["within_cosine"], marker="o", ms=3, color="tab:blue",
            label=lab("pairs in the same topic", "within_cosine"))
    ax.set_ylabel("mean pairwise cosine similarity\n(higher = more alike)", fontsize=9)
    ax.set_title("A. Do answers on the same topic become more alike? (same-topic pairs are more "
                 "similar by construction; compare trends, not levels)",
                 fontsize=10, color="dimgray", loc="left", pad=6)
    ax.legend(fontsize=8, loc="best")

    ax = axes[1]
    ax.plot(x, df["eff_topics_r"], marker="o", ms=3, color="tab:green",
            label=lab(f"effective number of topics ({RARE_SIZE}-answer samples)", "eff_topics_r"))
    ax.set_ylabel("effective # of topics\n(lower = fewer subjects)", fontsize=9)
    ax.set_title("B. How many subjects are in play? exp(entropy) of the topic mix: 50 if all "
                 "topics are used equally, 1 if everything is one topic",
                 fontsize=10, color="dimgray", loc="left", pad=6)
    ax.legend(fontsize=8, loc="best")

    ax = axes[2]
    ax.plot(x, df["comp_jsd_r"], marker="o", ms=3, color="tab:purple",
            label=lab("JSD from the pre-ChatGPT topic mix", "comp_jsd_r"))
    ax.set_ylabel("Jensen-Shannon divergence\n(0 = same mix as before)", fontsize=9)
    ax.set_title("C. Which subjects? How far this quarter's topic mix is from the usual "
                 "pre-ChatGPT mix (higher = people discuss different things)",
                 fontsize=10, color="dimgray", loc="left", pad=6)
    ax.legend(fontsize=8, loc="best")

    for ax in axes:
        ax.grid(True, alpha=0.3)
        if mx is not None:
            ax.axvline(mx, color="black", linestyle="--", alpha=0.7)
    if mx is not None:
        axes[0].text(mx, axes[0].get_ylim()[1], " ChatGPT (2022Q4)", va="top", fontsize=8)
    axes[-1].set_xticks(x[::4])
    axes[-1].set_xticklabels(quarters[::4], rotation=90, fontsize=7)
    axes[-1].set_xlabel("Quarter")

    n_top = int(df["n_topics"].max())
    foot = (f"Up to {int(df['n_sample'].max())} sampled answers/quarter (median "
            f"{int(df['n_sample'].median())}), each assigned to one of K={n_top} K-means topics "
            "found once over all quarters (topics mean the same thing across time; no answer "
            f"dropped). B and C use random {RARE_SIZE}-answer subsamples (mean of {RARE_DRAWS}) "
            "so quarters with fewer answers are comparable. Topic mix = share of answers in each "
            "topic. Pre-ChatGPT mix = shares over all sampled answers before 2022Q4, pooled. JSD "
            "compares two mixes: average of how each differs from their midpoint (KL divergence, "
            "base 2); 0 = identical, 1 = no topic in common. Quarters before 2022Q4 are above 0 "
            "too (sampling noise, slow drift); read the change after the break.")
    fig.text(0.5, 0.005, foot, ha="center", va="bottom", fontsize=8, color="dimgray", wrap=True)
    fig.suptitle(f"{corpus} \u2014 Are the subjects narrowing, or do answers on the same subject "
                 "converge? (family 13)", fontsize=13, fontweight="bold", y=0.995)
    fig.tight_layout(rect=(0, 0.07, 1, 0.98))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Plot -> {output}")

def main() -> None:
    ap = argparse.ArgumentParser(description="Within-topic vs between-topic decomposition (#13)")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("--out-dir", type=Path, default=source_dir("cross-validated"))
    ap.add_argument("--corpus", default="Cross Validated")
    ap.add_argument("--sample", type=int, default=800)
    ap.add_argument("--k", type=int, default=50, help="Number of global K-means topics")
    ap.add_argument("--min-answers", type=int, default=30)
    ap.add_argument("--break-quarter", default=CHATGPT_QUARTER)
    ap.add_argument("--cache-dir", type=Path, default=Path("data/models"))
    ap.add_argument("--emb-cache-dir", type=Path, default=Path("data/embeddings"))
    ap.add_argument("--no-emb-cache", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--embed", choices=EMBED_MODES, default="legacy")
    ap.add_argument("--suffix", default="",
                    help="appended to output file names, e.g. '_k25' for the K-sensitivity runs")
    ap.add_argument("--replot", action="store_true",
                    help="only redraw the plot from the existing CSVs in --out-dir")
    args = ap.parse_args()

    if args.replot:
        res = pd.read_csv(args.out_dir / f"13_topic_decomposition{args.suffix}.csv")
        sig = pd.read_csv(args.out_dir / f"13_decomposition_significance{args.suffix}.csv")
        plot_decomposition(res, args.out_dir / f"13_topic_decomposition{args.suffix}.png",
                           args.corpus, sig)
        return

    model = load_model(args.cache_dir)
    emb = embedding_setup(model, args.embed, args.emb_cache_dir, args.input.stem)
    df = pd.read_parquet(args.input)

    if args.no_emb_cache:
        raw_cache = None
    else:
        raw_path = emb.raw_path
        raw_cache = load_cache(raw_path)

    result = compute(df, model, sample=args.sample, K=args.k,
                     min_answers=args.min_answers, seed=args.seed, raw_cache=raw_cache,
                     embed_fn=emb.embed)

    if not args.no_emb_cache:
        save_cache(raw_path, raw_cache)
        print(f"Embedding cache -> {raw_path} ({len(raw_cache):,} vectors)")

    data_dir = args.out_dir
    plot_dir = args.out_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / f"13_topic_decomposition{args.suffix}.csv"
    result.to_csv(csv_path, index=False)
    print(f"Wrote {len(result)} quarters -> {csv_path}")

    sig = run_significance(result, args.corpus, args.break_quarter)
    sig_path = data_dir / f"13_decomposition_significance{args.suffix}.csv"
    sig.to_csv(sig_path, index=False)
    print(f"\n=== significance (break {args.break_quarter}) ===")
    with pd.option_context("display.width", 160, "display.max_columns", 20):
        print(sig.to_string(index=False))

    plot_decomposition(result, plot_dir / f"13_topic_decomposition{args.suffix}.png", args.corpus, sig)


if __name__ == "__main__":
    main()
