"""
01_cleaning.py
Purpose: clean VOC workforce dataset (contracts 1700-1780), standardize regions,
map ranks, recode outcomes, and save ready-to-use outputs.

Outputs:
- data_clean/contracts_clean.csv
- data_clean/persons_summary.csv
- tables/region_counts.csv
- tables/rank_counts.csv
- tables/outcome_counts.csv
- docs/methods_notes.txt
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

# Filter 1700–1780 (based on contract start year)
contracts["contract_start_year"] = pd.to_datetime(
    contracts["date_begin_contract"], errors="coerce"
).dt.year
contracts = contracts[(contracts["contract_start_year"] >= 1700) & (contracts["contract_start_year"] < 1790)]
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
print("[info] Recoding outcomes")
reason_col = "reason_end_contract" if "reason_end_contract" in contracts.columns else None
contracts["reason_end_contract_raw"] = contracts[reason_col] if reason_col else np.nan
def map_outcome(text):
    if pd.isna(text): return "Unknown"
    t = str(text).strip().lower()
    if " chamber" in t: return "Unknown"
    if any(k in t for k in ["deceased","died","death","shipwreck","execut","murder"]): return "Death"
    if any(k in t for k in ["desert","dismiss","dismissal","penal","removed"]): return "Attrition"
    if any(k in t for k in ["repatriat","returned home","homebound","free citizen","back to"]): return "Repatriated"
    if any(k in t for k in ["missing","last record","unknown","not recorded","no further record","age"]): return "Unknown"
    return "Unknown"
contracts["outcome_group"] = contracts["reason_end_contract_raw"].apply(map_outcome)

outcome_counts = contracts["outcome_group"].value_counts().reset_index()
outcome_counts.columns = ["outcome_group","n_contracts"]
save_csv(outcome_counts, os.path.join(TABLES, "outcome_counts.csv"))

# -------------------- Mark first contracts --------------------
if "is_first_contract" not in contracts.columns:
    if "person_cluster_id" in contracts.columns and "date_begin_contract" in contracts.columns:
        # Convert dates
        contracts["date_begin_contract"] = pd.to_datetime(contracts["date_begin_contract"], errors="coerce")

        # Find earliest contract per person
        first_dates = (
            contracts.groupby("person_cluster_id")["date_begin_contract"]
            .transform("min")
        )

        # Flag first contracts correctly
        contracts["is_first_contract"] = (contracts["date_begin_contract"] == first_dates).astype(int)
    else:
        # Fallback if we really cannot do better
        contracts["is_first_contract"] = 0


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
    f.write("- Outcomes grouped into: Death / Repatriated / Attrition / Unknown.\n")
print(f"[updated] {notes_path}")

print("[done] Cleaning complete.")
