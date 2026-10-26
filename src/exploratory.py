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
  3. task_mix_by_major_group.png -- usage share by SOC major group for each
     platform: the last weekly release (Feb 2026) and the last month (May 2026).
  4. task_automation_scatter.png -- task-level automation share, Claude.ai
     (x) vs. API (y), for tasks published on both platforms, every period.
     Points above the diagonal = businesses automate more on the same task.
  5. unpublished_tasks.png -- share of conversations with no published task,
     and (weekly releases) share of task-level collaboration records hidden
     as not_classified, by platform and period.

The geography figure was dropped: API data is global-only, so geography
cannot explain the API vs. Claude.ai gap.

Run from the repo root:  python src/exploratory.py
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from releases import (
    RELEASES, PLATFORMS, PATTERNS, load, collaboration_patterns, automation_split,
    major_group_mix, task_automation, unpublished_task_share,
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
    """data: one row per (release, period, platform) with the patterns and
    split. tasks: {(release, period, platform): task-level automation}.
    mixes: {(release, platform): major-group mix}. unpublished: rows for fig 5."""
    rows, tasks, mixes, unpublished = [], {}, {}, []
    for release in RELEASES:
        for platform in PLATFORMS:
            df = load(release["files"][platform])
            mixes[(release["release"], platform)] = major_group_mix(df, release)
            unpub = unpublished_task_share(df, release)
            for period, t in task_automation(df, release).items():
                tasks[(release["release"], period, platform)] = t
                hidden = None
                if "suppressed_n" in t:
                    hidden = t["suppressed_n"].sum() / (t["suppressed_n"].sum() + t["classified_n"].sum()) * 100
                unpublished.append({"release": release["release"], "period": period,
                                    "platform": platform, "no_task": unpub[period],
                                    "hidden_collab": hidden})
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
    return pd.DataFrame(rows), tasks, mixes, pd.DataFrame(unpublished)


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


# ---- FIGURE 3: task mix by SOC major group -----------------------------
MIX_PERIODS = [("2026-03-24", "2026-02-05 (1 wk)"), ("2026-06-26", "2026-05")]
TOP_GROUPS = 8


def plot_task_mix(mixes: dict):
    fig, axes = plt.subplots(1, len(MIX_PERIODS), figsize=(11, 4.8), sharey=True)

    # Same group order in both panels: the largest groups in the last period.
    last_rel, last_period = MIX_PERIODS[-1]
    combined = sum(mixes[(last_rel, p)][last_period] for p in PLATFORMS)
    groups = combined.sort_values(ascending=False).index[:TOP_GROUPS].tolist()

    for ax, (rel, period) in zip(axes, MIX_PERIODS):
        frame = pd.DataFrame({p: mixes[(rel, p)][period] for p in PLATFORMS}).fillna(0)
        other = frame.drop(index=[g for g in groups if g in frame.index]).sum()
        frame = frame.reindex(groups).fillna(0)
        frame.loc["All other groups"] = other
        frame = frame.iloc[::-1]
        y = range(len(frame))
        for i, platform in enumerate(PLATFORMS):
            ax.barh([v + (0.2 if i == 0 else -0.2) for v in y], frame[platform], height=0.38,
                    color=PLATFORM_COLORS[platform], label=PLATFORM_NAMES[platform])
        ax.set_yticks(list(y), frame.index)
        ax.set_xlabel("Share of usage with a published task (%)")
        ax.set_title(f"{rel} release | {period}")
        ax.grid(axis="y", visible=False)

    axes[0].legend(loc="lower right", frameon=False)
    fig.suptitle("Task mix by O*NET / SOC major group", color=INK)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "task_mix_by_major_group.png", dpi=150)
    plt.close(fig)
    print("Saved figures/task_mix_by_major_group.png")
    for (rel, platform), mix in mixes.items():
        top = mix.sort_values(mix.columns[-1], ascending=False).head(6)
        print(f"\n  {rel} / {platform}\n{top.round(2)}")


# ---- FIGURE 4: task-level automation, Claude.ai vs. API ----------------
def same_task_stats(tasks: dict) -> pd.DataFrame:
    """For tasks published on both platforms: how many, share of tasks where
    the API automates more, and the usage-weighted mean within-task gap."""
    rows = []
    periods = sorted({(r, p) for r, p, _ in tasks}, key=lambda k: k[0] + k[1])
    for rel, period in periods:
        api = tasks[(rel, period, "api")]
        cai = tasks[(rel, period, "claude_ai")]
        both = api[["automation_pct", "usage"]].join(
            cai[["automation_pct", "usage"]], lsuffix="_api", rsuffix="_cai", how="inner")
        gap = both["automation_pct_api"] - both["automation_pct_cai"]
        weight = both["usage_api"] + both["usage_cai"]
        rows.append({
            "release": rel, "period": period, "shared_tasks": len(both),
            "api_only": len(api) - len(both), "claude_only": len(cai) - len(both),
            "pct_tasks_api_higher": (gap > 0).mean() * 100,
            "pct_usage_api_higher": weight[gap > 0].sum() / weight.sum() * 100,
            "weighted_gap_pp": (gap * weight).sum() / weight.sum(),
            "median_gap_pp": gap.median(),
            "both": both,
        })
    return pd.DataFrame(rows)


def plot_task_automation_scatter(stats: pd.DataFrame):
    fig, axes = plt.subplots(1, len(stats), figsize=(16, 3.9), sharex=True, sharey=True)
    for ax, (_, row) in zip(axes, stats.iterrows()):
        both = row["both"]
        size = (both["usage_api"] + both["usage_cai"]) * 40 + 4
        ax.scatter(both["automation_pct_cai"], both["automation_pct_api"], s=size,
                   color=PLATFORM_COLORS["api"], alpha=0.35, edgecolor="white", linewidth=0.5)
        ax.plot([0, 100], [0, 100], color=INK_MUTED, linestyle="--", linewidth=1)
        ax.set_title(f"{row['period']}\nn={row['shared_tasks']:,}, API higher on "
                     f"{row['pct_tasks_api_higher']:.0f}%", fontsize=9)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xlabel("Claude.ai automation (%)")
    axes[0].set_ylabel("API automation (%)")
    fig.suptitle("Task-level automation share on tasks published on both platforms "
                 "(point size = combined usage; dashed = equal)", color=INK)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "task_automation_scatter.png", dpi=150)
    plt.close(fig)
    print("Saved figures/task_automation_scatter.png")
    print(stats.drop(columns="both").round(2).to_string(index=False))


# ---- FIGURE 5: unpublished / suppressed data ---------------------------
def plot_unpublished(unpub: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    order = list(dict.fromkeys(unpub["period"]))
    x = range(len(order))

    for i, platform in enumerate(PLATFORMS):
        sub = unpub[unpub["platform"] == platform].set_index("period").reindex(order)
        offset = -0.2 if i == 0 else 0.2
        axes[0].bar([v + offset for v in x], sub["no_task"], width=0.38,
                    color=PLATFORM_COLORS[platform], label=PLATFORM_NAMES[platform])
        weekly = sub["hidden_collab"].notna().tolist()
        axes[1].bar([v + offset for v, w in zip(x, weekly) if w],
                    sub["hidden_collab"].dropna(), width=0.38, color=PLATFORM_COLORS[platform])

    n_weekly = unpub.loc[unpub["hidden_collab"].notna(), "period"].nunique()
    axes[0].set_xticks(list(x), order, rotation=20, ha="right")
    axes[1].set_xticks(list(x)[:n_weekly], order[:n_weekly], rotation=20, ha="right")
    for ax in axes:
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("% of conversations")
    axes[0].set_title("Conversations with no published task")
    axes[1].set_ylabel("% of task-level collaboration records")
    axes[1].set_title("Task-level collaboration hidden as not_classified\n"
                      "(weekly releases only; monthly publishes shares)")
    axes[0].legend(frameon=False)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "unpublished_tasks.png", dpi=150)
    plt.close(fig)
    print("Saved figures/unpublished_tasks.png")
    print(unpub.round(2).to_string(index=False))


if __name__ == "__main__":
    data, tasks, mixes, unpub = collect()
    plot_automation_gap_over_time(data)
    plot_collaboration_distribution(data)
    plot_task_mix(mixes)
    plot_task_automation_scatter(same_task_stats(tasks))
    plot_unpublished(unpub)
