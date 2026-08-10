import os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(BASE, "data_raw")
TABLES = os.path.join(BASE, "tables")

os.makedirs(TABLES, exist_ok=True)

contracts_path = os.path.join(DATA_RAW, "voc_persons_contracts.csv")
contracts = pd.read_csv(contracts_path, low_memory=False)

total_rows = len(contracts)

reason_counts = (
    contracts["reason_end_contract"]
    .fillna("MISSING")
    .value_counts(dropna=False)
    .reset_index()
)

reason_counts.columns = ["reason_end_contract", "count"]
reason_counts["percentage"] = (reason_counts["count"] / total_rows * 100).round(2)

output_path = os.path.join(TABLES, "reason_end_contract_counts_full.csv")
reason_counts.to_csv(output_path, index=False)

print(f"Total rows: {total_rows}")
print(reason_counts.head(50))
print(f"\nSaved to: {output_path}")