"""P2a — segment answers by score and compare homogenization between groups.

Splits each quarter's answers at the *within-quarter* median score (so the split is
free of the age confound: older answers accumulate more votes) into a low- and a
high-score group, then measures per-group pairwise-cosine homogenization over time.
If a real AI effect were concentrated in low-effort/low-score answers it would show
here even though it is washed out in the pooled average.

Reuses the persistent MiniLM embedding cache and the bias-corrected bootstrap helper.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from metrics import tokenize
from semantic import spread_metrics, bootstrap_pairwise_samples
from semantic_bert import load_model, embed_texts
from embed_cache import load_cache, save_cache, cached_embed

CHATGPT_QUARTER = "2022Q4"
GROUPS = ("low", "high")


def _ci(v: np.ndarray, n_boot: int, ci: float, rng) -> tuple[float, float]:
    pc = bootstrap_pairwise_samples(v, n_boot, rng)
    if pc is None:
        return float("nan"), float("nan")
    alpha = 1.0 - ci
    return (float(np.nanpercentile(pc, 100 * alpha / 2)),
            float(np.nanpercentile(pc, 100 * (1 - alpha / 2))))


def _group_record(quarter: str, group: str, sub: pd.DataFrame, model, lc_window: int,
                  n_boot: int, ci: float, rng, raw_cache, lc_cache) -> dict:
    ids = sub["id"].tolist()
    texts = sub["text"].tolist()
    raw_emb = cached_embed(model, ids, texts, embed_texts, raw_cache)
    raw = spread_metrics(raw_emb)

    tokenized = [tokenize(t) for t in texts]
    lc_data = [(i, " ".join(tk[:lc_window])) for i, tk in zip(ids, tokenized)
               if len(tk) >= lc_window]
    if len(lc_data) >= 2:
        lc_emb = cached_embed(model, [i for i, _ in lc_data],
                              [t for _, t in lc_data], embed_texts, lc_cache)
        lc = spread_metrics(lc_emb)
    else:
        lc_emb, lc = None, {"pairwise_cosine": float("nan"),
                            "centroid_variance": float("nan"), "eff_dim": float("nan")}

    rec = {"quarter": quarter, "group": group, "n": len(sub), "n_lc": len(lc_data),
           "score_min": int(sub["score"].min()), "score_max": int(sub["score"].max())}
    rec.update({f"sem_{k}": val for k, val in raw.items()})
    rec.update({f"lc_sem_{k}": val for k, val in lc.items()})
    if n_boot:
        rec["sem_pairwise_cosine_lo"], rec["sem_pairwise_cosine_hi"] = _ci(raw_emb, n_boot, ci, rng)
        rec["lc_sem_pairwise_cosine_lo"], rec["lc_sem_pairwise_cosine_hi"] = (
            _ci(lc_emb, n_boot, ci, rng) if lc_emb is not None else (float("nan"), float("nan")))
    return rec


def compute_segments(df: pd.DataFrame, model, sample: int = 800, lc_window: int = 100,
                     min_answers: int = 30, min_group: int = 30, seed: int = 42,
                     n_boot: int = 0, ci: float = 0.95, raw_cache: dict | None = None,
                     lc_cache: dict | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    boot_rng = np.random.default_rng(seed + 1)
    records: list[dict] = []

    for quarter, group in tqdm(sorted(df.groupby("quarter")), desc="Quarters"):
        if len(group) < min_answers:
            continue
        if len(group) > sample:
            group = group.iloc[rng.choice(len(group), size=sample, replace=False)]
        # rank-based median split so ties don't unbalance the groups
        ranks = group["score"].rank(method="first")
        is_high = ranks > ranks.median()
        for name, sub in (("low", group[~is_high]), ("high", group[is_high])):
            if len(sub) < min_group:
                continue
            records.append(_group_record(quarter, name, sub, model, lc_window,
                                         n_boot, ci, boot_rng, raw_cache, lc_cache))

    return pd.DataFrame(records).sort_values(["quarter", "group"]).reset_index(drop=True)


def plot_segments(seg: pd.DataFrame, output: Path, corpus: str) -> None:
    quarters = sorted(seg["quarter"].unique())
    x = {q: i for i, q in enumerate(quarters)}
    marker_x = x.get(CHATGPT_QUARTER)
    colors = {"low": "tab:orange", "high": "tab:blue"}

    panels = [("sem_pairwise_cosine", "raw embeddings"),
              ("lc_sem_pairwise_cosine", "length-controlled (first 100 tokens)")]
    fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
    for ax, (col, title) in zip(axes, panels):
        for g in GROUPS:
            gd = seg[seg["group"] == g].sort_values("quarter")
            gx = [x[q] for q in gd["quarter"]]
            ax.plot(gx, gd[col], marker="o", ms=3, color=colors[g],
                    label=f"{g}-score (within-quarter median split)")
            lo = f"{col}_lo"
            if lo in gd.columns:
                ax.fill_between(gx, gd[lo], gd[f"{col}_hi"], color=colors[g], alpha=0.2)
        ax.set_ylabel("mean pairwise cosine\n(higher = homogeneous)", fontsize=9)
        ax.set_title(title, fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc="best")
        if marker_x is not None:
            ax.axvline(marker_x, color="black", linestyle="--", alpha=0.7)

    axes[-1].set_xticks(list(x.values()))
    axes[-1].set_xticklabels(quarters, rotation=90, fontsize=6)
    axes[-1].set_xlabel("Quarter")
    ci_note = "  (shaded = bootstrap CI)" if "sem_pairwise_cosine_lo" in seg.columns else ""
    fig.suptitle(f"{corpus} — homogenization by answer score (Sentence-BERT / MiniLM){ci_note}",
                 fontsize=13)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    print(f"Saved figure -> {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Segment homogenization by answer score (P2a)")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("--data-dir", type=Path, default=Path("artifacts/cross-validated/data"))
    ap.add_argument("--plots-dir", type=Path, default=Path("artifacts/cross-validated/plots"))
    ap.add_argument("--cache-dir", type=Path, default=Path("data/models"))
    ap.add_argument("--sample", type=int, default=800)
    ap.add_argument("--lc-window", type=int, default=100)
    ap.add_argument("--min-group", type=int, default=30)
    ap.add_argument("--bootstrap", type=int, default=1000,
                    help="Bootstrap resamples for per-group CIs (0 = off)")
    ap.add_argument("--ci", type=float, default=0.95)
    ap.add_argument("--emb-cache-dir", type=Path, default=Path("data/embeddings"))
    ap.add_argument("--no-emb-cache", action="store_true", help="Bypass the embedding cache")
    ap.add_argument("--corpus", default="Cross Validated")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df = pd.read_parquet(args.input)

    if args.no_emb_cache:
        raw_cache = lc_cache = None
        raw_path = lc_path = None
    else:
        tag = args.input.stem
        raw_path = args.emb_cache_dir / f"{tag}_minilm_raw.npz"
        lc_path = args.emb_cache_dir / f"{tag}_minilm_lc{args.lc_window}.npz"
        raw_cache, lc_cache = load_cache(raw_path), load_cache(lc_path)

    model = load_model(args.cache_dir)
    seg = compute_segments(df, model, sample=args.sample, lc_window=args.lc_window,
                           min_group=args.min_group, seed=args.seed, n_boot=args.bootstrap,
                           ci=args.ci, raw_cache=raw_cache, lc_cache=lc_cache)

    args.data_dir.mkdir(parents=True, exist_ok=True)
    out_csv = args.data_dir / "7_score_segments.csv"
    seg.to_csv(out_csv, index=False)
    print(f"Wrote {seg['quarter'].nunique()} quarters x 2 groups -> {out_csv}")

    plot_segments(seg, args.plots_dir / "7_score_segments.png", args.corpus)

    if not args.no_emb_cache:
        save_cache(raw_path, raw_cache)
        save_cache(lc_path, lc_cache)
        print(f"Embedding cache -> {args.emb_cache_dir} "
              f"({len(raw_cache):,} raw / {len(lc_cache):,} lc vectors)")


if __name__ == "__main__":
    main()
