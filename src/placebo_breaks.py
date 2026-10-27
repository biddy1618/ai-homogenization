"""Placebo break dates for family 8: does the segmented-regression test find "breaks" where none
should exist?

For every source, the family-5 whole-text series (``5_semantic_bert.csv``, metric
``sem_pairwise_cosine``) is cut to the quarters BEFORE ChatGPT (< 2022Q4), so the real change cannot
leak in, and the same ITS model as ``significance.py`` (OLS, Newey-West HAC, 4 lags) is fitted with a
fake break at every quarter from ``--first`` to ``--last`` that leaves at least ``--min-side``
quarters on each side. Outputs:

* ``artifacts/summary/data/8_placebo_breaks.csv`` - one row per source x placebo quarter;
* ``artifacts/summary/data/8_placebo_summary.csv`` - per source: share of placebo breaks with a
  significant upward slope change, and where the real 2022Q4 slope change falls among them
  (rank and z-score against the placebo distribution);
* ``artifacts/summary/8_placebo.png``.

Under no effect, a two-sided 5% test flags a significant *rise* about 2.5% of the time.

    python src/placebo_breaks.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from paths import ALL_SOURCES, ARTIFACTS, source_dir, summary_dir
from significance import CHATGPT_QUARTER, _q_ord, its_regression

METRIC = "sem_pairwise_cosine"
ALPHA = 0.05
COLOR = {"high": "#08519c", "low": "#e6550d", "external": "#238b45"}


def _label(t: int) -> str:
    return f"{t // 4}Q{t % 4 + 1}"


def run(artifacts: Path, first: str, last: str, min_side: int, hac_lags: int, matched: bool = False):
    t_real = _q_ord(CHATGPT_QUARTER)
    rows, summ = [], []
    for folder, label, cog in ALL_SOURCES:
        csv = source_dir(folder, artifacts) / "data" / "5_semantic_bert.csv"
        if not csv.exists():
            print(f"skip {label}: no {csv}")
            continue
        df = pd.read_csv(csv).dropna(subset=[METRIC])
        df["_t"] = df["quarter"].map(_q_ord)
        df = df.sort_values("_t")
        t_all, y_all = df["_t"].to_numpy(), df[METRIC].to_numpy()
        real = its_regression(t_all, y_all, t_real, hac_lags)

        pre = t_all < t_real
        t, y = t_all[pre], y_all[pre]
        n_post_real = int((t_all >= t_real).sum())
        cands = [b for b in range(_q_ord(first), _q_ord(last) + 1)
                 if (t < b).sum() >= min_side and (t >= b).sum() >= min_side
                 and (not matched or b + n_post_real <= t_real)]
        pl = []
        for b in cands:
            # matched: the placebo sees exactly as many post-break quarters as the real break
            w = (t < b + n_post_real) if matched else np.ones_like(t, dtype=bool)
            r = its_regression(t[w], y[w], b, hac_lags)
            rows.append({"corpus": label, "cog_load": cog, "placebo_quarter": _label(b),
                         "slope_change": r["slope_change"], "slope_change_p": r["slope_change_p"],
                         "level_jump": r["level_jump"], "level_jump_p": r["level_jump_p"]})
            pl.append(r)
        if not pl:
            continue
        sc = np.array([r["slope_change"] for r in pl])
        p = np.array([r["slope_change_p"] for r in pl])
        sd = sc.std(ddof=1) if len(sc) > 1 else np.nan
        summ.append({
            "corpus": label, "cog_load": cog, "n_placebo": len(pl),
            "placebo_sig_up": int(((sc > 0) & (p < ALPHA)).sum()),
            "placebo_sig_down": int(((sc < 0) & (p < ALPHA)).sum()),
            "placebo_sig_up_share": float(((sc > 0) & (p < ALPHA)).mean()),
            "real_slope_change": real["slope_change"], "real_p": real["slope_change_p"],
            "real_sig_up": bool(real["slope_change"] > 0 and real["slope_change_p"] < ALPHA),
            "real_rank_share": float((sc < real["slope_change"]).mean()),
            "real_z_vs_placebo": float((real["slope_change"] - sc.mean()) / sd) if sd else np.nan,
            "placebo_abs_mean": float(np.abs(sc).mean()),
        })
    return pd.DataFrame(rows), pd.DataFrame(summ)


def plot(rows: pd.DataFrame, summ: pd.DataFrame, out: Path) -> None:
    d = summ.sort_values("real_slope_change").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11, 0.32 * len(d) + 1.8))
    ax.axvline(0, color="0.5", lw=1)
    for i, r in d.iterrows():
        sub = rows[rows["corpus"] == r["corpus"]]
        sig = (sub["slope_change"] > 0) & (sub["slope_change_p"] < ALPHA)
        ax.scatter(sub.loc[~sig, "slope_change"], np.full((~sig).sum(), i), s=10, color="0.7", zorder=1)
        ax.scatter(sub.loc[sig, "slope_change"], np.full(sig.sum(), i), s=14, color="0.3", zorder=2)
        c = COLOR[r["cog_load"]]
        ax.scatter(r["real_slope_change"], i, s=80, zorder=3, edgecolor=c, linewidths=1.6,
                   facecolor=c if r["real_sig_up"] else "white")
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels(d["corpus"], fontsize=9)
    for tick, (_, r) in zip(ax.get_yticklabels(), d.iterrows()):
        tick.set_color(COLOR[r["cog_load"]])
    tot_sig, tot = int(summ["placebo_sig_up"].sum()), int(summ["n_placebo"].sum())
    ax.set_xlabel("slope change in mean pairwise cosine (per quarter)")
    ax.set_title("Placebo break dates (pre-ChatGPT data only) vs the real 2022Q4 break\n"
                 f"grey = placebo quarters (dark = significant rise: {tot_sig}/{tot} = "
                 f"{100 * tot_sig / tot:.1f}%); coloured = 2022Q4 (filled = significant rise: "
                 f"{int(summ['real_sig_up'].sum())}/{len(summ)})", fontsize=11)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"Saved figure -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--artifacts", type=Path, default=ARTIFACTS)
    ap.add_argument("--first", default="2016Q1")
    ap.add_argument("--last", default="2020Q4")
    ap.add_argument("--min-side", type=int, default=8)
    ap.add_argument("--hac-lags", type=int, default=4)
    ap.add_argument("--matched", action="store_true",
                    help="each placebo uses only as many post-break quarters as the real break has")
    a = ap.parse_args()
    rows, summ = run(a.artifacts, a.first, a.last, a.min_side, a.hac_lags, a.matched)
    sfx = "_matched" if a.matched else ""
    d = summary_dir(a.artifacts) / "data"
    d.mkdir(parents=True, exist_ok=True)
    rows.to_csv(d / f"8_placebo_breaks{sfx}.csv", index=False)
    summ.to_csv(d / f"8_placebo_summary{sfx}.csv", index=False)
    pd.set_option("display.width", 200)
    print(summ[["corpus", "cog_load", "n_placebo", "placebo_sig_up", "placebo_sig_down",
                "real_sig_up", "real_rank_share", "real_z_vs_placebo"]].round(2).to_string(index=False))
    tot_sig, tot = int(summ["placebo_sig_up"].sum()), int(summ["n_placebo"].sum())
    print(f"\nPlacebo significant rises: {tot_sig}/{tot} = {100 * tot_sig / tot:.1f}% "
          f"(down: {int(summ['placebo_sig_down'].sum())}); real 2022Q4: "
          f"{int(summ['real_sig_up'].sum())}/{len(summ)}")
    print(f"Real slope change above every placebo: {int((summ['real_rank_share'] == 1).sum())}/{len(summ)}; "
          f"median z vs placebo {summ['real_z_vs_placebo'].median():.2f}")
    plot(rows, summ, summary_dir(a.artifacts) / f"8_placebo{sfx}.png")


if __name__ == "__main__":
    main()
