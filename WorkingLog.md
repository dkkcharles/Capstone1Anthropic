**Week of Aug 31st 2026:
- Chose the Anthropic Economic Index dataset (open CSV releases, CC-BY, supports trend analysis across releases)
- Evaluated Q2 (geographic adoption) and Q3 (consumers vs. businesses) as questions of interest but I leaned more towards Q2 due to my lack of knowledge on geographic stereotypes.

**Week of Sep 7th 2026: No meeting
- Created GitHub repo and set up structure (notebooks/, src/, git-ignored data/, NOTES.md, README.md)
- Decided on Q3: Do businesses (API usage) show a higher automation share than individual
  consumers (Claude.ai usage) on the same tasks, and has that gap changed across releases?

**Week of Sep 14th 2026:
- Step 1 tasks 2–4: downloaded the 2025-09-15 release, recorded provenance (URL, release,
  license, citation) and dataset summary in NOTES.md
- Wrote src/inventory.py (files, sizes, rows, columns, missing-value rates)
- Built first claimed-vs-actual table: reproduced the report's 77% API automation figure

**Week of Sep 21st 2026:
- Step 1 tasks 5–6: first raw examples and PROFILE.md with three figures
  (collaboration patterns, usage tiers, automation by platform)

**Week of Sep 28th 2026: No meeting
- Explored the other releases; realised one release = one time point, so the
  "has the gap changed" half of the question couldn't be answered
- Decided to switch to releases 3–6 (2025-09-15 to 2026-06-26), the only releases with API data
  (releases 1–2 are Claude.ai-only)

**Week of Oct 5th 2026:
- Reworked Step 1 for four releases; found the 2026-06-26 release uses a new format
  (monthly totals, different column names), so wrote src/releases.py to read both formats
- Verified 12 headline numbers from the four reports against the data; all within 0.5 pp
- Found and fixed a definition error in the first table: the report's 49.1% is a share of ALL
  conversations, but I had compared it with a share of CLASSIFIED conversations
- Found that API automation jumps from ~80% to ~94% in the June 2026 release

**Week of Oct 12th 2026: No meeting
- None

**Week of Oct 19th 2026: Missed meeting
- Pinned the dataset to one Hugging Face commit and added src/fetch.py with checksum checks
- Investigated the June jump: the March 2026 report's API data includes Claude Code, the June
  release excludes it. That explains most of the jump, so I treat the June release as a
  separate regime
- Added task-level analysis for the "same tasks" part of the question:
  - Task mix: Computer & Math is ~50% of API usage vs ~33% of Claude.ai
  - Same-task comparison: the API is more automated on 85–98% of tasks published on both platforms
  - First sign that the gap comes mostly from behavior on the same tasks, not from task mix
- Added inventory checks: column tables, coverage per release, sample sizes, sampling error (±0.1 pp)
- Wrote 8 raw examples (e.g. California Aug 2025: 22.5% "none" vs 2.3% typical; editing task
  ~50 pp apart between platforms)
- Cut the geography section: API data is global-only, so geography can't explain the gap

**Week of Oct 26th 2026:
- Debated whether the June 2026 release could be split into weeks to compare with the weekly
  releases: not possible, since the files only contain monthly totals (April, May). The regime
  break is also caused by scope and method changes, not window length.
- Hypothesis testing for measurement asymmetry (src/hypothesis_tests.py, NOTES.md §9):
  paired Wilcoxon signed-rank tests on tasks published on both platforms, alpha = 0.05
  - Test 1: the API shows less feedback loop on the same task (reject H0 in all 5 periods),
    so multi-turn behavior is under-recorded on the API (the asymmetry is real)
  - Test 2: using only single-turn patterns, the API is still 18–26 pp more automated on the
    same task (reject H0 in all 5 periods), so the asymmetry does not explain the gap
  - Test 3: the API delegates LESS decision-making (AI autonomy) on 90–96% of shared tasks
    (reject H0 in all 4 periods), so businesses hand off execution, not judgement
  - Robustness: same decisions with no minimum task size and with a Bonferroni correction
- Found a format quirk: the 2026-03-24 release appends "::value" to task names in its
  numeric facets, which at first left zero tasks matched for that period
- Built the harmonization table into a script (src/harmonize.py, NOTES.md §3): one task ×
  platform × period dataset (21,037 rows) with one automation definition, consistent units,
  occupation major groups and a regime indicator
  - Task characteristics only exist from Nov 2025, so models that use them drop Aug 2025
  - Only ~half of tasks (60–69% of usage) can be matched across the June 2026 regime break
  - Several variables jump at the break on one platform only (e.g. Claude.ai multitasking
    8.8% → 22.8%), so levels are only compared within a regime
- Moved the hypothesis tests onto the harmonized dataset so every analysis uses the same
  data; all decisions unchanged (small differences from one duplicate task name in Apr 2026)

**Week of Nov 2nd 2026:
- Upcoming:
  - Regression with task fixed effects (gap on the same tasks, and how it changes by period)
  - Formal decomposition of the gap into task mix vs. behavior on the same task, per release
  - Track what changed for the same tasks across releases, within each regime