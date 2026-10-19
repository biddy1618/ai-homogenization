"""Semantic homogenization via TRUE contextual embeddings (Sentence-BERT / MiniLM).

This is the order-sensitive counterpart to ``semantic.py`` (which uses bag-of-words
LSA). It embeds each answer with ``all-MiniLM-L6-v2`` running under ONNX Runtime
(via ``fastembed`` — no PyTorch, so it installs cleanly on Windows), then reuses the
same ``spread_metrics`` (pairwise cosine, centroid variance, effective dimensionality)
so the numbers line up directly with the LSA run.

Model provisioning: the exact ONNX files the study has always used (originally the Qdrant GCS
tarball, which now returns 403) are published as a GitHub release asset. ``load_model`` downloads
them once into ``data/models/`` (gitignored), verifies their SHA256, and loads them via
``specific_model_path`` (bypassing fastembed's HuggingFace lookup).

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
MODEL_DIR = "fast-all-MiniLM-L6-v2"
_RELEASES = "https://github.com/biddy1618/ai-homogenization/releases/download/"
# Encoders, each a pinned copy on a GitHub release with SHA-256 checks so vectors are reproducible.
# Chunking is identical for all encoders (120-token chunks, 120-token opening window).
#   minilm:    byte-identical copy of the Qdrant GCS tarball the study used (that URL now returns 403)
#   bge-small: Hugging Face qdrant/bge-small-en-v1.5-onnx-q @ aa8f8b06 (BAAI/bge-small-en-v1.5, MIT)
ENCODERS = {
    "minilm": {
        "name": MODEL_NAME, "dir": MODEL_DIR, "file": "model.onnx",
        "url": _RELEASES + "minilm-v1/fast-all-MiniLM-L6-v2.zip",
        "sha256": {
            "model.onnx": "bbd7b466f6d58e646fdc2bd5fd67b2f5e93c0b687011bd4548c420f7bd46f0c5",
            "tokenizer.json": "da0e79933b9ed51798a3ae27893d3c5fa4a201126cef75586296df9b4d2c62a0",
        },
    },
    "bge-small": {
        "name": "BAAI/bge-small-en-v1.5", "dir": "bge-small-en-v1.5-onnx-q",
        "file": "model_optimized.onnx",
        "url": _RELEASES + "bge-small-v1/bge-small-en-v1.5-onnx-q.zip",
        "sha256": {
            "model_optimized.onnx": "51f1bd0addd6e859e42c2c8021a5e5461385bb676a649f4b269aa445449f2431",
            "tokenizer.json": "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66",
        },
    },
}
MODEL_URL = ENCODERS["minilm"]["url"]
MODEL_SHA256 = ENCODERS["minilm"]["sha256"]
ENCODER_LABEL = {"minilm": "Sentence-BERT / MiniLM", "bge-small": "BGE-small-en-v1.5"}


def load_model(cache_dir: Path, encoder: str = "minilm"):
    """Download (once) and verify the pinned ONNX files for ``encoder``, then return an embedder.

    ``minilm`` is the study's encoder; ``bge-small`` is the robustness encoder."""
    import hashlib
    import io
    import urllib.request
    import zipfile

    from fastembed import TextEmbedding

    spec = ENCODERS[encoder]
    model_dir = cache_dir / spec["dir"]
    if not (model_dir / spec["file"]).exists():
        model_dir.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(spec["url"], timeout=300) as r, \
                zipfile.ZipFile(io.BytesIO(r.read())) as z:
            for info in z.infolist():
                # Base name only: release zips may use Windows '\' separators.
                name = info.filename.replace("\\", "/").rsplit("/", 1)[-1]
                if name and not name.startswith("._"):
                    (model_dir / name).write_bytes(z.read(info))
    for name, want in spec["sha256"].items():
        got = hashlib.sha256((model_dir / name).read_bytes()).hexdigest()
        if got != want:
            raise RuntimeError(f"{model_dir / name}: sha256 {got} != expected {want}")
    return TextEmbedding(spec["name"], specific_model_path=str(model_dir))


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


def embedding_setup(model, mode: str, emb_dir: Path, stem: str, lc_window: int = 100,
                    max_chunks: int | None = None, encoder: str = "minilm") -> Embedding:
    tag = encoder.split("-")[0]  # cache-name tag: "minilm" (unchanged names) or "bge"
    if mode == "legacy":
        if encoder != "minilm":
            raise ValueError("legacy mode is MiniLM-only (it reproduces the delivered results)")
        return Embedding(mode, embed_texts, lambda ids, texts: legacy_lc(ids, texts, lc_window),
                         emb_dir / f"{stem}_minilm_raw.npz",
                         emb_dir / f"{stem}_minilm_lc{lc_window}.npz",
                         "raw", f"length-controlled (first {lc_window} tokens)")
    if mode != "whole":
        raise ValueError(f"unknown embedding mode {mode!r}")
    tok = counting_tokenizer(model)

    def embed(m, texts):
        return embed_documents(m, texts, embed_texts, tok=tok, max_chunks=max_chunks)

    def lc(ids, texts):
        return [(i, w) for i, t in zip(ids, texts) if (w := opening_window(tok, t)) is not None]

    def ntok(texts):
        return [len(e.ids) for e in tok.encode_batch([clean_text(tok, t) for t in texts],
                                                     add_special_tokens=False)]

    k = f"_k{max_chunks}" if max_chunks else ""
    raw_label = f"whole text (first <= {max_chunks} chunks)" if max_chunks else "whole text"
    return Embedding(mode, embed, lc, emb_dir / f"{stem}_{tag}_whole{k}.npz",
                     emb_dir / f"{stem}_{tag}_open{DEFAULT_BUDGET}.npz",
                     raw_label, f"opening window (first {DEFAULT_BUDGET} model tokens)", ntok)


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
                 emb: Embedding | None = None, encoder: str = "minilm",
                 show_lc: bool = False) -> None:
    """Family-5 plot. The opening-window / length-controlled line (``lc_*`` columns) is shown
    only with ``show_lc``; it agrees with whole text and is reported once, in family 8."""
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
        if show_lc:
            ax.plot(x, df[lc], marker="o", ms=3, color=c_lc, label=lc_label)
        if f"{raw}_lo" in df.columns:
            ax.fill_between(x, df[f"{raw}_lo"], df[f"{raw}_hi"], color=c_raw, alpha=0.2)
        if show_lc and f"{lc}_lo" in df.columns:
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
                 f"({ENCODER_LABEL[encoder]}){ci_note}", fontsize=13)
    if "n_sample" in df.columns:
        n_max, n_med = int(df["n_sample"].max()), int(df["n_sample"].median())
        if emb and emb.mode == "whole":
            how = ("Whole text: URLs/machine strings removed, split into sentence chunks of "
                   f"<= {DEFAULT_BUDGET} tokens, chunk vectors averaged.")
            if show_lc:
                how += (f" 'Opening window' embeds exactly the first {DEFAULT_BUDGET} model tokens "
                        "of each answer (shorter answers excluded), to rule out a length artifact.")
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
    ap.add_argument("--max-chunks", type=int, default=None,
                    help="whole mode: keep only each text's first K chunks (length-bias check)")
    ap.add_argument("--encoder", choices=sorted(ENCODERS), default="minilm",
                    help="sentence encoder; bge-small is the robustness check (whole mode only)")
    args = ap.parse_args()

    model = load_model(args.cache_dir, args.encoder)
    df = pd.read_parquet(args.input)
    emb = embedding_setup(model, args.embed, args.emb_cache_dir, args.input.stem, args.lc_window,
                          args.max_chunks, args.encoder)

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
    plot_metrics(result, args.plot, corpus=args.corpus, emb=emb, encoder=args.encoder)


if __name__ == "__main__":
    main()
