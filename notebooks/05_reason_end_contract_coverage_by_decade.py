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

coverage_by_decade = (
    contracts.groupby("decade", dropna=False)
    .agg(
        total_records=("reason_end_contract", "size"),
        known_reason=("reason_end_contract", lambda s: s.notna().sum()),
        missing_reason=("reason_end_contract", lambda s: s.isna().sum()),
    )
    .reset_index()
)

coverage_by_decade["known_reason_pct"] = (
    coverage_by_decade["known_reason"] / coverage_by_decade["total_records"] * 100
).round(2)

coverage_by_decade["missing_reason_pct"] = (
    coverage_by_decade["missing_reason"] / coverage_by_decade["total_records"] * 100
).round(2)

output_path = os.path.join(TABLES, "reason_end_contract_coverage_by_decade.csv")
coverage_by_decade.to_csv(output_path, index=False)

print(coverage_by_decade)
print(f"\nSaved to: {output_path}")