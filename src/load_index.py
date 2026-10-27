"""An objective cognitive-load index for the 26 SE sites, and family 9 re-run with it.

Text features from pre-ChatGPT posts (2019Q1-2022Q3; up to 3,000 answers and 3,000 questions per
site, fixed seed). Maths and code are stripped by the parser, so only plain-text signals are used:

* ``q_words`` / ``a_words``   - median question / answer length (words)
* ``word_len``                - mean word length (letters)
* ``long_word_share``         - share of words with 7+ letters
* ``sent_len``                - mean sentence length (words), answers
* ``fk_grade``                - Flesch-Kincaid grade level, answers (vowel-group syllable count)

``load_index`` = mean of the features' z-scores across the 26 sites. Checks: agreement with our
high/low labels (AUC), then family 9 with the index as a continuous measure: Spearman of the index
with the site's similarity change (linear slope change and HAC t from family 8; curved-trend z vs
own placebos from ``robust_break.py``), and question-length change from test 15.

Output: ``artifacts/summary/data/16_load_index.csv``, ``artifacts/summary/16_load_index.png``.

    python src/load_index.py
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from paths import ALL_SOURCES, ARTIFACTS, summary_dir
from question_change import PROC, _qfile

PRE = ("2019Q1", "2022Q3")
N = 3000
FEATURES = ("q_words", "a_words", "word_len", "long_word_share", "sent_len", "fk_grade")
WORD = re.compile(r"[A-Za-z]+")
SENT = re.compile(r"[.!?]+(?:\s|$)")
VOWELS = re.compile(r"[aeiouy]+")
COLOR = {"high": "#08519c", "low": "#e6550d"}


def _afile(folder: str) -> Path:
    q = _qfile(folder)
    return q.with_name("answers.parquet" if q.name == "questions.parquet"
                       else q.name.replace("_questions", "_answers"))


def _sample(path: Path) -> pd.Series:
    d = pd.read_parquet(path, columns=["quarter", "text"])
    d = d[(d["quarter"] >= PRE[0]) & (d["quarter"] <= PRE[1])]["text"].dropna()
    return d.sample(min(N, len(d)), random_state=0)


def _text_stats(texts: pd.Series) -> dict:
    words = sents = letters = longw = syll = 0
    for t in texts:
        ws = WORD.findall(t)
        if not ws:
            continue
        words += len(ws)
        sents += max(1, len(SENT.findall(t)))
        letters += sum(map(len, ws))
        longw += sum(len(w) >= 7 for w in ws)
        syll += sum(max(1, len(VOWELS.findall(w.lower()))) for w in ws)
    return {"word_len": letters / words, "long_word_share": longw / words,
            "sent_len": words / sents,
            "fk_grade": 0.39 * words / sents + 11.8 * syll / words - 15.59}


def main() -> None:
    rows = []
    for folder, label, cog in ALL_SOURCES:
        if cog == "external":
            continue
        a, q = _sample(_afile(folder)), _sample(_qfile(folder))
        rows.append({"corpus": label, "cog_load": cog,
                     "q_words": q.str.split().str.len().median(),
                     "a_words": a.str.split().str.len().median(), **_text_stats(a)})
        print(f"{label}: done", flush=True)
    df = pd.DataFrame(rows)
    z = (df[list(FEATURES)] - df[list(FEATURES)].mean()) / df[list(FEATURES)].std(ddof=1)
    df["load_index"] = z.mean(axis=1)

    sim = pd.read_csv(summary_dir(ARTIFACTS) / "data" / "8_robust_break.csv")
    for spec, col, name in (("linear", "slope_change", "sim_slope_linear"),
                            ("linear", "t", "sim_t_linear"),
                            ("quad", "z_vs_own_placebo", "sim_z_quad")):
        s = sim[sim["spec"] == spec].set_index("corpus")[col].rename(name)
        df = df.join(s, on="corpus")
    qc = pd.read_csv(summary_dir(ARTIFACTS) / "data" / "15_question_change.csv")
    df = df.join(qc.set_index("corpus")[["q_len_change", "answers_per_q"]], on="corpus")
    out = summary_dir(ARTIFACTS) / "data" / "16_load_index.csv"
    df.to_csv(out, index=False)

    pd.set_option("display.width", 200)
    print(df.sort_values("load_index", ascending=False)[["corpus", "cog_load", *FEATURES, "load_index"]]
          .round(2).to_string(index=False))
    hi = (df["cog_load"] == "high").astype(int)
    auc = stats.mannwhitneyu(df.loc[hi == 1, "load_index"], df.loc[hi == 0, "load_index"]).statistic \
        / (hi.sum() * (len(df) - hi.sum()))
    print(f"\nAgreement with our labels: AUC {auc:.2f}")
    for f in FEATURES:
        a = stats.mannwhitneyu(df.loc[hi == 1, f], df.loc[hi == 0, f]).statistic / (hi.sum() * (len(df) - hi.sum()))
        print(f"  {f:<16} AUC {a:.2f}")
    print("\nFamily 9 with the index (Spearman, n=26):")
    for c in ("sim_slope_linear", "sim_t_linear", "sim_z_quad", "q_len_change", "answers_per_q"):
        r, p = stats.spearmanr(df["load_index"], df[c])
        print(f"  load_index vs {c:<17} rho={r:+.2f}  p={p:.3f}")
    top = df["load_index"] >= df["load_index"].median()
    for c in ("sim_slope_linear", "sim_z_quad"):
        u = stats.mannwhitneyu(df.loc[top, c], df.loc[~top, c], alternative="greater")
        print(f"  median split on index, {c}: upper {df.loc[top, c].median():.4f} vs lower "
              f"{df.loc[~top, c].median():.4f}, one-sided p={u.pvalue:.3f}")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, c, lab in ((axes[0], "sim_slope_linear", "2022Q4 slope change (linear, family 8)"),
                       (axes[1], "sim_z_quad", "2022Q4 change, curved trend (z vs placebos)")):
        for cog, d in df.groupby("cog_load"):
            ax.scatter(d["load_index"], d[c], color=COLOR[cog], s=40, label=f"labelled {cog}")
        for _, r in df.iterrows():
            ax.annotate(r["corpus"].split()[0], (r["load_index"], r[c]), fontsize=7,
                        xytext=(3, 3), textcoords="offset points")
        rho, p = stats.spearmanr(df["load_index"], df[c])
        ax.set_title(f"rho={rho:+.2f}, p={p:.3f}", fontsize=10)
        ax.set_xlabel("objective load index (text complexity, pre-ChatGPT)")
        ax.set_ylabel(lab)
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=8)
    fig.suptitle(f"Family 9 with an objective load index (AUC vs our labels {auc:.2f})", fontsize=12)
    fig.tight_layout()
    png = summary_dir(ARTIFACTS) / "16_load_index.png"
    fig.savefig(png, dpi=150)
    print(f"\nWrote {out}\nSaved figure -> {png}")


if __name__ == "__main__":
    main()
