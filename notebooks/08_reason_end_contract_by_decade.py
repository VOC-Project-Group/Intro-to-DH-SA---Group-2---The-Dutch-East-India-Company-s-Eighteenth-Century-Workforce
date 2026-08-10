import os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(BASE, "data_raw")
TABLES = os.path.join(BASE, "tables")

os.makedirs(TABLES, exist_ok=True)

contracts_path = os.path.join(DATA_RAW, "voc_persons_contracts.csv")
contracts = pd.read_csv(contracts_path, low_memory=False)

contracts["contract_start_year"] = pd.to_datetime(
    contracts["date_begin_contract"], errors="coerce"
).dt.year

contracts["decade"] = (contracts["contract_start_year"] // 10) * 10
contracts["reason_end_contract"] = contracts["reason_end_contract"].fillna("MISSING")

# Raw reason distribution by decade
reason_by_decade = (
    contracts
    .groupby(["decade", "reason_end_contract"], dropna=False)
    .size()
    .reset_index(name="count")
)

# Add decade totals and percentages
decade_totals = (
    reason_by_decade
    .groupby("decade", dropna=False)["count"]
    .sum()
    .reset_index(name="decade_total")
)

reason_by_decade = reason_by_decade.merge(decade_totals, on="decade", how="left")
reason_by_decade["percentage_within_decade"] = (
    reason_by_decade["count"] / reason_by_decade["decade_total"] * 100
).round(2)

output_long = os.path.join(TABLES, "reason_end_contract_by_decade_long.csv")
reason_by_decade.to_csv(output_long, index=False)

# Pivot table for easier viewing
pivot = reason_by_decade.pivot_table(
    index="decade",
    columns="reason_end_contract",
    values="percentage_within_decade",
    fill_value=0
).reset_index()

output_pivot = os.path.join(TABLES, "reason_end_contract_by_decade_pct_pivot.csv")
pivot.to_csv(output_pivot, index=False)

print(reason_by_decade.head(50))
print(f"\nSaved long file to: {output_long}")
print(f"Saved pivot file to: {output_pivot}")