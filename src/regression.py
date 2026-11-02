"""
regression.py

Linear regressions on the harmonized task panel (harmonize.py). The unit is
a task x platform x period row; the outcome is automation_pct, the task's
automation share of classified conversations (0-100). All models use
weighted least squares with standard errors clustered by task, and alpha =
0.05.

  Model 1  The gap on the same task, per period, and whether it changed.
           automation ~ API x period, with a task x period fixed effect.
           The fixed effect means each task is only compared with itself in
           the same period, so each API x period coefficient is the
           within-task API vs. Claude.ai gap (pp) for that period. Wald
           tests check whether the gap changed WITHIN each regime; the
           cross-regime difference is reported but not interpreted, because
           the method changed at the break.
           Sample: tasks published on both platforms. Weight: the task's
           combined usage share in the period (same weight for both rows).

  Model 2  What predicts the automation LEVEL on each platform.
           automation ~ task characteristics + major group + period,
           run separately for each platform x regime. Characteristics are
           standardized (z-scores within the sample), so coefficients are
           pp of automation per 1 SD and can be compared with each other.
           Weight: the row's usage share.

  Model 3  What predicts the size of the GAP.
           automation ~ API + API x task characteristics, with a task x
           period fixed effect, run separately for each regime. The API
           coefficient is the gap at an average task; each API x
           characteristic coefficient is how much the gap changes (pp) per
           1 SD of that characteristic. Characteristics here are the task's
           average across the two platforms in the period.

Task characteristics (2026-01-15 release onwards, so Models 2-3 drop
Aug 2025): human_education_years, log(1 + human_only_time),
log(1 + human_with_ai_time), multitasking_pct, human_only_ability_pct,
use_case_work_pct. Left out on purpose: ai_education_years (r = 0.92 with
human_education_years), use_case_personal_pct (r = -0.86 with work), and
ai_autonomy (another measure of delegation, tested in hypothesis_tests.py,
not a characteristic of the task).

Fixed effects are absorbed by weighted within-group demeaning. Clustering
is by task, and every fixed-effect group sits inside one task cluster, so
no degrees-of-freedom correction for the absorbed effects is needed.

Run from the repo root:  python src/harmonize.py  then  python src/regression.py
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from releases import DATA_DIR

PANEL = DATA_DIR / "processed" / "task_panel.csv"
OUT_DIR = Path("figures")
OUT_DIR.mkdir(exist_ok=True)
ALPHA = 0.05
MIN_CLASSIFIED = 30
ROUNDED_ZERO_USAGE = 0.0025  # midpoint of [0, 0.005), see load_panel

PREDICTORS = {
    "human_education_years": "Human education (years)",
    "log_human_only_time": "log human-only time",
    "log_human_with_ai_time": "log human-with-AI time",
    "multitasking_pct": "Multitasking (%)",
    "human_only_ability_pct": "Human-only ability (%)",
    "use_case_work_pct": "Work use (%)",
}

INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
API_COLOR, CAI_COLOR = "#2a78d6", "#eb6834"


def load_panel() -> pd.DataFrame:
    if not PANEL.exists():
        raise SystemExit(f"{PANEL} not found. Run `python src/harmonize.py` first.")
    p = pd.read_csv(PANEL)
    p["api"] = (p["platform"] == "api").astype(float)
    p["log_human_only_time"] = np.log1p(p["human_only_time"])
    p["log_human_with_ai_time"] = np.log1p(p["human_with_ai_time"])
    p["group"] = p["task_key"] + " | " + p["period"]
    # The monthly release rounds task shares to 2 decimals, so ~half of its
    # tasks show usage = 0.00 (true share < 0.005%). For weighting only, give
    # them the midpoint of that rounding interval instead of a zero weight.
    p["usage_w"] = p["usage"].where(p["usage"] > 0, ROUNDED_ZERO_USAGE)
    return p


def demean(df: pd.DataFrame, cols: list, group: str, weight: str) -> pd.DataFrame:
    """Weighted within-group demeaning (absorbs a fixed effect per group)."""
    w = df[weight]
    out = df.copy()
    for c in cols:
        mean = (df[c] * w).groupby(df[group]).transform("sum") / w.groupby(df[group]).transform("sum")
        out[c] = df[c] - mean
    return out


def wls(y, X, w, clusters):
    return sm.WLS(y, X, weights=w).fit(cov_type="cluster", cov_kwds={"groups": clusters})


def coef_table(fit, names: dict = None) -> pd.DataFrame:
    ci = fit.conf_int(alpha=ALPHA)
    t = pd.DataFrame({"coef": fit.params, "se": fit.bse, "ci_low": ci[0], "ci_high": ci[1],
                      "p": fit.pvalues})
    t["reject_H0"] = t["p"] < ALPHA
    if names:
        t.index = [names.get(i, i) for i in t.index]
    return t


def pair_weight(df: pd.DataFrame) -> pd.Series:
    """Combined usage of the task in the period, the same for both platform rows."""
    return df.groupby("group")["usage_w"].transform("sum")


# ---- Model 1: within-task gap per period -------------------------------

def model1(p: pd.DataFrame, weighted: bool = True, min_n: int = 0) -> tuple:
    d = p[p["on_both_platforms"]].copy()
    if min_n:
        small = d["classified_n"].notna() & (d["classified_n"] < min_n)
        d = d[~d["group"].isin(d.loc[small, "group"])]
    d["w"] = pair_weight(d) if weighted else 1.0
    periods = d.drop_duplicates("period").sort_values("period_start")["period"].tolist()
    cols = []
    for per in periods:
        c = f"gap[{per}]"
        d[c] = d["api"] * (d["period"] == per)
        cols.append(c)
    dm = demean(d, ["automation_pct"] + cols, "group", "w")
    fit = wls(dm["automation_pct"], dm[cols], d["w"], d["task_key"])
    return fit, periods, d


def gap_change_tests(fit, periods, regimes: dict) -> pd.DataFrame:
    rows = []
    for regime, pers in regimes.items():
        names = [f"gap[{p}]" for p in pers]
        if len(names) < 2:
            continue
        r = np.zeros((len(names) - 1, len(fit.params)))
        for i in range(len(names) - 1):
            r[i, fit.params.index.get_loc(names[i])] = 1
            r[i, fit.params.index.get_loc(names[i + 1])] = -1
        test = fit.wald_test(r, scalar=True)
        rows.append({"regime": regime, "H0": " = ".join(f"gap({p})" for p in pers),
                     "statistic": float(test.statistic), "df": len(names) - 1,
                     "p": float(test.pvalue), "reject_H0": float(test.pvalue) < ALPHA})
    # Cross-regime contrast: mean monthly gap minus mean weekly gap (not interpreted causally).
    r = np.zeros((1, len(fit.params)))
    for p in regimes["weekly"]:
        r[0, fit.params.index.get_loc(f"gap[{p}]")] = -1 / len(regimes["weekly"])
    for p in regimes["monthly"]:
        r[0, fit.params.index.get_loc(f"gap[{p}]")] = 1 / len(regimes["monthly"])
    test = fit.t_test(r)
    rows.append({"regime": "monthly vs weekly (method change, descriptive only)",
                 "H0": "mean monthly gap = mean weekly gap",
                 "statistic": np.asarray(test.tvalue).item(), "df": 1,
                 "p": np.asarray(test.pvalue).item(),
                 "reject_H0": np.asarray(test.pvalue).item() < ALPHA,
                 "difference_pp": np.asarray(test.effect).item()})
    return pd.DataFrame(rows)


# ---- Model 2: predictors of automation level ---------------------------

def standardize(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        out[c] = (df[c] - df[c].mean()) / df[c].std()
    return out


def vif_table(df: pd.DataFrame, cols: list) -> pd.Series:
    X = sm.add_constant(df[cols])
    return pd.Series([variance_inflation_factor(X.values, i + 1) for i in range(len(cols))],
                     index=[PREDICTORS[c] for c in cols])


def model2(p: pd.DataFrame, platform: str, regime: str):
    cols = list(PREDICTORS)
    d = p[(p["platform"] == platform) & (p["regime"] == regime)]
    d = d.dropna(subset=cols + ["major_group", "automation_pct", "usage_w"])
    d = standardize(d, cols)
    X = pd.concat([d[cols],
                   pd.get_dummies(d["major_group"], prefix="mg", drop_first=True, dtype=float),
                   pd.get_dummies(d["period"], prefix="period", drop_first=True, dtype=float)],
                  axis=1)
    X = sm.add_constant(X)
    fit = wls(d["automation_pct"], X, d["usage_w"], d["task_key"])
    return fit, d


# ---- Model 3: predictors of the gap ------------------------------------

def model3(p: pd.DataFrame, regime: str):
    cols = list(PREDICTORS)
    d = p[(p["regime"] == regime) & p["on_both_platforms"]].copy()
    # Task characteristic = average of the two platforms' values in the period.
    for c in cols:
        d[c] = d.groupby("group")[c].transform("mean")
    d = d.dropna(subset=cols)
    d = d[d.groupby("group")["platform"].transform("nunique") == 2]
    d = standardize(d, cols)
    d["w"] = pair_weight(d)
    inter = []
    for c in cols:
        d[f"api_x_{c}"] = d["api"] * d[c]
        inter.append(f"api_x_{c}")
    regs = ["api"] + inter
    dm = demean(d, ["automation_pct"] + regs, "group", "w")
    fit = wls(dm["automation_pct"], dm[regs], d["w"], d["task_key"])
    names = {"api": "API gap at an average task"}
    names.update({f"api_x_{c}": f"API x {PREDICTORS[c]}" for c in cols})
    return fit, d, names


# ---- Figures -----------------------------------------------------------

OVERALL_GAP = {  # classified-share gap from inventory.py (PROFILE.md §1), for comparison
    "2025-08-04 (1 wk)": 35.10, "2025-11-13 (1 wk)": 37.13, "2026-02-05 (1 wk)": 34.20,
    "2026-04": 44.69, "2026-05": 45.59,
}


def plot_gap(fit, periods):
    t = coef_table(fit)
    x = np.arange(len(periods))
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.bar(x - 0.2, [OVERALL_GAP[p] for p in periods], width=0.38, color=GRID,
           edgecolor=INK_MUTED, label="Overall gap (different task mixes)")
    est = t.loc[[f"gap[{p}]" for p in periods]]
    ax.bar(x + 0.2, est["coef"], width=0.38, color=API_COLOR, label="Same-task gap (Model 1)")
    ax.errorbar(x + 0.2, est["coef"], yerr=[est["coef"] - est["ci_low"], est["ci_high"] - est["coef"]],
                fmt="none", ecolor=INK, capsize=4, linewidth=1)
    for xi, v, hi in zip(x + 0.2, est["coef"], est["ci_high"]):
        ax.text(xi, hi + 1, f"{v:.1f}", ha="center", fontsize=8, color=INK)
    for xi, p in zip(x - 0.2, periods):
        ax.text(xi, OVERALL_GAP[p] + 1, f"{OVERALL_GAP[p]:.1f}", ha="center", fontsize=8, color=INK_MUTED)
    ax.axvline(2.5, color=INK_MUTED, linestyle="--", linewidth=1)
    ax.text(2.45, 52, "method change", ha="right", fontsize=8, color=INK_MUTED)
    ax.set_xticks(x, periods, rotation=15)
    ax.set_ylabel("API minus Claude.ai automation (pp)")
    ax.set_ylim(0, 55)
    ax.set_title("Automation gap: overall vs. on the same task (95% CI, clustered by task)")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "regression_gap_by_period.png", dpi=150)
    plt.close(fig)
    print("Saved figures/regression_gap_by_period.png")


def plot_coefficients(m2: dict, m3: dict):
    labels = list(PREDICTORS.values())
    y = np.arange(len(labels))
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)

    styles = {("api", "weekly"): (API_COLOR, "o", "full"), ("api", "monthly"): (API_COLOR, "o", "none"),
              ("claude_ai", "weekly"): (CAI_COLOR, "s", "full"),
              ("claude_ai", "monthly"): (CAI_COLOR, "s", "none")}
    offsets = dict(zip(styles, [-0.27, -0.09, 0.09, 0.27]))
    for key, t in m2.items():
        color, marker, fill = styles[key]
        t = t.loc[labels]
        axes[0].errorbar(t["coef"], y + offsets[key], xerr=[t["coef"] - t["ci_low"], t["ci_high"] - t["coef"]],
                         fmt=marker, color=color, fillstyle=fill, markersize=6, capsize=2,
                         linewidth=1, label=f"{'API' if key[0] == 'api' else 'Claude.ai'}, {key[1]}")
    axes[0].set_title("Model 2: automation level\n(pp per 1 SD, within platform and regime)", fontsize=10)

    for i, (regime, t) in enumerate(m3.items()):
        t = t.loc[[f"API x {l}" for l in labels]]
        axes[1].errorbar(t["coef"], y + (-0.12 if i == 0 else 0.12),
                         xerr=[t["coef"] - t["ci_low"], t["ci_high"] - t["coef"]],
                         fmt="o", color=API_COLOR, fillstyle="full" if regime == "weekly" else "none",
                         markersize=6, capsize=2, linewidth=1, label=regime)
    axes[1].set_title("Model 3: size of the same-task gap\n(pp change in gap per 1 SD)", fontsize=10)

    for ax in axes:
        ax.axvline(0, color=INK, linestyle="--", linewidth=1)
        ax.grid(axis="x", color=GRID)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.08),
                  ncol=4 if ax is axes[0] else 2)
    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    fig.suptitle("Task characteristics associated with automation (95% CI, clustered by task)", color=INK)
    plt.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT_DIR / "regression_coefficients.png", dpi=150)
    plt.close(fig)
    print("Saved figures/regression_coefficients.png")


# ---- Main ---------------------------------------------------------------

def show(title, frame):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")
    print(frame.to_markdown(floatfmt=".3g"))


def main():
    p = load_panel()

    # Model 1
    fit1, periods, d1 = model1(p)
    regimes = {r: d1.loc[d1["regime"] == r].drop_duplicates("period").sort_values("period_start")["period"].tolist()
               for r in ["weekly", "monthly"]}
    t1 = coef_table(fit1)
    t1["overall_gap"] = [OVERALL_GAP[i[4:-1]] for i in t1.index]
    t1["same_task_share_of_overall_%"] = t1["coef"] / t1["overall_gap"] * 100
    t1["n_tasks"] = [d1.loc[d1["period"] == i[4:-1], "task_key"].nunique() for i in t1.index]
    show(f"MODEL 1: same-task gap per period (pp). n = {int(fit1.nobs):,} rows, "
         f"{d1['task_key'].nunique():,} task clusters", t1)
    show("MODEL 1: has the gap changed? (Wald tests, alpha = 0.05)", gap_change_tests(fit1, periods, regimes))

    rob = pd.DataFrame({
        "weighted (main)": coef_table(fit1)["coef"],
        "unweighted": coef_table(model1(p, weighted=False)[0])["coef"],
        f"weekly tasks n>={MIN_CLASSIFIED}": coef_table(model1(p, min_n=MIN_CLASSIFIED)[0])["coef"],
    })
    show("MODEL 1 robustness: same-task gap (pp) under alternative choices", rob)

    # Model 2
    m2 = {}
    for regime in ["weekly", "monthly"]:
        for platform in ["api", "claude_ai"]:
            fit, d = model2(p, platform, regime)
            t = coef_table(fit, PREDICTORS)
            m2[(platform, regime)] = t
            show(f"MODEL 2: automation level, {platform}, {regime} "
                 f"(n = {int(fit.nobs):,}, tasks = {d['task_key'].nunique():,}, R² = {fit.rsquared:.3f}). "
                 f"Major group and period dummies not shown.",
                 t.loc[list(PREDICTORS.values())])
            if (platform, regime) == ("claude_ai", "weekly"):
                show("VIF of the predictors (Claude.ai, weekly; > 5 would signal collinearity)",
                     vif_table(d, list(PREDICTORS)).to_frame("VIF"))

    # Model 3
    m3 = {}
    for regime in ["weekly", "monthly"]:
        fit, d, names = model3(p, regime)
        t = coef_table(fit, names)
        m3[regime] = t
        show(f"MODEL 3: size of the same-task gap, {regime} "
             f"(n = {int(fit.nobs):,} rows, tasks = {d['task_key'].nunique():,})", t)

    plot_gap(fit1, periods)
    plot_coefficients(m2, m3)


if __name__ == "__main__":
    main()
