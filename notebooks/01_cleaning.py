"""
01_cleaning.py

Cleaning script for the VOC project.

What this script does
- Loads the raw VOC contracts dataset.
- Creates cleaned variables used in the descriptive and modelling scripts.
- Filters the main analysis period to contracts starting from 1700 up to, but not including, 1790.
- Creates rank, region, decade, and other analysis variables.
- Creates the revised outcome grouping used in the article analysis.
- Creates a corrected first-contract indicator.

Important methodological choices
- First contracts are identified on the full dataset before applying the 1700-1780s analysis filter.
- First contracts are treated as a proxy for new workforce entry, not as a direct hiring rate.
- The revised outcome grouping separates:
  * Death
  * Repatriated
  * Chamber
  * Unknown / unclear
  * Other
  * Irregular exit
- Chamber outcomes are kept separate because they refer to administrative chamber categories rather than clear worker exits.
- Age and Free citizen are not treated as Unknown. They are placed in Other because they have specific meanings in the source data.
- Shipwrecked is grouped under Death because the source interpretation indicates drowning after ship sinking.

Main outputs
- data_clean/contracts_clean.csv
- tables/outcome_counts_revised.csv
- tables/reason_end_contract_mapping_check_revised.csv

Main columns created or updated
- contract_start_year
- decade
- rank_parent
- region_label
- outcome_group_revised
- outcome_group
- has_person_cluster_id
- is_first_contract_true
- is_first_contract
"""

import os, sys
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_RAW   = os.path.join(BASE, "data_raw")
DATA_CLEAN = os.path.join(BASE, "data_clean")
TABLES     = os.path.join(BASE, "tables")
DOCS       = os.path.join(BASE, "docs")

os.makedirs(DATA_CLEAN, exist_ok=True)
os.makedirs(TABLES, exist_ok=True)
os.makedirs(DOCS, exist_ok=True)

def save_csv(df, path):
    df.to_csv(path, index=False)
    print(f"[saved] {path}")

# ---------- 1) Load contracts ----------
print("[info] Loading contracts")
contracts_path = os.path.join(DATA_RAW, "voc_persons_contracts.csv")
contracts = pd.read_csv(contracts_path, low_memory=False)
before = len(contracts)

# Convert contract start dates before calculating first contracts and filtering
contracts["date_begin_contract"] = pd.to_datetime(
    contracts["date_begin_contract"], errors="coerce"
)

contracts["contract_start_year"] = contracts["date_begin_contract"].dt.year

# Mark whether a record has a person_cluster_id.
# First-contract status can only be identified for records with person_cluster_id.
contracts["has_person_cluster_id"] = contracts["person_cluster_id"].notna()

# Calculate true first contracts on the full dataset before filtering to 1700-1780.
# This avoids incorrectly treating a person's first visible contract inside the filtered
# period as their true first contract if they had an earlier contract before 1700.
if "person_cluster_id" in contracts.columns and "date_begin_contract" in contracts.columns:
    first_dates = (
        contracts
        .groupby("person_cluster_id")["date_begin_contract"]
        .transform("min")
    )

    contracts["is_first_contract_true"] = (
        (contracts["has_person_cluster_id"]) &
        (contracts["date_begin_contract"] == first_dates)
    ).astype(int)

    # Keep this older column name as well, so later scripts that already use
    # is_first_contract do not break.
    contracts["is_first_contract"] = contracts["is_first_contract_true"]
else:
    contracts["is_first_contract_true"] = 0
    contracts["is_first_contract"] = 0

print("[info] Created first-contract indicator on the full dataset before filtering.")

# Filter 1700-1780s for the actual analysis
contracts = contracts[
    (contracts["contract_start_year"] >= 1700) &
    (contracts["contract_start_year"] < 1790)
].copy()

after = len(contracts)
print(f"[info] Filtered contracts to 1700-1780: {before} -> {after}")
save_csv(contracts, os.path.join(DATA_CLEAN, "contracts_filtered.csv"))

# After filtering the contracts, we want to double-check that the number of contracts
# per decade looks reasonable. This helps catch mistakes like accidentally dropping years.

dec_counts = (
    contracts
    .assign(decade=(contracts["contract_start_year"] // 10) * 10)  # compute decade (e.g. 1785 -> 1780)
    .groupby("decade")
    .size()
)

print("[diag] contracts by decade:\n", dec_counts)

# Extra safety check: if the number of contracts in the last decade
# is much smaller than the previous one, it may mean we cut the data too early.
if len(dec_counts) >= 3:  # only check if we have at least 3 decades
    last = dec_counts.iloc[-1]
    prev = dec_counts.iloc[-2]
    if last < 0.3 * prev:  # if the final decade is less than 30% of the previous one
        print("[warn] Final decade count is much smaller than the previous decade.")
        print("       This could mean the upper bound of the filter is excluding data.")


# Keep raw origin text for coverage reporting
if "place_of_origin" in contracts.columns:
    contracts["place_of_origin_raw"] = contracts["place_of_origin"]
else:
    contracts["place_of_origin_raw"] = pd.NA

# ---------- 2) Load places ----------
places_std_path = os.path.join(DATA_RAW, "voc_places_standardized.csv")
if not os.path.exists(places_std_path):
    print("[error] Missing voc_places_standardized.csv")
    sys.exit(1)
places_std = pd.read_csv(places_std_path, low_memory=False)

# Load bridge file (place_id -> standardized)
places_bridge_path = os.path.join(DATA_RAW, "voc_places.csv")
if not os.path.exists(places_bridge_path):
    print("[error] Missing voc_places.csv")
    sys.exit(1)
places_bridge = pd.read_csv(places_bridge_path, low_memory=False)

# ---------- 3) Merge standardized places to regions ----------
print("[info] Merging places to region codes A–I")

REGION_LABELS = {
    "A": "Dutch Republic",
    "B": "Low German",
    "C": "German interior",
    "D": "British Isles",
    "E": "France",
    "F": "Iberia",
    "G": "Italy/Corsica",
    "H": "Scandinavia",
    "I": "Eastern/Southeastern Europe",
}

# 1) contracts.place_id -> standardized id
contracts = contracts.merge(
    places_bridge[["place_id", "place_standardized_id"]].drop_duplicates(),
    on="place_id", how="left"
)

# 2) standardized -> region and label
pl_std = places_std[["place_standardized_id", "place_standardized", "region"]].drop_duplicates().copy()
pl_std["region_label"] = pl_std["region"].map(REGION_LABELS)
contracts = contracts.merge(pl_std, on="place_standardized_id", how="left")

# Fill missing
contracts["region"] = contracts["region"].fillna("U")
contracts["region_label"] = contracts["region_label"].fillna("Unknown")

# Conservative fallbacks: Dutch hints
if "country_code" in contracts.columns:
    cc_dutch = {"NL","NLD","Netherlands","NETHERLANDS","nl","Nl","Netherland"}
    mask_cc = contracts["region_label"].eq("Unknown") & contracts["country_code"].astype(str).isin(cc_dutch)
    contracts.loc[mask_cc, "region_label"] = "Dutch Republic"

if "place_of_origin_raw" in contracts.columns:
    dutch_terms = [
        "amsterdam","rotterdam","delft","enkhuizen","hoorn","zeeland","holland",
        "utrecht","gelderland","friesland","groningen","overijssel","drenthe",
        "north holland","south holland","den haag","the hague","haarlem","middelburg","vlissingen"
    ]
    por = contracts["place_of_origin_raw"].astype(str).str.lower()
    mask_txt = contracts["region_label"].eq("Unknown") & por.str.contains("|".join(dutch_terms), na=False)
    contracts.loc[mask_txt, "region_label"] = "Dutch Republic"

contracts["is_dutch"] = (contracts["region_label"] == "Dutch Republic").astype(int)

# Coverage diagnostics
matched_region = float((contracts["region_label"] != "Unknown").mean() * 100.0)
if "place_of_origin_raw" in contracts.columns:
    has_any_origin_text = float(contracts["place_of_origin_raw"].notna().mean() * 100.0)
else:
    has_any_origin_text = float("nan")
txt_origin = f"{has_any_origin_text:.1f}%" if pd.notna(has_any_origin_text) else "n/a"
print(f"[info] Region coverage after fallbacks: {matched_region:.1f}% (raw origin text present: {txt_origin})")

# Region counts
region_counts = contracts["region_label"].value_counts(dropna=False).reset_index()
region_counts.columns = ["region_label", "n_contracts"]
save_csv(region_counts, os.path.join(TABLES, "region_counts.csv"))

# ---------- 4) Map ranks ----------
print("[info] Mapping ranks to 6 parent buckets and seniority")
ranks_path = os.path.join(DATA_RAW, "voc_ranks.csv")
ranks = pd.read_csv(ranks_path, low_memory=False)

contracts.columns = contracts.columns.str.strip()
ranks.columns = ranks.columns.str.strip()

def to_int_like(s):
    try:
        return s.astype("Int64")
    except Exception:
        return pd.to_numeric(s, errors="coerce").astype("Int64")

contracts["rank_id"] = to_int_like(contracts.get("rank_id"))
ranks["rank_id"] = to_int_like(ranks.get("rank_id"))

use_col = None
for c in ["category","parent_rank","subcategory"]:
    if c in ranks.columns:
        use_col = c; break

if use_col and "rank_id" in ranks.columns:
    ranks_min = ranks[["rank_id", use_col]].drop_duplicates()
    ranks_min.columns = ["rank_id","rank_group_raw"]
    contracts = contracts.merge(ranks_min,on="rank_id",how="left")
else:
    contracts["rank_group_raw"] = np.nan

contracts["rank_group_raw"] = contracts["rank_group_raw"].astype(str).str.upper()

RAW_TO_PARENT = {
    "SEA":"Sea","SHIP":"Ship","TRADE":"Trade","MEDICAL":"Medical",
    "MILITARY":"Military","OTHER":"Other"
}
def map_parent(x):
    if pd.isna(x) or x=="NAN": return np.nan
    if x in RAW_TO_PARENT: return RAW_TO_PARENT[x]
    xl = str(x).lower()
    if "sea" in xl: return "Sea"
    if any(k in xl for k in ["ship","sail","mate","boatswain"]): return "Ship"
    if any(k in xl for k in ["trad","merchant"]): return "Trade"
    if any(k in xl for k in ["medic","surg"]): return "Medical"
    if any(k in xl for k in ["milit","soldier","gunner","corporal"]): return "Military"
    return "Other"

contracts["rank_parent"] = contracts["rank_group_raw"].apply(map_parent).fillna("Unknown")

# Wage ladder
wage_col = None
ranks_cols_lower = {c.lower(): c for c in ranks.columns}
for cand in ["median_wage","median wage","median_wage_eur"]:
    if cand in ranks_cols_lower: wage_col = ranks_cols_lower[cand]; break
if wage_col is not None:
    wage_min = ranks[["rank_id",wage_col]].drop_duplicates().rename(columns={wage_col:"median_wage"})
    contracts = contracts.merge(wage_min,on="rank_id",how="left")
else:
    contracts["median_wage"] = np.nan

wages = contracts["median_wage"].dropna()
if len(wages) >= 5:
    q = wages.quantile([0.2,0.4,0.6,0.8]).to_dict()
    def wage_to_level(x):
        if pd.isna(x): return np.nan
        if x<=q[0.2]: return 1
        if x<=q[0.4]: return 2
        if x<=q[0.6]: return 3
        if x<=q[0.8]: return 4
        return 5
    contracts["rank_level"] = contracts["median_wage"].apply(wage_to_level)
else:
    fallback = {"Ship":2,"Sea":2,"Military":3,"Trade":4,"Medical":4,"Other":2,"Unknown":2}
    contracts["rank_level"] = contracts["rank_parent"].map(fallback)

contracts["is_high_rank"] = (contracts["rank_level"]>=4).astype(float)

rank_counts = contracts["rank_parent"].value_counts(dropna=False).reset_index()
rank_counts.columns = ["rank_parent","n_contracts"]
save_csv(rank_counts, os.path.join(TABLES, "rank_counts.csv"))

# ---------- 5) Outcomes ----------
print("[info] Recoding outcomes with revised outcome grouping")

reason_col = "reason_end_contract" if "reason_end_contract" in contracts.columns else None
contracts["reason_end_contract_raw"] = contracts[reason_col] if reason_col else np.nan


def normalize_reason(value):
    """
    Normalize raw reason_end_contract values before mapping.

    I keep the original raw value in the data, but use this normalized version
    only for the dictionary-based mapping.
    """
    if pd.isna(value):
        return None
    return str(value).strip().lower()


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
    "dismissed": "Irregular exit",
    "penalised or punished": "Irregular exit",
    "penalized or punished": "Irregular exit",
    "removed": "Irregular exit",
    "woman": "Irregular exit",

    # Chamber
    "amsterdam chamber": "Chamber",
    "delft chamber": "Chamber",
    "rotterdam chamber": "Chamber",
    "zeeland chamber": "Chamber",
    "hoorn chamber": "Chamber",
    "enkhuizen chamber": "Chamber",

    # Unknown / unclear
    "missing": "Unknown / unclear",
    "unknown": "Unknown / unclear",
    "not recorded": "Unknown / unclear",
    "last record": "Unknown / unclear",

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

contracts["reason_end_contract_normalized"] = (
    contracts["reason_end_contract_raw"].apply(normalize_reason)
)

contracts["outcome_group_revised"] = (
    contracts["reason_end_contract_normalized"]
    .map(OUTCOME_MAPPING_NORMALIZED)
)

# Actual null values are treated as Unknown / unclear.
contracts.loc[
    contracts["reason_end_contract_raw"].isna(),
    "outcome_group_revised"
] = "Unknown / unclear"

# Check whether any non-null categories were not mapped.
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
    raise ValueError("Unmapped reason_end_contract categories found. Please update OUTCOME_MAPPING_NORMALIZED.")

# Keep the old column name as an alias for compatibility with older scripts.
# Later, 02_descriptives.py and 03_models.py should be updated to use
# outcome_group_revised explicitly.
contracts["outcome_group"] = contracts["outcome_group_revised"]

outcome_counts = contracts["outcome_group_revised"].value_counts().reset_index()
outcome_counts.columns = ["outcome_group_revised", "n_contracts"]
save_csv(outcome_counts, os.path.join(TABLES, "outcome_counts_revised.csv"))

# Also save a mapping check table for transparency.
outcome_mapping_check = (
    contracts
    .assign(reason_end_contract_raw_for_table=contracts["reason_end_contract_raw"].fillna("NULL"))
    .groupby(
        [
            "reason_end_contract_raw_for_table",
            "reason_end_contract_normalized",
            "outcome_group_revised"
        ],
        dropna=False
    )
    .size()
    .reset_index(name="n_contracts")
    .sort_values("n_contracts", ascending=False)
)

outcome_mapping_check.columns = [
    "reason_end_contract_raw",
    "reason_end_contract_normalized",
    "outcome_group_revised",
    "n_contracts"
]

save_csv(
    outcome_mapping_check,
    os.path.join(TABLES, "reason_end_contract_mapping_check_revised.csv")
)


# ---------- 6) Save outputs ----------
save_csv(contracts, os.path.join(DATA_CLEAN,"contracts_clean.csv"))

# Methods notes
notes_path = os.path.join(DOCS,"methods_notes.txt")
with open(notes_path,"w",encoding="utf-8") as f:
    f.write("METHODS NOTES\n\n")
    f.write("Scope and selection\n")
    f.write(f"- Filtered contracts to 1700–1780: {before:,} → {after:,}\n")
    f.write("\nOrigins and regions\n")
    f.write(f"- Raw origin coverage: {txt_origin}\n")
    f.write(f"- Region coverage after fallbacks: {matched_region:.1f}%\n")
    f.write("\nRanks\n")
    f.write("- Ranks mapped to 6 parent categories; seniority derived from wage quintiles.\n")
    f.write("\nOutcomes\n")
    f.write("- Outcomes grouped into: Death, Repatriated, Chamber, Unknown / unclear, Other, and Irregular exit.\n")
print(f"[updated] {notes_path}")

print("[done] Cleaning complete.")
