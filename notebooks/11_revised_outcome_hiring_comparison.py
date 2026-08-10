"""
11_revised_outcome_hiring_comparison.py

Purpose:
Rerun the outcome grouping and compare contract endings against hiring/recruitment.

This script:
- loads the raw VOC contracts dataset
- filters to 1700–1780s
- maps reason_end_contract into revised outcome groups:
    Death
    Repatriated
    Irregular exit
    Chamber
    Unknown / unclear
    Other
- maps ranks into six parent rank categories
- marks first contracts as recruitment/hiring
- creates summary tables:
    1. outcome counts
    2. rank x outcome counts and percentages
    3. hiring by rank
    4. contract endings vs hiring by rank
    5. decade x rank x outcome
    6. decade x rank x hiring
    7. decade x rank comparison of endings and hiring

This script does NOT overwrite the existing cleaned data.
It only creates new CSV outputs in /tables/.
"""

import os
import sys
import pandas as pd
import numpy as np

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


# -------------------- Revised outcome mapping --------------------
OUTCOME_MAPPING = {
    # Death
    "Deceased": "Death",
    "Shipwrecked": "Death",
    "Murdered": "Death",
    "Death penalty": "Death",

    # Repatriated
    "Repatriated": "Repatriated",

    # Irregular exit
    "Deserted": "Irregular exit",
    "Dismissal": "Irregular exit",
    "Penalised or punished": "Irregular exit",
    "Removed": "Irregular exit",
    "Woman": "Irregular exit",

    # Unknown / unclear
    "Missing": "Unknown / unclear",
    "Unknown": "Unknown / unclear",
    "Not recorded": "Unknown / unclear",
    "Last record": "Unknown / unclear",

    # Chamber
    "Amsterdam chamber": "Chamber",
    "Delft chamber": "Chamber",
    "Rotterdam chamber": "Chamber",
    "Zeeland chamber": "Chamber",
    "Hoorn chamber": "Chamber",
    "Enkhuizen chamber": "Chamber",

    # Other known categories
    "Absent upon departure": "Other",
    "Age": "Other",
    "Free citizen": "Other",
    "Transferred": "Other",
    "To a man of war": "Other",
    "To a private ship": "Other",
    "To regiment": "Other",
    "Remains at the Cape": "Other",
    "Unfit to work": "Other",
    "Resignation": "Other",
    "Otherwise": "Other",
    "In lening gaan": "Other",
}


def map_parent_rank(x):
    """
    Maps detailed rank group labels to six parent rank categories.
    Same general logic as in 01_cleaning.py.
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

# -------------------- Filter to 1700–1780s --------------------
contracts["contract_start_year"] = pd.to_datetime(
    contracts["date_begin_contract"], errors="coerce"
).dt.year

contracts["decade"] = (contracts["contract_start_year"] // 10) * 10

before_filter = len(contracts)

contracts = contracts[
    (contracts["contract_start_year"] >= 1700) &
    (contracts["contract_start_year"] < 1790)
].copy()

print(f"[info] Filtered to 1700–1780s: {before_filter:,} -> {len(contracts):,}")

# -------------------- Map reason_end_contract --------------------
if "reason_end_contract" not in contracts.columns:
    print("[error] Column 'reason_end_contract' not found.")
    sys.exit(1)

# Actual null values, if any
contracts["reason_end_contract_raw"] = contracts["reason_end_contract"]

contracts["outcome_group_revised"] = contracts["reason_end_contract_raw"].map(OUTCOME_MAPPING)

# Check unmapped non-null categories
unmapped = (
    contracts.loc[
        contracts["outcome_group_revised"].isna() &
        contracts["reason_end_contract_raw"].notna(),
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
    print("\nPlease add these to OUTCOME_MAPPING before using results.")
else:
    print("[info] All non-null reason_end_contract categories are mapped.")

# Only actual null values are assigned as Unknown / unclear
contracts.loc[
    contracts["reason_end_contract_raw"].isna(),
    "outcome_group_revised"
] = "Unknown / unclear"

# If unmapped categories exist, keep them visible rather than silently assigning them
contracts["outcome_group_revised"] = contracts["outcome_group_revised"].fillna("UNMAPPED")


# -------------------- Load and map ranks --------------------
ranks_path = os.path.join(DATA_RAW, "voc_ranks.csv")

if not os.path.exists(ranks_path):
    print(f"[warn] Missing ranks file: {ranks_path}")
    contracts["rank_parent"] = "Unknown"
else:
    ranks = pd.read_csv(ranks_path, low_memory=False)

    contracts.columns = contracts.columns.str.strip()
    ranks.columns = ranks.columns.str.strip()

    contracts["rank_id"] = to_int_like(contracts.get("rank_id"))
    ranks["rank_id"] = to_int_like(ranks.get("rank_id"))

    use_col = None
    for c in ["category", "parent_rank", "subcategory"]:
        if c in ranks.columns:
            use_col = c
            break

    if use_col and "rank_id" in ranks.columns:
        ranks_min = ranks[["rank_id", use_col]].drop_duplicates()
        ranks_min.columns = ["rank_id", "rank_group_raw"]

        contracts = contracts.merge(
            ranks_min,
            on="rank_id",
            how="left"
        )

        contracts["rank_parent"] = contracts["rank_group_raw"].apply(map_parent_rank)
    else:
        print("[warn] Could not find a rank grouping column in voc_ranks.csv")
        contracts["rank_parent"] = "Unknown"


# -------------------- Mark first contracts as hiring / recruitment --------------------
if "person_cluster_id" in contracts.columns and "date_begin_contract" in contracts.columns:
    contracts["date_begin_contract"] = pd.to_datetime(
        contracts["date_begin_contract"], errors="coerce"
    )

    first_dates = (
        contracts
        .groupby("person_cluster_id")["date_begin_contract"]
        .transform("min")
    )

    contracts["is_first_contract"] = (
        contracts["date_begin_contract"] == first_dates
    ).astype(int)

    print("[info] Created is_first_contract as hiring/recruitment indicator.")
else:
    contracts["is_first_contract"] = 0
    print("[warn] Could not create is_first_contract. Missing person_cluster_id or date_begin_contract.")


# -------------------- Basic totals --------------------
total_records = len(contracts)
total_hires = int(contracts["is_first_contract"].sum())

print(f"[info] Total records in analysis subset: {total_records:,}")
print(f"[info] Total first contracts / hires: {total_hires:,}")


# ======================================================
# OUTPUT 1: revised outcome counts
# ======================================================
outcome_counts = (
    contracts["outcome_group_revised"]
    .value_counts()
    .reset_index()
)

outcome_counts.columns = ["outcome_group_revised", "count"]
outcome_counts["percentage"] = (
    outcome_counts["count"] / total_records * 100
).round(2)

save_csv(
    outcome_counts,
    os.path.join(TABLES, "revised_outcome_counts_1700_1780.csv")
)


# ======================================================
# OUTPUT 2: raw reason to revised outcome mapping
# ======================================================
reason_mapping = (
    contracts
    .assign(reason_end_contract_raw=contracts["reason_end_contract_raw"].fillna("NULL"))
    .groupby(["reason_end_contract_raw", "outcome_group_revised"], dropna=False)
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

reason_mapping["percentage_of_dataset"] = (
    reason_mapping["count"] / total_records * 100
).round(2)

save_csv(
    reason_mapping,
    os.path.join(TABLES, "reason_end_contract_mapping_revised_1700_1780.csv")
)


# ======================================================
# OUTPUT 3: rank x outcome counts
# ======================================================
rank_outcome_count = pd.crosstab(
    contracts["rank_parent"],
    contracts["outcome_group_revised"]
).reset_index()

save_csv(
    rank_outcome_count,
    os.path.join(TABLES, "rank_by_revised_outcome_count_1700_1780.csv")
)


# ======================================================
# OUTPUT 4: rank x outcome percentages within rank
# ======================================================
rank_outcome_pct = (
    pd.crosstab(
        contracts["rank_parent"],
        contracts["outcome_group_revised"],
        normalize="index"
    ) * 100
).round(2).reset_index()

save_csv(
    rank_outcome_pct,
    os.path.join(TABLES, "rank_by_revised_outcome_pct_1700_1780.csv")
)


# ======================================================
# OUTPUT 5: hiring by rank
# ======================================================
hiring_by_rank = (
    contracts
    .groupby("rank_parent", as_index=False)
    .agg(
        contracts_n=("rank_parent", "size"),
        hires_n=("is_first_contract", "sum")
    )
)

hiring_by_rank["hiring_rate_within_rank"] = (
    hiring_by_rank["hires_n"] / hiring_by_rank["contracts_n"] * 100
).round(2)

hiring_by_rank["hiring_share_of_all_hires"] = (
    hiring_by_rank["hires_n"] / total_hires * 100
).round(2)

hiring_by_rank = hiring_by_rank.sort_values("contracts_n", ascending=False)

save_csv(
    hiring_by_rank,
    os.path.join(TABLES, "hiring_by_rank_1700_1780.csv")
)


# ======================================================
# OUTPUT 6: endings vs hiring by rank
# ======================================================
# Endings here means all contracts in the selected period, grouped by outcome reason.
# Hiring means first contracts in the selected period.
rank_outcome_long = (
    contracts
    .groupby(["rank_parent", "outcome_group_revised"], as_index=False)
    .size()
    .rename(columns={"size": "endings_n"})
)

rank_totals = (
    contracts
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
    hiring_by_rank[[
        "rank_parent",
        "hires_n",
        "hiring_rate_within_rank",
        "hiring_share_of_all_hires"
    ]],
    on="rank_parent",
    how="left"
)

save_csv(
    rank_outcome_long,
    os.path.join(TABLES, "endings_vs_hiring_by_rank_1700_1780.csv")
)


# ======================================================
# OUTPUT 7: decade x rank x outcome
# ======================================================
decade_rank_outcome = (
    contracts
    .groupby(["decade", "rank_parent", "outcome_group_revised"], as_index=False)
    .size()
    .rename(columns={"size": "endings_n"})
)

decade_rank_totals = (
    contracts
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
    os.path.join(TABLES, "decade_rank_revised_outcome_1700_1780.csv")
)


# ======================================================
# OUTPUT 8: hiring by decade and rank
# ======================================================
hiring_decade_rank = (
    contracts
    .groupby(["decade", "rank_parent"], as_index=False)
    .agg(
        contracts_n=("rank_parent", "size"),
        hires_n=("is_first_contract", "sum")
    )
)

hiring_decade_rank["hiring_rate_within_decade_rank"] = (
    hiring_decade_rank["hires_n"] /
    hiring_decade_rank["contracts_n"] * 100
).round(2)

decade_hires = (
    hiring_decade_rank
    .groupby("decade", as_index=False)["hires_n"]
    .sum()
    .rename(columns={"hires_n": "total_hires_decade"})
)

hiring_decade_rank = hiring_decade_rank.merge(
    decade_hires,
    on="decade",
    how="left"
)

hiring_decade_rank["hiring_share_within_decade"] = (
    hiring_decade_rank["hires_n"] /
    hiring_decade_rank["total_hires_decade"] * 100
).round(2)

save_csv(
    hiring_decade_rank,
    os.path.join(TABLES, "hiring_by_decade_rank_1700_1780.csv")
)


# ======================================================
# OUTPUT 9: decade rank endings vs hiring
# ======================================================
decade_rank_comparison = decade_rank_outcome.merge(
    hiring_decade_rank[[
        "decade",
        "rank_parent",
        "hires_n",
        "hiring_rate_within_decade_rank",
        "hiring_share_within_decade"
    ]],
    on=["decade", "rank_parent"],
    how="left"
)

save_csv(
    decade_rank_comparison,
    os.path.join(TABLES, "endings_vs_hiring_by_decade_rank_1700_1780.csv")
)


# -------------------- Print summaries --------------------
print("\n==============================")
print("Revised outcome counts")
print("==============================")
print(outcome_counts)

print("\n==============================")
print("Hiring by rank")
print("==============================")
print(hiring_by_rank)

print("\n==============================")
print("Rank x outcome percentages")
print("==============================")
print(rank_outcome_pct)

print("\n[done] Revised outcome and hiring comparison complete.")