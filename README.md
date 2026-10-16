# AI Homogenization Research

Measuring whether generative AI (ChatGPT, public 2022Q4) made online writing more homogeneous.
Method: per-quarter text-diversity/similarity metrics across dated public corpora, with a layered
battery of statistical controls (length control, topic control, significance testing, a known-AI
anchor), replicated across 26 Stack Exchange communities and 4 external corpora (Hacker News, PubMed
oncology, arXiv CS, arXiv mathematics).

**Client:** Mark Nomellini (Kirkland & Ellis). **Started:** July 2026.

> **2026-10-13: embedding results under re-check.** The embedding model read only the first ~100
> words of each text; all embedding-based results are being re-run on whole text. See
> [docs/status.md](docs/status.md) → *Current state*.

## Start here

- **[docs/research/project-briefing.md](docs/research/project-briefing.md)** — the whole-project
  anchor: question, data, method, findings, glossary, and a Q&A bank. **Read this first.**
- **[paper/main.tex](paper/main.tex)** — the paper (LaTeX; compiled `paper/main.pdf`).
- **[tracker/README.md](tracker/README.md)** — the live homogenization tracker.
- **[docs/status.md](docs/status.md)** — current state, replication progress, open framing questions.
- **[docs/meetings.md](docs/meetings.md)** — client meeting log.

## Headline finding

The dramatic surface convergence is a **length artifact** (answers got longer). A smaller, real rise
in contextual-embedding similarity survives length control, but it is **largely topic composition**
(*what* people write about), not within-topic **style** (*how* they write). So: **no broad style
homogenization, but real topic-level homogenization** — a narrowing and drift of the topic mix. Full
detail in the project briefing.

## Repository structure

```
project-ai-homogenization/
├── src/                 # analysis pipeline (13 metric "families": lexical → LSA → BERT →
│                        #   topic control → significance → GPT-anchor → decomposition)
├── artifacts/           # committed results, whole text (see artifacts/README.md):
│                        #   summary/, se-hcl/, se-lcl/, external/, robustness/, meta/
├── paper/               # LaTeX paper (main.tex, references.bib, figures/, main.pdf)
├── deliverables/        # what was sent to Mark (2026-09-07, 2026-09-14)
├── tracker/             # live homogenization tracker (weekly GitHub Action + dashboard)
│   ├── tracker.py       #   Google top-10 via Serper.dev → raw result lists
│   ├── fullpage.py      #   full pages via ScrapingRobot → whole-page embeddings → % distinct
│   ├── dashboard/       #   build.py → self-contained index.html
│   ├── queries.txt      #   the (frozen) query panel
│   └── data/            #   committed weekly results (git = the datastore)
├── data/                # local-only heavy data (gitignored)
├── docs/
│   ├── status.md        #   current state + open framing questions
│   ├── meetings.md      #   client meeting log
│   ├── research/        #   project-briefing
│   ├── papers/          #   reference papers (PDFs)
│   └── archived/        #   superseded/background docs (see INDEX.md)
└── requirements.txt
```

## Theoretical grounding

Two priors motivate the study (PDFs in `docs/papers/`): **de Rooij & Biskjaer (2026)** — a
meta-analysis finding a small-but-significant homogenization effect in human–AI co-creation; and
**Samuelson & Zeckhauser (1988)** — status-quo bias (more options / weaker preference → defaulting to
the given answer), a mechanism by which an always-available AI default could drive convergence.
