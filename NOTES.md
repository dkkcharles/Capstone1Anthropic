Dataset: 
1. the exact URL, (https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2025_09_15/data/intermediate/aei_raw_1p_api_2025-08-04_to_2025-08-11.csv), https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2025_09_15/data/output/aei_enriched_claude_ai_2025-08-04_to_2025-08-11.csv
2. the version or release you downloaded, 2025-09-15 Release: Updated analysis with geographic and first-party API data using Sonnet 4
3. the download date, 13/09/2026
4. the license, Data released under CC-BY, code released under MIT License.
5. and the citation the authors ask for. ### Third release @online{appelmccrorytamkin2025geoapi, author = {Ruth Appel and Peter McCrory and Alex Tamkin and Michael Stern and Miles McCain and Tyler Neylon}, title = {Anthropic Economic Index Report: Uneven Geographic and Enterprise AI Adoption}, date = {2025-09-15},   year = {2025}, url = {www.anthropic.com/research/anthropic-economic-index-september-2025-report}, }

Dataset Summary
1. how the data was collected, The data was collected during August 2025 and consists of snapshots of Claude.ai Free and Pro conversations. The authors used Clio, an automated analysis framework powered by Claude itself, to analyze the conversations in manner to preserve privacy. This was combined with the US Department of Labor's O*NET task taxonomy to map each interaction onto a specific occupational task.
2. the unit of observation (a row = what, exactly?), Each row represents one metric value for a specific facet combination at global level (for API) or at global/country/subregion level (for Claude.ai).
3. how any labels were produced, Clio classifies each conversation into one of five collaboration patterns: Directive and Feedback Loop (grouped as automation), and Task Iteration, Learning, and Validation (grouped as augmentation). This classification was human-validated in the original paper: 90.7% agreement with human raters on a 150-example sample.
4. and 2–3 headline numbers the authors report (sizes, counts, baseline scores). 1 million privacy preserved Claude.ai web coversations and 1 million first party API transcripts were analysed and mapped across ~20k distinct O*NET occupational tasks. 49.1% automation vs. 47.0% augmentation,77% of API transcripts show automation patterns vs. ~50% for Claude.ai, 97% of API tasks vs. 47% of Claude.ai tasks

======================================================================
CLAIMED VS. ACTUAL -- copy into NOTES.md
======================================================================
| Platform   | Metric           |   Claimed |   Actual |   Diff (pp) | Status   |
|:-----------|:-----------------|----------:|---------:|------------:|:---------|
| claude_ai  | automation_pct   |      49.1 |    51.07 |        1.97 | Match    |
| claude_ai  | augmentation_pct |      47   |    48.93 |        1.93 | Match    |
| api        | automation_pct   |      77   |    77.37 |        0.37 | Match    |
| api        | augmentation_pct |      12   |    12.41 |        0.41 | Match    |