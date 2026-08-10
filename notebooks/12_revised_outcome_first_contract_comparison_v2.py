"""
12_revised_outcome_first_contract_comparison_v2.py

Purpose:
Rerun the revised outcome grouping and compare contract endings with first contracts.

I use first contracts as a proxy for hiring/recruitment. This is not the same as a direct
institutional hiring rate, but it helps show where new workers entered the workforce.

This version improves the previous script in two important ways:

1. I normalize reason_end_contract before mapping.
   This avoids problems such as "To regiment" vs "to regiment" or extra spaces.
   The mapping is still explicit, but more robust.

2. I calculate first contracts on the full dataset before filtering to 1700–1780.
   This is important because I want to identify a person's true first contract,
   not only the first contract visible inside the filtered period.

The script:
- loads the full VOC contracts dataset
- creates a true first-contract indicator using the full dataset
- filters to 1700–1780s for the actual analysis
- maps reason_end_contract into revised outcome groups:
    Death
    Repatriated
    Irregular exit
    Chamber
    Unknown / unclear
    Other
- maps ranks into six parent rank categories
- creates comparison tables for:
    outcome counts
    rank x outcome
    first contracts by rank
    endings vs first contracts by rank
    deaths vs first contracts by rank
    all endings vs first contracts by rank
    decade x rank x outcome
    decade x rank x first contracts
    decade x rank comparison
"""

import os
import sys
import pandas as pd

# -------------------- Paths --------------------
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(BASE, "data_raw")
TABLES = os.path.join(BASE, "tables")

os.makedirs(TABLES, exist_ok=True)


# -------------------- Helpers --------------------
def save_csv(df, path):
    df.to_csv(path, index=False)
    print(f"[saved] {path}")


def to_int_like(s):
    try:
        return s.astype("Int64")
    except Exception:
        return pd.to_numeric(s, errors="coerce").astype("Int64")


def normalize_reason(value):
    """
    Normalize raw reason_end_contract values before mapping.

    I keep the original raw value in the data, but use this normalized version
    only for the mapping. This makes the mapping safer against small differences
    in capitalization or spacing.
    """
    if pd.isna(value):
        return None

    return str(value).strip().lower()


# -------------------- Revised outcome mapping --------------------
# These keys are normalized lowercase versions of the raw reason_end_contract values.
OUTCOME_MAPPING_NORMALIZED = {
    # Death
    "deceased": "Death",
    "shipwrecked": "Death",
    "murdered": "Death",
    "death penalty": "Death",

    # Repatriated
    "repatriated": "Repatriated",

    # Irregular exit
    "deserted": "Irregular exit",
    "dismissal": "Irregular exit",
    "penalised or punished": "Irregular exit",
    "removed": "Irregular exit",
    "woman": "Irregular exit",

    # Unknown / unclear
    "missing": "Unknown / unclear",
    "unknown": "Unknown / unclear",
    "not recorded": "Unknown / unclear",
    "last record": "Unknown / unclear",

    # Chamber
    "amsterdam chamber": "Chamber",
    "delft chamber": "Chamber",
    "rotterdam chamber": "Chamber",
    "zeeland chamber": "Chamber",
    "hoorn chamber": "Chamber",
    "enkhuizen chamber": "Chamber",

    # Other known categories
    "absent upon departure": "Other",
    "age": "Other",
    "free citizen": "Other",
    "transferred": "Other",
    "to a man of war": "Other",
    "to a private ship": "Other",
    "to regiment": "Other",
    "remains at the cape": "Other",
    "unfit to work": "Other",
    "resignation": "Other",
    "otherwise": "Other",
    "in lening gaan": "Other",
}


def map_parent_rank(x):
    """
    Maps detailed rank group labels to six parent rank categories.
    This follows the same general logic as in the original cleaning script.
    """

    if pd.isna(x) or str(x).upper() == "NAN":
        return "Unknown"

    x_upper = str(x).upper()

    raw_to_parent = {
        "SEA": "Sea",
        "SHIP": "Ship",
        "TRADE": "Trade",
        "MEDICAL": "Medical",
        "MILITARY": "Military",
        "OTHER": "Other",
    }

    if x_upper in raw_to_parent:
        return raw_to_parent[x_upper]

    x_lower = str(x).lower()

    if "sea" in x_lower:
        return "Sea"

    if any(k in x_lower for k in ["ship", "sail", "mate", "boatswain"]):
        return "Ship"

    if any(k in x_lower for k in ["trad", "merchant"]):
        return "Trade"

    if any(k in x_lower for k in ["medic", "surg"]):
        return "Medical"

    if any(k in x_lower for k in ["milit", "soldier", "gunner", "corporal"]):
        return "Military"

    return "Other"


# -------------------- Load contracts --------------------
contracts_path = os.path.join(DATA_RAW, "voc_persons_contracts.csv")

if not os.path.exists(contracts_path):
    print(f"[error] Missing file: {contracts_path}")
    sys.exit(1)

contracts = pd.read_csv(contracts_path, low_memory=False)
print(f"[info] Loaded full dataset: {len(contracts):,} records")

if "reason_end_contract" not in contracts.columns:
    print("[error] Column 'reason_end_contract' not found.")
    sys.exit(1)

# -------------------- Create contract year and decade --------------------
contracts["date_begin_contract"] = pd.to_datetime(
    contracts["date_begin_contract"], errors="coerce"
)

contracts["contract_start_year"] = contracts["date_begin_contract"].dt.year
contracts["decade"] = (contracts["contract_start_year"] // 10) * 10


# -------------------- Create true first-contract indicator on the full dataset --------------------
if "person_cluster_id" in contracts.columns and "date_begin_contract" in contracts.columns:
    first_dates_full = (
        contracts
        .groupby("person_cluster_id")["date_begin_contract"]
        .transform("min")
    )

    contracts["is_first_contract_true"] = (
        contracts["date_begin_contract"] == first_dates_full
    ).astype(int)

    print("[info] Created is_first_contract_true using the full dataset before filtering.")
else:
    contracts["is_first_contract_true"] = 0
    print("[warn] Could not create is_first_contract_true. Missing person_cluster_id or date_begin_contract.")


# -------------------- Filter to 1700–1780s for actual analysis --------------------
before_filter = len(contracts)

analysis = contracts[
    (contracts["contract_start_year"] >= 1700) &
    (contracts["contract_start_year"] < 1790)
].copy()

print(f"[info] Filtered to 1700–1780s: {before_filter:,} -> {len(analysis):,}")


# -------------------- Map reason_end_contract --------------------
analysis["reason_end_contract_raw"] = analysis["reason_end_contract"]
analysis["reason_end_contract_normalized"] = analysis["reason_end_contract_raw"].apply(normalize_reason)

analysis["outcome_group_revised"] = analysis["reason_end_contract_normalized"].map(
    OUTCOME_MAPPING_NORMALIZED
)

# Actual null values are assigned to Unknown / unclear.
analysis.loc[
    analysis["reason_end_contract_raw"].isna(),
    "outcome_group_revised"
] = "Unknown / unclear"

# Check for unmapped non-null categories.
unmapped = (
    analysis.loc[
        analysis["outcome_group_revised"].isna() &
        analysis["reason_end_contract_raw"].notna(),
        "reason_end_contract_raw"
    ]
    .drop_duplicates()
    .sort_values()
    .tolist()
)

if len(unmapped) > 0:
    print("[warning] Unmapped reason_end_contract categories found:")
    for item in unmapped:
        print(f" - {item}")
    print("\nPlease add these to OUTCOME_MAPPING_NORMALIZED before using results.")
else:
    print("[info] All non-null reason_end_contract categories are mapped.")

# Keep possible unmapped values visible instead of silently assigning them.
analysis["outcome_group_revised"] = analysis["outcome_group_revised"].fillna("UNMAPPED")


# -------------------- Load and map ranks --------------------
ranks_path = os.path.join(DATA_RAW, "voc_ranks.csv")

if not os.path.exists(ranks_path):
    print(f"[warn] Missing ranks file: {ranks_path}")
    analysis["rank_parent"] = "Unknown"
else:
    ranks = pd.read_csv(ranks_path, low_memory=False)

    analysis.columns = analysis.columns.str.strip()
    ranks.columns = ranks.columns.str.strip()

    analysis["rank_id"] = to_int_like(analysis.get("rank_id"))
    ranks["rank_id"] = to_int_like(ranks.get("rank_id"))

    use_col = None
    for c in ["category", "parent_rank", "subcategory"]:
        if c in ranks.columns:
            use_col = c
            break

    if use_col and "rank_id" in ranks.columns:
        ranks_min = ranks[["rank_id", use_col]].drop_duplicates()
        ranks_min.columns = ["rank_id", "rank_group_raw"]

        analysis = analysis.merge(
            ranks_min,
            on="rank_id",
            how="left"
        )

        analysis["rank_parent"] = analysis["rank_group_raw"].apply(map_parent_rank)
    else:
        print("[warn] Could not find a rank grouping column in voc_ranks.csv")
        analysis["rank_parent"] = "Unknown"


# -------------------- Basic totals --------------------
total_records = len(analysis)
total_first_contracts = int(analysis["is_first_contract_true"].sum())

print(f"[info] Total records in analysis subset: {total_records:,}")
print(f"[info] Total true first contracts in analysis subset: {total_first_contracts:,}")


# ======================================================
# OUTPUT 1: revised outcome counts
# ======================================================
outcome_counts = (
    analysis["outcome_group_revised"]
    .value_counts()
    .reset_index()
)

outcome_counts.columns = ["outcome_group_revised", "count"]
outcome_counts["percentage"] = (
    outcome_counts["count"] / total_records * 100
).round(2)

save_csv(
    outcome_counts,
    os.path.join(TABLES, "v2_revised_outcome_counts_1700_1780.csv")
)


# ======================================================
# OUTPUT 2: raw reason to revised outcome mapping
# ======================================================
reason_mapping = (
    analysis
    .assign(reason_end_contract_raw=analysis["reason_end_contract_raw"].fillna("NULL"))
    .groupby(["reason_end_contract_raw", "reason_end_contract_normalized", "outcome_group_revised"], dropna=False)
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

reason_mapping["percentage_of_dataset"] = (
    reason_mapping["count"] / total_records * 100
).round(2)

save_csv(
    reason_mapping,
    os.path.join(TABLES, "v2_reason_end_contract_mapping_revised_1700_1780.csv")
)


# ======================================================
# OUTPUT 3: rank x outcome counts
# ======================================================
rank_outcome_count = pd.crosstab(
    analysis["rank_parent"],
    analysis["outcome_group_revised"]
).reset_index()

save_csv(
    rank_outcome_count,
    os.path.join(TABLES, "v2_rank_by_revised_outcome_count_1700_1780.csv")
)


# ======================================================
# OUTPUT 4: rank x outcome percentages within rank
# ======================================================
rank_outcome_pct = (
    pd.crosstab(
        analysis["rank_parent"],
        analysis["outcome_group_revised"],
        normalize="index"
    ) * 100
).round(2).reset_index()

save_csv(
    rank_outcome_pct,
    os.path.join(TABLES, "v2_rank_by_revised_outcome_pct_1700_1780.csv")
)


# ======================================================
# OUTPUT 5: first contracts by rank
# ======================================================
first_contracts_by_rank = (
    analysis
    .groupby("rank_parent", as_index=False)
    .agg(
        contracts_n=("rank_parent", "size"),
        first_contracts_n=("is_first_contract_true", "sum")
    )
)

# I use first contracts as a proxy for hiring/recruitment.
# To avoid confusion, I name this "first_contract_share" rather than "hiring rate".
# It shows the percentage of contracts within each rank that are first contracts.
first_contracts_by_rank["first_contract_share_within_rank"] = (
    first_contracts_by_rank["first_contracts_n"] / first_contracts_by_rank["contracts_n"] * 100
).round(2)

# This shows how first contracts are distributed across ranks.
# It helps compare where new workers entered with where contract endings/deaths are concentrated.
first_contracts_by_rank["first_contract_share_of_all_first_contracts"] = (
    first_contracts_by_rank["first_contracts_n"] / total_first_contracts * 100
).round(2)

first_contracts_by_rank = first_contracts_by_rank.sort_values("contracts_n", ascending=False)

save_csv(
    first_contracts_by_rank,
    os.path.join(TABLES, "v2_first_contracts_by_rank_1700_1780.csv")
)


# ======================================================
# OUTPUT 6: all endings share by rank
# ======================================================
# This shows how all contracts in the analysis subset are distributed across ranks.
# Since each row represents a contract record with an end reason, I use this as the distribution of contract endings by rank.
all_endings_by_rank = (
    analysis
    .groupby("rank_parent", as_index=False)
    .size()
    .rename(columns={"size": "all_endings_n"})
)

all_endings_by_rank["all_endings_share"] = (
    all_endings_by_rank["all_endings_n"] / total_records * 100
).round(2)

save_csv(
    all_endings_by_rank,
    os.path.join(TABLES, "v2_all_endings_by_rank_1700_1780.csv")
)


# ======================================================
# OUTPUT 7: deaths by rank and death share of all deaths
# ======================================================
death_records = analysis[analysis["outcome_group_revised"] == "Death"].copy()
total_deaths = len(death_records)

deaths_by_rank = (
    death_records
    .groupby("rank_parent", as_index=False)
    .size()
    .rename(columns={"size": "deaths_n"})
)

deaths_by_rank["death_share_of_all_deaths"] = (
    deaths_by_rank["deaths_n"] / total_deaths * 100
).round(2)

save_csv(
    deaths_by_rank,
    os.path.join(TABLES, "v2_deaths_by_rank_1700_1780.csv")
)


# ======================================================
# OUTPUT 8: first contracts vs all endings and deaths by rank
# ======================================================
rank_loss_first_contracts_comparison = (
    all_endings_by_rank
    .merge(deaths_by_rank, on="rank_parent", how="left")
    .merge(
        first_contracts_by_rank[[
            "rank_parent",
            "first_contracts_n",
            "first_contract_share_within_rank",
            "first_contract_share_of_all_first_contracts"
        ]],
        on="rank_parent",
        how="left"
    )
)

rank_loss_first_contracts_comparison["deaths_n"] = rank_loss_first_contracts_comparison["deaths_n"].fillna(0)
rank_loss_first_contracts_comparison["death_share_of_all_deaths"] = rank_loss_first_contracts_comparison["death_share_of_all_deaths"].fillna(0)

rank_loss_first_contracts_comparison["first_contract_minus_death_share"] = (
    rank_loss_first_contracts_comparison["first_contract_share_of_all_first_contracts"] -
    rank_loss_first_contracts_comparison["death_share_of_all_deaths"]
).round(2)

rank_loss_first_contracts_comparison["first_contract_minus_all_endings_share"] = (
    rank_loss_first_contracts_comparison["first_contract_share_of_all_first_contracts"] -
    rank_loss_first_contracts_comparison["all_endings_share"]
).round(2)

rank_loss_first_contracts_comparison = rank_loss_first_contracts_comparison.sort_values(
    "all_endings_n",
    ascending=False
)

save_csv(
    rank_loss_first_contracts_comparison,
    os.path.join(TABLES, "v2_first_contracts_vs_losses_by_rank_1700_1780.csv")
)

# ======================================================
# OUTPUT 8B: compact summary table for interpretation
# ======================================================
# This table brings the most important rank-level comparison into one file.
# It is meant as an easier table to inspect before updating the paper or GitHub.

rank_outcome_pct_for_summary = rank_outcome_pct.copy()

summary_rank_first_contracts_vs_deaths = rank_loss_first_contracts_comparison.merge(
    rank_outcome_pct_for_summary,
    on="rank_parent",
    how="left"
)

# Keep only the most useful columns for interpretation.
summary_columns = [
    "rank_parent",
    "all_endings_n",
    "all_endings_share",
    "first_contracts_n",
    "first_contract_share_within_rank",
    "first_contract_share_of_all_first_contracts",
    "deaths_n",
    "death_share_of_all_deaths",
    "first_contract_minus_death_share",
    "first_contract_minus_all_endings_share",
    "Death",
    "Repatriated",
    "Irregular exit",
    "Chamber",
    "Other",
    "Unknown / unclear",
]

# Only keep columns that exist, in case a category is absent in a future run.
summary_columns = [
    col for col in summary_columns
    if col in summary_rank_first_contracts_vs_deaths.columns
]

summary_rank_first_contracts_vs_deaths = summary_rank_first_contracts_vs_deaths[summary_columns]

save_csv(
    summary_rank_first_contracts_vs_deaths,
    os.path.join(TABLES, "summary_rank_first_contracts_vs_deaths.csv")
)

# ======================================================
# OUTPUT 9: rank x outcome long table with first-contract information added
# ======================================================
rank_outcome_long = (
    analysis
    .groupby(["rank_parent", "outcome_group_revised"], as_index=False)
    .size()
    .rename(columns={"size": "endings_n"})
)

rank_totals = (
    analysis
    .groupby("rank_parent", as_index=False)
    .size()
    .rename(columns={"size": "total_contracts_rank"})
)

rank_outcome_long = rank_outcome_long.merge(
    rank_totals,
    on="rank_parent",
    how="left"
)

rank_outcome_long["ending_pct_within_rank"] = (
    rank_outcome_long["endings_n"] /
    rank_outcome_long["total_contracts_rank"] * 100
).round(2)

rank_outcome_long = rank_outcome_long.merge(
    first_contracts_by_rank[[
        "rank_parent",
        "first_contracts_n",
        "first_contract_share_within_rank",
        "first_contract_share_of_all_first_contracts"
    ]],
    on="rank_parent",
    how="left"
)

save_csv(
    rank_outcome_long,
    os.path.join(TABLES, "v2_endings_vs_first_contracts_by_rank_1700_1780.csv")
)


# ======================================================
# OUTPUT 10: decade x rank x outcome
# ======================================================
decade_rank_outcome = (
    analysis
    .groupby(["decade", "rank_parent", "outcome_group_revised"], as_index=False)
    .size()
    .rename(columns={"size": "endings_n"})
)

decade_rank_totals = (
    analysis
    .groupby(["decade", "rank_parent"], as_index=False)
    .size()
    .rename(columns={"size": "total_contracts_decade_rank"})
)

decade_rank_outcome = decade_rank_outcome.merge(
    decade_rank_totals,
    on=["decade", "rank_parent"],
    how="left"
)

decade_rank_outcome["ending_pct_within_decade_rank"] = (
    decade_rank_outcome["endings_n"] /
    decade_rank_outcome["total_contracts_decade_rank"] * 100
).round(2)

save_csv(
    decade_rank_outcome,
    os.path.join(TABLES, "v2_decade_rank_revised_outcome_1700_1780.csv")
)


# ======================================================
# OUTPUT 11: first contracts by decade and rank
# ======================================================
first_contracts_decade_rank = (
    analysis
    .groupby(["decade", "rank_parent"], as_index=False)
    .agg(
        contracts_n=("rank_parent", "size"),
        first_contracts_n=("is_first_contract_true", "sum")
    )
)

# Percentage of contracts within each decade-rank combination that are first contracts.
first_contracts_decade_rank["first_contract_share_within_decade_rank"] = (
    first_contracts_decade_rank["first_contracts_n"] /
    first_contracts_decade_rank["contracts_n"] * 100
).round(2)

decade_first_contracts = (
    first_contracts_decade_rank
    .groupby("decade", as_index=False)["first_contracts_n"]
    .sum()
    .rename(columns={"first_contracts_n": "total_first_contracts_decade"})
)

first_contracts_decade_rank = first_contracts_decade_rank.merge(
    decade_first_contracts,
    on="decade",
    how="left"
)

# Share of all first contracts in a decade that belong to each rank.
first_contracts_decade_rank["first_contract_share_within_decade"] = (
    first_contracts_decade_rank["first_contracts_n"] /
    first_contracts_decade_rank["total_first_contracts_decade"] * 100
).round(2)

save_csv(
    first_contracts_decade_rank,
    os.path.join(TABLES, "v2_first_contracts_by_decade_rank_1700_1780.csv")
)


# ======================================================
# OUTPUT 12: decade-rank endings vs first contracts
# ======================================================
decade_rank_comparison = decade_rank_outcome.merge(
    first_contracts_decade_rank[[
        "decade",
        "rank_parent",
        "first_contracts_n",
        "first_contract_share_within_decade_rank",
        "first_contract_share_within_decade"
    ]],
    on=["decade", "rank_parent"],
    how="left"
)

save_csv(
    decade_rank_comparison,
    os.path.join(TABLES, "v2_endings_vs_first_contracts_by_decade_rank_1700_1780.csv")
)


# ======================================================
# OUTPUT 13: decade-rank death share vs first-contract share
# ======================================================
death_decade_rank = (
    death_records
    .groupby(["decade", "rank_parent"], as_index=False)
    .size()
    .rename(columns={"size": "deaths_n"})
)

death_totals_decade = (
    death_decade_rank
    .groupby("decade", as_index=False)["deaths_n"]
    .sum()
    .rename(columns={"deaths_n": "total_deaths_decade"})
)

death_decade_rank = death_decade_rank.merge(
    death_totals_decade,
    on="decade",
    how="left"
)

death_decade_rank["death_share_within_decade"] = (
    death_decade_rank["deaths_n"] /
    death_decade_rank["total_deaths_decade"] * 100
).round(2)

decade_rank_death_first_contracts_share = death_decade_rank.merge(
    first_contracts_decade_rank[[
        "decade",
        "rank_parent",
        "first_contracts_n",
        "first_contract_share_within_decade"
    ]],
    on=["decade", "rank_parent"],
    how="left"
)

decade_rank_death_first_contracts_share["first_contract_minus_death_share_within_decade"] = (
    decade_rank_death_first_contracts_share["first_contract_share_within_decade"] -
    decade_rank_death_first_contracts_share["death_share_within_decade"]
).round(2)

save_csv(
    decade_rank_death_first_contracts_share,
    os.path.join(TABLES, "v2_death_vs_first_contract_share_by_decade_rank_1700_1780.csv")
)


# -------------------- Print summaries --------------------
print("\n==============================")
print("Revised outcome counts")
print("==============================")
print(outcome_counts)

print("\n==============================")
print("First contracts by rank")
print("==============================")
print(first_contracts_by_rank)

print("\n==============================")
print("First contracts vs losses by rank")
print("==============================")
print(rank_loss_first_contracts_comparison)

print("\n==============================")
print("Rank x outcome percentages")
print("==============================")
print(rank_outcome_pct)

print("\n[done] Revised outcome and first contracts comparison v2 complete.")