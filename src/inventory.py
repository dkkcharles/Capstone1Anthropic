"""
inventory.py

Inventory of every release file in data/ (size, rows, columns with types,
missing-value rates) plus a claimed-vs-actual check of each report's
headline numbers. Release definitions and metric logic live in releases.py.

Run from the repo root:  python src/inventory.py
"""

import pandas as pd

from releases import (
    RELEASES, PLATFORMS, load, collaboration_patterns, automation_split,
    published_buckets, onet_task_shares, use_case_shares,
)

# Headline numbers from each report, used as verification targets.
# measure is one of: automation_raw, augmentation_raw (share of ALL
# conversations), directive (share of ALL conversations), top10_tasks
# (share of conversations in the 10 most common O*NET tasks).
TARGETS = [
    # 2025-09-15 report (Aug 4-11, 2025 sample)
    ("2025-09-15", "claude_ai", "automation_raw", 49.1, "49.1% automation"),
    ("2025-09-15", "claude_ai", "augmentation_raw", 47.0, "47.0% augmentation"),
    ("2025-09-15", "api", "automation_raw", 77.0, "77% of API transcripts show automation"),
    ("2025-09-15", "api", "augmentation_raw", 12.0, "12% augmentation"),
    # 2026-01-15 report (Nov 13-20, 2025 sample)
    ("2026-01-15", "claude_ai", "automation_raw", 45.0, "automated fell 4pp to 45%"),
    ("2026-01-15", "claude_ai", "augmentation_raw", 52.0, "augmented jumped 5pp to 52%"),
    ("2026-01-15", "claude_ai", "directive", 32.0, "directive fell 7pp to 32%"),
    ("2026-01-15", "api", "automation_raw", 75.0, "three-quarters automation"),
    ("2026-01-15", "claude_ai", "top10_tasks", 24.0, "top 10 tasks = 24% of conversations"),
    ("2026-01-15", "api", "top10_tasks", 32.0, "top ten tasks = 32% of traffic"),
    # 2026-03-24 report (Feb 5-12, 2026 sample)
    ("2026-03-24", "claude_ai", "top10_tasks", 19.0, "top 10 tasks went from 24% to 19%"),
    ("2026-03-24", "api", "top10_tasks", 33.0, "top 10 tasks 33% of traffic, up from 28%"),
    # 2026-06-26 report gives no automation/augmentation headline number.
]
ONET_TASK_TARGET = 19530  # Total O*NET tasks, original paper p.18, Figure 9.

TOLERANCE_PCT_POINTS = 2.0

# File / structural inventory

def inventory_file(label: str, path) -> pd.DataFrame:
    print(f"\n{'=' * 70}\nFILE: {label}  ->  {path}\n{'=' * 70}")

    if not path.exists():
        print(f"  !! FILE NOT FOUND at {path}")
        return None

    size_mb = path.stat().st_size / (1024 * 1024)
    df = load(path)
    row_count, col_count = len(df), len(df.columns)

    print(f"  Size: {size_mb:.2f} MB")
    print(f"  Rows: {row_count:,}")
    print(f"  Columns ({col_count}):")
    for col in df.columns:
        pct = df[col].isna().mean() * 100
        flag = "  <-- has missing values" if pct > 0 else ""
        print(f"    {col:<22} {str(df[col].dtype):<8} missing {pct:>6.2f}%{flag}")

    geo_col = "geography" if "geography" in df.columns else "geo_level"
    print(f"  Rows by date_start: {df['date_start'].value_counts().sort_index().to_dict()}")
    print(f"  Rows by {geo_col}: {df[geo_col].value_counts().to_dict()}")

    return df


def main():
    measures = {}  # (release, platform) -> {measure: {period: value}}
    split_rows, size_rows = [], []

    for release in RELEASES:
        for platform in PLATFORMS:
            path = release["files"][platform]
            df = inventory_file(f"{release['release']} / {platform}", path)
            if df is None:
                continue
            size_rows.append((release["release"], platform, path.name,
                              round(path.stat().st_size / 2**20, 1), len(df)))

            patterns = collaboration_patterns(df, release)
            split = automation_split(patterns)
            tasks = onet_task_shares(df, release)
            print(f"\n  Collaboration patterns (% of all conversations):\n"
                  f"{patterns.round(2).to_string()}")
            print(f"  Automation split:\n{split.round(2).to_string()}")
            if release["schema"] == "monthly":
                print(f"  Published collaboration_bucket_* (cross-check):\n"
                      f"{published_buckets(df).round(2).to_string()}")
            use_case = use_case_shares(df, release)
            if not use_case.empty:
                print(f"  Use case (% of conversations):\n{use_case.round(2).to_string()}")
            for period, shares in tasks.items():
                print(f"  O*NET tasks {period}: {shares.index.nunique():,} distinct, "
                      f"shares sum to {shares.sum():.2f}%, "
                      f"top 10 = {shares.nlargest(10).sum():.2f}%")

            measures[(release["release"], platform)] = {
                "automation_raw": split["automation_raw"].to_dict(),
                "augmentation_raw": split["augmentation_raw"].to_dict(),
                "directive": patterns["directive"].to_dict(),
                "top10_tasks": {p: s.nlargest(10).sum() for p, s in tasks.items()},
            }
            for period, row in split.iterrows():
                split_rows.append((release["release"], period, platform,
                                   round(row["automation_raw"], 2), round(row["augmentation_raw"], 2),
                                   round(row["none_raw"], 2), round(row["automation_pct"], 2)))

    print(f"\n{'=' * 70}\nFILE SUMMARY -- copy into NOTES.md\n{'=' * 70}")
    print(pd.DataFrame(size_rows, columns=["Release", "Platform", "File", "MB", "Rows"])
          .to_markdown(index=False))

    print(f"\n{'=' * 70}\nAUTOMATION SPLIT BY RELEASE -- copy into NOTES.md / PROFILE.md\n{'=' * 70}")
    print(pd.DataFrame(split_rows, columns=[
        "Release", "Period", "Platform", "Automation (all)", "Augmentation (all)",
        "None", "Automation (classified)",
    ]).to_markdown(index=False))

    print(f"\n{'=' * 70}\nCLAIMED VS. ACTUAL -- copy into NOTES.md\n{'=' * 70}")
    rows = []
    for rel, platform, measure, claimed, quote in TARGETS:
        for period, actual in measures.get((rel, platform), {}).get(measure, {}).items():
            diff = abs(actual - claimed)
            status = "Match" if diff <= TOLERANCE_PCT_POINTS else "MISMATCH"
            rows.append((rel, platform, measure, quote, claimed, round(actual, 2), round(diff, 2), status))
    print(pd.DataFrame(rows, columns=[
        "Release", "Platform", "Measure", "Report says", "Claimed", "Actual", "Diff (pp)", "Status",
    ]).to_markdown(index=False))
    print(f"\n  (O*NET task target from original paper, p.18: {ONET_TASK_TARGET:,} total tasks. "
          f"Only tasks with observed usage above the privacy threshold appear, so lower "
          f"counts above are expected, not a mismatch.)")


if __name__ == "__main__":
    main()
