# Step 3 split run — instructions for the personal-computer agent

**Temporary doc (2026-10-15).** Delete it once the results below are pushed and verified.

## Context (read first)
This repo studies whether online writing became more homogeneous after ChatGPT (2022Q4). The
embedding model (MiniLM via fastembed) only reads the first 128 tokens of a text, so all embedding
results are being re-run on **whole text** (`--embed whole`: cleaned text, sentence chunks of
<= 120 tokens, chunk vectors averaged; plus an exact 120-token opening-window control). Results go
to `artifacts/<site>/whole/`. Delivered (old) results in `artifacts/<site>/data|plots/` must stay
untouched.

Step 3 = whole-text family 5 on 21 Stack Exchange sites, split between two machines:

| Machine | Sites | State (2026-10-15 00:30) |
|---|---|---|
| Work VDI | bicycles, gardening, rpg, boardgames, money | done |
| Work VDI | photo | running — left to finish, not interrupted |
| Work VDI | workplace, diy, scifi, gaming, crypto, law, history | starts automatically after photo |
| **This computer** | **cs, biology, astronomy, chemistry, electronics, physics, softwareengineering, english** | **to run here** |

**This computer runs exactly these 8:**

`cs biology astronomy chemistry electronics physics softwareengineering english`

Do not run any other site — the VDI covers the other 13.

## Rules
- Do **not** edit any code or existing file. Do not run anything except the commands below.
- Commit **only** `artifacts/<site>/whole/` for the 8 sites above (16 files). Nothing else.
- `data/` is gitignored (dumps, parquets, embedding caches) — never force-add it.
- Use exactly Python 3.12 and the pinned versions below: they must match the VDI so the dumps are
  parsed identically.

## Steps (Windows, PowerShell)

```powershell
git clone https://github.com/biddy1618/ai-homogenization
cd ai-homogenization
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install numpy==2.5.1 pandas==3.0.5 pyarrow==25.0.0 fastembed==0.8.0 onnxruntime==1.28.0 `
  tokenizers==0.23.1 beautifulsoup4==4.15.0 lxml==6.1.1 py7zr==1.1.3 scikit-learn==1.9.0 `
  matplotlib==3.11.1 tqdm==4.70.0

python src/add_sites.py --embed whole --only cs biology astronomy chemistry electronics physics softwareengineering english
```

What `add_sites.py` does per site (resumable; finished sites are skipped on re-run):
1. downloads `<domain>.7z` from archive.org into `data/raw/` with `curl.exe` (~2.7 GB total;
   physics and electronics ~700 MB each),
2. extracts `Posts.xml`, parses it to `data/processed/<site>_answers.parquet`,
3. computes whole-text family 5 → `artifacts/<site>/whole/data/5_semantic_bert.csv` and
   `artifacts/<site>/whole/plots/5_semantic_bert.png`.

The MiniLM model downloads automatically on first use from the repo's GitHub release `minilm-v1`
(a byte-identical copy of the VDI's model; the original Google Cloud Storage URL now returns 403)
into `data/models/fast-all-MiniLM-L6-v2/`, and `load_model` refuses to run if the SHA256 of
`model.onnx` or `tokenizer.json` differs. Do not use any Hugging Face copy.
Expect roughly 30–60 minutes of compute per site. A line `[gate] SKIP family 5` or `FAILED` for a
site is a problem — stop and report it (all 8 sites passed the gate on the VDI).

*Mac/Linux only:* `add_sites.py` calls `curl.exe`; change it to `curl` locally for the run and do
**not** commit that change.

## Verify before committing
The parse must match the VDI exactly. The `volume` column (answers per quarter) of each new CSV must
equal the delivered CSV:

```powershell
python -c "
import pandas as pd
for s in 'cs biology astronomy chemistry electronics physics softwareengineering english'.split():
    a = pd.read_csv(f'artifacts/{s}/data/5_semantic_bert.csv').set_index('quarter')['volume']
    b = pd.read_csv(f'artifacts/{s}/whole/data/5_semantic_bert.csv').set_index('quarter')['volume']
    print(f'{s:22s} quarters {len(a)}/{len(b)}  volumes identical: {a.equals(b)}')
"
```

All 8 must print `volumes identical: True`. If any prints `False`, do not commit — report it.

## Commit and push

```powershell
git pull --rebase
git add artifacts/cs/whole artifacts/biology/whole artifacts/astronomy/whole artifacts/chemistry/whole `
  artifacts/electronics/whole artifacts/physics/whole artifacts/softwareengineering/whole artifacts/english/whole
git status --short   # expect exactly 16 new files, nothing else staged
git commit -m "Step 3: whole-text family 5 on 8 high-cog SE sites (personal-computer half)"
git push
```

Then tell the user it is pushed. The VDI agent will pull, re-check, and run the 26-site summary
(`significance.py --all --variant whole`, `cog_load_compare.py --variant whole`).
