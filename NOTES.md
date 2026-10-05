Dataset:
Source: Anthropic Economic Index, https://huggingface.co/datasets/Anthropic/EconomicIndex (primary source, Anthropic's own Hugging Face repo). Four releases are used so the API vs. Claude.ai automation gap can be tracked over time. Release definitions live in src/releases.py.

1. the exact URL,
   - 2025-09-15: https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2025_09_15/data/intermediate/aei_raw_1p_api_2025-08-04_to_2025-08-11.csv, https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2025_09_15/data/intermediate/aei_raw_claude_ai_2025-08-04_to_2025-08-11.csv
   - 2026-01-15: https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2026_01_15/data/intermediate/aei_raw_1p_api_2025-11-13_to_2025-11-20.csv, https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2026_01_15/data/intermediate/aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv
   - 2026-03-24: https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2026_03_24/data/aei_raw_1p_api_2026-02-05_to_2026-02-12.csv, https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2026_03_24/data/aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv
   - 2026-06-26: https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2026_06_26/data/aei_1p_api_2026-06-26.csv, https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv
2. the version or release you downloaded,
   - 2025-09-15 Release: Updated analysis with geographic and first-party API data using Sonnet 4
   - 2026-01-15 Release: Updated analysis with economic primitives and Sonnet 4.5
   - 2026-03-24 Release: Updated analysis with Opus 4.5/4.6 and learning curves
   - 2026-06-26 Release: Updated analysis with Artifacts and monthly aggregates
3. the download date, 2025-09-15 release first downloaded 13/09/2026 (the enriched Claude.ai file); all eight files above (re)downloaded 05/10/2026. The 2025-09-15 Claude.ai file is now the raw (intermediate) file instead of the enriched one, so all three older releases use the same raw format.
4. the license, Data released under CC-BY, code released under MIT License.
5. and the citation the authors ask for.
   - 2025-09-15: @online{appelmccrorytamkin2025geoapi, author = {Ruth Appel and Peter McCrory and Alex Tamkin and Michael Stern and Miles McCain and Tyler Neylon}, title = {Anthropic Economic Index Report: Uneven Geographic and Enterprise AI Adoption}, date = {2025-09-15}, year = {2025}, url = {www.anthropic.com/research/anthropic-economic-index-september-2025-report}, }
   - 2026-01-15: @online{anthropic2026aeiv4, author = {Ruth Appel and Maxim Massenkoff and Peter McCrory and Miles McCain and Ryan Heller and Tyler Neylon and Alex Tamkin}, title = {Anthropic Economic Index report: economic primitives}, date = {2026-01-15}, year = {2026}, url = {https://www.anthropic.com/research/anthropic-economic-index-january-2026-report}, }
   - 2026-03-24: @online{anthropic2026aeiv5, author = {Maxim Massenkoff and Eva Lyubich and Peter McCrory and Ruth Appel and Ryan Heller}, title = {Anthropic Economic Index report: Learning curves}, date = {2026-03-24}, year = {2026}, url = {https://www.anthropic.com/research/economic-index-march-2026-report}, }
   - 2026-06-26: @online{anthropic2026aeiv6, author = {Maxim Massenkoff and Eva Lyubich and Szymon Sacher and Zoe Hitzig and Shaoyi Zhang and Ryan Heller and Peter McCrory}, title = {Anthropic Economic Index report: Cadences}, date = {2026-06-26}, year = {2026}, url = {https://www.anthropic.com/research/economic-index-june-2026-report}, }

Dataset Summary
1. how the data was collected, Each release samples Claude.ai conversations and first-party (1P) API transcripts and analyses them with Clio, an automated, privacy-preserving analysis framework powered by Claude itself. Each conversation is mapped onto the US Department of Labor's O*NET task taxonomy.
   - 2025-09-15: one week, Aug 4–11 2025; ~1M Claude.ai Free and Pro conversations + ~1M API transcripts.
   - 2026-01-15: one week, Nov 13–20 2025; 1M Claude.ai Free, Pro and Max conversations + 1M API transcripts.
   - 2026-03-24: one week, Feb 5–12 2026; 1M Claude.ai conversations + 1M API transcripts.
   - 2026-06-26: calendar-month aggregates for April and May 2026. Claude.ai now covers chat and Cowork (Free, Pro and Max); the API file excludes Claude Code. The report says the conversations were sampled between April 10 and June 10, 2026.
2. the unit of observation (a row = what, exactly?),
   - Releases 2025-09-15 to 2026-03-24 (raw format): one row = one metric value (`variable`, e.g. collaboration_pct) for one facet value (`cluster_name`, e.g. "directive") in one geography, for the sampled week. API is global only; Claude.ai is global / country / US state (2025-09-15) or country-state (later).
   - Release 2026-06-26 (monthly format): one row = one metric value (`metric_id`) for one geography (`geo_id`), one category node (`category_name` + `node_name`/`node_external_id` at `hierarchy_level`), for one calendar month (`date_start`). Collaboration patterns are now their own metric_ids (collaboration_directive_pct, ...) rather than cluster_name values.
3. how any labels were produced, Clio classifies each conversation into one of five collaboration patterns: Directive and Feedback Loop (grouped as automation), and Task Iteration, Learning, and Validation (grouped as augmentation), plus "none" when no pattern applies. This classification was human-validated in the original paper: 90.7% agreement with human raters on a 150-example sample. The 2026-06-26 release publishes the grouped buckets directly (collaboration_bucket_automation_pct / _augmentation_pct, renormalized over classified conversations).
4. and 2–3 headline numbers the authors report (sizes, counts, baseline scores).
   - 2025-09-15: ~1M Claude.ai conversations and ~1M API transcripts, mapped across ~20k O*NET tasks (19,530, original paper p.18). Claude.ai 49.1% automation vs. 47.0% augmentation; 77% of API transcripts show automation patterns (12% augmentation).
   - 2026-01-15: Claude.ai augmented share "jumped 5pp to 52%", automated "fell 4pp to 45%"; directive "fell 7pp to 32%"; API about three-quarters automation. Top 10 tasks = 24% of Claude.ai conversations and 32% of API traffic; over 3,000 unique work tasks on Claude.ai.
   - 2026-03-24: Claude.ai augmentation "increased slightly"; top 10 tasks went from 24% to 19% of Claude.ai conversations; on the API, top 10 tasks 33% of traffic "up from 28%".
   - 2026-06-26: no headline automation/augmentation number. Personal use is ~35% of chat and Cowork conversations on weekdays and just under 50% on weekends.

======================================================================

INVENTORY (src/inventory.py)

======================================================================
| Release    | Platform   | File                                           |    MB |    Rows |
|:-----------|:-----------|:-----------------------------------------------|------:|--------:|
| 2025-09-15 | api        | aei_raw_1p_api_2025-08-04_to_2025-08-11.csv    |   6.7 |   33794 |
| 2025-09-15 | claude_ai  | aei_raw_claude_ai_2025-08-04_to_2025-08-11.csv |  18   |  100062 |
| 2026-01-15 | api        | aei_raw_1p_api_2025-11-13_to_2025-11-20.csv    |  39.6 |  187772 |
| 2026-01-15 | claude_ai  | aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv |  89.7 |  458778 |
| 2026-03-24 | api        | aei_raw_1p_api_2026-02-05_to_2026-02-12.csv    |  41.9 |  195156 |
| 2026-03-24 | claude_ai  | aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv |  98.5 |  477717 |
| 2026-06-26 | api        | aei_1p_api_2026-06-26.csv                      |  73.7 |  491705 |
| 2026-06-26 | claude_ai  | aei_claude_ai_2026-06-26.csv                   | 209   | 1636573 |

Missing values: the 2026-06-26 files have no missing values in any column. In the raw files only geo_id (≤0.02%) and cluster_name are ever blank; cluster_name is blank for 10.6% (Nov) and 11.6% (Feb) of Claude.ai rows because facets like ai_autonomy are numeric means with no category.

======================================================================

CLAIMED VS. ACTUAL

======================================================================
"Automation (all)" = directive + feedback loop as a share of ALL conversations, which is how the reports state their headline numbers.
| Release    | Platform   | Measure          | Report says                              |   Claimed |   Actual |   Diff (pp) | Status   |
|:-----------|:-----------|:-----------------|:-----------------------------------------|----------:|---------:|------------:|:---------|
| 2025-09-15 | claude_ai  | automation_raw   | 49.1% automation                         |      49.1 |    49.1  |        0    | Match    |
| 2025-09-15 | claude_ai  | augmentation_raw | 47.0% augmentation                       |      47   |    47.04 |        0.04 | Match    |
| 2025-09-15 | api        | automation_raw   | 77% of API transcripts show automation   |      77   |    77.37 |        0.37 | Match    |
| 2025-09-15 | api        | augmentation_raw | 12% augmentation                         |      12   |    12.41 |        0.41 | Match    |
| 2026-01-15 | claude_ai  | automation_raw   | automated fell 4pp to 45%                |      45   |    45.36 |        0.36 | Match    |
| 2026-01-15 | claude_ai  | augmentation_raw | augmented jumped 5pp to 52%              |      52   |    51.68 |        0.32 | Match    |
| 2026-01-15 | claude_ai  | directive        | directive fell 7pp to 32%                |      32   |    31.73 |        0.27 | Match    |
| 2026-01-15 | api        | automation_raw   | three-quarters automation                |      75   |    74.61 |        0.39 | Match    |
| 2026-01-15 | claude_ai  | top10_tasks      | top 10 tasks = 24% of conversations      |      24   |    24.25 |        0.25 | Match    |
| 2026-01-15 | api        | top10_tasks      | top ten tasks = 32% of traffic           |      32   |    32.14 |        0.14 | Match    |
| 2026-03-24 | claude_ai  | top10_tasks      | top 10 tasks went from 24% to 19%        |      19   |    19.44 |        0.44 | Match    |
| 2026-03-24 | api        | top10_tasks      | top 10 tasks 33% of traffic, up from 28% |      33   |    32.57 |        0.43 | Match    |

Distinct O*NET tasks with published shares (target: 19,530 total O*NET tasks, original paper p.18). Only tasks above the privacy threshold appear, so lower counts are expected rather than a mismatch:
| Release    | Period     | Claude.ai | API   |
|:-----------|:-----------|----------:|------:|
| 2025-09-15 | Aug 2025   |     2,616 | 2,054 |
| 2026-01-15 | Nov 2025   |     3,168 | 2,251 |
| 2026-03-24 | Feb 2026   |     3,258 | 2,297 |
| 2026-06-26 | Apr 2026   |     2,410 | 1,992 |
| 2026-06-26 | May 2026   |     2,713 | 2,295 |

Findings from the verification:
- Every headline number checked is within 0.5 pp of the data. Claude.ai 2026-01-15 ("over 3,000 unique work tasks") also matches: 3,168 tasks.
- Correction to the earlier table: it compared the Claude.ai share of *classified* conversations (51.07 / 48.93) against the report's share of *all* conversations. Measured the same way as the report, Claude.ai is an exact match (49.10 / 47.04). The API numbers were already measured the same way.
- The 2026-03-24 report's API baseline ("up from 28%") matches the Aug 2025 sample (27.61%), not the Nov 2025 sample the 2026-01-15 report gave (32.14%). Its Claude.ai baseline (24%) is Nov 2025. The two comparisons in that report use different baselines.
- The 2026-01-15 report says the sample is Free, Pro and Max, but the Nov 2025 file's platform_and_product says "Claude AI (Free and Pro)". Max first appears in the file label in the Feb 2026 release.
- The 2026-06-26 report says sampling ran April 10 – June 10, 2026, but the files are labelled with calendar months (date_start 2026-04-01 / 2026-05-01).
- In the 2026-06-26 release, global O*NET task shares sum to only 81–94% (vs. 88–94% in the raw files), because unpublished cells are missing rows, not zeros. The most common tasks also change: software tasks led every earlier release, but now "Search electronic sources ... for information" is #1 on both platforms. Task-level comparisons across this release boundary need care.
- The 2026-06-26 release publishes collaboration_bucket_automation_pct directly. Recomputing it from the five pattern metrics reproduces it to within 0.01 pp (93.67 vs 93.66 API Apr; 48.98 vs 48.98 Claude.ai Apr).


Raw Examples:
Row: GLOBAL, 1P API, collaboration, collaboration_pct, cluster_name="directive" — This row reports what share of API collaboration-classified conversations fell into the "directive" interaction pattern globally between 04/08/2025–11/08/2025. It makes sense as a proportion since there's a matching _count row right above it with the same cluster_name. 
Row: ABW, country, gdp_per_working_age_capita — value blank — Aruba's row for this variable, and several others (usage_count, usage_per_capita), is empty despite the country existing in the table with a usage_tier of "Minimal." This is likely a suppression rule for small-sample geographies rather than a true missing value. (This row is from the 2025-09-15 enriched file, which is no longer used. The 2026-06-26 data_documentation.md confirms the rule: a cell is published only if it meets both the aggregation thresholds and the geography's sample floor, and a missing row means the cell was not published, not that the value is zero.)
