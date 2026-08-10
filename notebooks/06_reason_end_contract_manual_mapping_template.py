import os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(BASE, "data_raw")
TABLES = os.path.join(BASE, "tables")

os.makedirs(TABLES, exist_ok=True)

contracts_path = os.path.join(DATA_RAW, "voc_persons_contracts.csv")
contracts = pd.read_csv(contracts_path, low_memory=False)

reason_counts = (
    contracts["reason_end_contract"]
    .fillna("MISSING")
    .value_counts(dropna=False)
    .reset_index()
)

reason_counts.columns = ["reason_end_contract", "count"]

# Empty columns for manual classification
reason_counts["proposed_group"] = ""
reason_counts["reason_for_grouping"] = ""
reason_counts["source_or_note"] = ""

output_path = os.path.join(TABLES, "reason_end_contract_manual_mapping_template.csv")
reason_counts.to_csv(output_path, index=False)

print(reason_counts.head(50))
print(f"\nSaved to: {output_path}")