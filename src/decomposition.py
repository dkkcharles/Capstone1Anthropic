"""
decomposition.py

Splits each period's API vs. Claude.ai automation gap into parts that add up
exactly, using the harmonized task panel (harmonize.py).

For platform p, the automation share rebuilt from published tasks is
    A_p = sum_i w_pi * a_pi
where a_pi is task i's automation share of classified conversations and
w_pi is task i's share of the platform's classified conversations:
usage_pi * (1 - none_pi / 100), renormalized over published tasks. (The
monthly release rounds usage to 2 decimals; rows shown as 0.00 get 0.0025,
the midpoint of the rounding interval, as in regression.py.)

The rebuilt gap G = A_api - A_claude splits into:

  Unshared   (A_api - A_api^S) - (A_claude - A_claude^S)
             The effect of tasks published on only one platform. A_p^S is
             the platform's automation share over shared tasks S only, with
             weights renormalized within S.
  Task mix   sum_{i in S} (w~_api,i - w~_claude,i) * a_ref,i
             The platforms spend different shares of their usage on each
             shared task.
  Behavior   sum_{i in S} w~_ref,i * (a_api,i - a_claude,i)
             The platforms automate the same task differently.

Mix + behavior = A_api^S - A_claude^S, the shared-task gap. Which platform
supplies the reference rates/weights changes the split (the index-number
problem), so both orderings are reported:
  ordering A: mix at Claude.ai rates,  behavior at API weights
  ordering B: mix at API rates,        behavior at Claude.ai weights
and their average (the Shapley split) is the headline.

Uncertainty: 95% percentile intervals from a bootstrap that resamples tasks
(with replacement) within each period, N_BOOT times. Sampling error in the
underlying ~1M conversations is negligible (PROFILE.md), so this captures
how much the result depends on which tasks happen to be published.

The rebuilt gap is compared with the published global gap (inventory.py);
the difference is what unpublished tasks contribute.

Run from the repo root:  python src/harmonize.py  then  python src/decomposition.py
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from releases import DATA_DIR

PANEL = DATA_DIR / "processed" / "task_panel.csv"
OUT_DIR = Path("figures")
OUT_DIR.mkdir(exist_ok=True)
ROUNDED_ZERO_USAGE = 0.0025
N_BOOT = 1000
SEED = 0

# Published global gap, classified definition (inventory.py, PROFILE.md §1).
PUBLISHED_GAP = {
    "2025-08-04 (1 wk)": 35.10, "2025-11-13 (1 wk)": 37.13, "2026-02-05 (1 wk)": 34.20,
    "2026-04": 44.69, "2026-05": 45.59,
}

INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
COLORS = {"behavior": "#2a78d6", "mix": "#eb6834", "unshared": "#b5b4ad"}


def load_panel() -> pd.DataFrame:
    if not PANEL.exists():
        raise SystemExit(f"{PANEL} not found. Run `python src/harmonize.py` first.")
    p = pd.read_csv(PANEL)
    usage = p["usage"].where(p["usage"] > 0, ROUNDED_ZERO_USAGE)
    p["w"] = usage * (1 - p["none_pct"].fillna(0) / 100)
    return p


def wide(period_rows: pd.DataFrame) -> pd.DataFrame:
    """One row per task: weight and automation on each platform (NaN if absent)."""
    w = period_rows.pivot_table(index="task_key", columns="platform", values="w")
    a = period_rows.pivot_table(index="task_key", columns="platform", values="automation_pct")
    return pd.DataFrame({"w_api": w.get("api"), "w_cai": w.get("claude_ai"),
                         "a_api": a.get("api"), "a_cai": a.get("claude_ai")})


def decompose(t: pd.DataFrame) -> dict:
    """Exact decomposition for one period from the task-level frame `t`."""
    out = {}
    for p in ["api", "cai"]:
        has = t[f"w_{p}"].notna()
        w = t.loc[has, f"w_{p}"] / t.loc[has, f"w_{p}"].sum()
        out[f"A_{p}"] = (w * t.loc[has, f"a_{p}"]).sum()

    s = t.dropna()  # shared tasks
    wa = s["w_api"] / s["w_api"].sum()
    wc = s["w_cai"] / s["w_cai"].sum()
    A_api_s = (wa * s["a_api"]).sum()
    A_cai_s = (wc * s["a_cai"]).sum()
    diff = s["a_api"] - s["a_cai"]

    mix_a = ((wa - wc) * s["a_cai"]).sum()       # ordering A
    beh_a = (wa * diff).sum()
    mix_b = ((wa - wc) * s["a_api"]).sum()       # ordering B
    beh_b = (wc * diff).sum()

    out.update({
        "gap": out["A_api"] - out["A_cai"],
        "unshared": (out["A_api"] - A_api_s) - (out["A_cai"] - A_cai_s),
        "shared_gap": A_api_s - A_cai_s,
        "mix_A": mix_a, "behavior_A": beh_a,
        "mix_B": mix_b, "behavior_B": beh_b,
        "mix": (mix_a + mix_b) / 2, "behavior": (beh_a + beh_b) / 2,
        "n_shared": len(s),
        "api_weight_in_shared": t.loc[s.index, "w_api"].sum() / t["w_api"].sum() * 100,
        "cai_weight_in_shared": t.loc[s.index, "w_cai"].sum() / t["w_cai"].sum() * 100,
    })
    return out


def bootstrap(t: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    keys = ["gap", "unshared", "mix", "behavior"]
    draws = []
    idx = np.arange(len(t))
    for _ in range(N_BOOT):
        sample = t.iloc[rng.choice(idx, size=len(idx), replace=True)].reset_index(drop=True)
        d = decompose(sample)
        draws.append({k: d[k] for k in keys})
    return pd.DataFrame(draws)


def run(p: pd.DataFrame):
    rng = np.random.default_rng(SEED)
    rows, cis = [], {}
    periods = p.drop_duplicates("period").sort_values("period_start")
    for _, prow in periods.iterrows():
        per = prow["period"]
        t = wide(p[p["period"] == per])
        d = decompose(t)
        boot = bootstrap(t, rng)
        cis[per] = boot.quantile([0.025, 0.975])
        rows.append({"release": prow["release"], "regime": prow["regime"], "period": per,
                     "published_gap": PUBLISHED_GAP[per], **d})
    res = pd.DataFrame(rows)
    res["unpublished"] = res["published_gap"] - res["gap"]
    for k in ["unshared", "mix", "behavior"]:
        res[f"{k}_%"] = res[k] / res["gap"] * 100
    return res, cis


def fmt_ci(cis, per, k):
    lo, hi = cis[per].loc[0.025, k], cis[per].loc[0.975, k]
    return f"{lo:.1f} to {hi:.1f}"


def plot(res: pd.DataFrame):
    x = np.arange(len(res))
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    bottom_pos = np.zeros(len(res))
    bottom_neg = np.zeros(len(res))
    for k, label in [("behavior", "Behavior on the same task"), ("mix", "Task mix (shared tasks)"),
                     ("unshared", "Tasks on one platform only")]:
        v = res[k].values
        base = np.where(v >= 0, bottom_pos, bottom_neg)
        ax.bar(x, v, bottom=base, color=COLORS[k], width=0.6, edgecolor="white", linewidth=1.5,
               label=label)
        bottom_pos += np.where(v >= 0, v, 0)
        bottom_neg += np.where(v < 0, v, 0)
    ax.scatter(x, res["gap"], marker="_", s=600, color=INK, linewidths=2, zorder=3,
               label="Rebuilt gap (sum of parts)")
    for xi, g, b in zip(x, res["gap"], res["behavior_%"]):
        ax.text(xi, max(g, 0) + 2, f"{g:.1f} pp\nbehavior {b:.0f}%", ha="center", fontsize=8, color=INK)
    ax.axhline(0, color=INK, linewidth=0.8)
    ax.axvline(2.5, color=INK_MUTED, linestyle="--", linewidth=1)
    ax.text(2.45, 56, "method change", ha="right", fontsize=8, color=INK_MUTED)
    ax.set_xticks(x, res["period"], rotation=15)
    ax.set_ylabel("Contribution to API minus Claude.ai gap (pp)")
    ax.set_ylim(min(0, bottom_neg.min() - 2), 62)
    ax.set_title("Decomposition of the automation gap (Shapley average of both orderings)")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "gap_decomposition.png", dpi=150)
    plt.close(fig)
    print("Saved figures/gap_decomposition.png")


def main():
    p = load_panel()
    res, cis = run(p)

    print(f"\n{'=' * 78}\nDECOMPOSITION (pp; Shapley average; 95% bootstrap CI over tasks, "
          f"{N_BOOT} draws)\n{'=' * 78}")
    table = pd.DataFrame({
        "Period": res["period"],
        "Published gap": res["published_gap"].round(2),
        "Rebuilt gap": res["gap"].round(2),
        "Unpublished (published - rebuilt)": res["unpublished"].round(2),
        "Behavior": res["behavior"].round(2),
        "Behavior CI": [fmt_ci(cis, p_, "behavior") for p_ in res["period"]],
        "Mix": res["mix"].round(2),
        "Mix CI": [fmt_ci(cis, p_, "mix") for p_ in res["period"]],
        "Unshared": res["unshared"].round(2),
        "Unshared CI": [fmt_ci(cis, p_, "unshared") for p_ in res["period"]],
        "Behavior %": res["behavior_%"].round(1),
        "Mix %": res["mix_%"].round(1),
        "Unshared %": res["unshared_%"].round(1),
    })
    print(table.to_markdown(index=False))

    print(f"\n{'=' * 78}\nBOTH ORDERINGS (index-number check)\n{'=' * 78}")
    print(res[["period", "shared_gap", "mix_A", "behavior_A", "mix_B", "behavior_B"]]
          .round(2).to_markdown(index=False))
    print("  A: mix at Claude.ai rates, behavior at API weights. "
          "B: mix at API rates, behavior at Claude.ai weights.")

    print(f"\n{'=' * 78}\nCOVERAGE OF SHARED TASKS\n{'=' * 78}")
    print(res[["period", "n_shared", "api_weight_in_shared", "cai_weight_in_shared", "A_api", "A_cai"]]
          .round(2).to_markdown(index=False))

    print(f"\n{'=' * 78}\nCHANGE WITHIN EACH REGIME (pp, later period minus earlier)\n{'=' * 78}")
    rows = []
    for regime, g in res.groupby("regime", sort=False):
        g = g.reset_index(drop=True)
        for i in range(1, len(g)):
            rows.append({"From": g.loc[i - 1, "period"], "To": g.loc[i, "period"],
                         **{k: round(g.loc[i, k] - g.loc[i - 1, k], 2)
                            for k in ["gap", "behavior", "mix", "unshared"]}})
    print(pd.DataFrame(rows).to_markdown(index=False))

    plot(res)


if __name__ == "__main__":
    main()
