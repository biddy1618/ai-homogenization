"""#3 — high- vs low-cognitive-load comparison of the semantic-similarity trend.

Reads the family-5 per-quarter BERT pairwise-cosine series for every corpus, tags each
with its cognitive-load bucket, and compares the post-ChatGPT movement across buckets.

Absolute cosine levels are not comparable across corpora (anisotropy + topic structure
differ), so we CENTER each series on its own pre-ChatGPT mean and compare the *change*.
Formal per-corpus significance lives in significance.py (family 8); this is the
cross-site visual + a compact delta/slope table.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CHATGPT_QUARTER = "2022Q4"
METRICS = ("sem_pairwise_cosine", "lc_sem_pairwise_cosine")
PANEL_TITLE = {"sem_pairwise_cosine": "Raw answer text",
               "lc_sem_pairwise_cosine": "Length-controlled (first 100 tokens)"}

# corpus folder -> (display label, cognitive-load bucket)
CORPORA = [
    # --- high cognitive load (technical / expert) ---
    ("cross-validated", "Cross Validated", "high"),
    ("philosophy", "Philosophy", "high"),
    ("economics", "Economics", "high"),
    ("crypto", "Cryptography", "high"),
    ("law", "Law", "high"),
    ("history", "History", "high"),
    ("cs", "Computer Science", "high"),
    ("biology", "Biology", "high"),
    ("astronomy", "Astronomy", "high"),
    ("chemistry", "Chemistry", "high"),
    ("electronics", "Electrical Engineering", "high"),
    ("physics", "Physics", "high"),
    ("softwareengineering", "Software Engineering", "high"),
    ("english", "English Language & Usage", "high"),
    # --- low cognitive load (everyday / practical / hobby / culture) ---
    ("seasoned-advice", "Seasoned Advice", "low"),
    ("travel", "Travel", "low"),
    ("bicycles", "Bicycles", "low"),
    ("gardening", "Gardening", "low"),
    ("rpg", "Role-playing Games", "low"),
    ("boardgames", "Board Games", "low"),
    ("money", "Personal Finance & Money", "low"),
    ("photo", "Photography", "low"),
    ("workplace", "The Workplace", "low"),
    ("diy", "Home Improvement", "low"),
    ("scifi", "Science Fiction & Fantasy", "low"),
    ("gaming", "Arqade (Gaming)", "low"),
]
# One colour per bucket — with 26 corpora, per-corpus colours are unreadable, so individual
# series are drawn faint and the bucket MEAN is drawn bold on top.
BUCKET_COLOR = {"high": "#08519c", "low": "#e6550d"}
BUCKET_LABEL = {"high": "High cognitive-load", "low": "Low cognitive-load"}


def _q_ord(q: str) -> int:
    return int(q[:4]) * 4 + (int(q[5:]) - 1)


def _slope(t: np.ndarray, y: np.ndarray) -> float:
    return float(np.polyfit(t, y, 1)[0]) if len(t) >= 2 else float("nan")


def load_series(artifacts: Path):
    series, table = {}, []
    t_break = _q_ord(CHATGPT_QUARTER)
    for folder, label, cog in CORPORA:
        csv = artifacts / folder / "data" / "5_semantic_bert.csv"
        if not csv.exists():
            print(f"  skip {label}: {csv} missing")
            continue
        d = pd.read_csv(csv).dropna(subset=["sem_pairwise_cosine"]).copy()
        d["_t"] = d["quarter"].map(_q_ord)
        d = d.sort_values("_t")
        series[folder] = (label, cog, d)
        rec = {"corpus": label, "cog_load": cog, "n_quarters": int(len(d)),
               "first_q": d["quarter"].iloc[0], "last_q": d["quarter"].iloc[-1]}
        for m in METRICS:
            pre = d[d["_t"] < t_break][m]
            post = d[d["_t"] >= t_break][m]
            rec[f"{m}_pre_mean"] = float(pre.mean())
            rec[f"{m}_post_mean"] = float(post.mean())
            rec[f"{m}_delta"] = float(post.mean() - pre.mean())
            rec[f"{m}_post_slope"] = _slope(d[d["_t"] >= t_break]["_t"].to_numpy(), post.to_numpy())
        table.append(rec)
    return series, pd.DataFrame(table), t_break


def _bucket_band(series: dict, metric: str, bucket: str, t_break: int, min_n: int = 3):
    """Mean (+SE) across corpora of the pre-centered metric, per quarter ordinal.

    Only quarters covered by at least `min_n` corpora are kept, so the bold bucket
    trajectory is not driven by a single early site.
    """
    from collections import defaultdict
    acc: dict[int, list[float]] = defaultdict(list)
    for _folder, (_label, cog, d) in series.items():
        if cog != bucket:
            continue
        pre_mean = d[d["_t"] < t_break][metric].mean()
        for t, v in zip(d["_t"], d[metric] - pre_mean):
            if np.isfinite(v):
                acc[int(t)].append(float(v))
    ts = sorted(t for t, vals in acc.items() if len(vals) >= min_n)
    means = np.array([np.mean(acc[t]) for t in ts])
    ses = np.array([np.std(acc[t], ddof=1) / np.sqrt(len(acc[t])) if len(acc[t]) > 1 else 0.0
                    for t in ts])
    return np.array(ts), means, ses


def plot_comparison(series: dict, t_break: int, output: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
    n_by_bucket = {b: sum(1 for _, (_, c, _) in series.items() if c == b)
                   for b in ("high", "low")}
    for ax, metric in zip(axes, METRICS):
        # thin faint context lines: one per corpus, coloured only by bucket
        for _folder, (_label, cog, d) in series.items():
            pre_mean = d[d["_t"] < t_break][metric].mean()
            ax.plot(d["_t"], d[metric] - pre_mean, color=BUCKET_COLOR[cog],
                    lw=0.8, alpha=0.18, zorder=1)
        # bold bucket mean with ±1 SE band on top
        for bucket in ("high", "low"):
            ts, means, ses = _bucket_band(series, metric, bucket, t_break)
            if len(ts) == 0:
                continue
            ax.fill_between(ts, means - ses, means + ses, color=BUCKET_COLOR[bucket],
                            alpha=0.18, zorder=2)
            ax.plot(ts, means, color=BUCKET_COLOR[bucket], lw=2.8, zorder=3,
                    label=f"{BUCKET_LABEL[bucket]} mean (n={n_by_bucket[bucket]})")
        ax.axhline(0, color="0.5", lw=0.8)
        ax.axvline(t_break, color="black", linestyle="--", alpha=0.7,
                   label="ChatGPT release (2022Q4)")
        # focus the y-axis on the bucket-mean envelope so sparse early-quarter
        # outliers (single-corpus spikes) don't dominate the view
        env = np.concatenate([_bucket_band(series, metric, b, t_break)[1]
                              for b in ("high", "low")
                              if len(_bucket_band(series, metric, b, t_break)[0])])
        if env.size:
            pad = 0.6 * (env.max() - env.min() + 1e-6)
            ax.set_ylim(env.min() - pad, env.max() + pad)
        ax.set_title(PANEL_TITLE[metric], fontsize=11, loc="left")
        ax.set_ylabel("cosine minus pre-ChatGPT mean", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9, loc="upper left", framealpha=0.9)
    # readable quarter ticks from the union of series
    all_ord = sorted({t for _, _, d in series.values() for t in d["_t"]})
    ord2q = {t: f"{t // 4}Q{t % 4 + 1}" for t in all_ord}
    ticks = all_ord[::8]
    axes[-1].set_xticks(ticks)
    axes[-1].set_xticklabels([ord2q[t] for t in ticks], rotation=45, ha="right")
    axes[-1].set_xlabel("quarter")
    fig.suptitle(
        "High- vs low-cognitive-load corpora: change in answer similarity around ChatGPT\n"
        "(thin lines = individual corpora centered on their own pre-ChatGPT mean; "
        "bold = bucket mean ±1 SE)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    print(f"Saved figure -> {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="High vs low cognitive-load comparison")
    ap.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    ap.add_argument("--out-csv", type=Path, default=Path("artifacts/9_cog_load_comparison.csv"))
    ap.add_argument("--plot", type=Path, default=Path("artifacts/9_cog_load_comparison.png"))
    args = ap.parse_args()

    series, table, t_break = load_series(args.artifacts)
    if table.empty:
        print("No corpora found — run semantic_bert.py first.")
        return
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out_csv, index=False)
    cols = ["corpus", "cog_load", "n_quarters", "first_q", "last_q",
            "sem_pairwise_cosine_delta", "sem_pairwise_cosine_post_slope",
            "lc_sem_pairwise_cosine_delta", "lc_sem_pairwise_cosine_post_slope"]
    print(table[cols].to_string(index=False))
    print("\nBucket means (raw delta / raw post-slope):")
    print(table.groupby("cog_load")[["sem_pairwise_cosine_delta",
                                      "sem_pairwise_cosine_post_slope"]].mean().to_string())
    print(f"\nWrote -> {args.out_csv}")
    plot_comparison(series, t_break, args.plot)


if __name__ == "__main__":
    main()
