"""#14 — topic control with Stack Exchange tags (topics defined by the community, not by us).

Every answer inherits the tags of its question (e.g. ``<regression><bayesian>``). For each
quarter, using the same answer sample and cached whole-text vectors as families 5 and 13:

* ``within_tag_cosine``  — mean cosine over answer pairs whose questions share at least one tag;
* ``between_tag_cosine`` — mean cosine over pairs that share no tag;
* ``p_shared``           — share of answer pairs that share a tag (rises if topics narrow);
* ``eff_tags_r``         — effective number of tags (exp entropy, each answer's tags weighted
  1/#tags) on fixed 100-answer subsamples, so quarters with fewer answers are not penalised;
* ``tag_jsd_r``          — Jensen-Shannon divergence of that tag mix from the pooled pre-ChatGPT
  mix, same subsampling;
* ``within_tag_cosine_lc`` — within-tag cosine on the opening window (first 120 model tokens).

A rise in ``within_tag_cosine`` = answers on the same subject converging (style/wording); a
drop in ``eff_tags_r`` / rise in ``tag_jsd_r`` = the subject mix narrowing or shifting.

    python src/tag_topics.py -i data/processed/economics_answers.parquet --corpus Economics \
        --out-dir artifacts/se-hcl/economics
    python src/tag_topics.py --all          # every SE site with a questions file + summary
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon

from embed_cache import cached_embed, load_cache, save_cache
from paths import CORPORA, answers_parquet, questions_parquet, source_dir, summary_dir
from semantic_bert import embedding_setup, embed_texts, load_model
from significance import _q_ord, analyze_metric
from topic_decomposition import RARE_DRAWS, RARE_SIZE, sample_quarters

CHATGPT_QUARTER = "2022Q4"
SIG_METRICS = ("overall_cosine", "within_tag_cosine", "between_tag_cosine", "p_shared",
               "eff_tags_r", "tag_jsd_r", "within_tag_cosine_lc")
_TAG = re.compile(r"<([^>]+)>")


def parse_tags(s: str) -> list[str]:
    return _TAG.findall(s or "")


def _pair_means(V: np.ndarray, shared: np.ndarray) -> tuple[float, float, float, float]:
    S = V @ V.T
    iu = np.triu_indices(len(V), 1)
    s, sh = S[iu], shared[iu]
    within = float(s[sh].mean()) if sh.any() else float("nan")
    between = float(s[~sh].mean()) if (~sh).any() else float("nan")
    return float(s.mean()), within, between, float(sh.mean())


def _tag_dist(tag_lists: list[list[str]], vocab: dict[str, int]) -> np.ndarray:
    p = np.zeros(len(vocab))
    for tags in tag_lists:
        for t in tags:
            p[vocab[t]] += 1.0 / len(tags)
    return p / p.sum()


def compute(df: pd.DataFrame, questions: pd.DataFrame, model, emb, raw_cache, lc_cache,
            sample: int = 800, min_answers: int = 30, seed: int = 42) -> pd.DataFrame:
    tags_of = dict(zip(questions["id"], questions["tags"].map(parse_tags)))
    ids, texts, quarters = sample_quarters(df, sample, min_answers, seed)
    parent = dict(zip(df["id"], df["parent_id"]))
    tag_lists = [tags_of.get(parent.get(i), []) for i in ids]
    keep = np.array([len(t) > 0 for t in tag_lists])
    print(f"Sampled {len(ids):,} answers; {keep.mean():.1%} have question tags")
    V = cached_embed(model, ids, texts, emb.embed, raw_cache)

    vocab = {t: k for k, t in enumerate(sorted({t for tl in tag_lists for t in tl}))}
    pre = np.array([_q_ord(q) < _q_ord(CHATGPT_QUARTER) for q in quarters]) & keep
    base = _tag_dist([tag_lists[i] for i in np.where(pre)[0]], vocab)
    rng = np.random.default_rng(seed)

    lc_pairs = emb.lc(ids, texts)
    lc_vec = {}
    if lc_pairs:
        lv = cached_embed(model, [i for i, _ in lc_pairs], [t for _, t in lc_pairs],
                          embed_texts, lc_cache)
        lc_vec = dict(zip((i for i, _ in lc_pairs), lv))

    rows = []
    for q in sorted(set(quarters)):
        idx = np.where((quarters == q) & keep)[0]
        if len(idx) < 2:
            continue
        tl = [set(tag_lists[i]) for i in idx]
        shared = np.array([[bool(a & b) for b in tl] for a in tl])
        overall, within, between, p_sh = _pair_means(V[idx], shared)
        rec = {"quarter": q, "n_sample": len(idx), "overall_cosine": overall,
               "within_tag_cosine": within, "between_tag_cosine": between, "p_shared": p_sh}
        if len(idx) >= RARE_SIZE:
            effs, jsds = [], []
            for _ in range(RARE_DRAWS):
                sub = rng.choice(idx, size=RARE_SIZE, replace=False)
                p = _tag_dist([tag_lists[i] for i in sub], vocab)
                nz = p[p > 0]
                effs.append(float(np.exp(-(nz * np.log(nz)).sum())))
                jsds.append(float(jensenshannon(p, base, base=2) ** 2))
            rec["eff_tags_r"], rec["tag_jsd_r"] = float(np.mean(effs)), float(np.mean(jsds))
        else:
            rec["eff_tags_r"] = rec["tag_jsd_r"] = float("nan")
        li = [k for k, i in enumerate(idx) if ids[i] in lc_vec]
        if len(li) >= 2:
            L = np.vstack([lc_vec[ids[idx[k]]] for k in li])
            rec["within_tag_cosine_lc"] = _pair_means(L, shared[np.ix_(li, li)])[1]
        else:
            rec["within_tag_cosine_lc"] = float("nan")
        rows.append(rec)
    return pd.DataFrame(rows)


def significance(res: pd.DataFrame, corpus: str) -> pd.DataFrame:
    d = res.copy()
    d["_t"] = d["quarter"].map(_q_ord)
    out = []
    for m in SIG_METRICS:
        if d[m].notna().sum() < 8:
            continue
        row, _ = analyze_metric(d.dropna(subset=[m]), m, _q_ord(CHATGPT_QUARTER), 4)
        out.append({"corpus": corpus, **row})
    return pd.DataFrame(out)


def plot(res: pd.DataFrame, sig: pd.DataFrame, output: Path, corpus: str) -> None:
    q = res["quarter"].tolist()
    x = np.arange(len(q))
    mx = q.index(CHATGPT_QUARTER) if CHATGPT_QUARTER in q else None
    s = sig.set_index("metric")

    def lab(name, m):
        if m not in s.index:
            return name
        r = s.loc[m]
        return f"{name} (slope change {r['slope_change']:+.4f}/qtr, p={r['slope_change_p']:.2g})"

    fig, axes = plt.subplots(3, 1, figsize=(13, 12), sharex=True)
    ax = axes[0]
    for m, name, c in (("within_tag_cosine", "pairs sharing a tag", "tab:blue"),
                       ("overall_cosine", "all answer pairs", "black")):
        ax.plot(x, res[m], marker="o", ms=2.5, color=c, label=lab(name, m))
    ax.set_ylabel("mean pairwise cosine similarity", fontsize=9)
    ax.set_title("A. Do answers on the same subject (shared question tag) become more alike?",
                 fontsize=10, color="dimgray", loc="left")
    ax.legend(fontsize=8, loc="best")
    ax = axes[1]
    ax.plot(x, res["eff_tags_r"], marker="o", ms=3, color="tab:green",
            label=lab(f"effective number of tags ({RARE_SIZE}-answer samples)", "eff_tags_r"))
    ax.set_ylabel("effective # of tags\n(lower = fewer subjects)", fontsize=9)
    ax.set_title("B. How many subjects are in play?", fontsize=10, color="dimgray", loc="left")
    ax.legend(fontsize=8, loc="best")
    ax = axes[2]
    ax.plot(x, res["tag_jsd_r"], marker="o", ms=3, color="tab:purple",
            label=lab("JSD from the pre-ChatGPT tag mix", "tag_jsd_r"))
    ax.set_ylabel("Jensen-Shannon divergence\n(0 = same mix as before)", fontsize=9)
    ax.set_title("C. Which subjects? How far this quarter's tag mix is from the usual "
                 "pre-ChatGPT mix", fontsize=10, color="dimgray", loc="left")
    ax.legend(fontsize=8, loc="best")
    for ax in axes:
        ax.grid(True, alpha=0.3)
        if mx is not None:
            ax.axvline(mx, color="black", linestyle="--", alpha=0.7)
    axes[-1].set_xticks(x[::4])
    axes[-1].set_xticklabels(q[::4], rotation=90, fontsize=7)
    foot = ("Each answer inherits its question's Stack Exchange tags (chosen by the asker). Same "
            "answer sample as families 5 and 13. B and C: random 100-answer subsamples (mean of 50); "
            "an answer with k tags counts 1/k towards each. Pre-ChatGPT mix = tag shares over all "
            "sampled answers before 2022Q4, pooled. JSD 0 = identical mix, 1 = no tag in common.")
    fig.text(0.5, 0.005, foot, ha="center", va="bottom", fontsize=8, color="dimgray", wrap=True)
    fig.suptitle(f"{corpus} \u2014 topic control with Stack Exchange tags (family 14)", fontsize=13)
    fig.tight_layout(rect=(0, 0.05, 1, 0.97))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    plt.close(fig)


def run_one(inp: Path, qpath: Path, corpus: str, out_dir: Path, model, emb_dir: Path) -> pd.DataFrame:
    questions = pd.read_parquet(qpath, columns=["id", "tags"])
    df = pd.read_parquet(inp, columns=["id", "parent_id", "quarter", "text"])
    emb = embedding_setup(model, "whole", emb_dir, inp.stem)
    raw_cache, lc_cache = load_cache(emb.raw_path), load_cache(emb.lc_path)
    res = compute(df, questions, model, emb, raw_cache, lc_cache)
    save_cache(emb.raw_path, raw_cache)
    save_cache(emb.lc_path, lc_cache)
    sig = significance(res, corpus)
    out_dir.mkdir(parents=True, exist_ok=True)
    res.to_csv(out_dir / "14_tag_topics.csv", index=False)
    sig.to_csv(out_dir / "14_tag_significance.csv", index=False)
    plot(res, sig, out_dir / "14_tag_topics.png", corpus)
    print(f"{corpus}: {len(res)} quarters -> {out_dir}")
    return sig


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-i", "--input", type=Path)
    ap.add_argument("-q", "--questions", type=Path, help="questions parquet (default: derived)")
    ap.add_argument("--corpus")
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--all", action="store_true", help="all SE sites with a questions file")
    ap.add_argument("--only", nargs="*", default=None, help="--all: restrict to these folders")
    ap.add_argument("--processed", type=Path, default=Path("data/processed"))
    ap.add_argument("--cache-dir", type=Path, default=Path("data/models"))
    ap.add_argument("--emb-cache-dir", type=Path, default=Path("data/embeddings"))
    ap.add_argument("--replot", action="store_true",
                    help="--all: only redraw plots from existing CSVs")
    args = ap.parse_args()

    if args.replot:
        for folder, label, _ in CORPORA:
            d = source_dir(folder)
            if (d / "14_tag_topics.csv").exists():
                plot(pd.read_csv(d / "14_tag_topics.csv"),
                     pd.read_csv(d / "14_tag_significance.csv"), d / "14_tag_topics.png", label)
        print("replotted")
        return

    model = load_model(args.cache_dir)
    if not args.all:
        qpath = args.questions or args.input.parent / args.input.name.replace("answers", "questions")
        run_one(args.input, qpath, args.corpus, args.out_dir, model, args.emb_cache_dir)
        return
    sigs = []
    for folder, label, cog in CORPORA:
        if args.only and folder not in args.only:
            continue
        qpath = questions_parquet(folder, args.processed)
        if not qpath.exists():
            print(f"  skip {label}: no questions file")
            continue
        sig = run_one(answers_parquet(folder, args.processed), qpath, label, source_dir(folder),
                      model, args.emb_cache_dir)
        sigs.append(sig.assign(cog_load=cog))
    out = pd.concat(sigs, ignore_index=True)
    summary_dir().mkdir(parents=True, exist_ok=True)
    out.to_csv(summary_dir() / "14_tag_topics_all.csv", index=False)
    print(f"Wrote -> {summary_dir() / '14_tag_topics_all.csv'}")


if __name__ == "__main__":
    main()
