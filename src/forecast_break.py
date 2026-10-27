"""Forecast-break test at 2022Q4 for question volume and for answer similarity (26 SE sites).

For a break quarter b, a linear or quadratic trend is fitted to the ``--fit`` quarters before b and
extrapolated over the next ``--horizon`` quarters; the break statistic is the mean forecast error
in units of the fit's residual SD (negative = below trend). The same statistic is computed at every
placebo quarter whose fit and horizon lie entirely before 2022Q4. Per site, the real value is
ranked among its own placebos; pooled, the 26 real values are compared with all placebo values.

Series: ``volume`` = log questions per quarter (``data/processed/*_questions.parquet``);
``similarity`` = family-5 whole-text mean pairwise cosine.

Output: ``artifacts/summary/data/17_forecast_break.csv`` and ``artifacts/summary/17_forecast_break.png``.

    python src/forecast_break.py
"""
from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from paths import ALL_SOURCES, ARTIFACTS, source_dir, summary_dir
from question_change import _qfile
from significance import CHATGPT_QUARTER, _q_ord

COLOR = {"high": "#08519c", "low": "#e6550d"}


def forecast_stat(t: np.ndarray, y: np.ndarray, b: int, fit: int, horizon: int, deg: int) -> float:
    tr = (t >= b - fit) & (t < b)
    te = (t >= b) & (t < b + horizon)
    if tr.sum() < fit - 1 or te.sum() < horizon:
        return np.nan
    c = np.polyfit(t[tr] - b, y[tr], deg)
    sd = np.std(y[tr] - np.polyval(c, t[tr] - b), ddof=deg + 1)
    return float(np.mean(y[te] - np.polyval(c, t[te] - b)) / sd)


def series(folder: str, kind: str):
    if kind == "volume":
        q = pd.read_parquet(_qfile(folder), columns=["quarter"])
        n = q[q["quarter"] < "2026Q2"].groupby("quarter").size()
        return np.array([_q_ord(x) for x in n.index]), np.log(n.to_numpy())
    d = pd.read_csv(source_dir(folder, ARTIFACTS) / "data" / "5_semantic_bert.csv").dropna(
        subset=["sem_pairwise_cosine"])
    return d["quarter"].map(_q_ord).to_numpy(), d["sem_pairwise_cosine"].to_numpy()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fit", type=int, default=16, help="quarters used to fit the trend")
    ap.add_argument("--horizon", type=int, default=4, help="quarters after the break")
    a = ap.parse_args()
    t_real = _q_ord(CHATGPT_QUARTER)
    rows = []
    for folder, label, cog in ALL_SOURCES:
        if cog == "external":
            continue
        for kind in ("volume", "similarity"):
            t, y = series(folder, kind)
            for deg, spec in ((1, "linear"), (2, "quad")):
                real = forecast_stat(t, y, t_real, a.fit, a.horizon, deg)
                pl = [forecast_stat(t, y, b, a.fit, a.horizon, deg)
                      for b in range(int(t.min()) + a.fit, t_real - a.horizon + 1)]
                pl = np.array([x for x in pl if np.isfinite(x)])
                rows.append({"corpus": label, "cog_load": cog, "series": kind, "spec": spec,
                             "real": real, "n_placebo": len(pl), "placebo": pl,
                             "rank_low": float((pl <= real).mean()), "rank_high": float((pl >= real).mean())})
    df = pd.DataFrame(rows)

    print(f"fit {a.fit} quarters, horizon {a.horizon}; statistic = mean forecast error / residual SD")
    for (kind, spec), d in df.groupby(["series", "spec"]):
        pl = np.concatenate(d["placebo"].to_list())
        crit_lo, crit_hi = np.quantile(pl, [0.025, 0.975])
        below = int((d["real"] < crit_lo).sum())
        above = int((d["real"] > crit_hi).sum())
        own_lo = int((d["rank_low"] == 0).sum())
        own_hi = int((d["rank_high"] == 0).sum())
        print(f"\n[{kind}, {spec}] median real {d['real'].median():+.2f} vs placebo median "
              f"{np.median(pl):+.2f} (2.5-97.5%: {crit_lo:+.2f}..{crit_hi:+.2f}; n={len(pl)})")
        print(f"  beyond pooled placebo range: below {below}/26, above {above}/26; "
              f"beyond every own placebo: below {own_lo}/26, above {own_hi}/26")
        for cog in ("high", "low"):
            s = d[d["cog_load"] == cog]
            print(f"  {cog:>4}: median {s['real'].median():+.2f}; above pooled 97.5% "
                  f"{int((s['real'] > crit_hi).sum())}/{len(s)}, below 2.5% {int((s['real'] < crit_lo).sum())}/{len(s)}")
    out = summary_dir(ARTIFACTS) / "data" / "17_forecast_break.csv"
    df.drop(columns="placebo").to_csv(out, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13, 8), sharey=True)
    for ax, kind in zip(axes, ("volume", "similarity")):
        d = df[(df["series"] == kind) & (df["spec"] == "linear")].sort_values("real").reset_index(drop=True)
        for i, r in d.iterrows():
            ax.scatter(r["placebo"], np.full(len(r["placebo"]), i), s=8, color="0.75")
            ax.scatter(r["real"], i, s=70, color=COLOR[r["cog_load"]], zorder=3)
        ax.set_yticks(range(len(d)))
        ax.set_yticklabels(d["corpus"], fontsize=8)
        ax.axvline(0, color="0.5", lw=1)
        ax.set_title(f"{'log question volume' if kind == 'volume' else 'answer similarity'}")
        ax.set_xlabel(f"forecast error in the {a.horizon} quarters after the break (residual SDs)")
        ax.grid(alpha=0.3, axis="x")
    fig.suptitle("2022Q4 (coloured) vs placebo quarters (grey): linear trend, "
                 f"{a.fit}-quarter fit", fontsize=12)
    fig.tight_layout()
    png = summary_dir(ARTIFACTS) / "17_forecast_break.png"
    fig.savefig(png, dpi=150)
    print(f"\nWrote {out}\nSaved figure -> {png}")


if __name__ == "__main__":
    main()
