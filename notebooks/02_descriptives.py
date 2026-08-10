"""
02_descriptives.py

Descriptive outputs for the VOC project.

What this script does
- Builds crosstabs (tables/*.csv) for:
  * region x rank_parent, counts and percentages
  * revised outcome group x rank_parent, counts and percentages
  * region x revised outcome group, counts and percentages

- Makes revised figures (figures/*.png):
  * fig_region_by_rank_parent.png
  * fig_rank_parent_by_outcome_revised.png
  * fig_trend_over_time_revised.png
  * fig_death_rate_and_first_contract_rate_by_decade.png
  * fig_first_contracts_vs_exits_by_rank_revised.png
  * fig_first_contracts_vs_exits_by_rank_1700s_revised.png ... fig_first_contracts_vs_exits_by_rank_1780s_revised.png
  * fig_outcome_rates_and_first_contract_share_by_rank_revised.png

- Saves revised descriptive tables, including:
  * trend_by_decade_revised.csv
  * first_contracts_vs_exits_by_rank_revised.csv
  * first_contracts_vs_exits_by_rank_1700s_revised.csv ... first_contracts_vs_exits_by_rank_1780s_revised.csv
  * outcome_rates_and_first_contract_share_by_decade_rank_revised.csv

- Updates docs/figure_captions_revised.txt.

Inputs produced by 01_cleaning.py
- data_clean/contracts_clean.csv

Main columns used
- outcome_group_revised
- outcome_group_for_descriptives
- is_first_contract_true
- first_contract_for_descriptives
- decade
- rank_parent
- region_label

Notes
- Labels on stacked bars appear only when a segment is >= 1%.
- First contracts are treated as a proxy for new workforce entry, not as a direct hiring rate.
- The revised figures compare first-contract patterns with major exit outcomes, especially Death and Repatriated.
- If revised columns are missing, the script falls back to older compatible columns where possible.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -------------------- Paths --------------------
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_CLEAN = os.path.join(BASE, "data_clean")
TABLES = os.path.join(BASE, "tables")
FIGURES = os.path.join(BASE, "figures")
DOCS = os.path.join(BASE, "docs")

os.makedirs(TABLES, exist_ok=True)
os.makedirs(FIGURES, exist_ok=True)
os.makedirs(DOCS, exist_ok=True)

# -------------------- Small helpers --------------------
def save_csv(df, path):
    df.to_csv(path, index=False)
    print(f"[saved] {path}")

def append_caption_once(path, line):
    """Append a caption line if it's not already present (no duplicates)."""
    existing = ""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = f.read()
    if line.strip() not in existing:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line if line.endswith("\n") else line + "\n")
        print(f"[updated] {path}")

def legend_outside(ax, loc="center left", bbox=(1.02, 0.5)):
    """Place legend outside the plotting area on the right."""
    leg = ax.legend(loc=loc, bbox_to_anchor=bbox, borderaxespad=0.0, frameon=False)
    return leg

def stacked_bar_with_threshold_labels(pct_df, title, out_path, ylabel="Share", legend_title=None):
    """
    Draw stacked bars from a percentage table (0-100). Label only segments >= 1%.
    pct_df: rows=x categories, columns=segments; values already in percent (0-100).
    """
    if pct_df.empty or pct_df.shape[1] == 0:
        print(f"[warn] Skip plot {out_path}: empty pivot"); return

    pct = pct_df.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    frac = pct / 100.0

    fig, ax = plt.subplots(figsize=(10.5, 6))  # a bit wider to make space
    frac.plot(kind="bar", stacked=True, ax=ax)

    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticklabels([str(i) for i in frac.index], rotation=0)

    # Labels only for segments >= 1%
    x_idx = np.arange(len(frac))
    cum = np.zeros(len(frac), dtype=float)
    for col in frac.columns:
        vals = frac[col].to_numpy()
        bottoms = cum.copy()
        cum += vals
        for xi, v, b in zip(x_idx, vals, bottoms):
            if v <= 0: 
                continue
            pct_val = v * 100.0
            if pct_val >= 1.0:
                y = b + v / 2.0
                ax.text(xi, y, f"{pct_val:.1f}%", ha="center", va="center", fontsize=7)

    # Legend placed outside on the right
    lg = legend_outside(ax)
    if legend_title and lg:
        lg.set_title(legend_title)

    # Leave extra room on the right for the legend
    plt.subplots_adjust(right=0.78)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()
    print(f"[saved] {out_path}")

# -------------------- Load data --------------------
contracts_path = os.path.join(DATA_CLEAN, "contracts_clean.csv")
contracts = pd.read_csv(contracts_path, low_memory=False)

# -------------------- Revised column aliases --------------------
# 01_cleaning.py now creates outcome_group_revised and is_first_contract_true.
# I keep local aliases here so the descriptive script is explicit and easy to update.
if "outcome_group_revised" in contracts.columns:
    OUTCOME_COL = "outcome_group_revised"
elif "outcome_group" in contracts.columns:
    OUTCOME_COL = "outcome_group"
else:
    raise ValueError("No outcome grouping column found. Expected outcome_group_revised or outcome_group.")

if "is_first_contract_true" in contracts.columns:
    FIRST_CONTRACT_COL = "is_first_contract_true"
elif "is_first_contract" in contracts.columns:
    FIRST_CONTRACT_COL = "is_first_contract"
else:
    FIRST_CONTRACT_COL = None

# Keep compatibility columns so older parts of the script do not break while the script is being updated.
contracts["outcome_group_for_descriptives"] = contracts[OUTCOME_COL]

if FIRST_CONTRACT_COL is not None:
    contracts["first_contract_for_descriptives"] = contracts[FIRST_CONTRACT_COL]
else:
    contracts["first_contract_for_descriptives"] = 0

print(f"[info] Using outcome column: {OUTCOME_COL}")
print(f"[info] Using first-contract column: {FIRST_CONTRACT_COL}")

# -------------------- Defensive fallbacks --------------------
# Ensure decade exists
if "decade" not in contracts.columns:
    if "date_begin_contract" in contracts.columns:
        contracts["contract_start_year"] = pd.to_datetime(
            contracts["date_begin_contract"], errors="coerce"
        ).dt.year
        contracts["decade"] = (contracts["contract_start_year"] // 10) * 10
    elif "contract_start_year" in contracts.columns:
        contracts["decade"] = (contracts["contract_start_year"] // 10) * 10
    else:
        contracts["decade"] = np.nan

# Preferred visual order of ranks.
# I use the same order as in the revised benchmark script, so outputs are easier to compare.
RANK_ORDER = ["Sea", "Military", "Ship", "Other", "Medical", "Trade", "Unknown"]

# Revised outcome order used after updating 01_cleaning.py.
OUTCOME_ORDER = [
    "Death",
    "Repatriated",
    "Chamber",
    "Unknown / unclear",
    "Other",
    "Irregular exit",
]

# -------------------- Crosstabs (counts & %) --------------------
def crosstab_counts_and_pct(df, row, col, counts_path, pct_path):
    counts = pd.crosstab(df[row], df[col])
    save_csv(counts.reset_index().rename_axis(None, axis=1), counts_path)
    pct = pd.crosstab(df[row], df[col], normalize="index") * 100.0
    pct = pct.round(2)
    save_csv(pct.reset_index().rename_axis(None, axis=1), pct_path)
    return counts, pct

# the region x rank_parent
c1_path = os.path.join(TABLES, "region_by_rank_parent_count.csv")
p1_path = os.path.join(TABLES, "region_by_rank_parent_pct.csv")
counts_rp, pct_rp = crosstab_counts_and_pct(contracts, "region_label", "rank_parent", c1_path, p1_path)

# revised outcome group x rank_parent
c2_path = os.path.join(TABLES, "rank_parent_by_outcome_revised_count.csv")
p2_path = os.path.join(TABLES, "rank_parent_by_outcome_revised_pct.csv")
counts_or, pct_or = crosstab_counts_and_pct(
    contracts,
    "outcome_group_for_descriptives",
    "rank_parent",
    c2_path,
    p2_path
)

# Crosstab: geographic region x revised outcome group
c3_path = os.path.join(TABLES, "region_by_outcome_group_revised_count.csv")
p3_path = os.path.join(TABLES, "region_by_outcome_group_revised_pct.csv")
counts_ro, pct_ro = crosstab_counts_and_pct(
    contracts,
    "region_label",
    "outcome_group_for_descriptives",
    c3_path,
    p3_path
)

# -------------------- Figures: stacked bars (legend outside) --------------------
# Region by Rank (share within rank): rows=ranks, columns=regions
pct_rank_rows = pd.crosstab(
    contracts["rank_parent"], contracts["region_label"], normalize="index"
) * 100.0
pct_rank_rows = pct_rank_rows.round(2)
# reorder rows if possible
pct_rank_rows = pct_rank_rows.reindex([r for r in RANK_ORDER if r in pct_rank_rows.index], fill_value=0.0)

fig1 = os.path.join(FIGURES, "fig_region_by_rank_parent.png")
stacked_bar_with_threshold_labels(
    pct_rank_rows, "Region by Rank (share within rank)", fig1, ylabel="Share", legend_title="region_label"
)

# Rank by revised outcome group: rows=outcomes, columns=ranks
pct_outcome_rows = pd.crosstab(
    contracts["outcome_group_for_descriptives"],
    contracts["rank_parent"],
    normalize="index"
) * 100.0

pct_outcome_rows = pct_outcome_rows.round(2)

# Reorder outcome rows and rank columns where possible.
rows = [o for o in OUTCOME_ORDER if o in pct_outcome_rows.index] + [
    o for o in pct_outcome_rows.index if o not in OUTCOME_ORDER
]
cols = [r for r in RANK_ORDER if r in pct_outcome_rows.columns] + [
    c for c in pct_outcome_rows.columns if c not in RANK_ORDER
]

pct_outcome_rows = pct_outcome_rows.loc[rows, cols]

fig2 = os.path.join(FIGURES, "fig_rank_parent_by_outcome_revised.png")

stacked_bar_with_threshold_labels(
    pct_outcome_rows,
    "Parent rank distribution within revised outcome groups",
    fig2,
    ylabel="Share within revised outcome group",
    legend_title="Rank"
)

# -------------------- Revised trends by decade --------------------
def outcome_rate(series, outcome_name):
    """
    Calculate the share of records in a decade that belong to one revised outcome group.
    """
    series = series.astype(str)
    return np.mean(series == outcome_name) if series.notna().any() else np.nan


trend = (
    contracts.groupby("decade", as_index=False)
    .agg(
        foreign_share=("is_dutch", lambda s: 1 - s.mean() if s.notna().any() else np.nan),
        death_rate=("outcome_group_for_descriptives", lambda s: outcome_rate(s, "Death")),
        repatriated_rate=("outcome_group_for_descriptives", lambda s: outcome_rate(s, "Repatriated")),
        irregular_exit_rate=("outcome_group_for_descriptives", lambda s: outcome_rate(s, "Irregular exit")),
        high_rank_share=("is_high_rank", "mean"),
        first_contracts_n=("first_contract_for_descriptives", "sum"),
        contracts_n=("first_contract_for_descriptives", "size"),
    )
)

trend["first_contract_rate"] = trend["first_contracts_n"] / trend["contracts_n"]

trend_path = os.path.join(TABLES, "trend_by_decade_revised.csv")
save_csv(trend, trend_path)

t = trend.sort_values("decade").copy()

for col in [
    "foreign_share",
    "death_rate",
    "repatriated_rate",
    "irregular_exit_rate",
    "high_rank_share",
    "first_contract_rate",
]:
    t[col] = pd.to_numeric(t[col], errors="coerce")

fig, ax = plt.subplots(figsize=(10.5, 6))
ax.plot(t["decade"].to_numpy(), t["foreign_share"].to_numpy(), marker="o", label="Foreign share")
ax.plot(t["decade"].to_numpy(), t["death_rate"].to_numpy(), marker="o", label="Death rate")
ax.plot(t["decade"].to_numpy(), t["repatriated_rate"].to_numpy(), marker="o", label="Repatriated rate")
ax.plot(t["decade"].to_numpy(), t["irregular_exit_rate"].to_numpy(), marker="o", label="Irregular exit rate")
ax.plot(t["decade"].to_numpy(), t["high_rank_share"].to_numpy(), marker="o", label="High-rank share")
ax.set_xlabel("Decade")
ax.set_ylabel("Rate")
ax.set_title("Revised outcome and workforce trends by decade")
legend_outside(ax)
plt.subplots_adjust(right=0.78)
plt.tight_layout()

fig3 = os.path.join(FIGURES, "fig_trend_over_time_revised.png")
plt.savefig(fig3, dpi=180)
plt.close()
print(f"[saved] {fig3}")


# -------------------- Death rate and first-contract rate by decade --------------------
fig, ax = plt.subplots(figsize=(10.5, 6))
ax.plot(t["decade"].to_numpy(), t["death_rate"].to_numpy(), marker="o", label="Death rate")
ax.plot(t["decade"].to_numpy(), t["first_contract_rate"].to_numpy(), marker="o", label="First-contract rate")
ax.set_xlabel("Decade")
ax.set_ylabel("Rate")
ax.set_title("Death rate and first-contract rate by decade")
legend_outside(ax)
plt.subplots_adjust(right=0.78)
plt.tight_layout()

fig4 = os.path.join(FIGURES, "fig_death_rate_and_first_contract_rate_by_decade.png")
plt.savefig(fig4, dpi=180)
plt.close()
print(f"[saved] {fig4}")

# -------------------- Helper: per-rank first-contract and exit stats --------------------
def per_rank_first_contract_exit_stats(group_df):
    """
    Create a per-rank summary comparing first contracts with major exit outcomes.

    This uses:
    - first contracts as a proxy for new workforce entry
    - Death
    - Repatriated
    - Death + Repatriated

    The shares are distributional shares across rank groups, not within-rank rates.
    This matches the revised benchmark interpretation.
    """

    out = (
        group_df.groupby("rank_parent", as_index=False)
        .agg(
            contracts_n=("outcome_group_for_descriptives", "size"),
            first_contracts_n=("first_contract_for_descriptives", lambda s: (s == 1).sum()),
            deaths_n=("outcome_group_for_descriptives", lambda s: (s == "Death").sum()),
            repatriated_n=("outcome_group_for_descriptives", lambda s: (s == "Repatriated").sum()),
        )
    )

    out["death_repatriated_n"] = out["deaths_n"] + out["repatriated_n"]

    totals = {
        "contracts_n": out["contracts_n"].sum(),
        "first_contracts_n": out["first_contracts_n"].sum(),
        "deaths_n": out["deaths_n"].sum(),
        "repatriated_n": out["repatriated_n"].sum(),
        "death_repatriated_n": out["death_repatriated_n"].sum(),
    }

    out["all_records_share"] = np.where(
        totals["contracts_n"] > 0,
        out["contracts_n"] / totals["contracts_n"] * 100,
        np.nan
    ).round(2)

    out["first_contract_share"] = np.where(
        totals["first_contracts_n"] > 0,
        out["first_contracts_n"] / totals["first_contracts_n"] * 100,
        np.nan
    ).round(2)

    out["death_share"] = np.where(
        totals["deaths_n"] > 0,
        out["deaths_n"] / totals["deaths_n"] * 100,
        np.nan
    ).round(2)

    out["repatriated_share"] = np.where(
        totals["repatriated_n"] > 0,
        out["repatriated_n"] / totals["repatriated_n"] * 100,
        np.nan
    ).round(2)

    out["death_repatriated_share"] = np.where(
        totals["death_repatriated_n"] > 0,
        out["death_repatriated_n"] / totals["death_repatriated_n"] * 100,
        np.nan
    ).round(2)

    out["first_contract_minus_death_share"] = (
        out["first_contract_share"] - out["death_share"]
    ).round(2)

    out["first_contract_minus_repatriated_share"] = (
        out["first_contract_share"] - out["repatriated_share"]
    ).round(2)

    out["first_contract_minus_death_repatriated_share"] = (
        out["first_contract_share"] - out["death_repatriated_share"]
    ).round(2)

    out["death_rate_within_rank"] = np.where(
        out["contracts_n"] > 0,
        out["deaths_n"] / out["contracts_n"] * 100,
        np.nan
    ).round(2)

    out["repatriated_rate_within_rank"] = np.where(
        out["contracts_n"] > 0,
        out["repatriated_n"] / out["contracts_n"] * 100,
        np.nan
    ).round(2)

    out["death_repatriated_rate_within_rank"] = np.where(
        out["contracts_n"] > 0,
        out["death_repatriated_n"] / out["contracts_n"] * 100,
        np.nan
    ).round(2)

    out["rank_parent"] = pd.Categorical(
        out["rank_parent"],
        categories=RANK_ORDER,
        ordered=True
    )

    out = out.sort_values("rank_parent").reset_index(drop=True)

    return out


def plot_rank_first_contract_exit_shares(rank_df, title, output_path):
    """
    Plot distributional shares by rank.

    This figure compares:
      - first-contract share
      - death share
      - repatriated share
      - death + repatriated share
    """

    plot_df = rank_df.copy()
    plot_df["rank_parent"] = pd.Categorical(
        plot_df["rank_parent"],
        categories=RANK_ORDER,
        ordered=True
    )
    plot_df = plot_df.sort_values("rank_parent")

    x = np.arange(len(plot_df))
    width = 0.20

    y_first = pd.to_numeric(plot_df["first_contract_share"], errors="coerce").fillna(0.0).to_numpy()
    y_death = pd.to_numeric(plot_df["death_share"], errors="coerce").fillna(0.0).to_numpy()
    y_rep = pd.to_numeric(plot_df["repatriated_share"], errors="coerce").fillna(0.0).to_numpy()
    y_exit = pd.to_numeric(plot_df["death_repatriated_share"], errors="coerce").fillna(0.0).to_numpy()

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.bar(x - 1.5 * width, y_first, width, label="First-contract share")
    ax.bar(x - 0.5 * width, y_death, width, label="Death share")
    ax.bar(x + 0.5 * width, y_rep, width, label="Repatriated share")
    ax.bar(x + 1.5 * width, y_exit, width, label="Death + repatriated share")

    ax.set_xticks(x)
    ax.set_xticklabels(plot_df["rank_parent"].astype(str).tolist(), rotation=0)
    ax.set_ylabel("Share across rank groups (%)")
    ax.set_title(title)

    handles, labels = ax.get_legend_handles_labels()
    leg = ax.legend(handles, labels, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)
    leg.get_frame().set_alpha(0.9)

    ymax = float(np.nanmax(np.r_[y_first, y_death, y_rep, y_exit])) if len(plot_df) else 0.0
    ax.set_ylim(0, max(1.0, ymax) * 1.15)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {output_path}")


# -------------------- First contracts vs exits by rank, overall --------------------
overall_rank = per_rank_first_contract_exit_stats(contracts)

rank_tbl_path = os.path.join(TABLES, "first_contracts_vs_exits_by_rank_revised.csv")
save_csv(overall_rank, rank_tbl_path)

plot_rank_first_contract_exit_shares(
    overall_rank,
    "First contracts vs major exits by rank, all decades",
    os.path.join(FIGURES, "fig_first_contracts_vs_exits_by_rank_revised.png")
)


# -------------------- First contracts vs exits by rank, per decade --------------------
decades = sorted([int(d) for d in contracts["decade"].dropna().unique()])

for dec in decades:
    sub = contracts[contracts["decade"] == dec]

    if sub.empty:
        continue

    rstats = per_rank_first_contract_exit_stats(sub)

    tbl_path = os.path.join(TABLES, f"first_contracts_vs_exits_by_rank_{dec}s_revised.csv")
    save_csv(rstats, tbl_path)

    fig_path = os.path.join(FIGURES, f"fig_first_contracts_vs_exits_by_rank_{dec}s_revised.png")

    plot_rank_first_contract_exit_shares(
        rstats,
        f"First contracts vs major exits by rank, {dec}s",
        fig_path
    )

# -------------------- Revised small multiples: outcome rates + first-contract share --------------------
# This figure shows one panel per rank.
#
# Each panel includes:
#   - Death rate within that rank and decade
#   - Repatriated rate within that rank and decade
#   - Death + Repatriated rate within that rank and decade
#   - First-contract share of that rank within the decade
#
# Important:
# Outcome rates are normalized within each rank and decade:
#   n_outcome / n_contracts for that rank and decade
#
# First-contract share is normalized across ranks within each decade:
#   first_contracts_in_rank_decade / total_first_contracts_in_decade
#
# These denominators are different, so the figure should be interpreted carefully.
# It is useful for visual comparison, but the benchmark tables remain the main
# evidence for the first-contract vs exit argument.

import math

RANKS_PRESENT = sorted(contracts["rank_parent"].dropna().unique().tolist())
RANKS_FOR_FACETS = [r for r in RANK_ORDER if r in RANKS_PRESENT] or RANKS_PRESENT

# Base counts by decade and rank
rank_decade_base = (
    contracts
    .dropna(subset=["decade", "rank_parent"])
    .groupby(["decade", "rank_parent"], as_index=False)
    .agg(
        contracts_n=("outcome_group_for_descriptives", "size"),
        deaths_n=("outcome_group_for_descriptives", lambda s: int((s == "Death").sum())),
        repatriated_n=("outcome_group_for_descriptives", lambda s: int((s == "Repatriated").sum())),
        first_contracts_n=("first_contract_for_descriptives", lambda s: int((s == 1).sum())),
    )
)

rank_decade_base["death_repatriated_n"] = (
    rank_decade_base["deaths_n"] + rank_decade_base["repatriated_n"]
)

# Within-rank outcome rates
rank_decade_base["death_rate"] = (
    rank_decade_base["deaths_n"] /
    rank_decade_base["contracts_n"].replace(0, np.nan)
)

rank_decade_base["repatriated_rate"] = (
    rank_decade_base["repatriated_n"] /
    rank_decade_base["contracts_n"].replace(0, np.nan)
)

rank_decade_base["death_repatriated_rate"] = (
    rank_decade_base["death_repatriated_n"] /
    rank_decade_base["contracts_n"].replace(0, np.nan)
)

# First-contract share across ranks within each decade
first_contracts_by_decade = (
    rank_decade_base
    .groupby("decade", as_index=False)["first_contracts_n"]
    .sum()
    .rename(columns={"first_contracts_n": "first_contracts_total_decade"})
)

rank_decade_base = rank_decade_base.merge(
    first_contracts_by_decade,
    on="decade",
    how="left"
)

rank_decade_base["first_contract_share_within_decade"] = (
    rank_decade_base["first_contracts_n"] /
    rank_decade_base["first_contracts_total_decade"].replace(0, np.nan)
)

# Difference columns for quick inspection
rank_decade_base["first_contract_minus_death_share"] = (
    rank_decade_base["first_contract_share_within_decade"] -
    rank_decade_base.groupby("decade")["deaths_n"].transform(
        lambda s: s / s.sum() if s.sum() > 0 else np.nan
    )
)

rank_decade_base["first_contract_minus_repatriated_share"] = (
    rank_decade_base["first_contract_share_within_decade"] -
    rank_decade_base.groupby("decade")["repatriated_n"].transform(
        lambda s: s / s.sum() if s.sum() > 0 else np.nan
    )
)

rank_decade_base["first_contract_minus_death_repatriated_share"] = (
    rank_decade_base["first_contract_share_within_decade"] -
    rank_decade_base.groupby("decade")["death_repatriated_n"].transform(
        lambda s: s / s.sum() if s.sum() > 0 else np.nan
    )
)

# Save table
small_multiples_table = rank_decade_base.copy()

percentage_cols = [
    "death_rate",
    "repatriated_rate",
    "death_repatriated_rate",
    "first_contract_share_within_decade",
    "first_contract_minus_death_share",
    "first_contract_minus_repatriated_share",
    "first_contract_minus_death_repatriated_share",
]

for col in percentage_cols:
    small_multiples_table[col] = (small_multiples_table[col] * 100).round(2)

save_csv(
    small_multiples_table,
    os.path.join(TABLES, "outcome_rates_and_first_contract_share_by_decade_rank_revised.csv")
)

# Plot small multiples
n = len(RANKS_FOR_FACETS)

if n == 0:
    print("[warn] No ranks to plot for revised outcome and first-contract trends.")
else:
    ncols = 3
    nrows = int(math.ceil(n / ncols))

    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(11.5, 3.6 * nrows),
        sharex=True,
        sharey=True
    )

    if not isinstance(axes, np.ndarray):
        axes = np.array([axes])

    axes = axes.flatten()

    global_handles, global_labels = None, None

    for i, rank in enumerate(RANKS_FOR_FACETS):
        ax = axes[i]

        sub = rank_decade_base[rank_decade_base["rank_parent"] == rank].copy()

        if sub.empty:
            ax.set_visible(False)
            continue

        sub["decade"] = pd.to_numeric(sub["decade"], errors="coerce")
        sub = sub.sort_values("decade")

        ax.plot(
            sub["decade"].to_numpy(),
            sub["death_rate"].to_numpy(),
            marker="o",
            label="Death rate"
        )

        ax.plot(
            sub["decade"].to_numpy(),
            sub["repatriated_rate"].to_numpy(),
            marker="o",
            label="Repatriated rate"
        )

        ax.plot(
            sub["decade"].to_numpy(),
            sub["death_repatriated_rate"].to_numpy(),
            marker="o",
            label="Death + repatriated rate"
        )

        ax.plot(
            sub["decade"].to_numpy(),
            sub["first_contract_share_within_decade"].to_numpy(),
            marker="s",
            linestyle="--",
            linewidth=2,
            label="First-contract share"
        )

        ax.set_title(str(rank))
        ax.set_ylim(0.0, 1.0)

        if i % ncols == 0:
            ax.set_ylabel("Rate / Share")

        if i >= (nrows - 1) * ncols:
            ax.set_xlabel("Decade")

        if global_handles is None:
            global_handles, global_labels = ax.get_legend_handles_labels()

    # Hide unused axes
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(
        "Revised outcome rates and first-contract share by decade and rank",
        y=0.995
    )

    if global_handles:
        fig.legend(
            global_handles,
            global_labels,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False
        )
        plt.subplots_adjust(right=0.80)

    plt.tight_layout()

    out_path = os.path.join(
        FIGURES,
        "fig_outcome_rates_and_first_contract_share_by_rank_revised.png"
    )

    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print(f"[saved] {out_path}")


# -------------------- Revised figure captions --------------------
# I write these to a separate revised captions file so the old conference-version
# captions can stay untouched for reference.

revised_caps = os.path.join(DOCS, "figure_captions_revised.txt")

caption_lines = [
    "fig_region_by_rank_parent.png - Share of origin regions within each parent rank category.",
    "fig_rank_parent_by_outcome_revised.png - Distribution of parent rank categories within revised outcome groups.",
    "fig_trend_over_time_revised.png - Foreign share, death rate, repatriated rate, irregular exit rate, and high-rank share by decade.",
    "fig_death_rate_and_first_contract_rate_by_decade.png - Death rate and first-contract rate by decade.",
    "fig_first_contracts_vs_exits_by_rank_revised.png - First-contract share, death share, repatriated share, and death + repatriated share by parent rank across all decades.",
    "fig_first_contracts_vs_exits_by_rank_1700s_revised.png - First-contract and major-exit shares by parent rank in the 1700s.",
    "fig_first_contracts_vs_exits_by_rank_1710s_revised.png - First-contract and major-exit shares by parent rank in the 1710s.",
    "fig_first_contracts_vs_exits_by_rank_1720s_revised.png - First-contract and major-exit shares by parent rank in the 1720s.",
    "fig_first_contracts_vs_exits_by_rank_1730s_revised.png - First-contract and major-exit shares by parent rank in the 1730s.",
    "fig_first_contracts_vs_exits_by_rank_1740s_revised.png - First-contract and major-exit shares by parent rank in the 1740s.",
    "fig_first_contracts_vs_exits_by_rank_1750s_revised.png - First-contract and major-exit shares by parent rank in the 1750s.",
    "fig_first_contracts_vs_exits_by_rank_1760s_revised.png - First-contract and major-exit shares by parent rank in the 1760s.",
    "fig_first_contracts_vs_exits_by_rank_1770s_revised.png - First-contract and major-exit shares by parent rank in the 1770s.",
    "fig_first_contracts_vs_exits_by_rank_1780s_revised.png - First-contract and major-exit shares by parent rank in the 1780s.",
    "fig_outcome_rates_and_first_contract_share_by_rank_revised.png - Per-rank revised outcome rates within rank and decade, shown together with first-contract share across ranks within each decade."
]

with open(revised_caps, "w", encoding="utf-8") as f:
    for line in caption_lines:
        f.write(line + "\n")

print(f"[saved] {revised_caps}")
print("[done] Descriptives complete.")