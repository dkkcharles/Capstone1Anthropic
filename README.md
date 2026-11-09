# Capstone1Anthropic
Data Science Capstone 1 - CMSC 681

Do businesses (API usage) show a higher automation share than individual consumers (Claude.ai usage) on the same tasks, and has that gap changed across the Anthropic Economic Index's releases?

## Dataset
Anthropic Economic Index, https://huggingface.co/datasets/Anthropic/EconomicIndex (CC-BY). Pinned to commit `4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6`.

Releases used: 2025-09-15, 2026-01-15, 2026-03-24 and 2026-06-26. API data first appears in the 2025-09-15 release. Releases 1 and 2 (2025-02-10, 2025-03-27) are Claude.ai-only, so they cannot show an API vs. Claude.ai gap and are not used. That leaves five periods per platform: three one-week samples (Aug 2025, Nov 2025, Feb 2026) and two monthly aggregates (Apr, May 2026).

## Sources
1. Dataset: https://huggingface.co/datasets/Anthropic/EconomicIndex
2. Original paper: arXiv:2503.04761 [cs.CY]
3. September 2025 report paper, which introduced the API comparison: arXiv:2511.15080
4. Reports:
   - https://www.anthropic.com/research/anthropic-economic-index-september-2025-report
   - https://www.anthropic.com/research/anthropic-economic-index-january-2026-report
   - https://www.anthropic.com/research/economic-index-march-2026-report
   - https://www.anthropic.com/research/economic-index-june-2026-report

## Reproduce
Run from the repo root:

```bash
python -m venv venv
venv/Scripts/pip install -r requirements.txt
venv/Scripts/python src/fetch.py
venv/Scripts/python src/inventory.py
venv/Scripts/python src/raw_examples.py
venv/Scripts/python src/exploratory.py
venv/Scripts/python src/hypothesis_tests.py
venv/Scripts/python src/harmonize.py
venv/Scripts/python src/regression.py
venv/Scripts/python src/decomposition.py
```

- `src/fetch.py`: downloads the data into git-ignored `data/` at the pinned commit and verifies checksums.
- `src/releases.py`: release definitions and shared metric logic.
- `src/inventory.py`: Step 4 inventory and claimed-vs-actual checks.
- `src/raw_examples.py`: the Step 5 slices in `NOTES.md`.
- `src/exploratory.py`: the figures in `PROFILE.md`.
- `src/hypothesis_tests.py`: the measurement-asymmetry tests in `NOTES.md` §9.
- `src/harmonize.py`: builds the harmonized task × platform × period panel (`data/processed/task_panel.csv`) used by the regression.
- `src/regression.py`: weighted regressions on the harmonized panel (same-task gap per period, predictors of automation and of the gap).
- `src/decomposition.py`: splits each period's gap into behavior on the same task, task mix, and tasks on one platform only.

Write-ups: `NOTES.md` (provenance, verification, harmonization, raw examples) and `PROFILE.md` (exploratory profile).
