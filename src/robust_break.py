"""Family 8/9 with a better-specified break test: curved pre-trend + placebo-calibrated p-values.

The plain segmented regression (``significance.py``) finds a significant "upturn" at ~55% of
placebo dates in pre-ChatGPT data (``placebo_breaks.py``): the series curve slowly, and a straight
pre-trend reads any curvature as a break. Here, for two specifications -

* ``linear`` - y = b0 + b1 t + level + slope_post            (the paper's model)
* ``quad``   - y = b0 + b1 t + b2 t^2 + level + slope_post   (curved underlying trend)

- the slope-change t-statistic (HAC, 4 lags) at the real break 2022Q4 is compared with the pooled
t-statistics of matched placebo breaks (pre-ChatGPT data only; each placebo sees as many
post-break quarters as the real break). Calibrated one-sided p = share of placebo t >= real t
(t-statistics are scale-free, so placebos are pooled over all 30 sources). Benjamini-Hochberg is
applied over the 30 sources. Family 9 (high vs low cognitive load, 26 SE sites) is re-run on the
calibrated verdicts (Fisher) and on each site's z of the real slope change vs its own placebos
(Mann-Whitney).

Outputs: ``artifacts/summary/data/8_robust_break.csv``, ``8_robust_placebo_t.csv``,
``9_cog_load_robust.csv`` and ``artifacts/summary/8_robust_break.png``.

    python src/robust_break.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests

from paths import ALL_SOURCES, ARTIFACTS, source_dir, summary_dir
from significance import CHATGPT_QUARTER, _q_ord

METRIC = "sem_pairwise_cosine"
ALPHA = 0.05
SPECS = ("linear", "quad")
COLOR = {"high": "#08519c", "low": "#e6550d", "external": "#238b45"}


def fit_break(t: np.ndarray, y: np.ndarray, t_break: int, spec: str, hac_lags: int = 4) -> dict:
    """Slope change at ``t_break`` (coef, t, p) under a linear or quadratic underlying trend."""
    tc = (t - t.mean()) / max(t.std(), 1)  # centred/scaled so t^2 is well conditioned
    cols = [np.ones_like(tc), tc]
    if spec == "quad":
        cols.append(tc ** 2)
    cols += [(t >= t_break).astype(float), np.clip(t - t_break, 0, None).astype(float)]
    fit = sm.OLS(y, np.column_stack(cols)).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    return {"slope_change": float(fit.params[-1]), "t": float(fit.tvalues[-1]),
            "p_hac": float(fit.pvalues[-1])}


def load(artifacts: Path):
    for folder, label, cog in ALL_SOURCES:
        csv = source_dir(folder, artifacts) / "data" / "5_semantic_bert.csv"
        if not csv.exists():
            print(f"skip {label}: no {csv}")
            continue
        df = pd.read_csv(csv).dropna(subset=[METRIC])
        df["_t"] = df["quarter"].map(_q_ord)
        df = df.sort_values("_t")
        yield label, cog, df["_t"].to_numpy(), df[METRIC].to_numpy()


def run(artifacts: Path, min_side: int, hac_lags: int):
    t_real = _q_ord(CHATGPT_QUARTER)
    real_rows, plac_rows = [], []
    for label, cog, t_all, y_all in load(artifacts):
        n_post = int((t_all >= t_real).sum())
        pre = t_all < t_real
        t, y = t_all[pre], y_all[pre]
        cands = [b for b in range(int(t.min()), t_real)
                 if (t < b).sum() >= min_side and (t >= b).sum() >= min_side and b + n_post <= t_real]
        for spec in SPECS:
            r = fit_break(t_all, y_all, t_real, spec, hac_lags)
            pl = []
            for b in cands:
                w = t < b + n_post
                p = fit_break(t[w], y[w], b, spec, hac_lags)
                plac_rows.append({"corpus": label, "cog_load": cog, "spec": spec,
                                  "placebo_quarter": f"{b // 4}Q{b % 4 + 1}", **p})
                pl.append(p["slope_change"])
            pl = np.array(pl)
            z = (r["slope_change"] - pl.mean()) / pl.std(ddof=1) if len(pl) > 1 else np.nan
            real_rows.append({"corpus": label, "cog_load": cog, "spec": spec, "n_placebo": len(pl),
                              **r, "z_vs_own_placebo": float(z)})
    real, plac = pd.DataFrame(real_rows), pd.DataFrame(plac_rows)

    out = []
    for spec in SPECS:
        r = real[real["spec"] == spec].copy()
        pt = plac.loc[plac["spec"] == spec, "t"].to_numpy()
        r["placebo_sig_rate"] = float(((plac.loc[plac["spec"] == spec, "slope_change"] > 0)
                                       & (plac.loc[plac["spec"] == spec, "p_hac"] < ALPHA)).mean())
        r["p_cal"] = [(1 + (pt >= tv).sum()) / (1 + len(pt)) for tv in r["t"]]
        r["p_cal_bh"] = multipletests(r["p_cal"], method="fdr_bh")[1]
        r["sig_hac"] = (r["slope_change"] > 0) & (r["p_hac"] < ALPHA)
        r["sig_cal"] = r["p_cal"] < ALPHA
        r["sig_cal_bh"] = r["p_cal_bh"] < ALPHA
        out.append(r)
    return pd.concat(out, ignore_index=True), plac


def cog_load(res: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for spec in SPECS:
        se = res[(res["spec"] == spec) & (res["cog_load"] != "external")]
        hi, lo = se[se["cog_load"] == "high"], se[se["cog_load"] == "low"]
        for col in ("sig_hac", "sig_cal", "sig_cal_bh"):
            a, b = int(hi[col].sum()), int(lo[col].sum())
            _, p = stats.fisher_exact([[a, len(hi) - a], [b, len(lo) - b]], alternative="greater")
            rows.append({"spec": spec, "test": f"Fisher on {col}", "high": f"{a}/{len(hi)}",
                         "low": f"{b}/{len(lo)}", "p_one_sided": p})
        for col in ("t", "z_vs_own_placebo"):
            u = stats.mannwhitneyu(hi[col], lo[col], alternative="greater")
            rows.append({"spec": spec, "test": f"Mann-Whitney on {col}",
                         "high": f"median {hi[col].median():.2f}", "low": f"median {lo[col].median():.2f}",
                         "p_one_sided": float(u.pvalue)})
    return pd.DataFrame(rows)


def plot(res: pd.DataFrame, plac: pd.DataFrame, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 10), sharey=True)
    order = (res[res["spec"] == "quad"].sort_values("t")["corpus"].tolist())
    for ax, spec in zip(axes, SPECS):
        r = res[res["spec"] == spec].set_index("corpus").loc[order]
        pt = plac[plac["spec"] == spec]
        crit = np.quantile(pt["t"], 1 - ALPHA)
        for i, c in enumerate(order):
            ts = pt.loc[pt["corpus"] == c, "t"]
            ax.scatter(ts, np.full(len(ts), i), s=9, color="0.75", zorder=1)
            col = COLOR[r.loc[c, "cog_load"]]
            ax.scatter(r.loc[c, "t"], i, s=80, zorder=3, edgecolor=col, linewidths=1.6,
                       facecolor=col if r.loc[c, "sig_cal"] else "white")
        ax.axvline(crit, color="k", ls="--", lw=1, label=f"placebo 95th pct (t={crit:.1f})")
        ax.axvline(1.96, color="0.5", ls=":", lw=1, label="nominal t=1.96")
        n_sig = int(r["sig_cal"].sum())
        se = r["cog_load"] != "external"
        ax.set_title(f"{spec} trend: placebo false-rise rate {100 * r['placebo_sig_rate'].iloc[0]:.0f}%\n"
                     f"calibrated significant: {n_sig}/{len(r)} (SE {int(r.loc[se, 'sig_cal'].sum())}/"
                     f"{int(se.sum())}; BH {int(r['sig_cal_bh'].sum())}/{len(r)})", fontsize=11)
        ax.set_xlabel("slope-change t-statistic at 2022Q4 (grey = matched placebo breaks)")
        ax.grid(True, axis="x", alpha=0.3)
        ax.legend(fontsize=8, loc="lower right")
    axes[0].set_yticks(range(len(order)))
    axes[0].set_yticklabels(order, fontsize=9)
    cog = res.drop_duplicates("corpus").set_index("corpus")["cog_load"]
    for tick in axes[0].get_yticklabels():
        tick.set_color(COLOR[cog[tick.get_text()]])
    fig.suptitle("Family 8, placebo-calibrated: did answer similarity turn up at ChatGPT?", fontsize=13)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"Saved figure -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--artifacts", type=Path, default=ARTIFACTS)
    ap.add_argument("--min-side", type=int, default=8)
    ap.add_argument("--hac-lags", type=int, default=4)
    a = ap.parse_args()
    res, plac = run(a.artifacts, a.min_side, a.hac_lags)
    cl = cog_load(res)
    d = summary_dir(a.artifacts) / "data"
    d.mkdir(parents=True, exist_ok=True)
    res.to_csv(d / "8_robust_break.csv", index=False)
    plac.to_csv(d / "8_robust_placebo_t.csv", index=False)
    cl.to_csv(d / "9_cog_load_robust.csv", index=False)
    pd.set_option("display.width", 220)
    wide = res.pivot(index=["corpus", "cog_load"], columns="spec",
                     values=["t", "p_hac", "p_cal", "sig_cal_bh"]).round(3)
    print(wide.sort_index(level=1).to_string())
    for spec in SPECS:
        r = res[res["spec"] == spec]
        se = r["cog_load"] != "external"
        print(f"\n[{spec}] placebo false-rise rate {100 * r['placebo_sig_rate'].iloc[0]:.1f}%; "
              f"nominal HAC sig {int(r['sig_hac'].sum())}/30; calibrated {int(r['sig_cal'].sum())}/30 "
              f"(SE {int(r.loc[se, 'sig_cal'].sum())}/26, ext {int(r.loc[~se, 'sig_cal'].sum())}/4); "
              f"after BH {int(r['sig_cal_bh'].sum())}/30: "
              + ", ".join(r.loc[r["sig_cal_bh"], "corpus"]))
    print("\nFamily 9 (high vs low load):\n" + cl.round(4).to_string(index=False))
    plot(res, plac, summary_dir(a.artifacts) / "8_robust_break.png")


if __name__ == "__main__":
    main()
