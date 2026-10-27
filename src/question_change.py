"""Test the explanation: did the questions change more on high-load sites after ChatGPT?

Per SE site (26), from the parsed questions (``data/processed/<site>_questions.parquet``; Cross
Validated is ``questions.parquet``) and the family-14 tag series:

* ``volume_drop``   - log(mean questions/quarter 2023Q1-) - log(mean 2021Q1-2022Q3) (negative = fewer)
* ``q_len_change``  - log ratio of median question length (words), same windows
* ``answers_per_q`` - change in mean answers per question, same windows
* ``tag_jsd_post``  - mean tag-mix distance from the pre-ChatGPT mix after 2022Q4 minus before
                      (``tag_jsd_r`` in ``14_tag_topics.csv``)

Then (a) high vs low cognitive load (Mann-Whitney, two-sided), and (b) Spearman correlation of
each change with the site's similarity change - the 2022Q4 slope change under the curved trend,
as a z against its own placebo dates (``8_robust_break.csv``, spec ``quad``) and the plain
linear slope change from family 8.

Output: ``artifacts/summary/data/15_question_change.csv`` and
``artifacts/summary/15_question_change.png``.

    python src/question_change.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from paths import ALL_SOURCES, ARTIFACTS, source_dir, summary_dir

PROC = Path(__file__).resolve().parents[1] / "data" / "processed"
PRE = ("2021Q1", "2022Q3")
POST_FROM = "2023Q1"
FILES = {"cross-validated": "questions.parquet", "seasoned-advice": "cooking_questions.parquet"}
MEASURES = ("volume_drop", "q_len_change", "answers_per_q", "tag_jsd_post")
COLOR = {"high": "#08519c", "low": "#e6550d"}


def _qfile(folder: str) -> Path:
    if folder in FILES:
        return PROC / FILES[folder]
    stem = {"crypto": "crypto"}.get(folder, folder)
    return PROC / f"{stem}_questions.parquet"


def site_row(folder: str, label: str, cog: str) -> dict | None:
    f = _qfile(folder)
    if not f.exists():
        print(f"skip {label}: no {f.name}")
        return None
    q = pd.read_parquet(f, columns=["quarter", "text", "answer_count"])
    q = q[q["quarter"] < "2026Q2"]  # last quarter is partial
    pre = q[(q["quarter"] >= PRE[0]) & (q["quarter"] <= PRE[1])]
    post = q[q["quarter"] >= POST_FROM]
    n_pre = pre.groupby("quarter").size().mean()
    n_post = post.groupby("quarter").size().mean()
    wl = lambda d: d["text"].fillna("").str.split().str.len().median()
    row = {"corpus": label, "cog_load": cog,
           "q_per_qtr_pre": n_pre, "q_per_qtr_post": n_post,
           "volume_drop": float(np.log(n_post / n_pre)),
           "q_len_change": float(np.log(wl(post) / wl(pre))),
           "answers_per_q": float(post["answer_count"].mean() - pre["answer_count"].mean())}
    tag = source_dir(folder, ARTIFACTS) / "data" / "14_tag_topics.csv"
    if tag.exists():
        t = pd.read_csv(tag).dropna(subset=["tag_jsd_r"])
        row["tag_jsd_post"] = float(t.loc[t["quarter"] >= "2022Q4", "tag_jsd_r"].mean()
                                    - t.loc[t["quarter"] < "2022Q4", "tag_jsd_r"].mean())
    return row


def main() -> None:
    rows = [r for f, l, c in ALL_SOURCES if c != "external" and (r := site_row(f, l, c))]
    df = pd.DataFrame(rows)
    sim = pd.read_csv(summary_dir(ARTIFACTS) / "data" / "8_robust_break.csv")
    quad = sim[sim["spec"] == "quad"].set_index("corpus")["z_vs_own_placebo"].rename("sim_z_quad")
    lin = sim[sim["spec"] == "linear"].set_index("corpus")["slope_change"].rename("sim_slope_linear")
    df = df.join(quad, on="corpus").join(lin, on="corpus")
    out = summary_dir(ARTIFACTS) / "data" / "15_question_change.csv"
    df.to_csv(out, index=False)

    pd.set_option("display.width", 200)
    print(df.drop(columns=["q_per_qtr_pre", "q_per_qtr_post"]).round(3)
          .sort_values(["cog_load", "volume_drop"]).to_string(index=False))
    hi, lo = df[df["cog_load"] == "high"], df[df["cog_load"] == "low"]
    print("\nHigh vs low load (median; Mann-Whitney two-sided):")
    for m in MEASURES:
        u = stats.mannwhitneyu(hi[m].dropna(), lo[m].dropna(), alternative="two-sided")
        print(f"  {m:<14} high {hi[m].median():+.3f}  low {lo[m].median():+.3f}  p={u.pvalue:.3f}")
    print("\nSpearman with the site's similarity change (n=26):")
    for m in MEASURES:
        for s in ("sim_z_quad", "sim_slope_linear"):
            d = df[[m, s]].dropna()
            r, p = stats.spearmanr(d[m], d[s])
            print(f"  {m:<14} vs {s:<17} rho={r:+.2f}  p={p:.3f}")

    fig, axes = plt.subplots(1, len(MEASURES), figsize=(16, 4.2), sharey=True)
    for ax, m in zip(axes, MEASURES):
        for cog, d in df.groupby("cog_load"):
            ax.scatter(d[m], d["sim_z_quad"], color=COLOR[cog], label=f"{cog} load", s=35)
        d = df[[m, "sim_z_quad"]].dropna()
        r, p = stats.spearmanr(d[m], d["sim_z_quad"])
        ax.set_title(f"{m}  (rho={r:+.2f}, p={p:.2f})", fontsize=10)
        ax.axhline(0, color="0.6", lw=0.8)
        ax.axvline(0, color="0.6", lw=0.8)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("similarity change at 2022Q4\n(curved trend, z vs own placebos)")
    axes[0].legend(fontsize=8)
    fig.suptitle("Did the questions change more where answer similarity rose? (26 SE sites)", fontsize=12)
    fig.tight_layout()
    png = summary_dir(ARTIFACTS) / "15_question_change.png"
    fig.savefig(png, dpi=150)
    print(f"\nWrote {out}\nSaved figure -> {png}")


if __name__ == "__main__":
    main()
