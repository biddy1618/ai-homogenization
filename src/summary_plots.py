"""Cross-site summary ("forest") plots for families 11, 12, 13 and 14.

One row per site (coloured by group), one column per measure. Each dot is that site's
post-ChatGPT slope change (family-8 interrupted time series on the measure); filled = p<0.05.
Column titles count significant increases and decreases per group.

    python src/summary_plots.py     # -> artifacts/summary/{11,12,13,14}_*_summary.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from paths import ALL_SOURCES, source_dir, summary_dir
from significance import COG_COLOR, COG_LABEL

ALPHA = 0.05
GROUP_ORDER = {"high": 0, "low": 1, "external": 2}


def _counts(d: pd.DataFrame, groups: list[str]) -> str:
    parts = []
    for g in groups:
        s = d[d["cog_load"] == g]
        if s.empty:
            continue
        up = int(((s["slope_change"] > 0) & (s["slope_change_p"] < ALPHA)).sum())
        dn = int(((s["slope_change"] < 0) & (s["slope_change_p"] < ALPHA)).sum())
        short = {"high": "high", "low": "low", "external": "ext"}[g]
        parts.append(f"{short} {up}\u2191 {dn}\u2193 /{len(s)}")
    return "  ".join(parts)


def forest(table: pd.DataFrame, columns: list[tuple[str, str]], title: str, out: Path,
           note: str = "") -> None:
    """``columns`` = [(metric, column title)]; rows ordered by group, then by the first column."""
    first = table[table["metric"] == columns[0][0]].set_index("corpus")["slope_change"]
    sites = (table[["corpus", "cog_load"]].drop_duplicates("corpus")
             .assign(_g=lambda d: d["cog_load"].map(GROUP_ORDER), _v=lambda d: d["corpus"].map(first))
             .sort_values(["_g", "_v"], ascending=[False, True]))
    y = {c: i for i, c in enumerate(sites["corpus"])}
    groups = [g for g in GROUP_ORDER if g in set(sites["cog_load"])]

    fig, axes = plt.subplots(1, len(columns), figsize=(4.6 * len(columns) + 2.2, 0.3 * len(y) + 2.4),
                             sharey=True, squeeze=False)
    for ax, (metric, ctitle) in zip(axes[0], columns):
        d = table[table["metric"] == metric]
        ax.axvline(0, color="0.5", lw=1)
        for _, r in d.iterrows():
            c = COG_COLOR[r["cog_load"]]
            sig = r["slope_change_p"] < ALPHA
            ax.scatter(r["slope_change"], y[r["corpus"]], s=55, zorder=3, edgecolor=c,
                       facecolor=c if sig else "white", linewidths=1.5)
        ax.set_title(f"{ctitle}\n{_counts(d, groups)}", fontsize=9.5)
        ax.grid(True, axis="x", alpha=0.3)
        ax.tick_params(axis="x", labelsize=8)
    # group separators
    bounds = sites.reset_index(drop=True)
    for i in range(1, len(bounds)):
        if bounds.loc[i, "cog_load"] != bounds.loc[i - 1, "cog_load"]:
            for ax in axes[0]:
                ax.axhline(i - 0.5, color="0.75", lw=0.8, ls="--")
    ax0 = axes[0][0]
    ax0.set_yticks(list(y.values()))
    ax0.set_yticklabels(list(y.keys()), fontsize=8.5)
    for tick, (_, r) in zip(ax0.get_yticklabels(), sites.iterrows()):
        tick.set_color(COG_COLOR[r["cog_load"]])
    ax0.set_ylim(-0.7, len(y) - 0.3)
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor="0.3", markeredgecolor="0.3",
                      markersize=8, label="p < 0.05"),
               Line2D([0], [0], marker="o", color="w", markerfacecolor="white", markeredgecolor="0.3",
                      markersize=8, label="not significant")]
    handles += [Line2D([0], [0], marker="s", color="w", markerfacecolor=COG_COLOR[g], markersize=9,
                       label=COG_LABEL[g]) for g in groups]
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), fontsize=8.5, frameon=False,
               bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(title, fontsize=12)
    foot = ("Each dot: post-ChatGPT slope change of the measure (per quarter), from an interrupted "
            "time series with a break at 2022Q4. " + note)
    fig.text(0.5, 0.035, foot, ha="center", va="bottom", fontsize=8, color="dimgray", wrap=True)
    fig.tight_layout(rect=(0, 0.08, 1, 0.97))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Saved figure -> {out}")


def _per_source(name: str, sources) -> pd.DataFrame:
    rows = []
    for folder, label, cog in sources:
        f = source_dir(folder) / "data" / name
        if f.exists():
            rows.append(pd.read_csv(f).assign(corpus=label, cog_load=cog))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def main() -> None:
    sd = summary_dir()
    d11 = pd.read_csv(sd / "data" / "11_same_question_all.csv")
    forest(d11, [("within_question_cosine", "Answers to the SAME question\n(similarity to each other)"),
                 ("overall_cosine", "Same answers, any pair\n(reference)")],
           "Family 11 - do answers to the same question become more alike after ChatGPT?",
           sd / "11_same_question_summary.png",
           "Left: mean similarity among answers to the same question. Right: the same answers "
           "paired at random within the quarter.")

    d13 = _per_source("13_decomposition_significance.csv", ALL_SOURCES)
    forest(d13, [("within_cosine", "Same-topic answer pairs\n(similarity, + = converging)"),
                 ("eff_topics_r", "Effective number of topics\n(\u2212 = fewer subjects)"),
                 ("comp_jsd_r", "Topic-mix drift from pre-ChatGPT\n(JSD, + = shifting)")],
           "Family 13 - K-means topics (K=50): converging within topics, or subjects narrowing?",
           sd / "13_topic_summary.png",
           "Topics: 50 K-means clusters over all quarters. Diversity and drift on random "
           "100-answer samples per quarter.")

    d14 = pd.read_csv(sd / "data" / "14_tag_topics_all.csv")
    forest(d14, [("within_tag_cosine", "Answers sharing a tag\n(similarity, + = converging)"),
                 ("eff_tags_r", "Effective number of tags\n(\u2212 = fewer subjects)"),
                 ("tag_jsd_r", "Tag-mix drift from pre-ChatGPT\n(JSD, + = shifting)")],
           "Family 14 - Stack Exchange tags: converging within a subject, or subjects narrowing?",
           sd / "14_tag_summary.png",
           "Topics: the question's tags, chosen by the asker. Diversity and drift on random "
           "100-answer samples per quarter.")

    f12 = sd / "data" / "12_anchor_all.csv"
    if f12.exists():
        d12 = pd.read_csv(f12)
        forest(d12, [("ai_match_cosine", "Similarity to GPT's answer\nfor the same question"),
                     ("lc_ai_match_cosine", "Same, first 120 tokens of both\n(length check)"),
                     ("pull", "Pull: same question minus\nsame-tag questions")],
               "Family 12 - do human answers move towards what GPT would write?",
               sd / "12_anchor_summary.png",
               "GPT anchor: gpt-4o-mini answer(s) to each sampled question. Pull isolates "
               "question-specific GPT-likeness from subject and length.")


if __name__ == "__main__":
    main()
