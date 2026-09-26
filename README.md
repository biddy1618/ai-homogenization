# AI Homogenization Research

Measuring whether generative AI (ChatGPT, public 2022Q4) made online writing more homogeneous.
Method: per-quarter text-diversity/similarity metrics across dated public corpora, with a layered
battery of statistical controls (length control, topic control, significance testing, a known-AI
anchor), replicated across 26 Stack Exchange communities and 3 external corpora.

**Client:** Mark Nomellini (Kirkland & Ellis). **Started:** July 2026.

## Start here

- **[docs/research/project-briefing.md](docs/research/project-briefing.md)** — the whole-project
  anchor: question, data, method, findings, glossary, and a Q&A bank. **Read this first.**
- **[docs/research/paper-draft.md](docs/research/paper-draft.md)** — the paper (draft v0.1).
- **[docs/research/tracker-plan.md](docs/research/tracker-plan.md)** — the live homogenization
  tracker: implementation, roadmap, sustainability, and handover.
- **[docs/status.md](docs/status.md)** — current status / what's done.
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
├── artifacts/           # committed outputs per corpus (data/ CSVs + plots/ PNGs)
├── tracker/             # live homogenization tracker
│   ├── tracker.py       #   SerpAPI top-N → MiniLM embed → Vendi + cosine + novelty
│   ├── queries.txt      #   the (frozen) query panel
│   └── data/            #   committed weekly results (git = the datastore)
├── data/                # local-only heavy data (gitignored)
├── docs/
│   ├── status.md        #   running status / what's done
│   ├── meetings.md      #   client meeting log
│   ├── research/        #   project-briefing, paper-draft, tracker-plan
│   ├── papers/          #   reference papers (PDFs)
│   └── archived/        #   superseded/background docs (see INDEX.md)
└── requirements.txt
```

## Theoretical grounding

Two priors motivate the study (PDFs in `docs/papers/`): **de Rooij & Biskjaer (2026)** — a
meta-analysis finding a small-but-significant homogenization effect in human–AI co-creation; and
**Samuelson & Zeckhauser (1988)** — status-quo bias (more options / weaker preference → defaulting to
the given answer), a mechanism by which an always-available AI default could drive convergence.
