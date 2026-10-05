"""
exploratory.py

Generates the figures for PROFILE.md across all four releases in releases.py.

  1. automation_gap_over_time.png -- automation share of classified
     conversations, API vs. Claude.ai, every period. This is the figure that
     speaks directly to the research question: do businesses (API) show a
     higher automation share than individual consumers (Claude.ai), and has
     that gap changed across releases?
  2. collaboration_distribution.png -- all five collaboration patterns plus
     "none", stacked to 100%, for each platform and period.
  3. usage_per_capita_distribution.png -- usage_per_capita_index across
     countries (Claude.ai, latest month). Only the 2026-06-26 release has
     this metric, so this figure is not compared across releases.

Run from the repo root:  python src/exploratory.py
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from releases import (
    RELEASES, PLATFORMS, PATTERNS, load, collaboration_patterns, automation_split,
)

OUT_DIR = Path("figures")
OUT_DIR.mkdir(exist_ok=True)

PLATFORM_NAMES = {"api": "1P API (businesses)", "claude_ai": "Claude.ai (consumers)"}
PLATFORM_COLORS = {"api": "#2a78d6", "claude_ai": "#eb6834"}
PATTERN_COLORS = {
    "directive": "#2a78d6",
    "feedback loop": "#4a3aa7",
    "task iteration": "#eb6834",
    "learning": "#eda100",
    "validation": "#e87ba4",
    "none": "#b5b4ad",
}
INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"

plt.rcParams.update({
    "axes.edgecolor": GRID, "axes.labelcolor": INK_MUTED, "axes.titlecolor": INK,
    "xtick.color": INK_MUTED, "ytick.color": INK_MUTED, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "axes.axisbelow": True, "font.size": 10,
})


def collect():
    """One row per (release, period, platform) with the patterns and split."""
    rows = []
    for release in RELEASES:
        for platform in PLATFORMS:
            df = load(release["files"][platform])
            patterns = collaboration_patterns(df, release)
            split = automation_split(patterns)
            starts = sorted(df["date_start"].unique())
            for start, (period, prow) in zip(starts, patterns.iterrows()):
                rows.append({
                    "release": release["release"], "schema": release["schema"],
                    "platform": platform, "period": period,
                    "date": pd.Timestamp(start), **prow.to_dict(),
                    **split.loc[period].to_dict(),
                })
            if release["schema"] == "monthly" and platform == "claude_ai":
                plot_usage_per_capita_distribution(df)
    return pd.DataFrame(rows)


# ---- FIGURE 1: automation share over time, by platform -----------------
def plot_automation_gap_over_time(data: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 4.8))

    for platform in PLATFORMS:
        sub = data[data["platform"] == platform].sort_values("date")
        ax.plot(sub["date"], sub["automation_pct"], color=PLATFORM_COLORS[platform],
                linewidth=2, marker="o", markersize=7, label=PLATFORM_NAMES[platform])
        last = sub.iloc[-1]
        ax.annotate(f"{last['automation_pct']:.1f}%", (last["date"], last["automation_pct"]),
                    xytext=(8, 0), textcoords="offset points", va="center", color=INK)

    # Gap labels, one per period.
    wide = data.pivot_table(index="date", columns="platform", values="automation_pct")
    for date, row in wide.iterrows():
        gap = row["api"] - row["claude_ai"]
        ax.annotate(f"gap\n{gap:.1f} pp", (date, (row["api"] + row["claude_ai"]) / 2),
                    ha="center", va="center", fontsize=8, color=INK_MUTED,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))

    schema_change = data.loc[data["schema"] == "monthly", "date"].min()
    ax.axvline(schema_change - pd.Timedelta(days=20), color=INK_MUTED, linestyle="--", linewidth=1)
    ax.text(schema_change - pd.Timedelta(days=24), 22, "2026-06-26 release:\nmonthly aggregates,\nnew method",
            ha="right", va="bottom", fontsize=8, color=INK_MUTED)

    ax.set_ylim(20, 100)
    ax.set_ylabel("Automation share of classified conversations (%)")
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[2, 5, 8, 11]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_title("Automation share by platform across releases")
    ax.legend(loc="lower left", frameon=False)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "automation_gap_over_time.png", dpi=150)
    plt.close(fig)
    print("Saved figures/automation_gap_over_time.png")
    print(wide.assign(gap=wide["api"] - wide["claude_ai"]).round(2))


# ---- FIGURE 2: collaboration pattern distribution ----------------------
def plot_collaboration_distribution(data: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)

    for ax, platform in zip(axes, PLATFORMS):
        sub = data[data["platform"] == platform].sort_values("date", ascending=False)
        labels = [f"{r} | {p}" for r, p in zip(sub["release"], sub["period"])]
        left = pd.Series(0.0, index=sub.index)
        totals = sub[PATTERNS].sum(axis=1)  # renormalize the tiny not_classified gap
        for pattern in PATTERNS:
            share = sub[pattern] / totals * 100
            ax.barh(labels, share, left=left, color=PATTERN_COLORS[pattern],
                    edgecolor="white", linewidth=1.5, label=pattern)
            left += share
        ax.set_xlim(0, 100)
        ax.set_xlabel("Share of conversations (%)")
        ax.set_title(PLATFORM_NAMES[platform])
        ax.grid(axis="y", visible=False)

    axes[0].set_ylabel("Release | period")
    handles, names = axes[0].get_legend_handles_labels()
    fig.legend(handles, names, loc="lower center", ncol=6, frameon=False)
    fig.suptitle("Collaboration pattern mix by release (automation = directive + feedback loop)",
                 color=INK)
    plt.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(OUT_DIR / "collaboration_distribution.png", dpi=150)
    plt.close(fig)
    print("Saved figures/collaboration_distribution.png")
    print(data.set_index(["platform", "release", "period"])[PATTERNS].round(2))


# ---- FIGURE 3: usage_per_capita_index across countries -----------------
def plot_usage_per_capita_distribution(df: pd.DataFrame):
    mask = (
        (df["metric_id"] == "usage_per_capita_index")
        & (df["geo_level"] == "country")
        & (df["category_name"] == "overall")
    )
    sub = df.loc[mask, ["date_start", "geo_id", "value"]]
    latest = sub["date_start"].max()
    sub = sub[sub["date_start"] == latest]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(sub["value"], bins=30, color=PLATFORM_COLORS["claude_ai"], edgecolor="white")
    ax.axvline(1.0, color=INK, linestyle="--", linewidth=1,
               label="1.0 = usage proportional to population")
    ax.set_ylabel("Number of countries")
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.set_xlabel("usage_per_capita_index")
    ax.set_title(f"Anthropic Usage Index across countries, Claude.ai ({latest[:7]}, n={len(sub)})")
    ax.legend(frameon=False)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "usage_per_capita_distribution.png", dpi=150)
    plt.close(fig)
    print("Saved figures/usage_per_capita_distribution.png")
    print(sub["value"].describe().round(2))
    print(f"  countries below 1.0: {(sub['value'] < 1).sum()}, at/above 1.0: {(sub['value'] >= 1).sum()}")
    print(f"  top 5: {sub.nlargest(5, 'value')[['geo_id', 'value']].values.tolist()}")


if __name__ == "__main__":
    data = collect()
    plot_automation_gap_over_time(data)
    plot_collaboration_distribution(data)
