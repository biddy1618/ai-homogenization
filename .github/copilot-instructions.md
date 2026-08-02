# Copilot instructions — AI Homogenization

## What this is
Research project measuring whether AI has homogenized online written text over time.
Client: Mark Nomellini (Kirkland & Ellis). ~10 hrs/week.

## Current state
- Prototype built on **Cross Validated** (Stats Stack Exchange), ~219k answers, 2010–2026.
- Pipeline: download dump → parse `Posts.xml` → clean prose → per-quarter metrics → plots.
- Metrics: TTR, MTLD, pairwise TF-IDF cosine — both raw and **length-controlled**.
- Key finding: after controlling for answer length, **no lexical homogenization**; the
  raw TTR/cosine trends were a length artifact (MTLD, length-robust, is flat/recovering).
- Next phase: **semantic** (embedding-based) similarity — surface metrics can't detect
  meaning-level convergence.

## Where things live
- `src/` — pipeline code: `parse_posts.py`, `text_clean.py`, `metrics.py`, `pipeline.py`,
  `plot.py`, `lc_sensitivity.py`, `validate_cleaning.py`.
- `artifacts/` — committed outputs (plots + metric CSVs).
- `data/` — heavy local data (dumps, `Posts.xml`, `answers.parquet`). **Gitignored.**
- `docs/` — `meetings.md` (running log), `workplan.md`, `papers/` (PDFs), `research/` (notes).

## Conventions
- Always use the project venv: `.venv/Scripts/python.exe`. Never install to system Python.
- Package installs need the public PyPI workaround:
  `--index-url https://pypi.org/simple/ --trusted-host pypi.org` (corp Artifactory lacks them).
- Windows PowerShell: use `;` not `&&`. The terminal runs from the projects root, so use
  **absolute paths** in commands.
- Generated outputs go to `artifacts/`; never commit anything under `data/`.

## Guardrails
- **Never commit or push without explicit user approval.** Show the diff and wait.
- Don't delete or move `data/` dumps (re-downloading is ~600 MB).
- Don't chain `Remove-Item` after a move/`git mv` that can fail — the delete still runs on `;`.
