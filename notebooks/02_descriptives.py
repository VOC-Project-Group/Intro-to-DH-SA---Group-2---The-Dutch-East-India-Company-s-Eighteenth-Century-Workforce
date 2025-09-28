"""
02_descriptives.py
Purpose: read the cleaned dataset and produce descriptive tables + figures.

Inputs:
  - data_clean/contracts_clean.csv

Outputs:
  - tables/*.csv  (crosstabs & trends)
  - figures/*.png (4 plots)
  - docs/figure_captions.txt (overwritten)
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_CLEAN = os.path.join(BASE, "data_clean")
TABLES     = os.path.join(BASE, "tables")
FIGURES    = os.path.join(BASE, "figures")
DOCS       = os.path.join(BASE, "docs")
os.makedirs(TABLES, exist_ok=True)
os.makedirs(FIGURES, exist_ok=True)
os.makedirs(DOCS, exist_ok=True)

contracts = pd.read_csv(os.path.join(DATA_CLEAN, "contracts_clean.csv"), low_memory=False)

# ---------- Helper to label stacked bars ----------
def safe_plot_bar_stacked(pivot_df, title, out_path, ylabel="Share"):
    """
    Stacked bars with labels:
      - >=1% -> exact 'xx.x%'
      - <1%  -> '<1%'
    Accepts input in fraction (0-1) or percent (0-100).
    """
    if pivot_df.empty or pivot_df.shape[1] == 0:
        print(f"[warn] Skip plot {out_path}: empty pivot"); return

    pivot_num = pivot_df.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    max_val = float(np.nanmax(pivot_num.to_numpy()))
    frac = pivot_num / 100.0 if max_val > 1.0001 else pivot_num

    ax = frac.plot(kind="bar", stacked=True, figsize=(8, 6))
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    x_idx = np.arange(len(frac))
    cum = np.zeros(len(frac), dtype=float)
    for col in frac.columns:
        vals = frac[col].to_numpy()
        bottoms = cum.copy()
        cum += vals
        for xi, v, b in zip(x_idx, vals, bottoms):
            if v <= 0: continue
            y = b + v / 2.0
            pct = v * 100.0
            txt = f"{pct:.1f}%" if pct >= 1 else "<1%"
            ax.text(xi, y, txt, ha="center", va="center", fontsize=7)

    ax.set_xticklabels([str(i) for i in frac.index], rotation=0)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()
    print(f"[saved] {out_path}")

# ---------- Tables ----------
# Region counts (simple)
region_counts = contracts["region_label"].value_counts(dropna=False).reset_index()
region_counts.columns = ["region_label", "n_contracts"]
region_counts.to_csv(os.path.join(TABLES, "region_counts.csv"), index=False)

# Crosstabs (counts and %)
def crosstab_save(row, col, fname, normalize=None):
    if normalize in (None, False):
        xt = pd.crosstab(contracts[row], contracts[col])
    else:
        xt = pd.crosstab(contracts[row], contracts[col], normalize=normalize) * 100
        xt = xt.round(2)
    xt.to_csv(os.path.join(TABLES, fname))
    print(f"[saved] tables/{fname}")

crosstab_save("region_label", "rank_parent", "region_by_rank_parent_count.csv", normalize=None)
crosstab_save("region_label", "rank_parent", "region_by_rank_parent_pct.csv",   normalize="index")
crosstab_save("outcome_group", "rank_parent", "rank_parent_by_outcome_count.csv", normalize=None)
crosstab_save("outcome_group", "rank_parent", "rank_parent_by_outcome_pct.csv",   normalize="index")
crosstab_save("region_label", "outcome_group", "region_by_outcome_group_count.csv", normalize=None)
crosstab_save("region_label", "outcome_group", "region_by_outcome_group_pct.csv",   normalize="index")

# ---------- Figures ----------
# Region by Rank (share within rank)
pivot_rr = pd.crosstab(contracts["rank_parent"], contracts["region_label"], normalize="index")
safe_plot_bar_stacked(
    pivot_rr,
    title="Region by Rank (share within rank)",
    out_path=os.path.join(FIGURES, "fig_region_by_rank_parent.png"),
    ylabel="Share"
)

# Rank by Outcome (share within outcome)
pivot_ro = pd.crosstab(contracts["outcome_group"], contracts["rank_parent"], normalize="index")
safe_plot_bar_stacked(
    pivot_ro,
    title="Rank by Outcome (share within outcome)",
    out_path=os.path.join(FIGURES, "fig_rank_parent_by_outcome.png"),
    ylabel="Share"
)

# Trends by decade (combined line chart)
# Recalculate from the cleaned contracts
trend = contracts.groupby("decade").agg(
    foreign_share=("is_dutch", lambda s: 1 - s.mean() if s.notna().any() else np.nan),
    attrition_rate=("outcome_group", lambda s: (s == "Attrition").mean()),
    death_rate=("outcome_group", lambda s: (s == "Death").mean()),
    high_rank_share=("is_high_rank", "mean")
).reset_index()

t = trend.sort_values("decade").copy()
for c in ["decade", "foreign_share", "attrition_rate", "death_rate", "high_rank_share"]:
    t[c] = pd.to_numeric(t[c], errors="coerce")

# keep only rows where decade is known
t = t.dropna(subset=["decade"])

# convert to NumPy arrays to avoid the pandas multidimensional indexing error
x = t["decade"].to_numpy()
y_foreign  = t["foreign_share"].to_numpy()
y_attrit   = t["attrition_rate"].to_numpy()
y_death    = t["death_rate"].to_numpy()
y_highrank = t["high_rank_share"].to_numpy()

plt.figure(figsize=(8, 6))
plt.plot(x, y_foreign,  marker="o", label="Foreign share")
plt.plot(x, y_attrit,   marker="o", label="Attrition rate")
plt.plot(x, y_death,    marker="o", label="Death rate")
plt.plot(x, y_highrank, marker="o", label="High-rank share")
plt.legend()
plt.xlabel("Decade")
plt.ylabel("Rate")
plt.title("Trends by decade")
plt.tight_layout()
fig3 = os.path.join(FIGURES, "fig_trend_over_time.png")
plt.savefig(fig3, dpi=180)
plt.close()
print(f"[saved] {fig3}")

# ----- Recruitment inflow: unique new recruits per decade -----
first_by_person = (
    contracts[["person_cluster_id", "decade"]]
    .dropna(subset=["person_cluster_id", "decade"])
    .groupby("person_cluster_id", as_index=False)["decade"].min()
    .rename(columns={"decade": "first_decade"})
)
new_workers_by_decade = (
    first_by_person.groupby("first_decade").size().reset_index(name="new_workers")
    .rename(columns={"first_decade": "decade"})
)

trend_extended = trend.merge(new_workers_by_decade, on="decade", how="left")
trend_extended["new_workers"] = trend_extended["new_workers"].fillna(0).astype(int)

# Save table
trend_ext_path = os.path.join(TABLES, "trend_with_recruitment.csv")
trend_extended.to_csv(trend_ext_path, index=False)
print(f"[saved] {trend_ext_path}")

# Plot: death rate vs new recruits
plt.figure()
plt.plot(trend_extended["decade"].to_numpy(),
         trend_extended["death_rate"].to_numpy(),
         marker="o", label="Death rate")
plt.plot(trend_extended["decade"].to_numpy(),
         (trend_extended["new_workers"] / 10000.0).to_numpy(),
         marker="o", label="New recruits (scaled /10k)")
plt.legend()
plt.xlabel("Decade")
plt.ylabel("Rate / Scaled count")
plt.title("Deaths vs New Recruits by Decade")
plt.tight_layout()
fig_path = os.path.join(FIGURES, "fig_death_vs_recruitment.png")
plt.savefig(fig_path, dpi=180)
plt.close()
print(f"[saved] {fig_path}")

# ---------- Figure captions (overwrite each run) ----------
caps = os.path.join(DOCS, "figure_captions.txt")
with open(caps, "w", encoding="utf-8") as f:
    f.write("FIGURE CAPTIONS\n")
    f.write("fig_region_by_rank_parent.png - Share of origin regions within each parent rank category.\n")
    f.write("fig_rank_parent_by_outcome.png - Distribution of parent rank categories across contract outcomes.\n")
    f.write("fig_trend_over_time.png - Foreign share, attrition rate, death rate, and share of high-ranking positions by decade.\n")
    f.write("fig_death_vs_recruitment.png - Comparison of death rates and inflow of new recruits (first-time entrants) by decade.\n")
print(f"[saved] {caps}")

print("[done] Descriptives complete.")
