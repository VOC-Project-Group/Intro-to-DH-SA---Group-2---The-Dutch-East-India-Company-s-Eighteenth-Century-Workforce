"""
01_cleaning.py
Purpose: load the raw VOC data, clean it, standardize regions/ranks,
and save one tidy dataset for the rest of the project.

Inputs (in data_raw/):
  - voc_persons_contracts.csv
  - voc_places_standardized.csv
  - voc_ranks.csv

Outputs:
  - data_clean/contracts_clean.csv
  - data_clean/persons_summary.csv
  - docs/methods_notes.txt  (auto-written each run)
"""

import os, sys
import numpy as np
import pandas as pd

# ---------- Paths ----------
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_RAW   = os.path.join(BASE, "data_raw")
DATA_CLEAN = os.path.join(BASE, "data_clean")
TABLES     = os.path.join(BASE, "tables")          # descriptives will also write here
FIGURES    = os.path.join(BASE, "figures")         # plots are made in 02_descriptives.py
DOCS       = os.path.join(BASE, "docs")

for p in [DATA_CLEAN, TABLES, FIGURES, DOCS]:
    os.makedirs(p, exist_ok=True)

contracts_path = os.path.join(DATA_RAW, "voc_persons_contracts.csv")
places_std_path = os.path.join(DATA_RAW, "voc_places_standardized.csv")
ranks_path = os.path.join(DATA_RAW, "voc_ranks.csv")

# ---------- Small helpers ----------
def save_csv(df, path):
    df.to_csv(path, index=False)
    print(f"[saved] {path}  rows={len(df)}")

def parse_date_ser(s):
    """Parse a date column that might be YYYY-MM-DD or textual. Returns datetime or NaT."""
    return pd.to_datetime(s, errors="coerce", dayfirst=False, utc=False)

def to_int_like(s):  # nice safe converter for rank_id, etc.
    try:
        return s.astype("Int64")
    except Exception:
        return pd.to_numeric(s, errors="coerce").astype("Int64")

# ---------- 1) Load raw ----------
if not os.path.exists(contracts_path):
    print(f"[error] Missing file: {contracts_path}"); sys.exit(1)
if not os.path.exists(places_std_path):
    print(f"[error] Missing file: {places_std_path}"); sys.exit(1)
if not os.path.exists(ranks_path):
    print(f"[error] Missing file: {ranks_path}"); sys.exit(1)

contracts = pd.read_csv(contracts_path, low_memory=False)
places_std = pd.read_csv(places_std_path, low_memory=False)
ranks = pd.read_csv(ranks_path, low_memory=False)

# ---------- 2) Basic cleaning & scope ----------
# Contract start date
if "date_begin_contract" in contracts.columns:
    contracts["contract_start_date"] = parse_date_ser(contracts["date_begin_contract"])
else:
    contracts["contract_start_date"] = pd.NaT

contracts["contract_start_year"] = contracts["contract_start_date"].dt.year

# Keep 1700–1780 (inclusive)
before = len(contracts)
contracts = contracts[contracts["contract_start_year"].between(1700, 1780, inclusive="both")]
after = len(contracts)
missing_start_dates = before - after
print(f"[info] Filtered contracts to 1700–1780: {before} -> {after}")

# decade helper
contracts["decade"] = (contracts["contract_start_year"] // 10) * 10

# Keep a copy of raw origin text (useful for transparency)
if "place_of_origin" in contracts.columns:
    contracts["place_of_origin_raw"] = contracts["place_of_origin"]
else:
    contracts["place_of_origin_raw"] = np.nan

# ---------- 3) Merge standardized places to get 9-region scheme ----------
print("[info] Merging places to region codes A-I")

expected_places_cols = ["place_standardized_id", "place_standardized", "region"]
missing = [c for c in expected_places_cols if c not in places_std.columns]
if missing:
    print("[error] Standardized places file is missing:", missing)
    print("Available:", places_std.columns.tolist()); sys.exit(1)

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

# contracts has 'place_id' (provided by dataset) that connects to place_standardized_id
if "place_id" not in contracts.columns:
    print("[error] 'place_id' missing in contracts. Columns:", contracts.columns.tolist()); sys.exit(1)

pl = places_std[["place_standardized_id", "place_standardized", "region"]].drop_duplicates().copy()
pl["region_label"] = pl["region"].map(REGION_LABELS)

contracts = contracts.merge(
    pl,
    left_on="place_id",
    right_on="place_standardized_id",
    how="left"
)

# Unknown label where merge failed
contracts["region"] = contracts["region"].fillna("U")
contracts["region_label"] = contracts["region_label"].fillna("Unknown")

# Dutch flag (strict = only A)
contracts["is_dutch"] = (contracts["region_label"] == "Dutch Republic").astype(int)

# Coverage stats for notes
has_any_origin_text = float(contracts["place_of_origin_raw"].notna().mean() * 100.0)
matched_region = float((contracts["region_label"] != "Unknown").mean() * 100.0)
print(f"[info] Region assigned for {matched_region:.1f}% of rows; raw origin text present in {has_any_origin_text:.1f}%.")

# ---------- 4) Rank grouping & seniority ----------
print("[info] Mapping ranks to 6 parent buckets and seniority")

# Normalize column names a bit
ranks.columns = ranks.columns.str.strip()
contracts.columns = contracts.columns.str.strip()
contracts["rank_id"] = to_int_like(contracts.get("rank_id"))

# Choose a high-level grouping present in ranks (category/parent_rank/subcategory)
use_col = None
for c in ["category", "parent_rank", "subcategory"]:
    if c in ranks.columns:
        use_col = c; break

if use_col and "rank_id" in ranks.columns:
    ranks_min = ranks[["rank_id", use_col]].drop_duplicates()
    ranks_min.columns = ["rank_id", "rank_group_raw"]
    contracts = contracts.merge(ranks_min, on="rank_id", how="left")
else:
    contracts["rank_group_raw"] = np.nan

contracts["rank_group_raw"] = contracts["rank_group_raw"].astype(str).str.upper()

RAW_TO_PARENT = {
    "SEA": "Sea",
    "SHIP": "Ship",
    "TRADE": "Trade",
    "MEDICAL": "Medical",
    "MILITARY": "Military",
    "OTHER": "Other",
}
def map_parent(x):
    if pd.isna(x) or x == "NAN": return np.nan
    if x in RAW_TO_PARENT: return RAW_TO_PARENT[x]
    xl = str(x).lower()
    if "sea" in xl: return "Sea"
    if any(k in xl for k in ["ship","sail","mate","boatswain"]): return "Ship"
    if any(k in xl for k in ["trad","merchant"]): return "Trade"
    if any(k in xl for k in ["medic","surg"]): return "Medical"
    if any(k in xl for k in ["milit","soldier","gunner","corporal"]): return "Military"
    return "Other"

contracts["rank_parent"] = contracts["rank_group_raw"].apply(map_parent).fillna("Unknown")

# Merge median wage and build rank_level from quintiles (1..5)
wage_col = None
ranks_cols_lower = {c.lower(): c for c in ranks.columns}
for cand in ["median_wage", "median wage", "median_wage_eur"]:
    if cand in ranks_cols_lower:
        wage_col = ranks_cols_lower[cand]; break

if wage_col is not None and "rank_id" in ranks.columns:
    wage_min = ranks[["rank_id", wage_col]].drop_duplicates().rename(columns={wage_col: "median_wage"})
    contracts = contracts.merge(wage_min, on="rank_id", how="left")
else:
    contracts["median_wage"] = np.nan

wages = contracts["median_wage"].dropna()
if len(wages) >= 5:
    q = wages.quantile([0.2, 0.4, 0.6, 0.8]).to_dict()
    def wage_to_level(x):
        if pd.isna(x): return np.nan
        if x <= q[0.2]: return 1
        if x <= q[0.4]: return 2
        if x <= q[0.6]: return 3
        if x <= q[0.8]: return 4
        return 5
    contracts["rank_level"] = contracts["median_wage"].apply(wage_to_level)
else:
    # Coarse fallback if wages are missing
    fallback = {"Ship": 2, "Sea": 2, "Military": 3, "Trade": 4, "Medical": 4, "Other": 2, "Unknown": 2}
    contracts["rank_level"] = contracts["rank_parent"].map(fallback)

contracts["is_high_rank"] = (contracts["rank_level"] >= 4).astype(float)

# ---------- 5) Outcome recoding ----------
print("[info] Recoding outcomes")
reason_col = "reason_end_contract" if "reason_end_contract" in contracts.columns else None
contracts["reason_end_contract_raw"] = contracts[reason_col] if reason_col else np.nan

def map_outcome(text):
    if pd.isna(text): return np.nan
    t = str(text).strip().lower()
    if " chamber" in t: return "Unknown"
    if any(k in t for k in ["deceased","died","death","shipwreck","execut","murder"]): return "Death"
    if any(k in t for k in ["desert","dismiss","dismissal","penal","removed"]): return "Attrition"
    if any(k in t for k in ["repatriat","returned home","homebound","free citizen","back to"]): return "Repatriated"
    if any(k in t for k in ["missing","last record","unknown","not recorded","no further record","age"]): return "Unknown"
    return "Unknown"

contracts["outcome_group"] = contracts["reason_end_contract_raw"].apply(map_outcome)

# ---------- 6) Person-level summary ----------
if "person_cluster_id" in contracts.columns:
    persons_summary = (
        contracts[["person_cluster_id","decade"]]
        .groupby("person_cluster_id", as_index=False)
        .agg(first_decade=("decade","min"), contracts_n=("decade","count"))
    )
    save_csv(persons_summary, os.path.join(DATA_CLEAN, "persons_summary.csv"))

# ---------- 7) Save cleaned dataset ----------
save_csv(contracts, os.path.join(DATA_CLEAN, "contracts_clean.csv"))

# ---------- 8) Methods notes (auto-written) ----------
def fmt_int(x:int) -> str:
    try: return f"{int(x):,}"
    except: return str(x)

notes_path = os.path.join(DOCS, "methods_notes.txt")
with open(notes_path, "w", encoding="utf-8") as f:
    f.write("**METHODS NOTES**\n\n")
    f.write("**Scope and selection**\n")
    f.write("* We analyze contracts that begin between 1700 and 1780 inclusive because coverage is near complete in this period.\n")
    f.write("* Earlier decades are fragmentary, and the final decades are less consistent due to chartered ships and foreign regiments.\n")
    f.write(f"* Rows dropped due to missing/invalid start dates when filtering: **{fmt_int(missing_start_dates)}**.\n\n")

    f.write("**Origins and regions**\n")
    f.write("* We use the dataset’s nine region codes (A-I) to make analysis feasible and comparable with prior work.\n")
    f.write("* We acknowledge possible misclassification from standardization and loss of local variation.\n")
    f.write(f"* **{has_any_origin_text:.1f}%** of contracts contain a raw origin string; **{matched_region:.1f}%** could be linked to a standardized region via the bridge.\n")
    f.write("* “Unknown” regions reflect missing/ambiguous IDs in the bridge, not absence of origin information.\n\n")

    f.write("**Ranks**\n")
    f.write("* Detailed ranks are mapped to six parent categories and supplemented with a numeric ladder that approximates seniority.\n")
    f.write("* Rank seniority is derived from median wage quintiles in _voc_ranks.csv_; ranks in the top two quintiles are classified as “high rank.”\n\n")

    f.write("**Outcomes**\n")
    f.write("* Raw reasons are grouped into four analytical outcome categories: _Death, Repatriated, Attrition_, and _Unknown_.\n\n")

    f.write("**Dropped or missing**\n")
    f.write("* Rows before filtering (as documented by the dataset): **774,200**.\n")
    f.write(f"* Rows after filtering to 1700-1780: **{fmt_int(len(contracts))}**.\n")
    f.write("* Rows dropped when building the modeling dataset: **to be added after 03_models.py**.\n\n")

    f.write("**Reproducibility**\n")
    f.write("* Cleaning is scripted in _01_cleaning.py_. Descriptives are in _02_descriptives.py_. Modeling is in _03_models.py_.\n")
    f.write("* Outputs are saved in _data_clean_, _tables_, and _figures_.\n")
    f.write("* This file is automatically overwritten each run.\n")

print(f"[saved] {notes_path}")
print("[done] Cleaning complete.")
