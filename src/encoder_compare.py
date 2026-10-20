"""Step 6: does the whole-text result hold with a second encoder (BGE-small vs MiniLM)?

For each source with both main (MiniLM) results and ``artifacts/robustness/bge/<source>/``:
  * family-8 slope change at the ChatGPT break, its p-value and direction, per encoder;
  * the slope change in units of that encoder's pre-period quarterly SD (BGE's similarity level
    is much higher than MiniLM's, so raw slopes are not comparable across encoders);
  * Spearman correlation of the two encoders' quarterly series (do they trace the same shape?).

    python src/encoder_compare.py      # -> artifacts/summary/6_encoder_compare.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

from scipy.stats import fisher_exact, mannwhitneyu

from paths import ALL_SOURCES, ARTIFACTS, bge_dir, source_dir, summary_dir
METRICS = ("sem_pairwise_cosine", "lc_sem_pairwise_cosine")
BREAK = "2022Q4"
ALPHA = 0.05


def _verdict(slope: float, p: float) -> str:
    return ("up*" if p < ALPHA else "up") if slope > 0 else ("down*" if p < ALPHA else "down")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artifacts", type=Path, default=ARTIFACTS)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    args.out = args.out or summary_dir(args.artifacts) / "data" / "6_encoder_compare.csv"

    main_sig = pd.read_csv(summary_dir(args.artifacts) / "data" / "8_significance_all.csv")
    rows = []
    for folder, label, cog in ALL_SOURCES:
        paths = {"minilm": source_dir(folder, args.artifacts), "bge": bge_dir(folder, args.artifacts)}
        if not (paths["bge"] / "data" / "8_significance.csv").exists():
            continue
        sig = {"minilm": main_sig[main_sig["corpus"] == label].set_index("metric"),
               "bge": pd.read_csv(paths["bge"] / "data" / "8_significance.csv").set_index("metric")}
        ser = {e: pd.read_csv(p / "data" / "5_semantic_bert.csv").set_index("quarter") for e, p in paths.items()}
        for metric in METRICS:
            row = {"corpus": label, "cog_load": cog, "metric": metric}
            for e in ("minilm", "bge"):
                s = sig[e].loc[metric]
                pre_sd = ser[e].loc[ser[e].index < BREAK, metric].std()
                row[f"{e}_slope_change"] = s["slope_change"]
                row[f"{e}_slope_change_sd"] = s["slope_change"] / pre_sd
                row[f"{e}_p"] = s["slope_change_p"]
                row[f"{e}_verdict"] = _verdict(s["slope_change"], s["slope_change_p"])
            both = ser["minilm"][[metric]].join(ser["bge"][[metric]], lsuffix="_m", rsuffix="_b").dropna()
            row["spearman_series"] = spearmanr(both.iloc[:, 0], both.iloc[:, 1]).statistic
            row["agree"] = row["minilm_verdict"] == row["bge_verdict"]
            rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        print("no corpus has both MiniLM and BGE results yet")
        return
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    show = out[["corpus", "cog_load", "metric", "minilm_verdict", "minilm_p", "bge_verdict", "bge_p",
                "minilm_slope_change_sd", "bge_slope_change_sd", "spearman_series", "agree"]]
    with pd.option_context("display.width", 200, "display.float_format", "{:.3g}".format):
        print(show.to_string(index=False))
    raw = out[out["metric"] == METRICS[0]]
    print(f"\nwhole text: verdict agrees in {int(raw['agree'].sum())}/{len(raw)} corpora "
          f"(* = p<{ALPHA}); opening window: "
          f"{int(out[out['metric'] == METRICS[1]]['agree'].sum())}/{len(raw)}")
    # family 9 with each encoder: high vs low cognitive load (SE only)
    se = out[(out["metric"] == METRICS[0]) & (out["cog_load"] != "external")]
    for e in ("minilm", "bge"):
        hi, lo = se[se["cog_load"] == "high"], se[se["cog_load"] == "low"]
        sh = int(((hi[f"{e}_slope_change"] > 0) & (hi[f"{e}_p"] < ALPHA)).sum())
        sl = int(((lo[f"{e}_slope_change"] > 0) & (lo[f"{e}_p"] < ALPHA)).sum())
        fp = fisher_exact([[sh, len(hi) - sh], [sl, len(lo) - sl]], alternative="greater")[1]
        mw = mannwhitneyu(hi[f"{e}_slope_change_sd"], lo[f"{e}_slope_change_sd"], alternative="greater").pvalue
        print(f"family 9, {e:<6}: significant up high {sh}/{len(hi)} vs low {sl}/{len(lo)} (Fisher p={fp:.3f}); "
              f"median slope change in pre-SD {hi[f'{e}_slope_change_sd'].median():+.2f} vs "
              f"{lo[f'{e}_slope_change_sd'].median():+.2f} (Mann-Whitney p={mw:.3f})")
    print(f"Wrote -> {args.out}")


if __name__ == "__main__":
    main()
