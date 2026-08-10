"""
10_cleaning_outcome_group_v3_test.py

Purpose:
Test a revised grouping of reason_end_contract into historically clearer outcome categories.

This script:
- loads the raw VOC contracts dataset
- filters to 1700–1780s, matching the original project scope
- maps reason_end_contract into revised outcome groups:
    Death
    Repatriated
    Irregular exit
    Other known / administrative
    Unknown / unclear
- maps ranks into parent rank categories
- creates summary tables for checking the new grouping

This script does NOT overwrite 01_cleaning.py or contracts_clean.csv.
It only creates test output files in /tables/.
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

# -------------------- Settings --------------------
FILTER_1700_1780 = True

# -------------------- Helper functions --------------------
def save_csv(df, path):
    df.to_csv(path, index=False)
    print(f"[saved] {path}")


def map_outcome_v3(text):
    """
    Revised outcome grouping based on a more careful interpretation of reason_end_contract.

    Key changes compared to old 01_cleaning.py:
    - "Attrition" is renamed to "Irregular exit"
    - "Age" is no longer treated as Unknown
    - "Free citizen" is no longer treated as Repatriated
    - Chamber-related categories are no longer treated as Unknown
    - Unknown is reserved for genuinely unclear/missing categories
    """

    if pd.isna(text):
        return "Unknown / unclear"

    t = str(text).strip().lower()

    # Real missing / unclear categories
    if t in [
        "missing",
        "unknown",
        "not recorded",
        "last record",
        "no further record",
        ""
    ]:
        return "Unknown / unclear"

    # Death-related categories
    if any(k in t for k in [
        "deceased",
        "death penalty",
        "murdered",
        "shipwrecked"
    ]):
        return "Death"

    # Clear repatriation
    if "repatriated" in t:
        return "Repatriated"

    # Irregular / non-standard exit
    if any(k in t for k in [
        "deserted",
        "dismissal",
        "penalised",
        "punished",
        "removed",
        "woman"
    ]):
        return "Irregular exit"

    # Other known / administrative outcomes
    if any(k in t for k in [
        "free citizen",
        "transferred",
        "to a man of war",
        "to a private ship",
        "to regiment",
        "remains at the cape",
        "chamber",
        "absent upon departure",
        "age",
        "unfit to work",
        "resignation",
        "otherwise",
        "in lening gaan"
    ]):
        return "Other known / administrative"

    # Fallback category
    return "Other known / administrative"


def map_outcome_old(text):
    """
    Old grouping logic from 01_cleaning.py.
    Included only for comparison.
    """

    if pd.isna(text):
        return "Unknown"

    t = str(text).strip().lower()

    if " chamber" in t:
        return "Unknown"

    if any(k in t for k in ["deceased", "died", "death", "shipwreck", "execut", "murder"]):
        return "Death"

    if any(k in t for k in ["desert", "dismiss", "dismissal", "penal", "removed"]):
        return "Attrition"

    if any(k in t for k in ["repatriat", "returned home", "homebound", "free citizen", "back to"]):
        return "Repatriated"

    if any(k in t for k in ["missing", "last record", "unknown", "not recorded", "no further record", "age"]):
        return "Unknown"

    return "Unknown"


def to_int_like(s):
    try:
        return s.astype("Int64")
    except Exception:
        return pd.to_numeric(s, errors="coerce").astype("Int64")


def map_parent_rank(x):
    """
    Maps detailed rank group labels to six parent rank categories.
    Same logic as in 01_cleaning.py.
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
        "OTHER": "Other"
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

if FILTER_1700_1780:
    before_filter = len(contracts)

    contracts = contracts[
        (contracts["contract_start_year"] >= 1700) &
        (contracts["contract_start_year"] < 1790)
    ].copy()

    print(f"[info] Filtered to 1700–1780s: {before_filter:,} -> {len(contracts):,}")

suffix = "1700_1780" if FILTER_1700_1780 else "full"

# -------------------- Check reason_end_contract --------------------
if "reason_end_contract" not in contracts.columns:
    print("[error] Column 'reason_end_contract' not found.")
    sys.exit(1)

contracts["reason_end_contract_raw"] = contracts["reason_end_contract"].fillna("MISSING")

# -------------------- Apply old and new outcome groupings --------------------
contracts["outcome_group_old"] = contracts["reason_end_contract_raw"].apply(map_outcome_old)
contracts["outcome_group_v3"] = contracts["reason_end_contract_raw"].apply(map_outcome_v3)

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

# -------------------- Summary 1: raw reason counts --------------------
total_records = len(contracts)

raw_reason_counts = (
    contracts["reason_end_contract_raw"]
    .value_counts()
    .reset_index()
)

raw_reason_counts.columns = ["reason_end_contract_raw", "count"]
raw_reason_counts["percentage"] = (
    raw_reason_counts["count"] / total_records * 100
).round(2)

save_csv(
    raw_reason_counts,
    os.path.join(TABLES, f"reason_end_contract_raw_counts_{suffix}.csv")
)

# -------------------- Summary 2: new outcome group counts --------------------
v3_counts = (
    contracts["outcome_group_v3"]
    .value_counts()
    .reset_index()
)

v3_counts.columns = ["outcome_group_v3", "count"]
v3_counts["percentage"] = (
    v3_counts["count"] / total_records * 100
).round(2)

save_csv(
    v3_counts,
    os.path.join(TABLES, f"outcome_group_v3_counts_{suffix}.csv")
)

# -------------------- Summary 3: old vs new grouping --------------------
old_vs_v3 = (
    contracts
    .groupby(["outcome_group_old", "outcome_group_v3"], dropna=False)
    .size()
    .reset_index(name="count")
    .sort_values(["outcome_group_old", "count"], ascending=[True, False])
)

old_vs_v3["percentage_of_dataset"] = (
    old_vs_v3["count"] / total_records * 100
).round(2)

save_csv(
    old_vs_v3,
    os.path.join(TABLES, f"outcome_group_old_vs_v3_{suffix}.csv")
)

# -------------------- Summary 4: raw reason to v3 mapping --------------------
reason_mapping_v3 = (
    contracts
    .groupby(["reason_end_contract_raw", "outcome_group_v3"], dropna=False)
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

reason_mapping_v3["percentage_of_dataset"] = (
    reason_mapping_v3["count"] / total_records * 100
).round(2)

save_csv(
    reason_mapping_v3,
    os.path.join(TABLES, f"reason_end_contract_mapping_v3_{suffix}.csv")
)

# -------------------- Summary 5: rank x outcome counts --------------------
rank_outcome_count = pd.crosstab(
    contracts["rank_parent"],
    contracts["outcome_group_v3"]
).reset_index()

save_csv(
    rank_outcome_count,
    os.path.join(TABLES, f"rank_parent_by_outcome_v3_count_{suffix}.csv")
)

# -------------------- Summary 6: rank x outcome percentages --------------------
rank_outcome_pct = (
    pd.crosstab(
        contracts["rank_parent"],
        contracts["outcome_group_v3"],
        normalize="index"
    ) * 100
).round(2).reset_index()

save_csv(
    rank_outcome_pct,
    os.path.join(TABLES, f"rank_parent_by_outcome_v3_pct_{suffix}.csv")
)

# -------------------- Summary 7: decade x outcome counts --------------------
decade_outcome_count = pd.crosstab(
    contracts["decade"],
    contracts["outcome_group_v3"]
).reset_index()

save_csv(
    decade_outcome_count,
    os.path.join(TABLES, f"decade_by_outcome_v3_count_{suffix}.csv")
)

# -------------------- Summary 8: decade x outcome percentages --------------------
decade_outcome_pct = (
    pd.crosstab(
        contracts["decade"],
        contracts["outcome_group_v3"],
        normalize="index"
    ) * 100
).round(2).reset_index()

save_csv(
    decade_outcome_pct,
    os.path.join(TABLES, f"decade_by_outcome_v3_pct_{suffix}.csv")
)

# -------------------- Print useful summaries --------------------
print("\n==============================")
print("Outcome group v3 counts")
print("==============================")
print(v3_counts)

print("\n==============================")
print("Old vs v3 grouping")
print("==============================")
print(old_vs_v3)

print("\n==============================")
print("Top raw reasons")
print("==============================")
print(raw_reason_counts.head(30))

print("\n[done] Outcome grouping v3 test complete.")