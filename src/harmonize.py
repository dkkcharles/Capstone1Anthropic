"""
harmonize.py

Builds one harmonized task-level panel from all four releases: one row per
task x platform x period, with the same variable names, definitions and
units in both schemas. This is the dataset the regression uses.

  data/processed/task_panel.csv   (git-ignored; rebuild with this script)

Columns
  release, regime, period, period_start, platform
  task_key        normalized task statement (lower-case, single spaces). The
                  join key across releases: weekly files identify tasks by
                  statement, the monthly file by Task ID, and only ~78% of
                  monthly IDs exist in the 2010 O*NET reference.
  task_id         O*NET Task ID where known (monthly file; reference lookup)
  major_group     SOC major group (reference lookup; monthly falls back to
                  Task ID when the statement does not match)
  usage           task share of the platform's conversations in the period (%)
  directive ... validation
                  each pattern as % of the task's CLASSIFIED conversations
                  (none and not_classified excluded; the five sum to 100)
  automation_pct  directive + feedback loop (classified definition)
  none_pct        "none" as % of the task's conversations incl. none
  classified_n    classified record count (weekly releases only)
  ai_autonomy, human_education_years, ai_education_years
                  per-task means (1-5 scale; years; years)
  human_only_time (hours), human_with_ai_time (minutes)
  multitasking_pct, human_only_ability_pct
                  % "yes" among classified conversations for the task
  use_case_work_pct, use_case_personal_pct, use_case_coursework_pct
                  % among classified use-case conversations for the task
  on_both_platforms  task published on both platforms in the same period
  in_both_regimes    task_key appears in a weekly AND the monthly release

Units: the 2026-06-26 documentation gives human_only_time in hours and
human_with_ai_time in minutes. The weekly-release documentation gives no
units; their global means (Claude.ai Feb 2026: 3.06 and 14.3) are consistent
with the same units, so the same units are assumed.

Run from the repo root:  python src/harmonize.py
"""

from pathlib import Path
import numpy as np
import pandas as pd

from releases import (
    RELEASES, PLATFORMS, DATA_DIR, ONET_REFERENCE, SOC_MAJOR_GROUPS, AUTOMATION_PATTERNS,
    AUGMENTATION_PATTERNS, NON_TASKS, load, period_label, onet_task_shares, task_patterns,
    task_mean,
)

OUT = DATA_DIR / "processed" / "task_panel.csv"
FIVE = AUTOMATION_PATTERNS + AUGMENTATION_PATTERNS
MEANS = ["ai_autonomy", "human_education_years", "ai_education_years",
         "human_only_time", "human_with_ai_time"]
# (output column, raw facet, raw "yes" category(ies), raw denominator categories, monthly metric)
SHARES = [
    ("multitasking_pct", "multitasking", ["yes"], ["yes", "no"], "multitasking_pct"),
    ("human_only_ability_pct", "human_only_ability", ["yes"], ["yes", "no"], "human_only_ability_pct"),
    ("use_case_work_pct", "use_case", ["work"], ["work", "personal", "coursework"], "use_case_work_pct"),
    ("use_case_personal_pct", "use_case", ["personal"], ["work", "personal", "coursework"], "use_case_personal_pct"),
    ("use_case_coursework_pct", "use_case", ["coursework"], ["work", "personal", "coursework"], "use_case_coursework_pct"),
]


def normalize(text: pd.Series) -> pd.Series:
    return text.str.lower().str.strip().str.replace(r"\s+", " ", regex=True)


def reference() -> tuple:
    """(statement -> major group, Task ID -> major group, statement -> Task ID).
    A statement shared by several occupations gets its most common major group."""
    ref = pd.read_excel(ONET_REFERENCE)
    ref["task_key"] = normalize(ref["Task"])
    ref["major_group"] = ref["O*NET-SOC Code"].str[:2].map(SOC_MAJOR_GROUPS)
    ref["task_id"] = ref["Task ID"].astype(str)
    by_text = ref.groupby("task_key")["major_group"].agg(lambda s: s.mode().iloc[0])
    by_id = ref.drop_duplicates("task_id").set_index("task_id")["major_group"]
    text_to_id = ref.groupby("task_key")["task_id"].first()
    return by_text, by_id, text_to_id


def raw_shares(df: pd.DataFrame, release: dict) -> dict:
    """{period: DataFrame of SHARES columns} for the raw schema, from the
    onet_task::<facet> count rows (not_classified excluded)."""
    out = {}
    g = df[(df["geography"] == "global") & df["facet"].str.startswith("onet_task::")
           & df["variable"].str.endswith("_count")]
    for col, facet, yes, denom, _ in SHARES:
        rows = g[g["facet"] == f"onet_task::{facet}"]
        if rows.empty:  # 2025-09-15 has no economic-primitive facets
            continue
        split = rows["cluster_name"].str.rsplit("::", n=1, expand=True)
        rows = rows.assign(task=split[0], cat=split[1])
        for start, r in rows.groupby("date_start"):
            counts = r.pivot_table(index="task", columns="cat", values="value", aggfunc="sum",
                                   fill_value=0).reindex(columns=denom, fill_value=0)
            total = counts.sum(axis=1)
            share = (counts[yes].sum(axis=1) / total * 100).where(total > 0)
            out.setdefault(period_label(release, start), {})[col] = share
    return {p: pd.DataFrame(cols) for p, cols in out.items()}


def raw_none(df: pd.DataFrame, release: dict) -> dict:
    rows = df[(df["geography"] == "global") & (df["facet"] == "onet_task::collaboration")
              & (df["variable"] == "onet_task_collaboration_count")]
    split = rows["cluster_name"].str.rsplit("::", n=1, expand=True)
    rows = rows.assign(task=split[0], cat=split[1])
    out = {}
    for start, r in rows.groupby("date_start"):
        counts = r.pivot_table(index="task", columns="cat", values="value", aggfunc="sum",
                               fill_value=0).reindex(columns=FIVE + ["none"], fill_value=0)
        out[period_label(release, start)] = counts["none"] / counts.sum(axis=1) * 100
    return out


def monthly_extra(df: pd.DataFrame, release: dict) -> dict:
    """{period: DataFrame indexed by Task ID with node_name, none_pct and the
    SHARES columns} for the monthly schema."""
    rows = df[(df["geo_id"] == "GLOBAL") & (df["category_name"] == "onet")
              & (df["hierarchy_level"] == 0)]
    metrics = [m for *_, m in SHARES] + ["collaboration_none_pct"] + \
              [f"collaboration_{p.replace(' ', '_')}_pct" for p in FIVE]
    out = {}
    for start, g in rows.groupby("date_start"):
        wide = g[g["metric_id"].isin(metrics)].pivot_table(
            index="node_external_id", columns="metric_id", values="value")
        all_six = wide[[c for c in wide.columns if c.startswith("collaboration_")]].sum(axis=1)
        frame = pd.DataFrame({col: wide.get(m) for col, *_, m in SHARES})
        frame["none_pct"] = wide["collaboration_none_pct"] / all_six * 100
        frame["node_name"] = g.drop_duplicates("node_external_id").set_index("node_external_id")["node_name"]
        out[period_label(release, start)] = frame
    return out


def build() -> pd.DataFrame:
    by_text, by_id, text_to_id = reference()
    frames = []
    for release in RELEASES:
        regime = "weekly" if release["schema"] == "raw" else "monthly"
        for platform in PLATFORMS:
            df = load(release["files"][platform])
            pats = task_patterns(df, release)
            means = {m: task_mean(df, release, m) for m in MEANS}
            starts = dict(zip(pats, sorted(df["date_start"].unique())))
            if release["schema"] == "raw":
                extra, none = raw_shares(df, release), raw_none(df, release)
            else:
                extra = monthly_extra(df, release)

            for period, t in pats.items():
                t = t.copy()
                for m in MEANS:
                    t[m] = means[m].get(period, pd.Series(dtype=float)).reindex(t.index)
                if release["schema"] == "raw":
                    t = t.join(extra.get(period, pd.DataFrame(index=t.index)), how="left")
                    t["none_pct"] = none[period].reindex(t.index)
                    t["task_key"] = normalize(t.index.to_series())
                    t["task_id"] = t["task_key"].map(text_to_id)
                else:
                    t = t.join(extra[period], how="left")
                    t["task_id"] = t.index.astype(str)
                    t["task_key"] = normalize(t["node_name"])
                    t = t.drop(columns="node_name")
                t["major_group"] = t["task_key"].map(by_text)
                t["major_group"] = t["major_group"].fillna(t["task_id"].map(by_id))
                t["automation_pct"] = t["directive"] + t["feedback loop"]
                t = t.assign(release=release["release"], regime=regime, period=period,
                             period_start=starts[period], platform=platform)
                frames.append(t.reset_index(drop=True))

    panel = pd.concat(frames, ignore_index=True)
    panel = panel.rename(columns={"feedback loop": "feedback_loop", "task iteration": "task_iteration"})
    panel = panel[~panel["task_key"].isin(NON_TASKS)]

    # A statement can appear under two Task IDs in the monthly file; keep the
    # higher-usage row so task_key is unique within platform x period.
    panel = (panel.sort_values("usage", ascending=False)
             .drop_duplicates(["platform", "period", "task_key"]))

    counts = panel.groupby(["period", "task_key"])["platform"].transform("nunique")
    panel["on_both_platforms"] = counts == 2
    regimes = panel.groupby("task_key")["regime"].transform("nunique")
    panel["in_both_regimes"] = regimes == 2

    order = ["release", "regime", "period", "period_start", "platform", "task_key", "task_id",
             "major_group", "usage", "directive", "feedback_loop", "task_iteration", "learning",
             "validation", "automation_pct", "none_pct", "classified_n", *MEANS,
             *[c for c, *_ in SHARES], "on_both_platforms", "in_both_regimes"]
    return panel.reindex(columns=order).sort_values(["period_start", "platform", "usage"],
                                                   ascending=[True, True, False])


def report(panel: pd.DataFrame):
    print(f"\n{'=' * 70}\nPANEL: {len(panel):,} rows (task x platform x period)\n{'=' * 70}")
    print(panel.groupby(["release", "period", "platform"]).agg(
        tasks=("task_key", "size"), shared=("on_both_platforms", "sum"),
        usage_covered=("usage", "sum")).round(1).to_markdown())

    print(f"\n{'=' * 70}\nVARIABLE AVAILABILITY (% of rows non-missing) -- copy into NOTES.md\n{'=' * 70}")
    cols = ["major_group", "automation_pct", "none_pct", "classified_n", *MEANS,
            *[c for c, *_ in SHARES]]
    avail = panel.groupby(["release", "platform"])[cols].agg(lambda s: s.notna().mean() * 100)
    print(avail.round(0).astype(int).T.to_markdown())

    print(f"\n{'=' * 70}\nTASK LINKAGE ACROSS REGIMES\n{'=' * 70}")
    rows = []
    for (period, platform), g in panel.groupby(["period", "platform"]):
        rows.append((period, platform, len(g), g["in_both_regimes"].mean() * 100,
                     g.loc[g["in_both_regimes"], "usage"].sum() / g["usage"].sum() * 100))
    print(pd.DataFrame(rows, columns=["Period", "Platform", "Tasks", "% of tasks linked",
                                      "% of usage linked"]).round(1).to_markdown(index=False))

    print(f"\n{'=' * 70}\nMEAN OF EACH VARIABLE BY REGIME AND PLATFORM (usage-weighted)\n{'=' * 70}")
    num = ["automation_pct", "none_pct", *MEANS, *[c for c, *_ in SHARES]]
    rows = {}
    for (regime, platform), g in panel.groupby(["regime", "platform"]):
        w = g["usage"].fillna(0)
        rows[f"{regime} / {platform}"] = {c: np.average(g[c].dropna(), weights=w[g[c].notna()])
                                          if g[c].notna().any() and w[g[c].notna()].sum() > 0 else np.nan
                                          for c in num}
    print(pd.DataFrame(rows).round(2).to_markdown())


def main():
    panel = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT, index=False)
    print(f"Saved {OUT}")
    report(panel)


if __name__ == "__main__":
    main()
