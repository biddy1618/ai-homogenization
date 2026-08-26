"""#12 — known-AI anchor test ("do human answers drift toward AI output over time?").

Pairwise-similarity families (5/6/11) ask whether humans write more like *each other*.
This asks a different, more causal question: do human answers move toward what an *AI*
would write for the **same question**, and does that pull strengthen after ChatGPT?

Design (per-question, the strong version — mirrors the family-11 topic control):
  1. Sample up to ``--per-quarter`` human answers per quarter (that have a resolvable
     question and enough tokens).
  2. For each distinct question in that sample, generate **one** AI answer from a fixed
     model (the "anchor"), using the question title + body as the prompt. Generations are
     cached to ``data/anchor/<corpus>__<model>.jsonl`` so re-runs never re-spend.
  3. Embed the AI answers and the human answers with the same MiniLM model.
  4. For each human answer, ``ai_match_cosine`` = cosine to *its own* question's AI answer;
     ``ai_mismatch_cosine`` = cosine to a random *other* question's AI answer (a generic
     "AI-style proximity" baseline). Bin both by the human answer's own quarter.
  5. If ``ai_match_cosine`` rises after 2022Q4 — especially relative to the mismatch
     baseline — that is human text drifting toward AI output on the same topic.

Provisioning the generator (no key is stored or passed through the assistant):
  * Azure OpenAI:  set ``AZURE_OPENAI_ENDPOINT``, ``AZURE_OPENAI_API_KEY``,
    ``AZURE_OPENAI_DEPLOYMENT`` (and optionally ``AZURE_OPENAI_API_VERSION``).
  * OpenAI:        set ``OPENAI_API_KEY`` and pass ``--model`` (default gpt-4o-mini).
  * Neither set:   the script runs in **dry-run** mode — it prints the sampling plan and a
    token estimate and exits (or analyses whatever generations are already cached).

Output: ``<out-dir>/data/12_anchor_drift.csv`` + ``<out-dir>/plots/12_anchor_drift.png``
and a significance row (ITS slope-change + Mann-Kendall) on ``ai_match_cosine``.
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
from semantic_bert import CHATGPT_QUARTER, load_model, embed_texts
from significance import _q_ord, analyze_metric

SYSTEM_PROMPT = (
    "You are a knowledgeable user answering a question on the {site} Stack Exchange. "
    "Write a single, self-contained, helpful answer in your own words. "
    "Do not include greetings, sign-offs, or meta commentary."
)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# --------------------------------------------------------------------------- sampling
def build_sample(answers: pd.DataFrame, questions: pd.DataFrame, per_quarter: int,
                 min_answers: int, min_tokens: int, max_questions: int | None,
                 seed: int) -> pd.DataFrame:
    """Return the sampled human answers joined to their question title/body."""
    rng = np.random.default_rng(seed)
    qids = set(questions["id"].tolist())
    a = answers[(answers["parent_id"].isin(qids)) & (answers["token_count"] >= min_tokens)].copy()
    if a.empty:
        raise SystemExit("No answers with a resolvable question — check the questions parquet.")

    picks = []
    for q, g in a.groupby("quarter"):
        if len(g) < min_answers:
            continue
        take = g if len(g) <= per_quarter else g.iloc[rng.choice(len(g), per_quarter, replace=False)]
        picks.append(take)
    sample = pd.concat(picks, ignore_index=True)

    if max_questions is not None and sample["parent_id"].nunique() > max_questions:
        keep = rng.choice(sample["parent_id"].unique(), size=max_questions, replace=False)
        sample = sample[sample["parent_id"].isin(keep)].reset_index(drop=True)

    qtext = questions.set_index("id")[["title", "text"]]
    sample = sample.join(qtext, on="parent_id", rsuffix="_q")
    sample = sample.rename(columns={"title": "q_title", "text_q": "q_body"})
    return sample.reset_index(drop=True)


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


def load_generations(path: Path) -> dict[int, str]:
    gens: dict[int, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                gens[int(rec["qid"])] = rec["text"]
    return gens


def append_generation(path: Path, qid: int, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"qid": int(qid), "text": text}) + "\n")


# --------------------------------------------------------------------------- metric
def compute_drift(sample: pd.DataFrame, gens: dict[int, str], model,
                  raw_cache: dict | None, ai_cache: dict | None,
                  min_answers: int, seed: int) -> pd.DataFrame:
    """Per-quarter mean cosine of human answers to the matched / mismatched AI answer."""
    rng = np.random.default_rng(seed)
    sample = sample[sample["parent_id"].isin(gens)].reset_index(drop=True)
    if sample.empty:
        raise SystemExit("No sampled answers have a cached AI generation yet.")

    # Embed AI answers once per unique question (cache keyed by qid).
    uq = sample["parent_id"].drop_duplicates().tolist()
    ai_vecs = cached_embed(model, uq, [gens[q] for q in uq], embed_texts, ai_cache)
    qid_to_row = {q: i for i, q in enumerate(uq)}

    # Embed the human answers (reuse the id-keyed raw cache).
    hvecs = cached_embed(model, sample["id"].tolist(), sample["text"].tolist(),
                         embed_texts, raw_cache)

    gi = sample["parent_id"].map(qid_to_row).to_numpy()
    match = np.einsum("ij,ij->i", hvecs, ai_vecs[gi])

    # Mismatch baseline: pair each answer with a *different* question's AI answer.
    perm = rng.permutation(len(uq))
    fixed = perm == np.arange(len(uq))
    if fixed.any() and len(uq) > 1:
        perm[fixed] = (perm[fixed] + 1) % len(uq)
    mismatch = np.einsum("ij,ij->i", hvecs, ai_vecs[perm[gi]])

    per = pd.DataFrame({"quarter": sample["quarter"].to_numpy(),
                        "match": match, "mismatch": mismatch})
    records = []
    for q, g in sorted(per.groupby("quarter")):
        if len(g) < min_answers:
            continue
        records.append({"quarter": q, "n_answers": int(len(g)),
                        "n_questions": int(sample.loc[g.index, "parent_id"].nunique()),
                        "ai_match_cosine": float(g["match"].mean()),
                        "ai_mismatch_cosine": float(g["mismatch"].mean()),
                        "match_minus_mismatch": float((g["match"] - g["mismatch"]).mean())})
    return pd.DataFrame(records).sort_values("quarter").reset_index(drop=True)


def plot_drift(df: pd.DataFrame, output: Path, corpus: str, footnote: str = "") -> None:
    d = df.copy()
    d["_t"] = d["quarter"].map(_q_ord)
    d = d.sort_values("_t")
    t_break = _q_ord(CHATGPT_QUARTER)

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(d["_t"], d["ai_match_cosine"], color="tab:blue", lw=2, marker="o", ms=3,
            label="Human answers vs the AI's answer to the SAME question")
    ax.plot(d["_t"], d["ai_mismatch_cosine"], color="tab:gray", lw=1.5, ls="--", marker="o", ms=3,
            label="Human answers vs the AI's answer to a DIFFERENT question (chance baseline)")
    ax.axvline(t_break, color="black", linestyle="--", alpha=0.7, label="ChatGPT release (2022Q4)")
    ax.axvspan(t_break, d["_t"].max(), color="tab:red", alpha=0.05)

    ord2q = dict(zip(d["_t"], d["quarter"]))
    ticks = sorted(ord2q)[::8]
    ax.set_xticks(ticks)
    ax.set_xticklabels([ord2q[t] for t in ticks], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("mean cosine to the AI's answer\n(higher = more AI-like)", fontsize=10)
    ax.set_xlabel("Quarter", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9, loc="best", framealpha=0.9)
    fig.suptitle(f"{corpus} \u2014 Are human answers drifting toward ChatGPT's answers? "
                 "(anchor test #12)", fontsize=13, fontweight="bold", y=0.995)
    ax.set_title("Blue rising above its gray chance baseline after 2022Q4 would mean humans "
                 "converging on AI phrasing", fontsize=9.5, color="dimgray", loc="center", pad=8)
    if footnote:
        fig.text(0.5, -0.02, footnote, ha="center", va="top", fontsize=7.5,
                 color="dimgray", wrap=True)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description="Known-AI anchor drift test (#12)")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/processed/answers.parquet"))
    ap.add_argument("-Q", "--questions", type=Path, default=Path("data/processed/questions.parquet"))
    ap.add_argument("--out-dir", type=Path, default=Path("artifacts/cross-validated"))
    ap.add_argument("--corpus", default="Cross Validated")
    ap.add_argument("--site", default="Cross Validated", help="Site name injected into the prompt")
    ap.add_argument("--gen-dir", type=Path, default=Path("data/anchor"))
    ap.add_argument("--cache-dir", type=Path, default=Path("data/models"))
    ap.add_argument("--emb-cache-dir", type=Path, default=Path("data/embeddings"))
    ap.add_argument("--model", default="gpt-4o-mini", help="OpenAI model (or Azure deployment fallback)")
    ap.add_argument("--per-quarter", type=int, default=25, help="Human answers sampled per quarter")
    ap.add_argument("--max-questions", type=int, default=None, help="Global cap on questions to generate")
    ap.add_argument("--min-answers", type=int, default=10, help="Min sampled answers for a quarter to count")
    ap.add_argument("--min-tokens", type=int, default=20, help="Skip very short human answers")
    ap.add_argument("--max-tokens", type=int, default=400, help="Max tokens per AI answer")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--concurrency", type=int, default=8, help="Parallel generation requests")
    ap.add_argument("--body-char-cap", type=int, default=4000, help="Truncate question body in the prompt")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--break-quarter", default=CHATGPT_QUARTER)
    ap.add_argument("--hac-lags", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true", help="Plan + estimate only; never call the API")
    args = ap.parse_args()

    if not args.questions.exists():
        raise SystemExit(f"{args.questions} not found — re-parse with "
                         f"`parse_posts.py <Posts.xml> -o answers.parquet -q {args.questions}`.")

    answers = pd.read_parquet(args.input)
    questions = pd.read_parquet(args.questions)
    sample = build_sample(answers, questions, args.per_quarter, args.min_answers,
                          args.min_tokens, args.max_questions, args.seed)
    need = sample["parent_id"].drop_duplicates().tolist()

    gen_path = args.gen_dir / f"{args.input.stem}__{_slug(args.model)}.jsonl"
    gens = load_generations(gen_path)
    uncached = [q for q in need if q not in gens]

    print(f"Sample: {len(sample):,} human answers across "
          f"{sample['quarter'].nunique()} quarters; {len(need):,} distinct questions "
          f"({len(uncached):,} need generation, {len(gens):,} already cached).")

    client, kind, deployment = get_client(args.model)

    if args.dry_run or client is None:
        if uncached:
            avg_chars = sample.drop_duplicates("parent_id")[["q_title", "q_body"]].apply(
                lambda r: len(str(r["q_title"])) + len(str(r["q_body"])), axis=1).mean()
            est_in = len(uncached) * (min(avg_chars, args.body_char_cap) / 4 + 40)
            est_out = len(uncached) * args.max_tokens
            print(f"\n[dry-run] would generate {len(uncached):,} answers with '{args.model}'.")
            print(f"[dry-run] rough token estimate: ~{est_in/1e3:,.0f}k prompt + "
                  f"~{est_out/1e3:,.0f}k completion tokens.")
        if client is None and not args.dry_run:
            print(f"\nGenerator not available: {kind}.")
            print("Set env vars, then re-run (key is entered by you in the terminal, never via chat):")
            print("  OpenAI:  $env:OPENAI_API_KEY='...'")
            print("  Azure:   $env:AZURE_OPENAI_API_KEY / _ENDPOINT / _DEPLOYMENT")
        if not gens:
            print("\nNo cached generations yet — nothing to analyse. Exiting.")
            return
        print(f"\nProceeding on the {len(gens):,} cached generations only.")
    else:
        workers = max(1, args.concurrency)
        print(f"\nGenerating {len(uncached):,} AI answers via {kind} ('{deployment}') "
              f"with {workers} worker(s)...")
        qmeta = sample.drop_duplicates("parent_id").set_index("parent_id")
        write_lock = threading.Lock()

        def _gen(qid):
            row = qmeta.loc[qid]
            text = generate_one(client, deployment, args.site, str(row["q_title"]),
                                str(row["q_body"]), args.max_tokens, args.temperature,
                                args.body_char_cap)
            return qid, text

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_gen, qid) for qid in uncached]
            for fut in tqdm(as_completed(futures), total=len(futures),
                            desc="Generating", unit="q"):
                qid, text = fut.result()
                gens[qid] = text
                with write_lock:
                    append_generation(gen_path, qid, text)
        print(f"Generations cached -> {gen_path} ({len(gens):,} total)")

    model = load_model(args.cache_dir)
    raw_path = args.emb_cache_dir / f"{args.input.stem}_minilm_raw.npz"
    ai_path = args.emb_cache_dir / f"{args.input.stem}_anchor_{_slug(args.model)}.npz"
    raw_cache, ai_cache = load_cache(raw_path), load_cache(ai_path)

    # Empty entries are content-filter skips: cached so they never re-spend, dropped here.
    gens_ok = {q: t for q, t in gens.items() if t and t.strip()}
    n_skip = len(gens) - len(gens_ok)
    if n_skip:
        print(f"Skipping {n_skip:,} content-filtered question(s) in the analysis.")

    result = compute_drift(sample, gens_ok, model, raw_cache, ai_cache,
                           args.min_answers, args.seed)

    save_cache(raw_path, raw_cache)
    save_cache(ai_path, ai_cache)

    csv_path = args.out_dir / "data" / "12_anchor_drift.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(csv_path, index=False)
    print(f"\nWrote {len(result)} quarters -> {csv_path}")
    print(result.to_string(index=False))

    plot_path = args.out_dir / "plots" / "12_anchor_drift.png"
    anchor_note = (f"Sampling: up to {args.per_quarter} human answers per quarter, each compared "
                   f"with one {args.model} answer to the same question. "
                   f"{len(result)} quarters; {int(result['n_answers'].sum()):,} human answers vs "
                   f"{len(gens_ok):,} AI answers"
                   + (f"; {n_skip} content-filtered question(s) excluded." if n_skip else "."))
    plot_drift(result, plot_path, corpus=args.corpus, footnote=anchor_note)
    print(f"Plot -> {plot_path}")

    t_break = _q_ord(args.break_quarter)
    result["_t"] = result["quarter"].map(_q_ord)
    print("\n=== significance (drift toward AI) ===")
    for metric in ("ai_match_cosine", "match_minus_mismatch"):
        row, _ = analyze_metric(result, metric, t_break, args.hac_lags)
        print(f"[{metric}] slope_change={row['slope_change']:+.5f} (p={row['slope_change_p']:.4g}) "
              f"| post_slope={row['post_slope']:+.5f} "
              f"| MK-post tau={row['mk_tau_post']:+.3f} (p={row['mk_p_post']:.4g}) "
              f"| pre/post diff={row['prepost_diff']:+.5f} (p={row['prepost_p']:.4g})")


if __name__ == "__main__":
    main()
