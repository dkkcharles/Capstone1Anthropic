"""
make_profile_plots.py

Generates the three figures for PROFILE.md, matching the real schema
confirmed in inventory.py (columns: geo_id, geography, date_start, date_end,
platform_and_product, facet, level, variable, cluster_name, value).

  1. Global collaboration cluster_name distribution (API file)
  2. usage_tier counts across countries (Claude.ai file)
  3. Automation vs. augmentation share, API vs. Claude.ai -- the figure that
     speaks directly to the research question: do businesses (API) show a
     higher automation share than individual consumers (Claude.ai)?

"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# ---- CONFIG -----------------------------------------------------------
DATA_DIR = Path("data")

FILES = {
    "claude_ai": DATA_DIR / "aei_enriched_claude_ai_2025-08-04_to_2025-08-11.csv",
    "api": DATA_DIR / "aei_raw_1p_api_2025-08-04_to_2025-08-11.csv",
}

AUTOMATION_PATTERNS = {"directive", "feedback loop"}
AUGMENTATION_PATTERNS = {"task iteration", "learning", "validation"}
EXCLUDE_PATTERNS = {"none", "not_classified"}

OUT_DIR = Path("figures")
OUT_DIR.mkdir(exist_ok=True)


# ---- FIGURE 1: Global collaboration cluster_name distribution ---------
def plot_collaboration_distribution(label="api"):
    df = pd.read_csv(FILES[label])

    mask = (
        (df["facet"] == "collaboration")
        & (df["variable"] == "collaboration_pct")
        & (df["geography"] == "global")
    )
    sub = df.loc[mask, ["cluster_name", "value"]].copy()

    if sub.empty:
        raise ValueError(
            f"No global collaboration_pct rows found in {FILES[label]}. "
            "Check facet/variable/geography spelling."
        )

    sub = sub.sort_values("value", ascending=False)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(sub["cluster_name"], sub["value"], color="#4C72B0")
    ax.set_ylabel("Share of conversations (%)")
    ax.set_xlabel("Interaction pattern (cluster_name)")
    ax.set_title(f"Global collaboration pattern distribution — {label}")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    fig.savefig(OUT_DIR / "collaboration_distribution.png", dpi=150)
    plt.close(fig)
    print("Saved figures/collaboration_distribution.png")
    print(sub)


# ---- FIGURE 2: usage_tier counts across countries ----------------------
def plot_usage_tier_distribution(label="claude_ai"):
    df = pd.read_csv(FILES[label])

    mask = (df["variable"] == "usage_tier") & (df["geography"] == "country")
    sub = df.loc[mask, ["geo_id", "cluster_name"]].dropna(subset=["cluster_name"])

    tier_counts = sub["cluster_name"].value_counts()

    tier_order = [
        "Minimal",
        "Emerging (bottom 25%)",
        "Established",
        "Advanced",
        "Leading (top 25%)",
    ]
    tier_counts = tier_counts.reindex(
        [t for t in tier_order if t in tier_counts.index]
    ).combine_first(tier_counts)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(tier_counts.index, tier_counts.values, color="#DD8452")
    ax.set_ylabel("Number of countries")
    ax.set_xlabel("usage_tier")
    ax.set_title("Country counts by usage tier")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    fig.savefig(OUT_DIR / "usage_tier_distribution.png", dpi=150)
    plt.close(fig)
    print("Saved figures/usage_tier_distribution.png")
    print(tier_counts)


# ---- FIGURE 3: automation vs. augmentation share, API vs. Claude.ai ----
def compute_split_from_five_patterns(df: pd.DataFrame) -> dict:
    """API file has no pre-computed rollup facet -- bucket the five raw
    collaboration patterns ourselves. Mirrors inventory.py exactly."""
    collab = df[(df["facet"] == "collaboration") & (df["variable"] == "collaboration_pct")]
    collab = collab[~collab["cluster_name"].isin(EXCLUDE_PATTERNS)]
    totals = collab.groupby("cluster_name")["value"].sum()

    automation_pct = totals[totals.index.isin(AUTOMATION_PATTERNS)].sum()
    augmentation_pct = totals[totals.index.isin(AUGMENTATION_PATTERNS)].sum()
    return {"automation_pct": automation_pct, "augmentation_pct": augmentation_pct}


def compute_split_from_rollup(df: pd.DataFrame) -> dict:
    """Claude.ai file has a pre-computed collaboration_automation_augmentation
    facet at the global level. Mirrors inventory.py exactly. Note: these
    percentages are renormalized over classified conversations only (sum to
    100%), unlike the report's headline figures (sum to ~96.1%) -- see
    NOTES.md for the explanation already written up from inventory.py."""
    aa = df[df["facet"] == "collaboration_automation_augmentation"]
    global_row = aa[aa["geography"] == "global"]
    pivot = global_row.set_index("cluster_name")["value"]
    return {
        "automation_pct": pivot.get("automation", float("nan")),
        "augmentation_pct": pivot.get("augmentation", float("nan")),
    }


def plot_automation_augmentation_by_platform():
    df_api = pd.read_csv(FILES["api"])
    df_claude = pd.read_csv(FILES["claude_ai"])

    actual_api = compute_split_from_five_patterns(df_api)
    actual_claude = compute_split_from_rollup(df_claude)

    combined = pd.DataFrame(
        {"API": actual_api, "Claude.ai": actual_claude}
    )  # index: automation_pct, augmentation_pct; columns: platform

    fig, ax = plt.subplots(figsize=(7, 4.5))
    combined.plot(kind="bar", ax=ax, color=["#4C72B0", "#DD8452"])
    ax.set_ylabel("Share of conversations (%)")
    ax.set_xlabel("")
    ax.set_title("Automation vs. augmentation share: API vs. Claude.ai (global)")
    plt.xticks(rotation=0)
    ax.legend(title="Platform")
    plt.tight_layout()
    fig.savefig(OUT_DIR / "automation_augmentation_by_platform.png", dpi=150)
    plt.close(fig)
    print("Saved figures/automation_augmentation_by_platform.png")
    print(combined)


if __name__ == "__main__":
    plot_collaboration_distribution()
    plot_usage_tier_distribution()
    plot_automation_augmentation_by_platform()