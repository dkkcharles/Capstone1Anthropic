"""
raw_examples.py

Prints the raw rows behind each Step 5 example in NOTES.md, so every
impression written there can be traced back to the exact slice of data.
The data is aggregated, so an "example" is a slice: one task, one
geography or one global row, read across platforms and/or releases.

Run from the repo root:  python src/raw_examples.py
"""

import pandas as pd

from releases import RELEASES, load

pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 90)

REL = {r["release"]: r for r in RELEASES}
COLLAB_PCT = ["collaboration_directive_pct", "collaboration_feedback_loop_pct",
              "collaboration_task_iteration_pct", "collaboration_learning_pct",
              "collaboration_validation_pct", "collaboration_none_pct",
              "collaboration_bucket_automation_pct"]


def raw_task(df, task_substring, facet="onet_task"):
    """Raw schema: global rows for one task (matched on the start of the
    lower-cased statement), its overall share and collaboration breakdown."""
    rows = df[(df["geography"] == "global") & df["facet"].isin([facet, f"{facet}::collaboration"])
              & df["cluster_name"].str.startswith(task_substring, na=False)]
    return rows[["facet", "variable", "cluster_name", "value"]]


def monthly_task(df, name_substring, month):
    rows = df[(df["geo_id"] == "GLOBAL") & (df["category_name"] == "onet")
              & (df["hierarchy_level"] == 0) & (df["date_start"] == month)
              & df["node_name"].str.contains(name_substring, case=False, regex=False)
              & df["metric_id"].isin(["pct"] + COLLAB_PCT)]
    wide = rows.pivot_table(index="metric_id", columns=["node_external_id", "node_name"], values="value")
    wide.columns = [f"{i}: {n[:60]}" for i, n in wide.columns]
    return wide


def show(title, frame):
    print(f"\n{'=' * 90}\n{title}\n{'=' * 90}")
    print(frame.to_string() if len(frame) else "  (no published rows)")


def main():
    raw = {(r, p): load(REL[r]["files"][p]) for r in ["2025-09-15", "2026-01-15", "2026-03-24"]
           for p in ["api", "claude_ai"]}
    monthly = {p: load(REL["2026-06-26"]["files"][p]) for p in ["api", "claude_ai"]}

    # 1. The new #1 task in the monthly release, on both platforms.
    for p in ["api", "claude_ai"]:
        show(f"1. 'Search electronic sources' task, May 2026, {p}",
             monthly_task(monthly[p], "Search electronic sources", "2026-05-01"))
    show("1b. Same task in the Feb 2026 weekly release (api)",
         raw_task(raw[("2026-03-24", "api")], "search electronic sources"))

    # 2. Top software task: Aug 2025 (weekly) vs. May 2026 (monthly).
    sw = "modify existing software to correct errors, allow it to adapt"
    for p in ["api", "claude_ai"]:
        show(f"2. Top software task, Aug 2025, {p}", raw_task(raw[("2025-09-15", p)], sw))
        show(f"2b. Same task, May 2026, {p}",
             monthly_task(monthly[p], "Modify existing software to correct errors, allow it", "2026-05-01"))

    # 3. API global collaboration rows: Feb 2026 (weekly) vs. Apr 2026 (monthly).
    df = raw[("2026-03-24", "api")]
    show("3. API global collaboration rows, Feb 2026",
         df[(df["geography"] == "global") & (df["facet"] == "collaboration")]
         [["variable", "cluster_name", "value"]])
    df = monthly["api"]
    show("3b. API global collaboration rows, Apr 2026",
         df[(df["geo_id"] == "GLOBAL") & (df["category_name"] == "overall")
            & (df["date_start"] == "2026-04-01") & df["metric_id"].str.startswith("collaboration_")]
         [["metric_id", "value"]])

    # 4. One country row and one US state row.
    df = monthly["claude_ai"]
    keep = ["usage_pct", "usage_per_capita_index", "collaboration_bucket_automation_pct",
            "collaboration_directive_pct", "collaboration_none_pct",
            "use_case_work_pct", "use_case_personal_pct", "ai_autonomy_mean"]
    show("4. United States (country) and California (subregion), Claude.ai, May 2026",
         df[df["geo_id"].isin(["USA", "US-CA"]) & (df["category_name"] == "overall")
            & (df["date_start"] == "2026-05-01") & df["metric_id"].isin(keep)]
         .pivot_table(index="metric_id", columns="geo_id", values="value"))
    df = raw[("2025-09-15", "claude_ai")]
    show("4b. California, Claude.ai, Aug 2025 (state_us rows)",
         df[(df["geo_id"] == "CA") & (df["geography"] == "state_us")]
         [["facet", "variable", "cluster_name", "value"]].head(12))

    # 5. An ai_autonomy row (introduced in the 2026-01-15 release).
    for p in ["api", "claude_ai"]:
        df = raw[("2026-01-15", p)]
        show(f"5. ai_autonomy, global, Nov 2025, {p}",
             df[(df["geography"] == "global") & (df["facet"] == "ai_autonomy")]
             [["variable", "cluster_name", "value"]])

    # 6. A task that is API-heavy but rare on Claude.ai, and the reverse (Feb 2026).
    api_s = raw[("2026-03-24", "api")]
    cai_s = raw[("2026-03-24", "claude_ai")]
    def shares(df):
        r = df[(df["geography"] == "global") & (df["facet"] == "onet_task")
               & (df["variable"] == "onet_task_pct")
               & ~df["cluster_name"].isin(["none", "not_classified"])]
        return r.set_index("cluster_name")["value"]
    both = pd.DataFrame({"api": shares(api_s), "claude_ai": shares(cai_s)}).fillna(0)
    both["ratio"] = (both["api"] + 0.01) / (both["claude_ai"] + 0.01)
    big = both[(both["api"] > 0.3) | (both["claude_ai"] > 0.3)]
    show("6. API-heavy tasks (Feb 2026, highest API/Claude.ai ratio)", big.nlargest(3, "ratio").round(3))
    show("6b. Claude.ai-heavy tasks (Feb 2026, lowest ratio)", big.nsmallest(3, "ratio").round(3))
    show("6c. Collaboration for the top API-heavy task, both platforms",
         pd.concat([raw_task(api_s, big.nlargest(1, "ratio").index[0][:60]).assign(platform="api"),
                    raw_task(cai_s, big.nlargest(1, "ratio").index[0][:60]).assign(platform="claude_ai")]))

    # 7. A writing / editing task across releases.
    edit = "prepare, rewrite and edit copy"
    for r in ["2025-09-15", "2026-03-24"]:
        for p in ["api", "claude_ai"]:
            show(f"7. Editing task, {r}, {p}", raw_task(raw[(r, p)], edit))


if __name__ == "__main__":
    main()
