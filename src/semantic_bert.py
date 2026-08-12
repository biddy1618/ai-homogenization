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
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from metrics import tokenize
from semantic import spread_metrics

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


def compute_quarterly(df: pd.DataFrame, model, sample: int = 800, lc_window: int = 100,
                      min_answers: int = 30, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    records: list[dict] = []

    for quarter, group in tqdm(sorted(df.groupby("quarter")), desc="Quarters"):
        volume = len(group)
        if volume < min_answers:
            continue
        if volume > sample:
            group = group.iloc[rng.choice(volume, size=sample, replace=False)]

        texts = group["text"].tolist()
        raw = spread_metrics(embed_texts(model, texts))

        tokenized = [tokenize(t) for t in texts]
        lc_texts = [" ".join(tk[:lc_window]) for tk in tokenized if len(tk) >= lc_window]
        if len(lc_texts) >= 2:
            lc = spread_metrics(embed_texts(model, lc_texts))
        else:
            lc = {"pairwise_cosine": float("nan"), "centroid_variance": float("nan"),
                  "eff_dim": float("nan")}

        rec = {"quarter": quarter, "volume": volume, "n_sample": len(group),
               "n_lc": len(lc_texts)}
        rec.update({f"sem_{k}": v for k, v in raw.items()})
        rec.update({f"lc_sem_{k}": v for k, v in lc.items()})
        records.append(rec)

    return pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)


def plot_metrics(df: pd.DataFrame, output: Path, corpus: str = "Cross Validated") -> None:
    quarters = df["quarter"].tolist()
    x = list(range(len(quarters)))
    marker_x = quarters.index(CHATGPT_QUARTER) if CHATGPT_QUARTER in quarters else None

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
        ax.plot(x, df[raw], marker="o", ms=3, color=c_raw, label="raw")
        ax.plot(x, df[lc], marker="o", ms=3, color=c_lc, label="length-controlled (100 tok)")
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
    fig.suptitle(f"{corpus} — semantic homogenization (Sentence-BERT / MiniLM)", fontsize=13)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    print(f"Saved figure -> {output}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Semantic homogenization metrics (Sentence-BERT)")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("-o", "--output", type=Path, default=Path("artifacts/semantic_bert_metrics.csv"))
    ap.add_argument("--plot", type=Path, default=Path("artifacts/semantic_bert_trends.png"))
    ap.add_argument("--cache-dir", type=Path, default=Path("data/models"))
    ap.add_argument("--sample", type=int, default=800)
    ap.add_argument("--lc-window", type=int, default=100)
    ap.add_argument("--corpus", default="Cross Validated")
    args = ap.parse_args()

    model = load_model(args.cache_dir)
    df = pd.read_parquet(args.input)
    result = compute_quarterly(df, model, sample=args.sample, lc_window=args.lc_window)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"Wrote {len(result)} quarters -> {args.output}")
    print(result.to_string(index=False))
    plot_metrics(result, args.plot, corpus=args.corpus)


if __name__ == "__main__":
    main()
