"""#3 confound test — overall vs within-topic significance across corpora.

The homogenization question is whether answers about the SAME topic grow more similar.
This reads each corpus's family-6 within-topic series and, for both the unconditioned
(overall) and topic-controlled (within-topic) pairwise cosine, reports the post-ChatGPT
trend (Theil-Sen slope + Mann-Kendall p) and the segmented-regression slope change.

If overall rises significantly but within-topic does not, the aggregate rise is a
topic-composition effect, not within-topic style convergence.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

CHATGPT_QUARTER = "2022Q4"
CORPORA = [
    ("cross-validated", "Cross Validated", "high"),
    ("philosophy", "Philosophy", "high"),
    ("economics", "Economics", "high"),
    ("seasoned-advice", "Seasoned Advice", "low"),
    ("travel", "Travel", "low"),
]


def _q_ord(q: str) -> int:
    return int(q[:4]) * 4 + (int(q[5:]) - 1)


def _its_slope_change(t: np.ndarray, y: np.ndarray, t_break: int) -> tuple[float, float]:
    lvl = (t >= t_break).astype(float)
    tp = np.clip(t - t_break, 0, None).astype(float)
    X = np.column_stack([np.ones_like(t, float), t.astype(float), lvl, tp])
    f = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    return float(f.params[3]), float(f.pvalues[3])


def analyze(csv: Path, label: str, cog: str, t_break: int) -> list[dict]:
    d = pd.read_csv(csv).sort_values("quarter")
    d["_t"] = d["quarter"].map(_q_ord)
    out = []
    for col, name in [("overall_cosine", "overall"), ("within_topic_cosine", "within")]:
        dd = d.dropna(subset=[col])
        t, y = dd["_t"].to_numpy(), dd[col].to_numpy()
        post = dd[dd["_t"] >= t_break]
        tp, yp = post["_t"].to_numpy(), post[col].to_numpy()
        sc, sc_p = _its_slope_change(t, y, t_break)
        tau, mk_p = stats.kendalltau(tp, yp)
        out.append({"corpus": label, "cog_load": cog, "metric": name,
                    "post_slope": float(stats.theilslopes(yp, tp)[0]),
                    "mk_post_tau": float(tau), "mk_post_p": float(mk_p),
                    "its_slope_change": sc, "its_slope_change_p": sc_p})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Overall vs within-topic significance")
    ap.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    ap.add_argument("--out-csv", type=Path, default=Path("artifacts/10_within_vs_overall.csv"))
    args = ap.parse_args()

    t_break = _q_ord(CHATGPT_QUARTER)
    rows = []
    for folder, label, cog in CORPORA:
        csv = args.artifacts / folder / "data" / "6_within_topic_similarity.csv"
        if not csv.exists():
            print(f"  skip {label}: {csv} missing")
            continue
        rows += analyze(csv, label, cog, t_break)
    table = pd.DataFrame(rows)
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out_csv, index=False)
    show = table.pivot(index="corpus", columns="metric",
                       values=["post_slope", "mk_post_p"])
    pd.set_option("display.float_format", lambda x: f"{x:+.4f}")
    print(show.to_string())
    print(f"\nWrote -> {args.out_csv}")
    print("\nReading: overall MK_post_p small = aggregate rises; within MK_post_p large = "
          "topic-controlled similarity does NOT rise -> topic-composition, not style homogenization.")


if __name__ == "__main__":
    main()
