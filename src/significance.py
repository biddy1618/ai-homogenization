"""#2 — statistical significance of the semantic-similarity increase.

Three complementary tests on the family-5 per-quarter series (`5_semantic_bert.csv`):

1. **Interrupted time series** (segmented regression, Wagner et al. spec) with a break at
   the ChatGPT quarter, fit by OLS with Newey-West (HAC) standard errors to handle
   autocorrelation — gives p-values on the level jump and the *slope change* after ChatGPT.
2. **Mann-Kendall** monotonic-trend test (via Kendall's tau) + **Theil-Sen** slope, on the
   full series and on the post-ChatGPT segment — non-parametric corroboration.
3. **Pre-vs-post bootstrap** difference in mean cosine (quarter-level resampling) with a
   percentile CI and one-sided p.

Run per corpus; the printed/CSV rows are directly comparable across sites.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

CHATGPT_QUARTER = "2022Q4"
METRICS = ("sem_pairwise_cosine", "lc_sem_pairwise_cosine")


def _q_ord(q: str) -> int:
    """Calendar ordinal of a quarter label (e.g. 2022Q4) so gaps are real gaps."""
    return int(q[:4]) * 4 + (int(q[5:]) - 1)


def its_regression(t: np.ndarray, y: np.ndarray, t_break: int, hac_lags: int = 4) -> dict:
    """Segmented regression y = b0 + b1*t + b2*level + b3*trend_post, HAC SEs."""
    level = (t >= t_break).astype(float)
    trend_post = np.clip(t - t_break, 0, None).astype(float)
    X = np.column_stack([np.ones_like(t, dtype=float), t.astype(float), level, trend_post])
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    names = ("intercept", "pre_slope", "level_jump", "slope_change")
    out = {n: float(fit.params[i]) for i, n in enumerate(names)}
    out.update({f"{n}_p": float(fit.pvalues[i]) for i, n in enumerate(names)})
    out["post_slope"] = out["pre_slope"] + out["slope_change"]
    out["_fitted"] = fit.fittedvalues
    return out


def bootstrap_prepost_diff(t: np.ndarray, y: np.ndarray, t_break: int,
                           n_boot: int = 10000, seed: int = 42) -> dict:
    """Quarter-level bootstrap of mean(post) - mean(pre)."""
    rng = np.random.default_rng(seed)
    pre, post = y[t < t_break], y[t >= t_break]
    if len(pre) < 2 or len(post) < 2:
        return {"prepost_diff": float("nan"), "prepost_diff_lo": float("nan"),
                "prepost_diff_hi": float("nan"), "prepost_p": float("nan")}
    diffs = (rng.choice(post, (n_boot, len(post))).mean(1)
             - rng.choice(pre, (n_boot, len(pre))).mean(1))
    return {"prepost_diff": float(post.mean() - pre.mean()),
            "prepost_diff_lo": float(np.percentile(diffs, 2.5)),
            "prepost_diff_hi": float(np.percentile(diffs, 97.5)),
            "prepost_p": float(np.mean(diffs <= 0))}


def analyze_metric(df: pd.DataFrame, metric: str, t_break: int, hac_lags: int) -> dict:
    d = df.dropna(subset=[metric]).sort_values("_t")
    t, y = d["_t"].to_numpy(), d[metric].to_numpy()
    its = its_regression(t, y, t_break, hac_lags)

    tau, mk_p = stats.kendalltau(t, y)
    theil = stats.theilslopes(y, t)
    post = t >= t_break
    if post.sum() >= 3:
        tau_post, mk_p_post = stats.kendalltau(t[post], y[post])
    else:
        tau_post, mk_p_post = float("nan"), float("nan")

    row = {"metric": metric, "n_quarters": int(len(d)),
           "pre_slope": its["pre_slope"], "pre_slope_p": its["pre_slope_p"],
           "level_jump": its["level_jump"], "level_jump_p": its["level_jump_p"],
           "slope_change": its["slope_change"], "slope_change_p": its["slope_change_p"],
           "post_slope": its["post_slope"],
           "mk_tau_full": float(tau), "mk_p_full": float(mk_p),
           "mk_tau_post": float(tau_post), "mk_p_post": float(mk_p_post),
           "theil_slope_full": float(theil[0])}
    row.update(bootstrap_prepost_diff(t, y, t_break))
    return row, (t, y, its["_fitted"])


PANEL_TITLE = {"sem_pairwise_cosine": "Raw answer text",
               "lc_sem_pairwise_cosine": "Length-controlled (first 100 tokens)"}


def plot_its(df: pd.DataFrame, fits: dict, rows: dict, t_break: int,
             output: Path, corpus: str) -> None:
    ord2q = dict(zip(df["_t"], df["quarter"]))
    ticks = sorted(ord2q)[::8]
    fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
    for ax, metric in zip(axes, METRICS):
        t, y, fitted = fits[metric]
        r = rows[metric]
        pre, post = t < t_break, t >= t_break
        # observed quarterly values
        ax.plot(t, y, color="0.6", lw=0.8, alpha=0.6, zorder=1)
        ax.scatter(t, y, s=16, color="0.4", zorder=2,
                   label="observed quarterly mean pairwise cosine")
        # fitted trend, drawn as two segments so the slope change is visible
        ax.plot(t[pre], fitted[pre], color="tab:blue", lw=2.5, zorder=3,
                label=f"pre-ChatGPT trend ({r['pre_slope']:+.4f}/qtr)")
        ax.plot(t[post], fitted[post], color="tab:red", lw=2.5, zorder=3,
                label=f"post-ChatGPT trend ({r['post_slope']:+.4f}/qtr)")
        ax.axvspan(t_break, t.max(), color="tab:red", alpha=0.05, zorder=0)
        ax.axvline(t_break, color="black", linestyle="--", alpha=0.7,
                   label="ChatGPT release (2022Q4)")
        ax.set_title(PANEL_TITLE[metric], fontsize=11, loc="left")
        ax.set_ylabel("mean pairwise cosine\n(higher = more similar)", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
        # significance callout
        p = r["slope_change_p"]
        ptxt = "p < 0.001" if p < 1e-3 else f"p = {p:.3g}"
        ax.text(0.985, 0.05,
                f"slope change after ChatGPT: {r['slope_change']:+.4f}/qtr  ({ptxt})",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
                bbox=dict(boxstyle="round", fc="lightyellow", ec="0.6", alpha=0.9))
    axes[-1].set_xticks(ticks)
    axes[-1].set_xticklabels([ord2q[t] for t in ticks], rotation=45, ha="right")
    axes[-1].set_xlabel("quarter")
    fig.suptitle(
        f"{corpus}: did answer-to-answer similarity rise after ChatGPT?\n"
        "Interrupted time-series fit — a trend line before vs. after the 2022Q4 break",
        fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    print(f"Saved figure -> {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Significance of the semantic-similarity increase")
    ap.add_argument("-i", "--input", type=Path, required=True, help="family-5 CSV")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out-csv", type=Path, required=True)
    ap.add_argument("--plot", type=Path, default=None)
    ap.add_argument("--break-quarter", default=CHATGPT_QUARTER)
    ap.add_argument("--hac-lags", type=int, default=4)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df["_t"] = df["quarter"].map(_q_ord)
    t_break = _q_ord(args.break_quarter)

    rows, fits = [], {}
    for metric in METRICS:
        row, series = analyze_metric(df, metric, t_break, args.hac_lags)
        row = {"corpus": args.corpus, **row}
        rows.append(row)
        fits[metric] = series
        print(f"\n[{args.corpus}] {metric}")
        print(f"  pre-slope   = {row['pre_slope']:+.5f}/qtr (p={row['pre_slope_p']:.3g})")
        print(f"  level jump  = {row['level_jump']:+.5f}     (p={row['level_jump_p']:.3g})")
        print(f"  slope chg   = {row['slope_change']:+.5f}/qtr (p={row['slope_change_p']:.3g})"
              f"  -> post-slope {row['post_slope']:+.5f}/qtr")
        print(f"  Mann-Kendall full tau={row['mk_tau_full']:+.3f} (p={row['mk_p_full']:.3g}); "
              f"post tau={row['mk_tau_post']:+.3f} (p={row['mk_p_post']:.3g})")
        print(f"  pre->post mean diff = {row['prepost_diff']:+.5f} "
              f"[{row['prepost_diff_lo']:+.5f}, {row['prepost_diff_hi']:+.5f}] "
              f"boot-p={row['prepost_p']:.3g}")

    out = pd.DataFrame(rows)
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out_csv, index=False)
    print(f"\nWrote -> {args.out_csv}")

    if args.plot is not None:
        plot_its(df, fits, {r["metric"]: r for r in rows}, t_break, args.plot, args.corpus)


if __name__ == "__main__":
    main()
