from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")

FILES = {
    "claude_ai": DATA_DIR / "aei_enriched_claude_ai_2025-08-04_to_2025-08-11.csv",
    "api": DATA_DIR / "aei_raw_1p_api_2025-08-04_to_2025-08-11.csv",
}

AUTOMATION_PATTERNS = {"directive", "feedback loop"}
AUGMENTATION_PATTERNS = {"task iteration", "learning", "validation"}
EXCLUDE_PATTERNS = {"none", "not_classified"}


TARGETS = {
    "claude_ai": {"automation_pct": 49.1, "augmentation_pct": 47.0},
    "api": {"automation_pct": 77.0, "augmentation_pct": 12.0},
}
ONET_TASK_TARGET = 19530  # p18 Figure 9.
 
TOLERANCE_PCT_POINTS = 2.0

# File / structural inventory

def inventory_file(label: str, path: Path) -> pd.DataFrame:
    print(f"\n{'=' * 70}\nFILE: {label}  ->  {path}\n{'=' * 70}")
 
    if not path.exists():
        print(f"  !! FILE NOT FOUND at {path}")
        return None
 
    size_mb = path.stat().st_size / (1024 * 1024)
    df = pd.read_csv(path, low_memory=False)
    row_count, col_count = len(df), len(df.columns)
 
    print(f"  Size: {size_mb:.2f} MB")
    print(f"  Rows: {row_count:,}")
    print(f"  Columns ({col_count}): {list(df.columns)}")
    print("  Missing-value rate per column:")
    for col in df.columns:
        pct = df[col].isna().mean() * 100
        flag = "  <-- has missing values" if pct > 0 else ""
        print(f"    {col:<25} {pct:>6.2f}%{flag}")
 
    return df

# Automation / augmentation split

def compute_split_from_five_patterns(df: pd.DataFrame, label: str) -> dict:
    """Bucket the five raw collaboration patterns into automation/augmentation.
    Used for the API file, which has no pre-computed rollup facet."""
    collab = df[(df["facet"] == "collaboration") & (df["variable"] == "collaboration_pct")]
    collab = collab[~collab["cluster_name"].isin(EXCLUDE_PATTERNS)]
    totals = collab.groupby("cluster_name")["value"].sum()
 
    automation_pct = totals[totals.index.isin(AUTOMATION_PATTERNS)].sum()
    augmentation_pct = totals[totals.index.isin(AUGMENTATION_PATTERNS)].sum()
 
    print(f"\n  [{label}] pattern shares (classified conversations only):")
    print(f"    {totals.to_string()}")
    print(f"  [{label}] automation%={automation_pct:.2f}  "
          f"augmentation%={augmentation_pct:.2f}  "
          f"(sums to {automation_pct + augmentation_pct:.2f}, "
          f"remainder is unclassified)")
 
    return {"automation_pct": automation_pct, "augmentation_pct": augmentation_pct}
 
 
def compute_split_from_rollup(df: pd.DataFrame, label: str) -> dict:
    """Read the pre-computed collaboration_automation_augmentation facet at
    the global level. Used for Claude.ai. Note: this facet's percentages are
    renormalized over classified conversations only (they sum to 100%),
    while the report's 49.1/47.0 headline sums to 96.1% (of all conversations,
    including ~3.9% unclassified) -- so a small, expected gap remains even
    on an exact match. See NOTES.md for the full explanation."""
    aa = df[df["facet"] == "collaboration_automation_augmentation"]
    global_row = aa[aa["geography"] == "global"]
 
    pivot = global_row.set_index("cluster_name")["value"]
    automation_pct = pivot.get("automation", float("nan"))
    augmentation_pct = pivot.get("augmentation", float("nan"))
 
    print(f"\n  [{label}] global automation/augmentation "
          f"(renormalized over classified conversations):")
    print(f"    automation%={automation_pct:.2f}  augmentation%={augmentation_pct:.2f}")
 
    return {"automation_pct": automation_pct, "augmentation_pct": augmentation_pct}


# Claimed vs. actual comparison

def compare_to_targets(label: str, actual: dict) -> list:
    rows = []
    target = TARGETS.get(label, {})
    for metric, computed in actual.items():
        target_val = target.get(metric)
        if target_val is None or pd.isna(computed):
            continue
        diff = abs(computed - target_val)
        status = "Match" if diff <= TOLERANCE_PCT_POINTS else "MISMATCH"
        rows.append((label, metric, target_val, round(computed, 2), round(diff, 2), status))
    return rows



def main():
    dataframes = {label: inventory_file(label, path) for label, path in FILES.items()}
 
    print(f"\n{'=' * 70}\nAUTOMATION / AUGMENTATION SPLIT\n{'=' * 70}")
    actual_claude = compute_split_from_rollup(dataframes["claude_ai"], "claude_ai")
    actual_api = compute_split_from_five_patterns(dataframes["api"], "api")
 
    # O*NET task count check (bonus, per Task 3's headline "~20k tasks")
    onet_claude = dataframes["claude_ai"]
    onet_task_count = onet_claude[onet_claude["facet"] == "onet_task"]["cluster_name"].nunique()
    print(f"\n  Distinct onet_task cluster_name values in Claude.ai file: {onet_task_count:,}")
    print(f"  (Target from original paper, p.18: {ONET_TASK_TARGET:,} total O*NET tasks. "
          f"This sample may only cover a subset with observed usage, so a lower "
          f"count here is expected, not necessarily a mismatch.)")
 
    print(f"\n{'=' * 70}\nCLAIMED VS. ACTUAL -- copy into NOTES.md\n{'=' * 70}")
    all_rows = (
        compare_to_targets("claude_ai", actual_claude)
        + compare_to_targets("api", actual_api)
    )
    summary = pd.DataFrame(
        all_rows,
        columns=["Platform", "Metric", "Claimed", "Actual", "Diff (pp)", "Status"],
    )
    print(summary.to_markdown(index=False))
 
 
if __name__ == "__main__":
    main()
