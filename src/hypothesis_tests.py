"""
hypothesis_tests.py

Tests whether the API vs. Claude.ai automation gap could be a measurement
artifact. An API record is a single prompt-response pair, while a Claude.ai
record is a whole conversation, so multi-turn patterns are structurally
harder to observe on the API ("measurement asymmetry").

All tests are paired across tasks published on both platforms in the same
period, so task mix is held fixed. For each task, d = API - Claude.ai.

  T1  Feedback loop share of classified conversations.
      Feedback loop is an AUTOMATION pattern that needs several turns.
      If the gap is mechanical, the API should show LESS of it on the same
      task (d < 0). If businesses genuinely delegate more, it should not be
      suppressed.
  T2  Automation using only single-turn-observable patterns:
      directive / (directive + learning + validation).
      Drops the two patterns that need iteration (feedback loop, task
      iteration). If the gap persists, it is not explained by the API's
      inability to show iteration.
  T3  AI autonomy (1-5, mean per task), from 2025-11 onwards.
      A different construct from automation: how much decision-making is
      delegated (2026-01-15 report). Asks whether the API's extra automation
      is also extra delegated judgement, or narrower, scripted work. The
      report found API autonomy "uniformly lower".

Statistics: Wilcoxon signed-rank test on d (zero differences dropped), at
alpha = 0.05 per test. T1 and T2 are one-sided because each direction was
predicted before testing; T3 is two-sided. Reported alongside: the statistic
W (sum of ranks of positive d), rank-biserial correlation as effect size, the
median d, the usage-weighted mean d, and the share of tasks with d > 0. A
Bonferroni-adjusted p (over every test row) is a stricter robustness check.
With ~1,000+ tasks per period, p-values will be tiny for almost any
difference, so read the effect sizes, not the p-values.

Weekly releases publish counts, so tasks with fewer than MIN_CLASSIFIED
classified records on either platform are dropped (and the unfiltered result
is reported as a sensitivity check). The monthly release publishes no counts;
its own privacy thresholds are the only filter.

Input: the harmonized panel from harmonize.py (data/processed/task_panel.csv),
so the tests share task keys and definitions with the regression.

Run from the repo root:  python src/harmonize.py  then  python src/hypothesis_tests.py
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon, rankdata

from releases import DATA_DIR

PANEL = DATA_DIR / "processed" / "task_panel.csv"  # built by harmonize.py
MIN_CLASSIFIED = 30
ALPHA = 0.05
OUT_DIR = Path("figures")
OUT_DIR.mkdir(exist_ok=True)

INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
API_COLOR = "#2a78d6"

# Alternative hypothesis for each test, as used by scipy's wilcoxon on d = API - Claude.ai.
ALTERNATIVE = {"T1": "less", "T2": "greater", "T3": "two-sided"}

TESTS = {
    "T1": "Feedback loop, % of classified",
    "T2": "Single-turn automation, directive / (directive + learning + validation) %",
    "T3": "AI autonomy, mean (1-5)",
}


def single_turn_automation(t: pd.DataFrame) -> pd.Series:
    denom = t["directive"] + t["learning"] + t["validation"]
    return (t["directive"] / denom * 100).where(denom > 0)


def paired(api: pd.Series, cai: pd.Series, weight: pd.Series, alternative: str) -> dict:
    """Paired comparison over tasks present (non-missing) on both platforms."""
    both = pd.DataFrame({"api": api, "cai": cai, "w": weight}).dropna(subset=["api", "cai"])
    d = both["api"] - both["cai"]
    nz = d[d != 0]
    ranks = rankdata(nz.abs())
    r_rb = (ranks[nz > 0].sum() - ranks[nz < 0].sum()) / ranks.sum() if len(nz) else np.nan
    test = wilcoxon(nz, alternative=alternative) if len(nz) > 0 else None
    w_plus = ranks[nz > 0].sum() if len(nz) else np.nan
    w = both["w"].fillna(0)
    return {
        "n_tasks": len(both),
        "api_mean": both["api"].mean(),
        "claude_mean": both["cai"].mean(),
        "median_d": d.median(),
        "weighted_mean_d": (d * w).sum() / w.sum() if w.sum() > 0 else np.nan,
        "pct_api_higher": (d > 0).mean() * 100,
        "rank_biserial": r_rb,
        "n_nonzero": len(nz),
        "W": w_plus,
        "p_value": test.pvalue if test is not None else np.nan,
        "d": d,
    }


def load_panel() -> pd.DataFrame:
    if not PANEL.exists():
        raise SystemExit(f"{PANEL} not found. Run `python src/harmonize.py` first.")
    return pd.read_csv(PANEL)


def run():
    """Every test reads the harmonized panel built by harmonize.py, so these
    results use the same task keys and definitions as the regression."""
    panel = load_panel()
    rows, diffs = [], []
    periods = panel.drop_duplicates("period").sort_values("period_start")
    for _, prow in periods.iterrows():
        period, release, regime = prow["period"], prow["release"], prow["regime"]
        sub = panel[panel["period"] == period]
        api = sub[sub["platform"] == "api"].set_index("task_key")
        cai = sub[sub["platform"] == "claude_ai"].set_index("task_key")
        weight = api["usage"].add(cai["usage"], fill_value=0)
        variants = [("all", api.index.intersection(cai.index))]
        if regime == "weekly":
            keep = api.index[api["classified_n"] >= MIN_CLASSIFIED].intersection(
                cai.index[cai["classified_n"] >= MIN_CLASSIFIED])
            variants = [(f"n>={MIN_CLASSIFIED}", keep)] + variants

        for subset, idx in variants:
            cases = {
                "T1": (api.loc[idx, "feedback_loop"], cai.loc[idx, "feedback_loop"]),
                "T2": (single_turn_automation(api.loc[idx]), single_turn_automation(cai.loc[idx])),
            }
            if api["ai_autonomy"].notna().any() and cai["ai_autonomy"].notna().any():
                cases["T3"] = (api.loc[idx, "ai_autonomy"], cai.loc[idx, "ai_autonomy"])
            for test, (a, c) in cases.items():
                res = paired(a, c, weight.reindex(idx), ALTERNATIVE[test])
                d = res.pop("d")
                rows.append({"test": test, "release": release, "period": period,
                             "subset": subset, **res})
                if subset != "all" or regime == "monthly":
                    diffs.append((test, period, d))

    results = pd.DataFrame(rows)
    results["p_bonferroni"] = (results["p_value"] * len(results)).clip(upper=1)
    results["reject_H0"] = results["p_value"] < ALPHA
    results["reject_H0_bonferroni"] = results["p_bonferroni"] < ALPHA
    return results, diffs


def plot(diffs):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    for ax, test in zip(axes, TESTS):
        data = [(p, d.values) for t, p, d in diffs if t == test]
        ax.boxplot([d for _, d in data], showfliers=False, widths=0.5,
                   medianprops=dict(color=API_COLOR, linewidth=2),
                   boxprops=dict(color=INK_MUTED), whiskerprops=dict(color=INK_MUTED),
                   capprops=dict(color=INK_MUTED))
        ax.set_xticks(range(1, len(data) + 1), [p for p, _ in data], rotation=20, ha="right")
        ax.axhline(0, color=INK, linestyle="--", linewidth=1)
        ax.set_title(f"{test}: {TESTS[test]}", fontsize=9, color=INK)
        ax.set_ylabel("API minus Claude.ai, per task")
        ax.grid(axis="y", color=GRID)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Measurement-asymmetry tests: paired per-task differences on shared tasks "
                 f"(weekly: tasks with >= {MIN_CLASSIFIED} classified records; whiskers 1.5 IQR)",
                 color=INK)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "hypothesis_tests.png", dpi=150)
    plt.close(fig)
    print("Saved figures/hypothesis_tests.png")


def main():
    results, diffs = run()
    cols = ["release", "period", "subset", "n_tasks", "api_mean", "claude_mean", "median_d",
            "weighted_mean_d", "pct_api_higher", "rank_biserial", "n_nonzero", "W", "p_value",
            "reject_H0", "p_bonferroni", "reject_H0_bonferroni"]
    for test, label in TESTS.items():
        print(f"\n{'=' * 70}\n{test}: {label}  (H1 alternative: {ALTERNATIVE[test]})\n{'=' * 70}")
        sub = results[results["test"] == test][cols]
        print(sub.to_markdown(index=False, floatfmt=".3g"))
    print(f"\nalpha = {ALPHA} per test; Bonferroni over {len(results)} test rows as a robustness check. "
          f"d = API - Claude.ai on the same task.")
    plot(diffs)


if __name__ == "__main__":
    main()
