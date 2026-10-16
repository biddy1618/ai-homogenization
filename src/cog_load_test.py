"""Family 9 test: is the post-ChatGPT turn stronger on high- than on low-cognitive-load sites?

Uses the family-8 slope change at the break (one value per site, 26 SE sites) and compares the
14 high-load vs 12 low-load sites three ways:
  * effect size: slope change raw, standardised by the site's pre-break quarterly SD (sites differ
    in noise), and relative to the site's pre-break mean similarity (sites differ in level);
    group medians + one-sided Mann-Whitney U (high > low);
  * count: sites with a significant upward turn (p<0.05, and after Benjamini-Hochberg across 26),
    high vs low, one-sided Fisher exact test;
  * a permutation test on the difference in mean standardised slope change (10,000 shuffles of
    the high/low labels).

    python src/cog_load_test.py      # -> artifacts/summary/9_cog_load_{test,sites}.{csv,png}
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu
from statsmodels.stats.multitest import multipletests

from paths import ALL_SOURCES, ARTIFACTS, source_dir, summary_dir
from significance import COG_COLOR

BREAK = "2022Q4"
METRICS = {"sem_pairwise_cosine": "main metric", "lc_sem_pairwise_cosine": "length-controlled"}
PANEL = {"sem_pairwise_cosine": "Whole text (sentence chunks, averaged)",
         "lc_sem_pairwise_cosine": "Opening window (first 120 model tokens)"}


def site_table(artifacts: Path, sig_csv: Path) -> pd.DataFrame:
    sig = pd.read_csv(sig_csv)
    rows = []
    for folder, label, cog in ALL_SOURCES:
        f = source_dir(folder, artifacts) / "5_semantic_bert.csv"
        if not f.exists() or label not in set(sig["corpus"]):
            continue
        s = pd.read_csv(f)
        pre = s[s["quarter"] < BREAK]
        for metric in METRICS:
            r = sig[(sig["corpus"] == label) & (sig["metric"] == metric)].iloc[0]
            rows.append({"corpus": label, "cog_load": cog, "metric": metric,
                         "slope_change": r["slope_change"], "p": r["slope_change_p"],
                         "slope_change_sd": r["slope_change"] / pre[metric].std(),
                         "slope_change_rel": r["slope_change"] / pre[metric].mean()})
    out = pd.DataFrame(rows)
    se = out["cog_load"] != "external"
    out["p_bh"] = np.nan
    out.loc[se, "p_bh"] = out[se].groupby("metric")["p"].transform(
        lambda p: multipletests(p, method="fdr_bh")[1])
    return out


def group_tests(t: pd.DataFrame, n_perm: int, rng) -> list[dict]:
    res = []
    t = t[t["cog_load"] != "external"]
    for metric, name in METRICS.items():
        d = t[t["metric"] == metric]
        hi, lo = d[d["cog_load"] == "high"], d[d["cog_load"] == "low"]
        row = {"metric": name, "n_high": len(hi), "n_low": len(lo)}
        for col in ("slope_change", "slope_change_sd", "slope_change_rel"):
            row[f"{col}_median_high"] = hi[col].median()
            row[f"{col}_median_low"] = lo[col].median()
            row[f"{col}_mwu_p"] = mannwhitneyu(hi[col], lo[col], alternative="greater").pvalue
        for tag, pcol in (("p05", "p"), ("bh", "p_bh")):
            sh = int(((hi["slope_change"] > 0) & (hi[pcol] < 0.05)).sum())
            sl = int(((lo["slope_change"] > 0) & (lo[pcol] < 0.05)).sum())
            row[f"sig_{tag}_high"], row[f"sig_{tag}_low"] = sh, sl
            row[f"sig_{tag}_fisher_p"] = fisher_exact([[sh, len(hi) - sh], [sl, len(lo) - sl]],
                                                      alternative="greater")[1]
        x, lab = d["slope_change_sd"].to_numpy(), (d["cog_load"] == "high").to_numpy()
        obs = x[lab].mean() - x[~lab].mean()
        perm = np.array([x[p].mean() - x[~p].mean()
                         for p in (rng.permutation(lab) for _ in range(n_perm))])
        row["perm_diff_sd"], row["perm_p"] = obs, (np.sum(perm >= obs) + 1) / (n_perm + 1)
        res.append(row)
    return res


def plot_test(sites: pd.DataFrame, tests: pd.DataFrame, out_png: Path) -> None:
    """Per-site slope change (pre-SD units) by group, filled = significant, with the test results."""
    import matplotlib.pyplot as plt

    groups = [g for g in ("high", "low", "external") if g in set(sites["cog_load"])]
    fig, axes = plt.subplots(1, 2, figsize=(15, 8.5), sharey=True)
    for ax, (metric, name) in zip(axes, METRICS.items()):
        d = sites[sites["metric"] == metric]
        r = tests[tests["metric"] == name].iloc[0]
        ax.axhline(0, color="0.5", lw=1)
        for x, g in enumerate(groups):
            sub = d[d["cog_load"] == g].sort_values("slope_change_sd")
            c = COG_COLOR[g]
            if g != "external":
                ax.boxplot(sub["slope_change_sd"], positions=[x], widths=0.5, showfliers=False,
                           medianprops=dict(color=c, lw=2), boxprops=dict(color=c, alpha=0.6),
                           whiskerprops=dict(color=c, alpha=0.6), capprops=dict(color=c, alpha=0.6))
            # alternate sides by rank so neighbouring labels don't collide
            side = np.where(np.arange(len(sub)) % 2 == 0, -1, 1)
            xs = x + 0.12 * side
            sig = (sub["slope_change"] > 0) & (sub["p"] < 0.05)
            ax.scatter(xs, sub["slope_change_sd"], s=55, zorder=3, edgecolor=c, linewidths=1.5,
                       facecolor=np.where(sig, c, "white"))
            for xi, s, (_, row) in zip(xs, side, sub.iterrows()):
                ax.annotate(row["corpus"], (xi, row["slope_change_sd"]), xytext=(8 * s, 0),
                            textcoords="offset points", fontsize=6.5, va="center", color=c,
                            ha="left" if s > 0 else "right")
        ax.set_xticks(range(len(groups)))
        short = {"high": "SE high load", "low": "SE low load", "external": "external"}
        ax.set_xticklabels([f"{short[g]}\n(n={int((d['cog_load'] == g).sum())})" for g in groups],
                           fontsize=9)
        ax.set_xlim(-0.8, len(groups) - 0.2)
        ax.grid(True, axis="y", alpha=0.3)
        ax.set_title(PANEL[metric], fontsize=11, loc="left")
        ax.text(0.5, -0.12,
                f"SE high vs low (one-sided): significant {r['sig_p05_high']}/{r['n_high']} vs "
                f"{r['sig_p05_low']}/{r['n_low']} (Fisher p={r['sig_p05_fisher_p']:.3f})\n"
                f"median {r['slope_change_sd_median_high']:+.2f} vs "
                f"{r['slope_change_sd_median_low']:+.2f} (Mann-Whitney p={r['slope_change_sd_mwu_p']:.3f});"
                f"  permutation p={r['perm_p']:.3f}",
                transform=ax.transAxes, ha="center", va="top", fontsize=8.5,
                bbox=dict(boxstyle="round", fc="lightyellow", ec="0.6", alpha=0.95))
    axes[0].set_ylabel("post-ChatGPT slope change, in units of the site's pre-ChatGPT SD\n"
                       "(filled = significant increase, p<0.05)", fontsize=9)
    fig.suptitle("Family 9 - is the post-ChatGPT turn stronger on high-cognitive-load sites?\n"
                 "Each dot = one site; external corpora shown for reference (not in the test)",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    fig.savefig(out_png, dpi=150)
    print(f"Saved figure -> {out_png}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artifacts", type=Path, default=ARTIFACTS)
    ap.add_argument("--n-perm", type=int, default=10000)
    args = ap.parse_args()

    base = summary_dir(args.artifacts)
    sites = site_table(args.artifacts, base / "8_significance_all.csv")
    tests = pd.DataFrame(group_tests(sites, args.n_perm, np.random.default_rng(42)))
    sites.to_csv(base / "9_cog_load_sites.csv", index=False)
    tests.to_csv(base / "9_cog_load_test.csv", index=False)
    plot_test(sites, tests, base / "9_cog_load_test.png")

    for _, r in tests.iterrows():
        print(f"\n== {r['metric']} ({r['n_high']} high vs {r['n_low']} low) ==")
        print(f"  significant upward turn, p<0.05:  high {r['sig_p05_high']}/{r['n_high']}  "
              f"low {r['sig_p05_low']}/{r['n_low']}   Fisher p={r['sig_p05_fisher_p']:.3f}")
        print(f"  significant after BH correction:  high {r['sig_bh_high']}/{r['n_high']}  "
              f"low {r['sig_bh_low']}/{r['n_low']}   Fisher p={r['sig_bh_fisher_p']:.3f}")
        for col, name in (("slope_change", "raw"), ("slope_change_sd", "in pre-SD units"),
                          ("slope_change_rel", "relative to pre level")):
            print(f"  median slope change {name:<22} high {r[f'{col}_median_high']:+.4g}  "
                  f"low {r[f'{col}_median_low']:+.4g}   Mann-Whitney p={r[f'{col}_mwu_p']:.3f}")
        print(f"  permutation (mean, pre-SD units): diff {r['perm_diff_sd']:+.3f}, p={r['perm_p']:.3f}")
    print(f"\nWrote -> {base / '9_cog_load_test.csv'}, {base / '9_cog_load_sites.csv'}, "
          f"{base / '9_cog_load_test.png'}")


if __name__ == "__main__":
    main()
