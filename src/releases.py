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

# Pinned Hugging Face dataset version (commit of 2026-09-30). Every file in
# data/ was checked byte-for-byte (sha256) against this commit; see fetch.py.
HF_REPO = "Anthropic/EconomicIndex"
HF_REVISION = "4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6"

RELEASES = [
    {
        "release": "2025-09-15",
        "schema": "raw",
        "hf_dir": "release_2025_09_15/data/intermediate",
        "files": {
            "claude_ai": DATA_DIR / "aei_raw_claude_ai_2025-08-04_to_2025-08-11.csv",
            "api": DATA_DIR / "aei_raw_1p_api_2025-08-04_to_2025-08-11.csv",
        },
    },
    {
        "release": "2026-01-15",
        "schema": "raw",
        "hf_dir": "release_2026_01_15/data/intermediate",
        "files": {
            "claude_ai": DATA_DIR / "aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv",
            "api": DATA_DIR / "aei_raw_1p_api_2025-11-13_to_2025-11-20.csv",
        },
    },
    {
        "release": "2026-03-24",
        "schema": "raw",
        "hf_dir": "release_2026_03_24/data",
        "files": {
            "claude_ai": DATA_DIR / "aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv",
            "api": DATA_DIR / "aei_raw_1p_api_2026-02-05_to_2026-02-12.csv",
        },
    },
    {
        "release": "2026-06-26",
        "schema": "monthly",
        "hf_dir": "release_2026_06_26/data",
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


# ---- Task-level helpers (task mix, same-task comparison, suppression) ----

ONET_REFERENCE = DATA_DIR / "reference" / "onet_task_statements_raw.xlsx"

# 2018 SOC major groups (the first two digits of an O*NET-SOC code). Titles
# match the soc_occupation major-group node_names in the 2026-06-26 files.
SOC_MAJOR_GROUPS = {
    "11": "Management", "13": "Business and Financial Operations",
    "15": "Computer and Mathematical", "17": "Architecture and Engineering",
    "19": "Life, Physical, and Social Science", "21": "Community and Social Service",
    "23": "Legal", "25": "Educational Instruction and Library",
    "27": "Arts, Design, Entertainment, Sports, and Media",
    "29": "Healthcare Practitioners and Technical", "31": "Healthcare Support",
    "33": "Protective Service", "35": "Food Preparation and Serving Related",
    "37": "Building and Grounds Cleaning and Maintenance", "39": "Personal Care and Service",
    "41": "Sales and Related", "43": "Office and Administrative Support",
    "45": "Farming, Fishing, and Forestry", "47": "Construction and Extraction",
    "49": "Installation, Maintenance, and Repair", "51": "Production",
    "53": "Transportation and Material Moving",
}


def task_major_groups() -> pd.DataFrame:
    """Raw-schema task statement (lower-cased) -> SOC major group, with a
    weight that splits a statement shared by several major groups equally."""
    ref = pd.read_excel(ONET_REFERENCE)
    ref["task"] = ref["Task"].str.lower().str.strip()
    ref["major_group"] = ref["O*NET-SOC Code"].str[:2].map(SOC_MAJOR_GROUPS)
    pairs = ref[["task", "major_group"]].drop_duplicates()
    pairs["weight"] = 1 / pairs.groupby("task")["major_group"].transform("size")
    return pairs


def major_group_mix(df: pd.DataFrame, release: dict) -> pd.DataFrame:
    """Usage share (%) by SOC major group, one column per period.
    Both schemas are renormalized over published, classified tasks so each
    column sums to 100 (unpublished cells are missing rows, not zeros).
      raw     -- task shares mapped to major groups via the O*NET reference.
      monthly -- the release's own soc_occupation major-group rows (its task
                 IDs only partly match the reference file, see NOTES.md)."""
    if release["schema"] == "raw":
        lookup = task_major_groups()
        cols = {}
        for period, shares in onet_task_shares(df, release).items():
            s = shares.rename("share").rename_axis("task").reset_index()
            s["task"] = s["task"].str.strip()
            m = s.merge(lookup, on="task", how="left")
            m["share"] *= m["weight"].fillna(1)
            cols[period] = m.groupby(m["major_group"].fillna("Unmatched"))["share"].sum()
        mix = pd.DataFrame(cols)
    else:
        rows = df[(df["geo_id"] == "GLOBAL") & (df["category_name"] == "soc_occupation")
                  & (df["hierarchy_level"] == 1) & (df["metric_id"] == "pct")]
        mix = rows.pivot_table(index="node_name", columns="date_start", values="value")
        mix.columns = [period_label(release, d) for d in mix.columns]
    return mix / mix.sum() * 100


def task_automation(df: pd.DataFrame, release: dict) -> dict:
    """{period: DataFrame indexed by task key with automation_pct (share of
    classified conversations for that task) and usage (task share, %)}.
    raw     -- from onet_task::collaboration counts; the per-task
               not_classified bucket (privacy-suppressed patterns) and none
               are excluded from the denominator.
    monthly -- from the per-task collaboration_bucket_automation_pct."""
    shares = onet_task_shares(df, release)
    out = {}
    if release["schema"] == "raw":
        rows = df[(df["geography"] == "global") & (df["facet"] == "onet_task::collaboration")
                  & (df["variable"] == "onet_task_collaboration_count")]
        split = rows["cluster_name"].str.rsplit("::", n=1, expand=True)
        rows = rows.assign(task=split[0], pattern=split[1])
        for start, g in rows.groupby("date_start"):
            counts = g.pivot_table(index="task", columns="pattern", values="value",
                                   aggfunc="sum", fill_value=0)
            counts = counts.reindex(columns=PATTERNS + ["not_classified"], fill_value=0)
            auto = counts[AUTOMATION_PATTERNS].sum(axis=1)
            classified = auto + counts[AUGMENTATION_PATTERNS].sum(axis=1)
            period = period_label(release, start)
            t = pd.DataFrame({
                "automation_pct": auto / classified * 100,
                "classified_n": classified,
                "suppressed_n": counts["not_classified"],
            })
            t = t[(classified > 0) & ~t.index.isin(NON_TASKS)]
            out[period] = t.join(shares[period].rename("usage"), how="left")
    else:
        rows = df[(df["geo_id"] == "GLOBAL") & (df["category_name"] == "onet")
                  & (df["hierarchy_level"] == 0)
                  & (df["metric_id"] == "collaboration_bucket_automation_pct")]
        for start, g in rows.groupby("date_start"):
            period = period_label(release, start)
            t = g.set_index("node_external_id")[["value"]].rename(columns={"value": "automation_pct"})
            out[period] = t.join(shares[period].rename("usage"), how="left")
    return out


def unpublished_task_share(df: pd.DataFrame, release: dict) -> dict:
    """{period: % of conversations with no published task}. raw: the none
    and not_classified task rows; monthly: 100 minus the published task shares."""
    if release["schema"] == "raw":
        rows = df[(df["geography"] == "global") & (df["facet"] == "onet_task")
                  & (df["variable"] == "onet_task_pct") & (df["cluster_name"].isin(NON_TASKS))]
        return {period_label(release, s): g["value"].sum() for s, g in rows.groupby("date_start")}
    return {p: 100 - s.sum() for p, s in onet_task_shares(df, release).items()}


def sample_size(df: pd.DataFrame, release: dict):
    """Raw schema only: total records = sum of global collaboration_count.
    The monthly schema publishes shares only, so this returns None."""
    if release["schema"] != "raw":
        return None
    rows = df[(df["geography"] == "global") & (df["facet"] == "collaboration")
              & (df["variable"] == "collaboration_count")]
    return rows["value"].sum()


# ---- Per-task pattern shares and numeric primitives (hypothesis_tests.py) --

def task_patterns(df: pd.DataFrame, release: dict) -> dict:
    """{period: DataFrame indexed by task key} with each of the five patterns
    as a share (%) of that task's classified conversations (none and
    not_classified excluded, so the five sum to 100), plus usage (task
    share, %) and, for the raw schema, classified_n (record count)."""
    shares = onet_task_shares(df, release)
    five = AUTOMATION_PATTERNS + AUGMENTATION_PATTERNS
    out = {}
    if release["schema"] == "raw":
        rows = df[(df["geography"] == "global") & (df["facet"] == "onet_task::collaboration")
                  & (df["variable"] == "onet_task_collaboration_count")]
        split = rows["cluster_name"].str.rsplit("::", n=1, expand=True)
        rows = rows.assign(task=split[0], pattern=split[1])
        for start, g in rows.groupby("date_start"):
            counts = g.pivot_table(index="task", columns="pattern", values="value",
                                   aggfunc="sum", fill_value=0).reindex(columns=five, fill_value=0)
            n = counts.sum(axis=1)
            t = counts[n > 0].div(n[n > 0], axis=0) * 100
            t = t[~t.index.isin(NON_TASKS)].assign(classified_n=n)
            period = period_label(release, start)
            out[period] = t.join(shares[period].rename("usage"), how="left")
    else:
        metrics = {m: p for m, p in MONTHLY_PATTERN_METRICS.items() if p in five}
        rows = df[(df["geo_id"] == "GLOBAL") & (df["category_name"] == "onet")
                  & (df["hierarchy_level"] == 0) & (df["metric_id"].isin(metrics))]
        for start, g in rows.groupby("date_start"):
            wide = g.pivot_table(index="node_external_id", columns="metric_id", values="value")
            wide = wide.rename(columns=metrics).reindex(columns=five).fillna(0)
            total = wide.sum(axis=1)
            t = wide[total > 0].div(total[total > 0], axis=0) * 100
            period = period_label(release, start)
            out[period] = t.join(shares[period].rename("usage"), how="left")
    return out


def task_mean(df: pd.DataFrame, release: dict, primitive: str) -> dict:
    """{period: Series of the per-task mean of a numeric primitive, e.g.
    'ai_autonomy'}. Empty for releases that do not have it (2025-09-15)."""
    if release["schema"] == "raw":
        rows = df[(df["geography"] == "global") & (df["facet"] == f"onet_task::{primitive}")
                  & (df["variable"] == f"onet_task_{primitive}_mean")]
        # The 2026-03-24 files append "::value" to the task name in numeric
        # intersection facets; earlier releases do not.
        rows = rows.assign(task=rows["cluster_name"].str.removesuffix("::value"))
        key = "task"
    else:
        rows = df[(df["geo_id"] == "GLOBAL") & (df["category_name"] == "onet")
                  & (df["hierarchy_level"] == 0) & (df["metric_id"] == f"{primitive}_mean")]
        key = "node_external_id"
    return {
        period_label(release, start): g.set_index(key)["value"]
        for start, g in rows.groupby("date_start")
    }
