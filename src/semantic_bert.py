"""Semantic homogenization via TRUE contextual embeddings (Sentence-BERT / MiniLM).

This is the order-sensitive counterpart to ``semantic.py`` (which uses bag-of-words
LSA). It embeds each answer with ``all-MiniLM-L6-v2`` running under ONNX Runtime
(via ``fastembed`` — no PyTorch, so it installs cleanly on Windows), then reuses the
same ``spread_metrics`` (pairwise cosine, centroid variance, effective dimensionality)
so the numbers line up directly with the LSA run.

Model provisioning: HuggingFace is blocked by the corporate proxy, but the Qdrant
Google-Cloud-Storage mirror is reachable, so we pull the ONNX tarball from there and
load it via ``specific_model_path`` (bypassing fastembed's HF lookup). The model is
cached under ``data/models/`` (gitignored).

Report RELATIVE change over time: absolute embedding cosines are inflated by
anisotropy/hubness, so the trend and the raw-vs-length-controlled gap are what matter.

Output: ``artifacts/semantic_bert_metrics.csv`` and ``artifacts/semantic_bert_trends.png``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from metrics import tokenize
from semantic import spread_metrics, bootstrap_pairwise_samples
from embed_cache import load_cache, save_cache, cached_embed
from chunk_embed import DEFAULT_BUDGET, clean_text, counting_tokenizer, embed_documents, opening_window

CHATGPT_QUARTER = "2022Q4"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
GCS_URL = (
    "https://storage.googleapis.com/qdrant-fastembed/"
    "sentence-transformers-all-MiniLM-L6-v2.tar.gz"
)


def load_model(cache_dir: Path, model_name: str = MODEL_NAME, url: str = GCS_URL):
    """Provision the ONNX model from the GCS mirror (cached) and return an embedder."""
    from fastembed import TextEmbedding
    from fastembed.text.onnx_embedding import OnnxTextEmbedding

    cache_dir.mkdir(parents=True, exist_ok=True)
    model_dir = OnnxTextEmbedding.retrieve_model_gcs(
        model_name, url, str(cache_dir), deprecated_tar_struct=True
    )
    return TextEmbedding(model_name, specific_model_path=str(model_dir))


def embed_texts(model, texts: list[str], batch_size: int = 256) -> np.ndarray:
    """Embed and L2-normalize a list of texts into a (n, dim) array."""
    vecs = np.asarray(list(model.embed(texts, batch_size=batch_size)), dtype=np.float64)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


EMBED_MODES = ("legacy", "whole")


@dataclass
class Embedding:
    """How texts become vectors, plus the matching length-controlled variant and cache files.

    legacy: the original results — the model silently truncates at 128 tokens; the length control
            is the first ``lc_window`` words.
    whole:  machine strings stripped, whole text sentence-chunked and averaged (chunk_embed); the
            length control is exactly the first 120 model tokens (texts shorter are excluded).
    """
    mode: str
    embed: Callable                 # (model, texts) -> (n, d) L2-normalised
    lc: Callable                    # (ids, texts) -> [(id, lc_text)]
    raw_path: Path
    lc_path: Path
    raw_label: str
    lc_label: str
    ntok: Callable | None = None    # texts -> model-token counts after cleaning (whole only)


def legacy_lc(ids, texts, lc_window: int = 100) -> list[tuple[int, str]]:
    out = []
    for i, t in zip(ids, texts):
        tk = tokenize(t)
        if len(tk) >= lc_window:
            out.append((i, " ".join(tk[:lc_window])))
    return out


def embedding_setup(model, mode: str, emb_dir: Path, stem: str, lc_window: int = 100) -> Embedding:
    if mode == "legacy":
        return Embedding(mode, embed_texts, lambda ids, texts: legacy_lc(ids, texts, lc_window),
                         emb_dir / f"{stem}_minilm_raw.npz",
                         emb_dir / f"{stem}_minilm_lc{lc_window}.npz",
                         "raw", f"length-controlled (first {lc_window} tokens)")
    if mode != "whole":
        raise ValueError(f"unknown embedding mode {mode!r}")
    tok = counting_tokenizer(model)

    def embed(m, texts):
        return embed_documents(m, texts, embed_texts, tok=tok)

    def lc(ids, texts):
        return [(i, w) for i, t in zip(ids, texts) if (w := opening_window(tok, t)) is not None]

    def ntok(texts):
        return [len(e.ids) for e in tok.encode_batch([clean_text(tok, t) for t in texts],
                                                     add_special_tokens=False)]

    return Embedding(mode, embed, lc, emb_dir / f"{stem}_minilm_whole.npz",
                     emb_dir / f"{stem}_minilm_open{DEFAULT_BUDGET}.npz",
                     "whole text", f"opening window (first {DEFAULT_BUDGET} model tokens)", ntok)


def bootstrap_pairwise_ci(v: np.ndarray, n_boot: int, ci: float, rng) -> tuple[float, float]:
    """Percentile-bootstrap CI for mean pairwise cosine (see semantic.bootstrap_pairwise_samples)."""
    pc = bootstrap_pairwise_samples(v, n_boot, rng)
    if pc is None:
        return float("nan"), float("nan")
    alpha = 1.0 - ci
    return (float(np.nanpercentile(pc, 100 * alpha / 2)),
            float(np.nanpercentile(pc, 100 * (1 - alpha / 2))))


def compute_quarterly(df: pd.DataFrame, model, sample: int = 800, lc_window: int = 100,
                      min_answers: int = 30, seed: int = 42, n_boot: int = 0,
                      ci: float = 0.95, raw_cache: dict | None = None,
                      lc_cache: dict | None = None, emb: Embedding | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    records: list[dict] = []
    embed_fn = emb.embed if emb else embed_texts
    lc_fn = emb.lc if emb else (lambda i, t: legacy_lc(i, t, lc_window))

    for quarter, group in tqdm(sorted(df.groupby("quarter")), desc="Quarters"):
        volume = len(group)
        if volume < min_answers:
            continue
        if volume > sample:
            group = group.iloc[rng.choice(volume, size=sample, replace=False)]

        ids = group["id"].tolist()
        texts = group["text"].tolist()
        raw_emb = cached_embed(model, ids, texts, embed_fn, raw_cache)
        raw = spread_metrics(raw_emb)

        lc_data = lc_fn(ids, texts)
        if len(lc_data) >= 2:
            lc_ids = [i for i, _ in lc_data]
            lc_emb = cached_embed(model, lc_ids, [t for _, t in lc_data], embed_texts, lc_cache)
            lc = spread_metrics(lc_emb)
        else:
            lc_emb = None
            lc = {"pairwise_cosine": float("nan"), "centroid_variance": float("nan"),
                  "eff_dim": float("nan")}

        rec = {"quarter": quarter, "volume": volume, "n_sample": len(group),
               "n_lc": len(lc_data)}
        if emb and emb.ntok:
            ntok = np.array(emb.ntok(texts))
            rec["mean_tokens"] = float(ntok.mean())
            rec["mean_chunks"] = float(np.ceil(ntok / DEFAULT_BUDGET).clip(min=1).mean())
        rec.update({f"sem_{k}": v for k, v in raw.items()})
        rec.update({f"lc_sem_{k}": v for k, v in lc.items()})
        if n_boot:
            lo, hi = bootstrap_pairwise_ci(raw_emb, n_boot, ci, rng)
            rec["sem_pairwise_cosine_lo"], rec["sem_pairwise_cosine_hi"] = lo, hi
            llo, lhi = (bootstrap_pairwise_ci(lc_emb, n_boot, ci, rng)
                        if lc_emb is not None else (float("nan"), float("nan")))
            rec["lc_sem_pairwise_cosine_lo"], rec["lc_sem_pairwise_cosine_hi"] = llo, lhi
        records.append(rec)

    return pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)


def plot_metrics(df: pd.DataFrame, output: Path, corpus: str = "Cross Validated",
                 emb: Embedding | None = None) -> None:
    quarters = df["quarter"].tolist()
    x = list(range(len(quarters)))
    marker_x = quarters.index(CHATGPT_QUARTER) if CHATGPT_QUARTER in quarters else None
    raw_label = emb.raw_label if emb else "raw"
    lc_label = emb.lc_label if emb else "length-controlled (100 tok)"

    panels = [
        ("sem_pairwise_cosine", "lc_sem_pairwise_cosine",
         "Semantic pairwise cosine\n(higher = homogeneous)", "tab:red", "tab:orange"),
        ("sem_centroid_variance", "lc_sem_centroid_variance",
         "Semantic centroid variance\n(lower = homogeneous)", "tab:blue", "tab:cyan"),
        ("sem_eff_dim", "lc_sem_eff_dim",
         "Effective dimensionality\n(higher = spread)", "tab:green", "tab:olive"),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)
    for ax, (raw, lc, label, c_raw, c_lc) in zip(axes, panels):
        ax.plot(x, df[raw], marker="o", ms=3, color=c_raw, label=raw_label)
        ax.plot(x, df[lc], marker="o", ms=3, color=c_lc, label=lc_label)
        if f"{raw}_lo" in df.columns:
            ax.fill_between(x, df[f"{raw}_lo"], df[f"{raw}_hi"], color=c_raw, alpha=0.2)
        if f"{lc}_lo" in df.columns:
            ax.fill_between(x, df[f"{lc}_lo"], df[f"{lc}_hi"], color=c_lc, alpha=0.2)
        ax.set_ylabel(label, fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, loc="best")
        if marker_x is not None:
            ax.axvline(marker_x, color="black", linestyle="--", alpha=0.7)
    if marker_x is not None:
        axes[0].text(marker_x, axes[0].get_ylim()[1], " ChatGPT (2022Q4)", va="top", fontsize=8)

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(quarters, rotation=90, fontsize=6)
    axes[-1].set_xlabel("Quarter")
    ci_note = "  (shaded = bootstrap CI)" if "sem_pairwise_cosine_lo" in df.columns else ""
    fig.suptitle(f"{corpus} \u2014 Are answers becoming more alike in meaning? "
                 f"(Sentence-BERT / MiniLM){ci_note}", fontsize=13)
    if "n_sample" in df.columns:
        n_max, n_med = int(df["n_sample"].max()), int(df["n_sample"].median())
        if emb and emb.mode == "whole":
            how = ("Whole text: URLs/machine strings removed, split into sentence chunks of "
                   f"<= {DEFAULT_BUDGET} tokens, chunk vectors averaged. 'Opening window' embeds "
                   f"exactly the first {DEFAULT_BUDGET} model tokens of each answer "
                   "(shorter answers excluded), to rule out a length artifact.")
        else:
            how = ("'Length-controlled' truncates each answer to its "
                   "first 100 tokens before embedding, to rule out a length artifact.")
        foot = (f"Each quarter: pairwise cosine over a random sample of up to {n_max} answers "
                f"(median {n_med}/quarter). " + how)
        fig.text(0.5, -0.01, foot, ha="center", va="top", fontsize=8, color="dimgray", wrap=True)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    print(f"Saved figure -> {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Semantic homogenization metrics (Sentence-BERT)")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("-o", "--output", type=Path, default=Path("artifacts/semantic_bert_metrics.csv"))
    ap.add_argument("--plot", type=Path, default=Path("artifacts/semantic_bert_trends.png"))
    ap.add_argument("--cache-dir", type=Path, default=Path("data/models"))
    ap.add_argument("--sample", type=int, default=800)
    ap.add_argument("--lc-window", type=int, default=100)
    ap.add_argument("--bootstrap", type=int, default=1000,
                    help="Bootstrap resamples for the pairwise-cosine CI (0 = off)")
    ap.add_argument("--ci", type=float, default=0.95, help="Confidence level for the CI")
    ap.add_argument("--emb-cache-dir", type=Path, default=Path("data/embeddings"),
                    help="Folder for the persistent id-keyed embedding cache")
    ap.add_argument("--no-emb-cache", action="store_true", help="Bypass the embedding cache")
    ap.add_argument("--corpus", default="Cross Validated")
    ap.add_argument("--embed", choices=EMBED_MODES, default="legacy",
                    help="legacy = original 128-token-truncated results; whole = whole-text chunked")
    args = ap.parse_args()

    model = load_model(args.cache_dir)
    df = pd.read_parquet(args.input)
    emb = embedding_setup(model, args.embed, args.emb_cache_dir, args.input.stem, args.lc_window)

    if args.no_emb_cache:
        raw_cache = lc_cache = None
    else:
        raw_path, lc_path = emb.raw_path, emb.lc_path
        raw_cache, lc_cache = load_cache(raw_path), load_cache(lc_path)

    result = compute_quarterly(df, model, sample=args.sample, lc_window=args.lc_window,
                               n_boot=args.bootstrap, ci=args.ci,
                               raw_cache=raw_cache, lc_cache=lc_cache, emb=emb)

    if not args.no_emb_cache:
        save_cache(raw_path, raw_cache)
        save_cache(lc_path, lc_cache)
        print(f"Embedding cache -> {args.emb_cache_dir} "
              f"({len(raw_cache):,} raw / {len(lc_cache):,} lc vectors)")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"Wrote {len(result)} quarters -> {args.output}")
    print(result.to_string(index=False))
    plot_metrics(result, args.plot, corpus=args.corpus, emb=emb)


if __name__ == "__main__":
    main()
