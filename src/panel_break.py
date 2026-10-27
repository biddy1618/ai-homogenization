"""Pooled panel break test: is there an AVERAGE ChatGPT-timed upturn across sites?

Per-site break tests cannot tell a 2022Q4 turn from smooth curvature (see ``robust_break.py``). Here
all sites in a group are fitted together. Each site's family-5 whole-text series is standardised by
its pre-ChatGPT SD; each site keeps its own intercept and its own linear or quadratic trend; the
level jump and the slope change at the break are SHARED. For a high-vs-low comparison the slope
change gets a high-load interaction.

Inference is by joint placebo dates: the same fake break quarter is applied to every site, using
pre-ChatGPT data only and the same number of post-break quarters as the real break (15). The
placebo p-value is the rank of the real shared slope change among the placebo estimates.

Outputs: ``artifacts/summary/data/8_panel_break.csv`` (real + placebo estimates) and
``artifacts/summary/8_panel_break.png``.

    python src/panel_break.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from paths import ARTIFACTS, summary_dir
from robust_break import load
from significance import CHATGPT_QUARTER, _q_ord

SPECS = ("linear", "quad")
MIN_SIDE = 8
GROUPS = {"all SE": ("high", "low"), "high-load SE": ("high",), "low-load SE": ("low",),
          "high minus low (SE)": ("high", "low"), "external": ("external",)}


def panel_fit(series: list, t_break: int, spec: str, interaction: bool) -> float:
    """Shared slope change (or its high-load interaction) at ``t_break`` from stacked OLS."""
    blocks, ys = [], []
    n = len(series)
    for i, (cog, t, y) in enumerate(series):
        tc = (t - t.mean()) / max(t.std(), 1)
        own = [tc] + ([tc ** 2] if spec == "quad" else [])
        X_site = np.zeros((len(t), n * (1 + len(own))))
        k = i * (1 + len(own))
        X_site[:, k] = 1
        for j, c in enumerate(own, 1):
            X_site[:, k + j] = c
        post = np.clip(t - t_break, 0, None).astype(float)
        shared = [(t >= t_break).astype(float), post]
        if interaction:
            hi = float(cog == "high")
            shared += [(t >= t_break) * hi, post * hi]
        blocks.append(np.column_stack([X_site] + shared))
        ys.append(y)
    X, Y = np.vstack(blocks), np.concatenate(ys)
    beta = np.linalg.lstsq(X, Y, rcond=None)[0]
    return float(beta[-1])


def run(artifacts: Path) -> pd.DataFrame:
    t_real = _q_ord(CHATGPT_QUARTER)
    data = []
    for label, cog, t, y in load(artifacts):
        pre = t < t_real
        y = (y - y[pre].mean()) / y[pre].std(ddof=1)
        data.append((label, cog, t, y))
    n_post = 15
    rows = []
    for gname, cogs in GROUPS.items():
        inter = gname.startswith("high minus")
        sites = [d for d in data if d[1] in cogs]
        for spec in SPECS:
            real = panel_fit([(c, t, y) for _, c, t, y in sites], t_real, spec, inter)
            rows.append({"group": gname, "spec": spec, "break": CHATGPT_QUARTER, "kind": "real",
                         "n_sites": len(sites), "slope_change": real})
            t0 = min(int(t.min()) for _, _, t, _ in sites)
            for b in range(t0, t_real - n_post + 1):
                sub = []
                for _, c, t, y in sites:
                    w = (t < t_real) & (t < b + n_post)
                    if (t[w] < b).sum() >= MIN_SIDE and (t[w] >= b).sum() >= MIN_SIDE:
                        sub.append((c, t[w], y[w]))
                if len(sub) < max(3, len(sites) // 2) or (inter and len({c for c, _, _ in sub}) < 2):
                    continue
                rows.append({"group": gname, "spec": spec, "break": f"{b // 4}Q{b % 4 + 1}",
                             "kind": "placebo", "n_sites": len(sub),
                             "slope_change": panel_fit(sub, b, spec, inter)})
    return pd.DataFrame(rows)


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (g, s), d in df.groupby(["group", "spec"], sort=False):
        real = d.loc[d["kind"] == "real", "slope_change"].iloc[0]
        pl = d.loc[d["kind"] == "placebo", "slope_change"].to_numpy()
        out.append({"group": g, "spec": s, "n_sites": int(d.loc[d["kind"] == "real", "n_sites"].iloc[0]),
                    "real_slope_change_sd_per_qtr": real, "n_placebo": len(pl),
                    "placebo_max": pl.max() if len(pl) else np.nan,
                    "z_vs_placebo": (real - pl.mean()) / pl.std(ddof=1) if len(pl) > 1 else np.nan,
                    "p_rank": (1 + (pl >= real).sum()) / (1 + len(pl))})
    return pd.DataFrame(out)


def plot(df: pd.DataFrame, summ: pd.DataFrame, out: Path) -> None:
    groups = list(GROUPS)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, spec in zip(axes, SPECS):
        for i, g in enumerate(groups):
            d = df[(df["group"] == g) & (df["spec"] == spec)]
            pl = d[d["kind"] == "placebo"]["slope_change"]
            ax.scatter(pl, np.full(len(pl), i), s=12, color="0.7")
            s = summ[(summ["group"] == g) & (summ["spec"] == spec)].iloc[0]
            ax.scatter(s["real_slope_change_sd_per_qtr"], i, s=90, color="tab:red", zorder=3)
            ax.annotate(f"p={s['p_rank']:.2f}", (s["real_slope_change_sd_per_qtr"], i),
                        textcoords="offset points", xytext=(6, 6), fontsize=8)
        ax.axvline(0, color="0.5", lw=1)
        ax.set_title(f"{spec} site trends")
        ax.set_xlabel("shared slope change (pre-period SDs per quarter)")
        ax.grid(True, axis="x", alpha=0.3)
    axes[0].set_yticks(range(len(groups)))
    axes[0].set_yticklabels(groups)
    fig.suptitle("Pooled panel test: red = 2022Q4, grey = joint placebo dates (pre-ChatGPT data, "
                 "matched post length)", fontsize=11)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"Saved figure -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--artifacts", type=Path, default=ARTIFACTS)
    a = ap.parse_args()
    df = run(a.artifacts)
    summ = summarise(df)
    d = summary_dir(a.artifacts) / "data"
    df.to_csv(d / "8_panel_break.csv", index=False)
    summ.to_csv(d / "8_panel_break_summary.csv", index=False)
    pd.set_option("display.width", 200)
    print(summ.round(3).to_string(index=False))
    plot(df, summ, summary_dir(a.artifacts) / "8_panel_break.png")


if __name__ == "__main__":
    main()
