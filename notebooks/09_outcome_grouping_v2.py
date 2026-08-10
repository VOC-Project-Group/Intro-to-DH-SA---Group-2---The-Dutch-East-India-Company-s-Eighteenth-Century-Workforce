"""
09_outcome_grouping_v2.py

Purpose:
Create a revised outcome grouping for reason_end_contract based on the source paper's
explanation of end-of-contract reasons.

This script:
- loads the full raw VOC contracts dataset
- optionally filters to 1700–1780, like the original project
- creates outcome_group_v2 with more historically careful categories
- saves counts and percentages
- compares the old 4-group logic with the new grouping
"""

import os
import pandas as pd
import numpy as np

# -------------------- Paths --------------------
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(BASE, "data_raw")
TABLES = os.path.join(BASE, "tables")

os.makedirs(TABLES, exist_ok=True)

# -------------------- Settings --------------------
# Change this to False if you want the full dataset instead of 1700–1780.
FILTER_1700_1780 = True

# -------------------- Load data --------------------
contracts_path = os.path.join(DATA_RAW, "voc_persons_contracts.csv")
contracts = pd.read_csv(contracts_path, low_memory=False)

print(f"[info] Loaded full dataset: {len(contracts):,} records")

# -------------------- Optional date filter --------------------
if FILTER_1700_1780:
    contracts["contract_start_year"] = pd.to_datetime(
        contracts["date_begin_contract"], errors="coerce"
    ).dt.year

    before_filter = len(contracts)
    contracts = contracts[
        (contracts["contract_start_year"] >= 1700) &
        (contracts["contract_start_year"] < 1790)
    ].copy()

    print(f"[info] Filtered to 1700–1780s: {before_filter:,} -> {len(contracts):,}")

# -------------------- Raw reason column --------------------
if "reason_end_contract" not in contracts.columns:
    raise ValueError("Column 'reason_end_contract' not found in the dataset.")

contracts["reason_end_contract_raw"] = contracts["reason_end_contract"].fillna("MISSING")


# -------------------- Old grouping logic from 01_cleaning.py --------------------
def map_outcome_old(text):
    """
    This reproduces the old 4-group logic from 01_cleaning.py.
    It is included only for comparison.
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


# -------------------- New historically careful grouping --------------------
def map_outcome_v2(text):
    """
    Revised outcome grouping.

    The goal is not to force all reasons into Death/Repatriated/Attrition/Unknown.
    Instead, this keeps more historically meaningful categories separate.

    Important changes:
    - Age is no longer Unknown.
    - Free citizen is no longer Repatriated.
    - Attrition is replaced with Irregular exit.
    - Chamber categories are kept separate from Unknown.
    """

    if pd.isna(text):
        return "Unknown / missing"

    t = str(text).strip().lower()

    # Actual missing / unclear categories
    if t in ["missing", "unknown", "not recorded", "last record", "no further record", "missing values"]:
        return "Unknown / unclear"

    if t == "missing":
        return "Unknown / missing"

    # Death-related categories
    if any(k in t for k in ["deceased", "death penalty", "murdered", "shipwrecked"]):
        return "Death"

    # Clear repatriation
    if "repatriated" in t:
        return "Repatriated"

    # Irregular / non-standard exit
    if any(k in t for k in ["deserted", "dismissal", "penalised", "punished", "removed", "woman"]):
        return "Irregular exit"

    # Age is not unknown according to the source-paper explanation.
    # It refers to rustgage/pension or entry into an institution.
    if t == "age":
        return "Retirement / institutional care"

    # Became a free citizen, not necessarily repatriated.
    if "free citizen" in t:
        return "Settlement / status change"

    # Transfers or continuation in another service context
    if any(k in t for k in ["transferred", "to a man of war", "to a private ship", "to regiment"]):
        return "Transfer / continued service"

    # Remained at the Cape
    if "remains at the cape" in t:
        return "Stayed at the Cape"

    # Chamber-related administrative categories
    if "chamber" in t:
        return "Chamber / administrative category"

    # Pre-departure absence
    if "absent upon departure" in t:
        return "Absent upon departure"

    # Health / ability
    if "unfit to work" in t:
        return "Unfit to work"

    # Voluntary exit
    if "resignation" in t:
        return "Resignation"

    # Other categories that need manual checking
    if "otherwise" in t:
        return "Other / specified elsewhere"

    if "in lening gaan" in t:
        return "Unclear / needs translation"

    # Fallback
    return "Other / needs review"


contracts["outcome_group_old"] = contracts["reason_end_contract_raw"].apply(map_outcome_old)
contracts["outcome_group_v2"] = contracts["reason_end_contract_raw"].apply(map_outcome_v2)

# -------------------- Summary tables --------------------
total = len(contracts)

raw_counts = (
    contracts["reason_end_contract_raw"]
    .value_counts()
    .reset_index()
)
raw_counts.columns = ["reason_end_contract_raw", "count"]
raw_counts["percentage"] = (raw_counts["count"] / total * 100).round(2)

old_counts = (
    contracts["outcome_group_old"]
    .value_counts()
    .reset_index()
)
old_counts.columns = ["outcome_group_old", "count"]
old_counts["percentage"] = (old_counts["count"] / total * 100).round(2)

v2_counts = (
    contracts["outcome_group_v2"]
    .value_counts()
    .reset_index()
)
v2_counts.columns = ["outcome_group_v2", "count"]
v2_counts["percentage"] = (v2_counts["count"] / total * 100).round(2)

# Raw reason to new group mapping table
mapping_table = (
    contracts
    .groupby(["reason_end_contract_raw", "outcome_group_v2"], dropna=False)
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

mapping_table["percentage_of_dataset"] = (mapping_table["count"] / total * 100).round(2)

# Compare old vs new grouping
old_vs_new = (
    contracts
    .groupby(["outcome_group_old", "outcome_group_v2"], dropna=False)
    .size()
    .reset_index(name="count")
    .sort_values(["outcome_group_old", "count"], ascending=[True, False])
)

old_vs_new["percentage_of_dataset"] = (old_vs_new["count"] / total * 100).round(2)

# -------------------- Save outputs --------------------
suffix = "1700_1780" if FILTER_1700_1780 else "full"

raw_path = os.path.join(TABLES, f"reason_end_contract_raw_counts_{suffix}.csv")
old_path = os.path.join(TABLES, f"outcome_group_old_counts_{suffix}.csv")
v2_path = os.path.join(TABLES, f"outcome_group_v2_counts_{suffix}.csv")
mapping_path = os.path.join(TABLES, f"reason_end_contract_mapping_v2_{suffix}.csv")
compare_path = os.path.join(TABLES, f"outcome_group_old_vs_v2_{suffix}.csv")

raw_counts.to_csv(raw_path, index=False)
old_counts.to_csv(old_path, index=False)
v2_counts.to_csv(v2_path, index=False)
mapping_table.to_csv(mapping_path, index=False)
old_vs_new.to_csv(compare_path, index=False)

print("\n[Raw reason counts]")
print(raw_counts.head(40))

print("\n[Old grouping counts]")
print(old_counts)

print("\n[New grouping counts]")
print(v2_counts)

print("\n[Old vs new grouping]")
print(old_vs_new)

print("\nSaved files:")
print(raw_path)
print(old_path)
print(v2_path)
print(mapping_path)
print(compare_path)