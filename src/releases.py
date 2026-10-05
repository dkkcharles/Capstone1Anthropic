"""
releases.py

One place that knows where each Anthropic Economic Index release lives and
how to read it. inventory.py and exploratory.py both import from here, so the
two scripts always compute the same numbers.

Two schemas are in play:
  "raw"   -- releases 2025-09-15, 2026-01-15, 2026-03-24. One sampled week per
             file. Columns: geo_id, geography, date_start, date_end,
             platform_and_product, facet, level, variable, cluster_name, value.
             Collaboration patterns are cluster_name values of the
             collaboration_pct variable.
  "monthly" -- release 2026-06-26. Calendar-month aggregates (April and May
             2026 in one file). Columns: date_start, date_end, geo_id,
             geo_level, category_name, hierarchy_level, metric_id, value,
             node_name, node_external_id. Collaboration patterns are their
             own metric_ids (collaboration_directive_pct, ...).
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")

RELEASES = [
    {
        "release": "2025-09-15",
        "schema": "raw",
        "files": {
            "claude_ai": DATA_DIR / "aei_raw_claude_ai_2025-08-04_to_2025-08-11.csv",
            "api": DATA_DIR / "aei_raw_1p_api_2025-08-04_to_2025-08-11.csv",
        },
    },
    {
        "release": "2026-01-15",
        "schema": "raw",
        "files": {
            "claude_ai": DATA_DIR / "aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv",
            "api": DATA_DIR / "aei_raw_1p_api_2025-11-13_to_2025-11-20.csv",
        },
    },
    {
        "release": "2026-03-24",
        "schema": "raw",
        "files": {
            "claude_ai": DATA_DIR / "aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv",
            "api": DATA_DIR / "aei_raw_1p_api_2026-02-05_to_2026-02-12.csv",
        },
    },
    {
        "release": "2026-06-26",
        "schema": "monthly",
        "files": {
            "claude_ai": DATA_DIR / "aei_claude_ai_2026-06-26.csv",
            "api": DATA_DIR / "aei_1p_api_2026-06-26.csv",
        },
    },
]

PLATFORMS = ["api", "claude_ai"]

# The five collaboration patterns, plus "none". Same names in both schemas
# once the monthly metric_ids are mapped back to cluster_name spelling.
AUTOMATION_PATTERNS = ["directive", "feedback loop"]
AUGMENTATION_PATTERNS = ["task iteration", "learning", "validation"]
PATTERNS = AUTOMATION_PATTERNS + AUGMENTATION_PATTERNS + ["none"]

MONTHLY_PATTERN_METRICS = {
    "collaboration_directive_pct": "directive",
    "collaboration_feedback_loop_pct": "feedback loop",
    "collaboration_task_iteration_pct": "task iteration",
    "collaboration_learning_pct": "learning",
    "collaboration_validation_pct": "validation",
    "collaboration_none_pct": "none",
}

# O*NET task rows that are not real tasks in the raw schema.
NON_TASKS = {"none", "not_classified"}


def load(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def period_label(release: dict, start: str) -> str:
    """Raw releases are one sampled week; monthly releases are whole months."""
    if release["schema"] == "raw":
        return f"{start} (1 wk)"
    return start[:7]


# ---- Collaboration patterns --------------------------------------------

def collaboration_patterns(df: pd.DataFrame, release: dict) -> pd.DataFrame:
    """Global share of ALL conversations in each pattern, one row per period.
    Raw files also carry a tiny not_classified bucket, which is left out."""
    if release["schema"] == "raw":
        rows = df[(df["geography"] == "global") & (df["facet"] == "collaboration")
                  & (df["variable"] == "collaboration_pct")]
        wide = rows.pivot_table(index="date_start", columns="cluster_name", values="value")
    else:
        rows = df[(df["geo_id"] == "GLOBAL") & (df["category_name"] == "overall")
                  & (df["metric_id"].isin(MONTHLY_PATTERN_METRICS))]
        wide = rows.pivot_table(index="date_start", columns="metric_id", values="value")
        wide = wide.rename(columns=MONTHLY_PATTERN_METRICS)
    wide.index = [period_label(release, d) for d in wide.index]
    return wide[PATTERNS]


def automation_split(patterns: pd.DataFrame) -> pd.DataFrame:
    """Two versions of the split, because the reports use both:
      *_raw  -- share of ALL conversations (what the 2025-09-15 and 2026-01-15
                headline numbers use; does not sum to 100 because of "none").
      *_pct  -- share of CLASSIFIED conversations (automation + augmentation
                = 100). This is the measure used to compare releases, because
                the API "none" share moves a lot between releases (10% -> 15%)."""
    auto = patterns[AUTOMATION_PATTERNS].sum(axis=1)
    aug = patterns[AUGMENTATION_PATTERNS].sum(axis=1)
    return pd.DataFrame({
        "automation_raw": auto,
        "augmentation_raw": aug,
        "none_raw": patterns["none"],
        "automation_pct": auto / (auto + aug) * 100,
        "augmentation_pct": aug / (auto + aug) * 100,
    })


def published_buckets(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly schema only: the collaboration_bucket_* metrics Anthropic
    publishes, used to cross-check automation_split()."""
    rows = df[(df["geo_id"] == "GLOBAL") & (df["category_name"] == "overall")
              & (df["metric_id"].str.startswith("collaboration_bucket_"))]
    wide = rows.pivot_table(index="date_start", columns="metric_id", values="value")
    wide.index = [d[:7] for d in wide.index]
    return wide


# ---- O*NET tasks ---------------------------------------------------------

def onet_task_shares(df: pd.DataFrame, release: dict) -> dict:
    """{period: Series of global task shares (%)}, real tasks only."""
    if release["schema"] == "raw":
        rows = df[(df["geography"] == "global") & (df["facet"] == "onet_task")
                  & (df["variable"] == "onet_task_pct")
                  & (~df["cluster_name"].isin(NON_TASKS))]
        key = "cluster_name"
    else:
        rows = df[(df["geo_id"] == "GLOBAL") & (df["category_name"] == "onet")
                  & (df["hierarchy_level"] == 0) & (df["metric_id"] == "pct")]
        key = "node_external_id"
    return {
        period_label(release, start): g.set_index(key)["value"]
        for start, g in rows.groupby("date_start")
    }


# ---- Use case (work / personal / coursework) ----------------------------

def use_case_shares(df: pd.DataFrame, release: dict) -> pd.DataFrame:
    if release["schema"] == "raw":
        rows = df[(df["geography"] == "global") & (df["facet"] == "use_case")
                  & (df["variable"] == "use_case_pct")
                  & (df["cluster_name"].isin(["work", "personal", "coursework"]))]
        wide = rows.pivot_table(index="date_start", columns="cluster_name", values="value")
    else:
        rows = df[(df["geo_id"] == "GLOBAL") & (df["category_name"] == "overall")
                  & (df["metric_id"].str.startswith("use_case_"))]
        wide = rows.pivot_table(index="date_start", columns="metric_id", values="value")
        wide = wide.rename(columns=lambda m: m.removeprefix("use_case_").removesuffix("_pct"))
    wide.index = [period_label(release, d) for d in wide.index]
    return wide
