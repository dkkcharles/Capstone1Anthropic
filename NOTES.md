# NOTES

Research question: Do businesses (API usage) show a higher automation share than individual consumers (Claude.ai usage) on the same tasks, and has that gap changed across the Anthropic Economic Index's releases?

Scripts behind everything below (run from the repo root):
- `src/fetch.py`: downloads every file at a pinned commit and checks checksums.
- `src/releases.py`: shared release definitions and metric logic.
- `src/inventory.py`: Step 4 inventory, claimed vs. actual.
- `src/raw_examples.py`: Step 5 slices.
- `src/exploratory.py`: Step 6 figures.

## 1. Provenance

**Source:** Anthropic Economic Index, https://huggingface.co/datasets/Anthropic/EconomicIndex. This is the primary source: Anthropic's own Hugging Face dataset.

**Pinned version:** commit `4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6` (2026-09-30). This is the latest commit before the files were downloaded. `src/fetch.py` downloads with `revision=` set to this commit and checks every CSV's sha256. All 8 local files match it byte for byte.

**Download dates:**
- 2026-09-13: first download (2025-09-15 release, enriched Claude.ai file, no longer used).
- 2026-10-05: all 8 CSVs below.
- 2026-10-25: documentation and O*NET reference file, via `src/fetch.py`.

**License:** data released under CC-BY; code released under the MIT License.

**Files** (permanent `/resolve/<commit>/` links):

| Release | Description (from the dataset README) | Files |
|:--|:--|:--|
| 2025-09-15 | Geographic and first-party API data using Sonnet 4 | [aei_raw_1p_api_2025-08-04_to_2025-08-11.csv](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2025_09_15/data/intermediate/aei_raw_1p_api_2025-08-04_to_2025-08-11.csv), [aei_raw_claude_ai_2025-08-04_to_2025-08-11.csv](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2025_09_15/data/intermediate/aei_raw_claude_ai_2025-08-04_to_2025-08-11.csv) |
| 2026-01-15 | Economic primitives and Sonnet 4.5 | [aei_raw_1p_api_2025-11-13_to_2025-11-20.csv](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2026_01_15/data/intermediate/aei_raw_1p_api_2025-11-13_to_2025-11-20.csv), [aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2026_01_15/data/intermediate/aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv) |
| 2026-03-24 | Opus 4.5/4.6 and learning curves | [aei_raw_1p_api_2026-02-05_to_2026-02-12.csv](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2026_03_24/data/aei_raw_1p_api_2026-02-05_to_2026-02-12.csv), [aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2026_03_24/data/aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv) |
| 2026-06-26 | Artifacts and monthly aggregates | [aei_1p_api_2026-06-26.csv](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2026_06_26/data/aei_1p_api_2026-06-26.csv), [aei_claude_ai_2026-06-26.csv](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv) |

Also fetched:
- each release's `data_documentation.md`;
- `release_2025_09_15/data/input/onet_task_statements_raw.xlsx`, which maps each task to its O*NET-SOC code and is used for the task mix.

Releases 1 and 2 (2025-02-10, 2025-03-27) are Claude.ai-only. They can't show an API vs. Claude.ai gap, so they are not used.

**Citations:**
- 2025-09-15: @online{appelmccrorytamkin2025geoapi, author = {Ruth Appel and Peter McCrory and Alex Tamkin and Michael Stern and Miles McCain and Tyler Neylon}, title = {Anthropic Economic Index Report: Uneven Geographic and Enterprise AI Adoption}, date = {2025-09-15}, year = {2025}, url = {www.anthropic.com/research/anthropic-economic-index-september-2025-report}, }
- 2026-01-15: @online{anthropic2026aeiv4, author = {Ruth Appel and Maxim Massenkoff and Peter McCrory and Miles McCain and Ryan Heller and Tyler Neylon and Alex Tamkin}, title = {Anthropic Economic Index report: economic primitives}, date = {2026-01-15}, year = {2026}, url = {https://www.anthropic.com/research/anthropic-economic-index-january-2026-report}, }
- 2026-03-24: @online{anthropic2026aeiv5, author = {Maxim Massenkoff and Eva Lyubich and Peter McCrory and Ruth Appel and Ryan Heller}, title = {Anthropic Economic Index report: Learning curves}, date = {2026-03-24}, year = {2026}, url = {https://www.anthropic.com/research/economic-index-march-2026-report}, }
- 2026-06-26: @online{anthropic2026aeiv6, author = {Maxim Massenkoff and Eva Lyubich and Szymon Sacher and Zoe Hitzig and Shaoyi Zhang and Ryan Heller and Peter McCrory}, title = {Anthropic Economic Index report: Cadences}, date = {2026-06-26}, year = {2026}, url = {https://www.anthropic.com/research/economic-index-june-2026-report}, }

## 2. Dataset summary

### Collection
Each release samples Claude.ai conversations and first-party (1P) API traffic. It analyses them with Clio, an automated, privacy-preserving framework in which Claude reads the transcripts and no human does. Each conversation is mapped to a task in the U.S. Department of Labor's O*NET catalog.

- **2025-09-15:** one week, 2025-08-04 to 2025-08-11.
  - Claude.ai: 1M Free and Pro conversations.
  - API: 1M transcripts sampled from a pool of 1P API customers that makes up roughly half of API usage.
- **2026-01-15:** one week, 2025-11-13 to 2025-11-20. 1M conversations and 1M API transcripts.
- **2026-03-24:** one week, 2026-02-05 to 2026-02-12. 1M conversations from each platform. The API sample includes Claude Code (report footnote 2).
- **2026-06-26:** calendar-month aggregates for April and May 2026.
  - Conversations are sampled continuously every day; the report contrasts this with the earlier seven-day samples.
  - Claude.ai covers chat and Cowork (Free, Pro, Max).
  - The API file excludes Claude Code (documentation, Source Files table).

### Unit of observation
- **Weekly releases** (2025-09-15 to 2026-03-24, "raw" schema): one row = one metric (`variable`) for one facet value (`cluster_name`) in one geography, for the sampled week.
  - Underneath, a Claude.ai record is a conversation. An API record is a single prompt–response pair, so API "conversations" are not full multi-turn trajectories.
  - The API is global only. Claude.ai is global / country / US state (2025-09-15) or global / country / country-state (later).
- **Monthly release** (2026-06-26, "monthly" schema): one row = one metric (`metric_id`) for one geography (`geo_id`) × one category node (`category_name`, `node_name` / `node_external_id`, `hierarchy_level`) × one month (`date_start`).
  - Collaboration patterns are their own metric_ids.
  - Only shares are published, no counts.

### Labels
Clio assigns each conversation one of five collaboration patterns, or "none":
- **Automation:** directive, feedback loop.
- **Augmentation:** task iteration, learning, validation.

The classification was hand-validated only in the original paper: 90.7% of 150 conversations were judged to have their best label (arXiv 2503.04761, Appendix C "Human Validation", p.21). That validation applies to the original setup. The classifying model has changed since:
- V2 used Sonnet 3.7, and V3 (2025-09-15) used Sonnet 4 (2025-09-15 report).
- 2026-01-15 used Sonnet 4.5. That report's footnote 7 says model changes affect classifications, though the effects "tend to be modest".
- The 2026-03-24 and 2026-06-26 reports don't name the classifying model. 2026-06-26 adds a new artifact classifier.

No validation has been published for later releases or for API transcripts specifically.

### Headline numbers (verification targets)
- **2025-09-15:**
  - ~1M Claude.ai conversations and ~1M API transcripts.
  - 19,530 O*NET tasks in the taxonomy (arXiv 2503.04761, p.18, Figure 9).
  - Claude.ai: 49.1% automation vs. 47.0% augmentation. API: 77% automation, 12% augmentation.
  - Claude.ai directive share rose from 27% to 39% (arXiv 2511.15080).
- **2026-01-15:**
  - Claude.ai: augmented "jumped 5pp to 52%"; automated "fell 4pp to 45%"; directive "fell 7pp to 32%".
  - API: about three-quarters automation.
  - Top 10 tasks: 24% of Claude.ai usage, 32% of API usage. Over 3,000 tasks on Claude.ai.
- **2026-03-24:**
  - Claude.ai augmentation "increased slightly". API automation "decreased sharply".
  - Top 10 tasks: 24% → 19% on Claude.ai; 33% on the API, "up from 28%".
- **2026-06-26:** no automation headline. Personal use is ~35% of chat and Cowork conversations on weekdays and just under 50% on weekends.

## 3. Harmonization table

The three weekly releases form one regime and the monthly release another. Compare within a regime, and treat any jump at the 2026-06-26 boundary as possibly caused by the change in method (see §7).

| Release | Sample | Claude.ai scope | API scope | Classifier model | O*NET version | Format |
|:--|:--|:--|:--|:--|:--|:--|
| 2025-09-15 | 1 week, Aug 2025 | Free, Pro | Customer pool (~half of API use); Claude Code not stated | Sonnet 4 | 2010 (per 2026-03-24 fn 3) | raw, counts + shares |
| 2026-01-15 | 1 week, Nov 2025 | Free, Pro, Max per report; file says "Free and Pro" | Claude Code not stated | Sonnet 4.5 | 2010 (per 2026-03-24 fn 3) | raw, counts + shares; adds economic primitives (ai_autonomy etc.) |
| 2026-03-24 | 1 week, Feb 2026 | Free, Pro, Max | **Includes Claude Code** | not stated | **2019** O*NET-SOC | raw, counts + shares |
| 2026-06-26 | Monthly, Apr + May 2026 (daily sampling) | Chat + **Cowork**, Free, Pro, Max | **Excludes Claude Code** | not stated; new artifact classifier | Task IDs match the 2010 reference for only ~78% of tasks | monthly, shares only |

Automation metric used everywhere: (directive + feedback loop) / (all five patterns), recomputed from the patterns in every release ("classified" definition). The reports' headline numbers use the "all conversations" definition: (directive + feedback loop) / all conversations, including "none". The two are not mixed.

## 4. Inventory (`src/inventory.py`)

| Release | Platform | File | MB | Rows | Records sampled (sum of collaboration_count) |
|:--|:--|:--|--:|--:|--:|
| 2025-09-15 | api | aei_raw_1p_api_2025-08-04_to_2025-08-11.csv | 6.7 | 33,794 | 944,638 |
| 2025-09-15 | claude_ai | aei_raw_claude_ai_2025-08-04_to_2025-08-11.csv | 18.0 | 100,062 | 964,494 |
| 2026-01-15 | api | aei_raw_1p_api_2025-11-13_to_2025-11-20.csv | 39.6 | 187,772 | 971,525 |
| 2026-01-15 | claude_ai | aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv | 89.7 | 458,778 | 999,875 |
| 2026-03-24 | api | aei_raw_1p_api_2026-02-05_to_2026-02-12.csv | 41.9 | 195,156 | 1,000,000 |
| 2026-03-24 | claude_ai | aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv | 98.5 | 477,717 | 1,000,000 |
| 2026-06-26 | api | aei_1p_api_2026-06-26.csv | 73.7 | 491,705 | not published |
| 2026-06-26 | claude_ai | aei_claude_ai_2026-06-26.csv | 209.0 | 1,636,573 | not published |

### Columns: raw schema (three weekly releases)
| Column | Dtype | Example | Missing % |
|:--|:--|:--|--:|
| geo_id | str | GLOBAL | 0.01 |
| geography | str | global | 0 |
| date_start | str | 2025-11-13 | 0 |
| date_end | str | 2025-11-20 | 0 |
| platform_and_product | str | Claude AI (Free and Pro) | 0 |
| facet | str | onet_task::human_with_ai_time | 0 |
| level | int64 | 0 | 0 |
| variable | str | onet_task_human_with_ai_time_stdev | 0 |
| cluster_name | str | observe children's behavior for irregulari... | 4.88 |
| value | float64 | 10.4898 | 0 |

`cluster_name` is blank for numeric facets (e.g. the ai_autonomy mean), where there is no category. That's 10.6% of Claude.ai rows in Nov 2025 and 11.6% in Feb 2026.

### Columns: monthly schema (2026-06-26)
| Column | Dtype | Example | Missing % |
|:--|:--|:--|--:|
| date_start | str | 2026-05-01 | 0 |
| date_end | str | 2026-06-01 | 0 |
| geo_id | str | IT-52 | 0 |
| geo_level | str | subregion | 0 |
| category_name | str | onet | 0 |
| hierarchy_level | int64 | 2 | 0 |
| metric_id | str | pct | 0 |
| value | float64 | 2.77 | 0 |
| node_name | str | Teach academic or vocational subjects. | 0 |
| node_external_id | str | 4.A.4.b.3.I02 | 0 |

### Coverage
| Release | Platform | Geographies | Facets / categories | Collaboration categories |
|:--|:--|:--|--:|:--|
| 2025-09-15 | api | global | 8 | 5 patterns + none + not_classified |
| 2025-09-15 | claude_ai | global, country, state_us | 7 | 5 patterns + none + not_classified |
| 2026-01-15 | api | global | 38 | 5 patterns + none + not_classified |
| 2026-01-15 | claude_ai | global, country, country-state | 34 | 5 patterns + none + not_classified |
| 2026-03-24 | api | global | 38 | 5 patterns + none (**no not_classified**) |
| 2026-03-24 | claude_ai | global, country, country-state | 34 | 5 patterns + none + not_classified |
| 2026-06-26 | api | global | 4 | 6 pattern metrics + 2 bucket metrics |
| 2026-06-26 | claude_ai | global, country, subregion | 4 | 6 pattern metrics + 2 bucket metrics |

Pattern names are the same in every release ("feedback loop" in the raw schema, `collaboration_feedback_loop_pct` in the monthly schema). `releases.py` maps between them.

### Published tasks
How the task shares that don't sum to 100% are handled:
- **Task-mix comparisons:** shares are renormalized over published, classified tasks in every release, because unpublished cells are missing rows, not zeros.
- **Task-level automation:** none and not_classified are left out of the denominator. The same choice is used in `PROFILE.md`.

| Release | Period | Platform | Tasks published | % of conversations without a published task |
|:--|:--|:--|--:|--:|
| 2025-09-15 | Aug 2025 | api | 2,054 | 12.16 |
| 2025-09-15 | Aug 2025 | claude_ai | 2,616 | 8.13 |
| 2026-01-15 | Nov 2025 | api | 2,251 | 11.72 |
| 2026-01-15 | Nov 2025 | claude_ai | 3,168 | 6.49 |
| 2026-03-24 | Feb 2026 | api | 2,297 | 9.71 |
| 2026-03-24 | Feb 2026 | claude_ai | 3,258 | 7.03 |
| 2026-06-26 | Apr 2026 | api | 1,992 | 18.87 |
| 2026-06-26 | May 2026 | api | 2,295 | 15.00 |
| 2026-06-26 | Apr 2026 | claude_ai | 2,410 | 11.60 |
| 2026-06-26 | May 2026 | claude_ai | 2,713 | 5.68 |

The original taxonomy has 19,530 O*NET tasks (arXiv 2503.04761, p.18). Only tasks above the privacy threshold are published, so lower counts are expected and not a mismatch.

## 5. Claimed vs. actual

**Match** = within 0.5 pp of the claimed figure. Every claim is a rounded number, so 0.5 pp is the widest gap that still rounds to it.

| Release | Platform | Measure | Report says | Claimed | Actual | Diff (pp) | Status |
|:--|:--|:--|:--|--:|--:|--:|:--|
| 2025-09-15 | claude_ai | automation (all) | 49.1% automation | 49.1 | 49.10 | 0.00 | Match |
| 2025-09-15 | claude_ai | augmentation (all) | 47.0% augmentation | 47.0 | 47.04 | 0.04 | Match |
| 2025-09-15 | claude_ai | directive | directive rose from 27% to 39% (arXiv 2511.15080) | 39.0 | 38.78 | 0.22 | Match |
| 2025-09-15 | api | automation (all) | 77% of API transcripts show automation | 77.0 | 77.37 | 0.37 | Match |
| 2025-09-15 | api | augmentation (all) | 12% augmentation | 12.0 | 12.41 | 0.41 | Match |
| 2026-01-15 | claude_ai | automation (all) | automated fell 4pp to 45% | 45.0 | 45.36 | 0.36 | Match |
| 2026-01-15 | claude_ai | augmentation (all) | augmented jumped 5pp to 52% | 52.0 | 51.68 | 0.32 | Match |
| 2026-01-15 | claude_ai | directive | directive fell 7pp to 32% | 32.0 | 31.73 | 0.27 | Match |
| 2026-01-15 | api | automation (all) | three-quarters automation | 75.0 | 74.61 | 0.39 | Match |
| 2026-01-15 | claude_ai | top 10 tasks | top 10 tasks = 24% of conversations | 24.0 | 24.25 | 0.25 | Match |
| 2026-01-15 | api | top 10 tasks | top ten tasks = 32% of traffic | 32.0 | 32.14 | 0.14 | Match |
| 2026-03-24 | claude_ai | top 10 tasks | top 10 tasks went from 24% to 19% | 19.0 | 19.44 | 0.44 | Match |
| 2026-03-24 | api | top 10 tasks | top 10 tasks 33% of traffic, up from 28% | 33.0 | 32.57 | 0.43 | Match |

Directional claims (the report states only the direction of change):

| Report says | Platform | Before (Nov 2025) | After (Feb 2026) | Change (pp) | Status |
|:--|:--|--:|--:|--:|:--|
| 2026-03-24: Claude.ai augmentation increased slightly | claude_ai | 51.68 | 52.79 | +1.11 | Match |
| 2026-03-24: automation decreased sharply on the 1P API | api | 74.61 | 67.63 | −6.98 | Match |

**Sample sizes.** The reports say 1M per platform.
- **Weekly releases:** the published `collaboration_count` rows add up to the number of records. Feb 2026 is exactly 1,000,000 on both platforms. The earlier files fall short: 944,638 (API, Aug 2025), 964,494 (Claude.ai, Aug 2025), 971,525 (API, Nov 2025) and 999,875 (Claude.ai, Nov 2025). The likeliest explanation is records dropped after sampling (e.g. filtered traffic), but no documentation says so.
- **Monthly release:** only shares are published, so its sample size cannot be checked at all.

## 6. Findings from verification

- **Every headline check matches** within 0.5 pp, including both directional claims and the "over 3,000 tasks" claim (3,168).
- **Two automation definitions:**
  - The reports use the share of **all** conversations: Claude.ai 49.10%, API 77.37% in Aug 2025.
  - This project's comparisons use the share of **classified** conversations: 51.07% and 86.17%. That keeps changes in "none" from leaking in; the API's "none" share ranges from 5.5% to 15.2%.
  - The first claimed-vs-actual table compared the wrong definition for Claude.ai. Corrected above.
- **Inconsistent baseline in the 2026-03-24 report:** its API "up from 28%" matches Aug 2025 (27.61%), not Nov 2025 (32.14%). Its Claude.ai baseline (24%) is Nov 2025.
- **Mislabelled file:** the 2026-01-15 report says Free, Pro and Max, but the file labels the sample "Claude AI (Free and Pro)".
- **Date labels:** the 2026-06-26 report says sampling ran 2026-04-10 to 2026-06-10, but the file labels the periods as calendar months.
- **Published buckets reproduce:** recomputing the 2026-06-26 `collaboration_bucket_automation_pct` from the five patterns gives the same value within rounding (93.67 vs 93.66).
- **The task taxonomy breaks between regimes.** "Search electronic sources ... for information" goes from 0.10% of API usage (Feb 2026) to 5.72% (May 2026) and becomes #1 on both platforms. The top software task falls from 8.10% to 0.34% (see §8).
- **Claude Code drives API task mix.** "Computer and Mathematical" falls from 51.6% of API usage (Feb 2026, Claude Code included) to 30.8% (May 2026, excluded).

## 7. Open questions investigated

**Did earlier API files include Claude Code?**
- Yes for 2026-03-24: its footnote 2 says the API data "includes data from Claude Code", and that Claude Code's design splits coding work into smaller API calls labelled as separate tasks.
- The 2025-09-15 and 2026-01-15 reports and documentation don't mention Claude Code.
- The story is consistent: as Claude Code grew, API automation fell (classified: 86.2 → 83.9 → 79.8%, and the 2026-03-24 report calls the drop "sharp"). Removing Claude Code in 2026-06-26 sent it back up to 93.7%.
- So the 14-point June jump is mainly a change in who is sampled, not in behavior. It also means the weekly-release API trend partly reflects Claude Code's growing share.

**Did anything else change in 2026-06-26?**
- **Sampling:** continuous daily sampling, aggregated monthly, instead of seven-day samples. Only shares are published, with no counts.
- **Scope:** Claude.ai adds Cowork; the API excludes Claude Code.
- **Classifier:** a new artifact classifier was added, and the collaboration classifier's model isn't stated.
- **Taxonomy:** task IDs match the 2010 O*NET reference for only ~78% of tasks. The 2026-03-24 report had already moved to 2019 O*NET-SOC codes.
- **Privacy thresholds:** cells are published only above "aggregation thresholds" and a "geography sample floor", with no numbers given. Earlier documentation gives 200 conversations per country and 100 per US state.
- The 2026-06-26 report gives no warning about comparability with earlier releases.

## 8. Raw examples (`src/raw_examples.py`)

The data is aggregated, so each example is a slice of rows.

1. **The new #1 task, May 2026 (task 16221, "Search electronic sources ... for information").**
   - It is 5.72% of API usage and 4.95% of Claude.ai usage, #1 on both platforms.
   - Automation is 96.96% on the API (directive 88.98%) vs. 67.16% on Claude.ai, where learning (17.54%) and task iteration (12.72%) are much higher.
   - In Feb 2026 the same task was only 0.10% of API usage (1,039 records), a 50× jump in one release. A jump that size points to a change in how conversations are mapped to tasks, not in what people do.

2. **Top software task, Aug 2025 vs. May 2026 ("Modify existing software to correct errors ...").**
   - Aug 2025: 8.10% of API usage (76,473 records) and 3.82% of Claude.ai usage.
   - May 2026: 0.34% and 0.19%. Its share collapsed, consistent with Claude Code being removed and the taxonomy changing.
   - Automation within the task barely moved: API 86.9% → 82.7%, Claude.ai 69.6% → 71.1% (classified). The gap within this task (12–17 pp) is much smaller than the overall gap (35–46 pp).
   - Feedback loop is unusually large here on both platforms (25–44%), which fits debugging as an iterative task.

3. **API global collaboration rows, Feb 2026 vs. Apr 2026.**
   - Feb: counts add up to exactly 1,000,000; none is 15.19% (151,944 records). This is the only file with no `not_classified` category.
   - Apr: only shares; directive 80.88% (up 22.7 pp) and none 5.73% (down 9.5 pp).
   - A change that large two months apart on the same platform is much more plausible as a change in coverage (Claude Code) than in behavior.

4. **United States (country) vs. California (subregion), Claude.ai, May 2026.**
   - Automation: US 49.59%, California 48.00%, both close to the global 48.62%. Directive ~31.5% for both.
   - Usage index: US 3.87, California 1.62. The California figure only makes sense as relative to the US (California is 19.25% of US usage), which suggests subregion metrics are measured against their country.
   - Geography barely moves automation, which supports leaving geography out of the profile.

5. **California, Claude.ai, Aug 2025 (state_us rows).**
   - "None" is 22.5% of California's 52,617 records, against a median of 2.3% across states and 3.9% globally. Directive is 32.8% and feedback loop only 6.2%.
   - This looks like a large block of non-collaborative traffic, perhaps scripted use, that week. The 2026-01-15 report excluded Wyoming and Seychelles for abusive traffic, so state-level automation in this release needs care.

6. **ai_autonomy, global, Nov 2025.**
   - Mean AI autonomy is 2.84 on the API (median 3) vs. 3.38 on Claude.ai (median 4). The 95% intervals are about ±0.002.
   - Odd: the platform with far more automation by collaboration pattern has *lower* AI autonomy. The two measures don't capture the same idea, so the definitions need checking before using either as a robustness check.
   - The histogram bins are labelled "[1.0, 1.0)", an empty interval, which is a formatting quirk.

7. **Tasks mostly on one platform (Feb 2026).**
   - API-heavy: "perform system analysis, data analysis or programming ..." is 0.37% of API usage vs. 0.009% on Claude.ai. On the API, 35% of its conversations are "none". On Claude.ai only directive and learning are published and 21.8% of records are not_classified, because the cell is small.
   - Claude.ai-heavy: "instruct individuals in career development techniques ..." is 1.20% vs. 0.04%.
   - 539 tasks are API-only and 842 are Claude.ai-only that week. Task-level comparisons can only use the ~1,358 shared tasks, and the smallest of those are mostly hidden detail.

8. **Editing task across releases ("prepare, rewrite and edit copy to improve readability ...").**
   - Aug 2025: API directive 86.7% vs. Claude.ai directive 39.7% and task iteration 54.6%.
   - Feb 2026: API directive 81.8% vs. Claude.ai directive 30.5% and task iteration 63.8%.
   - The same task shows a persistent ~50 pp difference in style. Feedback loop is near zero on both, so for this task the gap is purely one-shot delegation vs. iterating.
   - It also fits the measurement asymmetry: a single API prompt–response pair cannot show iteration.

9. **GLOBAL, 1P API, collaboration, collaboration_pct, cluster_name="directive", Aug 2025.** This row reports what share of API conversations fell into the "directive" pattern globally between 2025-08-04 and 2025-08-11 (66.30%). It makes sense as a proportion, since a matching `_count` row (626,255) sits right above it with the same cluster_name.

10. **ABW, country, gdp_per_working_age_capita, value blank (2025-09-15 enriched file, no longer used).** Aruba's rows for this and several other variables are empty, although the country appears with usage_tier "Minimal". The documentation confirms this is suppression:
    - 2025-09-15 documentation: a minimum of 200 conversations per country, applied in enrichment.
    - 2026-06-26 documentation: a missing row means the cell was not published, not that the value is zero.
