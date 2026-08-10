"""
13_revised_outcome_first_contract_benchmark.py

Supplementary benchmark script for the revised VOC article analysis.

Purpose
- Checks how first contracts compare with major exit outcomes by rank.
- Uses first contracts as a proxy for new workforce entry, not as a direct hiring rate.
- Compares first-contract shares with:
  * Death share
  * Repatriated share
  * Death + Repatriated share
- Runs the comparison both overall and by decade.
- Includes identifiable-only sensitivity checks because many records have missing person_cluster_id.

Important methodological choices
- First contracts are calculated on the full dataset before filtering to the main analysis period.
- The main analysis period is 1700 up to, but not including, 1790.
- Revised outcome groups are used.
- The benchmark focuses on distributional shares across rank groups.
- This script helped refine the interpretation from a broad new-workforce-entry claim to a more specific first-contract versus exit-pattern comparison.

Main interpretation supported by this script
- Military ranks are consistently overrepresented among Death outcomes relative to their first-contract share.
- Repatriation follows a different pattern and is more concentrated among Sea ranks.
- Combining Death and Repatriated does not simply strengthen the military underrepresentation claim.
- The article should therefore frame the result as a rank-specific mismatch between new workforce entry and different types of exits, especially mortality.

Main outputs
- v3_reason_end_contract_mapping_check_1700_1780.csv
- v3_missing_person_cluster_by_disambiguation_1700_1780.csv
- v3_missing_person_cluster_by_rank_1700_1780.csv
- v3_rank_first_contract_exit_benchmark_all_records_1700_1780.csv
- v3_rank_first_contract_exit_benchmark_identifiable_only_1700_1780.csv
- v3_decade_rank_first_contract_exit_benchmark_all_records_1700_1780.csv
- v3_decade_rank_first_contract_exit_benchmark_identifiable_only_1700_1780.csv
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
START_YEAR = 1700
END_YEAR_EXCLUSIVE = 1790

# The project describes the period as 1700-1780.
# In the code, this means keeping all contracts from 1700 through the 1780s.
# So the filter is year >= 1700 and year < 1790.
RANK_ORDER = ["Sea", "Military", "Ship", "Other", "Medical", "Trade", "Unknown"]


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


def map_parent_rank(x):
    """
    Map rank category labels to the parent rank categories used in the analysis.

    For this benchmark, I use the category column from voc_ranks.csv. It already
    contains the main rank groups: SEA, MILITARY, SHIP, OTHER, MEDICAL, and TRADE.
    This function makes the labels consistent with the earlier output tables.
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

    return "Unknown"


def add_share_column(df, count_col, share_col):
    """
    Add a percentage share column based on the total of a count column.
    Shares are calculated across rank categories.
    """

    total = df[count_col].sum()

    if total == 0:
        df[share_col] = np.nan
    else:
        df[share_col] = (df[count_col] / total * 100).round(2)

    return df


def safe_pct(numerator, denominator):
    """
    Calculate a percentage safely when the denominator can be zero.
    """

    return np.where(denominator > 0, numerator / denominator * 100, np.nan)


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


# -------------------- Benchmark functions --------------------
def make_rank_benchmark(df, output_filename):
    """
    Create a rank-level benchmark table.

    This table compares the rank distribution of:
    - all records
    - identifiable records
    - unidentifiable records
    - first contracts
    - non-first identifiable records
    - deaths
    - repatriations
    - death + repatriation

    This helps check whether first contracts were aligned with major exits and
    with the overall rank structure.
    """

    all_records = df.groupby("rank_parent").size().rename("all_records_n")

    identifiable_records = (
        df[df["has_person_cluster_id"]]
        .groupby("rank_parent")
        .size()
        .rename("identifiable_records_n")
    )

    unidentifiable_records = (
        df[~df["has_person_cluster_id"]]
        .groupby("rank_parent")
        .size()
        .rename("unidentifiable_records_n")
    )

    first_contracts = (
        df[df["is_first_contract_true"] == 1]
        .groupby("rank_parent")
        .size()
        .rename("first_contracts_n")
    )

    non_first_identifiable = (
        df[
            (df["has_person_cluster_id"]) &
            (df["is_first_contract_true"] == 0)
        ]
        .groupby("rank_parent")
        .size()
        .rename("non_first_identifiable_n")
    )

    deaths = (
        df[df["outcome_group_revised"] == "Death"]
        .groupby("rank_parent")
        .size()
        .rename("deaths_n")
    )

    repatriated = (
        df[df["outcome_group_revised"] == "Repatriated"]
        .groupby("rank_parent")
        .size()
        .rename("repatriated_n")
    )

    death_repatriated = (
        df[df["outcome_group_revised"].isin(["Death", "Repatriated"])]
        .groupby("rank_parent")
        .size()
        .rename("death_repatriated_n")
    )

    out = pd.concat(
        [
            all_records,
            identifiable_records,
            unidentifiable_records,
            first_contracts,
            non_first_identifiable,
            deaths,
            repatriated,
            death_repatriated,
        ],
        axis=1,
    ).fillna(0)

    out = out.reset_index()

    count_cols = [
        "all_records_n",
        "identifiable_records_n",
        "unidentifiable_records_n",
        "first_contracts_n",
        "non_first_identifiable_n",
        "deaths_n",
        "repatriated_n",
        "death_repatriated_n",
    ]

    for col in count_cols:
        out[col] = out[col].astype(int)

    # Shares across rank groups
    out = add_share_column(out, "all_records_n", "all_records_share")
    out = add_share_column(out, "identifiable_records_n", "identifiable_records_share")
    out = add_share_column(out, "unidentifiable_records_n", "unidentifiable_records_share")
    out = add_share_column(out, "first_contracts_n", "first_contract_share")
    out = add_share_column(out, "non_first_identifiable_n", "non_first_identifiable_share")
    out = add_share_column(out, "deaths_n", "death_share")
    out = add_share_column(out, "repatriated_n", "repatriated_share")
    out = add_share_column(out, "death_repatriated_n", "death_repatriated_share")

    # Within-rank rates
    out["missing_person_cluster_pct_within_rank"] = safe_pct(
        out["unidentifiable_records_n"],
        out["all_records_n"]
    ).round(2)

    out["first_contract_rate_among_identifiable_within_rank"] = safe_pct(
        out["first_contracts_n"],
        out["identifiable_records_n"]
    ).round(2)

    out["death_rate_within_rank_all_records"] = safe_pct(
        out["deaths_n"],
        out["all_records_n"]
    ).round(2)

    out["repatriated_rate_within_rank_all_records"] = safe_pct(
        out["repatriated_n"],
        out["all_records_n"]
    ).round(2)

    out["death_repatriated_rate_within_rank_all_records"] = safe_pct(
        out["death_repatriated_n"],
        out["all_records_n"]
    ).round(2)

    # Differences between first contracts and exits
    out["first_contract_minus_death_share"] = (
        out["first_contract_share"] - out["death_share"]
    ).round(2)

    out["first_contract_minus_repatriated_share"] = (
        out["first_contract_share"] - out["repatriated_share"]
    ).round(2)

    out["first_contract_minus_death_repatriated_share"] = (
        out["first_contract_share"] - out["death_repatriated_share"]
    ).round(2)

    # Differences between all records and exits
    out["all_records_minus_death_share"] = (
        out["all_records_share"] - out["death_share"]
    ).round(2)

    out["all_records_minus_repatriated_share"] = (
        out["all_records_share"] - out["repatriated_share"]
    ).round(2)

    out["all_records_minus_death_repatriated_share"] = (
        out["all_records_share"] - out["death_repatriated_share"]
    ).round(2)

    # Differences between identifiable records and exits
    out["identifiable_minus_death_share"] = (
        out["identifiable_records_share"] - out["death_share"]
    ).round(2)

    out["identifiable_minus_repatriated_share"] = (
        out["identifiable_records_share"] - out["repatriated_share"]
    ).round(2)

    out["identifiable_minus_death_repatriated_share"] = (
        out["identifiable_records_share"] - out["death_repatriated_share"]
    ).round(2)

    # Sort ranks in the same order as previous outputs
    out["rank_parent"] = pd.Categorical(
        out["rank_parent"],
        categories=RANK_ORDER,
        ordered=True
    )

    out = out.sort_values("rank_parent").reset_index(drop=True)

    save_csv(out, os.path.join(TABLES, output_filename))

    return out


def make_decade_rank_benchmark(df, output_filename):
    """
    Create a decade-rank benchmark table.

    Shares are calculated within each decade. This helps check whether the
    mismatch between first contracts and major exits is stable over time.
    """

    decades = sorted(df["decade"].dropna().unique())

    full_index = pd.MultiIndex.from_product(
        [decades, RANK_ORDER],
        names=["decade", "rank_parent"]
    )

    all_records = (
        df.groupby(["decade", "rank_parent"])
        .size()
        .rename("all_records_n")
    )

    identifiable_records = (
        df[df["has_person_cluster_id"]]
        .groupby(["decade", "rank_parent"])
        .size()
        .rename("identifiable_records_n")
    )

    unidentifiable_records = (
        df[~df["has_person_cluster_id"]]
        .groupby(["decade", "rank_parent"])
        .size()
        .rename("unidentifiable_records_n")
    )

    first_contracts = (
        df[df["is_first_contract_true"] == 1]
        .groupby(["decade", "rank_parent"])
        .size()
        .rename("first_contracts_n")
    )

    deaths = (
        df[df["outcome_group_revised"] == "Death"]
        .groupby(["decade", "rank_parent"])
        .size()
        .rename("deaths_n")
    )

    repatriated = (
        df[df["outcome_group_revised"] == "Repatriated"]
        .groupby(["decade", "rank_parent"])
        .size()
        .rename("repatriated_n")
    )

    death_repatriated = (
        df[df["outcome_group_revised"].isin(["Death", "Repatriated"])]
        .groupby(["decade", "rank_parent"])
        .size()
        .rename("death_repatriated_n")
    )

    out = pd.concat(
        [
            all_records,
            identifiable_records,
            unidentifiable_records,
            first_contracts,
            deaths,
            repatriated,
            death_repatriated,
        ],
        axis=1,
    )

    out = out.reindex(full_index).fillna(0).reset_index()

    count_cols = [
        "all_records_n",
        "identifiable_records_n",
        "unidentifiable_records_n",
        "first_contracts_n",
        "deaths_n",
        "repatriated_n",
        "death_repatriated_n",
    ]

    for col in count_cols:
        out[col] = out[col].astype(int)

    # Shares within each decade
    share_pairs = [
        ("all_records_n", "all_records_share_within_decade"),
        ("identifiable_records_n", "identifiable_records_share_within_decade"),
        ("unidentifiable_records_n", "unidentifiable_records_share_within_decade"),
        ("first_contracts_n", "first_contract_share_within_decade"),
        ("deaths_n", "death_share_within_decade"),
        ("repatriated_n", "repatriated_share_within_decade"),
        ("death_repatriated_n", "death_repatriated_share_within_decade"),
    ]

    for count_col, share_col in share_pairs:
        totals = out.groupby("decade")[count_col].transform("sum")
        out[share_col] = np.where(totals > 0, out[count_col] / totals * 100, np.nan)
        out[share_col] = out[share_col].round(2)

    # Differences within decade
    out["first_contract_minus_death_share"] = (
        out["first_contract_share_within_decade"] -
        out["death_share_within_decade"]
    ).round(2)

    out["first_contract_minus_repatriated_share"] = (
        out["first_contract_share_within_decade"] -
        out["repatriated_share_within_decade"]
    ).round(2)

    out["first_contract_minus_death_repatriated_share"] = (
        out["first_contract_share_within_decade"] -
        out["death_repatriated_share_within_decade"]
    ).round(2)

    out["all_records_minus_death_share"] = (
        out["all_records_share_within_decade"] -
        out["death_share_within_decade"]
    ).round(2)

    out["all_records_minus_repatriated_share"] = (
        out["all_records_share_within_decade"] -
        out["repatriated_share_within_decade"]
    ).round(2)

    out["all_records_minus_death_repatriated_share"] = (
        out["all_records_share_within_decade"] -
        out["death_repatriated_share_within_decade"]
    ).round(2)

    out["rank_parent"] = pd.Categorical(
        out["rank_parent"],
        categories=RANK_ORDER,
        ordered=True
    )

    out = out.sort_values(["decade", "rank_parent"]).reset_index(drop=True)

    save_csv(out, os.path.join(TABLES, output_filename))

    return out


# -------------------- Load contracts --------------------
contracts_path = os.path.join(DATA_RAW, "voc_persons_contracts.csv")

if not os.path.exists(contracts_path):
    print(f"[error] Missing file: {contracts_path}")
    sys.exit(1)

contracts = pd.read_csv(
    contracts_path,
    usecols=[
        "vocop_id",
        "person_cluster_id",
        "disambiguated_person",
        "rank_id",
        "date_begin_contract",
        "reason_end_contract",
    ],
    low_memory=False
)

print(f"[info] Loaded full dataset: {len(contracts):,} records")


# -------------------- Create year and decade --------------------
contracts["date_begin_contract"] = pd.to_datetime(
    contracts["date_begin_contract"],
    errors="coerce"
)

contracts["contract_start_year"] = contracts["date_begin_contract"].dt.year
contracts["decade"] = (contracts["contract_start_year"] // 10) * 10


# -------------------- Create true first-contract indicator on the full dataset --------------------
contracts["has_person_cluster_id"] = contracts["person_cluster_id"].notna()

first_dates_full = (
    contracts
    .groupby("person_cluster_id")["date_begin_contract"]
    .transform("min")
)

contracts["is_first_contract_true"] = (
    (contracts["has_person_cluster_id"]) &
    (contracts["date_begin_contract"] == first_dates_full)
).astype(int)

print("[info] Created is_first_contract_true using the full dataset before filtering.")


# -------------------- Load and map ranks --------------------
ranks_path = os.path.join(DATA_RAW, "voc_ranks.csv")

if not os.path.exists(ranks_path):
    print(f"[error] Missing file: {ranks_path}")
    sys.exit(1)

ranks = pd.read_csv(
    ranks_path,
    usecols=["rank_id", "category"],
    low_memory=False
)

contracts["rank_id"] = to_int_like(contracts["rank_id"])
ranks["rank_id"] = to_int_like(ranks["rank_id"])

contracts = contracts.merge(
    ranks,
    on="rank_id",
    how="left"
)

contracts["rank_parent"] = contracts["category"].apply(map_parent_rank)

print("[info] Added rank_parent using voc_ranks.csv category column.")


# -------------------- Filter to 1700-1780s for actual analysis --------------------
before_filter = len(contracts)

analysis = contracts[
    (contracts["contract_start_year"] >= START_YEAR) &
    (contracts["contract_start_year"] < END_YEAR_EXCLUSIVE)
].copy()

print(f"[info] Filtered to 1700-1780s: {before_filter:,} -> {len(analysis):,}")


# -------------------- Map reason_end_contract --------------------
analysis["reason_end_contract_raw"] = analysis["reason_end_contract"]
analysis["reason_end_contract_normalized"] = (
    analysis["reason_end_contract_raw"].apply(normalize_reason)
)

analysis["outcome_group_revised"] = (
    analysis["reason_end_contract_normalized"]
    .map(OUTCOME_MAPPING_NORMALIZED)
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

    unmapped_table = (
        analysis.loc[
            analysis["reason_end_contract_raw"].isin(unmapped),
            "reason_end_contract_raw"
        ]
        .value_counts()
        .reset_index()
    )

    unmapped_table.columns = ["reason_end_contract_raw", "count"]

    save_csv(
        unmapped_table,
        os.path.join(TABLES, "v3_unmapped_reason_end_contract_values_1700_1780.csv")
    )

    print("\nPlease add these values to OUTCOME_MAPPING_NORMALIZED before using the results.")
    sys.exit(1)

print("[info] All non-null reason_end_contract categories are mapped.")


# -------------------- Basic totals --------------------
total_records = len(analysis)
total_first_contracts = int(analysis["is_first_contract_true"].sum())
total_identifiable = int(analysis["has_person_cluster_id"].sum())
total_unidentifiable = int((~analysis["has_person_cluster_id"]).sum())

print(f"[info] Total records in analysis subset: {total_records:,}")
print(f"[info] Identifiable records with person_cluster_id: {total_identifiable:,}")
print(f"[info] Unidentifiable records without person_cluster_id: {total_unidentifiable:,}")
print(f"[info] Total true first contracts in analysis subset: {total_first_contracts:,}")


# ======================================================
# OUTPUT 1: raw reason to revised outcome mapping check
# ======================================================
reason_mapping = (
    analysis
    .assign(
        reason_end_contract_raw=analysis["reason_end_contract_raw"].fillna("NULL")
    )
    .groupby(
        [
            "reason_end_contract_raw",
            "reason_end_contract_normalized",
            "outcome_group_revised"
        ],
        dropna=False
    )
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

reason_mapping["percentage_of_dataset"] = (
    reason_mapping["count"] / total_records * 100
).round(4)

save_csv(
    reason_mapping,
    os.path.join(TABLES, "v3_reason_end_contract_mapping_check_1700_1780.csv")
)


# ======================================================
# OUTPUT 2: missing person_cluster_id by disambiguation
# ======================================================
missing_by_disambiguation = (
    analysis
    .groupby("disambiguated_person", dropna=False)
    .agg(
        records=("vocop_id", "size"),
        missing_person_cluster_id=("person_cluster_id", lambda s: s.isna().sum())
    )
    .reset_index()
)

missing_by_disambiguation["missing_pct"] = (
    missing_by_disambiguation["missing_person_cluster_id"] /
    missing_by_disambiguation["records"] * 100
).round(2)

save_csv(
    missing_by_disambiguation,
    os.path.join(TABLES, "v3_missing_person_cluster_by_disambiguation_1700_1780.csv")
)


# ======================================================
# OUTPUT 3: missing person_cluster_id by rank
# ======================================================
missing_by_rank = (
    analysis
    .groupby("rank_parent", dropna=False)
    .agg(
        records=("vocop_id", "size"),
        missing_person_cluster_id=("person_cluster_id", lambda s: s.isna().sum())
    )
    .reset_index()
)

missing_by_rank["missing_pct"] = (
    missing_by_rank["missing_person_cluster_id"] /
    missing_by_rank["records"] * 100
).round(2)

missing_by_rank["rank_parent"] = pd.Categorical(
    missing_by_rank["rank_parent"],
    categories=RANK_ORDER,
    ordered=True
)

missing_by_rank = missing_by_rank.sort_values("rank_parent").reset_index(drop=True)

save_csv(
    missing_by_rank,
    os.path.join(TABLES, "v3_missing_person_cluster_by_rank_1700_1780.csv")
)


# ======================================================
# OUTPUT 4: rank-level benchmark using all records
# ======================================================
rank_benchmark_all = make_rank_benchmark(
    analysis,
    "v3_rank_first_contract_exit_benchmark_all_records_1700_1780.csv"
)


# ======================================================
# OUTPUT 5: rank-level benchmark using identifiable records only
# ======================================================
analysis_identifiable = analysis[analysis["has_person_cluster_id"]].copy()

rank_benchmark_identifiable = make_rank_benchmark(
    analysis_identifiable,
    "v3_rank_first_contract_exit_benchmark_identifiable_only_1700_1780.csv"
)


# ======================================================
# OUTPUT 6: decade-rank benchmark using all records
# ======================================================
decade_rank_benchmark_all = make_decade_rank_benchmark(
    analysis,
    "v3_decade_rank_first_contract_exit_benchmark_all_records_1700_1780.csv"
)


# ======================================================
# OUTPUT 7: decade-rank benchmark using identifiable records only
# ======================================================
decade_rank_benchmark_identifiable = make_decade_rank_benchmark(
    analysis_identifiable,
    "v3_decade_rank_first_contract_exit_benchmark_identifiable_only_1700_1780.csv"
)


# -------------------- Console summary --------------------
summary_cols = [
    "rank_parent",
    "all_records_share",
    "identifiable_records_share",
    "first_contract_share",
    "death_share",
    "repatriated_share",
    "death_repatriated_share",
    "first_contract_minus_death_share",
    "first_contract_minus_repatriated_share",
    "first_contract_minus_death_repatriated_share",
]

print("\n[summary] Rank benchmark using all records")
print(rank_benchmark_all[summary_cols].to_string(index=False))

print("\n[summary] Rank benchmark using identifiable records only")
print(rank_benchmark_identifiable[summary_cols].to_string(index=False))

print("\n[done] Benchmark script finished.")
print("[done] Output files are saved in the tables folder.")