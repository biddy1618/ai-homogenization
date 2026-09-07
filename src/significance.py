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


def _verdict(raw: dict, lc: dict, alpha: float = 0.05) -> str:
    """One-line classification of a corpus from its raw + length-controlled ITS rows."""
    raw_up = raw["slope_change"] > 0 and raw["slope_change_p"] < alpha
    lc_up = lc["slope_change"] > 0 and lc["slope_change_p"] < alpha
    raw_dn = raw["slope_change"] < 0 and raw["slope_change_p"] < alpha
    if raw_up and lc_up:
        return "rise SURVIVES length control"
    if raw_up and not lc_up:
        return "rise is a LENGTH ARTIFACT"
    if raw_dn:
        return "significant DECREASE"
    return "no significant change"


def plot_summary(rep: pd.DataFrame, out_png: Path, break_quarter: str, alpha: float) -> None:
    """Forest/dot plot: per-corpus post-ChatGPT slope change, raw vs length-controlled."""
    d = rep.sort_values("raw_slope").reset_index(drop=True)
    y = np.arange(len(d))
    cog_color = {"high": "#08519c", "low": "#e6550d"}
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.axvline(0, color="0.5", lw=1)
    for i, r in d.iterrows():
        c = cog_color[r["cog"]]
        # connector between raw and length-controlled estimate
        ax.plot([r["raw_slope"], r["lc_slope"]], [i, i], color=c, lw=1, alpha=0.35, zorder=1)
        # raw = filled if significant, hollow if not
        ax.scatter(r["raw_slope"], i, s=70, zorder=3,
                   facecolor=c if r["raw_p"] < alpha else "white", edgecolor=c, linewidths=1.6)
        # length-controlled = small diamond
        ax.scatter(r["lc_slope"], i, marker="D", s=32, zorder=2,
                   facecolor=c if r["lc_p"] < alpha else "white", edgecolor=c, linewidths=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r['corpus']}" for _, r in d.iterrows()], fontsize=9)
    for tick, (_, r) in zip(ax.get_yticklabels(), d.iterrows()):
        tick.set_color(cog_color[r["cog"]])
    ax.set_xlabel("post-ChatGPT slope change in mean pairwise cosine (per quarter)")
    ax.grid(True, axis="x", alpha=0.3)
    from matplotlib.lines import Line2D
    legend = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="0.3", markeredgecolor="0.3",
               markersize=9, label="raw (filled = p<0.05)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="white", markeredgecolor="0.3",
               markersize=9, label="raw (hollow = n.s.)"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor="0.3", markeredgecolor="0.3",
               markersize=7, label="length-controlled"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#08519c", markersize=9,
               label="high cognitive-load"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#e6550d", markersize=9,
               label="low cognitive-load")]
    ax.legend(handles=legend, fontsize=8, loc="lower right", framealpha=0.95)
    n_sig = int(((rep["raw_slope"] > 0) & (rep["raw_p"] < alpha)).sum())
    ax.set_title(f"Family 8 - did answer similarity rise after ChatGPT? ({break_quarter} break)\n"
                 f"{n_sig}/{len(rep)} corpora show a significant increase; "
                 "dots right of 0 = converging", fontsize=12)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150)
    print(f"Saved figure -> {out_png}")


def run_all(artifacts: Path, out_csv: Path, break_quarter: str, hac_lags: int,
            alpha: float = 0.05, summary_png: Path | None = None,
            per_corpus_plots: bool = True) -> None:
    """Family-8 across every corpus in the shared registry -> one aggregate CSV + report."""
    from cog_load_compare import CORPORA  # shared corpus registry (folder, label, cog)

    t_break = _q_ord(break_quarter)
    rows, per = [], {}
    for folder, label, cog in CORPORA:
        csv = artifacts / folder / "data" / "5_semantic_bert.csv"
        if not csv.exists():
            print(f"  skip {label}: missing {csv}")
            continue
        df = pd.read_csv(csv)
        df["_t"] = df["quarter"].map(_q_ord)
        per[label] = {"cog": cog}
        fits, mrows = {}, {}
        for metric in METRICS:
            row, series = analyze_metric(df, metric, t_break, hac_lags)
            rows.append({"corpus": label, "cog_load": cog, **row})
            per[label][metric] = row
            fits[metric] = series
            mrows[metric] = row
        if per_corpus_plots:
            plot_its(df, fits, mrows, t_break,
                     artifacts / folder / "plots" / "8_its.png", label)

    out = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)

    # ---- readable "which source shows a significant increase?" report ----
    raw_m, lc_m = METRICS
    report = []
    for label, d in per.items():
        if raw_m not in d or lc_m not in d:
            continue
        raw, lc = d[raw_m], d[lc_m]
        report.append({
            "corpus": label, "cog": d["cog"],
            "raw_slope": raw["slope_change"], "raw_p": raw["slope_change_p"],
            "lc_slope": lc["slope_change"], "lc_p": lc["slope_change_p"],
            "verdict": _verdict(raw, lc, alpha)})
    rep = pd.DataFrame(report)
    if not rep.empty:
        # order: high-cog first, then by raw slope descending
        rep = rep.sort_values(["cog", "raw_slope"], ascending=[True, False])
        print(f"\n{'='*104}\nFamily 8 — significance of the post-ChatGPT similarity change "
              f"(break {break_quarter}, alpha={alpha})\n{'='*104}")
        print(f"{'corpus':<26}{'cog':<6}{'raw dslope/qtr':>16}{'p':>10}"
              f"{'lc dslope/qtr':>16}{'p':>10}  verdict")
        print("-" * 104)
        for _, r in rep.iterrows():
            print(f"{r['corpus']:<26}{r['cog']:<6}{r['raw_slope']:>+16.5f}{r['raw_p']:>10.2g}"
                  f"{r['lc_slope']:>+16.5f}{r['lc_p']:>10.2g}  {r['verdict']}")
        print("-" * 104)
        raw_sig = rep[(rep["raw_slope"] > 0) & (rep["raw_p"] < alpha)]
        lc_sig = rep[(rep["lc_slope"] > 0) & (rep["lc_p"] < alpha)]
        print(f"raw metric: {len(raw_sig)}/{len(rep)} corpora show a SIGNIFICANT increase "
              f"({', '.join(raw_sig['corpus']) or 'none'})")
        print(f"length-controlled: {len(lc_sig)}/{len(rep)} corpora survive "
              f"({', '.join(lc_sig['corpus']) or 'none'})")
        for cog in ("high", "low"):
            sub = rep[rep["cog"] == cog]
            rs = sub[(sub["raw_slope"] > 0) & (sub["raw_p"] < alpha)]
            ls = sub[(sub["lc_slope"] > 0) & (sub["lc_p"] < alpha)]
            print(f"  {cog:>4}-cog: raw {len(rs)}/{len(sub)} sig, "
                  f"length-controlled {len(ls)}/{len(sub)} survive")
        if summary_png is not None:
            plot_summary(rep, summary_png, break_quarter, alpha)
    print(f"\nWrote -> {out_csv}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Significance of the semantic-similarity increase")
    ap.add_argument("-i", "--input", type=Path, help="family-5 CSV (single-corpus mode)")
    ap.add_argument("--corpus", help="display name (single-corpus mode)")
    ap.add_argument("--out-csv", type=Path, help="output CSV")
    ap.add_argument("--plot", type=Path, default=None)
    ap.add_argument("--break-quarter", default=CHATGPT_QUARTER)
    ap.add_argument("--hac-lags", type=int, default=4)
    ap.add_argument("--all", action="store_true",
                    help="run every corpus in the registry -> one aggregate CSV + report")
    ap.add_argument("--artifacts", type=Path, default=Path("artifacts"),
                    help="artifacts root (--all mode)")
    ap.add_argument("--no-its-plots", action="store_true",
                    help="--all mode: skip per-corpus ITS plots (CSV + summary only)")
    args = ap.parse_args()

    if args.all:
        out_csv = args.out_csv or Path("artifacts/8_significance_all.csv")
        summary_png = args.plot or Path("artifacts/8_significance_all.png")
        run_all(args.artifacts, out_csv, args.break_quarter, args.hac_lags,
                summary_png=summary_png, per_corpus_plots=not args.no_its_plots)
        return

    if not (args.input and args.corpus and args.out_csv):
        ap.error("single-corpus mode needs -i/--input, --corpus and --out-csv "
                 "(or use --all)")

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
