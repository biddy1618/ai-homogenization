"""#12 - GPT anchor: do human answers move towards what GPT would write for the same question?

Pairwise families (5/11/13/14) ask whether humans write more like *each other*. This asks
whether they write more like *an AI* answering the same question, and whether that pull
strengthens after ChatGPT (2022Q4).

Design:
  1. Sample up to ``--per-quarter`` human answers per quarter (resolvable question, at least
     ``--min-tokens`` words), for every quarter, including years before ChatGPT existed: the
     fixed model is a ruler, and pre-2022 quarters show how GPT-like humans already were.
  2. For each sampled question, generate ``--samples`` answers with a fixed model (title + body
     as the prompt). Their whole-text vectors are averaged into one "typical GPT answer" (the
     anchor). Generations are cached in ``data/anchor/<input>__<model>.jsonl``.
  3. For each human answer h to question q in quarter t:
       match     = cos(h, anchor_q)
       same_tag  = mean cos(h, anchor_q') over up to 5 other sampled questions q' in quarter t
                   that share a Stack Exchange tag with q (subject held fixed)
       other     = mean cos(h, anchor_q') over all other sampled questions in quarter t
       pull      = match - same_tag   (GPT-likeness specific to the question, beyond subject)
  4. Per quarter averages; family-8 interrupted time series on ``pull`` and ``match``.

``gpt_draw_cosine`` = mean cosine between draws for the same question (how stable the anchor is).

API key: ``OPENAI_API_KEY`` or ``--api-key-file`` (default ``.secrets/openai_api_key.txt``); Azure
via ``AZURE_OPENAI_*``. Without a key the script analyses cached generations only.

Output: ``<out-dir>/data/12_anchor_drift.csv``, ``<out-dir>/data/12_anchor_significance.csv``,
``<out-dir>/12_anchor_drift.png``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from embed_cache import load_cache, save_cache, cached_embed
from paths import source_dir
from semantic_bert import CHATGPT_QUARTER, EMBED_MODES, embedding_setup, embed_texts, load_model
from significance import _q_ord, analyze_metric

SYSTEM_PROMPT = (
    "You are a knowledgeable user answering a question on the {site} Stack Exchange. "
    "Write a single, self-contained, helpful answer in your own words. "
    "Do not include greetings, sign-offs, or meta commentary."
)
SIG_METRICS = ("pull", "ai_match_cosine", "pull_any", "lc_pull", "lc_ai_match_cosine")
_TAG = re.compile(r"<([^>]+)>")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# --------------------------------------------------------------------------- sampling
def build_sample(answers: pd.DataFrame, questions: pd.DataFrame, per_quarter: int,
                 min_answers: int, min_tokens: int, seed: int) -> pd.DataFrame:
    """Sampled human answers joined to their question title, body and tags."""
    rng = np.random.default_rng(seed)
    qids = set(questions["id"].tolist())
    a = answers[(answers["parent_id"].isin(qids)) & (answers["token_count"] >= min_tokens)].copy()
    if a.empty:
        raise SystemExit("No answers with a resolvable question - check the questions parquet.")
    picks = []
    for _, g in a.groupby("quarter"):
        if len(g) < min_answers:
            continue
        picks.append(g if len(g) <= per_quarter
                     else g.iloc[rng.choice(len(g), per_quarter, replace=False)])
    sample = pd.concat(picks, ignore_index=True)
    q = questions.set_index("id")[["title", "text", "tags"]].rename(
        columns={"title": "q_title", "text": "q_body", "tags": "q_tags"})
    return sample.join(q, on="parent_id").reset_index(drop=True)


# --------------------------------------------------------------------------- generation
def get_client(model: str):
    """Return (client, kind, model_or_deployment) from env, or (None, reason, model).

    Azure is preferred when ``AZURE_OPENAI_ENDPOINT`` is set: API key if provided, else
    Azure AD (your ``az login``) via an auto-refreshing token provider — needed when key
    access is locked down but you hold the data-plane role.
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if endpoint:
        try:
            from openai import AzureOpenAI
        except ImportError:
            return None, "openai package not installed (pip install openai)", model
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", model)
        if os.getenv("AZURE_OPENAI_API_KEY"):
            client = AzureOpenAI(api_key=os.environ["AZURE_OPENAI_API_KEY"],
                                 azure_endpoint=endpoint, api_version=api_version)
            return client, "azure(key)", deployment
        try:
            from azure.identity import AzureCliCredential, get_bearer_token_provider
        except ImportError:
            return None, "azure-identity not installed (pip install azure-identity)", model
        provider = get_bearer_token_provider(
            AzureCliCredential(), "https://cognitiveservices.azure.com/.default")
        client = AzureOpenAI(azure_ad_token_provider=provider,
                             azure_endpoint=endpoint, api_version=api_version)
        return client, "azure(aad)", deployment
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
        except ImportError:
            return None, "openai package not installed (pip install openai)", model
        return OpenAI(), "openai", model
    return None, "no API key in env (set AZURE_OPENAI_ENDPOINT+az login, or OPENAI_API_KEY)", model


def generate_one(client, deployment: str, site: str, title: str, body: str,
                 max_tokens: int, temperature: float, body_char_cap: int) -> str:
    """Generate a single AI answer, with a few retries on transient errors."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(site=site)},
        {"role": "user", "content": f"{title}\n\n{body[:body_char_cap]}".strip()},
    ]
    for attempt in range(5):
        try:
            resp = client.chat.completions.create(
                model=deployment, messages=messages,
                max_tokens=max_tokens, temperature=temperature,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001 — surface after retries
            # Content-filter rejections are deterministic — cache an empty skip, don't retry.
            if getattr(exc, "code", None) == "content_filter" or "content_filter" in str(exc):
                return ""
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    return ""


def load_generations(path: Path) -> dict[int, dict[int, str]]:
    """qid -> {draw: text}. Lines without ``draw`` (older runs) count as draw 0."""
    gens: dict[int, dict[int, str]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                gens.setdefault(int(rec["qid"]), {})[int(rec.get("draw", 0))] = rec["text"]
    return gens


def append_generation(path: Path, qid: int, draw: int, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"qid": int(qid), "draw": int(draw), "text": text}) + "\n")


def _ai_key(qid: int, draw: int) -> int:
    """Embedding-cache id for a GPT draw (draw 0 keeps the qid, as in earlier runs)."""
    return int(qid) if draw == 0 else -(int(qid) * 16 + draw)


# --------------------------------------------------------------------------- metric
def _anchor_vectors(model, gens_ok, uq, embed_fn, cache, text_fn=None):
    """Per-question anchor (normalised mean of draw vectors) and mean draw-to-draw cosine.

    ``text_fn(keys, texts) -> [(key, text)]`` optionally maps each draw to another text (the
    opening window); draws it drops are left out. Questions without any draw get NaN rows."""
    keys, texts, owner = [], [], []
    for qi, q in enumerate(uq):
        for d, t in sorted(gens_ok[q].items()):
            keys.append(_ai_key(q, d)); texts.append(t); owner.append(qi)
    if text_fn is not None:
        kept = dict(text_fn(keys, texts))
        sel = [i for i, k in enumerate(keys) if k in kept]
        keys = [keys[i] for i in sel]; texts = [kept[keys_i] for keys_i in keys]
        owner = [owner[i] for i in sel]
    dv = cached_embed(model, keys, texts, embed_fn, cache)
    owner = np.array(owner)
    anchor = np.full((len(uq), dv.shape[1]), np.nan)
    sums = np.zeros_like(anchor)
    np.add.at(sums, owner, dv)
    has = np.bincount(owner, minlength=len(uq)) > 0
    anchor[has] = sums[has] / np.linalg.norm(sums[has], axis=1, keepdims=True)
    draw_cos = np.full(len(uq), np.nan)
    for qi in np.where(np.bincount(owner, minlength=len(uq)) >= 2)[0]:
        v = dv[owner == qi]
        s = v @ v.T
        draw_cos[qi] = (s.sum() - len(v)) / (len(v) * (len(v) - 1))
    return anchor, draw_cos


def _quarter_pull(Hq, A, answer_q, qs, tags, rng, n_baseline):
    """match / same-tag baseline / any-other baseline per answer (rows of Hq), NaN-safe."""
    S = Hq @ A.T
    col = {q: j for j, q in enumerate(qs)}
    valid = ~np.isnan(A).any(axis=1)
    match, same, other, fallback = [], [], [], 0
    for i, q in enumerate(answer_q):
        j = col[q]
        others = [k for k in range(len(qs)) if k != j and valid[k]]
        if not valid[j] or not others or np.isnan(Hq[i]).any():
            continue
        shared = [k for k in others if tags[qs[k]] & tags[q]]
        pool = shared if shared else others
        fallback += not shared
        pick = rng.choice(pool, size=min(n_baseline, len(pool)), replace=False)
        match.append(S[i, j]); same.append(S[i, pick].mean()); other.append(S[i, others].mean())
    return np.array(match), np.array(same), np.array(other), fallback


def compute_drift(sample: pd.DataFrame, gens: dict[int, dict[int, str]], model,
                  raw_cache, ai_cache, min_answers: int, seed: int, embed_fn,
                  lc_fn=None, lc_cache=None, ai_lc_cache=None,
                  n_baseline: int = 5) -> pd.DataFrame:
    """Whole-text match / baseline / pull per quarter; with ``lc_fn`` also the same on the
    opening window (first 120 model tokens of both the human and the GPT answer)."""
    rng = np.random.default_rng(seed)
    ok = {q: {d: t for d, t in ds.items() if t and t.strip()} for q, ds in gens.items()}
    ok = {q: ds for q, ds in ok.items() if ds}
    sample = sample[sample["parent_id"].isin(ok)].reset_index(drop=True)
    if sample.empty:
        raise SystemExit("No sampled answers have a cached GPT generation yet.")
    uq = sample["parent_id"].drop_duplicates().tolist()
    qrow = {q: i for i, q in enumerate(uq)}
    tags = {q: set(_TAG.findall(str(t))) for q, t in
            sample.drop_duplicates("parent_id").set_index("parent_id")["q_tags"].items()}

    print(f"Embedding GPT answers for {len(uq):,} questions (cache-backed)...")
    anchor, draw_cos = _anchor_vectors(model, ok, uq, embed_fn, ai_cache)
    print(f"Embedding {len(sample):,} human answers (cache-backed)...")
    H = cached_embed(model, sample["id"].tolist(), sample["text"].tolist(), embed_fn, raw_cache)

    if lc_fn is not None:
        print("Opening window: embedding first 120 tokens of human and GPT answers...")
        anchor_lc, _ = _anchor_vectors(model, ok, uq, embed_texts, ai_lc_cache, lc_fn)
        pairs = lc_fn(sample["id"].tolist(), sample["text"].tolist())
        H_lc = np.full_like(H, np.nan)
        if pairs:
            v = cached_embed(model, [i for i, _ in pairs], [t for _, t in pairs], embed_texts, lc_cache)
            pos = {int(i): r for r, i in enumerate(sample["id"])}
            H_lc[[pos[int(i)] for i, _ in pairs]] = v

    records = []
    for quarter, g in sorted(sample.groupby("quarter")):
        if len(g) < min_answers:
            continue
        qs = g["parent_id"].drop_duplicates().tolist()
        if len(qs) < 2:
            continue
        idx = g.index.to_numpy()
        A = anchor[[qrow[q] for q in qs]]
        m, s, o, fb = _quarter_pull(H[idx], A, g["parent_id"].tolist(), qs, tags, rng, n_baseline)
        dc = draw_cos[[qrow[q] for q in qs]]
        rec = {"quarter": quarter, "n_answers": int(len(g)), "n_questions": len(qs),
               "ai_match_cosine": float(m.mean()), "ai_same_tag_cosine": float(s.mean()),
               "ai_other_cosine": float(o.mean()), "pull": float((m - s).mean()),
               "pull_any": float((m - o).mean()), "baseline_fallback_share": fb / len(g),
               "gpt_draw_cosine": float(np.nanmean(dc)) if np.isfinite(dc).any() else float("nan")}
        if lc_fn is not None:
            ml, sl, _, _ = _quarter_pull(H_lc[idx], anchor_lc[[qrow[q] for q in qs]],
                                         g["parent_id"].tolist(), qs, tags, rng, n_baseline)
            rec.update({"n_lc": int(len(ml)),
                        "lc_ai_match_cosine": float(ml.mean()) if len(ml) else float("nan"),
                        "lc_pull": float((ml - sl).mean()) if len(ml) else float("nan")})
        records.append(rec)
    return pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)


def significance(result: pd.DataFrame, corpus: str, break_quarter: str, hac_lags: int) -> pd.DataFrame:
    d = result.copy()
    d["_t"] = d["quarter"].map(_q_ord)
    rows = []
    for m in SIG_METRICS:
        if m not in d or d[m].notna().sum() < 8:
            continue
        row, _ = analyze_metric(d.dropna(subset=[m]), m, _q_ord(break_quarter), hac_lags)
        rows.append({"corpus": corpus, **row})
    return pd.DataFrame(rows)


def plot_drift(df: pd.DataFrame, sig: pd.DataFrame, output: Path, corpus: str,
               footnote: str = "") -> None:
    d = df.copy()
    d["_t"] = d["quarter"].map(_q_ord)
    d = d.sort_values("_t")
    t_break = _q_ord(CHATGPT_QUARTER)
    s = sig.set_index("metric")

    def lab(name, m):
        if m not in s.index:
            return name
        return f"{name}  (slope change {s.loc[m, 'slope_change']:+.4f}/qtr, p={s.loc[m, 'slope_change_p']:.2g})"

    fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
    ax = axes[0]
    ax.plot(d["_t"], d["ai_match_cosine"], color="tab:blue", lw=2, marker="o", ms=3,
            label=lab("GPT's answer to the SAME question", "ai_match_cosine"))
    ax.plot(d["_t"], d["ai_same_tag_cosine"], color="tab:orange", lw=1.5, marker="o", ms=3,
            label="GPT's answers to OTHER questions with the same tag (same quarter)")
    ax.plot(d["_t"], d["ai_other_cosine"], color="tab:gray", lw=1, ls="--",
            label="GPT's answers to any other question (same quarter)")
    if "lc_ai_match_cosine" in d:
        ax.plot(d["_t"], d["lc_ai_match_cosine"], color="tab:blue", lw=1.2, ls=":", marker="o", ms=2,
                label=lab("same question, first 120 tokens of both (length check)",
                          "lc_ai_match_cosine"))
    ax.set_ylabel("cosine similarity of human answer\nto GPT answer", fontsize=9)
    ax.set_title("A. How close are human answers to GPT's answers?", fontsize=10,
                 color="dimgray", loc="left")
    ax.legend(fontsize=8, loc="best")
    ax = axes[1]
    ax.plot(d["_t"], d["pull"], color="tab:purple", lw=2, marker="o", ms=3,
            label=lab("pull = same question minus same-tag questions", "pull"))
    if "lc_pull" in d:
        ax.plot(d["_t"], d["lc_pull"], color="tab:purple", lw=1.2, ls=":", marker="o", ms=2,
                label=lab("pull, first 120 tokens of both (length check)", "lc_pull"))
    ax.axhline(0, color="0.5", lw=0.8)
    ax.set_ylabel("question-specific\nGPT-likeness", fontsize=9)
    ax.set_title("B. Is a human answer closer to what GPT says for THIS question than for "
                 "others on the same subject? (rising = more GPT-like)", fontsize=10,
                 color="dimgray", loc="left")
    ax.legend(fontsize=8, loc="best")
    for ax in axes:
        ax.grid(True, alpha=0.3)
        ax.axvline(t_break, color="black", linestyle="--", alpha=0.7)
    ord2q = dict(zip(d["_t"], d["quarter"]))
    ticks = sorted(ord2q)[::4]
    axes[-1].set_xticks(ticks)
    axes[-1].set_xticklabels([ord2q[t] for t in ticks], rotation=90, fontsize=7)
    fig.suptitle(f"{corpus} - do human answers move towards what GPT would write? (family 12)",
                 fontsize=13)
    if footnote:
        fig.text(0.5, 0.005, footnote, ha="center", va="bottom", fontsize=8, color="dimgray",
                 wrap=True)
    fig.tight_layout(rect=(0, 0.05, 1, 0.97))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("-Q", "--questions", type=Path, default=Path("data/processed/questions.parquet"))
    ap.add_argument("--out-dir", type=Path, default=source_dir("cross-validated"))
    ap.add_argument("--corpus", default="Cross Validated")
    ap.add_argument("--site", default=None, help="site name in the prompt (default: --corpus)")
    ap.add_argument("--gen-dir", type=Path, default=Path("data/anchor"))
    ap.add_argument("--cache-dir", type=Path, default=Path("data/models"))
    ap.add_argument("--emb-cache-dir", type=Path, default=Path("data/embeddings"))
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--samples", type=int, default=3, help="GPT answers per question (averaged)")
    ap.add_argument("--per-quarter", type=int, default=100, help="human answers sampled per quarter")
    ap.add_argument("--min-answers", type=int, default=20, help="min sampled answers for a quarter")
    ap.add_argument("--min-tokens", type=int, default=20, help="skip very short human answers")
    ap.add_argument("--max-tokens", type=int, default=400, help="max tokens per GPT answer")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--body-char-cap", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--break-quarter", default=CHATGPT_QUARTER)
    ap.add_argument("--hac-lags", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true", help="plan + estimate only")
    ap.add_argument("--no-generate", action="store_true", help="analyse cached generations only")
    ap.add_argument("--generate-only", action="store_true",
                    help="stop after generating (no embedding / analysis), e.g. on a machine "
                         "without the embedding database")
    ap.add_argument("--api-key-file", type=Path, default=Path(".secrets/openai_api_key.txt"))
    ap.add_argument("--embed", choices=EMBED_MODES, default="whole")
    args = ap.parse_args()
    site = args.site or args.corpus

    answers = pd.read_parquet(args.input)
    questions = pd.read_parquet(args.questions)
    sample = build_sample(answers, questions, args.per_quarter, args.min_answers,
                          args.min_tokens, args.seed)
    need = sample["parent_id"].drop_duplicates().tolist()
    gen_path = args.gen_dir / f"{args.input.stem}__{_slug(args.model)}.jsonl"
    gens = load_generations(gen_path)
    todo = [(q, d) for q in need for d in range(args.samples) if d not in gens.get(q, {})]
    print(f"Sample: {len(sample):,} human answers, {sample['quarter'].nunique()} quarters, "
          f"{len(need):,} questions; {len(todo):,} GPT answers to generate "
          f"({args.samples} per question).")

    if todo and not (args.dry_run or args.no_generate):
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_ENDPOINT") \
                and args.api_key_file.exists():
            os.environ["OPENAI_API_KEY"] = args.api_key_file.read_text().strip()
        client, kind, deployment = get_client(args.model)
        if client is None:
            raise SystemExit(f"Generator not available: {kind}")
        qmeta = sample.drop_duplicates("parent_id").set_index("parent_id")
        lock = threading.Lock()

        def _gen(task):
            q, d = task
            row = qmeta.loc[q]
            return q, d, generate_one(client, deployment, site, str(row["q_title"]),
                                      str(row["q_body"]), args.max_tokens, args.temperature,
                                      args.body_char_cap)

        t0 = time.time()
        with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
            futures = [pool.submit(_gen, t) for t in todo]
            for fut in tqdm(as_completed(futures), total=len(futures), desc="Generating", unit="ans"):
                q, d, text = fut.result()
                gens.setdefault(q, {})[d] = text
                with lock:
                    append_generation(gen_path, q, d, text)
        print(f"Generated {len(todo):,} in {time.time() - t0:,.0f}s -> {gen_path}")
    elif todo and args.dry_run:
        avg = sample.drop_duplicates("parent_id").apply(
            lambda r: len(str(r["q_title"])) + len(str(r["q_body"])), axis=1).mean()
        tin, tout = len(todo) * (min(avg, args.body_char_cap) / 4 + 60), len(todo) * args.max_tokens * 0.8
        print(f"[dry-run] ~{tin / 1e6:.1f}M prompt + ~{tout / 1e6:.1f}M completion tokens")
        return
    if args.generate_only:
        return

    model = load_model(args.cache_dir)
    emb = embedding_setup(model, args.embed, args.emb_cache_dir, args.input.stem)
    ai_path = args.emb_cache_dir / f"{args.input.stem}_anchor_{_slug(args.model)}_{args.embed}.npz"
    ai_lc_path = args.emb_cache_dir / f"{args.input.stem}_anchor_{_slug(args.model)}_open120.npz"
    raw_cache, ai_cache = load_cache(emb.raw_path), load_cache(ai_path)
    lc_cache, ai_lc_cache = load_cache(emb.lc_path), load_cache(ai_lc_path)
    result = compute_drift(sample, gens, model, raw_cache, ai_cache, args.min_answers, args.seed,
                           emb.embed, lc_fn=emb.lc, lc_cache=lc_cache, ai_lc_cache=ai_lc_cache)
    save_cache(emb.raw_path, raw_cache)
    save_cache(ai_path, ai_cache)
    save_cache(emb.lc_path, lc_cache)
    save_cache(ai_lc_path, ai_lc_cache)

    sig = significance(result, args.corpus, args.break_quarter, args.hac_lags)
    (args.out_dir / "data").mkdir(parents=True, exist_ok=True)
    result.to_csv(args.out_dir / "data" / "12_anchor_drift.csv", index=False)
    sig.to_csv(args.out_dir / "data" / "12_anchor_significance.csv", index=False)
    n_gpt = sum(len([t for t in gens.get(q, {}).values() if t]) for q in need)
    note = (f"Up to {args.per_quarter} human answers per quarter; each question answered "
            f"{args.samples} times by {args.model} (temperature {args.temperature}), draws averaged. "
            f"{len(result)} quarters, {int(result['n_answers'].sum()):,} human answers, "
            f"{n_gpt:,} GPT answers. Mean cosine between draws of the same question: "
            f"{result['gpt_draw_cosine'].mean():.2f}. Same-tag baseline falls back to any other "
            f"question for {result['baseline_fallback_share'].mean():.0%} of answers.")
    plot_drift(result, sig, args.out_dir / "12_anchor_drift.png", args.corpus, note)
    print(result.to_string(index=False))
    print(sig[["metric", "slope_change", "slope_change_p", "prepost_diff", "prepost_p"]].to_string(index=False))


if __name__ == "__main__":
    main()
