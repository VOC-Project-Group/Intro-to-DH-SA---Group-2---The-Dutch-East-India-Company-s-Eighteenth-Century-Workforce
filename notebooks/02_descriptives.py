"""
02_descriptives.py

Descriptive outputs for the VOC project.

What this script does
- Builds crosstabs (tables/*.csv) for:
  * region x rank_parent (counts and %)
  * outcome_group x rank_parent (counts and %)
  * region x outcome_group (counts and %)

- Makes figures (figures/*.png):
  * fig_region_by_rank_parent.png       (stacked bars; legend outside)
  * fig_rank_parent_by_outcome.png      (stacked bars; legend outside)
  * fig_trend_over_time.png             (foreign share, attrition, death, high-rank by decade; legend outside)
  * fig_death_vs_recruitment.png        (death rate vs. inflow of new workers by decade; legend outside)
  * fig_death_vs_recruitment_by_rank.png        (per-rank death rate and recruitment share, all decades; legend outside)
  * fig_death_vs_recruitment_by_rank_1700s.png  (same, per-decade panels 1700s ... 1780s)
  * ...
  * fig_death_vs_recruitment_by_rank_1780s.png

- Updates docs/figure_captions.txt (without duplicating lines).

Inputs (produced by 01_cleaning.py)
- data_clean/contracts_clean.csv

Notes
- Labels on stacked bars appear only when a segment is >= 1% (no labels for tiny segments).
- If is_first_contract or decade are missing, the script computes conservative fallbacks.
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

# Preferred visual order of ranks (kept if present)
RANK_ORDER = ["Medical", "Military", "Other", "Sea", "Ship", "Trade", "Unknown"]

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

# outcome_group x rank_parent
c2_path = os.path.join(TABLES, "rank_parent_by_outcome_count.csv")
p2_path = os.path.join(TABLES, "rank_parent_by_outcome_pct.csv")
counts_or, pct_or = crosstab_counts_and_pct(contracts, "outcome_group", "rank_parent", c2_path, p2_path)

# the region x outcome_group
c3_path = os.path.join(TABLES, "region_by_outcome_group_count.csv")
p3_path = os.path.join(TABLES, "region_by_outcome_group_pct.csv")
counts_ro, pct_ro = crosstab_counts_and_pct(contracts, "region_label", "outcome_group", c3_path, p3_path)

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

# Rank by Outcome (share within outcome): rows=outcomes, columns=ranks
pct_outcome_rows = pd.crosstab(
    contracts["outcome_group"], contracts["rank_parent"], normalize="index"
) * 100.0
pct_outcome_rows = pct_outcome_rows.round(2)
# reorder columns if possible
pct_outcome_rows = pct_outcome_rows.reindex(columns=[r for r in RANK_ORDER if r in pct_outcome_rows.columns], fill_value=0.0)

fig2 = os.path.join(FIGURES, "fig_rank_parent_by_outcome.png")
stacked_bar_with_threshold_labels(
    pct_outcome_rows, "Rank by Outcome (share within outcome)", fig2, ylabel="Share", legend_title="rank_parent"
)

# -------------------- Trends by decade (legend outside) --------------------
def mean_if_any_bool(s, cond):
    s = s.astype(str)
    return np.mean(s == cond) if s.notna().any() else np.nan

trend = (
    contracts.groupby("decade", as_index=False)
    .agg(
        foreign_share=("is_dutch", lambda s: 1 - s.mean() if s.notna().any() else np.nan),
        attrition_rate=("outcome_group", lambda s: mean_if_any_bool(s, "Attrition")),
        death_rate=("outcome_group", lambda s: mean_if_any_bool(s, "Death")),
        high_rank_share=("is_high_rank", "mean"),
        new_workers=("is_first_contract", "sum"),
        contracts_n=("is_first_contract", "size"),
    )
)
trend_path = os.path.join(TABLES, "trend_by_decade.csv")
save_csv(trend, trend_path)

t = trend.sort_values("decade").copy()
for col in ["foreign_share", "attrition_rate", "death_rate", "high_rank_share"]:
    t[col] = pd.to_numeric(t[col], errors="coerce")

fig, ax = plt.subplots(figsize=(10.5, 6))
ax.plot(t["decade"].to_numpy(), t["foreign_share"].to_numpy(), marker="o", label="Foreign share")
ax.plot(t["decade"].to_numpy(), t["attrition_rate"].to_numpy(), marker="o", label="Attrition rate")
ax.plot(t["decade"].to_numpy(), t["death_rate"].to_numpy(), marker="o", label="Death rate")
ax.plot(t["decade"].to_numpy(), t["high_rank_share"].to_numpy(), marker="o", label="High-rank share")
ax.set_xlabel("Decade")
ax.set_ylabel("Rate")
ax.set_title("Trends by decade")
legend_outside(ax)
plt.subplots_adjust(right=0.78)
plt.tight_layout()
fig3 = os.path.join(FIGURES, "fig_trend_over_time.png")
plt.savefig(fig3, dpi=180); plt.close()
print(f"[saved] {fig3}")

# -------------------- Deaths vs recruitment by decade (legend outside) --------------------
t["new_workers"] = pd.to_numeric(t["new_workers"], errors="coerce").fillna(0)
max_new = t["new_workers"].max()
nw_norm = (t["new_workers"] / max_new) if max_new > 0 else t["new_workers"]

fig, ax = plt.subplots(figsize=(10.5, 6))
ax.plot(t["decade"].to_numpy(), t["death_rate"].to_numpy(), marker="o", label="Death rate")
ax.plot(t["decade"].to_numpy(), nw_norm.to_numpy(), marker="o", label="Recruitment (normalised)")
ax.set_xlabel("Decade")
ax.set_ylabel("Rate / Normalised inflow")
ax.set_title("Death rate vs recruitment by decade")
legend_outside(ax)
plt.subplots_adjust(right=0.78)
plt.tight_layout()
fig4 = os.path.join(FIGURES, "fig_death_vs_recruitment.png")
plt.savefig(fig4, dpi=180); plt.close()
print(f"[saved] {fig4}")

# -------------------- Helper: per-rank stats --------------------
def per_rank_death_recruit(group_df):
    """
    Returns a per-rank summary with:
      - contracts_n (total contracts)
      - deaths_n (number of Death outcomes)
      - recruits_n (number of first-time contracts)
      - death_rate = deaths_n / contracts_n
      - recruitment_share = recruits_n / total recruits
    """
    out = (
        group_df.groupby("rank_parent", as_index=False)
        .agg(
            contracts_n=("outcome_group", "size"),
            deaths_n=("outcome_group", lambda s: (s == "Death").sum()),
            recruits_n=("is_first_contract", lambda s: (s == 1).sum()),
        )
    )
    out["death_rate"] = out["deaths_n"] / out["contracts_n"]
    total_recruits = out["recruits_n"].sum()
    out["recruitment_share"] = (
        out["recruits_n"] / total_recruits if total_recruits > 0 else 0.0
    )
    return out


# -------------------- Death vs recruitment by rank (overall) --------------------
overall_rank = per_rank_death_recruit(contracts)
rank_tbl_path = os.path.join(TABLES, "death_recruitment_by_rank.csv")
save_csv(overall_rank, rank_tbl_path)

# Ensure numeric arrays (NaNs -> 0) and a consistent category order
cats = ["Military", "Sea", "Ship", "Medical", "Trade", "Other", "Unknown"]
overall_rank = overall_rank.copy()
overall_rank["rank_parent"] = pd.Categorical(overall_rank["rank_parent"], categories=cats, ordered=True)
overall_rank = overall_rank.sort_values("rank_parent")

x = np.arange(len(overall_rank))
width = 0.38
y1 = pd.to_numeric(overall_rank["death_rate"], errors="coerce").fillna(0.0).to_numpy()
y2 = pd.to_numeric(overall_rank["recruitment_share"], errors="coerce").fillna(0.0).to_numpy()

fig, ax = plt.subplots(figsize=(9, 6))
ax.bar(x - width/2, y1, width, label="Death rate")
ax.bar(x + width/2, y2, width, label="Recruitment share")
ax.set_xticks(x)
ax.set_xticklabels(overall_rank["rank_parent"].astype(str).tolist(), rotation=0)
ax.set_ylabel("Rate / Share")
ax.set_title("Deaths vs. Recruitment by rank (all decades)")

# Put legend outside
handles, labels = ax.get_legend_handles_labels()
leg = ax.legend(handles, labels, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)
leg.get_frame().set_alpha(0.9)

# Make sure we have a sensible y-limit even if values are small
ymax = float(np.nanmax(np.r_[y1, y2])) if (len(y1) and len(y2)) else 0.0
ax.set_ylim(0, max(0.01, ymax) * 1.15)

fig.tight_layout()
fig.savefig(os.path.join(FIGURES, "fig_death_vs_recruitment_by_rank.png"), dpi=180, bbox_inches="tight")
plt.close(fig)
print(f"[saved] {os.path.join(FIGURES, 'fig_death_vs_recruitment_by_rank.png')}")

# -------------------- Death vs recruitment by rank (per decade panels) --------------------
decades = sorted([int(d) for d in contracts["decade"].dropna().unique()])
for dec in decades:
    sub = contracts[contracts["decade"] == dec]
    if sub.empty:
        continue

    rstats = per_rank_death_recruit(sub).copy()
    rstats["rank_parent"] = pd.Categorical(rstats["rank_parent"], categories=cats, ordered=True)
    rstats = rstats.sort_values("rank_parent")

    # Save table
    tbl_path = os.path.join(TABLES, f"death_recruitment_by_rank_{dec}s.csv")
    save_csv(rstats, tbl_path)

    x = np.arange(len(rstats))
    y1 = pd.to_numeric(rstats["death_rate"], errors="coerce").fillna(0.0).to_numpy()
    y2 = pd.to_numeric(rstats["recruitment_share"], errors="coerce").fillna(0.0).to_numpy()

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.bar(x - width/2, y1, width, label="Death rate")
    ax.bar(x + width/2, y2, width, label="Recruitment share")
    ax.set_xticks(x)
    ax.set_xticklabels(rstats["rank_parent"].astype(str).tolist(), rotation=0)
    ax.set_ylabel("Rate / Share")
    ax.set_title(f"Deaths vs. Recruitment by rank — {dec}s")

    handles, labels = ax.get_legend_handles_labels()
    leg = ax.legend(handles, labels, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)
    leg.get_frame().set_alpha(0.9)

    ymax = float(np.nanmax(np.r_[y1, y2])) if (len(y1) and len(y2)) else 0.0
    ax.set_ylim(0, max(0.01, ymax) * 1.15)

    outp = os.path.join(FIGURES, f"fig_death_vs_recruitment_by_rank_{dec}s.png")
    fig.tight_layout()
    fig.savefig(outp, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {outp}")



# -------------------- Figure captions (no duplicates) --------------------
caps = os.path.join(DOCS, "figure_captions.txt")
append_caption_once(caps, "fig_region_by_rank_parent.png - Share of origin regions within each parent rank category.")
append_caption_once(caps, "fig_rank_parent_by_outcome.png - Distribution of parent rank categories across contract outcomes.")
append_caption_once(caps, "fig_trend_over_time.png - Foreign share, attrition rate, death rate, and share of high-ranking positions by decade.")
append_caption_once(caps, "fig_death_vs_recruitment.png - Comparison of death rate and inflow of new recruits (first-time entrants) by decade.")
append_caption_once(caps, "fig_death_vs_recruitment_by_rank.png - Death rate vs recruitment share by parent rank (all decades).")
for dec, sub in (contracts.dropna(subset=["decade"])
                 .groupby("decade", sort=True)):
    append_caption_once(caps, f"fig_death_vs_recruitment_by_rank_{dec}s.png - Death rate vs recruitment share by parent rank in the {dec}s.")

print(f"[saved] {caps}")
print("[done] Descriptives complete.")

