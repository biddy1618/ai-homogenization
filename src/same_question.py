"""#11 — same-question topic control (the gold-standard confound test).

Answers to the *same question* (shared ``parent_id``) are, by construction, about
exactly the same thing — so grouping by question holds the subject perfectly fixed
with zero clustering, zero parameters, and zero dropped "outliers".

For every question with >=2 answers we embed its answers (MiniLM, reusing the
id-keyed cache) and, for each answer, take its mean cosine to the *other* answers of
the same question. Binning those per-answer values by the answer's own quarter gives
``within_question_cosine`` — "how much does a typical answer echo the other answers to
its question, over time". If this rises after ChatGPT, that is genuine homogenization
holding topic fixed; if it stays flat while the aggregate (family 5/8) rises, the
aggregate rise is a topic-composition effect.

``overall_cosine`` is the mean pairwise cosine among the *same* answer set each quarter
(ignoring which question they belong to) — an internal apples-to-apples reference on
identical data.

Output: ``<out-dir>/data/11_same_question.csv`` + ``<out-dir>/plots/11_same_question.png``
and a significance row (ITS slope-change + Mann-Kendall) on ``within_question_cosine``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from embed_cache import load_cache, save_cache, cached_embed
from semantic import spread_metrics
from semantic_bert import CHATGPT_QUARTER, load_model, embed_texts
from significance import _q_ord, analyze_metric


def _bootstrap_mean_ci(values: np.ndarray, n_boot: int, ci: float, rng) -> tuple[float, float]:
    """Percentile CI for the mean of per-answer sibling-similarities in a quarter."""
    if len(values) < 2 or n_boot <= 0:
        return float("nan"), float("nan")
    means = rng.choice(values, (n_boot, len(values))).mean(1)
    alpha = 1.0 - ci
    return float(np.percentile(means, 100 * alpha / 2)), float(np.percentile(means, 100 * (1 - alpha / 2)))


def compute_same_question(df: pd.DataFrame, model, min_answers: int = 30,
                          overall_sample: int = 800, seed: int = 42,
                          n_boot: int = 0, ci: float = 0.95,
                          raw_cache: dict | None = None) -> pd.DataFrame:
    """Per-quarter within-question and overall pairwise cosine on multi-answer questions."""
    rng = np.random.default_rng(seed)

    df = df[df["parent_id"] > 0].copy()
    # keep only answers whose question has >=2 answers (a question we can compare within)
    sizes = df.groupby("parent_id")["id"].transform("size")
    df = df[sizes >= 2].reset_index(drop=True)
    if df.empty:
        raise SystemExit("No multi-answer questions found — is parent_id populated?")

    ids = df["id"].tolist()
    texts = df["text"].tolist()
    emb = cached_embed(model, ids, texts, embed_texts, raw_cache)  # (n, d) L2-normalized
    quarter = df["quarter"].to_numpy()
    parent = df["parent_id"].to_numpy()

    # Per-answer mean cosine to same-question siblings.
    sib_sim = np.full(len(df), np.nan)
    for idx in tqdm(df.groupby("parent_id").indices.values(), desc="Questions"):
        if len(idx) < 2:
            continue
        v = emb[idx]
        s = v @ v.T                      # cosine matrix (unit vectors)
        m = len(idx)
        sib_sim[idx] = (s.sum(axis=1) - 1.0) / (m - 1)   # exclude self

    per = pd.DataFrame({"quarter": quarter, "parent_id": parent, "sim": sib_sim})

    records = []
    for q, g in sorted(per.groupby("quarter")):
        n_ans = len(g)
        if n_ans < min_answers:
            continue
        qmask = quarter == q
        qemb = emb[qmask]
        if len(qemb) > overall_sample:
            qemb = qemb[rng.choice(len(qemb), size=overall_sample, replace=False)]
        overall = spread_metrics(qemb)["pairwise_cosine"] if len(qemb) >= 2 else float("nan")

        rec = {"quarter": q, "n_answers": int(n_ans),
               "n_questions": int(g["parent_id"].nunique()),
               "within_question_cosine": float(g["sim"].mean()),
               "overall_cosine": float(overall)}
        if n_boot:
            lo, hi = _bootstrap_mean_ci(g["sim"].to_numpy(), n_boot, ci, rng)
            rec["within_question_cosine_lo"], rec["within_question_cosine_hi"] = lo, hi
        records.append(rec)

    return pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)


def plot_same_question(df: pd.DataFrame, output: Path, corpus: str, footnote: str = "") -> None:
    d = df.copy()
    d["_t"] = d["quarter"].map(_q_ord)
    d = d.sort_values("_t")
    t_break = _q_ord(CHATGPT_QUARTER)

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(d["_t"], d["overall_cosine"], color="tab:gray", lw=1.5, marker="o", ms=3,
            label="Any two answers in the quarter (overall baseline)")
    ax.plot(d["_t"], d["within_question_cosine"], color="tab:blue", lw=2, marker="o", ms=3,
            label="Answers to the SAME question (human vs human)")
    if "within_question_cosine_lo" in d:
        ax.fill_between(d["_t"], d["within_question_cosine_lo"], d["within_question_cosine_hi"],
                        color="tab:blue", alpha=0.15)
    ax.axvline(t_break, color="black", linestyle="--", alpha=0.7, label="ChatGPT release (2022Q4)")
    ax.axvspan(t_break, d["_t"].max(), color="tab:red", alpha=0.05)

    ord2q = dict(zip(d["_t"], d["quarter"]))
    ticks = sorted(ord2q)[::8]
    ax.set_xticks(ticks)
    ax.set_xticklabels([ord2q[t] for t in ticks], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("mean pairwise cosine\n(higher = more similar)", fontsize=10)
    ax.set_xlabel("Quarter", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9, loc="best", framealpha=0.9)
    fig.suptitle(f"{corpus} \u2014 Are answers to the SAME question getting more alike? "
                 "(same-question control #11)", fontsize=13, fontweight="bold", y=0.995)
    ax.set_title("Blue flat while gray rises = the aggregate rise is topic composition, "
                 "not homogenization", fontsize=9.5, color="dimgray", loc="center", pad=8)
    if footnote:
        fig.text(0.5, -0.02, footnote, ha="center", va="top", fontsize=7.5,
                 color="dimgray", wrap=True)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description="Same-question topic control (#11)")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("--out-dir", type=Path, default=Path("artifacts/cross-validated"))
    ap.add_argument("--corpus", default="Cross Validated")
    ap.add_argument("--cache-dir", type=Path, default=Path("data/models"))
    ap.add_argument("--emb-cache-dir", type=Path, default=Path("data/embeddings"))
    ap.add_argument("--no-emb-cache", action="store_true")
    ap.add_argument("--min-answers", type=int, default=30,
                    help="Min contributing answers for a quarter to count")
    ap.add_argument("--overall-sample", type=int, default=800)
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--ci", type=float, default=0.95)
    ap.add_argument("--break-quarter", default=CHATGPT_QUARTER)
    ap.add_argument("--hac-lags", type=int, default=4)
    args = ap.parse_args()

    model = load_model(args.cache_dir)
    df = pd.read_parquet(args.input)
    if "parent_id" not in df.columns:
        raise SystemExit(f"{args.input} has no parent_id column — re-parse with the updated "
                         "parse_posts.py first.")

    raw_cache = None
    if not args.no_emb_cache:
        raw_path = args.emb_cache_dir / f"{args.input.stem}_minilm_raw.npz"
        raw_cache = load_cache(raw_path)

    result = compute_same_question(df, model, min_answers=args.min_answers,
                                   overall_sample=args.overall_sample,
                                   n_boot=args.bootstrap, ci=args.ci, raw_cache=raw_cache)

    if not args.no_emb_cache:
        save_cache(raw_path, raw_cache)
        print(f"Embedding cache -> {raw_path} ({len(raw_cache):,} vectors)")

    csv_path = args.out_dir / "data" / "11_same_question.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(csv_path, index=False)
    print(f"Wrote {len(result)} quarters -> {csv_path}")
    print(result.to_string(index=False))

    plot_path = args.out_dir / "plots" / "11_same_question.png"
    sq_note = (f"No topic clustering: within-question compares answers to the exact same question "
               f"(quarters with >= {args.min_answers} contributing answers). The overall line "
               f"samples up to {args.overall_sample} answers/quarter. {len(result)} quarters shown.")
    plot_same_question(result, plot_path, corpus=args.corpus, footnote=sq_note)
    print(f"Plot -> {plot_path}")

    # Significance: ITS slope-change + Mann-Kendall on the within-question series.
    t_break = _q_ord(args.break_quarter)
    result["_t"] = result["quarter"].map(_q_ord)
    print("\n=== significance (within_question_cosine) ===")
    for metric in ("within_question_cosine", "overall_cosine"):
        row, _ = analyze_metric(result, metric, t_break, args.hac_lags)
        print(f"[{metric}] slope_change={row['slope_change']:+.5f} (p={row['slope_change_p']:.4g}) "
              f"| post_slope={row['post_slope']:+.5f} "
              f"| MK-post tau={row['mk_tau_post']:+.3f} (p={row['mk_p_post']:.4g}) "
              f"| pre/post diff={row['prepost_diff']:+.5f} (p={row['prepost_p']:.4g})")


if __name__ == "__main__":
    main()
